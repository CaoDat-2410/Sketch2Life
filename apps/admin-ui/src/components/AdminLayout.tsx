import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Home, Users, GraduationCap, Folder, Shield, BarChart2,
  FileText, Database, Clock, Settings, LogOut,
  Bell, ChevronRight, School,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/',              label: 'Tổng quan',         icon: Home,          end: true },
  { to: '/users',         label: 'Người dùng',        icon: Users },
  { to: '/classes',       label: 'Lớp học',           icon: GraduationCap },
  { to: '/content',       label: 'Nội dung',          icon: Folder },
  { to: '/ai-policy',     label: 'Chính sách AI',     icon: Shield },
  { to: '/monitoring',    label: 'Giám sát',          icon: BarChart2 },
  { to: '/reports',       label: 'Báo cáo',           icon: FileText },
  { to: '/data-requests', label: 'Consent & dữ liệu', icon: Database },
  { to: '/logs',          label: 'Nhật ký',           icon: Clock },
  { to: '/settings',      label: 'Cấu hình',          icon: Settings },
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

export function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const pageTitle = PAGE_TITLES[location.pathname] ?? 'Tổng quan'

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* ── Sidebar ── */}
      <aside className="w-60 flex-shrink-0 bg-white border-r border-gray-100 flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 pt-5 pb-4">
          {/* Sketch2Life logo icon — rocket + leaf matching design */}
          <div className="w-8 h-8 flex items-center justify-center">
            <svg viewBox="0 0 36 36" width="36" height="36" fill="none">
              {/* Leaf / wing shape */}
              <ellipse cx="12" cy="22" rx="9" ry="5" fill="#22C55E" transform="rotate(-30 12 22)"/>
              {/* Rocket body */}
              <path d="M18 6 C18 6 26 10 26 20 L18 28 L10 20 C10 10 18 6 18 6Z" fill="#2563EB"/>
              {/* Rocket window */}
              <circle cx="18" cy="17" r="3" fill="white" opacity="0.9"/>
              {/* Rocket flame */}
              <path d="M15 28 Q18 34 21 28" fill="#F59E0B"/>
            </svg>
          </div>
          <span className="text-[17px] font-bold text-blue-900 tracking-tight">Sketch2Life</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 pb-3">
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest px-2 mb-2 mt-1">
            Quản trị
          </p>
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2.5 rounded-xl mb-0.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={17} className={isActive ? 'text-blue-600' : 'text-gray-400'} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t border-gray-100 p-3">
          <button className="flex items-center gap-2.5 w-full px-2 py-2 rounded-xl hover:bg-gray-50 transition-colors">
            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
              QT
            </div>
            <div className="flex-1 text-left min-w-0">
              <p className="text-sm font-semibold text-gray-800 leading-tight truncate">Quản trị viên</p>
            </div>
            <ChevronRight size={14} className="text-gray-400 flex-shrink-0" />
          </button>
          <button
            onClick={() => navigate('/login')}
            className="flex items-center gap-2.5 w-full px-2 py-2 mt-1 rounded-xl text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors text-sm"
          >
            <LogOut size={16} className="text-gray-400" />
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-14 bg-white border-b border-gray-100 flex items-center justify-between px-6 flex-shrink-0">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Home size={15} className="text-gray-500" />
            <span className="text-gray-300">/</span>
            <span className="text-gray-800 font-medium">{pageTitle}</span>
          </div>

          {/* Right */}
          <div className="flex items-center gap-3">
            {/* School selector */}
            <button className="flex items-center gap-2 text-sm text-gray-700 bg-gray-50/80 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-100 transition-colors font-medium">
              <School size={15} className="text-gray-500" />
              Trường Mầm Xanh
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M3 4.5L6 7.5L9 4.5" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>

            {/* Bell */}
            <button className="relative w-9 h-9 flex items-center justify-center rounded-full hover:bg-gray-50 transition-colors">
              <Bell size={18} className="text-gray-500" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
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
