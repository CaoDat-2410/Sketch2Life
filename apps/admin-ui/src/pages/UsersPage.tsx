import { useState } from 'react'
import {
  Search,
  UserPlus,
  ChevronRight,
  ChevronDown,
  X,
  Edit2,
  Ban,
  Info,
  Users,
  List,
  BookOpen,
} from 'lucide-react'

interface UserItem {
  id: string
  initials: string
  avatarBg: string
  avatarText: string
  name: string
  subtitle: string
  role: string
  roleColor: string
  scope: string
  status: string
  statusColor: string
  dotColor: string
  updated: string
}

const USERS: UserItem[] = [
  {
    id: 'gv-an',
    initials: 'GA',
    avatarBg: 'bg-[#DCEBFF]',
    avatarText: 'text-[#1565F9]',
    name: 'GV An',
    subtitle: 'Giáo viên',
    role: 'Giáo viên',
    roleColor: 'text-[#1565F9] bg-[#E8F1FF]',
    scope: 'Lớp Lá',
    status: 'Đang hoạt động',
    statusColor: 'text-[#059669] bg-[#E2F7EB]',
    dotColor: 'bg-[#10B981]',
    updated: '10/10/2026',
  },
  {
    id: 'gv-binh',
    initials: 'GB',
    avatarBg: 'bg-[#E2F7EB]',
    avatarText: 'text-[#059669]',
    name: 'GV Bình',
    subtitle: 'Giáo viên',
    role: 'Giáo viên',
    roleColor: 'text-[#1565F9] bg-[#E8F1FF]',
    scope: 'Lớp Hoa',
    status: 'Chờ nhận lời mời',
    statusColor: 'text-[#D97706] bg-[#FEF3C7]',
    dotColor: 'bg-[#F59E0B]',
    updated: '09/10/2026',
  },
  {
    id: 'qt-minh',
    initials: 'QM',
    avatarBg: 'bg-[#F3E8FF]',
    avatarText: 'text-[#7C3AED]',
    name: 'QT Minh',
    subtitle: 'Quản trị hệ thống',
    role: 'Quản trị viên',
    roleColor: 'text-[#7C3AED] bg-[#F3E8FF]',
    scope: 'Trường Mầm Xanh',
    status: 'Đang hoạt động',
    statusColor: 'text-[#059669] bg-[#E2F7EB]',
    dotColor: 'bg-[#10B981]',
    updated: '08/10/2026',
  },
]

export function UsersPage() {
  const [selected, setSelected] = useState<string>('gv-an')
  const [activeTab, setActiveTab] = useState<'permissions' | 'history'>('permissions')
  const [reason, setReason] = useState('')
  const [search, setSearch] = useState('')

  const selectedUser = USERS.find((u) => u.id === selected)

  return (
    <div className="px-6 py-4 max-w-[1440px] mx-auto">
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* LEFT COLUMN (7 cols) */}
        <div className="col-span-7 flex flex-col gap-3.5 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <h1 className="text-[25px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
                Người dùng &amp; vai trò
              </h1>
              <p className="text-[13.5px] text-slate-500 mt-1 font-medium">
                Quản lý tài khoản người lớn và quyền theo lớp.
              </p>
            </div>
            <button className="inline-flex items-center justify-center gap-2 bg-[#1565F9] hover:bg-blue-700 text-white text-[13px] font-semibold px-4 py-2.5 rounded-xl transition shadow-sm cursor-pointer whitespace-nowrap shrink-0">
              <UserPlus size={15} className="shrink-0" />
              <span>Mời người dùng</span>
            </button>
          </div>

          {/* Search & Filters Card */}
          <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 shadow-[0_1px_3px_rgba(15,23,42,0.02)] grid grid-cols-12 gap-3 items-end">
            <div className="col-span-6 min-w-0">
              <label className="block text-[11.5px] font-semibold text-slate-500 mb-1">
                Tìm kiếm
              </label>
              <div className="relative">
                <Search
                  size={15}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Tìm tài khoản (tên hiển thị)..."
                  className="w-full h-[38px] pl-9 pr-3 border border-slate-200 rounded-xl text-[13px] text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-[#FAFBFD]"
                />
              </div>
            </div>

            <div className="col-span-3 min-w-0">
              <label className="block text-[11.5px] font-semibold text-slate-500 mb-1">
                Vai trò
              </label>
              <button className="w-full h-[38px] flex items-center justify-between border border-slate-200 rounded-xl px-3 text-[13px] font-medium text-slate-700 bg-white hover:bg-slate-50 whitespace-nowrap">
                <span>Tất cả</span>
                <ChevronDown size={14} className="text-slate-400 shrink-0" />
              </button>
            </div>

            <div className="col-span-3 min-w-0">
              <label className="block text-[11.5px] font-semibold text-slate-500 mb-1">
                Trạng thái
              </label>
              <button className="w-full h-[38px] flex items-center justify-between border border-slate-200 rounded-xl px-3 text-[13px] font-medium text-slate-700 bg-white hover:bg-slate-50 whitespace-nowrap">
                <span>Tất cả</span>
                <ChevronDown size={14} className="text-slate-400 shrink-0" />
              </button>
            </div>
          </div>

          {/* Table Card */}
          <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex-1">
            <div className="border border-slate-100 rounded-xl overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#F4F7FB] border-b border-slate-100 text-slate-600">
                    <th className="text-left py-2.5 pl-3 pr-2 text-[12px] font-semibold whitespace-nowrap">
                      Tài khoản
                    </th>
                    <th className="text-left py-2.5 px-2 text-[12px] font-semibold whitespace-nowrap">
                      Vai trò
                    </th>
                    <th className="text-left py-2.5 px-2 text-[12px] font-semibold whitespace-nowrap">
                      Phạm vi lớp
                    </th>
                    <th className="text-left py-2.5 px-2 text-[12px] font-semibold whitespace-nowrap">
                      Trạng thái
                    </th>
                    <th className="text-left py-2.5 pl-2 pr-3 text-[12px] font-semibold whitespace-nowrap">
                      Cập nhật
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {USERS.filter((u) =>
                    u.name.toLowerCase().includes(search.toLowerCase())
                  ).map((u) => {
                    const isSelected = selected === u.id
                    return (
                      <tr
                        key={u.id}
                        onClick={() => setSelected(u.id)}
                        className={`cursor-pointer transition ${
                          isSelected ? 'bg-[#EBF3FF]/80' : 'hover:bg-slate-50'
                        }`}
                      >
                        <td className="py-3 pl-3 pr-2 whitespace-nowrap">
                          <div className="flex items-center gap-2.5">
                            <div
                              className={`w-8 h-8 rounded-full ${u.avatarBg} ${u.avatarText} text-[11.5px] font-bold flex items-center justify-center flex-shrink-0`}
                            >
                              {u.initials}
                            </div>
                            <div>
                              <p className="font-bold text-slate-900 text-[13px] leading-tight">
                                {u.name}
                              </p>
                              <p className="text-[11px] text-slate-500 mt-0.5">{u.subtitle}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-2 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center justify-center text-[11px] font-semibold px-2 py-0.5 rounded-lg whitespace-nowrap shrink-0 ${u.roleColor}`}
                          >
                            {u.role}
                          </span>
                        </td>
                        <td className="py-3 px-2 text-slate-700 text-[12.5px] font-medium whitespace-nowrap">
                          {u.scope}
                        </td>
                        <td className="py-3 px-2 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap shrink-0 ${u.statusColor}`}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${u.dotColor}`} />
                            {u.status}
                          </span>
                        </td>
                        <td className="py-3 pl-2 pr-3 text-slate-600 text-[12px] whitespace-nowrap">
                          <div className="flex items-center justify-between gap-2">
                            <span>{u.updated}</span>
                            <ChevronRight size={14} className="text-slate-400 shrink-0" />
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN — Floating detail card (5 cols) */}
        {selectedUser && (
          <div className="col-span-5 bg-white rounded-2xl border border-slate-200/70 p-4 px-5 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between min-w-0">
            <div>
              {/* Panel header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-11 h-11 rounded-full ${selectedUser.avatarBg} ${selectedUser.avatarText} font-bold text-[14px] flex items-center justify-center`}
                  >
                    {selectedUser.initials}
                  </div>
                  <div>
                    <p className="font-extrabold text-slate-900 text-[17px]">
                      {selectedUser.name}
                    </p>
                    <p className="text-[12.5px] text-slate-500">{selectedUser.subtitle}</p>
                  </div>
                </div>
                <button className="text-slate-400 hover:text-slate-600 p-1">
                  <X size={18} />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-slate-200 mb-3.5">
                {(['permissions', 'history'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 text-[13px] font-semibold border-b-2 transition -mb-px ${
                      activeTab === tab
                        ? 'border-[#1565F9] text-[#1565F9]'
                        : 'border-transparent text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    {tab === 'permissions' ? 'Quyền' : 'Lịch sử'}
                  </button>
                ))}
              </div>

              {activeTab === 'permissions' ? (
                <div className="space-y-3.5">
                  {/* Thông tin chung */}
                  <div>
                    <p className="text-[13px] font-bold text-slate-900 mb-2">
                      Thông tin chung
                    </p>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 text-[13px]">Vai trò</span>
                        <span
                          className={`text-[11.5px] font-semibold px-2.5 py-0.5 rounded-lg ${selectedUser.roleColor}`}
                        >
                          {selectedUser.role}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 text-[13px]">Phạm vi lớp</span>
                        <span className="flex items-center gap-2 text-[12.5px] font-semibold text-slate-800 border border-slate-200 rounded-xl px-3 py-1 w-40">
                          <BookOpen size={13.5} className="text-[#1565F9] shrink-0" />
                          <span className="truncate">{selectedUser.scope}</span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 text-[13px]">Trạng thái</span>
                        <span
                          className={`inline-flex items-center gap-1.5 text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full ${selectedUser.statusColor}`}
                        >
                          <span className={`w-2 h-2 rounded-full ${selectedUser.dotColor}`} />
                          {selectedUser.status}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 text-[13px]">Cập nhật gần nhất</span>
                        <span className="text-slate-700 font-medium text-[13px]">
                          {selectedUser.updated}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Quyền được cấp */}
                  <div className="pt-3 border-t border-slate-100">
                    <div className="flex items-center gap-1.5 mb-2.5">
                      <p className="text-[13px] font-bold text-slate-900">Quyền được cấp</p>
                      <Info size={13.5} className="text-slate-400" />
                    </div>
                    <div className="grid grid-cols-2 gap-2.5 mb-2.5">
                      <div className="border border-slate-200/80 rounded-xl p-2.5 flex items-start gap-2">
                        <div className="w-7 h-7 rounded-lg bg-[#E2F7EB] text-[#10B981] flex items-center justify-center shrink-0 mt-0.5">
                          <Users size={15} />
                        </div>
                        <div>
                          <p className="text-[12.5px] font-bold text-slate-900">Quản lý lớp</p>
                          <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">
                            Xem và quản lý hoạt động của lớp được phân công
                          </p>
                        </div>
                      </div>
                      <div className="border border-slate-200/80 rounded-xl p-2.5 flex items-start gap-2">
                        <div className="w-7 h-7 rounded-lg bg-[#FEF3C7] text-[#F59E0B] flex items-center justify-center shrink-0 mt-0.5">
                          <List size={15} />
                        </div>
                        <div>
                          <p className="text-[12.5px] font-bold text-slate-900">Điều phối phiên</p>
                          <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">
                            Tạo và điều phối phiên hoạt động
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 bg-[#EAF3FF] rounded-xl px-3 py-2 text-[11.5px] text-slate-700 font-medium">
                      <span className="w-4 h-4 rounded-full bg-[#1565F9] text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                        i
                      </span>
                      <span>Không có quyền nội dung trẻ ngoài phạm vi được cấp.</span>
                    </div>
                  </div>

                  {/* Lý do thay đổi */}
                  <div className="pt-2.5 border-t border-slate-100">
                    <label className="block text-[13px] font-bold text-slate-900 mb-1.5">
                      Lý do thay đổi
                    </label>
                    <textarea
                      rows={2}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="Nhập lý do thay đổi (bắt buộc)"
                      className="w-full border border-slate-200 rounded-xl p-2.5 text-[12.5px] text-slate-700 placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-[#FAFBFD]"
                    />
                  </div>
                </div>
              ) : (
                <div className="text-[13px] text-slate-400 text-center py-8">
                  Chưa có lịch sử thay đổi.
                </div>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 pt-3">
              <button className="flex-1 flex items-center justify-center gap-2 border border-blue-200 bg-[#EAF2FF] text-[#1565F9] text-[13px] font-semibold py-2 rounded-xl hover:bg-blue-100 transition cursor-pointer whitespace-nowrap">
                <Edit2 size={14} />
                <span>Sửa phân công</span>
              </button>
              <button className="flex-1 flex items-center justify-center gap-2 border border-rose-200 bg-[#FEE2E2]/70 text-[#DC2626] text-[13px] font-semibold py-2 rounded-xl hover:bg-rose-100 transition cursor-pointer whitespace-nowrap">
                <Ban size={14} />
                <span>Đình chỉ</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
