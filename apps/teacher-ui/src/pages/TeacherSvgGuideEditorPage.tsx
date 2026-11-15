import { useEffect, useMemo, useRef, useState } from 'react'
import type {
  LessonContentV1,
  LessonDetailV1,
  LessonPresentationSlideV1,
  LessonSummaryV1,
  SketchStrokeGuideV3,
  SvgCatalogAssetV1,
  SvgGuideRevisionV1,
  SvgGuideRevisionDraft,
} from '../domain/svgGuide'
import { SvgGuideRenderer } from '../components/SvgGuideRenderer'
import { SvgReviewPanel } from '../components/TeacherSvgGuideEditor'
import { TeacherSvgGuidePresentation } from '../components/TeacherDeckPresentation'
import { SvgCatalogServiceError, svgCatalogService } from '../services/svgCatalogService'
import { authService } from '../services/authService'

type StageDraft = { instruction_vi: string }
type EditorSnapshot = {
  guideTitle: string
  stageDrafts: StageDraft[]
  pathDrafts: SvgGuideRevisionDraft[]
}
type LocalEditorDraft = {
  base_revision: number
  asset_id: string
  slide_id: string
  guide_title: string
  stage_drafts: StageDraft[]
  path_drafts: SvgGuideRevisionDraft[]
}

const MIN_STAGES = 4
const MAX_STAGES = 8
const AUTOSAVE_MS = 1500
const ASSET_FILE_LIMIT = 1_000_000
const MAX_UNDO_STATES = 100

export function TeacherSvgGuideEditorPage() {
  const [lessons, setLessons] = useState<LessonSummaryV1[]>([])
  const [assets, setAssets] = useState<SvgCatalogAssetV1[]>([])
  const [guideRevisions, setGuideRevisions] = useState<SvgGuideRevisionV1[]>([])
  const [lesson, setLesson] = useState<LessonDetailV1 | null>(null)
  const [assetId, setAssetId] = useState('')
  const [slideId, setSlideId] = useState('')
  const [guideTitle, setGuideTitle] = useState('')
  const [stageDrafts, setStageDrafts] = useState<StageDraft[]>(Array.from({ length: MIN_STAGES }, () => ({ instruction_vi: '' })))
  const [pathDrafts, setPathDrafts] = useState<SvgGuideRevisionDraft[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingLesson, setLoadingLesson] = useState(false)
  const [saving, setSaving] = useState(false)
  const [autosaveBlocked, setAutosaveBlocked] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [conflict, setConflict] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [reviewReason, setReviewReason] = useState('')
  const [reviewBusy, setReviewBusy] = useState(false)
  const [presentationOpen, setPresentationOpen] = useState(false)
  const [savedGuideRevision, setSavedGuideRevision] = useState<SvgGuideRevisionV1 | null>(null)
  const [savedGuideSignature, setSavedGuideSignature] = useState('')
  const [undoCursor, setUndoCursor] = useState(0)
  const [undoLength, setUndoLength] = useState(1)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadBusy, setUploadBusy] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadTopic, setUploadTopic] = useState('')
  const [uploadAlt, setUploadAlt] = useState('')
  const [sourceUri, setSourceUri] = useState('')
  const [licenseId, setLicenseId] = useState('')
  const [licenseUri, setLicenseUri] = useState('')
  const mountedRef = useRef(true)
  const saveTimerRef = useRef<number | null>(null)
  const selectedAssetIdRef = useRef('')
  const undoHistoryRef = useRef<EditorSnapshot[]>([{ guideTitle: '', stageDrafts: Array.from({ length: MIN_STAGES }, () => ({ instruction_vi: '' })), pathDrafts: [] }])
  const undoCursorRef = useRef(0)

  const asset = assets.find((item) => item.catalog_entry_id === assetId) ?? null
  const currentPrincipalRef = authService.getCurrentUser()?.uid ?? null
  const guideResult = useMemo(
    () => (lesson && asset ? buildGuide({ asset, slideId, guideTitle, stageDrafts, pathDrafts }) : { guide: null, error: '' }),
    [lesson, asset, slideId, guideTitle, stageDrafts, pathDrafts],
  )
  const guide = guideResult.guide
  const updatedContent = useMemo(() => {
    if (!lesson || !asset || !guide) return null
    const base = lesson.current_version.content
    const priorSlides = base.presentation?.slides ?? []
    const slide: LessonPresentationSlideV1 = {
      slide_id: slideId,
      kind: 'drawing_guide',
      title_vi: guideTitle.trim(),
      body_vi: '',
      guide,
    }
    const slides = [...priorSlides.filter((item) => item.slide_id !== slideId), slide]
    return {
      ...base,
      presentation: { schema_version: 'LessonPresentationV1' as const, slides },
    } satisfies LessonContentV1
  }, [lesson, asset, guide, slideId, guideTitle])

  useEffect(() => {
    mountedRef.current = true
    void loadCatalog()
    return () => {
      mountedRef.current = false
      if (saveTimerRef.current !== null) window.clearTimeout(saveTimerRef.current)
    }
  }, [])

  useEffect(() => {
    if (!lesson || !asset || !dirty) return
    const draftKey = localDraftKey(lesson.lesson_id)
    const localDraft: LocalEditorDraft = {
      base_revision: lesson.revision,
      asset_id: asset.catalog_entry_id,
      slide_id: slideId,
      guide_title: guideTitle,
      stage_drafts: stageDrafts,
      path_drafts: pathDrafts,
    }
    localStorage.setItem(draftKey, JSON.stringify(localDraft))
    if (conflict || saving || autosaveBlocked || !updatedContent || !guide) return
    if (saveTimerRef.current !== null) window.clearTimeout(saveTimerRef.current)
    saveTimerRef.current = window.setTimeout(() => void saveCurrentContent(updatedContent), AUTOSAVE_MS)
    return () => {
      if (saveTimerRef.current !== null) window.clearTimeout(saveTimerRef.current)
    }
  }, [lesson, asset, dirty, updatedContent, guide, conflict, saving, autosaveBlocked, slideId, guideTitle, stageDrafts, pathDrafts])

  async function loadCatalog(): Promise<void> {
    setLoading(true)
    setError('')
    try {
      const [lessonPage, assetPage] = await Promise.all([
        svgCatalogService.listLessons(),
        svgCatalogService.listAssets(),
      ])
      if (!mountedRef.current) return
      setLessons(lessonPage.items)
      setAssets(assetPage.items.filter((item) => Boolean(item.document)))
    } catch (cause) {
      if (mountedRef.current) setError(errorMessage(cause))
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }

  async function chooseLesson(lessonId: string): Promise<void> {
    setLoadingLesson(true)
    setError('')
    setNotice('')
    setConflict(false)
    setDirty(false)
    setAutosaveBlocked(false)
    try {
      const detail = await svgCatalogService.getLesson(lessonId)
      const priorSlide = detail.current_version.content.presentation?.slides[0]
      const matchingAsset = priorSlide
        ? assets.find((item) => item.source_asset_ref === priorSlide.guide.source_asset_ref && item.source_asset_version === priorSlide.guide.source_asset_version)
        : undefined
      if (matchingAsset && priorSlide) {
        loadEditorState(detail, matchingAsset, priorSlide.guide, priorSlide.slide_id)
        void loadGuideRevisions(matchingAsset)
      } else {
        setLesson(detail)
        setAssetId('')
        selectedAssetIdRef.current = ''
        setGuideRevisions([])
        setSavedGuideRevision(null)
        setSavedGuideSignature('')
        setSlideId(`guide-${crypto.randomUUID()}`)
        setGuideTitle(detail.current_version.content.drawing_subject || detail.current_version.content.title)
        setStageDrafts(Array.from({ length: MIN_STAGES }, () => ({ instruction_vi: '' })))
        setPathDrafts([])
        resetUndoHistory({ guideTitle: detail.current_version.content.drawing_subject || detail.current_version.content.title, stageDrafts: Array.from({ length: MIN_STAGES }, () => ({ instruction_vi: '' })), pathDrafts: [] })
      }
      const saved = readLocalDraft(detail.lesson_id)
      if (saved) {
        const savedAsset = assets.find((item) => item.catalog_entry_id === saved.asset_id)
        if (savedAsset?.document) {
          setAssetId(saved.asset_id)
          selectedAssetIdRef.current = saved.asset_id
          void loadGuideRevisions(savedAsset)
          setSlideId(saved.slide_id)
          setGuideTitle(saved.guide_title)
          setStageDrafts(saved.stage_drafts)
          setPathDrafts(saved.path_drafts)
          resetUndoHistory({ guideTitle: saved.guide_title, stageDrafts: saved.stage_drafts, pathDrafts: saved.path_drafts })
          setConflict(saved.base_revision !== detail.revision)
          setDirty(true)
          setNotice(saved.base_revision === detail.revision
            ? 'Đã khôi phục bản nháp được lưu trên trình duyệt.'
            : 'Có bản nháp cục bộ dựa trên revision cũ. Hãy chọn cách xử lý trước khi lưu tiếp.')
        }
      }
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setLoadingLesson(false)
    }
  }

  function loadEditorState(
    detail: LessonDetailV1,
    selectedAsset: SvgCatalogAssetV1,
    existingGuide?: SketchStrokeGuideV3,
    existingSlideId?: string,
  ): void {
    setLesson(detail)
    setAssetId(selectedAsset.catalog_entry_id)
    selectedAssetIdRef.current = selectedAsset.catalog_entry_id
    setSlideId(existingSlideId ?? `guide-${crypto.randomUUID()}`)
    setGuideTitle(existingGuide?.title_vi ?? selectedAsset.title_vi)
    if (!selectedAsset.document) return
    const stageCount = existingGuide?.stages.length ?? MIN_STAGES
    const nextStages = Array.from({ length: stageCount }, (_, index) => ({
      instruction_vi: existingGuide?.stages[index]?.instruction_vi ?? '',
    }))
    const nextPaths = selectedAsset.document.paths.map((path) => {
      const part = existingGuide?.parts.find((item) => item.path_ids.includes(path.path_id))
      const stage = existingGuide?.stages.find((item) => item.new_path_ids.includes(path.path_id))
      return {
        path_id: path.path_id,
        part_id: part?.part_id ?? '',
        label_vi: part?.label_vi ?? '',
        stage_index: stage ? stage.step_index - 1 : null,
      }
    })
    setStageDrafts(nextStages)
    setPathDrafts(nextPaths)
    resetUndoHistory({ guideTitle: existingGuide?.title_vi ?? selectedAsset.title_vi, stageDrafts: nextStages, pathDrafts: nextPaths })
  }

  function chooseAsset(nextAssetId: string): void {
    const selectedAsset = assets.find((item) => item.catalog_entry_id === nextAssetId)
    if (!selectedAsset?.document) return
    selectAssetRecord(selectedAsset)
  }

  function selectAssetRecord(selectedAsset: SvgCatalogAssetV1): void {
    if (!lesson || !selectedAsset.document) return
    setAssetId(selectedAsset.catalog_entry_id)
    selectedAssetIdRef.current = selectedAsset.catalog_entry_id
    setSlideId(`guide-${crypto.randomUUID()}`)
    setGuideTitle(selectedAsset.title_vi)
    const nextStages = Array.from({ length: MIN_STAGES }, () => ({ instruction_vi: '' }))
    const nextPaths = selectedAsset.document.paths.map((path) => ({ path_id: path.path_id, part_id: '', label_vi: '', stage_index: null }))
    setStageDrafts(nextStages)
    setPathDrafts(nextPaths)
    resetUndoHistory({ guideTitle: selectedAsset.title_vi, stageDrafts: nextStages, pathDrafts: nextPaths })
    setSavedGuideRevision(null)
    setSavedGuideSignature('')
    setGuideRevisions([])
    void loadGuideRevisions(selectedAsset)
    markDirty()
  }

  async function loadGuideRevisions(selectedAsset: SvgCatalogAssetV1): Promise<void> {
    try {
      const page = await svgCatalogService.listGuideRevisions(selectedAsset)
      if (mountedRef.current && selectedAssetIdRef.current === selectedAsset.catalog_entry_id) setGuideRevisions(page.items)
    } catch (cause) {
      if (mountedRef.current) setError(errorMessage(cause))
    }
  }

  function markDirty(): void {
    setDirty(true)
    setAutosaveBlocked(false)
    setNotice('')
  }

  function resetUndoHistory(snapshot: EditorSnapshot): void {
    undoHistoryRef.current = [cloneSnapshot(snapshot)]
    undoCursorRef.current = 0
    setUndoCursor(0)
    setUndoLength(1)
  }

  function recordUndoSnapshot(snapshot: EditorSnapshot): void {
    const current = undoHistoryRef.current[undoCursorRef.current]
    if (current && JSON.stringify(current) === JSON.stringify(snapshot)) return
    let next = [...undoHistoryRef.current.slice(0, undoCursorRef.current + 1), cloneSnapshot(snapshot)]
    if (next.length > MAX_UNDO_STATES) next = next.slice(next.length - MAX_UNDO_STATES)
    undoHistoryRef.current = next
    undoCursorRef.current = next.length - 1
    setUndoCursor(undoCursorRef.current)
    setUndoLength(next.length)
  }

  function moveUndoHistory(delta: -1 | 1): void {
    const nextIndex = Math.min(undoHistoryRef.current.length - 1, Math.max(0, undoCursorRef.current + delta))
    if (nextIndex === undoCursorRef.current) return
    const snapshot = undoHistoryRef.current[nextIndex]
    undoCursorRef.current = nextIndex
    setUndoCursor(nextIndex)
    setGuideTitle(snapshot.guideTitle)
    setStageDrafts(cloneSnapshot(snapshot).stageDrafts)
    setPathDrafts(cloneSnapshot(snapshot).pathDrafts)
    markDirty()
  }

  function changeStageCount(delta: number): void {
    const nextCount = Math.min(MAX_STAGES, Math.max(MIN_STAGES, stageDrafts.length + delta))
    if (nextCount === stageDrafts.length) return
    const nextStages = Array.from({ length: nextCount }, (_, index) => stageDrafts[index] ?? { instruction_vi: '' })
    const nextPaths = delta < 0 ? pathDrafts.map((path) => ({
      ...path,
      stage_index: path.stage_index !== null && path.stage_index >= nextCount ? null : path.stage_index,
    })) : pathDrafts
    setStageDrafts(nextStages)
    setPathDrafts(nextPaths)
    recordUndoSnapshot({ guideTitle, stageDrafts: nextStages, pathDrafts: nextPaths })
    markDirty()
  }

  async function saveCurrentContent(content: LessonContentV1): Promise<void> {
    if (!lesson || saving || conflict) return
    const targetGuide = content.presentation?.slides.find((item) => item.slide_id === slideId)?.guide
    if (!asset || !targetGuide) return
    setSaving(true)
    setError('')
    try {
      const signature = JSON.stringify(targetGuide)
      let revision = savedGuideRevision
      if (!revision || savedGuideSignature !== signature) {
        revision = await svgCatalogService.createGuideRevision(asset, targetGuide)
        setSavedGuideRevision(revision)
        setSavedGuideSignature(signature)
        setGuideRevisions((current) => [revision!, ...current.filter((item) => item.guide_revision_id !== revision!.guide_revision_id)])
      }
      const updated = await svgCatalogService.updateLesson(lesson.lesson_id, lesson.revision, content)
      setLesson(updated)
      setDirty(false)
      setConflict(false)
      setAutosaveBlocked(false)
      localStorage.removeItem(localDraftKey(updated.lesson_id))
      setNotice(`Đã lưu giáo án revision ${updated.current_version.version_no} và hướng dẫn SVG revision ${revision.guide_revision}.`)
    } catch (cause) {
      if (cause instanceof SvgCatalogServiceError && cause.status === 409) {
        setConflict(true)
        setError('Giáo án đã có revision mới hơn. Bản nháp cục bộ vẫn được giữ.')
      } else {
        setError(errorMessage(cause))
        setAutosaveBlocked(true)
      }
    } finally {
      setSaving(false)
    }
  }

  async function reloadServerVersion(): Promise<void> {
    if (!lesson) return
    setLoadingLesson(true)
    try {
      const fresh = await svgCatalogService.getLesson(lesson.lesson_id)
      const existing = fresh.current_version.content.presentation?.slides[0]
      const selectedAsset = existing
        ? assets.find((item) => item.source_asset_ref === existing.guide.source_asset_ref && item.source_asset_version === existing.guide.source_asset_version)
        : undefined
      setLesson(fresh)
      if (selectedAsset) loadEditorState(fresh, selectedAsset, existing?.guide, existing?.slide_id)
      else {
        setAssetId('')
        selectedAssetIdRef.current = ''
        setPathDrafts([])
        setGuideRevisions([])
        const emptySnapshot = { guideTitle: fresh.current_version.content.drawing_subject || fresh.current_version.content.title, stageDrafts: Array.from({ length: MIN_STAGES }, () => ({ instruction_vi: '' })), pathDrafts: [] }
        setGuideTitle(emptySnapshot.guideTitle)
        setStageDrafts(emptySnapshot.stageDrafts)
        resetUndoHistory(emptySnapshot)
      }
      setConflict(false)
      setDirty(false)
      setAutosaveBlocked(false)
      setSavedGuideRevision(null)
      setSavedGuideSignature('')
      localStorage.removeItem(localDraftKey(fresh.lesson_id))
      setNotice('Đã tải revision mới nhất từ máy chủ.')
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setLoadingLesson(false)
    }
  }

  async function reapplyToLatest(): Promise<void> {
    if (!lesson) return
    try {
      const fresh = await svgCatalogService.getLesson(lesson.lesson_id)
      setLesson(fresh)
      setConflict(false)
      setDirty(true)
      setAutosaveBlocked(false)
      setNotice('Đang áp dụng bản hướng dẫn cục bộ lên revision mới nhất…')
    } catch (cause) {
      setError(errorMessage(cause))
    }
  }

  async function saveAsSeparateDraft(): Promise<void> {
    if (!updatedContent || !guide) return
    setSaving(true)
    try {
      const content = { ...updatedContent, title: `${updatedContent.title.slice(0, 145)} — Bản riêng` }
      const created = await svgCatalogService.createSeparateLesson(content)
      setLesson(created)
      setLessons((current) => [
        { lesson_id: created.lesson_id, title: created.current_version.content.title, topic: created.current_version.content.topic, current_version_no: created.current_version.version_no, review_state: 'DRAFT', visibility: 'PRIVATE', activity_count: created.current_version.content.activities.length, updated_at: new Date().toISOString() },
        ...current,
      ])
      setConflict(false)
      setDirty(false)
      localStorage.removeItem(localDraftKey(lesson?.lesson_id ?? ''))
      setNotice('Đã tạo giáo án riêng dạng nháp từ nội dung cục bộ.')
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setSaving(false)
    }
  }

  async function uploadSvg(): Promise<void> {
    if (!uploadFile) return
    setUploadBusy(true)
    setError('')
    try {
      if (!uploadFile.name.toLowerCase().endsWith('.svg') || uploadFile.size > ASSET_FILE_LIMIT) {
        throw new Error('Chọn tệp SVG không quá 1 MB.')
      }
      const sourceSvg = await uploadFile.text()
      const created = await svgCatalogService.createAsset({
        title_vi: uploadTitle.trim(),
        topic_key: toTopicKey(uploadTopic),
        alt_text_vi: uploadAlt.trim(),
        source_uri: sourceUri.trim(),
        license_id: licenseId.trim(),
        license_uri: licenseUri.trim(),
        source_svg: sourceSvg,
      })
      setAssets((current) => [created, ...current.filter((item) => item.catalog_entry_id !== created.catalog_entry_id)])
      setUploadOpen(false)
      setUploadFile(null)
      setNotice('Đã lưu nguồn SVG an toàn vào phạm vi trường. Nguồn cần người khác duyệt trước khi được Parent xem.')
      if (lesson && created.document) selectAssetRecord(created)
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setUploadBusy(false)
    }
  }

  async function reviewSource(decision: 'APPROVE' | 'REJECT'): Promise<void> {
    if (!asset || (decision === 'REJECT' && !reviewReason.trim())) return
    setReviewBusy(true)
    setError('')
    try {
      await svgCatalogService.reviewSource(asset, decision, reviewReason)
      await loadCatalog()
      setReviewReason('')
      setNotice(decision === 'APPROVE' ? 'Đã duyệt đúng hash nguồn SVG.' : 'Đã từ chối nguồn SVG theo hash hiện tại.')
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setReviewBusy(false)
    }
  }

  async function reviewGuide(revision: SvgGuideRevisionV1, decision: 'APPROVE' | 'REJECT'): Promise<void> {
    if (!asset || (decision === 'REJECT' && !reviewReason.trim())) return
    setReviewBusy(true)
    setError('')
    try {
      await svgCatalogService.reviewGuide(asset, revision, decision, reviewReason)
      const page = await svgCatalogService.listGuideRevisions(asset)
      setGuideRevisions(page.items)
      setReviewReason('')
      setNotice(decision === 'APPROVE' ? 'Đã duyệt đúng revision và hash hướng dẫn.' : 'Đã từ chối revision hướng dẫn theo hash hiện tại.')
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setReviewBusy(false)
    }
  }

  return (
    <>
    <main className="mx-auto max-w-7xl space-y-6 px-6 py-7">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Thư viện SVG · giáo án thật</p>
        <h1 className="mt-2 text-3xl font-extrabold text-slate-950">Biên tập hướng dẫn từng nét</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Chọn một nguồn SVG an toàn, gán các path có sẵn vào từng bộ phận và bước vẽ. Hình học nguồn không bị sửa. Mỗi lần lưu tạo revision giáo án mới.</p>
      </header>

      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}
      {notice && <div role="status" className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">{notice}</div>}

      {conflict && <section className="rounded-2xl border border-amber-300 bg-amber-50 p-4" role="alert">
        <h2 className="font-bold text-amber-950">Có revision mới hơn</h2>
        <p className="mt-1 text-sm text-amber-900">Bản sửa hiện tại vẫn nằm trên trình duyệt. Chọn cách tiếp tục.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" onClick={() => void reloadServerVersion()} className="rounded-lg border border-amber-400 bg-white px-3 py-2 text-sm font-semibold">Dùng bản trên máy chủ</button>
          <button type="button" onClick={() => void reapplyToLatest()} className="rounded-lg bg-amber-700 px-3 py-2 text-sm font-semibold text-white">Áp dụng sửa đổi lên bản mới nhất</button>
          <button type="button" onClick={() => void saveAsSeparateDraft()} disabled={!guide || saving} className="rounded-lg border border-amber-400 bg-white px-3 py-2 text-sm font-semibold disabled:opacity-50">Tạo giáo án nháp riêng</button>
        </div>
      </section>}

      <section className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-bold text-slate-900">1. Chọn giáo án</h2>
              {lesson && <span className="text-xs font-semibold text-slate-500">Revision {lesson.revision}</span>}
            </div>
            {loading ? <p className="mt-4 text-sm text-slate-500">Đang tải giáo án…</p> : <select
              aria-label="Chọn giáo án"
              value={lesson?.lesson_id ?? ''}
              disabled={loadingLesson || saving}
              onChange={(event) => event.target.value && void chooseLesson(event.target.value)}
              className="mt-4 w-full rounded-xl border border-slate-300 bg-white px-3 py-3 text-sm"
            >
              <option value="">Chọn giáo án thật từ thư viện…</option>
              {lessons.map((item) => <option key={item.lesson_id} value={item.lesson_id}>{item.title} · {item.topic}</option>)}
            </select>}
            {!loading && lessons.length === 0 && <p className="mt-3 text-sm text-slate-600">Chưa có giáo án trong phạm vi tổ chức này.</p>}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-bold text-slate-900">2. Chọn nguồn nét</h2>
              <button type="button" onClick={() => setUploadOpen((value) => !value)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold">Tải SVG</button>
            </div>
            <select
              aria-label="Chọn nguồn SVG"
              value={assetId}
              disabled={!lesson || saving}
              onChange={(event) => chooseAsset(event.target.value)}
              className="mt-4 w-full rounded-xl border border-slate-300 bg-white px-3 py-3 text-sm disabled:bg-slate-50"
            >
              <option value="">Chọn hình từ kho SVG…</option>
              {assets.filter((item) => item.document).map((item) => <option key={item.catalog_entry_id} value={item.catalog_entry_id}>{item.title_vi} · {item.readiness}</option>)}
            </select>
            {asset && <div className="mt-3 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-600">
              <p><strong>Nguồn:</strong> {asset.source_uri}</p>
              <p><strong>Giấy phép:</strong> {asset.license_id} · {asset.license_uri}</p>
              <p><strong>Trạng thái:</strong> {asset.review_state} · {asset.document?.paths.length ?? 0} path</p>
            </div>}
            {uploadOpen && <div className="mt-4 space-y-3 border-t border-slate-200 pt-4">
              <p className="text-sm font-semibold text-slate-800">Thêm nguồn có provenance</p>
              <input type="file" accept="image/svg+xml,.svg" onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)} className="block w-full text-sm" />
              <div className="grid gap-3 sm:grid-cols-2">
                <TextInput label="Tên tiếng Việt" value={uploadTitle} onChange={setUploadTitle} />
                <TextInput label="Chủ đề" value={uploadTopic} onChange={setUploadTopic} />
                <TextInput label="Mô tả thay thế" value={uploadAlt} onChange={setUploadAlt} />
                <TextInput label="Mã giấy phép" value={licenseId} onChange={setLicenseId} />
                <TextInput label="URL nguồn HTTPS" value={sourceUri} onChange={setSourceUri} />
                <TextInput label="URL giấy phép HTTPS" value={licenseUri} onChange={setLicenseUri} />
              </div>
              <button type="button" disabled={uploadBusy || !lesson || !uploadFile || !uploadTitle.trim() || !uploadTopic.trim() || !uploadAlt.trim() || !sourceUri.trim() || !licenseId.trim() || !licenseUri.trim()} onClick={() => void uploadSvg()} className="rounded-lg bg-blue-700 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">{uploadBusy ? 'Đang kiểm tra và lưu…' : 'Lưu nguồn SVG'}</button>
            </div>}
          </section>

          {asset?.document && <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-bold text-slate-900">3. Phân nhóm path và bước</h2>
              <div className="flex items-center gap-2">
                <button type="button" disabled={undoCursor === 0 || saving} onClick={() => moveUndoHistory(-1)} className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-bold disabled:opacity-40">Hoàn tác</button>
                <button type="button" disabled={undoCursor >= undoLength - 1 || saving} onClick={() => moveUndoHistory(1)} className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-bold disabled:opacity-40">Làm lại</button>
                <button type="button" disabled={stageDrafts.length <= MIN_STAGES || saving} onClick={() => changeStageCount(-1)} className="h-9 w-9 rounded-lg border border-slate-300 font-bold disabled:opacity-40">−</button>
                <span className="min-w-20 text-center text-sm font-semibold">{stageDrafts.length} bước</span>
                <button type="button" disabled={stageDrafts.length >= MAX_STAGES || saving} onClick={() => changeStageCount(1)} className="h-9 w-9 rounded-lg border border-slate-300 font-bold disabled:opacity-40">+</button>
              </div>
            </div>
            <TextInput label="Tiêu đề hướng dẫn" value={guideTitle} onChange={(value) => { setGuideTitle(value); recordUndoSnapshot({ guideTitle: value, stageDrafts, pathDrafts }); markDirty() }} disabled={saving} />
            <div className="mt-4 max-h-[440px] space-y-2 overflow-auto pr-1">
              {pathDrafts.map((draft, index) => <div key={draft.path_id} className="grid gap-2 rounded-xl border border-slate-200 p-3 md:grid-cols-[minmax(0,1fr)_0.8fr_1fr_0.7fr] md:items-end">
                <div className="min-w-0"><p className="truncate text-xs font-mono text-slate-500">{draft.path_id}</p><PathPreview asset={asset} pathId={draft.path_id} /></div>
                <TextInput label="Mã bộ phận" value={draft.part_id} disabled={saving} onChange={(value) => updatePath(index, { part_id: value, label_vi: draft.label_vi }, pathDrafts, setPathDrafts, markDirty)} />
                <TextInput label="Tên bộ phận" value={draft.label_vi} disabled={saving} onChange={(value) => updatePath(index, { part_id: draft.part_id, label_vi: value }, pathDrafts, setPathDrafts, markDirty)} />
                <label className="block text-xs font-semibold text-slate-700">Bước
                  <select value={draft.stage_index === null ? '' : String(draft.stage_index)} disabled={saving} onChange={(event) => {
                    const value = event.target.value === '' ? null : Number(event.target.value)
                    const next = [...pathDrafts]
                    next[index] = { ...draft, stage_index: value }
                    setPathDrafts(next)
                    recordUndoSnapshot({ guideTitle, stageDrafts, pathDrafts: next })
                    markDirty()
                  }} className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-2 py-2 text-sm">
                    <option value="">Chọn</option>
                    {stageDrafts.map((_, stageIndex) => <option key={stageIndex} value={stageIndex}>{stageIndex + 1}</option>)}
                  </select>
                </label>
              </div>)}
            </div>
            <div className="mt-5 space-y-3">
              {stageDrafts.map((stage, index) => <label key={index} className="block text-xs font-semibold text-slate-700">
                Chỉ dẫn bước {index + 1}
                <textarea value={stage.instruction_vi} disabled={saving} maxLength={500} onChange={(event) => {
                  const next = [...stageDrafts]
                  next[index] = { instruction_vi: event.target.value }
                  setStageDrafts(next)
                  recordUndoSnapshot({ guideTitle, stageDrafts: next, pathDrafts })
                  markDirty()
                }} rows={2} className="mt-1 block w-full rounded-xl border border-slate-300 px-3 py-2 text-sm font-normal" placeholder="Ví dụ: Vẽ vòng tròn nhỏ làm phần đầu…" />
              </label>)}
            </div>
            {guideResult.error && <p role="status" className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">{guideResult.error}</p>}
          </section>}
        </div>

        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-bold text-slate-900">Bản xem trước</h2>
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-500">Path mới nét đứt · nét trước liền</span>
                <button type="button" disabled={!guide || !asset?.document} onClick={() => setPresentationOpen(true)} className="rounded-lg bg-blue-700 px-3 py-2 text-sm font-bold text-white disabled:opacity-40">Mở trình chiếu</button>
              </div>
            </div>
            {asset?.document && guide ? <div className="mx-auto mt-4 max-w-2xl"><SvgGuideRenderer document={asset.document} guide={guide} /></div> : <div className="mt-4 grid aspect-square place-items-center rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">Chọn nguồn, gán ít nhất 4 path vào 4–8 bước và nhập chỉ dẫn để xem trước.</div>}
          </section>
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-bold text-slate-900">Lưu vào giáo án</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">Tự lưu sau {AUTOSAVE_MS / 1000} giây khi hướng dẫn hợp lệ. Mỗi lần lưu tạo lesson version mới và kiểm tra revision bằng If-Match.</p>
            <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
              <span className={`rounded-full px-3 py-1 font-semibold ${saving ? 'bg-blue-50 text-blue-800' : dirty ? 'bg-amber-50 text-amber-900' : 'bg-green-50 text-green-800'}`} aria-live="polite">
                {saving ? 'Đang lưu…' : dirty ? (guide ? 'Đang chờ tự lưu' : 'Bản nháp cục bộ') : 'Đã đồng bộ'}
              </span>
              <span className="text-slate-500">{lesson ? `Revision ${lesson.revision}` : 'Chưa chọn giáo án'}</span>
              {autosaveBlocked && !conflict && <button type="button" onClick={() => { setAutosaveBlocked(false); setDirty(true) }} className="rounded-lg border border-slate-300 px-3 py-1.5 font-semibold text-slate-700">Thử lưu lại</button>}
            </div>
          </section>
          {asset && <SvgReviewPanel
            asset={asset}
            revisions={guideRevisions}
            currentPrincipalRef={currentPrincipalRef}
            reason={reviewReason}
            busy={reviewBusy}
            onReasonChange={setReviewReason}
            onReviewSource={(decision) => void reviewSource(decision)}
            onReviewGuide={(revision, decision) => void reviewGuide(revision, decision)}
          />}
        </div>
      </section>
    </main>
    {presentationOpen && asset?.document && guide && lesson && <TeacherSvgGuidePresentation
      title={lesson.current_version.content.title}
      document={asset.document}
      guide={guide}
      onClose={() => setPresentationOpen(false)}
    />}
    </>
  )

  function updatePath(
    index: number,
    nextValue: Pick<SvgGuideRevisionDraft, 'part_id' | 'label_vi'>,
    current: SvgGuideRevisionDraft[],
    setter: (paths: SvgGuideRevisionDraft[]) => void,
    onDirty: () => void,
  ): void {
    const next = [...current]
    next[index] = { ...next[index], ...nextValue }
    setter(next)
    recordUndoSnapshot({ guideTitle, stageDrafts, pathDrafts: next })
    onDirty()
  }
}

function TextInput({ label, value, onChange, disabled = false }: { label: string; value: string; onChange: (value: string) => void; disabled?: boolean }) {
  return <label className="mt-3 block text-xs font-semibold text-slate-700">{label}<input value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} className="mt-1 block w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm font-normal disabled:bg-slate-50" /></label>
}

function PathPreview({ asset, pathId }: { asset: SvgCatalogAssetV1; pathId: string }) {
  const path = asset.document?.paths.find((item) => item.path_id === pathId)
  if (!path || !asset.document) return null
  return <svg viewBox={asset.document.view_box} className="mt-1 h-8 w-full rounded bg-slate-50" aria-label={`Xem path ${pathId}`}>
    <path d={path.d} fill="none" stroke={path.stroke} strokeWidth={path.stroke_width} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
}

function buildGuide(input: {
  asset: SvgCatalogAssetV1
  slideId: string
  guideTitle: string
  stageDrafts: StageDraft[]
  pathDrafts: SvgGuideRevisionDraft[]
}): { guide: SketchStrokeGuideV3 | null; error: string } {
  const { asset, slideId, guideTitle, stageDrafts, pathDrafts } = input
  if (!asset.document || !asset.source_asset_ref || !asset.source_asset_version) return { guide: null, error: 'Nguồn SVG chưa có dữ liệu hình học an toàn.' }
  if (asset.document.paths.length < 4) return { guide: null, error: 'Hướng dẫn cần ít nhất 4 path độc lập.' }
  if (stageDrafts.length < MIN_STAGES || stageDrafts.length > MAX_STAGES) return { guide: null, error: 'Hướng dẫn cần từ 4 đến 8 bước.' }
  if (!guideTitle.trim()) return { guide: null, error: 'Nhập tên hướng dẫn.' }
  if (pathDrafts.length !== asset.document.paths.length) return { guide: null, error: 'Danh sách path chưa khớp với nguồn SVG.' }
  const pathById = new Map(pathDrafts.map((draft) => [draft.path_id, draft]))
  if (pathById.size !== asset.document.paths.length) return { guide: null, error: 'Path bị lặp; cần giữ nguyên ID nguồn.' }
  if (pathDrafts.some((draft) => !draft.part_id.trim() || !draft.label_vi.trim() || draft.stage_index === null)) {
    return { guide: null, error: 'Gán mọi path vào một bộ phận và một bước.' }
  }
  const partsById = new Map<string, { label_vi: string; path_ids: string[] }>()
  for (const draft of pathDrafts) {
    if (!/^[A-Za-z0-9._:-]{1,96}$/.test(draft.part_id.trim())) return { guide: null, error: `Mã bộ phận của ${draft.path_id} không hợp lệ.` }
    const existing = partsById.get(draft.part_id.trim())
    if (existing && existing.label_vi !== draft.label_vi.trim()) return { guide: null, error: `Các path cùng mã ${draft.part_id} cần dùng cùng tên bộ phận.` }
    partsById.set(draft.part_id.trim(), {
      label_vi: draft.label_vi.trim(),
      path_ids: [...(existing?.path_ids ?? []), draft.path_id],
    })
  }
  const stages = stageDrafts.map((stage, index) => {
    const newPathIds = asset.document!.paths
      .map((path) => path.path_id)
      .filter((pathId) => pathById.get(pathId)?.stage_index === index)
    const partIds = [...new Set(newPathIds.map((pathId) => pathById.get(pathId)!.part_id.trim()))]
    return {
      step_index: index + 1,
      instruction_vi: stage.instruction_vi.trim(),
      part_ids: partIds,
      new_path_ids: newPathIds,
      animation_order: newPathIds,
    }
  })
  if (stages.some((stage) => !stage.instruction_vi || !stage.new_path_ids.length)) {
    return { guide: null, error: 'Mỗi bước cần có chỉ dẫn tiếng Việt và ít nhất một path mới.' }
  }
  const parts = [...partsById.entries()].map(([part_id, part]) => ({
    part_id,
    label_vi: part.label_vi,
    path_ids: part.path_ids,
    depends_on: [],
  }))
  if (!parts.length || parts.some((part) => !stages.some((stage) => stage.part_ids.includes(part.part_id)))) {
    return { guide: null, error: 'Mọi bộ phận cần xuất hiện trong ít nhất một bước.' }
  }
  return {
    error: '',
    guide: {
      schema_version: 'SketchStrokeGuideV3',
      guide_id: `guide-${slideId}`,
      title_vi: guideTitle.trim(),
      source_asset_ref: asset.source_asset_ref,
      source_asset_version: asset.source_asset_version,
      source_sha256: asset.source_sha256,
      parts,
      stages,
    },
  }
}

function localDraftKey(lessonId: string): string { return `sketch2life:teacher-svg-guide:${lessonId}` }

function cloneSnapshot(snapshot: EditorSnapshot): EditorSnapshot {
  return {
    guideTitle: snapshot.guideTitle,
    stageDrafts: snapshot.stageDrafts.map((stage) => ({ ...stage })),
    pathDrafts: snapshot.pathDrafts.map((path) => ({ ...path })),
  }
}

function readLocalDraft(lessonId: string): LocalEditorDraft | null {
  try {
    const raw = localStorage.getItem(localDraftKey(lessonId))
    if (!raw) return null
    const value = JSON.parse(raw) as LocalEditorDraft
    return value && typeof value.asset_id === 'string' && Array.isArray(value.path_drafts) && Array.isArray(value.stage_drafts) ? value : null
  } catch {
    return null
  }
}

function toTopicKey(value: string): string {
  return value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('vi-VN').replace(/đ/g, 'd').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 120)
}

function errorMessage(cause: unknown): string {
  if (cause instanceof Error) return cause.message
  return 'Không thể kết nối với thư viện SVG.'
}
