import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Home,
  User,
  GraduationCap,
  Folder,
  Shield,
  BarChart2,
  FileText,
  Database,
  Clock,
  Settings,
  Bell,
  ChevronDown,
  ChevronRight,
  LogOut,
  School,
} from 'lucide-react'
import sidebarLogo from '../assets/sidebar-logo.png'
import { authService } from '../services/authService'

const NAV_ITEMS = [
  { to: '/', label: 'Tổng quan', icon: Home, end: true },
  { to: '/users', label: 'Người dùng', icon: User },
  { to: '/classes', label: 'Lớp học', icon: GraduationCap },
  { to: '/content', label: 'Nội dung', icon: Folder },
  { to: '/ai-policy', label: 'Chính sách AI', icon: Shield },
  { to: '/monitoring', label: 'Giám sát', icon: BarChart2 },
  { to: '/reports', label: 'Báo cáo', icon: FileText },
  { to: '/data-requests', label: 'Consent & dữ liệu', icon: Database },
  { to: '/logs', label: 'Nhật ký', icon: Clock },
  { to: '/settings', label: 'Cấu hình', icon: Settings },
]

const PAGE_TITLES: Record<string, string> = {
  '/': 'Tổng quan',
  '/users': 'Người dùng',
  '/classes': 'Lớp học',
  '/content': 'Nội dung',
  '/ai-policy': 'Chính sách AI',
  '/monitoring': 'Giám sát & sự cố',
  '/reports': 'Báo cáo',
  '/data-requests': 'Consent & dữ liệu',
  '/logs': 'Nhật ký',
  '/settings': 'Cấu hình',
}

const QUICK_SCREENS = [
  { code: 'A00', label: 'Đăng nhập quản trị', to: '/login' },
  { code: 'A01', label: 'Tổng quan', to: '/' },
  { code: 'A02', label: 'Người dùng & vai trò', to: '/users' },
  { code: 'A03', label: 'Lớp học & phân công', to: '/classes' },
  { code: 'A04', label: 'Quản trị nội dung', to: '/content' },
  { code: 'A05', label: 'Chính sách AI', to: '/ai-policy' },
  { code: 'A06', label: 'Giám sát & sự cố', to: '/monitoring' },
  { code: 'A07', label: 'Báo cáo theo phạm vi', to: '/reports' },
  { code: 'A08', label: 'Consent & yêu cầu dữ liệu', to: '/data-requests' },
  { code: 'A08b', label: 'Yêu cầu xóa dữ liệu (DR-024)', to: '/data-requests/DR-024' },
  { code: 'A09', label: 'Nhật ký kiểm toán', to: '/logs' },
  { code: 'A10', label: 'Cấu hình & vòng đời dữ liệu', to: '/settings' },
]

export function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [showQuickNav, setShowQuickNav] = useState(false)

  const isDeleteDetail = location.pathname.startsWith('/data-requests/')
  const detailId = isDeleteDetail ? location.pathname.split('/')[2] : null
  const pageTitle = PAGE_TITLES[location.pathname] ?? 'Tổng quan'

  return (
    <div className="flex h-screen bg-[#F4F7FB] overflow-hidden select-none">
      {/* ── Sidebar ─────────────────────────────────── */}
      <aside className="w-[224px] flex-shrink-0 bg-[#F8FBFF] border-r border-slate-200/70 flex flex-col justify-between">
        <div>
          {/* Logo */}
          <div
            onClick={() => navigate('/')}
            className="flex items-center px-6 h-[68px] cursor-pointer"
          >
            <img
              src={sidebarLogo}
              alt="Sketch2Life"
              className="h-[42px] w-auto object-contain"
            />
          </div>

          {/* Section label */}
          <p className="px-6 pt-3 pb-2 text-[11px] font-bold tracking-[0.08em] text-slate-400 uppercase">
            QUẢN TRỊ
          </p>

          {/* Nav items */}
          <nav className="px-3 space-y-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `flex items-center gap-3.5 px-4 py-2.5 rounded-xl text-[14px] transition-colors ${
                    isActive
                      ? 'bg-[#E2EEFF] text-[#1D63F2] font-semibold'
                      : 'text-[#334155] font-medium hover:bg-slate-100/80 hover:text-slate-900'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      size={18}
                      strokeWidth={isActive ? 2.2 : 1.9}
                      className={isActive ? 'text-[#1D63F2]' : 'text-[#475569]'}
                    />
                    <span>{label}</span>
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* User footer card */}
        <div className="m-3 p-2 bg-[#F4F8FD] border border-slate-200/80 rounded-2xl space-y-0.5">
          <div className="flex items-center justify-between px-2.5 py-2 rounded-xl hover:bg-white/70 cursor-pointer transition">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[#DCEBFF] text-[#1D63F2] text-xs font-bold flex items-center justify-center">
                QT
              </div>
              <span className="text-[14px] font-bold text-slate-800">Quản trị viên</span>
            </div>
            <ChevronRight size={15} className="text-slate-400" />
          </div>
          <button
            onClick={() => void authService.logout().then(() => navigate('/login', { replace: true }))}
            className="flex items-center gap-3 w-full px-3 py-2 text-[14px] font-medium text-slate-600 hover:text-red-600 hover:bg-red-50/60 rounded-xl transition-colors"
          >
            <LogOut size={17} className="text-slate-500" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      {/* ── Right: Topbar + Content ──────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-[58px] flex-shrink-0 bg-white border-b border-slate-200/70 px-6 flex items-center justify-between relative z-30">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2.5 text-[14px] text-slate-500">
            <Home
              size={17}
              className="text-slate-600 cursor-pointer hover:text-blue-600"
              onClick={() => navigate('/')}
            />
            <span className="text-slate-300">/</span>
            {isDeleteDetail ? (
              <>
                <span
                  onClick={() => navigate('/data-requests')}
                  className="text-slate-600 font-medium cursor-pointer hover:text-blue-600"
                >
                  Consent &amp; dữ liệu
                </span>
                <span className="text-slate-300">/</span>
                <span className="text-slate-700 font-medium">{detailId}</span>
              </>
            ) : (
              <span className="text-slate-600 font-medium">{pageTitle}</span>
            )}
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-3.5">
            {/* School selector */}
            <button className="flex items-center gap-2.5 bg-[#F1F5F9] hover:bg-slate-200/70 text-slate-700 text-[13px] font-semibold px-3.5 py-2 rounded-xl transition-colors">
              <School size={16} className="text-slate-600" />
              <span>Tổ chức đã xác minh qua BE1</span>
              <ChevronDown size={14} className="text-slate-500 ml-0.5" />
            </button>

            {/* Notification bell + Quick Screen Switcher */}
            <div className="relative">
              <button
                onClick={() => setShowQuickNav((v) => !v)}
                title="Chuyển nhanh màn hình (A00 - A10)"
                className="relative p-2 text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
              >
                <Bell size={19} />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-white" />
              </button>

              {showQuickNav && (
                <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-2xl shadow-xl py-2 z-50">
                  <div className="px-3.5 py-1.5 border-b border-slate-100 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-700">Danh sách 12 màn hình Admin</span>
                    <button
                      onClick={() => setShowQuickNav(false)}
                      className="text-xs text-slate-400 hover:text-slate-600"
                    >
                      Đóng
                    </button>
                  </div>
                  <div className="max-h-80 overflow-y-auto py-1">
                    {QUICK_SCREENS.map((sc) => (
                      <button
                        key={sc.code}
                        onClick={() => {
                          setShowQuickNav(false)
                          navigate(sc.to)
                        }}
                        className={`w-full px-3.5 py-2 text-left text-xs flex items-center justify-between hover:bg-blue-50/70 transition ${
                          location.pathname === sc.to ? 'bg-blue-50 text-blue-600 font-bold' : 'text-slate-700'
                        }`}
                      >
                        <span>{sc.label}</span>
                        <span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                          {sc.code}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Avatar */}
            <div className="w-9 h-9 rounded-full bg-[#DCEBFF] text-[#1D63F2] text-[13px] font-bold flex items-center justify-center">
              QT
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
