from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Google Generative AI Embeddingsインスタンスを返す。"""
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.GOOGLE_API_KEY,
    )
