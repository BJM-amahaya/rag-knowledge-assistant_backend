from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel,Field
from app.config import settings
import json

SYSTEM_PROMPT = """あなたは時間見積もりの専門家です。
与えられたサブタスクリストを見て、各タスクの所要時間を予測します。

## 見積もりのルール
1.時間は、必ず「分」単位で出力して下さい
  - 例：1時間 → 60、1.5時間 → 90、2時間 → 120
2.各見積もりには確信度（confidence）を設定
  - 高 : 明確で単純なタスク、経験豊富な領域
  - 中 : 一般的なタスク、ある程度予測可能
  - 低 : 不確定要素が多い、調査が必要、複雑
3. reasoning には必ず見積もりの根拠を記載
4. 現実的な時間を設定（1サブタスク = 30分〜120分が目安）
5. total_minutes は全estimatesの合計値

## 出力形式
必ず以下のJSON形式で出力して下さい。他の文章は含めないで下さい。
{                                                                                                                                           
    "estimates": [                                                                                                                          
        {                                                                                                                                   
            "subtask_id": "subtask_1",                                                                                                      
            "estimated_minutes": 30,                                                                                                        
            "confidence": "高",                                                                                                             
            "reasoning": "単純な構成検討のため"                                                                                             
        }                                                                                                                                   
    ],                                                                                                                                      
    "total_minutes": 30                                                                                                                     
}
"""
class TimeEstimate(BaseModel):
    subtask_id: str=Field(
        description="サブタスク固有ID（例: subtask_1）"
    )
    estimated_minutes: int=Field(
        description="タスクの所要時間"
    )
    confidence: str=Field(
        description="確信度"
    )
    reasoning: str=Field(
        description="根拠"
    )


class EstimatorResult(BaseModel):
    estimates:list[TimeEstimate]=Field(
        description="分解されたサブタスク"
    )
    total_minutes:int=Field(
        description="サブタスクの総数"
    )

def create_user_prompt(task:str) -> str:
    return f"""

"""


def estimate(state: dict) -> dict[str,Any]:
    try:
        task=state["original_task"]
        analysis=state.get("analysis",{})
    except