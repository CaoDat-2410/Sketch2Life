import React from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { ParentProvider, useParent } from "./context/ParentContext";
import { MobileLayout } from "./components/MobileLayout";
import { ApiUnavailableView, isLocalPreview } from "../../shared/backendApi";
import {
  P01LessonLibraryPage,
  P02LessonDetailPage,
  P03DrawingLineGuidePage,
  P04CaptureSubjectConfirmationPage,
  P05ContextIdeaConfirmationPage,
  P05bActivitySelectionPage,
  P06StoryReviewPage,
  P07VideoJobStatusPage,
  P08VideoAndActivitiesPage,
  P08bOutdoorActivityPage,
  P08cSessionFeedbackPage,
  P09HistoryFeedbackPage,
  P10ChildProfileDetailPage,
  P11AuthenticationPage,
  P12VideoQuotaPage,
  P13SettingsPage,
} from "./pages/ParentScreens";

function apiOrPreview(element: React.ReactNode, title: string, endpoint: string, detail: string) {
  return isLocalPreview() ? element : <ApiUnavailableView title={title} endpoint={endpoint} detail={detail} />;
}

function ParentRoutes() {
  const { isAuthenticated } = useParent();
  const location = useLocation();
  const authPath = location.pathname === "/p11-authentication" || location.pathname === "/login";
  if (!isAuthenticated && !authPath) return <Navigate to="/p11-authentication" replace />;
  if (isAuthenticated && authPath) return <Navigate to="/p01-lesson-library" replace />;

  return (
    <Routes>
      <Route path="/" element={<Navigate to={isAuthenticated ? "/p01-lesson-library" : "/p11-authentication"} replace />} />
      <Route path="/login" element={<Navigate to="/p11-authentication" replace />} />
      <Route path="/p01-lesson-library" element={<P01LessonLibraryPage />} />
      <Route path="/p02-lesson-detail" element={<P02LessonDetailPage />} />
      <Route path="/p03-drawing-line-guide" element={apiOrPreview(<P03DrawingLineGuidePage />, "Gợi ý nét vẽ", "/api/*", "Backend hiện chưa có API Parent cho job tạo line-sketch guide.")} />
      <Route path="/p04-capture-subject-confirmation" element={apiOrPreview(<P04CaptureSubjectConfirmationPage />, "Chụp tranh và xác nhận chủ thể", "/api/*", "Backend sản phẩm hiện chưa có Story Run API cho upload tranh và duyệt chủ thể.")} />
      <Route path="/p05-context-idea-confirmation" element={apiOrPreview(<P05ContextIdeaConfirmationPage />, "Xác nhận ý tưởng", "/api/*", "Luồng story/context Parent chưa có API bền vững trong backend hiện tại.")} />
      <Route path="/p05b-activity-selection" element={apiOrPreview(<P05bActivitySelectionPage />, "Chọn hoạt động", "/api/lesson-library/v1/me/lessons/{id}", "Hoạt động được đọc trong chi tiết giáo án; chưa có API lưu lựa chọn activity vào Story Run.")} />
      <Route path="/p06-story-review" element={apiOrPreview(<P06StoryReviewPage />, "Duyệt kịch bản", "/api/*", "Backend sản phẩm hiện chưa có API tạo hoặc xác nhận story revision cho Parent.")} />
      <Route path="/p07-video-job-status" element={apiOrPreview(<P07VideoJobStatusPage />, "Tiến trình video", "/api/*", "Backend sản phẩm hiện chưa có API Parent để tạo hoặc theo dõi video job.")} />
      <Route path="/p08-video-and-activities" element={apiOrPreview(<P08VideoAndActivitiesPage />, "Video và hoạt động", "/api/*", "Backend hiện chưa có API Parent cho video playback hoặc lịch sử hoạt động.")} />
      <Route path="/p08b-outdoor-activity" element={apiOrPreview(<P08bOutdoorActivityPage />, "Hoạt động ngoài trời", "/api/lesson-library/v1/me/lessons/{id}", "Backend trả hoạt động trong giáo án; chưa có API ghi nhận phiên thực hiện hoặc phản hồi.")} />
      <Route path="/p08c-session-feedback" element={apiOrPreview(<P08cSessionFeedbackPage />, "Phản hồi phiên học", "/api/*", "Chưa có API Parent để lưu phản hồi Story Run.")} />
      <Route path="/p09-history-feedback" element={apiOrPreview(<P09HistoryFeedbackPage />, "Lịch sử và phản hồi", "/api/*", "Backend hiện chưa có API Parent cho lịch sử Story Run hoặc feedback.")} />
      <Route path="/p10-child-profiles" element={<Navigate to="/p13-settings#child-profiles" replace />} />
      <Route path="/p10-child-profiles/:childId" element={apiOrPreview(<P10ChildProfileDetailPage />, "Chi tiết hồ sơ trẻ", "/api/*", "Chưa có Parent API để đọc hoặc sửa hồ sơ trẻ.")} />
      <Route path="/p11-authentication" element={<P11AuthenticationPage />} />
      <Route path="/p12-video-quota" element={apiOrPreview(<P12VideoQuotaPage />, "Quota video", "/api/*", "Backend hiện chưa có Parent API về video quota, thanh toán hoặc top-up.")} />
      <Route path="/p13-settings" element={apiOrPreview(<P13SettingsPage />, "Cài đặt tài khoản chưa nối API", "/api/*", "Backend hiện chưa có API Parent cho mật khẩu, 2FA, email, thông báo hoặc tuỳ chọn tài khoản. Giao diện cài đặt chỉ dùng trong bản xem thử.")} />
      <Route path="*" element={<Navigate to="/p01-lesson-library" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <ParentProvider>
        <MobileLayout><ParentRoutes /></MobileLayout>
      </ParentProvider>
    </BrowserRouter>
  );
}

export default App;
