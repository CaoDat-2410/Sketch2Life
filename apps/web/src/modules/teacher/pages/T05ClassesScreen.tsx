import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, LockKeyhole, RefreshCw, Users } from "lucide-react";
import { PageHeading } from "../../../shared/FeatureAvailability";
import {
  BackendApiError,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
  type Be1Class,
} from "../../../shared/backendApi";

type Profile = { child_id: string; display_name: string; age_months: number };
type Consent = { consent_id: string; child_id: string; purpose_ref: string; state: string; effective: boolean };

function NoBackendSession() {
  return <div className="s2l-note"><LockKeyhole size={15} aria-hidden="true" />Lớp và hồ sơ chỉ tải khi có phiên Firebase cùng assignment Teacher đang hiệu lực.</div>;
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
        const page = await backendApi.classes(organizationId);
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
          <span className="s2l-class-copy"><strong>{item.display_name}</strong><small>Trạng thái lớp · {item.state}</small></span>
          <span className="s2l-class-open">Xem roster <ArrowRight size={15} aria-hidden="true" /></span>
        </button>
      ))}
      <div className="s2l-note"><LockKeyhole size={15} aria-hidden="true" />Hồ sơ trẻ chỉ hiển thị khi API xác minh assignment và consent hiệu lực.</div>
    </div>
  );
}

function TeacherApiClassDetailPage({ classId }: { classId: string }) {
  const navigate = useNavigate();
  const [classItem, setClassItem] = useState<Be1Class | null>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [consents, setConsents] = useState<Consent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    const organizationId = configuredOrganizationId();
    if (!hasFirebaseAuthBridge() || !organizationId) {
      setError(!hasFirebaseAuthBridge() ? "Chưa có Firebase ID token." : "Chưa cấu hình organization_id.");
      setLoading(false);
      return () => { active = false; };
    }

    setLoading(true);
    setError(null);
    setProfileError(null);
    setConsentError(null);
    setProfiles([]);
    setConsents([]);
    backendApi.assignments(organizationId)
      .then(async (identity) => {
        const mayOpenClass = identity.assignments.some((assignment) =>
          assignment.role === "teacher" && assignment.active !== false && assignment.class_id === classId,
        );
        if (!mayOpenClass) throw new BackendApiError("Lớp này không nằm trong assignment Teacher hiện hành.", "CLASS_SCOPE_FORBIDDEN", 403);
        const classPage = await backendApi.classes(organizationId);
        const actualClass = classPage.items.find((item) => item.class_id === classId);
        if (!actualClass) throw new BackendApiError("Lớp không nằm trong phạm vi assignment hiện tại.", "CLASS_SCOPE_FORBIDDEN", 403);
        if (active) setClassItem(actualClass);

        const [profileResult, consentResult] = await Promise.allSettled([
          backendApi.profiles(organizationId, classId),
          backendApi.consents(organizationId, classId),
        ]);
        if (!active) return;
        if (consentResult.status === "fulfilled") setConsents(consentResult.value.items);
        else setConsentError(backendMessage(consentResult.reason));
        if (profileResult.status === "fulfilled") setProfiles(profileResult.value.items);
        else setProfileError(backendMessage(profileResult.reason));
      })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [classId, reload]);

  const visibleProfiles = profiles.filter((profile) =>
    consents.some((consent) => consent.child_id === profile.child_id && consent.effective),
  );

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading eyebrow="Teacher · Roster được cấp quyền" title={classItem?.display_name ?? "Chi tiết lớp"} description="Chỉ dữ liệu API trả về trong assignment hiện hành được hiển thị." action={<button type="button" className="s2l-button" disabled={loading} onClick={() => setReload((value) => value + 1)}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>} />
      <button type="button" className="s2l-secondary-link" onClick={() => navigate("/teacher/t05-classes-and-children")}><ArrowLeft size={16} aria-hidden="true" />Danh sách lớp</button>
      {loading && <p className="s2l-data-card" role="status">Đang xác minh phạm vi và consent…</p>}
      {error && <div className="s2l-alert" role="alert">{error}</div>}
      {profileError && <div className="s2l-alert" role="alert">Hồ sơ chưa thể hiển thị: {profileError}</div>}
      {consentError && <div className="s2l-alert" role="alert">Consent chưa thể xác minh; roster được ẩn cho đến khi tải được trạng thái consent.</div>}
      {classItem && !loading && !error && (
        <section className="s2l-data-card" aria-labelledby="teacher-roster-title">
          <div className="s2l-section-heading"><div><h2 id="teacher-roster-title">Hồ sơ có consent hiệu lực</h2><p>Thông tin nhận diện chỉ dùng trong lớp thuộc assignment hiện hành.</p></div><span className="s2l-status-tag is-available">{visibleProfiles.length} hồ sơ</span></div>
          {consentError ? null : visibleProfiles.length === 0 ? <p className="s2l-note">API không trả hồ sơ có consent hiệu lực cho lớp này.</p> : (
            <ul className="s2l-roster-list">
              {visibleProfiles.map((profile) => {
                const childConsents = consents.filter((consent) => consent.child_id === profile.child_id && consent.effective);
                return <li key={profile.child_id}><span className="s2l-roster-avatar" aria-hidden="true">{profile.display_name.trim().slice(0, 1) || "•"}</span><span className="s2l-class-copy"><strong>{profile.display_name}</strong><small>{profile.age_months} tháng · {childConsents.map((consent) => consent.purpose_ref).join(", ")}</small></span><span className="s2l-status-tag is-available">Consent hiệu lực</span></li>;
              })}
            </ul>
          )}
        </section>
      )}
      {classItem && !consentError && <section className="s2l-data-card">
        <h2>Trạng thái consent từ API</h2>
        {consents.length === 0 ? <p>API không trả consent record cho lớp này.</p> : <ul className="s2l-consent-list">{consents.map((consent) => <li key={consent.consent_id}><span>{consent.purpose_ref}</span><span className={"s2l-status-tag" + (consent.effective ? " is-available" : "")}>{consent.effective ? "Hiệu lực" : consent.state + " · chưa hiệu lực"}</span></li>)}</ul>}
      </section>}
      <div className="s2l-note"><LockKeyhole size={15} aria-hidden="true" />Màn hình chỉ đọc; không cấp consent, sửa hồ sơ hoặc thực hiện chuyển lớp.</div>
    </div>
  );
}

export function T05ClassDetailPage({ classId }: { classId: string }) {
  return <TeacherApiClassDetailPage classId={classId} />;
}
