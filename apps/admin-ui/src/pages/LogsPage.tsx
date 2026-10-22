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
    <div className="px-6 py-4 max-w-[1440px] mx-auto">
      <div className="grid grid-cols-12 gap-4 items-start">
        {/* LEFT COLUMN (8 cols) */}
        <div className={`${selectedLog ? 'col-span-8' : 'col-span-12'} flex flex-col gap-3.5 min-w-0`}>
          {/* Header */}
          <div>
            <h1 className="text-[25px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
              Nhật ký kiểm toán
            </h1>
            <p className="text-[13.5px] text-slate-500 mt-1 font-medium">
              Theo dõi các hoạt động quản trị, truy cập và thay đổi trong hệ thống
            </p>
          </div>

          {/* Filters Card */}
          <div className="bg-white border border-slate-200/70 rounded-2xl p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] space-y-3">
            <div className="grid grid-cols-3 gap-3.5">
              {/* Row 1 col 1 */}
              <div className="space-y-1">
                <label className="text-[12px] font-semibold text-slate-700 block">
                  Khoảng thời gian
                </label>
                <button className="flex items-center justify-between border border-slate-200 bg-white text-[13px] text-slate-800 font-medium px-3 py-2 rounded-xl hover:bg-slate-50 w-full transition whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <Calendar size={15} className="text-slate-500 shrink-0" />
                    <span>10/10/2026</span>
                  </div>
                  <ChevronDown size={14} className="text-slate-400 shrink-0" />
                </button>
              </div>
              {/* Row 1 col 2 */}
              <div className="space-y-1">
                <label className="text-[12px] font-semibold text-slate-700 block">Hành động</label>
                <button className="flex items-center justify-between border border-slate-200 bg-white text-[13px] text-slate-800 font-medium px-3 py-2 rounded-xl hover:bg-slate-50 w-full transition whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <ListFilter size={15} className="text-slate-500 shrink-0" />
                    <span>Tất cả</span>
                  </div>
                  <ChevronDown size={14} className="text-slate-400 shrink-0" />
                </button>
              </div>
              {/* Row 1 col 3 */}
              <div className="space-y-1">
                <label className="text-[12px] font-semibold text-slate-700 block">Phạm vi</label>
                <button className="flex items-center justify-between border border-slate-200 bg-white text-[13px] text-slate-800 font-medium px-3 py-2 rounded-xl hover:bg-slate-50 w-full transition whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <Layers size={15} className="text-slate-500 shrink-0" />
                    <span>Tất cả</span>
                  </div>
                  <ChevronDown size={14} className="text-slate-400 shrink-0" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-12 gap-3.5">
              {/* Row 2 col 1: Kết quả (5 cols) */}
              <div className="col-span-5 space-y-1">
                <label className="text-[12px] font-semibold text-slate-700 block">Kết quả</label>
                <button className="flex items-center justify-between border border-slate-200 bg-white text-[13px] text-slate-800 font-medium px-3 py-2 rounded-xl hover:bg-slate-50 w-full transition whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 size={15} className="text-slate-500 shrink-0" />
                    <span>Tất cả</span>
                  </div>
                  <ChevronDown size={14} className="text-slate-400 shrink-0" />
                </button>
              </div>

              {/* Row 2 col 2: Tra cứu correlation (7 cols) */}
              <div className="col-span-7 space-y-1">
                <label className="text-[12px] font-semibold text-slate-700 block">
                  Tra cứu correlation
                </label>
                <div className="relative">
                  <Search
                    size={15}
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                  />
                  <input
                    type="text"
                    className="w-full pl-9 pr-3 py-2 text-[13px] border border-slate-200 rounded-xl bg-[#FAFBFD] focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                    placeholder="Nhập mã correlation (ví dụ: COR-031)"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Table Card */}
          <div className="bg-white border border-slate-200/70 rounded-2xl p-3.5 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
            <div className="border border-slate-100 rounded-xl overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#F4F7FB] border-b border-slate-100">
                    <th className="px-3 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span>Thời điểm</span>
                        <ArrowUpDown size={12} className="text-slate-400" />
                      </div>
                    </th>
                    <th className="px-3 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                      Actor ref
                    </th>
                    <th className="px-3 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                      Hành động
                    </th>
                    <th className="px-3 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                      Resource
                    </th>
                    <th className="px-3 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                      Phiên bản
                    </th>
                    <th className="px-3 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                      Kết quả
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {LOG_ROWS.map((row) => {
                    const isSelected =
                      selectedLog?.actor === row.actor && selectedLog?.time === row.time
                    return (
                      <tr
                        key={row.time + row.actor}
                        onClick={() => setSelectedLog(row)}
                        className={`cursor-pointer transition ${
                          isSelected ? 'bg-[#DCEBFF]/65' : 'hover:bg-slate-50/70'
                        }`}
                      >
                        <td className="px-3 py-3.5 text-slate-800 font-medium text-[13px] whitespace-nowrap">
                          {row.time}
                        </td>
                        <td className="px-3 py-3.5 font-semibold text-slate-900 text-[13px] whitespace-nowrap">
                          {row.actor}
                        </td>
                        <td className="px-3 py-3.5 text-slate-800 text-[13px] whitespace-nowrap">
                          {row.action}
                        </td>
                        <td className="px-3 py-3.5 text-slate-700 text-[13px] whitespace-nowrap">
                          {row.resource}
                        </td>
                        <td className="px-3 py-3.5 text-slate-700 text-[13px] whitespace-nowrap">
                          {row.version}
                        </td>
                        <td className="px-3 py-3.5 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1.5 text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0 ${
                              row.resultColor === 'green'
                                ? 'bg-[#E2F7EB] text-[#059669]'
                                : 'bg-[#FEE2E2] text-[#DC2626]'
                            }`}
                          >
                            <span
                              className={`w-2 h-2 rounded-full shrink-0 ${
                                row.resultColor === 'green' ? 'bg-[#10B981]' : 'bg-[#EF4444]'
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
          </div>

          {/* Footer info banner */}
          {showBanner && (
            <div className="flex items-center justify-between gap-3 bg-[#EAF3FF] border border-blue-200/90 rounded-xl px-4 py-2 text-[12.5px] text-[#1565F9] font-semibold">
              <div className="flex items-center gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#1565F9] text-white flex items-center justify-center text-[11px] font-bold shrink-0">
                  i
                </span>
                <span>Nhật ký đã lược bỏ dữ liệu nhạy cảm • Chỉ đọc.</span>
              </div>
              <button
                onClick={() => setShowBanner(false)}
                className="text-slate-400 hover:text-slate-600 transition"
              >
                <X size={15} />
              </button>
            </div>
          )}

          {/* Footer actions */}
          <div className="flex items-center justify-between pt-0.5">
            <span className="text-[12.5px] text-slate-600">Đã hiển thị 3 kết quả</span>
            <div className="flex items-center gap-2.5">
              <button className="flex items-center gap-2 border border-slate-200 bg-white hover:bg-blue-50 text-[#1565F9] text-[13px] font-semibold px-3.5 py-2 rounded-xl shadow-sm transition cursor-pointer whitespace-nowrap">
                <LinkIcon size={14} />
                <span>Liên kết sự cố</span>
              </button>
              <button className="flex items-center gap-2 bg-[#1565F9] hover:bg-blue-700 text-white text-[13px] font-semibold px-3.5 py-2 rounded-xl shadow-sm transition cursor-pointer whitespace-nowrap">
                <Download size={14} />
                <span>Xuất nhật ký theo quyền</span>
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT — Event detail floating card (4 cols) */}
        {selectedLog && (
          <div className="col-span-4 flex flex-col justify-between min-w-0">
            <div className="bg-white border border-slate-200/70 rounded-2xl shadow-[0_1px_3px_rgba(15,23,42,0.02)] overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <AlertTriangle size={19} className="text-[#EF4444]" strokeWidth={2.2} />
                  <h2 className="text-[17px] font-extrabold text-slate-900">Chi tiết sự kiện</h2>
                </div>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="text-slate-400 hover:text-slate-600 transition p-1"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-4 space-y-3.5">
                {/* Alert Card */}
                <div
                  className={`flex items-start gap-2.5 p-3 rounded-xl border ${
                    selectedLog.resultColor === 'red'
                      ? 'bg-[#FEE2E2]/60 border-rose-200/70'
                      : 'bg-[#E2F7EB]/60 border-emerald-200/70'
                  }`}
                >
                  <AlertTriangle
                    size={19}
                    className={`mt-0.5 shrink-0 ${
                      selectedLog.resultColor === 'red' ? 'text-[#EF4444]' : 'text-[#10B981]'
                    }`}
                  />
                  <div>
                    <p
                      className={`text-[13.5px] font-bold ${
                        selectedLog.resultColor === 'red' ? 'text-[#DC2626]' : 'text-[#059669]'
                      }`}
                    >
                      {selectedLog.resultColor === 'red'
                        ? 'Yêu cầu truy cập bị từ chối'
                        : selectedLog.action + ' thành công'}
                    </p>
                    <p className="text-[12px] text-slate-500 mt-0.5">{selectedLog.time}</p>
                  </div>
                </div>

                {/* Top Metadata Group */}
                <div className="space-y-2 text-[12.5px]">
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Correlation</span>
                    <span className="font-bold text-slate-900">COR-031</span>
                  </div>
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Actor ref</span>
                    <div>
                      <p className="font-bold text-slate-900">{selectedLog.actor}</p>
                      <p className="text-[11.5px] text-slate-500">Tài khoản quản trị viên</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Hành động</span>
                    <span className="font-bold text-slate-900">{selectedLog.action}</span>
                  </div>
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Resource</span>
                    <div>
                      <p className="font-bold text-slate-900">{selectedLog.resource}</p>
                      <p className="text-[11.5px] text-slate-500">Tài nguyên hệ thống</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Phiên bản</span>
                    <span className="font-bold text-slate-900">{selectedLog.version}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-slate-500 w-32 shrink-0">Kết quả</span>
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#EF4444]" />
                      <span className="bg-[#FEE2E2] text-[#DC2626] text-[11.5px] font-semibold px-2.5 py-0.5 rounded-lg">
                        {selectedLog.result}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Divider + Bottom Metadata Group */}
                <div className="pt-2.5 border-t border-slate-100 space-y-2 text-[12.5px]">
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Mục đích</span>
                    <span className="font-bold text-slate-900">Điều tra sự cố</span>
                  </div>
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Quyết định</span>
                    <span className="font-bold text-slate-900">Không có grant phù hợp</span>
                  </div>
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Chính sách áp dụng</span>
                    <span className="font-bold text-slate-900">v1</span>
                  </div>
                  <div className="flex items-start">
                    <span className="text-slate-500 w-32 shrink-0">Thời điểm</span>
                    <span className="font-bold text-slate-900">{selectedLog.time}</span>
                  </div>
                </div>

                {/* Lý do từ chối */}
                {selectedLog.resultColor === 'red' && (
                  <div className="pt-2.5 border-t border-slate-100">
                    <p className="text-[12.5px] font-medium text-slate-600 mb-1.5">Lý do từ chối</p>
                    <div className="w-full text-[12.5px] text-slate-700 rounded-xl p-3 bg-[#F4F7FB] leading-relaxed">
                      Tài khoản không có quyền truy cập vào tài nguyên này theo chính sách hiện hành.
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
