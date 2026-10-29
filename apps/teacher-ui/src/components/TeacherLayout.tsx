import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Home,
  Users,
  BookOpen,
  Sparkles,
  Image as ImageIcon,
  BarChart2,
  Settings,
  LogOut,
  Bell,
  User,
} from 'lucide-react'
import logoIcon from '../assets/logo-icon.png'

const NAV_ITEMS = [
  { key: 'home',      to: '/',          label: 'Tổng quan',     icon: Home,      match: (p: string) => p === '/' },
  { key: 'classes',   to: '/classes',   label: 'Lớp học',       icon: Users,     match: (p: string) => p.startsWith('/classes') },
  { key: 'session',   to: '/session/orchestrate', label: 'Phiên học', icon: BookOpen, match: (p: string) => p.startsWith('/session') },
  { key: 'ai-review', to: '/ai-review', label: 'Duyệt AI',      icon: Sparkles,  match: (p: string) => p.startsWith('/ai-review') },
  { key: 'library',   to: '/library/gallery', label: 'Thư viện', icon: ImageIcon, match: (p: string) => p.startsWith('/library') },
  { key: 'portfolio', to: '/portfolio', label: 'Hồ sơ học tập', icon: BarChart2, match: (p: string) => p.startsWith('/portfolio') },
  { key: 'settings',  to: '/settings',  label: 'Cài đặt',       icon: Settings,  match: (p: string) => p.startsWith('/settings') },
]

const ALL_SCREENS = [
  { code: 'T00', label: 'Đăng nhập giáo viên', to: '/login' },
  { code: 'T01', label: 'Trang chủ giáo viên', to: '/' },
  { code: 'T02', label: 'Lớp học & hồ sơ trẻ', to: '/classes' },
  { code: 'T03', label: 'Thiết lập phiên học', to: '/session/setup' },
  { code: 'T04', label: 'Phòng chờ & tiếp nhận', to: '/session/lobby' },
  { code: 'T05', label: 'Điều phối lớp', to: '/session/orchestrate' },
  { code: 'T06', label: 'Không gian nhóm', to: '/session/group' },
  { code: 'T07', label: 'Duyệt từng gợi ý AI (Hợp lệ)', to: '/ai-review' },
  { code: 'T07b', label: 'Gợi ý không còn hợp lệ', to: '/ai-review/stale' },
  { code: 'T08', label: 'Phòng tranh của lớp', to: '/library/gallery' },
  { code: 'T09', label: 'Duyệt video', to: '/session/video' },
  { code: 'T09b', label: 'Đang tạo video', to: '/session/video/generating' },
  { code: 'T09c', label: 'Lỗi video: giáo viên quyết định', to: '/session/video/error' },
  { code: 'T10', label: 'Hoạt động ngoài màn hình', to: '/library/offline' },
  { code: 'T11', label: 'Phản hồi & quan sát', to: '/portfolio/observation' },
  { code: 'T12', label: 'Hồ sơ học tập', to: '/portfolio' },
  { code: 'T13', label: 'Soạn nội dung', to: '/library/authoring' },
  { code: 'T14', label: 'Mẫu phiên & tự động hóa', to: '/settings' },
]

function getBreadcrumb(pathname: string): { parent: string; current: string } {
  if (pathname === '/session/group') {
    return { parent: 'Điều phối lớp', current: 'Nhóm Lá' }
  }
  if (pathname === '/library/authoring') {
    return { parent: 'Thư viện', current: 'Bản nháp' }
  }
  return { parent: 'Mầm Xanh', current: 'Lớp Mầm Xanh' }
}

export function TeacherLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [showQuickNav, setShowQuickNav] = useState(false)
  const breadcrumb = getBreadcrumb(location.pathname)

  return (
    <div className="flex h-screen overflow-hidden bg-[#F6F9FC] text-[#0F172A]">
      {/* ── Left Sidebar ── */}
      <aside className="w-[238px] flex-shrink-0 bg-white border-r border-slate-200/70 flex flex-col justify-between select-none">
        <div>
          {/* Brand Logo */}
          <div
            onClick={() => navigate('/')}
            className="flex items-center gap-2.5 px-5 pt-5 pb-5 cursor-pointer"
          >
            <img
              src={logoIcon}
              alt="Sketch2Life"
              className="w-10 h-10 object-contain flex-shrink-0"
            />
            <div className="leading-tight">
              <div className="text-[19px] font-extrabold text-[#1E50E2] tracking-tight">
                Sketch2Life
              </div>
              <div className="text-[12.5px] font-medium text-slate-600 mt-0.5">
                Giáo viên
              </div>
            </div>
          </div>

          {/* Navigation Menu */}
          <nav className="px-3 space-y-1">
            {NAV_ITEMS.map(({ key, to, label, icon: Icon, match }) => {
              const active = match(location.pathname)
              return (
                <button
                  key={key}
                  onClick={() => navigate(to)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[14px] transition-all cursor-pointer ${
                    active
                      ? 'bg-[#1D63F2] text-white font-semibold shadow-sm'
                      : 'text-[#1E293B] font-medium hover:bg-slate-100/80'
                  }`}
                >
                  <Icon
                    size={18}
                    strokeWidth={active ? 2.2 : 1.9}
                    className={active ? 'text-white' : 'text-[#334155]'}
                  />
                  <span>{label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="px-3.5 pb-4 pt-3 border-t border-slate-100 space-y-2.5">
          <div className="flex items-center gap-2.5 px-1.5 py-1">
            <div className="w-7 h-7 rounded-full bg-slate-200/90 flex items-center justify-center text-slate-600">
              <User size={15} strokeWidth={2.2} />
            </div>
            <span className="text-[14px] font-medium text-slate-700">Giáo viên</span>
          </div>

          <button
            onClick={() => navigate('/login')}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-[14px] font-medium text-slate-700 transition-colors cursor-pointer"
          >
            <LogOut size={16} className="text-slate-600" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-12 bg-white border-b border-slate-200/70 flex items-center justify-between px-7 flex-shrink-0 relative">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-[13.5px] text-slate-500">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none" className="text-slate-400">
              <path
                d="M8 1.5L9.6 6.4L14.5 8L9.6 9.6L8 14.5L6.4 9.6L1.5 8L6.4 6.4L8 1.5Z"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinejoin="round"
              />
            </svg>
            <span className="text-slate-600 font-medium">{breadcrumb.parent}</span>
            <span className="text-slate-300">/</span>
            <span className="text-slate-600 font-medium">{breadcrumb.current}</span>
          </div>

          {/* Right side: Notification Bell (click to open quick screen switcher) */}
          <div className="relative">
            <button
              onClick={() => setShowQuickNav(!showQuickNav)}
              title="Chuyển nhanh màn hình (T00 - T14)"
              className="relative w-8 h-8 flex items-center justify-center rounded-full hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <Bell size={18} className="text-slate-600 fill-slate-600" />
              <span className="absolute top-1 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white" />
            </button>

            {showQuickNav && (
              <div className="absolute right-0 top-10 w-72 bg-white rounded-2xl shadow-xl border border-slate-200 p-2 z-50 max-h-[80vh] overflow-y-auto">
                <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Danh sách 18 màn hình (T00–T14)
                </div>
                {ALL_SCREENS.map((scr) => {
                  const isCurrent = location.pathname === scr.to
                  return (
                    <button
                      key={scr.code}
                      onClick={() => {
                        setShowQuickNav(false)
                        navigate(scr.to)
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left text-[13px] transition cursor-pointer ${
                        isCurrent
                          ? 'bg-[#EFF6FF] text-[#1D63F2] font-bold'
                          : 'text-slate-700 hover:bg-slate-50 font-medium'
                      }`}
                    >
                      <span className="w-10 text-[11.5px] font-mono font-bold text-slate-400">
                        {scr.code}
                      </span>
                      <span className="truncate">{scr.label}</span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </header>

        {/* Page Outlet */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
