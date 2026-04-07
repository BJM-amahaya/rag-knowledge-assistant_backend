from fastapi import APIRouter, File, UploadFile

from app.models.document import Document
from app.services.document_service import (
    delete_document,
    get_all_documents,
    process_upload,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[Document])
def get_documents():
    return get_all_documents()


@router.post("", response_model=Document)
def upload_document(file: UploadFile = File(...)):
    return process_upload(file)


@router.delete("/{doc_id}", response_model=Document)
def remove_document(doc_id: str):
    return delete_document(doc_id)
