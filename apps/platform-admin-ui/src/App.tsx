import React from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { TeacherProvider, useTeacher } from "./context/TeacherContext";
import { AdminLayout } from "./components/AdminLayout";
import { WebPortalLoginPage } from "../../shared/WebPortalLoginPage";
import { A01ContentModerationPage, A02PlatformOperationsPage } from "./pages/AdminScreens";
import "../../shared/portal-ui.css";
import "../../shared/ui-primitives.css";

function AdminPortalRoutes() {
  const location = useLocation();
  const { currentRole, isAuthenticated, loginAsRole, logout, showToast } = useTeacher();
  if (isAuthenticated && currentRole !== "ADMIN") {
    return <main className="tw-hero-bg" style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}><section className="tw-card" role="alert"><h1 className="tw-h2">Phiên đăng nhập không thuộc cổng Quản trị</h1><p className="tw-sub">Đăng xuất phiên hiện tại để tiếp tục. Cổng này không hiển thị màn hình của role khác.</p><button type="button" className="tw-btn" onClick={logout}>Đăng xuất và quay lại</button></section></main>;
  }
  if (location.pathname !== "/login" && !isAuthenticated) return <Navigate to="/login" replace />;
  if (location.pathname === "/login" && isAuthenticated) return <Navigate to="/a02-platform-operations" replace />;
  return (
    <Routes>
      <Route path="/" element={<Navigate to={isAuthenticated ? "/a02-platform-operations" : "/login"} replace />} />
      <Route path="/login" element={<WebPortalLoginPage portalRole="ADMIN" onLogin={loginAsRole} />} />
      <Route path="/a01-content-moderation" element={<A01ContentModerationPage showToast={showToast} />} />
      <Route path="/a02-platform-operations" element={<A02PlatformOperationsPage showToast={showToast} />} />
      <Route path="*" element={<Navigate to="/a02-platform-operations" replace />} />
    </Routes>
  );
}

function AdminPortalFrame() {
  const location = useLocation();
  const { toast } = useTeacher();
  const routes = <AdminPortalRoutes />;
  return location.pathname === "/login" ? routes : <AdminLayout toast={toast}>{routes}</AdminLayout>;
}

export function App() {
  return <BrowserRouter><TeacherProvider><AdminPortalFrame /></TeacherProvider></BrowserRouter>;
}

export default App;
