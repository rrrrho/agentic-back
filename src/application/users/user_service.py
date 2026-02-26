from src.application.users.i_users_repository import UserRepository
from src.domain.user import User
import bcrypt

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user_email, user_name, user_password):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), salt)

        user = User(
            name=user_name,
            email=user_email,
            password=hashed_password
        )

        await self.repository.create_user(user)

    async def get_user_by_email(self, user_email):
        user = await self.repository.get_user_by_email(user_email)
        return user

        
