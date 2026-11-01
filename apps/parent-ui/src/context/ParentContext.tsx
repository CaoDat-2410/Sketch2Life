import React, { createContext, useContext, useState } from "react";
import {
  AccessGrantItem,
  ChildProfileItem,
  INITIAL_GRANTS,
  INITIAL_LESSONS,
  INITIAL_PROFILES,
  INITIAL_SCENES,
  LessonCardItem,
  SceneItem,
} from "../data/mockParentData";

export type VideoJobMode = "RUNNING" | "SAFETY_BLOCKED" | "SERVICE_ERROR" | "READY";
export type Ui05LibraryState = "NORMAL" | "LOADING" | "EMPTY" | "STALE_409" | "FORBIDDEN_403";
export type ActiveSheetType =
  | null
  | "CONFIRM_SCRIPT"
  | "EDIT_SUBJECT"
  | "CANCEL_VIDEO"
  | "CAMERA_PERMISSION"
  | "ACCESS_GRANTS";

export interface FeedbackMessage {
  id: string;
  sender: "Phụ huynh" | "Cô Thảo · Trường Mầm non Ánh Dương";
  text: string;
  date: string;
}

interface ParentContextValue {
  isAuthenticated: boolean;
  setIsAuthenticated: (v: boolean) => void;
  profiles: ChildProfileItem[];
  selectedProfileId: string;
  setSelectedProfileId: (id: string) => void;
  addProfile: (displayName: string, ageMonths: number, interests: string[]) => void;
  updateProfile: (id: string, displayName: string, ageMonths: number) => void;
  archiveProfile: (id: string) => void;
  restoreProfile: (id: string) => void;
  lessons: LessonCardItem[];
  selectedLessonId: string;
  setSelectedLessonId: (id: string) => void;
  libraryState: Ui05LibraryState;
  setLibraryState: (s: Ui05LibraryState) => void;
  guideEnabled: boolean;
  setGuideEnabled: (v: boolean) => void;
  guideTopic: string;
  setGuideTopic: (v: string) => void;
  detectedSubject: string;
  setDetectedSubject: (v: string) => void;
  subjectConfirmed: boolean;
  setSubjectConfirmed: (v: boolean) => void;
  ideaTranscript: string;
  setIdeaTranscript: (v: string) => void;
  contextConfirmed: boolean;
  setContextConfirmed: (v: boolean) => void;
  scenes: SceneItem[];
  scriptRevision: number;
  rewriteCount: number;
  rewriteSuggestion: string;
  setRewriteSuggestion: (v: string) => void;
  requestAiRewrite: () => void;
  scriptConfirmed: boolean;
  confirmScriptAndStartVideo: () => void;
  videoJobMode: VideoJobMode;
  setVideoJobMode: (m: VideoJobMode) => void;
  quotaRemaining: number;
  quotaUsed: number;
  quotaTotal: number;
  captionsEnabled: boolean;
  setCaptionsEnabled: (v: boolean) => void;
  hasActiveRun: boolean;
  setHasActiveRun: (v: boolean) => void;
  historyDeleted: boolean;
  setHistoryDeleted: (v: boolean) => void;
  feedbackMessages: FeedbackMessage[];
  sendFeedback: (text: string) => void;
  clearFeedbackForDemo: () => void;
  restoreFeedbackForDemo: () => void;
  grants: AccessGrantItem[];
  revokeGrant: (id: string) => void;
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

const ParentContext = createContext<ParentContextValue | null>(null);

export function ParentProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [profiles, setProfiles] = useState<ChildProfileItem[]>(INITIAL_PROFILES);
  const [selectedProfileId, setSelectedProfileId] = useState("child-minh");
  const [lessons] = useState<LessonCardItem[]>(INITIAL_LESSONS);
  const [selectedLessonId, setSelectedLessonId] = useState("lesson-butterfly");
  const [libraryState, setLibraryState] = useState<Ui05LibraryState>("NORMAL");
  const [guideEnabled, setGuideEnabled] = useState(true);
  const [guideTopic, setGuideTopic] = useState("Con bướm");
  const [detectedSubject, setDetectedSubject] = useState("Con bướm");
  const [subjectConfirmed, setSubjectConfirmed] = useState(true);
  const [ideaTranscript, setIdeaTranscript] = useState("Vì sao sâu biến thành bướm?");
  const [contextConfirmed, setContextConfirmed] = useState(true);
  const [scenes, setScenes] = useState<SceneItem[]>(INITIAL_SCENES);
  const [scriptRevision, setScriptRevision] = useState(1);
  const [rewriteCount, setRewriteCount] = useState(0);
  const [rewriteSuggestion, setRewriteSuggestion] = useState("Thêm cảnh bướm ghé một bông hoa");
  const [scriptConfirmed, setScriptConfirmed] = useState(false);
  const [videoJobMode, setVideoJobMode] = useState<VideoJobMode>("RUNNING");
  const [quotaRemaining, setQuotaRemaining] = useState(2);
  const [quotaUsed, setQuotaUsed] = useState(4);
  const quotaTotal = 6;
  const [captionsEnabled, setCaptionsEnabled] = useState(true);
  const [hasActiveRun, setHasActiveRun] = useState(true);
  const [historyDeleted, setHistoryDeleted] = useState(false);
  const [feedbackMessages, setFeedbackMessages] = useState<FeedbackMessage[]>(DEFAULT_FEEDBACK);
  const [grants, setGrants] = useState<AccessGrantItem[]>(INITIAL_GRANTS);
  const [activeSheet, setActiveSheet] = useState<ActiveSheetType>(null);
  const [toast, setToast] = useState<{ kind: "ok" | "info" | "warn" | "err"; text: string } | null>(null);

  const showToast = (text: string, kind: "ok" | "info" | "warn" | "err" = "ok") => {
    setToast({ kind, text });
    window.setTimeout(() => setToast(null), 3500);
  };

  const addProfile = (displayName: string, ageMonths: number, interests: string[]) => {
    const years = Math.max(3, Math.floor(ageMonths / 12));
    const newItem: ChildProfileItem = {
      id: `child-${Date.now()}`,
      displayName,
      ageMonths,
      ageLabel: `${years} tuổi`,
      ageGroup: ageMonths < 60 ? "3–4 tuổi (Mầm)" : "4–5 tuổi (Mẫu giáo)",
      interests,
      archived: false,
    };
    setProfiles((prev) => [...prev, newItem]);
    setSelectedProfileId(newItem.id);
    showToast(`Đã tạo hồ sơ ${displayName} (${ageMonths} tháng tuổi).`, "ok");
  };

  const updateProfile = (id: string, displayName: string, ageMonths: number) => {
    const years = Math.max(3, Math.floor(ageMonths / 12));
    setProfiles((prev) =>
      prev.map((p) =>
        p.id === id
          ? {
              ...p,
              displayName,
              ageMonths,
              ageLabel: `${years} tuổi`,
              ageGroup: ageMonths < 60 ? "3–4 tuổi (Mầm)" : "4–5 tuổi (Mẫu giáo)",
            }
          : p
      )
    );
    showToast("Đã lưu thay đổi hồ sơ của bé.", "ok");
  };

  const archiveProfile = (id: string) => {
    setProfiles((prev) => prev.map((p) => (p.id === id ? { ...p, archived: true } : p)));
    showToast("Đã lưu trữ hồ sơ bé. Bạn có thể khôi phục bên dưới.", "info");
  };

  const restoreProfile = (id: string) => {
    setProfiles((prev) => prev.map((p) => (p.id === id ? { ...p, archived: false } : p)));
    setSelectedProfileId(id);
    showToast("Đã khôi phục hồ sơ của bé.", "ok");
  };

  const requestAiRewrite = () => {
    if (rewriteCount >= 3) {
      showToast("Đã dùng tối đa 3/3 lần viết lại kịch bản cho buổi này.", "warn");
      return;
    }
    const hint = rewriteSuggestion.trim() || "Thêm cảnh bướm ghé một bông hoa";
    const nextRev = scriptRevision + 1;
    setRewriteCount((c) => c + 1);
    setScriptRevision(nextRev);
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
    showToast(`AI đã tạo kịch bản Bản ${nextRev} · 5 cảnh. Vui lòng rà soát và xác nhận lại.`, "info");
  };

  const confirmScriptAndStartVideo = () => {
    if (quotaRemaining <= 0) {
      showToast("Đã hết lượt tạo video trong kỳ. Vui lòng xem lựa chọn bổ sung.", "warn");
      return;
    }
    setScriptConfirmed(true);
    setQuotaRemaining((q) => Math.max(0, q - 1));
    setQuotaUsed((u) => u + 1);
    setVideoJobMode("RUNNING");
    setActiveSheet(null);
    showToast("Đã xác nhận kịch bản và bắt đầu tạo video.", "ok");
  };

  const sendFeedback = (text: string) => {
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
    showToast("Đã gửi phản hồi gắn với bài học Vòng đời bướm.", "ok");
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
    showToast("Đã thu hồi quyền chia sẻ.", "info");
  };

  return (
    <ParentContext.Provider
      value={{
        isAuthenticated,
        setIsAuthenticated,
        profiles,
        selectedProfileId,
        setSelectedProfileId,
        addProfile,
        updateProfile,
        archiveProfile,
        restoreProfile,
        lessons,
        selectedLessonId,
        setSelectedLessonId,
        libraryState,
        setLibraryState,
        guideEnabled,
        setGuideEnabled,
        guideTopic,
        setGuideTopic,
        detectedSubject,
        setDetectedSubject,
        subjectConfirmed,
        setSubjectConfirmed,
        ideaTranscript,
        setIdeaTranscript,
        contextConfirmed,
        setContextConfirmed,
        scenes,
        scriptRevision,
        rewriteCount,
        rewriteSuggestion,
        setRewriteSuggestion,
        requestAiRewrite,
        scriptConfirmed,
        confirmScriptAndStartVideo,
        videoJobMode,
        setVideoJobMode,
        quotaRemaining,
        quotaUsed,
        quotaTotal,
        captionsEnabled,
        setCaptionsEnabled,
        hasActiveRun,
        setHasActiveRun,
        historyDeleted,
        setHistoryDeleted,
        feedbackMessages,
        sendFeedback,
        clearFeedbackForDemo,
        restoreFeedbackForDemo,
        grants,
        revokeGrant,
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
