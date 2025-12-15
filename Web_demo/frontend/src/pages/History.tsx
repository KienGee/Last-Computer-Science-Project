import React from "react";
import HistoryView from "../components/HistoryView";

const History: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = React.useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("theme") !== "light";
    }
    return true;
  });

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("theme", isDarkMode ? "dark" : "light");
      // Update body background
      document.body.style.background = isDarkMode ? "#020617" : "#f8fafc";
    }
  }, [isDarkMode]);

  const handleToggleTheme = () => {
    setIsDarkMode((prev) => !prev);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: isDarkMode ? "#020617" : "#f8fafc",
      }}
    >
      <HistoryView
        isDarkMode={isDarkMode}
        onToggleTheme={handleToggleTheme}
      />
    </div>
  );
};

export default History;
