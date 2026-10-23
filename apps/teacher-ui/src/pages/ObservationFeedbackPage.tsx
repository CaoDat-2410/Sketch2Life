import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Check,
  ChevronRight,
  MessageSquare,
  Lightbulb,
  Pencil,
  Ban,
  Flag,
  FileText,
  Calendar,
  Target,
  Image as ImageIcon,
} from 'lucide-react'
import {
  GreenCheckCircle,
  CloudBadgeIcon,
  LeafBadgeIcon,
  FlowerBadgeIcon,
  SunBadgeIcon,
  SproutBadgeIcon,
} from '../components/Icons'
import evidenceMay from '../assets/evidence-may.png'

const RUBRIC_LEVELS = [
  {
    key: 'none',
    title: 'Chưa quan sát',
  },
  {
    key: 'supported',
    title: 'Thể hiện với hỗ trợ',
  },
  {
    key: 'active',
    title: 'Thể hiện trong hoạt động',
  },
  {
    key: 'extended',
    title: 'Mở rộng ý tưởng',
  },
]

export function ObservationFeedbackPage() {
  const navigate = useNavigate()
  const [selectedChild, setSelectedChild] = useState('may')
  const [rubric, setRubric] = useState('active')
  const [comment, setComment] = useState(
    'Mây giải thích hình dạng chiếc lá và thử thêm gân lá.'
  )

  return (
    <div className="px-7 py-3.5 space-y-3 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Phản hồi & quan sát
          </h1>
          <div className="text-[19px] font-extrabold text-[#0F172A] mt-0.5">
            Khu vườn của chúng mình{' '}
            <span className="font-normal text-slate-600">• Nhóm tuổi 6–8</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="inline-flex items-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2.5 rounded-xl text-[13.5px] transition cursor-pointer">
            <FileText size={15} />
            <span>Lưu nháp</span>
          </button>
          <button
            onClick={() => navigate('/portfolio')}
            className="flex items-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold px-5 py-2.5 rounded-xl text-[13.5px] shadow-xs transition cursor-pointer"
          >
            <Check size={16} />
            <span>Xác nhận nhận xét</span>
          </button>
        </div>
      </div>

      {/* ── Child Selector Row ── */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5">
          {[
            { id: 'may', name: 'Mây', icon: <CloudBadgeIcon size={22} /> },
            { id: 'la', name: 'Lá', icon: <LeafBadgeIcon size={22} /> },
            { id: 'nang', name: 'Nắng', icon: <SunBadgeIcon size={22} /> },
            { id: 'hoa', name: 'Hoa', icon: <FlowerBadgeIcon size={22} /> },
          ].map((c) => {
            const active = selectedChild === c.id
            return (
              <button
                key={c.id}
                onClick={() => setSelectedChild(c.id)}
                className={`flex items-center gap-2.5 px-4 py-2 rounded-xl text-[14px] font-bold transition cursor-pointer border ${
                  active
                    ? 'border-[#3B82F6] bg-[#EFF6FF] text-[#1D63F2]'
                    : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                {c.icon}
                <span>{c.name}</span>
              </button>
            )
          })}
        </div>

        <div className="h-5 w-px bg-slate-300 mx-1" />

        <div className="flex items-center gap-2 text-[13.5px] text-slate-600 font-medium">
          <Calendar size={15} className="text-slate-500" />
          <span>Quan sát trong hoạt động hôm nay</span>
        </div>
      </div>

      {/* ── Main 2-Column Layout ── */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* ── LEFT COLUMN (5 cols) ── */}
        <div className="col-span-5 space-y-3.5">
          {/* Card 1: Bằng chứng trực tiếp */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[18px] font-extrabold text-[#0F172A]">
              Bằng chứng trực tiếp
            </h2>

            {/* Evidence 1: Drawing */}
            <div className="bg-[#F8FAFC] border border-slate-200/70 rounded-2xl p-3 flex items-center gap-3.5">
              <img
                src={evidenceMay}
                alt="Phần đóng góp của Mây"
                className="w-[155px] h-[115px] rounded-xl object-cover border border-slate-200/60 flex-shrink-0"
              />
              <div className="space-y-1.5">
                <div className="flex items-start gap-1.5 text-[14px] font-extrabold text-[#0F172A] leading-snug">
                  <ImageIcon size={16} className="text-[#16A34A] flex-shrink-0 mt-0.5" />
                  <span>Phần đóng góp của Mây đã ghi nhận</span>
                </div>
                <p className="text-[12.5px] text-slate-600 leading-relaxed">
                  Tranh vẽ lá cây cho khu vườn chung của nhóm.
                </p>
              </div>
            </div>

            {/* Evidence 2: Offline activity */}
            <div className="flex items-start gap-3 px-1">
              <div className="w-10 h-10 rounded-full bg-[#EFF6FF] flex items-center justify-center flex-shrink-0">
                <SproutBadgeIcon size={20} />
              </div>
              <div>
                <div className="text-[14px] font-bold text-[#0F172A]">
                  Quan sát hoạt động ngoài màn hình
                </div>
                <p className="text-[12.5px] text-slate-600 leading-snug mt-0.5">
                  Mây tích cực trao đổi ý tưởng với bạn khi chọn hình dạng lá.
                </p>
              </div>
            </div>

            <button className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-[13.5px] font-semibold text-[#1D63F2] transition cursor-pointer whitespace-nowrap">
              <FileText size={15} className="shrink-0" />
              <span>Xem bằng chứng</span>
              <ChevronRight size={15} className="shrink-0" />
            </button>
          </div>

          {/* Card 2: Phản hồi của trẻ */}
          <div className="bg-[#ECFDF5]/60 rounded-2xl border border-emerald-200/70 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h3 className="text-[17px] font-extrabold text-[#0F172A]">
              Phản hồi của trẻ
            </h3>
            <div className="bg-white border border-slate-200/70 rounded-2xl p-3.5 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2.5">
                <CloudBadgeIcon size={28} />
                <span className="text-[13.5px] font-medium text-[#0F172A]">
                  “Em thích cùng bạn tạo khu vườn”
                </span>
              </div>
              <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[11.5px] font-semibold px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                <MessageSquare size={12.5} className="shrink-0" /> <span>Trẻ chia sẻ</span>
              </span>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN: Quan sát của giáo viên (7 cols) ── */}
        <div className="col-span-7 space-y-3.5">
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[18px] font-extrabold text-[#0F172A]">
              Quan sát của giáo viên
            </h2>

            {/* Rubric Section */}
            <div className="space-y-2.5">
              <div className="bg-[#F8FAFC] border border-slate-100 rounded-xl px-3.5 py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target size={17} className="text-[#1D63F2]" />
                  <span className="text-[14.5px] font-extrabold text-[#0F172A]">
                    Diễn đạt ý tưởng trong hoạt động
                  </span>
                </div>
                <span className="text-slate-600 text-[12.5px] font-medium">
                  Rubric 6–8 tuổi • v1
                </span>
              </div>

              <div className="grid grid-cols-4 gap-2.5">
                {RUBRIC_LEVELS.map((lvl) => {
                  const isSelected = rubric === lvl.key
                  return (
                    <div
                      key={lvl.key}
                      onClick={() => setRubric(lvl.key)}
                      className={`p-3 rounded-xl border cursor-pointer transition flex items-center gap-2.5 ${
                        isSelected
                          ? 'border-2 border-[#3B82F6] bg-[#EFF6FF]'
                          : 'border-slate-200 bg-white hover:bg-slate-50'
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded-full flex-shrink-0 ${
                          isSelected
                            ? 'border-4 border-[#1D63F2] bg-white'
                            : 'border border-slate-300 bg-white'
                        }`}
                      />
                      <div
                        className={`text-[12.5px] font-semibold leading-snug whitespace-pre-line ${
                          isSelected ? 'text-[#1D63F2] font-bold' : 'text-slate-700'
                        }`}
                      >
                        {lvl.title}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Teacher Comment */}
            <div className="space-y-1.5">
              <label className="block text-[13.5px] font-extrabold text-[#0F172A]">
                Nhận xét của giáo viên
              </label>
              <textarea
                rows={2}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="w-full p-3 bg-white border border-slate-200 rounded-xl text-[13.5px] text-[#0F172A] resize-none focus:outline-none focus:ring-2 focus:ring-[#1D63F2]"
              />
            </div>

            {/* AI Suggestion Box */}
            <div className="bg-[#FFFDF5] border border-amber-200 rounded-2xl p-3.5 space-y-2.5">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-[#FEF3C7] text-[#D97706] flex items-center justify-center">
                  <Lightbulb size={15} />
                </div>
                <span className="text-[14px] font-extrabold text-[#0F172A]">Gợi ý AI •</span>
                <span className="inline-flex items-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D97706]" />
                  Chưa xác nhận
                </span>
              </div>

              <div className="bg-[#FEF9E7] rounded-xl px-3.5 py-2 text-[13px] text-slate-800">
                Có thể hỏi thêm về cách nhóm chọn hình dạng.
              </div>

              <div className="flex items-center justify-end gap-2">
                <button className="inline-flex items-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[12px] px-3 py-1.5 rounded-xl transition cursor-pointer">
                  <Pencil size={12.5} />
                  <span>Chỉnh gợi ý</span>
                </button>
                <button className="inline-flex items-center gap-1.5 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-[12px] px-3 py-1.5 rounded-xl transition cursor-pointer">
                  <Ban size={12.5} />
                  <span>Không sử dụng</span>
                </button>
              </div>
            </div>
          </div>

          {/* Bottom Bar Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 px-4 py-3 flex items-center justify-between shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center gap-2 text-[13.5px] text-slate-700 font-medium">
              <GreenCheckCircle size={18} />
              <span>Bản nháp đã lưu</span>
            </div>

            <button
              onClick={() => navigate('/portfolio')}
              className="inline-flex items-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] px-5 py-2 rounded-xl shadow-xs transition cursor-pointer"
            >
              <Flag size={14} />
              <span>Hoàn tất kết quả phiên</span>
              <ChevronRight size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
