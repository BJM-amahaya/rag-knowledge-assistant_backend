from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.core.vector_store import search

SYSTEM_PROMPT = """あなたはナレッジアシスタントです。
提供されたコンテキスト情報のみを使って、ユーザーの質問に正確に回答してください。

回答のルール:
- コンテキストから直接引用できる場合は、該当部分を引用してください
- 複数のコンテキストに関連情報がある場合は、統合して回答してください
- コンテキストに答えが含まれていない場合は、「提供された情報では回答できません」と伝えてください
- 回答の最後に、参考にしたドキュメント名とページ番号を記載してください"""


def generate_answer(query: str, k: int = settings.search_k) -> dict:
    """質問を受け取り、Bedrock KB検索→Bedrock Claudeで回答を生成する。"""
    # 1. Bedrock Knowledge Base で関連ドキュメントを取得
    docs = search(query, k=k)
    context = "\n\n".join(doc.page_content for doc in docs)

    # 2. Bedrock Claude で回答生成
    llm = ChatBedrock(
        model_id=settings.BEDROCK_MODEL_ID,
        region_name=settings.AWS_REGION,
        model_kwargs={
            "max_tokens": 2000,
            "temperature": 0.0,
        },
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"## コンテキスト\n{context}\n\n## 質問\n{query}"
        ),
    ]

    response = llm.invoke(messages)

    return {
        "answer": response.content,
        "sources": [doc.metadata for doc in docs],
    }
