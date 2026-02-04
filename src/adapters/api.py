from contextlib import asynccontextmanager
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.application.memory.long_term_memory_int import create_search_database_tool, create_web_search_tool
from src.config import settings

from src.adapters.dependencies import get_compiled_graph
from src.application.workflow.generate_response import Agent
from src.infrastructure.database.client import MongoClientWrapper
from src.infrastructure.database.embeddings import get_hugging_face_embedding
from src.infrastructure.database.retrievers import get_mongo_hybrid_search_retriever
from src.infrastructure.database.splitters import get_splitter
from src.infrastructure.database.vector_stores import get_mongo_vector_store
from src.infrastructure.llm.providers import get_groq_chat_model
from src.infrastructure.tools.long_term_memory_tool import LongTermMemoryTool
from src.infrastructure.tools.metasearch_engine import SearXNGWebSearchEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """handles startup and shutdown events for the API."""
    db_client = MongoClientWrapper(model=BaseModel, database_name=settings.MONGO_DB_NAME)

    async with db_client:
    
        checkpointer = db_client.get_checkpointer()

        embedding = get_hugging_face_embedding(model_id=settings.RAG_TEXT_EMBEDDING_MODEL_ID, device=settings.RAG_DEVICE)
        vector_store = get_mongo_vector_store(embedding=embedding)
        splitter = get_splitter(chunk_size=settings.RAG_CHUNK_SIZE)
        retriever = get_mongo_hybrid_search_retriever(vector_store=vector_store)
        web_search_engine = SearXNGWebSearchEngine()

        rag_tool = LongTermMemoryTool(vector_store=vector_store, splitter=splitter, retriever=retriever, web_search_engine=web_search_engine)
        tools = [create_search_database_tool(retriever=rag_tool), create_web_search_tool(retriever=rag_tool)]

        llm = get_groq_chat_model(temperature=0.7, model_name=settings.GROQ_LLM_MODEL)
        poor_llm = get_groq_chat_model(temperature=0.7, model_name=settings.GROQ_SUMMARY_LLM_MODEL)

        graph = get_compiled_graph(checkpointer=checkpointer, tools=tools, llm=llm, poor_llm=poor_llm)
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

