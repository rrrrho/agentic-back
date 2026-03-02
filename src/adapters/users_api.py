from fastapi import APIRouter, Request, Depends, Response
from src.adapters.dependencies import get_user_service
from src.adapters.utilities import decode_token, encode_token
from src.application.users.user_service import UserService
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# --- Auth Endpoints ---

@router.post('/token')
async def login(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], service: UserService = Depends(get_user_service)):

    user = await service.get_user_by_email(form_data.username)
    token = encode_token(user)

    response.set_cookie(
        key='access_token', 
        value=token, 
        httponly=True, 
        secure=True,   
        samesite='Lax',  
        max_age=3600,   
    )

    response.status_code = 200

    return { 'message': 'logged successfully' }

@router.post('/logout')
async def logout(response: Response):
    response.delete_cookie(
        key='access_token', 
        httponly=True, 
        samesite='lax',
        secure=False    # true for HTTPS, false for localhost
    )

    return { 'message': 'logged out successfully' }


@router.get('/user/profile')
async def profile(response: Response, my_user: Annotated[dict, Depends(decode_token)], service: UserService = Depends(get_user_service)):
    return await service.get_user_by_email(my_user['email'])

# --- CRUD Endpoints ---

@router.post('/user')
async def post_user(request: Request, response: Response, service: UserService = Depends(get_user_service)):
    data = await request.json()
    user_email = data.get('email', '')
    user_name = data.get('name', '')
    user_password = data.get('password', '')

    id = await service.create_user(user_email=user_email, user_name=user_name, user_password=user_password)
    token = encode_token({'_id': id, 'email': user_email, 'name': user_name })

    response.set_cookie(
        key='access_token', 
        value=token, 
        httponly=True, 
        secure=True,   
        samesite='Lax',  
        max_age=3600,   
    )

    response.status_code = 201

    return { 'message': 'user created successfully' }

