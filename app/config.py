from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    GOOGLE_API_KEY:str
    debug: bool = False

    # RAGパラメータ
    chunk_size: int = 300
    chunk_overlap: int = 50
    search_k: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
settings = Settings()    