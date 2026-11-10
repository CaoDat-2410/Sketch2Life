import React, { createContext, useContext, useEffect, useState } from "react";
import { isLocalPreview } from "../../../shared/backendApi";
import {
  AccessGrantItem,
  ChildProfileItem,
  INITIAL_GRANTS,
  INITIAL_LESSONS,
  INITIAL_NOTIFICATIONS,
  INITIAL_PROFILES,
  INITIAL_QUOTA_LEDGER,
  INITIAL_RUN_HISTORY,
  INITIAL_SCENES,
  LessonCardItem,
  ParentNotificationItem,
  QuotaLedgerEntry,
  RunHistoryRecord,
  SceneItem,
} from "../data/mockParentData";

const isValidParentAge = (ageMonths: number) =>
  Number.isInteger(ageMonths) && ageMonths >= 36 && ageMonths <= 120;

export type VideoJobMode =
  | "ADMISSION_PENDING"
  | "QUEUED"
  | "RUNNING"
  | "SAFETY_VALIDATING"
  | "RECONCILING"
  | "SAFETY_BLOCKED"
  | "SERVICE_ERROR"
  | "READY"
  | "DELETE_PENDING"
  | "DELETED";

export type AudioInputMode = "VALID" | "TOO_LONG" | "TOO_LARGE" | "MIC_DENIED";
export type PaymentSimStatus = "IDLE" | "PENDING" | "SUCCEEDED" | "FAILED";
export type Ui05LibraryState = "NORMAL" | "LOADING" | "EMPTY" | "STALE_409" | "FORBIDDEN_403";
export type ThemeMode = "light" | "dark";

export type ActiveSheetType =
  | null
  | "CONFIRM_SCRIPT"
  | "EDIT_SUBJECT"
  | "CANCEL_VIDEO"
  | "CAMERA_PERMISSION"
  | "ACCESS_GRANTS"
  | "NOTIFICATIONS"
  | "REPORT_UNSUITABLE"
  | "ADD_CHILD";

export interface FeedbackMessage {
  id: string;
  sender: "Phụ huynh" | "Cô Thảo · Trường Mầm non Ánh Dương";
  text: string;
  date: string;
}

interface ParentContextValue {
  theme: ThemeMode;
  setTheme: (t: ThemeMode) => void;
  isAuthenticated: boolean;
  setIsAuthenticated: (v: boolean) => void;
  profiles: ChildProfileItem[];
  selectedProfileId: string;
  setSelectedProfileId: (id: string) => void;
  addProfile: (
    displayName: string,
    ageMonths: number,
    interests: string[],
    learningNotes?: string,
    supportNeedsNote?: string,
    consentAccepted?: boolean
  ) => boolean;
  updateProfile: (
    id: string,
    displayName: string,
    ageMonths: number,
    learningNotes?: string,
    supportNeedsNote?: string,
    interests?: string[]
  ) => boolean;
  toggleProfileConsent: (id: string) => void;
  archiveProfile: (id: string) => void;
  restoreProfile: (id: string) => void;
  deleteProfileLifecycle: (id: string) => void;
  lessons: LessonCardItem[];
  selectedLessonId: string;
  setSelectedLessonId: (id: string) => void;
  libraryState: Ui05LibraryState;
  setLibraryState: (s: Ui05LibraryState) => void;
  skippedOptionalSetup: boolean;
  setSkippedOptionalSetup: (v: boolean) => void;
  guideEnabled: boolean;
  setGuideEnabled: (v: boolean) => void;
  guideTopic: string;
  setGuideTopic: (v: string) => void;
  detectedSubject: string;
  setDetectedSubject: (v: string) => void;
  subjectRevision: number;
  subjectConfirmed: boolean;
  setSubjectConfirmed: (v: boolean) => void;
  audioMode: AudioInputMode;
  setAudioMode: (m: AudioInputMode) => void;
  isRecording: boolean;
  setIsRecording: (v: boolean) => void;
  rawTranscript: string;
  ideaTranscript: string;
  setIdeaTranscript: (v: string) => void;
  transcriptRevision: number;
  transcriptConfirmed: boolean;
  confirmTranscript: () => void;
  contextSnapshotRevision: number;
  contextConfirmed: boolean;
  setContextConfirmed: (v: boolean) => void;
  confirmContextSnapshot: () => void;
  scenes: SceneItem[];
  scriptRevision: number;
  scriptHash: string;
  rewriteCount: number;
  rewriteSuggestion: string;
  setRewriteSuggestion: (v: string) => void;
  requestAiRewrite: () => void;
  scriptConfirmed: boolean;
  confirmScriptAndStartVideo: () => boolean;
  videoJobMode: VideoJobMode;
  setVideoJobMode: (m: VideoJobMode) => void;
  videoRegenCount: number;
  lastUnsuitableReason: string;
  reportVideoUnsuitableAndRegenerate: (reason: string) => boolean;
  cancelPurgeStep: number;
  triggerCancelIncompleteRun: () => void;
  landscapeVideo: boolean;
  setLandscapeVideo: (v: boolean) => void;
  autoLandscapeOnPlay: boolean;
  setAutoLandscapeOnPlay: (v: boolean) => void;
  includedQuotaRemaining: number;
  topupQuotaRemaining: number;
  quotaRemaining: number;
  quotaUsed: number;
  quotaTotal: number;
  quotaExceededDemo: boolean;
  setQuotaExceededDemo: (v: boolean) => void;
  usageLedger: QuotaLedgerEntry[];
  paymentStatus: PaymentSimStatus;
  setPaymentStatus: (s: PaymentSimStatus) => void;
  simulateTopupPurchase: (units: number, method: "MoMo" | "VNPAY", outcome: "SUCCEEDED" | "FAILED") => void;
  captionsEnabled: boolean;
  setCaptionsEnabled: (v: boolean) => void;
  hasActiveRun: boolean;
  setHasActiveRun: (v: boolean) => void;
  historyDeleted: boolean;
  setHistoryDeleted: (v: boolean) => void;
  runHistory: RunHistoryRecord[];
  deleteRunRecordLifecycle: (id: string) => void;
  resolve144hRun: (id: string, action: "COMPLETE" | "AUTO_168H") => void;
  restoreRunHistoryDemo: () => void;
  feedbackMessages: FeedbackMessage[];
  sendFeedback: (text: string, silentToast?: boolean) => void;
  clearFeedbackForDemo: () => void;
  restoreFeedbackForDemo: () => void;
  grants: AccessGrantItem[];
  revokeGrant: (id: string) => void;
  acceptGrantInvite: (id: string) => void;
  declineGrantInvite: (id: string) => void;
  createProfileShareGrant: (recipient: string, childName: string, expiresAt: string) => void;
  notifications: ParentNotificationItem[];
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  pushEndpointActive: boolean;
  setPushEndpointActive: (v: boolean) => void;
  activeSheet: ActiveSheetType;
  setActiveSheet: (s: ActiveSheetType) => void;
  toast: { kind: "ok" | "info" | "warn" | "err"; text: string } | null;
  showToast: (text: string, kind?: "ok" | "info" | "warn" | "err") => void;
}

const DEFAULT_FEEDBACK: FeedbackMessage[] = [
  {
    id: "fb-1",
    sender: "Phụ huynh",
    text: "Bé thích phần quan sát cánh bướm và đã cùng mẹ ra vườn tìm lá cây.",
    date: "30/10/2026",
  },
  {
    id: "fb-2",
    sender: "Cô Thảo · Trường Mầm non Ánh Dương",
    text: "Cô sẽ chuẩn bị thêm hoạt động quan sát ở buổi học tiếp theo cho Minh nhé.",
    date: "30/10/2026",
  },
];

function getInitialTheme(): ThemeMode {
  try {
    return window.localStorage.getItem("s2l-parent-theme") === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

const ParentContext = createContext<ParentContextValue | null>(null);

export function ParentProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>(getInitialTheme);
  const [isAuthenticated, setIsAuthenticated] = useState(isLocalPreview());
  const [profiles, setProfiles] = useState<ChildProfileItem[]>(INITIAL_PROFILES);
  const [selectedProfileId, setSelectedProfileId] = useState("child-minh");
  const [lessons] = useState<LessonCardItem[]>(INITIAL_LESSONS);
  const [selectedLessonId, setSelectedLessonId] = useState("lesson-butterfly");
  const [libraryState, setLibraryState] = useState<Ui05LibraryState>("NORMAL");
  const [skippedOptionalSetup, setSkippedOptionalSetup] = useState<boolean>(true);
  const [guideEnabled, setGuideEnabled] = useState(true);
  const [guideTopic, setGuideTopic] = useState("Con bướm");
  const [detectedSubject, setDetectedSubjectState] = useState("Con bướm");
  const [subjectRevision, setSubjectRevision] = useState(1);
  const [subjectConfirmed, setSubjectConfirmed] = useState(true);

  // Audio & idea input state
  const [audioMode, setAudioMode] = useState<AudioInputMode>("VALID");
  const [isRecording, setIsRecording] = useState(false);
  const [rawTranscript] = useState("vì sao con sâu nhỏ trên lá lại biến thành con bướm nhiều màu");
  const [ideaTranscript, setIdeaTranscriptState] = useState("Chú bướm nhỏ bay qua khu vườn đầy hoa nắng ấm.");
  const [transcriptRevision, setTranscriptRevision] = useState(1);
  const [transcriptConfirmed, setTranscriptConfirmed] = useState(true);

  const [contextSnapshotRevision, setContextSnapshotRevision] = useState(1);
  const [contextConfirmed, setContextConfirmed] = useState(true);

  // Script & Rewrite rules
  const [scenes, setScenes] = useState<SceneItem[]>(INITIAL_SCENES);
  const [scriptRevision, setScriptRevision] = useState(1);
  const [scriptHash, setScriptHash] = useState("sha256:8f4b2c...e91a");
  const [rewriteCount, setRewriteCount] = useState(0);
  const [rewriteSuggestion, setRewriteSuggestion] = useState("Thêm cảnh bướm ghé một bông hoa");
  const [scriptConfirmed, setScriptConfirmed] = useState(false);

  // Video job & playback landscape mode
  const [videoJobMode, setVideoJobMode] = useState<VideoJobMode>("RUNNING");
  const [videoRegenCount, setVideoRegenCount] = useState(0);
  const [lastUnsuitableReason, setLastUnsuitableReason] = useState("");
  const [cancelPurgeStep, setCancelPurgeStep] = useState(0);
  const [landscapeVideo, setLandscapeVideo] = useState(false);
  const [autoLandscapeOnPlay, setAutoLandscapeOnPlay] = useState(false);

  // Quota & Top-up & Ledger
  const [includedQuotaRemaining, setIncludedQuotaRemaining] = useState(1);
  const [topupQuotaRemaining, setTopupQuotaRemaining] = useState(1);
  const [quotaUsed, setQuotaUsed] = useState(4);
  const [quotaExceededDemo, setQuotaExceededDemo] = useState(false);
  const [usageLedger, setUsageLedger] = useState<QuotaLedgerEntry[]>(INITIAL_QUOTA_LEDGER);
  const [paymentStatus, setPaymentStatus] = useState<PaymentSimStatus>("IDLE");

  const quotaRemaining = quotaExceededDemo ? 0 : includedQuotaRemaining + topupQuotaRemaining;
  const quotaTotal = quotaUsed + quotaRemaining;

  const [captionsEnabled, setCaptionsEnabled] = useState(true);
  const [hasActiveRun, setHasActiveRun] = useState(true);
  const [historyDeleted, setHistoryDeleted] = useState(false);
  const [runHistory, setRunHistory] = useState<RunHistoryRecord[]>(INITIAL_RUN_HISTORY);
  const [feedbackMessages, setFeedbackMessages] = useState<FeedbackMessage[]>(DEFAULT_FEEDBACK);
  const [grants, setGrants] = useState<AccessGrantItem[]>(INITIAL_GRANTS);

  // Notifications & Push endpoint
  const [notifications, setNotifications] = useState<ParentNotificationItem[]>(INITIAL_NOTIFICATIONS);
  const [pushEndpointActive, setPushEndpointActive] = useState(true);

  const [activeSheet, setActiveSheet] = useState<ActiveSheetType>(null);
  const [toast, setToast] = useState<{ kind: "ok" | "info" | "warn" | "err"; text: string } | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      window.localStorage.setItem("s2l-parent-theme", theme);
    } catch {
      // ignore storage errors
    }
  }, [theme]);

  const setTheme = (t: ThemeMode) => {
    setThemeState(t);
  };

  const showToast = (text: string, kind: "ok" | "info" | "warn" | "err" = "ok") => {
    const visibleText = isLocalPreview() && !text.startsWith("Bản xem thử") ? `Bản xem thử · ${text}` : text;
    setToast({ kind, text: visibleText });
    window.setTimeout(() => setToast(null), 3500);
  };

  const pushNotification = (
    category: ParentNotificationItem["category"],
    title: string,
    body: string,
    targetPath: string,
    actionLabel: string
  ) => {
    setNotifications((prev) => [
      {
        id: `notif-${Date.now()}`,
        category,
        title,
        body,
        timestamp: "Vừa xong",
        unread: true,
        targetPath,
        actionLabel,
      },
      ...prev,
    ]);
  };

  const setDetectedSubject = (v: string) => {
    setDetectedSubjectState(v);
    setSubjectRevision((r) => r + 1);
  };

  const setIdeaTranscript = (v: string) => {
    setIdeaTranscriptState(v);
    setTranscriptConfirmed(true);
  };

  const confirmTranscript = () => {
    if (audioMode !== "VALID") {
      showToast("Vui lòng kiểm tra bản ghi âm (tối đa 2 phút, 20 MB).", "warn");
      return;
    }
    setTranscriptRevision((r) => r + 1);
    setTranscriptConfirmed(true);
  };

  const confirmContextSnapshot = () => {
    setContextSnapshotRevision((r) => r + 1);
    setContextConfirmed(true);
  };

  const addProfile = (
    displayName: string,
    ageMonths: number,
    interests: string[],
    learningNotes = "Bé thích quan sát tranh ảnh và hoạt động ngoài trời.",
    supportNeedsNote = "Mặc định loại khỏi ngữ cảnh AI.",
    consentAccepted = true
  ): boolean => {
    if (!isValidParentAge(ageMonths)) return false;
    const years = Math.max(3, Math.floor(ageMonths / 12));
    const newItem: ChildProfileItem = {
      id: `child-${Date.now()}`,
      displayName,
      ageMonths,
      ageLabel: `${years} tuổi (${ageMonths} tháng)`,
      ageGroup:
        ageMonths < 48
          ? "36–120 tháng · Mầm (3–4 tuổi)"
          : ageMonths < 72
          ? "36–120 tháng · Mẫu giáo (4–6 tuổi)"
          : "36–120 tháng · Tiểu học (6–10 tuổi)",
      interests: interests.length > 0 ? interests : ["Khám phá thiên nhiên", "Vẽ màu sáp"],
      learningNotes,
      supportNeedsNote,
      consentAccepted,
      consentUpdatedAt: "30/10/2026 10:00",
      archived: false,
      deletionStatus: "ACTIVE",
    };
    setProfiles((prev) => [...prev, newItem]);
    setSelectedProfileId(newItem.id);
    showToast(`Đã tạo hồ sơ ${displayName} (${years} tuổi · ${ageMonths} tháng).`, "ok");
    return true;
  };

  const updateProfile = (
    id: string,
    displayName: string,
    ageMonths: number,
    learningNotes?: string,
    supportNeedsNote?: string,
    interests?: string[]
  ): boolean => {
    if (!isValidParentAge(ageMonths)) return false;
    const years = Math.max(3, Math.floor(ageMonths / 12));
    setProfiles((prev) =>
      prev.map((p) =>
        p.id === id
          ? {
              ...p,
              displayName,
              ageMonths,
              ageLabel: `${years} tuổi (${ageMonths} tháng)`,
              ageGroup:
                ageMonths < 48
                  ? "36–120 tháng · Mầm (3–4 tuổi)"
                  : ageMonths < 72
                  ? "36–120 tháng · Mẫu giáo (4–6 tuổi)"
                  : "36–120 tháng · Tiểu học (6–10 tuổi)",
              learningNotes: learningNotes ?? p.learningNotes,
              supportNeedsNote: supportNeedsNote ?? p.supportNeedsNote,
              interests: interests ?? p.interests,
            }
          : p
      )
    );
    showToast(`Đã lưu cập nhật hồ sơ ${displayName}.`, "ok");
    return true;
  };

  const toggleProfileConsent = (id: string) => {
    setProfiles((prev) =>
      prev.map((p) => {
        if (p.id !== id) return p;
        const next = !p.consentAccepted;
        showToast(
          next
            ? `Đã bật đồng ý xử lý dữ liệu học tập cho ${p.displayName}.`
            : `Đã tắt đồng ý dữ liệu của ${p.displayName}. Các yêu cầu tạo AI mới sẽ tạm khóa.`,
          next ? "ok" : "warn"
        );
        return { ...p, consentAccepted: next, consentUpdatedAt: "30/10/2026 10:15" };
      })
    );
  };

  const archiveProfile = (id: string) => {
    setProfiles((prev) => prev.map((p) => (p.id === id ? { ...p, archived: true } : p)));
    showToast("Đã lưu trữ hồ sơ của bé.", "info");
  };

  const restoreProfile = (id: string) => {
    setProfiles((prev) =>
      prev.map((p) => (p.id === id ? { ...p, archived: false, deletionStatus: "ACTIVE" } : p))
    );
    setSelectedProfileId(id);
    showToast("Đã khôi phục hồ sơ của bé.", "ok");
  };

  const deleteProfileLifecycle = (id: string) => {
    setProfiles((prev) =>
      prev.map((p) => (p.id === id ? { ...p, deletionStatus: "DELETE_PENDING" } : p))
    );
    showToast("Đang thu hồi quyền chia sẻ và xóa dữ liệu hồ sơ…", "warn");
    window.setTimeout(() => {
      setProfiles((prev) =>
        prev.map((p) => (p.id === id ? { ...p, deletionStatus: "DELETED", archived: true } : p))
      );
      showToast("Đã xóa hồ sơ của bé.", "info");
    }, 900);
  };

  const requestAiRewrite = () => {
    if (rewriteCount >= 3) {
      showToast("Đã dùng tối đa 3/3 lần viết lại kịch bản trong phiên này.", "warn");
      return;
    }
    const hint = rewriteSuggestion.trim() || "Thêm cảnh bướm ghé một bông hoa";
    const nextRev = scriptRevision + 1;
    const nextHash = `sha256:9c${nextRev}d7a...b0${nextRev}f`;
    setRewriteCount((c) => c + 1);
    setScriptRevision(nextRev);
    setScriptHash(nextHash);
    setScriptConfirmed(false);
    setScenes((prev) =>
      prev.map((s, idx) =>
        idx === 3
          ? {
              ...s,
              title: "Cảnh 4 · Bướm ghé thăm bông hoa vàng",
              narration: `Theo gợi ý "${hint}", chú bướm dừng lại bên bông hoa vàng rực rỡ và vẫy đôi cánh màu sáp.`,
            }
          : s
      )
    );
    showToast(`AI đã cập nhật kịch bản Bản #${nextRev}. Bố mẹ hãy kiểm tra lại nhé.`, "info");
  };

  const consumeOneQuotaUnit = (runLabel: string) => {
    let bucketUsed: QuotaLedgerEntry["sourceBucket"] = "Lượt định kỳ";
    if (includedQuotaRemaining > 0) {
      setIncludedQuotaRemaining((q) => Math.max(0, q - 1));
      bucketUsed = "Lượt định kỳ";
    } else if (topupQuotaRemaining > 0) {
      setTopupQuotaRemaining((q) => Math.max(0, q - 1));
      bucketUsed = "Lượt mua thêm (FIFO)";
    }
    setQuotaUsed((u) => u + 1);
    setUsageLedger((prev) => [
      {
        id: `led-${Date.now()}`,
        date: "30/10/2026 10:20",
        runTitle: runLabel,
        sourceBucket: bucketUsed,
        delta: "-1 lượt",
        outcome: "Job đã được chấp nhận xử lý",
        tone: "ok",
      },
      ...prev,
    ]);
  };

  const confirmScriptAndStartVideo = (): boolean => {
    if (quotaRemaining <= 0) {
      showToast("Đã hết lượt tạo video. Vui lòng mua thêm lượt.", "warn");
      return false;
    }
    setScriptConfirmed(true);
    setHasActiveRun(true);
    consumeOneQuotaUnit(`Câu chuyện ${detectedSubject} · Bản #${scriptRevision}`);
    setVideoJobMode("RUNNING");
    setCancelPurgeStep(0);
    setActiveSheet(null);
    pushNotification(
      "VIDEO_JOB",
      `Đã nhận yêu cầu tạo video (Bản #${scriptRevision})`,
      "Hệ thống đang dựng 5 cảnh phim và kiểm tra an toàn tự động.",
      "/p07-video-job-status",
      "Xem tiến trình"
    );
    showToast(`Đã duyệt kịch bản Bản #${scriptRevision} và bắt đầu tạo video.`, "ok");
    return true;
  };

  const reportVideoUnsuitableAndRegenerate = (reason: string): boolean => {
    if (videoRegenCount >= 2) {
      showToast("Đã dùng tối đa 2/2 lần tạo lại cho phiên này.", "warn");
      return false;
    }
    setVideoRegenCount((c) => c + 1);
    setLastUnsuitableReason(reason);
    setScriptConfirmed(false);
    setLandscapeVideo(false);
    setActiveSheet(null);
    pushNotification(
      "VIDEO_JOB",
      "Đã ẩn video chưa phù hợp",
      `Lý do: ${reason}. Đã dùng ${videoRegenCount + 1}/2 lần tạo lại.`,
      "/p06-story-review",
      "Rà soát kịch bản"
    );
    showToast(`Đã ẩn video cũ · Lần tạo lại ${videoRegenCount + 1}/2. Quay về kịch bản.`, "info");
    return true;
  };

  const triggerCancelIncompleteRun = () => {
    setVideoJobMode("DELETE_PENDING");
    setHasActiveRun(false);
    setCancelPurgeStep(1);
    showToast("Đang hủy phiên tạo video và dọn tài nguyên…", "warn");
    window.setTimeout(() => setCancelPurgeStep(2), 450);
    window.setTimeout(() => setCancelPurgeStep(3), 900);
    window.setTimeout(() => {
      setCancelPurgeStep(4);
      setVideoJobMode("DELETED");
      showToast("Đã xóa hoàn toàn dữ liệu phiên tạo video.", "info");
    }, 1400);
  };

  const deleteRunRecordLifecycle = (id: string) => {
    setRunHistory((prev) =>
      prev.map((r) =>
        r.id === id
          ? {
              ...r,
              lifecycleState: "DELETE_PENDING",
              note: "Đang thu hồi URL phát và xóa dữ liệu câu chuyện…",
            }
          : r
      )
    );
    showToast("Đang xóa câu chuyện khỏi lịch sử…", "warn");
    window.setTimeout(() => {
      setRunHistory((prev) =>
        prev.map((r) =>
          r.id === id
            ? {
                ...r,
                lifecycleState: "DELETED",
                note: "Đã xóa toàn bộ media & dữ liệu câu chuyện.",
              }
            : r
        )
      );
      showToast("Đã xóa hoàn toàn câu chuyện.", "info");
    }, 1100);
  };

  const resolve144hRun = (id: string, action: "COMPLETE" | "AUTO_168H") => {
    setRunHistory((prev) =>
      prev.map((r) => {
        if (r.id !== id) return r;
        if (action === "COMPLETE") {
          return {
            ...r,
            lifecycleState: "COMPLETED",
            idleHours: 145,
            note: "Phụ huynh đã xác nhận hoàn tất trước mốc 168h.",
          };
        }
        return {
          ...r,
          lifecycleState: "COMPLETED",
          idleHours: 168,
          note: "Quá 168h ở trạng thái sẵn sàng → Hệ thống tự chuyển sang Hoàn thành.",
        };
      })
    );
    showToast(
      action === "COMPLETE"
        ? "Đã hoàn tất câu chuyện trước hạn 168h."
        : "Đã tự đóng câu chuyện ở mốc 168h.",
      "ok"
    );
  };

  const restoreRunHistoryDemo = () => {
    setRunHistory(INITIAL_RUN_HISTORY);
    setHistoryDeleted(false);
    showToast("Đã khôi phục dữ liệu lịch sử câu chuyện.", "ok");
  };

  const simulateTopupPurchase = (
    units: number,
    method: "MoMo" | "VNPAY",
    outcome: "SUCCEEDED" | "FAILED"
  ) => {
    setPaymentStatus("PENDING");
    showToast(`Đang tạo giao dịch mua +${units} lượt qua ${method}…`, "info");
    window.setTimeout(() => {
      setPaymentStatus(outcome);
      if (outcome === "SUCCEEDED") {
        setTopupQuotaRemaining((q) => q + units);
        setQuotaExceededDemo(false);
        setUsageLedger((prev) => [
          {
            id: `led-${Date.now()}`,
            date: "30/10/2026 10:25",
            runTitle: `Mua thêm gói +${units} lượt (${method})`,
            sourceBucket: "Nạp thêm (Top-up)",
            delta: `+${units} lượt`,
            outcome: "Thanh toán thành công · Giữ qua kỳ theo FIFO",
            tone: "ok",
          },
          ...prev,
        ]);
        pushNotification(
          "QUOTA_PAYMENT",
          `Thanh toán thành công +${units} lượt (${method})`,
          `Đã cộng +${units} lượt mua thêm vào tài khoản của bạn.`,
          "/p12-video-quota",
          "Xem số dư"
        );
        showToast(`Thanh toán ${method} thành công! Đã cộng +${units} lượt.`, "ok");
      } else {
        showToast(`Giao dịch ${method} thất bại. Chưa trừ tiền.`, "err");
      }
    }, 800);
  };

  const sendFeedback = (text: string, silentToast = false) => {
    if (!text.trim()) return;
    setFeedbackMessages((prev) => [
      ...prev,
      {
        id: `fb-${Date.now()}`,
        sender: "Phụ huynh",
        text: text.trim(),
        date: "30/10/2026",
      },
    ]);
    if (!silentToast) {
      showToast("Đã lưu đánh giá của bố mẹ.", "ok");
    }
  };

  const clearFeedbackForDemo = () => {
    setFeedbackMessages([]);
  };

  const restoreFeedbackForDemo = () => {
    setFeedbackMessages(DEFAULT_FEEDBACK);
  };

  const revokeGrant = (id: string) => {
    setGrants((prev) =>
      prev.map((g) => (g.id === id ? { ...g, status: "Đã thu hồi", updatedAt: "30/10/2026" } : g))
    );
    showToast("Đã thu hồi quyền chia sẻ ngay lập tức.", "info");
  };

  const acceptGrantInvite = (id: string) => {
    setGrants((prev) =>
      prev.map((g) => (g.id === id ? { ...g, status: "Đang hiệu lực", updatedAt: "30/10/2026" } : g))
    );
    showToast("Đã chấp nhận lời mời chia sẻ hồ sơ trẻ.", "ok");
  };

  const declineGrantInvite = (id: string) => {
    setGrants((prev) =>
      prev.map((g) => (g.id === id ? { ...g, status: "Đã từ chối", updatedAt: "30/10/2026" } : g))
    );
    showToast("Đã từ chối lời mời chia sẻ hồ sơ trẻ.", "info");
  };

  const createProfileShareGrant = (recipient: string, childName: string, expiresAt: string) => {
    setGrants((prev) => [
      {
        id: `grant-prof-${Date.now()}`,
        kind: "CHILD_PROFILE",
        recipient,
        scope: `Hồ sơ bé: ${childName} (Ẩn ghi chú hỗ trợ nhạy cảm)`,
        expiresAt,
        status: "Đang hiệu lực",
        updatedAt: "30/10/2026",
      },
      ...prev,
    ]);
    showToast(`Đã cấp quyền chia sẻ hồ sơ ${childName} cho ${recipient}.`, "ok");
  };

  const markNotificationRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, unread: false } : n)));
  };

  const markAllNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
    showToast("Đã đánh dấu đọc tất cả thông báo.", "ok");
  };

  return (
    <ParentContext.Provider
      value={{
        theme,
        setTheme,
        isAuthenticated,
        setIsAuthenticated,
        profiles,
        selectedProfileId,
        setSelectedProfileId,
        addProfile,
        updateProfile,
        toggleProfileConsent,
        archiveProfile,
        restoreProfile,
        deleteProfileLifecycle,
        lessons,
        selectedLessonId,
        setSelectedLessonId,
        libraryState,
        setLibraryState,
        skippedOptionalSetup,
        setSkippedOptionalSetup,
        guideEnabled,
        setGuideEnabled,
        guideTopic,
        setGuideTopic,
        detectedSubject,
        setDetectedSubject,
        subjectRevision,
        subjectConfirmed,
        setSubjectConfirmed,
        audioMode,
        setAudioMode,
        isRecording,
        setIsRecording,
        rawTranscript,
        ideaTranscript,
        setIdeaTranscript,
        transcriptRevision,
        transcriptConfirmed,
        confirmTranscript,
        contextSnapshotRevision,
        contextConfirmed,
        setContextConfirmed,
        confirmContextSnapshot,
        scenes,
        scriptRevision,
        scriptHash,
        rewriteCount,
        rewriteSuggestion,
        setRewriteSuggestion,
        requestAiRewrite,
        scriptConfirmed,
        confirmScriptAndStartVideo,
        videoJobMode,
        setVideoJobMode,
        videoRegenCount,
        lastUnsuitableReason,
        reportVideoUnsuitableAndRegenerate,
        cancelPurgeStep,
        triggerCancelIncompleteRun,
        landscapeVideo,
        setLandscapeVideo,
        autoLandscapeOnPlay,
        setAutoLandscapeOnPlay,
        includedQuotaRemaining,
        topupQuotaRemaining,
        quotaRemaining,
        quotaUsed,
        quotaTotal,
        quotaExceededDemo,
        setQuotaExceededDemo,
        usageLedger,
        paymentStatus,
        setPaymentStatus,
        simulateTopupPurchase,
        captionsEnabled,
        setCaptionsEnabled,
        hasActiveRun,
        setHasActiveRun,
        historyDeleted,
        setHistoryDeleted,
        runHistory,
        deleteRunRecordLifecycle,
        resolve144hRun,
        restoreRunHistoryDemo,
        feedbackMessages,
        sendFeedback,
        clearFeedbackForDemo,
        restoreFeedbackForDemo,
        grants,
        revokeGrant,
        acceptGrantInvite,
        declineGrantInvite,
        createProfileShareGrant,
        notifications,
        markNotificationRead,
        markAllNotificationsRead,
        pushEndpointActive,
        setPushEndpointActive,
        activeSheet,
        setActiveSheet,
        toast,
        showToast,
      }}
    >
      {children}
    </ParentContext.Provider>
  );
}

export function useParent() {
  const ctx = useContext(ParentContext);
  if (!ctx) throw new Error("useParent must be used inside ParentProvider");
  return ctx;
}
