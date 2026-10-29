import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AdminLayout } from './components/AdminLayout'
import { ClassesPage } from './pages/ClassesPage'
import { LoginPage } from './pages/LoginPage'
import { authService } from './services/authService'
import { classService } from './services/classService'

function AdminAccessGate() {
  const [state, setState] = useState<'loading' | 'signed-out' | 'authorized' | 'forbidden' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => authService.observe((user) => {
    if (!user) {
      setState('signed-out')
      return
    }
    classService.currentAssignments().then((result) => {
      const isOrgAdmin = result.assignments.some((item) => item.role === 'school_admin' && item.class_id === null)
      setState(isOrgAdmin ? 'authorized' : 'forbidden')
    }).catch((cause: unknown) => {
      setMessage(cause instanceof Error ? cause.message : 'Không xác minh được quyền quản trị BE1.')
      setState('error')
    })
  }), [])

  if (state === 'loading') return <main className="p-8 text-slate-600">Đang xác minh quyền school_admin qua BE1…</main>
  if (state === 'signed-out') return <Navigate to="/login" replace />
  if (state === 'forbidden' || state === 'error') {
    return <main className="m-8 max-w-2xl rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-950"><h1 className="text-xl font-bold">Không thể mở cổng quản trị</h1><p className="mt-2 text-sm">{message || 'Tài khoản này chưa có phân công school_admin cấp trường trong BE1.'}</p><button onClick={() => void authService.logout().then(() => { window.location.assign('/login') })} className="mt-4 rounded-lg border border-amber-300 bg-white px-4 py-2 text-sm font-semibold">Đăng xuất</button></main>
  }
  return <AdminLayout />
}

function UnsupportedAdminPage() {
  return <section className="m-7 rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-950"><h1 className="text-xl font-bold">Chức năng quản trị chưa nối BE1</h1><p className="mt-2 text-sm">Không có API contract đang được Admin UI sử dụng cho mục này. Dữ liệu mẫu và thao tác thay đổi đã được ẩn để tránh hiểu nhầm là đã lưu.</p><p className="mt-3 text-sm">Màn hiện được nối: danh sách và tạo lớp. Consent, yêu cầu dữ liệu, phân quyền, audit, nội dung và chính sách cần contract/permission review riêng.</p></section>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<AdminAccessGate />}>
          <Route index element={<Navigate to="/classes" replace />} />
          <Route path="classes" element={<ClassesPage />} />
          <Route path="*" element={<UnsupportedAdminPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
