# app/routers/news.py
from __future__ import annotations

import json
from typing import Iterable
from datetime import datetime, timedelta

from dateutil import parser as dtparse
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.news import NewsArticle, NewsNLP
from app.schemas.news import (
    CrawlRequest,
    CrawledNews,
)
from app.services.classifier import classify
from app.services.crawler import crawl_today_news
from app.services.summarizer import summarize

router = APIRouter()

VI_WEEKDAYS = [
    "Thứ hai",
    "Thứ ba",
    "Thứ tư",
    "Thứ năm",
    "Thứ sáu",
    "Thứ bảy",
    "Chủ nhật",
]

MODEL_VERSION = "v1"  # tuỳ bạn đặt theo version mô hình


def _format_vietnamnet_published(published_at: str | None) -> str | None:
    """
    Định dạng lại thời gian của Vietnamnet sang format tiếng Việt.
    """
    if not published_at:
        return published_at

    try:
        dt = dtparse.parse(published_at)
    except Exception:
        return published_at

    weekday = VI_WEEKDAYS[dt.weekday()]
    return f"{weekday}, {dt.day:02d}/{dt.month:02d}/{dt.year}, {dt.hour:02d}:{dt.minute:02d} (GMT+7)"


def _strip_vietnamnet_author(summary: str) -> str:
    """
    Một số bài Vietnamnet phần tóm tắt sẽ có tên phóng viên đầu dòng,
    hàm này thử loại bỏ cụm tên đó nếu detect được.
    """
    if not summary:
        return summary

    tokens = summary.strip().split()
    if len(tokens) < 3:
        return summary

    def is_name_token(tok: str) -> bool:
        t = tok.strip(",.:-–—")
        if not t:
            return False
        return t[0].isupper() and not t.isupper() and len(t) <= 15

    if is_name_token(tokens[0]) and is_name_token(tokens[1]):
        new_text = " ".join(tokens[2:]).lstrip(",.:-–— ").strip()
        if not new_text:
            return summary
        return new_text[0].upper() + new_text[1:]
    return summary


def _get_or_create_article(
    db: Session,
    *,
    url: str,
    source: str,
    title: str,
    body: str,
    published_at: str | None,
) -> NewsArticle:
    """
    Tìm article theo URL; nếu chưa có thì tạo mới.
    """
    article = db.query(NewsArticle).filter(NewsArticle.url == url).first()
    if article:
        # Cập nhật lại thông tin nếu cần
        changed = False
        if article.title != title:
            article.title = title
            changed = True
        if article.body != body:
            article.body = body
            changed = True
        if article.source != source:
            article.source = source
            changed = True
        if article.published_at != published_at:
            article.published_at = published_at
            changed = True
        if changed:
            db.add(article)
            db.commit()
            db.refresh(article)
        return article

    article = NewsArticle(
        url=url,
        source=source,
        title=title,
        body=body,
        published_at=published_at,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def _get_or_create_nlp(
    db: Session,
    *,
    article_id: int,
    summary: str,
    category: str | None,
    model_version: str = MODEL_VERSION,
) -> NewsNLP:
    """
    Lưu/khởi tạo record NLP cho bài viết. Nếu đã có cùng model_version thì dùng lại.
    """
    nlp = (
        db.query(NewsNLP)
        .filter(
            NewsNLP.article_id == article_id,
            NewsNLP.model_version == model_version,
        )
        .first()
    )
    if nlp:
        return nlp

    nlp = NewsNLP(
        article_id=article_id,
        summary=summary,
        category=category,
        model_version=model_version,
    )
    db.add(nlp)
    db.commit()
    db.refresh(nlp)
    return nlp


def _process_crawled_item(
    db: Session,
    item,
    force_refresh: bool = False,
) -> CrawledNews:
    """
    Nhận 1 item từ crawler:
      - Chuẩn hoá published_at, summary cho Vietnamnet
      - Gọi summarize + classify (nếu chưa có trong DB hoặc force_refresh=True)
      - Lưu vào SQLite
      - Trả về CrawledNews cho response
    """
    # Chuẩn hoá thời gian
    published_at = item.published_at
    if item.source == "vietnamnet":
        published_at = _format_vietnamnet_published(published_at)

    # Nếu đã có NLP cho bài này (cùng model_version) và không force_refresh thì dùng lại,
    # tránh phải chạy summarize/classify lại.
    article = db.query(NewsArticle).filter(NewsArticle.url == item.url).first()
    if not force_refresh and article and article.nlp and article.nlp.model_version == MODEL_VERSION:
        nlp = article.nlp
        return CrawledNews(
            title=article.title,
            body=article.body,
            source=article.source,
            url=article.url,
            published_at=article.published_at,
            summary=nlp.summary,
            category=nlp.category,
        )

    # Chưa có hoặc model_version khác → chạy model lại
    summary = summarize(item.title, item.body)
    if item.source == "vietnamnet":
        summary = _strip_vietnamnet_author(summary)

    # Category từ URL (không cần model phân loại)
    category = item.category

    # Ghi xuống DB
    article = _get_or_create_article(
        db,
        url=item.url,
        source=item.source,
        title=item.title,
        body=item.body,
        published_at=published_at,
    )

    nlp = _get_or_create_nlp(
        db,
        article_id=article.id,
        summary=summary,
        category=category,
        model_version=MODEL_VERSION,
    )

    return CrawledNews(
        title=article.title,
        body=article.body,
        source=article.source,
        url=article.url,
        published_at=article.published_at,
        summary=nlp.summary,
        category=nlp.category,
    )


@router.post("/crawl_today", response_model=list[CrawledNews])
def crawl_today(
    payload: CrawlRequest,
    db: Session = Depends(get_db),
):
    """
    Crawl Today (Test - Non-Stream)
    
    Endpoint để test trong docs. Xử lý xong hết rồi mới trả về JSON array.
    Frontend nên dùng /crawl_today_stream để có UX tốt hơn.
    """
    sources = payload.sources or ["vnexpress"]
    limit = payload.limit or 12

    raw_items = crawl_today_news(sources, limit=limit)

    results: list[CrawledNews] = []
    for item in raw_items:
        crawled = _process_crawled_item(db, item)
        results.append(crawled)

    return results


@router.post("/crawl_today_stream")
def crawl_today_stream(
    payload: CrawlRequest,
    db: Session = Depends(get_db),
):
    """
    Bản stream: model xử lý xong bài nào thì:
      - Lưu vào SQLite
      - Stream 1 dòng JSON (NDJSON) về frontend bài đó
    """
    sources = payload.sources or ["vnexpress"]
    limit = payload.limit or 12
    force_refresh = payload.force_refresh

    raw_items = crawl_today_news(sources, limit=limit)

    def iter_items() -> Iterable[str]:
        count = 0
        seen_urls = set()
        skipped = 0
        for item in raw_items:
            try:
                # Check duplicate trong raw_items từ crawler
                if item.url in seen_urls:
                    skipped += 1
                    continue
                seen_urls.add(item.url)
                
                count += 1
                print(f"[{count}] {item.title[:80]}")
                crawled = _process_crawled_item(db, item, force_refresh=force_refresh)
                # Mỗi bài là 1 dòng JSON, kết thúc bằng \n
                yield json.dumps(crawled.model_dump(), ensure_ascii=False) + "\n"
            except Exception as e:
                print(f"[{count}] ERROR: {str(e)[:100]}")
                # Skip item này và tiếp tục với item tiếp theo
                continue
        print(f"\n=== Finished: {count} articles processed, {skipped} duplicates skipped ===")

    return StreamingResponse(iter_items(), media_type="application/json")


@router.get("/by_date", response_model=list[CrawledNews])
def get_news_by_date(
    date: str = Query(..., description="Ngày cần xem tin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Lấy tất cả tin tức đã crawl trong 1 ngày cụ thể từ database.
    Ví dụ: /api/v1/news/by_date?date=2025-11-28
    """
    try:
        # Parse ngày
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Định dạng ngày không hợp lệ. Dùng YYYY-MM-DD")
    
    # Tạo range từ 00:00:00 đến 23:59:59
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())
    
    # Query theo created_at - không dùng join để tránh duplicate
    articles = (
        db.query(NewsArticle)
        .filter(NewsArticle.created_at >= start_dt)
        .filter(NewsArticle.created_at <= end_dt)
        .order_by(NewsArticle.created_at.desc())
        .all()
    )
    
    if not articles:
        return []
    
    results: list[CrawledNews] = []
    for article in articles:
        # Lấy NLP record với model_version hiện tại hoặc mới nhất
        nlp = (
            db.query(NewsNLP)
            .filter(NewsNLP.article_id == article.id)
            .order_by(NewsNLP.created_at.desc())
            .first()
        )
        
        if not nlp:
            continue
        
        results.append(
            CrawledNews(
                title=article.title,
                body=article.body,
                source=article.source,
                url=article.url,
                published_at=article.published_at,
                summary=nlp.summary,
                category=nlp.category,
            )
        )
    
    return results


@router.get("/available_dates")
def get_available_dates(db: Session = Depends(get_db)):
    """
    Lấy danh sách các ngày có tin tức trong database.
    """
    # Lấy danh sách các ngày duy nhất từ created_at
    dates = (
        db.query(func.date(NewsArticle.created_at).label("date"))
        .distinct()
        .order_by(func.date(NewsArticle.created_at).desc())
        .limit(30)  # Lấy 30 ngày gần nhất
        .all()
    )
    
    return {"dates": [str(d[0]) for d in dates]}
