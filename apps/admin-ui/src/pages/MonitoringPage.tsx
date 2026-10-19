import { useState } from 'react'
import { RefreshCw, Calendar, Filter, X, Users, BookOpen } from 'lucide-react'

const INCIDENTS = [
  { id: 'INC-024', desc: 'Video chưa hoàn thành', scope: 'Phiên S-024', status: 'Đang xử lý', statusColor: 'text-blue-600 bg-blue-50', handler: 'QT Minh' },
  { id: 'INC-025', desc: 'Chưa nhận checkpoint', scope: 'Nhóm G-03', status: 'Chờ kiểm tra', statusColor: 'text-amber-600 bg-amber-50', handler: 'Chưa phân công' },
]

const TIMELINE = [
  { color: 'bg-green-500', title: 'Yêu cầu tạo video', desc: 'Hệ thống ghi nhận yêu cầu tạo video.', time: '10/10/2026 09:12' },
  { color: 'bg-red-500', title: 'Đã ghi nhận lỗi', desc: 'Hệ thống phát hiện lỗi khi xử lý tác vụ.', time: '10/10/2026 09:18' },
  { color: 'bg-gray-300', title: 'Chờ quyết định giáo viên', desc: 'Đang chờ giáo viên kiểm tra và quyết định bước tiếp theo.', time: '10/10/2026 09:36' },
]

export function MonitoringPage() {
  const [selected, setSelected] = useState<string>('INC-024')
  const [showBanner, setShowBanner] = useState(true)
  const sel = INCIDENTS.find((i) => i.id === selected)

  return (
    <div className="flex h-full overflow-hidden flex-col">
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT */}
        <div className="flex-1 overflow-auto p-6 flex flex-col gap-5">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Giám sát &amp; sự cố</h1>
              <p className="text-sm text-gray-500 mt-0.5">Theo dõi hoạt động hệ thống và xử lý các sự cố</p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 bg-white border border-gray-200 text-gray-600 text-sm font-medium px-3 py-2 rounded-lg hover:bg-gray-50 transition">
                  <Calendar size={14} />
                  Hôm nay
                  <svg width="12" height="12" viewBox="0 0 12 12"><path d="M3 4.5L6 7.5L9 4.5" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round"/></svg>
                </button>
                <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition">
                  <RefreshCw size={14} />
                  Làm mới
                </button>
              </div>
              <p className="text-xs text-gray-400">Cập nhật lúc 09:40</p>
            </div>
          </div>

          {/* Status cards */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { icon: '⚙️', bg: 'bg-green-50', label: 'API', value: <span className="flex items-center gap-2 text-2xl font-bold text-green-600"><span className="w-3 h-3 bg-green-500 rounded-full"></span>Hoạt động</span>, sub: 'Các dịch vụ hoạt động bình thường.' },
              { icon: '🗄️', bg: 'bg-amber-50', label: 'Checkpoint', value: <span className="flex items-center gap-3"><span className="text-3xl font-bold text-gray-900">1</span><span className="text-amber-600 font-semibold text-lg">● cần kiểm tra</span></span>, sub: 'Có checkpoint cần được kiểm tra.' },
              { icon: '📋', bg: 'bg-orange-50', label: 'Hàng đợi AI', value: <span className="flex items-center gap-2 text-2xl font-bold text-amber-600"><span className="w-3 h-3 bg-amber-400 rounded-full"></span>Có độ trễ</span>, sub: 'Một số tác vụ đang chờ xử lý.' },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-10 h-10 ${s.bg} rounded-xl flex items-center justify-center text-xl`}>{s.icon}</div>
                  <p className="text-sm text-gray-500">{s.label}</p>
                </div>
                <div className="mb-1">{s.value}</div>
                <p className="text-xs text-gray-400">{s.sub}</p>
              </div>
            ))}
          </div>

          {/* Incidents table */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 flex-1">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-red-500 text-lg">⚠</span>
                <h2 className="text-sm font-semibold text-gray-800">Sự cố đang mở</h2>
              </div>
              <button className="flex items-center gap-2 border border-gray-200 text-gray-600 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-gray-50 transition">
                <Filter size={13} />
                Tất cả trạng thái
                <svg width="12" height="12" viewBox="0 0 12 12"><path d="M3 4.5L6 7.5L9 4.5" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round"/></svg>
              </button>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  {['Mã', 'Mô tả', 'Phạm vi', 'Trạng thái', 'Người xử lý'].map((h) => (
                    <th key={h} className="text-left py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {INCIDENTS.map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => setSelected(inc.id)}
                    className={`border-b border-gray-50 last:border-0 cursor-pointer transition ${selected === inc.id ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                  >
                    <td className="py-3 pr-4 font-mono text-xs font-semibold text-gray-700">{inc.id}</td>
                    <td className="py-3 pr-4 font-medium text-gray-800">{inc.desc}</td>
                    <td className="py-3 pr-4 text-gray-500">{inc.scope}</td>
                    <td className="py-3 pr-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${inc.statusColor}`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60"></span>
                        {inc.status}
                      </span>
                    </td>
                    <td className="py-3 text-gray-600">{inc.handler}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT panel */}
        {sel && (
          <div className="w-96 flex-shrink-0 border-l border-gray-100 bg-white overflow-auto">
            <div className="p-5">
              <div className="flex items-start gap-3 mb-5">
                <div className="w-9 h-9 bg-red-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-red-500 text-lg">⚠</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-bold text-gray-900 text-base">{sel.id}</p>
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${sel.statusColor}`}>
                      ● {sel.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5">{sel.desc}</p>
                </div>
              </div>

              <div className="space-y-2.5 text-sm mb-5">
                {[
                  { label: 'Mã tương quan', value: 'COR-024' },
                  { label: 'Nguồn', value: 'Ứng dụng (sự kiện hệ thống)' },
                  { label: 'Phạm vi', value: sel.scope },
                  { label: 'Trạng thái', value: sel.status, isStatus: true },
                  { label: 'Người xử lý', value: sel.handler },
                  { label: 'Ngày tạo', value: '10/10/2026 09:12' },
                  { label: 'Cập nhật gần nhất', value: '10/10/2026 09:36' },
                ].map((row) => (
                  <div key={row.label} className="flex items-start justify-between border-b border-gray-50 pb-2.5 last:border-0">
                    <span className="text-gray-500 flex-shrink-0 w-36">{row.label}</span>
                    {row.isStatus ? (
                      <span className="text-blue-600 font-semibold">● {row.value}</span>
                    ) : (
                      <span className="text-gray-800 font-medium text-right">{row.value}</span>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-2 mb-3">
                <span className="text-gray-400 text-sm">🕐</span>
                <p className="text-sm font-semibold text-gray-800">Dòng thời gian xử lý</p>
              </div>
              <div className="space-y-0 relative ml-3">
                {TIMELINE.map((t, i) => (
                  <div key={t.title} className="flex gap-3 pb-5 last:pb-0 relative">
                    <div className="flex flex-col items-center">
                      <div className={`w-3 h-3 rounded-full ${t.color} flex-shrink-0 mt-0.5 z-10`}></div>
                      {i < TIMELINE.length - 1 && <div className="w-0.5 flex-1 bg-gray-200 mt-1"></div>}
                    </div>
                    <div className="flex-1 pb-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-semibold text-gray-800">{t.title}</p>
                        <span className="text-xs text-gray-400">{t.time}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{t.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-2 mt-5">
                <button className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2.5 rounded-xl transition shadow-sm">
                  <Users size={14} />
                  Phân công
                </button>
                <button className="flex-1 flex items-center justify-center gap-2 border border-blue-200 bg-white text-blue-600 text-sm font-semibold py-2.5 rounded-xl hover:bg-blue-50 transition">
                  <BookOpen size={14} />
                  Mở runbook
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom banner & watermark */}
      <div className="flex items-center justify-between border-t border-blue-100 bg-blue-50 px-6 py-2.5 flex-shrink-0">
        {showBanner ? (
          <div className="flex items-center gap-2 text-sm text-blue-700 flex-1">
            <span className="text-blue-500 font-bold">ℹ</span>
            <span>Chỉ hiển thị dữ liệu vận hành đã lược bỏ thông tin nhạy cảm.</span>
            <button onClick={() => setShowBanner(false)} className="text-blue-400 hover:text-blue-600 ml-2">
              <X size={15} />
            </button>
          </div>
        ) : <div className="flex-1" />}
        <span className="text-xs text-gray-400 shrink-0">Dữ liệu minh họa • Bản thiết kế UI.</span>
      </div>
    </div>
  )
}
