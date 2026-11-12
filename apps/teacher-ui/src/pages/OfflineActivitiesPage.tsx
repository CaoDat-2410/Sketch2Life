import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  X,
  Play,
  Check,
  ClipboardCheck,
  FileText,
  Pencil,
  BookOpen,
  Users,
  Target,
  Lightbulb,
} from 'lucide-react'
import {
  GreenCheckCircle,
  LeafBadgeIcon,
  SproutBadgeIcon,
} from '../components/Icons'
import offlineLeafCraft from '../assets/offline-leaf-craft.png'
import actThumb1 from '../assets/act-thumb-1.png'
import actThumb2 from '../assets/act-thumb-2.png'
import actThumb3 from '../assets/act-thumb-3.png'
import actThumb4 from '../assets/act-thumb-4.png'
import actThumb5 from '../assets/act-thumb-5.png'
import actThumb6 from '../assets/act-thumb-6.png'

const ACTIVITIES = [
  {
    id: '1',
    thumb: actThumb1,
    title: 'Xếp hình khu vườn từ lá',
    desc: 'Quan sát hình dạng và cùng sắp xếp',
  },
  {
    id: '2',
    thumb: actThumb2,
    title: 'Trồng hạt và quan sát',
    desc: 'Tìm hiểu cây con lớn lên như thế nào',
  },
  {
    id: '3',
    thumb: actThumb3,
    title: 'Vẽ khu vườn mơ ước',
    desc: 'Vẽ và kể về khu vườn của mình',
  },
  {
    id: '4',
    thumb: actThumb4,
    title: 'In lá lên giấy',
    desc: 'Khám phá hình dạng và hoa văn của lá',
  },
  {
    id: '5',
    thumb: actThumb5,
    title: 'Làm chuông gió từ lá',
    desc: 'Khéo tay tạo sản phẩm từ lá khô',
  },
  {
    id: '6',
    thumb: actThumb6,
    title: 'Đi dạo tìm lá',
    desc: 'Quan sát và so sánh các loại lá',
  },
]

export function OfflineActivitiesPage() {
  const navigate = useNavigate()
  const [selectedId, setSelectedId] = useState('1')
  const [scope, setScope] = useState<'group' | 'class'>('group')
  const [note, setNote] = useState('')

  return (
    <div className="px-7 py-3 space-y-2.5 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div>
        <h1 className="text-[27px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
          Hoạt động ngoài màn hình
        </h1>
        <div className="text-[19px] font-extrabold text-[#0F172A] mt-0.5">
          Khu vườn của chúng mình
        </div>

        <div className="flex items-center gap-2 mt-2">
          <button className="inline-flex items-center gap-2 bg-[#1D63F2] text-white font-semibold text-[13px] px-4 py-2 rounded-xl shadow-2xs">
            <BookOpen size={15} />
            <span>Thư viện</span>
          </button>
          <button className="inline-flex items-center gap-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold text-[13px] px-4 py-2 rounded-xl">
            <FileText size={15} />
            <span>Hoạt động của phiên</span>
          </button>
        </div>
      </div>

      {/* ── Main 3-Column Layout ── */}
      <div className="grid grid-cols-12 gap-4 items-start">
        {/* ── LEFT COLUMN: Activity List (3 cols) ── */}
        <div className="col-span-3 bg-white rounded-2xl border border-slate-200/80 p-3 space-y-2 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          {/* Search */}
          <div className="relative">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              placeholder="Tìm hoạt động"
              className="w-full pl-8 pr-3 py-1.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-[12.5px] placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1D63F2]"
            />
          </div>

          {/* Filter Chips */}
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center gap-1 bg-[#EFF6FF] text-[#1D63F2] text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full">
              6–8 tuổi
              <X size={11} className="cursor-pointer" />
            </span>
            <span className="inline-flex items-center gap-1 bg-[#EFF6FF] text-[#1D63F2] text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full">
              Khu vườn
              <X size={11} className="cursor-pointer" />
            </span>
          </div>

          {/* Activity Items */}
          <div className="space-y-1.5">
            {ACTIVITIES.map((act) => {
              const isSelected = act.id === selectedId
              return (
                <div
                  key={act.id}
                  onClick={() => setSelectedId(act.id)}
                  className={`flex items-center gap-2.5 p-2 rounded-xl border cursor-pointer transition ${
                    isSelected
                      ? 'border-2 border-[#3B82F6] bg-[#EFF6FF]/70'
                      : 'border-slate-200/80 bg-white hover:bg-slate-50'
                  }`}
                >
                  <img
                    src={act.thumb}
                    alt={act.title}
                    className="w-11 h-11 rounded-lg object-cover border border-slate-100 flex-shrink-0"
                  />
                  <div className="min-w-0">
                    <div className="text-[12.5px] font-bold text-[#0F172A] leading-tight">
                      {act.title}
                    </div>
                    <div className="text-[11px] text-slate-600 mt-0.5 leading-snug">
                      {act.desc}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* ── CENTER COLUMN: Activity Details (4 cols) ── */}
        <div className="col-span-4 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div>
            <h2 className="text-[18.5px] font-extrabold text-[#0F172A]">
              Xếp hình khu vườn từ lá
            </h2>
            <div className="flex flex-wrap items-center gap-2 mt-1.5">
              <span className="inline-flex items-center gap-1 bg-[#DCFCE7] text-[#15803D] text-[11px] font-semibold px-2.5 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]" />
                Thư viện đã duyệt • v1
              </span>
              <span className="inline-flex items-center gap-1 text-[#1D63F2] text-[11.5px] font-semibold">
                <Lightbulb size={13} />
                Gợi ý vì liên quan hình dạng lá
              </span>
            </div>
          </div>

          <div className="rounded-xl overflow-hidden border border-slate-100 h-[170px]">
            <img
              src={offlineLeafCraft}
              alt="Xếp hình khu vườn từ lá"
              className="w-full h-full object-cover"
            />
          </div>

          {/* Mục tiêu hoạt động */}
          <div className="bg-[#EFF6FF]/80 rounded-xl p-3 flex items-start gap-2.5">
            <div className="w-8 h-8 rounded-full bg-white text-[#1D63F2] flex items-center justify-center flex-shrink-0 shadow-2xs">
              <Target size={17} />
            </div>
            <div>
              <h3 className="text-[13.5px] font-extrabold text-[#1D63F2]">
                Mục tiêu hoạt động
              </h3>
              <p className="text-[12.5px] text-slate-700 mt-0.5">
                Quan sát hình dạng và cùng sắp xếp.
              </p>
            </div>
          </div>

          {/* Vật liệu */}
          <div>
            <div className="flex items-center gap-1.5 text-[13.5px] font-extrabold text-[#0F172A]">
              <SproutBadgeIcon size={15} />
              <span>Vật liệu</span>
            </div>
            <p className="text-[12.5px] text-slate-700 mt-1 pl-1">
              Lá sạch, giấy, bút màu.
            </p>
          </div>

          {/* Các bước thực hiện */}
          <div className="pt-1 border-t border-slate-100">
            <div className="flex items-center gap-1.5 text-[13.5px] font-extrabold text-[#0F172A] mb-2">
              <ClipboardCheck size={15} className="text-[#1D63F2]" />
              <span>Các bước thực hiện</span>
            </div>
            <div className="space-y-2 text-[12.5px]">
              <div className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#EFF6FF] text-[#1D63F2] font-bold text-[11px] flex items-center justify-center flex-shrink-0 mt-0.5">
                  1
                </span>
                <div>
                  <div className="font-bold text-[#0F172A]">Quan sát lá</div>
                  <div className="text-[11.5px] text-slate-600">
                    Cùng nhau quan sát hình dạng, màu sắc của các loại lá.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#EFF6FF] text-[#1D63F2] font-bold text-[11px] flex items-center justify-center flex-shrink-0 mt-0.5">
                  2
                </span>
                <div>
                  <div className="font-bold text-[#0F172A]">Cùng sắp xếp</div>
                  <div className="text-[11.5px] text-slate-600">
                    Sắp xếp các chiếc lá thành bức tranh khu vườn theo ý thích.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#EFF6FF] text-[#1D63F2] font-bold text-[11px] flex items-center justify-center flex-shrink-0 mt-0.5">
                  3
                </span>
                <div>
                  <div className="font-bold text-[#0F172A]">Kể về khu vườn</div>
                  <div className="text-[11.5px] text-slate-600">
                    Chia sẻ về bức tranh và những loài cây trong khu vườn.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN: Giao hoạt động (5 cols) ── */}
        <div className="col-span-5 space-y-2.5">
          {/* Card 1: Giao hoạt động */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users size={17} className="text-[#1D63F2]" />
                <h2 className="text-[16.5px] font-extrabold text-[#0F172A]">Giao hoạt động</h2>
              </div>
              <button className="inline-flex items-center justify-center gap-1.5 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[12px] px-3 py-1 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                <Pencil size={12.5} className="shrink-0" />
                <span>Chỉnh bàn giao</span>
              </button>
            </div>

            <div>
              <div className="text-[12.5px] font-bold text-[#1D63F2] mb-1.5">Phạm vi giao</div>
              <div className="grid grid-cols-2 gap-2.5">
                <div
                  onClick={() => setScope('group')}
                  className={`p-2.5 rounded-xl border cursor-pointer transition flex items-center gap-2.5 ${
                    scope === 'group'
                      ? 'border-[#3B82F6] bg-[#EFF6FF]/60'
                      : 'border-slate-200 bg-white'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full ${
                      scope === 'group'
                        ? 'border-4 border-[#1D63F2] bg-white'
                        : 'border border-slate-300'
                    }`}
                  />
                  <LeafBadgeIcon size={24} />
                  <div>
                    <div className="text-[13.5px] font-bold text-[#0F172A]">Nhóm Lá</div>
                    <div className="text-[11.5px] text-slate-500">Mây • Lá</div>
                  </div>
                </div>

                <div
                  onClick={() => setScope('class')}
                  className={`p-2.5 rounded-xl border cursor-pointer transition flex items-center gap-2.5 ${
                    scope === 'class'
                      ? 'border-[#3B82F6] bg-[#EFF6FF]/60'
                      : 'border-slate-200 bg-white'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full ${
                      scope === 'class'
                        ? 'border-4 border-[#1D63F2] bg-white'
                        : 'border border-slate-300'
                    }`}
                  />
                  <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                    <Users size={15} />
                  </div>
                  <div>
                    <div className="text-[13.5px] font-bold text-[#0F172A]">Cả lớp</div>
                    <div className="text-[11.5px] text-slate-500">3 nhóm</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Kiểm tra chuẩn bị */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center gap-2 text-[15.5px] font-extrabold text-[#0F172A]">
              <ClipboardCheck size={17} className="text-[#1D63F2]" />
              <span>Kiểm tra chuẩn bị</span>
            </div>

            <div className="space-y-1.5 text-[12.5px]">
              {[
                {
                  title: 'Vật liệu đã có',
                  sub: 'Lá sạch, giấy, bút màu đã sẵn sàng.',
                },
                {
                  title: 'Không gian phù hợp',
                  sub: 'Có không gian rộng rãi, an toàn.',
                },
                {
                  title: 'Đủ giám sát',
                  sub: 'Giáo viên luôn giám sát trong quá trình hoạt động.',
                },
                {
                  title: 'Phù hợp độ tuổi',
                  sub: 'Nội dung phù hợp với trẻ 6–8 tuổi.',
                },
              ].map((chk) => (
                <div key={chk.title} className="flex items-start gap-2.5">
                  <span className="w-4 h-4 rounded bg-[#16A34A] text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check size={12} strokeWidth={3} />
                  </span>
                  <div>
                    <div className="font-bold text-[#0F172A] leading-tight">{chk.title}</div>
                    <div className="text-[11.5px] text-slate-500">{chk.sub}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-[#DCFCE7]/80 rounded-xl p-2.5 flex items-center gap-2.5">
              <GreenCheckCircle size={18} />
              <div>
                <div className="text-[12.5px] font-bold text-[#15803D]">
                  Giáo viên đã xác nhận
                </div>
                <div className="text-[11px] text-slate-600">
                  Tôi đã kiểm tra và xác nhận các điều kiện trên.
                </div>
              </div>
            </div>

            <div className="space-y-1.5 pt-0.5">
              <button
                onClick={() => navigate('/portfolio/observation')}
                className="w-full flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] py-2 rounded-xl shadow-xs transition cursor-pointer"
              >
                <Play size={14} className="fill-white" />
                <span>Bắt đầu hoạt động</span>
              </button>

              <button className="w-full border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] py-1.5 rounded-xl transition cursor-pointer">
                Chọn hoạt động khác
              </button>

              <div className="flex items-center gap-1.5 text-[11px] text-slate-500 pt-0.5">
                <span className="w-3.5 h-3.5 rounded-full border border-slate-400 text-slate-500 text-[9px] font-bold flex items-center justify-center">
                  i
                </span>
                <span>Nếu thiếu vật liệu hoặc chưa an toàn, quay lại chuẩn bị.</span>
              </div>
            </div>
          </div>

          {/* Card 3: Ghi chú điều chỉnh */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center gap-1.5 text-[13.5px] font-extrabold text-[#0F172A]">
              <FileText size={15} className="text-[#1D63F2]" />
              <span>Ghi chú điều chỉnh của giáo viên</span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Nhập ghi chú (tùy chọn)..."
                className="flex-1 px-3 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-[12.5px] text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#1D63F2]"
              />
              <button className="inline-flex items-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[12.5px] px-3 py-2 rounded-xl transition cursor-pointer flex-shrink-0">
                <Check size={14} />
                <span>Ghi nhận hoàn tất</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
