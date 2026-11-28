import { useEffect, useId, useRef, useState } from "react";
import { FormField } from "../../../shared/ui";
import { FormActionBar } from "./FormActionBar";
import { BackendApiError } from "../../../shared/api/backendApi";
import { canWatchTeacherRun, readTeacherPlayback } from "../../../shared/api/teacherPlayback";
import { teacherRunApi, type TeacherRun } from "../../../shared/api/teacherRunApi";
import { storyVideoCopy as text } from "../services/teacherRunCopy";
import type { QualityReason } from "../services/teacherStoryVideo";

interface Props {
  run: TeacherRun;
  fail: (error: unknown) => void;
  execute: (fingerprint: unknown[], action: (key: string) => Promise<unknown>) => Promise<void>;
  planFenced?: boolean;
}

export function TeacherRunVideo({ run, fail, execute, planFenced = false }: Props) {
  const reasonId = useId();
  const [reason, setReason] = useState<QualityReason>("QUALITY_LOW");
  const [url, setUrl] = useState<string | null>(null);
  const [playError, setPlayError] = useState(false);
  const stream = useRef<AbortController | null>(null);
  const objectUrl = useRef<string | null>(null);
  useEffect(() => () => { stream.current?.abort(); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); }, []);

  async function watch() {
    stream.current?.abort();
    const controller = new AbortController();
    stream.current = controller;
    setPlayError(false);
    try {
      const blob = await readTeacherPlayback(run.run_id, controller.signal, async () => (await teacherRunApi.ownerToken(run.run_id)).playback);
      if (controller.signal.aborted) return;
      const next = URL.createObjectURL(blob);
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = next;
      setUrl(next);
    } catch (e) {
      if (controller.signal.aborted) return;
      if (e instanceof BackendApiError && e.status === 404) fail(e);
      else setPlayError(true);
    }
  }

  if (!run.story || run.story_revision_no === null) return null;
  const video = run.video;
  const needsReason = (video?.video_requests_used ?? 0) > 0;
  const canWatch = canWatchTeacherRun(run);
  const completed = run.run_state === "COMPLETED";
  const safetyBlocked = video?.state === "SAFETY_BLOCKED" || video?.job?.error_code === "VIDEO_SAFETY_BLOCKED";
  const failureMessage = run.run_state === "FAILED" ? text.failureMessage(video?.job?.error_code) : null;
  const canGenerate = !planFenced && !completed && run.run_state === "SCRIPT_REVIEW" && run.story_status === "CONFIRMED" && run.story_confirmation_required !== true && (video?.video_requests_used ?? 0) < 3 && !!run.story_sha256;
  const canReviewReady = !planFenced && !completed && run.run_state === "VIDEO_READY" && !!video?.current_generation_id;

  const selectReason = (
    <FormField label={text.reason} htmlFor={reasonId}>
      <select id={reasonId} className="cozy-input" value={reason} onChange={(e) => setReason(e.target.value as QualityReason)}>
        {Object.entries(text.reasons).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
      </select>
    </FormField>
  );

  return (
    <section className="cozy-form-section cozy-form-stack tp-run-section">
      <div className="tp-form-section-intro">
        <h3>Video mẫu</h3>
        {video && <p>{text.remaining(video.video_requests_remaining)}</p>}
      </div>
      {(run.run_state === "VIDEO_ADMISSION_PENDING" || video?.state === "ADMISSION_PENDING") && <p className="s2l-note">{text.pending}</p>}
      {safetyBlocked && <p className="s2l-alert">{text.blocked}</p>}
      {failureMessage && <p className="s2l-alert" role="alert">{failureMessage}</p>}
      {canGenerate && (
        <div className="cozy-form-stack">
          {needsReason && selectReason}
          <FormActionBar>
            <button
              type="button"
              className="s2l-button is-primary"
              onClick={() => {
                const hash = run.story_sha256!;
                const choice = needsReason ? reason : undefined;
                void execute(["generate", run.run_id, run.run_revision, hash, choice], (key) => teacherRunApi.generateVideo(run.run_id, run.run_revision, hash, choice, key));
              }}
            >
              {text.generate}
            </button>
          </FormActionBar>
        </div>
      )}
      {canWatch && (
        <div className="cozy-form-stack">
          <div className="tp-actions">
            <button type="button" className={completed && !canReviewReady ? "s2l-button is-primary" : "s2l-button"} onClick={() => void watch()}>{text.watch}</button>
          </div>
          {playError && <p className="s2l-alert" role="alert">{text.playbackError}</p>}
          {url && <video className="tp-run-video" src={url} controls controlsList="nodownload noremoteplayback" disablePictureInPicture />}
        </div>
      )}
      {canReviewReady && video?.current_generation_id && (
        <div className="cozy-form-stack">
          {selectReason}
          <FormActionBar hint={text.completeRule}>
            <button
              type="button"
              className="s2l-button"
              onClick={() => {
                const generation = video.current_generation_id!;
                void execute(["unsuitable", run.run_id, run.run_revision, generation, reason], (key) => teacherRunApi.unsuitable(run.run_id, run.run_revision, generation, reason, key));
              }}
            >
              {text.unsuitable}
            </button>
            <button
              type="button"
              className="s2l-button is-primary"
              onClick={() => void execute(["complete", run.run_id, run.run_revision], (key) => teacherRunApi.complete(run.run_id, run.run_revision, key))}
            >
              {text.complete}
            </button>
          </FormActionBar>
        </div>
      )}
    </section>
  );
}
