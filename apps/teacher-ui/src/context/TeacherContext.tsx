import React, { createContext, useContext, useState } from "react";
import {
  ClassRosterRow,
  INITIAL_ROSTER,
  INITIAL_SAMPLE_SCENES,
  INITIAL_TEACHER_FEEDBACK,
  INITIAL_TEACHER_GRANTS,
  INITIAL_TEACHER_LESSONS,
  SampleSceneItem,
  TeacherFeedbackItem,
  TeacherGrantRow,
  TeacherLessonCard,
} from "../data/mockTeacherData";

export type ImportErrorMode = "NONE" | "TOO_LARGE" | "TOO_MANY_PAGES" | "SCANNED_PDF" | "PASSWORD_PROTECTED";
export type TeacherUi05Mode = "NORMAL" | "LOADING" | "EMPTY" | "STALE_409" | "FORBIDDEN_403";

interface TeacherContextValue {
  lessons: TeacherLessonCard[];
  archiveLesson: (id: string) => void;
  restoreDefaultLessons: () => void;
  ui05Mode: TeacherUi05Mode;
  setUi05Mode: (m: TeacherUi05Mode) => void;
  roster: ClassRosterRow[];
  addRosterChild: (label: string, ageMonths: number) => void;
  sketchDeckEnabled: boolean;
  setSketchDeckEnabled: (v: boolean) => void;
  activeDeckStep: number;
  setActiveDeckStep: (n: number) => void;
  deckRevision: number;
  regenerateDeckStep: () => void;
  followLessonDirection: boolean;
  setFollowLessonDirection: (v: boolean) => void;
  sampleScenes: SampleSceneItem[];
  sampleRewriteCount: number;
  sampleRewriteHint: string;
  setSampleRewriteHint: (v: string) => void;
  requestSampleRewrite: () => void;
  sampleVideoConfirmed: boolean;
  confirmSampleScript: () => void;
  presentationConfirmed: boolean;
  confirmClassroomPresentation: () => void;
  captionsOn: boolean;
  setCaptionsOn: (v: boolean) => void;
  importErrorMode: ImportErrorMode;
  setImportErrorMode: (m: ImportErrorMode) => void;
  grants: TeacherGrantRow[];
  revokeTeacherGrant: (id: string) => void;
  addLessonGrant: (recipient: string, scope: string) => void;
  feedbackThread: TeacherFeedbackItem[];
  replyToFeedback: (text: string) => void;
  archiveModalTarget: TeacherLessonCard | null;
  setArchiveModalTarget: (l: TeacherLessonCard | null) => void;
  toast: { kind: "ok" | "info" | "warn" | "err"; text: string } | null;
  showToast: (text: string, kind?: "ok" | "info" | "warn" | "err") => void;
}

const TeacherContext = createContext<TeacherContextValue | null>(null);

export function TeacherProvider({ children }: { children: React.ReactNode }) {
  const [lessons, setLessons] = useState<TeacherLessonCard[]>(INITIAL_TEACHER_LESSONS);
  const [ui05Mode, setUi05Mode] = useState<TeacherUi05Mode>("NORMAL");
  const [roster, setRoster] = useState<ClassRosterRow[]>(INITIAL_ROSTER);
  const [sketchDeckEnabled, setSketchDeckEnabled] = useState(true);
  const [activeDeckStep, setActiveDeckStep] = useState(1);
  const [deckRevision, setDeckRevision] = useState(1);
  const [followLessonDirection, setFollowLessonDirection] = useState(true);
  const [sampleScenes, setSampleScenes] = useState<SampleSceneItem[]>(INITIAL_SAMPLE_SCENES);
  const [sampleRewriteCount, setSampleRewriteCount] = useState(0);
  const [sampleRewriteHint, setSampleRewriteHint] = useState("Nhấn mạnh bước sâu hóa nhộng trên cành lá");
  const [sampleVideoConfirmed, setSampleVideoConfirmed] = useState(false);
  const [presentationConfirmed, setPresentationConfirmed] = useState(false);
  const [captionsOn, setCaptionsOn] = useState(true);
  const [importErrorMode, setImportErrorMode] = useState<ImportErrorMode>("NONE");
  const [grants, setGrants] = useState<TeacherGrantRow[]>(INITIAL_TEACHER_GRANTS);
  const [feedbackThread, setFeedbackThread] = useState<TeacherFeedbackItem[]>(INITIAL_TEACHER_FEEDBACK);
  const [archiveModalTarget, setArchiveModalTarget] = useState<TeacherLessonCard | null>(null);
  const [toast, setToast] = useState<{ kind: "ok" | "info" | "warn" | "err"; text: string } | null>(null);

  const showToast = (text: string, kind: "ok" | "info" | "warn" | "err" = "ok") => {
    setToast({ kind, text });
    window.setTimeout(() => setToast(null), 3500);
  };

  const archiveLesson = (id: string) => {
    setLessons((prev) => prev.filter((l) => l.id !== id));
    setArchiveModalTarget(null);
    showToast("Đã lưu trữ phiên bản giáo án.", "info");
  };

  const restoreDefaultLessons = () => {
    setLessons(INITIAL_TEACHER_LESSONS);
    setUi05Mode("NORMAL");
    showToast("Đã khôi phục danh sách giáo án mẫu.", "ok");
  };

  const addRosterChild = (label: string, ageMonths: number) => {
    const years = Math.max(3, Math.floor(ageMonths / 12));
    setRoster((prev) => [
      ...prev,
      {
        id: `roster-${Date.now()}`,
        displayLabel: `${label} · ${years} tuổi`,
        ageMonths,
        ageText: `${ageMonths} tháng`,
        profileShared: false,
        className: "Lớp Mầm 2",
      },
    ]);
    showToast(`Đã thêm ${label} (${ageMonths} tháng tuổi) vào danh sách Lớp Mầm 2.`, "ok");
  };

  const regenerateDeckStep = () => {
    setDeckRevision((r) => r + 1);
    showToast(`Đã tạo lại nét gợi ý Bước ${activeDeckStep} (Bản ${deckRevision + 1}, không trừ lượt tạo video).`, "ok");
  };

  const requestSampleRewrite = () => {
    if (sampleRewriteCount >= 3) {
      showToast("Đã đạt giới hạn 3/3 lần viết lại kịch bản mẫu.", "warn");
      return;
    }
    setSampleRewriteCount((c) => c + 1);
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
    showToast("AI đã cập nhật kịch bản mẫu 5 cảnh. Vui lòng rà soát trước khi xác nhận.", "info");
  };

  const confirmSampleScript = () => {
    setSampleVideoConfirmed(true);
    showToast("Đã xác nhận kịch bản và gửi yêu cầu tạo video mẫu cho buổi học.", "ok");
  };

  const confirmClassroomPresentation = () => {
    setPresentationConfirmed(true);
    showToast("Đã ghi nhận xác nhận trình chiếu video mẫu cho Lớp Mầm 2 (30/10/2026).", "ok");
  };

  const revokeTeacherGrant = (id: string) => {
    setGrants((prev) =>
      prev.map((g) => (g.id === id ? { ...g, status: "Đã thu hồi" } : g))
    );
    showToast("Đã thu hồi quyền chia sẻ.", "info");
  };

  const addLessonGrant = (recipient: string, scope: string) => {
    setGrants((prev) => [
      {
        id: `tg-${Date.now()}`,
        kind: "LESSON",
        recipient,
        scope,
        expiresAt: "30/11/2026",
        status: "Đang hiệu lực",
      },
      ...prev,
    ]);
    showToast("Đã tạo quyền chia sẻ giáo án mới.", "ok");
  };

  const replyToFeedback = (text: string) => {
    if (!text.trim()) return;
    setFeedbackThread((prev) => [
      ...prev,
      {
        id: `tfb-${Date.now()}`,
        sender: "Cô Thảo · Trường Mầm non Ánh Dương",
        text: text.trim(),
        date: "30/10/2026",
      },
    ]);
    showToast("Đã gửi phản hồi của giáo viên cho phụ huynh bé Minh.", "ok");
  };

  return (
    <TeacherContext.Provider
      value={{
        lessons,
        archiveLesson,
        restoreDefaultLessons,
        ui05Mode,
        setUi05Mode,
        roster,
        addRosterChild,
        sketchDeckEnabled,
        setSketchDeckEnabled,
        activeDeckStep,
        setActiveDeckStep,
        deckRevision,
        regenerateDeckStep,
        followLessonDirection,
        setFollowLessonDirection,
        sampleScenes,
        sampleRewriteCount,
        sampleRewriteHint,
        setSampleRewriteHint,
        requestSampleRewrite,
        sampleVideoConfirmed,
        confirmSampleScript,
        presentationConfirmed,
        confirmClassroomPresentation,
        captionsOn,
        setCaptionsOn,
        importErrorMode,
        setImportErrorMode,
        grants,
        revokeTeacherGrant,
        addLessonGrant,
        feedbackThread,
        replyToFeedback,
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
