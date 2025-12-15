# 📰 Hệ thống Tóm tắt Tin tức Tiếng Việt với ViT5

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Đồ án tốt nghiệp xây dựng hệ thống tóm tắt tin tức tiếng Việt tự động sử dụng mô hình Transformer ViT5-base. Hệ thống hỗ trợ hai phương pháp tóm tắt: **Extractive** (chọn câu quan trọng) và **Abstractive** (paraphrase lại nội dung).

## ✨ Tính năng chính

- 🤖 **Hai mô hình tóm tắt độc lập**: Extractive và Abstractive
- 📊 **Crawl tự động** từ VnExpress và Vietnamnet
- ⚡ **Streaming real-time**: Hiển thị kết quả ngay khi xử lý xong từng bài
- 🎯 **Phân loại tự động**: 11 chuyên mục tin tức
- 🌓 **Dark/Light theme**: Giao diện thân thiện
- 📈 **Lưu lịch sử**: Xem lại tin đã xử lý theo ngày

## 📊 Kết quả đánh giá

| Model | ROUGE-1 | ROUGE-2 | ROUGE-L | BERT F1 | Inference Time |
|-------|---------|---------|---------|---------|----------------|
| **Extractive** | 50.48% | 22.84% | 30.61% | 71.33% | 20.46s |
| **Abstractive** | 45.17% | 22.18% | 27.60% | 69.22% | 10.97s |

*Tested trên 200 mẫu từ dataset VietNews*

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────┐
│            Frontend (React + TypeScript)         │
│  - NewsFeed với streaming support               │
│  - History với date picker                      │
│  - Dark/Light theme toggle                      │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/NDJSON
┌─────────────────▼───────────────────────────────┐
│           Backend (FastAPI + SQLAlchemy)        │
│  - Crawl service (VnExpress, Vietnamnet)       │
│  - Summarizer (ViT5 abstractive)               │
│  - Category extraction từ URL                   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│                  SQLite Database                │
│  - news_article: URL, title, body              │
│  - news_nlp: summary, category                 │
└─────────────────────────────────────────────────┘
```

## 🚀 Cài đặt và Chạy

### Prerequisites

- Python 3.10+
- Node.js 18+
- GPU với CUDA (khuyến nghị, không bắt buộc)

### 1. Clone repository

```bash
git clone https://github.com/<your-username>/do-an-tot-nghiep.git
cd do-an-tot-nghiep
```

### 2. Setup Backend

```bash
cd Web_demo/backend

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt
```

**⚠️ Download models:**

Model đã được upload lên HuggingFace Hub. Có 2 cách sử dụng:

**Option 1: Auto-download từ HuggingFace** (Khuyến nghị)
```python
# Trong Web_demo/backend/app/services/summarizer.py
# Thay MODEL_PATH thành:
MODEL_PATH = "NishiKyen/vit5-vietnamese-news"  # Auto download từ HF
```

**Option 2: Download thủ công**
```bash
# Sử dụng huggingface-cli
pip install -U huggingface-hub
huggingface-cli download NishiKyen/vit5-vietnamese-news --local-dir models/final_vit5_model_phase2
```

🔗 **Model on HuggingFace**: [NishiKyen/vit5-vietnamese-news](https://huggingface.co/NishiKyen/vit5-vietnamese-news)

**Chạy backend:**

```bash
cd Web_demo/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 3. Setup Frontend

```bash
cd Web_demo/frontend

# Cài đặt dependencies
npm install

# Chạy dev server
npm run dev
```

Frontend: http://localhost:5173

## 📁 Cấu trúc thư mục

```
do-an-tot-nghiep/
├── 01_data_clean.ipynb           # Tiền xử lý dữ liệu
├── 02_build_summaries.ipynb      # Tạo dataset extractive (TF-IDF + K-Means)
├── 03_train_summarize.ipynb      # Train model extractive
├── 04_train_classification.ipynb # Train baseline classifier
├── 05_train_phobert.ipynb        # Train PhoBERT (không dùng trong production)
├── abstractive_vit5.ipynb        # Train model abstractive
├── ROUGE.ipynb                   # Đánh giá ROUGE scores
├── evaluation_analysis.ipynb     # Phân tích chi tiết kết quả
├── compare.ipynb                 # So sánh 2 models
│
├── dataset/
│   ├── clean_data.csv            # 11,385 bài báo đã làm sạch
│   ├── summarize_data_combined.csv # Dataset extractive (11,353 mẫu)
│   └── crawl_news.py             # Script crawl dữ liệu
│
├── models/
│   ├── best_model_combined/      # Model extractive (⚠️ không push lên Git)
│   └── final_vit5_model_phase2/  # Model abstractive (⚠️ không push lên Git)
│
├── outputs/
│   ├── evaluation/               # Kết quả đánh giá (biểu đồ, metrics)
│   └── compare_results/          # So sánh chi tiết 2 models
│
└── Web_demo/
    ├── backend/
    │   ├── app/
    │   │   ├── main.py           # FastAPI entry point
    │   │   ├── database.py       # SQLAlchemy setup
    │   │   ├── models/           # Database models
    │   │   ├── routers/          # API endpoints
    │   │   ├── schemas/          # Pydantic schemas
    │   │   └── services/         # Business logic
    │   │       ├── crawler.py    # Crawl VnExpress/Vietnamnet
    │   │       ├── summarizer.py # ViT5 summarization
    │   │       └── classifier.py # Category extraction
    │   └── requirements.txt
    │
    └── frontend/
        ├── src/
        │   ├── pages/
        │   │   ├── Home.tsx      # Trang chính với streaming
        │   │   └── History.tsx   # Xem lịch sử
        │   ├── components/
        │   │   ├── NewsFeed.tsx  # Component hiển thị tin
        │   │   └── HistoryView.tsx
        │   └── api/
        │       └── http.ts       # Axios client
        ├── package.json
        └── vite.config.ts
```

## 🎓 Notebooks giải thích

### Training Pipeline

1. **`01_data_clean.ipynb`**: Crawl và làm sạch 11,385 bài báo
2. **`02_build_summaries.ipynb`**: Tạo 11,353 cặp (bài báo, tóm tắt) bằng TF-IDF + K-Means
3. **`03_train_summarize.ipynb`**: Train model extractive trên dataset tự tạo
4. **`abstractive_vit5.ipynb`**: Train model abstractive trên dataset 8Opt

### Evaluation

5. **`ROUGE.ipynb`**: Tính ROUGE scores trên 200 mẫu test
6. **`evaluation_analysis.ipynb`**: Phân tích chi tiết (inference time, compression ratio, repetition)
7. **`compare.ipynb`**: So sánh trực tiếp 2 models với visualizations

## 🔬 Chi tiết kỹ thuật

### Extractive Model
- **Base**: VietAI/vit5-base (220M params)
- **Dataset**: 11,353 mẫu tự động tạo bằng TF-IDF + K-Means clustering
- **Max length**: 1500/320 tokens (input/output)
- **Training**: 5 epochs, batch 8, lr 5e-5
- **Đặc điểm**: ROUGE cao (50.48%) nhưng tóm tắt dài (96.3 từ) và chậm (20.46s)

### Abstractive Model (⭐ Được chọn cho production)
- **Base**: VietAI/vit5-base (220M params)
- **Dataset**: 8Opt/vietnamese-summarization-dataset (tóm tắt viết tay)
- **Max length**: 1280/256 tokens (input/output)
- **Training**: 3 epochs, batch 8, lr 5e-5, repetition_penalty 2.5
- **Đặc điểm**: Tóm tắt ngắn gọn (63.5 từ), nhanh gấp 2 lần (10.97s), tự nhiên hơn

### Category Classification
- Không dùng model ML, trích xuất trực tiếp từ URL slug
- 11 categories: Chính trị, Thế giới, Kinh doanh, Khoa học công nghệ, Giải trí, Thể thao, Pháp luật, Giáo dục, Sức khỏe, Đời sống, Du lịch
- Accuracy: 100% với VnExpress và Vietnamnet

## 📊 API Endpoints

### Crawl và Tóm tắt (Streaming)
```bash
POST /api/v1/news/crawl-streaming
Content-Type: application/json

{
  "sources": ["vnexpress", "vietnamnet"],
  "limit": 20
}

Response: application/x-ndjson (streaming)
{"url": "...", "title": "...", "summary": "...", "category": "..."}
{"url": "...", "title": "...", "summary": "...", "category": "..."}
...
```

### Lịch sử
```bash
# Lấy danh sách ngày có dữ liệu
GET /api/v1/news/history-dates

# Lấy tin theo ngày
GET /api/v1/news/history?date=2025-12-15
```

## 🎯 Hướng phát triển

- [ ] **Multi-label classification**: PhoBERT để gán nhiều categories
- [ ] **Batch inference**: Xử lý nhiều bài cùng lúc để tăng tốc
- [ ] **Model quantization**: INT8/FP16 để giảm model size
- [ ] **PostgreSQL + Redis**: Scale database cho production
- [ ] **User authentication**: JWT token cho personalization
- [ ] **More sources**: Thêm VietnamNet, Tuổi Trẻ, Dân Trí
- [ ] **Mobile app**: React Native hoặc Flutter

## 📝 Trích dẫn

Nếu bạn sử dụng code này, vui lòng trích dẫn:

```bibtex
@thesis{vietnamese-news-summarization,
  author = {[Tên của bạn]},
  title = {Hệ thống Tóm tắt Tin tức Tiếng Việt sử dụng mô hình ViT5},
  school = {[Tên trường]},
  year = {2025},
  type = {Đồ án tốt nghiệp}
}
```

## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết chi tiết

## 🙏 Acknowledgments

- [VietAI](https://github.com/vietai/ViT5) - Pre-trained ViT5 model
- [8Opt](https://huggingface.co/datasets/8Opt/vietnamese-summarization-dataset-0001) - Abstractive dataset
- [VnExpress](https://vnexpress.net) & [Vietnamnet](https://vietnamnet.vn) - Nguồn tin tức

## 📧 Contact

- Email: [darkpunch09@gmail.com]
- GitHub: [@KienGee](https://github.com/KienGee)

---

⭐ Nếu project này hữu ích, hãy cho một star!
