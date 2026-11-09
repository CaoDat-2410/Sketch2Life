import React from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { TeacherProvider, useTeacher } from "./context/TeacherContext";
import { TeacherLayout } from "./components/TeacherLayout";
import { WebPortalLoginPage } from "../../shared/WebPortalLoginPage";
import { ApiUnavailableView, isLocalPreview } from "../../shared/backendApi";
import { TeacherApiLessonPage } from "./pages/TeacherApiLessonPage";
import { TeacherApiImportPage } from "./pages/TeacherApiImportPage";
import {
  T01LessonWorkspacePage,
  T02LessonAuthoringPage,
  T03DocumentImportReviewPage,
  T04SessionSketchDeckPage,
  T05ClassesAndChildrenPage,
  T05ClassDetailPage,
  T06SampleStoryRunPage,
  T07VideoPresentationConfirmationPage,
  T08TeacherSettingsPage,
} from "./pages/TeacherScreens";
import "../../shared/portal-ui.css";
import "../../shared/ui-primitives.css";

const ROLE_HOME = "/t01-lesson-workspace";
const ROLE = "TEACHER" as const;

function ApiOrPreview({ children, title, endpoint }: { children: React.ReactNode; title: string; endpoint: string }) {
  if (isLocalPreview()) return <>{children}</>;
  return <ApiUnavailableView
    title={title}
    endpoint={endpoint}
    detail="Màn này vẫn có giao diện xem thử, nhưng chưa được nối tới API sản phẩm đã đọc. Dữ liệu hoặc thao tác minh họa không được phép xuất hiện trong phiên backend."
  />;
}

function TeacherPortalRoutes() {
  const location = useLocation();
  const { currentRole, isAuthenticated, loginAsRole, logout } = useTeacher();

  if (isAuthenticated && currentRole !== ROLE) {
    return <main className="tw-hero-bg" style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}><section className="tw-card" role="alert"><h1 className="tw-h2">Phiên đăng nhập không thuộc cổng Giáo viên</h1><p className="tw-sub">Đăng xuất phiên hiện tại để tiếp tục. Cổng này không hiển thị màn hình của role khác.</p><button type="button" className="tw-btn" onClick={logout}>Đăng xuất và quay lại</button></section></main>;
  }
  if (location.pathname !== "/login" && !isAuthenticated) return <Navigate to="/login" replace />;
  if (location.pathname === "/login" && isAuthenticated) return <Navigate to={ROLE_HOME} replace />;

  return (
    <Routes>
      <Route path="/" element={<Navigate to={isAuthenticated ? ROLE_HOME : "/login"} replace />} />
      <Route path="/login" element={<WebPortalLoginPage portalRole={ROLE} onLogin={loginAsRole} />} />
      <Route path={ROLE_HOME} element={<T01LessonWorkspacePage />} />
      <Route path="/t05-classes-and-children" element={<T05ClassesAndChildrenPage />} />
      <Route path="/t05-classes-and-children/:classId" element={<T05ClassDetailPage />} />
      <Route path="/t02-lesson-authoring" element={isLocalPreview() ? <T02LessonAuthoringPage /> : <TeacherApiLessonPage />} />
      <Route path="/t03-document-import-review" element={isLocalPreview() ? <T03DocumentImportReviewPage /> : <TeacherApiImportPage />} />
      <Route path="/t04-session-sketch-deck" element={<ApiOrPreview title="AI Sketch Deck chưa thuộc luồng API/SRS hiện hành" endpoint="Lesson Library API không có endpoint cho lớp vẽ cộng tác" ><T04SessionSketchDeckPage /></ApiOrPreview>} />
      <Route path="/t06-sample-story-run" element={<ApiOrPreview title="Chưa có API Teacher cho Story Run sản phẩm" endpoint="Không có endpoint lesson-library cho story/video" ><T06SampleStoryRunPage /></ApiOrPreview>} />
      <Route path="/t07-video-presentation-confirmation" element={<ApiOrPreview title="Chưa có API sản phẩm cho trình chiếu video" endpoint="Không có endpoint sản phẩm tương ứng trong API đã nối" ><T07VideoPresentationConfirmationPage /></ApiOrPreview>} />
      <Route path="/t08-settings" element={<ApiOrPreview title="Chưa có API hồ sơ và cài đặt Teacher" endpoint="Không có endpoint profile/settings trong nhóm API đã đọc" ><T08TeacherSettingsPage /></ApiOrPreview>} />
      <Route path="*" element={<Navigate to={ROLE_HOME} replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <TeacherProvider>
        <TeacherLayout><TeacherPortalRoutes /></TeacherLayout>
      </TeacherProvider>
    </BrowserRouter>
  );
}

export default App;
