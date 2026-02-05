from langchain_core.documents import Document
from langchain_chroma import Chroma
from app.core.embeddings import get_embeddings

PERSIST_DIR = "./chroma_data"


def get_vector_store() -> Chroma:
    """Chromaベクトルストアのインスタンスを取得する。"""
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=get_embeddings(),
    )


def add_documents(docs: list[Document]) -> None:
    """ドキュメントをベクトルストアに追加する。"""
    store = get_vector_store()
    store.add_documents(docs)


def search(query: str, k: int = 3) -> list[Document]:
    """クエリに類似するドキュメントを検索する。"""
    store = get_vector_store()
    return store.similarity_search(query, k=k)
