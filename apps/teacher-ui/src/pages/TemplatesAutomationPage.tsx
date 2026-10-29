import { useState } from 'react'
import {
  Plus,
  Copy,
  Save,
  ChevronDown,
  ChevronRight,
  Lock,
  Pin,
  Check,
  Bell,
  Square,
  Pencil,
  Palette,
  Eraser,
  Undo2,
  MessageSquare,
  Play,
  Shield,
  Search,
  Users,
  Clock,
  MoreVertical,
} from 'lucide-react'
import { GreenCheckCircle } from '../components/Icons'
import artSprout from '../assets/art-sprout.png'
import artFlowers from '../assets/art-flowers.png'

export function TemplatesAutomationPage() {
  const [allowAiHint, setAllowAiHint] = useState(true)
  const [autoNotify, setAutoNotify] = useState(true)

  return (
    <div className="px-7 py-3 space-y-3 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[27px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Mẫu phiên & tự động hóa
          </h1>
          <p className="text-[14.5px] text-slate-600 mt-0.5">
            Cấu hình rõ ràng, giáo viên luôn điều phối
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button className="inline-flex items-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-4 py-2 rounded-xl transition cursor-pointer">
            <Plus size={15} />
            <span>Tạo mẫu</span>
          </button>

          <button className="inline-flex items-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-4 py-2 rounded-xl transition cursor-pointer">
            <Copy size={14} />
            <span>Nhân bản</span>
          </button>

          <button className="inline-flex items-center gap-1.5 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13px] px-4 py-2 rounded-xl shadow-xs transition cursor-pointer">
            <Save size={15} />
            <span>Lưu phiên bản</span>
          </button>
        </div>
      </div>

      {/* ── Main 3-Column Layout ── */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* ── LEFT COLUMN: Mẫu phiên (3 cols) ── */}
        <div className="col-span-3 bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <h2 className="text-[16px] font-extrabold text-[#0F172A] px-0.5">Mẫu phiên</h2>

          <div className="border-2 border-[#3B82F6] bg-[#EFF6FF]/70 rounded-2xl p-3 flex items-center justify-between gap-2 cursor-pointer">
            <div className="flex items-start gap-2.5 min-w-0">
              <img
                src={artSprout}
                alt="Khám phá khu vườn"
                className="w-12 h-14 rounded-xl object-cover border border-slate-200/60 flex-shrink-0"
              />
              <div className="min-w-0 space-y-0.5">
                <div className="text-[13px] font-extrabold text-[#0F172A] leading-snug">
                  Khám phá khu vườn • v1
                </div>
                <div className="text-[11px] text-slate-600 truncate">
                  Khu vườn của chúng mình
                </div>
                <div className="text-[11px] text-slate-500">
                  3 nhóm • Lá / Hoa / Nắng
                </div>
                <div className="pt-0.5">
                  <span className="inline-flex items-center gap-1 bg-[#DCFCE7] text-[#15803D] text-[10.5px] font-semibold px-2 py-0.5 rounded-full">
                    <GreenCheckCircle size={12} />
                    Đã kiểm tra
                  </span>
                </div>
              </div>
            </div>
            <ChevronRight size={14} className="text-[#1D63F2] flex-shrink-0" />
          </div>

          <div className="border border-slate-200/80 bg-white hover:bg-slate-50 rounded-2xl p-3 flex items-center justify-between gap-2 cursor-pointer transition">
            <div className="flex items-start gap-2.5 min-w-0">
              <img
                src={artFlowers}
                alt="Vẽ tự do có hỗ trợ"
                className="w-12 h-14 rounded-xl object-cover border border-slate-200/60 flex-shrink-0"
              />
              <div className="min-w-0 space-y-0.5">
                <div className="text-[13px] font-bold text-[#0F172A] truncate">
                  Vẽ tự do có hỗ trợ
                </div>
                <div className="text-[11px] text-slate-600 truncate">
                  Sáng tạo theo ý thích
                </div>
                <div className="text-[11px] text-slate-500">
                  3 nhóm • Lá / Hoa / Nắng
                </div>
              </div>
            </div>
            <ChevronRight size={14} className="text-slate-400 flex-shrink-0" />
          </div>
        </div>

        {/* ── CENTER COLUMN: Cấu hình mẫu (5 cols) ── */}
        <div className="col-span-5 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <h2 className="text-[16.5px] font-extrabold text-[#0F172A]">Cấu hình mẫu</h2>

          {/* Chủ đề */}
          <div className="flex items-center gap-3">
            <label className="text-[12.5px] font-semibold text-slate-700 w-16 flex-shrink-0">
              Chủ đề
            </label>
            <input
              type="text"
              readOnly
              value="Khu vườn của chúng mình"
              className="flex-1 px-3 py-1.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-[13px] font-semibold text-[#0F172A]"
            />
          </div>

          {/* Nhóm tuổi & Chế độ vẽ */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] font-semibold text-slate-700 mb-1">
                Nhóm tuổi
              </label>
              <button className="w-full flex items-center justify-between px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-[13px] font-semibold text-[#0F172A]">
                <span>6–8</span>
                <ChevronDown size={14} className="text-slate-500" />
              </button>
            </div>

            <div>
              <label className="block text-[12px] font-semibold text-slate-700 mb-1">
                Chế độ vẽ
              </label>
              <button className="w-full flex items-center justify-between px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-[13px] font-semibold text-[#0F172A]">
                <span>Theo nhóm</span>
                <ChevronDown size={14} className="text-slate-500" />
              </button>
            </div>
          </div>

          {/* Công cụ cho trẻ */}
          <div>
            <label className="block text-[12.5px] font-bold text-[#0F172A] mb-1.5">
              Công cụ cho trẻ
            </label>
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="inline-flex items-center gap-1.5 bg-[#EFF6FF] border border-[#3B82F6] text-[#1D63F2] font-semibold text-[12px] px-2.5 py-1 rounded-xl">
                <Pencil size={13} />
                <span>Bút</span>
              </span>
              <span className="inline-flex items-center gap-1.5 bg-white border border-slate-200 text-slate-700 font-medium text-[12px] px-2.5 py-1 rounded-xl">
                <Palette size={13} className="text-slate-500" />
                <span>Màu</span>
              </span>
              <span className="inline-flex items-center gap-1.5 bg-white border border-slate-200 text-slate-700 font-medium text-[12px] px-2.5 py-1 rounded-xl">
                <Eraser size={13} className="text-slate-500" />
                <span>Tẩy nét của mình</span>
              </span>
              <span className="inline-flex items-center gap-1.5 bg-white border border-slate-200 text-slate-700 font-medium text-[12px] px-2.5 py-1 rounded-xl">
                <Undo2 size={13} className="text-slate-500" />
                <span>Hoàn tác</span>
              </span>
            </div>
          </div>

          {/* Hỗ trợ AI */}
          <div className="space-y-1.5">
            <label className="block text-[12.5px] font-bold text-[#0F172A]">Hỗ trợ AI</label>
            <div className="bg-white border border-slate-200/80 rounded-xl px-3 py-2 flex items-center justify-between">
              <span className="flex items-center gap-2 text-[13px] font-semibold text-[#0F172A]">
                <MessageSquare size={14} className="text-slate-500" />
                <span>Trẻ có thể xin gợi ý</span>
              </span>
              <button
                onClick={() => setAllowAiHint(!allowAiHint)}
                className={`w-10 h-5.5 rounded-full p-0.5 transition cursor-pointer ${
                  allowAiHint ? 'bg-[#1D63F2]' : 'bg-slate-300'
                }`}
              >
                <div
                  className={`w-4.5 h-4.5 rounded-full bg-white shadow-xs transition-transform ${
                    allowAiHint ? 'translate-x-4.5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            <div className="bg-[#F1F5F9] border border-slate-200/80 rounded-xl px-3 py-2 flex items-center justify-between text-[12px]">
              <div className="flex items-center gap-2 font-medium text-slate-700">
                <Lock size={13.5} className="text-slate-500" />
                <span>Duyệt từng gợi ý: Bắt buộc</span>
              </div>
              <span className="inline-flex items-center gap-1 text-slate-500 text-[11px]">
                <span>Không thể thay đổi</span>
                <Lock size={11} />
              </span>
            </div>
          </div>

          {/* Video */}
          <div className="space-y-1.5">
            <label className="block text-[12.5px] font-bold text-[#0F172A]">Video</label>
            <div className="bg-[#F1F5F9] border border-slate-200/80 rounded-xl px-3 py-2 flex items-center justify-between text-[12px]">
              <div className="flex items-center gap-2 font-medium text-slate-700">
                <Play size={13.5} className="text-slate-500" />
                <span>Duyệt video trước khi chiếu: Bắt buộc</span>
              </div>
              <span className="inline-flex items-center gap-1 text-slate-500 text-[11px]">
                <span>Không thể thay đổi</span>
                <Lock size={11} />
              </span>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN: Chính sách hiệu lực (4 cols) ── */}
        <div className="col-span-4 bg-white rounded-2xl border border-slate-200/80 p-4 flex flex-col justify-between space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="space-y-2.5">
            <div>
              <h2 className="text-[16.5px] font-extrabold text-[#0F172A]">
                Chính sách hiệu lực
              </h2>
              <p className="text-[11.5px] text-slate-600 mt-0.5 leading-snug">
                Chính sách này áp dụng cho mẫu phiên và các phiên mới tạo từ mẫu.
              </p>
            </div>

            <div className="space-y-2 text-[12px]">
              <div className="bg-[#F8FAFC] border border-slate-100 rounded-xl p-2.5 flex items-center justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center flex-shrink-0">
                    <Shield size={15} />
                  </div>
                  <div>
                    <div className="font-bold text-[#0F172A]">Quyền theo tuổi & vùng</div>
                    <div className="text-[11px] text-slate-600 leading-snug">
                      Áp dụng giới hạn tính năng phù hợp với nhóm tuổi 6–8.
                    </div>
                  </div>
                </div>
                <ChevronRight size={14} className="text-slate-400 flex-shrink-0" />
              </div>

              <div className="bg-[#F8FAFC] border border-slate-100 rounded-xl p-2.5 flex items-center justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#FEF3C7] text-[#D97706] flex items-center justify-center flex-shrink-0">
                    <Search size={15} />
                  </div>
                  <div>
                    <div className="font-bold text-[#0F172A]">Kiểm tra phạm vi xử lý</div>
                    <div className="text-[11px] text-slate-600 leading-snug">
                      Chỉ xử lý nội dung trong phạm vi hoạt động lớp học.
                    </div>
                  </div>
                </div>
                <ChevronRight size={14} className="text-slate-400 flex-shrink-0" />
              </div>

              <div className="bg-[#F8FAFC] border border-slate-100 rounded-xl p-2.5 flex items-center justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#FFE4E6] text-[#E11D48] flex items-center justify-center flex-shrink-0">
                    <Lock size={15} />
                  </div>
                  <div>
                    <div className="font-bold text-[#0F172A]">
                      Không bỏ qua duyệt AI/video
                    </div>
                    <div className="text-[11px] text-slate-600 leading-snug">
                      Luôn giữ bước duyệt để đảm bảo an toàn cho trẻ.
                    </div>
                  </div>
                </div>
                <ChevronRight size={14} className="text-slate-400 flex-shrink-0" />
              </div>
            </div>

            <div className="bg-[#DCFCE7]/80 rounded-xl p-2.5 flex items-start gap-2.5">
              <Pin size={16} className="text-[#15803D] flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-[12.5px] font-bold text-[#15803D]">
                  Phiên đang dùng v1
                </div>
                <div className="text-[11px] text-slate-600">
                  Đây là mẫu hiện tại của lớp Mầm Xanh.
                </div>
              </div>
            </div>
          </div>

          <button className="w-full flex items-center justify-center gap-1.5 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13px] py-2 rounded-xl shadow-xs transition cursor-pointer">
            <Check size={15} />
            <span>Áp dụng cho phiên mới</span>
          </button>
        </div>
      </div>

      {/* ── Bottom 2-Column Section ── */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* Left: Tự động hóa (8 cols) */}
        <div className="col-span-8 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-[16px] font-extrabold text-[#0F172A]">Tự động hóa</h2>
              <p className="text-[12px] text-slate-600">
                Thiết lập phản hồi tự động theo trạng thái hoạt động của trẻ.
              </p>
            </div>
            <button className="inline-flex items-center gap-1 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[12px] px-3 py-1.5 rounded-xl transition cursor-pointer">
              <Plus size={14} />
              <span>Thêm quy tắc</span>
            </button>
          </div>

          <div className="bg-[#F8FAFC] border border-slate-200/70 rounded-xl p-2.5 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center">
                  <Users size={15} />
                </div>
                <div>
                  <div className="text-[11px] text-slate-500">Khi nào</div>
                  <div className="text-[13px] font-bold text-[#0F172A]">
                    Khi nhóm xin hỗ trợ
                  </div>
                </div>
              </div>

              <span className="text-slate-400 font-bold">→</span>

              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center">
                  <Bell size={15} />
                </div>
                <div>
                  <div className="text-[11px] text-slate-500">Thực hiện</div>
                  <div className="text-[13px] font-bold text-[#0F172A]">
                    Thông báo giáo viên
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="text-right">
                <div className="text-[11px] text-slate-600 font-medium mb-0.5">Bật</div>
                <button
                  onClick={() => setAutoNotify(!autoNotify)}
                  className={`w-10 h-5 rounded-full p-0.5 transition cursor-pointer ${
                    autoNotify ? 'bg-[#1D63F2]' : 'bg-slate-300'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white shadow-xs transition-transform ${
                      autoNotify ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
              <MoreVertical size={15} className="text-slate-400" />
            </div>
          </div>

          <div className="bg-[#EFF6FF] rounded-xl px-3 py-1.5 flex items-center gap-2 text-[12px] text-slate-700">
            <div className="w-4 h-4 rounded-full bg-[#1D63F2] text-white text-[9.5px] font-bold flex items-center justify-center">
              i
            </div>
            <span>Tự động hóa không tự đổi hoạt động của lớp.</span>
          </div>
        </div>

        {/* Right: Điều phối & lịch sử (4 cols) */}
        <div className="col-span-4 bg-white rounded-2xl border border-slate-200/80 p-4 flex flex-col justify-between space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-[16px] font-extrabold text-[#0F172A]">
                Điều phối & lịch sử
              </h2>
              <p className="text-[11.5px] text-slate-600 mt-0.5">
                Giáo viên có thể tắt tự động hóa khi cần thiết.
              </p>
            </div>

            <button className="inline-flex items-center justify-center gap-1.5 border border-red-300 bg-white hover:bg-red-50 text-red-600 font-semibold text-[11.5px] px-2.5 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
              <Square size={12} className="shrink-0" />
              <span>Tắt tự động hóa</span>
            </button>
          </div>

          <div className="bg-[#F8FAFC] border border-slate-200/70 rounded-xl p-2.5 flex items-center justify-between gap-2 text-[12px]">
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center flex-shrink-0 mt-0.5">
                <Clock size={13.5} />
              </div>
              <div>
                <div className="font-bold text-[#0F172A]">
                  Giáo viên điều chỉnh công cụ
                </div>
                <div className="text-[11px] text-slate-600">
                  giữ v1 cho phiên hiện hành
                </div>
              </div>
            </div>
            <div className="text-right text-[11px] text-slate-500 flex-shrink-0">
              <div>Hôm nay 09:24</div>
              <div>bởi Giáo viên</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
