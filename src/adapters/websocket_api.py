import asyncio
from contextlib import asynccontextmanager
import datetime
from http.cookies import SimpleCookie
from jose import JWTError, jwt
import uuid
from pymongo import AsyncMongoClient
import uvicorn
from pydantic import BaseModel
from fastapi import Depends, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
import socketio
from src.application.memory.long_term_memory_int import create_search_database_tool, create_web_search_tool
from src.application.threads.threads_service import ThreadService
from src.config import settings

from src.adapters.dependencies import get_checkpointer, get_compiled_graph, get_thread_service
from src.application.workflow.generate_response import Agent
from src.infrastructure.database.client import MongoClientWrapper
from src.infrastructure.database.embeddings import get_hugging_face_embedding
from src.infrastructure.database.mongo_thread_repository import MongoThreadRepository
from src.infrastructure.database.retrievers import get_mongo_hybrid_search_retriever
from src.infrastructure.database.splitters import get_splitter
from src.infrastructure.database.vector_stores import get_mongo_vector_store
from src.infrastructure.llm.providers import get_groq_chat_model
from src.infrastructure.tools.long_term_memory_tool import LongTermMemoryTool
from src.infrastructure.tools.metasearch_engine import SearXNGWebSearchEngine

from src.adapters.http_api import router as http_router
from src.adapters.users_api import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """handles startup and shutdown events for the API."""
    db_client = AsyncMongoClient(settings.MONGO_URI, appname='agentic-back')
    app.state.mongo_client = db_client
    db = db_client[settings.MONGO_DB_NAME]
    app.state.mongo_database = db
    thread_repo = MongoThreadRepository(client=db_client, database=db, model=BaseModel)
    app.state.thread_service = ThreadService(repository=thread_repo)

    checkpointer = get_checkpointer(
        db_client=db_client, 
        db_name=settings.MONGO_DB_NAME, 
        checkpoint_collection_name=settings.MONGO_STATE_CHECKPOINT_COLLECTION, 
        writes_collection_name=settings.MONGO_STATE_WRITES_COLLECTION)

    embedding = get_hugging_face_embedding(model_id=settings.RAG_TEXT_EMBEDDING_MODEL_ID, device=settings.RAG_DEVICE)
    vector_store = get_mongo_vector_store(embedding=embedding)
    splitter = get_splitter(chunk_size=settings.RAG_CHUNK_SIZE)
    retriever = get_mongo_hybrid_search_retriever(vector_store=vector_store)
    web_search_engine = SearXNGWebSearchEngine()

    rag_tool = LongTermMemoryTool(vector_store=vector_store, splitter=splitter, retriever=retriever, web_search_engine=web_search_engine)
    tools = [create_search_database_tool(retriever=rag_tool), create_web_search_tool(retriever=rag_tool)]

    llm = get_groq_chat_model(temperature=0.7, model_name=settings.GROQ_LLM_MODEL)
    poor_llm = get_groq_chat_model(temperature=0.7, model_name=settings.GROQ_SUMMARY_LLM_MODEL)

    graph = get_compiled_graph(checkpointer=checkpointer, tools=tools, llm=llm, poor_llm=poor_llm)
    app.state.agent = Agent(graph=graph, llms=[ { 'tag': 'poor', 'model': poor_llm } ] )

    yield

    await db_client.close()

fastapi_app = FastAPI(lifespan=lifespan)
fastapi_app.include_router(http_router)
fastapi_app.include_router(users_router)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=['http://localhost:5173'])
app = socketio.ASGIApp(sio, fastapi_app)

@sio.event
async def connect(sid, environ):
    cookies_str = environ.get('HTTP_COOKIE', '')
    cookie = SimpleCookie()
    cookie.load(cookies_str)

    access_token = cookie.get('access_token')

    if not access_token:
        raise ConnectionRefusedError('authentication required')

    try:
        payload = jwt.decode(access_token.value, settings.AUTH_JWT_SECRET, algorithms=[settings.AUTH_JWT_ALGORITHM])
        user_id = payload.get('_id')
        
        if not user_id:
            raise ConnectionRefusedError('invalid token payload')
            
        # save user_id in socket session
        await sio.save_session(sid, {'user_id': user_id})
        print(f'connected and authenticated client: {sid} - {user_id}')
        
    except JWTError:
        raise ConnectionRefusedError('invalid or expired token')

    print(f"connected client: {sid}")

@sio.on('chat')
async def chat(sid, data):
    agent = fastapi_app.state.agent
    service = fastapi_app.state.thread_service

    session = await sio.get_session(sid)
    user_id = session.get('user_id')

    try:
        if 'message' not in data:
            await sio.emit('error',
                {
                    "error": "invalid message format. required fields: 'message'"
                },
                to=sid
            )
            return
        
        title = ''
        if 'thread_id' not in data:
            message = [data['message']]

            title = await asyncio.create_task(
                agent.get_chat_title(
                messages=message
            ))

            thread_id = await service.create_thread(user_id, title)
            
        else:
            thread_id = data['thread_id']
            state = await agent.get_state(thread_id)
            messages = state.values.get('messages', [])

            title = await asyncio.create_task(
                agent.get_chat_title(
                messages=messages
            ))

            if title:
                await service.update_thread_title(thread_id, title)
            

        try:
            response_stream = agent.get_response(messages=data['message'], thread_id=thread_id)

            await sio.emit('status', { 'streaming': True }, to=sid)

            full_response = ''
            async for chunk in response_stream:
                full_response += chunk
                await sio.emit('chunk', { 'text': chunk }, to=sid)

            if title:
                await sio.emit('response', 
                    { 'response': full_response, 'streaming': False, 'thread_id': thread_id, 'title': title }, 
                    to=sid
                )
            else:
                await sio.emit('response', 
                    { 'response': full_response, 'streaming': False }, 
                    to=sid
                )

        except Exception as err:
            await sio.emit('error', { 'error': str(err) }, to=sid)

    except Exception as err:
        print(err)

@sio.event
async def disconnect(sid):
    print(f"disconnected client: {sid}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

