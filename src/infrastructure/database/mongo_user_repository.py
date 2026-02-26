from pymongo import AsyncMongoClient
from src.application.users.i_users_repository import UserRepository
from src.config import settings

class MongoUserRepository(UserRepository):

    def __init__(
            self, 
            database_name: str = settings.MONGO_DB_NAME, 
            mongodb_uri: str = settings.MONGO_URI,
            collection_name: str = settings.MONGO_USERS_COLLECTION
        ) -> None:
        
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name

        try:
            self.client = AsyncMongoClient(mongodb_uri, appname='agentic-back')
        except Exception as err:
            raise err
        
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]

    async def create_user(self, user):

        await self.collection.insert_one(
            {
                'name': user.name,
                'email': user.email,
                'password': user.password
            }
        )

    async def get_user_by_email(self, email: str):
        user = await self.collection.find_one({'email': email}, {'_id': 0})
        user['password'] = user['password'].decode('utf-8') if user and 'password' in user else None
        return user
