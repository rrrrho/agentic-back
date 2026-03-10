from langchain.chat_models import init_chat_model
from langchain_groq import ChatGroq
from src.config import settings

def get_groq_chat_model(temperature: float = 0.7, model_name: str = settings.GROQ_LLM_MODEL) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=model_name,
        temperature=temperature
    )

def get_open_router_chat_model(temperature: float = 0.7, model_name: str = settings.OPEN_ROUTER_MODEL, provider: str = 'openai'):
    return init_chat_model(
        model=model_name,
        model_provider=provider,
        base_url="https://openrouter.ai/api/v1",
        max_tokens=1500,
        api_key=settings.OPEN_ROUTER_API_KEY
    )