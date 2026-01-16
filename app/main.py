from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAG Knowledge Assistant API",
    description="RAGアプリです。",
    version = "1.0.0"
)

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