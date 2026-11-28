import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { EmptyState, formatDateTimeDdMmYyyy } from "../../../shared/ui";
import { FormActionBar } from "../components/FormActionBar";
import { BackendApiError } from "../../../shared/api/backendApi";
import { teacherOccurrenceApi, type Occurrence } from "../../../shared/api/teacherOccurrenceApi";
import { readTeacherPlayback } from "../../../shared/api/teacherPlayback";
import { teacherRunApi, type ProjectionReceipt, type TeacherRun } from "../../../shared/api/teacherRunApi";
import { ActionKeys } from "../services/actionKeys";
import { recalledSampleRun } from "../services/lastSampleRun";
import { copy, projectionCopy as text, projectionError } from "../services/teacherRunCopy";

export function TeacherProjectionPage() {
  const [params] = useSearchParams();
  const id = params.get("occurrence") ?? "";
  return <ProjectionForOccurrence key={id} id={id} />;
}

function ProjectionForOccurrence({ id }: { id: string }) {
  const valid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
  const [occ, setOcc] = useState<Occurrence | null>(null);
  const [run, setRun] = useState<TeacherRun | null>(null);
  const [receipt, setReceipt] = useState<ProjectionReceipt | null>(null);
  const [ack, setAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [url, setUrl] = useState("");
  const etag = useRef<string | undefined>(undefined);
  const occurrenceId = useRef(id);
  const revision = useRef<number | undefined>(undefined);
  const keys = useRef(new ActionKeys());
  const controller = useRef<AbortController | null>(null);
  const objectUrl = useRef("");
  const alive = useRef(true);
  const lock = useRef(false);
  const clearVideo = useCallback(() => { controller.current?.abort(); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); objectUrl.current = ""; setUrl(""); }, []);
  const fail = useCallback((cause: unknown) => { if (!alive.current) return; setError(projectionError(cause)); if (cause instanceof BackendApiError && cause.status === 404) { clearVideo(); setOcc(null); setRun(null); setReceipt(null); } }, [clearVideo]);
  const load = useCallback(async () => {
    if (occurrenceId.current !== id) { occurrenceId.current = id; etag.current = undefined; revision.current = undefined; setReceipt(null); setRun(null); }
    const [o, r] = await Promise.all([teacherOccurrenceApi.get(id, etag.current), teacherRunApi.active()]);
    if (!alive.current) return;
    if (o.etag) etag.current = o.etag;
    if (o.data) { if (revision.current !== undefined && revision.current !== o.data.revision) keys.current = new ActionKeys(); revision.current = o.data.revision; setOcc(o.data); }
    let current = "story_run" in r ? r.story_run : null;
    if ("story_run" in r && !current && o.data?.sample_video.run_ref) {
      const runId = o.data.sample_video.run_ref;
      const byId = await teacherRunApi.get(runId);
      if (!alive.current) return;
      current = byId.data && "story_run" in byId.data ? byId.data.story_run : null;
    }
    // Completed before any projection confirmation: no active run and no run_ref on the occurrence.
    const remembered = "story_run" in r && !current && !o.data?.sample_video.run_ref ? recalledSampleRun(id) : null;
    if (remembered) {
      try {
        const byId = await teacherRunApi.get(remembered);
        current = byId.data && "story_run" in byId.data ? byId.data.story_run : null;
      } catch (cause) {
        if (!(cause instanceof BackendApiError && cause.status === 404)) throw cause;
      }
      if (!alive.current) return;
    }
    setRun(current);
  }, [id]);
  useEffect(() => { alive.current = true; if (valid) void load().catch(fail); return () => { alive.current = false; controller.current?.abort(); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); }; }, [valid, load, fail]);
  const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
  const claimedForRun = !!occ && !!run && occ.sample_video.slot_state === "CLAIMED" && occ.sample_video.run_ref === run.run_id;
  const completedAt = run?.timeline?.find((event) => event.event === "RUN_COMPLETED")?.at;
  const claimTime = occ?.sample_video.claimed_at ? Date.parse(occ.sample_video.claimed_at) : Number.NaN;
  const completeTime = completedAt ? Date.parse(completedAt) : Number.NaN;
  const claimAfterComplete = run?.run_state === "COMPLETED" && claimedForRun && Number.isFinite(claimTime) && Number.isFinite(completeTime) && claimTime >= completeTime;
  const claimBeforeComplete = run?.run_state === "COMPLETED" && claimedForRun && Number.isFinite(claimTime) && Number.isFinite(completeTime) && claimTime < completeTime;
  const slotAvailable = occ?.sample_video.slot_state === "AVAILABLE";
  const slotUsable = slotAvailable || (run?.run_state === "VIDEO_READY" && claimedForRun) || claimAfterComplete;
  const ready = !!occ && !!run && run.occurrence_id === id && uuid.test(run.run_id) && ["VIDEO_READY", "COMPLETED"].includes(run.run_state) && run.video?.playback.state === "AVAILABLE" && !!run.video.current_generation_id && uuid.test(run.video.current_generation_id) && slotUsable && ["APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"].includes(occ.state);
  const confirmed = ready && receipt?.run_id === run.run_id && receipt.generation_id === run.video?.current_generation_id;
  const videoPending = !!run && run.occurrence_id === id && ["VIDEO_ADMISSION_PENDING", "VIDEO_QUEUED", "VIDEO_GENERATING", "VIDEO_SAFETY_VALIDATING"].includes(run.run_state);
  async function refresh() {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError(""); clearVideo(); setReceipt(null); setAck(false);
    try { await load(); }
    catch (cause) { fail(cause); }
    finally { lock.current = false; if (alive.current) setBusy(false); }
  }
  async function confirm() {
    if (!ready || !occ || (occ.sample_video.slot_state !== "AVAILABLE" && !claimedForRun) || !run?.video?.current_generation_id || !ack || lock.current) return;
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
  const deadEnd = !!occ && !!run && run.occurrence_id === id && claimBeforeComplete;
  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading
        eyebrow="Giáo viên · Buổi dạy"
        title={text.title}
        description="Xác nhận và phát video mẫu đã sẵn sàng cho cả lớp."
        action={<Link className="s2l-button" to="/teacher/t04-session-sketch-deck">{copy.back}</Link>}
      />
      {!valid && (
        <section className="s2l-data-card">
          <EmptyState
            title="Chưa chọn buổi dạy"
            description={copy.missing}
            action={<Link className="s2l-button is-primary" to="/teacher/t04-session-sketch-deck">Chọn buổi dạy</Link>}
          />
        </section>
      )}
      {error && <p className="s2l-alert" role="alert">{error}</p>}
      {occ && (
        <section className="s2l-data-card cozy-form-stack">
          <div className="tp-form-column">
            <h2>{occ.title}</h2>
            {deadEnd ? (
              <p className="s2l-alert">{text.deadEnd}</p>
            ) : !ready ? (
              <div className="cozy-form-stack">
                <p className="s2l-note">{videoPending ? text.waiting : text.unavailable}</p>
                {videoPending && <button type="button" className="s2l-button" disabled={busy} onClick={() => void refresh()}>{busy ? text.refreshing : text.refresh}</button>}
              </div>
            ) : (
              <div className="cozy-form-stack">
                {!confirmed && (
                  <div className="cozy-form-section">
                    <div className="tp-form-section-intro">
                      <h3>1. Xác nhận video hiện tại</h3>
                      <p>{text.confirmationRequired}</p>
                    </div>
                    <label className="cozy-form-checkbox-card">
                      <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} />
                      <span>{text.acknowledgement}</span>
                    </label>
                    <FormActionBar hint={!ack ? "Đánh dấu xác nhận ở trên để bật nút chiếu cho lớp." : undefined}>
                      <button type="button" className="s2l-button is-primary" disabled={!ack || busy} onClick={() => void confirm()}>{text.confirm}</button>
                    </FormActionBar>
                  </div>
                )}
                {confirmed && (
                  <div className="cozy-form-section" data-s2l-presenting="true">
                    <div className="tp-form-section-intro">
                      <h3>Phát video cho lớp</h3>
                    </div>
                    {receipt && (
                      <div className="cozy-form-stack">
                        <p className="s2l-note">{text.confirmedCurrent} {formatDateTimeDdMmYyyy(receipt.confirmed_at)}</p>
                        {!receipt.plan.is_current && <p className="s2l-alert">{text.planNote}</p>}
                      </div>
                    )}
                    <FormActionBar>
                      <button type="button" className="s2l-button is-primary" disabled={busy} onClick={() => void play()}>{text.play}</button>
                    </FormActionBar>
                  </div>
                )}
                {url && <video className="tp-run-video" controls controlsList="nodownload noremoteplayback" disablePictureInPicture src={url} />}
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
