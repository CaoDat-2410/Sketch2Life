import { TeacherRunInputs } from "../components/TeacherRunInputs";
import { TeacherRunStory } from "../components/TeacherRunStory";
import { TeacherRunVideo } from "../components/TeacherRunVideo";
import { FormActionBar } from "../components/FormActionBar";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { ConfirmDialog, EmptyState, FormField, StatusBadge } from "../../../shared/ui";
import { teacherStatusMeta } from "../services/teacherStatus";
import { BackendApiError, configuredOrganizationId } from "../../../shared/api/backendApi";
import { teacherOccurrenceApi, type Occurrence, type PlanRevision } from "../../../shared/api/teacherOccurrenceApi";
import { teacherRunApi, type ChildSelection, type RunResponse, type TeacherRun } from "../../../shared/api/teacherRunApi";
import { teacherQuotaApi } from "../../../shared/api/teacherQuotaApi";
import { ActionKeys } from "../services/actionKeys";
import { rememberSampleRun } from "../services/lastSampleRun";
import { ageLabel, copy, deleteErrorCopy, errorCopy, stateLabel, storyVideoCopy } from "../services/teacherRunCopy";
import { availableActions, shouldPoll, waitingForFirstStory } from "../services/teacherRunLogic";

type PendingRunAction = {
  kind: "cancel" | "delete";
  occurrenceId: string;
  runId: string;
  runRevision: number;
  runState: string;
};

export function TeacherSampleRunPage() {
  const [params] = useSearchParams();
  const id = params.get("occurrence") ?? "";
  return <SampleRunForOccurrence key={id} id={id} />;
}

function SampleRunForOccurrence({ id }: { id: string }) {
  const activitySelectId = useId();
  const quotaOrganizationId = configuredOrganizationId();
  const valid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
  const [occ, setOcc] = useState<Occurrence | null>(null);
  const [plan, setPlan] = useState<PlanRevision | null>(null);
  const [selection, setSelection] = useState<ChildSelection | null>(null);
  const [selectionReady, setSelectionReady] = useState(false);
  const [activity, setActivity] = useState("");
  const [run, setRun] = useState<TeacherRun | null>(null);
  const [lifecycle, setLifecycle] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [purgeState, setPurgeState] = useState("");
  const [quotaBalance, setQuotaBalance] = useState<string>(quotaOrganizationId ? copy.quotaLoading : copy.quotaUnavailable);
  const [now, setNow] = useState(0);
  const [planFenceRunId, setPlanFenceRunId] = useState<string | null>(null);
  const [pendingRunAction, setPendingRunAction] = useState<PendingRunAction | null>(null);
  const pollStart = useRef<{ id: string; at: number } | null>(null);
  const keys = useRef(new ActionKeys());
  const runEtag = useRef<string | undefined>(undefined);
  const runEtagId = useRef<string | undefined>(undefined);
  const selectionEtag = useRef<string | undefined>(undefined);
  const occurrenceEtag = useRef<string | undefined>(undefined);
  const lock = useRef(false);

  const fail = useCallback((cause: unknown) => {
    setError(errorCopy(cause));
    if (cause instanceof BackendApiError && cause.status === 404) {
      setRun(null); setSelection(null); setOcc(null); setPlan(null); setLifecycle(""); setPurgeState("");
    }
  }, []);

  const applyRun = useCallback((value: RunResponse) => {
    setSelection(null);
    setSelectionReady(false);
    if ("lifecycle" in value) {
      setRun(null); setLifecycle(value.lifecycle.run_state); setPurgeState(value.lifecycle.purge_state); setPlanFenceRunId(null);
    } else {
      setLifecycle(""); setPurgeState(""); setRun(value.story_run);
      setPlanFenceRunId((current) => current && value.story_run?.run_id !== current ? null : current);
    }
  }, []);

  const loadOccurrence = useCallback(async (): Promise<Occurrence | null> => {
    const result = await teacherOccurrenceApi.get(id, occurrenceEtag.current);
    if (result.etag) occurrenceEtag.current = result.etag;
    if (result.data) {
      setOcc(result.data);
      if (result.data.approved_plan) {
        const p = await teacherOccurrenceApi.getPlan(id, result.data.approved_plan.revision_no);
        setPlan(p.data);
      } else setPlan(null);
    }
    return result.data;
  }, [id]);

  const active = useCallback(async () => {
    const response = await teacherRunApi.active();
    if ("lifecycle" in response) {
      setRun(null); setLifecycle(response.lifecycle.run_state); setPurgeState(response.lifecycle.purge_state);
    } else {
      setRun(response.story_run); setLifecycle(""); setPurgeState("");
    }
    return response;
  }, []);

  const refreshRun = useCallback(async (runId: string, signal?: AbortSignal, force = false): Promise<TeacherRun | null> => {
    if (force || runEtagId.current !== runId) {
      runEtagId.current = runId;
      runEtag.current = undefined;
    }
    try {
      const result = await teacherRunApi.get(runId, runEtag.current, signal);
      if (result.etag) runEtag.current = result.etag;
      if (result.data) {
        applyRun(result.data);
        return "story_run" in result.data ? result.data.story_run : null;
      }
    } catch (e) {
      if (!(e instanceof Error && e.name === "AbortError")) fail(e);
    }
    return null;
  }, [applyRun, fail]);

  useEffect(() => {
    let alive = true;
    async function load() {
      setLoading(true); setError(""); setRun(null); setSelection(null); setOcc(null); setPlan(null);
      setLifecycle(""); setPurgeState(""); setPlanFenceRunId(null);
      runEtag.current = undefined; runEtagId.current = undefined;
      if (valid) {
        try {
          const [current, occurrence] = await Promise.all([active(), loadOccurrence()]);
          if (alive && "story_run" in current && !current.story_run && occurrence?.sample_video.run_ref) {
            await refreshRun(occurrence.sample_video.run_ref);
          }
        } catch (e) {
          if (alive) fail(e);
        }
      }
      if (alive) setLoading(false);
    }
    void load();
    return () => { alive = false; };
  }, [valid, id, active, loadOccurrence, refreshRun, fail]);

  useEffect(() => {
    if (!selection?.confirmation_expires_at || selection.state !== "CONFIRMED") return;
    const delay = Date.parse(selection.confirmation_expires_at) - Date.now();
    const timer = setTimeout(() => setNow(Date.now()), Math.max(0, Math.min(delay, 2147483647)));
    return () => clearTimeout(timer);
  }, [selection]);

  useEffect(() => {
    let alive = true;
    if (!quotaOrganizationId) return () => { alive = false; };
    teacherQuotaApi.getMyVideoQuota(quotaOrganizationId)
      .then((value) => { if (alive) setQuotaBalance(!value.allocation || !value.allocation.active ? copy.noQuota : copy.quotaBalance(value.allocation.available_units)); })
      .catch((cause: unknown) => { if (alive) setQuotaBalance(cause instanceof BackendApiError && cause.status === 503 ? copy.quotaServiceUnavailable : copy.quotaUnavailable); });
    return () => { alive = false; };
  }, [quotaOrganizationId]);

  const sampleRunId = run && run.occurrence_id === id ? run.run_id : null;
  useEffect(() => { if (sampleRunId) rememberSampleRun(id, sampleRunId); }, [id, sampleRunId]);

  const pollingRunId = run && run.occurrence_id === id && shouldPoll(run) ? run.run_id : null;
  const pollingState = run?.run_state;
  useEffect(() => {
    if (!pollingRunId) { pollStart.current = null; return; }
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let delay = 2000;
    const marker = `${pollingRunId}:${pollingState}`;
    if (pollStart.current?.id !== marker) pollStart.current = { id: marker, at: Date.now() };
    const started = pollStart.current.at;
    const tick = () => {
      timer = setTimeout(() => {
        if (Date.now() - started >= 600000) return;
        if (document.hidden) { tick(); return; }
        void (async () => { if (!controller.signal.aborted) await refreshRun(pollingRunId, controller.signal); })()
          .finally(() => { if (!controller.signal.aborted) { delay = Math.min(delay * 2, 10000); tick(); } });
      }, delay);
    };
    tick();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [pollingRunId, pollingState, refreshRun]);

  async function command<T>(fingerprint: unknown[], action: (key: string) => Promise<T>): Promise<T | undefined> {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError("");
    try {
      const value = await action(keys.current.key(...fingerprint));
      keys.current.settled(fingerprint);
      return value;
    } catch (e) {
      keys.current.settled(fingerprint, e);
      throw e;
    } finally {
      lock.current = false; setBusy(false);
    }
  }

  async function readSelection(value: ChildSelection) {
    if (!value.selection_id) { setSelection(value); setSelectionReady(false); return; }
    const result = await teacherRunApi.getSelection(id, value.selection_id, selectionEtag.current);
    if (result.etag) selectionEtag.current = result.etag;
    const next = result.data ?? value;
    setSelection(next);
    setSelectionReady(next.state === "OPEN" && !!next.child);
  }

  async function draw() {
    try {
      selectionEtag.current = undefined;
      const result = await command(["draw", id], (key) => teacherRunApi.draw(id, key));
      if (result) { setSelection(result); await readSelection(result); }
    } catch (e) { fail(e); }
  }

  async function confirm() {
    if (!selection?.selection_id || selection.revision === null || !selection.selection_sha256) return;
    const s = selection;
    try {
      const result = await command(["confirm", id, s.selection_id, s.revision, s.selection_sha256], (key) => teacherRunApi.confirmSelection(id, s.selection_id!, s.revision!, s.selection_sha256!, key));
      if (result) { setSelection(result); setSelectionReady(false); }
    } catch (e) {
      fail(e);
      if (e instanceof BackendApiError && e.code === "STALE_REVISION") {
        try { selectionEtag.current = undefined; await readSelection(s); } catch (err) { fail(err); }
      }
    }
  }

  async function create() {
    if (!selection?.child || !selection.selection_id || !selection.selection_sha256 || !selection.plan || !activity || !selection.confirmation_expires_at || Date.parse(selection.confirmation_expires_at) <= Date.now()) return;
    const input = { profile_ref: { kind: "MANAGED_PROFILE" as const, id: selection.child.profile_id }, occurrence_id: id, plan: selection.plan, activity_id: activity, selection_id: selection.selection_id, selection_sha256: selection.selection_sha256 };
    try {
      const response = await command(["create", input], (key) => teacherRunApi.create(input, key));
      if (response) applyRun(response);
    } catch (e) {
      if (e instanceof BackendApiError && e.code === "ACTIVE_RUN_EXISTS") {
        try {
          setSelection(null);
          const current = await active();
          if ("story_run" in current && !current.story_run) setError(copy.active);
        } catch (err) { fail(err); }
      } else {
        fail(e);
        if (e instanceof BackendApiError && e.code === "STALE_REVISION") {
          try { await loadOccurrence(); selectionEtag.current = undefined; await readSelection(selection); } catch (err) { fail(err); }
        }
      }
    }
  }

  async function storyVideoCommand(fingerprint: unknown[], action: (key: string) => Promise<unknown>) {
    if (!run) return;
    const sentRunRevision = run.run_revision;
    try {
      const result = await command(fingerprint, action);
      if (!result) return;
      if (typeof result === "object" && ("story_run" in result || "lifecycle" in result)) applyRun(result as RunResponse);
      else await refreshRun(run.run_id);
    } catch (e) {
      if (fingerprint[0] === "generate" && e instanceof BackendApiError && e.status === 409 && e.code === "STALE_REVISION") {
        const current = await refreshRun(run.run_id, undefined, true);
        if (current?.run_revision === sentRunRevision) { setPlanFenceRunId(run.run_id); setError(storyVideoCopy.planFence); }
        else setError(errorCopy(e));
        return;
      }
      fail(e);
    }
  }

  const options = plan?.activities.filter((a) => !!a.plan_activity_id) ?? [];
  const canDraw = occ && ["APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"].includes(occ.state) && occ.approved_plan && occ.sample_video.slot_state === "AVAILABLE";
  const runActions = run ? availableActions(run) : { cancel: false, delete: false };
  const activePendingRunAction = pendingRunAction &&
    run &&
    pendingRunAction.occurrenceId === id &&
    run.run_id === pendingRunAction.runId &&
    run.run_revision === pendingRunAction.runRevision &&
    run.run_state === pendingRunAction.runState &&
    (pendingRunAction.kind === "cancel" ? runActions.cancel : runActions.delete)
    ? pendingRunAction
    : null;

  if (pendingRunAction && !activePendingRunAction) {
    setPendingRunAction(null);
  }

  function requestCancel() {
    if (!run || lock.current || busy || activePendingRunAction) return;
    setPendingRunAction({ kind: "cancel", occurrenceId: id, runId: run.run_id, runRevision: run.run_revision, runState: run.run_state });
  }

  function requestDeleteRun() {
    if (!run || lock.current || busy || activePendingRunAction) return;
    setPendingRunAction({ kind: "delete", occurrenceId: id, runId: run.run_id, runRevision: run.run_revision, runState: run.run_state });
  }

  async function confirmRunAction() {
    const action = activePendingRunAction;
    if (!action) return;
    setPendingRunAction(null);
    if (action.kind === "cancel") {
      try {
        const value = await command(["cancel", action.runId, action.runRevision], (key) => teacherRunApi.cancel(action.runId, action.runRevision, key));
        if (value) applyRun(value);
      } catch (e) { fail(e); }
      return;
    }
    try {
      const value = await command(["delete", action.runId], (key) => teacherRunApi.delete(action.runId, key));
      if (value) applyRun(value);
    } catch (e) {
      setError(deleteErrorCopy(e));
      if (e instanceof BackendApiError && e.status === 404) {
        setRun(null); setSelection(null); setOcc(null); setPlan(null); setLifecycle(""); setPurgeState("");
      }
    }
  }

  const isOwnRun = run?.occurrence_id === id;
  const runStatusTone = run ? teacherStatusMeta(run.run_state, "job").tone : "neutral";
  const destructiveAction = run && runActions.cancel
    ? <button type="button" className="s2l-button tp-quiet-danger" disabled={busy || Boolean(activePendingRunAction)} onClick={requestCancel}>{copy.cancel}</button>
    : run && runActions.delete
      ? <button type="button" className="s2l-button tp-quiet-danger" disabled={busy || Boolean(activePendingRunAction)} onClick={requestDeleteRun}>{copy.delete}</button>
      : undefined;

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading
        eyebrow="Giáo viên · Buổi dạy"
        title={copy.title}
        description="Chọn bé, xem kịch bản và tạo video mẫu cho buổi dạy."
        action={valid ? <Link className="s2l-button" to="/teacher/t04-session-sketch-deck">{copy.back}</Link> : undefined}
      />
      {!valid ? (
        <section className="s2l-data-card">
          <EmptyState
            title="Chưa chọn buổi dạy"
            description={copy.missing}
            action={<Link className="s2l-button is-primary" to="/teacher/t04-session-sketch-deck">Chọn buổi dạy</Link>}
          />
        </section>
      ) : !run ? (
        <section className="s2l-data-card cozy-form-stack">
          <div className="tw-row tw-between tw-wrap">
            <span className="tp-value-chip" role="status">{quotaBalance}</span>
          </div>
          {loading && <p className="s2l-muted-copy" role="status">{copy.loading}</p>}
          {error && <p className="s2l-alert" role="alert">{error}</p>}
          {lifecycle && (
            <div className="cozy-form-stack">
              <StatusBadge tone="neutral" dot>{stateLabel(lifecycle)}</StatusBadge>
              {(lifecycle === "DELETE_PENDING" || purgeState === "PENDING") && <p className="s2l-muted-copy" role="status">{copy.deletePending}</p>}
              {lifecycle === "DELETED" && purgeState !== "PENDING" && <p className="s2l-muted-copy" role="status">{copy.deleted}</p>}
            </div>
          )}
        </section>
      ) : (
        error && <p className="s2l-alert" role="alert">{error}</p>
      )}

      {run && (
        <div className="cozy-form-stack">
          <section className="s2l-data-card cozy-form-stack" aria-label="Trạng thái lượt video mẫu">
            <div className="s2l-section-heading">
              <div>
                <h2>{occ?.title ?? "Lượt video mẫu"}</h2>
                {isOwnRun && run.video && <p className="tw-meta">{copy.videoSummary}: {stateLabel(run.run_state)}</p>}
              </div>
              <div className="tp-chip-row">
                <span className="tp-value-chip" role="status">{quotaBalance}</span>
                {isOwnRun && <StatusBadge tone={runStatusTone} dot>{stateLabel(run.run_state)}</StatusBadge>}
              </div>
            </div>
            {run.occurrence_id && run.occurrence_id !== id && (
              <div className="s2l-note">
                <span>{copy.active} {copy.other}</span>
                <Link className="s2l-button" to={`/teacher/t06-sample-story-run?occurrence=${encodeURIComponent(run.occurrence_id)}`}>{copy.openOther}</Link>
              </div>
            )}
            {isOwnRun && (run.story_revision_no === null || !run.story) && (
              <p className="s2l-muted-copy">
                {run.run_state === "SCRIPT_GENERATING" ? copy.generatingStory : waitingForFirstStory(run) ? copy.waitingStory : copy.firstStory}
              </p>
            )}
            <FormActionBar danger={destructiveAction}>
              {run.occurrence_id === id && (
                <Link className="s2l-button" to={`/teacher/t07-video-presentation-confirmation?occurrence=${encodeURIComponent(id)}`}>Chiếu cho lớp</Link>
              )}
              <button type="button" className="s2l-button" onClick={() => { if (isOwnRun) void refreshRun(run.run_id); else void active().catch(fail); void loadOccurrence().catch(fail); }}>{copy.refresh}</button>
            </FormActionBar>
          </section>

          {isOwnRun && <><TeacherRunInputs key={run.run_id} run={run} refresh={async () => { await refreshRun(run.run_id); }} fail={fail} lifecycle={applyRun} />
          <TeacherRunStory key={`story-${run.run_id}`} run={run} execute={storyVideoCommand} planFenced={planFenceRunId === run.run_id} />
          <TeacherRunVideo key={`video-${run.run_id}`} run={run} fail={fail} execute={storyVideoCommand} planFenced={planFenceRunId === run.run_id} /></>}
        </div>
      )}

      {!loading && !run && !lifecycle && occ && (
        <section className="s2l-data-card cozy-form-stack">
          <div className="tp-form-column">
            {!canDraw ? (
              <p className="s2l-note">{!occ.approved_plan ? copy.noPlan : occ.sample_video.slot_state !== "AVAILABLE" ? copy.used : copy.unavailable}</p>
            ) : !selection ? (
              <div className="cozy-form-section">
                <div className="tp-form-section-intro">
                  <h3>1. Chọn bé cho video mẫu</h3>
                  <p>Hệ thống chọn ngẫu nhiên một trẻ đủ điều kiện trong lớp để tạo video mẫu.</p>
                </div>
                <FormActionBar>
                  <button type="button" className="s2l-button is-primary" disabled={busy} onClick={() => void draw()}>{copy.draw}</button>
                </FormActionBar>
              </div>
            ) : (
              <>
                {selection.child && ["OPEN", "CONFIRMED"].includes(selection.state) && (
                  <div className="cozy-form-section">
                    <div className="tp-form-section-intro">
                      <h3>1. Thông tin bé được chọn</h3>
                      <p>{copy.offer}</p>
                    </div>
                    <p className="s2l-note"><span><strong>{selection.child.display_name}</strong> · {ageLabel(selection.child.age_months)}</span></p>
                    <p className="s2l-muted-copy">{copy.until} {new Date((selection.state === "CONFIRMED" ? selection.confirmation_expires_at : selection.expires_at) ?? "").toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}</p>
                    {selection.state === "OPEN" && (
                      <FormActionBar>
                        <button type="button" className="s2l-button is-primary" disabled={busy || !selectionReady} onClick={() => void confirm()}>{copy.confirm}</button>
                      </FormActionBar>
                    )}
                  </div>
                )}
                {selection.state === "CONFIRMED" && (
                  <div className="cozy-form-section">
                    <div className="tp-form-section-intro">
                      <h3>2. Chọn hoạt động và bắt đầu</h3>
                      <p>Chọn một hoạt động từ kế hoạch đã duyệt để khởi tạo lượt tạo video mẫu.</p>
                    </div>
                    {options.length === 0 ? (
                      <p className="s2l-note">{copy.activityGap}</p>
                    ) : (
                      <FormField label={copy.activity} htmlFor={activitySelectId} required>
                        <select id={activitySelectId} className="cozy-input" value={activity} onChange={(e) => setActivity(e.target.value)}>
                          <option value="">—</option>
                          {options.map((a) => <option key={a.plan_activity_id} value={a.plan_activity_id!}>{a.title ?? copy.activity}</option>)}
                        </select>
                      </FormField>
                    )}
                    <FormActionBar hint={!activity && options.length > 0 ? "Chọn hoạt động ở trên để bật nút bắt đầu." : undefined}>
                      <button type="button" className="s2l-button is-primary" disabled={busy || !activity || !selection.confirmation_expires_at || Date.parse(selection.confirmation_expires_at) <= now} onClick={() => void create()}>{copy.create}</button>
                    </FormActionBar>
                  </div>
                )}
                {(["EXPIRED", "STALE", "VOID"].includes(selection.state)) && (
                  <div className="cozy-form-stack">
                    <p className="s2l-alert">{selection.state === "STALE" ? copy.stale : copy.expired}</p>
                    <FormActionBar>
                      <button type="button" className="s2l-button is-primary" disabled={busy} onClick={() => void draw()}>{copy.reselect}</button>
                    </FormActionBar>
                  </div>
                )}
                {(selection.outcome === "NO_ELIGIBLE_CHILD" || selection.state === "EMPTY") && selection.state !== "STOPPED" && <p className="s2l-note">{copy.empty}</p>}
                {selection.state === "STOPPED" && <p className="s2l-note">{copy.stopped}</p>}
                {selection.state === "CONSUMED" && (
                  <div className="cozy-form-stack">
                    <p className="s2l-note">{copy.consumed}</p>
                    {selection.consumed_run_ref && (
                      <FormActionBar>
                        <button type="button" className="s2l-button is-primary" onClick={() => void refreshRun(selection.consumed_run_ref!)}>{copy.openRun}</button>
                      </FormActionBar>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </section>
      )}
      <ConfirmDialog
        open={Boolean(activePendingRunAction)}
        onOpenChange={(open) => {
          if (!open) setPendingRunAction(null);
        }}
        title={activePendingRunAction?.kind === "delete" ? "Xóa lượt kể chuyện?" : "Hủy lượt?"}
        description={activePendingRunAction?.kind === "delete" ? copy.deleteConfirm : copy.cancelConfirm}
        confirmLabel={activePendingRunAction?.kind === "delete" ? "Xóa" : "Hủy lượt"}
        tone="danger"
        onConfirm={() => { void confirmRunAction(); }}
      />
    </div>
  );
}
