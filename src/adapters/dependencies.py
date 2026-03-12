from fastapi import Depends, Request
from pydantic import BaseModel
from src.application.image_workflow.graph import create_image_workflow_graph
from src.application.threads.threads_service import ThreadService
from src.application.users.user_service import UserService
from src.application.workflow.graph import create_workflow_graph
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from langchain_core.tools import BaseTool

from src.infrastructure.database.mongo_thread_repository import MongoThreadRepository
from src.infrastructure.database.mongo_user_repository import MongoUserRepository

from src.config import settings
from src.infrastructure.llm.providers import get_open_router_chat_model

models = {
    'fast': get_open_router_chat_model(temperature=0.7, model_name='google/gemini-3-flash-preview'),
    'reasoning': get_open_router_chat_model(temperature=0.7, model_name='google/gemini-3.1-pro-preview-customtools'),
}

def get_compiled_graph(checkpointer: AsyncMongoDBSaver, tools: list[BaseTool], llm, poor_llm):
    builder = create_workflow_graph(models=models, tools=tools, llm=llm, poor_llm=poor_llm)
    return builder.compile(checkpointer=checkpointer)

def get_compiled_image_graph(checkpointer: AsyncMongoDBSaver, translator_model, image_generation_model):
    builder = create_image_workflow_graph(translator_llm=translator_model, image_generation_llm=image_generation_model)
    return builder.compile(checkpointer=checkpointer)

def get_client(request: Request):
    return request.app.state.mongo_client

def get_database(client = Depends(get_client)):
    return client[settings.MONGO_DB_NAME]

def get_checkpointer(db_client, db_name, checkpoint_collection_name, writes_collection_name) -> AsyncMongoDBSaver:
    """returns an AsyncMongoDBSaver instance for state checkpointing."""

    return AsyncMongoDBSaver(
        client=db_client,
        db_name=db_name,
        checkpoint_collection_name=checkpoint_collection_name,
        writes_collection_name=writes_collection_name
    )

def get_thread_repository(db = Depends(get_database), client = Depends(get_client)):
    return MongoThreadRepository(client=client, database=db, model=BaseModel)

def get_user_repository(db = Depends(get_database)):
    return MongoUserRepository(database=db)

def get_thread_service(repository = Depends(get_thread_repository)):
    return ThreadService(repository=repository)

def get_user_service(repository = Depends(get_user_repository)):
    return UserService(repository=repository)

    