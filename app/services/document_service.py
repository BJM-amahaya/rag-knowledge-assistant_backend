import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.core.chunker import split_documents
from app.core.document_loader import load_document
from app.core.vector_store import add_documents, delete_by_doc_id
from app.models.document import Document

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
METADATA_FILE = UPLOAD_DIR / "metadata.json"


def _load_metadata() -> dict:
    """metadata.json を読み込む。なければ空辞書を返す。"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_metadata(metadata: dict) -> None:
    """metadata.json を保存する。"""
    UPLOAD_DIR.mkdir(exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


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

    # 3. UUID生成（チャンクへの埋め込みとメタデータ保存に使う）
    doc_id = str(uuid.uuid4())

    try:
        # 4. テキスト抽出
        documents = load_document(str(file_path))
        if not documents:
            raise HTTPException(status_code=400, detail="PDFからテキストを抽出できませんでした")

        # 5. チャンク分割
        chunks = split_documents(
            documents,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        # 6. 各チャンクに doc_id を埋め込む
        for chunk in chunks:
            chunk.metadata["doc_id"] = doc_id

        # 7. ベクトルストアに登録
        add_documents(chunks)
        logger.info("ドキュメント登録完了: %s (%d チャンク)", file.filename, len(chunks))

        # 8. metadata.json に保存
        uploaded_at = datetime.now().strftime("%Y-%m-%d")
        metadata = _load_metadata()
        metadata[doc_id] = {
            "name": file.filename,
            "uploadedAt": uploaded_at,
            "filePath": str(file_path),
        }
        _save_metadata(metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("ドキュメント処理中にエラー: %s", e)
        raise HTTPException(status_code=400, detail=f"ドキュメントの処理に失敗しました: {e}")

    # 9. ドキュメント情報を返す
    return Document(
        id=doc_id,
        name=file.filename,
        uploadedAt=uploaded_at,
    )


def get_all_documents() -> list[Document]:
    """登録済み全ドキュメントを返す。"""
    metadata = _load_metadata()
    return [
        Document(id=doc_id, name=info["name"], uploadedAt=info["uploadedAt"])
        for doc_id, info in metadata.items()
    ]


def delete_document(doc_id: str) -> Document:
    """ドキュメントを削除する（metadata + Chroma + PDFファイル）。"""
    metadata = _load_metadata()

    if doc_id not in metadata:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

    doc_info = metadata[doc_id]

    # 1. Chroma からチャンク削除
    delete_by_doc_id(doc_id)

    # 2. PDFファイル削除
    file_path = Path(doc_info["filePath"])
    if file_path.exists():
        file_path.unlink()

    # 3. metadata.json から削除
    deleted = metadata.pop(doc_id)
    _save_metadata(metadata)

    logger.info("ドキュメント削除完了: %s (id=%s)", deleted["name"], doc_id)

    return Document(id=doc_id, name=deleted["name"], uploadedAt=deleted["uploadedAt"])
