from contextlib import asynccontextmanager
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.application.workflow.generate_response import get_response

@asynccontextmanager
async def lifespan(app: FastAPI):
    """handles startup and shutdown events for the API."""
    # startup code (if any) goes here
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket('/chat')
async def chat(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            if 'message' not in data:
                await websocket.send_json(
                    {
                        "error": "invalid message format. required fields: 'message'"
                    }
                )
                continue

            if 'thread_id' not in data:
                thread_id = str(uuid.uuid4())
            else:
                thread_id = data['thread_id']

            try:
                response_stream = get_response(messages=data['message'], thread_id=thread_id)

                await websocket.send_json({ 'streaming': True })

                full_response = ''
                async for chunk in response_stream:
                    full_response += chunk
                    await websocket.send_json({ 'chunk': chunk })

                await websocket.send_json(
                    { 'response': full_response, 'streaming': False, 'thread_id': thread_id }
                )

            except Exception as err:
                await websocket.send_json({ 'error': str(err) })

    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

