from app.models.chat import ChatRequest, ChatResponse, Source

def process_chat(request: ChatRequest) -> ChatResponse:
    # TODO: 将来的に agent_graph を使ったRAG処理に置き換え
    response = ChatResponse(
        message=f"「{request.message}」について、現在は固定応答です。RAG連携は今後実装予定です。",
        sources=[
            Source(documentName="sample.pdf", page=1)
        ]
    )
    return response
