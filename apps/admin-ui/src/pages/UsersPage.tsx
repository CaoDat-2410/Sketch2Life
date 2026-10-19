import { useState } from 'react'
import { UserPlus, Search, ChevronRight, X, Info, Edit, Ban, BookOpen } from 'lucide-react'

const USERS = [
  { id: 1, initials: 'GA', color: 'bg-blue-100 text-blue-700', name: 'GV An', sub: 'Giáo viên', role: 'Giáo viên', roleColor: 'bg-blue-50 text-blue-700', scope: 'Lớp Lá', status: 'Đang hoạt động', statusColor: 'text-green-600', statusDot: 'bg-green-500', updated: '10/10/2026' },
  { id: 2, initials: 'GB', color: 'bg-emerald-100 text-emerald-700', name: 'GV Bình', sub: 'Giáo viên', role: 'Giáo viên', roleColor: 'bg-blue-50 text-blue-700', scope: 'Lớp Hoa', status: 'Chờ nhận lời mời', statusColor: 'text-amber-600', statusDot: 'bg-amber-400', updated: '09/10/2026' },
  { id: 3, initials: 'QM', color: 'bg-purple-100 text-purple-700', name: 'QT Minh', sub: 'Quản trị hệ thống', role: 'Quản trị viên', roleColor: 'bg-purple-50 text-purple-700', scope: 'Trường Mầm Xanh', status: 'Đang hoạt động', statusColor: 'text-green-600', statusDot: 'bg-green-500', updated: '08/10/2026' },
]

export function UsersPage() {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<number>(1)

  const sel = USERS.find((u) => u.id === selected)

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── LEFT ── */}
      <div className="flex-1 overflow-auto p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-5">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Người dùng &amp; vai trò</h1>
            <p className="text-sm text-gray-500 mt-0.5">Quản lý tài khoản người lớn và quyền theo lớp.</p>
          </div>
          <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition">
            <UserPlus size={15} />
            Mời người dùng
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-4 items-end">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm tài khoản (tên hiển thị)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-500">Vai trò</label>
            <select className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[130px]">
              <option>Tất cả</option>
              <option>Giáo viên</option>
              <option>Quản trị viên</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-500">Trạng thái</label>
            <select className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[150px]">
              <option>Tất cả</option>
              <option>Đang hoạt động</option>
              <option>Chờ nhận lời mời</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Tài khoản</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Vai trò</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Phạm vi lớp</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Trạng thái</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Cập nhật</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {USERS.filter((u) => u.name.toLowerCase().includes(search.toLowerCase())).map((user) => (
                <tr
                  key={user.id}
                  onClick={() => setSelected(user.id)}
                  className={`border-b border-gray-50 last:border-0 cursor-pointer transition ${selected === user.id ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                >
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-full ${user.color} flex items-center justify-center text-xs font-bold flex-shrink-0`}>
                        {user.initials}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-800">{user.name}</p>
                        <p className="text-xs text-gray-400">{user.sub}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-lg ${user.roleColor}`}>{user.role}</span>
                  </td>
                  <td className="px-4 py-3.5 text-gray-600">{user.scope}</td>
                  <td className="px-4 py-3.5">
                    <span className={`flex items-center gap-1.5 text-sm font-medium ${user.statusColor}`}>
                      <span className={`w-2 h-2 rounded-full ${user.statusDot} inline-block`}></span>
                      {user.status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-gray-500 text-xs">{user.updated}</td>
                  <td className="px-4 py-3.5">
                    <ChevronRight size={16} className="text-gray-300" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── RIGHT panel ── */}
      {sel && (
        <div className="w-80 flex-shrink-0 border-l border-gray-100 bg-white overflow-auto">
          <div className="p-5">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`w-11 h-11 rounded-full ${sel.color} flex items-center justify-center text-sm font-bold flex-shrink-0`}>
                  {sel.initials}
                </div>
                <div>
                  <p className="font-bold text-gray-900">{sel.name}</p>
                  <p className="text-sm text-gray-500">{sel.sub}</p>
                </div>
              </div>
              <button onClick={() => setSelected(0)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-100 mb-5">
              <button className="px-4 py-2.5 text-sm font-semibold text-blue-600 border-b-2 border-blue-600">Quyền</button>
              <button className="px-4 py-2.5 text-sm text-gray-500 hover:text-gray-700">Lịch sử</button>
            </div>

            {/* Info */}
            <div className="mb-5">
              <p className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-3">Thông tin chung</p>
              <div className="space-y-2.5 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Vai trò</span>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-lg ${sel.roleColor}`}>{sel.role}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Phạm vi lớp</span>
                  <div className="border border-gray-200 rounded-lg px-3 py-1 flex items-center gap-2 font-medium text-gray-800 bg-white">
                    <BookOpen size={14} className="text-blue-600" />
                    <span>{sel.scope}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Trạng thái</span>
                  <span className={`flex items-center gap-1.5 text-sm font-semibold ${sel.statusColor}`}>
                    <span className={`w-2 h-2 rounded-full ${sel.statusDot} inline-block`}></span>
                    {sel.status}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Cập nhật gần nhất</span>
                  <span className="text-gray-700">{sel.updated}</span>
                </div>
              </div>
            </div>

            {/* Permissions */}
            <div className="mb-5">
              <div className="flex items-center gap-1.5 mb-3">
                <p className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Quyền được cấp</p>
                <Info size={13} className="text-gray-400" />
              </div>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-green-50 border border-green-100 rounded-xl p-3">
                  <div className="w-7 h-7 bg-green-100 rounded-lg flex items-center justify-center mb-2">
                    <span className="text-sm">👥</span>
                  </div>
                  <p className="text-xs font-semibold text-gray-800">Quản lý lớp</p>
                  <p className="text-[11px] text-gray-500 mt-0.5 leading-tight">Xem và quản lý hoạt động của lớp được phân công</p>
                </div>
                <div className="bg-amber-50 border border-amber-100 rounded-xl p-3">
                  <div className="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center mb-2">
                    <span className="text-sm">📋</span>
                  </div>
                  <p className="text-xs font-semibold text-gray-800">Điều phối phiên</p>
                  <p className="text-[11px] text-gray-500 mt-0.5 leading-tight">Tạo và điều phối phiên hoạt động</p>
                </div>
              </div>
              <div className="bg-blue-50 rounded-xl p-3">
                <p className="text-xs text-blue-700">
                  <span className="font-semibold">ℹ</span> Không có quyền nội dung trẻ ngoài phạm vi được cấp.
                </p>
              </div>
            </div>

            {/* Reason */}
            <div className="mb-5">
              <p className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Lý do thay đổi</p>
              <textarea
                placeholder="Nhập lý do thay đổi (bắt buộc)"
                rows={3}
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button className="flex-1 flex items-center justify-center gap-2 bg-blue-50 border border-blue-200 text-blue-600 text-sm font-semibold py-2.5 rounded-xl hover:bg-blue-100 transition">
                <Edit size={14} />
                Sửa phân công
              </button>
              <button className="flex-1 flex items-center justify-center gap-2 bg-red-50 border border-red-200 text-red-500 text-sm font-semibold py-2.5 rounded-xl hover:bg-red-100 transition">
                <Ban size={14} />
                Đình chỉ
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
