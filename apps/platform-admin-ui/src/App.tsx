import React, { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AdminLayout } from "./components/AdminLayout";
import { A01ContentModerationPage, A02PlatformOperationsPage } from "./pages/AdminScreens";

export function App() {
  const [toast, setToast] = useState<{ kind: "ok" | "info" | "warn" | "err"; text: string } | null>(null);

  const showToast = (text: string, kind: "ok" | "info" | "warn" | "err" = "ok") => {
    setToast({ kind, text });
    window.setTimeout(() => setToast(null), 3500);
  };

  return (
    <BrowserRouter>
      <AdminLayout toast={toast}>
        <Routes>
          <Route path="/" element={<Navigate to="/a01-content-moderation" replace />} />
          <Route
            path="/a01-content-moderation"
            element={<A01ContentModerationPage showToast={showToast} />}
          />
          <Route
            path="/a02-platform-operations"
            element={<A02PlatformOperationsPage showToast={showToast} />}
          />
        </Routes>
      </AdminLayout>
    </BrowserRouter>
  );
}

export default App;
