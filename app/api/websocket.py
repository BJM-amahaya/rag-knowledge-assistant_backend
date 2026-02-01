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
            for connection in self.connections[task_id]:
                print(f'コネクションAMA：{connection}')
                await connection.send_text(message)

    async def send_personal_message(self,message:str,websocket:WebSocket):
        await websocket.send_text(message)

router = APIRouter(tags=["websocket"])
manager = ConnectionManager()

@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket:WebSocket,task_id:str):
    await manager.connect(websocket,task_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(
                f"受信しました:{data}",
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket,task_id)
        print(f"クライアント{task_id}が切断しました。")