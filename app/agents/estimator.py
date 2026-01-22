from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel,Field
from app.config import settings
from typing import Any
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

def create_user_prompt(task:str,subtasks:list[dict]) -> str:
    subtask_text = ""
    for st in subtasks:
        subtask_text += f"- {st['id']}:{st['title']}\n"
    return f""" 以下のサブタスクの所要時間を見積もってください。
## 元のタスク
{task}

## サブタスク一覧
{subtask_text}

【指示】
- 各サブタスクの所要時間を「分」単位で見積もってください
- confidence（確信度）を設定してください
- reasoning（根拠）を必ず記載してください
- JSON形式のみで出力してください
"""

def parse_estimator_result(llm_output:str)->EstimatorResult:
    start = llm_output.find("{")
    end = llm_output.rfind("}")+1

    if start == -1 or end ==0:
        raise ValueError("JSONが見つかりません。")
    json_str = llm_output[start:end]
    data = json.loads(json_str)
    return EstimatorResult(**data)

def estimate(state: dict) -> dict[str,Any]:
    try:
        task=state["original_task"]
        sub_tasks=state.get("subtasks",[])

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-04-17",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=create_user_prompt(task,sub_tasks))
        ]

        response = llm.invoke(messages)
        result = parse_estimator_result(response.content)
        return {
            "estimates":[st.model_dump()for st in result.estimates],
            "total_minutes": result.total_minutes 
        }
    except json.JSONDecodeError as e:
        return {"estimates": None, "error": f"JSONパースエラー: {e}"}
    except Exception as e:
        return {"estimates": None, "error": f"見積もりエラー: {e}"}