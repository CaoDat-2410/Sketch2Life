import { useNavigate } from 'react-router-dom'
import {
  PlusCircle,
  Users,
  PlayCircle,
  FileText,
  AlertTriangle,
  ChevronRight,
  Info,
  Contact,
} from 'lucide-react'
import {
  CloudBadgeIcon,
  LeafBadgeIcon,
  FlowerBadgeIcon,
  SunBadgeIcon,
} from '../components/Icons'
import artSprout from '../assets/art-sprout.png'
import artFlowers from '../assets/art-flowers.png'

export function HomePage() {
  const navigate = useNavigate()

  return (
    <div className="px-7 py-6 space-y-5 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Chào cô/thầy
          </h1>
          <p className="text-[15.5px] text-slate-600 mt-1">
            Một nơi để chuẩn bị và đồng hành cùng lớp
          </p>
        </div>
        <button
          onClick={() => navigate('/session/setup')}
          className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold px-5 py-3 rounded-xl text-[14.5px] shadow-sm transition cursor-pointer whitespace-nowrap shrink-0"
        >
          <PlusCircle size={18} className="shrink-0" />
          <span>Tạo phiên học</span>
        </button>
      </div>

      {/* ── 4 Stat Cards ── */}
      <div className="grid grid-cols-4 gap-4">
        <div
          onClick={() => navigate('/classes')}
          className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)] cursor-pointer hover:border-blue-200 transition"
        >
          <div className="w-12 h-12 rounded-full bg-[#E0F2FE] flex items-center justify-center text-[#0284C7] flex-shrink-0">
            <Users size={23} />
          </div>
          <div>
            <div className="text-[26px] font-extrabold text-[#0F172A] leading-tight">1</div>
            <div className="text-[13.5px] text-slate-600">lớp được phân công</div>
          </div>
        </div>

        <div
          onClick={() => navigate('/session/orchestrate')}
          className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)] cursor-pointer hover:border-emerald-200 transition"
        >
          <div className="w-12 h-12 rounded-full bg-[#DCFCE7] flex items-center justify-center text-[#16A34A] flex-shrink-0">
            <PlayCircle size={23} />
          </div>
          <div>
            <div className="text-[26px] font-extrabold text-[#0F172A] leading-tight">1</div>
            <div className="text-[13.5px] text-slate-600">phiên đang học</div>
          </div>
        </div>

        <div
          onClick={() => navigate('/ai-review')}
          className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)] cursor-pointer hover:border-rose-200 transition"
        >
          <div className="w-12 h-12 rounded-full bg-[#FFE4E6] flex items-center justify-center text-[#E11D48] flex-shrink-0">
            <FileText size={22} />
          </div>
          <div>
            <div className="text-[26px] font-extrabold text-[#0F172A] leading-tight">2</div>
            <div className="text-[13.5px] text-slate-600">gợi ý chờ duyệt</div>
          </div>
        </div>

        <div
          onClick={() => navigate('/session/orchestrate')}
          className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)] cursor-pointer hover:border-amber-200 transition"
        >
          <div className="w-12 h-12 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706] flex-shrink-0">
            <AlertTriangle size={22} />
          </div>
          <div>
            <div className="text-[26px] font-extrabold text-[#0F172A] leading-tight">1</div>
            <div className="text-[13.5px] text-slate-600">việc cần hỗ trợ</div>
          </div>
        </div>
      </div>

      {/* ── Middle 2-Column Section ── */}
      <div className="grid grid-cols-12 gap-5">
        {/* Left: Lớp của tôi & Phiên hiện hành */}
        <div className="col-span-8 bg-white rounded-2xl border border-slate-200/80 p-5 space-y-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          {/* Lớp của tôi */}
          <div>
            <h2 className="text-[17px] font-bold text-[#0F172A] mb-3">Lớp của tôi</h2>
            <div className="border border-slate-200/80 rounded-2xl p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <img
                  src={artSprout}
                  alt="Lớp Mầm Xanh"
                  className="w-[128px] h-[118px] rounded-xl object-cover border border-slate-100 flex-shrink-0"
                />
                <div>
                  <h3 className="text-[18px] font-bold text-[#0F172A]">Lớp Mầm Xanh</h3>
                  <div className="flex items-center flex-wrap gap-2 mt-2">
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <Contact size={14} className="text-slate-500 shrink-0" />
                      <span>18 hồ sơ</span>
                    </span>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <Users size={14} className="text-slate-500 shrink-0" />
                      <span>Nhóm tuổi 6–8</span>
                    </span>
                  </div>

                  <p className="text-[12.5px] text-slate-500 mt-3 mb-1.5">Các nhóm trong lớp</p>
                  <div className="flex items-center flex-wrap gap-2">
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <LeafBadgeIcon size={16} />
                      <span>Nhóm Lá</span>
                    </span>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <FlowerBadgeIcon size={16} />
                      <span>Nhóm Hoa</span>
                    </span>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <SunBadgeIcon size={16} />
                      <span>Nhóm Nắng</span>
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => navigate('/classes')}
                className="inline-flex items-center justify-center gap-1.5 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
              >
                <span>Mở lớp</span>
                <ChevronRight size={16} className="shrink-0" />
              </button>
            </div>
          </div>

          {/* Phiên hiện hành */}
          <div>
            <h2 className="text-[17px] font-bold text-[#0F172A] mb-3">Phiên hiện hành</h2>
            <div className="border border-slate-200/80 rounded-2xl p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <img
                  src={artFlowers}
                  alt="Khu vườn của chúng mình"
                  className="w-[128px] h-[96px] rounded-xl object-cover border border-slate-100 flex-shrink-0"
                />
                <div>
                  <div className="flex items-center gap-2.5">
                    <h3 className="text-[17.5px] font-bold text-[#0F172A]">
                      Khu vườn của chúng mình
                    </h3>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <span className="w-2 h-2 rounded-full bg-[#16A34A] shrink-0" />
                      <span>Đang học</span>
                    </span>
                  </div>

                  <div className="mt-2">
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <Users size={14} className="text-slate-500 shrink-0" />
                      <span>18 trẻ <span className="mx-0.5">•</span> 3 nhóm</span>
                    </span>
                  </div>

                  <div className="flex items-center flex-wrap gap-2 mt-2.5">
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                      <CloudBadgeIcon size={16} /> <span>Mây</span>
                    </span>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                      <LeafBadgeIcon size={16} /> <span>Lá</span>
                    </span>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                      <FlowerBadgeIcon size={16} /> <span>Hoa</span>
                    </span>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12.5px] font-medium px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                      <SunBadgeIcon size={16} /> <span>Nắng</span>
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => navigate('/session/orchestrate')}
                className="inline-flex items-center justify-center gap-1.5 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] px-4 py-2.5 rounded-xl shadow-xs transition cursor-pointer whitespace-nowrap shrink-0"
              >
                <span>Tiếp tục điều phối</span>
                <ChevronRight size={16} className="shrink-0" />
              </button>
            </div>
          </div>
        </div>

        {/* Right: Việc cần xử lý */}
        <div className="col-span-4 bg-white rounded-2xl border border-slate-200/80 p-5 flex flex-col justify-between shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div>
            <h2 className="text-[17px] font-bold text-[#0F172A] pb-3 border-b border-slate-100">
              Việc cần xử lý
            </h2>

            <div className="divide-y divide-slate-100">
              {/* Item 1 */}
              <div
                onClick={() => navigate('/ai-review')}
                className="py-4 flex items-center justify-between gap-3 cursor-pointer hover:bg-slate-50/70 rounded-xl px-2 -mx-2 transition"
              >
                <div className="flex items-start gap-3.5">
                  <div className="w-11 h-11 rounded-full bg-[#FFE4E6] flex items-center justify-center text-[#E11D48] flex-shrink-0 mt-0.5">
                    <FileText size={20} />
                  </div>
                  <div>
                    <h4 className="text-[14.5px] font-bold text-[#0F172A]">
                      Duyệt gợi ý của Mây
                    </h4>
                    <p className="text-[13px] text-slate-500 mt-1 leading-relaxed">
                      Mây đã gửi gợi ý cho hoạt động tạo khu vườn bằng lá.
                    </p>
                  </div>
                </div>
                <ChevronRight size={18} className="text-slate-400 flex-shrink-0" />
              </div>

              {/* Item 2 */}
              <div
                onClick={() => navigate('/session/orchestrate')}
                className="py-4 flex items-center justify-between gap-3 cursor-pointer hover:bg-slate-50/70 rounded-xl px-2 -mx-2 transition"
              >
                <div className="flex items-start gap-3.5">
                  <div className="w-11 h-11 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706] flex-shrink-0 mt-0.5">
                    <AlertTriangle size={20} />
                  </div>
                  <div>
                    <h4 className="text-[14.5px] font-bold text-[#0F172A] leading-snug">
                      Kiểm tra chuẩn bị hoạt động Nhóm Hoa
                    </h4>
                    <p className="text-[13px] text-slate-500 mt-1 leading-relaxed">
                      Cần kiểm tra vật liệu và cách tổ chức hoạt động cho Nhóm Hoa.
                    </p>
                  </div>
                </div>
                <ChevronRight size={18} className="text-slate-400 flex-shrink-0" />
              </div>
            </div>
          </div>

          <button
            onClick={() => navigate('/ai-review')}
            className="w-full flex items-center justify-center gap-1.5 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[13.5px] py-2.5 rounded-xl transition cursor-pointer mt-2"
          >
            <span>Mở danh sách</span>
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* ── Bottom Section: Phiên gần đây ── */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
        <div className="flex items-center justify-between mb-3.5">
          <h2 className="text-[17px] font-bold text-[#0F172A]">Phiên gần đây</h2>
          <div className="flex items-center gap-1.5 text-[12.5px] text-slate-500">
            <Info size={14} className="text-slate-400" />
            <span>Chỉ hiển thị lớp và phiên được phân công</span>
          </div>
        </div>

        <div className="overflow-hidden rounded-xl border border-slate-100">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#F8FAFC] text-[13px] font-medium text-slate-500 border-b border-slate-100">
                <th className="py-3 px-4">Tên phiên</th>
                <th className="py-3 px-4">Chủ đề</th>
                <th className="py-3 px-4">Nhóm tuổi</th>
                <th className="py-3 px-4">Kết quả</th>
                <th className="py-3 px-4">Hành động</th>
                <th className="py-3 px-4">Xem kết quả</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-[14px]">
              {/* Row 1 */}
              <tr className="hover:bg-slate-50/60 transition">
                <td className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <img
                      src={artSprout}
                      alt="Màu sắc của lá"
                      className="w-11 h-9 rounded-lg object-cover border border-slate-200"
                    />
                    <span className="font-bold text-[#0F172A]">Màu sắc của lá</span>
                  </div>
                </td>
                <td className="py-3 px-4 text-slate-600">Thế giới thực vật</td>
                <td className="py-3 px-4 text-slate-600">6–8</td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <span className="inline-flex items-center gap-2 text-[#15803D] font-medium whitespace-nowrap">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#16A34A] shrink-0" />
                    <span>Đã hoàn tất</span>
                  </span>
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <button
                    onClick={() => navigate('/session/orchestrate')}
                    className="inline-flex items-center justify-center gap-1.5 w-28 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[13px] px-3.5 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap"
                  >
                    <span>Mở lại</span>
                    <ChevronRight size={15} className="shrink-0" />
                  </button>
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <button
                    onClick={() => navigate('/portfolio/observation')}
                    className="inline-flex items-center justify-center gap-1 text-[#1D63F2] hover:underline font-semibold text-[13.5px] cursor-pointer whitespace-nowrap"
                  >
                    <span>Xem kết quả</span>
                    <ChevronRight size={15} className="shrink-0" />
                  </button>
                </td>
              </tr>

              {/* Row 2 */}
              <tr className="hover:bg-slate-50/60 transition">
                <td className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <img
                      src={artFlowers}
                      alt="Khu vườn nhỏ"
                      className="w-11 h-9 rounded-lg object-cover border border-slate-200 shrink-0"
                    />
                    <span className="font-bold text-[#0F172A] whitespace-nowrap">Khu vườn nhỏ</span>
                  </div>
                </td>
                <td className="py-3 px-4 text-slate-600 whitespace-nowrap">Khu vườn</td>
                <td className="py-3 px-4 text-slate-600 whitespace-nowrap">6–8</td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <span className="inline-flex items-center gap-2 text-slate-700 font-medium whitespace-nowrap">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B] shrink-0" />
                    <span>Đã lưu nháp</span>
                  </span>
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <button
                    onClick={() => navigate('/session/setup')}
                    className="inline-flex items-center justify-center gap-1.5 w-28 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[13px] px-3.5 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap"
                  >
                    <span>Tiếp tục</span>
                    <ChevronRight size={15} className="shrink-0" />
                  </button>
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <button
                    onClick={() => navigate('/portfolio/observation')}
                    className="inline-flex items-center justify-center gap-1 text-[#1D63F2] hover:underline font-semibold text-[13.5px] cursor-pointer whitespace-nowrap"
                  >
                    <span>Xem kết quả</span>
                    <ChevronRight size={15} className="shrink-0" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
