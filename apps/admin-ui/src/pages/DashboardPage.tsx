import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, Calendar, BookOpen, Play, List, AlertTriangle, AlertCircle, X } from 'lucide-react'

export function DashboardPage() {
  const navigate = useNavigate()
  const [showBanner, setShowBanner] = useState(true)

  return (
    <div className="p-6 space-y-5">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tổng quan</h1>
          <p className="text-sm text-gray-500 mt-0.5">Vận hành trường và an toàn dữ liệu</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-2 bg-white border border-gray-200 text-gray-600 text-sm font-medium px-3 py-2 rounded-lg hover:bg-gray-50 transition">
              <Calendar size={14} />
              Hôm nay
              <svg width="12" height="12" viewBox="0 0 12 12"><path d="M3 4.5L6 7.5L9 4.5" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round"/></svg>
            </button>
            <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition">
              <RefreshCw size={14} />
              Làm mới
            </button>
          </div>
          <p className="text-xs text-gray-400">Cập nhật lúc 09:40</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Lớp hoạt động', value: '1', icon: <BookOpen size={20} />, iconBg: 'bg-green-100', iconColor: 'text-green-600' },
          { label: 'Phiên đang diễn ra', value: '1', icon: <Play size={20} />, iconBg: 'bg-blue-100', iconColor: 'text-blue-600' },
          { label: 'Tác vụ AI đang chờ', value: '3', icon: <List size={20} />, iconBg: 'bg-amber-100', iconColor: 'text-amber-600' },
          { label: 'Cảnh báo cần xử lý', value: '2', icon: <AlertTriangle size={20} />, iconBg: 'bg-red-100', iconColor: 'text-red-500' },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-10 h-10 rounded-xl ${s.iconBg} ${s.iconColor} flex items-center justify-center`}>
                {s.icon}
              </div>
              <p className="text-sm text-gray-500">{s.label}</p>
            </div>
            <p className="text-3xl font-bold text-gray-900">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Middle row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Live session */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-blue-100 rounded-lg flex items-center justify-center">
                <BookOpen size={15} className="text-blue-600" />
              </div>
              <h2 className="text-sm font-semibold text-gray-800">Phiên hiện hành</h2>
            </div>
            <span className="flex items-center gap-1.5 text-xs font-semibold text-green-700 bg-green-50 px-2.5 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block"></span>
              Đang hoạt động
            </span>
          </div>
          <div className="flex items-start gap-3 mb-4">
            <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <BookOpen size={24} className="text-blue-500" />
            </div>
            <div>
              <p className="font-semibold text-gray-800 text-[15px]">Lớp Lá • Khu vườn của chúng mình</p>
              <p className="text-sm text-gray-500 mt-1 flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="5" r="3" stroke="#9CA3AF" strokeWidth="1.2" fill="none"/><path d="M2 12c0-2.8 2.2-4 5-4s5 1.2 5 4" stroke="#9CA3AF" strokeWidth="1.2" fill="none" strokeLinecap="round"/></svg>
                24 trẻ đã tiếp nhận
              </p>
              <p className="text-sm text-gray-500 flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="5" r="3" stroke="#9CA3AF" strokeWidth="1.2" fill="none"/><path d="M2 12c0-2.8 2.2-4 5-4s5 1.2 5 4" stroke="#9CA3AF" strokeWidth="1.2" fill="none" strokeLinecap="round"/></svg>
                Giáo viên: GV An
              </p>
            </div>
          </div>
          <div className="flex justify-end mt-4">
            <button
              onClick={() => navigate('/monitoring')}
              className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition"
            >
              Xem trạng thái
              <svg width="14" height="14" viewBox="0 0 14 14"><path d="M3 7h8M7 3l4 4-4 4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
          </div>
        </div>

        {/* System health */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 bg-blue-50 rounded-lg flex items-center justify-center">
              <span className="text-blue-600 text-sm font-bold">⚙️</span>
            </div>
            <h2 className="text-sm font-semibold text-gray-800">Sức khỏe hệ thống</h2>
          </div>
          <div className="space-y-3">
            {[
              { name: 'API', status: 'Hoạt động', color: 'text-green-600', dot: 'bg-green-500', icon: '⚙️' },
              { name: 'Lưu checkpoint', status: 'Hoạt động', color: 'text-green-600', dot: 'bg-green-500', icon: '🗄️' },
              { name: 'Hàng đợi AI', status: 'Có độ trễ', color: 'text-amber-600', dot: 'bg-amber-500', icon: '📋' },
            ].map((svc) => (
              <div key={svc.name} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center text-sm">
                    {svc.icon}
                  </div>
                  <span className="text-sm text-gray-700 font-medium">{svc.name}</span>
                </div>
                <span className={`flex items-center gap-1.5 text-sm font-semibold ${svc.color}`}>
                  <span className={`w-2 h-2 rounded-full ${svc.dot} inline-block`}></span>
                  {svc.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action table */}
      <div className="bg-white rounded-xl border border-gray-100 p-5">
        <div className="flex items-center gap-2 mb-4">
          <List size={16} className="text-blue-600" />
          <h2 className="text-sm font-semibold text-gray-800">Việc cần xử lý</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Mô tả</th>
              <th className="text-left py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Mã sự cố</th>
              <th className="text-left py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {[
              { icon: <AlertTriangle size={18} className="text-red-500" />, iconBg: 'bg-red-50', title: 'Tác vụ video chưa hoàn thành', desc: 'Một số tác vụ video đang xử lý nhưng chưa hoàn thành.', code: 'INC-024', action: 'Mở sự cố' },
              { icon: <AlertCircle size={18} className="text-amber-500" />, iconBg: 'bg-amber-50', title: 'Thiết bị chưa đồng bộ', desc: 'Có thiết bị chưa đồng bộ dữ liệu lên hệ thống.', code: 'INC-025', action: 'Kiểm tra' },
            ].map((row) => (
              <tr key={row.code} className="border-b border-gray-50 last:border-0">
                <td className="py-3.5">
                  <div className="flex items-start gap-3">
                    <div className={`w-9 h-9 rounded-xl ${row.iconBg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                      {row.icon}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">{row.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{row.desc}</p>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 text-gray-600 font-mono text-xs">{row.code}</td>
                <td className="py-3.5">
                  <button
                    onClick={() => navigate('/monitoring')}
                    className="bg-blue-50 hover:bg-blue-100 text-blue-600 text-sm font-semibold px-5 py-2 rounded-lg transition"
                  >
                    {row.action}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer banner & watermark */}
      <div className="flex items-center justify-between pt-2">
        {showBanner ? (
          <div className="flex-1 flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 mr-4">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#3B82F6" strokeWidth="1.3"/><path d="M8 7v4M8 5.5v.5" stroke="#3B82F6" strokeWidth="1.3" strokeLinecap="round"/></svg>
            <p className="text-sm text-blue-700 flex-1">
              <span className="font-semibold">Phạm vi một trường</span> • Dữ liệu tổng hợp theo quyền.
            </p>
            <button onClick={() => setShowBanner(false)} className="text-blue-400 hover:text-blue-600">
              <X size={15} />
            </button>
          </div>
        ) : <div className="flex-1" />}
        <span className="text-xs text-gray-400 shrink-0">Dữ liệu minh họa • Bản thiết kế UI.</span>
      </div>
    </div>
  )
}
