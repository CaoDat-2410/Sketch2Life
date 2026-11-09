import React, { createContext, useContext, useEffect, useState } from "react";
import { isLocalPreview } from "../../../shared/backendApi";
import {
  ClassRosterRow,
  INITIAL_ASSIGNED_CLASSES,
  INITIAL_ORG_QUOTA_LEDGER,
  INITIAL_PRESENTATION_AUDIT,
  INITIAL_ROSTER,
  INITIAL_SAMPLE_SCENES,
  INITIAL_TEACHER_FEEDBACK,
  INITIAL_TEACHER_GRANTS,
  INITIAL_TEACHER_LESSONS,
  INITIAL_TEACHER_NOTIFICATIONS,
  OrgQuotaLedgerItem,
  PresentationAuditEntry,
  PUBLIC_LIBRARY_TEMPLATES,
  SampleSceneItem,
  TeacherAssignedClassInfo,
  TeacherFeedbackItem,
  TeacherGrantRow,
  TeacherLessonCard,
  TeacherNotificationItem,
} from "../data/mockTeacherData";

export type WebTheme = "light" | "dark";

export interface LessonMutationInput {
  title: string;
  topic: string;
  ageBand: string;
  visibility: TeacherLessonCard["visibility"];
  description: string;
  objectives: string;
  activities: string[];
  approvedForSession?: boolean;
  remixedFrom?: string;
}

export type ImportErrorMode = "NONE" | "TOO_LARGE" | "TOO_MANY_PAGES" | "SCANNED_PDF" | "PASSWORD_PROTECTED";
export type TeacherUi05Mode = "NORMAL" | "LOADING" | "EMPTY" | "STALE_409" | "FORBIDDEN_403";
export type OccurrenceStatus =
  | "DRAFT"
  | "DOCUMENT_REVIEW"
  | "PLAN_REVIEW"
  | "APPROVED"
  | "SAMPLE_AVAILABLE"
  | "SAMPLE_USED";
export type SketchDeckJobStatus = "NOT_REQUESTED" | "GENERATING" | "READY" | "FAILED" | "STALE";
export type SampleVideoJobStatus =
  | "ADMISSION_PENDING"
  | "GENERATING"
  | "VIDEO_READY"
  | "SAFETY_BLOCKED"
  | "FAILED"
  | "DELETE_PENDING"
  | "DELETED"
  | "COMPLETED";

export type WebPortalRole = "TEACHER" | "MANAGER" | "ADMIN";

const WEB_ROLE_STORAGE_KEY = "s2l-web-role";
const WEB_AUTH_STORAGE_KEY = "s2l-web-authenticated";

function isWebPortalRole(value: string | null): value is WebPortalRole {
  return value === "TEACHER" || value === "MANAGER" || value === "ADMIN";
}

function readStoredWebRole(): WebPortalRole {
  if (typeof window === "undefined") return "TEACHER";
  const role = window.sessionStorage.getItem(WEB_ROLE_STORAGE_KEY);
  return isWebPortalRole(role) ? role : "TEACHER";
}

interface TeacherContextValue {
  // Theme (Light / Dark Mode)
  theme: WebTheme;
  setTheme: (t: WebTheme) => void;
  toggleTheme: () => void;

  // Web Portal Role & Auth
  currentRole: WebPortalRole;
  loginAsRole: (r: WebPortalRole, email?: string) => void;
  logout: () => void;

  // Group 1 & 2: Auth, RBAC, School/Class Capacity & Reassignment Saga
  isAuthenticated: boolean;
  accountActivationState: "ACTIVATED" | "PENDING_INVITE" | "ACCOUNT_SETUP_UNAVAILABLE";
  setAccountActivationState: (s: "ACTIVATED" | "PENDING_INVITE" | "ACCOUNT_SETUP_UNAVAILABLE") => void;
  assignedClasses: TeacherAssignedClassInfo[];
  activeClassId: string;
  setActiveClassId: (id: string) => void;
  baseClassSlots: number;
  addonClassSlots: number;
  usedClassSlots: number;
  graceDaysRemaining: number;
  forceCloseConflictAndCompleteTransfer: (classId: string, reason: string) => void;
  purchaseAddonClassSlot: () => void;

  // Group 5: Lesson Library, Full CRUD, Remix, Versioning, Public Review
  lessons: TeacherLessonCard[];
  publicTemplates: TeacherLessonCard[];
  createLesson: (input: LessonMutationInput) => TeacherLessonCard;
  updateLesson: (id: string, patch: Partial<LessonMutationInput>) => void;
  deleteLesson: (id: string) => void;
  approveLessonForSession: (id: string) => void;
  archiveLesson: (id: string) => void;
  restoreDefaultLessons: () => void;
  remixLesson: (id: string) => void;
  createNewLessonVersion: (id: string) => void;
  useLessonForOccurrence: (id: string) => void;
  ui05Mode: TeacherUi05Mode;
  setUi05Mode: (m: TeacherUi05Mode) => void;

  // Group 3: Roster (36–155 months), Edit, Class Transfer, Profile Deletion
  roster: ClassRosterRow[];
  addRosterChild: (
    label: string,
    ageMonths: number,
    interests?: string[],
    learningNotes?: string,
    supportNeedsNote?: string,
    targetClassName?: string
  ) => void;
  updateRosterChild: (
    childId: string,
    patch: {
      label: string;
      ageMonths: number;
      interests: string[];
      learningNotes: string;
      supportNeedsNote: string;
    }
  ) => void;
  transferChildClass: (childId: string, targetClassName: string) => void;
  deleteRosterChildLifecycle: (childId: string) => void;

  // Group 6: Document Upload, Provenance & Revision
  importErrorMode: ImportErrorMode;
  setImportErrorMode: (m: ImportErrorMode) => void;
  uploadedFileName: string;
  uploadedFileSizeMb: string;
  uploadedSha256: string;
  documentRevision: number;
  handleRealDocumentUpload: (fileName: string, sizeBytes: number) => void;
  approveExtractedDocumentRevision: () => void;

  // Group 7 & 8: Occurrence, Pinned Plan & Safety Checklist, Opt-In Sketch Deck & Stale Deck
  occurrenceId: string;
  occurrenceStatus: OccurrenceStatus;
  setOccurrenceStatus: (s: OccurrenceStatus) => void;
  pinnedLessonTitle: string;
  setPinnedLessonTitle: (t: string) => void;
  pinnedPlanRevision: number;
  pinnedPlanHash: string;
  pinnedActivities: string[];
  setPinnedActivities: (acts: string[]) => void;
  safetyChecklistConfirmed: boolean;
  setSafetyChecklistConfirmed: (v: boolean) => void;
  approveOccurrencePlan: () => void;
  simulatePlanChangeStaleDeck: () => void;
  sketchDeckEnabled: boolean;
  setSketchDeckEnabled: (v: boolean) => void;
  deckJobStatus: SketchDeckJobStatus;
  setDeckJobStatus: (s: SketchDeckJobStatus) => void;
  activeDeckStep: number;
  setActiveDeckStep: (n: number) => void;
  skippedSteps: number[];
  toggleSkipDeckStep: (step: number) => void;
  deckRevision: number;
  regenerateDeckStep: () => void;

  // Group 9: Sample Story Run (Eligible child, Artwork, Voice/Whisper, Minimal Context, Storyboard)
  selectedSampleChildId: string;
  setSelectedSampleChildId: (id: string) => void;
  selectedSampleActivity: string;
  setSelectedSampleActivity: (act: string) => void;
  sampleArtworkName: string;
  setSampleArtworkName: (name: string) => void;
  sampleDetectedSubject: string;
  setSampleDetectedSubject: (sub: string) => void;
  sampleSubjectRevision: number;
  sampleAudioDurationSec: number;
  sampleAudioSizeMb: number;
  sampleRawTranscript: string;
  sampleEditedTranscript: string;
  setSampleEditedTranscript: (v: string) => void;
  sampleTranscriptConfirmed: boolean;
  confirmSampleTranscript: () => void;
  sampleContextConfirmed: boolean;
  confirmSampleContextSnapshot: () => void;
  followLessonDirection: boolean;
  setFollowLessonDirection: (v: boolean) => void;
  sampleScenes: SampleSceneItem[];
  sampleScriptRevision: number;
  sampleScriptHash: string;
  sampleRewriteCount: number;
  sampleRewriteHint: string;
  setSampleRewriteHint: (v: string) => void;
  requestSampleRewrite: () => void;
  sampleVideoConfirmed: boolean;
  confirmSampleScript: () => void;

  // Group 10: Video Job, Sample Slot rule, Org Quota, Playback Token & Audit, Complete/Cancel/Delete, Live Notifications & Feedback
  sampleVideoJobStatus: SampleVideoJobStatus;
  setSampleVideoJobStatus: (s: SampleVideoJobStatus) => void;
  sampleRegenCount: number;
  markSampleVideoUnsuitable: (reason: string) => boolean;
  completeSampleRun: () => void;
  cancelOrDeleteSampleRun: () => void;
  orgIncludedQuota: number;
  orgTopupQuota: number;
  orgQuotaLedger: OrgQuotaLedgerItem[];
  presentationConfirmed: boolean;
  playbackTokenIssued: string | null;
  presentationAuditLog: PresentationAuditEntry[];
  confirmClassroomPresentation: () => void;
  captionsOn: boolean;
  setCaptionsOn: (v: boolean) => void;

  // Group 4: Grants & Consent
  grants: TeacherGrantRow[];
  revokeTeacherGrant: (id: string) => void;
  addLessonGrant: (recipient: string, scope: string, expiresAt?: string) => void;
  requestParentProfileGrant: (childLabel: string) => void;
  simulateParentAcceptGrant: (id: string) => void;

  // Feedback & Notifications
  feedbackThread: TeacherFeedbackItem[];
  replyToFeedback: (text: string) => void;
  teacherNotifications: TeacherNotificationItem[];
  markTeacherNotifRead: (id: string) => void;
  markAllTeacherNotifsRead: () => void;

  archiveModalTarget: TeacherLessonCard | null;
  setArchiveModalTarget: (l: TeacherLessonCard | null) => void;
  toast: { kind: "ok" | "info" | "warn" | "err"; text: string } | null;
  showToast: (text: string, kind?: "ok" | "info" | "warn" | "err") => void;
}

const TeacherContext = createContext<TeacherContextValue | null>(null);

export function TeacherProvider({ children }: { children: React.ReactNode }) {
  // Theme State (Light / Dark Mode)
  const [theme, setThemeState] = useState<WebTheme>(() => {
    if (typeof window !== "undefined") {
      const saved = window.localStorage.getItem("s2l-web-theme");
      if (saved === "dark" || saved === "light") return saved;
    }
    return "light";
  });

  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.dataset.theme = theme;
    }
    if (typeof window !== "undefined") {
      window.localStorage.setItem("s2l-web-theme", theme);
    }
  }, [theme]);

  const setTheme = (nextTheme: WebTheme) => {
    setThemeState(nextTheme);
  };

  const toggleTheme = () => {
    setThemeState((prev) => (prev === "dark" ? "light" : "dark"));
  };

  // Web Portal Role & Auth State
  const [currentRole, setCurrentRole] = useState<WebPortalRole>(readStoredWebRole);
  const [isAuthenticated, setIsAuthenticated] = useState(() =>
    typeof window !== "undefined" &&
    isWebPortalRole(window.sessionStorage.getItem(WEB_ROLE_STORAGE_KEY)) &&
    window.sessionStorage.getItem(WEB_AUTH_STORAGE_KEY) === "true"
  );

  const loginAsRole = (role: WebPortalRole, _email?: string) => {
    setCurrentRole(role);
    setIsAuthenticated(true);
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(WEB_ROLE_STORAGE_KEY, role);
      window.sessionStorage.setItem(WEB_AUTH_STORAGE_KEY, "true");
    }
    setAccountActivationState("ACTIVATED");
    const roleName = role === "TEACHER" ? "Giáo viên" : role === "MANAGER" ? "Quản lý trường" : "Quản trị nền tảng";
    showToast(`Đăng nhập thành công với vai trò ${roleName}.`, "ok");
  };

  const logout = () => {
    setIsAuthenticated(false);
    if (typeof window !== "undefined") {
      const firebaseSignOut = window.sketch2lifeAuth?.signOut;
      if (firebaseSignOut) void firebaseSignOut().catch(() => undefined);
    }
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(WEB_ROLE_STORAGE_KEY);
      window.sessionStorage.removeItem(WEB_AUTH_STORAGE_KEY);
    }
    showToast("Đã đăng xuất khỏi Hệ thống Web Sketch2Life.", "info");
  };

  // Group 1 & 2
  const [accountActivationState, setAccountActivationState] = useState<
    "ACTIVATED" | "PENDING_INVITE" | "ACCOUNT_SETUP_UNAVAILABLE"
  >("ACTIVATED");
  const [assignedClasses, setAssignedClasses] = useState<TeacherAssignedClassInfo[]>(
    INITIAL_ASSIGNED_CLASSES
  );
  const [activeClassId, setActiveClassId] = useState("cls-mam-2");
  const [baseClassSlots] = useState(10);
  const [addonClassSlots, setAddonClassSlots] = useState(2);
  const [usedClassSlots] = useState(9);
  const [graceDaysRemaining] = useState(7);

  // Group 5
  const [lessons, setLessons] = useState<TeacherLessonCard[]>(INITIAL_TEACHER_LESSONS);
  const [publicTemplates] = useState<TeacherLessonCard[]>(PUBLIC_LIBRARY_TEMPLATES);
  const [ui05Mode, setUi05Mode] = useState<TeacherUi05Mode>("NORMAL");

  // Group 3
  const [roster, setRoster] = useState<ClassRosterRow[]>(INITIAL_ROSTER);

  // Group 6
  const [importErrorMode, setImportErrorMode] = useState<ImportErrorMode>("NONE");
  const [uploadedFileName, setUploadedFileName] = useState("Giao_an_vong_doi_buom.docx");
  const [uploadedFileSizeMb, setUploadedFileSizeMb] = useState("2,4 MB");
  const [uploadedSha256, setUploadedSha256] = useState("sha256:7d8f44a2...91b0");
  const [documentRevision, setDocumentRevision] = useState(1);

  // Group 7 & 8
  const [occurrenceId] = useState("occ-20261030-mam2");
  const [occurrenceStatus, setOccurrenceStatus] = useState<OccurrenceStatus>("APPROVED");
  const [pinnedLessonTitle, setPinnedLessonTitle] = useState("Vòng đời bướm");
  const [pinnedPlanRevision, setPinnedPlanRevision] = useState(3);
  const [pinnedPlanHash, setPinnedPlanHash] = useState("sha256:4a9c11...e08b");
  const [pinnedActivities, setPinnedActivities] = useState<string[]>(
    INITIAL_TEACHER_LESSONS[0]?.activities ?? [
      "Quan sát vòng đời bướm ngoài vườn trường",
      "Đôi cánh bướm mùa xuân (Sân cỏ)",
    ]
  );
  const [safetyChecklistConfirmed, setSafetyChecklistConfirmed] = useState(true);
  const [sketchDeckEnabled, setSketchDeckEnabled] = useState(true);
  const [deckJobStatus, setDeckJobStatus] = useState<SketchDeckJobStatus>("READY");
  const [activeDeckStep, setActiveDeckStep] = useState(1);
  const [skippedSteps, setSkippedSteps] = useState<number[]>([]);
  const [deckRevision, setDeckRevision] = useState(1);

  // Group 9
  const [selectedSampleChildId, setSelectedSampleChildId] = useState("roster-minh");
  const [selectedSampleActivity, setSelectedSampleActivity] = useState(
    "Quan sát vòng đời bướm ngoài vườn trường"
  );
  const [sampleArtworkName, setSampleArtworkName] = useState("tranh-buom-minh-a4.png");
  const [sampleDetectedSubject, setSampleDetectedSubjectState] = useState("Con bướm");
  const [sampleSubjectRevision, setSampleSubjectRevision] = useState(1);
  const [sampleAudioDurationSec] = useState(22);
  const [sampleAudioSizeMb] = useState(1.4);
  const [sampleRawTranscript] = useState("chú sâu ăn lá xanh rồi hóa thành bướm bay quanh sân trường");
  const [sampleEditedTranscript, setSampleEditedTranscript] = useState(
    "Chú sâu ăn lá xanh rồi hóa thành bướm bay quanh sân trường."
  );
  const [sampleTranscriptConfirmed, setSampleTranscriptConfirmed] = useState(true);
  const [sampleContextConfirmed, setSampleContextConfirmed] = useState(true);
  const [followLessonDirection, setFollowLessonDirection] = useState(true);
  const [sampleScenes, setSampleScenes] = useState<SampleSceneItem[]>(INITIAL_SAMPLE_SCENES);
  const [sampleScriptRevision, setSampleScriptRevision] = useState(1);
  const [sampleScriptHash, setSampleScriptHash] = useState("sha256:5e21a0...c409");
  const [sampleRewriteCount, setSampleRewriteCount] = useState(0);
  const [sampleRewriteHint, setSampleRewriteHint] = useState("Nhấn mạnh bước sâu hóa nhộng trên cành lá");
  const [sampleVideoConfirmed, setSampleVideoConfirmed] = useState(false);

  // Group 10
  const [sampleVideoJobStatus, setSampleVideoJobStatusState] =
    useState<SampleVideoJobStatus>("VIDEO_READY");
  const [sampleRegenCount, setSampleRegenCount] = useState(0);
  const [orgIncludedQuota, setOrgIncludedQuota] = useState(32);
  const [orgTopupQuota, setOrgTopupQuota] = useState(6);
  const [orgQuotaLedger, setOrgQuotaLedger] =
    useState<OrgQuotaLedgerItem[]>(INITIAL_ORG_QUOTA_LEDGER);
  const [presentationConfirmed, setPresentationConfirmed] = useState(false);
  const [playbackTokenIssued, setPlaybackTokenIssued] = useState<string | null>(
    "jwt:proj_98a1...3c (TTL 15m · Nội bộ lớp)"
  );
  const [presentationAuditLog, setPresentationAuditLog] = useState<PresentationAuditEntry[]>(
    INITIAL_PRESENTATION_AUDIT
  );
  const [captionsOn, setCaptionsOn] = useState(true);

  // Group 4, Feedback & Notifications
  const [grants, setGrants] = useState<TeacherGrantRow[]>(INITIAL_TEACHER_GRANTS);
  const [feedbackThread, setFeedbackThread] = useState<TeacherFeedbackItem[]>(
    INITIAL_TEACHER_FEEDBACK
  );
  const [teacherNotifications, setTeacherNotifications] = useState<TeacherNotificationItem[]>(
    INITIAL_TEACHER_NOTIFICATIONS
  );
  const [archiveModalTarget, setArchiveModalTarget] = useState<TeacherLessonCard | null>(null);
  const [toast, setToast] = useState<{ kind: "ok" | "info" | "warn" | "err"; text: string } | null>(null);

  const showToast = (text: string, kind: "ok" | "info" | "warn" | "err" = "ok") => {
    const visibleText = isLocalPreview() && !text.startsWith("Bản xem thử") ? `Bản xem thử · ${text}` : text;
    setToast({ kind, text: visibleText });
    window.setTimeout(() => setToast(null), 3500);
  };

  const pushTeacherNotif = (
    category: TeacherNotificationItem["category"],
    title: string,
    body: string,
    targetRoute: string
  ) => {
    setTeacherNotifications((prev) => [
      {
        id: `tnotif-${Date.now()}`,
        category,
        title,
        body,
        timestamp: "Vừa xong",
        unread: true,
        targetRoute,
      },
      ...prev,
    ]);
  };

  const forceCloseConflictAndCompleteTransfer = (classId: string, reason: string) => {
    setAssignedClasses((prev) =>
      prev.map((c) =>
        c.id === classId
          ? {
              ...c,
              rbacState: "ACTIVE",
              ownerTeacher: c.pendingTargetTeacher || "Cô Mai",
              pendingTargetTeacher: undefined,
              hasActiveRunConflict: false,
            }
          : c
      )
    );
    pushTeacherNotif(
      "CLASS_RBAC",
      "Đã hoàn tất bàn giao lớp (2-Owner Reassignment Saga)",
      `Đã đóng khẩn cấp run xung đột (Lý do: ${reason}) và chuyển quyền phụ trách lớp.`,
      "/t05-classes-and-children"
    );
    showToast(`Đã đóng khẩn cấp run xung đột (Audit: "${reason}") và hoàn tất bàn giao lớp.`, "ok");
  };

  const purchaseAddonClassSlot = () => {
    setAddonClassSlots((n) => n + 1);
    showToast("Đã mua thêm +1 slot lớp học (Prorate theo kỳ hiện tại).", "ok");
  };

  const deleteLesson = (id: string) => {
    setLessons((prev) => prev.filter((l) => l.id !== id));
    setArchiveModalTarget(null);
    showToast("Đã xóa và chuyển giáo án vào kho lưu trữ.", "info");
  };

  const archiveLesson = (id: string) => {
    deleteLesson(id);
  };

  const createLesson = (input: LessonMutationInput): TeacherLessonCard => {
    const cleanActivities =
      input.activities.filter((a) => a.trim().length > 0).length > 0
        ? input.activities.map((a) => a.trim()).filter(Boolean)
        : ["Hoạt động 1: Quan sát và trò chuyện theo chủ đề", "Hoạt động 2: Thực hành vẽ sáng tạo trên giấy A4"];
    const created: TeacherLessonCard = {
      id: `les-${Date.now()}`,
      title: input.title.trim() || "Giáo án mới",
      version: "Bản 1",
      versionHistory: [
        input.remixedFrom
          ? `Bản 1 (30/10/2026 · Tạo từ mẫu ${input.remixedFrom})`
          : "Bản 1 (30/10/2026 · Khởi tạo mới)",
      ],
      visibility: input.visibility,
      publicReviewStatus: input.visibility === "Công khai" ? "Chờ duyệt công khai" : "Bản nháp",
      updatedAt: "30/10/2026",
      ageBand: input.ageBand,
      topic: input.topic || "Thiên nhiên",
      description: input.description.trim() || input.objectives.trim(),
      objectives: input.objectives.trim(),
      activities: cleanActivities,
      approvedForSession: Boolean(input.approvedForSession),
      remixedFrom: input.remixedFrom,
      authorName: "Cô Nguyễn Phương Thảo",
    };
    setLessons((prev) => [created, ...prev]);
    if (input.approvedForSession) {
      setPinnedLessonTitle(created.title);
      setPinnedActivities(created.activities);
      setPinnedPlanRevision((r) => r + 1);
      setSafetyChecklistConfirmed(true);
      setOccurrenceStatus("SAMPLE_AVAILABLE");
      setDeckJobStatus("READY");
    }
    showToast(`Đã tạo giáo án "${created.title}" thành công.`, "ok");
    return created;
  };

  const updateLesson = (id: string, patch: Partial<LessonMutationInput>) => {
    setLessons((prev) =>
      prev.map((l) => {
        if (l.id !== id) return l;
        const nextNum = l.versionHistory.length + 1;
        const nextVer = `Bản ${nextNum}`;
        const updatedActivities =
          patch.activities !== undefined
            ? patch.activities.map((a) => a.trim()).filter(Boolean)
            : l.activities;
        const nextTitle = patch.title !== undefined ? patch.title.trim() || l.title : l.title;
        if (l.title === pinnedLessonTitle) {
          setPinnedLessonTitle(nextTitle);
          setPinnedActivities(updatedActivities);
        }
        return {
          ...l,
          title: nextTitle,
          topic: patch.topic ?? l.topic,
          ageBand: patch.ageBand ?? l.ageBand,
          visibility: patch.visibility ?? l.visibility,
          publicReviewStatus:
            patch.visibility === "Công khai" && l.publicReviewStatus === "Bản nháp"
              ? "Chờ duyệt công khai"
              : l.publicReviewStatus,
          description: patch.description !== undefined ? patch.description : l.description,
          objectives: patch.objectives !== undefined ? patch.objectives : l.objectives,
          activities: updatedActivities,
          approvedForSession:
            patch.approvedForSession !== undefined ? patch.approvedForSession : l.approvedForSession,
          version: nextVer,
          updatedAt: "30/10/2026",
          versionHistory: [...l.versionHistory, `${nextVer} (30/10/2026 · Cập nhật nội dung)`],
        };
      })
    );
    showToast("Đã cập nhật giáo án và lưu phiên bản mới.", "ok");
  };

  const approveLessonForSession = (id: string) => {
    const src = lessons.find((l) => l.id === id) || publicTemplates.find((t) => t.id === id) || lessons[0];
    if (!src) return;
    setLessons((prev) =>
      prev.map((l) => ({
        ...l,
        approvedForSession: l.id === src.id ? true : l.approvedForSession,
      }))
    );
    setPinnedLessonTitle(src.title);
    setPinnedActivities(src.activities);
    setPinnedPlanRevision((r) => r + 1);
    setPinnedPlanHash(`sha256:9c${Date.now().toString().slice(-4)}...f04b`);
    setSafetyChecklistConfirmed(true);
    setOccurrenceStatus("SAMPLE_AVAILABLE");
    setDeckJobStatus("READY");
    if (src.activities[0]) setSelectedSampleActivity(src.activities[0]);
    showToast(`Đã duyệt an toàn (BR-14) và ghim "${src.title}" cho buổi học hôm nay.`, "ok");
  };

  const restoreDefaultLessons = () => {
    setLessons(INITIAL_TEACHER_LESSONS);
    setUi05Mode("NORMAL");
    showToast("Đã khôi phục danh sách giáo án mẫu.", "ok");
  };

  const remixLesson = (id: string) => {
    const src =
      lessons.find((l) => l.id === id) ||
      publicTemplates.find((t) => t.id === id) ||
      lessons[0];
    const clone: TeacherLessonCard = {
      id: `les-remix-${Date.now()}`,
      title: `${src.title} (Bản Remix)`,
      version: "Bản 1",
      versionHistory: [`Bản 1 (30/10/2026 · Remix từ ${src.title} ${src.version})`],
      visibility: "Riêng tư",
      publicReviewStatus: "Bản nháp",
      updatedAt: "30/10/2026",
      ageBand: src.ageBand,
      topic: src.topic,
      description: src.description,
      objectives: src.objectives,
      activities: [...src.activities],
      approvedForSession: false,
      remixedFrom: `${src.title} · ${src.version}`,
      authorName: "Cô Nguyễn Phương Thảo",
    };
    setLessons((prev) => [clone, ...prev]);
    showToast(`Đã tạo bản sao Remix từ "${src.title} · ${src.version}".`, "ok");
  };

  const createNewLessonVersion = (id: string) => {
    setLessons((prev) =>
      prev.map((l) => {
        if (l.id !== id) return l;
        const nextNum = l.versionHistory.length + 1;
        const nextVer = `Bản ${nextNum}`;
        return {
          ...l,
          version: nextVer,
          updatedAt: "30/10/2026",
          versionHistory: [...l.versionHistory, `${nextVer} (30/10/2026 · Phiên bản bất biến mới)`],
        };
      })
    );
    showToast("Đã phát hành phiên bản giáo án bất biến mới.", "ok");
  };

  const useLessonForOccurrence = (id: string) => {
    const src =
      lessons.find((l) => l.id === id) ||
      publicTemplates.find((t) => t.id === id) ||
      lessons[0];
    if (!src) return;
    setPinnedLessonTitle(src.title);
    setPinnedActivities(src.activities);
    if (src.activities[0]) setSelectedSampleActivity(src.activities[0]);
    setPinnedPlanRevision((r) => r + 1);
    setPinnedPlanHash(`sha256:8b${Date.now().toString().slice(-4)}...e12a`);
    setOccurrenceStatus("APPROVED");
    setDeckJobStatus("READY");
    showToast(`Đã chọn giáo án "${src.title}" cho buổi học hiện tại.`, "ok");
  };

  const addRosterChild = (
    label: string,
    ageMonths: number,
    interests = ["Khám phá thiên nhiên", "Vẽ màu sáp"],
    learningNotes = "Trẻ tích cực tham gia giờ vẽ trên giấy.",
    supportNeedsNote = "Mặc định loại khỏi ngữ cảnh AI (BR-20).",
    targetClassName?: string
  ) => {
    const activeCls = assignedClasses.find((c) => c.id === activeClassId) || assignedClasses[0];
    const resolvedClass = targetClassName || activeCls?.className || "Lớp Mầm 2";
    const years = Math.max(3, Math.floor(ageMonths / 12));
    const formattedLabel = label.includes("tuổi") ? label.trim() : `${label.trim()} · ${years} tuổi`;
    setRoster((prev) => [
      ...prev,
      {
        id: `roster-${Date.now()}`,
        displayLabel: formattedLabel,
        ageMonths,
        ageText: `${ageMonths} tháng · ${years} tuổi`,
        profileShared: true,
        consentAccepted: true,
        className: resolvedClass,
        enrollmentStatus: "ACTIVE",
        interests,
        learningNotes,
        supportNeedsNote,
      },
    ]);
    showToast(`Đã thêm ${formattedLabel} (${ageMonths} tháng) vào ${resolvedClass}.`, "ok");
  };

  const updateRosterChild = (
    childId: string,
    patch: {
      label: string;
      ageMonths: number;
      interests: string[];
      learningNotes: string;
      supportNeedsNote: string;
    }
  ) => {
    const years = Math.max(3, Math.floor(patch.ageMonths / 12));
    const cleanBase = patch.label.replace(/\s*·\s*\d+\s*tuổi$/i, "").trim();
    const formattedLabel = `${cleanBase} · ${years} tuổi`;
    setRoster((prev) =>
      prev.map((r) =>
        r.id === childId
          ? {
              ...r,
              displayLabel: formattedLabel,
              ageMonths: patch.ageMonths,
              ageText: `${patch.ageMonths} tháng · ${years} tuổi`,
              interests: patch.interests,
              learningNotes: patch.learningNotes,
              supportNeedsNote: patch.supportNeedsNote,
            }
          : r
      )
    );
    showToast(`Đã cập nhật hồ sơ học sinh ${formattedLabel}.`, "ok");
  };

  const transferChildClass = (childId: string, targetClassName: string) => {
    setRoster((prev) =>
      prev.map((r) =>
        r.id === childId
          ? {
              ...r,
              previousClassHistory: `Đã đóng ghi danh ${r.className} (30/10/2026)`,
              className: targetClassName,
              enrollmentStatus: "ACTIVE",
            }
          : r
      )
    );
    pushTeacherNotif(
      "CLASS_RBAC",
      `Đã chuyển lớp cho học sinh sang ${targetClassName}`,
      "Ghi danh lớp cũ đã đóng và lưu lịch sử; ghi danh lớp mới đã kích hoạt (1 lớp ACTIVE duy nhất).",
      "/t05-classes-and-children"
    );
    showToast(
      `Đã đóng ghi danh lớp cũ và chuyển trẻ sang ${targetClassName} (tối đa 1 lớp ACTIVE / trẻ).`,
      "ok"
    );
  };

  const deleteRosterChildLifecycle = (childId: string) => {
    setRoster((prev) =>
      prev.map((r) => (r.id === childId ? { ...r, enrollmentStatus: "DELETE_PENDING" } : r))
    );
    showToast("Hồ sơ chuyển sang DELETE_PENDING: đang thu hồi grant và xóa dữ liệu...", "warn");
    window.setTimeout(() => {
      setRoster((prev) =>
        prev.map((r) =>
          r.id === childId ? { ...r, enrollmentStatus: "DELETED", profileShared: false } : r
        )
      );
      showToast("Đã hoàn tất xóa hồ sơ trẻ khỏi danh sách hoạt động (DELETED).", "info");
    }, 1000);
  };

  const handleRealDocumentUpload = (fileName: string, sizeBytes: number) => {
    const mb = (sizeBytes / (1024 * 1024)).toFixed(2).replace(".", ",");
    setUploadedFileName(fileName);
    setUploadedFileSizeMb(`${mb} MB`);
    setUploadedSha256(`sha256:${Math.random().toString(16).slice(2, 10)}...f82c`);
    setImportErrorMode("NONE");
    showToast(`Đã tải lên "${fileName}" (${mb} MB) theo từng phần ≤ 4 MiB & kiểm tra SHA-256.`, "ok");
  };

  const approveExtractedDocumentRevision = () => {
    const nextRev = documentRevision + 1;
    setDocumentRevision(nextRev);
    setOccurrenceStatus("PLAN_REVIEW");
    pushTeacherNotif(
      "OCCURRENCE",
      `Đã duyệt dữ liệu trích xuất (Document Revision #${nextRev})`,
      `Nguồn tệp: ${uploadedFileName} (${uploadedSha256}).`,
      "/t04-session-sketch-deck"
    );
    showToast(`Đã lưu dữ liệu đã lọc thành Document Revision #${nextRev} (bất biến).`, "ok");
  };

  const approveOccurrencePlan = () => {
    if (!safetyChecklistConfirmed) {
      showToast("Vui lòng xác nhận Checklist an toàn trước khi duyệt kế hoạch buổi học.", "warn");
      return;
    }
    setOccurrenceStatus("SAMPLE_AVAILABLE");
    setDeckJobStatus("READY");
    pushTeacherNotif(
      "OCCURRENCE",
      `Đã duyệt kế hoạch buổi học (${occurrenceId})`,
      `Đã ghim ${pinnedLessonTitle} · Bản #${pinnedPlanRevision} (${pinnedPlanHash}). Mở quyền tạo Sketch Deck & Video mẫu.`,
      "/t04-session-sketch-deck"
    );
    showToast(
      `Đã duyệt kế hoạch buổi học (Plan Revision #${pinnedPlanRevision}). Đã mở quyền Sketch Deck & 1 suất Video mẫu.`,
      "ok"
    );
  };

  const simulatePlanChangeStaleDeck = () => {
    const nextPlanRev = pinnedPlanRevision + 1;
    setPinnedPlanRevision(nextPlanRev);
    setPinnedPlanHash(`sha256:3f0${nextPlanRev}c9...a71d`);
    setDeckJobStatus("STALE");
    showToast(
      `Kế hoạch buổi học vừa đổi sang Bản #${nextPlanRev}: Sketch Deck cũ chuyển sang STALE và bị khóa chiếu cho đến khi tạo lại.`,
      "warn"
    );
  };

  const toggleSkipDeckStep = (step: number) => {
    setSkippedSteps((prev) =>
      prev.includes(step) ? prev.filter((s) => s !== step) : [...prev, step]
    );
  };

  const regenerateDeckStep = () => {
    const nextRev = deckRevision + 1;
    setDeckRevision(nextRev);
    setDeckJobStatus("READY");
    showToast(
      `Đã tạo lại nét gợi ý Bước ${activeDeckStep} → Deck Revision #${nextRev} (Gắn với Plan #${pinnedPlanRevision}, không trừ quota video).`,
      "ok"
    );
  };

  const setSampleDetectedSubject = (sub: string) => {
    setSampleDetectedSubjectState(sub);
    setSampleSubjectRevision((r) => r + 1);
  };

  const confirmSampleTranscript = () => {
    setSampleTranscriptConfirmed(true);
    showToast("Đã xác nhận Transcript giọng nói (Whisper ASR) cho video mẫu.", "ok");
  };

  const confirmSampleContextSnapshot = () => {
    setSampleContextConfirmed(true);
    showToast("Đã xác nhận Minimal Profile Context Snapshot (không chứa tên thật & ghi chú nhạy cảm).", "ok");
  };

  const requestSampleRewrite = () => {
    if (sampleRewriteCount >= 3) {
      showToast("STORY_REWRITE_LIMIT_REACHED: Đã đạt giới hạn 3/3 lần viết lại kịch bản mẫu.", "warn");
      return;
    }
    const nextRev = sampleScriptRevision + 1;
    const nextHash = `sha256:6b${nextRev}e82...d1${nextRev}a`;
    setSampleRewriteCount((c) => c + 1);
    setSampleScriptRevision(nextRev);
    setSampleScriptHash(nextHash);
    setSampleVideoConfirmed(false);
    setSampleScenes((prev) =>
      prev.map((s, idx) =>
        idx === 1
          ? {
              ...s,
              title: "Cảnh 2 · Chiếc kén nhỏ dưới tán lá xanh",
              narration: `Theo hướng giáo án (${sampleRewriteHint}), chú sâu tạo kén nhỏ dưới chiếc lá xanh.`,
            }
          : s
      )
    );
    showToast(
      `AI đã tạo kịch bản mẫu Bản #${nextRev} (${nextHash}). Vui lòng rà soát và xác nhận lại.`,
      "info"
    );
  };

  const confirmSampleScript = () => {
    setSampleVideoConfirmed(true);
    setSampleVideoJobStatusState("VIDEO_READY");
    setOccurrenceStatus("SAMPLE_USED");
    setOrgIncludedQuota((q) => Math.max(0, q - 1));
    setOrgQuotaLedger((prev) => [
      {
        id: `org-led-${Date.now()}`,
        date: "30/10/2026 10:30",
        runTitle: `Video mẫu Lớp Mầm 2 · ${pinnedLessonTitle} (Bản #${sampleScriptRevision})`,
        bucket: "Gói trường hàng tháng",
        delta: "-1 lượt",
        note: "VIDEO_READY · Đã phát hành video mẫu đầu tiên → Chiếm vĩnh viễn suất SAMPLE_USED của buổi học",
      },
      ...prev,
    ]);
    pushTeacherNotif(
      "VIDEO_JOB",
      `Đã tạo xong Video mẫu (Bản kịch bản #${sampleScriptRevision})`,
      "Suất mẫu của buổi học đã chuyển sang SAMPLE_USED. Vui lòng xác nhận trình chiếu tại T07.",
      "/t07-video-presentation-confirmation"
    );
    showToast(
      `Đã xác nhận kịch bản Bản #${sampleScriptRevision} (${sampleScriptHash}) & tạo video mẫu.`,
      "ok"
    );
  };

  const setSampleVideoJobStatus = (s: SampleVideoJobStatus) => {
    setSampleVideoJobStatusState(s);
    if (s === "SAFETY_BLOCKED" || s === "FAILED") {
      setOccurrenceStatus("SAMPLE_AVAILABLE");
    } else if (s === "VIDEO_READY") {
      setOccurrenceStatus("SAMPLE_USED");
    }
  };

  const markSampleVideoUnsuitable = (reason: string): boolean => {
    if (sampleRegenCount >= 2) {
      showToast("Đã dùng hết 2/2 lần tạo lại vì chất lượng cho video mẫu này.", "warn");
      return false;
    }
    setSampleRegenCount((c) => c + 1);
    setSampleVideoConfirmed(false);
    pushTeacherNotif(
      "VIDEO_JOB",
      "Giáo viên đã báo video mẫu không phù hợp (REJECTED_BY_ADULT)",
      `Lý do: ${reason}. Đã ẩn ngay video cũ (${sampleRegenCount + 1}/2 lần tạo lại).`,
      "/t06-sample-story-run"
    );
    showToast(
      `Đã ẩn ngay video mẫu cũ (REJECTED_BY_ADULT) · Lần tạo lại ${sampleRegenCount + 1}/2.`,
      "info"
    );
    return true;
  };

  const completeSampleRun = () => {
    setSampleVideoJobStatusState("COMPLETED");
    pushTeacherNotif(
      "VIDEO_JOB",
      "Đã hoàn tất buổi trình chiếu video mẫu (COMPLETED)",
      `Buổi học ${occurrenceId} · Lớp Mầm 2 đã hoàn tất.`,
      "/t01-lesson-workspace"
    );
    showToast("Đã hoàn tất vòng đời video mẫu của buổi học (COMPLETED).", "ok");
  };

  const cancelOrDeleteSampleRun = () => {
    setSampleVideoJobStatusState("DELETE_PENDING");
    setPlaybackTokenIssued(null);
    showToast("Run chuyển sang DELETE_PENDING: đang thu hồi token phát và xóa tài nguyên...", "warn");
    window.setTimeout(() => {
      setSampleVideoJobStatusState("DELETED");
      showToast("Đã xóa hoàn toàn dữ liệu run (DELETED). Lượt quota đã nhận không hoàn lại.", "info");
    }, 900);
  };

  const confirmClassroomPresentation = () => {
    const newToken = `jwt:proj_${Math.random().toString(16).slice(2, 8)}...9f (TTL 15m · Nội bộ lớp)`;
    setPresentationConfirmed(true);
    setPlaybackTokenIssued(newToken);
    setPresentationAuditLog((prev) => [
      {
        id: `aud-${Date.now()}`,
        timestamp: "30/10/2026 10:35",
        teacherName: "Cô Thảo",
        className: "Lớp Mầm 2",
        occurrenceId,
        scriptRevision: sampleScriptRevision,
        tokenSummary: newToken,
      },
      ...prev,
    ]);
    pushTeacherNotif(
      "VIDEO_JOB",
      "Đã ghi nhận Audit trình chiếu lớp học & cấp Playback Token",
      `Lớp Mầm 2 · Buổi học ${occurrenceId} · Token: ${newToken}`,
      "/t07-video-presentation-confirmation"
    );
    showToast("Đã ghi nhật ký kiểm toán (Audit Log) & cấp projection-playback-token ngắn hạn.", "ok");
  };

  const revokeTeacherGrant = (id: string) => {
    setGrants((prev) =>
      prev.map((g) =>
        g.id === id ? { ...g, status: "Đã thu hồi", consentState: "Đã rút Consent" } : g
      )
    );
    pushTeacherNotif(
      "GRANT_CONSENT",
      "Đã thu hồi quyền chia sẻ (Grant Revoked)",
      `Mã bản ghi ${id} đã chuyển sang trạng thái Đã thu hồi ngay lập tức.`,
      "/t05-classes-and-children"
    );
    showToast("Đã thu hồi quyền chia sẻ ngay lập tức.", "info");
  };

  const addLessonGrant = (recipient: string, scope: string, expiresAt = "30/11/2026") => {
    setGrants((prev) => [
      {
        id: `tg-${Date.now()}`,
        kind: "LESSON",
        recipient,
        scope,
        consentState: "Đã đồng ý",
        expiresAt,
        status: "Đang hiệu lực",
      },
      ...prev,
    ]);
    pushTeacherNotif(
      "GRANT_CONSENT",
      `Đã chia sẻ giáo án cho ${recipient}`,
      scope,
      "/t02-lesson-authoring"
    );
    showToast(`Đã cấp quyền chia sẻ giáo án cho "${recipient}".`, "ok");
  };

  const requestParentProfileGrant = (childLabel: string) => {
    setGrants((prev) => [
      {
        id: `tg-prof-${Date.now()}`,
        kind: "CHILD_PROFILE",
        recipient: "Cô Thảo · Lớp Mầm 2",
        scope: `Lời mời chia sẻ hồ sơ trẻ: ${childLabel} (36–120 tháng)`,
        consentState: "Đang chờ phụ huynh",
        expiresAt: "30/11/2026",
        status: "Đang chờ",
      },
      ...prev,
    ]);
    showToast(`Đã gửi lời mời chia sẻ hồ sơ của ${childLabel} tới phụ huynh.`, "ok");
  };

  const simulateParentAcceptGrant = (id: string) => {
    setGrants((prev) =>
      prev.map((g) =>
        g.id === id ? { ...g, status: "Đang hiệu lực", consentState: "Đã đồng ý" } : g
      )
    );
    pushTeacherNotif(
      "GRANT_CONSENT",
      "Phụ huynh đã chấp nhận lời mời chia sẻ hồ sơ",
      "Giáo viên đã có quyền xem thông tin học tập tối thiểu của trẻ.",
      "/t05-classes-and-children"
    );
    showToast("Phụ huynh đã đồng ý Consent & kích hoạt Grant chia sẻ hồ sơ.", "ok");
  };

  const replyToFeedback = (text: string) => {
    if (!text.trim()) return;
    setFeedbackThread((prev) => [
      ...prev,
      {
        id: `tfb-${Date.now()}`,
        sender: "Cô Thảo · Trường Mầm non Ánh Dương",
        lessonTitle: `${pinnedLessonTitle} · Bản ${pinnedPlanRevision}`,
        text: text.trim(),
        date: "30/10/2026 10:40",
      },
    ]);
    pushTeacherNotif(
      "FEEDBACK",
      "Đã gửi phản hồi cho Phụ huynh bé Minh",
      `Nội dung: "${text.trim()}"`,
      "/t01-lesson-workspace?view=feedback"
    );
    showToast("Đã gửi phản hồi của giáo viên và đồng bộ vào hộp thư sự kiện.", "ok");
  };

  const markTeacherNotifRead = (id: string) => {
    setTeacherNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, unread: false } : n))
    );
  };

  const markAllTeacherNotifsRead = () => {
    setTeacherNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
    showToast("Đã đánh dấu đã đọc tất cả thông báo.", "ok");
  };

  return (
    <TeacherContext.Provider
      value={{
        theme,
        setTheme,
        toggleTheme,
        currentRole,
        loginAsRole,
        logout,
        isAuthenticated,
        accountActivationState,
        setAccountActivationState,
        assignedClasses,
        activeClassId,
        setActiveClassId,
        baseClassSlots,
        addonClassSlots,
        usedClassSlots,
        graceDaysRemaining,
        forceCloseConflictAndCompleteTransfer,
        purchaseAddonClassSlot,
        lessons,
        publicTemplates,
        createLesson,
        updateLesson,
        deleteLesson,
        approveLessonForSession,
        archiveLesson,
        restoreDefaultLessons,
        remixLesson,
        createNewLessonVersion,
        useLessonForOccurrence,
        ui05Mode,
        setUi05Mode,
        roster,
        addRosterChild,
        updateRosterChild,
        transferChildClass,
        deleteRosterChildLifecycle,
        importErrorMode,
        setImportErrorMode,
        uploadedFileName,
        uploadedFileSizeMb,
        uploadedSha256,
        documentRevision,
        handleRealDocumentUpload,
        approveExtractedDocumentRevision,
        occurrenceId,
        occurrenceStatus,
        setOccurrenceStatus,
        pinnedLessonTitle,
        setPinnedLessonTitle,
        pinnedPlanRevision,
        pinnedPlanHash,
        pinnedActivities,
        setPinnedActivities,
        safetyChecklistConfirmed,
        setSafetyChecklistConfirmed,
        approveOccurrencePlan,
        simulatePlanChangeStaleDeck,
        sketchDeckEnabled,
        setSketchDeckEnabled,
        deckJobStatus,
        setDeckJobStatus,
        activeDeckStep,
        setActiveDeckStep,
        skippedSteps,
        toggleSkipDeckStep,
        deckRevision,
        regenerateDeckStep,
        selectedSampleChildId,
        setSelectedSampleChildId,
        selectedSampleActivity,
        setSelectedSampleActivity,
        sampleArtworkName,
        setSampleArtworkName,
        sampleDetectedSubject,
        setSampleDetectedSubject,
        sampleSubjectRevision,
        sampleAudioDurationSec,
        sampleAudioSizeMb,
        sampleRawTranscript,
        sampleEditedTranscript,
        setSampleEditedTranscript,
        sampleTranscriptConfirmed,
        confirmSampleTranscript,
        sampleContextConfirmed,
        confirmSampleContextSnapshot,
        followLessonDirection,
        setFollowLessonDirection,
        sampleScenes,
        sampleScriptRevision,
        sampleScriptHash,
        sampleRewriteCount,
        sampleRewriteHint,
        setSampleRewriteHint,
        requestSampleRewrite,
        sampleVideoConfirmed,
        confirmSampleScript,
        sampleVideoJobStatus,
        setSampleVideoJobStatus,
        sampleRegenCount,
        markSampleVideoUnsuitable,
        completeSampleRun,
        cancelOrDeleteSampleRun,
        orgIncludedQuota,
        orgTopupQuota,
        orgQuotaLedger,
        presentationConfirmed,
        playbackTokenIssued,
        presentationAuditLog,
        confirmClassroomPresentation,
        captionsOn,
        setCaptionsOn,
        grants,
        revokeTeacherGrant,
        addLessonGrant,
        requestParentProfileGrant,
        simulateParentAcceptGrant,
        feedbackThread,
        replyToFeedback,
        teacherNotifications,
        markTeacherNotifRead,
        markAllTeacherNotifsRead,
        archiveModalTarget,
        setArchiveModalTarget,
        toast,
        showToast,
      }}
    >
      {children}
    </TeacherContext.Provider>
  );
}

export function useTeacher() {
  const ctx = useContext(TeacherContext);
  if (!ctx) throw new Error("useTeacher must be used inside TeacherProvider");
  return ctx;
}
