import { useEffect, useState, type ReactNode } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { TeacherLayout } from './components/TeacherLayout'
import { authService } from './services/authService'
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

function TeacherAccessGate() {
  const [state, setState] = useState<'loading' | 'signed-in' | 'signed-out'>('loading')

  useEffect(() => authService.observe((user) => setState(user ? 'signed-in' : 'signed-out')), [])

  if (state === 'loading') {
    return <main className="p-8 text-slate-600">Đang xác minh tài khoản giáo viên…</main>
  }
  if (state === 'signed-out') return <Navigate to="/login" replace />
  return <TeacherLayout />
}

function PrototypeOnly({ title, children }: { title: string; children: ReactNode }) {
  const location = useLocation()
  if (new URLSearchParams(location.search).get('demo') === '1') return children
  return (
    <main className="mx-auto max-w-3xl space-y-4 px-7 py-8">
      <p className="text-sm font-semibold text-amber-800">Bản mẫu · chưa nối API đã duyệt</p>
      <h1 className="text-2xl font-bold text-slate-900">{title} chưa được nối BE1/BE2</h1>
      <p className="text-sm text-slate-700">Trang này vẫn có dữ liệu và thao tác demo. Không dùng nó để ghi nhận kết quả lớp học thật. Chỉ mở demo rõ ràng bằng đường dẫn có <code>?demo=1</code>.</p>
      <a className="inline-block font-semibold text-blue-800 underline" href={`${location.pathname}?demo=1`}>Mở bản demo</a>
    </main>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* T00 — Đăng nhập giáo viên */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Teacher UI Routes */}
        <Route path="/" element={<TeacherAccessGate />}>
          {/* T01 — Trang chủ giáo viên (Tổng quan) */}
          <Route index element={<PrototypeOnly title="Trang tổng quan"><HomePage /></PrototypeOnly>} />

          {/* T02 — Lớp và hồ sơ trẻ */}
          <Route path="classes" element={<PrototypeOnly title="Lớp học và hồ sơ"><ClassesProfilesPage /></PrototypeOnly>} />

          {/* T03 — Thiết lập phiên học */}
          <Route path="session/setup" element={<SessionSetupPage />} />

          {/* T04 — Phòng chờ & tiếp nhận */}
          <Route path="session/lobby" element={<SessionLobbyPage />} />

          {/* T05 — Điều phối lớp */}
          <Route path="session" element={<Navigate to="/session/orchestrate" replace />} />
          <Route path="session/orchestrate" element={<SessionOrchestratePage />} />

          {/* T06 — Không gian nhóm */}
          <Route path="session/group" element={<PrototypeOnly title="Không gian nhóm"><GroupWorkspacePage /></PrototypeOnly>} />

          {/* T07 & T07b — Duyệt gợi ý AI */}
          <Route path="ai-review" element={<PrototypeOnly title="Duyệt gợi ý AI"><AiSuggestionReviewPage stale={false} /></PrototypeOnly>} />
          <Route path="ai-review/stale" element={<PrototypeOnly title="Gợi ý AI cũ"><AiSuggestionReviewPage stale={true} /></PrototypeOnly>} />

          {/* T08 — Phòng tranh của lớp */}
          <Route path="library" element={<Navigate to="/library/gallery" replace />} />
          <Route path="library/gallery" element={<PrototypeOnly title="Phòng tranh"><ClassGalleryPage /></PrototypeOnly>} />

          {/* T09, T09b, T09c — Kiến thức & video */}
          <Route path="session/video" element={<PrototypeOnly title="Kiến thức và video"><VideoKnowledgePage mode="review" /></PrototypeOnly>} />
          <Route path="session/video/generating" element={<PrototypeOnly title="Tạo video"><VideoKnowledgePage mode="generating" /></PrototypeOnly>} />
          <Route path="session/video/error" element={<PrototypeOnly title="Lỗi tạo video"><VideoKnowledgePage mode="error" /></PrototypeOnly>} />

          {/* T10 — Hoạt động ngoài màn hình */}
          <Route path="library/offline" element={<PrototypeOnly title="Hoạt động ngoài màn hình"><OfflineActivitiesPage /></PrototypeOnly>} />

          {/* T11 — Phản hồi & quan sát */}
          <Route path="portfolio/observation" element={<ObservationFeedbackPage />} />

          {/* T12 — Hồ sơ học tập */}
          <Route path="portfolio" element={<PrototypeOnly title="Hồ sơ học tập"><LearningPortfolioPage /></PrototypeOnly>} />

          {/* T13 — Soạn nội dung */}
          <Route path="library/authoring" element={<PrototypeOnly title="Soạn nội dung"><ContentAuthoringPage /></PrototypeOnly>} />

          {/* T14 — Mẫu phiên & tự động hóa */}
          <Route path="settings" element={<PrototypeOnly title="Mẫu phiên và tự động hóa"><TemplatesAutomationPage /></PrototypeOnly>} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
