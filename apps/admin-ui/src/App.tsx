import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AdminLayout } from './components/AdminLayout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { UsersPage } from './pages/UsersPage'
import { ClassesPage } from './pages/ClassesPage'
import { ContentPage } from './pages/ContentPage'
import { AiPolicyPage } from './pages/AiPolicyPage'
import { MonitoringPage } from './pages/MonitoringPage'
import { ReportsPage } from './pages/ReportsPage'
import { DataRequestsPage } from './pages/DataRequestsPage'
import { LogsPage } from './pages/LogsPage'
import { SettingsPage } from './pages/SettingsPage'
import { DeleteRequestDetailPage } from './pages/DeleteRequestDetailPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* A00 — Đăng nhập */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected admin routes */}
        <Route path="/" element={<AdminLayout />}>
          {/* A01 — Tổng quan */}
          <Route index element={<DashboardPage />} />
          {/* A02 — Người dùng & vai trò */}
          <Route path="users" element={<UsersPage />} />
          {/* A03 — Lớp và trường */}
          <Route path="classes" element={<ClassesPage />} />
          {/* A04 — Quản trị nội dung */}
          <Route path="content" element={<ContentPage />} />
          {/* A05 — Chính sách AI */}
          <Route path="ai-policy" element={<AiPolicyPage />} />
          {/* A06 — Giám sát & sự cố */}
          <Route path="monitoring" element={<MonitoringPage />} />
          {/* A07 — Báo cáo */}
          <Route path="reports" element={<ReportsPage />} />
          {/* A08 / A08b — Consent & xóa dữ liệu */}
          <Route path="data-requests" element={<DataRequestsPage />} />
          <Route path="data-requests/:id" element={<DeleteRequestDetailPage />} />
          {/* A09 — Nhật ký */}
          <Route path="logs" element={<LogsPage />} />
          {/* A10 — Cấu hình */}
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
