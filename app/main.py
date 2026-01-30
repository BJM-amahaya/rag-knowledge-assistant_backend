from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import tasks
from app.api import websocket

app = FastAPI(
    title="RAG Knowledge Assistant API",
    description="RAGアプリです。",
    version = "1.0.0"
)

app.include_router(tasks.router)
app.include_router(websocket.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True 
)

@app.get("/")
def root():
    return {"message": "Hello", "status": "ok"}   