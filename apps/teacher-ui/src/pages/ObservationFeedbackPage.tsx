import { useState } from 'react'
import { loadActiveSession } from '../services/activeSessionStore'
import {
  observationService,
  type TeacherObservationLevel,
  type TeacherObservationReceipt,
} from '../services/observationService'

const LEVELS: Array<{ value: TeacherObservationLevel; label: string }> = [
  { value: 'not_observed', label: 'Chưa quan sát' },
  { value: 'with_support', label: 'Thể hiện với hỗ trợ' },
  { value: 'during_activity', label: 'Thể hiện trong hoạt động' },
  { value: 'extended_idea', label: 'Mở rộng ý tưởng' },
]

export function ObservationFeedbackPage() {
  const activeSession = loadActiveSession()
  const children = activeSession?.admittedChildren ?? []
  const [selectedChildId, setSelectedChildId] = useState('')
  const [level, setLevel] = useState<TeacherObservationLevel | null>(null)
  const [comment, setComment] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [receipt, setReceipt] = useState<TeacherObservationReceipt | null>(null)
  const selectedChild = children.find((child) => child.childId === selectedChildId) ?? children[0]

  const saveObservation = async () => {
    if (!activeSession || !selectedChild || !level || !comment.trim()) {
      setError('Chọn hồ sơ, mức quan sát và nhập ghi chú trước khi lưu.')
      return
    }
    setSaving(true)
    setError('')
    try {
      const saved = await observationService.submitObservation({
        organizationId: activeSession.organizationId,
        classId: activeSession.classId,
        sessionId: activeSession.sessionId,
        childId: selectedChild.childId,
        level,
        comment: comment.trim(),
      })
      setReceipt(saved)
    } catch (cause) {
      setError(observationService.formatError(cause))
    } finally {
      setSaving(false)
    }
  }

  if (!activeSession || children.length === 0) {
    return (
      <main className="mx-auto max-w-3xl space-y-4 px-7 py-8">
        <h1 className="text-2xl font-bold text-slate-900">Phản hồi & quan sát</h1>
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
          <p>Chưa có phiên và danh sách trẻ được tiếp nhận trong bộ nhớ phiên của trình duyệt này.</p>
          <p className="mt-2">Hãy mở phiên BE1, tiếp nhận trẻ rồi quay lại. API đọc lại roster sau khi refresh chưa có.</p>
          <a className="mt-4 inline-block font-semibold text-blue-800 underline" href="/session/setup">Mở thiết lập phiên</a>
        </section>
      </main>
    )
  }

  if (activeSession.state !== 'active' && activeSession.state !== 'paused') {
    return (
      <main className="mx-auto max-w-3xl space-y-4 px-7 py-8">
        <h1 className="text-2xl font-bold text-slate-900">Phản hồi & quan sát</h1>
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
          Phiên hiện ở trạng thái “{activeSession.state}”. Quan sát này chỉ được gửi trong phiên đang chạy hoặc tạm dừng.
        </section>
      </main>
    )
  }

  const resetForm = () => {
    setLevel(null)
    setComment('')
    setReceipt(null)
    setError('')
  }

  return (
    <main className="mx-auto max-w-4xl space-y-5 px-7 py-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">Quan sát do giáo viên nhập · lưu qua BE1</p>
        <h1 className="mt-1 text-3xl font-extrabold text-slate-900">Phản hồi & quan sát</h1>
        <p className="mt-2 text-sm text-slate-600">Phiên {activeSession.title} · {activeSession.sessionId}</p>
      </header>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <label className="block text-sm font-semibold text-slate-800" htmlFor="observation-child">Hồ sơ trẻ đã được tiếp nhận</label>
        <select
          id="observation-child"
          value={selectedChild?.childId ?? ''}
          onChange={(event) => { setSelectedChildId(event.target.value); setReceipt(null) }}
          disabled={Boolean(receipt) || saving}
          className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm"
        >
          {children.map((child) => <option key={child.childId} value={child.childId}>{child.displayName}</option>)}
        </select>

        <fieldset className="mt-6">
          <legend className="text-sm font-semibold text-slate-800">Mức quan sát</legend>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {LEVELS.map((item) => (
              <label key={item.value} className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 text-sm ${level === item.value ? 'border-blue-500 bg-blue-50 text-blue-900' : 'border-slate-200 text-slate-700'}`}>
                <input
                  type="radio"
                  name="observation-level"
                  value={item.value}
                  checked={level === item.value}
                  disabled={Boolean(receipt) || saving}
                  onChange={() => { setLevel(item.value); setReceipt(null) }}
                />
                {item.label}
              </label>
            ))}
          </div>
        </fieldset>

        <label className="mt-6 block text-sm font-semibold text-slate-800" htmlFor="observation-comment">Ghi chú dựa trên điều giáo viên trực tiếp quan sát</label>
        <textarea
          id="observation-comment"
          rows={4}
          maxLength={4000}
          value={comment}
          disabled={Boolean(receipt) || saving}
          onChange={(event) => { setComment(event.target.value); setReceipt(null) }}
          placeholder="Ghi lại hành vi hoặc lời nói cụ thể đã quan sát…"
          className="mt-2 w-full resize-y rounded-xl border border-slate-300 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-50"
        />
        <p className="mt-1 text-xs text-slate-500">Thông tin này được lưu dưới dạng observation của giáo viên; không phải phản hồi do trẻ gửi hoặc kết luận AI.</p>

        {error && <div role="alert" className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{error}</div>}
        {receipt && <div role="status" className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">BE1 đã xác nhận lưu observation <code>{receipt.observation_id}</code>. Lưu này không tự chuyển chặng SRS hoặc hoàn tất phiên.</div>}

        <div className="mt-5 flex flex-wrap gap-3">
          {receipt
            ? <button onClick={resetForm} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700">Ghi nhận quan sát khác</button>
            : <button onClick={() => void saveObservation()} disabled={saving || !selectedChild} className="rounded-xl bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{saving ? 'Đang lưu qua BE1…' : 'Lưu observation qua BE1'}</button>}
        </div>
      </section>

      <aside className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
        BE1 chưa có API để đọc lại roster sau khi làm mới, nhận reflection trực tiếp từ Child, duyệt assessment, hoặc lưu kết quả chặng. Nếu mạng ngắt sau khi gửi, API hiện không có khoá idempotency cho observation; hãy kiểm tra với quản trị viên trước khi gửi lặp.
      </aside>
    </main>
  )
}
