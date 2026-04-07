from pydantic import BaseModel, Field

class Document(BaseModel):
    id: str = Field(description="ドキュメントの一意なID")
    name: str = Field(description="ドキュメント名")
    uploadedAt: str = Field(description="アップロード日時")
