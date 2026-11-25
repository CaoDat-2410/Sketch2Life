import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { BackendApiError, backendApi, configuredOrganizationId, createIdempotencyKey } from "../../../shared/api/backendApi";
import { teacherFeedbackApi, type TeacherFeedbackListPage, type TeacherFeedbackThreadPage, type TeacherFeedbackSummary } from "../../../shared/api/teacherFeedbackApi";
import { Alert, Button, FormField } from "../../../shared/ui";

const PAGE_SIZE = 25;

function replyError(cause: unknown): { text: string; reload?: "thread" | "list" } {
  if (cause instanceof BackendApiError) {
    if (cause.status === 409 || cause.code === "STALE_REVISION") return { text: "Phản hồi đã thay đổi. Hãy kiểm tra và gửi lại.", reload: "thread" };
    if (cause.status === 404) return { text: "Không tìm thấy phản hồi hoặc bạn không có quyền truy cập. Danh sách đã được tải lại.", reload: "list" };
    if (cause.status === 403) return { text: "Bạn không có quyền gửi phản hồi." };
    if (cause.status === 422) return { text: "Nội dung phản hồi không hợp lệ." };
    if (cause.status === 428) return { text: "Thiếu phiên bản phản hồi. Hãy tải lại và thử lại.", reload: "thread" };
    if (cause.status === 429) return { text: "Có quá nhiều yêu cầu. Hãy thử lại sau." };
  }
  return { text: "Chưa rõ kết quả. Hãy gửi lại cùng yêu cầu." };
}

function mergeById<T>(current: T[], incoming: T[], id: (item: T) => string): T[] {
  const seen = new Set(current.map(id));
  return [...current, ...incoming.filter((item) => { const key = id(item); if (seen.has(key)) return false; seen.add(key); return true; })];
}

function dateLabel(value: string): string {
  return Number.isNaN(Date.parse(value)) ? "Không rõ ngày" : new Date(value).toLocaleDateString("vi-VN");
}

export function TeacherFeedbackPage() {
  const organizationId = configuredOrganizationId();
  const [threads, setThreads] = useState<TeacherFeedbackSummary[]>([]);
  const [next, setNext] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [selected, setSelected] = useState("");
  const [thread, setThread] = useState<TeacherFeedbackThreadPage | null>(null);
  const [threadLoading, setThreadLoading] = useState(false);
  const [threadError, setThreadError] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [replyProblem, setReplyProblem] = useState("");
  const [lessonTitles, setLessonTitles] = useState<Record<string, string>>({});
  const keys = useRef(new Map<string, string>());
  const selectedRef = useRef("");
  const threadRequest = useRef(0);
  const listRequest = useRef(0);

  const loadList = useCallback(async (cursor?: string) => {
    const request = ++listRequest.current;
    setListLoading(true);
    setListError("");
    if (!organizationId) {
      setListError("Chưa cấu hình tổ chức để tải phản hồi.");
      setListLoading(false);
      return;
    }
    try {
      const page: TeacherFeedbackListPage = await teacherFeedbackApi.feedbackThreads(organizationId, PAGE_SIZE, cursor);
      if (request !== listRequest.current) return;
      setThreads((previous) => cursor ? mergeById(previous, page.items, (item) => item.thread_id) : page.items);
      setTotal(page.total);
      setNext(page.next_cursor === cursor ? null : page.next_cursor);
    } catch {
      if (request === listRequest.current) setListError("Không tải được danh sách phản hồi.");
    } finally {
      if (request === listRequest.current) setListLoading(false);
    }
  }, [organizationId]);

  const loadThread = useCallback(async (id: string, cursor?: string) => {
    const request = ++threadRequest.current;
    setThreadLoading(true);
    setThreadError("");
    if (!organizationId) {
      setThreadError("Chưa cấu hình tổ chức để tải phản hồi.");
      setThreadLoading(false);
      return;
    }
    try {
      const page = await teacherFeedbackApi.feedbackThread(organizationId, id, PAGE_SIZE, cursor);
      if (request !== threadRequest.current || selectedRef.current !== id) return;
      setThread((previous) => cursor && previous
        ? { ...page, items: mergeById(previous.items, page.items, (item) => item.message_id), next_cursor: page.next_cursor === cursor ? null : page.next_cursor }
        : page);
    } catch (cause) {
      if (request !== threadRequest.current || selectedRef.current !== id) return;
      setThreadError(cause instanceof BackendApiError && cause.status === 404
        ? "Không tìm thấy phản hồi hoặc bạn không có quyền truy cập."
        : "Không tải được nội dung phản hồi.");
    } finally {
      if (request === threadRequest.current && selectedRef.current === id) setThreadLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    const lists = listRequest;
    const details = threadRequest;
    void Promise.resolve().then(() => loadList());
    return () => { lists.current++; details.current++; };
  }, [loadList]);

  useEffect(() => {
    let active = true;
    if (organizationId) {
      void backendApi.lessons(organizationId).then((page) => {
        if (active) setLessonTitles(Object.fromEntries(page.items.map((lesson) => [lesson.lesson_id, lesson.title])));
      }).catch(() => undefined);
    }
    return () => { active = false; };
  }, [organizationId]);

  const select = (id: string) => {
    if (id === selectedRef.current) return;
    selectedRef.current = id;
    setSelected(id);
    setThread(null);
    setBody("");
    setNotice("");
    setReplyProblem("");
    void loadThread(id);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = body.trim();
    if (!thread || !text || busy || !organizationId) return;
    const id = selected;
    const request = threadRequest.current;
    const signature = JSON.stringify([id, text, thread.revision]);
    let key = keys.current.get(signature);
    if (!key) {
      key = createIdempotencyKey();
      keys.current.set(signature, key);
    }
    setBusy(true);
    setReplyProblem("");
    setNotice("");
    try {
      await teacherFeedbackApi.replyFeedback(organizationId, id, text, thread.revision, key);
      keys.current.delete(signature);
      if (selectedRef.current === id && threadRequest.current === request) {
        setBody("");
        setNotice("Đã gửi phản hồi.");
        await loadThread(id);
      }
    } catch (cause) {
      if (selectedRef.current === id && threadRequest.current === request) {
        const outcome = replyError(cause);
        setReplyProblem(outcome.text);
        if (outcome.reload === "thread") await loadThread(id);
        if (outcome.reload === "list") {
          setThreadError("Không tìm thấy phản hồi hoặc bạn không có quyền truy cập.");
          await loadList();
        }
      }
    } finally {
      setBusy(false);
    }
  };

  const lessonHeading = (lessonId: string, versionId: string) => {
    const title = lessonTitles[lessonId];
    return <>Giáo án {lessonId}{title ? ` · ${title}` : ""} · Phiên bản {versionId}</>;
  };

  return <div className="s2l-page">
    <PageHeading eyebrow="Teacher" title="Phản hồi giáo án" description="Xem và trả lời phản hồi về giáo án trong tổ chức." />
    <p>Phụ huynh tạo luồng phản hồi. Giáo viên có thể xem và trả lời, không thể bắt đầu luồng mới.</p>
    <section className="s2l-data-card" aria-labelledby="teacher-feedback-list-title">
      <h2 id="teacher-feedback-list-title">Danh sách phản hồi</h2>
      <p>{total} phản hồi</p>
      {listError && <Alert role="alert" tone="danger">{listError} <Button type="button" variant="secondary" onClick={() => void loadList()}>Tải lại</Button></Alert>}
      {listLoading && <p role="status">Đang tải phản hồi…</p>}
      {!listLoading && !listError && threads.length === 0 && <p>Chưa có phản hồi nào.</p>}
      <ul className="s2l-record-list">{threads.map((item) => <li key={item.thread_id}>
        <Button type="button" variant="secondary" aria-pressed={selected === item.thread_id} onClick={() => select(item.thread_id)}>
          {lessonHeading(item.lesson_id, item.version_id)} · {dateLabel(item.created_at)}
        </Button>
      </li>)}</ul>
      {next && <Button type="button" variant="secondary" disabled={listLoading} onClick={() => void loadList(next)}>Tải thêm</Button>}
    </section>
    {selected && <section className="s2l-data-card cozy-form-card cozy-form-card--wide cozy-form-stack" aria-labelledby="teacher-feedback-thread-title">
      <h2 id="teacher-feedback-thread-title">Nội dung phản hồi</h2>
      {thread && <p>{lessonHeading(thread.lesson_id, thread.version_id)} · {dateLabel(threads.find((item) => item.thread_id === selected)?.created_at ?? "")}</p>}
      {threadLoading && <p role="status">Đang tải nội dung…</p>}
      {threadError && <Alert role="alert" tone="danger">{threadError} <Button type="button" variant="secondary" onClick={() => void loadThread(selected)}>Tải lại</Button></Alert>}
      {thread && <div className="cozy-form-grid">
        <div className="cozy-span-3 cozy-form-stack">
          {thread.items.length === 0 && <p>Chưa có tin nhắn trong luồng này.</p>}
          <ol className="s2l-record-list">{thread.items.map((item) => <li key={item.message_id}><strong>{item.from_you ? "Bạn" : "Phụ huynh"}</strong><p>{item.body}</p></li>)}</ol>
          {thread.next_cursor && <div><Button type="button" variant="secondary" disabled={threadLoading || busy} onClick={() => void loadThread(selected, thread.next_cursor ?? undefined)}>Tải thêm tin nhắn</Button></div>}
        </div>
        <form className="cozy-form-stack cozy-span-3" style={{ marginTop: 0 }} onSubmit={(event) => void submit(event)}>
          <FormField label="Nội dung phản hồi" htmlFor="teacher-feedback-reply" required labelAction={<span className="cozy-form-counter">{body.length}/2000</span>}>
            <textarea id="teacher-feedback-reply" className="cozy-textarea" maxLength={2000} value={body} disabled={busy} onChange={(event) => setBody(event.target.value)} />
          </FormField>
          {replyProblem && <Alert role="alert" tone="danger">{replyProblem}</Alert>}
          {notice && <Alert role="status" tone="success">{notice}</Alert>}
          {!busy && !threadLoading && !threadError && !body.trim() && <p className="cozy-form-disabled-hint">Nhập nội dung phản hồi để bật nút gửi.</p>}
          <div className="cozy-form-actions" style={{ marginTop: 0 }}>
            <Button type="submit" variant="primary" loading={busy} disabled={busy || threadLoading || !!threadError || !body.trim()}>Gửi phản hồi</Button>
          </div>
        </form>
      </div>}
    </section>}
  </div>;
}
