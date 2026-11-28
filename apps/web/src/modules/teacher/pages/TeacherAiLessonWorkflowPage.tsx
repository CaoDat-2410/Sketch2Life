import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, FormField, Select } from '../../../shared/ui'
import { PageHeading } from '../../../shared/components/FeatureAvailability'
import { AutoGrowTextarea } from '../components/AutoGrowTextarea'
import {
  backendApi,
  backendMessage,
  configuredOrganizationId,
  createIdempotencyKey,
  type LessonActivity,
  type LessonContent,
} from '../../../shared/api/backendApi'
import { clearAiWorkflowDraft, useAiWorkflowState } from '../services/aiWorkflowSession'
import {
  beginAiTask,
  clearAiTaskStatusIfCurrent,
  finishAiTask,
  scheduleAiTaskStatusSeen,
  useAiTaskMark,
  type AiTaskKey,
  type AiTaskMark,
} from '../services/aiTaskStatus'
import {
  aiWorkflowService,
  type TeacherLessonSuggestionInput,
} from '../services/aiWorkflowService'
import { teacherAgeBandForMonths, isTeacherAgeBand } from '../services/ageBands'

type ActivityKind = LessonActivity['activity_kind']

type SuggestedActivity = Partial<LessonActivity> & {
  title: string
  objective: string
}

type ActivityDraft = {
  activity_ref: string
  title: string
  goal: string
  materials: string
  preparation: string
  instructions: string
  observation_notes: string
  safety_notes: string
  activity_kind: ActivityKind
}

type SaveCommand = { signature: string; key: string }
type SavedLesson = { title: string; signature: string }

const textLength = (value: string) => [...value].length

function textLimitError(label: string, value: string, maximum: number, required = false): string {
  if (required && !value.trim()) return `${label} không được để trống.`
  if (textLength(value) > maximum) return `${label} tối đa ${maximum.toLocaleString('vi-VN')} ký tự.`
  return ''
}

function lessonContentError(content: LessonContent): string {
  const fields: Array<[string, string, number, boolean?]> = [
    ['Tên giáo án', content.title, 160, true],
    ['Chủ đề', content.topic, 120, true],
    ['Đối tượng cần vẽ', content.drawing_subject, 160, true],
    ['Các bước vẽ', content.drawing_steps_text, 4000, true],
    ['Ghi chú kiến thức', content.subject_learning_notes, 5000, true],
  ]
  for (const [label, value, maximum, required] of fields) {
    const error = textLimitError(label, value, maximum, required)
    if (error) return error
  }
  if (!isTeacherAgeBand(content.target_age_band_ref, content.target_age_band_version)) {
    return 'Tuổi mục tiêu chưa thuộc nhóm tuổi được hỗ trợ.'
  }
  if (content.objectives.length < 1 || content.objectives.length > 12) {
    return 'Giáo án cần từ 1 đến 12 mục tiêu.'
  }
  for (const [index, objective] of content.objectives.entries()) {
    const error = textLimitError(`Mục tiêu ${index + 1}`, objective, 1000, true)
    if (error) return error
  }
  if (content.script_direction !== null) {
    const error = textLimitError('Định hướng kịch bản', content.script_direction, 2000, true)
    if (error) return error
  }
  if (content.activities.length < 1 || content.activities.length > 24) {
    return 'Giáo án cần từ 1 đến 24 hoạt động.'
  }
  for (const [index, activity] of content.activities.entries()) {
    const label = `Hoạt động ${index + 1}`
    const activityFields: Array<[string, string, number, boolean?]> = [
      [`${label} · tên`, activity.title, 160, true],
      [`${label} · mục tiêu`, activity.objective, 1000, true],
      [`${label} · vật liệu`, activity.materials_text, 2000],
      [`${label} · chuẩn bị`, activity.preparation_text, 2000],
      [`${label} · cách thực hiện`, activity.instructions_text, 5000, true],
      [`${label} · ghi chú quan sát`, activity.observation_notes, 3000],
      [`${label} · lưu ý an toàn`, activity.safety_notes, 3000],
    ]
    for (const [fieldLabel, value, maximum, required] of activityFields) {
      const error = textLimitError(fieldLabel, value, maximum, required)
      if (error) return error
    }
  }
  return ''
}

function drawingStepsError(actions: string[], placements: string[]): string {
  if (actions.length === 0 || placements.length !== actions.length) {
    return 'Giáo án cần ít nhất một bước vẽ có thao tác và vị trí.'
  }
  if (actions.some((action, index) => !action.trim() || !placements[index]?.trim())) {
    return 'Hãy điền thao tác và vị trí cho từng bước vẽ.'
  }
  return ''
}

function splitSteps(value: unknown): string[] {
  if (typeof value !== 'string') return []
  return value
    .split(/\r?\n|\s*;\s*|(?<=\.)\s+(?=\d+[.)])/)
    .map((item) => item.replace(/^\s*(?:\d+[.)]|[-•])\s*/, '').trim())
    .filter(Boolean)
}

function splitNotes(value: unknown): string[] {
  if (typeof value !== 'string') return []
  return value
    .split(/\r?\n|\s*;\s*/)
    .flatMap((line) => line.split(/(?<!\S)(?=\d+[.)]\s+)/))
    .map((item) => item.trim())
    .filter((item) => item && !/^\d+[.)]$/.test(item))
    .map((item) => item.replace(/^(?:\d+[.)]\s+|[-*\u2022\u2023\u25E6]\s*)/, '').trim())
    .filter(Boolean)
}

const DEFAULT_PLACEMENT = 'trên trang vẽ'

function useDocumentVisible() {
  const [visible, setVisible] = useState(() => document.visibilityState === 'visible')
  useEffect(() => {
    const update = () => setVisible(document.visibilityState === 'visible')
    document.addEventListener('visibilitychange', update)
    return () => document.removeEventListener('visibilitychange', update)
  }, [])
  return visible
}

function useClearSeenAiTaskMark(key: AiTaskKey, visible: boolean, mark?: AiTaskMark) {
  const seenRunId = useRef<number | undefined>(undefined)
  useEffect(() => {
    if (!visible || !mark || mark.status === 'pending') return
    seenRunId.current = mark.runId
    return scheduleAiTaskStatusSeen(key, mark.runId)
  }, [key, visible, mark])
  useEffect(() => () => {
    if (seenRunId.current !== undefined) clearAiTaskStatusIfCurrent(key, seenRunId.current)
  }, [key])
}

export function TeacherAiLessonWorkflowPage() {
  const [topic, setTopic] = useAiWorkflowState('topic', '')
  const [ageMonths, setAgeMonths] = useAiWorkflowState('ageMonths', '')
  const [drawingSubject, setDrawingSubject] = useAiWorkflowState('drawingSubject', '')
  const [objectivesText, setObjectivesText] = useAiWorkflowState('objectivesText', '')
  const [lessonTitle, setLessonTitle] = useAiWorkflowState('lessonTitle', '')
  const [scriptDirectionText, setScriptDirectionText] = useAiWorkflowState('scriptDirectionText', '')
  const [activityCount, setActivityCount] = useAiWorkflowState('activityCount', '1')
  const [activityKind, setActivityKind] = useAiWorkflowState<'outdoor' | 'indoor' | 'mixed'>('activityKind', 'outdoor')
  const [suggestion, setSuggestion] = useAiWorkflowState<Record<string, unknown> | null>('suggestion', null)
  const [actions, setActions] = useAiWorkflowState<string[]>('actions', [])
  const [placements, setPlacements] = useAiWorkflowState<string[]>('placements', [])
  const [knowledgeText, setKnowledgeText] = useAiWorkflowState('knowledgeText', '')
  const [activities, setActivities] = useAiWorkflowState<ActivityDraft[]>('activities', [])
  const [reviewConfirmed, setReviewConfirmed] = useAiWorkflowState('reviewConfirmed', false)
  const [saveCommand, setSaveCommand] = useAiWorkflowState<SaveCommand | null>('saveCommand', null)
  const [savedLesson, setSavedLesson] = useAiWorkflowState<SavedLesson | null>('savedLesson', null)
  const [busy, setBusy] = useAiWorkflowState('busy', '')
  const [error, setError] = useAiWorkflowState('error', '')
  const [notice, setNotice] = useAiWorkflowState('notice', '')
  const [promptErrors, setPromptErrors] = useAiWorkflowState<{
    topic?: string
    drawingSubject?: string
    ageMonths?: string
    activityCount?: string
    objectives?: string
  }>('promptErrors', {})
  const suggestionTaskMark = useAiTaskMark('suggestion')
  const saveInFlight = useRef(false)
  const documentVisible = useDocumentVisible()
  useClearSeenAiTaskMark('suggestion', documentVisible, suggestionTaskMark)

  const objectives = useMemo(
    () => objectivesText.split(/\r?\n|;/).map((value) => value.trim()).filter(Boolean),
    [objectivesText],
  )

  function markDraftEdited() {
    setReviewConfirmed(false)
    setError('')
    setNotice('')
  }

  function lessonContent(): LessonContent {
    const ageBand = teacherAgeBandForMonths(Number(ageMonths))
    return {
      locale: 'vi-VN',
      title: lessonTitle.trim(),
      topic: topic.trim(),
      target_age_band_ref: ageBand?.ref ?? '',
      target_age_band_version: ageBand?.version ?? 0,
      objectives,
      drawing_subject: drawingSubject.trim(),
      drawing_steps_text: actions.map((action, index) =>
        `Bước ${index + 1}: ${action.trim()} — vị trí: ${placements[index]?.trim() ?? ''}`,
      ).join('\n'),
      subject_learning_notes: knowledgeText.trim(),
      script_direction: scriptDirectionText.trim() || null,
      script_following_allowed: false,
      activities: activities.map((activity) => ({
        title: activity.title.trim(),
        objective: activity.goal.trim(),
        materials_text: activity.materials.trim(),
        preparation_text: activity.preparation.trim(),
        instructions_text: activity.instructions.trim(),
        observation_notes: activity.observation_notes.trim(),
        safety_notes: activity.safety_notes.trim(),
        activity_kind: activity.activity_kind,
      })),
    }
  }

  async function requestSuggestion() {
    setError('')
    setNotice('')
    setPromptErrors({})
    setSavedLesson(null)
    setSaveCommand(null)
    const age = Number(ageMonths)
    const count = Number(activityCount)
    const nextErrors: typeof promptErrors = {}
    if (!topic.trim()) nextErrors.topic = 'Nhập chủ đề.'
    else if (textLength(topic.trim()) > 120) nextErrors.topic = 'Chủ đề tối đa 120 ký tự.'
    if (!drawingSubject.trim()) nextErrors.drawingSubject = 'Nhập chủ thể trẻ sẽ vẽ.'
    else if (textLength(drawingSubject.trim()) > 160) nextErrors.drawingSubject = 'Chủ thể cần vẽ tối đa 160 ký tự.'
    if (!Number.isInteger(age) || age < 36 || age > 120) nextErrors.ageMonths = 'Tuổi mục tiêu từ 36–120 tháng.'
    if (!Number.isInteger(count) || count < 1 || count > 6) nextErrors.activityCount = 'Số hoạt động từ 1–6.'
    if (objectives.length < 1 || objectives.length > 4) nextErrors.objectives = 'Nhập từ 1 đến 4 mục tiêu cho gợi ý AI.'
    else if (objectives.some((objective) => textLength(objective) > 1000)) nextErrors.objectives = 'Mỗi mục tiêu tối đa 1.000 ký tự.'
    if (Object.keys(nextErrors).length > 0) {
      setPromptErrors(nextErrors)
      setError('Kiểm tra chủ đề, chủ thể vẽ, mục tiêu, số hoạt động và tuổi trước khi gửi yêu cầu.')
      return
    }
    const taskRunId = beginAiTask('suggestion')
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
      if (!response.suggestion) throw new Error('Chưa nhận được bản nháp giáo án. Hãy thử lại.')
      const result = response.suggestion
      const initialActions = splitSteps(result.drawing_steps_text)
      const initialActivities = Array.isArray(result.activities)
        ? (result.activities as SuggestedActivity[]).map((activity, index) => ({
            activity_ref: `activity-${index + 1}`,
            title: typeof activity.title === 'string' ? activity.title : '',
            goal: typeof activity.objective === 'string' ? activity.objective : '',
            materials: typeof activity.materials_text === 'string' ? activity.materials_text : '',
            preparation: typeof activity.preparation_text === 'string' ? activity.preparation_text : '',
            instructions: typeof activity.instructions_text === 'string' ? activity.instructions_text : '',
            observation_notes: typeof activity.observation_notes === 'string' ? activity.observation_notes : '',
            safety_notes: typeof activity.safety_notes === 'string' ? activity.safety_notes : '',
            activity_kind: activity.activity_kind ?? activityKind,
          }))
        : []
      setSuggestion(result)
      setLessonTitle(typeof result.title === 'string' ? result.title : topic.trim())
      setScriptDirectionText(typeof result.script_direction === 'string' ? result.script_direction : '')
      setActions(initialActions)
      setPlacements(initialActions.map(() => DEFAULT_PLACEMENT))
      setKnowledgeText(splitNotes(result.subject_learning_notes).join('\n'))
      setActivities(initialActivities)
      setReviewConfirmed(false)
      finishAiTask('suggestion', taskRunId, 'done')
      setNotice('Bản nháp giáo án đã sẵn sàng. Hãy rà soát và chỉnh sửa trước khi lưu thành giáo án.')
    } catch {
      finishAiTask('suggestion', taskRunId, 'failed')
      setError('Chưa thể tạo gợi ý giáo án. Hãy kiểm tra thông tin rồi thử lại.')
    } finally {
      setBusy('')
    }
  }

  function removeDrawingStep(index: number) {
    setActions((items) => items.filter((_, itemIndex) => itemIndex !== index))
    setPlacements((items) => items.filter((_, itemIndex) => itemIndex !== index))
    markDraftEdited()
  }

  function updateActivity(index: number, change: Partial<ActivityDraft>) {
    setActivities((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, ...change } : item))
    markDraftEdited()
  }

  function startOver() {
    // A suggestion costs minutes of GPU time: do not drop it on a stray click.
    if (suggestion && !window.confirm('Xóa bản nháp giáo án đang soạn và bắt đầu lại?')) return
    clearAiWorkflowDraft()
  }

  async function saveLesson() {
    if (saveInFlight.current) return
    setError('')
    setNotice('')
    if (!reviewConfirmed) {
      setError('Hãy rà soát nội dung rồi xác nhận trước khi lưu thành giáo án.')
      return
    }
    const stepError = drawingStepsError(actions, placements)
    if (stepError) {
      setError(stepError)
      return
    }
    const content = lessonContent()
    const contentError = lessonContentError(content)
    if (contentError) {
      setError(contentError)
      return
    }
    const organizationId = configuredOrganizationId()
    if (!organizationId) {
      setError('Chưa cấu hình tổ chức cho thư viện giáo án.')
      return
    }
    const signature = JSON.stringify([organizationId, content])
    if (savedLesson?.signature === signature) return
    const command = saveCommand?.signature === signature
      ? saveCommand
      : { signature, key: createIdempotencyKey() }
    if (command !== saveCommand) setSaveCommand(command)
    saveInFlight.current = true
    setBusy('save')
    try {
      await backendApi.createLesson(organizationId, content, command.key)
      setSavedLesson({ title: content.title, signature })
      setSaveCommand(null)
      setNotice(`Đã lưu “${content.title}” thành giáo án riêng tư.`)
    } catch (cause) {
      setError(backendMessage(cause))
    } finally {
      saveInFlight.current = false
      setBusy('')
    }
  }

  const currentLessonContent = lessonContent()
  const currentSignature = JSON.stringify([configuredOrganizationId(), currentLessonContent])
  const savedLessonForDraft = savedLesson?.signature === currentSignature ? savedLesson : null

  return (
    <div className="teacher-ai-workflow mx-auto max-w-5xl space-y-5 px-6 py-7">
      <PageHeading
        eyebrow="Giáo viên · Soạn nội dung"
        title="Gợi ý giáo án AI"
        description="Nhập chủ đề, rà soát bản nháp rồi lưu thành giáo án trong thư viện."
      />

      <div className="flex justify-end">
        <Button type="button" variant="secondary" disabled={busy === 'suggestion' || busy === 'save'} onClick={startOver}>Soạn mới</Button>
      </div>

      {notice && <Alert tone="success" role="status">{notice}</Alert>}

      <section className="cozy-form-card cozy-form-card--wide cozy-form-stack">
        <div className="cozy-form-grid">
        <FormField className="cozy-span-3" label="Chủ đề" htmlFor="ai-topic" required error={promptErrors.topic}>
          <input id="ai-topic" className="cozy-input" maxLength={120} value={topic} onChange={(event) => { setTopic(event.target.value); markDraftEdited(); setPromptErrors((prev) => ({ ...prev, topic: undefined })); }} placeholder="Ví dụ: vòng đời của bướm" />
        </FormField>
        <FormField className="cozy-span-3" label="Chủ thể trẻ sẽ vẽ" htmlFor="ai-drawing-subject" required error={promptErrors.drawingSubject}>
          <input id="ai-drawing-subject" className="cozy-input" maxLength={160} value={drawingSubject} onChange={(event) => { setDrawingSubject(event.target.value); markDraftEdited(); setPromptErrors((prev) => ({ ...prev, drawingSubject: undefined })); }} placeholder="Ví dụ: con bướm" />
        </FormField>
        <FormField className="cozy-span-2" label="Tuổi mục tiêu (tháng)" htmlFor="ai-age-months" required error={promptErrors.ageMonths}>
          <input id="ai-age-months" className="cozy-input" type="number" min={36} max={120} value={ageMonths} onChange={(event) => { setAgeMonths(event.target.value); markDraftEdited(); setPromptErrors((prev) => ({ ...prev, ageMonths: undefined })); }} placeholder="36–120" />
        </FormField>
        <FormField className="cozy-span-2" label="Số hoạt động liên quan" htmlFor="ai-activity-count" required error={promptErrors.activityCount}>
          <input id="ai-activity-count" className="cozy-input" type="number" min={1} max={6} value={activityCount} onChange={(event) => { setActivityCount(event.target.value); markDraftEdited(); setPromptErrors((prev) => ({ ...prev, activityCount: undefined })); }} />
        </FormField>
        <FormField className="cozy-span-2" label="Loại hoạt động" htmlFor="ai-activity-kind" required>
          <Select id="ai-activity-kind" aria-label="Loại hoạt động" value={activityKind} onChange={(event) => { setActivityKind(event.target.value as typeof activityKind); markDraftEdited(); }}>
            <option value="outdoor">Ngoài trời</option><option value="indoor">Trong lớp</option><option value="mixed">Trong lớp và ngoài trời</option>
          </Select>
        </FormField>
        <FormField label="Mục tiêu quan sát/học tập (mỗi dòng một mục tiêu)" htmlFor="ai-objectives" required error={promptErrors.objectives}>
          <textarea id="ai-objectives" className="cozy-textarea" maxLength={12011} value={objectivesText} onChange={(event) => { setObjectivesText(event.target.value); markDraftEdited(); setPromptErrors((prev) => ({ ...prev, objectives: undefined })); }} rows={3} placeholder="Trẻ quan sát hình dáng và đặc điểm nhìn thấy của chủ thể" />
        </FormField>
        </div>
        {error && !suggestion && <Alert tone="danger" role="alert">{error}</Alert>}
        <div className="cozy-form-actions" style={{ marginTop: 0 }}>
          <Button type="button" variant="primary" loading={busy === 'suggestion'} disabled={busy !== ''} onClick={() => { void requestSuggestion() }}>
            {busy === 'suggestion' ? 'Đang tạo bản nháp…' : 'Gợi ý giáo án bằng AI'}
          </Button>
        </div>
      </section>

      {suggestion && (
        <section className="cozy-form-card cozy-form-card--wide cozy-form-stack">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Rà soát bản nháp giáo án</h2>
            <p className="mt-1 text-sm text-slate-600">Đây là nội dung nháp. Chỉnh sửa các trường cần thiết rồi xác nhận trước khi lưu thành giáo án.</p>
          </div>
          <div className="cozy-form-stack">
            <FormField label="Tên giáo án" htmlFor="ai-lesson-title" required>
              <input id="ai-lesson-title" className="cozy-input" maxLength={160} value={lessonTitle} onChange={(event) => { setLessonTitle(event.target.value); markDraftEdited(); }} />
            </FormField>
            <div className="cozy-form-grid">
            <section className="cozy-form-section cozy-form-stack cozy-span-3">
              <div className="cozy-form-section-head">
                <h3>Các bước vẽ<span className="cozy-form-required" aria-hidden="true">*</span></h3>
              </div>
              {actions.map((value, index) => (
                <FormField key={`action-${index}`} label={`Bước ${index + 1}`} htmlFor={`ai-action-${index}`} required>
                  <AutoGrowTextarea
                    id={`ai-action-${index}`}
                    singleLine
                    maxLength={4000}
                    aria-label={`Bước vẽ ${index + 1}`}
                    value={value}
                    onValueChange={(next) => { setActions((items) => items.map((item, i) => i === index ? next : item)); markDraftEdited(); }}
                  />
                  {actions.length > 1 && (
                    <Button type="button" variant="secondary" size="sm" aria-label={`Bỏ bước ${index + 1}`} onClick={() => removeDrawingStep(index)}>
                      Bỏ bước
                    </Button>
                  )}
                </FormField>
              ))}
              <div>
                <Button type="button" variant="secondary" onClick={() => { setActions((items) => [...items, '']); setPlacements((items) => [...items, '']); markDraftEdited(); }}>
                  Thêm bước
                </Button>
              </div>
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
              <p className="s2l-muted-copy">“{DEFAULT_PLACEMENT}” là giá trị mặc định, không phải gợi ý của AI. Hãy sửa lại cho đúng vị trí của từng bước.</p>
              {placements.map((value, index) => (
                <FormField key={`placement-${index}`} label={`Vị trí bước ${index + 1}`} htmlFor={`ai-placement-${index}`} required>
                  <AutoGrowTextarea
                    id={`ai-placement-${index}`}
                    singleLine
                    maxLength={4000}
                    aria-label={`Vị trí bước ${index + 1}`}
                    value={value}
                    onValueChange={(next) => { setPlacements((items) => items.map((item, i) => i === index ? next : item)); markDraftEdited(); }}
                  />
                </FormField>
              ))}
            </section>
            </div>
            <FormField label="Ghi chú kiến thức" htmlFor="ai-knowledge" required>
              <AutoGrowTextarea id="ai-knowledge" maxLength={5000} value={knowledgeText} onValueChange={(next) => { setKnowledgeText(next); markDraftEdited(); }} rows={3} />
            </FormField>
            <FormField label="Định hướng kịch bản" htmlFor="ai-script-direction">
              <AutoGrowTextarea id="ai-script-direction" maxLength={2000} value={scriptDirectionText} onValueChange={(next) => { setScriptDirectionText(next); markDraftEdited(); }} rows={3} />
            </FormField>
          </div>
          {activities.map((activity, index) => (
            <section key={activity.activity_ref} className="cozy-form-section cozy-form-grid">
              <div className="cozy-form-section-head">
                <h3>Hoạt động {index + 1}</h3>
              </div>
              <FormField className="cozy-span-3" label="Tên hoạt động" htmlFor={`ai-act-title-${index}`} required>
                <AutoGrowTextarea id={`ai-act-title-${index}`} singleLine maxLength={160} aria-label={`Tên hoạt động ${index + 1}`} value={activity.title} onValueChange={(next) => updateActivity(index, { title: next })} />
              </FormField>
              <FormField className="cozy-span-3" label="Mục tiêu" htmlFor={`ai-act-goal-${index}`} required>
                <AutoGrowTextarea id={`ai-act-goal-${index}`} maxLength={1000} aria-label={`Mục tiêu hoạt động ${index + 1}`} value={activity.goal} onValueChange={(next) => updateActivity(index, { goal: next })} rows={2} />
              </FormField>
              <FormField className="cozy-span-3" label="Vật liệu" htmlFor={`ai-act-materials-${index}`}>
                <AutoGrowTextarea id={`ai-act-materials-${index}`} maxLength={2000} aria-label={`Vật liệu hoạt động ${index + 1}`} value={activity.materials} onValueChange={(next) => updateActivity(index, { materials: next })} rows={2} />
              </FormField>
              <FormField className="cozy-span-3" label="Chuẩn bị" htmlFor={`ai-act-preparation-${index}`}>
                <AutoGrowTextarea id={`ai-act-preparation-${index}`} maxLength={2000} aria-label={`Chuẩn bị hoạt động ${index + 1}`} value={activity.preparation} onValueChange={(next) => updateActivity(index, { preparation: next })} rows={2} />
              </FormField>
              <FormField className="cozy-span-3" label="Cách thực hiện" htmlFor={`ai-act-instructions-${index}`} required>
                <AutoGrowTextarea id={`ai-act-instructions-${index}`} maxLength={5000} aria-label={`Cách thực hiện hoạt động ${index + 1}`} value={activity.instructions} onValueChange={(next) => updateActivity(index, { instructions: next })} rows={3} />
              </FormField>
              <FormField label="Ghi chú quan sát" htmlFor={`ai-act-observation-${index}`}>
                <AutoGrowTextarea id={`ai-act-observation-${index}`} maxLength={3000} aria-label={`Ghi chú quan sát hoạt động ${index + 1}`} value={activity.observation_notes} onValueChange={(next) => updateActivity(index, { observation_notes: next })} rows={2} />
              </FormField>
              <FormField label="Lưu ý an toàn" htmlFor={`ai-act-safety-${index}`}>
                <AutoGrowTextarea id={`ai-act-safety-${index}`} maxLength={3000} aria-label={`Lưu ý an toàn hoạt động ${index + 1}`} value={activity.safety_notes} onValueChange={(next) => updateActivity(index, { safety_notes: next })} rows={2} />
              </FormField>
              <FormField label="Loại hoạt động" htmlFor={`ai-act-kind-${index}`} required>
                <Select id={`ai-act-kind-${index}`} aria-label={`Loại hoạt động ${index + 1}`} value={activity.activity_kind} onChange={(event) => updateActivity(index, { activity_kind: event.target.value as ActivityKind })}>
                  <option value="outdoor">Ngoài trời</option>
                  <option value="indoor">Trong lớp</option>
                  <option value="mixed">Trong lớp và ngoài trời</option>
                </Select>
              </FormField>
            </section>
          ))}
          <label className="flex min-h-11 items-start gap-2 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800">
            <input type="checkbox" checked={reviewConfirmed} onChange={(event) => { setReviewConfirmed(event.target.checked); setError('') }} className="mt-1" />
            <span>Tôi đã đọc và rà soát các trường giáo án, hoạt động và lưu ý an toàn ở trên.</span>
          </label>
          {!reviewConfirmed && (
            <p className="cozy-form-disabled-hint">
              Đánh dấu xác nhận rà soát ở trên để bật nút lưu giáo án.
            </p>
          )}
          {error && suggestion && <Alert tone="danger" role="alert">{error}</Alert>}
          <div className="cozy-form-actions" style={{ marginTop: 0 }}>
            <Button type="button" variant="primary" loading={busy === 'save'} disabled={busy !== '' || !reviewConfirmed || Boolean(savedLessonForDraft)} onClick={() => void saveLesson()}>
              {busy === 'save' ? 'Đang lưu giáo án…' : savedLessonForDraft ? 'Đã lưu thành giáo án' : 'Lưu thành giáo án'}
            </Button>
          </div>
        </section>
      )}

      {savedLessonForDraft && (
        <section className="cozy-form-card cozy-form-card--wide cozy-form-stack" aria-labelledby="saved-lesson-heading">
          <div>
            <h2 id="saved-lesson-heading" className="text-xl font-bold text-slate-900">Đã lưu thành giáo án</h2>
            <p className="mt-1 text-base font-semibold text-slate-900">{savedLessonForDraft.title}</p>
            <p className="mt-2 text-sm text-slate-600">Giáo án đang ở trạng thái bản nháp riêng tư, chưa được duyệt nên chưa thể ghim vào buổi dạy. Mở thư viện để gửi yêu cầu duyệt công khai tới quản lý nhà trường.</p>
          </div>
          <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-700">
            <li>Sau khi giáo án được duyệt, ghim giáo án vào một buổi dạy.</li>
            <li>Rà soát và duyệt kế hoạch của buổi dạy.</li>
            <li>Tạo Sketch Deck từ trang buổi dạy.</li>
          </ol>
          <div className="flex flex-wrap gap-3">
            <Link className="s2l-button is-primary" to="/teacher/t02-lesson-authoring">Mở thư viện giáo án</Link>
            <Link className="s2l-button" to="/teacher/t04-session-sketch-deck">Mở trang buổi dạy</Link>
          </div>
        </section>
      )}
    </div>
  )
}
