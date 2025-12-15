import React, { useEffect, useState } from "react";
import { http } from "../api/http";
import { Link } from "react-router-dom";
import type { CrawledNews } from "../types/news";

interface HistoryViewProps {
  isDarkMode?: boolean;
  onToggleTheme?: () => void;
}

const HistoryView: React.FC<HistoryViewProps> = ({
  isDarkMode: isDarkModeProp,
  onToggleTheme,
}) => {
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [news, setNews] = useState<CrawledNews[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [internalDarkMode, setInternalDarkMode] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("theme") !== "light";
    }
    return true;
  });

  const isDarkMode =
    isDarkModeProp !== undefined ? isDarkModeProp : internalDarkMode;

  const handleToggleTheme = () => {
    if (onToggleTheme) {
      onToggleTheme();
    } else {
      setInternalDarkMode((prev) => {
        const next = !prev;
        if (typeof window !== "undefined") {
          localStorage.setItem("theme", next ? "dark" : "light");
        }
        return next;
      });
    }
  };

  const theme = {
    bg: isDarkMode ? "#020617" : "#f8fafc",
    cardBg: isDarkMode ? "#020617" : "#ffffff",
    border: isDarkMode ? "#1f2937" : "#e2e8f0",
    text: isDarkMode ? "#f9fafb" : "#0f172a",
    textSecondary: isDarkMode ? "#e5e7eb" : "#475569",
    textMuted: isDarkMode ? "#9ca3af" : "#6b7280",
    inputBg: isDarkMode ? "#020617" : "#ffffff",
    inputBorder: isDarkMode ? "#374151" : "#cbd5e1",
    badgeCategory: isDarkMode ? "#fbbf24" : "#92400e",
    link: isDarkMode ? "#fb923c" : "#ea580c",
  };

  // Lấy danh sách các ngày có tin
  const fetchDates = async () => {
    try {
      const res = await http.get<{ dates: string[] }>(
        "/api/v1/news/available_dates"
      );
      setAvailableDates(res.data.dates);
      if (res.data.dates.length > 0) {
        setSelectedDate(res.data.dates[0]); // ngày mới nhất
      }
    } catch (err) {
      console.error("Failed to fetch dates:", err);
    }
  };

  useEffect(() => {
    fetchDates();
  }, []);

  // Update body background theo theme
  useEffect(() => {
    if (typeof window !== "undefined") {
      document.body.style.background = isDarkMode ? "#020617" : "#f8fafc";
    }
  }, [isDarkMode]);

  // Lấy tin theo ngày được chọn
  const fetchNews = async () => {
    if (!selectedDate) return;
    try {
      setIsLoading(true);
      setError(null);
      const res = await http.get<CrawledNews[]>(
        `/api/v1/news/by_date?date=${selectedDate}`
      );
      setNews(res.data);
    } catch (err: any) {
      console.error(err);
      setError("Không tải được tin tức.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, [selectedDate]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("vi-VN", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <section
      style={{
        maxWidth: "1100px",
        margin: "24px auto 40px",
        padding: "0 12px 24px",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "16px",
        }}
      >
        <h2
          style={{
            fontSize: "20px",
            fontWeight: 600,
            color: theme.text,
          }}
        >
          Xem lại tin tức các ngày trước
        </h2>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <button
            onClick={handleToggleTheme}
            style={{
              padding: "8px 12px",
              borderRadius: "999px",
              border: `1px solid ${theme.inputBorder}`,
              background: theme.cardBg,
              color: theme.text,
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            {isDarkMode ? "🌙 Tối" : "☀️ Sáng"}
          </button>

          <Link
            to="/"
            style={{
              padding: "8px 16px",
              borderRadius: "999px",
              border: `1px solid ${theme.inputBorder}`,
              color: theme.text,
              fontSize: "13px",
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            ← Quay lại
          </Link>
        </div>
      </div>

      {/* Dropdown chọn ngày */}
      <div style={{ marginBottom: "20px" }}>
        <label
          style={{
            display: "block",
            fontSize: "14px",
            color: theme.textMuted,
            marginBottom: "8px",
          }}
        >
          Chọn ngày:
        </label>
        <select
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          style={{
            padding: "8px 12px",
            borderRadius: "8px",
            border: `1px solid ${theme.inputBorder}`,
            background: theme.inputBg,
            color: theme.text,
            fontSize: "14px",
            minWidth: "250px",
          }}
        >
          {availableDates.map((date) => (
            <option key={date} value={date}>
              {formatDate(date)}
            </option>
          ))}
        </select>
      </div>

      {error && <p style={{ color: "#f97316", marginBottom: "8px" }}>{error}</p>}

      {isLoading && (
        <p style={{ color: theme.textMuted, fontStyle: "italic" }}>
          Đang tải...
        </p>
      )}

      {!isLoading && news.length === 0 && (
        <p style={{ color: theme.textMuted, fontStyle: "italic" }}>
          Không có tin tức trong ngày này.
        </p>
      )}

      {/* Danh sách tin */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {news.map((item, idx) => (
          <article
            key={`${item.source}-${idx}-${item.url ?? ""}`}
            style={{
              background: theme.cardBg,
              borderRadius: "12px",
              padding: "16px 20px",
              border: `1px solid ${theme.border}`,
              boxShadow: isDarkMode ? "none" : "0 1px 3px rgba(0,0,0,0.1)",
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
    </section>
  );
};

export default HistoryView;
