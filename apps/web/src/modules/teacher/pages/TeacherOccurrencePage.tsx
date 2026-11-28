import { entryLinks } from "../services/teacherRunLogic";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw, Upload, FileText, ClipboardList, CalendarDays } from "lucide-react";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { Button, DateField, FormField, Select, StatusBadge, formatDateDdMmYyyy, formatDateTimeDdMmYyyy } from "../../../shared/ui";
import { FormActionBar } from "../components/FormActionBar";
import { PlanActivityPicker } from "../components/PlanActivityPicker";
import { TeacherSketchDeckPanel } from "../components/TeacherSketchDeckPanel";
import { teacherStatusMeta } from "../services/teacherStatus";
import { authService } from "../../school-manager/be1/services/authService";
import {
  BackendApiError,
  backendApi,
  configuredOrganizationId,
  createIdempotencyKey,
  hasFirebaseAuthBridge,
  type Be1Class,
  type LessonSummary,
} from "../../../shared/api/backendApi";
import {
  OccurrenceApiError,
  PLAN_LIMITS,
  pollJob,
  teacherOccurrenceApi,
  type ConditionalResult,
  type DocumentRevision,
  type DocumentRevisionSummary,
  type FieldIssue,
  type JobState,
  type JobStatus,
  type LessonVersionRef,
  type Occurrence,
  type OccurrenceState,
  type OccurrenceUploadKeys,
  type PlanRevision,
  type PlanRevisionSummary,
  type SourceDocument,
} from "../../../shared/api/teacherOccurrenceApi";

const OCCURRENCE_STATE_LABEL: Record<OccurrenceState, string> = {
  DRAFT: "Bản nháp", DOCUMENT_REVIEW: "Rà soát tài liệu", PLAN_REVIEW: "Rà soát kế hoạch", APPROVED: "Đã duyệt",
  SAMPLE_AVAILABLE: "Có thể tạo video mẫu", SAMPLE_USED: "Đã dùng video mẫu", ARCHIVED: "Đã lưu trữ",
};
const JOB_STATE_LABEL: Record<JobState, string> = {
  queued: "Đang chờ xử lý", running: "Đang xử lý", succeeded: "Đã hoàn tất", failed_retryable: "Gặp lỗi, hệ thống sẽ thử lại",
  failed_exhausted: "Không xử lý được", blocked_unsafe: "Bị chặn vì nội dung không an toàn", cancelled: "Đã hủy",
};
const PLAN_STATE_LABEL: Record<PlanRevision["state"], string> = { DRAFT: "Bản nháp", APPROVED: "Đã xác nhận", SUPERSEDED: "Đã thay thế" };
const DOCUMENT_STATE_LABEL: Record<SourceDocument["document_state"], string> = { EXTRACTED: "Đã trích xuất", DELETED: "Đã xóa" };

type KeyedIdentity = { key: string; fingerprint: string };
type UploadIdentity = { fingerprint: string; keys: OccurrenceUploadKeys; uploadId: string | null; assetRef: string | null; attachKey: string; abortKey: string };
type Cached<T> = { etag: string; data: T };
type RequestContext = { step: string; method: string; path: string };
type RequestDiagnostic = RequestContext & { status: string; code: string; requestId: string };

class ContextualRequestError extends Error {
  readonly context: RequestContext;
  readonly original: unknown;

  constructor(context: RequestContext, original: unknown) {
    super(errorText(original));
    this.name = "ContextualRequestError";
    this.context = context;
    this.original = original;
  }
}

async function withRequestContext<T>(context: RequestContext, request: () => Promise<T>): Promise<T> {
  try { return await request(); }
  catch (cause) { throw new ContextualRequestError(context, cause); }
}

function diagnosticFor(cause: unknown): RequestDiagnostic | null {
  if (!(cause instanceof ContextualRequestError)) return null;
  const original = cause.original;
  const apiError = original instanceof BackendApiError ? original : null;
  return {
    ...cause.context,
    status: apiError ? String(apiError.status) : "Không có",
    code: apiError?.code ?? "Không có",
    requestId: apiError?.requestId ?? "Không có",
  };
}

function messageForFailure(cause: unknown): string {
  return cause instanceof ContextualRequestError ? errorText(cause.original) : errorText(cause);
}

function originalCause(cause: unknown): unknown {
  return cause instanceof ContextualRequestError ? cause.original : cause;
}

/** One key per user action: a retry of the same body reuses it, a rejected (4xx) or finished action drops it. */
async function keyedWrite<T>(identity: { current: KeyedIdentity | null }, body: unknown, write: (key: string) => Promise<T>): Promise<T> {
  const fingerprint = JSON.stringify(body);
  const key = identity.current?.fingerprint === fingerprint ? identity.current.key : createIdempotencyKey();
  identity.current = { key, fingerprint };
  try { const result = await write(key); identity.current = null; return result; }
  catch (cause) {
    if (cause instanceof BackendApiError && cause.status >= 400 && cause.status < 500) identity.current = null;
    throw cause;
  }
}

/** Conditional GET that keeps the last body, so a 304 answers from the cache of this screen. */
async function cachedGet<T>(cache: Map<string, Cached<T>>, key: string, read: (etag?: string) => Promise<ConditionalResult<T>>): Promise<T> {
  const hit = cache.get(key);
  const result = await read(hit?.etag);
  if (result.data) { if (result.etag) cache.set(key, { etag: result.etag, data: result.data }); return result.data; }
  if (hit) return hit.data;
  throw new BackendApiError("Dịch vụ không trả về dữ liệu.", "INVALID_RESPONSE", 304);
}

const charLength = (value: string) => [...value].length;
const FIELD_LABEL: Record<string, string> = {
  objectives: "Mục tiêu học tập", teacher_direction: "Hướng dẫn cho giáo viên", safety_notes: "Ghi chú an toàn",
  document_revision_ref: "Bản văn bản làm nguồn", activities: "Hoạt động", expected_head_revision_no: "Bản kế hoạch hiện tại",
  extracted_text: "Văn bản", title: "Tên buổi dạy", scheduled_date: "Ngày dự kiến", lesson_version_ref: "Giáo án đã ghim",
};
const CODE_LABEL: Record<string, string> = {
  INVALID_FORMAT: "không hợp lệ", NOT_SUPPORTED: "chưa được hỗ trợ", REQUIRED: "còn thiếu", TOO_LONG: "quá dài", TOO_MANY: "quá nhiều mục",
};
/** One safe line per field error: a known label (or the field path) and a short Vietnamese reason. */
function fieldIssueText(issue: FieldIssue): string {
  const root = issue.field.split(/[.[]/)[0];
  const index = /^objectives\[(\d+)\]/.exec(issue.field);
  const label = index ? `${FIELD_LABEL.objectives} (dòng ${Number(index[1]) + 1})` : FIELD_LABEL[root] ?? issue.field;
  return `${label}: ${CODE_LABEL[issue.code] ?? "không hợp lệ"}.`;
}
const errorText = (cause: unknown) => cause instanceof Error ? cause.message : "Không thể hoàn tất yêu cầu. Hãy thử lại.";
const isAbort = (cause: unknown) => cause instanceof Error && cause.name === "AbortError";
const isStale = (cause: unknown) => {
  const source = originalCause(cause);
  return source instanceof BackendApiError && source.code === "STALE_REVISION";
};

const OCCURRENCE_STEPS = [
  { id: "teacher-occurrence-documents", label: "Tài liệu" },
  { id: "teacher-occurrence-plan", label: "Kế hoạch" },
  { id: "teacher-occurrence-sketch-deck", label: "Sketch Deck" },
] as const;

export function TeacherOccurrencePage() {
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [selectedClassId, setSelectedClassId] = useState("");
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [selectedLessonId, setSelectedLessonId] = useState("");
  const [occurrences, setOccurrences] = useState<Occurrence[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [occurrence, setOccurrence] = useState<Occurrence | null>(null);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [revisions, setRevisions] = useState<DocumentRevisionSummary[]>([]);
  const [selectedRevision, setSelectedRevision] = useState<DocumentRevision | null>(null);
  const [plans, setPlans] = useState<PlanRevisionSummary[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<PlanRevision | null>(null);
  const [title, setTitle] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState("");
  const [uploadAbortable, setUploadAbortable] = useState(false);
  const [editedText, setEditedText] = useState("");
  const [objectives, setObjectives] = useState("");
  const [direction, setDirection] = useState("");
  const [safetyNotes, setSafetyNotes] = useState("");
  const [planDocumentRevision, setPlanDocumentRevision] = useState("");
  const [carriedActivities, setCarriedActivities] = useState<Array<{ kind: "LESSON"; lesson_activity_id: string }>>([]);
  const [copiedActivitiesFromPlan, setCopiedActivitiesFromPlan] = useState(false);
  const [jobId, setJobId] = useState("");
  const [job, setJob] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyCount, setBusyCount] = useState(0);
  const [error, setError] = useState("");
  const [diagnostic, setDiagnostic] = useState<RequestDiagnostic | null>(null);
  const failureStepRef = useRef<string | null>(null);
  const [fieldIssues, setFieldIssues] = useState<FieldIssue[]>([]);
  const [notice, setNotice] = useState("");
  const occurrenceCache = useRef(new Map<string, Cached<Occurrence>>());
  const documentCache = useRef(new Map<string, Cached<SourceDocument>>());
  const revisionCache = useRef(new Map<string, Cached<DocumentRevision>>());
  const planCache = useRef(new Map<string, Cached<PlanRevision>>());
  const createOccurrenceIdentity = useRef<KeyedIdentity | null>(null);
  const editTextIdentity = useRef<KeyedIdentity | null>(null);
  const createPlanIdentity = useRef<KeyedIdentity | null>(null);
  const confirmPlanIdentity = useRef<KeyedIdentity | null>(null);
  const uploadIdentity = useRef<UploadIdentity | null>(null);
  const occurrenceIdRef = useRef("");
  const classIdRef = useRef("");
  const accountUidRef = useRef<string | null>(null);
  const assignmentClassIdsRef = useRef<string[]>([]);
  const dataEpochRef = useRef(0);
  const uploadController = useRef<AbortController | null>(null);
  const busy = busyCount > 0;
  const organizationId = configuredOrganizationId();
  const occurrenceId = occurrence?.occurrence_id ?? "";
  const selectedClass = classes.find((item) => item.class_id === selectedClassId) ?? null;
  const selectedDocument = documents.find((item) => item.source_document_id === selectedDocumentId) ?? null;
  const headRevisionNo = selectedDocument?.head_revision_no;
  const currentHeadPlan = plans[0] ?? null;
  const lessonLabel = lessons.find((item) => item.lesson_id === selectedLessonId)?.title ?? "";
  const objectiveLines = objectives.split("\n").map((item) => item.trim()).filter(Boolean);
  const objectivesProblem =
    objectiveLines.length > PLAN_LIMITS.objectives
      ? `Tối đa ${PLAN_LIMITS.objectives} mục tiêu (đang có ${objectiveLines.length}).`
      : objectiveLines.some((item) => charLength(item) > PLAN_LIMITS.objectiveChars)
        ? `Mỗi mục tiêu tối đa ${PLAN_LIMITS.objectiveChars} ký tự.`
        : "";
  const directionProblem = charLength(direction) > PLAN_LIMITS.directionChars ? `Hướng dẫn tối đa ${PLAN_LIMITS.directionChars} ký tự.` : "";
  const safetyProblem = charLength(safetyNotes) > PLAN_LIMITS.safetyNotesChars ? `Ghi chú an toàn tối đa ${PLAN_LIMITS.safetyNotesChars} ký tự.` : "";
  const planProblems = [objectivesProblem, directionProblem, safetyProblem].filter(Boolean);
  const issueFor = (rootField: string) => {
    const matched = fieldIssues.filter((issue) => issue.field.split(/[.[]/)[0] === rootField);
    return matched.length ? matched.map(fieldIssueText).join(" ") : undefined;
  };
  const mappedFields = new Set([
    "title",
    "scheduled_date",
    "lesson_version_ref",
    "extracted_text",
    "objectives",
    "teacher_direction",
    "safety_notes",
    "document_revision_ref",
  ]);
  const unmappedIssues = fieldIssues.filter((issue) => !mappedFields.has(issue.field.split(/[.[]/)[0]));
  const checklistBlocked = Boolean(selectedPlan?.activities.some((activity) => activity.checklist_required && !activity.confirmed));

  const showFailure = useCallback((cause: unknown) => {
    const nextDiagnostic = diagnosticFor(cause);
    failureStepRef.current = nextDiagnostic?.step ?? null;
    setError(messageForFailure(cause));
    setDiagnostic(nextDiagnostic);
  }, []);

  const clearAccountScopedData = useCallback(() => {
    dataEpochRef.current += 1;
    classIdRef.current = "";
    occurrenceIdRef.current = "";
    setClasses([]); setSelectedClassId(""); setLessons([]); setSelectedLessonId("");
    setOccurrences([]); setNextCursor(null); setOccurrence(null);
    setDocuments([]); setSelectedDocumentId(""); setRevisions([]); setSelectedRevision(null);
    setPlans([]); setSelectedPlan(null); setJobId(""); setJob(null);
    setTitle(""); setScheduledDate(""); setFile(null); setUploadProgress(""); setUploadAbortable(false);
    setEditedText(""); setObjectives(""); setDirection(""); setSafetyNotes(""); setPlanDocumentRevision(""); setCarriedActivities([]); setCopiedActivitiesFromPlan(false);
    failureStepRef.current = null;
    setError(""); setDiagnostic(null); setFieldIssues([]); setNotice("");
    occurrenceCache.current.clear(); documentCache.current.clear(); revisionCache.current.clear(); planCache.current.clear();
    createOccurrenceIdentity.current = null; editTextIdentity.current = null; createPlanIdentity.current = null; confirmPlanIdentity.current = null;
    uploadController.current?.abort(); uploadController.current = null; uploadIdentity.current = null;
  }, []);

  const refreshClasses = useCallback(async () => {
    if (!hasFirebaseAuthBridge()) throw new BackendApiError("Phiên đăng nhập chưa sẵn sàng.", "AUTHENTICATION_REQUIRED", 401);
    if (!organizationId) throw new BackendApiError("Chưa cấu hình tổ chức.", "ORGANIZATION_REQUIRED", 400);
    const encodedOrganizationId = encodeURIComponent(organizationId);
    const identityEpoch = dataEpochRef.current;
    const identity = await withRequestContext(
      { step: "Tải lớp được phân công", method: "GET", path: `/api/be1/v1/organizations/${encodedOrganizationId}/me` },
      () => backendApi.assignments(organizationId),
    );
    if (identityEpoch !== dataEpochRef.current) return;
    const allowed = new Set(identity.assignments
      .filter((assignment) => assignment.role === "teacher" && assignment.active !== false)
      .flatMap((assignment) => assignment.class_id ? [assignment.class_id] : []));
    const nextAssignmentIds = [...allowed].sort();
    if (JSON.stringify(nextAssignmentIds) !== JSON.stringify(assignmentClassIdsRef.current)) {
      assignmentClassIdsRef.current = nextAssignmentIds;
      clearAccountScopedData();
      setLoading(true);
    }
    const requestEpoch = dataEpochRef.current;
    if (!allowed.size) { setClasses([]); setLessons([]); setSelectedClassId(""); return; }
    const [classPage, lessonPage] = await Promise.all([
      withRequestContext(
        { step: "Tải lớp được phân công", method: "GET", path: `/api/be1/v1/organizations/${encodedOrganizationId}/classes?state=active&limit=100` },
        () => backendApi.classes(organizationId, "active"),
      ),
      withRequestContext(
        { step: "Tải giáo án", method: "GET", path: `/api/lesson-library/v1/organizations/${encodedOrganizationId}/lessons?state=ACTIVE` },
        () => backendApi.lessons(organizationId, { state: "ACTIVE" }),
      ),
    ]);
    if (requestEpoch !== dataEpochRef.current) return;
    const assignedClasses = classPage.items.filter((item) => allowed.has(item.class_id));
    setClasses(assignedClasses);
    setLessons(lessonPage.items.filter((item) => item.review_state === "APPROVED"));
    const nextSelectedClass = assignedClasses.some((item) => item.class_id === classIdRef.current) ? classIdRef.current : assignedClasses[0]?.class_id ?? "";
    classIdRef.current = nextSelectedClass;
    setSelectedClassId(nextSelectedClass);
  }, [clearAccountScopedData, organizationId]);

  const refreshOccurrences = useCallback(async (classId: string, cursor?: string) => {
    if (!classId) { setOccurrences([]); setNextCursor(null); setOccurrence(null); return; }
    const query = new URLSearchParams({ limit: "25", class_id: classId });
    if (cursor) query.set("cursor", cursor);
    const page = await withRequestContext(
      { step: "Tải danh sách buổi dạy", method: "GET", path: `/v1/lesson-occurrences?${query}` },
      () => teacherOccurrenceApi.list(classId, { cursor }),
    );
    if (classIdRef.current !== classId) return; // the Teacher switched class while this page was loading
    if (failureStepRef.current === "Tải danh sách buổi dạy") {
      failureStepRef.current = null;
      setError("");
      setDiagnostic(null);
    }
    setNextCursor(page.next_cursor);
    setOccurrences((items) => cursor ? [...items, ...page.items.filter((item) => !items.some((known) => known.occurrence_id === item.occurrence_id))] : page.items);
    if (!cursor) setOccurrence((current) => page.items.find((item) => item.occurrence_id === current?.occurrence_id) ?? page.items[0] ?? null);
  }, []);

  const refreshOccurrence = useCallback(async (id: string) => {
    const fresh = await withRequestContext(
      { step: "Tải buổi dạy", method: "GET", path: `/v1/lesson-occurrences/${encodeURIComponent(id)}` },
      () => cachedGet(occurrenceCache.current, id, (etag) => teacherOccurrenceApi.get(id, etag)),
    );
    setOccurrence((current) => current?.occurrence_id === id ? fresh : current);
    setOccurrences((items) => items.map((item) => item.occurrence_id === id ? fresh : item));
  }, []);

  const refreshDocumentsAndPlans = useCallback(async (id: string) => {
    const documentPage = await withRequestContext(
      { step: "Tải tài liệu", method: "GET", path: `/v1/lesson-occurrences/${encodeURIComponent(id)}/documents?limit=25` },
      () => teacherOccurrenceApi.listDocuments(id),
    );
    if (occurrenceIdRef.current !== id) return;
    setDocuments(documentPage.items);
    setSelectedDocumentId((current) => documentPage.items.some((item) => item.source_document_id === current) ? current : documentPage.items[0]?.source_document_id ?? "");
    const planPage = await withRequestContext(
      { step: "Tải kế hoạch", method: "GET", path: `/v1/lesson-occurrences/${encodeURIComponent(id)}/plan-revisions?limit=25` },
      () => teacherOccurrenceApi.listPlans(id),
    );
    if (occurrenceIdRef.current !== id) return;
    setPlans(planPage.items);
    return planPage.items;
  }, []);

  useEffect(() => { occurrenceIdRef.current = occurrenceId; }, [occurrenceId]);
  useEffect(() => { classIdRef.current = selectedClassId; }, [selectedClassId]);
  useEffect(() => () => uploadController.current?.abort(), []);

  useEffect(() => {
    let current = true;
    const unsubscribe = authService.observe((user) => {
      if (!current) return;
      const nextUid = user?.uid ?? null;
      if (accountUidRef.current === nextUid) return;
      accountUidRef.current = nextUid;
      assignmentClassIdsRef.current = [];
      clearAccountScopedData();
      if (!user) { setLoading(false); return; }
      setLoading(true);
      refreshClasses()
        .catch((cause: unknown) => { if (current) showFailure(cause); })
        .finally(() => { if (current) setLoading(false); });
    });
    return () => { current = false; accountUidRef.current = null; unsubscribe(); };
  }, [clearAccountScopedData, refreshClasses, showFailure]);

  useEffect(() => {
    const refreshAssignments = () => {
      if (document.visibilityState === "hidden" || !accountUidRef.current) return;
      refreshClasses().catch(showFailure);
    };
    window.addEventListener("focus", refreshAssignments);
    document.addEventListener("visibilitychange", refreshAssignments);
    return () => {
      window.removeEventListener("focus", refreshAssignments);
      document.removeEventListener("visibilitychange", refreshAssignments);
    };
  }, [refreshClasses, showFailure]);

  useEffect(() => {
    let current = true;
    refreshOccurrences(selectedClassId).catch((cause: unknown) => { if (current) showFailure(cause); });
    return () => { current = false; };
  }, [selectedClassId, refreshOccurrences, showFailure]);

  useEffect(() => {
    setDocuments([]); setSelectedDocumentId(""); setRevisions([]); setSelectedRevision(null); setPlans([]); setSelectedPlan(null);
    setJobId(""); setJob(null);
    setObjectives(""); setDirection(""); setSafetyNotes(""); setPlanDocumentRevision(""); setCarriedActivities([]); setCopiedActivitiesFromPlan(false); setEditedText("");
    setFile(null); setUploadProgress(""); setUploadAbortable(false);
    uploadController.current?.abort(); uploadIdentity.current = null;
    if (!occurrenceId) return;
    let current = true;
    refreshDocumentsAndPlans(occurrenceId).catch((cause: unknown) => { if (current) showFailure(cause); });
    return () => { current = false; };
  }, [occurrenceId, refreshDocumentsAndPlans, showFailure]);

  // Revision history and the head text of the selected document. A 304 reuses the cached body.
  useEffect(() => {
    if (!occurrenceId || !selectedDocumentId || headRevisionNo === undefined) { setRevisions([]); setSelectedRevision(null); return; }
    let current = true;
    (async () => {
      const [revisionPage, fresh] = await Promise.all([
        withRequestContext(
          { step: "Tải tài liệu", method: "GET", path: `/v1/lesson-occurrences/${encodeURIComponent(occurrenceId)}/documents/${encodeURIComponent(selectedDocumentId)}/revisions?limit=25` },
          () => teacherOccurrenceApi.listDocumentRevisions(occurrenceId, selectedDocumentId),
        ),
        withRequestContext(
          { step: "Tải tài liệu", method: "GET", path: `/v1/lesson-occurrences/${encodeURIComponent(occurrenceId)}/documents/${encodeURIComponent(selectedDocumentId)}` },
          () => cachedGet(documentCache.current, selectedDocumentId, (etag) => teacherOccurrenceApi.getDocument(occurrenceId, selectedDocumentId, etag)),
        ),
      ]);
      const headNo = Math.max(fresh.head_revision_no, headRevisionNo);
      const text = await withRequestContext(
        { step: "Tải tài liệu", method: "GET", path: `/v1/lesson-occurrences/${encodeURIComponent(occurrenceId)}/documents/${encodeURIComponent(selectedDocumentId)}/revisions/${headNo}` },
        () => cachedGet(revisionCache.current, `${selectedDocumentId}:${headNo}`, (etag) => teacherOccurrenceApi.getDocumentRevision(occurrenceId, selectedDocumentId, headNo, etag)),
      );
      if (!current) return;
      setRevisions(revisionPage.items); setSelectedRevision(text); setEditedText(text.extracted_text);
      setDocuments((items) => items.map((item) => item.source_document_id === fresh.source_document_id && fresh.head_revision_no > item.head_revision_no ? fresh : item));
    })().catch((cause: unknown) => { if (current) showFailure(cause); });
    return () => { current = false; };
  }, [occurrenceId, selectedDocumentId, headRevisionNo, showFailure]);

  // One poller per extraction job; unmounting or switching occurrence aborts it.
  useEffect(() => {
    if (!jobId) return;
    const controller = new AbortController();
    const forOccurrence = occurrenceIdRef.current;
    pollJob(jobId, setJob, controller.signal)
      .then(async (terminal) => {
        setNotice(terminal.state === "succeeded" ? "Tài liệu đã được trích xuất." : `Trạng thái xử lý: ${JOB_STATE_LABEL[terminal.state]}.`);
        await refreshDocumentsAndPlans(forOccurrence);
        await refreshOccurrence(forOccurrence);
      })
      .catch((cause: unknown) => { if (!isAbort(cause)) showFailure(cause); });
    return () => controller.abort();
  }, [jobId, refreshDocumentsAndPlans, refreshOccurrence, showFailure]);

  /** After a STALE_REVISION answer: show the safe message, then reload the heads so the next try is made on current data. */
  const reloadHeads = async () => {
    const id = occurrenceIdRef.current;
    if (!id) return;
    const planItems = await refreshDocumentsAndPlans(id);
    await refreshOccurrence(id);
    documentCache.current.clear();
    const head = planItems?.[0];
    setSelectedPlan(head ? await cachedGet(planCache.current, `${id}:${head.revision_no}`, (etag) => teacherOccurrenceApi.getPlan(id, head.revision_no, etag)) : null);
    setNotice("Đã tải lại bản mới nhất. Hãy kiểm tra rồi thử lại.");
  };

  const runAction = async (action: () => Promise<void>) => {
    setBusyCount((count) => count + 1); setError(""); setDiagnostic(null); setFieldIssues([]); setNotice("");
    try { await action(); }
    catch (cause) {
      if (isAbort(cause)) return;
      showFailure(cause);
      const source = originalCause(cause);
      if (source instanceof OccurrenceApiError) setFieldIssues(source.fieldErrors);
      if (isStale(cause)) { try { await reloadHeads(); } catch (reloadCause) { showFailure(reloadCause); } }
    }
    finally { setBusyCount((count) => count - 1); }
  };

  const createOccurrence = () => runAction(async () => {
    if (!selectedClassId) throw new Error("Chọn lớp được phân công trước khi tạo buổi dạy.");
    let lessonVersionRef: LessonVersionRef | null = null;
    if (selectedLessonId) {
      const detail = await backendApi.teacherLesson(organizationId, selectedLessonId);
      if (!detail.current_version.content || detail.current_version.review_state !== "APPROVED") throw new Error("Chỉ có thể ghim phiên bản giáo án đã được duyệt.");
      lessonVersionRef = { lesson_id: detail.lesson_id, version_id: detail.current_version.version_id, content_sha256: detail.current_version.structured_content_hash };
    }
    const input = { class_id: selectedClassId, title: title.trim(), scheduled_date: scheduledDate || null, lesson_version_ref: lessonVersionRef };
    const created = await withRequestContext(
      { step: "Tạo buổi dạy", method: "POST", path: "/v1/lesson-occurrences" },
      () => keyedWrite(createOccurrenceIdentity, input, (key) => teacherOccurrenceApi.create(input, key)),
    );
    setTitle(""); setScheduledDate(""); setSelectedLessonId("");
    setOccurrences((items) => [created, ...items.filter((item) => item.occurrence_id !== created.occurrence_id)]);
    setOccurrence(created); setNotice("Đã tạo buổi dạy.");
  });

  const selectOccurrence = (item: Occurrence) => runAction(async () => {
    setOccurrence(item); setSelectedPlan(null);
    await refreshOccurrence(item.occurrence_id);
  });

  const uploadAndAttach = () => runAction(async () => {
    if (!file || !occurrence) return;
    const id = occurrence.occurrence_id;
    const fingerprint = `${id}:${file.name}:${file.size}:${file.lastModified}`;
    if (uploadIdentity.current?.fingerprint !== fingerprint) {
      uploadIdentity.current = { fingerprint, keys: { create: createIdempotencyKey(), complete: createIdempotencyKey() }, uploadId: null, assetRef: null, attachKey: createIdempotencyKey(), abortKey: createIdempotencyKey() };
    }
    const transaction = uploadIdentity.current;
    const controller = new AbortController();
    uploadController.current = controller;
    setUploadAbortable(true);
    try {
      transaction.assetRef ??= await teacherOccurrenceApi.uploadOccurrenceFile(file, id, {
        keys: transaction.keys,
        signal: controller.signal,
        onSession: (session) => { transaction.uploadId = session.upload_id; },
        onProgress: (done, total) => { if (!controller.signal.aborted) setUploadProgress(`${Math.round(done / total * 100)}%`); },
      });
      if (controller.signal.aborted) return;
      const accepted = await teacherOccurrenceApi.attachDocument(id, transaction.assetRef, transaction.attachKey);
      uploadIdentity.current = null;
      if (controller.signal.aborted || occurrenceIdRef.current !== id) return;
      setUploadAbortable(false); setFile(null); setUploadProgress("");
      setNotice("Đã đính kèm tài liệu. Đang theo dõi quá trình trích xuất.");
      await refreshDocumentsAndPlans(id);
      if (occurrenceIdRef.current !== id) return;
      setSelectedDocumentId(accepted.source_document_id);
      setJob(null); setJobId(accepted.job.job_id);
    } catch (cause) {
      // A refusal (4xx: expired session, conflict, bad content) cannot be retried with the same keys.
      if (cause instanceof BackendApiError && cause.status >= 400 && cause.status < 500 && occurrenceIdRef.current === id) { uploadIdentity.current = null; setUploadAbortable(false); setUploadProgress(""); }
      throw cause;
    }
  });

  const stopUpload = () => uploadController.current?.abort();

  const abortUpload = () => runAction(async () => {
    const transaction = uploadIdentity.current;
    const clear = () => { uploadIdentity.current = null; setUploadAbortable(false); setUploadProgress(""); setFile(null); };
    try {
      if (transaction?.uploadId && !transaction.assetRef) await teacherOccurrenceApi.abortOpenUpload(transaction.uploadId, transaction.abortKey);
      clear();
      setNotice("Đã hủy phiên tải lên.");
    } catch (cause) {
      // Keep the session (and the abort key) for a retry on a stale revision or a transient failure; a final refusal
      // (expired, not found, wrong state) ends it.
      if (cause instanceof BackendApiError && cause.status >= 400 && cause.status < 500 && cause.code !== "STALE_REVISION") clear();
      throw cause;
    }
  });

  const openRevision = (revisionNo: number) => runAction(async () => {
    if (!occurrence || !selectedDocument) return;
    const id = selectedDocument.source_document_id;
    const revision = await withRequestContext(
      { step: "Tải tài liệu", method: "GET", path: `/v1/lesson-occurrences/${encodeURIComponent(occurrence.occurrence_id)}/documents/${encodeURIComponent(id)}/revisions/${revisionNo}` },
      () => cachedGet(revisionCache.current, `${id}:${revisionNo}`, (etag) => teacherOccurrenceApi.getDocumentRevision(occurrence.occurrence_id, id, revisionNo, etag)),
    );
    setSelectedRevision(revision); setEditedText(revision.extracted_text);
  });

  const saveEditedText = () => runAction(async () => {
    if (!occurrence || !selectedDocument) return;
    const input = { occurrence_id: occurrence.occurrence_id, document_id: selectedDocument.source_document_id, extracted_text: editedText, expected_head_revision_no: selectedDocument.head_revision_no };
    const saved = await keyedWrite(editTextIdentity, input, (key) => teacherOccurrenceApi.editDocumentRevision(input.occurrence_id, input.document_id, input.extracted_text, input.expected_head_revision_no, key));
    setSelectedRevision(saved); setEditedText(saved.extracted_text); setNotice(`Đã lưu bản văn bản ${saved.revision_no}.`);
    await refreshDocumentsAndPlans(occurrence.occurrence_id);
  });

  const savePlan = () => runAction(async () => {
    if (!occurrence) return;
    if (planProblems.length) throw new Error(planProblems[0]);
    const [documentId, revisionText] = planDocumentRevision.split(":");
    const revisionNo = Number(revisionText);
    const input = {
      expected_head_revision_no: currentHeadPlan?.revision_no ?? 0,
      document_revision_ref: documentId && revisionNo > 0 ? { document_id: documentId, revision_no: revisionNo } : null,
      objectives: objectiveLines,
      teacher_direction: direction,
      safety_notes: safetyNotes.trim() ? safetyNotes : null,
      activities: carriedActivities,
    };
    const saved = await keyedWrite(createPlanIdentity, { occurrence_id: occurrence.occurrence_id, ...input }, (key) => teacherOccurrenceApi.createPlan(occurrence.occurrence_id, input, key));
    setSelectedPlan(saved); setNotice(`Đã tạo bản kế hoạch ${saved.revision_no} ở trạng thái nháp.`);
    await refreshDocumentsAndPlans(occurrence.occurrence_id);
  });

  /** New revision from the selected one: copies its text fields and its LESSON activities; the head is re-read on save. */
  const editPlan = (plan: PlanRevision) => {
    setObjectives(plan.objectives.join("\n")); setDirection(plan.teacher_direction); setSafetyNotes(plan.safety_notes ?? "");
    setPlanDocumentRevision(plan.document_revision_ref ? `${plan.document_revision_ref.document_id}:${plan.document_revision_ref.revision_no}` : "");
    setCarriedActivities(plan.activities.flatMap((activity) => activity.kind === "LESSON" && activity.lesson_activity_id ? [{ kind: "LESSON" as const, lesson_activity_id: activity.lesson_activity_id }] : []));
    setCopiedActivitiesFromPlan(true);
  };

  const openPlan = (revisionNo: number) => runAction(async () => {
    if (!occurrence) return;
    const plan = await withRequestContext(
      { step: "Tải kế hoạch", method: "GET", path: `/v1/lesson-occurrences/${encodeURIComponent(occurrence.occurrence_id)}/plan-revisions/${revisionNo}` },
      () => cachedGet(planCache.current, `${occurrence.occurrence_id}:${revisionNo}`, (etag) => teacherOccurrenceApi.getPlan(occurrence.occurrence_id, revisionNo, etag)),
    );
    setSelectedPlan(plan);
  });

  const confirmPlan = () => runAction(async () => {
    if (!occurrence || !selectedPlan || !currentHeadPlan || selectedPlan.revision_no !== currentHeadPlan.revision_no || selectedPlan.state !== "DRAFT") throw new Error("Chỉ có thể xác nhận bản nháp mới nhất.");
    const input = { occurrence_id: occurrence.occurrence_id, revision_no: selectedPlan.revision_no, expected_plan_hash: selectedPlan.content_hash };
    const confirmed = await keyedWrite(confirmPlanIdentity, input, (key) => teacherOccurrenceApi.confirmPlan(input.occurrence_id, input.revision_no, input.expected_plan_hash, key));
    planCache.current.clear();
    setSelectedPlan(confirmed); setNotice("Đã xác nhận bản kế hoạch.");
    await refreshDocumentsAndPlans(occurrence.occurrence_id);
    await refreshOccurrence(occurrence.occurrence_id);
  });

  const refreshAll = () => runAction(async () => {
    await refreshClasses();
    const currentClassId = classIdRef.current;
    const currentOccurrenceId = occurrenceIdRef.current;
    if (currentClassId) await refreshOccurrences(currentClassId);
    if (currentOccurrenceId) { await refreshDocumentsAndPlans(currentOccurrenceId); await refreshOccurrence(currentOccurrenceId); }
  });

  return (
    <div className="s2l-page s2l-data-page teacher-occurrence-page">
      <PageHeading
        eyebrow="Giáo viên · Buổi dạy"
        title="Buổi dạy"
        description="Tạo buổi dạy trong lớp được phân công, rà soát tài liệu và quản lý các bản kế hoạch."
        action={<button type="button" className="s2l-button" onClick={() => void refreshAll()} disabled={busy}><RefreshCw size={16} aria-hidden="true" />Làm mới</button>}
      />
      {error && !(diagnostic?.method === "POST" && diagnostic.path === "/v1/lesson-occurrences") && <div className="s2l-alert teacher-occurrence-error" role="alert">
        {diagnostic && <p className="teacher-occurrence-error-context"><strong>Bước lỗi:</strong> {diagnostic.step}</p>}
        <p className="teacher-occurrence-error-message">{error}</p>
        {diagnostic && <details className="teacher-occurrence-error-details">
          <summary>Thông tin kỹ thuật</summary>
          <dl>
            <dt>Phương thức</dt><dd>{diagnostic.method}</dd>
            <dt>Đường dẫn</dt><dd><code>{diagnostic.path}</code></dd>
            <dt>Trạng thái</dt><dd>{diagnostic.status}</dd>
            <dt>Mã lỗi</dt><dd>{diagnostic.code}</dd>
            <dt>Mã yêu cầu</dt><dd>{diagnostic.requestId}</dd>
          </dl>
        </details>}
      </div>}
      {unmappedIssues.length > 0 && <ul className="s2l-alert" aria-label="Trường chưa hợp lệ">{unmappedIssues.map((issue) => <li key={`${issue.field}:${issue.code}`}>{fieldIssueText(issue)}</li>)}</ul>}
      {notice && <div className="s2l-note" role="status">{notice}</div>}
      {!hasFirebaseAuthBridge() && <div className="s2l-alert" role="alert">Chưa có phiên đăng nhập giáo viên.</div>}
      {loading ? <p className="s2l-data-card" role="status">Đang tải lớp và giáo án được cấp quyền…</p> : (
        <div className="teacher-occurrence-layout">
          <div className="teacher-occurrence-top">
            <section className="s2l-data-card teacher-occurrence-sidebar" aria-label="Danh sách buổi dạy">
              <FormField label="Lớp được phân công" htmlFor="occurrence-class">
                <Select id="occurrence-class" value={selectedClassId} disabled={busy} onChange={(event) => {
                  const nextClassId = event.target.value;
                  if (nextClassId === selectedClassId) return;
                  classIdRef.current = nextClassId;
                  occurrenceIdRef.current = "";
                  setSelectedClassId(nextClassId);
                  setOccurrence(null);
                  setOccurrences([]);
                  setNextCursor(null);
                }}>
                  <option value="">Chọn lớp</option>{classes.map((item) => <option key={item.class_id} value={item.class_id}>{item.display_name}</option>)}
                </Select>
              </FormField>
              {classes.length === 0 && <p className="s2l-note">Tài khoản chưa có lớp được phân công.</p>}
              <h2>Buổi dạy gần đây</h2>
              {occurrences.length === 0 ? <p className="s2l-note">Chưa có buổi dạy trong lớp này.</p> : <ul className="teacher-occurrence-list">{occurrences.map((item) => <li key={item.occurrence_id}><button type="button" disabled={busy} aria-current={item.occurrence_id === occurrenceId ? "true" : undefined} onClick={() => void selectOccurrence(item)}><strong>{item.title}</strong><small>{item.scheduled_date ? formatDateDdMmYyyy(item.scheduled_date) : "Chưa đặt ngày"} · {OCCURRENCE_STATE_LABEL[item.state]}</small></button></li>)}</ul>}
              {nextCursor && <Button type="button" variant="secondary" disabled={busy} onClick={() => void runAction(() => refreshOccurrences(selectedClassId, nextCursor))}>Tải thêm buổi dạy</Button>}
            </section>

            <form onSubmit={(event) => { event.preventDefault(); void createOccurrence(); }} className="s2l-data-card cozy-form-card cozy-form-card--wide teacher-occurrence-create cozy-form-stack">
              <div className="tp-form-column">
                <h2><CalendarDays size={18} aria-hidden="true" /> Tạo buổi dạy</h2>
                <div className="cozy-form-grid">
                  <FormField className="cozy-span-6" label="Tên buổi dạy" htmlFor="occurrence-title" required help="Tên ngắn giúp dễ nhận biết buổi học." error={issueFor("title")}>
                    <input id="occurrence-title" className="cozy-input" value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={200} placeholder="Ví dụ: Buổi vẽ lá cây" />
                  </FormField>
                  <FormField className="cozy-span-3" label="Ngày dự kiến" htmlFor="occurrence-date" labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>} error={issueFor("scheduled_date")}>
                    <DateField id="occurrence-date" type="date" value={scheduledDate} onChange={(event) => setScheduledDate(event.target.value)} />
                  </FormField>
                  <FormField className="cozy-span-3" label="Ghim giáo án đã duyệt" htmlFor="occurrence-lesson" labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>} error={issueFor("lesson_version_ref")}>
                    <Select id="occurrence-lesson" value={selectedLessonId} onChange={(event) => setSelectedLessonId(event.target.value)}>
                      <option value="">Không ghim giáo án</option>{lessons.map((item) => <option key={item.lesson_id} value={item.lesson_id}>{item.title}</option>)}
                    </Select>
                  </FormField>
                </div>
                {lessonLabel && <p className="s2l-note">Đã chọn: {lessonLabel}. Buổi dạy giữ đúng phiên bản hiện tại của giáo án.</p>}
                {error && diagnostic?.method === "POST" && diagnostic.path === "/v1/lesson-occurrences" && (
                  <div className="s2l-alert" role="alert">{error}</div>
                )}
                <FormActionBar hint={!busy && (!selectedClassId || !title.trim()) ? "Nhập tên buổi dạy để bật nút tạo buổi." : undefined}>
                  <Button type="submit" variant="primary" loading={busy} disabled={busy || !selectedClassId || !title.trim()} className="teacher-occurrence-submit">Tạo buổi dạy</Button>
                </FormActionBar>
              </div>
            </form>
          </div>

          {occurrence ? <div className="teacher-occurrence-main">
            <section className="s2l-data-card" aria-label="Chi tiết buổi dạy">
              <div className="teacher-occurrence-heading">
                <div>
                  <p className="teacher-occurrence-eyebrow">{selectedClass?.display_name ?? "Lớp"}</p>
                  <h2>{occurrence.title}</h2>
                </div>
                <div className="tp-chip-row">
                  <StatusBadge tone={teacherStatusMeta(occurrence.state, "session").tone} dot>{OCCURRENCE_STATE_LABEL[occurrence.state]}</StatusBadge>
                  <span className="tp-value-chip">{occurrence.scheduled_date ? formatDateDdMmYyyy(occurrence.scheduled_date) : "Chưa đặt ngày"}</span>
                </div>
              </div>
              {occurrence.lesson_version_ref && <p className="s2l-note">Đã ghim giáo án {lessons.find((item) => item.lesson_id === occurrence.lesson_version_ref?.lesson_id)?.title ?? "đã chọn"} · Phiên bản {occurrence.lesson_version_no}</p>}
              {occurrence.approved_plan && <p className="s2l-note">Kế hoạch đã xác nhận: Phiên bản {occurrence.approved_plan.revision_no}</p>}
              <div className="tp-actions">
                <Link className="s2l-button" to={`/teacher/t02-presentation?occurrence=${encodeURIComponent(occurrence.occurrence_id)}`}>Chỉnh sửa và trình bày slide</Link>
                {entryLinks(occurrence).sample && <Link className="s2l-button" to={`/teacher/t06-sample-story-run?occurrence=${encodeURIComponent(occurrence.occurrence_id)}`}>Video mẫu</Link>}
                {entryLinks(occurrence).projection && <Link className="s2l-button is-primary" to={`/teacher/t07-video-presentation-confirmation?occurrence=${encodeURIComponent(occurrence.occurrence_id)}`}>Chiếu cho lớp</Link>}
              </div>
              <nav className="teacher-occurrence-steps" aria-label="Các bước chuẩn bị buổi dạy">
                <span>Đi tới:</span>
                {OCCURRENCE_STEPS.map((step, index) => <button key={step.id} type="button" onClick={() => document.getElementById(step.id)?.scrollIntoView?.({ behavior: "smooth", block: "start" })}>
                  <b aria-hidden="true">{index + 1}</b>{step.label}
                </button>)}
              </nav>
            </section>

            <TeacherSketchDeckPanel
              key={`${occurrence.occurrence_id}:${occurrence.approved_plan?.revision_no ?? "none"}`}
              occurrenceId={occurrence.occurrence_id}
              approvedRevisionNo={occurrence.approved_plan?.revision_no ?? null}
            />

            <section id="teacher-occurrence-documents" className="s2l-data-card" aria-label="Tài liệu của buổi dạy">
              <p className="teacher-occurrence-eyebrow teacher-occurrence-step-label">Bước 1 · Chuẩn bị tài liệu</p>
              <div className="teacher-occurrence-section-title"><h2><FileText size={18} aria-hidden="true" /> Tài liệu và văn bản trích xuất</h2></div>
              <form onSubmit={(event) => { event.preventDefault(); void uploadAndAttach(); }} className="teacher-occurrence-upload cozy-form-stack">
                <div className="teacher-file-field">
                  <span id="occurrence-file-label" className="cozy-form-label">
                    Tải PDF, DOCX hoặc PPTX{" "}
                    <span className="cozy-form-required" aria-hidden="true">*</span>
                  </span>
                  <label className="teacher-file-picker" htmlFor="occurrence-file">
                    <span className="teacher-file-picker-button"><Upload size={16} aria-hidden="true" /> Chọn tệp</span>
                    <span className="teacher-file-picker-name">{file?.name ?? "Chưa chọn tệp"}</span>
                    <input key={occurrenceId} id="occurrence-file" className="teacher-file-picker-input" type="file" accept=".pdf,.docx,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation" aria-labelledby="occurrence-file-label" aria-required="true" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
                  </label>
                  <p className="cozy-form-hint">Dung lượng tối đa 25 MB.</p>
                </div>
                {uploadProgress && <span role="status">Đang tải: {uploadProgress}</span>}
                <FormActionBar hint={!busy && !file ? "Chọn tệp ở trên để bật nút tải và đính kèm." : undefined}>
                  {uploadAbortable && busy && <Button type="button" variant="secondary" onClick={stopUpload}>Dừng tải lên</Button>}
                  {uploadAbortable && !busy && <Button type="button" variant="secondary" onClick={() => void abortUpload()}>Hủy phiên tải lên</Button>}
                  <Button type="submit" variant="primary" loading={busy} disabled={busy || !file} iconLeft={<Upload size={16} aria-hidden="true" />}>Tải và đính kèm</Button>
                </FormActionBar>
              </form>
              {job && <p className="s2l-note" role="status">Xử lý tài liệu: {JOB_STATE_LABEL[job.state]}{job.progress.kind === "percentage" && job.progress.value !== null ? ` · ${Math.round(job.progress.value)}%` : ""}{job.failure?.public_message ? ` · ${job.failure.public_message}` : ""}</p>}
              {documents.length === 0 ? <p className="s2l-note">Chưa có tài liệu đính kèm.</p> : <div className="teacher-occurrence-document-grid">
                <ul className="teacher-occurrence-list" aria-label="Tài liệu của buổi dạy">{documents.map((item) => <li key={item.source_document_id}><button type="button" aria-current={item.source_document_id === selectedDocumentId ? "true" : undefined} onClick={() => setSelectedDocumentId(item.source_document_id)}><strong>{item.file_name}</strong><small>{item.file_extension} · {item.page_or_slide_count ?? "Không rõ số trang"} · Phiên bản {item.head_revision_no}</small></button></li>)}</ul>
                {selectedDocument && <div className="teacher-occurrence-revisions cozy-form-stack">
                  <p><strong>{selectedDocument.file_name}</strong> · {DOCUMENT_STATE_LABEL[selectedDocument.document_state]}</p>
                  {selectedDocument.warnings.length > 0 && <ul className="s2l-note">{selectedDocument.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
                  <FormField label="Lịch sử văn bản" htmlFor="document-revision">
                    <Select id="document-revision" value={selectedRevision?.revision_no ?? selectedDocument.head_revision_no} onChange={(event) => void openRevision(Number(event.target.value))}>
                      {revisions.map((revision) => <option key={revision.revision_no} value={revision.revision_no}>Phiên bản {revision.revision_no} · {revision.origin === "EXTRACTION" ? "trích xuất" : "chỉnh sửa"} · {revision.review_state === "NEEDS_REVIEW" ? "cần rà soát" : "đã xác nhận"}</option>)}
                    </Select>
                  </FormField>
                  <FormField label={`Văn bản của phiên bản ${selectedRevision?.revision_no ?? selectedDocument.head_revision_no}`} htmlFor="document-text" required error={issueFor("extracted_text")} help="Lưu sẽ tạo bản mới bất biến; chỉ bản mới nhất có thể được chỉnh sửa tiếp.">
                    <textarea id="document-text" className="cozy-textarea" value={editedText} onChange={(event) => setEditedText(event.target.value)} rows={3} />
                  </FormField>
                  <FormActionBar
                    hint={!busy && (!selectedRevision || selectedRevision.revision_no !== selectedDocument.head_revision_no)
                      ? "Chỉ chỉnh sửa được bản mới nhất của tài liệu."
                      : !busy && selectedRevision && selectedRevision.revision_no === selectedDocument.head_revision_no && !editedText.trim()
                        ? "Nhập nội dung văn bản để bật nút lưu."
                        : undefined}
                  >
                    <Button type="button" variant="primary" loading={busy} onClick={() => void saveEditedText()} disabled={busy || !selectedRevision || selectedRevision.revision_no !== selectedDocument.head_revision_no || !editedText.trim()}>Lưu thành bản mới</Button>
                  </FormActionBar>
                </div>}
              </div>}
            </section>

            <section id="teacher-occurrence-plan" className="s2l-data-card" aria-label="Kế hoạch buổi dạy">
              <p className="teacher-occurrence-eyebrow teacher-occurrence-step-label">Bước 2 · Lập và xác nhận kế hoạch</p>
              <div className="teacher-occurrence-section-title"><h2><ClipboardList size={18} aria-hidden="true" /> Kế hoạch buổi dạy</h2></div>
              <div className="teacher-occurrence-plan-layout">
                <div>
                  <h3>Các bản kế hoạch</h3>
                  {plans.length === 0 ? <p className="s2l-note">Chưa có kế hoạch. Bản đầu tiên sẽ là bản nháp.</p> : <ul className="teacher-occurrence-list">{plans.map((plan) => <li key={plan.revision_no}><button type="button" aria-current={plan.revision_no === selectedPlan?.revision_no ? "true" : undefined} onClick={() => void openPlan(plan.revision_no)}><strong>Phiên bản {plan.revision_no} · {PLAN_STATE_LABEL[plan.state]}</strong><small>{plan.activity_count} hoạt động · {formatDateTimeDdMmYyyy(plan.created_at)}</small></button></li>)}</ul>}
                  {selectedPlan && <div className="teacher-occurrence-plan-detail">
                    <div className="tw-row tw-between tw-wrap">
                      <h3>Phiên bản {selectedPlan.revision_no} · {PLAN_STATE_LABEL[selectedPlan.state]}</h3>
                      <StatusBadge tone={teacherStatusMeta(selectedPlan.state, "plan").tone} size="sm" dot>{PLAN_STATE_LABEL[selectedPlan.state]}</StatusBadge>
                    </div>
                    <p>{selectedPlan.objectives.join(" · ")}</p><p>{selectedPlan.teacher_direction}</p>{selectedPlan.safety_notes && <p>{selectedPlan.safety_notes}</p>}
                    {selectedPlan.activities.length > 0 && <ul className="s2l-note">{selectedPlan.activities.map((activity) => <li key={activity.order}>{activity.order}. {activity.title ?? "Hoạt động của giáo án"}</li>)}</ul>}
                    {checklistBlocked && <p className="s2l-note">Bản này có hoạt động cần danh mục kiểm tra an toàn nhưng danh mục chưa được cấu hình, nên chưa thể xác nhận.</p>}
                    <FormActionBar hint={!busy && !checklistBlocked && (selectedPlan.state !== "DRAFT" || selectedPlan.revision_no !== currentHeadPlan?.revision_no) ? "Chỉ xác nhận được bản nháp mới nhất." : undefined}>
                      <Button type="button" variant="secondary" onClick={() => editPlan(selectedPlan)}>Tạo bản mới từ bản này</Button>
                      <Button type="button" variant="primary" loading={busy} onClick={() => void confirmPlan()} disabled={busy || checklistBlocked || selectedPlan.state !== "DRAFT" || selectedPlan.revision_no !== currentHeadPlan?.revision_no}>Xác nhận bản nháp mới nhất</Button>
                    </FormActionBar>
                  </div>}
                </div>
                <form onSubmit={(event) => { event.preventDefault(); void savePlan(); }} className="teacher-occurrence-plan-form cozy-form-stack">
                  <h3>{selectedPlan ? "Tạo bản kế hoạch tiếp theo" : "Tạo bản kế hoạch"}</h3>
                  <div className="cozy-form-grid">
                    <FormField
                      className="cozy-span-6"
                      label="Mục tiêu học tập"
                      htmlFor="plan-objectives"
                      required
                      help={`Mỗi dòng một mục tiêu. Tối đa ${PLAN_LIMITS.objectives} mục, mỗi mục tối đa ${PLAN_LIMITS.objectiveChars} ký tự.`}
                      error={issueFor("objectives") ?? (objectivesProblem || undefined)}
                    >
                      <textarea id="plan-objectives" className="cozy-textarea" value={objectives} onChange={(event) => setObjectives(event.target.value)} rows={3} required />
                    </FormField>
                    <FormField
                      className="cozy-span-6"
                      label="Hướng dẫn cho giáo viên"
                      htmlFor="plan-direction"
                      required
                      help={`Tối đa ${PLAN_LIMITS.directionChars} ký tự.`}
                      error={issueFor("teacher_direction") ?? (directionProblem || undefined)}
                    >
                      <textarea id="plan-direction" className="cozy-textarea" maxLength={PLAN_LIMITS.directionChars} value={direction} onChange={(event) => setDirection(event.target.value)} rows={3} required />
                    </FormField>
                    <FormField
                      className="cozy-span-6"
                      label="Ghi chú an toàn"
                      htmlFor="plan-safety"
                      labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}
                      help={`Tối đa ${PLAN_LIMITS.safetyNotesChars} ký tự.`}
                      error={issueFor("safety_notes") ?? (safetyProblem || undefined)}
                    >
                      <textarea id="plan-safety" className="cozy-textarea" maxLength={PLAN_LIMITS.safetyNotesChars} value={safetyNotes} onChange={(event) => setSafetyNotes(event.target.value)} rows={3} />
                    </FormField>
                    <FormField
                      className="cozy-span-6"
                      label="Bản văn bản làm nguồn"
                      htmlFor="plan-document-revision"
                      labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}
                      error={issueFor("document_revision_ref")}
                    >
                      <Select id="plan-document-revision" value={planDocumentRevision} onChange={(event) => setPlanDocumentRevision(event.target.value)}>
                        <option value="">Không chọn nguồn văn bản</option>
                        {selectedDocument && revisions.map((revision) => <option key={revision.revision_no} value={`${selectedDocument.source_document_id}:${revision.revision_no}`}>{selectedDocument.file_name} · Phiên bản {revision.revision_no}</option>)}
                      </Select>
                    </FormField>
                  </div>
                  {occurrence.lesson_version_ref && <PlanActivityPicker
                    key={`${occurrence.occurrence_id}:${organizationId}:${occurrence.lesson_version_ref.lesson_id}:${occurrence.lesson_version_ref.version_id}`}
                    organizationId={organizationId}
                    lessonVersionRef={occurrence.lesson_version_ref}
                    selection={carriedActivities}
                    onSelectionChange={setCarriedActivities}
                    copiedFromPlan={copiedActivitiesFromPlan}
                    disabled={busy}
                  />}
                  <p className="s2l-note">Kế hoạch mới được lưu thành bản nháp riêng.</p>
                  <FormActionBar hint={!busy && (planProblems.length > 0 || objectiveLines.length === 0 || !direction.trim()) ? "Nhập mục tiêu học tập và hướng dẫn cho giáo viên hợp lệ để bật nút lưu." : undefined}>
                    <Button type="submit" variant="primary" loading={busy} disabled={busy || planProblems.length > 0 || objectiveLines.length === 0 || !direction.trim()}>Lưu bản kế hoạch</Button>
                  </FormActionBar>
                </form>
              </div>
            </section>
          </div> : <section className="s2l-data-card teacher-occurrence-empty"><h2>Chọn buổi dạy</h2><p>Chọn một buổi dạy trong lớp hoặc tạo buổi mới để quản lý tài liệu và kế hoạch.</p></section>}
        </div>
      )}
    </div>
  );
}
