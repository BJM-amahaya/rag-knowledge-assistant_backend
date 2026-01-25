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

class DecompositionResult(BaseModel):
    subtasks:list[SubTask]=Field(
        description="分解されたサブタスクのリスト"
    )
    total_subtasks:int=Field(
        description="サブタスクの総数"
    )


def create_user_prompt(task: str, analysis: dict) -> str:
    complexity = analysis.get("complexity","中")
    if complexity == "高":
        split_range = "8~10個"
    elif complexity == "低":
        split_range = "3~5個"
    else:
        split_range = "5~7個"
    return f"""以下のタスクを分解してください。

【元のタスク】
{task}

【分析結果】
- カテゴリ: {analysis.get('category', '不明')}
- 目的: {analysis.get('purpose', '不明')}
- 緊急度: {analysis.get('urgency', '中')}
- 複雑さ: {complexity}
- 重要要素: {', '.join(analysis.get('key_requirements', []))}
- 制約: {', '.join(analysis.get('constraints', []))}

【指示】
- {split_range}のサブタスクに分解してください
- 各サブタスクは1〜2時間で完了できる大きさに
- 依存関係を明確に記載してください
- JSON形式のみで出力してください
"""

def parse_decomposition_result(llm_output:str)->DecompositionResult:
    start = llm_output.find("{")
    end = llm_output.rfind("}")+1

    if start == -1 or end ==0:
        raise ValueError("JSONが見つかりません。")
    json_str = llm_output[start:end]
    data = json.loads(json_str)
    return DecompositionResult(**data)

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
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=create_user_prompt(task,analysis))
        ]
    
        response = llm.invoke(messages)
        result = parse_decomposition_result(response.content)
        return {
            "subtasks":[st.model_dump()for st in result.subtasks]
        }

    except json.JSONDecodeError as e:
        return {"subtasks": None, "error": f"JSONパースエラー: {e}"}
    except Exception as e:
        return {"subtasks": None, "error": f"分解エラー: {e}"}