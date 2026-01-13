
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file='.env', extra='ignore', env_file_encoding='utf8'
    )

    # groq config
    GROQ_API_KEY: str
    GROQ_LLM_MODEL: str = 'llama-3.3-70b-versatile'

settings = Settings()