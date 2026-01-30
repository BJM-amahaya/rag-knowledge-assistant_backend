from fastapi import APIRouter,WebSocket,WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self,websocket:WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self,websocket:WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self,message:str,websocket:WebSocket):
        await websocket.send_text(message)

router = APIRouter(tags=["websocket"])
manager = ConnectionManager()

@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket:WebSocket,task_id:str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(
                f"受信しました:{data}",
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"クライアント{task_id}が切断しました。")