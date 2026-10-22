import { useState } from 'react'
import {
  ChevronDown,
  FileText,
  Upload,
  BarChart2,
  List,
  MoreVertical,
  X,
  GraduationCap,
  Calendar,
  Users,
  AlertTriangle,
  Database,
  Clock,
} from 'lucide-react'

// ── SVG Line Chart ──────────────────────────────────────────────────────────
const POINTS = [
  { week: 'Tuần 1', val: 2 },
  { week: 'Tuần 2', val: 4 },
  { week: 'Tuần 3', val: 6 },
  { week: 'Tuần 4', val: 8 },
]
const W = 680
const H = 148
const PAD = { top: 12, right: 45, bottom: 26, left: 36 }
const maxVal = 8
const minVal = 0

function xOf(i: number) {
  return PAD.left + 32 + (i / (POINTS.length - 1)) * (W - PAD.left - PAD.right - 64)
}
function yOf(v: number) {
  return PAD.top + ((maxVal - v) / (maxVal - minVal)) * (H - PAD.top - PAD.bottom)
}

function LineChart() {
  const pts = POINTS.map((p, i) => ({ x: xOf(i), y: yOf(p.val), ...p }))
  const linePath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  const areaPath =
    linePath + ` L${pts[pts.length - 1].x},${yOf(0)} L${pts[0].x},${yOf(0)} Z`
  const yGridLines = [0, 2, 4, 6, 8]

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto">
      <defs>
        <linearGradient id="reportAreaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#93C5FD" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#EFF6FF" stopOpacity="0.05" />
        </linearGradient>
      </defs>

      {/* horizontal grid lines */}
      {yGridLines.map((v) => (
        <g key={v}>
          <line
            x1={PAD.left}
            y1={yOf(v)}
            x2={W - PAD.right}
            y2={yOf(v)}
            stroke="#E2E8F0"
            strokeWidth="1"
          />
          <text
            x={PAD.left - 10}
            y={yOf(v) + 4}
            textAnchor="end"
            fontSize="11"
            fill="#64748B"
          >
            {v}
          </text>
        </g>
      ))}

      {/* vertical axis line */}
      <line
        x1={PAD.left}
        y1={PAD.top}
        x2={PAD.left}
        y2={yOf(0)}
        stroke="#CBD5E1"
        strokeWidth="1"
      />

      {/* vertical dashed grid lines at points */}
      {pts.map((p) => (
        <line
          key={`vline-${p.week}`}
          x1={p.x}
          y1={PAD.top}
          x2={p.x}
          y2={yOf(0)}
          stroke="#E2E8F0"
          strokeWidth="1"
          strokeDasharray="3 3"
        />
      ))}

      {/* area fill */}
      <path d={areaPath} fill="url(#reportAreaGrad)" />

      {/* line */}
      <path
        d={linePath}
        fill="none"
        stroke="#1565F9"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />

      {/* dots */}
      {pts.map((p) => (
        <circle
          key={p.week}
          cx={p.x}
          cy={p.y}
          r="5"
          fill="#1565F9"
          stroke="white"
          strokeWidth="2"
        />
      ))}

      {/* x-axis labels */}
      {pts.map((p) => (
        <text
          key={p.week}
          x={p.x}
          y={H - 8}
          textAnchor="middle"
          fontSize="11.5"
          fill="#475569"
        >
          {p.week}
        </text>
      ))}

      {/* x-axis line */}
      <line
        x1={PAD.left}
        y1={yOf(0)}
        x2={W - PAD.right}
        y2={yOf(0)}
        stroke="#CBD5E1"
        strokeWidth="1"
      />
    </svg>
  )
}

const REPORTS = [
  {
    id: 'RP-012',
    name: 'Tổng hợp vận hành',
    scope: 'Lớp Lá',
    date: '10/10/2026',
    status: 'Hoàn tất',
    statusColor: 'green',
  },
  {
    id: 'RP-013',
    name: 'Báo cáo học tập',
    scope: 'Lớp Lá',
    date: '10/10/2026',
    status: 'Chờ kiểm tra quyền',
    statusColor: 'amber',
  },
]

export function ReportsPage() {
  const [showBanner, setShowBanner] = useState(true)

  return (
    <div className="px-6 py-3 space-y-2.5 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[24px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
            Báo cáo theo phạm vi
          </h1>
          <p className="text-[13px] text-slate-500 mt-0.5 font-medium">
            Xem dữ liệu tổng hợp trong phạm vi được cấp quyền
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <button className="flex items-center gap-2 border border-slate-200/90 bg-white hover:bg-slate-50 text-slate-700 text-[12.5px] font-semibold px-3.5 py-1.5 rounded-xl shadow-[0_1px_2px_rgba(15,23,42,0.03)] transition cursor-pointer whitespace-nowrap">
            <FileText size={14} className="text-slate-600" />
            <span>Tạo báo cáo</span>
          </button>
          <button className="flex items-center gap-2 bg-[#1565F9] hover:bg-blue-700 text-white text-[12.5px] font-semibold px-3.5 py-1.5 rounded-xl shadow-sm transition cursor-pointer whitespace-nowrap">
            <Upload size={14} />
            <span>Yêu cầu xuất</span>
          </button>
        </div>
      </div>

      {/* Filter dropdowns */}
      <div className="flex items-center gap-3">
        <button className="w-52 flex items-center justify-between border border-slate-200/90 bg-white text-[13px] font-medium text-slate-700 px-3.5 py-1.5 rounded-xl hover:bg-slate-50 shadow-[0_1px_2px_rgba(15,23,42,0.02)]">
          <span className="flex items-center gap-2">
            <GraduationCap size={15} className="text-slate-500" />
            <span>Lớp Lá</span>
          </span>
          <ChevronDown size={13.5} className="text-slate-400" />
        </button>

        <button className="w-40 flex items-center justify-between border border-slate-200/90 bg-white text-[13px] font-medium text-slate-700 px-3.5 py-1.5 rounded-xl hover:bg-slate-50 shadow-[0_1px_2px_rgba(15,23,42,0.02)]">
          <span className="flex items-center gap-2">
            <Calendar size={14} className="text-slate-500" />
            <span>Tháng này</span>
          </span>
          <ChevronDown size={13.5} className="text-slate-400" />
        </button>

        <button className="w-80 flex items-center justify-between border border-slate-200/90 bg-white text-[13px] font-medium text-slate-700 px-3.5 py-1.5 rounded-xl hover:bg-slate-50 shadow-[0_1px_2px_rgba(15,23,42,0.02)]">
          <span className="flex items-center gap-2">
            <BarChart2 size={14} className="text-slate-500" />
            <span>Vận hành / Học tập được cấp quyền</span>
          </span>
          <ChevronDown size={13.5} className="text-slate-400" />
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200/70 rounded-2xl p-3 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center gap-3.5">
          <div className="w-11 h-11 bg-[#E2F7EB] text-[#10B981] rounded-2xl flex items-center justify-center shrink-0">
            <Users size={22} strokeWidth={2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Phiên đã kết thúc</p>
            <p className="text-[24px] leading-tight font-extrabold text-slate-900 mt-0.5">8</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200/70 rounded-2xl p-3 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center gap-3.5">
          <div className="w-11 h-11 bg-[#FEF3C7] text-[#F59E0B] rounded-2xl flex items-center justify-center shrink-0">
            <List size={22} strokeWidth={2.2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Hoạt động ngoài màn hình</p>
            <p className="text-[24px] leading-tight font-extrabold text-slate-900 mt-0.5">8</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200/70 rounded-2xl p-3 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center gap-3.5">
          <div className="w-11 h-11 bg-[#FEE2E2] text-[#EF4444] rounded-2xl flex items-center justify-center shrink-0">
            <AlertTriangle size={22} strokeWidth={2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Yêu cầu hỗ trợ</p>
            <p className="text-[24px] leading-tight font-extrabold text-slate-900 mt-0.5">12</p>
          </div>
        </div>
      </div>

      {/* Chart (8 cols) + Definition (4 cols) */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* Line chart */}
        <div className="col-span-8 bg-white border border-slate-200/70 rounded-2xl p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-6.5 h-6.5 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
              <BarChart2 size={14} strokeWidth={2.2} />
            </div>
            <h2 className="text-[15px] font-bold text-slate-900">Tổng phiên tích lũy</h2>
          </div>
          <LineChart />
        </div>

        {/* Definition panel */}
        <div className="col-span-4 bg-white border border-slate-200/70 rounded-2xl p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6.5 h-6.5 rounded-lg bg-[#E6F0FF] flex items-center justify-center">
              <span className="w-4 h-4 rounded-full bg-[#1565F9] text-white flex items-center justify-center text-[10px] font-bold">
                i
              </span>
            </div>
            <h2 className="text-[15px] font-bold text-slate-900">Định nghĩa dữ liệu</h2>
          </div>

          <div className="space-y-2.5 text-[12.5px]">
            <div className="flex items-center gap-2.5">
              <Database size={15} className="text-slate-600 shrink-0" />
              <div>
                <span className="font-bold text-slate-800">Nguồn: </span>
                <span className="text-slate-600">sự kiện phiên</span>
              </div>
            </div>
            <div className="flex items-center gap-2.5">
              <Users size={15} className="text-slate-600 shrink-0" />
              <div>
                <span className="font-bold text-slate-800">Phạm vi: </span>
                <span className="text-slate-600">lớp được cấp quyền</span>
              </div>
            </div>
            <div className="flex items-center gap-2.5">
              <Clock size={15} className="text-slate-600 shrink-0" />
              <div>
                <span className="font-bold text-slate-800">Cập nhật: </span>
                <span className="text-slate-600">09:40</span>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <FileText size={15} className="text-slate-600 shrink-0 mt-0.5" />
              <p className="text-slate-600 leading-snug">
                Số lượt hoạt động không thay thế đánh giá học tập.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Reports table */}
      <div className="bg-white border border-slate-200/70 rounded-2xl p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
        <div className="flex items-center gap-2 mb-2.5">
          <div className="w-6.5 h-6.5 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
            <FileText size={14} strokeWidth={2.2} />
          </div>
          <h2 className="text-[15px] font-bold text-slate-900">Báo cáo đã tạo</h2>
        </div>

        <div className="border border-slate-100 rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#F4F7FB] border-b border-slate-100">
                {[
                  'Mã báo cáo',
                  'Tên báo cáo',
                  'Phạm vi',
                  'Ngày tạo',
                  'Trạng thái',
                  'Hành động',
                ].map((h) => (
                  <th
                    key={h}
                    className="px-3.5 py-2 text-left text-[11.5px] font-semibold text-slate-600 whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {REPORTS.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/70 transition">
                  <td className="px-3.5 py-2 font-semibold text-slate-800 text-[13px] whitespace-nowrap">
                    {r.id}
                  </td>
                  <td className="px-3.5 py-2 font-semibold text-slate-800 text-[13px] whitespace-nowrap">
                    {r.name}
                  </td>
                  <td className="px-3.5 py-2 text-slate-600 text-[13px] whitespace-nowrap">{r.scope}</td>
                  <td className="px-3.5 py-2 text-slate-600 text-[13px] whitespace-nowrap">{r.date}</td>
                  <td className="px-3.5 py-2 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center gap-1.5 text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0 ${
                        r.statusColor === 'green'
                          ? 'bg-[#E2F7EB] text-[#059669]'
                          : 'bg-[#FEF3C7] text-[#D97706]'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                          r.statusColor === 'green' ? 'bg-[#10B981]' : 'bg-[#F59E0B]'
                        }`}
                      />
                      {r.status}
                    </span>
                  </td>
                  <td className="px-3.5 py-2 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <button className="inline-flex items-center justify-center bg-[#EAF2FF] hover:bg-blue-100 border border-blue-200/80 text-[#1565F9] text-[12.5px] font-semibold px-4 py-1 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                        Xem
                      </button>
                      <button className="text-slate-400 hover:text-slate-600 p-1">
                        <MoreVertical size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bottom info banner + watermark */}
      <div className="flex items-center justify-between gap-4">
        {showBanner ? (
          <div className="flex-1 flex items-center justify-between bg-[#EAF3FF] border border-blue-200/90 rounded-xl px-3.5 py-2 text-[12px] text-[#1565F9] font-semibold">
            <div className="flex items-center gap-2">
              <span className="w-4.5 h-4.5 rounded-full bg-[#1565F9] text-white flex items-center justify-center text-[10.5px] font-bold shrink-0">
                i
              </span>
              <span>Dữ liệu nhóm nhỏ cần kiểm tra trước khi chia sẻ.</span>
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
