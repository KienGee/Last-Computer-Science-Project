from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, List, Tuple
import re
import threading

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Disable meta device warnings
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

# Model paths
SUMMARIZER_DIR = Path(r"D:/do-an-tot-nghiep/models/final_vit5_model_phase2")

# Giới hạn input / output token
MAX_SOURCE_LEN = 1500
MAX_TARGET_LEN = 320

# Số đoạn tối đa dùng trong paragraph-mode
MAX_PARAS_SUMMARIZED = 8

_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_tokenizer: Optional[AutoTokenizer] = None
_model: Optional[AutoModelForSeq2SeqLM] = None
_lock = threading.Lock()  # Thread-safe tokenizer access


def _load_summarizer() -> Tuple[AutoTokenizer, AutoModelForSeq2SeqLM]:
    """Lazy-load tokenizer và model lên GPU/CPU."""
    global _tokenizer, _model

    if _tokenizer is not None and _model is not None:
        return _tokenizer, _model

    if not SUMMARIZER_DIR.exists():
        raise RuntimeError(f"Không tìm thấy model tóm tắt ở: {SUMMARIZER_DIR}")

    _tokenizer = AutoTokenizer.from_pretrained(
        SUMMARIZER_DIR,
        local_files_only=True,
        use_fast=False,  # Force dùng SentencePiece tokenizer
    )

    # Load model
    if _DEVICE.type == "cuda":
        _model = AutoModelForSeq2SeqLM.from_pretrained(
            SUMMARIZER_DIR,
            local_files_only=True,
        )
        _model = _model.to(_DEVICE).half()  # Convert to float16
    else:
        _model = AutoModelForSeq2SeqLM.from_pretrained(
            SUMMARIZER_DIR,
            local_files_only=True,
        )
        _model = _model.to(_DEVICE)
    
    _model.eval()

    return _tokenizer, _model


# ================== ƯỚC LƯỢNG ĐỘ DÀI SUMMARY ==================

def _estimate_new_token_range(
    text: str,
    num_paras: int | None = None,
) -> Tuple[int, int]:
    """
    Ước lượng độ dài tóm tắt dựa trên độ dài bài gốc.
    Tăng ngưỡng để tóm tắt chi tiết hơn, giữ được nhiều ý quan trọng.
    
    - n_words <= 500  -> max_new = 250 (~60-70 từ)
    - n_words <= 1000 -> max_new = 350 (~85-95 từ)
    - n_words  > 1000 -> max_new = 450 (~110-120 từ)
    
    Nếu bài nhiều đoạn (num_paras >= 10) thì tăng max_new thêm 50.
    """
    n_words = len(text.split())

    if n_words <= 500:
        min_new, max_new = 100, 250
    elif n_words <= 1000:
        min_new, max_new = 180, 350
    else:
        min_new, max_new = 250, 450

    # Bài dài nhiều đoạn → tăng thêm để bao quát
    if num_paras is not None and num_paras >= 10:
        max_new = min(600, max_new + 50)

    # Đảm bảo min < max
    if max_new <= 10:
        return max_new, max_new
    
    min_new = min(min_new, max_new - 20)
    return int(min_new), int(max_new)


def _truncate_to_last_sentence(text: str) -> str:
    """
    Cắt đến dấu câu cuối; bỏ qua '.' nằm giữa 2 chữ số (số thập phân / 1.000).
    Nếu không có dấu câu, cắt mềm theo khoảng trắng.
    """
    text = text.strip()
    if not text:
        return text

    end_chars = ".?!…"
    last_idx = -1

    for i in range(len(text) - 1, -1, -1):
        ch = text[i]
        if ch not in end_chars:
            continue
        if ch == "." and i > 0 and i < len(text) - 1:
            if text[i - 1].isdigit() and text[i + 1].isdigit():
                continue
        last_idx = i
        break

    if last_idx != -1:
        truncated = text[: last_idx + 1].strip()
        tail = text[last_idx + 1:].strip()
        if len(tail) > 40 and not any(c in tail for c in end_chars):
            return truncated
        if len(truncated) < 20:
            return text
        return truncated

    if len(text) > 120:
        last_space = text.rfind(" ", 0, len(text) - 5)
        if last_space != -1 and last_space > 20:
            return text[:last_space].strip() + "..."
    return text


# ================== XỬ LÝ VĂN BẢN INPUT ==================

_SENT_SPLIT_REGEX = re.compile(r"(?<=[\.!?…])\s+")
_MEDIA_PREFIXES = [
    "ảnh:",
    "xem ảnh:",
    "video:",
    "xem video:",
    "clip:",
    "xem clip:",
    "hình:",
    "hình ảnh:",
    "xem hình ảnh:",
    "ảnh minh họa:",
    "xem hình:",
    "xem ảnh minh họa:",
]

# Các pattern nhận diện box tâm sự Vietnamnet
_NOISE_PARAGRAPH_PATTERNS = [
    "mời độc giả chia sẻ",
    "tâm sự gửi về email:",
    "tâm sự gửi về e-mail:",
    "bandosong@vietnamnet.vn",
    "@vietnamnet.vn",
]


def _split_into_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    sentences = _SENT_SPLIT_REGEX.split(text)
    return [s.strip() for s in sentences if s.strip()]


def _filter_media_sentences(text: str) -> str:
    """Loại caption ảnh / video và tên file ảnh."""
    sentences = _split_into_sentences(text)
    if not sentences:
        return text.strip()

    filtered: List[str] = []

    for s in sentences:
        s0 = s.strip()
        if not s0:
            continue

        lower = s0.lower()

        is_media_prefix = any(lower.startswith(pref) for pref in _MEDIA_PREFIXES)
        is_image_filename = (
            ("image" in lower or "img" in lower)
            and (".png" in lower or ".jpg" in lower or ".jpeg" in lower)
        )

        if is_media_prefix or is_image_filename:
            if is_media_prefix and filtered:
                prev = filtered[-1]
                if len(prev.split()) <= 20:
                    filtered.pop()
            continue

        filtered.append(s0)

    return " ".join(filtered).strip()


def _split_into_paragraphs(text: str) -> List[str]:
    """
    Chia theo đoạn xuống dòng trống.
    Nếu chỉ có 1 đoạn dài, chia theo cụm ~5 câu.
    """
    text = text.strip()
    if not text:
        return []

    paras = re.split(r"\n\s*\n+", text)
    paras = [p.strip() for p in paras if p.strip()]

    if len(paras) <= 1:
        sentences = _split_into_sentences(text)
        if len(sentences) <= 5:
            return [" ".join(sentences)]

        chunk_size = 5
        paras = []
        for i in range(0, len(sentences), chunk_size):
            chunk = " ".join(sentences[i: i + chunk_size]).strip()
            if chunk:
                paras.append(chunk)

    return paras


def _count_tokens(text: str, tokenizer: AutoTokenizer) -> int:
    with _lock:
        return len(tokenizer.encode(text, add_special_tokens=False))


def _need_paragraph_mode(total_tokens: int, num_paras: int) -> bool:
    """
    Dùng paragraph-mode nếu:
    - Dài hơn MAX_SOURCE_LEN
    - Hoặc rất nhiều đoạn
    - Hoặc khá dài + nhiều đoạn
    """
    if total_tokens > MAX_SOURCE_LEN:
        return True
    if num_paras >= 10:
        return True
    if total_tokens > 1000 and num_paras >= 5:
        return True
    return False


def _select_paragraphs(paras: List[str], max_paras: int) -> List[str]:
    """Giới hạn số đoạn: ưu tiên 3 head + 5 tail khi nhiều."""
    if len(paras) <= max_paras:
        return paras

    if max_paras >= 8:
        head_count = 3
        tail_count = max_paras - head_count
    else:
        head_count = max_paras // 3
        tail_count = max_paras - head_count

    head = paras[:head_count]
    tail = paras[-tail_count:]
    return head + tail


# ================== NHẬN DIỆN & BỎ DÒNG TÁC GIẢ / CREDIT / BOX TÂM SỰ ==================

def _is_author_line(line: str) -> bool:
    """Nhận diện dòng tác giả / credit dạng ngắn, thường không có số."""
    s = line.strip()
    if not s:
        return False

    lower = s.lower()

    # Dòng kiểu 'Theo AP', 'Theo VnExpress' nếu không có câu văn
    if (" theo " in lower or lower.startswith("theo ")) and not any(
        ch in s for ch in ".?!"
    ):
        return True

    no_paren = re.sub(r"\(.*?\)", "", s).strip()
    if not no_paren or len(no_paren) > 50:
        return False

    words = no_paren.split()
    if not (1 <= len(words) <= 4):
        return False

    if any(any(ch.isdigit() for ch in w) for w in words):
        return False

    cap_count = sum(1 for w in words if w[0].isupper())
    return cap_count >= max(1, len(words) - 1)


def _remove_trailing_author(text: str) -> str:
    """Bỏ các dòng tác giả ở cuối bài (VnExpress...)."""
    lines = text.rstrip().splitlines()
    end = len(lines)

    while end > 0:
        line = lines[end - 1].strip()
        if not line:
            end -= 1
            continue
        if _is_author_line(line):
            end -= 1
            continue
        break

    return "\n".join(lines[:end]).strip()


def _remove_header_noise(text: str, title: Optional[str]) -> str:
    """
    Bỏ phần header Vietnamnet:
    - dòng trùng tiêu đề
    - tên tác giả
    - 'Xem các bài viết của tác giả', 'icon', số rating...
    """
    lines = text.lstrip().splitlines()
    i = 0
    n = len(lines)

    while i < n and not lines[i].strip():
        i += 1

    if title:
        t = title.strip()
        if i < n:
            first = lines[i].strip()
            if first == t or first.startswith(t):
                i += 1
                while i < n and not lines[i].strip():
                    i += 1

    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        lower = s.lower()

        if _is_author_line(s):
            i += 1
            continue

        if "xem các bài viết của tác giả" in lower:
            i += 1
            continue

        if lower == "icon":
            i += 1
            continue

        if s.isdigit() and len(s) <= 2:
            i += 1
            continue

        break

    return "\n".join(lines[i:]).lstrip()


def _remove_trailing_credit_sentence(text: str) -> str:
    """
    Xoá câu credit cuối dạng 'Theo Báo X', 'Theo Y'... (không có dấu phẩy).
    """
    sentences = _split_into_sentences(text)
    if not sentences:
        return text.strip()

    while sentences:
        last = sentences[-1].strip()
        lower = last.lower()

        if lower.startswith("theo "):
            if "," in last:
                break
            if len(last.split()) <= 15:
                sentences.pop()
                continue
        break

    return " ".join(sentences).strip()


def _is_noise_paragraph(text: str) -> bool:
    """
    Nhận diện đoạn noise 
    """
    s = text.strip().lower()
    if not s:
        return False
    return any(pat in s for pat in _NOISE_PARAGRAPH_PATTERNS)


# ================== HẬU XỬ LÝ SUMMARY ==================

def _postprocess_summary(raw_summary: str) -> str:
    """Dọn caption, bỏ tác giả / credit, cắt gọn đến câu cuối hợp lý."""
    s = raw_summary.strip()
    if not s:
        return s
    s = _filter_media_sentences(s)
    s = _remove_trailing_author(s)
    s = _remove_trailing_credit_sentence(s)
    s = _truncate_to_last_sentence(s)
    return s


# ================== GỌI MODEL ==================

def _generate_summary_with_range(
    input_text: str,
    *,
    min_new_tokens: int,
    max_new_tokens: int,
    max_source_len: int = MAX_SOURCE_LEN,
) -> str:
    tokenizer, model = _load_summarizer()

    with _lock:
        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=max_source_len,
            padding=False,
        )

    model_device = next(model.parameters()).device
    inputs = {k: v.to(model_device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            min_new_tokens=int(min_new_tokens),
            max_new_tokens=int(max_new_tokens),
            num_beams=5,  
            length_penalty=0.7,  
            no_repeat_ngram_size=3,
            repetition_penalty=1.1,  
            early_stopping=True,
            do_sample=False,
        )

    with _lock:
        raw_summary = tokenizer.decode(
            output_ids[0],
            skip_special_tokens=True,
        ).strip()

    return _postprocess_summary(raw_summary)


# ================== API CHÍNH ==================

def summarize(title: Optional[str], body: str) -> str:
    
    try:
        if not body or not body.strip():
            return ""

        tokenizer, _ = _load_summarizer()

        body = _remove_trailing_author(body)
        body = _remove_header_noise(body, title)

        raw_paras = _split_into_paragraphs(body)
        cleaned_paras: List[str] = []
        for p in raw_paras:
            if _is_noise_paragraph(p):
                # Bỏ các đoạn "ô xanh" kêu gọi gửi tâm sự, email...
                continue
            p_clean = _filter_media_sentences(p)
            if p_clean.strip():
                cleaned_paras.append(p_clean.strip())

        if cleaned_paras:
            cleaned_body = "\n\n".join(cleaned_paras)
            num_paras = len(cleaned_paras)
        else:
            cleaned_body = _filter_media_sentences(body).strip()
            num_paras = 1

        if not cleaned_body:
            return ""

        total_tokens = _count_tokens(cleaned_body, tokenizer)
        use_paragraph_mode = _need_paragraph_mode(total_tokens, num_paras)

        # -------- SINGLE-PASS --------
        if not use_paragraph_mode:
            full_input = cleaned_body
            min_new, max_new = _estimate_new_token_range(
                cleaned_body,
                num_paras=num_paras,
            )
            return _generate_summary_with_range(
                full_input,
                min_new_tokens=min_new,
                max_new_tokens=max_new,
                max_source_len=MAX_SOURCE_LEN,
            )

        # -------- PARAGRAPH MODE --------
        max_paras = min(num_paras, MAX_PARAS_SUMMARIZED)
        selected_paras = _select_paragraphs(cleaned_paras, max_paras)

        mini_summaries: List[str] = []
        for _, para in enumerate(selected_paras):
            if not para.strip():
                continue

            para_text = para  # chỉ body, không ghép title

            mini_min, mini_max = _estimate_new_token_range(para_text)
            mini_max = min(mini_max, 160)
            if mini_max <= 10:
                mini_min = mini_max
            else:
                mini_min = min(mini_min, mini_max - 10)

            mini_summary = _generate_summary_with_range(
                para_text,
                min_new_tokens=mini_min,
                max_new_tokens=mini_max,
                max_source_len=min(MAX_SOURCE_LEN, 900),
            )
            if mini_summary:
                mini_summaries.append(mini_summary)

        if not mini_summaries:
            full_input = cleaned_body
            min_new, max_new = _estimate_new_token_range(
                cleaned_body,
                num_paras=num_paras,
            )
            return _generate_summary_with_range(
                full_input,
                min_new_tokens=min_new,
                max_new_tokens=max_new,
                max_source_len=MAX_SOURCE_LEN,
            )

        # Ghép mini-summary: ưu tiên đuôi, chỉ giữ 2 head + 3 tail nếu nhiều
        n = len(mini_summaries)
        if n <= 5:
            if n >= 2:
                head_count = max(1, n // 3)
                head_part = mini_summaries[:head_count]
                tail_part = mini_summaries[head_count:]
                ordered_minis = tail_part + head_part
            else:
                ordered_minis = mini_summaries
        else:
            keep_head = min(2, n)
            keep_tail = min(3, n - keep_head)
            head_part = mini_summaries[:keep_head]
            tail_part = mini_summaries[-keep_tail:] if keep_tail > 0 else []
            ordered_minis = tail_part + head_part

        intermediate_text = " ".join(ordered_minis).strip()
        if not intermediate_text:
            return ""

        inter_min, inter_max = _estimate_new_token_range(
            intermediate_text,
            num_paras=num_paras,
        )
        inter_tokens = _count_tokens(intermediate_text, tokenizer)
        if inter_tokens <= inter_max * 1.2:
            return _truncate_to_last_sentence(intermediate_text)

        final_input = intermediate_text  # vẫn chỉ body

        return _generate_summary_with_range(
            final_input,
            min_new_tokens=inter_min,
            max_new_tokens=inter_max,
            max_source_len=MAX_SOURCE_LEN,
        )

    except Exception as e:
        # Return fallback summary on error
        safe = _filter_media_sentences(body.strip())
        safe = _remove_trailing_author(safe)
        safe = _remove_trailing_credit_sentence(safe)
        if len(safe) > 800:
            safe = safe[:800] + "..."
        return safe


def clear_model():
    """Giải phóng model khỏi GPU/CPU memory."""
    global _model, _tokenizer
    if _model is not None:
        del _model
        _model = None
    if _tokenizer is not None:
        del _tokenizer
        _tokenizer = None

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("=== Model cleared from memory ===")
