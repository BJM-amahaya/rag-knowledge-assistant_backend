from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Optional,Any

from .analyzer import analyze
from .decomposer import decompose
from .estimator import estimate
from .prioritizer import prioritize
from .scheduler import schedule

class  AgentState(TypedDict):
    original_task: str
    analysis:Optional[dict[str,Any]]
    subtasks:Optional[list[dict[str,Any]]]
    estimates:Optional[list[dict[str,Any]]]
    total_minutes:Optional[int]
    priorities:Optional[list[dict[str,Any]]]
    schedule:Optional[list[dict[str,Any]]]
    total_days:Optional[int]
    warnings:Optional[list[str]]

def create_agent_graph():
    builder = StateGraph(AgentState)
    builder.add_node("analyzer",analyze)
    builder.add_node("decomposer",decompose)
    builder.add_node("estimator",estimate)
    builder.add_node("prioritizer",prioritize)
    builder.add_node("scheduler",schedule)

    builder.add_edge(START, "analyzer")
    builder.add_edge("analyzer", "decomposer")
    builder.add_edge("decomposer", "estimator")
    builder.add_edge("estimator", "prioritizer")
    builder.add_edge("prioritizer", "scheduler")
    builder.add_edge("scheduler", END)

    return builder.compile()

agent_graph = create_agent_graph()
