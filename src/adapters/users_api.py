from fastapi import APIRouter, Request
from src.application.users.user_service import UserService
from src.infrastructure.database.mongo_user_repository import MongoUserRepository

router = APIRouter()

service = UserService(repository=MongoUserRepository())

@router.post('/user')
async def post_user(request: Request):
    data = await request.json()
    user_email = data.get('email')
    user_name = data.get('name')
    user_password = data.get('password')

    if not user_email or not user_name or not user_password:
        return {'error': 'user_email, user_name and user_password are required'}

    await service.create_user(user_email=user_email, user_name=user_name, user_password=user_password)

    return {'message': 'user created successfully', 'user_email': user_email, 'user_name': user_name}