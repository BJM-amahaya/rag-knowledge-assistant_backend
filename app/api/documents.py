from fastapi import APIRouter, UploadFile, File
from app.models.document import Document
import uuid
from datetime import datetime

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("", response_model=list[Document])
def get_documents():
    # リアル感出すためにゆくゆくは、本物のデータを入れたい。
    return [
        {"id": "1", "name": "プロジェクト計画書.pdf", "uploadedAt": datetime.now().strftime("%Y-%m-%d")},
        {"id": "2", "name": "技術仕様書.docx", "uploadedAt": datetime.now().strftime("%Y-%m-%d")},
    ]

@router.post("", response_model=Document)
def upload_document(file: UploadFile = File(...)):
    return Document(
        id=str(uuid.uuid4()),
        name=file.filename,
        uploadedAt=datetime.now().strftime("%Y-%m-%d")
    )