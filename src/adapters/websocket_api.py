import asyncio
from contextlib import asynccontextmanager
import datetime
import uuid
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from src.application.memory.long_term_memory_int import create_search_database_tool, create_web_search_tool
from src.config import settings

from src.adapters.dependencies import get_compiled_graph
from src.application.workflow.generate_response import Agent
from src.infrastructure.database.client import MongoClientWrapper
from src.infrastructure.database.embeddings import get_hugging_face_embedding
from src.infrastructure.database.retrievers import get_mongo_hybrid_search_retriever
from src.infrastructure.database.splitters import get_splitter
from src.infrastructure.database.vector_stores import get_mongo_vector_store
from src.infrastructure.llm.providers import get_groq_chat_model
from src.infrastructure.tools.long_term_memory_tool import LongTermMemoryTool
from src.infrastructure.tools.metasearch_engine import SearXNGWebSearchEngine

from src.adapters.http_api import router as http_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """handles startup and shutdown events for the API."""
    db_client = MongoClientWrapper(model=BaseModel, database_name=settings.MONGO_DB_NAME)

    async with db_client:
        app.state.mongo_db = db_client
        checkpointer = db_client.get_checkpointer()

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

fastapi_app = FastAPI(lifespan=lifespan)
fastapi_app.include_router(http_router)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = socketio.ASGIApp(sio, fastapi_app)

@sio.event
async def connect(sid, environ):
    print(f"connected client: {sid}")

@sio.on('chat')
async def chat(sid, data):
    mongo = fastapi_app.state.mongo_db
    agent = fastapi_app.state.agent

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
            thread_id = str(uuid.uuid4())
            message = [data['message']]

            title = await asyncio.create_task(
                agent.get_chat_title(
                messages=message
            ))

            await mongo.create_thread_title(thread_id=thread_id, title=title)
            
        else:
            thread_id = data['thread_id']
            state = await agent.get_state(thread_id)
            messages = state.values.get('messages', [])

            title = await asyncio.create_task(
                agent.get_chat_title(
                messages=messages
            ))

            if title:
                await mongo.update_thread_title(thread_id=thread_id, title=title)
            

        try:
            response_stream = agent.get_response(messages=data['message'], thread_id=thread_id)

            await sio.emit('status', { 'streaming': True }, to=sid)

            full_response = ''
            async for chunk in response_stream:
                full_response += chunk
                await sio.emit('chunk', { 'text': chunk }, to=sid)

            await sio.emit('response', 
                { 'response': full_response, 'streaming': False, 'thread_id': thread_id, 'title': title }, 
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

