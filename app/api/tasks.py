from fastapi import APIRouter, HTTPException
from app.models.task import TaskRequest,TaskResponse
from app.services.task_service import process_task
from app.services.firestore_service import firestore_service


router = APIRouter(prefix="/tasks",tags=["tasks"])
@router.post("",response_model=TaskResponse)
def create_task(request:TaskRequest):
    response = process_task(request)
    return response

@router.get("")
def get_tasks():
    tasks = firestore_service.get_all()
    return tasks

@router.get("/{task_id}")
def get_task(task_id :str):
    task = firestore_service.get(task_id)
    if task is None:
        raise HTTPException(status_code=404,detail="Task not found")
    return task

@router.delete("/{task_id}")
def delete_task(task_id:str):
    task = firestore_service.get(task_id)
    if task is None:
        raise HTTPException(status_code=404,detail="Task not found")
    return firestore_service.delete(task_id)
