import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  RefreshCw,
  Calendar,
  ChevronRight,
  ChevronDown,
  X,
  Users,
  User,
  Play,
  List,
  AlertTriangle,
  BookOpen,
  Settings,
  Database,
  Layout,
} from 'lucide-react'

const TASKS = [
  {
    iconBg: 'bg-[#FEE2E2]',
    iconColor: 'text-[#EF4444]',
    title: 'Tác vụ video chưa hoàn thành',
    desc: 'Một số tác vụ video đang xử lý nhưng chưa hoàn thành.',
    code: 'INC-024',
    action: 'Mở sự cố',
  },
  {
    iconBg: 'bg-[#FEF3C7]',
    iconColor: 'text-[#F59E0B]',
    title: 'Thiết bị chưa đồng bộ',
    desc: 'Có thiết bị chưa đồng bộ dữ liệu lên hệ thống.',
    code: 'INC-025',
    action: 'Kiểm tra',
  },
]

export function DashboardPage() {
  const [showBanner, setShowBanner] = useState(true)
  const navigate = useNavigate()

  return (
    <div className="px-6 py-3 space-y-3 max-w-[1440px] mx-auto">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[24px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
            Tổng quan
          </h1>
          <p className="text-[13px] text-slate-500 mt-0.5 font-medium">
            Vận hành trường và an toàn dữ liệu
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

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-3.5">
        {/* Card 1 */}
        <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-[#E2F7EB] text-[#10B981] flex items-center justify-center shrink-0">
            <Users size={22} strokeWidth={2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Lớp hoạt động</p>
            <p className="text-[26px] leading-tight font-extrabold text-slate-900 mt-0.5">1</p>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-[#E6F0FF] flex items-center justify-center shrink-0">
            <div className="w-6 h-6 rounded-full bg-[#1565F9] text-white flex items-center justify-center">
              <Play size={11.5} fill="currentColor" className="ml-0.5" />
            </div>
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Phiên đang diễn ra</p>
            <p className="text-[26px] leading-tight font-extrabold text-slate-900 mt-0.5">1</p>
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-[#FEF3C7] text-[#F59E0B] flex items-center justify-center shrink-0">
            <List size={22} strokeWidth={2.2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Tác vụ AI đang chờ</p>
            <p className="text-[26px] leading-tight font-extrabold text-slate-900 mt-0.5">3</p>
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-white rounded-2xl border border-slate-200/70 p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-[#FEE2E2] text-[#EF4444] flex items-center justify-center shrink-0">
            <AlertTriangle size={22} strokeWidth={2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Cảnh báo cần xử lý</p>
            <p className="text-[26px] leading-tight font-extrabold text-slate-900 mt-0.5">2</p>
          </div>
        </div>
      </div>

      {/* Middle 2-col: Phiên hiện hành (7 cols) + Sức khỏe hệ thống (5 cols) */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* Phiên hiện hành */}
        <div className="col-span-7 bg-white rounded-2xl border border-slate-200/70 p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-6.5 h-6.5 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
                  <Layout size={14} strokeWidth={2.2} />
                </div>
                <h2 className="text-[15px] font-bold text-slate-900">Phiên hiện hành</h2>
              </div>
              <span className="flex items-center gap-1.5 text-[11.5px] font-semibold text-[#059669] bg-[#E2F7EB] px-2.5 py-0.5 rounded-full">
                <span className="w-2 h-2 bg-[#10B981] rounded-full" />
                Đang hoạt động
              </span>
            </div>

            <div className="flex items-center gap-3.5">
              <div className="w-14 h-14 bg-[#EBF3FF] rounded-2xl flex items-center justify-center flex-shrink-0 text-[#1565F9]">
                <BookOpen size={26} strokeWidth={1.9} />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-slate-900 text-[15px]">
                  Lớp Lá • Khu vườn của chúng mình
                </p>
                <div className="flex items-center gap-2 text-[12.5px] text-slate-600">
                  <Users size={14} className="text-slate-500" />
                  <span>
                    <strong className="font-bold text-slate-800">24 trẻ</strong> đã tiếp nhận
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[12.5px] text-slate-600">
                  <User size={14} className="text-slate-500" />
                  <span>
                    Giáo viên: <strong className="font-bold text-slate-800">GV An</strong>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2.5 mt-3 border-t border-slate-100 flex justify-end">
            <button
              onClick={() => navigate('/monitoring')}
              className="flex items-center gap-1.5 bg-[#1565F9] hover:bg-blue-700 text-white text-[12.5px] font-semibold px-3.5 py-2 rounded-xl transition cursor-pointer shadow-sm"
            >
              <span>Xem trạng thái</span>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>

        {/* Sức khỏe hệ thống */}
        <div className="col-span-5 bg-white rounded-2xl border border-slate-200/70 p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6.5 h-6.5 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
              <Settings size={14} strokeWidth={2.2} />
            </div>
            <h2 className="text-[15px] font-bold text-slate-900">Sức khỏe hệ thống</h2>
          </div>

          <div className="divide-y divide-slate-100">
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#E2F7EB] text-[#10B981] flex items-center justify-center">
                  <Settings size={16} />
                </div>
                <span className="text-[13px] font-bold text-slate-800">API</span>
              </div>
              <span className="flex items-center gap-2 text-[12.5px] font-semibold text-[#059669]">
                <span className="w-2 h-2 rounded-full bg-[#10B981]" />
                Hoạt động
              </span>
            </div>

            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#E6F0FF] text-[#1565F9] flex items-center justify-center">
                  <Database size={16} />
                </div>
                <span className="text-[13px] font-bold text-slate-800">Lưu checkpoint</span>
              </div>
              <span className="flex items-center gap-2 text-[12.5px] font-semibold text-[#059669]">
                <span className="w-2 h-2 rounded-full bg-[#10B981]" />
                Hoạt động
              </span>
            </div>

            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#FEF3C7] text-[#F59E0B] flex items-center justify-center">
                  <List size={16} />
                </div>
                <span className="text-[13px] font-bold text-slate-800">Hàng đợi AI</span>
              </div>
              <span className="flex items-center gap-2 text-[12.5px] font-semibold text-[#D97706]">
                <span className="w-2 h-2 rounded-full bg-[#F59E0B]" />
                Có độ trễ
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Việc cần xử lý */}
      <div className="bg-white rounded-2xl border border-slate-200/70 p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
        <div className="flex items-center gap-2 mb-2.5">
          <div className="w-6.5 h-6.5 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
            <List size={14} strokeWidth={2.2} />
          </div>
          <h2 className="text-[15px] font-bold text-slate-900">Việc cần xử lý</h2>
        </div>

        <div className="border border-slate-100 rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#F4F7FB] border-b border-slate-100">
                <th className="text-left px-3.5 py-2 text-[12px] font-semibold text-slate-600">
                  Mô tả
                </th>
                <th className="text-left px-3.5 py-2 text-[12px] font-semibold text-slate-600 w-40">
                  Mã sự cố
                </th>
                <th className="text-left px-3.5 py-2 text-[12px] font-semibold text-slate-600 w-40">
                  Hành động
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {TASKS.map((t) => (
                <tr key={t.code} className="hover:bg-slate-50/60 transition">
                  <td className="px-3.5 py-2.5">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-9 h-9 ${t.iconBg} ${t.iconColor} rounded-xl flex items-center justify-center flex-shrink-0`}
                      >
                        <AlertTriangle size={17} strokeWidth={2} />
                      </div>
                      <div>
                        <p className="font-bold text-slate-900 text-[13px]">{t.title}</p>
                        <p className="text-[11.5px] text-slate-500 mt-0.5">{t.desc}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-3.5 py-2.5 font-bold text-slate-800 text-[13px] whitespace-nowrap">
                    {t.code}
                  </td>
                  <td className="px-3.5 py-2.5 whitespace-nowrap">
                    <button
                      onClick={() => navigate('/monitoring')}
                      className="inline-flex items-center justify-center w-28 bg-[#EAF2FF] hover:bg-blue-100 text-[#1565F9] border border-blue-200/80 text-[12.5px] font-semibold py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap"
                    >
                      {t.action}
                    </button>
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
              <span>Phạm vi một trường • Dữ liệu tổng hợp theo quyền.</span>
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
