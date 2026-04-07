import logging

from app.models.chat import ChatRequest, ChatResponse, Source
from app.core.rag_pipeline import generate_answer

logger = logging.getLogger(__name__)


def process_chat(request: ChatRequest) -> ChatResponse:
    try:
        result = generate_answer(request.message)
    except Exception as e:
        logger.error("RAGパイプラインでエラーが発生: %s", e)
        return ChatResponse(
            message="エラーが発生しました。ドキュメントをアップロードしてから質問してください。",
            sources=[],
        )

    sources = [
        Source(
            documentName=s.get("source", "不明"),
            page=s.get("page", 0),
        )
        for s in result.get("sources", [])
    ]

    return ChatResponse(
        message=result["answer"],
        sources=sources,
    )
