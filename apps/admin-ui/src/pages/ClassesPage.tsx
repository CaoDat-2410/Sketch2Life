import { useState } from 'react'
import { Plus, Search, CheckCircle, AlertCircle, Edit, Trash2 } from 'lucide-react'

const CLASSES = [
  { id: 1, name: 'Lớp Lá', ageGroup: '6 – 8 tuổi', teacher: 'GV An', profiles: 24, ready: true, readyLabel: 'Đủ điều kiện', status: 'Hoạt động', iconBg: 'bg-emerald-100 text-emerald-600', icon: '🌱' },
  { id: 2, name: 'Lớp Hoa', ageGroup: '3 – 5 tuổi', teacher: 'GV Bình', profiles: 16, ready: false, readyLabel: 'Cần kiểm tra chính sách', status: 'Hoạt động', iconBg: 'bg-red-100 text-red-500', icon: '🌸' },
]

export function ClassesPage() {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<number>(1)
  const sel = CLASSES.find((c) => c.id === selected)

  return (
    <div className="flex h-full overflow-hidden">
      {/* LEFT */}
      <div className="flex-1 overflow-auto p-6 flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between mb-5">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Lớp học &amp; phân công</h1>
              <p className="text-sm text-gray-500 mt-0.5">Quản lý lớp học, phân công giáo viên và kiểm tra điều kiện vận hành</p>
            </div>
            <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition shadow-sm">
              <Plus size={16} />
              Tạo lớp
            </button>
          </div>

          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
                <span className="text-sm">📋</span>
              </div>
              <h2 className="text-sm font-semibold text-gray-800">Danh sách lớp học</h2>
            </div>

            <div className="relative mb-4">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Tìm theo tên lớp hoặc giáo viên..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              />
            </div>

            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Lớp</th>
                  <th className="text-left py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Nhóm tuổi</th>
                  <th className="text-left py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Giáo viên</th>
                  <th className="text-left py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Hồ sơ</th>
                  <th className="text-left py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Sẵn sàng</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {CLASSES.filter((c) => c.name.includes(search) || c.teacher.includes(search)).map((cls) => (
                  <tr
                    key={cls.id}
                    onClick={() => setSelected(cls.id)}
                    className={`cursor-pointer transition ${selected === cls.id ? 'bg-blue-50/80 ring-2 ring-blue-500/80 rounded-xl' : 'hover:bg-gray-50'}`}
                  >
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-9 h-9 rounded-xl ${cls.iconBg} flex items-center justify-center text-lg flex-shrink-0`}>
                          {cls.icon}
                        </div>
                        <span className="font-semibold text-gray-900">{cls.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-gray-600">{cls.ageGroup}</td>
                    <td className="py-3 px-3 text-gray-600">{cls.teacher}</td>
                    <td className="py-3 px-3 text-gray-600">{cls.profiles}</td>
                    <td className="py-3 px-3">
                      {cls.ready ? (
                        <span className="inline-flex items-center gap-1.5 text-green-700 bg-green-50 px-2.5 py-1 rounded-full text-xs font-semibold">
                          <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                          {cls.readyLabel}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full text-xs font-semibold">
                          <span className="w-1.5 h-1.5 bg-amber-400 rounded-full"></span>
                          {cls.readyLabel}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Watermark */}
        <div className="text-right text-xs text-gray-400 pt-4">
          Dữ liệu minh họa • Bản thiết kế UI.
        </div>
      </div>

      {/* RIGHT panel */}
      {sel && (
        <div className="w-96 flex-shrink-0 border-l border-gray-100 bg-white overflow-auto">
          <div className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 ${sel.iconBg} rounded-2xl flex items-center justify-center text-2xl flex-shrink-0`}>
                  {sel.icon}
                </div>
                <div>
                  <p className="font-bold text-gray-900 text-lg">{sel.name}</p>
                  <p className="text-xs text-gray-500">Thông tin lớp học và điều kiện vận hành</p>
                </div>
              </div>
              <span className="flex items-center gap-1.5 text-xs font-semibold text-green-700 bg-green-50 px-2.5 py-1 rounded-full border border-green-100">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                {sel.status}
              </span>
            </div>

            {/* General info */}
            <div className="bg-white border border-gray-100 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm">📋</span>
                  <h3 className="text-sm font-semibold text-gray-800">Thông tin chung</h3>
                </div>
                <button className="flex items-center gap-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-semibold px-2.5 py-1 rounded-lg transition">
                  <Edit size={12} />
                  Chỉnh sửa
                </button>
              </div>
              <div className="space-y-2.5 text-sm">
                {[
                  { label: 'Tên lớp', value: sel.name },
                  { label: 'Giáo viên phụ trách', value: `👤 ${sel.teacher}`, hasAction: true },
                  { label: 'Chính sách nhóm tuổi', value: 'v1', hasAction: true },
                  { label: 'Số lượng hồ sơ', value: `${sel.profiles} hồ sơ` },
                  { label: 'Trạng thái', value: sel.status, isStatus: true },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between">
                    <span className="text-gray-500">{row.label}</span>
                    <div className="flex items-center gap-2">
                      {row.isStatus ? (
                        <span className="flex items-center gap-1.5 text-green-600 font-semibold text-xs">
                          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                          {row.value}
                        </span>
                      ) : (
                        <span className="font-medium text-gray-800 text-xs">{row.value}</span>
                      )}
                      {row.hasAction && (
                        <button className="text-xs text-blue-600 bg-blue-50 hover:bg-blue-100 px-2.5 py-0.5 rounded-lg font-semibold transition">
                          Thay đổi
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Readiness checks */}
            <div className="bg-white border border-gray-100 rounded-xl p-4 mb-5">
              <div className="flex items-center gap-2 mb-3">
                <span>🛡️</span>
                <h3 className="text-sm font-semibold text-gray-800">Kiểm tra điều kiện sẵn sàng</h3>
              </div>
              <div className="space-y-3">
                {[
                  { ok: true, title: 'Phân công giáo viên', desc: 'Đã phân công giáo viên phụ trách lớp.' },
                  { ok: true, title: 'Chính sách nhóm tuổi', desc: 'Đã áp dụng phiên bản chính sách phù hợp.' },
                  { ok: false, title: 'Consent: kiểm tra theo mục đích', desc: 'Kiểm tra và xác nhận consent theo mục đích sử dụng nội dung trong lớp.' },
                ].map((item) => (
                  <div key={item.title} className="flex items-start gap-2.5">
                    {item.ok ? (
                      <CheckCircle size={17} className="text-green-500 flex-shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle size={17} className="text-amber-500 flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{item.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 mb-2">
              <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-3 rounded-xl transition shadow-sm">
                Lưu thay đổi
              </button>
              <button className="flex-1 flex items-center justify-center gap-2 bg-red-50 border border-red-100 text-red-500 text-sm font-semibold py-3 rounded-xl hover:bg-red-100 transition">
                <Trash2 size={14} />
                Lưu trữ lớp
              </button>
            </div>
            <p className="text-xs text-gray-400 text-center">Lưu trữ lớp không xóa hồ sơ hay lịch sử đóng góp.</p>
          </div>
        </div>
      )}
    </div>
  )
}
