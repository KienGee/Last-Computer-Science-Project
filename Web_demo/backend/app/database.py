# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./news.db"  # file news.db đặt cạnh main.py

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # bắt buộc với SQLite + nhiều thread
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency dùng trong FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
