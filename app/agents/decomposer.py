from pydantic import BaseModel, Field
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage,HumanMessage
from app.config import settings
import json

SYSTEM_PROMPT="""あなたはタスク分解の専門家です。
大きなタスクを、実行可能なサブタスクに分解します。

## 分解のルール
1. 1つのサブタスクは1〜2時間で完了できる大きさ
2. 細かすぎず、大きすぎない粒度
3. サブタスク間の依存関係を明確に

## 出力形式
必ず以下のJSON形式で出力してください。余計な文章は不要です。

{
    "subtasks": [
    {
    "id": "subtask_1",
    "title": "...",
    "description": "...",
    "dependencies": []
    }
    ],
    "total_subtasks": 数値
    """

class SubTask(BaseModel):
    id:str=Field(
        description="サブタスク固有ID（例: subtask_1）"
    )
    title:str=Field(
        description="サブタスク名（短く明確に）"
    )
    description:str=Field(
        description="詳細な説明"
    )
    dependencies:list[str]=Field(
        default_factory=list,
        description="依存するサブタスクIDのリスト"
    )

def create_user_prompt(task: str, analysis: dict) -> str:
    # ユーザープロンプト生成

def decompose(state:dict)->dict[str,Any]:
    try:
        task=state["original_task"]
        analysis=state.get("analysis",{})

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-04-17",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT)
            HumanMessage(content=create_user_prompt(task,analysis))
        ]


    except: