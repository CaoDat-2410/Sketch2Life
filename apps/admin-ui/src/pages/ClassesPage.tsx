import { useState } from 'react'
import {
  Search,
  Plus,
  Edit2,
  Trash2,
  Layout,
  User,
  Shield,
  Check,
} from 'lucide-react'
import classSprout from '../assets/class-sprout.png'
import classFlower from '../assets/class-flower.png'

interface ClassItem {
  id: string
  thumb: string
  name: string
  ageGroup: string
  teacher: string
  profiles: number
  readyStatus: string
  readyColor: string
  dotColor: string
}

const CLASSES: ClassItem[] = [
  {
    id: 'lop-la',
    thumb: classSprout,
    name: 'Lớp Lá',
    ageGroup: '6 – 8 tuổi',
    teacher: 'GV An',
    profiles: 24,
    readyStatus: 'Đủ điều kiện',
    readyColor: 'text-[#059669] bg-[#E2F7EB]',
    dotColor: 'bg-[#10B981]',
  },
  {
    id: 'lop-hoa',
    thumb: classFlower,
    name: 'Lớp Hoa',
    ageGroup: '3 – 5 tuổi',
    teacher: 'GV Bình',
    profiles: 16,
    readyStatus: 'Cần kiểm tra chính sách',
    readyColor: 'text-[#D97706] bg-[#FEF3C7]',
    dotColor: 'bg-[#F59E0B]',
  },
]

const CHECKLIST = [
  {
    status: 'ok',
    title: 'Phân công giáo viên',
    desc: 'Đã phân công giáo viên phụ trách lớp.',
  },
  {
    status: 'ok',
    title: 'Chính sách nhóm tuổi',
    desc: 'Đã áp dụng phiên bản chính sách phù hợp.',
  },
  {
    status: 'warn',
    title: 'Consent: kiểm tra theo mục đích',
    desc: 'Kiểm tra và xác nhận consent theo mục đích sử dụng nội dung trong lớp.',
  },
]

export function ClassesPage() {
  const [selected, setSelected] = useState<string>('lop-la')
  const [search, setSearch] = useState('')
  const selectedClass = CLASSES.find((c) => c.id === selected)

  return (
    <div className="px-6 py-3 space-y-2.5 max-w-[1440px] mx-auto">
      {/* Full-width Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[24px] font-extrabold text-[#0F1F38] tracking-tight leading-tight">
            Lớp học &amp; phân công
          </h1>
          <p className="text-[13px] text-slate-500 mt-0.5 font-medium">
            Quản lý lớp học, phân công giáo viên và kiểm tra điều kiện vận hành
          </p>
        </div>
        <button className="inline-flex items-center justify-center gap-2 bg-[#1565F9] hover:bg-blue-700 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition shadow-sm cursor-pointer whitespace-nowrap shrink-0">
          <Plus size={15} className="shrink-0" />
          <span>Tạo lớp</span>
        </button>
      </div>

      {/* 2-Column Grid */}
      <div className="grid grid-cols-12 gap-4 items-stretch">
        {/* LEFT CARD — Danh sách lớp học (6 cols) */}
        <div className="col-span-6 bg-white rounded-2xl border border-slate-200/70 p-4 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col min-w-0">
          <div className="flex items-center gap-2.5 mb-2.5">
            <div className="w-7 h-7 bg-[#E6F0FF] text-[#1565F9] rounded-lg flex items-center justify-center">
              <Layout size={15} strokeWidth={2.2} />
            </div>
            <h2 className="text-[15.5px] font-bold text-slate-900">Danh sách lớp học</h2>
          </div>

          <div className="relative mb-2.5">
            <Search
              size={15}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm theo tên lớp hoặc giáo viên..."
              className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-[13px] text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-[#FAFBFD]"
            />
          </div>

          <div className="border border-slate-100 rounded-xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#F4F7FB] border-b border-slate-100">
                  {['Lớp', 'Nhóm tuổi', 'Giáo viên', 'Hồ sơ', 'Sẵn sàng'].map((h) => (
                    <th
                      key={h}
                      className="text-left py-2.5 px-2 first:pl-3 last:pr-3 text-[11.5px] font-semibold text-slate-600 whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {CLASSES.filter(
                  (c) =>
                    c.name.toLowerCase().includes(search.toLowerCase()) ||
                    c.teacher.toLowerCase().includes(search.toLowerCase())
                ).map((c) => {
                  const isSel = selected === c.id
                  return (
                    <tr
                      key={c.id}
                      onClick={() => setSelected(c.id)}
                      className={`cursor-pointer transition ${
                        isSel
                          ? 'bg-[#EBF3FF]/80 ring-1 ring-inset ring-blue-300'
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      <td className="py-3 pl-3 pr-2 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <img
                            src={c.thumb}
                            alt={c.name}
                            className="w-8 h-8 rounded-lg object-cover shrink-0"
                          />
                          <span className="font-bold text-slate-900 text-[13px] whitespace-nowrap">
                            {c.name}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-2 text-slate-600 text-[12px] whitespace-nowrap">
                        {c.ageGroup}
                      </td>
                      <td className="py-3 px-2 text-slate-800 font-semibold text-[12.5px] whitespace-nowrap">
                        {c.teacher}
                      </td>
                      <td className="py-3 px-2 text-slate-800 font-semibold text-[12.5px] whitespace-nowrap">
                        {c.profiles}
                      </td>
                      <td className="py-3 pl-2 pr-3 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap shrink-0 ${c.readyColor}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${c.dotColor}`} />
                          {c.readyStatus}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT CARD — Class detail (6 cols) */}
        {selectedClass && (
          <div className="col-span-6 bg-white rounded-2xl border border-slate-200/70 p-4 px-5 shadow-[0_1px_3px_rgba(15,23,42,0.02)] flex flex-col justify-between min-w-0">
            <div className="space-y-2.5">
              {/* Top header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <img
                    src={selectedClass.thumb}
                    alt={selectedClass.name}
                    className="w-12 h-12 rounded-2xl object-cover shrink-0"
                  />
                  <div>
                    <h2 className="text-[18px] font-extrabold text-slate-900 leading-tight">
                      {selectedClass.name}
                    </h2>
                    <p className="text-[12.5px] text-slate-500 mt-0.5">
                      Thông tin lớp học và điều kiện vận hành
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 text-[11.5px] font-semibold text-[#059669] bg-[#E2F7EB] px-2.5 py-1 rounded-full shrink-0">
                  <span className="w-2 h-2 rounded-full bg-[#10B981]" />
                  Hoạt động
                </span>
              </div>

              {/* Thông tin chung card */}
              <div className="border border-slate-200/70 rounded-2xl p-3 px-3.5">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className="w-5.5 h-5.5 bg-[#E6F0FF] text-[#1565F9] rounded-md flex items-center justify-center">
                      <Layout size={12.5} strokeWidth={2.2} />
                    </div>
                    <p className="text-[13.5px] font-bold text-slate-900">Thông tin chung</p>
                  </div>
                  <button className="flex items-center gap-1.5 text-[11.5px] text-[#1565F9] bg-[#EAF2FF] hover:bg-blue-100 font-semibold px-2.5 py-1 rounded-lg transition">
                    <Edit2 size={11.5} />
                    <span>Chỉnh sửa</span>
                  </button>
                </div>

                <div className="divide-y divide-slate-100 text-[12.5px]">
                  <div className="flex items-center py-1.5">
                    <span className="text-slate-500 w-44 shrink-0">Tên lớp</span>
                    <span className="font-bold text-slate-900">{selectedClass.name}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5">
                    <span className="text-slate-500 w-44 shrink-0">Giáo viên phụ trách</span>
                    <div className="flex-1 flex items-center justify-between">
                      <span className="flex items-center gap-2 font-bold text-slate-900">
                        <User size={13.5} className="text-slate-500" />
                        {selectedClass.teacher}
                      </span>
                      <button className="text-[11.5px] text-[#1565F9] bg-[#EAF2FF] border border-blue-200/70 font-semibold px-2.5 py-0.5 rounded-lg hover:bg-blue-100">
                        Thay đổi
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between py-1.5">
                    <span className="text-slate-500 w-44 shrink-0">Chính sách nhóm tuổi</span>
                    <div className="flex-1 flex items-center justify-between">
                      <span className="font-bold text-slate-900">v1</span>
                      <button className="text-[11.5px] text-[#1565F9] bg-[#EAF2FF] border border-blue-200/70 font-semibold px-2.5 py-0.5 rounded-lg hover:bg-blue-100">
                        Thay đổi
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center py-1.5">
                    <span className="text-slate-500 w-44 shrink-0">Số lượng hồ sơ</span>
                    <span className="font-bold text-slate-900">
                      {selectedClass.profiles} hồ sơ
                    </span>
                  </div>
                  <div className="flex items-center py-1.5">
                    <span className="text-slate-500 w-44 shrink-0">Trạng thái</span>
                    <span className="flex items-center gap-2 text-[#059669] font-semibold">
                      <span className="w-2 h-2 rounded-full bg-[#10B981]" />
                      Hoạt động
                    </span>
                  </div>
                </div>
              </div>

              {/* Kiểm tra điều kiện sẵn sàng */}
              <div className="border border-slate-200/70 rounded-2xl p-3 px-3.5">
                <div className="flex items-center gap-2 mb-1.5">
                  <div className="w-5.5 h-5.5 bg-[#E6F0FF] text-[#1565F9] rounded-md flex items-center justify-center">
                    <Shield size={12.5} strokeWidth={2.2} />
                  </div>
                  <p className="text-[13.5px] font-bold text-slate-900">
                    Kiểm tra điều kiện sẵn sàng
                  </p>
                </div>
                <div className="divide-y divide-slate-100">
                  {CHECKLIST.map((item) => (
                    <div key={item.title} className="flex items-start gap-2.5 py-1.5">
                      {item.status === 'ok' ? (
                        <span className="w-4.5 h-4.5 rounded-full bg-[#10B981] text-white flex items-center justify-center shrink-0 mt-0.5">
                          <Check size={11} strokeWidth={3} />
                        </span>
                      ) : (
                        <span className="w-4.5 h-4.5 rounded-full bg-[#F59E0B] text-white flex items-center justify-center text-[10.5px] font-extrabold shrink-0 mt-0.5">
                          !
                        </span>
                      )}
                      <div>
                        <p className="text-[12.5px] font-bold text-slate-900">{item.title}</p>
                        <p className="text-[11.5px] text-slate-500 mt-0.5">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom actions */}
            <div className="pt-2.5">
              <div className="flex gap-3">
                <button className="flex-1 bg-[#1565F9] hover:bg-blue-700 text-white text-[13px] font-bold py-2 rounded-xl transition shadow-sm cursor-pointer">
                  Lưu thay đổi
                </button>
                <button className="flex-1 flex items-center justify-center gap-2 border border-rose-200 bg-[#FEE2E2]/60 text-[#DC2626] text-[13px] font-bold py-2 rounded-xl hover:bg-rose-100 transition cursor-pointer">
                  <Trash2 size={14} />
                  <span>Lưu trữ lớp</span>
                </button>
              </div>
              <p className="text-[11px] text-slate-400 text-center mt-1.5">
                Lưu trữ lớp không xóa hồ sơ hay lịch sử đóng góp.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
