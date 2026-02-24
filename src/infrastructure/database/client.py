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

    async def update_thread_title(self, thread_id: str, title: str):
        db = self.client[self.database_name]
        collection = db['threads_metadata']
        
        await collection.update_one(
            {"thread_id": thread_id},
            {"$set": {'title': title, 'updated_at': datetime.datetime.now()}},
            upsert=True
        )

    async def create_thread_title(self, thread_id: str, title: str):
        db = self.client[self.database_name]
        collection = db['threads_metadata']
        
        await collection.insert_one({
            'thread_id': thread_id,
            'title': title,
            'created_at': datetime.datetime.now()
        })

    async def delete_thread(self, thread_id: str):
        db = self.client[self.database_name]
        threads_collection = db['threads_metadata']
        checkpoints_collection = db['agentic_back_checkpoints']
        writes_collection = db['agentic_back_writes']

        async def perform_delete(session):
            await checkpoints_collection.delete_many(
                {"thread_id": thread_id}, 
                session=session
            )
            await threads_collection.delete_one(
                {"thread_id": thread_id}, 
                session=session
            )
            await writes_collection.delete_many(
                {"thread_id": thread_id},
                session=session
            )

        async with self.client.start_session() as session:
            try:

                await session.with_transaction(perform_delete)
                print(f"Conversación {thread_id} eliminada con éxito.")
                
            except Exception as err:
                print(f"Error en la transacción, rollback automático aplicado. Error: {err}")
                raise err

