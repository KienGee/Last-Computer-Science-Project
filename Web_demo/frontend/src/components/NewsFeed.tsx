import React, { useEffect, useMemo, useState } from "react";
import type { CrawledNews } from "../types/news";

type CategoryKey =
  | "all"
  | "Chính trị"
  | "Thế giới"
  | "Giáo dục"
  | "Giải trí"
  | "Khoa học công nghệ"
  | "Kinh doanh"
  | "Pháp luật"
  | "Sức khỏe"
  | "Du lịch"
  | "Thể thao"
  | "Đời sống";

const CATEGORY_TABS: { key: CategoryKey; label: string }[] = [
  { key: "all", label: "Tất cả" },
  { key: "Chính trị", label: "Chính trị" },
  { key: "Thế giới", label: "Thế giới" },
  { key: "Giáo dục", label: "Giáo dục" },
  { key: "Giải trí", label: "Giải trí" },
  { key: "Khoa học công nghệ", label: "Khoa học công nghệ" },
  { key: "Kinh doanh", label: "Kinh doanh" },
  { key: "Pháp luật", label: "Pháp luật" },
  { key: "Sức khỏe", label: "Sức khỏe" },
  { key: "Du lịch", label: "Du lịch" },
  { key: "Thể thao", label: "Thể thao" },
  { key: "Đời sống", label: "Đời sống" },
];

const CACHE_KEY = "fastnews_daily_cache_v1";
const PAGE_SIZE = 10; // Số bài trên mỗi trang

interface NewsCache {
  date: string; // yyyy-mm-dd
  items: CrawledNews[];
}

interface NewsFeedProps {
  isDarkMode?: boolean;
}

const getTodayDateKey = () => new Date().toISOString().slice(0, 10);

/**
 * Lấy danh sách các chủ đề (dùng cho filter theo tab).
 * Category được lấy từ URL, không còn dùng model phân loại.
 */
const getCategoriesForNews = (item: CrawledNews): string[] => {
  const category = item.category?.trim();
  return category ? [category] : [];
};

const NewsFeed: React.FC<NewsFeedProps> = ({ isDarkMode: isDarkModeProp }) => {
  const isDarkMode =
    isDarkModeProp ??
    (typeof window !== "undefined"
      ? localStorage.getItem("theme") !== "light"
      : true);

  const theme = {
    bg: isDarkMode ? "#020617" : "#f8fafc",
    cardBg: isDarkMode ? "#020617" : "#ffffff",
    border: isDarkMode ? "#1f2937" : "#e2e8f0",
    text: isDarkMode ? "#f9fafb" : "#0f172a",
    textSecondary: isDarkMode ? "#e5e7eb" : "#475569",
    textMuted: isDarkMode ? "#9ca3af" : "#6b7280",
    inputBg: isDarkMode ? "#020617" : "#ffffff",
    inputBorder: isDarkMode ? "#374151" : "#cbd5e1",
    chipActiveBg: isDarkMode ? "#111827" : "#fff7ed",
    chipActiveBorder: isDarkMode ? "#f97316" : "#fdba74",
    chipActiveText: isDarkMode ? "#f97316" : "#c2410c",
    chipBorder: isDarkMode ? "#374151" : "#cbd5e1",
    chipText: isDarkMode ? "#e5e7eb" : "#334155",
    badgeCategory: isDarkMode ? "#fbbf24" : "#92400e",
    link: isDarkMode ? "#fb923c" : "#ea580c",
    paginationBg: isDarkMode ? "#020617" : "#ffffff",
    paginationBgCurrent: isDarkMode ? "#111827" : "#fee2e2",
    paginationBorder: isDarkMode ? "#374151" : "#cbd5e1",
    paginationBorderCurrent: "#f97316",
    paginationText: isDarkMode ? "#e5e7eb" : "#0f172a",
    paginationTextCurrent: isDarkMode ? "#f97316" : "#b91c1c",
    paginationBgDisabled: isDarkMode ? "#111827" : "#e5e7eb",
    paginationTextDisabled: isDarkMode ? "#9ca3af" : "#94a3b8",
    modalBg: isDarkMode ? "#020617" : "#ffffff",
  };

  const [news, setNews] = useState<CrawledNews[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [selectedCategories, setSelectedCategories] = useState<Set<CategoryKey>>(
    new Set(["all"])
  );
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSources, setSelectedSources] = useState<{
    vnexpress: boolean;
    vietnamnet: boolean;
  }>({
    vnexpress: true,
    vietnamnet: true,
  });

  const [currentPage, setCurrentPage] = useState(1);

  const [selectedNewsItem, setSelectedNewsItem] = useState<CrawledNews | null>(
    null
  );

  const openModal = (item: CrawledNews) => {
    setSelectedNewsItem(item);
    if (typeof document !== "undefined") {
      document.body.style.overflow = "hidden";
    }
  };

  const closeModal = () => {
    setSelectedNewsItem(null);
    if (typeof document !== "undefined") {
      document.body.style.overflow = "";
    }
  };

  useEffect(() => {
    return () => {
      if (typeof document !== "undefined") {
        document.body.style.overflow = "";
      }
    };
  }, []);

  const toggleCategory = (key: CategoryKey) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);

      if (key === "all") {
        setCurrentPage(1);
        return new Set(["all"]);
      }

      next.delete("all");

      if (next.has(key)) {
        next.delete(key);
        if (next.size === 0) {
          next.add("all");
        }
      } else {
        next.add(key);
      }

      setCurrentPage(1);
      return next;
    });
  };

  const saveCache = (items: CrawledNews[]) => {
    try {
      const payload: NewsCache = {
        date: getTodayDateKey(),
        items,
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(payload));
    } catch {
      // ignore
    }
  };

  const loadCache = (): CrawledNews[] | null => {
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return null;

      const parsed = JSON.parse(raw) as NewsCache;
      if (!parsed || parsed.date !== getTodayDateKey()) return null;
      if (!Array.isArray(parsed.items)) return null;

      return parsed.items;
    } catch {
      return null;
    }
  };

  const fetchNews = async (loadFromDB: boolean = true, append: boolean = false) => {
    try {
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);

      const enabledSources = Object.entries(selectedSources)
        .filter(([, v]) => v)
        .map(([k]) => k);

      const sourcesToSend =
        enabledSources.length > 0 ? enabledSources : ["vnexpress", "vietnamnet"];

      const res = await fetch(
        "http://localhost:8000/api/v1/news/crawl_today_stream",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            sources: sourcesToSend,
            limit: 999,
            force_new: !loadFromDB, // false = load từ DB, true = crawl web
            force_refresh: false, // Luôn dùng cache DB sau lần đầu
          }),
        }
      );

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      if (!res.body) {
        setError("Không nhận được dữ liệu stream.");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let addedCount = 0;

      // Luôn check duplicate để tránh thêm bài trùng
      const existingKeys = new Set(news.map((n) => n.url || `${n.source}__${n.title}`));

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          try {
            const item = JSON.parse(trimmed) as CrawledNews;
            const key = item.url || `${item.source}__${item.title}`;
            
            // Check duplicate trong existingKeys
            if (existingKeys.has(key)) continue;
            existingKeys.add(key);

            setNews((prev) => {
              // Double check: không thêm nếu đã có trong state
              const alreadyExists = prev.some(
                (n) => (n.url && n.url === item.url) || 
                       (!n.url && !item.url && n.title === item.title && n.source === item.source)
              );
              if (alreadyExists) return prev;
              
              const updated = [item, ...prev];
              // Không save cache ở đây để tránh write quá nhiều lần
              return updated;
            });

            addedCount++;
          } catch (e) {
            console.error("Parse chunk error:", e, trimmed);
          }
        }
      }

      const last = buffer.trim();
      if (last) {
        try {
          const item = JSON.parse(last) as CrawledNews;
          const key = item.url || `${item.source}__${item.title}`;
          if (!existingKeys.has(key)) {
            existingKeys.add(key);
            setNews((prev) => {
              // Double check: không thêm nếu đã có trong state
              const alreadyExists = prev.some(
                (n) => (n.url && n.url === item.url) || 
                       (!n.url && !item.url && n.title === item.title && n.source === item.source)
              );
              if (alreadyExists) return prev;
              
              const updated = [item, ...prev];
              // Không save cache ở đây để tránh write quá nhiều lần
              return updated;
            });
            addedCount++;
          }
        } catch (e) {
          console.error("Parse last chunk error:", e, last);
        }
      }

      // Save cache 1 lần sau khi hoàn tất tất cả items
      setNews((prev) => {
        saveCache(prev);
        return prev;
      });

      if (append) {
        if (addedCount > 0) {
          setSuccessMessage(`Đã thêm ${addedCount} bài mới`);
        } else {
          setSuccessMessage("Không có bài mới (có thể bài đã tồn tại)");
        }
        setTimeout(() => setSuccessMessage(null), 5000);
      }
    } catch (err: any) {
      console.error(err);
      setError("Không tải được tin tức. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const cached = loadCache();
    if (cached && cached.length > 0) {
      setNews(cached);
      return;
    }

    // Không có cache → load từ DB trước
    fetchNews(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedSources, searchTerm, selectedCategories]);

  const filteredNews = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    return news.filter((item) => {
      const srcKey = (item.source || "").toLowerCase();
      if (srcKey === "vnexpress" && !selectedSources.vnexpress) return false;
      if (srcKey === "vietnamnet" && !selectedSources.vietnamnet) return false;

      if (!selectedCategories.has("all")) {
        const cats = getCategoriesForNews(item);
        const hasMatch = cats.some((c) =>
          selectedCategories.has(c as CategoryKey)
        );
        if (!hasMatch) return false;
      }

      if (term) {
        const combined =
          (item.title || "") +
          " " +
          (item.summary || "") +
          " " +
          (item.body || "");
        if (!combined.toLowerCase().includes(term)) return false;
      }

      return true;
    });
  }, [news, selectedCategories, selectedSources, searchTerm]);

  const totalPages =
    filteredNews.length === 0
      ? 1
      : Math.ceil(filteredNews.length / PAGE_SIZE);

  const currentPageSafe = Math.min(currentPage, totalPages);
  const startIndex = (currentPageSafe - 1) * PAGE_SIZE;
  const paginatedNews = filteredNews.slice(
    startIndex,
    startIndex + PAGE_SIZE
  );

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <section
      style={{
        maxWidth: "1100px",
        margin: "24px auto 40px",
        padding: "0 12px 24px",
      }}
    >
      {/* Header + nút làm mới */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "12px",
        }}
      >
        <h2
          style={{
            fontSize: "20px",
            fontWeight: 600,
            color: theme.text,
          }}
        >
          Tin tức gần đây
        </h2>
        <button
          onClick={() => fetchNews(false, true)}
          disabled={isLoading}
          style={{
            padding: "6px 16px",
            borderRadius: "999px",
            border: "none",
            background:
              "linear-gradient(90deg,rgba(249,115,22,1),rgba(251,146,60,1))",
            color: "#fff",
            fontSize: "14px",
            fontWeight: 500,
            cursor: isLoading ? "not-allowed" : "pointer",
          }}
        >
          {isLoading ? "Đang tải..." : "Làm mới"}
        </button>
      </div>

      {/* Tabs chủ đề */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "8px",
          marginBottom: "12px",
        }}
      >
        {CATEGORY_TABS.map((tab) => {
          const isActive = selectedCategories.has(tab.key);
          return (
            <button
              key={tab.key}
              onClick={() => toggleCategory(tab.key)}
              style={{
                padding: "6px 12px",
                borderRadius: "999px",
                border: isActive
                  ? `1px solid ${theme.chipActiveBorder}`
                  : `1px solid ${theme.chipBorder}`,
                background: isActive ? theme.chipActiveBg : "transparent",
                color: isActive ? theme.chipActiveText : theme.chipText,
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Search + nguồn */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "8px",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <input
          type="text"
          placeholder="Tìm theo tiêu đề, nội dung..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            flex: "1 1 260px",
            minWidth: "220px",
            padding: "8px 12px",
            borderRadius: "999px",
            border: `1px solid ${theme.inputBorder}`,
            background: theme.inputBg,
            color: theme.text,
            outline: "none",
            fontSize: "13px",
          }}
        />

        <div
          style={{
            display: "flex",
            gap: "12px",
            alignItems: "center",
            fontSize: "13px",
            color: theme.text,
          }}
        >
          <span style={{ color: theme.textMuted }}>Nguồn:</span>
          <label style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <input
              type="checkbox"
              checked={selectedSources.vnexpress}
              onChange={(e) =>
                setSelectedSources((prev) => ({
                  ...prev,
                  vnexpress: e.target.checked,
                }))
              }
            />
            VnExpress
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <input
              type="checkbox"
              checked={selectedSources.vietnamnet}
              onChange={(e) =>
                setSelectedSources((prev) => ({
                  ...prev,
                  vietnamnet: e.target.checked,
                }))
              }
            />
            Vietnamnet
          </label>
        </div>
      </div>

      {error && (
        <p style={{ color: "#f97316", marginBottom: "8px" }}>{error}</p>
      )}

      {successMessage && (
        <p style={{ color: "#10b981", marginBottom: "8px" }}>
          {successMessage}
        </p>
      )}

      {news.length === 0 && isLoading && !error && (
        <p style={{ color: theme.textMuted, fontStyle: "italic" }}>
          Đang tải tin tức...
        </p>
      )}

      {filteredNews.length === 0 && !isLoading && !error && news.length > 0 && (
        <p style={{ color: theme.textMuted, fontStyle: "italic" }}>
          Không có bài viết phù hợp với bộ lọc hiện tại.
        </p>
      )}

      {/* Danh sách bài trên trang hiện tại */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {paginatedNews.map((item, idx) => (
          <article
            key={`${item.source}-${startIndex + idx}-${item.url ?? ""}`}
            onClick={() => openModal(item)}
            style={{
              background: theme.cardBg,
              borderRadius: "12px",
              padding: "16px 20px",
              border: `1px solid ${theme.border}`,
              cursor: "pointer",
            }}
          >
            <h3
              style={{
                fontSize: "16px",
                fontWeight: 600,
                marginBottom: "4px",
                color: theme.text,
              }}
            >
              {item.title}
            </h3>

            <p
              style={{
                fontSize: "12px",
                color: theme.textMuted,
                marginBottom: "10px",
              }}
            >
              <span style={{ fontWeight: 500 }}>{item.source}</span>
              {item.published_at && <> • {item.published_at}</>}
            </p>

            <p
              style={{
                fontSize: "14px",
                color: theme.textSecondary,
                marginBottom: "10px",
                lineHeight: 1.5,
              }}
            >
              {item.summary || item.body.slice(0, 260).trim() + "..."}
            </p>

            <p
              style={{
                fontSize: "13px",
                color: theme.badgeCategory,
                marginBottom: "6px",
              }}
            >
              Chủ đề: {item.category || "Không xác định"}
            </p>

            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                style={{
                  display: "inline-block",
                  fontSize: "13px",
                  color: theme.link,
                  textDecoration: "none",
                }}
              >
                Đọc toàn bộ bài →
              </a>
            )}
          </article>
        ))}
      </div>

      {/* Thanh pagination */}
      {filteredNews.length > 0 && (
        <div
          style={{
            marginTop: "20px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: "8px",
            flexWrap: "wrap",
          }}
        >
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPageSafe === 1}
            style={{
              padding: "6px 10px",
              borderRadius: "999px",
              border: `1px solid ${theme.paginationBorder}`,
              background:
                currentPageSafe === 1
                  ? theme.paginationBgDisabled
                  : theme.paginationBg,
              color:
                currentPageSafe === 1
                  ? theme.paginationTextDisabled
                  : theme.paginationText,
              fontSize: "13px",
              cursor: currentPageSafe === 1 ? "not-allowed" : "pointer",
            }}
          >
            Trang trước
          </button>

          {pages.map((p) => (
            <button
              key={p}
              onClick={() => setCurrentPage(p)}
              style={{
                padding: "6px 10px",
                borderRadius: "999px",
                border:
                  p === currentPageSafe
                    ? `1px solid ${theme.paginationBorderCurrent}`
                    : `1px solid ${theme.paginationBorder}`,
                background:
                  p === currentPageSafe
                    ? theme.paginationBgCurrent
                    : theme.paginationBg,
                color:
                  p === currentPageSafe
                    ? theme.paginationTextCurrent
                    : theme.paginationText,
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              {p}
            </button>
          ))}

          <button
            onClick={() =>
              setCurrentPage((p) => Math.min(totalPages, p + 1))
            }
            disabled={currentPageSafe === totalPages}
            style={{
              padding: "6px 10px",
              borderRadius: "999px",
              border: `1px solid ${theme.paginationBorder}`,
              background:
                currentPageSafe === totalPages
                  ? theme.paginationBgDisabled
                  : theme.paginationBg,
              color:
                currentPageSafe === totalPages
                  ? theme.paginationTextDisabled
                  : theme.paginationText,
              fontSize: "13px",
              cursor:
                currentPageSafe === totalPages ? "not-allowed" : "pointer",
            }}
          >
            Trang sau
          </button>
        </div>
      )}

      {/* Modal chi tiết */}
      {selectedNewsItem && (
        <div
          onClick={closeModal}
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(15,23,42,0.7)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 50,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "min(900px, 95vw)",
              background: theme.modalBg,
              borderRadius: "16px",
              border: `1px solid ${theme.border}`,
              padding: "20px 24px",
              boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "12px",
                marginBottom: "8px",
              }}
            >
              <h3
                style={{
                  fontSize: "18px",
                  fontWeight: 600,
                  color: theme.text,
                  flex: 1,
                }}
              >
                {selectedNewsItem.title}
              </h3>
              <button
                onClick={closeModal}
                style={{
                  border: "none",
                  background: "transparent",
                  color: theme.textMuted,
                  cursor: "pointer",
                  fontSize: "20px",
                  lineHeight: 1,
                }}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <p
              style={{
                fontSize: "12px",
                color: theme.textMuted,
                marginBottom: "12px",
              }}
            >
              <span style={{ fontWeight: 500 }}>
                {selectedNewsItem.source}
              </span>
              {selectedNewsItem.published_at && (
                <> • {selectedNewsItem.published_at}</>
              )}
            </p>

            <p
              style={{
                fontSize: "15px",
                color: theme.textSecondary,
                marginBottom: "12px",
                lineHeight: 1.6,
              }}
            >
              {selectedNewsItem.summary ||
                (selectedNewsItem.body.length > 400
                  ? selectedNewsItem.body.slice(0, 400).trim() + "..."
                  : selectedNewsItem.body)}
            </p>

            <p
              style={{
                fontSize: "13px",
                color: theme.badgeCategory,
                marginBottom: "10px",
              }}
            >
              Chủ đề: {selectedNewsItem.category || "Không xác định"}
            </p>

            {selectedNewsItem.url && (
              <a
                href={selectedNewsItem.url}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: "inline-block",
                  fontSize: "13px",
                  color: theme.link,
                  textDecoration: "none",
                  marginRight: "12px",
                }}
              >
                Đọc toàn bộ bài →
              </a>
            )}

            <button
              onClick={closeModal}
              style={{
                padding: "6px 16px",
                borderRadius: "999px",
                border: `1px solid ${theme.inputBorder}`,
                background: theme.cardBg,
                color: theme.text,
                fontSize: "13px",
                cursor: "pointer",
                float: "right",
              }}
            >
              Đóng
            </button>
          </div>
        </div>
      )}
    </section>
  );
};

export default NewsFeed;
