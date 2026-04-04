import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import boto3
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.models.document import Document

logger = logging.getLogger(__name__)

METADATA_DIR = Path("uploads")
METADATA_FILE = METADATA_DIR / "metadata.json"


def _get_s3_client():
    """S3クライアントを取得する。"""
    return boto3.client("s3", region_name=settings.AWS_REGION)


def _get_dynamodb_table():
    """DynamoDB テーブルオブジェクトを返す。未設定なら None"""
    table_name = settings.DYNAMODB_DOCUMENTS_TABLE
    if not table_name:
        return None
    dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    return dynamodb.Table(table_name)


def _get_bedrock_agent_client():
    """Bedrock Agentクライアントを取得する。"""
    return boto3.client("bedrock-agent", region_name=settings.AWS_REGION)


def _load_metadata() -> dict:
    """metadata.json を読み込む。なければ空辞書を返す。"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_metadata(metadata: dict) -> None:
    """metadata.json を保存する。"""
    METADATA_DIR.mkdir(exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def _sync_knowledge_base() -> None:
    """Bedrock Knowledge Base の同期（Ingestion Job）をトリガーする。"""
    try:
        client = _get_bedrock_agent_client()
        response = client.start_ingestion_job(
            knowledgeBaseId=settings.BEDROCK_KB_ID,
            dataSourceId=settings.BEDROCK_DATA_SOURCE_ID,
        )
        job_id = response["ingestionJob"]["ingestionJobId"]
        logger.info("KB同期ジョブ開始: %s", job_id)
    except Exception as e:
        logger.error("KB同期トリガーに失敗: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge Base の同期に失敗しました: {e}",
        )


def process_upload(file: UploadFile) -> Document:
    """PDFをS3にアップロードし、Bedrock KBの同期をトリガーする。"""

    # 1. PDFかどうかチェック
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="PDFファイルのみアップロード可能です"
        )

    # 2. UUID生成
    doc_id = str(uuid.uuid4())

    # 3. S3にアップロード
    s3_key = f"documents/{doc_id}/{file.filename}"
    try:
        s3 = _get_s3_client()
        s3.upload_fileobj(
            file.file,
            settings.S3_DOCUMENTS_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "application/pdf"},
        )
        logger.info("S3アップロード完了: s3://%s/%s", settings.S3_DOCUMENTS_BUCKET, s3_key)
    except Exception as e:
        logger.error("S3アップロードエラー: %s", e)
        raise HTTPException(
            status_code=500, detail=f"S3へのアップロードに失敗しました: {e}"
        )

    # 4. Bedrock KB 同期トリガー
    _sync_knowledge_base()

    # 5. メタデータを保存
    uploaded_at = datetime.now().strftime("%Y-%m-%d")
    table = _get_dynamodb_table()
    if table:
        # DynamoDB に保存
        table.put_item(Item={
            "docId": doc_id,
            "name": file.filename,
            "uploadedAt": uploaded_at,
            "s3Key": s3_key,
        })
    else:
        # フォールバック: ファイルに保存（ローカル開発用）
        metadata = _load_metadata()
        metadata[doc_id] = {
            "name": file.filename,
            "uploadedAt": uploaded_at,
            "s3Key": s3_key,
        }
        _save_metadata(metadata)

    logger.info("ドキュメント登録完了: %s (id=%s)", file.filename, doc_id)

    return Document(
        id=doc_id,
        name=file.filename,
        uploadedAt=uploaded_at,
    )


def get_all_documents() -> list[Document]:
    """登録済み全ドキュメントを返す。"""
    table = _get_dynamodb_table()
    if table:
        # DynamoDB からすべて取得
        response = table.scan()
        items = response.get("Items", [])
        return [
            Document(id=item["docId"], name=item["name"], uploadedAt=item["uploadedAt"])
            for item in items
        ]
    else:
        # フォールバック: ファイルから読み込み
        metadata = _load_metadata()
        return [
            Document(id=doc_id, name=info["name"], uploadedAt=info["uploadedAt"])
            for doc_id, info in metadata.items()
        ]


def delete_document(doc_id: str) -> Document:
    """ドキュメントを削除する（metadata + S3）。"""
    table = _get_dynamodb_table()
    if table:
        # DynamoDB から取得して削除
        response = table.get_item(Key={"docId": doc_id})
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

        # 1. S3 からファイル削除
        s3_key = item.get("s3Key")
        if s3_key:
            try:
                s3 = _get_s3_client()
                s3.delete_object(
                    Bucket=settings.S3_DOCUMENTS_BUCKET,
                    Key=s3_key,
                )
                logger.info("S3ファイル削除完了: %s", s3_key)
            except Exception as e:
                logger.warning("S3ファイル削除に失敗: %s", e)

        # 2. KB 再同期（削除を反映）
        try:
            _sync_knowledge_base()
        except Exception as e:
            logger.warning("削除後のKB同期に失敗: %s", e)

        # 3. DynamoDB から削除
        table.delete_item(Key={"docId": doc_id})
        logger.info("ドキュメント削除完了: %s (id=%s)", item["name"], doc_id)
        return Document(id=doc_id, name=item["name"], uploadedAt=item["uploadedAt"])
    else:
        # フォールバック: ファイルから削除
        metadata = _load_metadata()

        if doc_id not in metadata:
            raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

        doc_info = metadata[doc_id]

        # 1. S3 からファイル削除
        s3_key = doc_info.get("s3Key")
        if s3_key:
            try:
                s3 = _get_s3_client()
                s3.delete_object(
                    Bucket=settings.S3_DOCUMENTS_BUCKET,
                    Key=s3_key,
                )
                logger.info("S3ファイル削除完了: %s", s3_key)
            except Exception as e:
                logger.warning("S3ファイル削除に失敗: %s", e)

        # 2. KB 再同期（削除を反映）
        try:
            _sync_knowledge_base()
        except Exception as e:
            logger.warning("削除後のKB同期に失敗: %s", e)

        # 3. metadata.json から削除
        deleted = metadata.pop(doc_id)
        _save_metadata(metadata)

        logger.info("ドキュメント削除完了: %s (id=%s)", deleted["name"], doc_id)

        return Document(id=doc_id, name=deleted["name"], uploadedAt=deleted["uploadedAt"])
