from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class TaskResponse(BaseModel):
    id:str=Field(description="タスクの一意なID")
    original_task:str=Field(description="タスクの内容")
    status:str=Field(description="処理ステータス",examples=["completed"])

    analysis: Optional[dict[str,Any]] = Field(default=None, description="タスク分析結果")
    subtasks: Optional[list[dict[str,Any]]] = Field(default=None, description="サブタスク一覧")
    estimates: Optional[list[dict[str,Any]]] = Field(default=None, description="時間見積もり")
    total_minutes: Optional[int] = Field(default=None, description="合計時間（分）")
    priorities: Optional[list[dict[str,Any]]] = Field(default=None, description="優先度一覧")
    schedule: Optional[list[dict[str,Any]]] = Field(default=None, description="スケジュール")
    total_days: Optional[int] = Field(default=None, description="合計日数")
    warnings: Optional[list[str]] = Field(default=None, description="警告事項")

    created_at:datetime = Field(
        default_factory=datetime.now,
        description="作成日時"
    )