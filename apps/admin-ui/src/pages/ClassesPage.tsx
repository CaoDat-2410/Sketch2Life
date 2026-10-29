import { useEffect, useState } from 'react'
import { Plus, RefreshCw, School } from 'lucide-react'
import { classService, type Be1Class } from '../services/classService'

export function ClassesPage() {
  const [classes, setClasses] = useState<Be1Class[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const selected = classes.find((item) => item.class_id === selectedId) ?? classes[0]

  const refresh = async () => {
    setError('')
    try {
      const items = await classService.listClasses()
      setClasses(items)
      setSelectedId((current) => items.some((item) => item.class_id === current) ? current : items[0]?.class_id ?? '')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không tải được danh sách lớp từ BE1.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void refresh() }, [])

  const createClass = async (event: React.FormEvent) => {
    event.preventDefault()
    const name = displayName.trim()
    if (!name) return
    setCreating(true)
    setError('')
    try {
      const created = await classService.createClass(name)
      setDisplayName('')
      await refresh()
      setSelectedId(created.class_id)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'BE1 chưa tạo được lớp.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <main className="mx-auto max-w-6xl space-y-5 px-7 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div><p className="text-sm font-semibold text-blue-700">Dữ liệu trực tiếp · BE1</p><h1 className="mt-1 text-3xl font-extrabold text-slate-900">Lớp học</h1><p className="mt-2 text-sm text-slate-600">Danh sách và tạo lớp dùng API được cấp quyền theo tài khoản school_admin.</p></div>
        <button onClick={() => void refresh()} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800 disabled:opacity-50"><RefreshCw size={16} />Làm mới từ BE1</button>
      </header>

      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>}

      <form onSubmit={createClass} className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-5">
        <label className="min-w-64 flex-1 text-sm font-semibold text-slate-800">Tên lớp mới
          <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} maxLength={200} required className="mt-2 block w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal" placeholder="Ví dụ: Lớp Lá 1" />
        </label>
        <button type="submit" disabled={creating || !displayName.trim()} className="inline-flex items-center gap-2 rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white disabled:opacity-50"><Plus size={17} />{creating ? 'Đang lưu…' : 'Tạo lớp trên BE1'}</button>
      </form>

      <section className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="mb-4 text-lg font-bold text-slate-900">Danh sách được cấp quyền</h2>
          {loading ? <p className="text-sm text-slate-600">Đang tải lớp…</p> : classes.length === 0 ? <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">BE1 chưa trả lớp nào cho tài khoản này.</p> : <ul className="divide-y divide-slate-100">{classes.map((item) => <li key={item.class_id}>
            <button onClick={() => setSelectedId(item.class_id)} className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left ${selected?.class_id === item.class_id ? 'bg-blue-50' : 'hover:bg-slate-50'}`}>
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700"><School size={19} /></span>
              <span className="min-w-0 flex-1"><span className="block font-semibold text-slate-900">{item.display_name}</span><span className="block truncate text-xs text-slate-500">{item.class_id}</span></span>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${item.state === 'active' ? 'bg-emerald-50 text-emerald-800' : 'bg-slate-100 text-slate-700'}`}>{item.state}</span>
            </button>
          </li>)}</ul>}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-bold text-slate-900">Thông tin lớp</h2>
          {selected ? <div className="mt-4 space-y-3 text-sm"><div><p className="text-xs font-semibold uppercase text-slate-500">Tên</p><p className="mt-1 font-semibold text-slate-900">{selected.display_name}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Mã lớp</p><p className="mt-1 break-all font-mono text-slate-800">{selected.class_id}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Trạng thái BE1</p><p className="mt-1 font-semibold text-slate-800">{selected.state}</p></div></div> : <p className="mt-3 text-sm text-slate-600">Chọn lớp trong danh sách để xem thông tin BE1 đã trả.</p>}
          <p className="mt-5 rounded-xl bg-amber-50 p-3 text-xs text-amber-950">API hiện không trả nhóm tuổi, giáo viên phụ trách, số hồ sơ, trạng thái consent tổng hợp, chỉnh sửa hoặc lưu trữ lớp. Những mục này chưa được suy ra hay giả lập.</p>
        </div>
      </section>
    </main>
  )
}
