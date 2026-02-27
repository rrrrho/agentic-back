from http.client import HTTPException
from fastapi import Request
from jose import jwt
from src.config import settings

def encode_token(payload: dict) -> str:
    token = jwt.encode(payload, settings.AUTH_JWT_SECRET, algorithm=settings.AUTH_JWT_ALGORITHM)
    return token

def decode_token(request: Request) -> dict:
    token = request.cookies.get('access_token')
    
    if not token:
        raise HTTPException(status_code=401, detail="No estás autenticado (Cookie no encontrada)")
    data = jwt.decode(token, settings.AUTH_JWT_SECRET, algorithms=[settings.AUTH_JWT_ALGORITHM])
    return data