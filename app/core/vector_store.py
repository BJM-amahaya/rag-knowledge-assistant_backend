import logging

import boto3
from langchain_core.documents import Document

from app.config import settings

logger = logging.getLogger(__name__)


def _get_client():
    """Bedrock Agent Runtime クライアントを取得する。"""
    return boto3.client(
        "bedrock-agent-runtime",
        region_name=settings.AWS_REGION,
    )


def search(query: str, k: int = settings.search_k) -> list[Document]:
    """Bedrock Knowledge Base からクエリに関連するドキュメントを検索する。"""
    client = _get_client()

    response = client.retrieve(
        knowledgeBaseId=settings.BEDROCK_KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": settings.rerank_initial_results,
                "overrideSearchType": "HYBRID",
            },
            "rerankingConfiguration": {
                "type": "BEDROCK_RERANKER",
                "bedrockRerankingConfiguration": {
                    "modelConfiguration": {
                        "modelArn": (
                            f"arn:aws:bedrock:{settings.AWS_REGION}"
                            "::foundation-model/cohere.rerank-v3-5:0"
                        ),
                    },
                    "numberOfRerankedResults": k,
                },
            },
        },
    )

    documents = []
    for result in response.get("retrievalResults", []):
        content = result.get("content", {}).get("text", "")
        metadata = {}

        # S3のロケーション情報からソース名を取得
        location = result.get("location", {})
        if location.get("type") == "S3":
            s3_uri = location.get("s3Location", {}).get("uri", "")
            # s3://bucket/key からファイル名を抽出
            metadata["source"] = s3_uri.split("/")[-1] if s3_uri else "不明"

        # スコア情報
        metadata["score"] = result.get("score", 0.0)

        documents.append(
            Document(page_content=content, metadata=metadata)
        )

    logger.info("Bedrock KB検索完了: %d 件の結果", len(documents))
    return documents
