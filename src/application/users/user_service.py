from src.application.exceptions.bad_request import BadRequestException
from src.application.exceptions.user.user_already_exists import UserAlreadyExistsException
from src.application.exceptions.user.user_not_found_ex import UserNotFoundException
from src.application.users.i_users_repository import UserRepository
from src.domain.user import User
import bcrypt

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user_email, user_name, user_password):
        if not user_email or not user_name or not user_password:
            raise BadRequestException('required params missing.')
        
        existing_user = await self.get_user_by_email(user_email)

        if existing_user:
            raise UserAlreadyExistsException('user already exists.')

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), salt)

        user = User(
            name=user_name,
            email=user_email,
            password=hashed_password
        )

        return await self.repository.create_user(user)

    async def get_user_by_email(self, user_email):
        user = await self.repository.get_user_by_email(user_email)

        print(user)

        if not user:
            raise UserNotFoundException('user not found.')

        user['_id']= str(user['_id'])
        return user

        
