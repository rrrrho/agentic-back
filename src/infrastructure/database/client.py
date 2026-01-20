from typing import Generic, Type, TypeVar
from bson import ObjectId
from pydantic import BaseModel
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError
from src.config import settings
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

T = TypeVar("T", bound=BaseModel)

class MongoClientWrapper(Generic[T]):

    def __init__(
            self, 
            model: Type[T],
            database_name: str = settings.MONGO_DB_NAME, 
            mongodb_uri: str = settings.MONGO_URI
        ) -> None:
        
        self.model = model
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name

        try:
            self.client = AsyncMongoClient(mongodb_uri, appname='agentic-back')
            self.client.admin.command('ping')
        except Exception as err:
            raise err
        
        self.database = self.client[database_name]

    def get_checkpointer(self) -> AsyncMongoDBSaver:
        """returns an AsyncMongoDBSaver instance for state checkpointing."""

        return AsyncMongoDBSaver(
            client=self.client,
            db_name=self.database_name,
            checkpoint_collection_name=settings.MONGO_STATE_CHECKPOINT_COLLECTION,
            writes_collection_name=settings.MONGO_STATE_WRITES_COLLECTION
        )

    # context manager
    async def __aenter__(self) -> 'MongoClientWrapper':
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        """close the MongoDB connection.

        this method should be called when the service is no longer needed
        to properly release resources, unless using the context manager.
        """

        await self.client.close()

