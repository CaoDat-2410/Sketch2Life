import { useState } from 'react'
import {
  FileText,
  Send,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Puzzle,
  X,
  Plus,
  User,
  Users,
  Megaphone,
  Clock,
} from 'lucide-react'
import { GreenCheckCircle } from '../components/Icons'
import artSprout from '../assets/art-sprout.png'
import artFlowers from '../assets/art-flowers.png'

export function ContentAuthoringPage() {
  const [contentType, setContentType] = useState<'knowledge' | 'activity'>('knowledge')
  const [title, setTitle] = useState('Khám phá chiếc lá')
  const [body, setBody] = useState(
    'Cùng quan sát hình dạng, màu sắc và gân lá. Trẻ chia sẻ điều mình nhìn thấy trước khi nghe giải thích.'
  )

  return (
    <div className="px-7 py-3.5 space-y-3 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
              Soạn nội dung
            </h1>
            <span className="inline-flex items-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[12.5px] font-semibold px-3 py-1 rounded-full">
              <span className="w-2 h-2 rounded-full bg-[#D97706]" />
              Bản nháp v2
            </span>
          </div>
          <p className="text-[14.5px] text-slate-600 mt-1">
            Tạo và chỉnh sửa nội dung học tập cho lớp Mầm Xanh.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button className="inline-flex items-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition cursor-pointer">
            <FileText size={15} />
            <span>Lưu nháp</span>
          </button>
          <button className="inline-flex items-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] px-5 py-2.5 rounded-xl shadow-xs transition cursor-pointer">
            <Send size={15} />
            <span>Gửi duyệt</span>
          </button>
        </div>
      </div>

      {/* ── Main 3-Column Layout ── */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* ── LEFT COLUMN: Bản nháp của tôi (3 cols) ── */}
        <div className="col-span-3 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="flex items-center justify-between">
            <h2 className="text-[16px] font-extrabold text-[#0F172A]">
              Bản nháp của tôi
            </h2>
            <button className="w-7 h-7 rounded-lg bg-[#1D63F2] text-white flex items-center justify-center hover:bg-[#1554D6] cursor-pointer">
              <Plus size={15} />
            </button>
          </div>

          <div className="border-2 border-[#3B82F6] bg-[#EFF6FF]/70 rounded-2xl p-3 flex items-center justify-between gap-2.5 cursor-pointer">
            <div className="flex items-center gap-2.5 min-w-0">
              <img
                src={artSprout}
                alt="Khám phá chiếc lá"
                className="w-12 h-12 rounded-xl object-cover border border-slate-200/60 flex-shrink-0"
              />
              <div className="min-w-0">
                <div className="text-[13.5px] font-bold text-[#0F172A] truncate">
                  Khám phá chiếc lá
                </div>
                <div className="text-[11.5px] text-slate-600 mt-0.5">
                  Kiến thức • Bản nháp v2
                </div>
              </div>
            </div>
            <ChevronRight size={15} className="text-[#1D63F2] flex-shrink-0" />
          </div>

          <div className="border border-slate-200/80 bg-white hover:bg-slate-50 rounded-2xl p-3 flex items-center justify-between gap-2.5 cursor-pointer transition">
            <div className="flex items-center gap-2.5 min-w-0">
              <img
                src={artFlowers}
                alt="Xếp hình khu vườn"
                className="w-12 h-12 rounded-xl object-cover border border-slate-200/60 flex-shrink-0"
              />
              <div className="min-w-0">
                <div className="text-[13.5px] font-bold text-[#0F172A] truncate">
                  Xếp hình khu vườn
                </div>
                <div className="text-[11.5px] text-slate-600 mt-0.5">
                  Hoạt động • Bản nháp
                </div>
              </div>
            </div>
            <ChevronRight size={15} className="text-slate-400 flex-shrink-0" />
          </div>
        </div>

        {/* ── CENTER COLUMN: Form (5 cols) ── */}
        <div className="col-span-5 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          {/* Loại nội dung */}
          <div>
            <div className="flex items-center gap-1.5 mb-1.5">
              <label className="text-[14px] font-extrabold text-[#0F172A]">
                Loại nội dung
              </label>
              <span className="w-4 h-4 rounded-full border border-slate-400 text-slate-500 text-[10px] font-bold flex items-center justify-center">
                i
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2.5">
              <button
                onClick={() => setContentType('knowledge')}
                className={`py-2 px-3 rounded-xl text-[13.5px] font-bold border inline-flex items-center justify-center gap-2 transition cursor-pointer ${
                  contentType === 'knowledge'
                    ? 'border-[#3B82F6] bg-[#EFF6FF] text-[#1D63F2]'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <BookOpen size={15} />
                <span>Kiến thức</span>
              </button>
              <button
                onClick={() => setContentType('activity')}
                className={`py-2 px-3 rounded-xl text-[13.5px] font-semibold border inline-flex items-center justify-center gap-2 transition cursor-pointer ${
                  contentType === 'activity'
                    ? 'border-[#3B82F6] bg-[#EFF6FF] text-[#1D63F2]'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Puzzle size={15} />
                <span>Hoạt động</span>
              </button>
            </div>
          </div>

          {/* Tiêu đề */}
          <div>
            <label className="block text-[13px] font-bold text-[#0F172A] mb-1">
              Tiêu đề <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2 bg-white border border-slate-200 rounded-xl text-[13.5px] text-[#0F172A] font-medium focus:outline-none focus:ring-2 focus:ring-[#1D63F2]"
            />
          </div>

          {/* Nhóm tuổi */}
          <div>
            <label className="block text-[13px] font-bold text-[#0F172A] mb-1">
              Nhóm tuổi <span className="text-red-500">*</span>
            </label>
            <button className="w-full flex items-center justify-between px-3.5 py-2 bg-white border border-slate-200 rounded-xl text-[13.5px] font-medium text-[#0F172A]">
              <span>6–8</span>
              <ChevronDown size={15} className="text-slate-500" />
            </button>
          </div>

          {/* Nội dung */}
          <div>
            <label className="block text-[13px] font-bold text-[#0F172A] mb-1">
              Nội dung <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={3}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="w-full p-3 bg-white border border-slate-200 rounded-xl text-[13px] text-[#0F172A] leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-[#1D63F2]"
            />
            <div className="text-right text-[11px] text-slate-500 mt-0.5">
              87/1.000
            </div>
          </div>

          {/* Nguồn tham khảo */}
          <div className="pt-1 border-t border-slate-100 space-y-2">
            <div>
              <div className="flex items-center gap-1.5">
                <label className="text-[13.5px] font-extrabold text-[#0F172A]">
                  Nguồn tham khảo
                </label>
                <span className="w-4 h-4 rounded-full border border-slate-400 text-slate-500 text-[10px] font-bold flex items-center justify-center">
                  i
                </span>
              </div>
              <div className="text-[11.5px] text-slate-500 mt-0.5">
                Tài liệu kiến thức đã kiểm tra
              </div>
            </div>

            <div className="space-y-2">
              <div className="bg-white border border-slate-200 rounded-xl px-3 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-[#FFE4E6] text-[#E11D48] flex items-center justify-center">
                    <FileText size={14} />
                  </div>
                  <div>
                    <div className="text-[12.5px] font-bold text-[#0F172A]">
                      Cây xanh quanh bé
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Tài liệu nội bộ • Đã kiểm tra
                    </div>
                  </div>
                </div>
                <X size={14} className="text-slate-400 cursor-pointer" />
              </div>

              <div className="bg-white border border-slate-200 rounded-xl px-3 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center">
                    <FileText size={14} />
                  </div>
                  <div>
                    <div className="text-[12.5px] font-bold text-[#0F172A]">
                      Một số loại lá phổ biến
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Tài liệu nội bộ • Đã kiểm tra
                    </div>
                  </div>
                </div>
                <X size={14} className="text-slate-400 cursor-pointer" />
              </div>
            </div>

            <button className="w-full flex items-center justify-center gap-1.5 border border-dashed border-slate-300 bg-[#F8FAFC] hover:bg-blue-50 text-[#1D63F2] font-semibold text-[12.5px] py-2 rounded-xl transition cursor-pointer">
              <Plus size={14} />
              <span>Thêm nguồn</span>
            </button>
          </div>
        </div>

        {/* ── RIGHT COLUMN (4 cols) ── */}
        <div className="col-span-4 space-y-3">
          {/* Card 1: Kiểm tra trước khi gửi */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[16px] font-extrabold text-[#0F172A]">
              Kiểm tra trước khi gửi
            </h2>

            <div className="space-y-2 text-[12.5px]">
              {[
                { title: 'Có nguồn nội dung', sub: 'Đã thêm 2 tài liệu' },
                { title: 'Phù hợp độ tuổi', sub: 'Nội dung phù hợp nhóm 6–8 tuổi' },
                { title: 'Đã ghi chú an toàn', sub: 'Không có nội dung nhạy cảm' },
                { title: 'Không chứa dữ liệu trẻ', sub: 'Không có thông tin nhận dạng cá nhân' },
              ].map((item) => (
                <div key={item.title} className="flex items-start gap-2.5">
                  <div className="mt-0.5">
                    <GreenCheckCircle size={17} />
                  </div>
                  <div>
                    <div className="font-bold text-[#0F172A] leading-tight">
                      {item.title}
                    </div>
                    <div className="text-[11.5px] text-slate-500">{item.sub}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-[#DCFCE7]/80 rounded-xl p-2.5 flex items-center gap-2.5">
              <GreenCheckCircle size={18} />
              <div>
                <div className="text-[13px] font-bold text-[#15803D]">
                  Sẵn sàng gửi duyệt
                </div>
                <div className="text-[11px] text-slate-600">
                  Nội dung đã đáp ứng các yêu cầu kiểm tra.
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Lịch sử phiên bản */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center gap-1.5">
              <Clock size={15} className="text-slate-500" />
              <h2 className="text-[15.5px] font-extrabold text-[#0F172A]">
                Lịch sử phiên bản
              </h2>
            </div>
            <div className="flex items-center gap-2 text-[12px]">
              <span className="bg-[#DCFCE7] text-[#15803D] font-semibold px-2.5 py-0.5 rounded-full">
                v1 đã duyệt
              </span>
              <span className="text-slate-400">•</span>
              <span className="inline-flex items-center gap-1.5 bg-[#FEF3C7] text-[#B45309] font-semibold px-2.5 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-[#D97706]" />
                v2 bản nháp
              </span>
            </div>
            <div className="text-[11.5px] text-slate-600">
              Chỉnh nội dung đã công bố tạo phiên bản mới.
            </div>
          </div>

          {/* Card 3: Quy trình duyệt */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[15.5px] font-extrabold text-[#0F172A]">Quy trình duyệt</h2>

            <div className="flex items-center justify-between text-center gap-2">
              <div className="flex flex-col items-center gap-1.5 flex-1">
                <div className="w-8 h-8 rounded-full bg-[#EFF6FF] text-[#1D63F2] flex items-center justify-center shrink-0">
                  <User size={15} />
                </div>
                <span className="text-[11px] font-bold text-[#1D63F2] whitespace-nowrap">
                  Giáo viên soạn
                </span>
              </div>

              <div className="text-slate-400 font-bold text-xs shrink-0">→</div>

              <div className="flex flex-col items-center gap-1.5 flex-1">
                <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center shrink-0">
                  <Users size={15} />
                </div>
                <span className="text-[11px] font-medium text-slate-600 whitespace-nowrap">
                  Người có quyền duyệt
                </span>
              </div>

              <div className="text-slate-400 font-bold text-xs shrink-0">→</div>

              <div className="flex flex-col items-center gap-1.5 flex-1">
                <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center shrink-0">
                  <Megaphone size={15} />
                </div>
                <span className="text-[11px] font-medium text-slate-600 whitespace-nowrap">
                  Công bố
                </span>
              </div>
            </div>

            <div className="bg-[#FFFBEB] border border-amber-200/90 rounded-xl p-2.5 flex items-start gap-2 text-[11.5px] text-slate-700 leading-snug">
              <span className="w-4 h-4 rounded-full bg-[#F59E0B] text-white text-[9.5px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                !
              </span>
              <span>
                Bạn không có quyền tự duyệt và công bố. Vui lòng gửi duyệt để tiếp tục.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
