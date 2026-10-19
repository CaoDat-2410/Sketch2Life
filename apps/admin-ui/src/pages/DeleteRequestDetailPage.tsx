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
  FolderOpen,
  Info,
  List,
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
    iconColor: 'text-gray-500',
    place: 'Dữ liệu hoạt động',
    result: 'Đã xóa',
    resultColor: 'green',
    evidence: 'RC-01',
    badge: { label: 'Đã kiểm chứng', color: 'green' },
    next: '—',
  },
  {
    icon: ImageIcon,
    iconColor: 'text-gray-500',
    place: 'Tranh chung',
    result: 'Đã tạo bản che dữ liệu',
    resultColor: 'blue',
    evidence: 'RC-02',
    badge: { label: 'Đã review tác động', color: 'blue' },
    next: '—',
  },
  {
    icon: Laptop,
    iconColor: 'text-gray-500',
    place: 'Cache thiết bị',
    result: 'Chờ kết nối',
    resultColor: 'amber',
    evidence: 'Chưa có',
    badge: null,
    next: 'Xác nhận khi thiết bị trở lại',
  },
  {
    icon: Cloud,
    iconColor: 'text-gray-500',
    place: 'Bản sao provider',
    result: 'Chờ xử lý',
    resultColor: 'amber',
    evidence: 'Chưa có',
    badge: null,
    next: 'Theo dõi yêu cầu',
  },
  {
    icon: Database,
    iconColor: 'text-gray-500',
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
    <div className="flex-1 flex flex-col overflow-auto p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Yêu cầu xóa dữ liệu</h1>
          <p className="text-sm text-gray-500 mt-1">Xem chi tiết và theo dõi tiến trình xử lý yêu cầu xóa dữ liệu.</p>
        </div>
        <button
          onClick={() => navigate('/data-requests')}
          className="flex items-center gap-1.5 border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium px-3.5 py-2 rounded-xl shadow-sm shrink-0 transition"
        >
          <ChevronLeft size={16} />
          Quay lại danh sách
        </button>
      </div>

      {/* Row 1: 2 Cards (Left: Info & Metadata, Right: Impact & Notice) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left Card (span 7 or 8) */}
        <div className="lg:col-span-8 bg-white border border-gray-200/80 rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-5">
          {/* Warning banner */}
          <div className="flex items-center justify-between gap-4 bg-amber-50/80 border border-amber-200/70 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
                <AlertTriangle className="text-amber-500" size={22} />
              </div>
              <div>
                <p className="text-base font-bold text-gray-900">Hoàn tất một phần</p>
                <p className="text-xs text-gray-600 mt-0.5">Một số bản sao vẫn đang chờ xử lý.</p>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200/80 text-emerald-800 px-3.5 py-2 rounded-xl text-left shrink-0">
              <ShieldCheck size={18} className="text-emerald-600 shrink-0" />
              <div>
                <p className="text-xs font-bold text-emerald-900 leading-tight">Đã xác minh</p>
                <p className="text-[11px] text-emerald-700 leading-tight">Quyền yêu cầu</p>
              </div>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-x-8 gap-y-3.5 pt-1">
            <div>
              <p className="text-xs text-gray-400">Mã yêu cầu</p>
              <p className="text-sm font-bold text-gray-900 mt-0.5">DR-024</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Ngày tạo</p>
              <p className="text-sm font-bold text-gray-900 mt-0.5">10/10/2026</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Đối tượng</p>
              <p className="text-sm font-bold text-gray-900 mt-0.5">HS-021</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Người tạo</p>
              <p className="text-sm font-bold text-gray-900 mt-0.5">Quản trị viên</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Phạm vi</p>
              <p className="text-sm font-bold text-gray-900 mt-0.5">Phiên S-024</p>
            </div>
            <div />
            <div className="col-span-2">
              <p className="text-xs text-gray-400">Lý do yêu cầu</p>
              <p className="text-sm font-bold text-gray-900 mt-0.5">
                Phụ huynh yêu cầu xóa dữ liệu của con theo quyền cá nhân.
              </p>
            </div>
          </div>
        </div>

        {/* Right Card (span 4) */}
        <div className="lg:col-span-4 bg-white border border-gray-200/80 rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-4">
          <div className="flex items-center gap-2">
            <Shield size={18} className="text-blue-600" />
            <h2 className="text-base font-bold text-gray-900">Tác động và lưu ý</h2>
          </div>

          <div className="space-y-3 flex-1 flex flex-col justify-center">
            {/* Box 1: Team contribution */}
            <div className="p-4 bg-blue-50/70 rounded-xl border border-blue-100">
              <div className="flex items-center gap-2 mb-1.5">
                <Info size={16} className="text-blue-600 shrink-0" />
                <p className="text-xs font-bold text-blue-900">Bảo vệ phần đóng góp của các bạn cùng nhóm</p>
              </div>
              <p className="text-xs text-blue-700 leading-relaxed">
                Dữ liệu trong tranh chung có thể chứa đóng góp của nhiều học sinh. Cần xem xét và xử lý cho dữ liệu phù hợp, đảm bảo không ảnh hưởng đến các bạn khác.
              </p>
            </div>

            {/* Box 2: Attribution */}
            <div className="p-4 bg-amber-50/70 rounded-xl border border-amber-200/60">
              <div className="flex items-center gap-2 mb-1.5">
                <FileText size={16} className="text-amber-600 shrink-0" />
                <p className="text-xs font-bold text-amber-900">Cần xem xét ghi công</p>
              </div>
              <p className="text-xs text-amber-800 leading-relaxed">
                Xử lý ghi công theo chính sách và bảo vệ đóng góp của các bạn. Không suy đoán bằng AI.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Progress Stepper */}
      <div className="bg-white border border-gray-200/80 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between relative px-6">
          {/* Connector Line behind circles */}
          <div className="absolute top-4 left-14 right-14 h-0.5 bg-blue-600 z-0" />

          {STEPS.map((step) => (
            <div key={step.num} className="flex flex-col items-center relative z-10">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition shadow-sm ${
                  step.done
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border-2 border-gray-300 text-gray-400'
                }`}
              >
                {step.num}
              </div>
              <p className="text-xs font-bold text-gray-900 mt-2 text-center">{step.label}</p>
              <p className="text-[11px] text-gray-500 text-center mt-0.5">{step.date}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Row 3: Storage detail table */}
      <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
            <List size={14} />
          </div>
          <h2 className="text-sm font-bold text-gray-900">Chi tiết xử lý theo nơi lưu</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50/70 border-b border-gray-100">
              <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Nơi lưu</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Kết quả</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Bằng chứng</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Bước tiếp theo</th>
            </tr>
          </thead>
          <tbody>
            {STORAGE_ROWS.map((row) => {
              const Icon = row.icon
              return (
                <tr key={row.place} className="border-b border-gray-50 hover:bg-gray-50/60 transition">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <Icon size={16} className={row.iconColor} />
                      <span className="text-gray-900 font-medium text-sm">{row.place}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          row.resultColor === 'green'
                            ? 'bg-emerald-500'
                            : row.resultColor === 'blue'
                            ? 'bg-blue-500'
                            : row.resultColor === 'amber'
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                        }`}
                      />
                      <span className="text-gray-800 text-sm">{row.result}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-800 text-sm font-medium">{row.evidence}</span>
                      {row.badge && (
                        <span
                          className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                            row.badge.color === 'green'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                              : 'bg-blue-50 text-blue-700 border border-blue-200/60'
                          }`}
                        >
                          {row.badge.color === 'green' ? (
                            <ShieldCheck size={12} className="text-emerald-600" />
                          ) : (
                            <ShieldCheck size={12} className="text-blue-600" />
                          )}
                          {row.badge.label}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-gray-600 text-sm">{row.next}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Row 4: Bottom banner and actions */}
      <div className="flex items-center justify-between gap-4 bg-amber-50/60 border border-amber-200/80 rounded-2xl p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <AlertTriangle size={24} className="text-amber-500 shrink-0" />
          <div>
            <p className="text-sm font-bold text-amber-900">Không đồng nghĩa đã xóa toàn bộ bản sao.</p>
            <p className="text-xs text-amber-700 mt-0.5">
              Một số bản sao có thể vẫn tồn tại theo chính sách và đang trong quá trình xử lý.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <button className="flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium px-4 py-2.5 rounded-xl shadow-sm transition">
            <Eye size={15} />
            Theo dõi ngoại lệ
          </button>
          <button
            disabled
            className="flex items-center gap-2 border border-gray-200 bg-gray-100 text-gray-400 text-sm font-medium px-4 py-2.5 rounded-xl cursor-not-allowed"
          >
            <RotateCcw size={15} />
            Thử lại bước lỗi
          </button>
          <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2.5 rounded-xl shadow-sm transition">
            <FolderOpen size={15} />
            Xem bằng chứng theo quyền
          </button>
        </div>
      </div>

      {/* Watermark */}
      <div className="text-right text-xs text-gray-400 py-1">
        Dữ liệu minh họa • Bản thiết kế UI.
      </div>
    </div>
  )
}
