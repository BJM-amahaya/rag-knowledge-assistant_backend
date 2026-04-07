import json
import logging
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from app.config import settings
from typing import Any

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """あなたはスケジュールの専門家です。
サブタスクリストを分解して、最適な実行スケジュールを作成します。

## スケジューリングルール

1.**依存関係の尊重**
    - タスクAがタスクBに依存している場合、Aを先に配置

2.**優先度の反映**
    - 優先度1(最優先) → 早い日時に配置
    - 優先度5(保留) → 後回しまたはスキップ

3. **作業時間の反映**
    - 1日の作業時間: 9:00 ~ 17:00 (8時間)
    - 昼休憩: 12:00 ~ 13:00
    - タスク間の休憩: 10分

4. **日付ルール**
    - 開始日: 指定がなければ翌営業日
    - 土日祝は除外

## 出力形式
必ず以下のJSON形式のみで出力してください :
{
    "schedule": [
        {
            "subtask_id": "subtask_1",
            "scheduled_date": "2026-01-24",
            "scheduled_time": "09:00",
            "duration_minutes": 60
        }
    ],
    "total_days": 3,
    "warnings": ["タスクXは締め切りに間に合わない可能性があります"]
}
"""

class ScheduledTask(BaseModel):
    subtask_id: str = Field(
        description="サブタスク固有ID（例: subtask_1）"
    )
    scheduled_date: str = Field(
        description="予定日(例:2026-01-24)"
    )
    scheduled_time: str = Field(
        description="開始時刻(例:09:00)"
    )
    duration_minutes: int = Field(
        description="所要時間(分)"
    )

class SchedulerResult(BaseModel):
    schedule: list[ScheduledTask] = Field(
        description="スケジュールされたタスクのリスト"
    )
    total_days: int = Field(
        description="全体の所要日数"
    )
    warnings: list[str] = Field(
        description="注意事項・警告メッセージ"
    )

def create_user_prompt(task, subtasks, estimates, priorities) -> str:
    estimates_map = {e["subtask_id"]: e for e in estimates}
    priorities_map = {e["subtask_id"]: e for e in priorities}

    subtask_text = ""
    for st in subtasks:
        est = estimates_map.get(st["id"])
        pri = priorities_map.get(st["id"])

        minutes = est["estimated_minutes"] if est else "不明"
        priority = pri["priority"] if pri else "不明"
        deps = st.get("dependencies", [])

        subtask_text += f"- {st['id']}:{st['title']}\n"
        subtask_text += f"  - 見積もり: {minutes}分\n"
        subtask_text += f"  - 優先度: {priority}\n"
        subtask_text += f"  - 依存: {deps}\n"

    return f"""以下のサブタスクのスケジュールを作成してください。
## 元のタスク
{task}

## サブタスク一覧
{subtask_text}

【指示】
- 依存関係を考慮して順序を決定してください
- 優先度の高いタスクを早い時間帯に配置してください
- JSON形式のみで出力してください
"""

def parse_scheduler_result(llm_output: str) -> SchedulerResult:
    start = llm_output.find("{")
    end = llm_output.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("JSONが見つかりません。")
    json_str = llm_output[start:end]
    data = json.loads(json_str)
    return SchedulerResult(**data)


def schedule(state: dict) -> dict[str, Any]:

    try:
        logger.info("[scheduler] 開始")
        task = state["original_task"]
        subtasks = state.get("subtasks")
        estimates = state.get("estimates")
        priorities = state.get("priorities")

        # Nullガード: 前のノードが失敗していたらスキップ
        if not subtasks or not estimates or not priorities:
            logger.warning("[scheduler] subtasks/estimates/prioritiesのいずれかがNullのためスキップ")
            return {"schedule": None, "error": "前段のエージェントが失敗したためスキップ"}

        llm = ChatBedrock(
            model_id=settings.BEDROCK_MODEL_ID,
            region_name=settings.AWS_REGION,
            model_kwargs={
                "max_tokens": 2000,
                "temperature": 0.0,
            },
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=create_user_prompt(task, subtasks, estimates, priorities))
        ]

        logger.info("[scheduler] LLM呼び出し開始")
        response = llm.invoke(messages)
        logger.info("[scheduler] LLM応答受信: %d文字", len(response.content))
        result = parse_scheduler_result(response.content)
        logger.info("[scheduler] パース完了")
        return {
            "schedule": [st.model_dump() for st in result.schedule],
            "total_days": result.total_days,
            "warnings": result.warnings
        }
    except json.JSONDecodeError as e:
        logger.error("[scheduler] JSONパースエラー: %s", e, exc_info=True)
        return {"schedule": None, "error": f"JSONパースエラー: {e}"}
    except Exception as e:
        logger.error("[scheduler] エラー: %s", e, exc_info=True)
        return {"schedule": None, "error": f"スケジューリングエラー: {e}"}
