import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTeacher } from "../context/TeacherContext";
import { TeacherLessonCard } from "../data/mockTeacherData";
import { Icon, IconName } from "../components/Icon";
import { PublicLibraryModal, topicIconName, topicTone } from "../components/PublicLibraryModal";
import {
  detectSketchTheme,
  getStepsForTheme,
  ProgressiveWhiteboardSvg,
  SketchTheme,
} from "../components/SketchWhiteboardArt";
import { IconTile, PageHead, Toggle } from "./T01WorkspaceScreen";

interface DeckActivityItem {
  id: string;
  title: string;
  description: string;
  theme: SketchTheme;
  icon: IconName;
  tone: "" | "is-amber" | "is-mint" | "is-rose";
  stepsCount: number;
}

const DEFAULT_DECK_ACTIVITIES: DeckActivityItem[] = [
  {
    id: "act-butterfly",
    title: "Con bướm mùa xuân",
    description: "Cùng vẽ chú bướm có đôi cánh đối xứng rực rỡ bay quanh vườn trường!",
    theme: "butterfly",
    icon: "palette",
    tone: "is-rose",
    stepsCount: 4,
  },
  {
    id: "act-caterpillar",
    title: "Chú sâu nhỏ trên chiếc lá",
    description: "Vẽ chiếc lá xanh lớn và chú sâu mũm mĩm đang bò tìm thức ăn.",
    theme: "caterpillar",
    icon: "leaf",
    tone: "is-mint",
    stepsCount: 4,
  },
  {
    id: "act-flower",
    title: "Bông hoa hướng dương đón nắng",
    description: "Vẽ nhụy hoa tròn ở giữa và những cánh hoa xòe đều quanh ánh mặt trời.",
    theme: "flower",
    icon: "star",
    tone: "is-amber",
    stepsCount: 4,
  },
  {
    id: "act-tree",
    title: "Cây xanh sân trường",
    description: "Vẽ thân cây vững chãi, hai nhánh cành vươn cao và tán lá xanh mát.",
    theme: "tree",
    icon: "leaf",
    tone: "is-mint",
    stepsCount: 4,
  },
];

function buildActivitiesFromLesson(lesson: TeacherLessonCard | undefined): DeckActivityItem[] {
  if (!lesson || lesson.activities.length === 0) return DEFAULT_DECK_ACTIVITIES;
  const fromLesson: DeckActivityItem[] = lesson.activities.map((raw, idx) => {
    const cleanTitle = raw.replace(/^Hoạt động \d+\s*:\s*/i, "").trim() || raw;
    const theme = detectSketchTheme(`${cleanTitle} ${lesson.topic}`);
    return {
      id: `${lesson.id}-act-${idx}`,
      title: cleanTitle,
      description: `Hoạt động #${idx + 1} thuộc giáo án "${lesson.title}" (${lesson.ageBand}).`,
      theme,
      icon: topicIconName(cleanTitle + " " + lesson.topic),
      tone: topicTone(cleanTitle + " " + lesson.topic),
      stepsCount: 4,
    };
  });
  return fromLesson.length >= 2 ? fromLesson : [...fromLesson, ...DEFAULT_DECK_ACTIVITIES.slice(0, 2)];
}

export function T04SessionSketchDeckPage() {
  const navigate = useNavigate();
  const {
    assignedClasses,
    activeClassId,
    lessons,
    publicTemplates,
    pinnedLessonTitle,
    setPinnedLessonTitle,
    setPinnedActivities,
    useLessonForOccurrence,
    sketchDeckEnabled,
    setSketchDeckEnabled,
    deckJobStatus,
    activeDeckStep,
    setActiveDeckStep,
    skippedSteps,
    toggleSkipDeckStep,
    deckRevision,
    regenerateDeckStep,
    setSelectedSampleActivity,
    showToast,
  } = useTeacher();

  const [stageView, setStageView] = useState<"select" | "present">("select");
  const [selectedActivityId, setSelectedActivityId] = useState<string>("");
  const [ageBandDeck, setAgeBandDeck] = useState("4–5 tuổi (48–59 tháng)");
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);

  const cls = assignedClasses.find((c) => c.id === activeClassId) || assignedClasses[0];

  const allSelectableLessons = useMemo(() => {
    const map = new Map<string, TeacherLessonCard>();
    lessons.forEach((l) => map.set(l.title, l));
    publicTemplates.forEach((t) => {
      if (!map.has(t.title)) map.set(t.title, t);
    });
    return Array.from(map.values());
  }, [lessons, publicTemplates]);

  const currentLesson =
    allSelectableLessons.find((l) => l.title === pinnedLessonTitle) || allSelectableLessons[0];

  const activities = useMemo(
    () => buildActivitiesFromLesson(currentLesson),
    [currentLesson]
  );

  const currentActivity =
    activities.find((a) => a.id === selectedActivityId) || activities[0];

  const stepList = useMemo(
    () => getStepsForTheme(currentActivity.theme),
    [currentActivity.theme]
  );

  const safeStepNum = Math.min(Math.max(activeDeckStep, 1), stepList.length);
  const currentStepMeta = stepList[safeStepNum - 1] || stepList[0];
  const isCurrentSkipped = skippedSteps.includes(safeStepNum);
  const stale = deckJobStatus === "STALE";

  useEffect(() => {
    if (!fullscreen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setFullscreen(false);
      else if (e.key === "ArrowRight") setActiveDeckStep(Math.min(4, safeStepNum + 1));
      else if (e.key === "ArrowLeft") setActiveDeckStep(Math.max(1, safeStepNum - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [fullscreen, safeStepNum, setActiveDeckStep]);

  const handleOpenActivity = (act: DeckActivityItem) => {
    setSelectedActivityId(act.id);
    setSelectedSampleActivity(act.title);
    setActiveDeckStep(1);
    setStageView("present");
  };

  const handleSelectLibraryTemplate = (tpl: TeacherLessonCard) => {
    setPinnedLessonTitle(tpl.title);
    setPinnedActivities(tpl.activities);
    setAgeBandDeck(tpl.ageBand);
    setSelectedActivityId("");
    setStageView("select");
    setLibraryOpen(false);
    showToast(`Đã nạp mẫu "${tpl.title}" vào AI Assisted!`, "ok");
  };

  /* ── Screen Mode B: Màn hình lớn từng bước vẽ riêng biệt (16:9 Whiteboard Stage) ── */
  if (stageView === "present" && sketchDeckEnabled) {
    const stageContent = (
      <div className="tw-stage-wrap" style={fullscreen ? { maxWidth: 1120 } : undefined}>
        {/* Thanh điều khiển phía trên: Chọn hoạt động khác + Tên hoạt động + Chấm Bước 1..4 + Toàn màn hình */}
        <div
          className={fullscreen ? "tw-row tw-between tw-wrap" : "tw-card tw-row tw-between tw-wrap"}
          style={fullscreen ? { padding: "4px 0" } : { padding: "14px 20px" }}
        >
          <div className="tw-row tw-wrap" style={{ gap: 12 }}>
            <button
              type="button"
              className="tw-btn is-ghost is-sm"
              onClick={() => {
                setFullscreen(false);
                setStageView("select");
              }}
            >
              <Icon name="arrow-left" size={16} /> Chọn hoạt động khác
            </button>
            <div>
              <h1
                style={{
                  margin: 0,
                  fontSize: 22,
                  fontWeight: 800,
                  color: fullscreen ? "#F6F7F9" : undefined,
                }}
              >
                {currentActivity.title}
              </h1>
              <div
                className="tw-meta"
                style={{ fontSize: 13, color: fullscreen ? "#B9C0CC" : undefined }}
              >
                Giáo án: {currentLesson?.title} · {cls.className} · Bản vẽ #{deckRevision}
              </div>
            </div>
          </div>

          <div className="tw-row tw-wrap" role="tablist" aria-label="Các bước vẽ trên bảng">
            {stepList.map((st) => {
              const active = st.step === safeStepNum;
              const skipped = skippedSteps.includes(st.step);
              return (
                <button
                  key={st.step}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  className={
                    "tw-step-dot" +
                    (active ? " is-on" : "") +
                    (skipped ? " is-skipped" : "")
                  }
                  onClick={() => setActiveDeckStep(st.step)}
                >
                  <b>{st.step}</b> Bước {st.step}
                </button>
              );
            })}
          </div>

          <button
            type="button"
            className={fullscreen ? "tw-btn is-amber is-sm" : "tw-btn is-ghost is-sm"}
            onClick={() => setFullscreen((f) => !f)}
          >
            <Icon name={fullscreen ? "minimize" : "maximize"} size={16} />{" "}
            {fullscreen ? "Thu nhỏ" : "Toàn màn hình"}
          </button>
        </div>

        {stale && (
          <div className="tw-card is-amber tw-row tw-between tw-wrap">
            <div className="tw-row">
              <IconTile name="alert" tone="is-amber" />
              <strong>
                Giáo án vừa cập nhật nên bộ nét vẽ cũ chuyển sang trạng thái STALE. Nhấn làm mới để đồng bộ!
              </strong>
            </div>
            <button type="button" className="tw-btn is-amber is-sm" onClick={regenerateDeckStep}>
              <Icon name="refresh" size={16} /> Làm mới bảng vẽ
            </button>
          </div>
        )}

        {/* Khung bảng trắng 16:9 khổng lồ cho lớp học + Hướng dẫn chữ to rõ ràng */}
        <div
          className={fullscreen ? "" : "tw-card"}
          style={
            fullscreen
              ? { display: "flex", flexDirection: "column", gap: 16 }
              : { display: "flex", flexDirection: "column", gap: 18, padding: 24 }
          }
        >
          <div
            className="tw-whiteboard-frame"
            style={{ opacity: isCurrentSkipped ? 0.45 : 1, position: "relative" }}
          >
            <ProgressiveWhiteboardSvg theme={currentActivity.theme} stepNum={safeStepNum} />
            {isCurrentSkipped && (
              <span
                className="tw-chip is-amber"
                style={{ position: "absolute", top: 16, right: 16, fontSize: 14 }}
              >
                Bước này đang tạm ẩn khi chiếu
              </span>
            )}
          </div>

          <div
            className={fullscreen ? "" : "tw-item is-sky"}
            style={
              fullscreen
                ? {
                    background: "#16233A",
                    padding: "18px 22px",
                    borderRadius: 18,
                    color: "#F6F7F9",
                  }
                : { padding: "18px 22px", borderRadius: 18 }
            }
          >
            <div className="tw-row tw-between tw-wrap">
              <h2
                style={{
                  margin: 0,
                  fontSize: 24,
                  fontWeight: 800,
                  color: fullscreen ? "#F6F7F9" : undefined,
                }}
              >
                {currentStepMeta.title}
              </h2>
              <span className="tw-chip is-mint">
                Bước {safeStepNum} / {stepList.length} · Bảng 16:9
              </span>
            </div>
            <p
              style={{
                fontSize: 17,
                lineHeight: 1.55,
                marginTop: 8,
                color: fullscreen ? "#CBD0D8" : undefined,
              }}
            >
              {currentStepMeta.instruction}
            </p>
          </div>

          {/* Thanh điều hướng bước lớn phía dưới */}
          <div className="tw-row tw-between tw-wrap" style={{ gap: 12 }}>
            <button
              type="button"
              className="tw-btn is-ghost is-lg"
              disabled={safeStepNum <= 1}
              onClick={() => setActiveDeckStep(Math.max(1, safeStepNum - 1))}
            >
              <Icon name="arrow-left" size={20} /> Bước trước
            </button>

            <div className="tw-row tw-wrap" style={{ gap: 10 }}>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={regenerateDeckStep}
              >
                <Icon name="refresh" size={16} /> Tạo lại bước này bằng AI
              </button>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={() => toggleSkipDeckStep(safeStepNum)}
              >
                <Icon name={isCurrentSkipped ? "eye" : "eye-off"} size={16} />{" "}
                {isCurrentSkipped ? "Hiện lại bước này" : "Ẩn bước này"}
              </button>
            </div>

            {safeStepNum < stepList.length ? (
              <button
                type="button"
                className="tw-btn is-lg"
                onClick={() => setActiveDeckStep(safeStepNum + 1)}
              >
                Bước tiếp theo <Icon name="arrow-right" size={20} />
              </button>
            ) : (
              <button
                type="button"
                className="tw-btn is-mint is-lg"
                onClick={() => {
                  setFullscreen(false);
                  showToast("Đã hoàn tất hướng dẫn vẽ cho lớp! Chuyển sang tạo video mẫu.", "ok");
                  navigate("/t06-sample-story-run");
                }}
              >
                Hoàn tất bài vẽ · Sang Tạo video mẫu <Icon name="arrow-right" size={20} />
              </button>
            )}
          </div>
        </div>
      </div>
    );

    if (fullscreen) {
      return <div className="tw-fullscreen-stage">{stageContent}</div>;
    }

    return <div className="tw-page">{stageContent}</div>;
  }

  /* ── Screen Mode A: Chọn giáo án & Chọn hoạt động (Spacious 2-Column Activity Cards) ── */
  return (
    <div className="tw-page">
      <PageHead
        title="AI Assisted · Bảng vẽ từng bước (16:9)"
        hint="Chọn giáo án hoặc mẫu công khai, rồi mở hoạt động để chiếu từng bước vẽ 16:9 cho cả lớp (Không trừ quota · BR-43,&nbsp;BR-44)."
        right={
          <button
            type="button"
            className="tw-btn is-ghost"
            onClick={() => setLibraryOpen(true)}
          >
            <Icon name="star" size={18} /> Chọn mẫu từ Thư viện công khai
          </button>
        }
      />

      {/* Thanh chọn Giáo án, Độ tuổi & Opt-in Toggle */}
      <div className="tw-card is-sky" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="tw-grid-3" style={{ alignItems: "end" }}>
          <label className="tw-label">
            Giáo án đang dùng cho buổi học
            <select
              className="tw-input"
              value={currentLesson?.id ?? ""}
              onChange={(e) => {
                const chosen = allSelectableLessons.find((l) => l.id === e.target.value);
                if (chosen) {
                  useLessonForOccurrence(chosen.id);
                  setAgeBandDeck(chosen.ageBand);
                  setSelectedActivityId("");
                }
              }}
            >
              {allSelectableLessons.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.title} ({l.version} · {l.topic})
                </option>
              ))}
            </select>
          </label>

          <label className="tw-label">
            Độ tuổi mục tiêu của lớp
            <select
              className="tw-input"
              value={ageBandDeck}
              onChange={(e) => setAgeBandDeck(e.target.value)}
            >
              <option>3–4 tuổi (36–47 tháng)</option>
              <option>4–5 tuổi (48–59 tháng)</option>
              <option>5–6 tuổi (60–83 tháng)</option>
              <option>7–8 tuổi (84–107 tháng)</option>
            </select>
          </label>

          <div className="tw-item tw-row tw-between" style={{ padding: "11px 16px" }}>
            <div>
              <div className="tw-strong" style={{ fontSize: 14 }}>
                Bật AI Sketch Deck (BR-43)
              </div>
              <div className="tw-meta" style={{ fontSize: 12.5 }}>
                Tùy chọn trình chiếu 16:9
              </div>
            </div>
            <Toggle
              on={sketchDeckEnabled}
              onChange={setSketchDeckEnabled}
              label="Bật AI Sketch Deck 16:9"
            />
          </div>
        </div>
      </div>

      {sketchDeckEnabled ? (
        <>
          <div className="tw-row tw-between tw-wrap">
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800 }}>
              Chọn hoạt động để mở bảng vẽ từng bước ({activities.length} hoạt động)
            </h2>
            <span className="tw-chip is-mint">
              Nhấn vào hoạt động để mở màn hình trình chiếu lớn ở Bước 1
            </span>
          </div>

          <div className="tw-grid-2">
            {activities.map((act, idx) => (
              <div
                key={act.id}
                className="tw-card is-lift"
                role="button"
                tabIndex={0}
                onClick={() => handleOpenActivity(act)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleOpenActivity(act);
                  }
                }}
                style={{ display: "flex", flexDirection: "column", gap: 14, padding: 24 }}
              >
                <div className="tw-row tw-between" style={{ alignItems: "flex-start", gap: 14 }}>
                  <div className="tw-row" style={{ gap: 14, flex: 1, minWidth: 0, alignItems: "flex-start" }}>
                    <span
                      className={`tw-ico ${act.tone}`}
                      style={{ width: 52, height: 52, borderRadius: 16 }}
                      aria-hidden="true"
                    >
                      <Icon name={act.icon} size={24} />
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, lineHeight: 1.3 }}>
                        {act.title.replace(/\s+(\S+)$/, "\u00A0$1")}
                      </h3>
                      <div className="tw-meta" style={{ fontSize: 13.5, marginTop: 3 }}>
                        Hoạt động {idx + 1} · {ageBandDeck}
                      </div>
                    </div>
                  </div>
                  <span className="tw-chip is-mint">{act.stepsCount} bước vẽ</span>
                </div>

                <p style={{ fontSize: 15, lineHeight: 1.55 }}>{act.description}</p>

                <div className="tw-row tw-between tw-wrap" style={{ marginTop: "auto", paddingTop: 6 }}>
                  <span className="tw-chip is-gray">Bảng trắng 16:9 · Nét đen rõ nét</span>
                  <span className="tw-btn is-sm">
                    Mở Bước 1 <Icon name="arrow-right" size={16} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="tw-card is-amber tw-row tw-between tw-wrap">
          <div className="tw-row">
            <IconTile name="palette" tone="is-amber" />
            <div>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>
                AI Sketch Deck đang tắt (Opt-In · BR-43)
              </h2>
              <p className="tw-meta" style={{ marginTop: 2 }}>
                Cô vẫn có thể hướng dẫn trẻ vẽ trực tiếp trên bảng lớp và chuyển sang bước Tạo video mẫu.
              </p>
            </div>
          </div>
          <button
            type="button"
            className="tw-btn is-amber is-sm"
            onClick={() => setSketchDeckEnabled(true)}
          >
            Bật lại AI Sketch Deck
          </button>
        </div>
      )}

      <div className="tw-row tw-between tw-wrap">
        <button
          type="button"
          className="tw-btn is-ghost"
          onClick={() => navigate("/t02-lesson-authoring")}
        >
          <Icon name="arrow-left" size={16} /> Quay lại Quản lý giáo án
        </button>
        <button
          type="button"
          className="tw-btn"
          onClick={() => navigate("/t06-sample-story-run")}
        >
          <Icon name="video" size={18} /> Sang Tạo video mẫu cho lớp
        </button>
      </div>

      <PublicLibraryModal
        open={libraryOpen}
        onClose={() => setLibraryOpen(false)}
        templates={publicTemplates}
        onSelectTemplate={handleSelectLibraryTemplate}
        primaryActionLabel="Dùng mẫu này cho AI Assisted"
      />
    </div>
  );
}
