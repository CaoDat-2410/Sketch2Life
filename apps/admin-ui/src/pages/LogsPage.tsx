import { useState } from 'react'
import {
  ChevronDown,
  Search,
  Link as LinkIcon,
  Download,
  X,
  AlertTriangle,
  Calendar,
  ListFilter,
  Layers,
  CheckCircle2,
  ArrowUpDown,
  Info,
} from 'lucide-react'

const LOG_ROWS = [
  {
    time: '10/10/2026 09:40',
    actor: 'AD-01',
    action: 'Đổi phân công',
    resource: 'CL-01',
    version: 'v3',
    result: 'Thành công',
    resultColor: 'green',
  },
  {
    time: '10/10/2026 09:36',
    actor: 'AD-01',
    action: 'Duyệt nội dung',
    resource: 'CT-08',
    version: 'v2',
    result: 'Thành công',
    resultColor: 'green',
  },
  {
    time: '10/10/2026 09:31',
    actor: 'AC-02',
    action: 'Yêu cầu truy cập',
    resource: 'RS-07',
    version: 'v1',
    result: 'Từ chối',
    resultColor: 'red',
  },
]

export function LogsPage() {
  const [selectedLog, setSelectedLog] = useState<(typeof LOG_ROWS)[0] | null>(LOG_ROWS[2])
  const [showBanner, setShowBanner] = useState(true)

  return (
    <div className="flex h-full overflow-hidden">
      {/* LEFT — main */}
      <div className="flex-1 flex flex-col overflow-auto p-6 space-y-5">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Nhật ký kiểm toán</h1>
          <p className="text-sm text-gray-500 mt-1">Theo dõi các hoạt động quản trị, truy cập và thay đổi trong hệ thống</p>
        </div>

        {/* Filters Card */}
        <div className="bg-white border border-gray-200/80 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Row 1 col 1 */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-600">Khoảng thời gian</label>
              <button className="flex items-center justify-between border border-gray-200 bg-white text-sm text-gray-700 px-3.5 py-2.5 rounded-xl hover:bg-gray-50 w-full transition shadow-sm">
                <div className="flex items-center gap-2 text-gray-700">
                  <Calendar size={16} className="text-gray-400" />
                  <span>10/10/2026</span>
                </div>
                <ChevronDown size={14} className="text-gray-400" />
              </button>
            </div>
            {/* Row 1 col 2 */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-600">Hành động</label>
              <button className="flex items-center justify-between border border-gray-200 bg-white text-sm text-gray-700 px-3.5 py-2.5 rounded-xl hover:bg-gray-50 w-full transition shadow-sm">
                <div className="flex items-center gap-2 text-gray-700">
                  <ListFilter size={16} className="text-gray-400" />
                  <span>Tất cả</span>
                </div>
                <ChevronDown size={14} className="text-gray-400" />
              </button>
            </div>
            {/* Row 1 col 3 */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-600">Phạm vi</label>
              <button className="flex items-center justify-between border border-gray-200 bg-white text-sm text-gray-700 px-3.5 py-2.5 rounded-xl hover:bg-gray-50 w-full transition shadow-sm">
                <div className="flex items-center gap-2 text-gray-700">
                  <Layers size={16} className="text-gray-400" />
                  <span>Tất cả</span>
                </div>
                <ChevronDown size={14} className="text-gray-400" />
              </button>
            </div>

            {/* Row 2 col 1: Kết quả */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-600">Kết quả</label>
              <button className="flex items-center justify-between border border-gray-200 bg-white text-sm text-gray-700 px-3.5 py-2.5 rounded-xl hover:bg-gray-50 w-full transition shadow-sm">
                <div className="flex items-center gap-2 text-gray-700">
                  <CheckCircle2 size={16} className="text-gray-400" />
                  <span>Tất cả</span>
                </div>
                <ChevronDown size={14} className="text-gray-400" />
              </button>
            </div>

            {/* Row 2 col 2-3: Tra cứu correlation */}
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-semibold text-gray-600">Tra cứu correlation</label>
              <div className="relative">
                <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  className="w-full pl-10 pr-3.5 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm transition"
                  placeholder="Nhập mã correlation (ví dụ: COR-031)"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Table Card */}
        <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50/70 border-b border-gray-100">
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">
                  <div className="flex items-center gap-1.5">
                    <span>Thời điểm</span>
                    <ArrowUpDown size={13} className="text-gray-400" />
                  </div>
                </th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Actor ref</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Hành động</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Resource</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Phiên bản</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Kết quả</th>
              </tr>
            </thead>
            <tbody>
              {LOG_ROWS.map((row) => {
                const isSelected = selectedLog?.actor === row.actor && selectedLog?.time === row.time
                return (
                  <tr
                    key={row.time + row.actor}
                    onClick={() => setSelectedLog(row)}
                    className={`border-b border-gray-50 cursor-pointer transition ${
                      isSelected
                        ? 'bg-blue-50/70'
                        : 'hover:bg-gray-50/60'
                    }`}
                  >
                    <td className="px-5 py-4 text-gray-600 whitespace-nowrap">{row.time}</td>
                    <td className="px-5 py-4 font-semibold text-gray-900">{row.actor}</td>
                    <td className="px-5 py-4 text-gray-800">{row.action}</td>
                    <td className="px-5 py-4 text-gray-600">{row.resource}</td>
                    <td className="px-5 py-4 text-gray-600">{row.version}</td>
                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${
                          row.resultColor === 'green'
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-rose-50 text-rose-700'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            row.resultColor === 'green' ? 'bg-emerald-500' : 'bg-rose-500'
                          }`}
                        />
                        {row.result}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Footer info banner */}
        {showBanner && (
          <div className="flex items-center justify-between gap-3 bg-blue-50/70 border border-blue-200/80 rounded-xl px-4 py-3 text-sm text-blue-700">
            <div className="flex items-center gap-2">
              <Info size={16} className="text-blue-600 shrink-0" />
              <span>Nhật ký đã lược bỏ dữ liệu nhạy cảm • Chỉ đọc.</span>
            </div>
            <button
              onClick={() => setShowBanner(false)}
              className="text-gray-400 hover:text-gray-600 transition"
            >
              <X size={15} />
            </button>
          </div>
        )}

        {/* Footer actions */}
        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-gray-500">Đã hiển thị 3 kết quả</span>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 border border-blue-200 bg-white hover:bg-blue-50 text-blue-600 text-sm font-semibold px-4 py-2.5 rounded-xl shadow-sm transition">
              <LinkIcon size={15} />
              Liên kết sự cố
            </button>
            <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2.5 rounded-xl shadow-sm transition">
              <Download size={15} />
              Xuất nhật ký theo quyền
            </button>
          </div>
        </div>

        {/* Watermark */}
        <div className="text-right text-xs text-gray-400 py-1">
          Dữ liệu minh họa • Bản thiết kế UI.
        </div>
      </div>

      {/* RIGHT — Event detail panel */}
      {selectedLog && (
        <div className="w-[380px] shrink-0 border-l border-gray-200 bg-white overflow-auto flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between p-5 border-b border-gray-100">
              <div className="flex items-center gap-2.5">
                <AlertTriangle size={18} className="text-rose-500" />
                <h2 className="text-base font-bold text-gray-900">Chi tiết sự kiện</h2>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-gray-400 hover:text-gray-600 transition p-1"
              >
                <X size={16} />
              </button>
            </div>

            <div className="p-5 space-y-5">
              {/* Alert Card */}
              <div
                className={`flex items-start gap-3 p-3.5 rounded-xl border ${
                  selectedLog.resultColor === 'red'
                    ? 'bg-rose-50/80 border-rose-100'
                    : 'bg-emerald-50/80 border-emerald-100'
                }`}
              >
                <AlertTriangle
                  size={18}
                  className={`mt-0.5 shrink-0 ${
                    selectedLog.resultColor === 'red' ? 'text-rose-500' : 'text-emerald-500'
                  }`}
                />
                <div>
                  <p
                    className={`text-sm font-bold ${
                      selectedLog.resultColor === 'red' ? 'text-rose-700' : 'text-emerald-700'
                    }`}
                  >
                    {selectedLog.resultColor === 'red' ? 'Yêu cầu truy cập bị từ chối' : selectedLog.action + ' thành công'}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">{selectedLog.time}</p>
                </div>
              </div>

              {/* Metadata Key-Value pairs */}
              <div className="space-y-3">
                {[
                  { label: 'Correlation', value: 'COR-031' },
                  {
                    label: 'Actor ref',
                    value: selectedLog.actor,
                    sub: selectedLog.actor === 'AC-02' ? 'Tài khoản quản trị viên' : 'Admin',
                  },
                  { label: 'Hành động', value: selectedLog.action },
                  {
                    label: 'Resource',
                    value: selectedLog.resource,
                    sub: selectedLog.resource === 'RS-07' ? 'Tài nguyên hệ thống' : '',
                  },
                  { label: 'Phiên bản', value: selectedLog.version },
                  { label: 'Kết quả', value: selectedLog.result, isStatus: true, color: selectedLog.resultColor },
                  { label: 'Mục đích', value: 'Điều tra sự cố' },
                  { label: 'Quyết định', value: 'Không có grant phù hợp' },
                  { label: 'Chính sách áp dụng', value: 'v1' },
                  { label: 'Thời điểm', value: selectedLog.time },
                ].map((item) => (
                  <div key={item.label} className="flex items-start justify-between gap-4 py-0.5">
                    <span className="text-xs text-gray-500 shrink-0">{item.label}</span>
                    <div className="text-right">
                      {item.isStatus ? (
                        <span
                          className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full ${
                            item.color === 'green'
                              ? 'bg-emerald-50 text-emerald-700'
                              : 'bg-rose-50 text-rose-700'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              item.color === 'green' ? 'bg-emerald-500' : 'bg-rose-500'
                            }`}
                          />
                          {item.value}
                        </span>
                      ) : (
                        <>
                          <p className="text-xs font-bold text-gray-900">{item.value}</p>
                          {item.sub && <p className="text-[11px] text-gray-400 mt-0.5">{item.sub}</p>}
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Lý do từ chối */}
              {selectedLog.resultColor === 'red' && (
                <div className="pt-2">
                  <p className="text-xs font-semibold text-gray-700 mb-2">Lý do từ chối</p>
                  <div className="w-full text-xs text-gray-700 border border-gray-200/80 rounded-xl p-3 bg-gray-50/70 leading-relaxed">
                    Tài khoản không có quyền truy cập vào tài nguyên này theo chính sách hiện hành.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
