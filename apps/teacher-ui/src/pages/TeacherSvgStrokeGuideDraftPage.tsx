import { useState, type FormEvent } from 'react'
import { LoaderCircle, Pencil, Sparkles } from 'lucide-react'
import type { SvgTopicStrokeGuideDraftV1 } from '../domain/svgGuide'
import { SvgGuideRenderer } from '../components/SvgGuideRenderer'
import { svgGuideDraftService } from '../services/svgGuideDraftService'

export function TeacherSvgStrokeGuideDraftPage() {
  const [topic, setTopic] = useState('')
  const [draft, setDraft] = useState<SvgTopicStrokeGuideDraftV1 | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setDraft(null)
    setBusy(true)
    try {
      setDraft(await svgGuideDraftService.generate(topic.trim()))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không tạo được hướng dẫn nét SVG.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <header className="flex items-start gap-4">
        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-blue-100 text-blue-800">
          <Pencil aria-hidden="true" size={24} />
        </div>
        <div>
          <p className="text-sm font-bold uppercase tracking-wide text-blue-800">Teacher · bản nháp cần xem lại</p>
          <h1 className="mt-1 text-2xl font-extrabold text-slate-950">Tạo hướng dẫn nét vẽ</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Mỗi bước thêm nét mới để trẻ vẽ theo. Bản xem trước chưa được lưu vào giáo án hay thư viện.</p>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[minmax(280px,0.7fr)_minmax(440px,1.3fr)]">
        <form onSubmit={submit} className="h-fit space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <label className="block text-sm font-bold text-slate-800" htmlFor="svg-guide-topic">Chủ đề</label>
          <input
            id="svg-guide-topic"
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            maxLength={120}
            minLength={2}
            required
            placeholder="Ví dụ: con hươu"
            className="w-full rounded-xl border border-slate-300 px-3 py-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
          />
          <p className="text-xs leading-5 text-slate-500">Chỉ gửi chủ đề và độ khó chung; không gửi hồ sơ trẻ hay tranh vẽ.</p>
          {error ? <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</p> : null}
          <button disabled={busy || topic.trim().length < 2} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-700 px-4 py-3 font-bold text-white disabled:opacity-50">
            {busy ? <LoaderCircle className="animate-spin" size={18} /> : <Sparkles size={18} />}
            {busy ? 'Đang tạo bản nháp…' : 'Tạo guide SVG'}
          </button>
        </form>

        {draft ? <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-amber-700">Bản nháp · chưa lưu</p>
              <h2 className="mt-1 text-xl font-extrabold text-slate-950">{draft.guide.title_vi}</h2>
              <p className="mt-1 text-sm text-slate-600">{draft.stage_count} bước · {draft.path_count} nét · Qwen3.5</p>
              {draft.reference_source ? <p className="mt-2 max-w-2xl text-xs leading-5 text-slate-500">
                Tham chiếu hình: {draft.reference_source.dataset_name} v{draft.reference_source.dataset_revision}
                {draft.reference_source.dataset_doi
                  ? <> · DOI {draft.reference_source.dataset_doi}</>
                  : draft.reference_source.dataset_uri
                    ? <> · <a href={draft.reference_source.dataset_uri} target="_blank" rel="noreferrer">Nguồn</a></>
                    : null}
                {' · '}SHA-256 {draft.reference_source.source_sha256.slice(0, 12)}…
                {' · '}{draft.reference_source.license_id}
              </p> : null}
            </div>
            <span className="rounded-full bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-800">Teacher cần duyệt</span>
          </div>
          <SvgGuideRenderer document={draft.document} guide={draft.guide} />
        </section> : <div className="grid min-h-64 place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
          Nhập chủ đề để xem các nét được thêm dần qua từng bước.
        </div>}
      </section>
    </main>
  )
}
