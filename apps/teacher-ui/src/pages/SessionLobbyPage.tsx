import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Play,
  RotateCcw,
  Clock,
  Users,
  Tablet,
  AlertTriangle,
  QrCode,
  Eye,
  Info,
  Pencil,
} from 'lucide-react'
import {
  GreenCheckCircle,
  CloudBadgeIcon,
  LeafBadgeIcon,
  FlowerBadgeIcon,
  SunBadgeIcon,
  SproutBadgeIcon,
} from '../components/Icons'
import avatarMay from '../assets/avatar-may.png'
import avatarNang from '../assets/avatar-nang.png'
import avatarHoa from '../assets/avatar-hoa.png'
import profileLa from '../assets/profile-la.png'
import { loadActiveSession } from '../services/activeSessionStore'
import { SessionLobbyRuntime } from './SessionLobbyRuntime'

function DemoSessionLobbyPage() {
  const navigate = useNavigate()
  const [activeDrawer, setActiveDrawer] = useState<'may' | 'la'>('may')

  return (
    <div className="px-7 py-6 space-y-5 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Phòng chờ & tiếp nhận
          </h1>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="text-[20px] font-extrabold text-[#0F172A]">
              Khu vườn của chúng mình
            </span>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[13px] font-semibold px-3.5 py-1 rounded-full whitespace-nowrap shrink-0">
              <Clock size={14} className="text-[#D97706] shrink-0" />
              <span>Chờ bắt đầu</span>
            </span>
          </div>

          <div className="flex items-center flex-wrap gap-2.5 mt-3">
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#ECFDF5] text-[#047857] text-[13px] font-semibold px-3.5 py-1 rounded-full whitespace-nowrap shrink-0">
              <SproutBadgeIcon size={15} color="#047857" /> <span>Mầm Xanh</span>
            </span>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#EFF6FF] text-[#1D63F2] text-[13px] font-semibold px-3.5 py-1 rounded-full whitespace-nowrap shrink-0">
              <SproutBadgeIcon size={15} color="#1D63F2" /> <span>Khu vườn của chúng mình</span>
            </span>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[13px] font-medium px-3.5 py-1 rounded-full whitespace-nowrap shrink-0">
              <Users size={14} className="text-slate-500 shrink-0" />
              <span>18 trẻ <span className="mx-0.5">•</span> 3 nhóm</span>
            </span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/session/orchestrate')}
              className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold px-5 py-2.5 rounded-xl text-[14.5px] shadow-xs transition cursor-pointer whitespace-nowrap shrink-0"
            >
              <Play size={17} className="fill-white shrink-0" />
              <span>Bắt đầu phiên</span>
            </button>
            <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2.5 rounded-xl text-[14px] transition cursor-pointer whitespace-nowrap shrink-0">
              <RotateCcw size={16} className="shrink-0" />
              <span>Thu hồi mã tham gia</span>
            </button>
          </div>
          <div className="flex items-center gap-1.5 text-[12.5px] text-slate-500 whitespace-nowrap">
            <div className="w-4 h-4 rounded-full bg-slate-400 text-white text-[10px] font-bold flex items-center justify-center shrink-0">
              i
            </div>
            <span>Trẻ chỉ vào phiên sau khi được tiếp nhận</span>
          </div>
        </div>
      </div>

      {/* ── Main 2-Column Layout ── */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* ── LEFT COLUMN (8 cols) ── */}
        <div className="col-span-8 space-y-5">
          {/* Card 1: Yêu cầu tham gia */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[18px] font-extrabold text-[#0F172A] mb-3.5">
              Yêu cầu tham gia
            </h2>

            <div className="flex items-center bg-[#F8FAFC] rounded-xl px-4 py-2.5 text-[13px] font-medium text-slate-500 mb-2">
              <div className="w-[22%]">Thiết bị</div>
              <div className="w-[16%]">Hồ sơ an toàn</div>
              <div className="w-[16%]">Nhóm đề xuất</div>
              <div className="w-[26%]">Trạng thái</div>
              <div className="w-[20%] text-center">Thao tác</div>
            </div>

            <div className="divide-y divide-slate-100">
              {/* Row 1: Tablet 02 - Lá */}
              <div className="flex items-center px-4 py-4">
                <div className="w-[22%] flex items-center gap-3 pr-2">
                  <Tablet size={22} className="text-slate-700 shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[14.5px] font-bold text-[#0F172A] whitespace-nowrap">Tablet 02</div>
                    <div className="text-[12px] text-slate-500 whitespace-nowrap">Thiết bị trong lớp</div>
                  </div>
                </div>

                <div className="w-[16%] flex items-center gap-2.5 pr-2">
                  <img
                    src={profileLa}
                    alt="Lá"
                    className="w-11 h-12 rounded-xl object-cover border border-slate-100 shrink-0"
                  />
                  <span className="text-[14.5px] font-bold text-[#0F172A] whitespace-nowrap">Lá</span>
                </div>

                <div className="w-[16%] pr-2">
                  <span className="inline-flex items-center gap-1.5 text-[13.5px] text-slate-700 font-medium whitespace-nowrap">
                    <LeafBadgeIcon size={20} />
                    <span>Nhóm Lá</span>
                  </span>
                </div>

                <div className="w-[26%] pr-2">
                  <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                    <GreenCheckCircle size={14} />
                    <span>Đủ điều kiện</span>
                  </span>
                </div>

                <div className="w-[20%] space-y-2">
                  <button className="w-full inline-flex items-center justify-center bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13px] py-2 px-3 rounded-xl transition cursor-pointer whitespace-nowrap">
                    Tiếp nhận
                  </button>
                  <button className="w-full inline-flex items-center justify-center border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] py-2 px-3 rounded-xl transition cursor-pointer whitespace-nowrap">
                    Từ chối
                  </button>
                </div>
              </div>

              {/* Row 2: Tablet 03 - Hoa */}
              <div className="flex items-center px-4 py-4">
                <div className="w-[22%] flex items-center gap-3 pr-2">
                  <Tablet size={22} className="text-slate-700 shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[14.5px] font-bold text-[#0F172A] whitespace-nowrap">Tablet 03</div>
                    <div className="text-[12px] text-slate-500 whitespace-nowrap">Thiết bị trong lớp</div>
                  </div>
                </div>

                <div className="w-[16%] flex items-center gap-2.5 pr-2">
                  <img
                    src={avatarHoa}
                    alt="Hoa"
                    className="w-11 h-12 rounded-xl object-cover border border-slate-100 shrink-0"
                  />
                  <span className="text-[14.5px] font-bold text-[#0F172A] whitespace-nowrap">Hoa</span>
                </div>

                <div className="w-[16%] pr-2">
                  <span className="inline-flex items-center gap-1.5 text-[13.5px] text-slate-700 font-medium whitespace-nowrap">
                    <FlowerBadgeIcon size={20} />
                    <span>Nhóm Hoa</span>
                  </span>
                </div>

                <div className="w-[26%] pr-2">
                  <span className="inline-flex items-center justify-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[12px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                    <AlertTriangle size={14} className="text-[#D97706] shrink-0" />
                    <span>Chờ nhà trường xác minh</span>
                  </span>
                </div>

                <div className="w-[20%] space-y-2">
                  <button
                    disabled
                    className="w-full inline-flex items-center justify-center bg-slate-200 text-slate-500 font-semibold text-[13px] py-2 px-3 rounded-xl cursor-not-allowed whitespace-nowrap"
                  >
                    Tiếp nhận
                  </button>
                  <button
                    onClick={() => navigate('/classes')}
                    className="w-full inline-flex items-center justify-center border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[12px] py-2 px-2 rounded-xl transition cursor-pointer whitespace-nowrap"
                  >
                    Xem việc cần xử lý
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Đã tiếp nhận */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[18px] font-extrabold text-[#0F172A] mb-3.5">Đã tiếp nhận</h2>

            <div className="flex items-center bg-[#F8FAFC] rounded-xl px-4 py-2.5 text-[13px] font-medium text-slate-500 mb-2">
              <div className="w-[18%]">Hồ sơ</div>
              <div className="w-[22%]">Nhóm</div>
              <div className="w-[25%]">Thiết bị</div>
              <div className="w-[22%]">Trạng thái</div>
              <div className="w-[13%] text-right pr-2">Thời điểm</div>
            </div>

            <div className="divide-y divide-slate-100">
              {/* Row 1: Mây */}
              <div className="flex items-center px-4 py-3.5">
                <div className="w-[18%] flex items-center gap-2.5 pr-2">
                  <img
                    src={avatarMay}
                    alt="Mây"
                    className="w-11 h-11 rounded-full object-cover border border-slate-100 shrink-0"
                  />
                  <span className="text-[14.5px] font-bold text-[#0F172A] whitespace-nowrap">Mây</span>
                </div>

                <div className="w-[22%] pr-2">
                  <span className="inline-flex items-center gap-1.5 text-[13.5px] text-slate-700 font-medium whitespace-nowrap">
                    <LeafBadgeIcon size={20} />
                    <span>Nhóm Lá</span>
                  </span>
                </div>

                <div className="w-[25%] flex items-center gap-2.5 pr-2">
                  <Tablet size={19} className="text-slate-700 shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[14px] font-bold text-[#0F172A] whitespace-nowrap">Tablet 01</div>
                    <div className="text-[12px] text-slate-500 whitespace-nowrap">Thiết bị trong lớp</div>
                  </div>
                </div>

                <div className="w-[22%] pr-2">
                  <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                    <span className="w-2 h-2 rounded-full bg-[#16A34A] shrink-0" />
                    <span>Đã tiếp nhận</span>
                  </span>
                </div>

                <div className="w-[13%] text-right pr-2 text-[14px] text-slate-700 font-medium whitespace-nowrap">
                  09:12
                </div>
              </div>

              {/* Row 2: Nắng */}
              <div className="flex items-center px-4 py-3.5">
                <div className="w-[18%] flex items-center gap-2.5 pr-2">
                  <img
                    src={avatarNang}
                    alt="Nắng"
                    className="w-11 h-11 rounded-full object-cover border border-slate-100 shrink-0"
                  />
                  <span className="text-[14.5px] font-bold text-[#0F172A] whitespace-nowrap">Nắng</span>
                </div>

                <div className="w-[22%] pr-2">
                  <span className="inline-flex items-center gap-1.5 text-[13.5px] text-slate-700 font-medium whitespace-nowrap">
                    <SunBadgeIcon size={20} />
                    <span>Nhóm Nắng</span>
                  </span>
                </div>

                <div className="w-[25%] flex items-center gap-2.5 pr-2">
                  <Tablet size={19} className="text-slate-700 shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[14px] font-bold text-[#0F172A] whitespace-nowrap">Tablet 04</div>
                    <div className="text-[12px] text-slate-500 whitespace-nowrap">Thiết bị trong lớp</div>
                  </div>
                </div>

                <div className="w-[22%] pr-2">
                  <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                    <span className="w-2 h-2 rounded-full bg-[#16A34A] shrink-0" />
                    <span>Đã tiếp nhận</span>
                  </span>
                </div>

                <div className="w-[13%] text-right pr-2 text-[14px] text-slate-700 font-medium whitespace-nowrap">
                  09:15
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN (4 cols) ── */}
        <div className="col-span-4 space-y-4">
          {/* Card 1: Mã tham gia phiên */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h3 className="text-[17px] font-extrabold text-[#0F172A] mb-3.5">
              Mã tham gia phiên
            </h3>
            <div className="flex items-start gap-4">
              <div className="w-20 h-20 rounded-2xl bg-[#EFF6FF] flex items-center justify-center text-[#1D63F2] shrink-0">
                <QrCode size={42} />
              </div>
              <div className="space-y-1.5">
                <div className="text-[14px] font-bold text-[#0F172A]">
                  Mã tham gia được quản lý riêng
                </div>
                <p className="text-[12.5px] text-slate-500 leading-relaxed">
                  Giáo viên hiển thị trên lớp khi cần thiết.
                </p>
                <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-4 py-2 rounded-xl mt-1 transition cursor-pointer whitespace-nowrap shrink-0">
                  <Eye size={15} className="shrink-0" />
                  <span>Hiện mã trên lớp</span>
                </button>
              </div>
            </div>
          </div>

          {/* Card 2: Thiết bị dùng chung */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 space-y-4 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between">
              <h3 className="text-[17px] font-extrabold text-[#0F172A]">
                Thiết bị dùng chung
              </h3>
              <Info size={17} className="text-slate-400 shrink-0" />
            </div>

            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-700 shrink-0">
                  <Tablet size={20} />
                </div>
                <div>
                  <div className="text-[14.5px] font-bold text-[#0F172A] whitespace-nowrap">Tablet 01</div>
                  <div className="text-[12px] text-slate-500 whitespace-nowrap">Thiết bị trong lớp</div>
                </div>
              </div>
              <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                <Pencil size={12} className="shrink-0" />
                <span>Trẻ đang vẽ</span>
              </span>
            </div>

            <div>
              <div className="text-[13px] text-slate-600 mb-2">Trẻ đã được tiếp nhận</div>
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 text-[13.5px] font-medium text-[#0F172A]">
                  <CloudBadgeIcon size={22} />
                  Mây
                </span>
                <span className="inline-flex items-center gap-1.5 text-[13.5px] font-medium text-[#0F172A]">
                  <LeafBadgeIcon size={22} />
                  Lá
                </span>
              </div>
            </div>

            <hr className="border-slate-100" />

            <div>
              <div className="text-[13px] text-slate-600 mb-2">Chọn trẻ đang vẽ</div>
              <div className="grid grid-cols-2 gap-2.5">
                <div
                  onClick={() => setActiveDrawer('may')}
                  className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border cursor-pointer transition ${
                    activeDrawer === 'may'
                      ? 'border-[#3B82F6] bg-[#EFF6FF] text-[#1D63F2] font-bold'
                      : 'border-slate-200 bg-white text-slate-700 font-medium'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full border-4 ${
                      activeDrawer === 'may' ? 'border-[#1D63F2] bg-white' : 'border-slate-300'
                    }`}
                  />
                  <CloudBadgeIcon size={18} />
                  <span className="text-[13.5px]">Mây</span>
                </div>

                <div
                  onClick={() => setActiveDrawer('la')}
                  className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border cursor-pointer transition ${
                    activeDrawer === 'la'
                      ? 'border-[#3B82F6] bg-[#EFF6FF] text-[#1D63F2] font-bold'
                      : 'border-slate-200 bg-white text-slate-700 font-medium'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full border ${
                      activeDrawer === 'la'
                        ? 'border-4 border-[#1D63F2] bg-white'
                        : 'border-slate-300'
                    }`}
                  />
                  <LeafBadgeIcon size={18} />
                  <span className="text-[13.5px]">Lá</span>
                </div>
              </div>
              <p className="text-[12px] text-slate-500 mt-2">
                Chọn theo lượt; nét cũ giữ người vẽ.
              </p>
            </div>

            <button className="w-full bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[14px] py-3 rounded-xl transition cursor-pointer">
              Xác nhận thiết bị
            </button>
          </div>

          {/* Card 3: Tình trạng sẵn sàng */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between mb-3.5">
              <h3 className="text-[16.5px] font-extrabold text-[#0F172A]">
                Tình trạng sẵn sàng
              </h3>
              <Info size={17} className="text-slate-400" />
            </div>

            <div className="grid grid-cols-3 gap-2.5">
              <div className="bg-[#ECFDF5] rounded-xl p-3">
                <div className="flex items-center gap-1.5">
                  <Tablet size={16} className="text-[#16A34A]" />
                  <span className="text-[18px] font-extrabold text-[#0F172A]">2</span>
                </div>
                <div className="text-[11.5px] text-slate-600 mt-1">thiết bị sẵn sàng</div>
              </div>

              <div className="bg-[#FEF3C7]/70 rounded-xl p-3">
                <div className="flex items-center gap-1.5">
                  <Clock size={16} className="text-[#D97706]" />
                  <span className="text-[18px] font-extrabold text-[#0F172A]">1</span>
                </div>
                <div className="text-[11.5px] text-slate-600 mt-1">yêu cầu chờ xử lý</div>
              </div>

              <div className="bg-[#EFF6FF] rounded-xl p-3 flex items-center gap-2">
                <Users size={18} className="text-[#1D63F2] flex-shrink-0" />
                <div className="text-[11px] text-slate-700 leading-tight font-medium">
                  Giáo viên quyết định khi bắt đầu
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function SessionLobbyPage() {
  const activeSession = loadActiveSession()
  if (activeSession) return <SessionLobbyRuntime />
  if (new URLSearchParams(window.location.search).get('demo') === '1') return <DemoSessionLobbyPage />
  return <main className="m-7 rounded-2xl border border-slate-200 bg-white p-7"><h1 className="text-2xl font-bold text-slate-900">Chưa có phiên lớp đang mở</h1><p className="mt-2 text-sm text-slate-600">Tạo phiên và mở phòng chờ qua BE1 từ Thiết lập phiên học. Giao diện mẫu chỉ mở khi thêm ?demo=1 vào đường dẫn.</p></main>
}
