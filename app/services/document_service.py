import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.chunker import split_documents
from app.core.document_loader import load_document
from app.core.vector_store import add_documents
from app.models.document import Document

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")


def process_upload(file: UploadFile) -> Document:
    """PDFをアップロードし、ベクトルストアに登録する。"""

    # 1. PDFかどうかチェック
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDFファイルのみアップロード可能です")

    # 2. uploads/ ディレクトリにファイル保存
    UPLOAD_DIR.mkdir(exist_ok=True)
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 3. テキスト抽出
        documents = load_document(str(file_path))
        if not documents:
            raise HTTPException(status_code=400, detail="PDFからテキストを抽出できませんでした")

        # 4. チャンク分割
        chunks = split_documents(documents)

        # 5. ベクトルストアに登録
        add_documents(chunks)
        logger.info("ドキュメント登録完了: %s (%d チャンク)", file.filename, len(chunks))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ドキュメント処理中にエラー: %s", e)
        raise HTTPException(status_code=400, detail=f"ドキュメントの処理に失敗しました: {e}")

    # 6. ドキュメント情報を返す
    return Document(
        id=str(uuid.uuid4()),
        name=file.filename,
        uploadedAt=datetime.now().strftime("%Y-%m-%d"),
    )
