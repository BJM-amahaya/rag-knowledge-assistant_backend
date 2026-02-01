from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from app.services.task_service import process_task_streaming
import json

class ConnectionManager:
    def __init__(self):
        self.connections:dict[str, list[WebSocket]] = {}

    async def connect(self,websocket:WebSocket,task_id:str):
        await websocket.accept()
        if task_id not in self.connections:
            self.connections[task_id] = []
        self.connections[task_id].append(websocket)
    
    def disconnect(self,websocket:WebSocket,task_id:str):
        if task_id in self.connections:
            self.connections[task_id].remove(websocket)
            if not self.connections[task_id]:
                del self.connections[task_id]
    
    async def broadcast(self, task_id: str, message: str):
        if task_id in self.connections:
            dead_connections = []
            for connection in self.connections[task_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.append(connection)
            
            for dead in dead_connections:
                self.connections[task_id].remove(dead)


router = APIRouter(tags=["websocket"])
manager = ConnectionManager()

@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket:WebSocket,task_id:str):
    await manager.connect(websocket,task_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "start_task":
                task = message.get("task")
                async def on_progress(tid: str, chunk: dict):
                    await manager.broadcast(tid,json.dumps({
                        "type":"progress",
                        "data":chunk
                    }))
                result = await process_task_streaming(
                    task_id=task_id,
                    task=task,
                    callback=on_progress
                )

                await manager.broadcast(task_id,json.dumps({
                    "type":"complete",
                    "data":result
                }))

    except WebSocketDisconnect:
        manager.disconnect(websocket,task_id)
        print(f"クライアント{task_id}が切断しました。")