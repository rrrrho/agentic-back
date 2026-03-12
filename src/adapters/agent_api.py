import asyncio
import json
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.adapters.dependencies import get_thread_service
from src.adapters.utilities import decode_token
from src.application.threads.threads_service import ThreadService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    model_name: str

class RegenerateRequest(BaseModel):
    thread_id: str

@router.post('/chat')
async def send_message(data: ChatRequest, request: Request, my_user: Annotated[dict, Depends(decode_token)], service: ThreadService = Depends(get_thread_service)):

    agent = request.app.state.agent
    user_id = my_user['_id']

    title = ''
    if not data.thread_id:
        message = [data.message]

        title = await asyncio.create_task(
            agent.get_chat_title(
            messages=message
        ))

        thread_id = await service.create_thread(user_id, title)
            
    else:
        thread_id = data.thread_id
        state = await agent.get_state(thread_id)
        messages = state.values.get('messages', [])

        title = await asyncio.create_task(
            agent.get_chat_title(
            messages=messages
        ))

        if title:
            await service.update_thread_title(thread_id, title)
            
    response_stream = agent.get_response(messages=data.message, thread_id=thread_id, model_name=data.model_name)

    async def token_generator():
        yield f"data: {json.dumps({'type': 'metadata', 'thread_id': thread_id, 'title': title})}\n\n"
        async for chunk in response_stream:
            yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")

@router.post('/chat/regenerate')
async def send_message(data: RegenerateRequest, request: Request):

    thread_id = data.thread_id
    agent = request.app.state.agent
    
    response_stream = agent.regenerate_response(thread_id=thread_id)

    async def token_generator():
        async for chunk in response_stream:
            yield f"data: {chunk}\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")

@router.post('/chat/image')
async def send_image_message(data: ChatRequest, request: Request):

    thread_id = data.thread_id
    message = data.message
    agent = request.app.state.agent
            
    response = await agent.generate_image(message=message, thread_id=thread_id)

    return { 'message': response }
    