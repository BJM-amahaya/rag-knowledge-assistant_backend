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
    try:
        async for chunk in agent_graph.astream(
            {
            "original_task":task
            },
            stream_mode="updates"
        ):
            print(f"[stream] チャンク受信: {list(chunk.keys())}")
            await callback(task_id,chunk)
            if final_state is None:
                final_state = chunk
            else:
                final_state.update(chunk)
    except Exception as e:
        print(f"[stream] エラー: {e}")
        error_chunk = {"error": str(e)}
        await callback(task_id, error_chunk)
        return error_chunk
    print("[stream] 完了")

    # final_state をフラット化して Firestore に保存
    if final_state and "error" not in final_state:
        flat = {}
        for node_output in final_state.values():
            if isinstance(node_output, dict):
                flat.update(node_output)

        response = TaskResponse(
            id=task_id,
            task=task,
            status="completed",
            analysis=flat.get("analysis"),
            subtasks=flat.get("subtasks"),
            estimates=flat.get("estimates"),
            total_minutes=flat.get("total_minutes"),
            priorities=flat.get("priorities"),
            schedule=flat.get("schedule"),
            total_days=flat.get("total_days"),
            warnings=flat.get("warnings"),
        )
        firestore_service.save(task_id, response.model_dump())

    return final_state