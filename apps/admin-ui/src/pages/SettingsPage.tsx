import { useState } from 'react'
import {
  FileText,
  FilePlus,
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
} from 'lucide-react'

type Tab = 'policy' | 'purpose' | 'device' | 'history'

const DATA_POLICIES = [
  {
    icon: ImageIcon,
    iconBg: 'bg-[#E2F7EB] text-[#10B981]',
    name: 'Tranh & dữ liệu phiên',
    desc: 'Sản phẩm sáng tạo và dữ liệu phát sinh trong phiên.',
    retention: '90 ngày',
    milestone: 'Sau khi phiên kết thúc',
    status: 'Đã xác nhận',
    statusColor: 'green',
  },
  {
    icon: Users,
    iconBg: 'bg-[#E6F0FF] text-[#1565F9]',
    name: 'Hồ sơ trẻ',
    desc: 'Thông tin phục vụ quản lý và tổ chức lớp học.',
    retention: 'Cần hoàn thiện',
    milestone: 'Chính sách riêng',
    status: 'Chưa sẵn sàng',
    statusColor: 'red',
  },
  {
    icon: Folder,
    iconBg: 'bg-[#FEF3C7] text-[#F59E0B]',
    name: 'Portfolio',
    desc: 'Tuyển tập sản phẩm theo lớp và theo chủ đề.',
    retention: 'Cần hoàn thiện',
    milestone: 'Chính sách riêng',
    status: 'Chưa sẵn sàng',
    statusColor: 'red',
  },
  {
    icon: FileText,
    iconBg: 'bg-[#F3E8FF] text-[#7C3AED]',
    name: 'Audit',
    desc: 'Nhật ký hệ thống và hoạt động quản trị.',
    retention: 'Cần hoàn thiện',
    milestone: 'Chính sách riêng',
    status: 'Chưa sẵn sàng',
    statusColor: 'red',
  },
  {
    icon: Database,
    iconBg: 'bg-[#FEE2E2] text-[#EF4444]',
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
    <div className="px-6 py-4 space-y-3.5 max-w-[1440px] mx-auto">
      {/* Full-width Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[25px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
            Cấu hình &amp; vòng đời dữ liệu
          </h1>
          <p className="text-[13.5px] text-slate-500 mt-0.5 font-medium">
            Thiết lập chính sách, mục đích và cách xử lý dữ liệu trong toàn trường.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-2.5 border border-slate-200/80 bg-[#F4F7FB] rounded-xl px-3.5 py-2 text-[13px] text-slate-600 font-medium whitespace-nowrap">
            <span>Phiên bản đang hiệu lực</span>
            <span className="bg-[#D1FAE5] text-[#059669] font-bold px-2.5 py-0.5 rounded-lg text-[12px]">
              v1
            </span>
          </div>
          <button className="flex items-center gap-2 bg-[#1565F9] hover:bg-blue-700 text-white text-[13px] font-semibold px-4 py-2 rounded-xl shadow-sm transition cursor-pointer whitespace-nowrap shrink-0">
            <FilePlus size={15} />
            <span>Tạo bản nháp</span>
          </button>
        </div>
      </div>

      {/* Full-width 4-Tab Bar Card */}
      <div className="bg-white border border-slate-200/70 rounded-2xl p-1.5 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex items-center">
        {TABS.map((t, idx) => {
          const Icon = t.icon
          const isActive = activeTab === t.key
          return (
            <div key={t.key} className="flex items-center">
              <button
                onClick={() => setActiveTab(t.key)}
                className={`flex items-center gap-2 px-5 py-2 text-[13.5px] rounded-xl transition cursor-pointer whitespace-nowrap ${
                  isActive
                    ? 'bg-[#E6F0FF] text-[#1565F9] font-bold'
                    : 'text-slate-700 font-medium hover:bg-slate-50'
                }`}
              >
                <Icon size={16} className={isActive ? 'text-[#1565F9]' : 'text-slate-600'} />
                <span>{t.label}</span>
              </button>
              {idx < TABS.length - 1 && <div className="h-5 w-px bg-slate-200 mx-1.5" />}
            </div>
          )
        })}
      </div>

      {/* 2-Column Content Grid: Left (8 cols) + Right (4 cols) */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* LEFT — Policy tab content (8 cols) */}
        <div className="col-span-8 bg-white border border-slate-200/70 rounded-2xl p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between min-w-0">
          {activeTab === 'policy' ? (
            <>
              <div>
                <div className="flex items-start gap-2.5 mb-3">
                  <div className="w-8 h-8 rounded-xl bg-[#E6F0FF] flex items-center justify-center text-[#1565F9] shrink-0 mt-0.5">
                    <Database size={16} strokeWidth={2.2} />
                  </div>
                  <div>
                    <h2 className="text-[16px] font-bold text-slate-900 leading-tight">
                      Chính sách dữ liệu
                    </h2>
                    <p className="text-[12.5px] text-slate-500 mt-0.5">
                      Quy định thời hạn lưu trữ và nguyên tắc xử lý cho từng loại dữ liệu.
                    </p>
                  </div>
                </div>

                <div className="border border-slate-100 rounded-xl overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-[#F4F7FB] border-b border-slate-100">
                        <th className="px-3.5 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                          Loại dữ liệu
                        </th>
                        <th className="px-3 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                          Thời hạn
                        </th>
                        <th className="px-3 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                          Mốc tính
                        </th>
                        <th className="px-3.5 py-2.5 text-left text-[12px] font-semibold text-slate-600 whitespace-nowrap">
                          Trạng thái
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {DATA_POLICIES.map((policy) => {
                        const Icon = policy.icon
                        return (
                          <tr key={policy.name} className="hover:bg-slate-50/60 transition">
                            <td className="px-3.5 py-2.5">
                              <div className="flex items-center gap-3">
                                <div
                                  className={`w-9 h-9 rounded-xl ${policy.iconBg} flex items-center justify-center shrink-0`}
                                >
                                  <Icon size={18} />
                                </div>
                                <div>
                                  <p className="font-bold text-slate-900 text-[13px]">
                                    {policy.name}
                                  </p>
                                  <p className="text-[11.5px] text-slate-500 mt-0.5 leading-snug">
                                    {policy.desc}
                                  </p>
                                </div>
                              </div>
                            </td>
                            <td className="px-3 py-2.5 text-slate-800 font-medium text-[13px] whitespace-nowrap">
                              {policy.retention}
                            </td>
                            <td className="px-3 py-2.5 text-slate-700 text-[12.5px] leading-snug whitespace-nowrap">
                              {policy.milestone}
                            </td>
                            <td className="px-3.5 py-2.5 whitespace-nowrap">
                              <span
                                className={`inline-flex items-center gap-1.5 text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0 ${
                                  policy.statusColor === 'green'
                                    ? 'bg-[#E2F7EB] text-[#059669]'
                                    : 'bg-[#FEE2E2] text-[#DC2626]'
                                }`}
                              >
                                <span
                                  className={`w-2 h-2 rounded-full shrink-0 ${
                                    policy.statusColor === 'green'
                                      ? 'bg-[#10B981]'
                                      : 'bg-[#EF4444]'
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
                </div>
              </div>

              {/* Footer info callout */}
              <div className="mt-3 px-3.5 py-2.5 bg-[#EAF3FF] border border-blue-200/80 rounded-xl flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#1565F9] text-white flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5">
                  i
                </span>
                <div>
                  <p className="text-[12.5px] font-bold text-[#1565F9]">
                    Không đổi ngầm policy đang được pin trong phiên.
                  </p>
                  <p className="text-[11.5px] text-slate-600 mt-0.5">
                    Các thay đổi chỉ có hiệu lực khi kích hoạt phiên bản mới.
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-sm py-20">
              Đang hiển thị tab {activeTab}
            </div>
          )}
        </div>

        {/* RIGHT — Draft panel (4 cols) */}
        <div className="col-span-4 bg-white border border-slate-200/70 rounded-2xl p-4 px-5 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between min-w-0">
          <div className="space-y-3.5">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#E6F0FF] text-[#1565F9] flex items-center justify-center shrink-0">
                <FileText size={20} />
              </div>
              <div>
                <h2 className="text-[17px] font-extrabold text-slate-900">Bản nháp v2</h2>
                <p className="text-[12.5px] text-slate-500 mt-0.5">Chưa sẵn sàng để kích hoạt.</p>
              </div>
            </div>

            {/* Warning alert */}
            <div className="flex items-start gap-2.5 p-3 bg-[#FEF6E7] rounded-xl border border-amber-200/70">
              <AlertTriangle size={19} className="text-[#F59E0B] mt-0.5 shrink-0" />
              <div>
                <p className="text-[12.5px] font-bold text-[#B45309] leading-snug">
                  Chưa đủ chính sách bắt buộc để kích hoạt.
                </p>
                <p className="text-[11.5px] text-slate-600 mt-0.5">
                  Vui lòng hoàn thiện các mục còn thiếu.
                </p>
              </div>
            </div>

            {/* Metadata */}
            <div className="space-y-2.5 pt-0.5 text-[13px]">
              <div className="flex items-center">
                <div className="flex items-center gap-2.5 text-slate-600 w-36 shrink-0">
                  <div className="w-6.5 h-6.5 rounded-lg bg-[#E2F7EB] text-[#10B981] flex items-center justify-center">
                    <BarChart2 size={14} />
                  </div>
                  <span>Phiên bản</span>
                </div>
                <span className="font-bold text-slate-900">v2 (bản nháp)</span>
              </div>

              <div className="flex items-center">
                <div className="flex items-center gap-2.5 text-slate-600 w-36 shrink-0">
                  <div className="w-6.5 h-6.5 rounded-lg bg-[#E6F0FF] text-[#1565F9] flex items-center justify-center">
                    <Calendar size={14} />
                  </div>
                  <span>Ngày tạo</span>
                </div>
                <span className="font-bold text-slate-900">10/10/2026</span>
              </div>

              <div className="flex items-center">
                <div className="flex items-center gap-2.5 text-slate-600 w-36 shrink-0">
                  <div className="w-6.5 h-6.5 rounded-lg bg-[#F3E8FF] text-[#7C3AED] flex items-center justify-center">
                    <Layers size={14} />
                  </div>
                  <span>Hiệu lực</span>
                </div>
                <div className="flex items-center gap-2 font-bold text-[#D97706]">
                  <span className="w-2 h-2 rounded-full bg-[#F59E0B]" />
                  <span>Cần xác nhận</span>
                </div>
              </div>

              <div className="flex items-center">
                <div className="flex items-center gap-2.5 text-slate-600 w-36 shrink-0">
                  <div className="w-6.5 h-6.5 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
                    <User size={14} />
                  </div>
                  <span>Người phê duyệt</span>
                </div>
                <div className="flex items-center gap-2 font-bold text-[#DC2626]">
                  <span className="w-2 h-2 rounded-full bg-[#EF4444]" />
                  <span>Chưa duyệt</span>
                </div>
              </div>

              {/* Lý do thay đổi */}
              <div className="pt-0.5">
                <div className="flex items-center gap-2.5 text-slate-600 mb-1">
                  <div className="w-6.5 h-6.5 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
                    <FileText size={14} />
                  </div>
                  <span>Lý do thay đổi</span>
                </div>
                <p className="text-[12px] text-slate-600 leading-relaxed pl-9">
                  Cập nhật chính sách dữ liệu và bổ sung phạm vi xử lý cho các loại dữ liệu.
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-2.5 pt-3 border-t border-slate-100">
            <button className="w-full flex items-center justify-center gap-2 border border-[#1565F9] text-[#1565F9] hover:bg-blue-50 font-semibold text-[13px] py-2 rounded-xl transition cursor-pointer whitespace-nowrap">
              <Search size={14} />
              <span>Kiểm tra bản nháp</span>
            </button>
            <button
              disabled
              className="w-full flex items-center justify-center gap-2 bg-slate-200/80 text-slate-400 font-semibold text-[13px] py-2 rounded-xl cursor-not-allowed whitespace-nowrap"
            >
              <Play size={13} fill="currentColor" />
              <span>Kích hoạt</span>
            </button>
            <p className="text-[11.5px] text-center text-slate-500">
              Hoàn thiện các mục bắt buộc để kích hoạt.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
