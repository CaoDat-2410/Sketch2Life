import { useMemo, useState } from 'react'
import { parseTeacherSketchDeck, TeacherDeckPresentation } from '../components/TeacherDeckPresentation'
import {
  aiWorkflowService,
  type TeacherLessonSuggestionInput,
  type TeacherReviewedPlanInput,
} from '../services/aiWorkflowService'

type SuggestedActivity = {
  title: string
  objective: string
  materials_text: string
  preparation_text: string
  instructions_text: string
  safety_notes: string
  activity_kind: string
}

type ActivityDraft = TeacherReviewedPlanInput['activities'][number]

function splitSteps(value: unknown): string[] {
  if (typeof value !== 'string') return []
  return value
    .split(/\r?\n|\s*;\s*|(?<=\.)\s+(?=\d+[.)])/)
    .map((item) => item.replace(/^\s*(?:\d+[.)]|[-•])\s*/, '').trim())
    .filter(Boolean)
    .slice(0, 5)
}

function splitNotes(value: unknown): string[] {
  if (typeof value !== 'string') return []
  return value.split(/\r?\n|\s*;\s*|(?<=\.)\s+/).map((item) => item.trim()).filter(Boolean).slice(0, 8)
}

export function ModalAiLessonFlowPage() {
  const [topic, setTopic] = useState('')
  const [ageMonths, setAgeMonths] = useState('')
  const [drawingSubject, setDrawingSubject] = useState('')
  const [objectivesText, setObjectivesText] = useState('')
  const [activityCount, setActivityCount] = useState('1')
  const [activityKind, setActivityKind] = useState<'outdoor' | 'indoor' | 'mixed'>('outdoor')
  const [suggestion, setSuggestion] = useState<Record<string, unknown> | null>(null)
  const [planRevisionRef, setPlanRevisionRef] = useState('')
  const [actions, setActions] = useState<string[]>([])
  const [placements, setPlacements] = useState<string[]>([])
  const [knowledge, setKnowledge] = useState<string[]>([])
  const [activities, setActivities] = useState<ActivityDraft[]>([])
  const [reviewConfirmed, setReviewConfirmed] = useState(false)
  const [deck, setDeck] = useState<unknown>(null)
  const [visual, setVisual] = useState<string | null>(null)
  const [visualError, setVisualError] = useState('')
  const [presentationOpen, setPresentationOpen] = useState(false)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const objectives = useMemo(
    () => objectivesText.split(/\r?\n|;/).map((value) => value.trim()).filter(Boolean).slice(0, 4),
    [objectivesText],
  )

  async function requestSuggestion() {
    setError('')
    setNotice('')
    setDeck(null)
    setVisual(null)
    setVisualError('')
    setPresentationOpen(false)
    setPlanRevisionRef('')
    const age = Number(ageMonths)
    const count = Number(activityCount)
    if (!topic.trim() || !drawingSubject.trim() || !Number.isInteger(age) || age < 36 || age > 120 || objectives.length < 1 || !Number.isInteger(count) || count < 1 || count > 6) {
      setError('Nhập chủ đề, chủ thể vẽ, 1–4 mục tiêu, 1–6 hoạt động và tuổi từ 36–120 tháng.')
      return
    }
    setBusy('suggestion')
    try {
      const input: TeacherLessonSuggestionInput = {
        topic: topic.trim(),
        target_age_months: age,
        objectives,
        drawing_subject: drawingSubject.trim(),
        activity_count: count,
        activity_kind: activityKind,
        script_following_allowed: false,
        script_direction: null,
      }
      const response = await aiWorkflowService.suggestLessonPlan(input)
      if (!response.suggestion) throw new Error('Backend không trả về bản nháp giáo án.')
      const result = response.suggestion
      const initialActions = splitSteps(result.drawing_steps_text)
      const initialActivities = Array.isArray(result.activities)
        ? (result.activities as SuggestedActivity[]).map((activity, index) => ({
            activity_ref: `activity-${index + 1}`,
            title: activity.title,
            goal: activity.objective,
            materials: activity.materials_text || 'Giáo viên chuẩn bị vật liệu phù hợp.',
            preparation: activity.preparation_text || 'Giáo viên chuẩn bị trước buổi học.',
            instructions: activity.instructions_text,
            safety_notes: activity.safety_notes,
          }))
        : []
      setSuggestion(result)
      setPlanRevisionRef(`teacher-${response.request_id}`)
      setActions(initialActions)
      setPlacements(initialActions.map(() => 'trên trang vẽ'))
      setKnowledge(splitNotes(result.subject_learning_notes))
      setActivities(initialActivities)
      setReviewConfirmed(false)
      setNotice(`Bản nháp từ Qwen đã sẵn sàng. Mã yêu cầu ${response.request_id}; hãy rà soát và chỉnh sửa trước khi tạo deck.`)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể tạo gợi ý giáo án.')
    } finally {
      setBusy('')
    }
  }

  function reviewedPlan(): TeacherReviewedPlanInput | null {
    const age = Number(ageMonths)
    if (!reviewConfirmed || actions.length < 3 || actions.length > 5 || actions.some((item) => !item.trim()) || placements.length !== actions.length || placements.some((item) => !item.trim()) || !suggestion || !planRevisionRef || activities.length < 1) {
      setError('Rà soát nội dung, nhập đủ 3–5 bước vẽ và xác nhận duyệt bản nháp trước.')
      return null
    }
    return {
      review_confirmed: true,
      plan_revision_ref: planRevisionRef,
      topic: topic.trim(),
      target_age_months: age,
      objectives,
      drawing_steps: actions.map((action, index) => ({ action: action.trim(), placement: placements[index].trim() })),
      subject_knowledge: knowledge.filter((item) => item.trim()),
      activities,
    }
  }

  async function generateDeck() {
    setError('')
    setNotice('')
    setVisual(null)
    const input = reviewedPlan()
    if (!input) return
    setBusy('deck')
    try {
      const response = await aiWorkflowService.generateSketchDeck(input)
      const parsedDeck = parseTeacherSketchDeck(response.deck)
      if (!parsedDeck) throw new Error('Sketch Deck trả về không đúng schema hoặc chưa có đủ các slide hợp lệ.')
      setDeck(response.deck)
      setPresentationOpen(false)
      setNotice(`Sketch Deck Qwen đã tạo ở trạng thái bản nháp; mã yêu cầu ${response.request_id}.`)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể tạo Sketch Deck.')
    } finally {
      setBusy('')
    }
  }

  async function generateVisual() {
    setError('')
    setVisualError('')
    setNotice('')
    const input = reviewedPlan()
    if (!input) return
    setBusy('visual')
    try {
      const response = await aiWorkflowService.generateLessonVisual(input)
      if (!response.image_base64) throw new Error('Backend chưa trả ảnh minh họa hợp lệ.')
      setVisual(response.image_base64 ?? null)
      setNotice(`FLUX đã tạo ảnh minh họa bản nháp; mã yêu cầu ${response.request_id}.`)
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Không thể tạo ảnh minh họa.'
      setError(message)
      setVisualError(message)
    } finally {
      setBusy('')
    }
  }

  const presentationDeck = parseTeacherSketchDeck(deck)

  return (
    <main className="mx-auto max-w-5xl space-y-5 px-6 py-7">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Soạn nội dung · bản nháp</p>
        <h1 className="mt-1 text-3xl font-extrabold text-slate-950">Tạo giáo án có AI hỗ trợ</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">Nhập chủ đề và các trường có cấu trúc. Giáo viên luôn rà soát trước khi tạo Sketch Deck hoặc ảnh minh họa.</p>
      </header>

      {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</p>}
      {notice && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">{notice}</p>}

      <section className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-2">
        <label className="space-y-1 text-sm font-semibold text-slate-800">Chủ đề
          <input value={topic} onChange={(event) => setTopic(event.target.value)} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" placeholder="Ví dụ: vòng đời của bướm" />
        </label>
        <label className="space-y-1 text-sm font-semibold text-slate-800">Chủ thể trẻ sẽ vẽ
          <input value={drawingSubject} onChange={(event) => setDrawingSubject(event.target.value)} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" placeholder="Ví dụ: con bướm" />
        </label>
        <label className="space-y-1 text-sm font-semibold text-slate-800">Tuổi mục tiêu (tháng)
          <input type="number" min={36} max={120} value={ageMonths} onChange={(event) => setAgeMonths(event.target.value)} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" placeholder="36–120" />
        </label>
        <label className="space-y-1 text-sm font-semibold text-slate-800">Số hoạt động liên quan
          <input type="number" min={1} max={6} value={activityCount} onChange={(event) => setActivityCount(event.target.value)} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" />
        </label>
        <label className="space-y-1 text-sm font-semibold text-slate-800 md:col-span-2">Mục tiêu quan sát/học tập (mỗi dòng một mục tiêu)
          <textarea value={objectivesText} onChange={(event) => setObjectivesText(event.target.value)} rows={3} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" placeholder="Trẻ quan sát hình dáng và đặc điểm nhìn thấy của chủ thể" />
        </label>
        <label className="space-y-1 text-sm font-semibold text-slate-800">Loại hoạt động
          <select value={activityKind} onChange={(event) => setActivityKind(event.target.value as typeof activityKind)} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal">
            <option value="outdoor">Ngoài trời</option><option value="indoor">Trong nhà</option><option value="mixed">Trong nhà và ngoài trời</option>
          </select>
        </label>
        <div className="flex items-end">
          <button disabled={busy !== ''} onClick={() => void requestSuggestion()} className="rounded-xl bg-blue-700 px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50">{busy === 'suggestion' ? 'Đang tạo bản nháp…' : 'Gợi ý giáo án bằng AI'}</button>
        </div>
      </section>

      {suggestion && (
        <section className="space-y-4 rounded-2xl border border-blue-200 bg-blue-50/50 p-5">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Rà soát bản nháp Qwen</h2>
            <p className="mt-1 text-sm text-slate-600">Đây là nội dung chưa được duyệt. Sửa các trường cần thiết rồi xác nhận trước khi tạo deck.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-1 text-sm font-semibold">Các bước vẽ (3–5 dòng)
              {actions.map((value, index) => <input key={`action-${index}`} aria-label={`Bước vẽ ${index + 1}`} value={value} onChange={(event) => setActions((items) => items.map((item, i) => i === index ? event.target.value : item))} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" />)}
              {actions.length < 5 && <button type="button" onClick={() => { setActions((items) => [...items, '']); setPlacements((items) => [...items, '']); }} className="mt-1 text-xs font-bold text-blue-800 underline">Thêm bước</button>}
            </label>
            <label className="space-y-1 text-sm font-semibold">Vị trí đặt nét (theo từng bước)
              {placements.map((value, index) => <input key={`placement-${index}`} aria-label={`Vị trí bước ${index + 1}`} value={value} onChange={(event) => setPlacements((items) => items.map((item, i) => i === index ? event.target.value : item))} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" />)}
            </label>
            <label className="space-y-1 text-sm font-semibold md:col-span-2">Ghi chú kiến thức (mỗi dòng một ý)
              <textarea value={knowledge.join('\n')} onChange={(event) => setKnowledge(splitNotes(event.target.value))} rows={3} className="block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" />
            </label>
          </div>
          {activities.map((activity, index) => (
            <fieldset key={activity.activity_ref} className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 md:grid-cols-2">
              <legend className="px-1 text-sm font-bold">Hoạt động {index + 1} · {activity.activity_ref}</legend>
              <label className="text-xs font-semibold">Tên hoạt động<input aria-label={`Tên hoạt động ${index + 1}`} value={activity.title} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, title: event.target.value } : item))} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" /></label>
              <label className="text-xs font-semibold">Mục tiêu<textarea aria-label={`Mục tiêu hoạt động ${index + 1}`} value={activity.goal} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, goal: event.target.value } : item))} rows={2} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" /></label>
              <label className="text-xs font-semibold md:col-span-2">Vật liệu và chuẩn bị<input aria-label={`Vật liệu hoạt động ${index + 1}`} value={activity.materials} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, materials: event.target.value } : item))} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" /></label>
              <label className="text-xs font-semibold md:col-span-2">Cách thực hiện<textarea aria-label={`Cách thực hiện hoạt động ${index + 1}`} value={activity.instructions} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, instructions: event.target.value } : item))} rows={3} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" /></label>
              <label className="text-xs font-semibold md:col-span-2">Lưu ý an toàn<textarea aria-label={`Lưu ý an toàn hoạt động ${index + 1}`} value={activity.safety_notes} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, safety_notes: event.target.value } : item))} rows={2} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" /></label>
            </fieldset>
          ))}
          <label className="flex items-start gap-2 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800">
            <input type="checkbox" checked={reviewConfirmed} onChange={(event) => { setReviewConfirmed(event.target.checked); setError('') }} className="mt-1" />
            <span>Tôi đã đọc và rà soát các trường giáo án, hoạt động và lưu ý an toàn ở trên.</span>
          </label>
          <div className="flex flex-wrap gap-3">
            <button disabled={busy !== '' || !reviewConfirmed} onClick={() => void generateDeck()} className="rounded-xl bg-blue-700 px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50">{busy === 'deck' ? 'Đang tạo Sketch Deck…' : 'Tạo Sketch Deck'}</button>
            <button disabled={busy !== '' || !reviewConfirmed} onClick={() => void generateVisual()} className="rounded-xl border border-blue-700 bg-white px-5 py-2.5 text-sm font-bold text-blue-800 disabled:opacity-50">{busy === 'visual' ? 'Đang tạo ảnh…' : 'Tạo ảnh minh họa tùy chọn'}</button>
          </div>
        </section>
      )}

      {presentationDeck && (
        <section className="rounded-2xl border border-emerald-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-emerald-800">Sketch Deck · bản nháp cần duyệt</p>
              <h2 className="mt-1 text-xl font-bold text-slate-950">{presentationDeck.topic}</h2>
              <p className="mt-1 text-sm text-slate-600">{presentationDeck.slides.length} slide · khung 16:9 · {presentationDeck.ageMonths} tháng</p>
            </div>
            <button type="button" onClick={() => setPresentationOpen(true)} className="rounded-xl bg-blue-700 px-5 py-3 text-sm font-bold text-white hover:bg-blue-800">Mở trình chiếu</button>
          </div>
          <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3" aria-label="Các slide đã tạo">
            {presentationDeck.slides.map((slide) => <li key={slide.slideIndex} className="rounded-lg border border-slate-200 bg-slate-50 p-3"><span className="text-xs font-bold text-blue-700">Slide {slide.slideIndex}</span><p className="mt-1 text-sm font-semibold text-slate-900">{slide.title}</p></li>)}
          </ol>
        </section>
      )}
      {deck !== null && deck !== undefined && !presentationDeck && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">Sketch Deck không khớp schema trình chiếu được hỗ trợ. Hãy tạo lại bản nháp sau khi rà soát giáo án.</p>}
      {visual && <section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-xl font-bold">Ảnh minh họa · bản nháp cần duyệt</h2><img alt="Ảnh minh họa do AI tạo, chưa được duyệt" src={`data:image/png;base64,${visual}`} className="mt-3 max-h-[30rem] rounded-xl border border-slate-200 object-contain" /></section>}
      {presentationOpen && presentationDeck && <TeacherDeckPresentation deck={presentationDeck} visualBase64={visual} visualBusy={busy === 'visual'} visualError={visualError} onGenerateVisual={() => void generateVisual()} onClose={() => setPresentationOpen(false)} />}
    </main>
  )
}
