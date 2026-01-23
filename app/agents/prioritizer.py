from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel,Field
from app.config import settings
from typing import Any
import json

SYSTEM_PROMPT = """
あなたは、タスク優先度決定の専門家です。
サブタスクのリストを分析して、アイゼンハワーマトリクスに基づいて優先度を割り当てます。

## アイゼンハワーマトリクス

優先度は「緊急度」と「重要度」の2軸で判断します：

  | 優先度 | 緊急度 | 重要度 | 説明 |                                                                                                                                                
  |--------|--------|--------|------|                                                                                                                                                
  | 1 | 高 | 高 | 最優先：すぐに着手すべき |                                                                                                                                         
  | 2 | 低 | 高 | 高優先：計画的に実行 |                                                                                                                                             
  | 3 | 高 | 低 | 中優先：可能なら早めに |                                                                                                                                           
  | 4 | 低 | 低 | 低優先：後回しでOK |                                                                                                                                               
  | 5 | - | - | 保留：今回は不要 | 

## 判断基準

### 緊急度の判断
- 高 : 他のタスクがブロックされる、締め切りが近い(1~2日以内)
- 低 : 時間的余裕がある、他タスクへの影響が少ない

### 重要度の判断
- 高 : プロジェクト完了の必須要件、基盤となる機能
- 低 : あれば便利だが必須ではない、補助的な機能

## 出力形式

必ず以下のJSON形式のみで出力して下さい：

  {                                                                                                                                                                                  
    "priorities": [                                                                                                                                                                  
      {                                                                                                                                                                              
        "subtask_id": "サブタスクのID",                                                                                                                                              
        "priority": 1,                                                                                                                                                               
        "urgency": "高",                                                                                                                                                             
        "importance": "高",                                                                                                                                                          
        "reasoning": "優先度を決めた理由"                                                                                                                                            
      }                                                                                                                                                                              
    ]                                                                                                                                                                                
  } 
"""

class PriorityAssignment(BaseModel):
    subtask_id: str=Field(
        description="サブタスク固有ID（例: subtask_1）"
    )
    priority: int=Field(
        description="優先度(1-5)"
    )
    urgency: str=Field(
        description="緊急度(高/低)"
    )
    importance: str=Field(
        description="緊急度(高/低)"
    )
    reasoning: str=Field(
        description="判断理由"
    )


class PrioritizerResult(BaseModel):
    priorities:list[PriorityAssignment]=Field(
        description="分解されたサブタスク"
    )

def create_user_prompt(task,subtasks,estimates) -> str:
    estimates_map = {e["subtask_id"]: e for e in estimates} 
    subtask_text=""
    for st in subtasks:
        est = estimates_map.get(st["id"])
        minutes = est["estimated_minutes"] if est else "不明"
        deps = st.get("dependencies", []) 
        subtask_text += f"- {st['id']}: {st['title']}\n"
        subtask_text += f"  - 見積もり: {minutes}分\n"                                                                                                        
        subtask_text += f"  - 依存: {deps}\n"
    return f""" 以下のサブタスクの優先度を決定してください。
## 元のタスク
{task}

## サブタスク一覧
{subtask_text}

【指示】
- subtasks + estimates の両方の情報を含める                                                                                                              
- 依存関係や見積もり時間も判断材料として提示   
- JSON形式のみで出力してください
"""

def parse_prioritizer_result(llm_output:str)->PrioritizerResult:
    start = llm_output.find("{")
    end = llm_output.rfind("}")+1

    if start == -1 or end ==0:
        raise ValueError("JSONが見つかりません。")
    json_str = llm_output[start:end]
    data = json.loads(json_str)
    return PrioritizerResult(**data)

def prioritize(state: dict) -> dict[str,Any]:
    try:
        task=state["original_task"]
        sub_tasks=state.get("subtasks",[])
        estimates = state.get("estimates", [])

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-04-17",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=create_user_prompt(task,sub_tasks,estimates))
        ]

        response = llm.invoke(messages)
        result = parse_prioritizer_result(response.content)
        return {
            "priorities":[st.model_dump()for st in result.priorities],
        }
    except json.JSONDecodeError as e:
        return {"priorities": None, "error": f"JSONパースエラー: {e}"}
    except Exception as e:
        return {"priorities": None, "error": f"見積もりエラー: {e}"}