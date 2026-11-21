import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { AdminBe1Error } from "../services/be1Client";
import { managerBusinessService, type FeedbackSummary, type FeedbackThread } from "../services/managerBusinessService";

function replyError(cause: unknown): { text: string; reload?: "thread" | "list" } {
  if (cause instanceof AdminBe1Error) {
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

export function FeedbackPage() {
  const [threads, setThreads] = useState<FeedbackSummary[]>([]);
  const [next, setNext] = useState<string | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [selected, setSelected] = useState("");
  const [thread, setThread] = useState<FeedbackThread | null>(null);
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
    setListLoading(true); setListError("");
    try {
      const page = await managerBusinessService.feedbackThreads(cursor);
      if (request !== listRequest.current) return;
      setThreads((previous) => cursor ? mergeById(previous, page.items, (item) => item.thread_id) : page.items);
      setNext(page.next_cursor === cursor ? null : page.next_cursor);
    } catch { if (request === listRequest.current) setListError("Không tải được danh sách phản hồi."); }
    finally { if (request === listRequest.current) setListLoading(false); }
  }, []);

  const loadThread = useCallback(async (id: string, cursor?: string) => {
    const request = ++threadRequest.current;
    setThreadLoading(true); setThreadError("");
    try {
      const page = await managerBusinessService.feedbackThread(id, cursor);
      if (request !== threadRequest.current || selectedRef.current !== id) return;
      setThread((previous) => cursor && previous ? { ...page, items: mergeById(previous.items, page.items, (item) => item.message_id), next_cursor: page.next_cursor === cursor ? null : page.next_cursor } : page);
    } catch (cause) {
      if (request !== threadRequest.current || selectedRef.current !== id) return;
      setThreadError(cause instanceof AdminBe1Error && cause.status === 404 ? "Không tìm thấy phản hồi hoặc bạn không có quyền truy cập." : "Không tải được nội dung phản hồi.");
    } finally { if (request === threadRequest.current && selectedRef.current === id) setThreadLoading(false); }
  }, []);

  useEffect(() => {
    const lists = listRequest; const details = threadRequest;
    void Promise.resolve().then(() => loadList());
    return () => { lists.current++; details.current++; };
  }, [loadList]);

  const select = (id: string) => {
    if (id === selectedRef.current) return;
    selectedRef.current = id; setSelected(id); setThread(null); setBody(""); setNotice(""); setReplyProblem("");
    void loadThread(id);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = body.trim();
    if (!thread || !text || busy) return;
    const id = selected; const request = threadRequest.current; const signature = JSON.stringify([id, text, thread.revision]);
    let key = keys.current.get(signature);
    if (!key) { key = crypto.randomUUID(); keys.current.set(signature, key); }
    setBusy(true); setReplyProblem(""); setNotice("");
    try {
      await managerBusinessService.replyFeedback(id, text, thread.revision, key);
      keys.current.delete(signature);
      if (selectedRef.current === id && threadRequest.current === request) { setBody(""); setNotice("Đã gửi phản hồi."); await loadThread(id); }
    } catch (cause) {
      if (selectedRef.current === id && threadRequest.current === request) {
        const outcome = replyError(cause); setReplyProblem(outcome.text);
        if (outcome.reload === "thread") await loadThread(id);
        if (outcome.reload === "list") { setThreadError("Không tìm thấy phản hồi hoặc bạn không có quyền truy cập."); await loadList(); }
      }
    } finally { setBusy(false); }
  };

  return <div className="s2l-page manager-business-page">
    <PageHeading eyebrow="School Manager" title="Phản hồi trong trường" description="Xem và trả lời phản hồi về giáo án trong trường." />
    <p>Đây là luồng phản hồi về giáo án, không phải chat; không có đánh dấu hoàn thành hay tải ảnh.</p>
    <section className="manager-business-card">
      <h2>Danh sách phản hồi</h2>
      {listError && <p role="alert" className="manager-business-alert">{listError} <button className="manager-business-button" onClick={() => void loadList()}>Tải lại</button></p>}
      {listLoading && <p role="status">Đang tải phản hồi…</p>}
      {!listLoading && !listError && threads.length === 0 && <p>Chưa có phản hồi nào trong trường.</p>}
      <ul className="manager-feedback-list">{threads.map((item) => <li key={item.thread_id}><button type="button" className="manager-business-button" aria-pressed={selected === item.thread_id} onClick={() => select(item.thread_id)}>Giáo án {item.lesson_id} · Phiên bản {item.version_id} · {Number.isNaN(Date.parse(item.created_at)) ? "Không rõ ngày" : new Date(item.created_at).toLocaleDateString("vi-VN")}</button></li>)}</ul>
      {next && <button className="manager-business-button" disabled={listLoading} onClick={() => void loadList(next)}>Tải thêm</button>}
    </section>
    {selected && <section className="manager-business-card">
      <h2>Nội dung phản hồi</h2>
      {threadLoading && <p role="status">Đang tải nội dung…</p>}
      {threadError && <p role="alert" className="manager-business-alert">{threadError} <button className="manager-business-button" onClick={() => void loadThread(selected)}>Tải lại</button></p>}
      {thread && <>
        <ol className="manager-feedback-list">{thread.items.map((item) => <li key={item.message_id}><strong>{item.from_you ? "Bạn" : "Phụ huynh hoặc nhân sự trường"}</strong><p>{item.body}</p></li>)}</ol>
        {thread.next_cursor && <button className="manager-business-button" disabled={threadLoading || busy} onClick={() => void loadThread(selected, thread.next_cursor ?? undefined)}>Tải thêm tin nhắn</button>}
        <form className="manager-feedback-form" onSubmit={(event) => void submit(event)}><label htmlFor="feedback-reply">Nội dung phản hồi</label><textarea id="feedback-reply" maxLength={2000} value={body} disabled={busy} onChange={(event) => setBody(event.target.value)} /><span>{body.length}/2000</span><button className="manager-business-button is-primary" disabled={busy || threadLoading || !!threadError || !body.trim()}>Gửi phản hồi</button></form>
      </>}
      {replyProblem && <p role="alert" className="manager-business-alert">{replyProblem}</p>}{notice && <p role="status" className="manager-business-success">{notice}</p>}
    </section>}
  </div>;
}
