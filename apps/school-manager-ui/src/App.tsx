import React from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { TeacherProvider, useTeacher } from "./context/TeacherContext";
import { ManagerLayout } from "./components/ManagerLayout";
import { WebPortalLoginPage } from "../../shared/WebPortalLoginPage";
import { M01PublicationReviewPage, M02OrganizationManagementPage } from "./pages/ManagerScreens";
import "../../shared/portal-ui.css";
import "../../shared/ui-primitives.css";
import "./styles/mg-manage.css";

function ManagerPortalRoutes() {
  const location = useLocation();
  const { currentRole, isAuthenticated, loginAsRole, logout, showToast } = useTeacher();
  if (isAuthenticated && currentRole !== "MANAGER") {
    return <main className="tw-hero-bg" style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}><section className="tw-card" role="alert"><h1 className="tw-h2">Phiên đăng nhập không thuộc cổng Quản lý trường</h1><p className="tw-sub">Đăng xuất phiên hiện tại để tiếp tục. Cổng này không hiển thị màn hình của role khác.</p><button type="button" className="tw-btn" onClick={logout}>Đăng xuất và quay lại</button></section></main>;
  }
  if (location.pathname !== "/login" && !isAuthenticated) return <Navigate to="/login" replace />;
  if (location.pathname === "/login" && isAuthenticated) return <Navigate to="/m02-organization-management" replace />;
  return (
    <Routes>
      <Route path="/" element={<Navigate to={isAuthenticated ? "/m02-organization-management" : "/login"} replace />} />
      <Route path="/login" element={<WebPortalLoginPage portalRole="MANAGER" onLogin={loginAsRole} />} />
      <Route path="/m01-publication-review" element={<M01PublicationReviewPage showToast={showToast} />} />
      <Route path="/m02-organization-management" element={<M02OrganizationManagementPage />} />
      <Route path="*" element={<Navigate to="/m02-organization-management" replace />} />
    </Routes>
  );
}

function ManagerPortalFrame() {
  const location = useLocation();
  const { toast, logout } = useTeacher();
  const routes = <ManagerPortalRoutes />;
  return location.pathname === "/login" ? routes : <ManagerLayout toast={toast} onLogout={logout}>{routes}</ManagerLayout>;
}

export function App() {
  return <BrowserRouter><TeacherProvider><ManagerPortalFrame /></TeacherProvider></BrowserRouter>;
}

export default App;
