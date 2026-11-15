import { useState, type FormEvent } from 'react'
import { Image as ImageIcon, LoaderCircle, Sparkles, Trash2 } from 'lucide-react'
import type { TeacherSvgIllustrationDraftV1 } from '../domain/svgGuide'
import { SvgDocumentPreview } from '../components/SvgDocumentPreview'
import { svgIllustrationService } from '../services/svgIllustrationService'

type VisualStyle = 'warm_storybook' | 'simple_classroom' | 'clean_outline'

const STYLE_LABELS: Readonly<Record<VisualStyle, string>> = {
  warm_storybook: 'Sách tranh ấm áp',
  simple_classroom: 'Rõ nét khi trình chiếu',
  clean_outline: 'Nét viền gọn, ít màu',
}

export function TeacherSvgIllustrationDraftPage() {
  const [topic, setTopic] = useState('')
  const [ageMonths, setAgeMonths] = useState('')
  const [visualStyle, setVisualStyle] = useState<VisualStyle>('warm_storybook')
  const [draft, setDraft] = useState<TeacherSvgIllustrationDraftV1 | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setDraft(null)
    setBusy(true)
    try {
      const result = await svgIllustrationService.generateDraft({
        topic: topic.trim(),
        target_age_months: Number(ageMonths),
        visual_style: visualStyle,
      })
      setDraft(result)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không tạo được minh họa SVG.')
    } finally {
      setBusy(false)
    }
  }

  function clearDraft() {
    setDraft(null)
    setError('')
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <header className="flex items-start gap-4">
        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-blue-100 text-blue-800">
          <ImageIcon aria-hidden="true" size={24} />
        </div>
        <div>
          <p className="text-sm font-bold uppercase tracking-wide text-blue-800">Teacher · bản thử nghiệm có kiểm soát</p>
          <h1 className="mt-1 text-2xl font-extrabold text-slate-950">Minh họa SVG cho bài giảng</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Tạo một bản nháp vector từ chủ đề để xem trước trong trình duyệt. Kết quả chưa được lưu vào giáo án hoặc thư viện.</p>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[minmax(280px,0.82fr)_minmax(420px,1.18fr)]">
        <form onSubmit={(event) => void submit(event)} className="h-fit space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <label className="block space-y-2">
            <span className="text-sm font-bold text-slate-800">Chủ đề</span>
            <input
              aria-label="Chủ đề"
              required
              minLength={2}
              maxLength={120}
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Nhập con vật hoặc đồ vật"
              className="w-full rounded-xl border border-slate-300 px-3.5 py-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-bold text-slate-800">Tuổi mục tiêu</span>
            <div className="flex items-center gap-3">
              <input
                aria-label="Tuổi mục tiêu theo tháng"
                type="number"
                required
                min={36}
                max={120}
                value={ageMonths}
                onChange={(event) => setAgeMonths(event.target.value)}
                placeholder="36–120"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              />
              <span className="shrink-0 text-sm text-slate-600">tháng</span>
            </div>
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-bold text-slate-800">Phong cách minh họa</span>
            <select
              aria-label="Phong cách minh họa"
              value={visualStyle}
              onChange={(event) => setVisualStyle(event.target.value as VisualStyle)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
            >
              {Object.entries(STYLE_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <button
            type="submit"
            disabled={busy || topic.trim().length < 2 || Number(ageMonths) < 36 || Number(ageMonths) > 120}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-700 px-4 py-3 text-sm font-bold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? <LoaderCircle aria-hidden="true" className="animate-spin" size={18} /> : <Sparkles aria-hidden="true" size={18} />}
            {busy ? 'Modal đang tạo SVG…' : 'Tạo bản nháp SVG'}
          </button>
          {busy && <p role="status" className="text-xs leading-5 text-slate-600">Lần đầu có thể chờ GPU khởi động. Không gửi lại yêu cầu nếu trạng thái chưa rõ.</p>}
          {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-800">{error}</p>}
          <p className="text-xs leading-5 text-slate-500">Chỉ gửi chủ đề, độ tuổi và phong cách đã chọn. Không gửi ảnh, hồ sơ trẻ hay dữ liệu cá nhân.</p>
        </form>

        <div className="min-h-[420px]">
          {draft ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
                <div>
                  <p className="text-sm font-bold text-amber-950">Bản nháp AI · cần giáo viên xem lại</p>
                  <p className="mt-1 text-xs text-amber-900">Chưa lưu · chưa được duyệt · chưa public · {draft.path_count} nét vector</p>
                </div>
                <button type="button" onClick={clearDraft} className="inline-flex items-center gap-2 rounded-lg border border-amber-300 bg-white px-3 py-2 text-xs font-semibold text-amber-950">
                  <Trash2 aria-hidden="true" size={15} /> Xóa bản nháp
                </button>
              </div>
              <SvgDocumentPreview document={draft.document} title={draft.title_vi} altText={draft.alt_text_vi} />
              <p className="break-all text-[11px] text-slate-500">Model {draft.model.id} · revision {draft.model.revision} · SHA-256 {draft.document_sha256}</p>
            </div>
          ) : (
            <div className="grid min-h-[420px] place-items-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
              <div className="max-w-sm">
                <div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-slate-100 text-slate-500"><ImageIcon aria-hidden="true" size={25} /></div>
                <h2 className="mt-4 text-base font-bold text-slate-800">Bản xem trước SVG</h2>
                <p className="mt-2 text-sm leading-6 text-slate-500">Nhập chủ đề và độ tuổi, sau đó tạo một bản nháp để xem các path vector được render trực tiếp.</p>
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
