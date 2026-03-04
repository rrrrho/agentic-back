from fastapi import Request
from fastapi.responses import JSONResponse

from src.application.exceptions.domain_ex import DomainException
from src.application.exceptions.user.user_already_exists import UserAlreadyExistsException
from src.application.exceptions.user.user_not_found_ex import UserNotFoundException

def add_exception_handlers(app):

    @app.exception_handler(AttributeError)
    async def attr_exception_handler(request: Request, exc: AttributeError):
        return JSONResponse(
            status_code=422, 
            content={
                'status': 'error',
                'code': 'INTERNAL_SERVER_ERROR',
                'message': exc.obj
            },
        )

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=422, 
            content={
                'status': 'error',
                'code': 'APPLICATION_ERROR',
                'message': exc.message
            },
        )

    @app.exception_handler(UserNotFoundException)
    async def user_not_found_handler(request: Request, exc: UserNotFoundException):
        return JSONResponse(
            status_code=404,
            content={
                'status': 'error',
                'code': 'USER_NOT_FOUND',
                'message': exc.message
            },
        )
    
    @app.exception_handler(UserAlreadyExistsException)
    async def user_already_exists(request: Request, exc: UserAlreadyExistsException):
        return JSONResponse(
            status_code=400,
            content={
                'status': 'error',
                'code': 'USER_ALREADY_EXISTS',
                'message': exc.message
            },
        )
    
    @app.exception_handler(UserAlreadyExistsException)
    async def bad_request_exception(request: Request, exc: UserAlreadyExistsException):
        return JSONResponse(
            status_code=400,
            content={
                'status': 'error',
                'code': 'BAD_REQUEST',
                'message': exc.message
            },
        )