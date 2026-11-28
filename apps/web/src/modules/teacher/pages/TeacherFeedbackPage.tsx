import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { BackendApiError, configuredOrganizationId, createIdempotencyKey } from "../../../shared/api/backendApi";
import { feedbackAuthorLabel } from "../../../shared/api/feedbackLabels";
import { teacherFeedbackApi, type TeacherFeedbackListPage, type TeacherFeedbackThreadPage, type TeacherFeedbackSummary } from "../../../shared/api/teacherFeedbackApi";
import { Alert, Button, FormField, formatDateDdMmYyyy } from "../../../shared/ui";
import { FormActionBar } from "../components/FormActionBar";

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
  const formatted = formatDateDdMmYyyy(value);
  return formatted || "Không rõ ngày";
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
      if (cause instanceof BackendApiError && cause.status === 400) keys.current.delete(signature);
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

  const lessonHeading = (title: string | null | undefined, versionNo: number | null | undefined) => {
    return <>Giáo án {title?.trim() || "Chưa rõ tiêu đề"}{versionNo ? ` · Phiên bản ${versionNo}` : ""}</>;
  };

  return <div className="s2l-page">
    <PageHeading eyebrow="Giáo viên · Trao đổi" title="Phản hồi giáo án" description="Phụ huynh gửi phản hồi; bạn xem và trả lời tại đây." />
    <section className="s2l-data-card" aria-labelledby="teacher-feedback-list-title">
      <h2 id="teacher-feedback-list-title">Danh sách phản hồi</h2>
      <p>{total} phản hồi</p>
      {listError && <Alert role="alert" tone="danger">{listError} <Button type="button" variant="secondary" onClick={() => void loadList()}>Tải lại</Button></Alert>}
      {listLoading && <p role="status">Đang tải phản hồi…</p>}
      {!listLoading && !listError && threads.length === 0 && <p>Chưa có phản hồi nào.</p>}
      <ul className="tp-thread-list">{threads.map((item) => <li key={item.thread_id}>
        <button type="button" className={"tp-thread-row" + (selected === item.thread_id ? " is-selected" : "")} aria-pressed={selected === item.thread_id} onClick={() => select(item.thread_id)}>
          <span className="tp-thread-main"><strong>{lessonHeading(item.lesson_title, item.version_no)}</strong><span className="tp-muted cozy-form-hint">{dateLabel(item.created_at)}</span></span>
          <span className="tp-thread-open" aria-hidden="true">{selected === item.thread_id ? "Đang xem" : "Mở ›"}</span>
        </button>
      </li>)}</ul>
      {next && <Button type="button" variant="secondary" disabled={listLoading} onClick={() => void loadList(next)}>Tải thêm</Button>}
    </section>
    {selected && <section className="s2l-data-card cozy-form-card cozy-form-card--wide cozy-form-stack tp-form-column" aria-labelledby="teacher-feedback-thread-title">
      <h2 id="teacher-feedback-thread-title">Nội dung phản hồi</h2>
      {thread && <p className="tp-muted">{lessonHeading(thread.lesson_title, thread.version_no)} · {dateLabel(threads.find((item) => item.thread_id === selected)?.created_at ?? "")}</p>}
      {threadLoading && <p role="status">Đang tải nội dung…</p>}
      {threadError && <Alert role="alert" tone="danger">{threadError} <Button type="button" variant="secondary" onClick={() => void loadThread(selected)}>Tải lại</Button></Alert>}
      {thread && <div className="cozy-form-stack">
        <div className="cozy-form-stack">
          {thread.items.length === 0 && <p>Chưa có tin nhắn phản hồi.</p>}
          <ol className="s2l-record-list tp-feedback-messages">{thread.items.map((item) => <li key={item.message_id} className="tp-feedback-message"><strong>{feedbackAuthorLabel(item.author_role, item.author_display_name, item.from_you)}</strong><p>{item.body}</p></li>)}</ol>
          {thread.next_cursor && <div><Button type="button" variant="secondary" disabled={threadLoading || busy} onClick={() => void loadThread(selected, thread.next_cursor ?? undefined)}>Tải thêm tin nhắn</Button></div>}
        </div>
        <form className="cozy-form-stack" style={{ marginTop: 0 }} onSubmit={(event) => void submit(event)}>
          <FormField label="Nội dung phản hồi" htmlFor="teacher-feedback-reply" required labelAction={<span className="cozy-form-counter">{body.length}/2000</span>}>
            <textarea id="teacher-feedback-reply" className="cozy-textarea" rows={3} maxLength={2000} value={body} disabled={busy} onChange={(event) => setBody(event.target.value)} />
          </FormField>
          {replyProblem && <Alert role="alert" tone="danger">{replyProblem}</Alert>}
          {notice && <Alert role="status" tone="success">{notice}</Alert>}
          <FormActionBar hint={!busy && !threadLoading && !threadError && !body.trim() ? "Nhập nội dung phản hồi để bật nút gửi." : undefined}>
            <Button type="submit" variant="primary" loading={busy} disabled={busy || threadLoading || !!threadError || !body.trim()}>Gửi phản hồi</Button>
          </FormActionBar>
        </form>
      </div>}
    </section>}
  </div>;
}
