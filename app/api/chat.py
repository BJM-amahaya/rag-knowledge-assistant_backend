from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import process_chat

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def send_chat(request: ChatRequest):
    try:
        response = process_chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")
