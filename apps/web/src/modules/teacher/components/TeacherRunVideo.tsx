import { useEffect, useRef, useState } from "react";
import { BackendApiError } from "../../../shared/api/backendApi";
import { pollJob } from "../../../shared/api/teacherOccurrenceApi";
import { readTeacherPlayback } from "../../../shared/api/teacherPlayback";
import { teacherRunApi, type TeacherRun } from "../../../shared/api/teacherRunApi";
import { storyVideoCopy as text } from "../services/teacherRunCopy";
import type { QualityReason } from "../services/teacherStoryVideo";

interface Props { run: TeacherRun; claimed: boolean; fail: (error: unknown) => void; execute: (fingerprint: unknown[], action: (key: string) => Promise<unknown>) => Promise<void> }
export function TeacherRunVideo({ run, claimed, fail, execute }: Props) {
  const [reason, setReason] = useState<QualityReason>("QUALITY_LOW");
  const [url, setUrl] = useState<string | null>(null); const [playError, setPlayError] = useState(false); const [blocked, setBlocked] = useState(false);
  const stream = useRef<AbortController | null>(null); const objectUrl = useRef<string | null>(null);
  useEffect(() => () => { stream.current?.abort(); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); }, []);
  const jobId = ["VIDEO_ADMISSION_PENDING", "VIDEO_QUEUED", "VIDEO_GENERATING", "VIDEO_SAFETY_VALIDATING"].includes(run.run_state) ? run.video?.job?.job_id : undefined;
  useEffect(() => {
    if (!jobId) return;
    const controller = new AbortController();
    void pollJob(jobId, job => setBlocked(job.state === "blocked_unsafe"), controller.signal, { pauseWhenHidden: true, maxElapsedMs: 600000 }).catch(e => { if (e instanceof BackendApiError) fail(e); });
    return () => controller.abort();
  }, [jobId, fail]);
  async function watch() {
    stream.current?.abort(); const controller = new AbortController(); stream.current = controller; setPlayError(false);
    try { const blob = await readTeacherPlayback(run.run_id, controller.signal, async () => (await teacherRunApi.ownerToken(run.run_id)).playback); if (controller.signal.aborted) return; const next = URL.createObjectURL(blob); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); objectUrl.current = next; setUrl(next); }
    catch (e) { if (controller.signal.aborted) return; if (e instanceof BackendApiError && e.status === 404) fail(e); else setPlayError(true); }
  }
  if (!run.story || run.story_revision_no === null) return null;
  const video = run.video; const needsReason = (video?.video_requests_used ?? 0) > 0;
  const selectReason = <label>{text.reason}<select value={reason} onChange={e => setReason(e.target.value as QualityReason)}>{Object.entries(text.reasons).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>;
  return <section>
    {video && <p>{text.remaining(video.video_requests_remaining)}</p>}
    {(run.run_state === "VIDEO_ADMISSION_PENDING" || video?.state === "ADMISSION_PENDING") && <p>{text.pending}</p>}
    {(run.run_state === "SAFETY_BLOCKED" || video?.state === "SAFETY_BLOCKED" || blocked) && <p>{text.blocked}</p>}
    {run.run_state === "SCRIPT_REVIEW" && run.story_status === "CONFIRMED" && run.story_sha256 && <>{needsReason && selectReason}<button type="button" onClick={() => { const hash = run.story_sha256!; const choice = needsReason ? reason : undefined; void execute(["generate", run.run_id, run.run_revision, hash, choice], key => teacherRunApi.generateVideo(run.run_id, run.run_revision, hash, choice, key)); }}>{text.generate}</button></>}
    {run.run_state === "VIDEO_READY" && video?.current_generation_id && <>{selectReason}<button type="button" onClick={() => { const generation = video.current_generation_id!; void execute(["unsuitable", run.run_id, run.run_revision, generation, reason], key => teacherRunApi.unsuitable(run.run_id, run.run_revision, generation, reason, key)); }}>{text.unsuitable}</button><button type="button" onClick={() => void watch()}>{text.watch}</button>{playError && <p role="alert">{text.playbackError}</p>}{url && <video src={url} controls controlsList="nodownload noremoteplayback" disablePictureInPicture />}<p>{text.completeRule}</p><button type="button" disabled={!claimed} onClick={() => void execute(["complete", run.run_id, run.run_revision], key => teacherRunApi.complete(run.run_id, run.run_revision, key))}>{text.complete}</button></>}
  </section>;
}
