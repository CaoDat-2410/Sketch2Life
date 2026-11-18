import { lazy, Suspense, useLayoutEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { PortalEntryPage } from "./PortalEntryPage";
import { PortalSessionProvider } from "../shared/PortalSessionContext";

const TeacherPortalApp = lazy(() => import("../modules/teacher/App").then((module) => ({ default: module.TeacherPortalApp })));
const SchoolManagerBe1App = lazy(() => import("../modules/school-manager/be1/App").then((module) => ({ default: module.SchoolManagerBe1App })));
const PlatformAdminApp = lazy(() => import("../modules/platform-admin/App").then((module) => ({ default: module.PlatformAdminApp })));

function PortalRoutes() {
  const location = useLocation();

  useLayoutEffect(() => {
    const path = location.pathname;
    document.documentElement.dataset.portal = path.startsWith("/teacher")
      ? "teacher"
      : path.startsWith("/school")
        ? "school-be1"
        : path.startsWith("/platform")
          ? "platform"
          : "entry";
  }, [location.pathname]);

  return (
    <Suspense fallback={<main className="s2l-route-loading" role="status">Đang mở không gian làm việc…</main>}>
      <Routes>
        <Route path="/login" element={<PortalEntryPage />} />
        <Route path="/teacher/login" element={<Navigate to="/login?role=teacher" replace />} />
        <Route path="/teacher/sign-in" element={<Navigate to="/login?role=teacher" replace />} />
        <Route path="/school/login" element={<Navigate to="/login?role=manager" replace />} />
        <Route path="/platform/login" element={<Navigate to="/login?role=admin" replace />} />
        <Route path="/school/preview/*" element={<Navigate to="/login?role=manager" replace />} />
        <Route path="/teacher/*" element={<TeacherPortalApp />} />
        <Route path="/school/*" element={<SchoolManagerBe1App />} />
        <Route path="/platform/*" element={<PlatformAdminApp />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <PortalSessionProvider>
      <BrowserRouter>
        <PortalRoutes />
      </BrowserRouter>
    </PortalSessionProvider>
  );
}
