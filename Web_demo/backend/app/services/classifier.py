#\app\services\classifier.py
"""
DEPRECATED: Module này không còn sử dụng.
Category được lấy trực tiếp từ URL khi crawl, không cần model phân loại.

Giữ lại file này để tương thích với code cũ, nhưng chỉ return category từ URL.
"""
from __future__ import annotations

from typing import Tuple

# Mapping category name để chuẩn hóa
CATEGORY_MAPPING = {
    "chinh-tri": "Chính trị",
    "du-lich": "Du lịch", 
    "giao-duc": "Giáo dục",
    "giai-tri": "Giải trí",
    "khoa-hoc": "Khoa học công nghệ",
    "cong-nghe": "Khoa học công nghệ",
    "kinh-doanh": "Kinh doanh",
    "phap-luat": "Pháp luật",
    "suc-khoe": "Sức khỏe",
    "the-gioi": "Thế giới",
    "the-thao": "Thể thao",
    "doi-song": "Đời sống",
}


def classify(
    title: str | None,
    body: str,
    url_category: str | None = None,
) -> Tuple[str, float, str, float, str, float]:
   
    # Nếu không có category từ URL, return mặc định
    if not url_category:
        return "Khác", 0.0, "Khác", 0.0, "Khác", 0.0
    
    # Chuẩn hóa category name từ URL
    url_category = url_category.lower().strip()
    category = CATEGORY_MAPPING.get(url_category, "Khác")
    
    # Return với score = 1.0 cho category chính, 0.0 cho các category phụ
    return category, 1.0, category, 0.0, category, 0.0
