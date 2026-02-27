from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status

from src.adapters.dependencies import get_thread_service
from src.adapters.utilities import decode_token
from src.application.threads.threads_service import ThreadService

router = APIRouter()

@router.get('/chat/history/{thread_id}')
async def get_chat_history(request: Request, thread_id: str):

    agent = request.app.state.agent
    
    try:
        state_snapshot = await agent.get_state(thread_id=thread_id)
    except Exception as e:
        print(f"err: {e}")
        return []

    if not state_snapshot:
        return []
        
    messages = state_snapshot.values.get("messages", [])
    
    formatted_history = []
    for msg in messages:

        if msg.type == "tool" or (msg.type == "ai" and not msg.content):
            continue

        role = "USER" if msg.type == "human" else "AI"
        formatted_history.append({
            "id": msg.id or str(uuid.uuid4()),
            "role": role,
            "content": msg.content
        })
        
    return formatted_history

@router.get('/chat/threads', status_code=status.HTTP_200_OK)
async def get_threads(my_user: Annotated[dict, Depends(decode_token)], service: ThreadService = Depends(get_thread_service)):
    print(my_user)
    try:
        threads = await service.get_threads_by_user_id(user_id=my_user['_id'])
            
        return { 'threads' : threads }

    except Exception as err:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
    
@router.delete('/chat/threads/{thread_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(thread_id: str, service: ThreadService = Depends(get_thread_service)):
    await service.delete_thread(thread_id)

    return { 'message': f'thread {thread_id} deleted successfully.' }