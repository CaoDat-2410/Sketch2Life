import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes, useNavigate } from 'react-router-dom'
import { AdminLayout } from './components/AdminLayout'
import { ClassesPage } from './pages/ClassesPage'
import { LoginPage } from './pages/LoginPage'
import { UsersPage } from './pages/UsersPage'
import { authService } from './services/authService'

function RequireRole({ requiredRole }: { requiredRole: 'school_manager' | 'platform_admin' }) {
  const [state, setState] = useState<'loading' | 'authorized' | 'signed-out' | 'forbidden' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => authService.observe((user) => {
    if (!user) {
      setState('signed-out')
      return
    }
    authService.getAccountRole().then((role) => {
      if (role === requiredRole) setState('authorized')
      else {
        setMessage('Tài khoản này không được cấp quyền cho trang quản trị này.')
        setState('forbidden')
      }
    }).catch((cause: unknown) => {
      setMessage(cause instanceof Error ? cause.message : 'Không xác minh được vai trò tài khoản.')
      setState('error')
    })
  }), [requiredRole])

  if (state === 'loading') return <main className="p-8 text-slate-600">Đang xác minh vai trò…</main>
  if (state === 'signed-out') return <Navigate to="/login" replace />
  if (state === 'forbidden' || state === 'error') {
    return <main className="m-8 max-w-2xl rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-950"><h1 className="text-xl font-bold">Không thể mở trang quản trị</h1><p className="mt-2 text-sm">{message}</p><button onClick={() => void authService.logout().then(() => { window.location.assign('/login') })} className="mt-4 rounded-lg border border-amber-300 bg-white px-4 py-2 text-sm font-semibold">Đăng nhập tài khoản khác</button></main>
  }
  return <Outlet />
}

function AccountHomeRedirect() {
  const navigate = useNavigate()
  const [message, setMessage] = useState('Đang xác minh tài khoản…')
  useEffect(() => {
    authService.getAccountRole().then((role) => {
      if (role === 'platform_admin') navigate('/users', { replace: true })
      else if (role === 'school_manager') navigate('/classes', { replace: true })
      else setMessage('Tài khoản này không được cấp quyền vào trang quản trị.')
    }).catch(() => navigate('/login', { replace: true }))
  }, [navigate])
  return <main className="p-8 text-slate-600">{message}</main>
}

function UnsupportedAdminPage() {
  return <section className="m-7 rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-950"><h1 className="text-xl font-bold">Chức năng quản trị chưa nối API</h1><p className="mt-2 text-sm">Màn này chưa có contract API được kết nối. Dữ liệu mẫu và thao tác thay đổi được ẩn để tránh hiểu nhầm là đã lưu.</p></section>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<AccountHomeRedirect />} />
        <Route element={<RequireRole requiredRole="school_manager" />}>
          <Route element={<AdminLayout role="school_manager" />}>
            <Route path="/classes" element={<ClassesPage />} />
            <Route path="/content" element={<UnsupportedAdminPage />} />
            <Route path="/ai-policy" element={<UnsupportedAdminPage />} />
            <Route path="/monitoring" element={<UnsupportedAdminPage />} />
            <Route path="/reports" element={<UnsupportedAdminPage />} />
            <Route path="/data-requests/*" element={<UnsupportedAdminPage />} />
            <Route path="/logs" element={<UnsupportedAdminPage />} />
            <Route path="/settings" element={<UnsupportedAdminPage />} />
          </Route>
        </Route>
        <Route element={<RequireRole requiredRole="platform_admin" />}>
          <Route element={<AdminLayout role="platform_admin" />}>
            <Route path="/users" element={<UsersPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
