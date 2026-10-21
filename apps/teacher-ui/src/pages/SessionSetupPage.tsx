import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText,
  Play,
  ChevronRight,
  ChevronDown,
  User,
  Users,
  Settings,
  Lock,
  Feather,
  Cloud,
  Lightbulb,
  Monitor,
  Heart,
  Palette,
  Wrench,
  Bot,
  List,
} from 'lucide-react'
import {
  LeafBadgeIcon,
  FlowerBadgeIcon,
  SunBadgeIcon,
  SproutBadgeIcon,
  GreenCheckCircle,
  BlueCheckBox,
} from '../components/Icons'
import artGardenWide from '../assets/art-garden-wide.png'

export function SessionSetupPage() {
  const navigate = useNavigate()
  const [topic, setTopic] = useState('Khu vườn của chúng mình')
  const [drawMode, setDrawMode] = useState<'individual' | 'group'>('group')

  return (
    <div className="px-7 py-4 space-y-3.5 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
              Thiết lập phiên học
            </h1>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[13px] font-semibold px-3.5 py-1 rounded-full whitespace-nowrap shrink-0">
              <span className="w-2 h-2 rounded-full bg-[#D97706] shrink-0" />
              <span>Bản nháp</span>
            </span>
          </div>
          <p className="text-[15.5px] text-slate-600 mt-1">
            Chuẩn bị theo nhu cầu của lớp
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2.5 rounded-xl text-[14px] transition cursor-pointer whitespace-nowrap shrink-0">
            <FileText size={17} className="shrink-0" />
            <span>Lưu nháp</span>
          </button>
          <button
            onClick={() => navigate('/session/lobby')}
            className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold px-5 py-2.5 rounded-xl text-[14px] shadow-xs transition cursor-pointer whitespace-nowrap shrink-0"
          >
            <Play size={17} className="shrink-0" />
            <span>Mở phòng chờ</span>
          </button>
        </div>
      </div>

      {/* ── 3-Step Stepper ── */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-2 grid grid-cols-12 items-center shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
        <div className="col-span-4 bg-[#EAF3FF] rounded-xl px-4 py-2.5 flex items-center gap-3.5">
          <div className="w-9 h-9 rounded-full bg-[#1D63F2] text-white font-bold text-[15px] flex items-center justify-center flex-shrink-0">
            1
          </div>
          <div>
            <div className="text-[14px] font-bold text-[#1D63F2]">Nội dung</div>
            <div className="text-[12.5px] text-slate-600">Chủ đề và hình thức</div>
          </div>
        </div>

        <div className="col-span-4 px-4 py-2.5 flex items-center justify-between">
          <ChevronRight size={18} className="text-slate-400 -ml-2 mr-2 flex-shrink-0" />
          <div className="flex items-center gap-3.5 flex-1">
            <div className="w-9 h-9 rounded-full bg-slate-200/80 text-slate-700 font-bold text-[15px] flex items-center justify-center flex-shrink-0">
              2
            </div>
            <div>
              <div className="text-[14px] font-bold text-slate-700">Nhóm & công cụ</div>
              <div className="text-[12.5px] text-slate-500">Chọn nhóm và công cụ</div>
            </div>
          </div>
          <ChevronRight size={18} className="text-slate-400 flex-shrink-0" />
        </div>

        <div className="col-span-4 px-4 py-2.5 flex items-center gap-3.5">
          <div className="w-9 h-9 rounded-full bg-slate-200/80 text-slate-700 font-bold text-[15px] flex items-center justify-center flex-shrink-0">
            3
          </div>
          <div>
            <div className="text-[14px] font-bold text-slate-700">Kiểm tra</div>
            <div className="text-[12.5px] text-slate-500">Xem lại trước khi mở</div>
          </div>
        </div>
      </div>

      {/* ── Main 2-Column Layout ── */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* ── LEFT COLUMN: Thông tin phiên học (7 cols) ── */}
        <div className="col-span-7 bg-white rounded-2xl border border-slate-200/80 p-5 space-y-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <h2 className="text-[18px] font-extrabold text-[#0F172A]">Thông tin phiên học</h2>

          {/* Chủ đề */}
          <div className="grid grid-cols-12 items-center gap-3">
            <label className="col-span-3 text-[14px] font-bold text-[#0F172A]">Chủ đề</label>
            <div className="col-span-9">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-[14px] text-[#0F172A] font-medium focus:outline-none focus:ring-2 focus:ring-[#1D63F2]"
              />
            </div>
          </div>

          {/* Lớp & Nhóm tuổi */}
          <div className="grid grid-cols-12 items-center gap-3">
            <label className="col-span-3 text-[14px] font-bold text-[#0F172A]">Lớp</label>
            <div className="col-span-4">
              <button className="w-full flex items-center justify-between px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-[14px] font-medium text-[#0F172A]">
                <span>Mầm Xanh</span>
                <ChevronDown size={16} className="text-slate-500" />
              </button>
            </div>
            <label className="col-span-2 text-[14px] font-bold text-[#0F172A] text-right pr-2">
              Nhóm tuổi
            </label>
            <div className="col-span-3">
              <button className="w-full flex items-center justify-between px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-[14px] font-medium text-[#0F172A]">
                <span>6–8</span>
                <ChevronDown size={16} className="text-slate-500" />
              </button>
            </div>
          </div>

          {/* Mẫu phiên */}
          <div className="grid grid-cols-12 items-center gap-3">
            <label className="col-span-3 text-[14px] font-bold text-[#0F172A]">Mẫu phiên</label>
            <div className="col-span-9">
              <button className="w-full flex items-center justify-between px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-[14px] font-medium text-[#0F172A]">
                <span>Khám phá khu vườn • v1</span>
                <ChevronDown size={16} className="text-slate-500" />
              </button>
            </div>
          </div>

          {/* Chế độ vẽ */}
          <div className="grid grid-cols-12 items-center gap-3 pt-0.5">
            <label className="col-span-3 text-[14px] font-bold text-[#0F172A]">Chế độ vẽ</label>
            <div className="col-span-9 grid grid-cols-2 gap-3">
              <div
                onClick={() => setDrawMode('individual')}
                className={`p-3 rounded-xl border flex items-center gap-3 cursor-pointer transition ${
                  drawMode === 'individual'
                    ? 'border-[#3B82F6] bg-[#F0F7FF]'
                    : 'border-slate-200 bg-[#F8FAFC]/60'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0 ${
                    drawMode === 'individual' ? 'border-[#1D63F2]' : 'border-slate-400'
                  }`}
                >
                  {drawMode === 'individual' && (
                    <div className="w-2 h-2 rounded-full bg-[#1D63F2]" />
                  )}
                </div>
                <User size={19} className="text-slate-600 flex-shrink-0" />
                <div>
                  <div className="text-[13.5px] font-bold text-[#0F172A]">Cá nhân</div>
                  <div className="text-[12px] text-slate-500">Mỗi trẻ vẽ trên trang riêng</div>
                </div>
              </div>

              <div
                onClick={() => setDrawMode('group')}
                className={`p-3 rounded-xl border flex items-center gap-3 cursor-pointer transition ${
                  drawMode === 'group'
                    ? 'border-[#3B82F6] bg-[#F0F7FF]'
                    : 'border-slate-200 bg-[#F8FAFC]/60'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full border-4 flex items-center justify-center flex-shrink-0 ${
                    drawMode === 'group' ? 'border-[#1D63F2] bg-white' : 'border-slate-400'
                  }`}
                />
                <Users size={19} className="text-[#1D63F2] flex-shrink-0" />
                <div>
                  <div className="text-[13.5px] font-bold text-[#1D63F2]">Cùng vẽ theo nhóm</div>
                  <div className="text-[12px] text-slate-600">
                    Các thành viên vẽ chung một trang
                  </div>
                </div>
              </div>
            </div>
          </div>

          <hr className="border-slate-100" />

          {/* Nhóm tham gia */}
          <div className="grid grid-cols-12 items-center gap-3">
            <label className="col-span-3 text-[14px] font-bold text-[#0F172A]">Nhóm tham gia</label>
            <div className="col-span-9 flex items-center justify-between gap-2">
              <div className="flex items-center flex-wrap gap-2">
                <span className="inline-flex items-center justify-center gap-2 bg-[#ECFDF5] text-[#065F46] font-semibold text-[13.5px] px-3.5 py-1.5 rounded-xl whitespace-nowrap shrink-0">
                  <LeafBadgeIcon size={17} /> <span>Lá</span>
                </span>
                <span className="inline-flex items-center justify-center gap-2 bg-[#FFF1F2] text-[#9F1239] font-semibold text-[13.5px] px-3.5 py-1.5 rounded-xl whitespace-nowrap shrink-0">
                  <FlowerBadgeIcon size={17} /> <span>Hoa</span>
                </span>
                <span className="inline-flex items-center justify-center gap-2 bg-[#FEFCE8] text-[#854D0E] font-semibold text-[13.5px] px-3.5 py-1.5 rounded-xl whitespace-nowrap shrink-0">
                  <SunBadgeIcon size={17} /> <span>Nắng</span>
                </span>
              </div>

              <button className="inline-flex items-center justify-center gap-1.5 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[13px] px-3.5 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                <Settings size={15} className="shrink-0" />
                <span>Chỉnh nhóm</span>
              </button>
            </div>
          </div>

          <hr className="border-slate-100" />

          {/* Công cụ vẽ */}
          <div className="grid grid-cols-12 items-center gap-3">
            <label className="col-span-2 text-[14px] font-bold text-[#0F172A]">Công cụ vẽ</label>
            <div className="col-span-10 flex flex-wrap items-center gap-2">
              {['Bút', 'Màu', 'Tẩy nét của mình', 'Hoàn tác của mình', 'Phóng to'].map((tool) => (
                <span
                  key={tool}
                  className="inline-flex items-center justify-center gap-1.5 bg-[#EFF6FF] text-[#1D63F2] font-semibold text-[12.5px] px-2.5 py-1.5 rounded-lg whitespace-nowrap shrink-0"
                >
                  <BlueCheckBox size={15} />
                  <span>{tool}</span>
                </span>
              ))}
            </div>
          </div>

          <hr className="border-slate-100" />

          {/* Hỗ trợ AI */}
          <div className="grid grid-cols-12 items-start gap-3">
            <label className="col-span-2 text-[14px] font-bold text-[#0F172A] pt-0.5">
              Hỗ trợ AI
            </label>
            <div className="col-span-10 space-y-1">
              <div className="flex items-center gap-2 text-[14px] font-medium text-[#0F172A]">
                <BlueCheckBox size={17} />
                <span>Cho phép xin gợi ý tham khảo</span>
              </div>
              <div className="flex items-center gap-1.5 text-[12.5px] text-slate-500 pl-6">
                <Lock size={13.5} className="text-slate-400" />
                <span>Giáo viên duyệt từng gợi ý trước khi trẻ xem</span>
              </div>
            </div>
          </div>

          <hr className="border-slate-100" />

          {/* Các hoạt động (tùy chọn) */}
          <div className="space-y-2.5">
            <div className="text-[14px] font-bold text-[#0F172A]">Các hoạt động (tùy chọn)</div>
            <div className="flex items-center justify-between gap-1.5">
              {/* Step 1 */}
              <div className="flex-1 bg-[#EFF6FF] border border-[#3B82F6] rounded-xl p-2 flex items-center gap-2">
                <Feather size={15} className="text-[#1D63F2] flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-[12px] font-bold text-[#1D63F2] truncate">Khám phá & vẽ</div>
                  <div className="text-[10.5px] text-slate-500 truncate">Tìm hiểu và sáng tạo</div>
                </div>
              </div>
              <span className="text-slate-400 text-xs">→</span>

              {/* Step 2 */}
              <div className="flex-1 bg-[#ECFDF5] border border-emerald-200/80 rounded-xl p-2 flex items-center gap-2">
                <Cloud size={15} className="text-emerald-600 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-[12px] font-bold text-[#0F172A] truncate">Chia sẻ</div>
                  <div className="text-[10.5px] text-slate-500 truncate">Giới thiệu tranh</div>
                </div>
              </div>
              <span className="text-slate-400 text-xs">→</span>

              {/* Step 3 */}
              <div className="flex-1 bg-[#FEFCE8] border border-amber-200/80 rounded-xl p-2 flex items-center gap-2">
                <Lightbulb size={15} className="text-amber-500 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-[12px] font-bold text-[#0F172A] truncate">Kiến thức</div>
                  <div className="text-[10.5px] text-slate-500 truncate">Mở rộng hiểu biết</div>
                </div>
              </div>
              <span className="text-slate-400 text-xs">→</span>

              {/* Step 4 */}
              <div className="flex-1 bg-[#FFF1F2] border border-rose-200/80 rounded-xl p-2 flex items-center gap-2">
                <Monitor size={15} className="text-rose-500 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-[12px] font-bold text-[#0F172A] truncate">Ngoài màn hình</div>
                  <div className="text-[10.5px] text-slate-500 truncate">Vận động, quan sát</div>
                </div>
              </div>
              <span className="text-slate-400 text-xs">→</span>

              {/* Step 5 */}
              <div className="flex-1 bg-[#F5F3FF] border border-purple-200/80 rounded-xl p-2 flex items-center gap-2">
                <Heart size={15} className="text-purple-600 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-[12px] font-bold text-[#0F172A] truncate">Cảm nhận</div>
                  <div className="text-[10.5px] text-slate-500 truncate">Nói về trải nghiệm</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN: Xem trước cấu hình (5 cols) ── */}
        <div className="col-span-5 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <h2 className="text-[18px] font-extrabold text-[#0F172A]">Xem trước cấu hình</h2>

          {/* Preview Box */}
          <div className="bg-[#F8FAFC] border border-slate-200/70 rounded-2xl p-3.5 space-y-2.5">
            <img
              src={artGardenWide}
              alt="Khu vườn của chúng mình"
              className="w-full h-[132px] object-cover rounded-xl border border-slate-200/60"
            />

            <div className="space-y-1.5 text-[12.5px] pt-0.5">
              <div className="grid grid-cols-12 items-center">
                <div className="col-span-4 flex items-center gap-2 text-slate-500">
                  <SproutBadgeIcon size={14} />
                  <span>Chủ đề</span>
                </div>
                <div className="col-span-8 font-medium text-[#0F172A]">{topic}</div>
              </div>

              <div className="grid grid-cols-12 items-center">
                <div className="col-span-4 flex items-center gap-2 text-slate-500">
                  <Users size={14} className="text-[#1D63F2]" />
                  <span>Lớp</span>
                </div>
                <div className="col-span-8 font-medium text-[#0F172A]">Mầm Xanh</div>
              </div>

              <div className="grid grid-cols-12 items-center">
                <div className="col-span-4 flex items-center gap-2 text-slate-500">
                  <Users size={14} className="text-slate-500" />
                  <span>Nhóm</span>
                </div>
                <div className="col-span-8 font-medium text-[#0F172A]">Lá • Hoa • Nắng</div>
              </div>

              <div className="grid grid-cols-12 items-center">
                <div className="col-span-4 flex items-center gap-2 text-slate-500">
                  <Palette size={14} className="text-slate-600" />
                  <span>Chế độ vẽ</span>
                </div>
                <div className="col-span-8 font-medium text-[#0F172A]">Cùng vẽ theo nhóm</div>
              </div>

              <div className="grid grid-cols-12 items-start">
                <div className="col-span-4 flex items-center gap-2 text-slate-500">
                  <Wrench size={14} className="text-slate-600" />
                  <span>Công cụ</span>
                </div>
                <div className="col-span-8 font-medium text-[#0F172A] leading-snug">
                  Bút, Màu, Tẩy nét của mình, Hoàn tác của mình, Phóng to
                </div>
              </div>

              <div className="grid grid-cols-12 items-start">
                <div className="col-span-4 flex items-center gap-2 text-slate-500">
                  <Bot size={14} className="text-slate-600" />
                  <span>Hỗ trợ AI</span>
                </div>
                <div className="col-span-8 font-medium text-[#0F172A] leading-snug">
                  Cho phép xin gợi ý tham khảo
                  <br />
                  <span className="text-slate-600">
                    Giáo viên duyệt từng gợi ý trước khi trẻ xem
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-12 items-center">
                <div className="col-span-4 flex items-center gap-2 text-slate-500">
                  <List size={14} className="text-slate-600" />
                  <span>Mẫu phiên</span>
                </div>
                <div className="col-span-8 font-medium text-[#0F172A]">
                  Khám phá khu vườn • v1
                </div>
              </div>
            </div>
          </div>

          {/* Kiểm tra trước khi mở */}
          <div className="bg-[#ECFDF5]/80 border border-emerald-200/80 rounded-2xl p-3.5 space-y-1.5">
            <h3 className="text-[14px] font-bold text-[#065F46] mb-0.5">
              Kiểm tra trước khi mở
            </h3>
            {[
              'Công cụ phù hợp tuổi',
              'Phạm vi xử lý đã kiểm tra',
              'Nhóm không trùng thành viên',
              'Mẫu phiên còn hợp lệ',
            ].map((item) => (
              <div key={item} className="flex items-center gap-2 text-[12.5px] text-[#065F46] font-medium">
                <GreenCheckCircle size={15} />
                <span>{item}</span>
              </div>
            ))}
          </div>

          {/* Bottom Info Alert */}
          <div className="bg-[#EFF6FF] border border-blue-200/80 rounded-2xl p-3.5 flex items-start gap-3">
            <div className="w-5 h-5 rounded-full bg-[#1D63F2] text-white font-bold text-[11px] flex items-center justify-center flex-shrink-0 mt-0.5">
              i
            </div>
            <div>
              <div className="text-[13px] font-bold text-[#1D63F2]">
                Kiểm tra thiết bị và tiếp nhận trẻ tại phòng chờ
              </div>
              <p className="text-[12px] text-slate-600 mt-0.5 leading-snug">
                Đảm bảo âm thanh, mạng và không gian học tập sẵn sàng trước khi mở phiên.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
