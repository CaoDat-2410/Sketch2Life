import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { BackendApiError, createIdempotencyKey } from "../../../shared/api/backendApi";
import { teacherOccurrenceApi, uploadFileForPurpose, type UploadSession } from "../../../shared/api/teacherOccurrenceApi";
import { teacherRunApi, type LifecycleEnvelope, type SubjectEntity, type SubjectRole, type TeacherRun, type Transcript } from "../../../shared/api/teacherRunApi";
import { FormActionBar } from "./FormActionBar";
import { ActionKeys } from "../services/actionKeys";
import { inputCopy as c } from "../services/teacherRunCopy";
import { cleanIdea, runFileMediaType, type RunUploadPurpose } from "../services/teacherRunInputs";
import { availableActions } from "../services/teacherRunLogic";

type Props = { run: TeacherRun; refresh: () => Promise<void>; fail: (error: unknown) => void; lifecycle: (value: LifecycleEnvelope) => void };
type UploadAttempt = { file: File; create: string; complete: string; command: string; abort: string; session?: UploadSession; controller: AbortController };

export function TeacherRunInputs({ run, refresh, fail, lifecycle }: Props) {
  const baseId = useId();
  const drawingInputId = `${baseId}-drawing`;
  const drawingLabelId = `${baseId}-drawing-label`;
  const ideaInputId = `${baseId}-idea`;
  const audioInputId = `${baseId}-audio`;
  const audioLabelId = `${baseId}-audio-label`;
  const correctionInputId = `${baseId}-correction`;
  const subjectInputId = `${baseId}-subject`;
  const [drawing, setDrawing] = useState<File | null>(null);
  const [audio, setAudio] = useState<File | null>(null);
  const [idea, setIdea] = useState("");
  const [correction, setCorrection] = useState("");
  const [subjectDraft, setSubjectDraft] = useState<{ revision: number | null; value: string } | null>(null);
  const [kept, setKept] = useState<Record<string, boolean>>({});
  const [correctedRevision, setCorrectedRevision] = useState<number | null>(null);
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [pollVersion, setPollVersion] = useState(0);
  const attempts = useRef<Partial<Record<RunUploadPurpose, UploadAttempt>>>({});
  const keys = useRef(new ActionKeys());
  const locked = useRef(false);
  const actions = availableActions(run);

  const readTranscript = useCallback(async (signal?: AbortSignal) => {
    const value = await teacherRunApi.transcript(run.run_id, signal);
    if (!signal?.aborted) { setTranscript(value); setCorrection(value.text ?? ""); }
    return value;
  }, [run.run_id]);

  useEffect(() => {
    if (!actions.transcript) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let delay = 2000;
    const started = Date.now();
    const read = async () => {
      try {
        const result = await readTranscript(controller.signal);
        if (result.state !== "PENDING" || controller.signal.aborted) return;
        const tick = () => {
          timer = setTimeout(() => {
            if (controller.signal.aborted || Date.now() - started >= 600000) return;
            if (document.hidden) { tick(); return; }
            void read();
          }, delay);
          delay = Math.min(delay * 2, 10000);
        };
        tick();
      } catch (error) {
        if (!controller.signal.aborted) fail(error);
      }
    };
    void read();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [actions.transcript, readTranscript, fail, pollVersion]);

  const subject = subjectDraft?.revision === run.understanding_revision ? subjectDraft.value : (run.candidate?.candidate_subject ?? "");

  function attempt(file: File, purpose: RunUploadPurpose) {
    let current = attempts.current[purpose];
    if (!current || current.file !== file) {
      current = { file, create: createIdempotencyKey(), complete: createIdempotencyKey(), command: createIdempotencyKey(), abort: createIdempotencyKey(), controller: new AbortController() };
      attempts.current[purpose] = current;
    }
    if (current.controller.signal.aborted) current.controller = new AbortController();
    return current;
  }

  useEffect(() => () => { for (const a of Object.values(attempts.current)) a?.controller.abort(); }, []);

  async function upload(file: File, purpose: RunUploadPurpose) {
    const mediaType = runFileMediaType(file, purpose);
    const a = attempt(file, purpose);
    const ref = await uploadFileForPurpose(file, run.run_id, purpose, mediaType, {
      keys: { create: a.create, complete: a.complete },
      signal: a.controller.signal,
      onSession: (value) => {
        a.session = value;
        if (a.controller.signal.aborted) void teacherOccurrenceApi.abortOpenUpload(value.upload_id, a.abort).catch(fail);
      },
    });
    return { ref, attempt: a };
  }

  async function stop() {
    for (const a of Object.values(attempts.current)) {
      if (a && !a.controller.signal.aborted) {
        a.controller.abort();
        if (a.session) try { await teacherOccurrenceApi.abortOpenUpload(a.session.upload_id, a.abort); } catch (error) { fail(error); }
      }
    }
  }

  async function execute(signature: unknown[], work: (key: string) => Promise<unknown>) {
    if (locked.current) return;
    locked.current = true; setBusy(true); setMessage("");
    try {
      const result = await work(keys.current.key(...signature));
      keys.current.settled(signature);
      if (result && typeof result === "object" && "lifecycle" in result) lifecycle(result as LifecycleEnvelope);
      else await refresh();
    } catch (error) {
      keys.current.settled(signature, error);
      if (error instanceof Error && error.name === "AbortError") return;
      fail(error);
      if (error instanceof BackendApiError && error.status === 409 && error.code === "STALE_REVISION") await refresh();
    } finally {
      locked.current = false; setBusy(false);
    }
  }

  async function sendDrawing() {
    if (!drawing) return;
    const fileAttempt = attempt(drawing, "RUN_ARTWORK");
    await execute(["drawing", run.run_id, run.run_revision, fileAttempt.command], async (key) => {
      const { ref } = await upload(drawing, "RUN_ARTWORK");
      return teacherRunApi.attachArtwork(run.run_id, ref, run.run_revision, key);
    });
  }

  async function sendIdea() {
    const text = idea.trim() ? cleanIdea(idea) : null;
    if ((idea.trim() && !text) || (!text && !audio)) { setMessage(c.invalidIdea); return; }
    const fileAttempt = audio ? attempt(audio, "RUN_AUDIO") : null;
    await execute(["idea", run.run_id, run.run_revision, text, fileAttempt?.command], async (key) => {
      const audioRef = audio ? (await upload(audio, "RUN_AUDIO")).ref : undefined;
      const result = await teacherRunApi.idea(run.run_id, { expected_run_revision: run.run_revision, ...(text ? { text } : {}), ...(audioRef ? { audio_ref: audioRef } : {}) }, key);
      if (audioRef && !("lifecycle" in result)) setPollVersion((v) => v + 1);
      return result;
    });
  }

  async function correct() {
    const text = cleanIdea(correction);
    if (!text || !transcript?.transcript_revision || correctedRevision === transcript.transcript_revision) { setMessage(c.invalidCorrection); return; }
    await execute(["correction", run.run_id, run.run_revision, transcript.transcript_revision, text], async (key) => {
      const result = await teacherRunApi.idea(run.run_id, { expected_run_revision: run.run_revision, transcript_correction: { base_revision: transcript.transcript_revision!, text } }, key);
      if (!("lifecycle" in result)) setCorrectedRevision(transcript.transcript_revision);
      return result;
    });
    setPollVersion((v) => v + 1);
  }

  async function confirmTranscript() {
    if (!transcript?.transcript_revision || !transcript.transcript_sha256) return;
    await execute(["transcript", run.run_id, transcript.transcript_revision, transcript.transcript_sha256], (key) => teacherRunApi.confirmTranscript(run.run_id, transcript.transcript_revision!, transcript.transcript_sha256!, key));
    setPollVersion((v) => v + 1);
  }

  async function confirmContext() {
    if (!run.context_snapshot_sha256) return;
    await execute(["context", run.run_id, run.context_revision, run.context_snapshot_sha256], (key) => teacherRunApi.confirmContext(run.run_id, run.context_revision, run.context_snapshot_sha256!, key));
  }

  async function confirmSubject() {
    const value = subject.trim();
    if (!value || Array.from(value).length > 160 || run.understanding_revision === null) { setMessage(c.invalidSubject); return; }
    // The story may use only the other objects the adult keeps; without roles it uses none.
    const roles: SubjectRole[] | undefined = others.length === 0 ? undefined : entities.map((entity) => entity.entity_id === mainId
      ? { entity_id: entity.entity_id, label: value, role: "main" }
      : { entity_id: entity.entity_id, label: entity.label, role: isKept(entity) && entity.label.trim().toLowerCase() !== value.toLowerCase() ? "secondary" : "excluded" });
    await execute(["subject", run.run_id, run.understanding_revision, value, ...(roles ? [roles] : [])], (key) => roles
      ? teacherRunApi.confirmSubject(run.run_id, run.understanding_revision!, value, key, roles)
      : teacherRunApi.confirmSubject(run.run_id, run.understanding_revision!, value, key));
  }

  const entities = run.candidate?.entities ?? [];
  const approved = run.candidate?.subject_roles ?? null;
  const mainId = approved?.find((item) => item.role === "main")?.entity_id ?? "main";
  const others = entities.filter((entity) => entity.entity_id !== mainId);
  const isKept = (entity: SubjectEntity) => kept[`${run.understanding_revision}:${entity.entity_id}`]
    ?? (approved ? approved.some((item) => item.entity_id === entity.entity_id && item.role === "secondary") : entity.suggested_included !== false);

  const showCorrection = Boolean(actions.transcript && transcript?.state === "NEEDS_CONFIRMATION" && transcript.origin !== "ADULT_CORRECTION" && correctedRevision !== transcript.transcript_revision);
  const primaryStep = actions.subject
    ? "subject"
    : actions.context && run.context_snapshot
      ? "context"
      : actions.transcript && transcript?.state === "NEEDS_CONFIRMATION"
        ? "transcript"
        : actions.artwork
          ? "artwork"
          : "idea";

  return (
    <div className="cozy-form-stack">
      {message && <p className="s2l-alert" role="alert">{message}</p>}
      {actions.artwork && (
        <section className="cozy-form-section cozy-form-stack tp-run-section">
          <div className="tp-form-section-intro"><h3>1. Tải tranh vẽ của bé</h3></div>
          <div className="teacher-file-field">
            <span id={drawingLabelId} className="cozy-form-label">{c.drawing}</span>
            <label className="teacher-file-picker" htmlFor={drawingInputId}>
              <span className="teacher-file-picker-button"><Upload size={16} aria-hidden="true" /> Chọn tệp</span>
              <span className="teacher-file-picker-name">{drawing?.name ?? "Chưa chọn tệp"}</span>
              <input id={drawingInputId} className="teacher-file-picker-input" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" aria-labelledby={drawingLabelId} onChange={(e) => setDrawing(e.target.files?.[0] ?? null)} />
            </label>
          </div>
          <FormActionBar hint={!busy && !drawing ? "Chọn ảnh bức tranh để bật nút tải ảnh." : undefined}>
            {busy && <button type="button" className="s2l-button" onClick={() => void stop()}>{c.stop}</button>}
            <button type="button" className={primaryStep === "artwork" ? "s2l-button is-primary" : "s2l-button"} disabled={busy || !drawing} onClick={() => void sendDrawing()}>{c.upload}</button>
          </FormActionBar>
        </section>
      )}
      {actions.idea && (
        <section className="cozy-form-section cozy-form-stack tp-run-section">
          <div className="tp-form-section-intro"><h3>2. Ý tưởng và ghi âm</h3></div>
          <div className="cozy-form-field">
            <label className="cozy-form-label" htmlFor={ideaInputId}>{c.idea}</label>
            <textarea id={ideaInputId} className="cozy-textarea" rows={3} value={idea} onChange={(e) => setIdea(e.target.value)} />
          </div>
          <div className="teacher-file-field">
            <span id={audioLabelId} className="cozy-form-label">{c.audio}</span>
            <label className="teacher-file-picker" htmlFor={audioInputId}>
              <span className="teacher-file-picker-button"><Upload size={16} aria-hidden="true" /> Chọn tệp</span>
              <span className="teacher-file-picker-name">{audio?.name ?? "Chưa chọn tệp"}</span>
              <input id={audioInputId} className="teacher-file-picker-input" type="file" accept="audio/wav,audio/mp4" aria-labelledby={audioLabelId} onChange={(e) => setAudio(e.target.files?.[0] ?? null)} />
            </label>
          </div>
          <FormActionBar>
            <button type="button" className={primaryStep === "idea" ? "s2l-button is-primary" : "s2l-button"} disabled={busy} onClick={() => void sendIdea()}>{c.submitIdea}</button>
          </FormActionBar>
        </section>
      )}
      {actions.transcript && transcript?.state === "PENDING" && (
        <section className="cozy-form-section cozy-form-stack tp-run-section">
          <p className="s2l-note">{c.pending}</p>
          <FormActionBar>
            <button type="button" className="s2l-button" onClick={() => setPollVersion((v) => v + 1)}>{c.refresh}</button>
          </FormActionBar>
        </section>
      )}
      {actions.transcript && transcript?.state === "NEEDS_CONFIRMATION" && (
        <section className="cozy-form-section cozy-form-stack tp-run-section">
          <div className="tp-form-section-intro"><h3>2. Xác nhận nội dung ghi âm</h3></div>
          <p className="s2l-note"><span><strong>{c.transcript}:</strong> {transcript.text}</span></p>
          {showCorrection && (
            <div className="cozy-form-field">
              <label className="cozy-form-label" htmlFor={correctionInputId}>{c.correction}</label>
              <textarea id={correctionInputId} className="cozy-textarea" rows={3} value={correction} onChange={(e) => setCorrection(e.target.value)} />
            </div>
          )}
          <FormActionBar>
            {showCorrection && <button type="button" className="s2l-button" disabled={busy} onClick={() => void correct()}>{c.saveCorrection}</button>}
            <button type="button" className={primaryStep === "transcript" ? "s2l-button is-primary" : "s2l-button"} disabled={busy} onClick={() => void confirmTranscript()}>{c.confirmTranscript}</button>
          </FormActionBar>
        </section>
      )}
      {actions.context && run.context_snapshot && (
        <section className="cozy-form-section cozy-form-stack tp-run-section">
          <div className="tp-form-section-intro"><h3>3. {c.context}</h3></div>
          <div className="tp-field-grid" style={{ marginTop: 0 }}>
            <p className="tp-field"><strong>{c.age}</strong><span>{run.context_snapshot.age_months}</span></p>
            {run.context_snapshot.activity_title && <p className="tp-field"><strong>{c.activity}</strong><span>{run.context_snapshot.activity_title}</span></p>}
            {run.context_snapshot.objectives && <p className="tp-field"><strong>{c.objectives}</strong><span>{run.context_snapshot.objectives.join(", ")}</span></p>}
            {run.context_snapshot.teacher_direction && <p className="tp-field"><strong>{c.direction}</strong><span>{run.context_snapshot.teacher_direction}</span></p>}
          </div>
          <FormActionBar>
            <button type="button" className={primaryStep === "context" ? "s2l-button is-primary" : "s2l-button"} disabled={busy} onClick={() => void confirmContext()}>{c.confirmContext}</button>
          </FormActionBar>
        </section>
      )}
      {actions.subject && run.candidate && (
        <section className="cozy-form-section cozy-form-stack tp-run-section">
          <div className="tp-form-section-intro"><h3>4. Xác nhận chủ thể bức tranh</h3></div>
          <div className="cozy-form-field">
            <label className="cozy-form-label" htmlFor={subjectInputId}>{c.subject}</label>
            <input id={subjectInputId} className="cozy-input" value={subject} onChange={(e) => setSubjectDraft({ revision: run.understanding_revision, value: e.target.value })} />
          </div>
          <p className="tp-field"><strong>{c.features}</strong><span>{run.candidate.visible_features.slice(0, 4).join(", ")}</span></p>
          {others.length > 0 && (
            <fieldset className="cozy-form-stack">
              <legend className="cozy-form-label">{c.others}</legend>
              {others.map((entity) => (
                <label key={entity.entity_id} className="cozy-form-checkbox-card">
                  <input type="checkbox" checked={isKept(entity)} onChange={(e) => setKept((current) => ({ ...current, [`${run.understanding_revision}:${entity.entity_id}`]: e.target.checked }))} />
                  <span>{entity.label}</span>
                </label>
              ))}
            </fieldset>
          )}
          <FormActionBar>
            <button type="button" className={primaryStep === "subject" ? "s2l-button is-primary" : "s2l-button"} disabled={busy} onClick={() => void confirmSubject()}>{c.confirmSubject}</button>
          </FormActionBar>
        </section>
      )}
    </div>
  );
}
