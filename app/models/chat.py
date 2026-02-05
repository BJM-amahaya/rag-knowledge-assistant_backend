from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(
        description="ユーザーのメッセージ",
        min_length=1,
        max_length=1000,
        examples=["RAGって何ですか？"]
    )

class Source(BaseModel):
    documentName: str = Field(description="参照元ドキュメント名")
    page: int = Field(description="参照ページ番号")

class ChatResponse(BaseModel):
    message: str = Field(description="AIの応答メッセージ")
    sources: list[Source] = Field(default=[], description="参照元ソース一覧")
