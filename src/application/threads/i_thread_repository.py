from abc import ABC, abstractmethod

from bson import ObjectId


class ThreadRepository(ABC):
    @abstractmethod
    async def get_threads_by_user_id(self, user_id: ObjectId):
        pass

    @abstractmethod
    async def create_thread(self, user_id: ObjectId, title: str) -> str:
        pass

    @abstractmethod
    async def update_thread_title(self, thread_id: ObjectId, title: str):
        pass

    @abstractmethod
    async def delete_thread(self, thread_id: ObjectId):
        pass


