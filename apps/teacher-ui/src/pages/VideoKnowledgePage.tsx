import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Play,
  Volume2,
  Maximize2,
  FileText,
  BookOpen,
  Pencil,
  Ban,
  Check,
  Clock,
  Users,
  AlertTriangle,
  ChevronRight,
  ChevronLeft,
  FastForward,
  Square,
  RotateCw,
  Shield,
  BarChart2,
} from 'lucide-react'
import {
  GreenCheckCircle,
  BlueCheckBox,
  LeafBadgeIcon,
  FlowerBadgeIcon,
  SunBadgeIcon,
} from '../components/Icons'
import videoPreview from '../assets/video-preview.png'
import videoClapper from '../assets/video-clapper.png'
import scriptStep1 from '../assets/script-step1.png'
import scriptStep2 from '../assets/script-step2.png'
import scriptStep3 from '../assets/script-step3.png'
import artSprout from '../assets/art-sprout.png'
import artFlowers from '../assets/art-flowers.png'
import artSun from '../assets/art-sun.png'

interface Props {
  mode?: 'review' | 'generating' | 'error'
}

export function VideoKnowledgePage({ mode = 'review' }: Props) {
  const navigate = useNavigate()
  const [checked1, setChecked1] = useState(true)
  const [checked2, setChecked2] = useState(true)

  // ── T09b — Đang tạo video ──
  if (mode === 'generating') {
    return (
      <div className="px-7 py-3.5 space-y-3 max-w-[1400px] mx-auto">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
              Kiến thức & video
            </h1>
            <div className="text-[19px] font-extrabold text-[#0F172A] mt-0.5">
              Khu vườn của chúng mình
            </div>
          </div>

          <button
            onClick={() => navigate('/session/orchestrate')}
            className="inline-flex items-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] text-[13.5px] font-semibold px-4 py-2 rounded-xl transition cursor-pointer"
          >
            <ChevronLeft size={16} />
            <span>Về điều phối lớp</span>
          </button>
        </div>

        {/* Main 2-Column Layout */}
        <div className="grid grid-cols-12 gap-4 items-stretch">
          {/* Left Card (7 cols) */}
          <div className="col-span-7 bg-white rounded-2xl border border-slate-200/80 p-5 flex flex-col items-center justify-between shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <img
              src={videoClapper}
              alt="Đang tạo video"
              className="w-[215px] h-auto object-contain mt-1"
            />

            <div className="text-center space-y-1 my-2">
              <h2 className="text-[23px] font-extrabold text-[#0F172A]">Đang tạo video</h2>
              <p className="text-[13.5px] text-slate-600">
                Nội dung đang được chuẩn bị cho lớp. Vui lòng chờ.
              </p>
            </div>

            {/* 3-Step Horizontal Stepper */}
            <div className="w-full max-w-[560px] py-2">
              <div className="flex items-center justify-between relative px-4">
                <div className="absolute left-16 right-16 top-3.5 h-0.5 bg-slate-200 -z-0" />
                <div className="absolute left-16 w-[42%] top-3.5 h-0.5 bg-[#3B82F6] -z-0" />

                <div className="relative z-10 flex flex-col items-center text-center">
                  <GreenCheckCircle size={24} />
                  <span className="text-[12px] text-slate-700 font-medium mt-1.5 leading-tight whitespace-nowrap">
                    Kịch bản đã xác nhận
                  </span>
                </div>

                <div className="relative z-10 flex flex-col items-center text-center">
                  <div className="w-6 h-6 rounded-full bg-[#DBEAFE] flex items-center justify-center">
                    <div className="w-3.5 h-3.5 rounded-full bg-[#1D63F2]" />
                  </div>
                  <span className="text-[12px] text-[#0F172A] font-bold mt-1.5 leading-tight whitespace-nowrap">
                    Đang tạo nội dung
                  </span>
                </div>

                <div className="relative z-10 flex flex-col items-center text-center">
                  <div className="w-6 h-6 rounded-full bg-slate-200" />
                  <span className="text-[12px] text-slate-500 font-medium mt-1.5 leading-tight whitespace-nowrap">
                    Chờ kiểm tra và duyệt
                  </span>
                </div>
              </div>
            </div>

            {/* 3 Inline Stats */}
            <div className="w-full pt-3 border-t border-slate-100 flex items-center justify-around text-[13px] text-slate-600">
              <div className="flex items-center gap-2">
                <Clock size={16} className="text-slate-500" />
                <span>
                  Đã chờ: <strong className="text-[#0F172A]">1 phút</strong>
                </span>
              </div>
              <div className="h-4 w-px bg-slate-200" />
              <div className="flex items-center gap-2">
                <Users size={16} className="text-slate-500" />
                <span>
                  Phạm vi: <strong className="text-[#0F172A]">Cả lớp</strong>
                </span>
              </div>
              <div className="h-4 w-px bg-slate-200" />
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-slate-500" />
                <span>
                  Phiên bản kịch bản: <strong className="text-[#0F172A]">3</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Right Card: Kịch bản đang dùng (5 cols) */}
          <div className="col-span-5 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-[17px] font-extrabold text-[#0F172A]">Kịch bản đang dùng</h2>
              <span className="bg-[#EFF6FF] text-[#1D63F2] font-semibold text-[11.5px] px-2.5 py-1 rounded-lg inline-flex items-center gap-1.5">
                <BookOpen size={13} />
                <span>Tài liệu lớp: Vòng đời cây đậu</span>
              </span>
            </div>

            <div className="space-y-2.5">
              {[
                {
                  num: 1,
                  numBg: 'bg-[#EFF6FF] text-[#1D63F2]',
                  img: scriptStep1,
                  title: 'Hạt nảy mầm',
                  desc: 'Quan sát hạt đậu và quá trình nảy mầm thành cây con.',
                },
                {
                  num: 2,
                  numBg: 'bg-[#FEF3C7] text-[#D97706]',
                  img: scriptStep2,
                  title: 'Cây lớn lên',
                  desc: 'Cây đậu phát triển lá, thân và cần ánh sáng, nước, đất.',
                },
                {
                  num: 3,
                  numBg: 'bg-[#DCFCE7] text-[#15803D]',
                  img: scriptStep3,
                  title: 'Cây ra hoa, kết quả',
                  desc: 'Cây đậu ra hoa, kết quả và tạo hạt để tiếp tục vòng đời.',
                },
              ].map((step) => (
                <div
                  key={step.num}
                  className="bg-white border border-slate-200/80 rounded-2xl p-3 flex items-center gap-3"
                >
                  <span
                    className={`w-7 h-7 rounded-full ${step.numBg} font-bold text-[13px] flex items-center justify-center flex-shrink-0 self-start`}
                  >
                    {step.num}
                  </span>
                  <img
                    src={step.img}
                    alt={step.title}
                    className="w-12 h-14 object-contain flex-shrink-0"
                  />
                  <div>
                    <div className="text-[14.5px] font-bold text-[#0F172A]">{step.title}</div>
                    <p className="text-[12px] text-slate-600 mt-0.5 leading-snug">
                      {step.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Card: Lớp học đang chờ */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="flex items-baseline gap-3">
            <h3 className="text-[16.5px] font-extrabold text-[#0F172A]">Lớp học đang chờ</h3>
            <span className="text-[12.5px] text-slate-500">
              Các nhóm sẽ được phát video sau khi giáo viên duyệt.
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[
              { name: 'Nhóm Lá', thumb: artSprout },
              { name: 'Nhóm Hoa', thumb: artFlowers },
              { name: 'Nhóm Nắng', thumb: artSun },
            ].map((g) => (
              <div
                key={g.name}
                className="bg-white border border-slate-200/80 rounded-xl p-2.5 flex items-center gap-3"
              >
                <img
                  src={g.thumb}
                  alt={g.name}
                  className="w-14 h-14 rounded-lg object-cover border border-slate-100 flex-shrink-0"
                />
                <div className="space-y-1.5">
                  <div className="font-extrabold text-[14.5px] text-[#0F172A]">{g.name}</div>
                  <span className="inline-flex items-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[12px] font-semibold px-3 py-0.5 rounded-full">
                    <Clock size={12.5} />
                    Chờ video
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Blue Banner */}
        <div className="bg-[#EFF6FF] border border-blue-200/70 rounded-xl px-4 py-2.5 flex items-center gap-2.5 text-[13px] text-[#1D63F2] font-medium">
          <div className="w-4 h-4 rounded-full bg-[#1D63F2] text-white text-[10px] font-bold flex items-center justify-center">
            i
          </div>
          <span>
            <strong>Chưa phát nội dung cho trẻ.</strong> Video sẽ được duyệt trước khi trình chiếu.
          </span>
        </div>
      </div>
    )
  }

  // ── T09c — Lỗi video: giáo viên quyết định ──
  if (mode === 'error') {
    return (
      <div className="px-7 py-3.5 space-y-3 max-w-[1400px] mx-auto">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
              Kiến thức & video
            </h1>
            <div className="text-[19px] font-extrabold text-[#0F172A] mt-0.5">
              Khu vườn của chúng mình
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => navigate('/session/orchestrate')}
              className="inline-flex items-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] text-[13px] font-semibold px-3.5 py-2 rounded-xl transition cursor-pointer"
            >
              <span>← Quay lại phiên học</span>
            </button>
            <button className="inline-flex items-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] text-[13px] font-semibold px-3.5 py-2 rounded-xl transition cursor-pointer">
              <FileText size={14} />
              <span>Xem kế hoạch</span>
            </button>
          </div>
        </div>

        {/* Warning Banner */}
        <div className="bg-[#FFFBEB] border border-amber-300/90 rounded-2xl p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706] flex-shrink-0">
              <AlertTriangle size={24} />
            </div>
            <div>
              <h3 className="text-[18px] font-extrabold text-[#0F172A]">
                Chưa tạo được video
              </h3>
              <p className="text-[13.5px] text-slate-700 mt-0.5">
                Các lần thử tự động đã kết thúc. Giáo viên chọn bước tiếp theo.
              </p>
            </div>
          </div>

          <span className="inline-flex items-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[13px] font-semibold px-3.5 py-1.5 rounded-full flex-shrink-0">
            <span className="w-4 h-4 rounded-full bg-[#D97706] text-white text-[10px] font-bold flex items-center justify-center">
              !
            </span>
            Cần giáo viên quyết định
          </span>
        </div>

        {/* Section 1: Kết quả vẫn được giữ */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="flex items-center justify-between">
            <h2 className="text-[17.5px] font-extrabold text-[#0F172A]">
              Kết quả vẫn được giữ
            </h2>
            <div className="flex items-center gap-2 bg-[#F8FAFC] border border-slate-200/70 rounded-xl px-3 py-1">
              <FileText size={14} className="text-[#1D63F2]" />
              <span className="text-[12.5px] font-medium text-slate-700">
                1 bản nháp đang chờ đồng bộ
              </span>
              <button className="inline-flex items-center gap-0.5 border border-[#3B82F6] bg-white text-[#1D63F2] text-[12px] font-semibold px-2.5 py-1 rounded-lg cursor-pointer ml-1">
                <span>Xem bản nháp</span>
                <ChevronRight size={13} />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {/* Box 1 */}
            <div className="bg-white border border-slate-200/80 rounded-2xl p-3.5 flex items-center gap-3.5">
              <img
                src={artSprout}
                alt="Tranh đã được lưu"
                className="w-20 h-24 rounded-xl object-cover border border-slate-100 flex-shrink-0"
              />
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-[14px] font-bold text-[#0F172A]">
                  <GreenCheckCircle size={17} />
                  <span>Tranh đã được lưu</span>
                </div>
                <div>
                  <div className="text-[11.5px] text-slate-500">Tên tranh</div>
                  <div className="text-[13px] font-bold text-[#0F172A]">
                    Khu vườn của chúng mình
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-1 pt-0.5">
                  <span className="inline-flex items-center gap-1 bg-[#F1F5F9] text-slate-700 text-[11px] font-medium px-2 py-0.5 rounded-full">
                    <LeafBadgeIcon size={13} /> Cây
                  </span>
                  <span className="inline-flex items-center gap-1 bg-[#F1F5F9] text-slate-700 text-[11px] font-medium px-2 py-0.5 rounded-full">
                    <FlowerBadgeIcon size={13} /> Hoa
                  </span>
                  <span className="inline-flex items-center gap-1 bg-[#F1F5F9] text-slate-700 text-[11px] font-medium px-2 py-0.5 rounded-full">
                    <SunBadgeIcon size={13} /> Mặt trời
                  </span>
                </div>
              </div>
            </div>

            {/* Box 2 */}
            <div className="bg-white border border-slate-200/80 rounded-2xl p-3.5 flex flex-col justify-between">
              <div className="flex items-start gap-2.5">
                <div className="w-9 h-9 rounded-full bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center flex-shrink-0">
                  <FileText size={17} />
                </div>
                <div className="space-y-1">
                  <div className="text-[14px] font-bold text-[#0F172A]">
                    Kịch bản phiên bản 3
                  </div>
                  <div className="text-[11.5px] text-slate-500">Chủ đề</div>
                  <div className="text-[13px] font-bold text-[#0F172A]">
                    Khu vườn của chúng mình
                  </div>
                  <div className="text-[11.5px] text-slate-500">
                    Trạng thái kịch bản: <strong className="text-[#0F172A]">Đã xác nhận</strong>
                  </div>
                </div>
              </div>
              <div className="flex justify-end pt-1">
                <button className="inline-flex items-center gap-1 border border-[#3B82F6] text-[#1D63F2] text-[12px] font-semibold px-3 py-1 rounded-lg hover:bg-blue-50 cursor-pointer">
                  <span>Xem kịch bản</span>
                  <ChevronRight size={13} />
                </button>
              </div>
            </div>

            {/* Box 3 */}
            <div className="bg-white border border-slate-200/80 rounded-2xl p-3.5 space-y-2">
              <div className="flex items-center gap-2 text-[14px] font-bold text-[#0F172A]">
                <div className="w-8 h-8 rounded-full bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center">
                  <BarChart2 size={16} />
                </div>
                <span>Tiến trình của các nhóm</span>
              </div>
              <div className="space-y-1.5 text-[12.5px]">
                <div className="flex items-center justify-between bg-[#F8FAFC] px-2.5 py-1.5 rounded-lg">
                  <span className="flex items-center gap-1.5 font-bold text-[#0F172A]">
                    <Users size={13} className="text-[#1D63F2]" /> Nhóm Lá
                  </span>
                  <span className="text-slate-600">Đã vẽ tranh</span>
                  <GreenCheckCircle size={15} />
                </div>
                <div className="flex items-center justify-between bg-[#F8FAFC] px-2.5 py-1.5 rounded-lg">
                  <span className="flex items-center gap-1.5 font-bold text-[#0F172A]">
                    <Users size={13} className="text-red-500" /> Nhóm Hoa
                  </span>
                  <span className="text-slate-600">Đã có kịch bản</span>
                  <GreenCheckCircle size={15} />
                </div>
                <div className="flex items-center justify-between bg-[#F8FAFC] px-2.5 py-1.5 rounded-lg">
                  <span className="flex items-center gap-1.5 font-bold text-[#0F172A]">
                    <Users size={13} className="text-amber-500" /> Nhóm Nắng
                  </span>
                  <span className="text-slate-600">Đang hoàn thiện</span>
                  <Clock size={14} className="text-[#D97706]" />
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Chọn bước tiếp theo */}
          <div className="pt-1 space-y-2.5">
            <h2 className="text-[17px] font-extrabold text-[#0F172A]">Chọn bước tiếp theo</h2>

            <div className="grid grid-cols-3 gap-4">
              {/* Option 1: Thử lại */}
              <div className="bg-white rounded-2xl border border-[#3B82F6] p-4 flex flex-col justify-between space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#EFF6FF] flex items-center justify-center text-[#1D63F2] flex-shrink-0">
                    <RotateCw size={18} />
                  </div>
                  <div>
                    <h3 className="text-[15.5px] font-extrabold text-[#0F172A]">Thử lại</h3>
                    <p className="text-[12.5px] text-slate-600 mt-0.5 leading-snug">
                      Gửi một yêu cầu tạo mới theo chính sách được phép.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/session/video/generating')}
                  className="w-full flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] py-2 rounded-xl transition cursor-pointer"
                >
                  <Play size={14} className="fill-white" />
                  <span>Thử lại</span>
                </button>
              </div>

              {/* Option 2: Bỏ qua video */}
              <div className="bg-white rounded-2xl border border-amber-300 p-4 flex flex-col justify-between space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706] flex-shrink-0">
                    <FastForward size={18} className="fill-[#D97706]" />
                  </div>
                  <div>
                    <h3 className="text-[15.5px] font-extrabold text-[#0F172A]">Bỏ qua video</h3>
                    <p className="text-[12.5px] text-slate-600 mt-0.5 leading-snug">
                      Ghi nhận quyết định và chuyển theo điều phối của giáo viên.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/library/offline')}
                  className="w-full flex items-center justify-center gap-2 bg-[#F59E0B] hover:bg-amber-600 text-white font-semibold text-[13.5px] py-2 rounded-xl transition cursor-pointer"
                >
                  <FastForward size={14} className="fill-white" />
                  <span>Bỏ qua video</span>
                </button>
              </div>

              {/* Option 3: Kết thúc phiên */}
              <div className="bg-white rounded-2xl border border-red-300 p-4 flex flex-col justify-between space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#FFE4E6] flex items-center justify-center text-[#E11D48] flex-shrink-0">
                    <Square size={16} />
                  </div>
                  <div>
                    <h3 className="text-[15.5px] font-extrabold text-[#0F172A]">Kết thúc phiên</h3>
                    <p className="text-[12.5px] text-slate-600 mt-0.5 leading-snug">
                      Xác nhận phần đã lưu trước khi kết thúc.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/portfolio/observation')}
                  className="w-full flex items-center justify-center gap-2 bg-[#EF4444] hover:bg-red-600 text-white font-semibold text-[13.5px] py-2 rounded-xl transition cursor-pointer"
                >
                  <Square size={13} className="fill-white" />
                  <span>Kết thúc phiên</span>
                </button>
              </div>
            </div>
          </div>

          {/* Footer Info */}
          <div className="bg-[#EFF6FF] rounded-xl px-4 py-2.5 flex items-center justify-between text-[12.5px]">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-[#1D63F2] text-white text-[11px] font-bold flex items-center justify-center">
                i
              </div>
              <strong className="text-[#0F172A]">Về điều phối lớp</strong>
              <span className="text-slate-600">
                Không tự chuyển hoạt động khi chưa có quyết định.
              </span>
            </div>
            <button
              onClick={() => navigate('/session/orchestrate')}
              className="inline-flex items-center gap-1 border border-[#3B82F6] bg-white text-[#1D63F2] font-semibold px-3 py-1 rounded-lg hover:bg-blue-50 cursor-pointer"
            >
              <span>Xem hướng dẫn</span>
              <ChevronRight size={13} />
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── T09 — Duyệt video (Chờ giáo viên duyệt) ──
  return (
    <div className="px-7 py-3.5 space-y-3 max-w-[1400px] mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
          Kiến thức & video
        </h1>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-[19.5px] font-extrabold text-[#0F172A]">
            Khu vườn của chúng mình
          </span>
          <span className="inline-flex items-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[12.5px] font-semibold px-3 py-1 rounded-full">
            <Clock size={13.5} className="text-[#D97706]" />
            Chờ giáo viên duyệt
          </span>
        </div>
      </div>

      {/* Main 2-Column Layout */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* Left Column (7 cols) */}
        <div className="col-span-7 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="text-[15px] font-extrabold text-[#0F172A]">
            Bản xem trước <span className="text-slate-400 mx-1">•</span> Phiên bản 3
          </div>

          {/* Video Frame */}
          <div className="rounded-xl overflow-hidden border border-slate-200 relative bg-slate-900">
            <img
              src={videoPreview}
              alt="Video preview"
              className="w-full h-[255px] object-cover block"
            />
            {/* Player Controls Overlay */}
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/50 to-transparent text-white px-4 py-2 flex items-center gap-3">
              <Play size={15} className="fill-white" />
              <div className="flex-1 h-1 bg-white/40 rounded-full overflow-hidden flex items-center">
                <div className="w-3 h-3 rounded-full bg-white" />
              </div>
              <span className="text-[12px] font-medium">0:00 / 1:18</span>
              <Volume2 size={15} />
              <Maximize2 size={14} />
            </div>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-6 border-b border-slate-100 px-1">
            <button className="py-2 text-[13.5px] font-bold text-[#1D63F2] border-b-2 border-[#1D63F2] inline-flex items-center gap-1.5">
              <FileText size={14} />
              <span>Kịch bản</span>
            </button>
            <button className="py-2 text-[13.5px] font-medium text-slate-600 hover:text-slate-900 inline-flex items-center gap-1.5">
              <BookOpen size={14} />
              <span>Nguồn kiến thức</span>
            </button>
            <button className="py-2 text-[13.5px] font-medium text-slate-600 hover:text-slate-900 inline-flex items-center gap-1.5">
              <Clock size={14} />
              <span>Lịch sử</span>
            </button>
          </div>

          {/* Script List */}
          <div className="space-y-2 text-[13.5px] text-slate-800">
            {[
              { num: 1, text: 'Hạt đậu nảy mầm khi có điều kiện phù hợp.' },
              { num: 2, text: 'Rễ giúp cây hấp thụ nước.' },
              { num: 3, text: 'Lá giúp cây nhận ánh sáng.' },
            ].map((s) => (
              <div key={s.num} className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-[#EFF6FF] text-[#1D63F2] font-bold text-[12px] flex items-center justify-center">
                  {s.num}
                </span>
                <span className="font-medium">{s.text}</span>
              </div>
            ))}
          </div>

          {/* Nguồn kiến thức Section */}
          <div className="pt-2 border-t border-slate-100 space-y-2">
            <h3 className="text-[14.5px] font-extrabold text-[#0F172A]">Nguồn kiến thức</h3>
            <div className="space-y-2">
              <div className="bg-[#F8FAFC] border border-slate-200/70 rounded-xl px-3.5 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center">
                    <FileText size={15} />
                  </div>
                  <div>
                    <div className="text-[13px] font-bold text-[#0F172A]">
                      Tài liệu lớp: Vòng đời cây đậu
                    </div>
                    <div className="text-[11.5px] text-slate-500">
                      Tài liệu giảng dạy đã được duyệt cho lớp Mầm Xanh
                    </div>
                  </div>
                </div>
                <ChevronRight size={15} className="text-slate-400" />
              </div>

              <div className="bg-[#F8FAFC] border border-slate-200/70 rounded-xl px-3.5 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center">
                    <BookOpen size={15} />
                  </div>
                  <div>
                    <div className="text-[13px] font-bold text-[#0F172A]">
                      Thư viện kiến thức đã duyệt
                    </div>
                    <div className="text-[11.5px] text-slate-500">
                      Kiến thức phù hợp với nhóm tuổi 6–8
                    </div>
                  </div>
                </div>
                <ChevronRight size={15} className="text-slate-400" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (5 cols) */}
        <div className="col-span-5 space-y-3">
          {/* Card 1: Phạm vi trình chiếu */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between">
              <h3 className="text-[16px] font-extrabold text-[#0F172A]">Phạm vi trình chiếu</h3>
              <button className="inline-flex items-center gap-1.5 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[12px] px-3 py-1 rounded-lg transition cursor-pointer">
                <Pencil size={12.5} />
                <span>Chỉnh</span>
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2 bg-[#F8FAFC] border border-slate-100 rounded-xl p-3 text-[12.5px]">
              <div>
                <div className="text-slate-500 text-[11.5px]">Lớp học</div>
                <div className="font-bold text-[#0F172A] mt-1 flex items-center gap-1">
                  <Users size={13.5} className="text-[#1D63F2]" />
                  <span>Lớp Mầm Xanh</span>
                </div>
              </div>
              <div>
                <div className="text-slate-500 text-[11.5px]">Phạm vi</div>
                <div className="font-bold text-[#0F172A] mt-1 flex items-center gap-1">
                  <Users size={13.5} className="text-slate-500" />
                  <span>Cả lớp</span>
                </div>
              </div>
              <div>
                <div className="text-slate-500 text-[11.5px]">Độ tuổi phù hợp</div>
                <div className="font-bold text-[#0F172A] mt-1 flex items-center gap-1">
                  <Users size={13.5} className="text-slate-500" />
                  <span>6 – 8 tuổi</span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Thông tin duyệt + Xác nhận + Hành động */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            {/* Thông tin duyệt */}
            <div className="space-y-2.5">
              <h3 className="text-[16px] font-extrabold text-[#0F172A]">Thông tin duyệt</h3>
              <div className="bg-[#F8FAFC] border border-slate-100 rounded-xl p-3 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center">
                  <FileText size={17} />
                </div>
                <div>
                  <div className="text-[13.5px] font-bold text-[#0F172A]">
                    Nội dung đang duyệt: phiên bản 3
                  </div>
                  <div className="text-[12px] text-slate-500">Khu vườn của chúng mình</div>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12px] font-semibold px-3 py-1 rounded-full">
                  <Shield size={13.5} />
                  An toàn nội dung: Đã kiểm tra
                </span>
                <span className="inline-flex items-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12px] font-semibold px-3 py-1 rounded-full">
                  <GreenCheckCircle size={13.5} />
                  Nguồn: Đã đối chiếu
                </span>
              </div>
            </div>

            {/* Xác nhận của giáo viên */}
            <div className="pt-2.5 border-t border-slate-100 space-y-2">
              <h3 className="text-[15.5px] font-extrabold text-[#0F172A]">
                Xác nhận của giáo viên
              </h3>
              <div
                onClick={() => setChecked1(!checked1)}
                className="flex items-center gap-2.5 text-[13px] text-slate-700 font-medium cursor-pointer"
              >
                <BlueCheckBox size={18} />
                <span>Tôi đã xem bản video này</span>
              </div>
              <div
                onClick={() => setChecked2(!checked2)}
                className="flex items-center gap-2.5 text-[13px] text-slate-700 font-medium cursor-pointer"
              >
                <BlueCheckBox size={18} />
                <span>Nội dung phù hợp với lớp</span>
              </div>
            </div>

            {/* Hành động */}
            <div className="pt-2.5 border-t border-slate-100 space-y-2.5">
              <h3 className="text-[15.5px] font-extrabold text-[#0F172A]">Hành động</h3>

              <div className="flex items-center justify-between gap-2">
                <button className="inline-flex items-center justify-center gap-1.5 border border-red-300 bg-white hover:bg-red-50 text-red-600 font-semibold text-[12.5px] px-3 py-2 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                  <Ban size={13.5} className="shrink-0" />
                  <span>Từ chối</span>
                </button>

                <button className="inline-flex items-center justify-center gap-1.5 border border-amber-400 bg-white hover:bg-amber-50 text-[#B45309] font-semibold text-[12.5px] px-3 py-2 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                  <Pencil size={13.5} className="shrink-0" />
                  <span>Yêu cầu chỉnh sửa</span>
                </button>

                <button className="flex-1 inline-flex items-center justify-center gap-1.5 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[12.5px] px-3 py-2 rounded-xl shadow-xs transition cursor-pointer whitespace-nowrap shrink-0">
                  <Check size={14} className="shrink-0" />
                  <span>Duyệt phiên bản này</span>
                </button>
              </div>

              <div className="flex items-center gap-3">
                <button
                  disabled
                  className="inline-flex items-center justify-center gap-2 bg-slate-200 text-slate-500 font-semibold text-[12.5px] px-4 py-2 rounded-xl cursor-not-allowed whitespace-nowrap shrink-0"
                >
                  <Play size={13.5} className="fill-slate-400 text-slate-400 shrink-0" />
                  <span>Trình chiếu cho lớp</span>
                </button>
                <span className="text-[11.5px] text-slate-500">
                  Chỉ trình chiếu sau khi giáo viên duyệt.
                </span>
              </div>

              <div className="bg-[#EFF6FF] rounded-xl p-2.5 flex items-start gap-2 text-[11.5px] text-slate-700 leading-snug">
                <div className="w-4 h-4 rounded-full bg-[#1D63F2] text-white text-[9.5px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                  i
                </div>
                <div>
                  <strong className="text-[#0F172A]">Chỉnh nội dung sẽ cần duyệt lại.</strong>
                  <div className="text-slate-600 mt-0.5">
                    Bất kỳ thay đổi nào về kịch bản, video hoặc phạm vi trình chiếu đều sẽ làm mất
                    hiệu lực phê duyệt hiện tại.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
