import React from "react";
import NewsFeed from "../components/NewsFeed";
import { Link } from "react-router-dom";
import LOGO from "/LOGO_DHXD.png";

const Home: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = React.useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("theme") !== "light";
    }
    return true;
  });

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("theme", isDarkMode ? "dark" : "light");
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode((prev) => !prev);
  };

  const theme = {
    bg: isDarkMode ? "#020617" : "#f8fafc",
    text: isDarkMode ? "#e5e7eb" : "#0f172a",
    subText: isDarkMode ? "#9ca3af" : "#64748b",
    accent: "#f97316",
    headerBorder: isDarkMode ? "#374151" : "#cbd5e1",
    toggleBg: isDarkMode ? "#020617" : "#ffffff",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: theme.bg,
        color: theme.text,
      }}
    >
      {/* Header đơn giản trên cùng */}
      <header
        style={{
          maxWidth: "1100px",
          margin: "0 auto",
          padding: "16px 12px 0",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <img
            src={LOGO}
            alt="Logo ĐHXD"
            style={{ width: 40, height: 40, borderRadius: "8px" }}
          />
          <div>
            <div
              style={{
                fontWeight: 700,
                fontSize: "16px",
                color: theme.accent,
              }}
            >
              Hệ thống đọc tin nhanh
            </div>
            <div style={{ fontSize: "12px", color: theme.subText }}>
              Khoa CNTT - Trường ĐH Xây dựng Hà Nội
            </div>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <button
            onClick={toggleTheme}
            style={{
              padding: "8px 12px",
              borderRadius: "999px",
              border: `1px solid ${theme.headerBorder}`,
              background: theme.toggleBg,
              color: theme.text,
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            {isDarkMode ? "🌙 Tối" : "☀️ Sáng"}
          </button>

          <Link
            to="/history"
            style={{
              padding: "8px 16px",
              borderRadius: "999px",
              border: "1px solid #f97316",
              color: "#f97316",
              fontSize: "13px",
              textDecoration: "none",
            }}
          >
            Xem lại tin tức
          </Link>
        </div>
      </header>

      {/* Danh sách tin tức */}
      <NewsFeed isDarkMode={isDarkMode} />
    </div>
  );
};

export default Home;
