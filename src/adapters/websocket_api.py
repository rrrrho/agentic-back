import asyncio
from http.cookies import SimpleCookie
from jose import JWTError, jwt
from src.config import settings
from src.adapters.main import sio, fastapi_app

@sio.event
async def connect(sid, environ):
    cookies_str = environ.get('HTTP_COOKIE', '')
    cookie = SimpleCookie()
    cookie.load(cookies_str)

    access_token = cookie.get('access_token')

    if not access_token:
        raise ConnectionRefusedError('authentication required')

    try:
        payload = jwt.decode(access_token.value, settings.AUTH_JWT_SECRET, algorithms=[settings.AUTH_JWT_ALGORITHM])
        user_id = payload.get('_id')
        
        if not user_id:
            raise ConnectionRefusedError('invalid token payload')
            
        # save user_id in socket session
        await sio.save_session(sid, {'user_id': user_id})
        print(f'connected and authenticated client: {sid} - {user_id}')
        
    except JWTError:
        raise ConnectionRefusedError('invalid or expired token')

    print(f"connected client: {sid}")

@sio.on('chat')
async def chat(sid, data):
    agent = fastapi_app.state.agent
    service = fastapi_app.state.thread_service

    session = await sio.get_session(sid)
    user_id = session.get('user_id')

    try:
        if 'message' not in data:
            await sio.emit('error',
                {
                    "error": "invalid message format. required fields: 'message'"
                },
                to=sid
            )
            return
        
        title = ''
        if 'thread_id' not in data:
            message = [data['message']]

            title = await asyncio.create_task(
                agent.get_chat_title(
                messages=message
            ))

            thread_id = await service.create_thread(user_id, title)
            
        else:
            thread_id = data['thread_id']
            state = await agent.get_state(thread_id)
            messages = state.values.get('messages', [])

            title = await asyncio.create_task(
                agent.get_chat_title(
                messages=messages
            ))

            if title:
                await service.update_thread_title(thread_id, title)
            

        try:
            response_stream = agent.get_response(messages=data['message'], thread_id=thread_id)

            await sio.emit('status', { 'streaming': True }, to=sid)

            full_response = ''
            async for chunk in response_stream:
                full_response += chunk
                await sio.emit('chunk', { 'text': chunk }, to=sid)

            if title:
                await sio.emit('response', 
                    { 'response': full_response, 'streaming': False, 'thread_id': thread_id, 'title': title }, 
                    to=sid
                )
            else:
                await sio.emit('response', 
                    { 'response': full_response, 'streaming': False }, 
                    to=sid
                )

        except Exception as err:
            await sio.emit('error', { 'error': str(err) }, to=sid)

    except Exception as err:
        print(err)

@sio.event
async def disconnect(sid):
    print(f"disconnected client: {sid}")
