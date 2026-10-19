import { useState } from 'react'
import {
  FileText,
  Search,
  Play,
  Database,
  Target,
  Laptop,
  Clock,
  Image as ImageIcon,
  Users,
  Folder,
  AlertTriangle,
  BarChart2,
  Calendar,
  Layers,
  User,
  Info,
} from 'lucide-react'

type Tab = 'policy' | 'purpose' | 'device' | 'history'

const DATA_POLICIES = [
  {
    icon: ImageIcon,
    iconBg: 'bg-emerald-50 text-emerald-600',
    name: 'Tranh & dữ liệu phiên',
    desc: 'Sản phẩm sáng tạo và dữ liệu phát sinh trong phiên.',
    retention: '90 ngày',
    milestone: 'Sau khi phiên kết thúc',
    status: 'Đã xác nhận',
    statusColor: 'green',
  },
  {
    icon: Users,
    iconBg: 'bg-blue-50 text-blue-600',
    name: 'Hồ sơ trẻ',
    desc: 'Thông tin phục vụ quản lý và tổ chức lớp học.',
    retention: 'Cần hoàn thiện',
    milestone: 'Chính sách riêng',
    status: 'Chưa sẵn sàng',
    statusColor: 'red',
  },
  {
    icon: Folder,
    iconBg: 'bg-amber-50 text-amber-600',
    name: 'Portfolio',
    desc: 'Tuyển tập sản phẩm theo lớp và theo chủ đề.',
    retention: 'Cần hoàn thiện',
    milestone: 'Chính sách riêng',
    status: 'Chưa sẵn sàng',
    statusColor: 'red',
  },
  {
    icon: FileText,
    iconBg: 'bg-purple-50 text-purple-600',
    name: 'Audit',
    desc: 'Nhật ký hệ thống và hoạt động quản trị.',
    retention: 'Cần hoàn thiện',
    milestone: 'Chính sách riêng',
    status: 'Chưa sẵn sàng',
    statusColor: 'red',
  },
  {
    icon: Database,
    iconBg: 'bg-rose-50 text-rose-600',
    name: 'Bản sao provider/backup',
    desc: 'Bản sao và dữ liệu dự phòng từ nhà cung cấp.',
    retention: 'Cần review',
    milestone: 'Theo loại bản sao',
    status: 'Chưa sẵn sàng',
    statusColor: 'red',
  },
]

const TABS: { key: Tab; label: string; icon: typeof Database }[] = [
  { key: 'policy', label: 'Chính sách dữ liệu', icon: Database },
  { key: 'purpose', label: 'Mục đích', icon: Target },
  { key: 'device', label: 'Thiết bị & hỗ trợ', icon: Laptop },
  { key: 'history', label: 'Lịch sử phiên bản', icon: Clock },
]

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('policy')

  return (
    <div className="flex h-full overflow-hidden">
      {/* LEFT — main */}
      <div className="flex-1 flex flex-col overflow-auto p-6 space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cấu hình & vòng đời dữ liệu</h1>
            <p className="text-sm text-gray-500 mt-1">Thiết lập chính sách, mục đích và cách xử lý dữ liệu trong toàn trường.</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <div className="flex items-center gap-2 border border-gray-200/80 bg-gray-50/50 rounded-xl px-3 py-1.5 text-xs text-gray-500">
              <span>Phiên bản đang hiệu lực</span>
              <span className="bg-emerald-100 text-emerald-700 font-bold px-2 py-0.5 rounded-full text-xs">
                v1
              </span>
            </div>
            <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2.5 rounded-xl shadow-sm transition">
              <FileText size={15} />
              Tạo bản nháp
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2">
          {TABS.map((t) => {
            const Icon = t.icon
            const isActive = activeTab === t.key
            return (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl transition ${
                  isActive
                    ? 'bg-blue-50 text-blue-600 font-semibold'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon size={16} className={isActive ? 'text-blue-600' : 'text-gray-400'} />
                {t.label}
              </button>
            )
          })}
        </div>

        {/* Policy tab content */}
        {activeTab === 'policy' && (
          <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-100">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                  <Database size={15} />
                </div>
                <h2 className="text-base font-bold text-gray-900">Chính sách dữ liệu</h2>
              </div>
              <p className="text-xs text-gray-500 mt-1">Quy định thời hạn lưu trữ và nguyên tắc xử lý cho từng loại dữ liệu.</p>
            </div>

            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50/70 border-b border-gray-100">
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Loại dữ liệu</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Thời hạn</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Mốc tính</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {DATA_POLICIES.map((policy) => {
                  const Icon = policy.icon
                  return (
                    <tr key={policy.name} className="border-b border-gray-50 hover:bg-gray-50/60 transition">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-9 h-9 rounded-xl ${policy.iconBg} flex items-center justify-center shrink-0`}>
                            <Icon size={18} />
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 text-sm">{policy.name}</p>
                            <p className="text-xs text-gray-400 mt-0.5">{policy.desc}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-gray-800 font-medium text-sm">{policy.retention}</td>
                      <td className="px-5 py-4 text-gray-600 text-sm">{policy.milestone}</td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${
                            policy.statusColor === 'green'
                              ? 'bg-emerald-50 text-emerald-700'
                              : 'bg-rose-50 text-rose-700'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              policy.statusColor === 'green' ? 'bg-emerald-500' : 'bg-rose-500'
                            }`}
                          />
                          {policy.status}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>

            {/* Footer info callout */}
            <div className="p-4">
              <div className="px-4 py-3 bg-blue-50/70 border border-blue-200/80 rounded-xl flex items-center gap-2.5 text-sm text-blue-800">
                <Info size={16} className="text-blue-600 shrink-0" />
                <div>
                  <span className="font-bold text-blue-900">Không đổi ngầm policy đang được pin trong phiên.</span>
                  <p className="text-xs text-blue-700 mt-0.5">Các thay đổi chỉ có hiệu lực khi kích hoạt phiên bản mới.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Placeholder for other tabs */}
        {activeTab !== 'policy' && (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            <div className="text-center">
              <p className="text-4xl mb-3">🚧</p>
              <p>Tab này đang được phát triển</p>
            </div>
          </div>
        )}

        {/* Watermark */}
        <div className="text-right text-xs text-gray-400 py-1">
          Dữ liệu minh họa • Bản thiết kế UI.
        </div>
      </div>

      {/* RIGHT — Draft panel */}
      <div className="w-[340px] shrink-0 border-l border-gray-200 bg-white p-5 space-y-4 overflow-auto">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
          <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <FileText size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-gray-900">Bản nháp v2</h2>
            <p className="text-xs text-gray-400">Chưa sẵn sàng để kích hoạt.</p>
          </div>
        </div>

        {/* Warning alert */}
        <div className="flex items-start gap-3 p-3 bg-amber-50/80 rounded-xl border border-amber-200/80">
          <AlertTriangle size={18} className="text-amber-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-xs font-bold text-amber-900">Chưa đủ chính sách bắt buộc để kích hoạt.</p>
            <p className="text-[11px] text-amber-700 mt-0.5">Vui lòng hoàn thiện các mục còn thiếu.</p>
          </div>
        </div>

        {/* Metadata */}
        <div className="space-y-3.5 py-1">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-gray-600">
              <BarChart2 size={15} className="text-emerald-500" />
              <span>Phiên bản</span>
            </div>
            <span className="font-semibold text-gray-900">v2 (bản nháp)</span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-gray-600">
              <Calendar size={15} className="text-blue-500" />
              <span>Ngày tạo</span>
            </div>
            <span className="font-semibold text-gray-900">10/10/2026</span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-gray-600">
              <Layers size={15} className="text-purple-500" />
              <span>Hiệu lực</span>
            </div>
            <div className="flex items-center gap-1.5 font-semibold text-amber-600">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
              <span>Cần xác nhận</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-gray-600">
              <User size={15} className="text-gray-400" />
              <span>Người phê duyệt</span>
            </div>
            <div className="flex items-center gap-1.5 font-semibold text-rose-500">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
              <span>Chưa duyệt</span>
            </div>
          </div>

          {/* Lý do thay đổi */}
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <FileText size={14} className="text-gray-400" />
              <span className="font-medium">Lý do thay đổi</span>
            </div>
            <p className="text-xs text-gray-600 leading-relaxed pl-5">
              Cập nhật chính sách dữ liệu và bổ sung phạm vi xử lý cho các loại dữ liệu.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2.5 pt-2">
          <button className="w-full flex items-center justify-center gap-2 border border-blue-600 text-blue-600 hover:bg-blue-50 font-semibold text-xs py-2.5 rounded-xl shadow-sm transition">
            <Search size={14} />
            Kiểm tra bản nháp
          </button>
          <button
            disabled
            className="w-full flex items-center justify-center gap-2 bg-gray-200 text-gray-400 font-semibold text-xs py-2.5 rounded-xl cursor-not-allowed"
          >
            <Play size={14} />
            Kích hoạt
          </button>
          <p className="text-[11px] text-center text-gray-400">Hoàn thiện các mục bắt buộc để kích hoạt.</p>
        </div>
      </div>
    </div>
  )
}
