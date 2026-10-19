import { useState } from 'react'
import { Search, Filter, Clock, CheckCircle, Edit, Check } from 'lucide-react'

const TABS = ['Chờ duyệt', 'Bản nháp', 'Đã xuất bản', 'Đã thu hồi']

const CONTENT = [
  { id: 1, emoji: '🌱', title: 'Vòng đời của hạt', category: 'Kiến thức', version: 'v2', age: '6-8 tuổi', status: 'pending', date: '10/10/2026', author: 'GV An' },
  { id: 2, emoji: '🍃', title: 'Khám phá lá cây', category: 'Hoạt động', version: 'v1', age: '3-5 tuổi', status: 'pending', date: '10/10/2026', author: 'GV Bình' },
]

const CAT_COLORS: Record<string, string> = {
  'Kiến thức': 'bg-amber-100 text-amber-700',
  'Hoạt động': 'bg-emerald-100 text-emerald-700',
}

export function ContentPage() {
  const [tab, setTab] = useState(0)
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<number>(1)

  const sel = CONTENT.find((c) => c.id === selected)

  return (
    <div className="flex h-full overflow-hidden">
      {/* LEFT */}
      <div className="flex-1 overflow-auto p-6 flex flex-col justify-between">
        <div>
          <div className="mb-5">
            <h1 className="text-2xl font-bold text-gray-900">Quản trị nội dung học tập</h1>
            <p className="text-sm text-gray-500 mt-0.5">Duyệt, xuất bản và quản lý các nội dung học tập cho nhà trường</p>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 mb-5 gap-1">
            {TABS.map((t, i) => (
              <button
                key={t}
                onClick={() => setTab(i)}
                className={`px-4 py-2.5 text-sm font-medium transition-colors relative ${
                  tab === i ? 'text-blue-600 border-b-2 border-blue-600 font-semibold' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {t}
                {t === 'Chờ duyệt' && (
                  <span className="ml-2 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">2</span>
                )}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="flex gap-2 mb-4">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Tìm theo tiêu đề, chủ đề, lứa tuổi..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              />
            </div>
            <button className="flex items-center gap-2 border border-gray-200 text-gray-600 text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-gray-50 transition bg-white">
              <Filter size={14} />
              Bộ lọc
            </button>
          </div>

          {/* Content cards */}
          <div className="space-y-3">
            {CONTENT.filter((c) => c.title.includes(search)).map((item) => (
              <div
                key={item.id}
                onClick={() => setSelected(item.id)}
                className={`bg-white rounded-2xl border p-4 cursor-pointer transition flex items-center gap-4 ${
                  selected === item.id ? 'border-2 border-blue-400 ring-2 ring-blue-100 shadow-sm' : 'border-gray-100 hover:border-gray-200'
                }`}
              >
                <div className="w-14 h-14 bg-emerald-50 rounded-xl flex items-center justify-center text-3xl flex-shrink-0">
                  {item.emoji}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <p className="font-semibold text-gray-900 mr-1">{item.title}</p>
                    <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-md ${CAT_COLORS[item.category]}`}>{item.category}</span>
                    <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-md">{item.version}</span>
                    <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded-md">{item.age}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="flex items-center gap-1.5 text-amber-700 text-xs font-semibold bg-amber-100/80 px-2.5 py-1 rounded-full">
                    <Clock size={12} />
                    Chờ duyệt
                  </span>
                  <span className="text-xs text-gray-400">{item.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Watermark */}
        <div className="text-right text-xs text-gray-400 pt-4">
          Dữ liệu minh họa • Bản thiết kế UI.
        </div>
      </div>

      {/* RIGHT panel */}
      {sel && (
        <div className="w-96 flex-shrink-0 border-l border-gray-100 bg-white overflow-auto">
          <div className="p-5">
            {/* Header */}
            <div className="flex items-start gap-3 mb-4">
              <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center text-4xl flex-shrink-0">
                {sel.emoji}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <p className="font-bold text-gray-900 text-lg leading-tight">{sel.title}</p>
                  <span className="flex items-center gap-1.5 text-amber-700 text-xs font-semibold bg-amber-100/80 px-2.5 py-0.5 rounded-full">
                    <Clock size={11} />
                    Chờ duyệt
                  </span>
                </div>
                <div className="flex items-center gap-2 flex-wrap mb-2">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-md ${CAT_COLORS[sel.category]}`}>{sel.category}</span>
                  <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-md">{sel.version}</span>
                  <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded-md">{sel.age}</span>
                </div>
                <p className="text-xs text-gray-500 mb-2">Cập nhật: {sel.date} • Tạo bởi: Giáo viên {sel.author}</p>
                <button className="text-xs text-blue-600 font-semibold flex items-center gap-1.5 bg-blue-50 border border-blue-200 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition">
                  <Clock size={13} />
                  Xem lịch sử phiên bản
                </button>
              </div>
            </div>

            {/* Review sections */}
            <div className="space-y-3">
              {[
                { emoji: '📚', title: 'Nguồn tham khảo', sub: 'Tài liệu giáo viên • nguồn đã đối chiếu', desc: 'Nội dung được xây dựng từ nguồn đã đối chiếu cho chủ đề học tập.' },
                { emoji: '👥', title: 'Phù hợp lứa tuổi', sub: '6–8 tuổi', desc: 'Nội dung, ngôn ngữ và hoạt động phù hợp với đặc điểm phát triển nhận thức của trẻ trong độ tuổi này.' },
              ].map((sec) => (
                <div key={sec.title} className="border border-gray-100 rounded-xl p-4 bg-white shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-sm">{sec.emoji}</div>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{sec.title}</p>
                      <p className="text-xs text-gray-500">{sec.sub}</p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed">{sec.desc}</p>
                </div>
              ))}

              {/* Safety checks */}
              <div className="border border-gray-100 rounded-xl p-4 bg-white shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center">🛡️</div>
                  <p className="text-sm font-semibold text-gray-800">An toàn và vật liệu</p>
                </div>
                {['Nội dung an toàn, phù hợp với môi trường giáo dục.', 'Vật liệu, dụng cụ sử dụng dễ tìm, an toàn và phù hợp tại trường.'].map((t) => (
                  <div key={t} className="flex items-start gap-2 mb-1.5">
                    <CheckCircle size={14} className="text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-xs text-gray-600">{t}</span>
                  </div>
                ))}
              </div>

              {/* Content check */}
              <div className="border border-gray-100 rounded-xl p-4 bg-white shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center">📄</div>
                  <p className="text-sm font-semibold text-gray-800">Kiểm tra nội dung</p>
                </div>
                {['Thông tin đã được đối chiếu với nguồn.', 'Ngôn ngữ tích cực, dễ hiểu.', 'Không có nội dung nhạy cảm hoặc không phù hợp.'].map((t) => (
                  <div key={t} className="flex items-start gap-2 mb-1.5">
                    <CheckCircle size={14} className="text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-xs text-gray-600">{t}</span>
                  </div>
                ))}
              </div>

              {/* Reviewer note */}
              <div className="bg-blue-50/60 border border-blue-100 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm">💬</span>
                  <p className="text-sm font-semibold text-gray-800">Nhận xét của người duyệt</p>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Nội dung rõ ràng, phù hợp. Đề nghị bổ sung thêm gợi ý mở rộng hoạt động ở phần cuối.
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-5">
              <button className="flex-1 flex items-center justify-center gap-2 border border-blue-200 bg-white text-blue-600 text-sm font-semibold py-2.5 rounded-xl hover:bg-blue-50 transition">
                <Edit size={14} />
                Yêu cầu chỉnh sửa
              </button>
              <button className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2.5 rounded-xl transition shadow-sm">
                <Check size={14} />
                Duyệt phiên bản
              </button>
            </div>
            <p className="text-xs text-gray-400 text-center mt-2.5">
              ℹ Chỉ xuất bản khi đủ quyền và hoàn tất review.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
