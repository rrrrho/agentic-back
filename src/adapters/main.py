from contextlib import asynccontextmanager
from pymongo import AsyncMongoClient
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import uvicorn
from src.adapters.global_exception_handler import add_exception_handlers
from src.application.memory.long_term_memory_int import create_search_database_tool, create_web_search_tool
from src.application.threads.threads_service import ThreadService
from src.config import settings

from src.adapters.dependencies import get_checkpointer, get_compiled_graph, get_compiled_image_graph
from src.application.workflow.generate_response import Agent, LanguageModels
from src.infrastructure.database.embeddings import get_hugging_face_embedding
from src.infrastructure.database.mongo_thread_repository import MongoThreadRepository
from src.infrastructure.database.retrievers import get_mongo_hybrid_search_retriever
from src.infrastructure.database.splitters import get_splitter
from src.infrastructure.database.vector_stores import get_mongo_vector_store
from src.infrastructure.llm.providers import get_groq_chat_model, get_open_router_chat_model
from src.infrastructure.tools.long_term_memory_tool import LongTermMemoryTool
from src.infrastructure.tools.metasearch_engine import SearXNGWebSearchEngine

from src.adapters.threads_api import router as http_router
from src.adapters.users_api import router as users_router
from src.adapters.agent_api import router as agent_router

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

    #llm = get_groq_chat_model(temperature=0.7, model_name=settings.GROQ_LLM_MODEL)
    chat_model = get_open_router_chat_model(temperature=0.7, model_name=settings.OPEN_ROUTER_MODEL)
    #poor_llm = get_groq_chat_model(temperature=0.7, model_name=settings.GROQ_SUMMARY_LLM_MODEL)
    summary_model = get_open_router_chat_model(temperature=0.7, model_name='openai/gpt-4.1-mini')
    image_model = get_open_router_chat_model(temperature=0.7, model_name=settings.OPEN_ROUTER_IMAGE_MODEL)

    graph = get_compiled_graph(checkpointer=checkpointer, tools=tools, llm=chat_model, poor_llm=summary_model)
    image_graph = get_compiled_image_graph(checkpointer=checkpointer, translator_model=summary_model, image_generation_model=image_model)

    models = LanguageModels(chat_model=chat_model, summary_model=summary_model, image_model=summary_model)
    app.state.agent = Agent(graph=graph, image_graph=image_graph, llms=models)

    yield

    await db_client.close()

fastapi_app = FastAPI(lifespan=lifespan)

add_exception_handlers(fastapi_app)
fastapi_app.include_router(http_router)
fastapi_app.include_router(users_router)
fastapi_app.include_router(agent_router)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=['http://localhost:5173'])
app = socketio.ASGIApp(sio, fastapi_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



