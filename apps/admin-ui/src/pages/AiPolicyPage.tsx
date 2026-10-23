import {
  FilePlus,
  Lock,
  Search,
  List,
  PauseCircle,
  Shield,
  FileText,
  Users,
  Play,
  SlidersHorizontal,
  Database,
  Check,
  AlertTriangle,
  Minus,
} from 'lucide-react'

const SAFETY_RULES = [
  {
    icon: Users,
    bg: 'bg-[#E6F0FF] text-[#1565F9]',
    title: 'Giáo viên duyệt từng gợi ý AI',
    desc: 'Mỗi gợi ý AI phải được giáo viên duyệt trước khi gửi cho trẻ.',
  },
  {
    icon: Play,
    bg: 'bg-[#FEF3C7] text-[#F59E0B]',
    isPlayCircle: true,
    title: 'Duyệt video trước trình chiếu',
    desc: 'Video do AI tạo cần được duyệt trước khi trình chiếu cho trẻ.',
  },
  {
    icon: FileText,
    bg: 'bg-[#E2F7EB] text-[#10B981]',
    title: 'Kiểm tra consent theo mục đích',
    desc: 'Chỉ cho phép tạo nội dung khi đã có consent phù hợp theo mục đích.',
  },
  {
    icon: Shield,
    bg: 'bg-[#FEE2E2] text-[#EF4444]',
    title: 'Kiểm tra an toàn',
    desc: 'Tự động kiểm tra nội dung để phát hiện rủi ro trước khi duyệt.',
  },
]

const COMPAT_CHECKS = [
  {
    status: 'ok',
    label: 'Cài đặt an toàn',
    badge: 'Đạt',
    badgeColor: 'text-[#059669] bg-[#E2F7EB]',
  },
  {
    status: 'ok',
    label: 'Phạm vi áp dụng',
    badge: 'Đạt',
    badgeColor: 'text-[#059669] bg-[#E2F7EB]',
  },
  {
    status: 'warn',
    label: 'Ảnh hưởng đến quy trình',
    badge: 'Cần đánh giá',
    badgeColor: 'text-[#D97706] bg-[#FEF3C7]',
  },
  {
    status: 'none',
    label: 'Tính nhất quán chính sách',
    badge: 'Chưa kiểm tra',
    badgeColor: 'text-slate-600 bg-slate-100',
  },
  {
    status: 'warn',
    label: 'Ghi chú thay đổi',
    badge: 'Cần bổ sung',
    badgeColor: 'text-[#D97706] bg-[#FEF3C7]',
  },
]

export function AiPolicyPage() {
  return (
    <div className="px-6 py-3 space-y-2.5 max-w-[1440px] mx-auto">
      {/* Full-width Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[24px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
            Chính sách AI
          </h1>
          <p className="text-[13px] text-slate-500 mt-0.5 font-medium">
            Chính sách có phiên bản • áp dụng theo phạm vi.
          </p>
        </div>
        <button className="flex items-center gap-2 bg-[#1565F9] hover:bg-blue-700 text-white text-[12.5px] font-semibold px-3.5 py-2 rounded-xl transition shadow-sm cursor-pointer whitespace-nowrap shrink-0">
          <FilePlus size={14} />
          <span>Tạo bản nháp</span>
        </button>
      </div>

      {/* Full-width Top 2 Stat Cards */}
      <div className="grid grid-cols-12 gap-4">
        {/* Phiên bản hiệu lực */}
        <div className="col-span-6 bg-white rounded-2xl border border-slate-200/70 p-3 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 bg-[#E2F7EB] text-[#10B981] rounded-2xl flex items-center justify-center shrink-0">
              <FileText size={22} strokeWidth={2} />
            </div>
            <div>
              <p className="text-[12.5px] text-slate-600 font-medium">Phiên bản hiệu lực</p>
              <p className="text-[24px] leading-tight font-extrabold text-slate-900 mt-0.5">P1</p>
            </div>
          </div>
          <span className="flex items-center gap-1.5 text-[11.5px] font-semibold text-[#059669] bg-[#E2F7EB] px-3 py-1 rounded-full">
            <span className="w-2 h-2 bg-[#10B981] rounded-full" />
            Đang hiệu lực
          </span>
        </div>

        {/* Tác vụ đang chờ */}
        <div className="col-span-6 bg-white rounded-2xl border border-slate-200/70 p-3 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center gap-3.5">
          <div className="w-11 h-11 bg-[#FEF3C7] text-[#F59E0B] rounded-2xl flex items-center justify-center shrink-0">
            <List size={22} strokeWidth={2.2} />
          </div>
          <div>
            <p className="text-[12.5px] text-slate-600 font-medium">Tác vụ đang chờ</p>
            <p className="text-[24px] leading-tight font-extrabold text-slate-900 mt-0.5">3</p>
          </div>
        </div>
      </div>

      {/* Middle 2-Column Section: Cài đặt an toàn (7 cols) + Bản nháp P2 (5 cols) */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* LEFT — Cài đặt an toàn */}
        <div className="col-span-7 bg-white rounded-2xl border border-slate-200/70 p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
          <div className="flex items-center gap-2 mb-0.5">
            <div className="w-6.5 h-6.5 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
              <Shield size={14} strokeWidth={2.2} />
            </div>
            <h2 className="text-[15px] font-bold text-slate-900">
              Cài đặt an toàn{' '}
              <span className="text-slate-500 font-medium text-[13.5px]">
                (đang áp dụng cho P1)
              </span>
            </h2>
          </div>
          <p className="text-[12px] text-slate-500 mb-2 ml-8">
            Các quy tắc bảo vệ trẻ em và kiểm soát nội dung được bật bắt buộc.
          </p>

          <div className="divide-y divide-slate-100">
            {SAFETY_RULES.map((r) => {
              const Icon = r.icon
              return (
                <div key={r.title} className="flex items-center justify-between py-2 first:pt-1 last:pb-0">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 ${r.bg} rounded-xl flex items-center justify-center flex-shrink-0`}
                    >
                      {r.isPlayCircle ? (
                        <div className="w-5 h-5 rounded-full bg-[#F59E0B] text-white flex items-center justify-center">
                          <Play size={10} fill="currentColor" className="ml-0.5" />
                        </div>
                      ) : (
                        <Icon size={18} />
                      )}
                    </div>
                    <div>
                      <p className="text-[13px] font-bold text-slate-900">{r.title}</p>
                      <p className="text-[11.5px] text-slate-500 mt-0.5">{r.desc}</p>
                    </div>
                  </div>
                  <span className="flex items-center gap-1.5 text-[11.5px] font-semibold text-[#1565F9] bg-[#EAF2FF] px-3 py-1.5 rounded-xl flex-shrink-0 ml-3 whitespace-nowrap">
                    <Lock size={12} />
                    <span>Bắt buộc</span>
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* RIGHT — Bản nháp P2 */}
        <div className="col-span-5 bg-white rounded-2xl border border-slate-200/70 p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-2">
                <div className="w-6.5 h-6.5 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
                  <FileText size={14} strokeWidth={2.2} />
                </div>
                <p className="font-bold text-slate-900 text-[15px]">Bản nháp P2</p>
              </div>
              <span className="flex items-center gap-1.5 text-[11.5px] font-semibold text-[#DC2626] bg-[#FEE2E2] px-2.5 py-0.5 rounded-full">
                <span className="w-2 h-2 bg-[#EF4444] rounded-full" />
                Cần đánh giá
              </span>
            </div>

            <div className="bg-[#FEF5E7] border border-amber-200/70 rounded-xl p-2.5 px-3 flex items-start gap-2.5 mb-2.5">
              <span className="w-5 h-5 rounded-full border-2 border-[#D97706] text-[#D97706] flex items-center justify-center text-[11px] font-extrabold shrink-0 mt-0.5">
                !
              </span>
              <div>
                <p className="text-[12.5px] font-bold text-[#B45309]">Chưa được kích hoạt</p>
                <p className="text-[11.5px] text-slate-600 mt-0.5">
                  Bản nháp này chưa được áp dụng cho trường.
                </p>
              </div>
            </div>

            <p className="text-[13px] font-bold text-slate-900 mb-0.5">
              Kết quả đánh giá tương thích
            </p>
            <p className="text-[11.5px] text-slate-500 mb-1.5">
              Kiểm tra các yêu cầu an toàn và phạm vi áp dụng.
            </p>

            <div className="divide-y divide-slate-100">
              {COMPAT_CHECKS.map((c) => (
                <div key={c.label} className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2">
                    {c.status === 'ok' && (
                      <span className="w-4 h-4 rounded-full bg-[#10B981] text-white flex items-center justify-center shrink-0">
                        <Check size={10} strokeWidth={3} />
                      </span>
                    )}
                    {c.status === 'warn' && (
                      <AlertTriangle size={15} className="text-[#F59E0B] shrink-0" />
                    )}
                    {c.status === 'none' && (
                      <span className="w-4 h-4 rounded-full bg-slate-500 text-white flex items-center justify-center shrink-0">
                        <Minus size={10} strokeWidth={3} />
                      </span>
                    )}
                    <span className="text-[12.5px] font-medium text-slate-700">{c.label}</span>
                  </div>
                  <span
                    className={`text-[11px] font-semibold px-2 py-0.5 rounded-lg whitespace-nowrap shrink-0 ${c.badgeColor}`}
                  >
                    {c.badge}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom 2-Column Section: Mức hỗ trợ AI + Ngân sách và giới hạn */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-6 bg-white rounded-2xl border border-slate-200/70 p-3 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-start gap-3">
          <div className="w-8 h-8 bg-[#E6F0FF] text-[#1565F9] rounded-xl flex items-center justify-center shrink-0 mt-0.5">
            <SlidersHorizontal size={16} />
          </div>
          <div>
            <h3 className="text-[14px] font-bold text-slate-900">Mức hỗ trợ AI</h3>
            <p className="text-[12px] font-semibold text-slate-600 mt-0.5">Theo cấu hình phiên</p>
            <p className="text-[11.5px] text-slate-500 mt-0.5 leading-snug">
              Phạm vi tính năng AI được cấu hình theo phiên bản chính sách đang hiệu lực tại trường.
            </p>
          </div>
        </div>

        <div className="col-span-6 bg-white rounded-2xl border border-slate-200/70 p-3 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-start gap-3">
          <div className="w-8 h-8 bg-[#E6F0FF] text-[#1565F9] rounded-xl flex items-center justify-center shrink-0 mt-0.5">
            <Database size={16} />
          </div>
          <div>
            <h3 className="text-[14px] font-bold text-slate-900">Ngân sách và giới hạn</h3>
            <p className="text-[12px] font-semibold text-slate-600 mt-0.5">Cần phê duyệt</p>
            <p className="text-[11.5px] text-slate-500 mt-0.5 leading-snug">
              Mọi thay đổi về ngân sách và giới hạn sử dụng cần được phê duyệt theo chính sách của trường.
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Action Bar & Watermark */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 bg-[#EAF3FF]/90 border border-blue-200/80 rounded-2xl p-1.5 px-3 flex items-center gap-2">
          <button className="flex items-center gap-1.5 bg-[#1565F9] hover:bg-blue-700 text-white text-[12.5px] font-semibold px-3.5 py-1.5 rounded-xl transition cursor-pointer shadow-sm whitespace-nowrap shrink-0">
            <Search size={13.5} />
            <span>Kiểm tra bản nháp</span>
          </button>
          <button className="flex items-center gap-1.5 border border-blue-200 bg-white text-[#1565F9] text-[12.5px] font-semibold px-3.5 py-1.5 rounded-xl hover:bg-blue-50 transition cursor-pointer whitespace-nowrap shrink-0">
            <List size={13.5} />
            <span>Xem thay đổi</span>
          </button>
          <button className="flex items-center gap-1.5 border border-rose-200 bg-[#FEE2E2]/80 text-[#DC2626] text-[12.5px] font-semibold px-3.5 py-1.5 rounded-xl hover:bg-rose-100 transition cursor-pointer whitespace-nowrap shrink-0">
            <PauseCircle size={13.5} />
            <span>Tạm dừng hàng đợi</span>
          </button>
          <div className="h-4 w-px bg-blue-200 mx-1" />
          <div className="flex items-center gap-1.5 text-[11.5px] text-slate-600 font-medium">
            <span className="w-4 h-4 rounded-full border border-slate-500 text-slate-600 flex items-center justify-center text-[10px] font-bold shrink-0">
              i
            </span>
            <span>Ngăn tác vụ mới trong phạm vi; tác vụ đang chạy xử lý theo chính sách.</span>
          </div>
        </div>
      </div>
    </div>
  )
}
