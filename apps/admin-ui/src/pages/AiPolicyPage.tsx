import { FileText, List, Users, Play, FileCheck, Shield, Search, PauseCircle } from 'lucide-react'

const CHECKS = [
  { icon: <Users size={17} className="text-green-600" />, bg: 'bg-green-50', title: 'Giáo viên duyệt từng gợi ý AI', desc: 'Mỗi gợi ý AI phải được giáo viên duyệt trước khi gửi cho trẻ.', badge: 'Bắt buộc' },
  { icon: <Play size={17} className="text-amber-500" />, bg: 'bg-amber-50', title: 'Duyệt video trước trình chiếu', desc: 'Video do AI tạo cần được duyệt trước khi trình chiếu cho trẻ.', badge: 'Bắt buộc' },
  { icon: <FileCheck size={17} className="text-blue-500" />, bg: 'bg-blue-50', title: 'Kiểm tra consent theo mục đích', desc: 'Chỉ cho phép tạo nội dung khi đã có consent phù hợp theo mục đích.', badge: 'Bắt buộc' },
  { icon: <Shield size={17} className="text-red-500" />, bg: 'bg-red-50', title: 'Kiểm tra an toàn', desc: 'Tự động kiểm tra nội dung để phát hiện rủi ro trước khi duyệt.', badge: 'Bắt buộc' },
]

const COMPAT = [
  { ok: true, label: 'Cài đặt an toàn', result: 'Đạt', resultColor: 'text-green-600 bg-green-50' },
  { ok: true, label: 'Phạm vi áp dụng', result: 'Đạt', resultColor: 'text-green-600 bg-green-50' },
  { ok: null, label: 'Ảnh hưởng đến quy trình', result: 'Cần đánh giá', resultColor: 'text-amber-600 bg-amber-50' },
  { ok: false, label: 'Tính nhất quán chính sách', result: 'Chưa kiểm tra', resultColor: 'text-gray-500 bg-gray-100' },
  { ok: null, label: 'Ghi chú thay đổi', result: 'Cần bổ sung', resultColor: 'text-amber-600 bg-amber-50' },
]

export function AiPolicyPage() {
  return (
    <div className="flex h-full overflow-hidden">
      {/* LEFT */}
      <div className="flex-1 overflow-auto p-6 flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between mb-5">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Chính sách AI</h1>
            <p className="text-sm text-gray-500 mt-0.5">Chính sách có phiên bản • áp dụng theo phạm vi.</p>
          </div>
          <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition">
            <FileText size={15} />
            Tạo bản nháp
          </button>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 gap-4 mb-5">
          <div className="bg-white rounded-xl border border-gray-100 p-4">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-9 h-9 bg-green-50 rounded-xl flex items-center justify-center">
                <FileText size={18} className="text-green-600" />
              </div>
              <p className="text-sm text-gray-500">Phiên bản hiệu lực</p>
            </div>
            <p className="text-3xl font-bold text-gray-900">P1</p>
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-green-700 bg-green-50 px-2.5 py-1 rounded-full mt-2 border border-green-100">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
              Đang hiệu lực
            </span>
          </div>
          <div className="bg-white rounded-xl border border-gray-100 p-4">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center">
                <List size={18} className="text-amber-500" />
              </div>
              <p className="text-sm text-gray-500">Tác vụ đang chờ</p>
            </div>
            <p className="text-3xl font-bold text-gray-900">3</p>
          </div>
        </div>

        {/* Safety settings */}
        <div className="bg-white rounded-xl border border-gray-100 p-5 mb-4 flex-1">
          <p className="text-sm font-semibold text-gray-800 mb-0.5">
            Cài đặt an toàn <span className="text-gray-400 font-normal">(đang áp dụng cho P1)</span>
          </p>
          <p className="text-xs text-gray-500 mb-4">Các quy tắc bảo vệ trẻ em và kiểm soát nội dung được bắt buộc.</p>
          <div className="space-y-3">
            {CHECKS.map((c) => (
              <div key={c.title} className="flex items-start gap-3 p-3 rounded-xl bg-gray-50">
                <div className={`w-8 h-8 ${c.bg} rounded-lg flex items-center justify-center flex-shrink-0`}>
                  {c.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-800">{c.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{c.desc}</p>
                </div>
                <span className="flex-shrink-0 flex items-center gap-1.5 text-xs font-semibold text-gray-600 bg-white border border-gray-200 px-2.5 py-1 rounded-lg">
                  🔒 {c.badge}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Two small cards */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {[
            { icon: '⚙️', title: 'Mức hỗ trợ AI', sub: 'Theo cấu hình phiên', desc: 'Phạm vi tính năng AI được cấu hình theo phiên bản chính sách đang hiệu lực tại trường.' },
            { icon: '🗄️', title: 'Ngân sách và giới hạn', sub: 'Cần phê duyệt', desc: 'Mọi thay đổi về ngân sách và giới hạn sử dụng cần được phê duyệt theo chính sách của trường.' },
          ].map((card) => (
            <div key={card.title} className="bg-white rounded-xl border border-gray-100 p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-base">{card.icon}</div>
                <div>
                  <p className="text-sm font-semibold text-gray-800">{card.title}</p>
                  <p className="text-xs text-gray-500">{card.sub}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{card.desc}</p>
            </div>
          ))}
        </div>

        {/* Bottom action bar */}
        <div className="bg-blue-50/60 border border-blue-100 rounded-xl px-4 py-3 flex items-center gap-3 mb-2">
          <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition shadow-sm">
            <Search size={14} />
            Kiểm tra bản nháp
          </button>
          <button className="flex items-center gap-2 border border-blue-200 bg-white text-blue-600 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-50 transition">
            <List size={14} />
            Xem thay đổi
          </button>
          <button className="flex items-center gap-2 border border-red-200 bg-red-50 text-red-600 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-red-100 transition">
            <PauseCircle size={14} />
            Tạm dừng hàng đợi
          </button>
          <p className="text-xs text-gray-500 ml-auto flex items-center gap-1.5">
            <span className="text-blue-500 font-bold">ℹ</span> Ngăn tác vụ mới trong phạm vi; tác vụ đang chạy xử lý theo chính sách.
          </p>
        </div>

        {/* Watermark */}
        <div className="text-right text-xs text-gray-400">
          Dữ liệu minh họa • Bản thiết kế UI.
        </div>
      </div>

      {/* RIGHT */}
      <div className="w-80 flex-shrink-0 border-l border-gray-100 bg-white overflow-auto p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
              <FileText size={16} className="text-blue-600" />
            </div>
            <div>
              <p className="font-bold text-gray-900">Bản nháp P2</p>
            </div>
          </div>
          <span className="flex items-center gap-1.5 text-xs font-semibold text-red-600 bg-red-50 px-2.5 py-1 rounded-full border border-red-100">
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
            Cần đánh giá
          </span>
        </div>

        <div className="bg-amber-50 border border-amber-200/80 rounded-xl p-3.5 mb-5">
          <div className="flex items-start gap-2.5">
            <span className="w-6 h-6 rounded-full bg-amber-400 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">!</span>
            <div>
              <p className="text-sm font-bold text-amber-900">Chưa được kích hoạt</p>
              <p className="text-xs text-amber-800/90 mt-0.5">Bản nháp này chưa được áp dụng cho trường.</p>
            </div>
          </div>
        </div>

        <p className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-1">Kết quả đánh giá tương thích</p>
        <p className="text-xs text-gray-500 mb-3">Kiểm tra các yêu cầu an toàn và phạm vi áp dụng.</p>

        <div className="space-y-2.5">
          {COMPAT.map((item) => (
            <div key={item.label} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
              <div className="flex items-center gap-2">
                {item.ok === true && <span className="w-4 h-4 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[10px] font-bold">✓</span>}
                {item.ok === null && <span className="w-4 h-4 rounded-full bg-amber-400 text-white flex items-center justify-center text-[10px] font-bold">!</span>}
                {item.ok === false && <span className="w-4 h-4 rounded-full bg-gray-400 text-white flex items-center justify-center text-[10px] font-bold">-</span>}
                <span className="text-sm text-gray-700">{item.label}</span>
              </div>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${item.resultColor}`}>
                {item.result}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
