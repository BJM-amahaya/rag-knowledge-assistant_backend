import logging
import time

from google.api_core.exceptions import ResourceExhausted
from langchain_core.documents import Document
from langchain_chroma import Chroma
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
)

from app.config import settings
from app.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)

PERSIST_DIR = "./chroma_data"

# --- リトライ設定 ---
BATCH_SIZE = 20          # 1バッチあたりのチャンク数
MAX_RETRIES = 5          # 最大リトライ回数
WAIT_MIN = 4             # 最小待機秒数
WAIT_MAX = 120           # 最大待機秒数
BATCH_DELAY = 2          # バッチ間の待機秒数（レート制限回避用）


def _is_rate_limit_error(exc: BaseException) -> bool:
    """429 (Rate Limit) エラーかどうかを判定する。"""
    if isinstance(exc, ResourceExhausted):
        return True
    # LangChainが例外をラップしている場合、メッセージで判定
    return "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc)


def get_vector_store(task_type: str = "RETRIEVAL_DOCUMENT") -> Chroma:
    """Chromaベクトルストアのインスタンスを取得する。"""
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=get_embeddings(task_type=task_type),
    )


@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=WAIT_MIN, max=WAIT_MAX),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _add_batch(store: Chroma, batch: list[Document], batch_num: int, total: int) -> None:
    """1バッチ分のドキュメントをベクトルストアに追加する（リトライ付き）。"""
    logger.info(f"バッチ {batch_num}/{total} を処理中（{len(batch)} チャンク）")
    store.add_documents(batch)


def add_documents(docs: list[Document]) -> None:
    """ドキュメントをベクトルストアに追加する（バッチ分割 + リトライ）。"""
    store = get_vector_store()

    # バッチに分割して処理
    batches = [docs[i:i + BATCH_SIZE] for i in range(0, len(docs), BATCH_SIZE)]
    total = len(batches)

    logger.info(f"合計 {len(docs)} チャンクを {total} バッチに分割して処理します")

    for idx, batch in enumerate(batches, start=1):
        _add_batch(store, batch, idx, total)
        # 最後のバッチ以外は待機してレート制限を回避
        if idx < total:
            logger.info(f"レート制限回避のため {BATCH_DELAY} 秒待機中...")
            time.sleep(BATCH_DELAY)

    logger.info(f"全 {total} バッチの処理が完了しました")


def delete_by_doc_id(doc_id: str) -> None:
    """指定された doc_id に紐づくチャンクをベクトルストアから削除する。"""
    store = get_vector_store()
    results = store.get(where={"doc_id": doc_id})
    if results["ids"]:
        store.delete(ids=results["ids"])


def search(query: str, k: int = settings.search_k) -> list[Document]:
    """クエリに類似するドキュメントを検索する。"""
    store = get_vector_store(task_type="RETRIEVAL_QUERY")
    return store.similarity_search(query, k=k)
