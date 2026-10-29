import { useNavigate } from 'react-router-dom'
import {
  ChevronDown,
  ChevronRight,
  FileText,
  Users,
  Pencil,
  Check,
  X,
  Sliders,
  RotateCw,
  AlertTriangle,
  Lock,
  MessageSquare,
  Shield,
  Monitor,
} from 'lucide-react'
import {
  GreenCheckCircle,
  LeafBadgeIcon,
} from '../components/Icons'
import sketchChildLeaf from '../assets/sketch-child-leaf.png'
import sketchAiLeaf from '../assets/sketch-ai-leaf.png'
import sketchMayUpdated from '../assets/sketch-may-updated.png'
import sketchAiStale from '../assets/sketch-ai-stale.png'
import avatarLa from '../assets/avatar-la.png'
import avatarHoa from '../assets/avatar-hoa.png'
import artSprout from '../assets/art-sprout.png'
import artFlowers from '../assets/art-flowers.png'
import artSun from '../assets/art-sun.png'

interface Props {
  stale?: boolean
}

export function AiSuggestionReviewPage({ stale = false }: Props) {
  const navigate = useNavigate()

  if (stale) {
    // ── T07b — Gợi ý không còn hợp lệ ──
    return (
      <div className="px-7 py-4 space-y-3.5 max-w-[1400px] mx-auto">
        {/* Header */}
        <div>
          <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Duyệt gợi ý AI
          </h1>
          <p className="text-[14.5px] text-slate-600 mt-1">
            Xem và duyệt các gợi ý học tập do AI tạo ra cho trẻ.
          </p>
        </div>

        {/* Main 2-Column Layout */}
        <div className="grid grid-cols-12 gap-5 items-start">
          {/* Left List (4 cols) */}
          <div className="col-span-4 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-[16.5px] font-extrabold text-[#0F172A]">
                Danh sách yêu cầu
              </h2>
              <span className="w-6 h-6 rounded-full bg-[#EFF6FF] text-[#1D63F2] text-[12.5px] font-bold flex items-center justify-center">
                3
              </span>
            </div>

            {/* Item 1 - Selected */}
            <div className="border-2 border-[#3B82F6] bg-[#F5F9FF] rounded-2xl p-3 flex items-center gap-3 cursor-pointer">
              <img
                src={artSprout}
                alt="Mây"
                className="w-14 h-14 rounded-xl object-cover border border-slate-200/60 flex-shrink-0"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-[14px] font-bold text-[#0F172A] truncate">
                    Mây • Nhóm Lá
                  </span>
                  <span className="inline-flex items-center justify-center gap-1 bg-[#FEF3C7] text-[#B45309] text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#D97706] shrink-0" />
                    <span>Cần cập nhật</span>
                  </span>
                </div>
                <div className="flex items-center justify-between text-[12px] text-slate-600 mt-1">
                  <span className="truncate">Khu vườn của chúng mình</span>
                  <ChevronRight size={14} className="text-slate-400 shrink-0" />
                </div>
                <div className="text-[11.5px] text-slate-500 mt-0.5">2 phút trước</div>
              </div>
            </div>

            {/* Item 2 */}
            <div className="border border-slate-200/80 bg-white hover:bg-slate-50 rounded-2xl p-3 flex items-center gap-3 cursor-pointer transition">
              <img
                src={artFlowers}
                alt="Hoa"
                className="w-14 h-14 rounded-xl object-cover border border-slate-200/60 shrink-0"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-[14px] font-bold text-[#0F172A] truncate">
                    Hoa • Nhóm Hoa
                  </span>
                  <span className="inline-flex items-center justify-center gap-1 bg-[#EFF6FF] text-[#1D63F2] text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1D63F2] shrink-0" />
                    <span>Đang chờ</span>
                  </span>
                </div>
                <div className="flex items-center justify-between text-[12px] text-slate-600 mt-1">
                  <span className="truncate">Khu vườn của chúng mình</span>
                  <ChevronRight size={14} className="text-slate-400 shrink-0" />
                </div>
                <div className="text-[11.5px] text-slate-500 mt-0.5">8 phút trước</div>
              </div>
            </div>

            {/* Item 3 */}
            <div className="border border-slate-200/80 bg-white hover:bg-slate-50 rounded-2xl p-3 flex items-center gap-3 cursor-pointer transition">
              <img
                src={artSun}
                alt="Nắng"
                className="w-14 h-14 rounded-xl object-cover border border-slate-200/60 shrink-0"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-[14px] font-bold text-[#0F172A] truncate">
                    Nắng • Nhóm Nắng
                  </span>
                  <span className="inline-flex items-center justify-center gap-1 bg-[#EFF6FF] text-[#1D63F2] text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1D63F2] shrink-0" />
                    <span>Đang chờ</span>
                  </span>
                </div>
                <div className="flex items-center justify-between text-[12px] text-slate-600 mt-1">
                  <span className="truncate">Khu vườn của chúng mình</span>
                  <ChevronRight size={14} className="text-slate-400 flex-shrink-0" />
                </div>
                <div className="text-[11.5px] text-slate-500 mt-0.5">15 phút trước</div>
              </div>
            </div>
          </div>

          {/* Right Detail (8 cols) */}
          <div className="col-span-8 space-y-3.5">
            {/* Warning Banner */}
            <div className="bg-[#FFFBEB] border border-amber-300/90 rounded-2xl p-4 flex items-center gap-3.5">
              <div className="w-11 h-11 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706] flex-shrink-0">
                <AlertTriangle size={24} />
              </div>
              <div>
                <h3 className="text-[16.5px] font-extrabold text-[#B45309]">
                  Gợi ý không còn khớp với tranh hiện tại
                </h3>
                <p className="text-[13.5px] text-slate-700 mt-0.5">
                  Trẻ đã thêm nét mới sau khi yêu cầu gợi ý. Hãy tạo lại và duyệt phiên bản mới.
                </p>
              </div>
            </div>

            {/* Detail Card */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
              <div>
                <h3 className="text-[16px] font-extrabold text-[#0F172A] mb-2.5">
                  Thông tin yêu cầu
                </h3>
                <div className="grid grid-cols-4 gap-3 text-[13px]">
                  <div className="flex items-center gap-2.5">
                    <LeafBadgeIcon size={34} />
                    <div>
                      <div className="text-slate-500 text-[11.5px]">Nhóm</div>
                      <div className="font-bold text-[#0F172A]">Nhóm Lá</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center flex-shrink-0">
                      <MessageSquare size={16} />
                    </div>
                    <div>
                      <div className="text-slate-500 text-[11.5px]">Mức hỗ trợ</div>
                      <div className="font-bold text-[#0F172A]">Gợi mở</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-[#FEF3C7] text-[#D97706] flex items-center justify-center flex-shrink-0">
                      <AlertTriangle size={16} />
                    </div>
                    <div>
                      <div className="text-slate-500 text-[11.5px]">Trạng thái</div>
                      <div className="font-bold text-[#B45309]">Cần cập nhật</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center flex-shrink-0">
                      <FileText size={16} />
                    </div>
                    <div>
                      <div className="text-slate-500 text-[11.5px]">Phiên bản gợi ý</div>
                      <div className="font-bold text-[#0F172A]">2</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Side-by-side comparison */}
              <div className="grid grid-cols-2 gap-4">
                <div className="border border-slate-200/80 rounded-2xl p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <Monitor size={15} className="text-[#16A34A]" />
                      <span className="text-[13.5px] font-bold text-[#0F172A]">
                        Tranh hiện tại của Mây
                      </span>
                    </div>
                    <span className="bg-[#DCFCE7] text-[#15803D] text-[11px] font-semibold px-2.5 py-0.5 rounded-full">
                      Đã thêm nét mới
                    </span>
                  </div>
                  <div className="rounded-xl overflow-hidden border border-slate-100 h-[195px] bg-white">
                    <img
                      src={sketchMayUpdated}
                      alt="Tranh hiện tại của Mây"
                      className="w-full h-full object-cover"
                    />
                  </div>
                </div>

                <div className="border border-slate-200/80 rounded-2xl p-3 space-y-2 bg-slate-50/40">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <FileText size={15} className="text-red-500" />
                      <span className="text-[13.5px] font-bold text-[#0F172A]">
                        Gợi ý cũ • Không phát cho trẻ
                      </span>
                    </div>
                    <span className="bg-[#FFE4E6] text-[#E11D48] text-[11px] font-semibold px-2.5 py-0.5 rounded-full">
                      Phiên bản 2
                    </span>
                  </div>
                  <div className="rounded-xl overflow-hidden border border-slate-200/80 h-[195px] bg-white relative">
                    <img
                      src={sketchAiStale}
                      alt="Gợi ý cũ"
                      className="w-full h-full object-cover"
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-1 space-y-2">
                <div className="grid grid-cols-3 gap-3">
                  <button
                    disabled
                    className="inline-flex items-center justify-center gap-2 bg-slate-200/90 text-slate-500 font-semibold text-[13.5px] py-2.5 rounded-xl cursor-not-allowed"
                  >
                    <Lock size={15} />
                    <span>Duyệt phiên bản này</span>
                  </button>

                  <button
                    onClick={() => navigate('/ai-review')}
                    className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] py-2.5 rounded-xl shadow-xs transition cursor-pointer"
                  >
                    <RotateCw size={15} />
                    <span>Tạo lại gợi ý</span>
                  </button>

                  <button className="border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13.5px] py-2.5 rounded-xl transition cursor-pointer">
                    Đóng yêu cầu
                  </button>
                </div>

                <div className="flex items-center gap-1.5 text-[12px] text-slate-600">
                  <span className="w-4 h-4 rounded-full border border-slate-400 text-slate-600 text-[10px] font-bold flex items-center justify-center">
                    i
                  </span>
                  <span>Mỗi gợi ý mới cần được giáo viên duyệt.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── T07 — Duyệt từng gợi ý AI (Hợp lệ) ──
  return (
    <div className="px-7 py-4 space-y-3.5 max-w-[1400px] mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
          Duyệt từng gợi ý AI
        </h1>
        <p className="text-[15px] text-slate-600 mt-1">
          Gợi ý chỉ đến trẻ sau quyết định của giáo viên
        </p>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-2.5">
        <button className="flex items-center justify-between gap-6 px-3.5 py-2 bg-white border border-slate-200 rounded-xl text-[13px] font-medium text-slate-700">
          <span className="flex items-center gap-2">
            <Users size={15} className="text-slate-500" />
            <span>Tất cả nhóm</span>
          </span>
          <ChevronDown size={15} className="text-[#1D63F2]" />
        </button>

        <button className="border border-[#3B82F6] bg-[#EFF6FF] text-[#1D63F2] font-semibold text-[13px] px-4 py-2 rounded-xl">
          Chờ duyệt (2)
        </button>
        <button className="border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 font-medium text-[13px] px-4 py-2 rounded-xl">
          Đã duyệt
        </button>
        <button className="border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 font-medium text-[13px] px-4 py-2 rounded-xl">
          Đã từ chối
        </button>
      </div>

      {/* Main 2-Column Layout */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* Left List (4 cols) */}
        <div className="col-span-4 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <h2 className="text-[16.5px] font-extrabold text-[#0F172A] px-1">
            Danh sách gợi ý (2)
          </h2>

          {/* Item 1 - Selected */}
          <div className="border-2 border-[#3B82F6] bg-[#EFF6FF]/70 rounded-2xl p-3.5 flex items-center gap-3 cursor-pointer">
            <img
              src={avatarLa}
              alt="Mây"
              className="w-11 h-11 rounded-full object-cover flex-shrink-0"
            />
            <div className="flex-1 min-w-0">
              {/* metadata & actions in T07 */}
              <div className="flex items-center justify-between gap-1">
                <span className="text-[14px] font-bold text-[#0F172A] truncate">Mây • Nhóm Lá</span>
                <span className="inline-flex items-center justify-center gap-1 bg-[#FEF3C7] text-[#B45309] text-[11px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D97706] shrink-0" />
                  <span>Chờ duyệt</span>
                </span>
              </div>
              <div className="text-[13px] text-slate-700 mt-0.5">Muốn vẽ chiếc lá</div>
              <div className="text-[11.5px] text-slate-500 mt-0.5">2 phút trước</div>
            </div>
          </div>

          {/* Item 2 */}
          <div className="border border-slate-200/80 bg-white hover:bg-slate-50 rounded-2xl p-3.5 flex items-center gap-3 cursor-pointer transition">
            <img
              src={avatarHoa}
              alt="Hoa"
              className="w-11 h-11 rounded-full object-cover shrink-0"
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-1">
                <span className="text-[14px] font-bold text-[#0F172A] truncate">Hoa • Nhóm Hoa</span>
                <span className="inline-flex items-center justify-center gap-1 bg-[#FEF3C7] text-[#B45309] text-[11px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D97706] shrink-0" />
                  <span>Chờ duyệt</span>
                </span>
              </div>
              <div className="text-[13px] text-slate-700 mt-0.5">Cách vẽ cánh hoa</div>
              <div className="text-[11.5px] text-slate-500 mt-0.5">Vừa gửi</div>
            </div>
          </div>
        </div>

        {/* Right Detail (8 cols) */}
        <div className="col-span-8 bg-white rounded-2xl border border-slate-200/80 p-5 space-y-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="flex items-center gap-3.5">
            <img
              src={avatarLa}
              alt="Gợi ý cho Mây"
              className="w-12 h-12 rounded-full object-cover shrink-0"
            />
            <div className="space-y-1.5">
              <h2 className="text-[19px] font-extrabold text-[#0F172A]">Gợi ý cho Mây</h2>
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                  <FileText size={13} className="text-[#16A34A] shrink-0" />
                  <span>Ảnh gốc v3 • Gợi ý v1</span>
                </span>
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                  <Users size={13} className="text-slate-500 shrink-0" />
                  <span>Mây • phiên hiện tại</span>
                </span>
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                  <Pencil size={13} className="text-slate-600 shrink-0" />
                  <span>Nét phác tham khảo</span>
                </span>
              </div>
            </div>
          </div>

          {/* Side-by-side boxes */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#F8FAFC] border border-slate-200/80 rounded-2xl p-3.5 space-y-2">
              <div className="text-[14px] font-bold text-[#0F172A]">Nét vẽ của trẻ</div>
              <div className="bg-white rounded-xl border border-slate-200/60 h-[215px] flex items-center justify-center p-3">
                <img
                  src={sketchChildLeaf}
                  alt="Nét vẽ của trẻ"
                  className="max-h-full max-w-full object-contain"
                />
              </div>
            </div>

            <div className="bg-[#F8FAFC] border border-slate-200/80 rounded-2xl p-3.5 space-y-2">
              <div className="text-[14px] font-bold text-[#0F172A]">Gợi ý riêng</div>
              <div className="bg-white rounded-xl border border-slate-200/60 h-[215px] flex items-center justify-center p-3">
                <img
                  src={sketchAiLeaf}
                  alt="Gợi ý riêng"
                  className="max-h-full max-w-full object-contain"
                />
              </div>
            </div>
          </div>

          {/* Metadata Box */}
          <div className="bg-[#F8FAFC] border border-slate-200/70 rounded-2xl p-3.5 flex items-center gap-4">
            <div className="flex-[1.3] flex items-center justify-between gap-2 border-r border-slate-200 pr-4">
              <div className="flex items-start gap-2.5">
                <MessageSquare size={17} className="text-slate-500 mt-0.5 shrink-0" />
                <div>
                  <div className="text-[12px] text-slate-500 whitespace-nowrap">Trẻ muốn vẽ</div>
                  <div className="text-[15px] font-extrabold text-[#0F172A] whitespace-nowrap">chiếc lá</div>
                </div>
              </div>
              <button className="inline-flex items-center justify-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[12px] px-3 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                <Pencil size={12.5} className="shrink-0" />
                <span>Chỉnh ý nghĩa</span>
              </button>
            </div>

            <div className="flex-1 flex items-start gap-2.5 border-r border-slate-200 pr-4">
              <Shield size={18} className="text-[#16A34A] mt-0.5 shrink-0" />
              <div>
                <div className="text-[12px] text-slate-500 mb-1 whitespace-nowrap">Kiểm tra an toàn</div>
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0">
                  <GreenCheckCircle size={13} />
                  <span>Đã kiểm tra</span>
                </span>
              </div>
            </div>

            <div className="flex-1 flex items-start gap-2.5">
              <FileText size={18} className="text-[#1D63F2] mt-0.5 shrink-0" />
              <div>
                <div className="text-[12px] text-slate-500 mb-1 whitespace-nowrap">Phiên bản hiện hành</div>
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0">
                  <GreenCheckCircle size={13} />
                  <span>Còn hợp lệ</span>
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-2.5">
            <div className="flex items-center flex-wrap gap-2.5">
              <button className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] px-5 py-2.5 rounded-xl shadow-xs transition cursor-pointer whitespace-nowrap shrink-0">
                <Check size={16} className="shrink-0" />
                <span>Duyệt gợi ý này</span>
              </button>

              <button className="inline-flex items-center justify-center gap-2 border border-red-300 bg-white hover:bg-red-50 text-red-600 font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                <X size={16} className="shrink-0" />
                <span>Từ chối</span>
              </button>

              <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                <Sliders size={15} className="shrink-0" />
                <span>Điều chỉnh mức hỗ trợ</span>
              </button>

              <button
                onClick={() => navigate('/ai-review/stale')}
                className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
              >
                <RotateCw size={15} className="shrink-0" />
                <span>Yêu cầu tạo lại</span>
              </button>
            </div>

            <div className="flex items-center gap-1.5 text-[12px] text-slate-500">
              <span className="w-4 h-4 rounded-full border border-slate-400 text-slate-500 text-[10px] font-bold flex items-center justify-center">
                i
              </span>
              <span>Chỉnh sửa tạo phiên bản mới và cần duyệt lại.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
