from src.application.threads.i_thread_repository import ThreadRepository
from bson import ObjectId


class ThreadService:
    def __init__(self, repository: ThreadRepository):
        self.repository = repository

    async def get_threads_by_user_id(self, user_id: str):
        user_id = ObjectId(user_id)

        try:
            threads = await self.repository.get_threads_by_user_id(user_id)
        
        except Exception as err:
            raise err
        
        return threads
    
    async def create_thread(self, user_id: str, title: str):
        user_id = ObjectId(user_id)

        try:
           return await self.repository.create_thread(user_id, title)
        
        except Exception as err:
            raise err
        
    async def update_thread_title(self, thread_id: str, title: str):
        thread_id = ObjectId(thread_id)

        try:
            await self.repository.update_thread_title(thread_id, title)
        
        except Exception as err:
            raise err
        
    async def delete_thread(self, thread_id: str):
        thread_id = ObjectId(thread_id)

        try:
            await self.repository.delete_thread(thread_id)
        
        except Exception as err:
            raise err
        
