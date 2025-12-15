// src/App.tsx
import React from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Home from "./pages/Home";
import History from "./pages/History";

const AppContent: React.FC = () => {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <>
      {/* Keep Home mounted to continue streaming */}
      <div style={{ display: isHome ? "block" : "none" }}>
        <Home />
      </div>
      {!isHome && <History />}
    </>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
};

export default App;
