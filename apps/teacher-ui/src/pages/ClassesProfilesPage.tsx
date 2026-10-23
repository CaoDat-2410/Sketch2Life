import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  UserPlus,
  Info,
  Search,
  ChevronDown,
  Shield,
  Users,
  AlertTriangle,
  ChevronRight,
  X,
  Pencil,
  MinusCircle,
  Image as ImageIcon,
  Sparkles,
  FileText,
  Sprout,
} from 'lucide-react'
import {
  GreenCheckCircle,
  LeafBadgeIcon,
  SunBadgeIcon,
  SproutBadgeIcon,
} from '../components/Icons'
import avatarMay from '../assets/avatar-may.png'
import avatarLa from '../assets/avatar-la.png'
import avatarNang from '../assets/avatar-nang.png'
import profileLa from '../assets/profile-la.png'

interface ChildProfile {
  id: string
  name: string
  group: string
  groupType: 'sprout' | 'leaf' | 'sun'
  age: string
  avatar: string
  profileImg: string
  scopeStatus: 'ok' | 'pending' | 'missing_ai'
  scopeLabel: string
}

const PROFILES: ChildProfile[] = [
  {
    id: 'may',
    name: 'Mây',
    group: 'Nhóm Lá',
    groupType: 'sprout',
    age: '7 tuổi 2 tháng',
    avatar: avatarMay,
    profileImg: avatarMay,
    scopeStatus: 'ok',
    scopeLabel: 'Đủ phạm vi',
  },
  {
    id: 'la',
    name: 'Lá',
    group: 'Nhóm Lá',
    groupType: 'leaf',
    age: '6 tuổi 8 tháng',
    avatar: avatarLa,
    profileImg: profileLa,
    scopeStatus: 'pending',
    scopeLabel: 'Chờ xác minh',
  },
  {
    id: 'nang',
    name: 'Nắng',
    group: 'Nhóm Nắng',
    groupType: 'sun',
    age: '8 tuổi 1 tháng',
    avatar: avatarNang,
    profileImg: avatarNang,
    scopeStatus: 'missing_ai',
    scopeLabel: 'Thiếu phạm vi AI',
  },
]

function renderGroupIcon(type: 'sprout' | 'leaf' | 'sun') {
  if (type === 'sprout') return <SproutBadgeIcon size={15} />
  if (type === 'leaf') return <LeafBadgeIcon size={16} />
  return <SunBadgeIcon size={16} />
}

export function ClassesProfilesPage() {
  const navigate = useNavigate()
  const [selectedId, setSelectedId] = useState<string>('la')
  const [search, setSearch] = useState('')

  const selected = PROFILES.find((p) => p.id === selectedId) ?? PROFILES[1]

  return (
    <div className="px-7 py-6 space-y-5 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[28px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Lớp học & hồ sơ trẻ
          </h1>
          <p className="text-[15.5px] text-slate-600 mt-1">
            Lớp Mầm Xanh <span className="mx-1">•</span> Hồ sơ do giáo viên quản lý
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold px-4 py-2.5 rounded-xl text-[14px] shadow-xs transition cursor-pointer whitespace-nowrap shrink-0">
            <UserPlus size={18} className="shrink-0" />
            <span>Thêm hồ sơ</span>
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2.5 rounded-xl text-[14px] transition cursor-pointer whitespace-nowrap shrink-0">
            <Info size={18} className="shrink-0" />
            <span>Thông tin lớp</span>
          </button>
        </div>
      </div>

      {/* ── Main 2-Column Layout ── */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* ── LEFT COLUMN (8 cols) ── */}
        <div className="col-span-8 space-y-4">
          {/* Search & Filters */}
          <div className="grid grid-cols-12 gap-3">
            <div className="col-span-5 relative">
              <Search
                size={18}
                className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Tìm biệt danh"
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200/90 rounded-xl text-[14px] text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1D63F2]"
              />
            </div>

            <div className="col-span-3">
              <button className="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 bg-white border border-slate-200/90 rounded-xl text-[13.5px] font-medium text-slate-700 hover:bg-slate-50 whitespace-nowrap">
                <span className="flex items-center gap-2 whitespace-nowrap">
                  <Sprout size={16} className="text-slate-500 shrink-0" />
                  <span>Đang tham gia</span>
                </span>
                <ChevronDown size={16} className="text-slate-500 shrink-0" />
              </button>
            </div>

            <div className="col-span-4">
              <button className="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 bg-white border border-slate-200/90 rounded-xl text-[13.5px] font-medium text-slate-700 hover:bg-slate-50 whitespace-nowrap">
                <span className="flex items-center gap-2 whitespace-nowrap">
                  <Shield size={16} className="text-slate-500 shrink-0" />
                  <span>Trạng thái đồng ý</span>
                </span>
                <ChevronDown size={16} className="text-slate-500 shrink-0" />
              </button>
            </div>
          </div>

          {/* 3 Stat Cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
              <div className="w-12 h-12 rounded-full bg-[#E0F2FE] flex items-center justify-center text-[#0284C7] flex-shrink-0">
                <Users size={22} />
              </div>
              <div>
                <div className="text-[25px] font-extrabold text-[#0F172A] leading-tight">18</div>
                <div className="text-[13.5px] text-slate-600">hồ sơ</div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
              <div className="w-12 h-12 rounded-full bg-[#DCFCE7] flex items-center justify-center text-[#16A34A] flex-shrink-0">
                <GreenCheckCircle size={22} />
              </div>
              <div>
                <div className="text-[25px] font-extrabold text-[#0F172A] leading-tight">16</div>
                <div className="text-[13.5px] text-slate-600">đủ phạm vi cho phiên</div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 px-5 py-4 flex items-center gap-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
              <div className="w-12 h-12 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706] flex-shrink-0">
                <AlertTriangle size={22} />
              </div>
              <div>
                <div className="text-[25px] font-extrabold text-[#0F172A] leading-tight">2</div>
                <div className="text-[13.5px] text-slate-600">cần nhà trường xử lý</div>
              </div>
            </div>
          </div>

          {/* Danh sách hồ sơ trẻ */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h2 className="text-[18px] font-bold text-[#0F172A] mb-3.5">Danh sách hồ sơ trẻ</h2>

            {/* Table Header */}
            <div className="flex items-center bg-[#F8FAFC] rounded-xl px-4 py-2.5 text-[13px] font-medium text-slate-500 mb-2">
              <div className="w-[23%]">Hồ sơ</div>
              <div className="w-[19%]">Tuổi đã xác nhận</div>
              <div className="w-[16%]">Ghi danh</div>
              <div className="w-[22%]">Phạm vi xử lý</div>
              <div className="w-[20%] text-right pr-2">Hành động</div>
            </div>

            {/* Rows */}
            <div className="space-y-2">
              {PROFILES.filter((p) =>
                p.name.toLowerCase().includes(search.toLowerCase())
              ).map((profile) => {
                const isSelected = profile.id === selectedId
                return (
                  <div
                    key={profile.id}
                    onClick={() => setSelectedId(profile.id)}
                    className={`flex items-center px-4 py-3 rounded-2xl transition cursor-pointer border ${
                      isSelected
                        ? 'bg-[#F0F7FF] border-[#3B82F6] shadow-xs'
                        : 'bg-white border-transparent hover:bg-slate-50/80'
                    }`}
                  >
                    {/* Hồ sơ */}
                    <div className="w-[23%] flex items-center gap-3 pr-2">
                      <img
                        src={profile.avatar}
                        alt={profile.name}
                        className="w-12 h-12 rounded-full object-cover border border-slate-200/60 shrink-0"
                      />
                      <div className="min-w-0">
                        <div className="text-[15.5px] font-bold text-[#0F172A] whitespace-nowrap">
                          {profile.name}
                        </div>
                        <div className="text-[12.5px] text-slate-600 flex items-center gap-1.5 mt-0.5 whitespace-nowrap">
                          {renderGroupIcon(profile.groupType)}
                          <span>{profile.group}</span>
                        </div>
                      </div>
                    </div>

                    {/* Tuổi đã xác nhận */}
                    <div className="w-[19%] text-[14px] text-slate-700 font-medium whitespace-nowrap">
                      {profile.age}
                    </div>

                    {/* Ghi danh */}
                    <div className="w-[16%]">
                      <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                        <span className="w-2 h-2 rounded-full bg-[#16A34A] shrink-0" />
                        <span>Đang học</span>
                      </span>
                    </div>

                    {/* Phạm vi xử lý */}
                    <div className="w-[22%]">
                      {profile.scopeStatus === 'ok' ? (
                        <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                          <GreenCheckCircle size={14} />
                          <span>{profile.scopeLabel}</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center justify-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                          <AlertTriangle size={13.5} className="text-[#D97706] shrink-0" />
                          <span>{profile.scopeLabel}</span>
                        </span>
                      )}
                    </div>

                    {/* Hành động */}
                    <div className="w-[20%] flex justify-end">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate('/portfolio')
                        }}
                        className="inline-flex items-center justify-center gap-1.5 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-3.5 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
                      >
                        <span>Xem hồ sơ</span>
                        <ChevronRight size={14} className="shrink-0" />
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Info Note Banner */}
          <div className="bg-[#F1F5F9]/90 border border-slate-200/80 rounded-2xl px-4 py-3.5 flex items-center gap-2.5 text-[13.5px] text-slate-600">
            <div className="w-5 h-5 rounded-full bg-slate-500 text-white flex items-center justify-center text-[11px] font-bold flex-shrink-0">
              i
            </div>
            <span>Ghi danh không tự tạo sự đồng ý xử lý dữ liệu.</span>
          </div>
        </div>

        {/* ── RIGHT COLUMN (4 cols) ── */}
        <div className="col-span-4 space-y-4">
          {/* Card 1: Hồ sơ: Lá */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[19px] font-extrabold text-[#0F172A]">
                Hồ sơ: {selected.name}
              </h3>
              <button className="text-slate-400 hover:text-slate-600 p-1">
                <X size={19} />
              </button>
            </div>

            <div className="flex items-center gap-4 pb-5 border-b border-slate-100">
              <img
                src={selected.profileImg}
                alt={selected.name}
                className="w-[76px] h-[76px] rounded-2xl object-cover border border-slate-100"
              />
              <div>
                <div className="text-[20px] font-extrabold text-[#0F172A]">
                  {selected.name}
                </div>
                <span className="inline-flex items-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[13px] font-medium px-3 py-1 rounded-full mt-1.5">
                  {renderGroupIcon(selected.groupType)}
                  <span>{selected.group}</span>
                </span>
              </div>
            </div>

            <div className="py-4 space-y-3.5 text-[14px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Tuổi đã xác nhận</span>
                <span className="font-semibold text-[#0F172A]">{selected.age}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Trạng thái ghi danh</span>
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[13px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                  <span className="w-2 h-2 rounded-full bg-[#16A34A] shrink-0" />
                  <span>Đang học</span>
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5 pt-2">
              <button className="inline-flex items-center justify-center gap-1.5 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13px] py-2.5 px-3 rounded-xl transition cursor-pointer whitespace-nowrap">
                <Pencil size={14} className="shrink-0" />
                <span>Chỉnh hồ sơ</span>
              </button>
              <button className="inline-flex items-center justify-center gap-1.5 border border-red-300 bg-white hover:bg-red-50 text-red-600 font-semibold text-[13px] py-2.5 px-3 rounded-xl transition cursor-pointer whitespace-nowrap">
                <MinusCircle size={14} className="shrink-0" />
                <span>Ngừng ghi danh</span>
              </button>
            </div>
          </div>

          {/* Card 2: Tóm tắt đồng ý */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <h3 className="text-[18px] font-extrabold text-[#0F172A] mb-4">
              Tóm tắt đồng ý
            </h3>

            <div className="space-y-3.5 text-[14px]">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2.5 text-slate-700 font-medium whitespace-nowrap">
                  <ImageIcon size={17} className="text-slate-500 shrink-0" />
                  <span>Lưu tranh</span>
                </div>
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                  <GreenCheckCircle size={14} />
                  <span>Được phép</span>
                </span>
              </div>

              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2.5 text-slate-700 font-medium whitespace-nowrap">
                  <Sparkles size={17} className="text-slate-500 shrink-0" />
                  <span>Sử dụng AI</span>
                </div>
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                  <AlertTriangle size={14} className="text-[#D97706] shrink-0" />
                  <span>Chờ xác minh</span>
                </span>
              </div>

              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2.5 text-slate-700 font-medium whitespace-nowrap">
                  <Users size={17} className="text-slate-500 shrink-0" />
                  <span>Chia sẻ trong lớp</span>
                </div>
                <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12.5px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
                  <GreenCheckCircle size={14} />
                  <span>Được phép</span>
                </span>
              </div>
            </div>

            <button className="w-full inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13.5px] py-2.5 rounded-xl mt-5 transition cursor-pointer whitespace-nowrap">
              <FileText size={16} className="shrink-0" />
              <span>Yêu cầu xử lý</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
