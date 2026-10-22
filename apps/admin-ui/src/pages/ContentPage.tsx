import { useState } from 'react'
import {
  Search,
  Filter,
  Clock,
  Edit2,
  Check,
  BookOpen,
  Users,
  Shield,
  FileText,
  MessageSquare,
} from 'lucide-react'
import seedSprout from '../assets/seed-sprout.png'
import leafExplore from '../assets/leaf-explore.png'

interface ContentItem {
  id: string
  thumb: string
  title: string
  typeTag: string
  typeColor: string
  version: string
  ageGroup: string
  status: string
  date: string
  author: string
}

const CONTENT_ITEMS: ContentItem[] = [
  {
    id: 'vong-doi-hat',
    thumb: seedSprout,
    title: 'Vòng đời của hạt',
    typeTag: 'Kiến thức',
    typeColor: 'text-[#D97706] bg-[#FEF3C7]',
    version: 'v2',
    ageGroup: '6–8 tuổi',
    status: 'Chờ duyệt',
    date: '10/10/2026',
    author: 'Giáo viên GV An',
  },
  {
    id: 'kham-pha-la',
    thumb: leafExplore,
    title: 'Khám phá lá cây',
    typeTag: 'Hoạt động',
    typeColor: 'text-[#059669] bg-[#E2F7EB]',
    version: 'v1',
    ageGroup: '3–5 tuổi',
    status: 'Chờ duyệt',
    date: '10/10/2026',
    author: 'Giáo viên GV Bình',
  },
]

const TABS = [
  { key: 'pending', label: 'Chờ duyệt', count: 2 },
  { key: 'draft', label: 'Bản nháp', count: null },
  { key: 'published', label: 'Đã xuất bản', count: null },
  { key: 'revoked', label: 'Đã thu hồi', count: null },
] as const

export function ContentPage() {
  const [activeTab, setActiveTab] = useState<string>('pending')
  const [selected, setSelected] = useState<string>('vong-doi-hat')
  const [search, setSearch] = useState('')

  const item = CONTENT_ITEMS.find((c) => c.id === selected)

  return (
    <div className="px-6 py-4 space-y-3.5 max-w-[1440px] mx-auto">
      {/* Full-width Header */}
      <div>
        <h1 className="text-[25px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
          Quản trị nội dung học tập
        </h1>
        <p className="text-[13.5px] text-slate-500 mt-0.5 font-medium">
          Duyệt, xuất bản và quản lý các nội dung học tập cho nhà trường
        </p>
      </div>

      {/* Full-width Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200/80">
        {TABS.map((t) => {
          const isActive = activeTab === t.key
          return (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2 text-[13.5px] rounded-t-xl border-b-2 transition -mb-px cursor-pointer whitespace-nowrap shrink-0 ${
                isActive
                  ? 'bg-white border-[#1565F9] text-[#1565F9] font-bold shadow-[0_-1px_3px_rgba(15,23,42,0.03)]'
                  : 'border-transparent text-slate-600 font-medium hover:text-slate-900'
              }`}
            >
              <span>{t.label}</span>
              {t.count !== null && (
                <span className="bg-[#EF4444] text-white text-[11px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {t.count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* 2-Column Content Grid — 50/50 split (chia đôi bố cục 6 cols / 6 cols) */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* LEFT CARD (6 cols) */}
        <div className="col-span-6 bg-white rounded-2xl border border-slate-200/70 p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col gap-3.5 min-w-0">
          {/* Search + filter */}
          <div className="flex gap-2.5">
            <div className="relative flex-1 min-w-0">
              <Search
                size={15}
                className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Tìm theo tiêu đề, chủ đề, lứa tuổi..."
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-[13px] text-slate-700 placeholder-slate-400 bg-[#FAFBFD] focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button className="flex items-center gap-1.5 border border-slate-200 bg-white text-slate-700 text-[13px] font-semibold px-3.5 py-2 rounded-xl hover:bg-slate-50 transition whitespace-nowrap shrink-0">
              <Filter size={14} className="text-slate-500" />
              <span>Bộ lọc</span>
            </button>
          </div>

          {/* Content cards list */}
          <div className="space-y-3">
            {CONTENT_ITEMS.filter((c) =>
              c.title.toLowerCase().includes(search.toLowerCase())
            ).map((c) => {
              const isSel = selected === c.id
              return (
                <div
                  key={c.id}
                  onClick={() => setSelected(c.id)}
                  className={`rounded-2xl border p-3.5 cursor-pointer transition ${
                    isSel
                      ? 'border-[#3B82F6] bg-[#EFF6FF]/70 shadow-[0_1px_4px_rgba(21,101,249,0.08)]'
                      : 'border-slate-200/70 bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <img
                      src={c.thumb}
                      alt={c.title}
                      className="w-16 h-16 rounded-2xl object-cover flex-shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-bold text-slate-900 text-[15px] leading-snug">
                          {c.title}
                        </p>
                        <span className="inline-flex items-center gap-1 text-[11.5px] font-semibold text-[#D97706] bg-[#FEF3C7] px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                          <Clock size={11} className="shrink-0" />
                          {c.status}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-2.5">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span
                            className={`text-[11.5px] font-semibold px-2.5 py-0.5 rounded-lg whitespace-nowrap shrink-0 ${c.typeColor}`}
                          >
                            {c.typeTag}
                          </span>
                          <span className="text-[11.5px] font-bold text-[#1565F9] bg-[#DCEBFF] px-2 py-0.5 rounded-lg whitespace-nowrap shrink-0">
                            {c.version}
                          </span>
                          <span className="text-[11.5px] font-medium text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-lg whitespace-nowrap shrink-0">
                            {c.ageGroup}
                          </span>
                        </div>
                        <span className="text-[12px] text-slate-500 whitespace-nowrap shrink-0">{c.date}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* RIGHT CARD — Detail panel (6 cols) */}
        {item && (
          <div className="col-span-6 bg-white rounded-2xl border border-slate-200/70 p-4 px-5 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between min-w-0">
            <div className="space-y-2.5">
              {/* Item header */}
              <div className="flex items-start gap-3.5 pb-1">
                <img
                  src={item.thumb}
                  alt={item.title}
                  className="w-16 h-16 rounded-2xl object-cover flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h2 className="text-[18px] font-extrabold text-slate-900 leading-tight">
                        {item.title}
                      </h2>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span
                          className={`text-[11px] font-semibold px-2 py-0.5 rounded-lg ${item.typeColor}`}
                        >
                          {item.typeTag}
                        </span>
                        <span className="text-[11px] font-bold text-[#1565F9] bg-[#DCEBFF] px-2 py-0.5 rounded-lg">
                          {item.version}
                        </span>
                        <span className="text-[11px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-lg">
                          {item.ageGroup}
                        </span>
                      </div>
                    </div>
                    <span className="flex items-center gap-1 text-[11.5px] font-semibold text-[#D97706] bg-[#FEF3C7] px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                      <Clock size={11.5} />
                      {item.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-2 mt-1.5">
                    <p className="text-[11.5px] text-slate-500 truncate">
                      Cập nhật: {item.date} • Tạo bởi: {item.author}
                    </p>
                    <button className="flex items-center gap-1 text-[11.5px] text-[#1565F9] border border-blue-300 bg-[#F2F7FF] px-2.5 py-1 rounded-xl hover:bg-blue-100 font-semibold transition whitespace-nowrap shrink-0">
                      <Clock size={11.5} />
                      <span>Xem lịch sử phiên bản</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* 2x2 Grid for the 4 inspection blocks (chia đôi bố cục chi tiết) */}
              <div className="grid grid-cols-2 gap-2.5">
                {/* 1. Nguồn tham khảo */}
                <div className="border border-slate-200/70 rounded-2xl p-3 flex items-start gap-2.5">
                  <div className="w-8 h-8 bg-[#E6F0FF] text-[#1565F9] rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
                    <BookOpen size={16} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[13px] font-bold text-slate-900">Nguồn tham khảo</p>
                    <p className="text-[11.5px] font-bold text-slate-700 mt-0.5">
                      Tài liệu giáo viên • nguồn đã đối chiếu
                    </p>
                    <p className="text-[11.5px] text-slate-500 mt-0.5 leading-snug">
                      Nội dung được xây dựng từ nguồn đã đối chiếu cho chủ đề học tập.
                    </p>
                  </div>
                </div>

                {/* 2. Phù hợp lứa tuổi */}
                <div className="border border-slate-200/70 rounded-2xl p-3 flex items-start gap-2.5">
                  <div className="w-8 h-8 bg-[#E2F7EB] text-[#10B981] rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Users size={16} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[13px] font-bold text-slate-900">Phù hợp lứa tuổi</p>
                    <p className="text-[11.5px] font-bold text-slate-700 mt-0.5">{item.ageGroup}</p>
                    <p className="text-[11.5px] text-slate-500 mt-0.5 leading-snug">
                      Nội dung, ngôn ngữ và hoạt động phù hợp với đặc điểm phát triển nhận thức của trẻ.
                    </p>
                  </div>
                </div>

                {/* 3. An toàn và vật liệu */}
                <div className="border border-slate-200/70 rounded-2xl p-3 flex items-start gap-2.5">
                  <div className="w-8 h-8 bg-[#FEE2E2] text-[#EF4444] rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Shield size={16} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-bold text-slate-900 mb-1">
                      An toàn và vật liệu
                    </p>
                    <div className="space-y-1">
                      <div className="flex items-start gap-1.5 text-[11.5px] text-slate-600 leading-snug">
                        <span className="w-3.5 h-3.5 rounded-full bg-[#10B981] text-white flex items-center justify-center shrink-0 mt-0.5">
                          <Check size={9} strokeWidth={3} />
                        </span>
                        <span>Nội dung an toàn, phù hợp môi trường giáo dục.</span>
                      </div>
                      <div className="flex items-start gap-1.5 text-[11.5px] text-slate-600 leading-snug">
                        <span className="w-3.5 h-3.5 rounded-full bg-[#10B981] text-white flex items-center justify-center shrink-0 mt-0.5">
                          <Check size={9} strokeWidth={3} />
                        </span>
                        <span>Vật liệu, dụng cụ dễ tìm, an toàn tại trường.</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 4. Kiểm tra nội dung */}
                <div className="border border-slate-200/70 rounded-2xl p-3 flex items-start gap-2.5">
                  <div className="w-8 h-8 bg-[#FEF3C7] text-[#F59E0B] rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
                    <FileText size={16} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-bold text-slate-900 mb-1">Kiểm tra nội dung</p>
                    <div className="space-y-1">
                      {[
                        'Thông tin đã được đối chiếu với nguồn.',
                        'Ngôn ngữ tích cực, dễ hiểu.',
                        'Không có nội dung nhạy cảm.',
                      ].map((txt) => (
                        <div key={txt} className="flex items-start gap-1.5 text-[11.5px] text-slate-600 leading-snug">
                          <span className="w-3.5 h-3.5 rounded-full bg-[#10B981] text-white flex items-center justify-center shrink-0 mt-0.5">
                            <Check size={9} strokeWidth={3} />
                          </span>
                          <span>{txt}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* 5. Nhận xét của người duyệt */}
              <div className="bg-[#EAF3FF]/80 rounded-2xl p-3 flex items-start gap-2.5">
                <MessageSquare size={17} className="text-[#1565F9] shrink-0 mt-0.5" />
                <div>
                  <p className="text-[13px] font-bold text-slate-900">Nhận xét của người duyệt</p>
                  <p className="text-[12px] text-slate-600 mt-0.5">
                    Nội dung rõ ràng, phù hợp. Đề nghị bổ sung thêm gợi ý mở rộng hoạt động ở phần cuối.
                  </p>
                </div>
              </div>
            </div>

            {/* Bottom buttons */}
            <div className="pt-3 flex flex-col items-end gap-1.5">
              <div className="flex items-center gap-3">
                <button className="flex items-center justify-center gap-2 border border-[#1565F9] bg-white text-[#1565F9] text-[13px] font-semibold px-4 py-2 rounded-xl hover:bg-blue-50 transition cursor-pointer whitespace-nowrap">
                  <Edit2 size={14} />
                  <span>Yêu cầu chỉnh sửa</span>
                </button>
                <button className="flex items-center justify-center gap-2 bg-[#1565F9] hover:bg-blue-700 text-white text-[13px] font-semibold px-5 py-2 rounded-xl transition shadow-sm cursor-pointer whitespace-nowrap">
                  <Check size={15} />
                  <span>Duyệt phiên bản</span>
                </button>
              </div>
              <div className="flex items-center gap-1.5 text-[11.5px] text-slate-500">
                <span className="w-4 h-4 rounded-full bg-[#1565F9] text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                  i
                </span>
                <span>Chỉ xuất bản khi đủ quyền và hoàn tất review.</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
