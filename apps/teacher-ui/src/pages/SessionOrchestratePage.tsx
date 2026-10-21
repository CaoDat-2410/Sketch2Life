import { useNavigate } from 'react-router-dom'
import {
  Pause,
  FileText,
  CornerUpRight,
  Square,
  Users,
  AlertTriangle,
  Cloud,
  ChevronRight,
  MessageSquare,
  Flag,
  Sprout,
  Laptop,
  Play,
} from 'lucide-react'
import {
  CloudBadgeIcon,
  LeafBadgeIcon,
  FlowerBadgeIcon,
  SunBadgeIcon,
  SproutBadgeIcon,
} from '../components/Icons'
import artSprout from '../assets/art-sprout.png'
import artFlowers from '../assets/art-flowers.png'
import artSun from '../assets/art-sun.png'

export function SessionOrchestratePage() {
  const navigate = useNavigate()

  return (
    <div className="px-7 py-6 space-y-5 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Điều phối lớp
          </h1>
          <div className="text-[20px] font-extrabold text-[#0F172A] mt-1">
            Khu vườn của chúng mình
          </div>

          <div className="flex items-center flex-wrap gap-2.5 mt-3">
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[13px] font-semibold px-3.5 py-1 rounded-full whitespace-nowrap shrink-0">
              <span className="w-2 h-2 rounded-full bg-[#16A34A] shrink-0" />
              <span>Phiên đang học</span>
            </span>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#EFF6FF] text-[#1D63F2] text-[13px] font-semibold px-3.5 py-1 rounded-full whitespace-nowrap shrink-0">
              <SproutBadgeIcon size={15} color="#1D63F2" /> <span>Khám phá & vẽ</span>
            </span>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[13px] font-medium px-3.5 py-1 rounded-full whitespace-nowrap shrink-0">
              <Users size={14} className="text-slate-500 shrink-0" />
              <span>18 trẻ <span className="mx-0.5">•</span> 3 nhóm</span>
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 shrink-0">
          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2.5 rounded-xl text-[14px] transition cursor-pointer whitespace-nowrap shrink-0">
            <Pause size={16} className="fill-[#1D63F2] shrink-0" />
            <span>Tạm dừng</span>
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2.5 rounded-xl text-[14px] transition cursor-pointer whitespace-nowrap shrink-0">
            <FileText size={16} className="shrink-0" />
            <span>Lưu nháp</span>
          </button>
          <button
            onClick={() => navigate('/library/gallery')}
            className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold px-4 py-2.5 rounded-xl text-[14px] shadow-xs transition cursor-pointer whitespace-nowrap shrink-0"
          >
            <CornerUpRight size={16} className="shrink-0" />
            <span>Chuyển hoạt động</span>
          </button>
          <button
            onClick={() => navigate('/portfolio/observation')}
            className="inline-flex items-center justify-center gap-2 border border-red-300 bg-white hover:bg-red-50 text-red-600 font-semibold px-4 py-2.5 rounded-xl text-[14px] transition cursor-pointer whitespace-nowrap shrink-0"
          >
            <Square size={15} className="shrink-0" />
            <span>Kết thúc sớm</span>
          </button>
        </div>
      </div>

      {/* ── 4 Stat Cards ── */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="w-12 h-12 rounded-full bg-[#E0F2FE] flex items-center justify-center text-[#0284C7] flex-shrink-0">
            <Users size={22} />
          </div>
          <div>
            <div className="text-[26px] font-extrabold text-[#0F172A] leading-tight">3</div>
            <div className="text-[13.5px] text-slate-600">nhóm đang vẽ</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="w-12 h-12 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706] flex-shrink-0">
            <AlertTriangle size={22} />
          </div>
          <div>
            <div className="text-[26px] font-extrabold text-[#0F172A] leading-tight">2</div>
            <div className="text-[13.5px] text-slate-600">cần hỗ trợ</div>
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

        <div className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="w-12 h-12 rounded-full bg-[#DCFCE7] flex items-center justify-center text-[#16A34A] flex-shrink-0">
            <Cloud size={22} />
          </div>
          <div>
            <div className="text-[16px] font-extrabold text-[#0F172A] leading-tight">
              Đã lưu trên hệ thống
            </div>
            <div className="text-[13px] text-slate-500 mt-0.5">Cập nhật vừa xong</div>
          </div>
        </div>
      </div>

      {/* ── Middle 2-Column Layout ── */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* ── LEFT COLUMN: Tiến độ từng nhóm (8 cols) ── */}
        <div className="col-span-8 bg-white rounded-2xl border border-slate-200/80 p-5 space-y-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <h2 className="text-[18px] font-extrabold text-[#0F172A]">Tiến độ từng nhóm</h2>

          <div className="space-y-3.5">
            {/* Group 1: Nhóm Lá */}
            <div className="border border-slate-200/80 rounded-2xl p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <img
                  src={artSprout}
                  alt="Nhóm Lá"
                  className="w-[120px] h-[100px] rounded-xl object-cover border border-slate-100 shrink-0"
                />
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <h3 className="text-[17.5px] font-bold text-[#0F172A] whitespace-nowrap">Nhóm Lá</h3>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#EFF6FF] text-[#1D63F2] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <span className="w-2 h-2 rounded-full bg-[#1D63F2] shrink-0" />
                      <span>Đang vẽ</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[13.5px] text-slate-700 font-medium whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5">
                      <CloudBadgeIcon size={20} />
                      <span>Mây</span>
                    </span>
                    <span className="text-slate-400">•</span>
                    <span className="inline-flex items-center gap-1.5">
                      <LeafBadgeIcon size={20} />
                      <span>Lá</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[13.5px] text-slate-600">
                    <Sprout size={15} className="text-slate-500 shrink-0" />
                    <span>Đang khám phá ý tưởng</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => navigate('/session/group')}
                className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
              >
                <span>Mở nhóm</span>
                <ChevronRight size={16} className="shrink-0" />
              </button>
            </div>

            {/* Group 2: Nhóm Hoa */}
            <div className="border border-slate-200/80 rounded-2xl p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <img
                  src={artFlowers}
                  alt="Nhóm Hoa"
                  className="w-[120px] h-[100px] rounded-xl object-cover border border-slate-100 shrink-0"
                />
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <h3 className="text-[17.5px] font-bold text-[#0F172A] whitespace-nowrap">Nhóm Hoa</h3>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <span className="w-2 h-2 rounded-full bg-[#D97706] shrink-0" />
                      <span>Cần hỗ trợ</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[13.5px] text-slate-700 font-medium whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5">
                      <FlowerBadgeIcon size={20} />
                      <span>Hoa</span>
                    </span>
                    <span className="text-slate-400">•</span>
                    <span className="inline-flex items-center gap-1.5">
                      <SunBadgeIcon size={20} />
                      <span>Nắng</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[13.5px] text-slate-600">
                    <MessageSquare size={15} className="text-slate-500 shrink-0" />
                    <span>Xin cô/thầy hỗ trợ nét vẽ</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => navigate('/session/group')}
                className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] px-4 py-2.5 rounded-xl shadow-xs transition cursor-pointer whitespace-nowrap shrink-0"
              >
                <span>Hỗ trợ nhóm</span>
                <ChevronRight size={16} className="shrink-0" />
              </button>
            </div>

            {/* Group 3: Nhóm Nắng */}
            <div className="border border-slate-200/80 rounded-2xl p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <img
                  src={artSun}
                  alt="Nhóm Nắng"
                  className="w-[120px] h-[100px] rounded-xl object-cover border border-slate-100 shrink-0"
                />
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <h3 className="text-[17.5px] font-bold text-[#0F172A] whitespace-nowrap">Nhóm Nắng</h3>
                    <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                      <span className="w-2 h-2 rounded-full bg-[#16A34A] shrink-0" />
                      <span>Sẵn sàng chia sẻ</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[13.5px] text-slate-700 font-medium whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5">
                      <SunBadgeIcon size={20} />
                      <span>Nắng</span>
                    </span>
                    <span className="text-slate-400">•</span>
                    <span className="inline-flex items-center gap-1.5">
                      <LeafBadgeIcon size={20} />
                      <span>Lá</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[13.5px] text-slate-600">
                    <Flag size={15} className="text-slate-500 shrink-0" />
                    <span>Chờ giáo viên điều phối</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => navigate('/session/group')}
                className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
              >
                <span>Mở nhóm</span>
                <ChevronRight size={16} className="shrink-0" />
              </button>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN (4 cols) ── */}
        <div className="col-span-4 space-y-4">
          {/* Card 1: Việc cần xử lý */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[18px] font-extrabold text-[#0F172A] mb-3.5">Việc cần xử lý</h2>

            <div className="divide-y divide-slate-100">
              {/* Item 1 */}
              <div className="pb-4 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-3">
                    <div className="w-11 h-11 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706] flex-shrink-0">
                      <AlertTriangle size={20} />
                    </div>
                    <div>
                      <div className="text-[14.5px] font-bold text-[#0F172A]">
                        Nhóm Hoa cần hỗ trợ
                      </div>
                      <div className="text-[13px] text-slate-500 mt-0.5">
                        Xin cô/thầy hỗ trợ nét vẽ
                      </div>
                    </div>
                  </div>
                  <span className="text-[12px] text-slate-400 flex-shrink-0">Vừa gửi</span>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => navigate('/session/group')}
                    className="inline-flex items-center justify-center gap-1 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[12.5px] px-3.5 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
                  >
                    <span>Xem nhóm</span>
                    <ChevronRight size={14} className="shrink-0" />
                  </button>
                </div>
              </div>

              {/* Item 2 */}
              <div className="pt-4 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-3">
                    <div className="w-11 h-11 rounded-full bg-[#FFE4E6] flex items-center justify-center text-[#E11D48] shrink-0">
                      <FileText size={20} />
                    </div>
                    <div>
                      <div className="text-[14.5px] font-bold text-[#0F172A]">
                        Gợi ý AI của Mây chờ duyệt
                      </div>
                      <div className="text-[13px] text-slate-500 mt-0.5">
                        Gợi ý cách vẽ chiếc lá
                      </div>
                    </div>
                  </div>
                  <span className="text-[12px] text-slate-400 shrink-0 whitespace-nowrap">2 phút trước</span>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => navigate('/ai-review')}
                    className="inline-flex items-center justify-center gap-1 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[12.5px] px-3.5 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
                  >
                    <span>Duyệt từng gợi ý</span>
                    <ChevronRight size={14} className="shrink-0" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Kết nối & lưu tranh */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 space-y-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[18px] font-extrabold text-[#0F172A]">Kết nối & lưu tranh</h2>

            <div className="flex items-center justify-between py-1.5 cursor-pointer hover:bg-slate-50 rounded-xl px-1 -mx-1">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#DCFCE7] flex items-center justify-center text-[#16A34A] shrink-0">
                  <Laptop size={16} />
                </div>
                <span className="text-[14px] font-medium text-slate-700">
                  Các thiết bị đang kết nối
                </span>
              </div>
              <ChevronRight size={17} className="text-slate-400 shrink-0" />
            </div>

            <div className="flex items-center justify-between gap-2 pt-1">
              <div className="flex items-center gap-3 pl-1.5">
                <span className="w-3 h-3 rounded-full bg-[#F59E0B] shrink-0" />
                <span className="text-[14px] font-medium text-slate-700">
                  1 bản nháp chưa gửi
                </span>
              </div>
              <button className="inline-flex items-center justify-center border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[12.5px] px-3.5 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
                Xem bản nháp
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Card: Video kiến thức ── */}
      <div className="bg-white rounded-2xl border border-slate-200/80 px-6 py-4 flex items-center justify-between gap-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[#F3E8FF] flex items-center justify-center shrink-0">
            <div className="w-6 h-6 rounded-full bg-[#7C3AED] flex items-center justify-center text-white">
              <Play size={12} className="fill-white ml-0.5" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h3 className="text-[17.5px] font-extrabold text-[#0F172A] whitespace-nowrap">Video kiến thức</h3>
              <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-600 text-[12.5px] font-medium px-3 py-0.5 rounded-full whitespace-nowrap shrink-0">
                <span className="w-2 h-2 rounded-full border border-slate-400 shrink-0" />
                <span>Chưa chuẩn bị</span>
              </span>
            </div>
            <p className="text-[13.5px] text-slate-500 mt-0.5">
              Chọn video ngắn phù hợp với chủ đề để chia sẻ cho cả lớp.
            </p>
          </div>
        </div>

        <button
          onClick={() => navigate('/session/video')}
          className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
        >
          <span>Mở duyệt video</span>
          <ChevronRight size={16} className="shrink-0" />
        </button>
      </div>
    </div>
  )
}
