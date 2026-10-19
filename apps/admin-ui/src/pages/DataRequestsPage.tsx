import { useState } from 'react'
import { Search, ChevronDown, FileText, Send, X, CheckCircle, Clock, Lock } from 'lucide-react'

// ── Types ────────────────────────────────────────────────────────────────────
type Tab = 'consent' | 'export' | 'delete'

const CONSENT_ROWS = [
  {
    id: 'HS-021',
    class: 'Lớp Lá',
    purposes: 'Vẽ trong lớp, Gợi ý AI',
    status: 'Có hiệu lực',
    statusColor: 'green',
    version: 'v1',
    evidence: 'EV-021',
    updated: '10/10/2026',
  },
  {
    id: 'HS-022',
    class: 'Lớp Lá',
    purposes: 'Vẽ trong lớp, Gợi ý AI',
    status: 'Chờ xác minh',
    statusColor: 'amber',
    version: 'v1',
    evidence: 'EV-022',
    updated: '10/10/2026',
  },
]

export function DataRequestsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('consent')
  const [selectedRow, setSelectedRow] = useState<string | null>('HS-022')

  const TABS: { key: Tab; label: string }[] = [
    { key: 'consent', label: 'Consent' },
    { key: 'export', label: 'Yêu cầu xuất' },
    { key: 'delete', label: 'Yêu cầu xóa' },
  ]

  return (
    <div className="flex h-full overflow-hidden">
      {/* LEFT — main list */}
      <div className="flex-1 flex flex-col overflow-auto p-6 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Consent & yêu cầu dữ liệu</h1>
            <p className="text-sm text-gray-500 mt-0.5">Quản lý consent và các yêu cầu liên quan đến dữ liệu của học sinh</p>
          </div>
          <div className="flex items-center gap-2.5 shrink-0">
            <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2.5 rounded-xl shadow-sm transition">
              <FileText size={16} />
              Ghi nhận consent
            </button>
            <button className="flex items-center gap-2 bg-blue-50 border border-blue-200 hover:bg-blue-100 text-blue-600 text-sm font-semibold px-4 py-2.5 rounded-xl transition">
              <Send size={15} />
              Tiếp nhận yêu cầu
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 pb-1">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`px-4 py-2 text-sm font-medium rounded-xl transition ${
                activeTab === t.key
                  ? 'bg-white text-blue-600 border border-blue-400 font-semibold shadow-sm'
                  : 'text-gray-500 hover:text-gray-800 bg-transparent'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Tìm theo mã học sinh..."
            />
          </div>
          {[
            { label: 'Lớp học', value: 'Tất cả' },
            { label: 'Trạng thái', value: 'Tất cả' },
          ].map((f) => (
            <div key={f.label} className="flex items-center gap-2 text-sm text-gray-600">
              <span className="font-medium">{f.label}</span>
              <button className="flex items-center gap-2 border border-gray-300 bg-white px-3 py-2 rounded-lg hover:bg-gray-50">
                {f.value}
                <ChevronDown size={13} className="text-gray-400" />
              </button>
            </div>
          ))}
        </div>

        {/* Table */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                {['Mã học sinh', 'Lớp học', 'Mục đích', 'Trạng thái', 'Phiên bản', 'Bằng chứng', 'Cập nhật gần nhất', ''].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CONSENT_ROWS.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => setSelectedRow(row.id)}
                  className={`border-b border-gray-50 cursor-pointer ${
                    selectedRow === row.id ? 'bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                >
                  <td className="px-4 py-3.5 font-semibold text-gray-900">{row.id}</td>
                  <td className="px-4 py-3.5 text-gray-600">{row.class}</td>
                  <td className="px-4 py-3.5 text-gray-600">{row.purposes}</td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${
                        row.statusColor === 'green'
                          ? 'bg-green-50 text-green-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${row.statusColor === 'green' ? 'bg-green-500' : 'bg-amber-500'}`} />
                      {row.status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-gray-600">{row.version}</td>
                  <td className="px-4 py-3.5 text-blue-600 font-medium">{row.evidence}</td>
                  <td className="px-4 py-3.5 text-gray-600">{row.updated}</td>
                  <td className="px-4 py-3.5 text-gray-400">
                    <button className="hover:text-gray-600">···</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 text-sm text-gray-500 border-t border-gray-100">
            <span>Hiển thị 1 - 2 của 2 bản ghi</span>
            <div className="flex items-center gap-1">
              <button className="w-7 h-7 border border-gray-200 rounded flex items-center justify-center hover:bg-gray-100 text-gray-400">&lsaquo;</button>
              <button className="w-7 h-7 border border-blue-500 bg-blue-500 text-white rounded flex items-center justify-center text-xs font-semibold">1</button>
              <button className="w-7 h-7 border border-gray-200 rounded flex items-center justify-center hover:bg-gray-100 text-gray-400">&rsaquo;</button>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT — Detail panel */}
      {selectedRow && (
        <div className="w-96 shrink-0 border-l border-gray-200 bg-white overflow-auto">
          <div className="flex items-start justify-between p-5 border-b border-gray-100">
            <div>
              <h2 className="text-base font-semibold text-gray-900">Chi tiết consent</h2>
              <p className="text-xs text-gray-500 mt-0.5">Thông tin consent và trạng thái xác minh</p>
            </div>
            <button onClick={() => setSelectedRow(null)} className="text-gray-400 hover:text-gray-600">
              <X size={16} />
            </button>
          </div>

          <div className="p-5 space-y-5">
            {/* Student header */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 text-lg">🎓</div>
              <div className="flex-1">
                <p className="text-base font-bold text-gray-900">HS-022</p>
                <p className="text-xs text-gray-500">Lớp Lá</p>
              </div>
              <span className="inline-flex items-center gap-1.5 text-xs font-medium bg-amber-50 text-amber-700 px-2.5 py-1 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                Chờ xác minh
              </span>
            </div>

            {/* Thông tin chung */}
            <div>
              <h3 className="text-xs font-semibold text-gray-700 mb-3">Thông tin chung</h3>
              <div className="space-y-2.5">
                {[
                  { icon: '🏫', label: 'Nguồn', value: 'Nhà trường thu thập' },
                  { icon: '📄', label: 'Phiên bản thông báo', value: 'v1' },
                  { icon: '📄', label: 'Bằng chứng (mã)', value: 'EV-022' },
                  { icon: '👤', label: 'Người ghi', value: 'GV An' },
                  { icon: '🕐', label: 'Cập nhật gần nhất', value: '10/10/2026' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-gray-500 text-sm">
                      <span>{item.icon}</span>
                      {item.label}
                    </div>
                    <span className="text-sm font-medium text-gray-800">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Mục đích được consent */}
            <div>
              <h3 className="text-xs font-semibold text-gray-700 mb-3">Mục đích được consent</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 rounded-lg border border-gray-100">
                  <CheckCircle size={16} className="text-green-500 mt-0.5 shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-800">Vẽ trong lớp</p>
                      <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full font-medium">● Có hiệu lực</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">Sử dụng tác phẩm vẽ trong các hoạt động học tập tại lớp.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-lg border border-gray-100">
                  <Clock size={16} className="text-amber-500 mt-0.5 shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-800">Gợi ý AI</p>
                      <span className="text-xs bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full font-medium">● Chờ xác minh</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">Sử dụng tác phẩm vẽ để gợi ý ý tưởng bằng AI trong lớp.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Red alert */}
            <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-100">
              <span className="text-red-500 text-base mt-0.5">⚠️</span>
              <div>
                <p className="text-sm font-semibold text-red-700">Chưa xác minh không kích hoạt mục đích bị hạn chế.</p>
                <p className="text-xs text-red-600 mt-0.5">Chỉ sử dụng dữ liệu cho các mục đích đã được xác minh và có hiệu lực.</p>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="p-5 border-t border-gray-100 flex items-center gap-2">
            <button className="flex-1 flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold py-2.5 rounded-xl transition shadow-sm">
              <FileText size={14} />
              Yêu cầu bổ sung
            </button>
            <button className="flex-1 flex items-center justify-center gap-1.5 bg-blue-50 border border-blue-200 hover:bg-blue-100 text-blue-600 text-xs font-semibold py-2.5 rounded-xl transition">
              <Clock size={14} />
              Xem lịch sử
            </button>
            <button
              disabled
              className="flex-1 flex items-center justify-center gap-1.5 border border-gray-200 bg-gray-50 text-gray-400 text-xs font-medium py-2.5 rounded-xl cursor-not-allowed"
            >
              <Lock size={13} />
              <span className="text-[11px] leading-tight">Chưa có quyền xem bằng chứng</span>
            </button>
          </div>
        </div>
      )}

      {/* Watermark */}
      <div className="fixed bottom-3 right-6 text-xs text-gray-400 pointer-events-none">
        Dữ liệu minh họa • Bản thiết kế UI.
      </div>
    </div>
  )
}
