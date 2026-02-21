from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings


def get_embeddings(task_type: str = "RETRIEVAL_DOCUMENT") -> GoogleGenerativeAIEmbeddings:
    """Google Generative AI Embeddingsインスタンスを返す。"""
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GOOGLE_API_KEY,
        task_type=task_type,
    )
