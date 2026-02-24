import uuid
from fastapi import APIRouter, Request

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

@router.get('/chat/threads')
async def get_threads(request: Request):

    db = request.app.state.mongo_db
    metadata_collection = db.database['threads_metadata']

    try:
        cursor = metadata_collection.find({})
        threads_list = await cursor.to_list(length=100)
        
        result = []
        for t in threads_list:
            result.append({
                'id': t['thread_id'],
                'title': t.get('title', 'New conversation')
            })
            
        return {'threads': result}

    except Exception as e:
        return {'threads': [], 'error': str(e)}
    
@router.delete('/chat/threads/{thread_id}')
async def delete_thread(request: Request, thread_id: str):
    client = request.app.state.mongo_db
    await client.delete_thread(thread_id)

    return { 'status': 'success', 'message': f'thread {thread_id} deleted successfully.' }