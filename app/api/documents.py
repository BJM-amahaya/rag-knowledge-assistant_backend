from datetime import datetime

from fastapi import APIRouter, File, UploadFile

from app.models.document import Document
from app.services.document_service import process_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[Document])
def get_documents():
    # TODO: 登録済みドキュメント一覧を返す実装に置き換え
    return [
        {"id": "1", "name": "プロジェクト計画書.pdf", "uploadedAt": datetime.now().strftime("%Y-%m-%d")},
        {"id": "2", "name": "技術仕様書.docx", "uploadedAt": datetime.now().strftime("%Y-%m-%d")},
    ]


@router.post("", response_model=Document)
def upload_document(file: UploadFile = File(...)):
    return process_upload(file)