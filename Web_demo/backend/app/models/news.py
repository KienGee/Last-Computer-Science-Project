# app/models/news.py
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_article"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, index=True, nullable=False)
    source = Column(String(50), index=True, nullable=False)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    published_at = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    nlp = relationship("NewsNLP", back_populates="article", uselist=False)

    # Index cho query hiệu quả
    __table_args__ = (
        # Composite index cho query tin mới theo nguồn
        # Ví dụ: SELECT * FROM news_article WHERE source='vnexpress' ORDER BY created_at DESC
        Index('idx_source_created', 'source', 'created_at'),
    )


class NewsNLP(Base):
    __tablename__ = "news_nlp"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_article.id"), nullable=False)

    summary = Column(Text, nullable=False)
    category = Column(String(100), index=True, nullable=True)  # Category từ URL

    model_version = Column(String(50), default="v1")  

    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("NewsArticle", back_populates="nlp")
