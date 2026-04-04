import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import tasks
from app.api import websocket
from app.api import documents
from app.api import chat

app = FastAPI(
    title="RAG Knowledge Assistant API",
    description="RAGアプリです。",
    version = "1.0.0"
)

app.include_router(tasks.router)
app.include_router(websocket.router)
app.include_router(documents.router)
app.include_router(chat.router)

allow_origins = [
    os.environ.get("CORS_ALLOWED_ORIGIN", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello", "status": "ok"}   