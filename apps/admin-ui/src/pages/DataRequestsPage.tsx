import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FilePlus,
  FileText,
  Send,
  X,
  Check,
  Clock,
  Lock,
  GraduationCap,
  User,
  AlertTriangle,
  MoreVertical,
} from 'lucide-react'

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
  const navigate = useNavigate()

  const TABS: { key: Tab; label: string }[] = [
    { key: 'consent', label: 'Consent' },
    { key: 'export', label: 'Yêu cầu xuất' },
    { key: 'delete', label: 'Yêu cầu xóa' },
  ]

  return (
    <div className="px-6 py-4 max-w-[1440px] mx-auto">
      <div className="grid grid-cols-12 gap-4 items-start">
        {/* LEFT — main list (8 cols when detail open, 12 cols otherwise) */}
        <div className={`${selectedRow ? 'col-span-8' : 'col-span-12'} flex flex-col space-y-4 min-w-0`}>
          {/* Header */}
          <div>
            <h1 className="text-[25px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
              Consent &amp; yêu cầu dữ liệu
            </h1>
            <p className="text-[13.5px] text-slate-500 mt-1 font-medium">
              Quản lý consent và các yêu cầu liên quan đến dữ liệu của học sinh
            </p>
          </div>

          {/* Tabs + Action Buttons on same row */}
          <div className="flex items-center justify-between gap-2 border-b border-slate-200/80 pb-0">
            <div className="flex items-center gap-1.5">
              {TABS.map((t) => {
                const isActive = activeTab === t.key
                return (
                  <button
                    key={t.key}
                    onClick={() => {
                      if (t.key === 'delete') {
                        navigate('/data-requests/DR-024')
                      } else {
                        setActiveTab(t.key)
                      }
                    }}
                    className={`px-4 py-2 text-[13.5px] rounded-t-xl border-b-2 transition -mb-px cursor-pointer whitespace-nowrap shrink-0 ${
                      isActive
                        ? 'bg-white border-[#1565F9] text-[#1565F9] font-bold shadow-[0_-1px_3px_rgba(15,23,42,0.03)]'
                        : 'bg-slate-200/60 border-transparent text-slate-600 font-medium hover:text-slate-900'
                    }`}
                  >
                    {t.label}
                  </button>
                )
              })}
            </div>

            <div className="flex items-center gap-2 pb-1.5 shrink-0">
              <button className="flex items-center gap-1.5 bg-[#1565F9] hover:bg-blue-700 text-white text-[13px] font-semibold px-3.5 py-2 rounded-xl shadow-sm transition cursor-pointer whitespace-nowrap shrink-0">
                <FilePlus size={15} className="shrink-0" />
                <span>Ghi nhận consent</span>
              </button>
              <button className="flex items-center gap-1.5 bg-[#EAF2FF] border border-blue-300/90 hover:bg-blue-100 text-[#1565F9] text-[13px] font-semibold px-3.5 py-2 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                <Send size={14} className="shrink-0" />
                <span>Tiếp nhận yêu cầu</span>
              </button>
            </div>
          </div>

          {/* Unified Filter + Table + Pagination Card */}
          <div className="bg-white border border-slate-200/70 rounded-2xl p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] space-y-3.5">
            {/* Filters */}
            <div className="flex items-center gap-3">
              <div className="relative flex-1 min-w-[180px]">
                <Search
                  size={15}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  className="w-full pl-9 pr-3 py-2 text-[13px] border border-slate-200 rounded-xl bg-[#FAFBFD] focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Tìm theo mã học sinh..."
                />
              </div>
              {[
                { label: 'Lớp học', value: 'Tất cả' },
                { label: 'Trạng thái', value: 'Tất cả' },
              ].map((f) => (
                <div
                  key={f.label}
                  className="flex items-center gap-2 text-[13px] text-slate-600 shrink-0 whitespace-nowrap"
                >
                  <span className="font-medium">{f.label}</span>
                  <button className="flex items-center justify-between gap-3 border border-slate-200 bg-white px-3 py-2 rounded-xl hover:bg-slate-50 font-medium text-slate-700 min-w-[96px] whitespace-nowrap">
                    <span>{f.value}</span>
                    <ChevronDown size={14} className="text-slate-400 shrink-0" />
                  </button>
                </div>
              ))}
            </div>

            {/* Table */}
            <div className="border border-slate-100 rounded-xl overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#F4F7FB] border-b border-slate-100">
                    {[
                      'Mã học sinh',
                      'Lớp học',
                      'Mục đích',
                      'Trạng thái',
                      'Phiên bản',
                      'Bằng chứng',
                      'Cập nhật gần nhất',
                      '',
                    ].map((h) => (
                      <th
                        key={h}
                        className="px-2.5 py-2.5 first:pl-3 last:pr-2 text-left text-[11.5px] font-semibold text-slate-600 whitespace-nowrap"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {CONSENT_ROWS.map((row) => (
                    <tr
                      key={row.id}
                      onClick={() => setSelectedRow(row.id)}
                      className={`cursor-pointer transition ${
                        selectedRow === row.id ? 'bg-[#EBF3FF]/80' : 'hover:bg-slate-50'
                      }`}
                    >
                      <td className="pl-3 pr-2.5 py-3.5 font-bold text-slate-900 text-[13px] whitespace-nowrap">
                        {row.id}
                      </td>
                      <td className="px-2.5 py-3.5 text-slate-700 text-[13px] whitespace-nowrap">
                        {row.class}
                      </td>
                      <td className="px-2.5 py-3.5 text-slate-700 text-[12.5px] leading-snug w-[105px]">
                        {row.purposes}
                      </td>
                      <td className="px-2.5 py-3.5 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1.5 text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0 ${
                            row.statusColor === 'green'
                              ? 'bg-[#E2F7EB] text-[#059669]'
                              : 'bg-[#FEF3C7] text-[#D97706]'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              row.statusColor === 'green' ? 'bg-[#10B981]' : 'bg-[#F59E0B]'
                            }`}
                          />
                          {row.status}
                        </span>
                      </td>
                      <td className="px-2.5 py-3.5 text-slate-700 text-[13px] whitespace-nowrap">
                        {row.version}
                      </td>
                      <td className="px-2.5 py-3.5 text-slate-800 font-medium text-[13px] whitespace-nowrap">
                        {row.evidence}
                      </td>
                      <td className="px-2.5 py-3.5 text-slate-700 text-[13px] whitespace-nowrap">
                        {row.updated}
                      </td>
                      <td className="pl-1 pr-2 py-3.5 text-slate-500">
                        <button className="hover:text-slate-700 p-1">
                          <MoreVertical size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between pt-1 text-[12.5px] text-slate-500">
              <span>Hiển thị 1 - 2 của 2 bản ghi</span>
              <div className="flex items-center gap-1.5">
                <button className="w-8 h-8 border border-slate-200 rounded-lg flex items-center justify-center hover:bg-slate-50 text-slate-500">
                  <ChevronLeft size={14} />
                </button>
                <button className="w-8 h-8 border border-[#3B82F6] bg-[#EFF6FF] text-[#1565F9] rounded-lg flex items-center justify-center text-[13px] font-bold">
                  1
                </button>
                <button className="w-8 h-8 border border-slate-200 rounded-lg flex items-center justify-center hover:bg-slate-50 text-slate-500">
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT — Detail panel (4 cols) */}
        {selectedRow && (
          <div className="col-span-4 rounded-2xl border border-slate-200/80 bg-white overflow-hidden flex flex-col justify-between shadow-[0_1px_3px_rgba(15,23,42,0.02)] min-w-0">
            <div className="p-4 space-y-2.5">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-[17px] font-extrabold text-slate-900">Chi tiết consent</h2>
                  <p className="text-[12px] text-slate-500 mt-0.5">
                    Thông tin consent và trạng thái xác minh
                  </p>
                </div>
                <button
                  onClick={() => setSelectedRow(null)}
                  className="text-slate-400 hover:text-slate-600 p-1"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Student header card */}
              <div className="border border-slate-200/70 rounded-2xl p-2.5 px-3 flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-[#E6F0FF] flex items-center justify-center text-[#1565F9] shrink-0">
                  <GraduationCap size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[16px] font-extrabold text-slate-900 leading-tight">HS-022</p>
                  <p className="text-[12px] text-slate-500 mt-0.5">Lớp Lá</p>
                </div>
                <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold bg-[#FEF3C7] text-[#D97706] px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] shrink-0" />
                  Chờ xác minh
                </span>
              </div>

              {/* Thông tin chung */}
              <div>
                <h3 className="text-[13.5px] font-bold text-slate-900 mb-1">Thông tin chung</h3>
                <div className="divide-y divide-slate-100 text-[12.5px]">
                  {[
                    { icon: GraduationCap, label: 'Nguồn', value: 'Nhà trường thu thập' },
                    { icon: FileText, label: 'Phiên bản thông báo', value: 'v1' },
                    { icon: FileText, label: 'Bằng chứng (mã)', value: 'EV-022' },
                    { icon: User, label: 'Người ghi', value: 'GV An' },
                    { icon: Clock, label: 'Cập nhật gần nhất', value: '10/10/2026' },
                  ].map((item) => {
                    const Icon = item.icon
                    return (
                      <div key={item.label} className="flex items-center py-1.5">
                        <div className="flex items-center gap-2 text-slate-500 w-40 shrink-0">
                          <Icon size={14} className="text-slate-500 shrink-0" />
                          <span>{item.label}</span>
                        </div>
                        <span className="font-bold text-slate-900">{item.value}</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Mục đích được consent */}
              <div>
                <h3 className="text-[13.5px] font-bold text-slate-900 mb-1.5">
                  Mục đích được consent
                </h3>
                <div className="space-y-2">
                  <div className="flex items-start gap-2.5 p-2.5 rounded-2xl border border-slate-200/70">
                    <div className="w-7 h-7 rounded-xl bg-[#E2F7EB] flex items-center justify-center shrink-0">
                      <span className="w-4 h-4 rounded-full bg-[#10B981] text-white flex items-center justify-center">
                        <Check size={10} strokeWidth={3} />
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[13px] font-bold text-slate-900">Vẽ trong lớp</p>
                        <span className="inline-flex items-center gap-1 text-[10.5px] bg-[#E2F7EB] text-[#059669] px-2 py-0.5 rounded-full font-semibold whitespace-nowrap shrink-0">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] shrink-0" />
                          Có hiệu lực
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">
                        Sử dụng tác phẩm vẽ trong các hoạt động học tập tại lớp.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5 p-2.5 rounded-2xl border border-slate-200/70">
                    <div className="w-7 h-7 rounded-xl bg-[#FEF3C7] text-[#F59E0B] flex items-center justify-center shrink-0">
                      <Clock size={16} strokeWidth={2.2} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[13px] font-bold text-slate-900">Gợi ý AI</p>
                        <span className="inline-flex items-center gap-1 text-[10.5px] bg-[#FEF3C7] text-[#D97706] px-2 py-0.5 rounded-full font-semibold whitespace-nowrap shrink-0">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] shrink-0" />
                          Chờ xác minh
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">
                        Sử dụng tác phẩm vẽ để gợi ý ý tưởng bằng AI trong lớp.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Red alert */}
              <div className="flex items-start gap-2 p-2.5 bg-[#FEE2E2]/60 rounded-2xl border border-rose-200/80">
                <AlertTriangle size={16} className="text-[#EF4444] mt-0.5 shrink-0" />
                <div>
                  <p className="text-[12px] font-bold text-[#DC2626] leading-snug">
                    Chưa xác minh không kích hoạt mục đích bị hạn chế.
                  </p>
                  <p className="text-[11px] text-slate-600 mt-0.5 leading-snug">
                    Chỉ sử dụng dữ liệu cho các mục đích đã được xác minh và có hiệu lực.
                  </p>
                </div>
              </div>
            </div>

            {/* Bottom actions */}
            <div className="px-4 pb-3 pt-1">
              <div className="flex items-center gap-1.5">
                <button className="inline-flex items-center justify-center gap-1 bg-[#1565F9] hover:bg-blue-700 text-white text-[11px] font-semibold py-2 px-2.5 rounded-xl transition shadow-sm cursor-pointer whitespace-nowrap shrink-0">
                  <FileText size={12} className="shrink-0" />
                  <span>Yêu cầu bổ sung</span>
                </button>
                <button className="inline-flex items-center justify-center gap-1 bg-[#EAF2FF] border border-blue-200 hover:bg-blue-100 text-[#1565F9] text-[11px] font-semibold py-2 px-2.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                  <Clock size={12} className="shrink-0" />
                  <span>Xem lịch sử</span>
                </button>
                <button
                  disabled
                  className="flex-1 inline-flex items-center justify-center gap-1 border border-slate-200 bg-slate-100 text-slate-400 text-[10.5px] font-medium py-2 px-2 rounded-xl cursor-not-allowed whitespace-nowrap shrink-0"
                >
                  <Lock size={11} className="shrink-0" />
                  <span>Chưa có quyền xem</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
