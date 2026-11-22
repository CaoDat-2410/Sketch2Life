import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BackendApiError } from "../../../shared/api/backendApi";
import { teacherOccurrenceApi, type Occurrence } from "../../../shared/api/teacherOccurrenceApi";
import { readTeacherPlayback } from "../../../shared/api/teacherPlayback";
import { teacherRunApi, type ProjectionReceipt, type TeacherRun } from "../../../shared/api/teacherRunApi";
import { ActionKeys } from "../services/actionKeys";
import { copy, projectionCopy as text, projectionError } from "../services/teacherRunCopy";

export function TeacherProjectionPage() {
  const [params] = useSearchParams();
  const id = params.get("occurrence") ?? "";
  const valid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id);
  const [occ, setOcc] = useState<Occurrence | null>(null);
  const [run, setRun] = useState<TeacherRun | null>(null);
  const [receipt, setReceipt] = useState<ProjectionReceipt | null>(null);
  const [ack, setAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [url, setUrl] = useState("");
  const etag = useRef<string | undefined>(undefined);
  const revision = useRef<number | undefined>(undefined);
  const keys = useRef(new ActionKeys());
  const controller = useRef<AbortController | null>(null);
  const objectUrl = useRef("");
  const alive = useRef(true);
  const lock = useRef(false);
  const clearVideo = useCallback(() => { controller.current?.abort(); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); objectUrl.current = ""; setUrl(""); }, []);
  const fail = useCallback((cause: unknown) => { if (!alive.current) return; setError(projectionError(cause)); if (cause instanceof BackendApiError && cause.status === 404) { clearVideo(); setOcc(null); setRun(null); setReceipt(null); } }, [clearVideo]);
  const load = useCallback(async () => {
    const [o, r] = await Promise.all([teacherOccurrenceApi.get(id, etag.current), teacherRunApi.active()]);
    if (!alive.current) return;
    if (o.etag) etag.current = o.etag;
    if (o.data) { if (revision.current !== undefined && revision.current !== o.data.revision) keys.current = new ActionKeys(); revision.current = o.data.revision; setOcc(o.data); }
    setRun("story_run" in r ? r.story_run : null);
  }, [id]);
  useEffect(() => { alive.current = true; if (valid) void load().catch(fail); return () => { alive.current = false; controller.current?.abort(); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); }; }, [valid, load, fail]);
  const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
  const ready = !!occ && !!run && run.occurrence_id === id && uuid.test(run.run_id) && run.run_state === "VIDEO_READY" && run.video?.playback.state === "AVAILABLE" && !!run.video.current_generation_id && uuid.test(run.video.current_generation_id) && ["APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"].includes(occ.state);
  const confirmed = ready && receipt?.run_id === run.run_id && receipt.generation_id === run.video?.current_generation_id;
  async function confirm() {
    if (!ready || !occ || !run?.video?.current_generation_id || !ack || lock.current) return;
    lock.current = true; setBusy(true); setError("");
    const fingerprint = [id, occ.revision, run.run_id, run.video.current_generation_id];
    try {
      const result = await teacherRunApi.projectionConfirm(id, occ.revision, run.run_id, run.video.current_generation_id, keys.current.key(...fingerprint));
      keys.current.settled(fingerprint); setReceipt(result); setAck(false); await load();
    } catch (cause) {
      keys.current.settled(fingerprint, cause); fail(cause);
      if (cause instanceof BackendApiError && cause.status === 409 && cause.code === "STALE_REVISION") { setReceipt(null); setAck(false); clearVideo(); try { await load(); } catch (next) { fail(next); } }
    } finally { lock.current = false; if (alive.current) setBusy(false); }
  }
  async function play() {
    if (!confirmed || !run || lock.current) return;
    lock.current = true; setBusy(true); setError(""); clearVideo(); const c = new AbortController(); controller.current = c;
    try { const blob = await readTeacherPlayback(run.run_id, c.signal, () => teacherRunApi.projectionToken(id)); if (!c.signal.aborted && alive.current) { objectUrl.current = URL.createObjectURL(blob); setUrl(objectUrl.current); } }
    catch (cause) { if (!c.signal.aborted) fail(cause); }
    finally { lock.current = false; if (alive.current) setBusy(false); }
  }
  const deadEnd = occ?.sample_video.slot_state === "CLAIMED" && (!run || run.occurrence_id !== id || run.run_state !== "VIDEO_READY");
  return <div className="s2l-page s2l-data-page"><h1>{text.title}</h1><a href="/teacher/t04-session-sketch-deck">{copy.back}</a>{!valid && <p>{copy.missing}</p>}{error && <p role="alert">{error}</p>}{occ && <section className="s2l-data-card"><h2>{occ.title}</h2>{deadEnd ? <p>{text.deadEnd}</p> : !ready ? <p>{text.unavailable}</p> : <>{!confirmed && <><label><input type="checkbox" checked={ack} onChange={e => setAck(e.target.checked)} />{text.acknowledgement}</label><button type="button" disabled={!ack || busy} onClick={() => void confirm()}>{text.title}</button></>}{confirmed && receipt && <><p>{text.receipt} {new Date(receipt.confirmed_at).toLocaleString("vi-VN")}</p>{!receipt.plan.is_current && <p>{text.planNote}</p>}<button type="button" disabled={busy} onClick={() => void play()}>{text.play}</button></>}{url && <video controls controlsList="nodownload noremoteplayback" disablePictureInPicture src={url} />}</>}</section>}</div>;
}
