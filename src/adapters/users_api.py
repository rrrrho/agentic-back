from fastapi import APIRouter, Request, Depends
from src.application.users.user_service import UserService
from src.infrastructure.database.mongo_user_repository import MongoUserRepository
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from jose import jwt

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

service = UserService(repository=MongoUserRepository())

def encode_token(payload: dict) -> str:
    token = jwt.encode(payload, 'my-secret', algorithm='HS256')
    return token

def decode_token(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    data = jwt.decode(token, 'my-secret', algorithms=['HS256'])

@router.post('/token')
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    token = encode_token({  })
    
    return { 'access_token': token }

@router.get('/user/profile')
def profile(my_user: Annotated[dict, Depends(decode_token)]):
    return my_user

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

