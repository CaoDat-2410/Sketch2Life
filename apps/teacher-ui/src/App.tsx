import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { TeacherLayout } from './components/TeacherLayout'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { ClassesProfilesPage } from './pages/ClassesProfilesPage'
import { SessionSetupPage } from './pages/SessionSetupPage'
import { SessionLobbyPage } from './pages/SessionLobbyPage'
import { SessionOrchestratePage } from './pages/SessionOrchestratePage'
import { GroupWorkspacePage } from './pages/GroupWorkspacePage'
import { AiSuggestionReviewPage } from './pages/AiSuggestionReviewPage'
import { ClassGalleryPage } from './pages/ClassGalleryPage'
import { VideoKnowledgePage } from './pages/VideoKnowledgePage'
import { OfflineActivitiesPage } from './pages/OfflineActivitiesPage'
import { ObservationFeedbackPage } from './pages/ObservationFeedbackPage'
import { LearningPortfolioPage } from './pages/LearningPortfolioPage'
import { ContentAuthoringPage } from './pages/ContentAuthoringPage'
import { TemplatesAutomationPage } from './pages/TemplatesAutomationPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* T00 — Đăng nhập giáo viên */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Teacher UI Routes */}
        <Route path="/" element={<TeacherLayout />}>
          {/* T01 — Trang chủ giáo viên (Tổng quan) */}
          <Route index element={<HomePage />} />

          {/* T02 — Lớp và hồ sơ trẻ */}
          <Route path="classes" element={<ClassesProfilesPage />} />

          {/* T03 — Thiết lập phiên học */}
          <Route path="session/setup" element={<SessionSetupPage />} />

          {/* T04 — Phòng chờ & tiếp nhận */}
          <Route path="session/lobby" element={<SessionLobbyPage />} />

          {/* T05 — Điều phối lớp */}
          <Route path="session" element={<Navigate to="/session/orchestrate" replace />} />
          <Route path="session/orchestrate" element={<SessionOrchestratePage />} />

          {/* T06 — Không gian nhóm */}
          <Route path="session/group" element={<GroupWorkspacePage />} />

          {/* T07 & T07b — Duyệt gợi ý AI */}
          <Route path="ai-review" element={<AiSuggestionReviewPage stale={false} />} />
          <Route path="ai-review/stale" element={<AiSuggestionReviewPage stale={true} />} />

          {/* T08 — Phòng tranh của lớp */}
          <Route path="library" element={<Navigate to="/library/gallery" replace />} />
          <Route path="library/gallery" element={<ClassGalleryPage />} />

          {/* T09, T09b, T09c — Kiến thức & video */}
          <Route path="session/video" element={<VideoKnowledgePage mode="review" />} />
          <Route path="session/video/generating" element={<VideoKnowledgePage mode="generating" />} />
          <Route path="session/video/error" element={<VideoKnowledgePage mode="error" />} />

          {/* T10 — Hoạt động ngoài màn hình */}
          <Route path="library/offline" element={<OfflineActivitiesPage />} />

          {/* T11 — Phản hồi & quan sát */}
          <Route path="portfolio/observation" element={<ObservationFeedbackPage />} />

          {/* T12 — Hồ sơ học tập */}
          <Route path="portfolio" element={<LearningPortfolioPage />} />

          {/* T13 — Soạn nội dung */}
          <Route path="library/authoring" element={<ContentAuthoringPage />} />

          {/* T14 — Mẫu phiên & tự động hóa */}
          <Route path="settings" element={<TemplatesAutomationPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
