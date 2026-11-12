import { useNavigate } from 'react-router-dom'
import {
  FileText,
  MessageSquare,
  Shield,
  ChevronRight,
  ChevronDown,
  BookOpen,
  Calendar,
  Users,
  Eye,
  Image as ImageIcon,
} from 'lucide-react'
import {
  GreenCheckCircle,
   SproutBadgeIcon,
} from '../components/Icons'
import avatarMay from '../assets/avatar-may.png'
import portfolioSession1 from '../assets/portfolio-session1.png'
import portfolioSession2 from '../assets/portfolio-session2.png'
import reportPreviewArt from '../assets/report-preview-art.png'

export function LearningPortfolioPage() {
  const navigate = useNavigate()

  return (
    <div className="px-7 py-3 space-y-2.5 max-w-[1400px] mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-start justify-between">
        <div className="space-y-1.5">
          <h1 className="text-[27px] font-extrabold text-[#0F172A] tracking-tight leading-tight">
            Hồ sơ học tập
          </h1>
          <div className="flex items-center gap-3">
            <img
              src={avatarMay}
              alt="Mây"
              className="w-14 h-14 rounded-full object-cover border border-sky-100"
            />
            <div>
              <div className="text-[20px] font-extrabold text-[#0F172A] leading-tight">
                Mây
              </div>
              <div className="text-[13px] text-slate-700 font-medium mt-0.5">
                7 tuổi 2 tháng
              </div>
              <div className="text-[12.5px] text-slate-600 mt-0.5">
                Lớp Mầm Xanh <span className="mx-1">•</span> Trong phạm vi được phân công
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2.5">
          <div className="flex items-center gap-2.5">
            <button className="inline-flex items-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-3.5 py-2 rounded-xl transition cursor-pointer">
              <FileText size={15} />
              <span>Yêu cầu xuất báo cáo</span>
            </button>

            <button className="inline-flex items-center gap-2 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[13px] px-3.5 py-2 rounded-xl transition cursor-pointer">
              <MessageSquare size={15} />
              <span>Đề nghị chỉnh sửa</span>
            </button>

            <button className="inline-flex items-center gap-2 border border-slate-200 bg-[#F1F5F9] hover:bg-slate-200/70 text-slate-700 font-semibold text-[13px] px-3.5 py-2 rounded-xl transition cursor-pointer">
              <Shield size={15} className="text-slate-600" />
              <span>Yêu cầu xử lý dữ liệu</span>
            </button>
          </div>

          <div className="flex items-center gap-2.5">
            <button className="inline-flex items-center justify-between gap-6 border border-slate-200 bg-white px-3.5 py-1.5 rounded-xl text-[12.5px] font-medium text-slate-700">
              <span className="flex items-center gap-1.5">
                <BookOpen size={14} className="text-slate-500" />
                <span>
                  Chủ đề: <strong className="text-[#0F172A]">Tất cả</strong>
                </span>
              </span>
              <ChevronDown size={14} className="text-slate-500" />
            </button>

            <button className="inline-flex items-center justify-between gap-6 border border-slate-200 bg-white px-3.5 py-1.5 rounded-xl text-[12.5px] font-medium text-slate-700">
              <span className="flex items-center gap-1.5">
                <Calendar size={14} className="text-slate-500" />
                <span>
                  Khoảng thời gian: <strong className="text-[#0F172A]">Tất cả</strong>
                </span>
              </span>
              <ChevronDown size={14} className="text-slate-500" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Main 3-Column Layout ── */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* ── LEFT COLUMN: Tiến trình của chính trẻ (3 cols) ── */}
        <div className="col-span-3 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3.5 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <h2 className="text-[15.5px] font-extrabold text-[#0F172A]">
            Tiến trình của chính trẻ
          </h2>

          <div className="flex flex-col items-center text-center py-2 border-b border-slate-100 pb-3.5">
            <img
              src={avatarMay}
              alt="Mây"
              className="w-24 h-24 rounded-full object-cover border-2 border-sky-100"
            />
            <div className="text-[20px] font-extrabold text-[#0F172A] mt-2">Mây</div>
            <div className="text-[13px] text-slate-600 mt-0.5">7 tuổi 2 tháng</div>
          </div>

          <div className="space-y-3 text-[12.5px]">
            <div className="flex items-center gap-2.5 pb-2.5 border-b border-slate-100">
              <SproutBadgeIcon size={16} />
              <span className="text-slate-600">Nhóm</span>
              <span className="bg-[#DCFCE7] text-[#15803D] font-bold text-[12px] px-2.5 py-0.5 rounded-full">
                Lá
              </span>
            </div>

            <div className="flex items-start gap-2.5 pb-2.5 border-b border-slate-100">
              <FileText size={16} className="text-[#1D63F2] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#0F172A]">Nguồn ghi nhận</div>
                <div className="text-slate-600 text-[12px] mt-0.5">
                  Kết quả của các phiên học
                </div>
              </div>
            </div>

            <div className="flex items-start gap-2.5 pb-2.5 border-b border-slate-100">
              <div className="mt-0.5">
                <GreenCheckCircle size={16} />
              </div>
              <div>
                <div className="font-bold text-[#0F172A]">Đóng góp</div>
                <div className="text-slate-600 text-[12px] mt-0.5">
                  Theo bằng chứng đã xác nhận
                </div>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <Shield size={16} className="text-[#1D63F2] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#0F172A]">Quyền xem hồ sơ</div>
                <div className="text-slate-600 text-[12px] mt-0.5">
                  Theo phân công hiện hành
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── CENTER COLUMN: Nhật ký học tập (6 cols) ── */}
        <div className="col-span-6 bg-white rounded-2xl border border-slate-200/80 p-4 space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <h2 className="text-[17px] font-extrabold text-[#0F172A]">Nhật ký học tập</h2>

          <div className="relative pl-4 border-l-2 border-slate-200 space-y-3">
            {/* Session 1 */}
            <div className="relative space-y-2.5">
              <span className="absolute -left-[22px] top-1 w-3 h-3 rounded-full bg-[#1D63F2] ring-4 ring-white" />
              <div className="text-[12px] font-semibold text-slate-600">Phiên gần đây</div>

              <div className="bg-white border border-slate-200/80 rounded-2xl p-3 space-y-2.5">
                <div className="flex items-start gap-3">
                  <img
                    src={portfolioSession1}
                    alt="Khu vườn của chúng mình"
                    className="w-20 h-24 rounded-xl object-cover border border-slate-100 flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="text-[16px] font-extrabold text-[#0F172A]">
                          Khu vườn của chúng mình
                        </h3>
                        <div className="flex flex-wrap items-center gap-1.5 mt-1">
                          <span className="inline-flex items-center gap-1 bg-[#DCFCE7]/80 text-[#15803D] text-[11px] font-semibold px-2 py-0.5 rounded-full">
                            <SproutBadgeIcon size={12} /> Chủ đề: Thiên nhiên
                          </span>
                          <span className="inline-flex items-center gap-1 bg-[#DCFCE7]/80 text-[#15803D] text-[11px] font-semibold px-2 py-0.5 rounded-full">
                            <Users size={11} /> Nhóm Lá
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={() => navigate('/portfolio/observation')}
                        className="inline-flex items-center justify-center gap-1 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[11.5px] px-3 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
                      >
                        <span>Xem kết quả phiên</span>
                        <ChevronRight size={13} className="shrink-0" />
                      </button>
                    </div>

                    <div className="text-[12.5px] font-bold text-[#0F172A] mt-2">
                      Phần đóng góp đã ghi nhận
                    </div>
                  </div>
                </div>

                {/* Bằng chứng 3 mini-cards */}
                <div>
                  <div className="text-[12px] font-bold text-slate-700 mb-1.5">Bằng chứng</div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-[#F0FDF4] border border-emerald-100 rounded-xl p-2 flex items-center justify-between gap-1.5">
                      <div className="flex items-start gap-1.5">
                        <ImageIcon size={14} className="text-[#16A34A] flex-shrink-0 mt-0.5" />
                        <span className="text-[11px] font-bold text-[#0F172A] leading-tight">
                          Nét vẽ lá và phần giải thích
                        </span>
                      </div>
                      <ChevronRight size={12} className="text-slate-400 flex-shrink-0" />
                    </div>

                    <div className="bg-[#FFFBEB] border border-amber-100 rounded-xl p-2 flex items-center justify-between gap-1.5">
                      <div className="flex items-start gap-1.5">
                        <Eye size={14} className="text-[#D97706] flex-shrink-0 mt-0.5" />
                        <div>
                          <div className="text-[11px] font-bold text-[#0F172A] leading-tight">
                            Quan sát giáo viên
                          </div>
                          <div className="text-[10px] text-slate-600 leading-tight mt-0.5">
                            Mây diễn đạt ý tưởng trong hoạt động
                          </div>
                        </div>
                      </div>
                      <ChevronRight size={12} className="text-slate-400 flex-shrink-0" />
                    </div>

                    <div className="bg-[#FFF1F2] border border-rose-100 rounded-xl p-2 flex items-center justify-between gap-1.5">
                      <div className="flex items-start gap-1.5">
                        <FileText size={14} className="text-[#E11D48] flex-shrink-0 mt-0.5" />
                        <div>
                          <div className="text-[11px] font-bold text-[#0F172A] leading-tight">
                            Gợi ý AI
                          </div>
                          <div className="text-[10px] text-slate-600 leading-tight mt-0.5">
                            Bản nháp tham khảo, chưa xác nhận
                          </div>
                        </div>
                      </div>
                      <ChevronRight size={12} className="text-slate-400 flex-shrink-0" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Session 2 */}
            <div className="relative space-y-2">
              <span className="absolute -left-[22px] top-1 w-3 h-3 rounded-full bg-slate-300 ring-4 ring-white" />
              <div className="text-[12px] font-semibold text-slate-600">Phiên trước</div>

              <div className="bg-white border border-slate-200/80 rounded-2xl p-3 flex items-start gap-3">
                <img
                  src={portfolioSession2}
                  alt="Màu sắc của lá"
                  className="w-20 h-24 rounded-xl object-cover border border-slate-100 flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-[15.5px] font-extrabold text-[#0F172A]">
                        Màu sắc của lá
                      </h3>
                      <div className="flex flex-wrap items-center gap-1.5 mt-1">
                        <span className="inline-flex items-center gap-1 bg-[#DCFCE7]/80 text-[#15803D] text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
                          <SproutBadgeIcon size={12} /> Chủ đề: Thiên nhiên
                        </span>
                        <span className="inline-flex items-center gap-1 bg-[#DCFCE7]/80 text-[#15803D] text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
                          <Users size={11} /> Nhóm Lá
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => navigate('/portfolio/observation')}
                      className="inline-flex items-center justify-center gap-1 border border-[#3B82F6] bg-white hover:bg-blue-50 text-[#1D63F2] font-semibold text-[11.5px] px-3 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap shrink-0"
                    >
                      <span>Xem bằng chứng</span>
                      <ChevronRight size={13} className="shrink-0" />
                    </button>
                  </div>

                  <div className="text-[12px] font-bold text-[#0F172A] mt-1.5">
                    Quan sát trong bối cảnh hoạt động
                  </div>
                  <p className="text-[11.5px] text-slate-600 leading-snug mt-0.5">
                    Mây quan sát và gọi tên các màu sắc của lá, thử nghiệm trộn màu khi vẽ.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN: Xem trước báo cáo (3 cols) ── */}
        <div className="col-span-3 bg-white rounded-2xl border border-slate-200/80 p-4 flex flex-col justify-between space-y-3 shadow-[0_2px_10px_rgba(15,23,42,0.02)]">
          <div className="space-y-3">
            <h2 className="text-[16px] font-extrabold text-[#0F172A]">
              Xem trước báo cáo
            </h2>

            <div className="flex justify-center">
              <img
                src={reportPreviewArt}
                alt="Xem trước báo cáo"
                className="h-[115px] w-auto object-contain"
              />
            </div>

            <div className="space-y-2.5 text-[12px]">
              <div className="flex items-start gap-2.5 pb-2 border-b border-slate-100">
                <div className="w-7 h-7 rounded-full bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center flex-shrink-0">
                  <ImageIcon size={14} />
                </div>
                <div>
                  <div className="font-bold text-[#0F172A]">Bằng chứng</div>
                  <div className="text-slate-600 text-[11.5px]">
                    Hình vẽ, sản phẩm, ghi chú
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5 pb-2 border-b border-slate-100">
                <div className="w-7 h-7 rounded-full bg-[#FEF3C7] text-[#D97706] flex items-center justify-center flex-shrink-0">
                  <Eye size={14} />
                </div>
                <div>
                  <div className="font-bold text-[#0F172A]">Quan sát giáo viên</div>
                  <div className="text-slate-600 text-[11.5px]">
                    Nhận xét và bối cảnh hoạt động
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <div className="w-7 h-7 rounded-full bg-[#FFE4E6] text-[#E11D48] flex items-center justify-center flex-shrink-0">
                  <FileText size={14} />
                </div>
                <div>
                  <div className="font-bold text-[#0F172A]">Gợi ý AI</div>
                  <div className="text-slate-600 text-[11.5px]">
                    Bản nháp tham khảo, chưa xác nhận
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-[#EFF6FF] border border-blue-200/70 rounded-xl p-2.5 flex items-start gap-2 text-[11.5px] leading-snug">
              <div className="w-4 h-4 rounded-full bg-[#1D63F2] text-white text-[9.5px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                i
              </div>
              <div>
                <div className="font-bold text-[#1D63F2]">
                  Xuất dữ liệu cần kiểm tra quyền và phạm vi.
                </div>
                <div className="text-slate-600 text-[11px] mt-0.5">
                  Chỉ bao gồm nội dung trong phạm vi được phân công giảng dạy.
                </div>
              </div>
            </div>
          </div>

          <button className="w-full inline-flex items-center justify-center gap-2 bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold text-[13.5px] py-2.5 rounded-xl shadow-xs transition cursor-pointer">
            <FileText size={15} />
            <span>Tạo yêu cầu xuất</span>
          </button>
        </div>
      </div>

      {/* ── Bottom Info Bar ── */}
      <div className="bg-[#F1F5F9]/90 border border-slate-200/80 rounded-xl px-4 py-2 flex items-center gap-2 text-[12px] text-slate-600">
        <span className="w-4 h-4 rounded-full border border-slate-400 text-slate-600 text-[9.5px] font-bold flex items-center justify-center flex-shrink-0">
          i
        </span>
        <span>Không so sánh xếp hạng trẻ. Tranh phiên có chính sách lưu riêng.</span>
      </div>
    </div>
  )
}
