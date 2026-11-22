import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, LockKeyhole, RefreshCw, UserPlus, Users } from "lucide-react";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { Alert, Button, FormField, Select } from "../../../shared/ui";
import {
  BackendApiError,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  createIdempotencyKey,
  hasFirebaseAuthBridge,
  type Be1Class,
} from "../../../shared/api/backendApi";
import {
  CLASS_READ_ONLY,
  NOT_FOUND_OR_NO_ACCESS,
  PROFILE_AGE_MONTHS,
  PROFILE_NAME_MAX,
  STALE_RELOADED,
  SYNTHETIC_NAME_PREFIX,
  TeacherRosterApiError,
  keepsCommandKey,
  profileInputProblem,
  teacherRosterApi,
  type TeacherConsent,
  type TeacherProfile,
} from "../../../shared/api/teacherRosterApi";

const STATE_LABELS: Record<string, string> = { active: "Đang hoạt động", suspended: "Tạm ngưng · chỉ đọc", archived: "Đã lưu trữ" };
const stateLabel = (state: string) => STATE_LABELS[state] ?? state;

function NoBackendSession() {
  return <div className="s2l-note"><LockKeyhole size={15} aria-hidden="true" />Lớp và hồ sơ chỉ tải khi có phiên Firebase cùng assignment Teacher đang hiệu lực.</div>;
}

/** Roster messages are already projected (uniform 404, safe 403, Retry-After); other errors use the shared text. */
function rosterError(cause: unknown): string {
  if (cause instanceof TeacherRosterApiError && cause.code !== "CONSENT_NOT_EFFECTIVE") {
    return cause.message + (cause.requestId ? ` Mã yêu cầu: ${cause.requestId}.` : "");
  }
  return backendMessage(cause);
}

/** What a failed command means for the screen: reload after a stale or state refusal (SRS l.1724). */
function commandOutcome(cause: unknown): { text: string; reload: boolean } {
  const text = rosterError(cause);
  if (cause instanceof BackendApiError) {
    if (cause.code === "STALE_REVISION") return { text: `${text} ${STALE_RELOADED}`, reload: true };
    if (cause.code === "INVALID_STATE_TRANSITION" || cause.status === 404) return { text, reload: true };
  }
  return { text, reload: false };
}

export function TeacherApiClassesPage() {
  const navigate = useNavigate();
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    const organizationId = configuredOrganizationId();
    if (!hasFirebaseAuthBridge()) {
      setError("Chưa có Firebase ID token để tải các lớp được phân công.");
      setLoading(false);
      return () => { active = false; };
    }
    if (!organizationId) {
      setError("Chưa cấu hình organization_id cho các API Teacher.");
      setLoading(false);
      return () => { active = false; };
    }

    setLoading(true);
    setError(null);
    backendApi.assignments(organizationId)
      .then(async (identity) => {
        const assignedClassIds = new Set(identity.assignments
          .filter((assignment) => assignment.role === "teacher" && assignment.active !== false)
          .flatMap((assignment) => assignment.class_id ? [assignment.class_id] : []));
        if (assignedClassIds.size === 0) return [];
        // T-7b: a suspended class stays visible to its Teacher (read-only); archived is never listed.
        const page = await backendApi.classes(organizationId, "all");
        return page.items.filter((item) => assignedClassIds.has(item.class_id));
      })
      .then((items) => { if (active) setClasses(items); })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reload]);

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading eyebrow="Teacher · Phạm vi assignment" title="Lớp được phân công" description="Chỉ lớp có assignment Teacher đang hoạt động mới xuất hiện." action={<button type="button" className="s2l-button" disabled={loading} onClick={() => setReload((value) => value + 1)}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>} />
      {!hasFirebaseAuthBridge() && <NoBackendSession />}
      {loading && <p className="s2l-data-card" role="status">Đang xác minh assignment Teacher…</p>}
      {error && <div className="s2l-alert" role="alert">{error}</div>}
      {!loading && !error && classes.length === 0 && <p className="s2l-data-card">Không có lớp nào trong assignment Teacher hiện hành.</p>}
      {!loading && !error && classes.map((item) => (
        <button key={item.class_id} type="button" className="s2l-class-row" onClick={() => navigate("/teacher/t05-classes-and-children/" + encodeURIComponent(item.class_id))}>
          <span className="s2l-class-mark"><Users size={18} aria-hidden="true" /></span>
          <span className="s2l-class-copy"><strong>{item.display_name}</strong><small>Trạng thái lớp · {stateLabel(item.state)}</small></span>
          <span className="s2l-class-open">Xem roster <ArrowRight size={15} aria-hidden="true" /></span>
        </button>
      ))}
      <div className="s2l-note"><LockKeyhole size={15} aria-hidden="true" />Hồ sơ trẻ chỉ hiển thị khi API xác minh assignment và consent hiệu lực.</div>
    </div>
  );
}

type MoveDraft = { childId: string; targetClassId: string };

function TeacherApiClassDetailPage({ classId }: { classId: string }) {
  const navigate = useNavigate();
  const organizationId = configuredOrganizationId();
  const [classItem, setClassItem] = useState<Be1Class | null>(null);
  const [moveTargets, setMoveTargets] = useState<Be1Class[]>([]);
  const [profiles, setProfiles] = useState<TeacherProfile[]>([]);
  const [consents, setConsents] = useState<TeacherConsent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileErrorCode, setProfileErrorCode] = useState<string | null>(null);
  const [profileErrorRequestId, setProfileErrorRequestId] = useState<string | null>(null);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  // T-7c / T-7d commands: one Idempotency-Key per exact user action, kept only while its outcome is unknown.
  const commandKeys = useRef(new Map<string, string>());
  const [busy, setBusy] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [retrySignature, setRetrySignature] = useState<string | null>(null);
  const [profileName, setProfileName] = useState(SYNTHETIC_NAME_PREFIX);
  const [ageMonths, setAgeMonths] = useState("60");
  const [moveDraft, setMoveDraft] = useState<MoveDraft | null>(null);

  useEffect(() => {
    let active = true;
    if (!hasFirebaseAuthBridge() || !organizationId) {
      setError(!hasFirebaseAuthBridge() ? "Chưa có Firebase ID token." : "Chưa cấu hình organization_id.");
      setLoading(false);
      return () => { active = false; };
    }

    setLoading(true);
    setError(null);
    setProfileError(null);
    setProfileErrorCode(null);
    setProfileErrorRequestId(null);
    setConsentError(null);
    setProfiles([]);
    setConsents([]);
    // T-7a2 (SRS l.864-865, AC-27): the server decides 403 versus the uniform 404 for this class; the
    // page no longer turns a class outside the caller's rows into its own 403.
    Promise.allSettled([
      backendApi.classes(organizationId, "all"),
      teacherRosterApi.profiles(organizationId, classId),
      teacherRosterApi.consents(organizationId, classId),
      backendApi.assignments(organizationId),
    ]).then(([classResult, profileResult, consentResult, identityResult]) => {
      if (!active) return;
      const profileConsentLocked = profileResult.status === "rejected"
        && profileResult.reason instanceof BackendApiError
        && profileResult.reason.code === "CONSENT_NOT_EFFECTIVE";
      const scopeFailure = [profileResult, consentResult]
        .flatMap((result, index) => result.status === "rejected"
          && !(index === 0 && profileConsentLocked)
          && result.reason instanceof BackendApiError
          && (result.reason.status === 404 || result.reason.status === 403) ? [result.reason] : [])
        .sort((left, right) => right.status - left.status)[0];
      if (scopeFailure) { setClassItem(null); setError(rosterError(scopeFailure)); return; }
      if (classResult.status === "rejected") { setClassItem(null); setError(backendMessage(classResult.reason)); return; }
      const actualClass = classResult.value.items.find((item) => item.class_id === classId) ?? null;
      if (!actualClass) { setClassItem(null); setError(NOT_FOUND_OR_NO_ACCESS); return; }
      setClassItem(actualClass);
      const ownClassIds = identityResult.status === "fulfilled"
        ? new Set(identityResult.value.assignments
          .filter((assignment) => assignment.role === "teacher" && assignment.active !== false && assignment.class_id)
          .map((assignment) => assignment.class_id as string))
        : new Set<string>();
      // T-7d: a move goes only to another active class taught by the same Teacher.
      setMoveTargets(classResult.value.items.filter((item) =>
        item.class_id !== classId && item.state === "active" && item.class_revision !== undefined && ownClassIds.has(item.class_id)));
      if (consentResult.status === "fulfilled") setConsents(consentResult.value);
      else setConsentError(rosterError(consentResult.reason));
      if (profileResult.status === "fulfilled") setProfiles(profileResult.value);
      else {
        setProfileError(rosterError(profileResult.reason));
        setProfileErrorCode(profileResult.reason instanceof BackendApiError ? profileResult.reason.code : null);
        setProfileErrorRequestId(profileResult.reason instanceof BackendApiError ? profileResult.reason.requestId ?? null : null);
      }
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [classId, organizationId, reload]);

  const visibleProfiles = profiles.filter((profile) =>
    consents.some((consent) => consent.child_id === profile.child_id && consent.effective),
  );
  const classRevision = classItem?.class_revision;
  const writable = classItem?.state === "active" && classRevision !== undefined;

  const runCommand = async (signature: string, send: (key: string) => Promise<string>) => {
    if (busy) return;
    const key = commandKeys.current.get(signature) ?? createIdempotencyKey();
    commandKeys.current.set(signature, key);
    setBusy(true); setCommandError(null); setNotice(null);
    try {
      const done = await send(key);
      commandKeys.current.delete(signature);
      setRetrySignature(null);
      setNotice(done);
      setMoveDraft(null);
      setReload((value) => value + 1);
    } catch (cause) {
      const keep = keepsCommandKey(cause);
      if (!keep) commandKeys.current.delete(signature);
      setRetrySignature(keep ? signature : null);
      const outcome = commandOutcome(cause);
      setCommandError(keep ? `${outcome.text} Hãy gửi lại cùng yêu cầu.` : outcome.text);
      if (outcome.reload) { setMoveDraft(null); setReload((value) => value + 1); }
    } finally {
      setBusy(false);
    }
  };

  const age = Number(ageMonths);
  const profileInput = { display_name: profileName, age_months: age };
  const inputProblem = profileInputProblem(profileInput);
  const showFieldProblems = profileName !== SYNTHETIC_NAME_PREFIX || ageMonths !== "60";
  const nameProblem = showFieldProblems
    ? !profileName.startsWith(SYNTHETIC_NAME_PREFIX) || profileName.trim().length <= SYNTHETIC_NAME_PREFIX.trim().length
      ? `Tên hồ sơ thử nghiệm phải bắt đầu bằng “${SYNTHETIC_NAME_PREFIX}” và có thêm tên phía sau.`
      : profileName.length > PROFILE_NAME_MAX
        ? `Tên hồ sơ tối đa ${PROFILE_NAME_MAX} ký tự.`
        : undefined
    : undefined;
  const ageProblem = showFieldProblems && (!Number.isInteger(age) || age < PROFILE_AGE_MONTHS.min || age > PROFILE_AGE_MONTHS.max)
    ? `Tuổi tính theo tháng phải từ ${PROFILE_AGE_MONTHS.min} đến ${PROFILE_AGE_MONTHS.max}.`
    : undefined;
  const createSignature = JSON.stringify(["create", classId, profileName, age, classRevision]);
  const createProfile = () => {
    if (!writable || inputProblem || classRevision === undefined) return;
    void runCommand(createSignature, async (key) => {
      const created = await teacherRosterApi.createProfile(organizationId, classId, classRevision, profileInput, key);
      setProfileName(SYNTHETIC_NAME_PREFIX);
      return `Đã tạo hồ sơ thử nghiệm “${created.display_name}”. Roster chỉ hiện hồ sơ khi consent hiệu lực; hồ sơ thử nghiệm chưa có consent nên có thể chưa hiện ở danh sách bên trên.`;
    });
  };

  const moveTarget = moveTargets.find((item) => item.class_id === moveDraft?.targetClassId);
  const moveSignature = moveDraft && moveTarget
    ? JSON.stringify(["move", classId, moveDraft.childId, moveTarget.class_id, classRevision, moveTarget.class_revision])
    : "";
  const moveProfile = () => {
    if (!writable || !moveDraft || !moveTarget || moveTarget.class_revision === undefined || classRevision === undefined) return;
    const target = { classId: moveTarget.class_id, revision: moveTarget.class_revision };
    void runCommand(moveSignature, async (key) => {
      await teacherRosterApi.moveProfile(classId, classRevision, moveDraft.childId, target, key);
      return `Đã chuyển hồ sơ sang lớp “${moveTarget.display_name}”; enrollment trước đó được đóng và lưu lại.`;
    });
  };

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading eyebrow="Teacher · Roster được cấp quyền" title={classItem?.display_name ?? "Chi tiết lớp"} description="Chỉ dữ liệu API trả về trong assignment hiện hành được hiển thị." action={<button type="button" className="s2l-button" disabled={loading || busy} onClick={() => setReload((value) => value + 1)}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>} />
      <button type="button" className="s2l-secondary-link" onClick={() => navigate("/teacher/t05-classes-and-children")}><ArrowLeft size={16} aria-hidden="true" />Danh sách lớp</button>
      {loading && <p className="s2l-data-card" role="status">Đang xác minh phạm vi và consent…</p>}
      {error && <div className="s2l-alert" role="alert">{error}</div>}
      {classItem && !error && classItem.state !== "active" && <div className="s2l-note" role="status"><LockKeyhole size={15} aria-hidden="true" />{CLASS_READ_ONLY}</div>}
      {notice && <p className="s2l-note" role="status">{notice}</p>}
      {classItem && !error && profileError && (profileErrorCode === "CONSENT_NOT_EFFECTIVE"
        ? <Alert role="status" tone="info" icon={<LockKeyhole size={16} aria-hidden="true" />} className="teacher-consent-locked">
            <strong>Danh sách hồ sơ tạm khóa đến khi có consent hiệu lực</strong>
            <p>Consent chưa được xác minh nên dữ liệu trẻ đang bị khóa.</p>
            {profileErrorRequestId && <small>Mã yêu cầu: {profileErrorRequestId}</small>}
          </Alert>
        : <div className="s2l-alert" role="alert">Hồ sơ chưa thể hiển thị: {profileError}</div>)}
      {classItem && !error && consentError && <div className="s2l-alert" role="alert">Consent chưa thể xác minh; roster được ẩn cho đến khi tải được trạng thái consent.</div>}
      {classItem && !loading && !error && (
        <section className="s2l-data-card" aria-labelledby="teacher-roster-title">
          <div className="s2l-section-heading"><div><h2 id="teacher-roster-title">Hồ sơ có consent hiệu lực</h2><p>Thông tin nhận diện chỉ dùng trong lớp thuộc assignment hiện hành.</p></div><span className="s2l-status-tag is-available">{visibleProfiles.length} hồ sơ</span></div>
          {consentError ? null : visibleProfiles.length === 0 ? <p className="s2l-note">API không trả hồ sơ có consent hiệu lực cho lớp này.</p> : (
            <ul className="s2l-roster-list">
              {visibleProfiles.map((profile) => {
                const childConsents = consents.filter((consent) => consent.child_id === profile.child_id && consent.effective);
                const moving = moveDraft?.childId === profile.child_id;
                return (
                  <li key={profile.child_id}>
                    <span className="s2l-roster-avatar" aria-hidden="true">{profile.display_name.trim().slice(0, 1) || "•"}</span>
                    <span className="s2l-class-copy"><strong>{profile.display_name}</strong><small>{profile.age_months} tháng · {childConsents.map((consent) => consent.purpose_ref).join(", ")}</small></span>
                    <span className="s2l-status-tag is-available">Consent hiệu lực</span>
                    {writable && moveTargets.length > 0 && !moving && (
                      <button type="button" className="s2l-button" disabled={busy} onClick={() => { setMoveDraft({ childId: profile.child_id, targetClassId: "" }); setCommandError(null); }}>Chuyển lớp</button>
                    )}
                    {moving && (
                      <div className="teacher-roster-move" role="group" aria-label={`Chuyển lớp cho ${profile.display_name}`}>
                        <FormField label="Lớp đích" htmlFor={`move-target-${profile.child_id}`} required>
                          <Select id={`move-target-${profile.child_id}`} aria-label="Lớp đích" value={moveDraft.targetClassId} disabled={busy} onChange={(event) => setMoveDraft({ childId: profile.child_id, targetClassId: event.target.value })}>
                            <option value="" disabled>Chọn lớp</option>
                            {moveTargets.map((item) => <option key={item.class_id} value={item.class_id}>{item.display_name}</option>)}
                          </Select>
                        </FormField>
                        <p className="cozy-form-hint" style={{ marginTop: 0 }}>Khi chuyển lớp, enrollment trước đó được đóng và lưu lại.</p>
                        {commandError && <Alert role="alert" tone="danger">{commandError}</Alert>}
                        {!busy && !moveTarget && (
                          <p className="cozy-form-disabled-hint">Chọn lớp đích để bật nút xác nhận chuyển lớp.</p>
                        )}
                        <div className="cozy-form-actions teacher-roster-move-actions" style={{ marginTop: 0 }}>
                          <Button type="button" variant="secondary" disabled={busy} onClick={() => setMoveDraft(null)}>Hủy</Button>
                          <Button type="button" variant="primary" loading={busy} disabled={busy || !moveTarget} onClick={moveProfile}>
                            {retrySignature !== null && retrySignature === moveSignature ? "Gửi lại cùng yêu cầu" : "Xác nhận chuyển lớp"}
                          </Button>
                        </div>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      )}
      {classItem && !consentError && !error && <section className="s2l-data-card">
        <h2>Trạng thái consent từ API</h2>
        {consents.length === 0 ? <p>API không trả consent record cho lớp này.</p> : <ul className="s2l-consent-list">{consents.map((consent) => <li key={consent.consent_id}><span>{consent.purpose_ref}</span><span className={"s2l-status-tag" + (consent.effective ? " is-available" : "")}>{consent.effective ? "Hiệu lực" : consent.state + " · chưa hiệu lực"}</span></li>)}</ul>}
      </section>}
      {classItem && !loading && !error && writable && (
        <section className="s2l-data-card cozy-form-card cozy-form-card--wide teacher-roster-create" aria-labelledby="teacher-profile-create-title">
          <h2 id="teacher-profile-create-title"><UserPlus size={17} aria-hidden="true" />Tạo hồ sơ thử nghiệm</h2>
          <p className="cozy-form-hint" style={{ marginTop: 0 }}>Chỉ tạo hồ sơ synthetic để thử nghiệm: chưa nhận dữ liệu trẻ thật và không giả consent. Tên phải bắt đầu bằng “{SYNTHETIC_NAME_PREFIX}”.</p>
          <form className="cozy-form-stack" onSubmit={(event) => { event.preventDefault(); createProfile(); }}>
            <div className="cozy-form-grid">
              <FormField className="cozy-span-4" label="Tên hiển thị" htmlFor="teacher-profile-name" required error={nameProblem}>
                <input id="teacher-profile-name" className="cozy-input" value={profileName} maxLength={PROFILE_NAME_MAX} required disabled={busy} onChange={(event) => setProfileName(event.target.value)} />
              </FormField>
              <FormField className="cozy-span-2" label="Tuổi (tháng)" htmlFor="teacher-profile-age" required error={ageProblem}>
                <input id="teacher-profile-age" className="cozy-input" type="number" min={PROFILE_AGE_MONTHS.min} max={PROFILE_AGE_MONTHS.max} step={1} value={ageMonths} required disabled={busy} onChange={(event) => setAgeMonths(event.target.value)} />
              </FormField>
            </div>
            {commandError && !moveDraft && <Alert role="alert" tone="danger">{commandError}</Alert>}
            {!busy && inputProblem && (
              <p className="cozy-form-disabled-hint">Nhập tên hợp lệ và tuổi từ {PROFILE_AGE_MONTHS.min}–{PROFILE_AGE_MONTHS.max} tháng để bật nút tạo hồ sơ.</p>
            )}
            <div className="cozy-form-actions" style={{ marginTop: 0 }}>
              <Button type="submit" variant="primary" loading={busy} disabled={busy || Boolean(inputProblem)}>
                {busy ? "Đang gửi…" : retrySignature !== null && retrySignature === createSignature ? "Gửi lại cùng yêu cầu" : "Tạo hồ sơ"}
              </Button>
            </div>
          </form>
        </section>
      )}
      <div className="s2l-note"><LockKeyhole size={15} aria-hidden="true" />Không cấp consent hoặc sửa hồ sơ tại đây; tạo hồ sơ và chuyển lớp chỉ dùng khi lớp đang hoạt động.</div>
    </div>
  );
}

export function T05ClassDetailPage({ classId }: { classId: string }) {
  return <TeacherApiClassDetailPage classId={classId} />;
}
