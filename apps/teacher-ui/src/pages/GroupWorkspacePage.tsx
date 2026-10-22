import { useState } from 'react'
import {
  FileText,
  Users,
  RotateCcw,
  Settings,
  ChevronRight,
  ChevronDown,
  UserCheck,
  Monitor,
  Clock,
  Image as ImageIcon,
  Maximize2,
} from 'lucide-react'
import {
  GreenCheckCircle,
  CloudBadgeIcon,
  LeafBadgeIcon,
  SproutBadgeIcon,
} from '../components/Icons'
import canvasGroup from '../assets/canvas-group.png'

export function GroupWorkspacePage() {
  const [activeTab, setActiveTab] = useState<'canvas' | 'regions' | 'history'>('canvas')
  const [currentTurn, setCurrentTurn] = useState<'may' | 'la'>('may')

  return (
    <div className="px-7 py-3 space-y-2.5 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[26px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Không gian nhóm
          </h1>
          <div className="text-[18.5px] font-extrabold text-[#0F172A] mt-0.5">
            Khu vườn của chúng mình
          </div>

          <div className="flex items-center flex-wrap gap-2 mt-1.5">
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
              <span className="w-2 h-2 rounded-full bg-[#16A34A] shrink-0" />
              <span>Đang hoạt động</span>
            </span>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#EFF6FF] text-[#1D63F2] text-[12px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
              <LeafBadgeIcon size={15} /> <span>Nhóm Lá (Mây • Lá)</span>
            </span>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#F1F5F9] text-slate-700 text-[12px] font-medium px-3 py-1 rounded-full whitespace-nowrap shrink-0">
              <Users size={13} className="text-slate-500 shrink-0" />
              <span>2 trẻ <span className="mx-0.5">•</span> 1 thiết bị chung</span>
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 shrink-0">
          <button className="inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold px-4 py-2 rounded-xl text-[13.5px] shadow-xs transition cursor-pointer whitespace-nowrap shrink-0">
            <FileText size={15} className="shrink-0" />
            <span>Ghi tiến độ</span>
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2 rounded-xl text-[13.5px] transition cursor-pointer whitespace-nowrap shrink-0">
            <Users size={15} className="shrink-0" />
            <span>Hỗ trợ nhóm</span>
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold px-4 py-2 rounded-xl text-[13.5px] transition cursor-pointer whitespace-nowrap shrink-0">
            <FileText size={15} className="shrink-0" />
            <span>Lưu nháp</span>
          </button>
        </div>
      </div>

      {/* ── Main 2-Column Layout ── */}
      <div className="grid grid-cols-12 gap-4 items-start">
        {/* ── LEFT COLUMN: Collaborative Canvas (7 cols) ── */}
        <div className="col-span-7 bg-white rounded-2xl border border-slate-200/80 p-3 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)] flex flex-col">
          {/* Pill Tabs */}
          <div className="flex items-center gap-2">
            {[
              { key: 'canvas', label: 'Xem tranh', icon: ImageIcon },
              { key: 'regions', label: 'Vùng & khóa', icon: Maximize2 },
              { key: 'history', label: 'Lịch sử', icon: Clock },
            ].map((t) => {
              const isActive = activeTab === t.key
              const Icon = t.icon
              return (
                <button
                  key={t.key}
                  onClick={() => setActiveTab(t.key as 'canvas' | 'regions' | 'history')}
                  className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-[12.5px] font-semibold border transition cursor-pointer ${
                    isActive
                      ? 'border-[#3B82F6] bg-[#EFF6FF] text-[#1D63F2]'
                      : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Icon size={14} />
                  <span>{t.label}</span>
                </button>
              )
            })}
          </div>

          {/* Canvas Area */}
          <div className="rounded-xl overflow-hidden border border-slate-100">
            <img
              src={canvasGroup}
              alt="Không gian vẽ Nhóm Lá"
              className="w-full h-[385px] block object-cover object-top"
            />
          </div>

          {/* Canvas Status Footer */}
          <div className="flex items-center flex-wrap gap-2.5 pt-0.5">
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#DCFCE7] text-[#15803D] text-[12px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
              <GreenCheckCircle size={14} />
              <span>Checkpoint đã lưu <span className="font-normal text-slate-600">• 10:24 hôm nay</span></span>
            </span>
            <span className="inline-flex items-center justify-center gap-1.5 bg-[#FEF3C7] text-[#B45309] text-[12px] font-semibold px-3 py-1 rounded-full whitespace-nowrap shrink-0">
              <span className="w-2 h-2 rounded-full bg-[#D97706] shrink-0" />
              <span>1 bản nháp trên thiết bị chưa gửi</span>
            </span>
          </div>
        </div>

        {/* ── RIGHT COLUMN (5 cols) ── */}
        <div className="col-span-5 space-y-2.5">
          {/* Card 1: Thành viên & lượt */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between">
              <h3 className="text-[15px] font-extrabold text-[#0F172A]">Thành viên & lượt</h3>
              <span className="inline-flex items-center gap-1.5 text-slate-600 text-[11.5px] font-medium">
                <Monitor size={13} className="text-slate-500" />
                Tablet 01 • thiết bị chung
              </span>
            </div>

            <div className="flex items-stretch gap-2.5">
              <div className="flex-1 space-y-1.5">
                <div
                  onClick={() => setCurrentTurn('may')}
                  className={`flex items-center justify-between px-3 py-2 rounded-xl cursor-pointer transition ${
                    currentTurn === 'may' ? 'bg-[#EFF6FF]' : 'bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-4 h-4 rounded-full ${
                        currentTurn === 'may'
                          ? 'border-4 border-[#1D63F2] bg-white'
                          : 'border border-slate-300 bg-white'
                      }`}
                    />
                    <CloudBadgeIcon size={22} />
                    <span className="text-[14px] font-bold text-[#0F172A]">Mây</span>
                  </div>
                  {currentTurn === 'may' && (
                    <span className="inline-flex items-center gap-1.5 bg-[#DBEAFE] text-[#1D63F2] text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#1D63F2]" />
                      Đang vẽ: Mây
                    </span>
                  )}
                </div>

                <div
                  onClick={() => setCurrentTurn('la')}
                  className={`flex items-center justify-between px-3 py-2 rounded-xl cursor-pointer transition ${
                    currentTurn === 'la' ? 'bg-[#EFF6FF]' : 'bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-4 h-4 rounded-full ${
                        currentTurn === 'la'
                          ? 'border-4 border-[#1D63F2] bg-white'
                          : 'border border-slate-300 bg-white'
                      }`}
                    />
                    <LeafBadgeIcon size={22} />
                    <span className="text-[14px] font-bold text-[#0F172A]">Lá</span>
                  </div>
                  {currentTurn === 'la' && (
                    <span className="inline-flex items-center gap-1.5 bg-[#DBEAFE] text-[#1D63F2] text-[11.5px] font-semibold px-2.5 py-0.5 rounded-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#1D63F2]" />
                      Đang vẽ: Lá
                    </span>
                  )}
                </div>
              </div>

              <button
                onClick={() => setCurrentTurn(currentTurn === 'may' ? 'la' : 'may')}
                className="w-[82px] flex flex-col items-center justify-center gap-1.5 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13px] rounded-xl transition cursor-pointer flex-shrink-0"
              >
                <RotateCcw size={17} />
                <span>Đổi lượt</span>
              </button>
            </div>
          </div>

          {/* Card 2: Quyền vùng vẽ */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <h3 className="text-[15px] font-extrabold text-[#0F172A]">Quyền vùng vẽ</h3>
                <span className="w-4 h-4 rounded-full border border-slate-300 text-slate-400 text-[10px] font-bold flex items-center justify-center">
                  i
                </span>
              </div>
              <button className="inline-flex items-center gap-1.5 border border-[#3B82F6] text-[#1D63F2] hover:bg-blue-50 font-semibold text-[11.5px] px-2.5 py-1 rounded-lg transition cursor-pointer">
                <Settings size={12.5} />
                <span>Điều chỉnh vùng</span>
              </button>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-slate-100 text-[12.5px]">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-md border-2 border-dashed border-[#3B82F6] bg-[#EFF6FF]" />
                <span className="font-bold text-[#0F172A]">Vùng Mây</span>
                <span className="inline-flex items-center gap-1 bg-[#DCFCE7] text-[#15803D] text-[11px] font-semibold px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]" />
                  Đang mở
                </span>
              </div>
              <span className="text-slate-600 text-[12px]">Mây được vẽ trong vùng này</span>
            </div>

            <div className="flex items-center justify-between py-1 text-[12.5px]">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-md border-2 border-dashed border-[#16A34A] bg-[#DCFCE7]/50" />
                <span className="font-bold text-[#0F172A]">Vùng Lá</span>
                <span className="inline-flex items-center gap-1 bg-[#DCFCE7] text-[#15803D] text-[11px] font-semibold px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]" />
                  Đang mở
                </span>
              </div>
              <span className="text-slate-600 text-[12px]">Lá được vẽ trong vùng này</span>
            </div>
          </div>

          {/* Card 3: Đang khám phá & vẽ */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-1.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <SproutBadgeIcon size={18} />
                <span className="text-[14.5px] font-extrabold text-[#0F172A]">
                  Đang khám phá & vẽ
                </span>
              </div>
              <span className="text-[11.5px] text-slate-500 font-medium">Nhóm tiến độ riêng</span>
            </div>

            <div className="flex items-center justify-between gap-2 pl-6">
              <p className="text-[12px] text-slate-600 leading-snug">
                Các bạn cùng nhau khám phá khu vườn và vẽ thêm chi tiết.
              </p>
              <button className="inline-flex items-center gap-1.5 border border-red-300 bg-white hover:bg-red-50 text-red-600 font-semibold text-[12px] px-3 py-1.5 rounded-xl transition cursor-pointer flex-shrink-0">
                <FileText size={13} />
                <span>Ghi nhận cần hỗ trợ</span>
              </button>
            </div>
          </div>

          {/* Card 4: Lịch sử hoạt động */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 space-y-2 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Clock size={15} className="text-slate-500" />
                <h3 className="text-[15px] font-extrabold text-[#0F172A]">Lịch sử hoạt động</h3>
              </div>
              <button className="inline-flex items-center gap-0.5 border border-[#3B82F6] text-[#1D63F2] text-[11.5px] font-semibold px-2.5 py-1 rounded-lg hover:bg-blue-50 cursor-pointer">
                <span>Xem lịch sử</span>
                <ChevronRight size={13} />
              </button>
            </div>

            <div className="space-y-1.5 text-[12.5px]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CloudBadgeIcon size={22} />
                  <div>
                    <div className="text-slate-700 font-medium">
                      <span className="font-bold text-[#0F172A]">Mây</span> thêm nét lá
                    </div>
                    <div className="text-slate-500 text-[11.5px]">trong vùng Mây</div>
                  </div>
                </div>
                <span className="text-slate-500 text-[12px]">10:18</span>
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                <div className="flex items-center gap-2">
                  <LeafBadgeIcon size={22} />
                  <div>
                    <div className="text-slate-700 font-medium">
                      <span className="font-bold text-[#0F172A]">Lá</span> thêm bông hoa
                    </div>
                    <div className="text-slate-500 text-[11.5px]">trong vùng Lá</div>
                  </div>
                </div>
                <span className="text-slate-500 text-[12px]">10:16</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Action Bar ── */}
      <div className="bg-white rounded-2xl border border-slate-200/80 px-4 py-2.5 flex items-center justify-between gap-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
        <div className="flex items-center gap-2.5">
          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-3.5 py-2 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
            <Users size={15} className="shrink-0" />
            <span>Chuyển thành viên</span>
            <ChevronDown size={14} className="shrink-0" />
          </button>

          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-3.5 py-2 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
            <RotateCcw size={14} className="shrink-0" />
            <span>Khôi phục phiên bản</span>
          </button>

          <button className="inline-flex items-center justify-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-3.5 py-2 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0">
            <UserCheck size={15} className="shrink-0" />
            <span>Xác nhận người đóng góp</span>
          </button>
        </div>

        <div className="flex items-center gap-1.5 text-[12.5px] text-slate-600 whitespace-nowrap">
          <span className="w-4 h-4 rounded-full border border-slate-400 text-slate-500 text-[10px] font-bold flex items-center justify-center shrink-0">
            i
          </span>
          <span>Khôi phục tạo bản mới; giữ lịch sử đóng góp.</span>
        </div>
      </div>
    </div>
  )
}
