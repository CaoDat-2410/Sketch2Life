import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowUpDown,
  Play,
  MoreHorizontal,
  Eye,
  Lightbulb,
  GripVertical,
  Trash2,
  Image as ImageIcon,
} from 'lucide-react'
import {
  BlueCheckBox,
  LeafBadgeIcon,
  FlowerBadgeIcon,
  SunBadgeIcon,
  SproutBadgeIcon,
} from '../components/Icons'
import galleryLa from '../assets/gallery-la.png'
import galleryHoa from '../assets/gallery-hoa.png'
import galleryNang from '../assets/gallery-nang.png'

export function ClassGalleryPage() {
  const navigate = useNavigate()
  const [caption, setCaption] = useState('Nhóm Lá quan sát hình dạng của lá')

  return (
    <div className="px-7 py-3.5 space-y-3 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Phòng tranh của lớp
          </h1>
          <div className="text-[19.5px] font-extrabold text-[#0F172A] mt-0.5">
            Khu vườn của chúng mình
          </div>
          <div className="mt-1.5">
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7]/80 border border-emerald-200 text-[#15803D] text-[12px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
              <SproutBadgeIcon size={14} />
              <span>Chỉ trong phiên này</span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2.5 rounded-xl text-[13.5px] transition cursor-pointer whitespace-nowrap shrink-0">
            <ArrowUpDown size={15} className="shrink-0" />
            <span>Sắp xếp trình bày</span>
          </button>
          <button
            onClick={() => navigate('/session/video')}
            className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold px-5 py-2.5 rounded-xl text-[13.5px] shadow-xs transition cursor-pointer whitespace-nowrap shrink-0"
          >
            <Play size={15} className="fill-white shrink-0" />
            <span>Bắt đầu trình bày</span>
          </button>
        </div>
      </div>

      {/* ── Main 2-Column Layout ── */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* ── LEFT COLUMN: Tabs + 3 Artwork Cards (8 cols) ── */}
        <div className="col-span-8 space-y-3">
          {/* Filter Tabs */}
          <div className="flex items-center gap-2">
            <button className="bg-[#1D63F2] text-white font-semibold text-[13px] px-5 py-1.5 rounded-full shadow-2xs">
              Đã chọn (3)
            </button>
            <button className="bg-slate-200/70 text-slate-700 hover:bg-slate-200 font-semibold text-[13px] px-5 py-1.5 rounded-full">
              Tranh trong phiên
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {/* Card 1: Nhóm Lá */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BlueCheckBox size={20} />
                  <span className="w-6 h-6 rounded-full bg-[#EFF6FF] text-[#1D63F2] font-bold text-[12.5px] flex items-center justify-center">
                    1
                  </span>
                </div>
                <button className="text-slate-400 hover:text-slate-600">
                  <MoreHorizontal size={18} />
                </button>
              </div>

              <div className="rounded-xl overflow-hidden border border-slate-100 h-[255px]">
                <img
                  src={galleryLa}
                  alt="Nhóm Lá"
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="space-y-1.5 pt-0.5">
                <div className="flex items-center gap-2">
                  <LeafBadgeIcon size={24} />
                  <h3 className="text-[16px] font-extrabold text-[#0F172A]">Nhóm Lá</h3>
                </div>
                <p className="text-[12px] text-slate-600">
                  Tranh nhóm • Đóng góp đã ghi nhận
                </p>
                <div className="pt-0.5">
                  <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7]/80 text-[#15803D] text-[11.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                    <ImageIcon size={13} className="shrink-0" />
                    <span>Bản chụp đã lưu</span>
                  </span>
                </div>
              </div>
            </div>

            {/* Card 2: Nhóm Hoa */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BlueCheckBox size={20} />
                  <span className="w-6 h-6 rounded-full bg-[#EFF6FF] text-[#1D63F2] font-bold text-[12.5px] flex items-center justify-center">
                    2
                  </span>
                </div>
                <button className="text-slate-400 hover:text-slate-600">
                  <MoreHorizontal size={18} />
                </button>
              </div>

              <div className="rounded-xl overflow-hidden border border-slate-100 h-[255px]">
                <img
                  src={galleryHoa}
                  alt="Nhóm Hoa"
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="space-y-1.5 pt-0.5">
                <div className="flex items-center gap-2">
                  <FlowerBadgeIcon size={24} />
                  <h3 className="text-[16px] font-extrabold text-[#0F172A]">Nhóm Hoa</h3>
                </div>
                <p className="text-[12px] text-slate-600">
                  Tranh nhóm • Có gợi ý riêng
                </p>
                <div className="flex items-center gap-1.5 pt-0.5">
                  <button className="inline-flex items-center justify-center gap-1 bg-white border border-[#3B82F6] text-[#1D63F2] text-[11.5px] font-semibold px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                    <Eye size={12.5} className="shrink-0" />
                    <span>Xem nét trẻ</span>
                  </button>
                  <button className="inline-flex items-center justify-center gap-1 bg-white border border-[#3B82F6] text-[#1D63F2] text-[11.5px] font-semibold px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                    <Lightbulb size={12.5} className="shrink-0" />
                    <span>Gợi ý</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Card 3: Nhóm Nắng */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BlueCheckBox size={20} />
                  <span className="w-6 h-6 rounded-full bg-[#EFF6FF] text-[#1D63F2] font-bold text-[12.5px] flex items-center justify-center">
                    3
                  </span>
                </div>
                <button className="text-slate-400 hover:text-slate-600">
                  <MoreHorizontal size={18} />
                </button>
              </div>

              <div className="rounded-xl overflow-hidden border border-slate-100 h-[255px]">
                <img
                  src={galleryNang}
                  alt="Nhóm Nắng"
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="space-y-1.5 pt-0.5">
                <div className="flex items-center gap-2">
                  <SunBadgeIcon size={24} />
                  <h3 className="text-[16px] font-extrabold text-[#0F172A]">Nhóm Nắng</h3>
                </div>
                <p className="text-[12px] text-slate-600">
                  Tranh nhóm • Đóng góp đã ghi nhận
                </p>
                <div className="pt-0.5">
                  <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7]/80 text-[#15803D] text-[11.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                    <ImageIcon size={13} className="shrink-0" />
                    <span>Bản chụp đã lưu</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN (4 cols) ── */}
        <div className="col-span-4 space-y-3.5">
          {/* Card 1: Trình tự chia sẻ */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[16.5px] font-extrabold text-[#0F172A]">Trình tự chia sẻ</h2>

            <div className="space-y-2">
              {[
                { num: 1, name: 'Nhóm Lá', icon: <LeafBadgeIcon size={22} /> },
                { num: 2, name: 'Nhóm Hoa', icon: <FlowerBadgeIcon size={22} /> },
                { num: 3, name: 'Nhóm Nắng', icon: <SunBadgeIcon size={22} /> },
              ].map((item) => (
                <div
                  key={item.num}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl border border-slate-200/70 bg-[#F8FAFC]"
                >
                  <GripVertical size={15} className="text-slate-400 cursor-grab" />
                  <span className="w-6 h-6 rounded-full bg-[#EFF6FF] text-[#1D63F2] font-bold text-[12px] flex items-center justify-center">
                    {item.num}
                  </span>
                  {item.icon}
                  <span className="text-[13.5px] font-bold text-[#0F172A]">{item.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Card 2: Chú thích tranh */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[16.5px] font-extrabold text-[#0F172A]">Chú thích tranh</h2>

            <div className="flex items-center gap-2 text-[14px] font-bold text-[#0F172A]">
              <LeafBadgeIcon size={22} />
              <span>Nhóm Lá</span>
            </div>

            <div>
              <label className="block text-[12.5px] font-bold text-[#0F172A] mb-1">
                Điều em muốn kể
              </label>
              <div className="relative">
                <textarea
                  rows={2}
                  value={caption}
                  onChange={(e) => setCaption(e.target.value)}
                  className="w-full p-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-[13px] text-slate-800 resize-none focus:outline-none focus:ring-2 focus:ring-[#1D63F2]"
                />
              </div>
              <div className="text-right text-[11px] text-slate-500 mt-0.5">
                {caption === 'Nhóm Lá quan sát hình dạng của lá' ? 32 : caption.length}/200
              </div>
              <div className="flex items-center gap-1.5 text-[12px] text-slate-600 mt-1">
                <div className="w-4 h-4 rounded-full bg-slate-500 text-white text-[9.5px] font-bold flex items-center justify-center">
                  i
                </div>
                <span>Chú thích tách khỏi tranh gốc</span>
              </div>
            </div>

            <button className="w-full flex items-center justify-center gap-2 border border-red-300 bg-white hover:bg-red-50 text-red-600 font-semibold text-[13px] py-2 rounded-xl transition cursor-pointer">
              <Trash2 size={14} />
              <span>Rút khỏi trình bày</span>
            </button>

            <div className="bg-[#EFF6FF] border border-blue-200/70 rounded-xl p-2.5 flex items-start gap-2 text-[11.5px] text-[#1D63F2] font-medium leading-relaxed">
              <div className="w-4 h-4 rounded-full bg-[#1D63F2] text-white text-[9.5px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                i
              </div>
              <span>Chỉ giáo viên điều phối chia sẻ trong lớp; bản gốc được giữ nguyên.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
