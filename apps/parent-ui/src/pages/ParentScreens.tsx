import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { VideoJobMode, useParent } from "../context/ParentContext";
import {
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  hasFirebaseAuthBridge,
  isLocalPreview,
  signInAndResolveRole,
  type AccessGrant,
  type ParentLessonDetail,
  type ParentLessonSummary,
} from "../../../shared/backendApi";
import { Icon, IconBadge } from "../components/Icon";
import { Accordion, AccordionContent, AccordionHeader, AccordionItem, AccordionTrigger } from "../../../shared/ui";
import {
  Btn,
  ChildAvatarSvg,
  GRADS,
  Note,
  ParentAvatarSvg,
  Progress,
  Soft,
  StepChips,
  Switch,
  TopBar,
  Waveform,
  Wordmark,
} from "../components/Kit";

/* ---------- helpers ---------- */
const AGE_BANDS = [
  { key: "3-4", months: 42, title: "3 – 4 tuổi" },
  { key: "5-6", months: 60, title: "5 – 6 tuổi" },
  { key: "7-8", months: 90, title: "7 – 8 tuổi" },
  { key: "9+", months: 114, title: "9+ tuổi" },
];

function subjectIcon(s: string) {
  const t = s.toLowerCase();
  if (t.includes("bướm")) return "sparkle";
  if (t.includes("cây") || t.includes("cỏ") || t.includes("hoa")) return "leaf";
  if (t.includes("mèo") || t.includes("người")) return "user";
  if (t.includes("cá")) return "image";
  if (t.includes("nhà")) return "home";
  return "palette";
}

function storyArtSrc(subject: string) {
  const value = subject.toLowerCase();
  if (value.includes("bướm") || value.includes("butterfly")) return "/illustrations/child-story-hero.webp";
  if (value.includes("cây") || value.includes("tree")) return "/illustrations/garden-discovery.webp";
  return "/illustrations/kite-ai-guide.webp";
}

function lessonPointIcon(title: string) {
  const value = title.toLowerCase();
  if (value.includes("trứng") || value.includes("mầm")) return "sparkle";
  if (value.includes("cánh") || value.includes("bướm")) return "star";
  if (value.includes("cây") || value.includes("lá") || value.includes("kén") || value.includes("thân")) return "leaf";
  return "sun";
}

function DrawingGuideIllustration({
  kind,
  stepIndex,
  enabled,
}: {
  kind: "butterfly" | "tree";
  stepIndex: number;
  enabled: boolean;
}) {
  const stage = Math.min(3, Math.max(0, stepIndex));
  const artTransform = kind === "butterfly" && stage < 2
    ? "translate(-30 0) scale(1.25)"
    : kind === "tree"
      ? "translate(-10 -7) scale(1.1)"
      : undefined;
  return (
    <svg className={`drawing-guide-svg ${enabled ? "" : "is-muted"}`} viewBox="0 0 320 220" aria-hidden="true">
      <path d="M24 190c42-12 79-14 119-7 42 7 94 7 153-5" fill="none" stroke="#d7e9c7" strokeWidth="3" strokeLinecap="round" />
      <g transform={artTransform}>
        {kind === "butterfly" ? (
        <>
          <path d="M45 153c38 4 69-2 97-23" fill="none" stroke="#79a96b" strokeWidth="5" strokeLinecap="round" />
          <path d="M84 145c-5-26-23-34-43-28 8 21 21 29 43 28Z" fill="#cbe9c2" stroke="#79a96b" strokeWidth="2.5" />
          <path d="M84 144c-12-11-23-18-36-22" fill="none" stroke="#79a96b" strokeWidth="2" strokeLinecap="round" />
          {stage >= 0 && <ellipse cx="113" cy="130" rx="7" ry="9" fill="#ffd66b" stroke="#e8ad37" strokeWidth="2" />}
          {stage >= 1 && (
            <g stroke="#b96f50" strokeWidth="2">
              <circle cx="147" cy="145" r="10" fill="#f8b77f" />
              <circle cx="163" cy="141" r="10" fill="#f6a96e" />
              <circle cx="179" cy="137" r="9" fill="#f5a267" />
              <circle cx="191" cy="133" r="7" fill="#ef9a63" />
              <circle cx="194" cy="131" r="1.4" fill="#17233b" stroke="none" />
              <path d="M190 125c-3-7-7-8-10-8M198 125c1-7 5-9 8-10" fill="none" strokeLinecap="round" />
            </g>
          )}
          {stage >= 2 && (
            <g>
              <path d="M231 66c-4 9-3 22 2 28 5-5 8-17 4-27Z" fill="#91c98e" stroke="#548766" strokeWidth="2.5" />
              <path d="M230 71l8 17M238 71l-6 16" fill="none" stroke="#548766" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M236 60c0-9-5-15-12-17M238 59c5-9 11-11 17-10" fill="none" stroke="#79a96b" strokeWidth="2.5" strokeLinecap="round" />
            </g>
          )}
          {stage >= 3 && (
            <g stroke="#315eab" strokeWidth="2.5">
              <ellipse cx="264" cy="90" rx="16" ry="22" transform="rotate(-30 264 90)" fill="#7bd5e9" />
              <ellipse cx="291" cy="90" rx="16" ry="22" transform="rotate(30 291 90)" fill="#f5bd62" />
              <ellipse cx="266" cy="116" rx="12" ry="15" transform="rotate(25 266 116)" fill="#f5a4b9" />
              <ellipse cx="289" cy="116" rx="12" ry="15" transform="rotate(-25 289 116)" fill="#b8a1ee" />
              <path d="M277 85v41M277 86c-5-8-10-9-14-9M278 86c5-8 10-9 14-9" fill="none" stroke="#604a77" strokeWidth="3" strokeLinecap="round" />
              <circle cx="277" cy="83" r="5" fill="#f5bd62" />
            </g>
          )}
        </>
      ) : (
        <>
          <path d="M54 184c52-5 108-5 212 0" fill="none" stroke="#79a96b" strokeWidth="4" strokeLinecap="round" />
          <ellipse cx="157" cy="180" rx="12" ry="7" fill="#d8b077" stroke="#a9804f" strokeWidth="2" />
          {stage >= 1 && <path d="M148 178c2-29 2-48 0-72h20c-2 24-1 47 4 72Z" fill="#c98c58" stroke="#9a6847" strokeWidth="3" strokeLinejoin="round" />}
          {stage >= 2 && (
            <g stroke="#5e9b68" strokeWidth="3">
              <circle cx="147" cy="82" r="35" fill="#bfe4ae" />
              <circle cx="119" cy="95" r="24" fill="#d4edba" />
              <circle cx="176" cy="98" r="26" fill="#a9d69e" />
              <circle cx="158" cy="59" r="22" fill="#d3edb8" />
            </g>
          )}
          {stage >= 3 && (
            <g>
              <circle cx="132" cy="88" r="5" fill="#f4c84e" />
              <circle cx="169" cy="71" r="5" fill="#f4c84e" />
              <circle cx="181" cy="103" r="5" fill="#f4c84e" />
              <path d="M128 88h8M132 84v8M165 71h8M169 67v8M177 103h8M181 99v8" stroke="#e4a832" strokeWidth="2" strokeLinecap="round" />
              <path d="M151 126c-12-11-22-9-25 3 12 3 20 2 25-3ZM169 143c11-12 21-11 25 1-11 4-19 4-25-1Z" fill="#dcf0cf" stroke="#72a56c" strokeWidth="2" />
            </g>
          )}
        </>
        )}
      </g>
    </svg>
  );
}

function cleanTitle(t: string) {
  return t.replace(/\s*\(.*\)\s*$/, "");
}

function compactAgeLabel(ageMonths: number) {
  const years = Math.floor(ageMonths / 12);
  return years > 0 ? `${years} tuổi` : `${ageMonths} tháng`;
}

function useLocState<T extends Record<string, unknown>>(): Partial<T> {
  const loc = useLocation();
  return ((loc.state as Partial<T> | null) ?? {}) as Partial<T>;
}

const HOME_FAQ_ITEMS = [
  {
    q: "Cách tạo câu chuyện mới nhanh nhất như thế nào?",
    a: "Trên Trang chủ, bố mẹ bấm «Tạo câu chuyện mới · Chụp tranh ngay» để chụp trực tiếp bức vẽ của bé. AI sẽ tự nhận diện nhân vật, nhận ý tưởng giọng nói/văn bản, gợi ý hoạt động đi kèm và tạo kịch bản 5 cảnh để bố mẹ duyệt trước khi dựng video.",
  },
  {
    q: "Bước chọn chủ đề và hướng dẫn vẽ có bắt buộc không?",
    a: "Không bắt buộc. Hai bước này hoàn toàn là tùy chọn dành cho trường hợp bé chưa biết vẽ gì và muốn xem gợi ý 3–5 nét vẽ cơ bản trước khi bắt đầu.",
  },
  {
    q: "Video được tạo trong bao lâu và xem ngang được không?",
    a: "Quá trình dựng phim AI 720p, lồng tiếng Việt, tạo phụ đề và kiểm tra an toàn thường mất khoảng 1–2 phút. Khi xem, bố mẹ có thể bấm «Xoay ngang / Toàn màn hình» để mở chế độ rạp chiếu 16:9 cho bé.",
  },
  {
    q: "Tôi có thể chỉnh sửa kịch bản hoặc tạo lại video không?",
    a: "Trước khi tạo video, bố mẹ có thể dùng AI viết lại kịch bản tối đa 3 lần. Nếu video chưa phù hợp, hãy báo cáo và tạo lại tối đa 2 lần trong phiên.",
  },
  {
    q: "Thông tin riêng tư của bé được bảo vệ ra sao?",
    a: "Tài khoản Phụ huynh tách biệt với Trường học. Tên thật và ghi chú hỗ trợ của bé được tự động loại khỏi nội dung gửi tới AI.",
  },
];

/* =====================================================================
   P01 · Trang chủ + Chọn chủ đề tùy chọn + FAQ cuối trang
   ===================================================================== */
export function P01LessonLibraryPage() {
  const nav = useNavigate();
  const st = useLocState<{ view: string }>();
  const [view, setView] = useState<"home" | "topics">(st.view === "topics" ? "topics" : "home");
  const [tag, setTag] = useState("Tất cả");
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [faqExpanded, setFaqExpanded] = useState(false);
  const {
    profiles,
    selectedProfileId,
    setSelectedProfileId,
    lessons,
    setSelectedLessonId,
    selectedLessonId,
    setSelectedActivityId,
    libraryState,
    setLibraryState,
    setSkippedOptionalSetup,
    setGuideTopic,
    runHistory,
    quotaRemaining,
    notifications,
    setActiveSheet,
    hasActiveRun,
    videoJobMode,
    showToast,
  } = useParent();

  const activeProfiles = profiles.filter((p) => !p.archived && p.deletionStatus !== "DELETED");
  const activeChild = activeProfiles.find((p) => p.id === selectedProfileId) ?? activeProfiles[0] ?? profiles[0];
  const unread = notifications.filter((n) => n.unread).length;
  const tags = ["Tất cả", ...Array.from(new Set(lessons.flatMap((l) => l.tags)))];
  const shown = lessons.filter((l) => tag === "Tất cả" || l.tags.includes(tag));
  const todayLesson = lessons.find((l) => l.id === selectedLessonId) ?? lessons[0];
  const todayAct = todayLesson?.outdoorActivities[0];
  const recent = runHistory.filter((r) => r.lifecycleState !== "DELETED");

  if (!isLocalPreview()) return <ParentApiLibraryPage />;

  if (view === "topics") {
    return (
      <div className="page">
        <TopBar
          title="Chọn chủ đề (Tùy chọn)"
          onBack={() => setView("home")}
          right={
            <button
              type="button"
              className="ghost-link"
              onClick={() => {
                setSkippedOptionalSetup(true);
                nav("/p04-capture-subject-confirmation");
              }}
            >
              Bỏ qua
            </button>
          }
        />
        <StepChips current={1} />
        <h1 className="h1">Gợi ý chủ đề cho bé</h1>
        <p className="sub">Bước này là tùy chọn. Nếu bé đã có sẵn tranh vẽ, bố mẹ có thể vào thẳng bước chụp ảnh.</p>

        <Soft
          onClick={() => {
            setSkippedOptionalSetup(true);
            nav("/p04-capture-subject-confirmation");
          }}
        >
          <Icon name="camera" size={18} /> Bỏ qua · Chụp tranh ngay
        </Soft>

        <div className="row wrap">
          {tags.map((t) => (
            <button key={t} type="button" className={`chip ${tag === t ? "on" : "line"}`} onClick={() => setTag(t)}>
              {t}
            </button>
          ))}
        </div>
        {libraryState === "LOADING" && (
          <div className="card row" style={{ justifyContent: "center", padding: 28 }}>
            <IconBadge name="palette" tone="primary" />
            <span className="sub">Đang mở hộp màu…</span>
          </div>
        )}
        {libraryState === "EMPTY" && (
          <div className="card stack" style={{ alignItems: "center", textAlign: "center" }}>
            <IconBadge name="folder" tone="neutral" size={52} />
            <p className="sub">Chưa có chủ đề nào. Hãy tải lại để lấy bài mới.</p>
            <Soft small onClick={() => setLibraryState("NORMAL")}>Tải lại</Soft>
          </div>
        )}
        {libraryState === "STALE_409" && (
          <Note tone="amber" icon="refresh">
            Danh sách đã cũ.{" "}
            <button type="button" className="ghost-link" onClick={() => setLibraryState("NORMAL")}>Làm mới</button>
          </Note>
        )}
        {libraryState === "FORBIDDEN_403" && (
          <Note tone="red" icon="lock">Tài khoản chưa được xem các bài này. Hãy nhờ cô giáo chia sẻ lại.</Note>
        )}
        {libraryState === "NORMAL" && (
          <div className="topic-grid">
            {shown.map((l, i) => (
              <button
                key={l.id}
                type="button"
                className={`topic ${l.id === selectedLessonId ? "on" : ""}`}
                onClick={() => {
                  setSelectedLessonId(l.id);
                  setGuideTopic(l.topic);
                  setSkippedOptionalSetup(false);
                  nav("/p02-lesson-detail");
                }}
              >
                <span className={`cov ${GRADS[i % GRADS.length]}`}><img src={l.coverKind === "butterfly" ? "/child-butterfly-art.png" : "/illustrations/garden-discovery.webp"} alt="" loading="lazy" /></span>
                <span className="h3">{l.title}</span>
                <span className="chip amber">{l.topic}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="page">
      <div className="topbar">
        <div className="row">
          <span className="avatar sm" style={{ overflow: "hidden" }}>
            <ParentAvatarSvg size={36} />
          </span>
          <div>
            <h1 className="h2">Chào chị Lan!</h1>
          </div>
        </div>
        <button type="button" className="round-btn" aria-label="Thông báo" onClick={() => setActiveSheet("NOTIFICATIONS")}>
          <Icon name="bell" size={20} />
          {unread > 0 && <span className="dot">{unread}</span>}
        </button>
      </div>

      {/* Compact 1-tap active child selector bar */}
      <div className="child-bar" role="region" aria-label="Hồ sơ bé đang chọn">
        <div className="child-pills">
          {activeProfiles.map((p, idx) => {
            const on = activeChild?.id === p.id;
            const yrs = Math.max(3, Math.floor(p.ageMonths / 12));
            return (
              <button
                key={p.id}
                type="button"
                className={`child-pill ${on ? "on" : ""}`}
                aria-pressed={on}
                onClick={() => setSelectedProfileId(p.id)}
              >
                <ChildAvatarSvg variant={idx} size={22} />
                <span>{p.displayName} · {yrs}t</span>
              </button>
            );
          })}
        </div>
        <button type="button" className="ghost-link" style={{ padding: "4px 6px", fontSize: 12 }} onClick={() => nav("/p13-settings#child-profiles")}>
          Hồ sơ →
        </button>
      </div>

      {/* Primary Hero CTA: Straight to P04 Capture */}
      <button
        type="button"
        className="hero-create"
        onClick={() => {
          if (quotaRemaining <= 0) {
            showToast("Bạn đã hết lượt tạo video. Bạn vẫn có thể chụp tranh và mua thêm lượt sau.", "warn");
          }
          setSkippedOptionalSetup(true);
          nav("/p04-capture-subject-confirmation");
        }}
      >
        <span className="plus"><Icon name="camera" size={26} strokeWidth={2.4} /></span>
        <span className="grow">
          <span className="t" style={{ display: "block" }}>Tạo câu chuyện mới</span>
          <span className="s" style={{ display: "block" }}>Chụp tranh để bắt đầu</span>
        </span>
        <img className="hero-kite" src="/illustrations/child-story-hero.webp" alt="" aria-hidden="true" />
      </button>

      {/* Secondary Optional Entry: Topic & Drawing Guide */}
      <Soft
        onClick={() => {
          setSkippedOptionalSetup(false);
          setView("topics");
        }}
      >
        <Icon name="palette" size={17} /> Gợi ý vẽ
        <span className="chip line" style={{ marginLeft: "auto" }}>Tùy chọn</span>
      </Soft>

      {hasActiveRun && videoJobMode !== "DELETED" && videoJobMode !== "DELETE_PENDING" && (
        <button
          type="button"
          className="act-row"
          onClick={() => nav(videoJobMode === "READY" ? "/p08-video-and-activities" : "/p07-video-job-status")}
        >
          <IconBadge name="video" tone="mint" size={44} />
          <span className="grow">
            <span className="h3" style={{ display: "block" }}>Câu chuyện đang thực hiện</span>
            <span className="tiny" style={{ display: "block" }}>{videoJobMode === "READY" ? "Video đã sẵn sàng phát" : "Đang dựng video AI"}</span>
          </span>
          <Icon name="arrow-right" size={18} />
        </button>
      )}

      <div className="sec-head">
        <h2 className="h2">Câu chuyện gần đây</h2>
        <button type="button" className="more" onClick={() => nav("/p09-history-feedback")}>Xem tất cả</button>
      </div>
      <div className="hscroll">
        {recent.slice(0, 2).map((r, i) => (
          <button
            key={r.id}
            type="button"
            className="story-card"
            onClick={() =>
              nav(
                r.lifecycleState === "COMPLETED" || r.lifecycleState === "VIDEO_READY_144H"
                  ? "/p08-video-and-activities"
                  : "/p09-history-feedback"
              )
            }
          >
            <span className={`thumb ${GRADS[i % GRADS.length]}`}>
              <img src={i === 0 ? "/child-butterfly-art.png" : "/illustrations/garden-discovery.webp"} alt="" loading="lazy" />
              <span className="pl"><Icon name="play" size={14} fill="#fff" /></span>
            </span>
            <span className="meta" style={{ display: "block" }}>
              <span className="h3" style={{ display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {cleanTitle(r.title)}
              </span>
              <span className="tiny" style={{ display: "block" }}>{r.date}</span>
            </span>
          </button>
        ))}
        {recent.length === 0 && (
          <div className="card sub" style={{ gridColumn: "1 / -1" }}>
            Chưa có câu chuyện nào. Hãy chụp bức vẽ đầu tiên của bé!
          </div>
        )}
      </div>

      {todayAct && (
        <>
          <h2 className="h2">Gợi ý hoạt động</h2>
          <button
            type="button"
            className="act-row"
            onClick={() => {
              setSelectedActivityId(todayAct.id);
              nav("/p08b-outdoor-activity");
            }}
          >
            <IconBadge name="sun" tone="accent" size={44} />
            <span className="grow">
              <span className="h3" style={{ display: "block" }}>{todayAct.title}</span>
            </span>
            <Icon name="arrow-right" size={18} />
          </button>
        </>
      )}

      {/* FAQ remains at the bottom of Home and opens only when requested. */}
      <section className="s2l-help-card" aria-label="Trợ giúp">
        <Accordion
          type="single"
          collapsible
          value={faqExpanded ? "help" : ""}
          onValueChange={(value) => setFaqExpanded(value === "help")}
        >
          <AccordionItem value="help" className="s2l-accordion-item">
            <AccordionHeader>
              <AccordionTrigger className="s2l-accordion-trigger s2l-help-trigger">
                <span className="s2l-help-heading">
                  <span>Trợ giúp</span>
                  <span className="s2l-help-count">{HOME_FAQ_ITEMS.length} câu hỏi</span>
                </span>
                <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="m5 7.5 5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </AccordionTrigger>
            </AccordionHeader>
            <AccordionContent className="s2l-accordion-content s2l-help-content">
              <div>
                <Accordion type="single" collapsible value={openFaq === null ? "" : String(openFaq)} onValueChange={(value) => setOpenFaq(value === "" ? null : Number(value))}>
                  {HOME_FAQ_ITEMS.map((item, idx) => (
                    <AccordionItem key={item.q} value={String(idx)} className="s2l-accordion-item">
                      <AccordionHeader>
                        <AccordionTrigger className="s2l-accordion-trigger">
                          <span>{item.q}</span>
                          <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="m5 7.5 5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
                        </AccordionTrigger>
                      </AccordionHeader>
                      <AccordionContent className="s2l-accordion-content"><div>{item.a}</div></AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </section>
    </div>
  );
}

function ParentApiLibraryPage() {
  const nav = useNavigate();
  const { setSelectedLessonId } = useParent();
  const [lessons, setLessons] = useState<ParentLessonSummary[]>([]);
  const [invitations, setInvitations] = useState<AccessGrant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyGrant, setBusyGrant] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    if (!hasFirebaseAuthBridge()) {
      setError("Chưa có Firebase ID token để tải thư viện Parent.");
      setLoading(false);
      return () => { active = false; };
    }
    Promise.all([backendApi.parentLessons(), backendApi.parentInvitations()])
      .then(([lessonPage, invitationPage]) => {
        if (!active) return;
        setLessons(lessonPage.items);
        setInvitations(invitationPage.items);
      })
      .catch((cause: unknown) => {
        if (active) setError(backendMessage(cause));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reload]);

  const respond = async (grant: AccessGrant, accept: boolean) => {
    setBusyGrant(grant.access_grant_id);
    setError(null);
    try {
      await backendApi.answerParentInvitation(grant.access_grant_id, accept);
      setReload((value) => value + 1);
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setBusyGrant(null);
    }
  };

  return (
    <div className="page">
      <BackendModeNotice roleLabel="Phụ huynh" />
      <div className="sec-head">
        <h1 className="h1">Thư viện giáo án</h1>
        <button type="button" className="ghost-link" onClick={() => setReload((value) => value + 1)}>Tải lại</button>
      </div>
      <p className="sub">Chỉ hiển thị giáo án public hoặc đã được chia sẻ với tài khoản này.</p>
      {error && <BackendNotice title="Không tải được dữ liệu" tone="error">{error}</BackendNotice>}
      {loading && <BackendNotice title="Đang tải thư viện">Đang đọc giáo án và lời mời từ backend.</BackendNotice>}
      {!loading && !error && lessons.length === 0 && (
        <BackendNotice title="Chưa có giáo án khả dụng">Bạn có thể nhận lời mời giáo án hoặc quay lại sau.</BackendNotice>
      )}
      {lessons.length > 0 && (
        <div className="stack">
          {lessons.map((lesson, index) => (
            <button
              key={`${lesson.lesson_id}:${lesson.version_id}`}
              type="button"
              className="act-row"
              onClick={() => {
                setSelectedLessonId(lesson.lesson_id);
                nav("/p02-lesson-detail", { state: { apiLessonId: lesson.lesson_id } });
              }}
            >
              <IconBadge name="book" tone={index % 2 ? "accent" : "primary"} size={44} />
              <span className="grow" style={{ minWidth: 0, textAlign: "left" }}>
                <span className="h3" style={{ display: "block" }}>{lesson.title}</span>
                <span className="tiny" style={{ display: "block" }}>{lesson.topic} · {lesson.activity_count} hoạt động · {lesson.access_source === "PUBLIC" ? "Công khai" : "Được chia sẻ"}</span>
              </span>
              <Icon name="arrow-right" size={18} />
            </button>
          ))}
        </div>
      )}

      <div className="sec-head" style={{ marginTop: 24 }}><h2 className="h2">Lời mời giáo án</h2></div>
      {invitations.length === 0 && !loading && !error && <p className="sub">Không có lời mời đang chờ.</p>}
      {invitations.map((grant) => (
        <div key={grant.access_grant_id} className="act-row">
          <IconBadge name="users" tone="mint" size={42} />
          <span className="grow" style={{ minWidth: 0 }}>
            <span className="h3" style={{ display: "block" }}>Giáo án {grant.lesson_id}</span>
            <span className="tiny">Quyền: {grant.capability} · Trạng thái: {grant.state}</span>
          </span>
          {grant.state === "INVITED" && (
            <span className="row">
              <button type="button" className="chip on" disabled={busyGrant === grant.access_grant_id} onClick={() => void respond(grant, true)}>Chấp nhận</button>
              <button type="button" className="chip line" disabled={busyGrant === grant.access_grant_id} onClick={() => void respond(grant, false)}>Từ chối</button>
            </span>
          )}
        </div>
      ))}
      <BackendNotice title="Story Run chưa có API Parent trong backend hiện tại" tone="warn">
        Tạo story, upload tranh/giọng nói, lịch sử video, hồ sơ trẻ và quota chưa được lưu qua API sản phẩm. Các màn tương ứng chỉ xuất hiện trong bản xem thử.
      </BackendNotice>
    </div>
  );
}

function ParentApiLessonDetail({ lessonId }: { lessonId: string }) {
  const nav = useNavigate();
  const [lesson, setLesson] = useState<ParentLessonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    if (!lessonId) {
      setError("Không có lesson_id để tải chi tiết.");
      setLoading(false);
      return () => { active = false; };
    }
    backendApi.parentLesson(lessonId)
      .then((result) => { if (active) setLesson(result); })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [lessonId]);
  return (
    <div className="page">
      <TopBar title="Chi tiết giáo án" onBack={() => nav("/p01-lesson-library")} />
      {loading && <BackendNotice title="Đang tải giáo án">Đang lấy phiên bản được phép xem từ backend.</BackendNotice>}
      {error && <BackendNotice title="Không mở được giáo án" tone="error">{error}</BackendNotice>}
      {lesson && <>
        <BackendModeNotice roleLabel="Phụ huynh" />
        <h1 className="h1">{lesson.title}</h1>
        <p className="sub">{lesson.topic} · phiên bản {lesson.version_no} · {lesson.access_source === "PUBLIC" ? "Công khai" : "Được chia sẻ"}</p>
        <h2 className="h2">Mục tiêu</h2>
        <ul>{lesson.objectives.map((item) => <li key={item}>{item}</li>)}</ul>
        <h2 className="h2">Hướng dẫn vẽ</h2>
        <p className="sub">{lesson.drawing_steps_text}</p>
        <h2 className="h2">Hoạt động</h2>
        {lesson.activities.map((activity, index) => <section className="card" key={`${activity.title}-${index}`}>
          <h3 className="h3">{activity.title}</h3>
          <p className="sub">{activity.objective}</p>
          <p>{activity.instructions_text}</p>
          {activity.materials_text && <p className="tiny">Chuẩn bị: {activity.materials_text}</p>}
          {activity.preparation_text && <p className="tiny">Cách chuẩn bị: {activity.preparation_text}</p>}
          {activity.safety_notes && <p className="tiny">An toàn: {activity.safety_notes}</p>}
        </section>)}
        <BackendNotice title="Chưa thể bắt đầu tạo story từ màn này" tone="warn">
          API hiện trả chi tiết giáo án; chưa có API Parent bền vững cho Story Run, tranh hoặc video.
        </BackendNotice>
      </>}
    </div>
  );
}

/* =====================================================================
   P02 · Chi tiết chủ đề (Tùy chọn)
   ===================================================================== */
export function P02LessonDetailPage() {
  const nav = useNavigate();
  const apiState = useLocState<{ apiLessonId: string }>();
  const { lessons, selectedLessonId, setGuideEnabled, setGuideTopic, setSkippedOptionalSetup } = useParent();
  if (!isLocalPreview()) {
    return <ParentApiLessonDetail lessonId={apiState.apiLessonId ?? selectedLessonId} />;
  }
  const lesson = lessons.find((l) => l.id === selectedLessonId) ?? lessons[0];
  const idx = lessons.indexOf(lesson);

  return (
    <div className="page">
      <TopBar
        title="Chi tiết bài học (Tùy chọn)"
        onBack={() => nav("/p01-lesson-library", { state: { view: "topics" } })}
      />
      <StepChips current={1} />

      <section className={`lesson-detail-hero ${GRADS[idx % GRADS.length]}`}>
        <div className="lesson-detail-cover">
          <img
            className="lesson-detail-art"
            src={storyArtSrc(lesson.coverKind)}
            alt=""
            aria-hidden="true"
          />
        </div>
        <div className="lesson-detail-copy">
          <h1 className="h1">{lesson.title}</h1>
          <p className="sub">{lesson.summary}</p>
        </div>
        <div className="row wrap lesson-detail-tags">
          <span className="chip amber">Bước tùy chọn</span>
          {lesson.tags.map((t) => (
            <span key={t} className="chip line">{t}</span>
          ))}
        </div>
      </section>

      <h2 className="h2">Điểm khám phá cùng bé</h2>
      <div className="stack">
        {lesson.knowledgePoints.map((k, i) => (
          <div key={k.title} className="card tight row">
            <span className={`tile3d ${["amber", "mint", "pink"][i % 3]}`} aria-hidden="true">
              <Icon name={lessonPointIcon(k.title)} size={20} />
            </span>
            <div className="grow">
              <h3 className="h3">{k.title}</h3>
              <p className="sub">{k.text}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="cta-bar">
        <Btn
          onClick={() => {
            setSkippedOptionalSetup(false);
            setGuideEnabled(true);
            setGuideTopic(lesson.topic);
            nav("/p03-drawing-line-guide");
          }}
        >
          <Icon name="palette" size={19} /> Xem gợi ý vẽ (Tùy chọn)
        </Btn>
        <Soft
          onClick={() => {
            setSkippedOptionalSetup(false);
            setGuideEnabled(false);
            setGuideTopic(lesson.topic);
            nav("/p04-capture-subject-confirmation");
          }}
        >
          <Icon name="camera" size={18} /> Bỏ qua · Chụp tranh ngay
        </Soft>
      </div>
    </div>
  );
}

/* =====================================================================
   P03 · Hướng dẫn vẽ 3–5 bước (Tùy chọn · BR-46)
   ===================================================================== */
export function P03DrawingLineGuidePage() {
  const nav = useNavigate();
  const { lessons, selectedLessonId, guideEnabled, setGuideEnabled, guideTopic, setSkippedOptionalSetup } = useParent();
  const lesson = lessons.find((l) => l.id === selectedLessonId) ?? lessons[0];
  const [i, setI] = useState(0);
  const [difficulty, setDifficulty] = useState<"Dễ (3 bước)" | "Vừa (4 bước)">("Vừa (4 bước)");
  const [landscapeOpen, setLandscapeOpen] = useState(false);
  const steps = lesson.drawingSteps;
  const step = steps[i];
  if (landscapeOpen) {
    return (
      <div className="page" style={{ background: "#09152b", color: "#f8fafc", minHeight: "100%", justifyContent: "space-between", padding: 16 }}>
        <div className="row between">
          <span className="chip mint">Gợi ý vẽ 16:9 · {guideTopic}</span>
          <button type="button" className="round-btn" aria-label="Thu nhỏ" onClick={() => setLandscapeOpen(false)}>
            <Icon name="close" size={18} />
          </button>
        </div>
        <div className="paper" style={{ aspectRatio: "16 / 9", background: "#fffdf7", borderColor: "#60a5fa" }}>
          <div className="inner" style={{ aspectRatio: "16 / 9", background: "#fffdf7", flexDirection: "column", gap: 6, padding: 12 }}>
            <DrawingGuideIllustration kind={lesson.coverKind} stepIndex={i} enabled={guideEnabled} />
          </div>
        </div>
        <div className="flat-box row between" style={{ background: "rgba(30, 49, 84, 0.85)", color: "#f8fafc" }}>
          <div>
            <h1 className="h3" style={{ color: "#ffffff" }}>Bước {i + 1}/{steps.length}: {step?.title}</h1>
            <div className="tiny" style={{ color: "#dbeafe" }}>{step?.hint}</div>
          </div>
          <div className="row">
            <button type="button" className="round-btn" aria-label="Bước trước" disabled={i === 0} onClick={() => setI(Math.max(0, i - 1))}>
              <Icon name="arrow-left" size={18} />
            </button>
            <button type="button" className="round-btn" aria-label="Bước sau" disabled={i >= steps.length - 1} onClick={() => setI(Math.min(steps.length - 1, i + 1))}>
              <Icon name="arrow-right" size={18} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <TopBar
        title={`Gợi ý vẽ (Tùy chọn)`}
        onBack={() => nav("/p02-lesson-detail")}
      />
      <StepChips current={1} />

      <div className="row between wrap">
        <h1 className="h2">Hướng dẫn vẽ theo chủ đề</h1>
        <span className="chip amber">Tùy chọn</span>
      </div>

      <Note tone="blue" icon="palette">
        Gợi ý 3–5 bước vẽ trên giấy trước khi chụp. Không gửi hồ sơ của bé và không trừ lượt video.
      </Note>

      <div className="row between wrap">
        <div className="row" style={{ gap: 6 }}>
          {(["Dễ (3 bước)", "Vừa (4 bước)"] as const).map((d) => (
            <button key={d} type="button" className={`chip ${difficulty === d ? "on" : "line"}`} onClick={() => setDifficulty(d)}>
              {d}
            </button>
          ))}
        </div>
        <div className="row" style={{ gap: 6 }}>
          <span className="tiny">Nét gợi ý</span>
          <Switch on={guideEnabled} label="Hiện nét hướng dẫn" onChange={() => setGuideEnabled(!guideEnabled)} />
        </div>
      </div>

      <div className="row drawing-step-picker" style={{ justifyContent: "center", gap: 8 }}>
        {steps.map((s, idx) => (
          <button
            key={s.step}
            type="button"
            className={`num ${idx === i ? "is-current" : idx < i ? "is-complete" : ""}`}
            aria-label={`Bước ${idx + 1}${idx === i ? ", đang xem" : ""}`}
            aria-current={idx === i ? "step" : undefined}
            style={{
              width: 34,
              height: 34,
              opacity: idx === i ? 1 : 0.78,
              cursor: "pointer",
            }}
            onClick={() => setI(idx)}
          >
            {idx + 1}
          </button>
        ))}
      </div>

      <div className="paper">
        <span className="tape" />
        <div className="inner" style={{ opacity: guideEnabled ? 1 : 0.45 }}>
          <DrawingGuideIllustration kind={lesson.coverKind} stepIndex={i} enabled={guideEnabled} />
        </div>
      </div>

      <div className="card row">
        <span className="num">{step?.step}</span>
        <div className="grow">
          <h2 className="h3">Bước {i + 1}: {step?.title}</h2>
          <p className="sub">{step?.hint}</p>
        </div>
        <button type="button" className="chip line" onClick={() => setLandscapeOpen(true)}>
          <Icon name="rotate" size={14} /> 16:9
        </button>
      </div>

      <div className="cta-bar">
        {i < steps.length - 1 ? (
          <Btn onClick={() => setI(i + 1)}>
            Bước tiếp theo <Icon name="arrow-right" size={18} />
          </Btn>
        ) : (
          <Btn
            onClick={() => {
              setSkippedOptionalSetup(false);
              nav("/p04-capture-subject-confirmation");
            }}
          >
            <Icon name="camera" size={19} /> Vẽ xong · Chụp tranh ngay
          </Btn>
        )}
        <Soft
          onClick={() => {
            setSkippedOptionalSetup(false);
            nav("/p04-capture-subject-confirmation");
          }}
        >
          <Icon name="camera" size={18} /> Bỏ qua · Chụp tranh ngay
        </Soft>
      </div>
    </div>
  );
}

/* =====================================================================
   P04 · Chụp tranh của bé & Xác nhận nhân vật chính (AI VLM)
   ===================================================================== */
export function P04CaptureSubjectConfirmationPage() {
  const nav = useNavigate();
  const {
    skippedOptionalSetup,
    guideTopic,
    detectedSubject,
    setDetectedSubject,
    setSubjectConfirmed,
    setActiveSheet,
    showToast,
  } = useParent();
  const [captured, setCaptured] = useState(false);

  useEffect(() => {
    const on = () => {
      setCaptured(true);
      showToast("Đã chụp bức vẽ của bé.", "ok");
    };
    window.addEventListener("s2l-captured", on);
    return () => window.removeEventListener("s2l-captured", on);
  }, [showToast]);

  const handleBackFromCapture = () => {
    nav(skippedOptionalSetup ? "/p01-lesson-library" : "/p02-lesson-detail");
  };

  const analysisBanner = skippedOptionalSetup ? (
    <Note tone="blue" icon="sparkle">
      AI sẽ tìm nhân vật và gợi ý câu chuyện từ tranh của bé.
    </Note>
  ) : (
    <Note tone="mint" icon="palette">
      AI gợi ý theo chủ đề «{guideTopic}» mà bạn đã chọn.
    </Note>
  );

  if (!captured) {
    return (
      <div className="page">
        <TopBar title="Chụp tranh của bé" onBack={handleBackFromCapture} />
        <StepChips current={2} optionalSkipped={skippedOptionalSetup} />
        <h1 className="h1 center">Chụp hoặc tải lên bức vẽ</h1>
        <p className="sub center">Giữ trọn bức tranh trong khung hình.</p>

        <div className="paper">
          <span className="tape" />
          <div className="inner">
            <img className="drawing-preview" src="/child-butterfly-art.png" alt="Tranh con bướm minh họa cho bản xem thử" />
          </div>
        </div>

        {analysisBanner}

        <div className="cap-grid">
          <button type="button" className="cap-btn blue" onClick={() => setActiveSheet("CAMERA_PERMISSION")}>
            <Icon name="camera" size={28} /> Chụp ảnh bức vẽ
          </button>
          <button type="button" className="cap-btn mint" onClick={() => setCaptured(true)}>
            <Icon name="image" size={28} /> Chọn từ thư viện
          </button>
        </div>

        <Note tone="amber" icon="shield">
          Chỉ chụp tranh; tránh khuôn mặt và thông tin cá nhân của bé.
        </Note>

        <div className="card tight tip-list">
          <span><Icon name="sun" size={16} /> Chụp nơi đủ sáng, tránh bóng tối che khuất nét vẽ</span>
          <span><Icon name="maximize" size={16} /> Giữ trọn tờ giấy nằm gọn trong khung hình</span>
        </div>
      </div>
    );
  }

  const detectedCandidates = [
    { label: detectedSubject, conf: "95%", role: "Nhân vật chính" },
    { label: "Bông hoa", conf: "89%", role: "Chi tiết phụ" },
    { label: "Mặt trời", conf: "92%", role: "Bối cảnh" },
    { label: "Bãi cỏ xanh", conf: "86%", role: "Bối cảnh" },
  ];

  return (
    <div className="page">
      <TopBar title="Xác nhận nhân vật chính" onBack={() => setCaptured(false)} />
      <StepChips current={2} optionalSkipped={skippedOptionalSetup} />

      <div className="paper">
        <span className="tape" />
        <div className="inner">
          <img className="drawing-preview" src="/child-butterfly-art.png" alt="Bức tranh minh họa đang được xác nhận" />
        </div>
      </div>

      {analysisBanner}

      <div className="row between">
        <h1 className="h2">Đây có phải là nhân vật chính?</h1>
        <span className="chip mint">95% tin cậy</span>
      </div>

      <div className="stack" style={{ gap: 8 }}>
        {detectedCandidates.map((c, idx) => {
          const active = c.label === detectedSubject;
          return (
            <button
              key={c.label + idx}
              type="button"
              className={`age-opt ${active ? "on" : ""}`}
              onClick={() => setDetectedSubject(c.label)}
            >
              <span className={`tile3d ${idx === 0 ? "" : idx === 1 ? "pink" : idx === 2 ? "amber" : "mint"}`} style={{ width: 42, height: 42, fontSize: 20 }}>
                <Icon name={subjectIcon(c.label)} size={20} />
              </span>
              <span className="grow">
                <span className="h3" style={{ display: "block" }}>{c.label}</span>
                <span className="tiny" style={{ display: "block" }}>{c.role} · Độ tin cậy {c.conf}</span>
              </span>
              <span className="rd">{active && <Icon name="check" size={12} strokeWidth={3} />}</span>
            </button>
          );
        })}
      </div>

      <Soft small onClick={() => setActiveSheet("EDIT_SUBJECT")}>
        <Icon name="edit" size={15} /> Đổi sang chủ thể khác
      </Soft>

      <div className="cta-bar">
        <Btn
          onClick={() => {
            setSubjectConfirmed(true);
            nav("/p05-context-idea-confirmation");
          }}
        >
          <Icon name="check" size={19} /> Xác nhận chủ thể &amp; Tiếp tục
        </Btn>
        <Soft onClick={() => setCaptured(false)}>Chụp lại bức vẽ</Soft>
      </div>
    </div>
  );
}

/* =====================================================================
   P05 · Gộp Nhập nội dung & Ghi âm giọng kể (Đã xóa Transcript & Context dư)
   ===================================================================== */
export function P05ContextIdeaConfirmationPage() {
  const nav = useNavigate();
  const [secs, setSecs] = useState(0);
  const [transcriptReview, setTranscriptReview] = useState<"none" | "needed" | "done">("none");
  const {
    audioMode,
    isRecording,
    setIsRecording,
    ideaTranscript,
    setIdeaTranscript,
    setContextConfirmed,
    detectedSubject,
    skippedOptionalSetup,
    showToast,
  } = useParent();

  useEffect(() => {
    if (!isRecording) return;
    const t = window.setInterval(() => {
      setSecs((s) => {
        if (s >= 120) {
          setIsRecording(false);
          return 120;
        }
        return s + 1;
      });
    }, 1000);
    return () => window.clearInterval(t);
  }, [isRecording, setIsRecording]);

  const mm = `${String(Math.floor(secs / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`;
  const audioError =
    audioMode === "TOO_LONG"
      ? "Bản ghi dài quá 2 phút. Hãy ghi lại ngắn hơn nhé."
      : audioMode === "TOO_LARGE"
      ? "Tệp ghi âm lớn quá 20 MB. Hãy ghi lại ngắn hơn nhé."
      : audioMode === "MIC_DENIED"
      ? "Chưa có quyền dùng micro. Hãy bật quyền micro hoặc gõ trực tiếp vào ô trên."
      : "";

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      const voiceSample = `Chú ${detectedSubject.toLowerCase()} nhỏ bay dạo quanh khu vườn đầy hoa và kết bạn với tia nắng sớm.`;
      const nextText = ideaTranscript.trim()
        ? `${ideaTranscript.trim()} ${voiceSample}`
        : voiceSample;
      setIdeaTranscript(nextText);
      setTranscriptReview("needed");
      showToast(isLocalPreview() ? "Đã điền lời kể minh họa. Hãy đọc lại trước khi tiếp tục." : "Đã nhận dạng lời kể. Hãy đọc lại trước khi tiếp tục.", "info");
    } else {
      setSecs(0);
      setTranscriptReview("none");
      setIsRecording(true);
    }
  };

  return (
    <div className="page">
      <TopBar title="Ý tưởng" onBack={() => nav("/p04-capture-subject-confirmation")} />
      <StepChips current={3} optionalSkipped={skippedOptionalSetup} />

      <div className="card stack">
        <div className="story-prompt">
          <img className="story-prompt-art" src={storyArtSrc(detectedSubject)} alt="" aria-hidden="true" />
          <div className="grow">
            <h1 className="h2">Giờ bé kể về {detectedSubject.toLowerCase()} nhé</h1>
            <p className="sub">Ghi âm hoặc nhập vài ý ngắn.</p>
          </div>
        </div>
        {ideaTranscript.trim().length > 0 && (
          <div className="row between">
            <button
              type="button"
              className="ghost-link"
              style={{ padding: "2px 4px", fontSize: 12 }}
              onClick={() => setIdeaTranscript("")}
            >
              Xóa nhanh
            </button>
          </div>
        )}
        <textarea
          className="textarea"
          value={ideaTranscript}
          aria-label={`Ý tưởng câu chuyện về ${detectedSubject}`}
          placeholder={`Ví dụ: ${detectedSubject} đi dạo trong khu vườn nắng ấm và gặp những người bạn tốt bụng...`}
          onChange={(e) => {
            setIdeaTranscript(e.target.value);
            if (transcriptReview === "done") setTranscriptReview("needed");
          }}
        />

        {transcriptReview !== "none" && (
          <div className="transcript-review" role="group" aria-label="Kiểm tra nội dung giọng kể">
            <div className="tiny">
              {isLocalPreview() ? "Lời kể minh họa đã điền vào ô trên." : "Nội dung nhận dạng đã điền vào ô trên."} Hãy đọc lại và sửa nếu cần.
            </div>
            <button
              type="button"
              className={`transcript-review-btn${transcriptReview === "done" ? " is-checked" : ""}`}
              role="checkbox"
              aria-checked={transcriptReview === "done"}
              onClick={() => setTranscriptReview((state) => state === "done" ? "needed" : "done")}
            >
              <span aria-hidden="true">{transcriptReview === "done" ? <Icon name="check" size={14} strokeWidth={3} /> : null}</span>
              {transcriptReview === "done" ? "Đã xem lại" : "Tôi đã xem lại nội dung"}
            </button>
          </div>
        )}

        {/* Unified Microphone Record bar directly underneath textarea inside the same card */}
        <div className="mic-bar">
          <div className="row between">
            <div className="row">
              <button
                type="button"
                className={`mic-btn ${isRecording ? "live" : ""}`}
                aria-label={isRecording ? "Dừng phần ghi âm minh họa" : "Bắt đầu phần ghi âm minh họa"}
                onClick={toggleRecording}
              >
                <Icon name={isRecording ? "stop" : "mic"} size={22} fill={isRecording ? "currentColor" : "none"} />
              </button>
              <div>
                <div className="h3">{isRecording ? "Đang minh họa ghi âm…" : "Ghi âm giọng kể"}</div>
                <div className="tiny">{isRecording ? "Chạm dừng để xem lời kể mẫu" : "Bản xem thử · chưa dùng micro thật"}</div>
              </div>
            </div>
            <span className="chip line timer-num">{mm} / 02:00</span>
          </div>
          {isRecording && <Waveform live={true} />}
        </div>
      </div>

      {audioError && <Note tone="red" icon="mic">{audioError}</Note>}

      <div className="cta-bar">
        <Btn
          disabled={!!audioError || isRecording || transcriptReview === "needed"}
          onClick={() => {
            setContextConfirmed(true);
            nav("/p05b-activity-selection");
          }}
        >
          Tiếp tục <Icon name="arrow-right" size={18} />
        </Btn>
        <Soft
          disabled={isRecording}
          onClick={() => {
            setIdeaTranscript("");
            setContextConfirmed(true);
            nav("/p05b-activity-selection");
          }}
        >
          Bỏ qua
        </Soft>
      </div>
    </div>
  );
}

/* =====================================================================
   P05b · Chọn một hoạt động cho câu chuyện (Trang riêng)
   ===================================================================== */
export function P05bActivitySelectionPage() {
  const nav = useNavigate();
  const {
    lessons,
    selectedLessonId,
    selectedActivityId,
    setSelectedActivityId,
    setContextConfirmed,
    skippedOptionalSetup,
  } = useParent();
  const lesson = lessons.find((l) => l.id === selectedLessonId) ?? lessons[0];
  const activities = lesson.outdoorActivities;
  const currentActId = activities.some((a) => a.id === selectedActivityId)
    ? selectedActivityId
    : activities[0]?.id ?? "";

  useEffect(() => {
    if (currentActId && currentActId !== selectedActivityId) {
      setSelectedActivityId(currentActId);
    }
  }, [currentActId, selectedActivityId, setSelectedActivityId]);

  return (
    <div className="page">
      <TopBar title="Chọn hoạt động cho câu chuyện" onBack={() => nav("/p05-context-idea-confirmation")} />
      <StepChips current={4} optionalSkipped={skippedOptionalSetup} />

      <h1 className="h1">Chọn 1 hoạt động đi kèm</h1>
      <p className="sub">Chọn hoạt động để cả nhà cùng khám phá sau khi xem video.</p>

      <div className="stack">
        {activities.map((a, idx) => {
          const on = currentActId === a.id;
          return (
            <button
              key={a.id}
              type="button"
              className={`age-opt ${on ? "on" : ""}`}
              onClick={() => setSelectedActivityId(a.id)}
            >
              <span className="activity-thumb" aria-hidden="true">
                <img src={storyArtSrc(lesson.coverKind)} alt="" />
              </span>
              <span className="grow">
                <span className="h3" style={{ display: "block" }}>{a.title}</span>
                <span className="sub" style={{ display: "block", marginTop: 2 }}>{a.materials.replace(/^Vật liệu:\s*/, "Chuẩn bị: ")}</span>
                {a.safetyNote && (
                  <span className="tiny" style={{ display: "block", marginTop: 4 }}>
                    Có lưu ý an toàn trước khi bắt đầu
                  </span>
                )}
              </span>
              <span className="rd">{on && <Icon name="check" size={12} strokeWidth={3} />}</span>
            </button>
          );
        })}
      </div>

      <div className="cta-bar">
        <Btn
          onClick={() => {
            setContextConfirmed(true);
            nav("/p06-story-review");
          }}
        >
          Tiếp theo: Duyệt kịch bản <Icon name="arrow-right" size={18} />
        </Btn>
      </div>
    </div>
  );
}

/* =====================================================================
   P06 · Duyệt kịch bản 5 cảnh (Đã bỏ hẳn Storyboard)
   ===================================================================== */
export function P06StoryReviewPage() {
  const nav = useNavigate();
  const {
    scenes,
    scriptRevision,
    rewriteCount,
    rewriteSuggestion,
    setRewriteSuggestion,
    requestAiRewrite,
    setActiveSheet,
    quotaRemaining,
    lastUnsuitableReason,
    detectedSubject,
    skippedOptionalSetup,
    lessons,
    selectedLessonId,
    selectedActivityId,
  } = useParent();
  const left = 3 - rewriteCount;
  const lesson = lessons.find((l) => l.id === selectedLessonId) ?? lessons[0];
  const act = lesson.outdoorActivities.find((a) => a.id === selectedActivityId) ?? lesson.outdoorActivities[0];
  const storyHeading = skippedOptionalSetup ? `Hành trình của ${detectedSubject}` : lesson.title;

  return (
    <div className="page">
      <TopBar title="Duyệt kịch bản câu chuyện" onBack={() => nav("/p05b-activity-selection")} />
      <StepChips current={5} optionalSkipped={skippedOptionalSetup} />

      <Note tone="blue" icon="shield">
        Kiểm tra kịch bản 5 cảnh trước khi dùng 1 lượt tạo video.
      </Note>
      {lastUnsuitableReason && (
        <Note tone="amber" icon="refresh">
          Lý do tạo lại lần trước: {lastUnsuitableReason}
        </Note>
      )}

      <section className="story-review-summary">
        <img className="story-review-art" src={storyArtSrc(lesson.coverKind)} alt="" aria-hidden="true" />
        <div className="story-review-copy">
          <div className="row between wrap" style={{ gap: 6 }}>
            <h1 className="h2">{storyHeading}</h1>
            <span className="chip line">Bản #{scriptRevision}</span>
          </div>
          <div className="tiny">{detectedSubject} · {act?.title}</div>
        </div>
      </section>

      <div className="card stack">
        {scenes.map((s, idx) => (
          <div
            key={s.index}
            className="row"
            style={{
              alignItems: "flex-start",
              paddingBottom: idx < scenes.length - 1 ? 10 : 0,
              borderBottom: idx < scenes.length - 1 ? "1px dashed var(--line)" : "none",
            }}
          >
            <span className="num" style={{ marginTop: 2 }}>{s.index}</span>
            <div className="grow">
              <h2 className="h3">{s.title.replace(/^Cảnh \d+\s*[·–—-]\s*/, "")}</h2>
              <p className="sub">{s.narration}</p>
              <div className="tiny" style={{ marginTop: 3 }}>Thời lượng cảnh: {s.durationSec} giây</div>
            </div>
          </div>
        ))}
      </div>

      <div className="card stack">
        <div className="row between">
          <h2 className="h2">Nhờ AI viết lại kịch bản</h2>
          <span className="tiny">Tối đa 3 lần / phiên · Còn {left}/3</span>
        </div>
        <input
          className="input"
          value={rewriteSuggestion}
          onChange={(e) => setRewriteSuggestion(e.target.value)}
          aria-label="Gợi ý cho AI viết lại kịch bản"
          placeholder="Ví dụ: Thêm chi tiết chú bướm bay qua vườn hoa..."
        />
        <Soft disabled={left <= 0} onClick={requestAiRewrite}>
          <Icon name="refresh" size={16} /> {left > 0 ? `Viết lại với AI (còn ${left} lần)` : "Đã hết 3 lần viết lại"}
        </Soft>
      </div>

      <div className="cta-bar">
        {quotaRemaining <= 0 && (
          <Note tone="red" icon="lock">
            Tài khoản đã hết lượt tạo video. Bố mẹ mua thêm lượt để tiếp tục nhé.
          </Note>
        )}
        {quotaRemaining <= 0 ? (
          <Btn tone="amber" onClick={() => nav("/p12-video-quota")}>
            Mua thêm lượt tạo
          </Btn>
        ) : (
          <Btn tone="mint" onClick={() => setActiveSheet("CONFIRM_SCRIPT")}>
            <Icon name="check" size={19} /> Duyệt kịch bản &amp; Tạo video
          </Btn>
        )}
      </div>
    </div>
  );
}

/* =====================================================================
   P07 · Tiến trình tạo video
   ===================================================================== */
const NEXT_MODE: Partial<Record<VideoJobMode, VideoJobMode>> = {
  ADMISSION_PENDING: "RUNNING",
  QUEUED: "RUNNING",
  RUNNING: "SAFETY_VALIDATING",
  SAFETY_VALIDATING: "RECONCILING",
  RECONCILING: "READY",
};

export function P07VideoJobStatusPage() {
  const nav = useNavigate();
  const { videoJobMode, setVideoJobMode, cancelPurgeStep, setActiveSheet, skippedOptionalSetup } = useParent();

  useEffect(() => {
    const next = NEXT_MODE[videoJobMode];
    if (!next) return;
    const t = window.setTimeout(() => setVideoJobMode(next), 3200);
    return () => window.clearTimeout(t);
  }, [videoJobMode, setVideoJobMode]);

  const stageOf: Partial<Record<VideoJobMode, number>> = {
    ADMISSION_PENDING: 0,
    QUEUED: 1,
    RUNNING: 1,
    SAFETY_VALIDATING: 2,
    RECONCILING: 3,
    READY: 4,
    SAFETY_BLOCKED: 3,
    SERVICE_ERROR: 2,
  };
  const stage = stageOf[videoJobMode] ?? 0;
  const labels = [
    "Đọc nội dung bức vẽ",
    "Chuẩn bị kịch bản đã duyệt",
    "Tạo hình ảnh và cảnh phim",
    "Thêm lời kể và kiểm tra an toàn",
  ];

  if (videoJobMode === "DELETE_PENDING" || videoJobMode === "DELETED") {
    return (
      <div className="page">
        <TopBar title="Đã dừng tạo video" back={false} />
        <div className="card stack" style={{ alignItems: "center", textAlign: "center" }}>
          <IconBadge name="trash" tone="danger" size={56} />
          <h1 className="h2">
            {videoJobMode === "DELETED" ? "Đã dọn sạch dữ liệu xem thử" : "Đang thu hồi dữ liệu…"}
          </h1>
          <p className="sub">
            {videoJobMode === "DELETED"
              ? "Dữ liệu minh họa của phiên này đã được xóa khỏi màn hình."
              : "Đang minh họa việc hủy tác vụ và dọn dữ liệu tạm…"}
          </p>
          <div className="video-job-state" role="status" aria-live="polite">Bước dọn dữ liệu {Math.min(cancelPurgeStep, 4)} / 4 · bản xem thử</div>
        </div>
        <Btn onClick={() => nav("/p01-lesson-library")}>Về trang chủ</Btn>
      </div>
    );
  }

  const blocked = videoJobMode === "SAFETY_BLOCKED";
  const failed = videoJobMode === "SERVICE_ERROR";

  return (
    <div className="page">
      <TopBar title="Tiến trình tạo video" onBack={() => nav("/p06-story-review")} />
      <StepChips current={6} optionalSkipped={skippedOptionalSetup} />
      <div className="card stack" style={{ alignItems: "center", textAlign: "center" }}>
        <img className="process-art" src="/illustrations/kite-ai-guide.webp" alt="Bạn diều giấy đang khám phá bức tranh" />
        <h1 className="h1">
          {blocked
            ? "Video cần được xem lại"
            : failed
            ? "Chưa tạo được video"
            : stage >= 4
            ? "Quy trình minh họa đã xong!"
            : "Đang tạo video..."}
        </h1>
        <div className="video-job-state" role="status" aria-live="polite">
          {blocked
            ? "Tạm dừng tại bước kiểm tra an toàn"
            : failed
            ? "Bước tạo video đang gặp lỗi"
            : stage >= 4
            ? "Minh họa hoàn tất"
            : `Đang minh họa bước ${Math.min(stage + 1, labels.length)} / ${labels.length}`}
        </div>
      </div>

      <Note tone="amber" icon="info">Bản xem thử: các bước này không gửi tác vụ tạo video thật.</Note>

      {blocked && (
        <Note tone="red" icon="shield">
          Video chưa đạt kiểm tra an toàn. Hãy điều chỉnh kịch bản rồi thử lại.
        </Note>
      )}
      {failed && (
        <Note tone="red" icon="alert">
          Bản xem thử đang mô phỏng lỗi dịch vụ; lượt tạo minh họa chưa thay đổi. Bố mẹ có thể thử lại hoặc sửa kịch bản.
        </Note>
      )}

      <div className="checklist">
        {labels.map((l, idx) => {
          const cls = idx < stage ? "done" : idx === stage && !blocked && !failed ? "now" : idx === stage ? "fail" : "";
          return (
            <div key={l} className={`check ${cls}`}>
              <span className="ck">{cls === "done" && <Icon name="check" size={15} strokeWidth={3} />}</span>
              <span>{l}</span>
            </div>
          );
        })}
      </div>

      <div className="cta-bar">
        {videoJobMode === "READY" && (
          <Btn tone="mint" onClick={() => nav("/p08-video-and-activities")}>
            <Icon name="play" size={18} fill="#fff" /> Xem video minh họa
          </Btn>
        )}
        {(blocked || failed) && (
          <>
            {failed && <Btn onClick={() => setVideoJobMode("QUEUED")}>Thử lại</Btn>}
            <Soft onClick={() => nav("/p06-story-review")}>Sửa kịch bản</Soft>
          </>
        )}
        {!["READY", "SAFETY_BLOCKED", "SERVICE_ERROR"].includes(videoJobMode) && (
          <Soft red onClick={() => setActiveSheet("CANCEL_VIDEO")}>Hủy tạo video</Soft>
        )}
      </div>
    </div>
  );
}

/* =====================================================================
   P08 · Xem video tối ưu không gian + Xoay ngang / Toàn màn hình 16:9
   ===================================================================== */
export function P08VideoAndActivitiesPage() {
  const nav = useNavigate();
  const [bgmMuted, setBgmMuted] = useState(false);
  const {
    captionsEnabled,
    setCaptionsEnabled,
    scenes,
    detectedSubject,
    skippedOptionalSetup,
    lessons,
    selectedLessonId,
    setActiveSheet,
    videoRegenCount,
    landscapeVideo,
    setLandscapeVideo,
    autoLandscapeOnPlay,
    setAutoLandscapeOnPlay,
  } = useParent();

  const lesson = lessons.find((l) => l.id === selectedLessonId) ?? lessons[0];
  const videoTitle = skippedOptionalSetup ? `Câu chuyện của ${detectedSubject}` : lesson.title;
  const videoArt = storyArtSrc(skippedOptionalSetup ? detectedSubject : lesson.coverKind);

  const [playing, setPlaying] = useState(false);
  const [prog, setProg] = useState(25);

  useEffect(() => {
    if (!playing) return;
    const t = window.setInterval(() => {
      setProg((p) => {
        if (p >= 100) {
          setPlaying(false);
          return 100;
        }
        return p + 1.2;
      });
    }, 150);
    return () => window.clearInterval(t);
  }, [playing]);

  const handlePlayToggle = () => {
    if (!playing) {
      if (prog >= 100) setProg(0);
      setPlaying(true);
      if (autoLandscapeOnPlay && !landscapeVideo) {
        setLandscapeVideo(true);
      }
    } else {
      setPlaying(false);
    }
  };

  const totalSec = scenes.reduce((acc, s) => acc + s.durationSec, 0) || 60;
  const elapsedSec = Math.round((prog / 100) * totalSec);
  const fmt = (n: number) => `${String(Math.floor(n / 60)).padStart(2, "0")}:${String(n % 60).padStart(2, "0")}`;
  const timeLabel = `${fmt(elapsedSec)} / ${fmt(totalSec)}`;

  const sceneIdx = Math.min(scenes.length - 1, Math.floor((prog / 100) * scenes.length));
  const scene = scenes[sceneIdx] ?? scenes[0];

  /* True Horizontal Landscape Cinema Mode inside .phone.is-landscape */
  if (landscapeVideo) {
    return (
      <div className="cinema-wrap">
        <div className="row between">
          <div className="row" style={{ gap: 8 }}>
            <h1 className="h3" style={{ color: "#ffffff" }}>{videoTitle}</h1>
            <span className="chip mint">16:9 Ngang</span>
          </div>
          <button
            type="button"
            className="btn-soft sm"
            style={{ background: "rgba(255,255,255,0.14)", borderColor: "rgba(255,255,255,0.28)", color: "#ffffff" }}
            onClick={() => setLandscapeVideo(false)}
          >
            <Icon name="minimize" size={15} /> Thu nhỏ / Dọc lại
          </button>
        </div>

        <div className="cinema-stage">
          <img className="cinema-stage-art" src={videoArt} alt="" aria-hidden="true" />
          {!playing && (
            <button
              type="button"
              className="round-btn"
              style={{ width: 64, height: 64, borderRadius: 32, marginTop: 8, background: "#ffffff", color: "#1d4ed8" }}
              aria-label="Phát video"
              onClick={handlePlayToggle}
            >
              <Icon name="play" size={28} fill="currentColor" />
            </button>
          )}
          {captionsEnabled && scene && <div className="cinema-cc">{scene.narration}</div>}
        </div>

        <div className="row" style={{ gap: 10 }}>
          <button
            type="button"
            className="ccb on"
            style={{
              border: 0,
              borderRadius: 10,
              minHeight: 34,
              padding: "6px 10px",
              background: "#2563eb",
              color: "#ffffff",
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
            }}
            aria-label={playing ? "Tạm dừng" : "Phát"}
            onClick={handlePlayToggle}
          >
            <Icon name={playing ? "pause" : "play"} size={15} fill="currentColor" />
          </button>
          <div className="grow">
            <Progress value={prog} />
          </div>
          <span className="tiny timer-num" style={{ color: "#f8fafc" }}>{timeLabel}</span>
          <button
            type="button"
            className={`chip ${captionsEnabled ? "on" : "line"}`}
            aria-pressed={captionsEnabled}
            onClick={() => setCaptionsEnabled(!captionsEnabled)}
          >
            CC
          </button>
          <button
            type="button"
            className="round-btn"
            style={{ width: 36, height: 36, background: "rgba(255,255,255,0.14)", borderColor: "rgba(255,255,255,0.25)", color: "#ffffff" }}
            aria-label={bgmMuted ? "Bật âm thanh nền" : "Tắt âm thanh nền"}
            onClick={() => setBgmMuted(!bgmMuted)}
          >
            <Icon name={bgmMuted ? "volume-off" : "volume"} size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <TopBar
        title="Xem video câu chuyện"
        onBack={() => nav("/p01-lesson-library")}
        right={
          <button
            type="button"
            className="round-btn"
            aria-label="Xoay ngang toàn màn hình"
            onClick={() => setLandscapeVideo(true)}
          >
            <Icon name="maximize" size={18} />
          </button>
        }
      />
      <StepChips current={6} optionalSkipped={skippedOptionalSetup} />

      <div className="row between">
        <h1 className="h2">{videoTitle}</h1>
        <span className="chip mint">Cảnh {sceneIdx + 1}/{scenes.length}</span>
      </div>

      <div className="player">
        <img className="player-art" src={videoArt} alt="" aria-hidden="true" />
        {!playing && (
          <button type="button" className="play" aria-label="Phát video" onClick={handlePlayToggle}>
            <Icon name="play" size={26} fill="currentColor" />
          </button>
        )}
        {captionsEnabled && scene && <div className="cc">{scene.narration}</div>}
        <div className="ctl">
          <button type="button" className="ccb on" aria-label={playing ? "Tạm dừng" : "Phát"} onClick={handlePlayToggle}>
            <Icon name={playing ? "pause" : "play"} size={13} fill="currentColor" />
          </button>
          <Progress value={prog} />
          <span className="timer-pill timer-num">{timeLabel}</span>
          <button
            type="button"
            className={`ccb ${captionsEnabled ? "on" : ""}`}
            aria-pressed={captionsEnabled}
            onClick={() => setCaptionsEnabled(!captionsEnabled)}
          >
            CC
          </button>
          <button
            type="button"
            className={`ccb ${!bgmMuted ? "on" : ""}`}
            aria-label={bgmMuted ? "Bật nhạc nền" : "Tắt nhạc nền"}
            onClick={() => setBgmMuted(!bgmMuted)}
          >
            <Icon name={bgmMuted ? "volume-off" : "volume"} size={13} />
          </button>
        </div>
      </div>

      <Soft onClick={() => setLandscapeVideo(true)}>
        <Icon name="rotate" size={18} /> Xoay ngang / Toàn màn hình (16:9)
      </Soft>

      <div className="card tight">
        <div className="row between">
          <div>
            <h2 className="h3">Tự động mở ngang khi phát</h2>
            <div className="tiny">Xoay khung xem 16:9 rộng rãi cho bé</div>
          </div>
          <Switch
            on={autoLandscapeOnPlay}
            label="Tự động mở ngang khi phát"
            onChange={() => setAutoLandscapeOnPlay(!autoLandscapeOnPlay)}
          />
        </div>
      </div>

      <Note tone="blue" icon="lock">
        Video phát riêng tư trong ứng dụng ở chất lượng HD. Không chia sẻ công khai ra bên ngoài.
      </Note>

      <div className="cta-bar">
        <Btn
          tone="mint"
          onClick={() => {
            setLandscapeVideo(false);
            nav("/p08b-outdoor-activity");
          }}
        >
          Tiếp tục: Khám phá hoạt động ngoài đời
        </Btn>
        <Soft onClick={() => setActiveSheet("REPORT_UNSUITABLE")}>
          <Icon name="refresh" size={16} /> Báo chưa phù hợp · Tạo lại ({2 - videoRegenCount}/2)
        </Soft>
      </div>
    </div>
  );
}

/* =====================================================================
   P08b · Cùng khám phá hoạt động ngoài đời (Trang riêng)
   ===================================================================== */
export function P08bOutdoorActivityPage() {
  const nav = useNavigate();
  const { lessons, selectedLessonId, selectedActivityId, setHasActiveRun } = useParent();
  const lesson = lessons.find((l) => l.id === selectedLessonId) ?? lessons[0];
  const activities = lesson.outdoorActivities;
  const activity = activities.find((a) => a.id === selectedActivityId) ?? activities[0];

  const [done, setDone] = useState<boolean[]>([false, false, false]);
  const [kidView, setKidView] = useState(false);

  if (!activity) return null;

  const checklistSteps = [
    {
      title: "Chuẩn bị cùng bố mẹ",
      detail: activity.materials.replace(/^Vật liệu:\s*/, ""),
      icon: "folder" as const,
    },
    {
      title: "Thực hiện khám phá",
      detail: activity.firstStep.replace(/^Bước \d+:\s*/, ""),
      icon: "leaf" as const,
    },
    {
      title: "Khoe thành quả",
      detail: "Kể lại điều thú vị bé vừa quan sát được cùng bố mẹ",
      icon: "star" as const,
    },
  ];

  const doneCount = done.filter(Boolean).length;

  return (
    <div className="page">
      <TopBar title="Hoạt động ngoài đời thật" onBack={() => nav("/p08-video-and-activities")} />

      <div className="card row">
        <IconBadge name="sun" tone="accent" size={50} />
        <div className="grow">
          <h1 className="h2">{activity.title}</h1>
          <span className="chip amber" style={{ marginTop: 6 }}>Hoạt động đi kèm đã chọn</span>
        </div>
      </div>
      <img className="outdoor-art" src="/illustrations/garden-discovery.webp" alt="Bé khám phá bướm trong vườn cùng bạn diều giấy" />

      <div className="card stack">
        <h2 className="h2">Dụng cụ chuẩn bị</h2>
        <div className="row wrap">
          {activity.materials
            .replace(/^Vật liệu:\s*/, "")
            .split(",")
            .map((m) => (
              <span key={m} className="chip mint">{m.trim()}</span>
            ))}
        </div>
      </div>

      {activity.safetyNote && (
        <Note tone="amber" icon="shield">
          <strong>Lưu ý an toàn:</strong> {activity.safetyNote}
        </Note>
      )}

      <div className="row between">
        <h2 className="h2">3 bước thực hiện ({doneCount}/3)</h2>
        <div className="row" style={{ gap: 6 }}>
          <span className="tiny">Chế độ cho bé</span>
          <Switch on={kidView} label="Chế độ đưa máy cho bé" onChange={() => setKidView(!kidView)} />
        </div>
      </div>

      <Progress value={(doneCount / 3) * 100} tone="mint" />

      <div className="stack">
        {checklistSteps.map((s, idx) => {
          const isChecked = done[idx];
          return (
            <button
              key={s.title}
              type="button"
              className={`kid-step ${kidView ? "large" : ""} ${isChecked ? "done" : ""}`}
              aria-pressed={isChecked}
              onClick={() => setDone(done.map((d, j) => (j === idx ? !d : d)))}
            >
              <IconBadge name={s.icon} tone={isChecked ? "mint" : "primary"} size={kidView ? 48 : 42} />
              <span className="grow">
                <span className="h3" style={{ display: "block", fontSize: kidView ? 16 : 14.5 }}>{s.title}</span>
                <span className="sub" style={{ display: "block", marginTop: 2 }}>{s.detail}</span>
              </span>
              <span className="ck"><Icon name="check" size={18} strokeWidth={3} /></span>
            </button>
          );
        })}
      </div>

      <div className="cta-bar">
        <Btn
          tone="mint"
          onClick={() => {
            setHasActiveRun(false);
            nav("/p08c-session-feedback");
          }}
        >
          <Icon name="check" size={18} /> Hoàn tất hoạt động &amp; Tiếp tục
        </Btn>
      </div>
    </div>
  );
}

/* =====================================================================
   P08c · Điểm kết thúc luồng — Đánh giá phiên & Về thẳng Trang chủ
   ===================================================================== */
const QUICK_FEEDBACK_TAGS = ["Bé rất thích", "Dễ thực hiện", "Hình ảnh sinh động", "Âm thanh rõ"];

export function P08cSessionFeedbackPage() {
  const nav = useNavigate();
  const { sendFeedback, setHasActiveRun, showToast } = useParent();
  const [rating, setRating] = useState(5);
  const [selectedTags, setSelectedTags] = useState<string[]>(["Bé rất thích"]);
  const [note, setNote] = useState("");

  const toggleTag = (t: string) => {
    setSelectedTags((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  };

  const ratingLabel =
    rating === 5
      ? "5/5 · Rất tuyệt vời!"
      : rating === 4
      ? "4/5 · Hài lòng"
      : rating === 3
      ? "3/5 · Bình thường"
      : rating === 2
      ? "2/5 · Cần cải thiện"
      : "1/5 · Chưa hài lòng";

  return (
    <div className="page">
      <TopBar title="Đánh giá buổi kể chuyện" onBack={() => nav("/p08b-outdoor-activity")} />

      <div className="card stack" style={{ alignItems: "center", textAlign: "center" }}>
        <img className="complete-art" src="/illustrations/garden-discovery.webp" alt="Bé vui vẻ khám phá thiên nhiên" />
        <h1 className="h1 center">Hoàn tất phiên kể chuyện!</h1>
        <p className="sub center">Bố mẹ hãy chia sẻ cảm nhận để Sketch2Life phục vụ gia đình tốt hơn nhé.</p>

        <div className="star-row" role="group" aria-label="Đánh giá số sao">
          {[1, 2, 3, 4, 5].map((n) => {
            const active = n <= rating;
            return (
              <button
                key={n}
                type="button"
                className={`star-btn ${active ? "on" : ""}`}
                aria-label={`${n} sao`}
                aria-pressed={rating === n}
                onClick={() => setRating(n)}
              >
                <Icon
                  name="star"
                  size={26}
                  fill={active ? "#fbbf24" : "none"}
                  color={active ? "#d97706" : "var(--ink-3)"}
                />
              </button>
            );
          })}
        </div>
        <span className="chip amber">{ratingLabel}</span>
      </div>

      <div className="card stack">
        <h2 className="h2">Cảm nhận nhanh</h2>
        <div className="row wrap">
          {QUICK_FEEDBACK_TAGS.map((t) => {
            const on = selectedTags.includes(t);
            return (
              <button
                key={t}
                type="button"
                className={`chip ${on ? "on" : "line"}`}
                aria-pressed={on}
                onClick={() => toggleTag(t)}
              >
                {on && <Icon name="check" size={12} strokeWidth={3} />}
                {t}
              </button>
            );
          })}
        </div>

        <div>
          <label className="field-label" htmlFor="session-feedback-note">Ghi chú thêm của bố mẹ (tùy chọn)</label>
          <textarea
            id="session-feedback-note"
            className="textarea"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Chia sẻ thêm trải nghiệm của bé sau khi xem phim và khám phá..."
          />
        </div>
      </div>

      <div className="cta-bar">
        <Btn
          tone="mint"
          onClick={() => {
            const summary = `[${rating} sao] ${selectedTags.join(", ")}${note.trim() ? ` — ${note.trim()}` : ""}`;
            sendFeedback(summary, true);
            setHasActiveRun(false);
            showToast("Cảm ơn bố mẹ! Đã lưu đánh giá và kết thúc phiên.", "ok");
            nav("/p01-lesson-library");
          }}
        >
          <Icon name="check" size={18} /> Gửi đánh giá &amp; Về trang chủ
        </Btn>
        <Soft
          onClick={() => {
            setHasActiveRun(false);
            nav("/p01-lesson-library");
          }}
        >
          Bỏ qua &amp; Về trang chủ
        </Soft>
      </div>
    </div>
  );
}

/* =====================================================================
   P09 · Lịch sử câu chuyện (Đã tách hẳn FAQ sang cuối Trang chủ)
   ===================================================================== */
export function P09HistoryFeedbackPage() {
  const nav = useNavigate();
  const [filter, setFilter] = useState<"ALL" | "ACTIVE" | "COMPLETED" | "CLOSED">("ALL");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [showAllFeedback, setShowAllFeedback] = useState(false);
  const {
    runHistory,
    feedbackMessages,
    historyDeleted,
    restoreRunHistoryDemo,
    deleteRunRecordLifecycle,
    resolve144hRun,
    setActiveSheet,
    showToast,
  } = useParent();

  const allRuns = historyDeleted ? [] : runHistory.filter((r) => r.lifecycleState !== "DELETED");
  const parentFeedback = feedbackMessages.filter((message) => message.sender === "Phụ huynh").slice().reverse();
  const visibleFeedback = showAllFeedback ? parentFeedback : parentFeedback.slice(0, 2);
  const visible = allRuns.filter((r) => {
    if (filter === "ALL") return true;
    if (filter === "ACTIVE") return r.lifecycleState === "VIDEO_READY_144H";
    if (filter === "COMPLETED") return r.lifecycleState === "COMPLETED";
    return r.lifecycleState === "ABANDONED_168H" || r.lifecycleState === "DELETE_PENDING";
  });

  const selectedRun = visible.find((r) => r.id === selectedRunId) ?? visible[0] ?? null;

  const chip = (s: string) =>
    s === "COMPLETED"
      ? { c: "mint", t: "Hoàn thành" }
      : s === "VIDEO_READY_144H"
      ? { c: "amber", t: "Đang mở (144h)" }
      : s === "ABANDONED_168H"
      ? { c: "line", t: "Đã đóng (168h)" }
      : { c: "red", t: "Đang xóa" };

  return (
    <div className="page">
      <TopBar
        title="Lịch sử câu chuyện"
        back={false}
        right={
          <button type="button" className="round-btn" aria-label="Thông báo" onClick={() => setActiveSheet("NOTIFICATIONS")}>
            <Icon name="bell" size={18} />
          </button>
        }
      />

      <section className="parent-feedback-history" aria-labelledby="parent-feedback-history-title">
        <div className="parent-feedback-history-head">
          <h2 id="parent-feedback-history-title" className="h2">Phản hồi đã gửi</h2>
          <span className="parent-feedback-history-count" aria-label={`${parentFeedback.length} phản hồi`}>{parentFeedback.length}</span>
        </div>
        {parentFeedback.length === 0 ? (
          <p className="tiny">Đánh giá sau hoạt động sẽ hiển thị tại đây.</p>
        ) : (
          <div className="parent-feedback-history-list">
            {visibleFeedback.map((message) => (
              <article key={message.id} className="parent-feedback-history-item">
                <span className="parent-feedback-history-icon" aria-hidden="true"><Icon name="message" size={17} /></span>
                <div className="parent-feedback-history-copy">
                  <p>{message.text}</p>
                  <div className="parent-feedback-history-meta">
                    <span>{message.date}</span>
                    <span className="parent-feedback-history-status"><Icon name="check" size={13} /> Đã ghi nhận</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
        {parentFeedback.length > 2 && (
          <button type="button" className="parent-feedback-history-more" onClick={() => setShowAllFeedback((current) => !current)}>
            {showAllFeedback ? "Thu gọn" : "Xem tất cả phản hồi"}
          </button>
        )}
      </section>

      <div className="row between">
        <h1 className="h2">Các câu chuyện của bé</h1>
        <span className="tiny">{visible.length} câu chuyện</span>
      </div>

      <div className="row wrap">
        {(
          [
            { k: "ALL", label: "Tất cả" },
            { k: "ACTIVE", label: "Đang mở" },
            { k: "COMPLETED", label: "Hoàn thành" },
            { k: "CLOSED", label: "Đã đóng" },
          ] as const
        ).map((f) => (
          <button
            key={f.k}
            type="button"
            className={`chip ${filter === f.k ? "on" : "line"}`}
            onClick={() => setFilter(f.k)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {selectedRun && (
        <div className="card stack selected-run-card">
          <div className="hist">
            <span className="history-cover" aria-hidden="true">
              <img src={storyArtSrc(selectedRun.title)} alt="" />
            </span>
            <div className="grow">
              <div className="row between wrap" style={{ gap: 6 }}>
                <h2 className="h2">{cleanTitle(selectedRun.title)}</h2>
                <span className={`chip ${chip(selectedRun.lifecycleState).c}`}>
                  {chip(selectedRun.lifecycleState).t}
                </span>
              </div>
              <div className="tiny" style={{ marginTop: 4 }}>{selectedRun.childName} · {selectedRun.date} · 5 cảnh</div>
            </div>
          </div>
          <p className="sub">{selectedRun.note}</p>
          <div className="row wrap">
            <Btn small onClick={() => nav("/p08-video-and-activities")}>
              <Icon name="play" size={14} fill="#fff" /> Xem lại
            </Btn>
            <Soft
              small
              onClick={() => {
                showToast("Mở kịch bản để tạo lại video.", "info");
                nav("/p06-story-review");
              }}
            >
              <Icon name="refresh" size={14} /> Tạo lại
            </Soft>
            {selectedRun.lifecycleState === "VIDEO_READY_144H" && (
              <Soft small onClick={() => resolve144hRun(selectedRun.id, "COMPLETE")}>
                <Icon name="check" size={14} /> Hoàn tất
              </Soft>
            )}
            {selectedRun.lifecycleState !== "DELETE_PENDING" && (
              <Soft small red onClick={() => deleteRunRecordLifecycle(selectedRun.id)}>
                <Icon name="trash" size={14} /> Xóa
              </Soft>
            )}
          </div>
        </div>
      )}

      {visible.length === 0 ? (
        <div className="card stack" style={{ alignItems: "center", textAlign: "center" }}>
          <IconBadge name="book" tone="neutral" size={52} />
          <h2 className="h3">Chưa có câu chuyện trong mục này</h2>
          <p className="sub">Bố mẹ có thể đổi bộ lọc hoặc khôi phục dữ liệu mẫu bên dưới.</p>
          <Soft small onClick={restoreRunHistoryDemo}>Khôi phục dữ liệu mẫu</Soft>
        </div>
      ) : (
        <>
          <h2 className="h2">Danh sách câu chuyện</h2>
          <div className="stack">
            {visible.map((r, idx) => {
              const c = chip(r.lifecycleState);
              const isSel = selectedRun?.id === r.id;
              return (
                <button
                  key={r.id}
                  type="button"
                  className={`act-row ${isSel ? "on" : ""}`}
                  onClick={() => setSelectedRunId(r.id)}
                >
                  <span className="history-thumb" aria-hidden="true">
                    <img src={storyArtSrc(r.title)} alt="" />
                  </span>
                  <span className="grow">
                    <span className="h3" style={{ display: "block" }}>{cleanTitle(r.title)}</span>
                    <span className="tiny" style={{ display: "block" }}>{r.childName} · {r.date}</span>
                  </span>
                  <span className={`chip ${c.c}`}>{c.t}</span>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

/* =====================================================================
   P10 · Hồ sơ của bé — Danh sách / Bảng tối giản
   ===================================================================== */
export function P10ChildProfilesPage() {
  const nav = useNavigate();
  const { profiles, selectedProfileId, setActiveSheet } = useParent();
  const visibleProfiles = profiles.filter((p) => p.deletionStatus !== "DELETED");

  return (
    <div className="page">
      <TopBar
        title="Hồ sơ của bé"
        back={false}
        right={
          <button type="button" className="chip on" onClick={() => setActiveSheet("ADD_CHILD")}>
            <Icon name="plus" size={14} /> Thêm
          </button>
        }
      />

      {visibleProfiles.length === 0 ? (
        <div className="card stack" style={{ alignItems: "center", textAlign: "center" }}>
          <IconBadge name="user" tone="primary" size={52} />
          <p className="sub">Chưa có hồ sơ nào. Bấm nút Thêm để tạo hồ sơ cho bé.</p>
          <Btn small onClick={() => setActiveSheet("ADD_CHILD")}>
            <Icon name="plus" size={16} /> Thêm hồ sơ mới
          </Btn>
        </div>
      ) : (
        <ul className="profile-table" aria-label="Danh sách hồ sơ trẻ">
          {visibleProfiles.map((p, index) => {
            const ageLabel = compactAgeLabel(p.ageMonths);
            const isSelected = selectedProfileId === p.id && !p.archived;
            const statusLabel = isSelected ? "Đang dùng" : p.archived ? "Đã lưu" : null;
            return (
              <li key={p.id} className="profile-list-item">
                <button
                  type="button"
                  className={`profile-row ${isSelected ? "is-selected" : ""}`}
                  aria-label={`Mở hồ sơ ${p.displayName}, ${ageLabel}${statusLabel ? `, ${statusLabel.toLowerCase()}` : ""}`}
                  onClick={() => nav(`/p10-child-profiles/${p.id}`)}
                >
                  <span className="profile-avatar"><ChildAvatarSvg variant={index} size={42} /></span>
                  <span className="profile-row-copy">
                    <span className="h3 profile-name">{p.displayName}</span>
                    <span className="profile-age">{ageLabel}</span>
                  </span>
                  {statusLabel && <span className={`profile-status ${isSelected ? "is-current" : "is-archived"}`}>{statusLabel}</span>}
                  <Icon name="chevron-right" size={18} color="var(--ink-3)" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/* =====================================================================
   P10 Detail · Chi tiết & Chỉnh sửa từng hồ sơ trẻ (/p10-child-profiles/:childId)
   ===================================================================== */
export function P10ChildProfileDetailPage() {
  const nav = useNavigate();
  const { childId } = useParams<{ childId: string }>();
  const {
    profiles,
    selectedProfileId,
    setSelectedProfileId,
    updateProfile,
    toggleProfileConsent,
    archiveProfile,
    restoreProfile,
    deleteProfileLifecycle,
    showToast,
  } = useParent();

  const childIdx = profiles.findIndex((p) => p.id === childId);
  const child = childIdx >= 0 ? profiles[childIdx] : undefined;

  const [nameDraft, setNameDraft] = useState(child?.displayName ?? "");
  const [monthsDraft, setMonthsDraft] = useState(String(child?.ageMonths ?? 60));
  const [interestsDraft, setInterestsDraft] = useState(child?.interests.join(", ") ?? "");
  const [learningDraft, setLearningDraft] = useState(child?.learningNotes ?? "");
  const [supportDraft, setSupportDraft] = useState(child?.supportNeedsNote ?? "");
  const [confirmDel, setConfirmDel] = useState(false);

  useEffect(() => {
    if (!child) return;
    setNameDraft(child.displayName);
    setMonthsDraft(String(child.ageMonths));
    setInterestsDraft(child.interests.join(", "));
    setLearningDraft(child.learningNotes);
    setSupportDraft(child.supportNeedsNote);
  }, [child]);

  if (!child || child.deletionStatus === "DELETED") {
    return (
      <div className="page">
        <TopBar title="Hồ sơ của bé" onBack={() => nav("/p10-child-profiles")} />
        <div className="card stack" style={{ alignItems: "center", textAlign: "center" }}>
          <IconBadge name="user" tone="neutral" size={52} />
          <h1 className="h2">Không tìm thấy hồ sơ</h1>
          <Btn small onClick={() => nav("/p10-child-profiles")}>Quay lại danh sách</Btn>
        </div>
      </div>
    );
  }

  const years = Math.max(3, Math.floor((Number(monthsDraft) || child.ageMonths) / 12));
  const isDefault = selectedProfileId === child.id && !child.archived;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const m = Math.max(36, Math.min(155, Number(monthsDraft) || child.ageMonths));
    const ints = interestsDraft
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
    updateProfile(
      child.id,
      nameDraft.trim() || child.displayName,
      m,
      learningDraft,
      supportDraft,
      ints.length > 0 ? ints : child.interests
    );
  };

  return (
    <div className="page">
      <TopBar title={child.displayName} onBack={() => nav("/p10-child-profiles")} />

      <div className="card row between">
        <div className="row">
          <span className="avatar" style={{ overflow: "hidden" }}>
            <ChildAvatarSvg variant={childIdx} size={48} />
          </span>
          <div>
            <h1 className="h2">{child.displayName}</h1>
            <div className="tiny">{child.ageLabel}</div>
          </div>
        </div>
        {isDefault ? (
          <span className="chip mint">Mặc định</span>
        ) : !child.archived ? (
          <Soft
            small
            onClick={() => {
              setSelectedProfileId(child.id);
              showToast(`Đã chọn ${child.displayName} làm hồ sơ mặc định.`, "ok");
            }}
          >
            Chọn mặc định
          </Soft>
        ) : (
          <span className="chip line">Đã lưu trữ</span>
        )}
      </div>

      {!isDefault && !child.archived && (
        <Soft
          onClick={() => {
            setSelectedProfileId(child.id);
            showToast(`Đã chọn ${child.displayName} làm hồ sơ mặc định.`, "ok");
          }}
        >
          <Icon name="check" size={16} /> Chọn làm hồ sơ mặc định
        </Soft>
      )}

      <form className="card stack" onSubmit={handleSave}>
        <h2 className="h2">Thông tin chi tiết</h2>

        <div>
          <label className="field-label" htmlFor="child-detail-name">Tên hiển thị của bé</label>
          <input
            id="child-detail-name"
            className="input"
            value={nameDraft}
            onChange={(e) => setNameDraft(e.target.value)}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="child-detail-months">Độ tuổi (36–155 tháng · {years} tuổi)</label>
          <input
            id="child-detail-months"
            className="input"
            type="number"
            min={36}
            max={155}
            value={monthsDraft}
            onChange={(e) => setMonthsDraft(e.target.value)}
          />
          <div className="row wrap" style={{ marginTop: 8 }}>
            {AGE_BANDS.map((b) => (
              <button
                key={b.key}
                type="button"
                className={`chip ${Number(monthsDraft) === b.months ? "on" : "line"}`}
                onClick={() => setMonthsDraft(String(b.months))}
              >
                {b.title}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="field-label" htmlFor="child-detail-interests">Sở thích (cách nhau bởi dấu phẩy)</label>
          <input
            id="child-detail-interests"
            className="input"
            value={interestsDraft}
            onChange={(e) => setInterestsDraft(e.target.value)}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="child-detail-learning">Quan sát học tập &amp; trải nghiệm</label>
          <textarea
            id="child-detail-learning"
            className="textarea"
            value={learningDraft}
            onChange={(e) => setLearningDraft(e.target.value)}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="child-detail-support">Ghi chú hỗ trợ riêng</label>
          <textarea
            id="child-detail-support"
            className="textarea"
            value={supportDraft}
            onChange={(e) => setSupportDraft(e.target.value)}
          />
          <div className="flat-box amber" style={{ marginTop: 8, fontSize: 12 }}>
            Mặc định ẩn khỏi AI và không dùng để suy diễn chẩn đoán.
          </div>
        </div>

        <Btn type="submit">Lưu thay đổi hồ sơ</Btn>
      </form>

      <div className="card stack">
        <div className="row between">
          <div className="grow">
            <h2 className="h3">Đồng ý xử lý dữ liệu học tập (Consent)</h2>
            <p className="sub">Cho phép hệ thống dùng nhóm tuổi và sở thích chung khi tạo câu chuyện{"\u00A0"}cho{"\u00A0"}bé.</p>
          </div>
          <Switch
            on={child.consentAccepted}
            label={`Đồng ý dữ liệu học tập cho ${child.displayName}`}
            onChange={() => toggleProfileConsent(child.id)}
          />
        </div>
        <div className="tiny">Cập nhật lần cuối: {child.consentUpdatedAt}</div>
      </div>

      <div className="cta-bar">
        {child.archived ? (
          <Btn tone="mint" onClick={() => restoreProfile(child.id)}>
            Khôi phục hồ sơ của bé
          </Btn>
        ) : (
          <Soft
            onClick={() => {
              archiveProfile(child.id);
              nav("/p10-child-profiles");
            }}
          >
            Lưu trữ hồ sơ
          </Soft>
        )}

        {confirmDel ? (
          <Btn
            tone="danger"
            onClick={() => {
              deleteProfileLifecycle(child.id);
              nav("/p10-child-profiles");
            }}
          >
            Xác nhận xóa vĩnh viễn hồ sơ
          </Btn>
        ) : (
          <Soft red onClick={() => setConfirmDel(true)}>
            <Icon name="trash" size={15} /> Xóa hồ sơ
          </Soft>
        )}
      </div>
    </div>
  );
}

/* =====================================================================
   P11 · Khởi động, giới thiệu, đăng nhập
   ===================================================================== */
export function P11AuthenticationPage() {
  const nav = useNavigate();
  const [stage, setStage] = useState<"splash" | "onb" | "auth">("splash");
  const [step, setStep] = useState(0);
  const [register, setRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { setIsAuthenticated, showToast } = useParent();

  const onb = [
    { art: <img className="onboarding-art" src="/illustrations/child-story-hero.webp" alt="Bé khoe bức tranh bướm cùng bạn diều giấy" />, t: "Nét vẽ của con thành câu chuyện", d: "Chụp tranh của bé để bắt đầu một câu chuyện riêng." },
    { art: <img className="onboarding-art" src="/illustrations/kite-ai-guide.webp" alt="Bạn diều giấy khám phá bức tranh" />, t: "Bé kể, AI giúp dựng phim", d: "Bé có thể kể bằng giọng nói hoặc nhập chữ. Bố mẹ duyệt trước khi tạo video." },
    { art: <img className="onboarding-art" src="/illustrations/garden-discovery.webp" alt="Bé khám phá bướm ngoài vườn" />, t: "Cùng khám phá ngoài đời", d: "Mỗi câu chuyện gợi một hoạt động an toàn để cả nhà cùng chơi." },
  ];

  const enter = async () => {
    setAuthError(null);
    if (isLocalPreview()) {
      setIsAuthenticated(true);
      showToast("Đang mở bản xem thử; dữ liệu không lưu vào backend.", "info");
      nav("/p01-lesson-library");
      return;
    }
    if (register) {
      setAuthError("Đăng ký tài khoản được xử lý bởi Firebase; ứng dụng hiện chưa có luồng tạo tài khoản.");
      return;
    }
    setSubmitting(true);
    try {
      await signInAndResolveRole("parent", email, pw);
      setIsAuthenticated(true);
      showToast("Đăng nhập thành công.", "ok");
      nav("/p01-lesson-library");
    } catch (cause) {
      setAuthError(backendMessage(cause));
    } finally {
      setSubmitting(false);
    }
  };

  if (stage === "splash") {
    return (
      <div className="splash">
        <div style={{ zIndex: 1 }}>
          <h1 style={{ margin: 0 }}><Wordmark size={44} /></h1>
          <p className="sub" style={{ marginTop: 8 }}>Mỗi nét vẽ đều có một câu chuyện đang chờ{"\u00A0"}được{"\u00A0"}kể…</p>
        </div>
        <img className="splash-art" src="/illustrations/child-story-hero.webp" alt="Bé và bạn diều giấy mở cuốn truyện từ bức tranh" />
        <div style={{ zIndex: 1, width: "100%" }}>
          <Btn onClick={() => setStage("onb")}>Bắt đầu thôi</Btn>
        </div>
        <span className="hill" aria-hidden="true" />
      </div>
    );
  }

  if (stage === "onb") {
    const s = onb[step];
    return (
      <div className="page onboarding-page" style={{ minHeight: "100%", justifyContent: "space-between", paddingTop: 20 }}>
        <div className="row between">
          <Wordmark size={22} />
          <button type="button" className="ghost-link" onClick={() => setStage("auth")}>Bỏ qua</button>
        </div>
        <div className="stack" style={{ alignItems: "center", textAlign: "center" }}>
          {s.art}
          <h1 className="h1">{s.t}</h1>
          <p className="sub">{s.d}</p>
        </div>
        <div className="stack">
          <div className="dots" aria-label={`Bước ${step + 1} trên 3`}>
            {onb.map((_, idx) => (
              <i key={idx} className={idx === step ? "on" : ""} />
            ))}
          </div>
          <Btn onClick={() => (step < 2 ? setStep(step + 1) : setStage("auth"))}>
            {step < 2 ? "Tiếp theo" : "Bắt đầu hành trình"}
          </Btn>
        </div>
      </div>
    );
  }

  return (
    <div className="page auth-page" style={{ paddingTop: 24 }}>
      <div className="stack" style={{ alignItems: "center", textAlign: "center" }}>
        <Wordmark size={34} />
        <img className="auth-art" src="/illustrations/kite-ai-guide.webp" alt="Bạn diều giấy chào đón gia đình" />
        <h1 className="h1">{register ? "Tạo tài khoản bố mẹ" : "Chào mừng bố mẹ"}</h1>
      </div>
      <form
        className="stack"
        onSubmit={(e) => {
          e.preventDefault();
          void enter();
        }}
      >
        <div>
          <label className="field-label" htmlFor="auth-email">Email đăng nhập</label>
          <input
            id="auth-email"
            className="input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="lan.nguyen@gmail.com"
            autoComplete="email"
          />
        </div>
        <div>
          <label className="field-label" htmlFor="auth-password">Mật khẩu</label>
          <input
            id="auth-password"
            className="input"
            type="password"
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            placeholder="Nhập mật khẩu"
            autoComplete={register ? "new-password" : "current-password"}
          />
        </div>
        <Btn type="submit" disabled={submitting || (register && !isLocalPreview())}>{submitting ? "Đang xác thực…" : isLocalPreview() ? "Mở bản xem thử" : register ? "Tạo tài khoản" : "Đăng nhập"}</Btn>
      </form>
      {authError && <BackendNotice title="Không thể đăng nhập" tone="error">{authError}</BackendNotice>}
      {!isLocalPreview() && !hasFirebaseAuthBridge() && <BackendNotice title="Firebase Authentication chưa được nối" tone="warn">Backend yêu cầu Firebase ID token. Không có tài khoản mẫu hoặc role tự chọn trong môi trường thật.</BackendNotice>}
      {isLocalPreview() && <BackendModeNotice roleLabel="Phụ huynh" />}
      <button type="button" className="ghost-link" onClick={() => setRegister(!register)}>
        {register ? "Đã có tài khoản? Đăng nhập" : "Chưa có tài khoản? Đăng ký"}
      </button>
    </div>
  );
}

/* =====================================================================
   P12 · Lượt tạo video
   ===================================================================== */
export function P12VideoQuotaPage() {
  const [pack, setPack] = useState(1);
  const [method, setMethod] = useState<"MoMo" | "VNPAY">("MoMo");
  const [showAll, setShowAll] = useState(false);
  const {
    quotaRemaining,
    quotaUsed,
    quotaTotal,
    simulateTopupPurchase,
    paymentStatus,
    usageLedger,
    includedQuotaRemaining,
    topupQuotaRemaining,
  } = useParent();

  const packs = [
    { n: 3, p: "29.000đ" },
    { n: 5, p: "45.000đ" },
    { n: 10, p: "79.000đ" },
  ];
  const R = 70;
  const C = 2 * Math.PI * R;
  const frac = quotaTotal > 0 ? quotaUsed / quotaTotal : 0;
  const rows = showAll ? usageLedger : usageLedger.slice(0, 3);

  return (
    <div className="page">
      <TopBar title="Lượt tạo video" back={false} />
      <div className="card stack" style={{ alignItems: "center" }}>
        <h1 className="h2">Số dư lượt tạo trong tháng</h1>
        <div className="gauge" role="img" aria-label={`Đã dùng ${quotaUsed} trên ${quotaTotal} lượt`}>
          <svg width="176" height="176" viewBox="0 0 176 176">
            <circle className="track" cx="88" cy="88" r={R} fill="none" strokeWidth="16" />
            <circle
              cx="88"
              cy="88"
              r={R}
              fill="none"
              stroke={quotaRemaining === 0 ? "#ef4444" : "#2563eb"}
              strokeWidth="16"
              strokeLinecap="round"
              strokeDasharray={`${C * frac} ${C}`}
            />
          </svg>
          <div className="mid">
            <span className="big">{quotaUsed}/{quotaTotal}</span>
            <span className="tiny">lượt đã dùng</span>
          </div>
        </div>
        <div className="row wrap" style={{ justifyContent: "center" }}>
          <span className="chip">Định kỳ còn {includedQuotaRemaining}</span>
          <span className="chip amber">Mua thêm còn {topupQuotaRemaining}</span>
        </div>
        {quotaRemaining === 0 && (
          <Note tone="red" icon="lock">
            Đã hết lượt. Mua thêm gói lượt bên dưới để tạo video mới.
          </Note>
        )}
      </div>

      <h2 className="h2">Mua thêm lượt</h2>
      <div className="row">
        {packs.map((p, idx) => (
          <button key={p.n} type="button" className={`pack ${pack === idx ? "on" : ""}`} onClick={() => setPack(idx)}>
            <span className="n">+{p.n}</span>
            <span className="p">{p.p}</span>
          </button>
        ))}
      </div>
      <div className="row wrap">
        {(["MoMo", "VNPAY"] as const).map((m) => (
          <button key={m} type="button" className={`chip ${method === m ? "on" : "line"}`} onClick={() => setMethod(m)}>
            {m}
          </button>
        ))}
        {paymentStatus === "PENDING" && <span className="chip amber">Đang xử lý…</span>}
        {paymentStatus === "SUCCEEDED" && <span className="chip mint">Giao dịch minh họa xong</span>}
        {paymentStatus === "FAILED" && <span className="chip red">Chưa thanh toán được</span>}
      </div>
      <Note tone="amber" icon="info">Bản xem thử: thanh toán chỉ mô phỏng, không phát sinh giao dịch thật.</Note>
      <Btn
        tone="amber"
        disabled={paymentStatus === "PENDING"}
        onClick={() => simulateTopupPurchase(packs[pack].n, method, "SUCCEEDED")}
      >
        Thử mua +{packs[pack].n} lượt ({packs[pack].p})
      </Btn>

      <div className="sec-head">
        <h2 className="h2">Lịch sử sử dụng lượt</h2>
        {usageLedger.length > 3 && (
          <button type="button" className="more" onClick={() => setShowAll(!showAll)}>
            {showAll ? "Thu gọn" : "Xem thêm"}
          </button>
        )}
      </div>
      <div className="card">
        {rows.map((l) => (
          <div key={l.id} className="ledger">
            <span className={`chip ${l.tone === "ok" ? "mint" : l.tone === "err" ? "red" : "amber"}`}>{l.delta}</span>
            <div className="grow">
              <div className="h3">{l.runTitle}</div>
              <div className="tiny">{l.date}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* =====================================================================
   P13 · Cài đặt tách riêng (Theme Light/Dark, Tài khoản, Mật khẩu, OTP, 2FA, Đăng xuất)
   ===================================================================== */
type SettingsSubView = "main" | "account" | "privacy" | "password" | "forgot" | "twofa";

export function P13SettingsPage() {
  const nav = useNavigate();
  const location = useLocation();
  const childProfilesRef = useRef<HTMLDivElement>(null);
  const {
    profiles,
    selectedProfileId,
    setActiveSheet,
    theme,
    setTheme,
    captionsEnabled,
    setCaptionsEnabled,
    pushEndpointActive,
    setPushEndpointActive,
    autoLandscapeOnPlay,
    setAutoLandscapeOnPlay,
    setIsAuthenticated,
    showToast,
  } = useParent();

  const [subView, setSubView] = useState<SettingsSubView>("main");
  const visibleProfiles = profiles.filter((profile) => profile.deletionStatus !== "DELETED");

  useEffect(() => {
    if (location.hash === "#child-profiles") {
      childProfilesRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [location.hash]);

  // Account state
  const [parentName, setParentName] = useState("Nguyễn Phương Lan");
  const [parentEmail, setParentEmail] = useState("lan.nguyen@gmail.com");

  // Password state
  const [curPw, setCurPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwError, setPwError] = useState("");

  // Forgot password OTP state
  const [recoveryEmail, setRecoveryEmail] = useState("lan.nguyen@gmail.com");
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [resetPw, setResetPw] = useState("");

  // 2FA state
  const [twoFaEnabled, setTwoFaEnabled] = useState(true);
  const [twoFaMethod, setTwoFaMethod] = useState<"APP" | "EMAIL">("APP");
  const [backupCodes, setBackupCodes] = useState([
    "S2L-8492-K1",
    "S2L-3910-M7",
    "S2L-6204-P3",
    "S2L-1589-V9",
  ]);

  if (subView === "account") {
    return (
      <div className="page">
        <TopBar title="Tài khoản & Tùy chọn" onBack={() => setSubView("main")} />
        <form
          className="card stack"
          onSubmit={(e) => {
            e.preventDefault();
            showToast("Đã cập nhật thông tin tài khoản phụ huynh.", "ok");
          }}
        >
          <h1 className="h2">Thông tin phụ huynh</h1>
          <div>
            <label className="field-label" htmlFor="acc-name">Họ và tên</label>
            <input id="acc-name" className="input" value={parentName} onChange={(e) => setParentName(e.target.value)} />
          </div>
          <div>
            <label className="field-label" htmlFor="acc-email">Email liên hệ</label>
            <input id="acc-email" type="email" className="input" value={parentEmail} onChange={(e) => setParentEmail(e.target.value)} />
          </div>
          <Btn type="submit">Lưu thông tin</Btn>
        </form>

        <div className="card">
          <div className="list-item">
            <IconBadge name="bell" tone="primary" />
            <span className="grow">
              <span className="h3" style={{ display: "block" }}>Thông báo đẩy</span>
              <span className="tiny" style={{ display: "block" }}>Khi video xong &amp; nhắc hạn 144h/168h</span>
            </span>
            <Switch on={pushEndpointActive} label="Nhận thông báo đẩy" onChange={() => setPushEndpointActive(!pushEndpointActive)} />
          </div>
          <div className="list-item">
            <IconBadge name="video" tone="accent" />
            <span className="grow">
              <span className="h3" style={{ display: "block" }}>Phụ đề tiếng Việt mặc định</span>
              <span className="tiny" style={{ display: "block" }}>Hiển thị lời kể trên khung phát video</span>
            </span>
            <Switch on={captionsEnabled} label="Phụ đề tiếng Việt mặc định" onChange={() => setCaptionsEnabled(!captionsEnabled)} />
          </div>
          <div className="list-item">
            <IconBadge name="rotate" tone="mint" />
            <span className="grow">
              <span className="h3" style={{ display: "block" }}>Tự mở ngang 16:9 khi phát</span>
              <span className="tiny" style={{ display: "block" }}>Tối ưu không gian xem video cho bé</span>
            </span>
            <Switch on={autoLandscapeOnPlay} label="Tự động mở ngang khi phát" onChange={() => setAutoLandscapeOnPlay(!autoLandscapeOnPlay)} />
          </div>
        </div>
      </div>
    );
  }

  if (subView === "privacy") {
    return (
      <div className="page">
        <TopBar title="Quyền riêng tư & Dữ liệu AI" onBack={() => setSubView("main")} />
        <h1 className="h2">Bảo vệ dữ liệu trẻ em</h1>
        <Note tone="blue" icon="shield">
          Tài khoản Phụ huynh tách biệt với tài khoản Trường học và Giáo viên.
        </Note>
        <div className="card stack">
          <div className="flat-box mint">
            <h2 className="h3">Ẩn tên thật khỏi AI</h2>
            <p className="sub" style={{ marginTop: 4 }}>
              Tên thật của bé được ẩn trước khi gửi nội dung tới AI.
            </p>
          </div>
          <div className="flat-box amber">
            <h2 className="h3">Ghi chú hỗ trợ không gửi cho AI</h2>
            <p className="sub" style={{ marginTop: 4 }}>
              Chỉ phụ huynh xem ghi chú này; không gửi cho AI.
            </p>
          </div>
        </div>

        <h2 className="h2">Quyền truy cập hồ sơ</h2>
        <Note tone="blue" icon="shield">
          Hồ sơ trẻ chỉ thuộc tài khoản Phụ huynh, không chia sẻ giữa các tài khoản.
        </Note>
      </div>
    );
  }

  if (subView === "password") {
    return (
      <div className="page">
        <TopBar title="Đổi mật khẩu" onBack={() => setSubView("main")} />
        <form
          className="card stack"
          onSubmit={(e) => {
            e.preventDefault();
            if (!curPw || !newPw) {
              setPwError("Vui lòng nhập đầy đủ mật khẩu hiện tại và mật khẩu mới.");
              return;
            }
            if (newPw.length < 8) {
              setPwError("Mật khẩu mới cần có ít nhất 8 ký tự.");
              return;
            }
            if (newPw !== confirmPw) {
              setPwError("Mật khẩu nhập lại chưa trùng khớp.");
              return;
            }
            setPwError("");
            setCurPw("");
            setNewPw("");
            setConfirmPw("");
            showToast("Đã đổi mật khẩu thành công.", "ok");
            setSubView("main");
          }}
        >
          <h1 className="h2">Cập nhật mật khẩu đăng nhập</h1>
          <div>
            <label className="field-label" htmlFor="cur-pw">Mật khẩu hiện tại *</label>
            <input
              id="cur-pw"
              type="password"
              className="input"
              value={curPw}
              onChange={(e) => setCurPw(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <div>
            <label className="field-label" htmlFor="new-pw">Mật khẩu mới (tối thiểu 8 ký tự) *</label>
            <input
              id="new-pw"
              type="password"
              className="input"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <div>
            <label className="field-label" htmlFor="confirm-pw">Nhập lại mật khẩu mới *</label>
            <input
              id="confirm-pw"
              type="password"
              className="input"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          {pwError && (
            <div role="alert">
              <Note tone="red" icon="alert">{pwError}</Note>
            </div>
          )}
          <Btn type="submit">Lưu mật khẩu mới</Btn>
        </form>
      </div>
    );
  }

  if (subView === "forgot") {
    return (
      <div className="page">
        <TopBar title="Quên mật khẩu" onBack={() => setSubView("main")} />
        <div className="card stack">
          <h1 className="h2">Khôi phục bằng mã OTP</h1>
          <p className="sub">Hệ thống sẽ gửi mã xác thực 6 chữ số tới địa chỉ email đăng ký của bố mẹ.</p>
          <div>
            <label className="field-label" htmlFor="recovery-email">Email đăng ký</label>
            <input
              id="recovery-email"
              type="email"
              className="input"
              value={recoveryEmail}
              onChange={(e) => setRecoveryEmail(e.target.value)}
            />
          </div>
          <Soft
            onClick={() => {
              setOtpSent(true);
              showToast(`Đã gửi mã OTP khôi phục tới ${recoveryEmail}.`, "info");
            }}
          >
            <Icon name="message" size={16} /> {otpSent ? "Gửi lại mã OTP" : "Gửi mã OTP khôi phục"}
          </Soft>

          {otpSent && (
            <div className="stack" style={{ paddingTop: 8, borderTop: "1px dashed var(--line)" }}>
              <div>
                <label className="field-label" htmlFor="otp-input">Mã xác thực OTP (6 số)</label>
                <input
                  id="otp-input"
                  className="input"
                  inputMode="numeric"
                  placeholder="Ví dụ: 482910"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                />
              </div>
              <div>
                <label className="field-label" htmlFor="reset-pw-input">Mật khẩu mới</label>
                <input
                  id="reset-pw-input"
                  type="password"
                  className="input"
                  placeholder="Tối thiểu 8 ký tự"
                  value={resetPw}
                  onChange={(e) => setResetPw(e.target.value)}
                />
              </div>
              <Btn
                disabled={otpCode.trim().length < 4 || resetPw.length < 8}
                onClick={() => {
                  setOtpSent(false);
                  setOtpCode("");
                  setResetPw("");
                  showToast("Đã đặt lại mật khẩu thành công.", "ok");
                  setSubView("main");
                }}
              >
                Xác nhận đặt lại mật khẩu
              </Btn>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (subView === "twofa") {
    return (
      <div className="page">
        <TopBar title="Bảo mật 2 lớp (2FA)" onBack={() => setSubView("main")} />
        <div className="card stack">
          <div className="row between">
            <div>
              <h1 className="h2">Xác thực 2 lớp</h1>
              <p className="sub">Tăng cường bảo vệ tài khoản phụ huynh khi đăng nhập trên thiết bị mới.</p>
            </div>
            <Switch
              on={twoFaEnabled}
              label="Bật bảo mật 2 lớp"
              onChange={() => {
                const next = !twoFaEnabled;
                setTwoFaEnabled(next);
                showToast(next ? "Đã bật bảo mật 2 lớp (2FA)." : "Đã tắt bảo mật 2 lớp.", next ? "ok" : "warn");
              }}
            />
          </div>

          {twoFaEnabled && (
            <>
              <h2 className="h3">Phương thức nhận mã</h2>
              <div className="seg" role="radiogroup" aria-label="Phương thức 2FA">
                <button
                  type="button"
                  className={twoFaMethod === "APP" ? "on" : ""}
                  onClick={() => setTwoFaMethod("APP")}
                >
                  Authenticator
                </button>
                <button
                  type="button"
                  className={twoFaMethod === "EMAIL" ? "on" : ""}
                  onClick={() => setTwoFaMethod("EMAIL")}
                >
                  Email OTP
                </button>
              </div>
            </>
          )}
        </div>

        <div className="card stack">
          <div className="row between">
            <h2 className="h2">Mã khôi phục dự phòng</h2>
            <span className="chip mint">Dùng 1 lần</span>
          </div>
          <p className="sub">Lưu giữ các mã này ở nơi an toàn để đăng nhập khi không có điện thoại bên cạnh.</p>
          <div className="code-grid">
            {backupCodes.map((c) => (
              <span key={c} className="code-pill">{c}</span>
            ))}
          </div>
          <Soft
            small
            onClick={() => {
              setBackupCodes(["S2L-7712-A4", "S2L-5038-C8", "S2L-9146-D2", "S2L-2680-F5"]);
              showToast("Đã tạo bộ mã khôi phục dự phòng mới.", "info");
            }}
          >
            <Icon name="refresh" size={15} /> Tạo bộ mã mới
          </Soft>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <TopBar title="Cài đặt" back={false} />

      <div className="card row">
        <span className="avatar" style={{ overflow: "hidden" }}>
          <ParentAvatarSvg size={48} />
        </span>
        <div className="grow">
          <h1 className="h2">{parentName}</h1>
          <div className="tiny">{parentEmail}</div>
        </div>
        <span className="chip mint">Phụ huynh</span>
      </div>

      <section id="child-profiles" ref={childProfilesRef} className="card stack" aria-labelledby="child-profiles-title">
        <div className="row between">
          <h2 id="child-profiles-title" className="h2">Hồ sơ bé</h2>
          <button type="button" className="chip on" onClick={() => setActiveSheet("ADD_CHILD")}>
            <Icon name="plus" size={14} /> Thêm
          </button>
        </div>
        {visibleProfiles.length === 0 ? (
          <p className="sub" style={{ margin: 0 }}>Chưa có hồ sơ bé.</p>
        ) : (
          <ul className="profile-table" aria-label="Danh sách hồ sơ trẻ">
            {visibleProfiles.map((profile, index) => {
              const ageLabel = compactAgeLabel(profile.ageMonths);
              const isSelected = selectedProfileId === profile.id && !profile.archived;
              const statusLabel = isSelected ? "Đang dùng" : profile.archived ? "Đã lưu" : null;
              return (
                <li key={profile.id} className="profile-list-item">
                  <button
                    type="button"
                    className={`profile-row ${isSelected ? "is-selected" : ""}`}
                    aria-label={`Mở hồ sơ ${profile.displayName}, ${ageLabel}${statusLabel ? `, ${statusLabel.toLowerCase()}` : ""}`}
                    onClick={() => nav(`/p10-child-profiles/${profile.id}`)}
                  >
                    <span className="profile-avatar"><ChildAvatarSvg variant={index} size={42} /></span>
                    <span className="profile-row-copy">
                      <span className="h3 profile-name">{profile.displayName}</span>
                      <span className="profile-age">{ageLabel}</span>
                    </span>
                    {statusLabel && <span className={`profile-status ${isSelected ? "is-current" : "is-archived"}`}>{statusLabel}</span>}
                    <Icon name="chevron-right" size={18} color="var(--ink-3)" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>
      {/* Light / Dark Theme Switcher */}
      <div className="card stack">
        <div className="row between">
          <h2 className="h2">Chế độ hiển thị</h2>
          <span className="tiny">{theme === "dark" ? "Giao diện tối" : "Giao diện sáng"}</span>
        </div>
        <div className="seg" role="radiogroup" aria-label="Chế độ hiển thị Sáng hoặc Tối">
          <button
            type="button"
            role="radio"
            aria-checked={theme === "light"}
            className={theme === "light" ? "on" : ""}
            onClick={() => setTheme("light")}
          >
            <Icon name="sun" size={16} /> Sáng
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={theme === "dark"}
            className={theme === "dark" ? "on" : ""}
            onClick={() => setTheme("dark")}
          >
            <Icon name="moon" size={16} /> Tối
          </button>
        </div>
      </div>

      {/* Settings sub-pages navigation */}
      <h2 className="h2">Tài khoản &amp; Bảo mật</h2>
      <div className="card">
        <button type="button" className="list-item" onClick={() => setSubView("account")}>
          <IconBadge name="user" tone="primary" />
          <span className="grow">
            <span className="h3" style={{ display: "block" }}>Tài khoản &amp; Tùy chọn</span>
            <span className="tiny" style={{ display: "block" }}>Thông tin phụ huynh, thông báo, phụ đề</span>
          </span>
          <Icon name="chevron-right" size={18} color="var(--ink-3)" />
        </button>

        <button type="button" className="list-item" onClick={() => setSubView("privacy")}>
          <IconBadge name="shield" tone="mint" />
          <span className="grow">
            <span className="h3" style={{ display: "block" }}>Quyền riêng tư &amp; Dữ liệu AI</span>
            <span className="tiny" style={{ display: "block" }}>Chính sách riêng tư &amp; kết nối</span>
          </span>
          <Icon name="chevron-right" size={18} color="var(--ink-3)" />
        </button>

        <button type="button" className="list-item" onClick={() => setSubView("password")}>
          <IconBadge name="key" tone="accent" />
          <span className="grow">
            <span className="h3" style={{ display: "block" }}>Đổi mật khẩu</span>
            <span className="tiny" style={{ display: "block" }}>Cập nhật mật khẩu hiện tại</span>
          </span>
          <Icon name="chevron-right" size={18} color="var(--ink-3)" />
        </button>

        <button type="button" className="list-item" onClick={() => setSubView("forgot")}>
          <IconBadge name="lock" tone="neutral" />
          <span className="grow">
            <span className="h3" style={{ display: "block" }}>Quên mật khẩu</span>
            <span className="tiny" style={{ display: "block" }}>Nhận mã khôi phục OTP qua email</span>
          </span>
          <Icon name="chevron-right" size={18} color="var(--ink-3)" />
        </button>

        <button type="button" className="list-item" onClick={() => setSubView("twofa")}>
          <IconBadge name="shield" tone="primary" />
          <span className="grow">
            <span className="h3" style={{ display: "block" }}>Bảo mật 2 lớp (2FA)</span>
            <span className="tiny" style={{ display: "block" }}>{twoFaEnabled ? "Đang bật · Đã có mã dự phòng" : "Đang tắt"}</span>
          </span>
          <Icon name="chevron-right" size={18} color="var(--ink-3)" />
        </button>
      </div>

      {/* Separated Destructive Action: Logout */}
      <div style={{ marginTop: 6 }}>
        <Soft
          red
          onClick={() => {
            setIsAuthenticated(false);
            showToast("Đã đăng xuất khỏi tài khoản.", "info");
            nav("/p11-authentication");
          }}
        >
          <Icon name="logout" size={17} /> Đăng xuất tài khoản
        </Soft>
      </div>
    </div>
  );
}
