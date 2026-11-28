import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Plus, Presentation, RefreshCw, Trash2 } from "lucide-react";
import { BackendApiError, createIdempotencyKey } from "../../../shared/api/backendApi";
import {
  NOT_FOUND_OR_NO_ACCESS,
  teacherOccurrenceApi,
  type CreateSketchDeckInput,
  type CurrentSketchDeck,
  type PlanRevision,
  type TeacherConfirmedAgeBandRef,
  type TeacherDrawingStep,
} from "../../../shared/api/teacherOccurrenceApi";
import { Button, FormField, Select } from "../../../shared/ui";
import { FormActionBar } from "./FormActionBar";
import { TeacherDeckPresentation } from "./TeacherDeckPresentation";
import { toTeacherSketchDeck } from "../services/teacherSketchDeckAdapter";

type Props = Readonly<{ occurrenceId: string; approvedRevisionNo: number | null }>;
type PanelError = Readonly<{
  message: string;
  step: string;
  method: string;
  path: string;
  status: string;
  code: string;
  requestId: string;
}>;
type KeyedRequest = Readonly<{ fingerprint: string; key: string }>;

const MIN_STEPS = 4;
const MAX_STEPS = 8;
const MAX_TEXT_LENGTH = 240;
const MAX_TOPIC_LENGTH = 120;
const MAX_KNOWLEDGE_ITEMS = 8;
const MAX_KNOWLEDGE_LENGTH = 10_000;
const GENERATION_LOCK_MS = 15 * 60 * 1000;
const TEACHER_AGE_BAND_OPTIONS: ReadonlyArray<{
  value: TeacherConfirmedAgeBandRef;
  label: string;
}> = [
  { value: "age-36-71-months-v1", label: "36–71 tháng" },
  { value: "age-72-107-months-v1", label: "72–107 tháng" },
  { value: "age-108-120-months-v1", label: "108–120 tháng" },
];

const textLength = (value: string) => Array.from(value).length;
const blankSteps = (): TeacherDrawingStep[] => Array.from({ length: MIN_STEPS }, () => ({ action: "", placement: "" }));
const panelError = (cause: unknown, step: string, method: string, path: string, drawingSteps?: TeacherDrawingStep[]): PanelError => {
  const apiError = cause instanceof BackendApiError ? cause : null;
  const countFieldError = apiError?.fieldErrors.some(({ field, code }) =>
    field === "drawing_steps" && ["EMPTY", "TOO_SHORT", "TOO_LONG"].includes(code),
  ) ?? false;
  const emptyStepFieldError = apiError?.fieldErrors.some(({ field, code }) =>
    /^drawing_steps\.(?:action|placement)$/.test(field) && code === "EMPTY",
  ) ?? false;
  const submittedStepCount = drawingSteps?.filter((item) => item.action.trim()).length;
  const topLevelEmptyCountError = apiError?.code === "EMPTY" && drawingSteps
    && (drawingSteps.length < MIN_STEPS || drawingSteps.length > MAX_STEPS
      || submittedStepCount! < MIN_STEPS || submittedStepCount! > MAX_STEPS);
  const topLevelEmptyStepError = apiError?.code === "EMPTY" && drawingSteps
    && drawingSteps.some((item) => !item.action.trim() || !item.placement.trim());
  const hasStepValidationError = countFieldError || emptyStepFieldError || topLevelEmptyCountError || topLevelEmptyStepError;
  return {
    message: countFieldError || topLevelEmptyCountError
      ? "Cần 4–8 bước vẽ."
      : emptyStepFieldError || topLevelEmptyStepError
        ? "Hãy điền thao tác và vị trí cho từng bước vẽ."
        : apiError?.status === 404 ? NOT_FOUND_OR_NO_ACCESS : cause instanceof Error ? cause.message : "Không thể hoàn tất yêu cầu. Hãy thử lại.",
    step,
    method,
    path,
    status: apiError ? String(apiError.status) : "Không có",
    code: hasStepValidationError ? "Không có" : apiError?.code ?? "Không có",
    requestId: apiError?.requestId ?? "Không có",
  };
};

function validateInput(
  topic: string,
  steps: TeacherDrawingStep[],
  notes: string[],
  reviewConfirmed: boolean,
  teacherAgeBandRequired: boolean,
  teacherAgeBandRef: TeacherConfirmedAgeBandRef | "",
): string[] {
  const errors: string[] = [];
  const cleanTopic = topic.trim();
  if (!cleanTopic || textLength(cleanTopic) > MAX_TOPIC_LENGTH || topic.includes("\0")) errors.push("Chủ đề cần có từ 1 đến 120 ký tự.");
  const filledStepCount = steps.filter((step) => step.action.trim()).length;
  if (steps.length < MIN_STEPS || steps.length > MAX_STEPS || filledStepCount < MIN_STEPS || filledStepCount > MAX_STEPS) {
    errors.push("Cần 4–8 bước vẽ.");
  }
  steps.forEach((step, index) => {
    if (!step.action.trim() || !step.placement.trim() || textLength(step.action.trim()) > MAX_TEXT_LENGTH || textLength(step.placement.trim()) > MAX_TEXT_LENGTH || step.action.includes("\0") || step.placement.includes("\0")) {
      errors.push(`Bước ${index + 1}: thao tác và vị trí cần có từ 1 đến 240 ký tự.`);
    }
  });
  if (notes.length < 1 || notes.length > MAX_KNOWLEDGE_ITEMS || notes.some((note) => !note.trim() || note.includes("\0"))) {
    errors.push("Cần có từ 1 đến 8 ghi chú chủ đề không để trống.");
  }
  if (notes.reduce((total, note) => total + textLength(note.trim()), 0) > MAX_KNOWLEDGE_LENGTH) errors.push("Tổng độ dài ghi chú chủ đề không được vượt quá 10.000 ký tự.");
  if (teacherAgeBandRequired && !TEACHER_AGE_BAND_OPTIONS.some(({ value }) => value === teacherAgeBandRef)) {
    errors.push("Hãy chọn nhóm tuổi mục tiêu để xác nhận cho kế hoạch chưa gắn bài học trong thư viện.");
  }
  if (!reviewConfirmed) errors.push("Hãy xác nhận đã rà soát thông tin trước khi tạo Sketch Deck.");
  return errors;
}

function stateLabel(state: NonNullable<CurrentSketchDeck["current_revision"]>["state"]): string {
  switch (state) {
    case "GENERATING": return "Đang tạo";
    case "READY": return "Sẵn sàng";
    case "FAILED": return "Tạo không thành công";
    case "STALE": return "Đã cũ";
    case "SUPERSEDED": return "Đã thay thế";
  }
}

export function TeacherSketchDeckPanel({ occurrenceId, approvedRevisionNo }: Props) {
  const [plan, setPlan] = useState<PlanRevision | null>(null);
  const [current, setCurrent] = useState<CurrentSketchDeck | null>(null);
  const [topic, setTopic] = useState("");
  const [drawingSteps, setDrawingSteps] = useState<TeacherDrawingStep[]>(blankSteps);
  const [subjectKnowledge, setSubjectKnowledge] = useState<string[]>([""]);
  const [teacherConfirmedAgeBandRef, setTeacherConfirmedAgeBandRef] = useState<TeacherConfirmedAgeBandRef | "">("");
  const [reviewConfirmed, setReviewConfirmed] = useState(false);
  const [loading, setLoading] = useState(Boolean(approvedRevisionNo));
  const [submitting, setSubmitting] = useState(false);
  const [attempted, setAttempted] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [error, setError] = useState<PanelError | null>(null);
  const [notice, setNotice] = useState("");
  const [generationClock, setGenerationClock] = useState(() => Date.now());
  const [presentationOpen, setPresentationOpen] = useState(false);
  // null = follow the default: the long form is folded while a deck is ready to present.
  const [formOpenChoice, setFormOpenChoice] = useState<boolean | null>(null);
  const submissionLock = useRef(false);
  const activeRequest = useRef(0);
  const keyedRequest = useRef<KeyedRequest | null>(null);

  const occurrencePath = `/v1/lesson-occurrences/${encodeURIComponent(occurrenceId)}`;
  const planPath = `${occurrencePath}/plan-revisions/${approvedRevisionNo ?? ""}`;
  const deckPath = `${occurrencePath}/sketch-decks`;

  const reload = useCallback(async (conflict = false) => {
    const requestNo = ++activeRequest.current;
    if (!approvedRevisionNo) {
      setPlan(null);
      setCurrent(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    let failedStep = "Tải kế hoạch";
    let failedPath = planPath;
    try {
      const planResult = await teacherOccurrenceApi.getPlan(occurrenceId, approvedRevisionNo);
      const nextPlan = planResult.data;
      if (!nextPlan) throw new BackendApiError("Dịch vụ không trả về dữ liệu.", "INVALID_RESPONSE", 304);
      if (requestNo !== activeRequest.current) return;
      if (nextPlan.state !== "APPROVED" || nextPlan.revision_no !== approvedRevisionNo || !nextPlan.plan_revision_id || !/^[0-9a-f]{64}$/.test(nextPlan.content_hash)) {
        setPlan(null);
        setCurrent(null);
        setNotice("Kế hoạch đã thay đổi. Hãy làm mới buổi dạy rồi chọn bản kế hoạch đã xác nhận mới nhất.");
        return;
      }
      failedStep = "Tải trạng thái Sketch Deck";
      failedPath = deckPath;
      const nextCurrent = await teacherOccurrenceApi.getSketchDeck(occurrenceId);
      if (requestNo !== activeRequest.current) return;
      setPlan(nextPlan);
      setCurrent(nextCurrent);
      setNotice(conflict ? "Đã tải lại kế hoạch và Sketch Deck hiện tại. Hãy kiểm tra trước khi thử lại." : "");
    } catch (cause) {
      if (requestNo === activeRequest.current) setError(panelError(cause, failedStep, "GET", failedPath));
    } finally {
      if (requestNo === activeRequest.current) setLoading(false);
    }
  }, [approvedRevisionNo, deckPath, occurrenceId, planPath]);

  useEffect(() => {
    void reload();
    return () => { activeRequest.current += 1; };
  }, [reload]);

  useEffect(() => {
    const revision = current?.current_revision;
    if (!revision) return;
    setTopic(revision.topic);
    setDrawingSteps(revision.drawing_steps.map((step) => ({ action: step.action, placement: step.placement })));
    setSubjectKnowledge([...revision.subject_knowledge]);
    setReviewConfirmed(false);
    setAttempted(false);
    setValidationErrors([]);
  }, [current?.current_revision?.sketch_deck_revision_id]);

  useEffect(() => {
    setTeacherConfirmedAgeBandRef("");
    setReviewConfirmed(false);
  }, [plan?.plan_revision_id]);

  useEffect(() => {
    const revision = current?.current_revision;
    if (revision?.state !== "GENERATING") return;
    const createdAt = Date.parse(revision.created_at);
    if (!Number.isFinite(createdAt)) return;
    const remainingMs = createdAt + GENERATION_LOCK_MS - Date.now();
    if (remainingMs < 0) return;
    const timer = window.setTimeout(() => setGenerationClock(Date.now()), remainingMs + 1);
    return () => window.clearTimeout(timer);
  }, [current?.current_revision?.created_at, current?.current_revision?.state]);

  const markEdited = () => { setReviewConfirmed(false); setAttempted(false); setValidationErrors([]); setError(null); };
  const changeTopic = (value: string) => { setTopic(value); markEdited(); };
  const changeStep = (index: number, field: keyof TeacherDrawingStep, value: string) => {
    setDrawingSteps((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item));
    markEdited();
  };
  const changeKnowledge = (index: number, value: string) => {
    setSubjectKnowledge((items) => items.map((item, itemIndex) => itemIndex === index ? value : item));
    markEdited();
  };
  const changeTeacherAgeBand = (value: string) => {
    setTeacherConfirmedAgeBandRef(value as TeacherConfirmedAgeBandRef | "");
    markEdited();
  };

  const revision = current?.current_revision ?? null;
  const needsTeacherAgeBand = plan?.lesson_version_ref === null;
  const planMatches = Boolean(plan && revision && revision.plan_revision_id === plan.plan_revision_id && revision.plan_content_hash === plan.content_hash);
  const stale = Boolean(current && revision && (current.stale || revision.state === "STALE" || !planMatches));
  const revisionCreatedAt = revision ? Date.parse(revision.created_at) : Number.NaN;
  const generationInProgress = Boolean(
    revision?.state === "GENERATING" && !stale && Number.isFinite(revisionCreatedAt)
    && generationClock - revisionCreatedAt < GENERATION_LOCK_MS,
  );

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!plan || submissionLock.current || loading || generationInProgress) return;
    setAttempted(true);
    const issues = validateInput(
      topic,
      drawingSteps,
      subjectKnowledge,
      reviewConfirmed,
      needsTeacherAgeBand,
      teacherConfirmedAgeBandRef,
    );
    setValidationErrors(issues);
    if (issues.length) return;

    const input: CreateSketchDeckInput = {
      expected_plan_revision_id: plan.plan_revision_id,
      expected_plan_hash: plan.content_hash,
      review_confirmed: true,
      topic: topic.trim(),
      drawing_steps: drawingSteps.map((step) => ({ action: step.action.trim(), placement: step.placement.trim() })),
      subject_knowledge: subjectKnowledge.map((note) => note.trim()),
    };
    if (teacherConfirmedAgeBandRef) {
      input.teacher_confirmed_age_band_ref = teacherConfirmedAgeBandRef;
    }
    const fingerprint = JSON.stringify([occurrenceId, input]);
    const key = keyedRequest.current?.fingerprint === fingerprint ? keyedRequest.current.key : createIdempotencyKey();
    keyedRequest.current = { fingerprint, key };
    submissionLock.current = true;
    setSubmitting(true);
    setError(null);
    setNotice("Đang tạo Sketch Deck. Quá trình này có thể mất vài phút.");
    try {
      const revision = await teacherOccurrenceApi.createSketchDeck(occurrenceId, input, key);
      keyedRequest.current = null;
      await reload();
      setNotice(revision.state === "GENERATING" ? "Yêu cầu đang được xử lý. Làm mới trạng thái để kiểm tra." : `Đã nhận bản Sketch Deck ${revision.revision_no}.`);
    } catch (cause) {
      if (cause instanceof BackendApiError && cause.status >= 400 && cause.status < 500) keyedRequest.current = null;
      if (cause instanceof BackendApiError && cause.status === 409 && cause.code === "STALE_REVISION") {
        setNotice("Kế hoạch hoặc nguồn đã thay đổi. Đang tải lại trạng thái hiện tại.");
        await reload(true);
      } else if (cause instanceof BackendApiError && cause.status === 409 && cause.code === "SKETCH_DECK_PLAN_INCOMPLETE") {
        setError({
          ...panelError(cause, "Tạo Sketch Deck", "POST", deckPath, drawingSteps),
          message: "Kế hoạch hiện tại chưa đủ điều kiện tạo Sketch Deck. Kế hoạch cần có nhóm tuổi từ bài học đã ghim hoặc Teacher xác nhận, 1–4 mục tiêu và 1–6 hoạt động đã được duyệt. Hoạt động Teacher tự soạn cần có xác nhận checklist an toàn. Hãy bổ sung thông tin rồi xác nhận lại kế hoạch.",
        });
        setNotice("");
      } else {
        setError(panelError(cause, "Tạo Sketch Deck", "POST", deckPath, drawingSteps));
        setNotice("");
      }
    } finally {
      submissionLock.current = false;
      setSubmitting(false);
    }
  };

  const presentationDeck = current ? toTeacherSketchDeck(current, plan?.activities) : null;
  const presentable = Boolean(current && revision?.state === "READY" && current.presentable && !stale && presentationDeck);
  const issues = attempted ? validationErrors : [];
  const formOpen = formOpenChoice ?? !presentable;

  return (
    <>
      <section id="teacher-occurrence-sketch-deck" className="s2l-data-card teacher-sketch-deck-panel" aria-labelledby="teacher-sketch-deck-title">
        <p className="teacher-occurrence-eyebrow teacher-occurrence-step-label">Bước 3 · Tạo và trình chiếu</p>
        <div className="teacher-occurrence-section-title">
          <h2 id="teacher-sketch-deck-title"><Presentation size={18} aria-hidden="true" /> Sketch Deck</h2>
          <Button type="button" variant="secondary" disabled={loading || submitting || !approvedRevisionNo} onClick={() => void reload()} iconLeft={<RefreshCw size={16} aria-hidden="true" />}>Làm mới trạng thái</Button>
        </div>

        {!approvedRevisionNo && <p className="s2l-note">Cần có kế hoạch đã xác nhận trước khi tạo Sketch Deck.</p>}
        {loading && <p className="s2l-note" role="status">Đang tải kế hoạch và trạng thái Sketch Deck…</p>}
        {error && <div className="s2l-alert" role="alert">
          <p>{error.message}</p>
          <details className="teacher-occurrence-error-details">
            <summary>Thông tin kỹ thuật</summary>
            <dl>
              <dt>Bước lỗi</dt><dd>{error.step}</dd>
              <dt>Phương thức</dt><dd>{error.method}</dd>
              <dt>Đường dẫn</dt><dd><code>{error.path}</code></dd>
              <dt>Trạng thái</dt><dd>{error.status}</dd>
              <dt>Mã lỗi</dt><dd>{error.code}</dd>
              <dt>Mã yêu cầu</dt><dd>{error.requestId}</dd>
            </dl>
          </details>
        </div>}
        {notice && <p className="s2l-note" role="status">{notice}</p>}

        {!loading && plan && current?.current_revision === null && <p className="s2l-note" role="status">Chưa có Sketch Deck cho buổi dạy này.</p>}
        {revision && <div className="tw-row tw-wrap tw-gap-2" aria-label="Trạng thái Sketch Deck">
          <span className="tp-value-chip">{stateLabel(revision.state)}</span>
          <span className="tp-value-chip">Bản {revision.revision_no}</span>
          <span className="tp-value-chip">Kế hoạch {plan?.revision_no ?? revision.revision_no}</span>
        </div>}
        {stale && <div className="s2l-alert" role="alert"><strong>Sketch Deck đã cũ.</strong> Kế hoạch hoặc nguồn đã thay đổi; bản này không thể trình bày.</div>}
        {revision?.state === "GENERATING" && <p className="s2l-note" role="status">{generationInProgress
          ? "Deck đang được tạo. Để tránh gửi yêu cầu tạo đồng thời, nút tạo được khóa trong 15 phút kể từ lúc bắt đầu. Hãy làm mới trạng thái để kiểm tra."
          : "Yêu cầu tạo đã kéo dài hơn 15 phút. Bạn có thể tạo lại hoặc làm mới trạng thái để kiểm tra."}</p>}
        {revision?.state === "FAILED" && <div className="s2l-alert" role="alert">Lần tạo Sketch Deck không thành công. Hãy rà soát thông tin rồi tạo một bản mới.</div>}
        {revision?.state === "SUPERSEDED" && <p className="s2l-note" role="status">Bản Sketch Deck này đã được thay thế.</p>}
        {revision?.state === "READY" && !stale && !current?.presentable && <p className="s2l-note" role="status">Backend chưa đánh dấu bản này có thể trình bày. Làm mới trạng thái để kiểm tra lại.</p>}
        {revision?.state === "READY" && !stale && current?.presentable && !presentationDeck && <p className="s2l-note" role="status">Nội dung này chưa khớp định dạng trình chiếu hiện có.</p>}
        {revision && presentable && <Button type="button" variant="primary" onClick={() => setPresentationOpen(true)}>Mở trình chiếu</Button>}

        {plan && <details className="teacher-sketch-deck-editor" open={formOpen} onToggle={(event) => setFormOpenChoice(event.currentTarget.open)}>
          <summary>
            <span>{revision ? "Soạn bản Sketch Deck mới" : "Soạn Sketch Deck"}</span>
            <small>Chủ đề, các bước vẽ và ghi chú</small>
          </summary>
        <form className="teacher-sketch-deck-form cozy-form-stack" onSubmit={(event) => void submit(event)} noValidate>
          <p className="s2l-note">Tạo từ kế hoạch đã xác nhận · Phiên bản {plan.revision_no}. Các thay đổi cần được rà soát lại trước khi tạo.</p>
          <FormField
            label="Nhóm tuổi mục tiêu"
            htmlFor="sketch-deck-age-band"
            required={needsTeacherAgeBand}
            help={needsTeacherAgeBand
              ? "Chọn nhóm tuổi để xác nhận cho kế hoạch chưa có nguồn bài học trong thư viện."
              : "Tùy chọn nếu bài học đã ghim chưa có nhóm tuổi được hỗ trợ; nếu nguồn đã có nhóm tuổi, xác nhận phải khớp."}
          >
            <Select id="sketch-deck-age-band" value={teacherConfirmedAgeBandRef} aria-required={needsTeacherAgeBand} onChange={(event) => changeTeacherAgeBand(event.target.value)}>
              <option value="">Chọn nhóm tuổi</option>
              {TEACHER_AGE_BAND_OPTIONS.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}
            </Select>
          </FormField>
          <FormField label="Chủ đề" htmlFor="sketch-deck-topic" required help={`${textLength(topic.trim())} / ${MAX_TOPIC_LENGTH} ký tự`}>
            <input id="sketch-deck-topic" className="cozy-input" value={topic} onChange={(event) => changeTopic(event.target.value)} />
          </FormField>

          <fieldset className="cozy-form-stack">
            <legend className="cozy-form-label">Các bước vẽ <span className="cozy-form-required" aria-hidden="true">*</span></legend>
            <p className="cozy-form-hint">Nhập từ 4 đến 8 bước. Thao tác và vị trí mỗi bước dài 1–240 ký tự.</p>
            <div className="grid min-w-0 gap-3 sm:grid-cols-2">
              {drawingSteps.map((step, index) => <section key={index} className="min-w-0 rounded-lg border border-slate-200 p-3">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold">Bước {index + 1}</h3>
                  {drawingSteps.length > MIN_STEPS && <Button type="button" variant="ghost" size="sm" aria-label={`Bỏ bước ${index + 1}`} onClick={() => { setDrawingSteps((items) => items.filter((_, itemIndex) => itemIndex !== index)); markEdited(); }}>Bỏ</Button>}
                </div>
                  <FormField label={`Thao tác bước ${index + 1}`} htmlFor={`sketch-deck-action-${index}`} required help={`${textLength(step.action.trim())} / ${MAX_TEXT_LENGTH}`}>
                  <textarea id={`sketch-deck-action-${index}`} className="cozy-textarea" rows={2} value={step.action} onChange={(event) => changeStep(index, "action", event.target.value)} />
                </FormField>
                <FormField label={`Vị trí bước ${index + 1}`} htmlFor={`sketch-deck-placement-${index}`} required help={`${textLength(step.placement.trim())} / ${MAX_TEXT_LENGTH}`}>
                  <textarea id={`sketch-deck-placement-${index}`} className="cozy-textarea" rows={2} value={step.placement} onChange={(event) => changeStep(index, "placement", event.target.value)} />
                </FormField>
              </section>)}
            </div>
            {drawingSteps.length < MAX_STEPS && <Button type="button" variant="secondary" iconLeft={<Plus size={16} aria-hidden="true" />} onClick={() => { setDrawingSteps((items) => [...items, { action: "", placement: "" }]); markEdited(); }}>Thêm bước</Button>}
          </fieldset>

          <fieldset className="cozy-form-stack">
            <legend className="cozy-form-label">Ghi chú về chủ đề <span className="cozy-form-required" aria-hidden="true">*</span></legend>
            <p className="cozy-form-hint">Nhập từ 1 đến 8 ghi chú; tổng độ dài tối đa 10.000 ký tự.</p>
            {subjectKnowledge.map((note, index) => <div key={index} className="flex min-w-0 items-start gap-2">
              <FormField className="min-w-0 flex-1" label={`Ghi chú ${index + 1}`} htmlFor={`sketch-deck-note-${index}`} required help={`${subjectKnowledge.reduce((total, item) => total + textLength(item.trim()), 0)} / ${MAX_KNOWLEDGE_LENGTH} ký tự`}>
                <textarea id={`sketch-deck-note-${index}`} className="cozy-textarea" rows={2} value={note} onChange={(event) => changeKnowledge(index, event.target.value)} />
              </FormField>
              {subjectKnowledge.length > 1 && <Button type="button" variant="ghost" size="sm" className="mt-7 shrink-0" aria-label={`Bỏ ghi chú ${index + 1}`} onClick={() => { setSubjectKnowledge((items) => items.filter((_, itemIndex) => itemIndex !== index)); markEdited(); }}><Trash2 size={16} aria-hidden="true" /></Button>}
            </div>)}
            {subjectKnowledge.length < MAX_KNOWLEDGE_ITEMS && <Button type="button" variant="secondary" iconLeft={<Plus size={16} aria-hidden="true" />} onClick={() => { setSubjectKnowledge((items) => [...items, ""]); markEdited(); }}>Thêm ghi chú</Button>}
          </fieldset>

          <label className="flex min-w-0 items-start gap-3 text-sm text-slate-800">
            <input className="mt-1 h-4 w-4 shrink-0" type="checkbox" checked={reviewConfirmed} onChange={(event) => { setReviewConfirmed(event.target.checked); setAttempted(false); setValidationErrors([]); }} />
            <span>Tôi đã rà soát chủ đề, các bước vẽ và ghi chú{needsTeacherAgeBand || teacherConfirmedAgeBandRef ? ", đồng thời xác nhận nhóm tuổi mục tiêu" : ""} trước khi tạo Sketch Deck.</span>
          </label>
          {issues.length > 0 && <ul className="s2l-alert" role="alert" aria-label="Thông tin Sketch Deck chưa hợp lệ">{issues.map((issue) => <li key={issue}>{issue}</li>)}</ul>}
          <FormActionBar hint={generationInProgress
            ? "Đang có yêu cầu tạo Sketch Deck được xử lý; hãy chờ hoặc làm mới trạng thái trước khi tạo lại."
            : !loading && !submitting && !reviewConfirmed ? "Xác nhận đã rà soát để tạo Sketch Deck." : undefined}>
            <Button type="submit" variant="primary" loading={submitting} disabled={loading || submitting || !plan || generationInProgress}>
              {submitting ? "Đang tạo Sketch Deck…" : "Tạo Sketch Deck"}
            </Button>
          </FormActionBar>
        </form>
        </details>}
      </section>

      {presentationOpen && presentable && presentationDeck && <TeacherDeckPresentation deck={presentationDeck} onClose={() => setPresentationOpen(false)} />}
    </>
  );
}
