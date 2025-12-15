#\app\main.py
import os

# Disable warnings
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import news

# Tạo các bảng database khi khởi động
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VN News Summarizer & Classifier",
    version="1.0.0",
    debug=True
)

# Include routers
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])

# CORS middleware
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "VN News Summarizer & Classifier is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "service": "VN News Summarizer & Classifier",
        "version": "1.0.0"
    }

# uvicorn app.main:app --reload --port 8000