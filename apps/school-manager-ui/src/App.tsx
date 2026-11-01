import React, { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ManagerLayout } from "./components/ManagerLayout";
import { M01PublicationReviewPage, M02OrganizationManagementPage } from "./pages/ManagerScreens";

export function App() {
  const [toast, setToast] = useState<{ kind: "ok" | "info" | "warn" | "err"; text: string } | null>(null);

  const showToast = (text: string, kind: "ok" | "info" | "warn" | "err" = "ok") => {
    setToast({ kind, text });
    window.setTimeout(() => setToast(null), 3500);
  };

  return (
    <BrowserRouter>
      <ManagerLayout toast={toast}>
        <Routes>
          <Route path="/" element={<Navigate to="/m01-publication-review" replace />} />
          <Route
            path="/m01-publication-review"
            element={<M01PublicationReviewPage showToast={showToast} />}
          />
          <Route
            path="/m02-organization-management"
            element={<M02OrganizationManagementPage showToast={showToast} />}
          />
        </Routes>
      </ManagerLayout>
    </BrowserRouter>
  );
}

export default App;
