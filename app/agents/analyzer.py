from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel,Field
from enum import Enum
from typing import TypedDict, Optional, Any
from app.config import settings
import json

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