import { useMemo, useState } from 'react'
import '../../../shared/styles/tailwind-utilities.css'
import { Alert, Button, FormField, Select } from '../../../shared/ui'
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

export function TeacherAiLessonWorkflowPage() {
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
  const [presentationOpen, setPresentationOpen] = useState(false)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [promptErrors, setPromptErrors] = useState<{
    topic?: string
    drawingSubject?: string
    ageMonths?: string
    activityCount?: string
    objectives?: string
  }>({})

  const objectives = useMemo(
    () => objectivesText.split(/\r?\n|;/).map((value) => value.trim()).filter(Boolean).slice(0, 4),
    [objectivesText],
  )

  async function requestSuggestion() {
    setError('')
    setNotice('')
    setPromptErrors({})
    setDeck(null)
    setVisual(null)
    setVisualError('')
    setPresentationOpen(false)
    setPlanRevisionRef('')
    const age = Number(ageMonths)
    const count = Number(activityCount)
    const nextErrors: typeof promptErrors = {}
    if (!topic.trim()) nextErrors.topic = 'Nhập chủ đề.'
    if (!drawingSubject.trim()) nextErrors.drawingSubject = 'Nhập chủ thể trẻ sẽ vẽ.'
    if (!Number.isInteger(age) || age < 36 || age > 120) nextErrors.ageMonths = 'Tuổi mục tiêu từ 36–120 tháng.'
    if (!Number.isInteger(count) || count < 1 || count > 6) nextErrors.activityCount = 'Số hoạt động từ 1–6.'
    if (objectives.length < 1) nextErrors.objectives = 'Nhập ít nhất 1 mục tiêu quan sát/học tập.'
    if (Object.keys(nextErrors).length > 0) {
      setPromptErrors(nextErrors)
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

  const presentationDeck = parseTeacherSketchDeck(deck)

  return (
    <div className="teacher-ai-workflow mx-auto max-w-5xl space-y-5 px-6 py-7">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Soạn nội dung · bản nháp</p>
        <h1 className="mt-1 text-3xl font-extrabold text-slate-950">Tạo giáo án có AI hỗ trợ</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">Nhập chủ đề và các trường có cấu trúc. Giáo viên luôn rà soát trước khi tạo Sketch Deck hoặc ảnh minh họa.</p>
      </header>

      {notice && <Alert tone="success" role="status">{notice}</Alert>}

      <section className="cozy-form-card cozy-form-card--wide cozy-form-stack">
        <div className="cozy-form-grid">
        <FormField className="cozy-span-3" label="Chủ đề" htmlFor="ai-topic" required error={promptErrors.topic}>
          <input id="ai-topic" className="cozy-input" value={topic} onChange={(event) => { setTopic(event.target.value); setPromptErrors((prev) => ({ ...prev, topic: undefined })); }} placeholder="Ví dụ: vòng đời của bướm" />
        </FormField>
        <FormField className="cozy-span-3" label="Chủ thể trẻ sẽ vẽ" htmlFor="ai-drawing-subject" required error={promptErrors.drawingSubject}>
          <input id="ai-drawing-subject" className="cozy-input" value={drawingSubject} onChange={(event) => { setDrawingSubject(event.target.value); setPromptErrors((prev) => ({ ...prev, drawingSubject: undefined })); }} placeholder="Ví dụ: con bướm" />
        </FormField>
        <FormField className="cozy-span-2" label="Tuổi mục tiêu (tháng)" htmlFor="ai-age-months" required error={promptErrors.ageMonths}>
          <input id="ai-age-months" className="cozy-input" type="number" min={36} max={120} value={ageMonths} onChange={(event) => { setAgeMonths(event.target.value); setPromptErrors((prev) => ({ ...prev, ageMonths: undefined })); }} placeholder="36–120" />
        </FormField>
        <FormField className="cozy-span-2" label="Số hoạt động liên quan" htmlFor="ai-activity-count" required error={promptErrors.activityCount}>
          <input id="ai-activity-count" className="cozy-input" type="number" min={1} max={6} value={activityCount} onChange={(event) => { setActivityCount(event.target.value); setPromptErrors((prev) => ({ ...prev, activityCount: undefined })); }} />
        </FormField>
        <FormField className="cozy-span-2" label="Loại hoạt động" htmlFor="ai-activity-kind" required>
          <Select id="ai-activity-kind" aria-label="Loại hoạt động" value={activityKind} onChange={(event) => setActivityKind(event.target.value as typeof activityKind)}>
            <option value="outdoor">Ngoài trời</option><option value="indoor">Trong nhà</option><option value="mixed">Trong nhà và ngoài trời</option>
          </Select>
        </FormField>
        <FormField label="Mục tiêu quan sát/học tập (mỗi dòng một mục tiêu)" htmlFor="ai-objectives" required error={promptErrors.objectives}>
          <textarea id="ai-objectives" className="cozy-textarea" value={objectivesText} onChange={(event) => { setObjectivesText(event.target.value); setPromptErrors((prev) => ({ ...prev, objectives: undefined })); }} rows={3} placeholder="Trẻ quan sát hình dáng và đặc điểm nhìn thấy của chủ thể" />
        </FormField>
        </div>
        {error && !suggestion && <Alert tone="danger" role="alert">{error}</Alert>}
        <div className="cozy-form-actions" style={{ marginTop: 0 }}>
          <Button type="button" variant="primary" loading={busy === 'suggestion'} disabled={busy !== ''} onClick={() => void requestSuggestion()}>
            {busy === 'suggestion' ? 'Đang tạo bản nháp…' : 'Gợi ý giáo án bằng AI'}
          </Button>
        </div>
      </section>

      {suggestion && (
        <section className="cozy-form-card cozy-form-card--wide cozy-form-stack">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Rà soát bản nháp Qwen</h2>
            <p className="mt-1 text-sm text-slate-600">Đây là nội dung chưa được duyệt. Sửa các trường cần thiết rồi xác nhận trước khi tạo deck.</p>
          </div>
          <div className="cozy-form-stack">
            <div className="cozy-form-grid">
            <section className="cozy-form-section cozy-form-stack cozy-span-3">
              <div className="cozy-form-section-head">
                <h3>
                  Các bước vẽ (3–5{" "}
                  <span className="cozy-form-label-tail">
                    dòng)<span className="cozy-form-required" aria-hidden="true">*</span>
                  </span>
                </h3>
              </div>
              {actions.map((value, index) => (
                <FormField key={`action-${index}`} label={`Bước ${index + 1}`} htmlFor={`ai-action-${index}`} required>
                  <input
                    id={`ai-action-${index}`}
                    className="cozy-input"
                    aria-label={`Bước vẽ ${index + 1}`}
                    value={value}
                    onChange={(event) => setActions((items) => items.map((item, i) => i === index ? event.target.value : item))}
                  />
                </FormField>
              ))}
              {actions.length < 5 && (
                <div>
                  <Button type="button" variant="secondary" onClick={() => { setActions((items) => [...items, '']); setPlacements((items) => [...items, '']); }}>
                    Thêm bước
                  </Button>
                </div>
              )}
            </section>
            <section className="cozy-form-section cozy-form-stack cozy-span-3">
              <div className="cozy-form-section-head">
                <h3>
                  Vị trí đặt nét (theo từng{" "}
                  <span className="cozy-form-label-tail">
                    bước)<span className="cozy-form-required" aria-hidden="true">*</span>
                  </span>
                </h3>
              </div>
              {placements.map((value, index) => (
                <FormField key={`placement-${index}`} label={`Vị trí bước ${index + 1}`} htmlFor={`ai-placement-${index}`} required>
                  <input
                    id={`ai-placement-${index}`}
                    className="cozy-input"
                    aria-label={`Vị trí bước ${index + 1}`}
                    value={value}
                    onChange={(event) => setPlacements((items) => items.map((item, i) => i === index ? event.target.value : item))}
                  />
                </FormField>
              ))}
            </section>
            </div>
            <FormField label="Ghi chú kiến thức (mỗi dòng một ý)" htmlFor="ai-knowledge">
              <textarea id="ai-knowledge" className="cozy-textarea" value={knowledge.join('\n')} onChange={(event) => setKnowledge(splitNotes(event.target.value))} rows={3} />
            </FormField>
          </div>
          {activities.map((activity, index) => (
            <section key={activity.activity_ref} className="cozy-form-section cozy-form-grid">
              <div className="cozy-form-section-head">
                <h3>Hoạt động {index + 1} · {activity.activity_ref}</h3>
              </div>
              <FormField className="cozy-span-3" label="Tên hoạt động" htmlFor={`ai-act-title-${index}`} required>
                <input id={`ai-act-title-${index}`} className="cozy-input" aria-label={`Tên hoạt động ${index + 1}`} value={activity.title} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, title: event.target.value } : item))} />
              </FormField>
              <FormField className="cozy-span-3" label="Mục tiêu" htmlFor={`ai-act-goal-${index}`} required>
                <textarea id={`ai-act-goal-${index}`} className="cozy-textarea" aria-label={`Mục tiêu hoạt động ${index + 1}`} value={activity.goal} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, goal: event.target.value } : item))} rows={2} />
              </FormField>
              <FormField className="cozy-span-3" label="Vật liệu và chuẩn bị" htmlFor={`ai-act-materials-${index}`}>
                <input id={`ai-act-materials-${index}`} className="cozy-input" aria-label={`Vật liệu hoạt động ${index + 1}`} value={activity.materials} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, materials: event.target.value } : item))} />
              </FormField>
              <FormField className="cozy-span-3" label="Cách thực hiện" htmlFor={`ai-act-instructions-${index}`} required>
                <textarea id={`ai-act-instructions-${index}`} className="cozy-textarea" aria-label={`Cách thực hiện hoạt động ${index + 1}`} value={activity.instructions} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, instructions: event.target.value } : item))} rows={3} />
              </FormField>
              <FormField label="Lưu ý an toàn" htmlFor={`ai-act-safety-${index}`}>
                <textarea id={`ai-act-safety-${index}`} className="cozy-textarea" aria-label={`Lưu ý an toàn hoạt động ${index + 1}`} value={activity.safety_notes} onChange={(event) => setActivities((items) => items.map((item, i) => i === index ? { ...item, safety_notes: event.target.value } : item))} rows={2} />
              </FormField>
            </section>
          ))}
          <label className="flex min-h-11 items-start gap-2 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800">
            <input type="checkbox" checked={reviewConfirmed} onChange={(event) => { setReviewConfirmed(event.target.checked); setError('') }} className="mt-1" />
            <span>Tôi đã đọc và rà soát các trường giáo án, hoạt động và lưu ý an toàn ở trên.</span>
          </label>
          {!reviewConfirmed && (
            <p className="cozy-form-disabled-hint">
              Đánh dấu xác nhận rà soát ở trên để bật nút tạo Sketch Deck và ảnh minh họa.
            </p>
          )}
          {error && suggestion && <Alert tone="danger" role="alert">{error}</Alert>}
          <div className="cozy-form-actions" style={{ marginTop: 0 }}>
            <Button type="button" variant="secondary" loading={busy === 'visual'} disabled={busy !== '' || !reviewConfirmed} onClick={() => void generateVisual()}>
              {busy === 'visual' ? 'Đang tạo ảnh…' : 'Tạo ảnh minh họa tùy chọn'}
            </Button>
            <Button type="button" variant="primary" loading={busy === 'deck'} disabled={busy !== '' || !reviewConfirmed} onClick={() => void generateDeck()}>
              {busy === 'deck' ? 'Đang tạo Sketch Deck…' : 'Tạo Sketch Deck'}
            </Button>
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
            <Button type="button" variant="primary" onClick={() => setPresentationOpen(true)}>Mở trình chiếu</Button>
          </div>
          <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3" aria-label="Các slide đã tạo">
            {presentationDeck.slides.map((slide) => <li key={slide.slideIndex} className="rounded-lg border border-slate-200 bg-slate-50 p-3"><span className="text-xs font-bold text-blue-700">Slide {slide.slideIndex}</span><p className="mt-1 text-sm font-semibold text-slate-900">{slide.title}</p></li>)}
          </ol>
        </section>
      )}
      {deck !== null && deck !== undefined && !presentationDeck && <Alert tone="danger" role="alert">Sketch Deck không khớp schema trình chiếu được hỗ trợ. Hãy tạo lại bản nháp sau khi rà soát giáo án.</Alert>}
      {visual && <section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-xl font-bold">Ảnh minh họa · bản nháp cần duyệt</h2><img alt="Ảnh minh họa do AI tạo, chưa được duyệt" src={`data:image/png;base64,${visual}`} className="mt-3 max-h-[30rem] rounded-xl border border-slate-200 object-contain" /></section>}
      {presentationOpen && presentationDeck && <TeacherDeckPresentation deck={presentationDeck} visualBase64={visual} visualBusy={busy === 'visual'} visualError={visualError} onGenerateVisual={() => void generateVisual()} onClose={() => setPresentationOpen(false)} />}
    </div>
  )
}
