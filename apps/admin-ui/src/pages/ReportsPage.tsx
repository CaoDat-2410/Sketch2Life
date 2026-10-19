import { useState } from 'react'
import { ChevronDown, FileText, Upload, BarChart2, List, MoreVertical, X } from 'lucide-react'

// ── SVG Line Chart ──────────────────────────────────────────────────────────
const POINTS = [
  { week: 'Tuần 1', val: 2 },
  { week: 'Tuần 2', val: 4 },
  { week: 'Tuần 3', val: 6 },
  { week: 'Tuần 4', val: 8 },
]
const W = 560
const H = 200
const PAD = { top: 20, right: 20, bottom: 40, left: 40 }
const maxVal = 8
const minVal = 0

function xOf(i: number) {
  return PAD.left + (i / (POINTS.length - 1)) * (W - PAD.left - PAD.right)
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
      {/* grid lines */}
      {yGridLines.map((v) => (
        <g key={v}>
          <line
            x1={PAD.left} y1={yOf(v)} x2={W - PAD.right} y2={yOf(v)}
            stroke="#e5e7eb" strokeWidth="1"
          />
          <text x={PAD.left - 6} y={yOf(v) + 4} textAnchor="end" fontSize="10" fill="#9ca3af">
            {v}
          </text>
        </g>
      ))}
      {/* area fill */}
      <path d={areaPath} fill="#dbeafe" opacity="0.6" />
      {/* line */}
      <path d={linePath} fill="none" stroke="#2563eb" strokeWidth="2.5" strokeLinejoin="round" />
      {/* dots */}
      {pts.map((p) => (
        <circle key={p.week} cx={p.x} cy={p.y} r={5} fill="#2563eb" stroke="white" strokeWidth="2" />
      ))}
      {/* x-axis labels */}
      {pts.map((p) => (
        <text key={p.week} x={p.x} y={H - 6} textAnchor="middle" fontSize="11" fill="#6b7280">
          {p.week}
        </text>
      ))}
      {/* x-axis line */}
      <line x1={PAD.left} y1={yOf(0)} x2={W - PAD.right} y2={yOf(0)} stroke="#d1d5db" strokeWidth="1" />
    </svg>
  )
}

// ── Data ────────────────────────────────────────────────────────────────────
const REPORTS = [
  { id: 'RP-012', name: 'Tổng hợp vận hành', scope: 'Lớp Lá', date: '10/10/2026', status: 'Hoàn tất', statusColor: 'green' },
  { id: 'RP-013', name: 'Báo cáo học tập', scope: 'Lớp Lá', date: '10/10/2026', status: 'Chờ kiểm tra quyền', statusColor: 'amber' },
]

export function ReportsPage() {
  const [showBanner, setShowBanner] = useState(true)

  return (
    <div className="flex flex-col h-full relative">
      {/* Main scrollable area */}
      <div className="flex-1 overflow-auto p-6 pb-14 space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Báo cáo theo phạm vi</h1>
            <p className="text-sm text-gray-500 mt-0.5">Xem dữ liệu tổng hợp trong phạm vi được cấp quyền</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button className="flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg">
              <FileText size={15} />
              Tạo báo cáo
            </button>
            <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
              <Upload size={15} />
              Yêu cầu xuất
            </button>
          </div>
        </div>

        {/* Filter dropdowns */}
        <div className="flex items-center gap-3">
          {[
            { icon: '🎓', label: 'Lớp Lá' },
            { icon: '📅', label: 'Tháng này' },
            { icon: '📊', label: 'Vận hành / Học tập được cấp quyền' },
          ].map((f) => (
            <button
              key={f.label}
              className="flex items-center gap-2 border border-gray-300 bg-white text-sm text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-50"
            >
              <span>{f.icon}</span>
              {f.label}
              <ChevronDown size={14} className="text-gray-400" />
            </button>
          ))}
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center text-xl">👥</div>
            <div>
              <p className="text-sm text-gray-500">Phiên đã kết thúc</p>
              <p className="text-3xl font-bold text-gray-900 mt-0.5">8</p>
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center text-xl">📋</div>
            <div>
              <p className="text-sm text-gray-500">Hoạt động ngoài màn hình</p>
              <p className="text-3xl font-bold text-gray-900 mt-0.5">8</p>
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center text-xl">⚠️</div>
            <div>
              <p className="text-sm text-gray-500">Yêu cầu hỗ trợ</p>
              <p className="text-3xl font-bold text-gray-900 mt-0.5">12</p>
            </div>
          </div>
        </div>

        {/* Chart + Definition side-by-side */}
        <div className="grid grid-cols-[1fr_300px] gap-4">
          {/* Line chart */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <BarChart2 size={16} className="text-blue-500" />
              Tổng phiên tích lũy
            </h2>
            <LineChart />
          </div>

          {/* Definition panel */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold">i</span>
              Định nghĩa dữ liệu
            </h2>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <span className="text-gray-400 mt-0.5">🗄️</span>
                <div>
                  <span className="text-xs text-gray-500">Nguồn: </span>
                  <span className="text-xs text-gray-800 font-medium">sự kiện phiên</span>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-gray-400 mt-0.5">👤</span>
                <div>
                  <span className="text-xs text-gray-500">Phạm vi: </span>
                  <span className="text-xs text-gray-800 font-medium">lớp được cấp quyền</span>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-gray-400 mt-0.5">🕐</span>
                <div>
                  <span className="text-xs text-gray-500">Cập nhật: </span>
                  <span className="text-xs text-gray-800 font-medium">09:40</span>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-gray-400 mt-0.5">📋</span>
                <p className="text-xs text-gray-600">Số lượng hoạt động không thay thế đánh giá học tập.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Reports table */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="p-5 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
              <List size={16} className="text-blue-500" />
              Báo cáo đã tạo
            </h2>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                {['Mã báo cáo', 'Tên báo cáo', 'Phạm vi', 'Ngày tạo', 'Trạng thái', 'Hành động'].map((h) => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {REPORTS.map((r) => (
                <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-5 py-3.5 font-medium text-gray-900">{r.id}</td>
                  <td className="px-5 py-3.5 text-gray-700">{r.name}</td>
                  <td className="px-5 py-3.5 text-gray-600">{r.scope}</td>
                  <td className="px-5 py-3.5 text-gray-600">{r.date}</td>
                  <td className="px-5 py-3.5">
                    <span
                      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${
                        r.statusColor === 'green'
                          ? 'bg-green-50 text-green-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${r.statusColor === 'green' ? 'bg-green-500' : 'bg-amber-500'}`}
                      />
                      {r.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 flex items-center gap-2">
                    <button className="bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-semibold px-4 py-1.5 rounded-lg transition">
                      Xem
                    </button>
                    <button className="text-gray-400 hover:text-gray-600 p-1">
                      <MoreVertical size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bottom info banner */}
      {showBanner && (
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between gap-3 bg-blue-50 border-t border-blue-200 px-5 py-3 text-sm text-blue-700">
          <div className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-200 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0">i</span>
            Dữ liệu nhóm nhỏ cần kiểm tra trước khi chia sẻ.
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-blue-500">Dữ liệu minh hoạ • Bản thiết kế UI.</span>
            <button onClick={() => setShowBanner(false)} className="text-blue-400 hover:text-blue-600">
              <X size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
