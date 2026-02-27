import datetime
from typing import Generic, Type, TypeVar
from bson import ObjectId
from pydantic import BaseModel
from src.application.threads.i_thread_repository import ThreadRepository
from src.config import settings

T = TypeVar("T", bound=BaseModel)

class MongoThreadRepository(ThreadRepository, Generic[T]):

    def __init__(
            self, 
            client,
            database,
            model: Type[T],
            metadata_collection: str = settings.MONGO_THREAD_METADATA_COLLECTION,
            checkpoint_collection: str = settings.MONGO_STATE_CHECKPOINT_COLLECTION,
            writes_collection: str = settings.MONGO_STATE_WRITES_COLLECTION
        ) -> None:
        
        self.client = client
        self.database = database
        self.model = model
        
        self.metadata_collection = self.database[metadata_collection]
        self.checkpoint_collection = self.database[checkpoint_collection]
        self.writes_collection = self.database[writes_collection]
        

    async def update_thread_title(self, thread_id: ObjectId, title: str):
        await self.metadata_collection.update_one(
            { '_id' : thread_id },
            { '$set': { 'title': title, 'updated_at': datetime.datetime.now() } },
            upsert=True
        )

    async def get_threads_by_user_id(self, user_id: ObjectId):
        cursor = self.metadata_collection.find( { 'user_id': user_id }, { 'user_id': 0 })
        threads = await cursor.to_list(length=100)        

        for thread in threads:
            thread['_id'] = str(thread['_id'])
            
        return threads
    
        return

    async def create_thread(self, user_id: ObjectId, title: str):
        
        response = await self.metadata_collection.insert_one({
            'user_id': user_id,
            'title': title,
            'created_at': datetime.datetime.now()
        })

        return str(response.inserted_id)

    async def delete_thread(self, thread_id: ObjectId):

        async def perform_delete(session):
            await self.checkpoint_collection.delete_many(
                { 'thread_id' : str(thread_id) }, 
                session=session
            )
            await self.metadata_collection.delete_one(
                { '_id' : thread_id }, 
                session=session
            )
            await self.writes_collection.delete_many(
                { 'thread_id' : str(thread_id) },
                session=session
            )

        async with self.client.start_session() as session:
            try:

                await session.with_transaction(perform_delete)
                print(f'conversation with id {str(thread_id)} deleted.')
                
            except Exception as err:
                print(f'error ocurred during transaction, auto-rollback applied. error details: {err}')
                raise err
