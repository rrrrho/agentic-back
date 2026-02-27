import datetime
from typing import Generic, Type, TypeVar
from pydantic import BaseModel
from pymongo import AsyncMongoClient
from src.config import settings
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

T = TypeVar("T", bound=BaseModel)

class MongoClientWrapper(Generic[T]):

    def __init__(
            self, 
            model: Type[T],
            mongodb_uri: str = settings.MONGO_URI
        ) -> None:
        
        self.model = model
        self.mongodb_uri = mongodb_uri

        try:
            self.client = AsyncMongoClient(mongodb_uri, appname='agentic-back')
        except Exception as err:
            raise err

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