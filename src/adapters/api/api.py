from contextlib import asynccontextmanager
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.application.workflow.long_term_memory_int import create_retrieve_context_tool
from src.config import settings
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

from src.adapters.api.dependencies import get_compiled_graph
from src.application.workflow.generate_response import Agent
from src.infrastructure.database.client import MongoClientWrapper
from src.infrastructure.database.embeddings import get_hugging_face_embedding
from src.infrastructure.database.splitters import get_splitter
from src.infrastructure.database.vector_stores import get_mongo_vector_store
from src.infrastructure.tools.long_term_memory_tool import LongTermMemoryTool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """handles startup and shutdown events for the API."""
    db_client = MongoClientWrapper(model=BaseModel, database_name=settings.MONGO_DB_NAME)

    async with db_client:
    
        checkpointer = db_client.get_checkpointer()

        embedding = get_hugging_face_embedding(model_id=settings.RAG_TEXT_EMBEDDING_MODEL_ID, device=settings.RAG_DEVICE)
        vector_store = get_mongo_vector_store(embedding=embedding)
        splitter = get_splitter(chunk_size=settings.RAG_CHUNK_SIZE)

        rag_tool = LongTermMemoryTool(vector_store=vector_store, splitter=splitter)
        tools = [create_retrieve_context_tool(retriever=rag_tool)]


        graph = get_compiled_graph(checkpointer=checkpointer, tools=tools)
        app.state.agent = Agent(graph=graph)


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
                response_stream = websocket.app.state.agent.get_response(messages=data['message'], thread_id=thread_id)

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

