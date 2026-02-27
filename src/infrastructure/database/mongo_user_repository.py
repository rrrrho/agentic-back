from src.application.users.i_users_repository import UserRepository
from src.config import settings
from bson import ObjectId

class MongoUserRepository(UserRepository):

    def __init__(
            self, 
            database,
            collection_name: str = settings.MONGO_USERS_COLLECTION
        ) -> None:
    
        self.database = database
        self.collection = self.database[collection_name]

    async def create_user(self, user):

        response = await self.collection.insert_one(
            {
                'name': user.name,
                'email': user.email,
                'password': user.password
            }
        )

        return str(response.inserted_id)

    async def get_user_by_email(self, email: str):
        user = await self.collection.find_one({ 'email': email }, { 'password': 0 })
        user['_id'] = str(user['_id'])
        return user
