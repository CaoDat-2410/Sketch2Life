import type { SvgCatalogAssetV1, SvgGuideRevisionV1 } from '../domain/svgGuide'

type Props = Readonly<{
  asset: SvgCatalogAssetV1
  revisions: SvgGuideRevisionV1[]
  currentPrincipalRef: string | null
  reason: string
  busy: boolean
  onReasonChange: (value: string) => void
  onReviewSource: (decision: 'APPROVE' | 'REJECT') => void
  onReviewGuide: (revision: SvgGuideRevisionV1, decision: 'APPROVE' | 'REJECT') => void
}>

export function SvgReviewPanel({
  asset,
  revisions,
  currentPrincipalRef,
  reason,
  busy,
  onReasonChange,
  onReviewSource,
  onReviewGuide,
}: Props) {
  const canReviewSource = currentPrincipalRef !== null
    && asset.created_by !== currentPrincipalRef
    && asset.review_state === 'PENDING_EDUCATOR_REVIEW'

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5" aria-labelledby="svg-review-heading">
      <div>
        <h2 id="svg-review-heading" className="text-lg font-bold text-slate-900">Duyệt độc lập theo phiên bản</h2>
        <p className="mt-1 text-sm text-slate-600">Quyết định được gắn với mã hash chính xác. Người tạo không thể tự duyệt nguồn hoặc hướng dẫn của mình.</p>
      </div>
      {canReviewSource && <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
        <p className="font-semibold text-amber-950">Nguồn SVG chờ giáo viên khác duyệt</p>
        <p className="mt-1 break-all font-mono text-xs text-amber-900">{asset.source_sha256}</p>
        <label className="mt-3 block text-xs font-semibold text-amber-950">Lý do nếu từ chối
          <textarea value={reason} onChange={(event) => onReasonChange(event.target.value)} rows={2} maxLength={1000} className="mt-1 block w-full rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm font-normal" />
        </label>
        <div className="mt-3 flex gap-2">
          <button type="button" disabled={busy} onClick={() => onReviewSource('APPROVE')} className="rounded-lg bg-emerald-700 px-3 py-2 text-sm font-bold text-white disabled:opacity-50">Duyệt nguồn</button>
          <button type="button" disabled={busy || !reason.trim()} onClick={() => onReviewSource('REJECT')} className="rounded-lg border border-red-300 bg-white px-3 py-2 text-sm font-bold text-red-800 disabled:opacity-50">Từ chối</button>
        </div>
      </div>}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Các revision hướng dẫn</h3>
        {revisions.length === 0 && <p className="text-sm text-slate-500">Chưa có revision hướng dẫn được lưu cho nguồn này.</p>}
        {revisions.map((revision) => {
          const canReview = currentPrincipalRef !== null
            && revision.authored_by !== currentPrincipalRef
            && revision.review_state === 'PENDING'
          return <article key={revision.guide_revision_id} className="rounded-xl border border-slate-200 p-3">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-semibold text-slate-900">{revision.guide.title_vi} · revision {revision.guide_revision}</p>
                <p className="mt-1 text-xs text-slate-500">{revision.review_state === 'PENDING' ? 'Chờ duyệt' : revision.review_state === 'APPROVED' ? 'Đã duyệt' : 'Đã từ chối'} · {revision.visibility_scope === 'PLATFORM' ? 'Nền tảng' : 'Trong trường'}</p>
                <p className="mt-1 break-all font-mono text-[11px] text-slate-500">Hash hướng dẫn: {revision.guide_sha256}</p>
              </div>
              {canReview && <div className="flex gap-2">
                <button type="button" disabled={busy} onClick={() => onReviewGuide(revision, 'APPROVE')} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-white disabled:opacity-50">Duyệt</button>
                <button type="button" disabled={busy || !reason.trim()} onClick={() => onReviewGuide(revision, 'REJECT')} className="rounded-lg border border-red-300 px-3 py-2 text-xs font-bold text-red-800 disabled:opacity-50">Từ chối</button>
              </div>}
            </div>
          </article>
        })}
      </div>
    </section>
  )
}
