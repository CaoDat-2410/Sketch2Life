import { useState } from 'react'
import {
  RefreshCw,
  Calendar,
  Filter,
  X,
  Users,
  BookOpen,
  ChevronDown,
  Settings,
  Database,
  List,
  AlertTriangle,
  Clock,
  Copy,
} from 'lucide-react'

const INCIDENTS = [
  {
    id: 'INC-024',
    desc: 'Video chưa hoàn thành',
    scope: 'Phiên S-024',
    status: 'Đang xử lý',
    statusColor: 'text-[#1565F9] bg-[#E8F1FF]',
    dotColor: 'bg-[#1565F9]',
    handler: 'QT Minh',
  },
  {
    id: 'INC-025',
    desc: 'Chưa nhận checkpoint',
    scope: 'Nhóm G-03',
    status: 'Chờ kiểm tra',
    statusColor: 'text-[#D97706] bg-[#FEF3C7]',
    dotColor: 'bg-[#F59E0B]',
    handler: 'Chưa phân công',
  },
]

const TIMELINE = [
  {
    color: 'bg-[#10B981]',
    title: 'Yêu cầu tạo video',
    desc: 'Hệ thống ghi nhận yêu cầu tạo video.',
    time: '10/10/2026 09:12',
  },
  {
    color: 'bg-[#EF4444]',
    title: 'Đã ghi nhận lỗi',
    desc: 'Hệ thống phát hiện lỗi khi xử lý tác vụ.',
    time: '10/10/2026 09:18',
  },
  {
    color: 'bg-slate-400',
    title: 'Chờ quyết định giáo viên',
    desc: 'Đang chờ giáo viên kiểm tra và quyết định bước tiếp theo.',
    time: '10/10/2026 09:36',
  },
]

export function MonitoringPage() {
  const [selected, setSelected] = useState<string>('INC-024')
  const [showBanner, setShowBanner] = useState(true)
  const sel = INCIDENTS.find((i) => i.id === selected)

  return (
    <div className="px-6 py-3 space-y-2.5 max-w-[1440px] mx-auto">
      {/* Full-width Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[24px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
            Giám sát &amp; sự cố
          </h1>
          <p className="text-[13px] text-slate-500 mt-0.5 font-medium">
            Theo dõi hoạt động hệ thống và xử lý các sự cố
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-2 bg-white border border-slate-200/90 text-slate-700 text-[12.5px] font-semibold px-3 py-1.5 rounded-xl hover:bg-slate-50 transition shadow-[0_1px_2px_rgba(15,23,42,0.03)] whitespace-nowrap">
              <Calendar size={14} className="text-slate-500" />
              <span>Hôm nay</span>
              <ChevronDown size={13} className="text-slate-400 ml-1" />
            </button>
            <button className="flex items-center gap-2 bg-[#1565F9] hover:bg-blue-700 text-white text-[12.5px] font-semibold px-3.5 py-1.5 rounded-xl transition shadow-sm cursor-pointer whitespace-nowrap">
              <RefreshCw size={13.5} />
              <span>Làm mới</span>
            </button>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">Cập nhật lúc 09:40</p>
        </div>
      </div>

      {/* Full-width 3 Status cards */}
      <div className="grid grid-cols-3 gap-3.5">
        {/* Card 1: API */}
        <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-start gap-3">
          <div className="w-11 h-11 bg-[#E2F7EB] text-[#10B981] rounded-2xl flex items-center justify-center shrink-0">
            <Settings size={22} strokeWidth={2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">API</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
              <span className="text-[19px] font-extrabold text-slate-900 leading-tight">
                Hoạt động
              </span>
            </div>
            <p className="text-[11.5px] text-slate-500 mt-0.5">
              Các dịch vụ hoạt động bình thường.
            </p>
          </div>
        </div>

        {/* Card 2: Checkpoint */}
        <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-start gap-3">
          <div className="w-11 h-11 bg-[#FEF3C7] text-[#F59E0B] rounded-2xl flex items-center justify-center shrink-0">
            <Database size={22} strokeWidth={2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Checkpoint</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[22px] font-extrabold text-slate-900 leading-tight">1</span>
              <span className="flex items-center gap-1.5 text-[15px] font-bold text-[#F59E0B]">
                <span className="w-2 h-2 rounded-full bg-[#F59E0B]" />
                cần kiểm tra
              </span>
            </div>
            <p className="text-[11.5px] text-slate-500 mt-0.5">
              Có checkpoint cần được kiểm tra.
            </p>
          </div>
        </div>

        {/* Card 3: Hàng đợi AI */}
        <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-start gap-3">
          <div className="w-11 h-11 bg-[#FEE2E2] text-[#EF4444] rounded-2xl flex items-center justify-center shrink-0">
            <List size={22} strokeWidth={2.2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Hàng đợi AI</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
              <span className="text-[19px] font-extrabold text-slate-900 leading-tight">
                Có độ trễ
              </span>
            </div>
            <p className="text-[11.5px] text-slate-500 mt-0.5">
              Một số tác vụ đang chờ xử lý.
            </p>
          </div>
        </div>
      </div>

      {/* 2-Column Section: Sự cố đang mở (7 cols) + INC-024 detail (5 cols) */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* LEFT — Sự cố đang mở */}
        <div className="col-span-7 bg-white rounded-2xl border border-slate-200/70 p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col min-w-0">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-xl bg-[#FEE2E2] text-[#EF4444] flex items-center justify-center">
                <AlertTriangle size={15} strokeWidth={2.2} />
              </div>
              <h2 className="text-[15.5px] font-bold text-slate-900">Sự cố đang mở</h2>
            </div>
            <button className="flex items-center gap-2 border border-slate-200 text-slate-700 text-[12.5px] font-medium px-3 py-1.5 rounded-xl hover:bg-slate-50 transition whitespace-nowrap shrink-0">
              <Filter size={12.5} className="text-slate-500" />
              <span>Tất cả trạng thái</span>
              <ChevronDown size={13.5} className="text-slate-400 ml-1" />
            </button>
          </div>

          <div className="border border-slate-100 rounded-xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#F4F7FB] border-b border-slate-100">
                  {['Mã', 'Mô tả', 'Phạm vi', 'Trạng thái', 'Người xử lý'].map((h) => (
                    <th
                      key={h}
                      className="text-left py-2.5 px-2.5 first:pl-3.5 last:pr-3.5 text-[12px] font-semibold text-slate-600 whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {INCIDENTS.map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => setSelected(inc.id)}
                    className={`cursor-pointer transition ${
                      selected === inc.id ? 'bg-[#EBF3FF]/80' : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className="py-3 pl-3.5 pr-2.5 font-bold text-slate-900 text-[13px] whitespace-nowrap">
                      {inc.id}
                    </td>
                    <td className="py-3 px-2.5 font-bold text-slate-900 text-[13px] whitespace-nowrap">
                      {inc.desc}
                    </td>
                    <td className="py-3 px-2.5 text-slate-600 text-[13px] whitespace-nowrap">
                      {inc.scope}
                    </td>
                    <td className="py-3 px-2.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1.5 text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0 ${inc.statusColor}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${inc.dotColor}`} />
                        {inc.status}
                      </span>
                    </td>
                    <td className="py-3 pl-2.5 pr-3.5 text-slate-700 text-[13px] whitespace-nowrap">
                      {inc.handler}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT — INC-024 Detail Card */}
        {sel && (
          <div className="col-span-5 bg-white rounded-2xl border border-slate-200/70 p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between min-w-0">
            <div>
              {/* Header */}
              <div className="flex items-start gap-3 mb-2.5">
                <div className="w-9 h-9 bg-[#FEE2E2] text-[#EF4444] rounded-xl flex items-center justify-center flex-shrink-0">
                  <AlertTriangle size={18} strokeWidth={2} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-extrabold text-slate-900 text-[16px] leading-tight">{sel.id}</p>
                    <span
                      className={`inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0 ${sel.statusColor}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${sel.dotColor}`} />
                      {sel.status}
                    </span>
                  </div>
                  <p className="text-[12.5px] text-slate-500 mt-0.5">{sel.desc}</p>
                </div>
              </div>

              {/* Metadata box */}
              <div className="bg-[#F8FAFC] border border-slate-100 rounded-xl p-2.5 px-3 space-y-1 text-[12px] mb-2.5">
                <div className="flex items-center">
                  <span className="text-slate-500 w-32 shrink-0">Mã tương quan</span>
                  <span className="flex items-center gap-1.5 text-slate-800 font-medium">
                    COR-024
                    <Copy size={12} className="text-slate-400 cursor-pointer hover:text-slate-600" />
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-slate-500 w-32 shrink-0">Nguồn</span>
                  <span className="text-slate-800 font-medium">
                    Ứng dụng (sự kiện hệ thống)
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-slate-500 w-32 shrink-0">Phạm vi</span>
                  <span className="text-slate-800 font-medium">{sel.scope}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-slate-500 w-32 shrink-0">Trạng thái</span>
                  <span className="flex items-center gap-1.5 text-[#1565F9] font-semibold">
                    <span className="w-2 h-2 rounded-full bg-[#1565F9]" />
                    {sel.status}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-slate-500 w-32 shrink-0">Người xử lý</span>
                  <span className="text-slate-800 font-medium">{sel.handler}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-slate-500 w-32 shrink-0">Ngày tạo</span>
                  <span className="text-slate-800 font-medium">10/10/2026 09:12</span>
                </div>
                <div className="flex items-center">
                  <span className="text-slate-500 w-32 shrink-0">Cập nhật gần nhất</span>
                  <span className="text-slate-800 font-medium">10/10/2026 09:36</span>
                </div>
              </div>

              {/* Timeline */}
              <div className="flex items-center gap-1.5 mb-2">
                <Clock size={13.5} className="text-slate-500" />
                <p className="text-[12.5px] font-bold text-slate-900">Dòng thời gian xử lý</p>
              </div>
              <div className="relative ml-2">
                {TIMELINE.map((t, i) => (
                  <div key={t.title} className="flex gap-2.5 pb-2 last:pb-0 relative">
                    <div className="flex flex-col items-center">
                      <div
                        className={`w-2 h-2 rounded-full ${t.color} flex-shrink-0 mt-1 z-10`}
                      />
                      {i < TIMELINE.length - 1 && (
                        <div className="w-px flex-1 bg-slate-200 mt-1" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[12px] font-bold text-slate-900">{t.title}</p>
                        <span className="text-[10.5px] text-slate-400 whitespace-nowrap">{t.time}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{t.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2.5 mt-2.5 pt-1">
              <button className="flex-1 flex items-center justify-center gap-1.5 bg-[#1565F9] hover:bg-blue-700 text-white text-[12.5px] font-semibold py-2 rounded-xl transition shadow-sm cursor-pointer whitespace-nowrap">
                <Users size={14} />
                <span>Phân công</span>
              </button>
              <button className="flex-1 flex items-center justify-center gap-1.5 border border-[#1565F9] bg-white text-[#1565F9] text-[12.5px] font-semibold py-2 rounded-xl hover:bg-blue-50 transition cursor-pointer whitespace-nowrap">
                <BookOpen size={14} />
                <span>Mở runbook</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Bottom banner & watermark */}
      <div className="flex items-center justify-between gap-4">
        {showBanner ? (
          <div className="flex-1 flex items-center justify-between bg-[#EAF3FF] border border-blue-200/90 rounded-xl px-3.5 py-2 text-[12px] text-[#1565F9] font-semibold">
            <div className="flex items-center gap-2">
              <span className="w-4.5 h-4.5 rounded-full bg-[#1565F9] text-white flex items-center justify-center text-[10.5px] font-bold shrink-0">
                i
              </span>
              <span>Chỉ hiển thị dữ liệu vận hành đã lược bỏ thông tin nhạy cảm.</span>
            </div>
            <button
              onClick={() => setShowBanner(false)}
              className="text-slate-400 hover:text-slate-600 transition"
            >
              <X size={14} />
            </button>
          </div>
        ) : (
          <div className="flex-1" />
        )}
      </div>
    </div>
  )
}
