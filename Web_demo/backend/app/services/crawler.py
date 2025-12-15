#\app\services\crawler.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from dateutil import parser as dtparse

from app.services import crawl_news


@dataclass
class RawNews:
    title: str
    body: str
    source: str
    category: str  # Category từ URL (ví dụ: "Kinh doanh", "Thể thao")
    url: Optional[str] = None
    published_at: Optional[str] = None


def crawl_today_news(
    sources: Optional[List[str]] = None, 
    limit: Optional[int] = None,
) -> List[RawNews]:
    
    # 1) Danh sách chủ đề & site cố định
    subjects = list(crawl_news.CANON.keys())  # 11 slug: chinh-tri, the-gioi, ...
    sites = ["vnexpress", "vietnamnet"]

    # Lấy tối đa 3 bài / (site, subject)
    per_pair_max = 3

    # 2) Biến theo dõi để tránh trùng
    seen_title = set()
    seen_bhash = set()
    items: List[RawNews] = []

    # 3) Vòng lặp qua từng chủ đề rồi từng site
    for subject_slug in subjects:
        # Lấy category name chuẩn từ CANON
        category_name = crawl_news.CANON.get(subject_slug, "Khác")
        
        for site in sites:

            list_sels = crawl_news.LIST_SELECTORS.get(site)
            pattern = crawl_news.PATTERNS.get(subject_slug, {}).get(site)
            if not list_sels or not pattern:
                # Nếu chưa cấu hình selector/pattern cho site này thì bỏ qua
                continue

            # Crawl tối đa 3 bài cho (site, subject) này
            rows = crawl_news.crawl_subject(
                site=site,
                subject_slug=subject_slug,
                pattern=pattern,
                list_selectors=list_sels,
                pages=1,
                seen_title=seen_title,
                seen_bhash=seen_bhash,
                max_items=per_pair_max,
            )

            for r in rows:
                items.append(
                    RawNews(
                        title=r["title"],
                        body=r["body"],
                        source=r["source"],
                        category=category_name,  # Category từ URL
                        url=r.get("url"),
                        published_at=r.get("published_at") or None,
                    )
                )

    return items
