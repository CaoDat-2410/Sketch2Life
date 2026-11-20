import { AdminSelect } from '../components/AdminSelect'
import { useState } from "react";
import { BookOpen, FilePlus2, Plus, X } from "lucide-react";
import {
  read,
  query,
  type Lesson,
  type Catalog,
  type LessonContent,
  type Activity,
  type Page,
  type AdminSession,
} from "../services/adminService";
import { useAdminQuery, useAdminCommand, useAdminCursor, label } from '../components/adminHooks'
import { Heading, Button, Field, Form, Feedback, LoadBoundary, Empty, Refresh, CursorPager, Status } from '../components/AdminUI'

const blankActivity = (): Activity => ({
  title: "",
  objective: "",
  instructions_text: "",
  safety_notes: "",
  materials_text: "",
  preparation_text: "",
  observation_notes: "",
  activity_kind: "indoor",
});
const blankLesson = (): LessonContent => ({
  locale: "vi-VN",
  title: "",
  topic: "",
  target_age_band_ref: "36-71",
  target_age_band_version: 1,
  objectives: [""],
  drawing_subject: "",
  drawing_steps_text: "",
  subject_learning_notes: "",
  activities: [blankActivity()],
});
function AgeField({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <Field label="Độ tuổi">
      <AdminSelect value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="36-71">3–5 tuổi</option>
        <option value="72-107">6–8 tuổi</option>
        <option value="108-120">9–10 tuổi</option>
      </AdminSelect>
    </Field>
  );
}
function ActivityFields({
  value,
  onChange,
}: {
  value: Activity;
  onChange: (value: Activity) => void;
}) {
  return (
    <div className="pa-form-grid">
      {(
        [
          { key: "title", title: "Tên hoạt động", limit: 160 },
          { key: "objective", title: "Mục tiêu", limit: 1000 },
          { key: "materials_text", title: "Vật liệu", limit: 2000 },
          { key: "preparation_text", title: "Chuẩn bị", limit: 2000 },
          {
            key: "instructions_text",
            title: "Hướng dẫn thực hiện",
            limit: 5000,
          },
          { key: "safety_notes", title: "Lưu ý an toàn", limit: 3000 },
          { key: "observation_notes", title: "Ghi chú quan sát", limit: 3000 },
        ] as const
      ).map((f) => (
        <Field key={f.key} label={f.title}>
          {f.key === "title" ? (
            <input
              required
              maxLength={f.limit}
              value={value[f.key] ?? ""}
              onChange={(e) => onChange({ ...value, [f.key]: e.target.value })}
            />
          ) : (
            <textarea
              required={f.key === "objective" || f.key === "instructions_text"}
              maxLength={f.limit}
              value={value[f.key] ?? ""}
              onChange={(e) => onChange({ ...value, [f.key]: e.target.value })}
            />
          )}
        </Field>
      ))}
      <Field label="Không gian">
        <AdminSelect
          value={value.activity_kind ?? "indoor"}
          onChange={(e) =>
            onChange({
              ...value,
              activity_kind: e.target.value as Activity["activity_kind"],
            })
          }
        >
          <option value="indoor">Trong nhà</option>
          <option value="outdoor">Ngoài trời</option>
          <option value="mixed">Kết hợp</option>
        </AdminSelect>
      </Field>
    </div>
  );
}
function LessonEditor({
  item,
  onSaved,
  onCancel,
}: {
  item?: Lesson;
  onSaved: (ref: string) => void;
  onCancel: () => void;
}) {
  const [content, setContent] = useState<LessonContent>(
      item ? structuredClone(item.content) : blankLesson(),
    ),
    cmd = useAdminCommand();
  function change<K extends keyof LessonContent>(
    key: K,
    value: LessonContent[K],
  ) {
    setContent((c) => ({ ...c, [key]: value }));
  }
  return (
    <section className="pa-panel pa-lesson-editor">
      <div className="pa-section-heading">
        <h2>{item ? "Tạo phiên bản mới" : "Soạn học liệu"}</h2>
        <Button onClick={onCancel}>
          <X size={16} />
          Đóng
        </Button>
      </div>
      <Feedback {...cmd} />
      <Form
        onSubmit={() =>
          cmd.run(
            () =>
              cmd.send<Lesson>(
                "/lessons" + (item ? "/" + item.lesson_id : ""),
                { content },
                item?.revision,
                item ? "PATCH" : "POST",
              ),
            (r) => onSaved(r.lesson_id),
          )
        }
      >
        <h3>Thông tin học liệu</h3>
        <div className="pa-form-grid lesson-basics">
          <Field label="Tên học liệu">
            <input
              autoFocus
              required
              maxLength={160}
              value={content.title}
              onChange={(e) => change("title", e.target.value)}
            />
          </Field>
          <Field label="Chủ đề">
            <input
              required
              maxLength={120}
              value={content.topic}
              onChange={(e) => change("topic", e.target.value)}
            />
          </Field>
          <AgeField
            value={content.target_age_band_ref}
            onChange={(v) => change("target_age_band_ref", v)}
          />
          <Field label="Mục tiêu (mỗi dòng một mục tiêu)">
            <textarea
              required
              value={content.objectives.join("\n")}
              onChange={(e) => change("objectives", e.target.value.split("\n"))}
            />
          </Field>
          </div>
        <h3>Nội dung vẽ</h3>
        <div className="pa-form-grid lesson-drawing">
          <Field label="Chủ thể vẽ">
            <input
              required
              maxLength={160}
              value={content.drawing_subject}
              onChange={(e) => change("drawing_subject", e.target.value)}
            />
          </Field>
          <Field label="Các bước hướng dẫn vẽ">
            <textarea
              required
              maxLength={4000}
              value={content.drawing_steps_text}
              onChange={(e) => change("drawing_steps_text", e.target.value)}
            />
          </Field>
          <Field label="Kiến thức về chủ thể">
            <textarea
              required
              maxLength={5000}
              value={content.subject_learning_notes}
              onChange={(e) => change("subject_learning_notes", e.target.value)}
            />
          </Field>
        </div>
        <h3>Hoạt động trong bài học</h3>
        {content.activities.map((a, index) => (
          <fieldset className="pa-activity" key={index}>
            <legend>Hoạt động {index + 1}</legend>
            <ActivityFields
              value={a}
              onChange={(v) =>
                change(
                  "activities",
                  content.activities.map((old, i) => (i === index ? v : old)),
                )
              }
            />
            {content.activities.length > 1 && (
              <Button
                onClick={() =>
                  change(
                    "activities",
                    content.activities.filter((_, i) => i !== index),
                  )
                }
              >
                Bỏ hoạt động
              </Button>
            )}
          </fieldset>
        ))}
        <div className="pa-actions">
          <Button
            disabled={content.activities.length >= 24}
            onClick={() =>
              change("activities", [...content.activities, blankActivity()])
            }
          >
            <Plus size={16} />
            Thêm hoạt động
          </Button>
          <Button primary type="submit" disabled={cmd.busy}>
            {cmd.busy ? "Đang lưu…" : "Lưu bản nháp"}
          </Button>
        </div>
      </Form>
    </section>
  );
}
function ActivityView({ activity }: { activity: Activity }) {
  return (
    <article className="pa-content-activity" aria-label="Nội dung hoạt động">
      {activity.objective && (
        <section className="pa-activity-objective">
          <h3>Mục tiêu</h3>
          <p>{activity.objective}</p>
        </section>
      )}
      {activity.instructions_text && (
        <section className="pa-activity-instructions">
          <h3>Cách thực hiện</h3>
          <p>{activity.instructions_text}</p>
        </section>
      )}
      {(activity.materials_text || activity.preparation_text) && (
        <div className="pa-activity-facts">
          {activity.materials_text && (
            <section>
              <h3>Vật liệu</h3>
              <p>{activity.materials_text}</p>
            </section>
          )}
          {activity.preparation_text && (
            <section>
              <h3>Chuẩn bị</h3>
              <p>{activity.preparation_text}</p>
            </section>
          )}
        </div>
      )}
      {activity.safety_notes && (
        <section className="pa-safety">
          <h3>An toàn</h3>
          <p>{activity.safety_notes}</p>
        </section>
      )}
      {activity.observation_notes && (
        <section className="pa-activity-observation">
          <h3>Ghi chú quan sát</h3>
          <p>{activity.observation_notes}</p>
        </section>
      )}
      {!activity.objective && !activity.instructions_text && (
        <p className="pa-activity-empty">Chưa có nội dung mô tả.</p>
      )}
    </article>
  );
}
export function LessonsPage() {
  const [state, setState] = useState(() => new URLSearchParams(window.location.search).get("state") === "PENDING_REVIEW" ? "PENDING_REVIEW" : ""),
    [selected, setSelected] = useState(""),
    [editing, setEditing] = useState(false),
    [creating, setCreating] = useState(false),
    [reason, setReason] = useState("");
  const pagination = useAdminCursor(state);
  const q = useAdminQuery(
    () => read<Page<Lesson>>("/lessons" + query({ state, cursor: pagination.cursor, limit: 25 })),
    JSON.stringify([state, pagination.cursor]),
  );
  const detail = useAdminQuery(
    () =>
      selected ? read<Lesson>("/lessons/" + selected) : Promise.resolve(null),
    selected,
  );
  const session = useAdminQuery(
      () => read<AdminSession>("/session"),
      "lesson-session",
    ),
    cmd = useAdminCommand();
  const canReview = session.data?.items.some(
      (g) => g.permission === "content_admin" && g.effective,
    ),
    item = detail.data;
  function refresh() {
    q.reload();
    detail.reload();
    session.reload();
  }
  function act(action: string) {
    if (!item) return;
    cmd.run(
      () =>
        cmd.send(
          "/lessons/" + item.lesson_id + "/actions",
          {
            action,
            version_id: item.version_id,
            content_hash: item.content_hash,
            review_id: item.reviews.find((r) => r.decision === "APPROVE")
              ?.review_id,
            reason: reason.trim() || undefined,
          },
          item.revision,
        ),
      () => {
        setReason("");
        refresh();
      },
    );
  }
  return (
    <div className="pa-page pa-lessons">
      <Heading
        title="Học liệu nền tảng"
      >
        {!creating && <Button
          primary
          onClick={() => {
            setCreating(true);
            setEditing(false);
          }}
        >
          <FilePlus2 size={16} />
          Soạn học liệu
        </Button>}
        <Refresh onClick={refresh} />
      </Heading>
      <Feedback {...cmd} />
      {creating ? (
        <LessonEditor
          onCancel={() => setCreating(false)}
          onSaved={(id) => {
            setCreating(false);
            setSelected(id);
            refresh();
          }}
        />
      ) : (
        <>
          
          <div className={"pa-content-layout" + (!selected ? " lesson-list-only" : "") + (!q.data?.items.length ? " is-list-empty" : "")}>
            <section className="pa-panel">
              <h2 className="pa-library-title">Danh sách học liệu {q.data?.total != null && <small>{q.data.total}</small>}</h2>
              <div className="lesson-list-filter"><Field label="Trạng thái duyệt">
            <AdminSelect
              value={state}
              onChange={(e) => {
                setState(e.target.value);
                setSelected("");
                setEditing(false);
              }}
            >
              <option value="">Tất cả học liệu</option>
              {["DRAFT", "PENDING_REVIEW", "APPROVED", "CHANGES_REQUESTED"].map(
                (s) => (
                  <option key={s} value={s}>
                    {label(s)}
                  </option>
                ),
              )}
            </AdminSelect>
          </Field></div>
              <LoadBoundary {...q}>
                {q.data?.items.length ? (
                  q.data.items.map((r) => (
                    <button
                      className={
                        "pa-content-item" +
                        (selected === r.lesson_id ? " is-selected" : "")
                      }
                      aria-pressed={selected === r.lesson_id} key={r.lesson_id}
                      onClick={() => {
                        setSelected(r.lesson_id);
                        setEditing(false);
                        setReason("");
                      }}
                    >
                      <span className="pa-book-icon">
                        <BookOpen size={20} />
                      </span>
                      <span>
                        <strong>{r.content.title}</strong>
                        <small>
                          {r.content.topic} · Phiên bản {r.version_no}
                        </small>
                        <Status
                          value={
                            r.moderation_state === "HIDDEN"
                              ? "HIDDEN"
                              : r.is_published_version
                              ? "PUBLIC"
                              : r.review_state
                          }
                        />
                      </span>
                    </button>
                  ))
                ) : (
                  <Empty text="Chưa có học liệu phù hợp" detail={state ? "Chọn trạng thái khác hoặc xóa bộ lọc để xem các học liệu còn lại." : "Bắt đầu bằng việc soạn học liệu đầu tiên cho thư viện."} action={<Button onClick={() => state ? setState("") : setCreating(true)}>{state ? "Xóa bộ lọc" : "Soạn học liệu"}</Button>} />
                )}
                <CursorPager
                  page={pagination.page}
                  total={q.data?.total}
                  count={q.data?.items.length ?? 0}
                  nextCursor={q.data?.next_cursor}
                  onNext={pagination.next}
                  onPrevious={pagination.back}
                />
              </LoadBoundary>
            </section>
            <div>
              {selected ? (
                <LoadBoundary {...detail}>
                  {item &&
                    (editing ? (
                      <LessonEditor
                        key={item.version_id}
                        item={item}
                        onCancel={() => setEditing(false)}
                        onSaved={() => {
                          setEditing(false);
                          refresh();
                        }}
                      />
                    ) : (
                      <section className="pa-panel pa-padded">
                        <div className="pa-section-heading">
                          <div>
                            <span className="pa-kicker">
                              PHIÊN BẢN {item.version_no}
                            </span>
                            <h2>{item.content.title}</h2>
                            <div className="pa-actions">
                          <Status value={item.review_state} />
                          {item.is_published_version && <Status value="PUBLIC" />}
                          {item.moderation_state === "HIDDEN" && <Status value="HIDDEN" />}
                        </div>
                          </div>
                          {item.is_author && (
                            <Button onClick={() => setEditing(true)}>
                              Chỉnh sửa
                            </Button>
                          )}
                        </div>
                        <div className="pa-reading">
                          <h3>Mục tiêu</h3>
                          <ul>
                            {item.content.objectives.map((o, i) => (
                              <li key={i}>{o}</li>
                            ))}
                          </ul>
                          <h3>{item.content.drawing_subject}</h3>
                          <p>{item.content.subject_learning_notes}</p>
                          <h4>Hướng dẫn vẽ</h4>
                          <p>{item.content.drawing_steps_text}</p>
                          {item.content.activities.map((a, i) => (
                            <section className="pa-lesson-activity" key={i}><h3>{a.title}</h3><ActivityView activity={a} /></section>
                          ))}
                        </div>
                        {item.reviews.map((r) => (
                          <p className="pa-review-note" key={r.review_id}>
                            {r.decision === "APPROVE"
                              ? "Đã được duyệt độc lập"
                              : "Yêu cầu chỉnh sửa"}
                            {r.reason && ": " + r.reason}
                          </p>
                        ))}
                        <div className="pa-command-area">
                          {!canReview && (
                            <p className="pa-muted">
                              Duyệt và xuất bản cần quyền Content Admin. Người
                              soạn không tự duyệt bài của mình.
                            </p>
                          )}
                          <Field label="Ghi chú / lý do">
                            <textarea
                              maxLength={1000}
                              value={reason}
                              onChange={(e) => setReason(e.target.value)}
                              placeholder="Bắt buộc khi yêu cầu chỉnh sửa hoặc ẩn bài"
                            />
                          </Field>
                          <div className="pa-actions">
                            {item.is_author &&
                              ["DRAFT", "CHANGES_REQUESTED"].includes(
                                item.review_state,
                              ) && (
                                <Button
                                  primary
                                  disabled={cmd.busy}
                                  onClick={() => act("submit")}
                                >
                                  Gửi duyệt
                                </Button>
                              )}
                            {!item.is_author &&
                              item.review_state === "PENDING_REVIEW" && (
                                <>
                                  <Button
                                    primary
                                    disabled={cmd.busy || !canReview}
                                    onClick={() => act("approve")}
                                  >
                                    Duyệt nội dung
                                  </Button>
                                  <Button
                                    disabled={
                                      cmd.busy || !canReview || !reason.trim()
                                    }
                                    onClick={() => act("request_changes")}
                                  >
                                    Yêu cầu chỉnh sửa
                                  </Button>
                                </>
                              )}
                            {!item.is_author &&
                              item.review_state === "APPROVED" &&
                              !item.is_published_version &&
                              item.moderation_state !== "HIDDEN" && (
                                <Button
                                  primary
                                  disabled={cmd.busy || !canReview}
                                  onClick={() => act("publish")}
                                >
                                  Xuất bản
                                </Button>
                              )}
                            {item.visibility === "PUBLIC" && (
                              <>
                                <Button
                                  disabled={cmd.busy || !canReview || !reason.trim()}
                                  onClick={() => act("unpublish")}
                                >
                                  Gỡ xuất bản
                                </Button>
                                <Button
                                  disabled={cmd.busy || !canReview || !reason.trim()}
                                  onClick={() => act("hide")}
                                >
                                  Ẩn học liệu
                                </Button>
                              </>
                            )}
                            {item.moderation_state === "HIDDEN" && (
                              <Button
                                disabled={cmd.busy || !canReview || !reason.trim()}
                                onClick={() => act("unpublish")}
                              >
                                Bỏ ẩn, giữ riêng tư
                              </Button>
                            )}
                          </div>
                        </div>
                      </section>
                    ))}
                </LoadBoundary>
              ) : (
                <section className="pa-panel">
                  <Empty
                    text="Chọn học liệu để xem"
                    detail="Nội dung và thao tác duyệt sẽ hiển thị tại đây."
                  />
                </section>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
function CatalogEditor({
  item,
  onSaved,
  onCancel,
}: {
  item?: Catalog;
  onSaved: (ref: string) => void;
  onCancel: () => void;
}) {
  const [activity, setActivity] = useState(
      item ? structuredClone(item.content.activity) : blankActivity(),
    ),
    [age, setAge] = useState(item?.content.age_band ?? "36-71"),
    cmd = useAdminCommand();
  return (
    <section className="pa-panel pa-padded">
      <div className="pa-section-heading">
        <h2>{item ? "Phiên bản hoạt động mới" : "Thêm hoạt động"}</h2>
        <Button onClick={onCancel}>Đóng</Button>
      </div>
      <Feedback {...cmd} />
      <Form
        onSubmit={() =>
          cmd.run(
            () =>
              cmd.send<Catalog>(
                "/catalog" + (item ? "/" + item.record_id : ""),
                {
                  activity,
                  age_band: age,
                  age_band_version: item?.content.age_band_version ?? 1,
                  provenance: "HUMAN_AUTHORED",
                },
                item?.revision,
                item ? "PATCH" : "POST",
              ),
            (r) => onSaved(r.record_id),
          )
        }
      >
        <AgeField value={age} onChange={setAge} />
        <ActivityFields value={activity} onChange={setActivity} />
        <Button primary type="submit" disabled={cmd.busy}>
          Lưu bản nháp
        </Button>
      </Form>
    </section>
  );
}
export function CatalogPage() {
  const [state, setState] = useState(""),
    [selected, setSelected] = useState(""),
    [creating, setCreating] = useState(false),
    [editing, setEditing] = useState(false),
    [reason, setReason] = useState("");
  const pagination = useAdminCursor(state);
  const q = useAdminQuery(
      () =>
        read<Page<Catalog>>("/catalog" + query({ state, cursor: pagination.cursor, limit: 25 })),
      JSON.stringify([state, pagination.cursor]),
    ),
    detail = useAdminQuery(
      () =>
        selected
          ? read<Catalog>("/catalog/" + selected)
          : Promise.resolve(null),
      selected,
    ),
    session = useAdminQuery(
      () => read<AdminSession>("/session"),
      "catalog-session",
    ),
    cmd = useAdminCommand(),
    item = detail.data;
  const canReview = session.data?.items.some(
    (g) => g.permission === "content_admin" && g.effective,
  );
  function refresh() {
    q.reload();
    detail.reload();
    session.reload();
  }
  function act(action: string, dimension?: string, decision?: string) {
    if (!item) return;
    cmd.run(
      () =>
        cmd.send(
          "/catalog/" + item.record_id + "/actions",
          {
            action,
            version: item.version,
            content_hash: item.content_hash,
            dimension,
            decision,
            reason: reason.trim() || undefined,
          },
          item.revision,
        ),
      () => {
        setReason("");
        refresh();
      },
    );
  }
  return (
    <div className="pa-page pa-catalog-page">
      <header className="pa-heading pa-catalog-heading">
        <div className="pa-catalog-heading-copy">
          <span className="pa-catalog-heading-icon" aria-hidden="true">
            <BookOpen size={20} strokeWidth={2} />
          </span>
          <div>
            <h1>Danh mục hoạt động</h1>
            <p>Quản lý và duyệt hoạt động dùng chung.</p>
          </div>
        </div>
        <div className="pa-actions">
          <Button primary onClick={() => setCreating(true)}>
            <Plus size={16} />
            Thêm hoạt động
          </Button>
          <Refresh onClick={refresh} />
        </div>
      </header>
      <Feedback {...cmd} />
      {creating ? (
        <CatalogEditor
          onCancel={() => setCreating(false)}
          onSaved={(id) => {
            setCreating(false);
            setSelected(id);
            refresh();
          }}
        />
      ) : (
        <>
          <div className={"pa-content-layout pa-catalog-layout" + (!selected ? " is-browsing" : "") + (!q.data?.items.length ? " is-list-empty" : "")}>
            <section className="pa-panel pa-catalog-list-panel" aria-label="Danh sách hoạt động">
              <div className="pa-catalog-list-toolbar">
                <div className="pa-catalog-list-heading">
                  <h2>Hoạt động</h2>
                  {q.data && <span>{q.data.total} mục</span>}
                </div>
                <Field label="Trạng thái">
                  <AdminSelect
                    value={state}
                    onChange={(e) => {
                      setState(e.target.value);
                      setSelected("");
                    }}
                  >
                    <option value="">Tất cả hoạt động</option>
                    {["draft", "submitted", "published", "recalled", "archived"].map(
                      (s) => (
                        <option key={s} value={s}>
                          {label(s)}
                        </option>
                      ),
                    )}
                  </AdminSelect>
                </Field>
              </div>
              <LoadBoundary {...q}>
                {q.data?.items.length ? (
                  q.data.items.map((r) => (
                    <button
                      className={
                        "pa-content-item" +
                        (selected === r.record_id ? " is-selected" : "")
                      }
                      aria-pressed={selected === r.record_id}
                      key={r.record_id}
                      onClick={() => {
                        setSelected(r.record_id);
                        setEditing(false);
                        setReason("");
                      }}
                    >
                      <span>
                        <strong>{r.content.activity.title}</strong>
                        <small>
                          Phiên bản {r.version} · {r.content.age_band} tháng
                        </small>
                        <Status value={r.state} />
                      </span>
                    </button>
                  ))
                ) : (
                  <Empty text="Chưa có hoạt động phù hợp" detail={state ? "Chọn trạng thái khác để xem các hoạt động còn lại." : "Thêm hoạt động đầu tiên để bắt đầu xây dựng danh mục."} action={<Button onClick={() => state ? setState("") : setCreating(true)}>{state ? "Xóa bộ lọc" : "Thêm hoạt động"}</Button>} />
                )}
                <CursorPager
                  page={pagination.page}
                  total={q.data?.total}
                  count={q.data?.items.length ?? 0}
                  nextCursor={q.data?.next_cursor}
                  onNext={pagination.next}
                  onPrevious={pagination.back}
                />
              </LoadBoundary>
            </section>
            <div className="pa-catalog-detail-column">
              {selected ? (
                <LoadBoundary {...detail}>
                  {item &&
                    (editing ? (
                      <CatalogEditor
                        key={item.revision}
                        item={item}
                        onCancel={() => setEditing(false)}
                        onSaved={() => {
                          setEditing(false);
                          refresh();
                        }}
                      />
                    ) : (
                      <section className="pa-panel pa-catalog-detail-panel">
                        <div className="pa-catalog-detail-header">
                          <div className="pa-catalog-detail-copy">
                            <p className="pa-kicker">Phiên bản {item.version}</p>
                            <h2>{item.content.activity.title}</h2>
                            <div className="pa-catalog-detail-meta">
                              <span>{item.content.age_band} tháng</span>
                              <Status value={item.state} />
                            </div>
                          </div>
                          {item.is_author && (
                            <Button onClick={() => setEditing(true)}>
                              Chỉnh sửa
                            </Button>
                          )}
                        </div>
                        <div className="pa-review-checks pa-catalog-review-checks">
                          {["safety", "pedagogical"].map((d) => (
                            (() => {
                              const review = item.reviews.find(
                                (r) => r.dimension === d,
                              );
                              return (
                                <div key={d}>
                                  <strong>{label(d)}</strong>
                                  <span
                                    className={
                                      "pa-catalog-review-state" +
                                      (review?.decision === "approve"
                                        ? " is-approved"
                                        : review
                                          ? " is-decided"
                                          : " is-pending")
                                    }
                                  >
                                    {review ? label(review.decision) : "Chưa duyệt"}
                                  </span>
                                </div>
                              );
                            })()
                          ))}
                        </div>
                        <ActivityView activity={item.content.activity} />
                        <div className="pa-command-area pa-catalog-command-area">
                          <Field label="Ghi chú / lý do">
                            <textarea
                              rows={3}
                              maxLength={200}
                              value={reason}
                              placeholder="Thêm ghi chú cho lần duyệt này…"
                              onChange={(e) => setReason(e.target.value)}
                            />
                          </Field>
                          <div className="pa-actions">
                            {item.is_author &&
                              ["draft", "changes_requested"].includes(
                                item.state,
                              ) && (
                                <Button
                                  primary
                                  disabled={cmd.busy}
                                  onClick={() => act("submit")}
                                >
                                  Gửi duyệt
                                </Button>
                              )}
                            {!item.is_author && item.state === "submitted" && (
                              <>
                                {["safety", "pedagogical"].map((d) => (
                                  <Button
                                    key={d}
                                    disabled={
                                      cmd.busy ||
                                      !canReview ||
                                      item.reviews.some(
                                        (r) =>
                                          r.dimension === d &&
                                          r.decision === "approve",
                                      )
                                    }
                                    onClick={() => act("review", d, "approve")}
                                  >
                                    Duyệt {label(d).toLowerCase()}
                                  </Button>
                                ))}
                                <Button
                                  disabled={
                                    cmd.busy || !canReview || !reason.trim()
                                  }
                                  onClick={() =>
                                    act(
                                      "review",
                                      "pedagogical",
                                      "request_changes",
                                    )
                                  }
                                >
                                  Yêu cầu chỉnh sửa
                                </Button>
                              </>
                            )}
                            {!item.is_author &&
                              ["submitted", "approved"].includes(
                                item.state,
                              ) && (
                                <Button
                                  primary
                                  disabled={
                                    cmd.busy ||
                                    !canReview ||
                                    !["safety", "pedagogical"].every((d) =>
                                      item.reviews.some(
                                        (r) =>
                                          r.dimension === d &&
                                          r.decision === "approve",
                                      ),
                                    )
                                  }
                                  onClick={() => act("publish")}
                                >
                                  Xuất bản
                                </Button>
                              )}
                            {item.state === "published" && (
                              <Button
                                disabled={
                                  cmd.busy || !canReview || !reason.trim()
                                }
                                onClick={() => act("hide")}
                              >
                                Thu hồi
                              </Button>
                            )}
                            {["recalled", "draft"].includes(item.state) && (
                              <Button
                                disabled={
                                  cmd.busy || !canReview || !reason.trim()
                                }
                                onClick={() => act("archive")}
                              >
                                Lưu trữ
                              </Button>
                            )}
                          </div>
                          {!canReview && (
                            <p className="pa-muted">
                              Tài khoản cần quyền Content Admin để duyệt và xuất
                              bản.
                            </p>
                          )}
                        </div>
                      </section>
                    ))}
                </LoadBoundary>
              ) : (
                <section className="pa-panel pa-catalog-empty-panel">
                  <Empty
                    text="Chọn hoạt động"
                    detail="Nội dung và trạng thái duyệt sẽ hiển thị tại đây."
                  />
                </section>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
