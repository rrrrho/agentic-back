from abc import ABC

from src.domain.user import User

class UserRepository(ABC):
    async def create_user(self, user: User) -> str:
        pass

    async def get_user_by_email(self, email: str) -> User:
        pass

    async def update_user(self, user_id: str, updated_user: User):
        pass

    async def delete_user_by_id(self, user_id: str):
        pass

