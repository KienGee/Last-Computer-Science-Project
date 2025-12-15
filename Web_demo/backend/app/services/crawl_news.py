#\app\services\crawl_news.py
import re, csv, time, ujson, argparse, hashlib, json
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparse

# --------- HTTP ----------
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,vi-VN;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}
TIMEOUT, SLEEP = 15, 0.7
SESSION = requests.Session()

def fetch(url):
    try:
        r = SESSION.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200 and r.text:
            return r.text
    except requests.RequestException:
        pass
    return None

# --------- Nhãn chuẩn ----------
CANON = {
    "chinh-tri": "Chính trị",
    "the-gioi": "Thế giới",
    "kinh-doanh": "Kinh doanh",
    "khoa-hoc-cong-nghe": "Khoa học công nghệ",
    "suc-khoe": "Sức khỏe",
    "the-thao": "Thể thao",
    "giai-tri": "Giải trí",
    "phap-luat": "Pháp luật",
    "giao-duc": "Giáo dục",
    "doi-song": "Đời sống",
    "du-lich": "Du lịch",
}


PATTERNS = {
    "chinh-tri": {
        "vnexpress": "https://vnexpress.net/thoi-su/chinh-tri-p{page}",
        "vietnamnet": "https://vietnamnet.vn/chinh-tri-page{page}",
    },
    "the-gioi": {
        "vnexpress": "https://vnexpress.net/the-gioi-p{page}",
        "vietnamnet": "https://vietnamnet.vn/the-gioi-page{page}",
    },
    "kinh-doanh": {
        "vnexpress": "https://vnexpress.net/kinh-doanh-p{page}",
        "vietnamnet": "https://vietnamnet.vn/kinh-doanh-page{page}",
    },
    "khoa-hoc-cong-nghe": {
        "vnexpress": "https://vnexpress.net/khoa-hoc-cong-nghe-p{page}",
        "vietnamnet": "https://vietnamnet.vn/cong-nghe-page{page}",
    },
    "suc-khoe": {
        "vnexpress": "https://vnexpress.net/suc-khoe-p{page}",
        "vietnamnet": "https://vietnamnet.vn/suc-khoe-page{page}",
    },
    "the-thao": {
        "vnexpress": "https://vnexpress.net/the-thao-p{page}",
        "vietnamnet": "https://vietnamnet.vn/the-thao-page{page}",
    },
    "giai-tri": {
        "vnexpress": "https://vnexpress.net/giai-tri-p{page}",
        "vietnamnet": "https://vietnamnet.vn/van-hoa-giai-tri-page{page}",
    },
    "phap-luat": {
        "vnexpress": "https://vnexpress.net/phap-luat-p{page}",
        "vietnamnet": "https://vietnamnet.vn/phap-luat-page{page}",
    },
    "giao-duc": {
        "vnexpress": "https://vnexpress.net/giao-duc-p{page}",
        "vietnamnet": "https://vietnamnet.vn/giao-duc-page{page}",
    },
    "doi-song": {
        "vnexpress": "https://vnexpress.net/doi-song-p{page}",
        "vietnamnet": "https://vietnamnet.vn/doi-song-page{page}",
    },
    "du-lich": {
        "vnexpress": "https://vnexpress.net/du-lich-p{page}",
        "vietnamnet": "https://vietnamnet.vn/du-lich-page{page}",
    },
}

# --------- CSS selector trang danh mục ----------
LIST_SELECTORS = {
    "vnexpress": [
        ("h3.title-news a", "title"),
        ("article.item-news h3 a", "title"),
        ("h2 a", "title"),
    ],
    "vietnamnet": [
        ("h2 a","title"),
        ("h3 a","title"),
        (".maincontent .title a","title"),
        (".content-item .title a","title"),
    ],
}

# --------- Utils ----------
def base_from(any_url):
    sp = urlsplit(any_url)
    return f"{sp.scheme}://{sp.netloc}"

def build_list_url(pattern, page: int) -> str:
    return pattern.format(page=page)

def norm(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.replace("’","'").replace("“",'"').replace("”",'"')

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()

def parse_dt_vi(raw: str) -> str:
    if not raw: return ""
    s = raw.strip()
    s = re.sub(r"^(Thứ\s+\w+|Chủ\s*nhật)\s*,\s*", "", s, flags=re.IGNORECASE)
    s = s.replace(" - ", " ")
    try:
        return dtparse.parse(s, dayfirst=True, fuzzy=True).isoformat()
    except Exception:
        return ""

def write_jsonl(path, rows):
    with open(path,"w",encoding="utf-8") as f:
        for r in rows: f.write(ujson.dumps(r, ensure_ascii=False)+"\n")

def write_csv(path, rows):
    with open(path,"w",encoding="utf-8-sig",newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "title","lead","body","url","subject","published_at","source","original_subject"
        ])
        w.writeheader()
        for r in rows: w.writerow(r)

def extract_pairs(html, selectors):
    soup = BeautifulSoup(html, "lxml")
    seen, out = set(), []
    for sel, mode in selectors:
        for a in soup.select(sel):
            href = a.get("href")
            if not href: continue
            t = a.get(mode) if mode in ("title","aria-label") else a.get_text(" ")
            t = norm(t)
            if not t: continue
            key = (t, href)
            if key in seen: continue
            seen.add(key); out.append((t, href))
    return out

# --------- Extractors ----------
def extract_article_vne(html):
    s = BeautifulSoup(html,"lxml")
    # title
    title = None
    for sel in ["h1.title-detail","h1","h2.title-detail"]:
        el = s.select_one(sel)
        if el and el.get_text(strip=True):
            title = norm(el.get_text(" ", strip=True)); break
    # lead
    lead = None
    for sel in ["p.description","p.lead",".sapo",".short_intro"]:
        el = s.select_one(sel)
        if el and el.get_text(strip=True):
            lead = norm(el.get_text(" ", strip=True)); break
    # body
    body_parts = []
    for sel in ["article.fck_detail p","div.fck_detail p","article p"]:
        for p in s.select(sel):
            t = norm(p.get_text(" ", strip=True))
            if len(t) >= 5 and not t.lower().startswith(("xem thêm:","video:","ảnh:")):
                body_parts.append(t)
        if body_parts: break
    body = " ".join(body_parts)

    # published_at
    pub = ""
    
    for sel in [".date-time", ".date", ".time"]:
        el = s.select_one(sel)
        if el and el.get_text(strip=True):
            pub = norm(el.get_text(" ", strip=True))
            break

    # fallback: nếu không tìm được chuỗi text thì dùng meta/time và parse sang ISO
    if not pub:
        for sel in ["time[datetime]", "meta[property='article:published_time']", "time"]:
            el = s.select_one(sel)
            if el:
                raw = el.get("datetime") or el.get("content") or el.get_text(" ", strip=True)
                pub = parse_dt_vi(raw)   # hàm cũ, trả ISO
                if pub:
                    break

    return title or "", lead or "", body or "", pub or ""


def extract_article_vnn(html):
    s = BeautifulSoup(html,"lxml")

    def _clean(x): 
        x = (x or "").strip()
        return re.sub(r"\s+"," ", x)

    def _lead_ok(x, lo=20, hi=300):
        if not x: return False
        n = len(x); return lo <= n <= hi

    # title
    title = None
    for sel in ["h1.content-detail-title","h1.title","h1"]:
        el = s.select_one(sel)
        if el and el.get_text(strip=True):
            title = _clean(el.get_text(" ", strip=True)); break

    # body
    body_parts = []
    for sel in ["article p",".ArticleContent p",".content-detail p",".maincontent p",".article__body p"]:
        for p in s.select(sel):
            t = _clean(p.get_text(" ", strip=True))
            if len(t) >= 5 and not t.lower().startswith(("ảnh:", "video:", "xem thêm:")):
                body_parts.append(t)
        if body_parts: break
    body = " ".join(body_parts)

    # lead 
    lead = None
    for sel in [
        ".content-detail-sapo",       
        "h2.content-detail-sapo",
        ".sapo","h2.sapo","p.sapo",
        ".article__sapo",".content-detail .lead",".maincontent .lead",
        ".bold-text",".summary",".post-sapo",
    ]:
        el = s.select_one(sel)
        if el and el.get_text(strip=True):
            cand = _clean(el.get_text(" ", strip=True))
            if _lead_ok(cand): 
                lead = cand; break

    if not lead:
        # meta
        for sel in [
            'meta[property="og:description"]',
            'meta[name="description"]',
            'meta[name="twitter:description"]',
        ]:
            el = s.select_one(sel)
            if el and el.get("content"):
                cand = _clean(el.get("content"))
                if _lead_ok(cand):
                    lead = cand; break

    if not lead:
        # JSON-LD
        for js in s.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(js.string)
                if isinstance(data, dict) and data.get("description"):
                    cand = _clean(data["description"])
                    if _lead_ok(cand):
                        lead = cand; break
            except Exception:
                pass

    if not lead and body:
        # Lấy 1–2 câu đầu của body
        sents = re.split(r'(?<=[.!?…])\s+|\n+', body)
        cand = " ".join(sents[:2]).strip()
        if not _lead_ok(cand):
            cand = sents[0].strip() if sents else ""
        lead = cand

    # published_at
    pub = ""
    for sel in [
        ".bread-crumb-detail__time",
        ".bread-crumbs__time",
        ".time-share",
        "time[datetime]",
        "meta[property='article:published_time']",
        "time",".date"
    ]:
        el = s.select_one(sel)
        if el:
            raw = el.get("datetime") or el.get("content") or el.get_text(" ", strip=True)
            x = (raw or "").strip()
            x = re.sub(r"^(Thứ\s+\w+|Chủ\s*nhật)\s*,\s*", "", x, flags=re.I)
            x = x.replace(" - ", " ")
            try:
                pub = dtparse.parse(x, dayfirst=True, fuzzy=True).isoformat()
            except:
                pub = ""
            if pub: break

    return title or "", lead or "", body or "", pub or ""

# --------- Crawl 1 subject x 1 site ----------
def crawl_subject(site, subject_slug, pattern, list_selectors, pages,
                  seen_title, seen_bhash, max_items=None):

    subject_display = CANON[subject_slug]
    results = []

    for page in range(1, pages+1):
        if max_items is not None and len(results) >= max_items:
            break

        url = build_list_url(pattern, page)
        html = fetch(url)
        if not html:
            print(f"[{site}:{subject_slug}] page {page}: lỗi tải"); time.sleep(SLEEP); continue

        pairs = extract_pairs(html, list_selectors)
        if not pairs:
            print(f"[{site}:{subject_slug}] page {page}: 0 link → dừng")
            break

        base = base_from(url)
        added = 0
        for _, href in pairs:
            if max_items is not None and len(results) >= max_items:
                break

            art = href if href.startswith("http") else urljoin(base, href)
            ahtml = fetch(art)
            if not ahtml: 
                continue

            if site == "vnexpress":
                t,l,b,pub = extract_article_vne(ahtml)
            else:
                t,l,b,pub = extract_article_vnn(ahtml)

            if not t or not b or len(b) < 200:
                continue

            tkey = norm(t).lower()
            bkey = sha1(norm(b))
            if tkey in seen_title or bkey in seen_bhash:
                continue

            seen_title.add(tkey); seen_bhash.add(bkey)
            results.append({
                "title": t,
                "lead": l or "",
                "body": b,
                "url": art,
                "subject": subject_display,
                "published_at": pub or "",
                "source": site,
                "original_subject": subject_display,
            })
            added += 1
            time.sleep(SLEEP/2)

        print(f"[{site}:{subject_slug}] page {page}: +{added} (subj total {len(results)})")
        time.sleep(SLEEP)

        if added == 0:
            print(f"[{site}:{subject_slug}] page {page}: không thêm mới → dừng")
            break

    return results


# --------- Main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_jsonl", default="data.jsonl")
    ap.add_argument("--out_csv",   default="data.csv")
    ap.add_argument("--pages_per_cat", type=int, default=20)
    args = ap.parse_args()

    all_rows, seen_title, seen_bhash = [], set(), set()
    SITES = [("vnexpress", LIST_SELECTORS["vnexpress"]),
             ("vietnamnet", LIST_SELECTORS["vietnamnet"])]

    for subject_slug in CANON.keys():
        for site, list_sels in SITES:
            pattern = PATTERNS.get(subject_slug, {}).get(site)
            if not pattern:
                continue
            rows = crawl_subject(site, subject_slug, pattern, list_sels,
                     args.pages_per_cat, seen_title, seen_bhash, max_items=None)

            all_rows.extend(rows)

    print(f"[SUMMARY] Tổng: {len(all_rows)} bài (unique theo title & body, body>=200).")
    write_jsonl(args.out_jsonl, all_rows)
    write_csv(args.out_csv, all_rows)
    print(f"- JSONL: {args.out_jsonl}\n- CSV  : {args.out_csv}")

if __name__ == "__main__":
    main()

#python crawl_news.py --pages_per_cat 20 --out_jsonl data.jsonl --out_csv data.csv