import uuid
from app.models.task import TaskRequest,TaskResponse
from app.agents.graph import agent_graph
from app.services.firestore_service import firestore_service

def process_task(request: TaskRequest) -> TaskResponse:
    task_id = str(uuid.uuid4())

    result = agent_graph.invoke({
        "original_task":request.task
    })

    response = TaskResponse(
        id=task_id,
        task=request.task,
        status="completed",
        analysis=result.get("analysis"),
        subtasks=result.get("subtasks"),
        estimates=result.get("estimates"),
        total_minutes=result.get("total_minutes"),
        priorities=result.get("priorities"),
        schedule=result.get("schedule"),
        total_days=result.get("total_days"),
        warnings=result.get("warnings"),
    )

    firestore_service.save(task_id, response.model_dump())

    return response

async def process_task_streaming(
        task_id:str,
        task:str,
        callback
        ):
    final_state = None
    async for chunk in agent_graph.astream(
        {
        "original_task":task
        },
        stream_mode="updates"
    ):
        await callback(task_id,chunk)
        if final_state is None:
            final_state = chunk
        else:
            final_state.update(chunk)
    return final_state