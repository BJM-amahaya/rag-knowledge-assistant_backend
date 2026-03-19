from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # AWS設定
    AWS_REGION: str = "ap-northeast-1"
    BEDROCK_KB_ID: str = ""
    BEDROCK_DATA_SOURCE_ID: str = ""
    S3_DOCUMENTS_BUCKET: str = ""
    BEDROCK_MODEL_ID: str = "anthropic.claude-sonnet-4-20250514"

    debug: bool = False

    # RAGパラメータ
    search_k: int = 5
    rerank_initial_results: int = 100  # Re-ranking前の初期取得件数

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
