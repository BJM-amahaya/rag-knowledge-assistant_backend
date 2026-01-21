from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel,Field
from enum import Enum
from typing import TypedDict, Optional, Any
from app.config import settings
import json

SYSTEM_PROMPT = """あなたはタスク分析の専門家です。
    ユーザーが入力したタスクを分析し、以下の項目を評価してください。

    ## 分析項目
    1. category: タスクの種類（仕事、勉強、家事、趣味、健康、その他）
    2. purpose: タスクの目的・最終ゴール
    3. urgency: 緊急度（高/中/低）
    4. complexity: 複雑さ（高/中/低）
    5. key_requirements: 達成に必要な要素のリスト
    6. constraints: 制約条件のリスト（期限、予算など）

    ## 出力形式
    必ず以下のJSON形式で出力してください。他の文章は含めないでください。

    {
    "category": "カテゴリ名",
    "purpose": "目的の説明",
    "urgency": "高 or 中 or 低",
    "complexity": "高 or 中 or 低",
    "key_requirements": ["要素1", "要素2"],
    "constraints": ["制約1", "制約2"]
    }
    """



class AgentState(TypedDict):
    original_task:str
    analysis:Optional[dict[str,Any]]

class UrgencyLevel(str,Enum):
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

class ComplexityLevel(str, Enum):
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

class AnalysisResult(BaseModel):
    category: str = Field(description='タスクの種類(例: 仕事、勉強、家事、趣味)')
    purpose: str = Field(description='このタスクの目的・ゴール')
    urgency: UrgencyLevel = Field(description='緊急度')
    complexity: ComplexityLevel = Field(description='複雑さ')
    key_requirements:list[str] =Field(
        default_factory=list,
        description='主要要素'
    )
    constraints:list[str] =Field(
        default_factory=list,
        description='制約条件'
)


def create_user_prompt(task:str) ->str:
    return f"""以下のタスクを分析してください。
    タスク: {task}
    JSON形式で分析結果を出力してください。"""

def parse_analysis_result(llm_output:str) -> AnalysisResult:

    start = llm_output.find("{")
    end = llm_output.rfind("}") +1
    json_str = llm_output[start:end]

    data = json.loads(json_str)
    return AnalysisResult(**data)


def analyze(state: AgentState) -> dict[str,Any]:
    try:
        task = state["original_task"]
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.0
            )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=create_user_prompt(task)),
            ]
        response = llm.invoke(messages)
        result = parse_analysis_result(response.content)
        return {"analysis": result.model_dump()}
    
    except json.JSONDecodeError as e:
        return{
            "analysis": None,
            "error": f"JSON パースエラー: {e}"
        }
    except Exception as e:
        return {
            "analysis": None,
            "error": f"分析エラー: {e}"
        }