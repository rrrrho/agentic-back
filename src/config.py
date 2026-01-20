
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file='.env', extra='ignore', env_file_encoding='utf8'
    )

    # --- GROQ Configuration ---
    GROQ_API_KEY: str
    GROQ_LLM_MODEL: str = 'llama-3.3-70b-versatile'
    GROQ_SUMMARY_LLM_MODEL: str = 'llama-3.1-8b-instant'

    # --- MongoDB Configuration ---
    MONGO_URI: str
    MONGO_DB_NAME: str = 'agentic-back-db'
    MONGO_STATE_CHECKPOINT_COLLECTION: str = 'agentic-back-checkpoints'
    MONGO_STATE_WRITES_COLLECTION: str = 'agentic-back-writes'
    MONGO_LONG_TERM_MEMORY_COLLECTION: str = 'agentic-back-long_term_memory'

    # --- Summary Configuration ---
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 5
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 30

    RAG_TEXT_EMBEDDING_MODEL_ID: str = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_TEXT_EMBEDDING_MODEL_DIM: int = 384
    RAG_TOP_K: int = 3
    RAG_DEVICE: str = "cpu"
    RAG_CHUNK_SIZE: int = 256
    RAG_SCORE_THRESHOLD: float = 0.7


settings = Settings()