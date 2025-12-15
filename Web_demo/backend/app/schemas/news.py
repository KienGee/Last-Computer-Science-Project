#app\schemas\news.py
from pydantic import BaseModel
from typing import Optional, List


class CrawlRequest(BaseModel):
    
    sources: List[str] = ["vnexpress", "vietnamnet"]
    limit: int = 20
    force_new: bool = False
    force_refresh: bool = False  # Bắt buộc chạy model lại, không dùng cache


class CrawledNews(BaseModel):
    title: str
    body: str
    source: str
    url: Optional[str] = None
    published_at: Optional[str] = None

    summary: str
    category: str  # Category từ URL, không còn dùng model phân loại
