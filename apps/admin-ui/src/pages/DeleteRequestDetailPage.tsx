import { useNavigate } from 'react-router-dom'
import {
  ChevronLeft,
  Shield,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Image as ImageIcon,
  Laptop,
  Cloud,
  Database,
  Eye,
  RotateCcw,
  Folder,
  List,
  Check,
} from 'lucide-react'

const STEPS = [
  { num: 1, label: 'Tiếp nhận', date: '10/10/2026', done: true },
  { num: 2, label: 'Kiểm tra quyền', date: '10/10/2026', done: true },
  { num: 3, label: 'Đánh giá tác động', date: '10/10/2026', done: true },
  { num: 4, label: 'Xử lý', date: '10/10/2026', done: true },
  { num: 5, label: 'Kiểm chứng', date: 'Đang thực hiện', done: false },
]

const STORAGE_ROWS = [
  {
    icon: FileText,
    place: 'Dữ liệu hoạt động',
    result: 'Đã xóa',
    resultColor: 'green',
    evidence: 'RC-01',
    badge: { label: 'Đã kiểm chứng', color: 'green' },
    next: '—',
  },
  {
    icon: ImageIcon,
    place: 'Tranh chung',
    result: 'Đã tạo bản che dữ liệu',
    resultColor: 'blue',
    evidence: 'RC-02',
    badge: { label: 'Đã review tác động', color: 'blue' },
    next: '—',
  },
  {
    icon: Laptop,
    place: 'Cache thiết bị',
    result: 'Chờ kết nối',
    resultColor: 'amber',
    evidence: 'Chưa có',
    badge: null,
    next: 'Xác nhận khi thiết bị trở lại',
  },
  {
    icon: Cloud,
    place: 'Bản sao provider',
    result: 'Chờ xử lý',
    resultColor: 'amber',
    evidence: 'Chưa có',
    badge: null,
    next: 'Theo dõi yêu cầu',
  },
  {
    icon: Database,
    place: 'Backup',
    result: 'Ngoại lệ có thời hạn',
    resultColor: 'red',
    evidence: 'EX-01',
    badge: null,
    next: 'Kiểm tra chính sách riêng',
  },
]

export function DeleteRequestDetailPage() {
  const navigate = useNavigate()

  return (
    <div className="px-6 py-2.5 space-y-2 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[24px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
            Yêu cầu xóa dữ liệu
          </h1>
          <p className="text-[13px] text-slate-500 mt-0.5 font-medium">
            Xem chi tiết và theo dõi tiến trình xử lý yêu cầu xóa dữ liệu.
          </p>
        </div>
        <button
          onClick={() => navigate('/data-requests')}
          className="flex items-center gap-1.5 border border-slate-200/90 bg-white hover:bg-slate-50 text-slate-700 text-[12.5px] font-semibold px-3.5 py-1.5 rounded-xl shadow-[0_1px_2px_rgba(15,23,42,0.03)] shrink-0 transition cursor-pointer whitespace-nowrap"
        >
          <ChevronLeft size={15} />
          <span>Quay lại danh sách</span>
        </button>
      </div>

      {/* Row 1: 2 Cards (Left 7 cols: Info & Metadata, Right 5 cols: Impact & Notice) */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* Left Card (7 cols) */}
        <div className="col-span-7 bg-white border border-slate-200/70 rounded-2xl p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between space-y-2.5">
          {/* Warning banner */}
          <div className="flex items-center justify-between gap-3 bg-[#FEF6E7] border border-amber-200/60 rounded-2xl p-2.5 px-3.5">
            <div className="flex items-center gap-3">
              <AlertTriangle className="text-[#F59E0B] shrink-0" size={24} strokeWidth={2} />
              <div>
                <p className="text-[15.5px] font-extrabold text-slate-900 leading-tight">
                  Hoàn tất một phần
                </p>
                <p className="text-[12px] text-slate-600 mt-0.5">
                  Một số bản sao vẫn đang chờ xử lý.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-[#E2F7EB] border border-emerald-200/80 text-[#059669] px-3 py-1.5 rounded-xl text-left shrink-0">
              <ShieldCheck size={16} className="text-[#059669] shrink-0" />
              <div>
                <p className="text-[12px] font-bold text-[#065F46] leading-tight">Đã xác minh</p>
                <p className="text-[10.5px] text-[#059669] leading-tight mt-0.5">Quyền yêu cầu</p>
              </div>
            </div>
          </div>

          {/* Single-column horizontal key-value list matching A08b */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-[12.5px] px-1">
            <div className="flex items-start">
              <span className="text-slate-500 w-28 shrink-0">Mã yêu cầu</span>
              <span className="font-bold text-slate-900">DR-024</span>
            </div>
            <div className="flex items-start">
              <span className="text-slate-500 w-28 shrink-0">Đối tượng</span>
              <span className="font-bold text-slate-900">HS-021</span>
            </div>
            <div className="flex items-start">
              <span className="text-slate-500 w-28 shrink-0">Phạm vi</span>
              <span className="font-bold text-slate-900">Phiên S-024</span>
            </div>
            <div className="flex items-start">
              <span className="text-slate-500 w-28 shrink-0">Ngày tạo</span>
              <span className="font-bold text-slate-900">10/10/2026</span>
            </div>
            <div className="flex items-start col-span-2">
              <span className="text-slate-500 w-28 shrink-0">Lý do yêu cầu</span>
              <span className="text-slate-700 font-medium leading-snug">
                Phụ huynh yêu cầu xóa dữ liệu của con theo quyền cá nhân.
              </span>
            </div>
            <div className="flex items-start col-span-2">
              <span className="text-slate-500 w-28 shrink-0">Người tạo</span>
              <span className="font-bold text-slate-900">Quản trị viên</span>
            </div>
          </div>
        </div>

        {/* Right Card (5 cols) */}
        <div className="col-span-5 bg-white border border-slate-200/70 rounded-2xl p-3.5 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-6.5 h-6.5 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
              <Shield size={14} strokeWidth={2.2} />
            </div>
            <h2 className="text-[15px] font-bold text-slate-900">Tác động và lưu ý</h2>
          </div>

          <div className="space-y-2 flex-1 flex flex-col justify-center">
            {/* Box 1: Team contribution */}
            <div className="p-2.5 px-3 bg-[#EAF3FF] rounded-xl border border-blue-200/60 flex items-start gap-2.5">
              <span className="w-4.5 h-4.5 rounded-full bg-[#1565F9] text-white flex items-center justify-center text-[10.5px] font-bold shrink-0 mt-0.5">
                i
              </span>
              <div>
                <p className="text-[12.5px] font-bold text-[#1565F9]">
                  Bảo vệ phần đóng góp của các bạn cùng nhóm
                </p>
                <p className="text-[11.5px] text-slate-700 leading-snug mt-0.5">
                  Dữ liệu trong tranh chung có thể chứa đóng góp của nhiều học sinh. Cần xem xét và xử lý phù hợp, đảm bảo không ảnh hưởng đến các bạn khác.
                </p>
              </div>
            </div>

            {/* Box 2: Attribution */}
            <div className="p-2.5 px-3 bg-[#FEF6E7] rounded-xl border border-amber-200/60 flex items-start gap-2.5">
              <FileText size={15} className="text-[#D97706] shrink-0 mt-0.5" />
              <div>
                <p className="text-[12.5px] font-bold text-[#B45309]">Cần xem xét ghi công</p>
                <p className="text-[11.5px] text-slate-700 leading-snug mt-0.5">
                  Xử lý ghi công theo chính sách và bảo vệ đóng góp của các bạn. Không suy đoán bằng AI.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Progress Stepper */}
      <div className="bg-white border border-slate-200/70 rounded-2xl py-1.5 px-12 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
        <div className="flex items-center justify-between relative">
          {/* Connector Line: blue for 1..4 (75%), gray for 4..5 (25%) */}
          <div className="absolute top-3 left-12 right-12 h-[2px] bg-slate-200 z-0">
            <div className="h-full w-[75%] bg-[#1565F9]" />
          </div>

          {STEPS.map((step) => (
            <div key={step.num} className="flex flex-col items-center relative z-10 w-32">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-[11.5px] font-bold transition ${
                  step.done
                    ? 'bg-[#1565F9] text-white'
                    : 'bg-white border-2 border-slate-300 text-slate-500'
                }`}
              >
                {step.num}
              </div>
              <p className="text-[12px] font-bold text-slate-900 mt-1 text-center">
                {step.label}
              </p>
              <p className="text-[11px] text-slate-500 text-center">{step.date}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Row 3: Storage detail table */}
      <div className="bg-white border border-slate-200/70 rounded-2xl p-3 px-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)]">
        <div className="flex items-center gap-2 mb-1.5">
          <div className="w-6.5 h-6.5 rounded-lg bg-[#E6F0FF] flex items-center justify-center text-[#1565F9]">
            <List size={14} strokeWidth={2.2} />
          </div>
          <h2 className="text-[15px] font-bold text-slate-900">Chi tiết xử lý theo nơi lưu</h2>
        </div>

        <div className="border border-slate-100 rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#F4F7FB] border-b border-slate-100">
                <th className="px-3.5 py-2 text-left text-[11.5px] font-semibold text-slate-600">
                  Nơi lưu
                </th>
                <th className="px-3.5 py-2 text-left text-[11.5px] font-semibold text-slate-600">
                  Kết quả
                </th>
                <th className="px-3.5 py-2 text-left text-[11.5px] font-semibold text-slate-600">
                  Bằng chứng
                </th>
                <th className="px-3.5 py-2 text-left text-[11.5px] font-semibold text-slate-600">
                  Bước tiếp theo
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {STORAGE_ROWS.map((row) => {
                const Icon = row.icon
                return (
                  <tr key={row.place} className="hover:bg-slate-50/60 transition">
                    <td className="px-3.5 py-1.5">
                      <div className="flex items-center gap-2.5">
                        <Icon size={15} className="text-slate-600" />
                        <span className="text-slate-900 font-semibold text-[13px]">
                          {row.place}
                        </span>
                      </div>
                    </td>
                    <td className="px-3.5 py-1.5">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            row.resultColor === 'green'
                              ? 'bg-[#10B981]'
                              : row.resultColor === 'blue'
                              ? 'bg-[#1565F9]'
                              : row.resultColor === 'amber'
                              ? 'bg-[#F59E0B]'
                              : 'bg-[#EF4444]'
                          }`}
                        />
                        <span className="text-slate-800 font-medium text-[13px]">
                          {row.result}
                        </span>
                      </div>
                    </td>
                    <td className="px-3.5 py-1.5 whitespace-nowrap">
                      <div className="flex items-center gap-5">
                        <span className="text-slate-800 text-[13px] font-medium w-16 whitespace-nowrap">
                          {row.evidence}
                        </span>
                        {row.badge && (
                          <span
                            className={`inline-flex items-center gap-1.5 text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0 ${
                              row.badge.color === 'green'
                                ? 'bg-[#E2F7EB] text-[#059669]'
                                : 'bg-[#E6F0FF] text-[#1565F9]'
                            }`}
                          >
                            <span
                              className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-white shrink-0 ${
                                row.badge.color === 'green' ? 'bg-[#10B981]' : 'bg-[#1565F9]'
                              }`}
                            >
                              <Check size={9} strokeWidth={3} />
                            </span>
                            {row.badge.label}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-3.5 py-1.5 text-slate-600 text-[13px] whitespace-nowrap">{row.next}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Row 4: Bottom banner and actions */}
      <div className="flex items-center justify-between gap-4 bg-[#FEF6E7] border border-amber-200/80 rounded-2xl p-2 px-3.5">
        <div className="flex items-center gap-2.5">
          <div className="w-5.5 h-5.5 rounded bg-[#F59E0B] text-white flex items-center justify-center font-bold text-xs shrink-0">
            !
          </div>
          <div>
            <p className="text-[12.5px] font-bold text-[#92400E]">
              Không đồng nghĩa đã xóa toàn bộ bản sao.
            </p>
            <p className="text-[11.5px] text-slate-600">
              Một số bản sao có thể vẫn tồn tại theo chính sách và đang trong quá trình xử lý.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button className="flex items-center gap-1.5 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[12.5px] font-semibold px-3 py-1.5 rounded-xl shadow-sm transition cursor-pointer whitespace-nowrap">
            <Eye size={14} />
            <span>Theo dõi ngoại lệ</span>
          </button>
          <button
            disabled
            className="flex items-center gap-1.5 border border-slate-200 bg-slate-100 text-slate-400 text-[12.5px] font-semibold px-3 py-1.5 rounded-xl cursor-not-allowed whitespace-nowrap"
          >
            <RotateCcw size={13.5} />
            <span>Thử lại bước lỗi</span>
          </button>
          <button className="flex items-center gap-1.5 bg-[#1565F9] hover:bg-blue-700 text-white text-[12.5px] font-semibold px-3.5 py-1.5 rounded-xl shadow-sm transition cursor-pointer whitespace-nowrap">
            <Folder size={14} />
            <span>Xem bằng chứng theo quyền</span>
          </button>
        </div>
      </div>
    </div>
  )
}

