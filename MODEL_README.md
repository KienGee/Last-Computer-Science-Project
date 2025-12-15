---
language:
- vi
license: mit
tags:
- summarization
- vietnamese
- news
- vit5
- abstractive-summarization
datasets:
- 8Opt/vietnamese-summarization-dataset-0001
metrics:
- rouge
pipeline_tag: summarization
widget:
- text: "Chính phủ Việt Nam đã ban hành quy định mới về thuế thu nhập cá nhân, áp dụng từ ngày 1 tháng 1 năm 2026. Theo đó, mức giảm trừ gia cảnh sẽ được tăng từ 11 triệu đồng lên 13 triệu đồng mỗi tháng. Đây là mức tăng cao nhất trong 5 năm qua, nhằm giảm gánh nặng thuế cho người lao động và kích thích tiêu dùng. Bộ Tài chính cho biết chính sách này sẽ có tác động tích cực đến khoảng 15 triệu người đóng thuế thu nhập cá nhân trên toàn quốc."
  example_title: "Tin tức chính trị"
---

# ViT5 Vietnamese News Summarization (Abstractive)

Mô hình tóm tắt tin tức tiếng Việt tự động sử dụng kiến trúc **ViT5-base** (Vietnamese T5), được fine-tune cho bài toán **abstractive summarization** (tóm tắt trừu tượng).

## 📊 Model Description

- **Base Model**: [VietAI/vit5-base](https://huggingface.co/VietAI/vit5-base)
- **Task**: Abstractive Text Summarization
- **Language**: Vietnamese (Tiếng Việt)
- **Parameters**: 220M
- **License**: MIT
- **Training Dataset**: [8Opt/vietnamese-summarization-dataset-0001](https://huggingface.co/datasets/8Opt/vietnamese-summarization-dataset-0001)

## 🎯 Performance

Evaluated on 200 samples from VietNews test set:

| Metric | Score |
|--------|-------|
| **ROUGE-1** | 45.17% |
| **ROUGE-2** | 22.18% |
| **ROUGE-L** | 27.60% |
| **BERT F1** | 69.22% |
| **Inference Time** | 10.97s/sample (CPU) |
| **Compression Ratio** | 0.292 |

### Comparison with Extractive Model

| Model | ROUGE-1 | ROUGE-2 | ROUGE-L | BERT F1 | Speed |
|-------|---------|---------|---------|---------|-------|
| **Abstractive** (this) | 45.17% | 22.18% | 27.60% | 69.22% | **10.97s** ⚡ |
| Extractive | 50.48% | 22.84% | 30.61% | 71.33% | 20.46s |

**Highlights:**
- ✅ **2x faster** than extractive model
- ✅ **Shorter summaries** (63.5 words vs 96.3 words)
- ✅ **More natural** paraphrasing instead of copying sentences
- ⚠️ Slightly lower ROUGE scores (expected for abstractive approach)

## 💻 Usage

### Installation

```bash
pip install transformers torch
```

### Basic Usage

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Load model and tokenizer
model_name = "NishiKyen/vit5-vietnamese-news"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Input text
text = """
Chính phủ Việt Nam đã ban hành quy định mới về thuế thu nhập cá nhân, 
áp dụng từ ngày 1 tháng 1 năm 2026. Theo đó, mức giảm trừ gia cảnh 
sẽ được tăng từ 11 triệu đồng lên 13 triệu đồng mỗi tháng.
"""

# Tokenize
inputs = tokenizer(
    text,
    max_length=1280,
    truncation=True,
    padding="max_length",
    return_tensors="pt"
)

# Generate summary
outputs = model.generate(
    inputs["input_ids"],
    max_new_tokens=256,
    num_beams=5,
    repetition_penalty=2.5,
    no_repeat_ngram_size=3,
    early_stopping=True
)

# Decode
summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(summary)
```

**Output:**
```
Chính phủ tăng mức giảm trừ gia cảnh lên 13 triệu đồng/tháng từ 1/1/2026, 
ảnh hưởng đến 15 triệu người nộp thuế TNCN.
```

### Advanced Usage with Dynamic Length

```python
def summarize_news(text, max_input_length=1280):
    """
    Tóm tắt tin tức với độ dài động
    """
    # Estimate output length based on input
    input_len = len(text.split())
    
    if input_len <= 500:
        max_new = 180
    elif input_len <= 1000:
        max_new = 250
    else:
        max_new = 256
    
    # Tokenize
    inputs = tokenizer(
        text,
        max_length=max_input_length,
        truncation=True,
        return_tensors="pt"
    )
    
    # Generate with optimal parameters
    outputs = model.generate(
        inputs["input_ids"],
        max_new_tokens=max_new,
        min_new_tokens=50,
        num_beams=5,
        length_penalty=1.0,
        repetition_penalty=2.5,
        no_repeat_ngram_size=3,
        early_stopping=True
    )
    
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return summary

# Usage
long_article = "..."  # Your news article
summary = summarize_news(long_article)
```

## 🏗️ Training Details

### Hyperparameters

- **Epochs**: 3
- **Batch Size**: 8 (effective: 8 with gradient accumulation)
- **Learning Rate**: 5e-5
- **Max Input Length**: 1280 tokens
- **Max Output Length**: 256 tokens
- **Optimizer**: AdamW
- **Scheduler**: Linear warmup
- **FP16**: Enabled
- **Repetition Penalty**: 2.5
- **No Repeat N-gram Size**: 3

### Training Configuration

```python
training_args = {
    "output_dir": "./models/vit5_abstractive",
    "num_train_epochs": 3,
    "per_device_train_batch_size": 8,
    "learning_rate": 5e-5,
    "warmup_steps": 500,
    "weight_decay": 0.01,
    "fp16": True,
    "evaluation_strategy": "epoch",
    "save_strategy": "epoch",
    "load_best_model_at_end": True,
}
```

## 📁 Model Architecture

```
ViT5-base (220M parameters)
├── Encoder: 12 layers, 768 hidden, 12 heads
├── Decoder: 12 layers, 768 hidden, 12 heads
└── Vocabulary: 32,000 SentencePiece tokens
```

## 🎓 Citation

```bibtex
@misc{vit5-vietnamese-news,
  author = {Nguyen Trung Kien},
  title = {ViT5 Vietnamese News Summarization},
  year = {2025},
  publisher = {HuggingFace},
  howpublished = {\url{https://huggingface.co/NishiKyen/vit5-vietnamese-news}}
}
```

## 📝 Notes

- Mô hình được fine-tune trên tóm tắt **abstractive** (paraphrase), khác với extractive (chọn câu gốc)
- Phù hợp cho tin tức tiếng Việt (chính trị, kinh tế, xã hội, v.v.)
- Output ngắn gọn hơn và tự nhiên hơn so với extractive model
- Inference time nhanh gấp 2 lần so với extractive variant

## 🔗 Related Resources

- **GitHub Repository**: [vietnamese-news-summarization](https://github.com/NishiKyen/vietnamese-news-summarization)
- **Base Model**: [VietAI/vit5-base](https://huggingface.co/VietAI/vit5-base)
- **Dataset**: [8Opt/vietnamese-summarization-dataset](https://huggingface.co/datasets/8Opt/vietnamese-summarization-dataset-0001)
- **Extractive Variant**: *Coming soon*

## 📧 Contact

- GitHub: [@NishiKyen](https://github.com/NishiKyen)
- Email: nguyentrungkine08102004@gmail.com

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details
