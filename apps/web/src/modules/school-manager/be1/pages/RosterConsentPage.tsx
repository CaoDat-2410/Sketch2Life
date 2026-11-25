import { useEffect, useRef, useState } from "react";
import { RefreshCw, Users } from "lucide-react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { Alert, EmptyState, FormField, Select, StatCard, StatusBadge, type StatusTone } from "../../../../shared/ui";
import { classService, classStateLabel, type Be1Class } from "../services/classService";
import { AdminBe1Error } from "../services/be1Client";
import { TeacherAssignmentCard } from "./TeacherAssignmentCard";
import "../styles/manager-business.css";
import {
  managerBusinessService,
  type Be1ManagerConsentStatus,
} from "../services/managerBusinessService";

type LoadState = "idle" | "loading" | "loaded" | "error";

function errorMessage(cause: unknown, fallback: string) {
  return cause instanceof Error ? cause.message : fallback;
}

function rosterErrorMessage(cause: unknown, fallback: string) {
  if (cause instanceof AdminBe1Error && cause.status === 403 && cause.code === "ACTION_NOT_ALLOWED") {
    return "Bạn không có quyền xem hồ sơ trẻ trong lớp này.";
  }
  return errorMessage(cause, fallback);
}

function consentStateLabel(state: string) {
  if (state === "pending") return "Đang chờ xác nhận";
  if (state === "revoked") return "Đã thu hồi";
  return "Trạng thái không xác định";
}

function consentStateTone(state: string): StatusTone {
  if (state === "pending") return "warn";
  if (state === "revoked") return "danger";
  return "neutral";
}

export function RosterConsentPage() {
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [classState, setClassState] = useState<LoadState>("loading");
  const [classError, setClassError] = useState("");
  const [selectedClassId, setSelectedClassId] = useState("");
  const [reloadCount, setReloadCount] = useState(0);
  const selectedClassIdRef = useRef("");
  // T-7a (SRS l.2586): the Manager sees how many active profiles a class has, never who they are.
  const [profileCount, setProfileCount] = useState<number | null>(null);
  const [profileState, setProfileState] = useState<LoadState>("idle");
  const [profileError, setProfileError] = useState("");
  const [consents, setConsents] = useState<Be1ManagerConsentStatus[]>([]);
  const [consentState, setConsentState] = useState<LoadState>("idle");
  const [consentError, setConsentError] = useState("");
  const [pendingRevoke, setPendingRevoke] = useState<{ classId: string; consentId: string; rowNumber: number } | null>(null);
  const [revokingConsentId, setRevokingConsentId] = useState<string | null>(null);
  const revocationLockRef = useRef(false);
  const [consentActionError, setConsentActionError] = useState("");
  const [consentActionMessage, setConsentActionMessage] = useState("");

  useEffect(() => {
    let current = true;
    // T-7b: every state, so a suspended or archived class stays visible to its School Manager.
    classService.listClasses("all")
      .then((items) => {
        if (!current) return;
        setClasses(items);
        const selected = selectedClassIdRef.current;
        const nextSelected = items.some((item) => item.class_id === selected)
          ? selected
          : items[0]?.class_id ?? "";
        selectedClassIdRef.current = nextSelected;
        setSelectedClassId(nextSelected);
        setProfileCount(null);
        setConsents([]);
        setProfileError("");
        setConsentError("");
        setPendingRevoke(null);
        setConsentActionError("");
        setConsentActionMessage("");
        setProfileState(nextSelected ? "loading" : "idle");
        setConsentState(nextSelected ? "loading" : "idle");
        setClassError("");
        setClassState("loaded");
      })
      .catch((cause: unknown) => {
        if (!current) return;
        setClasses([]);
        selectedClassIdRef.current = "";
        setSelectedClassId("");
        setClassError(errorMessage(cause, "Không tải được danh sách lớp từ BE1."));
        setProfileState("idle");
        setConsentState("idle");
        setClassState("error");
      });
    return () => { current = false; };
  }, [reloadCount]);

  useEffect(() => {
    if (!selectedClassId) return;

    const controller = new AbortController();

    managerBusinessService.rosterSummary(selectedClassId, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setProfileCount(result.active_profile_count);
          setProfileState("loaded");
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setProfileCount(null);
          setProfileError(rosterErrorMessage(cause, "Không tải được roster từ BE1."));
          setProfileState("error");
        }
      });

    managerBusinessService.consents(selectedClassId, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setConsents(result);
          setConsentState("loaded");
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setConsents([]);
          setConsentError(errorMessage(cause, "Không tải được trạng thái consent từ BE1."));
          setConsentState("error");
        }
      });

    return () => controller.abort();
  }, [reloadCount, selectedClassId]);

  const selectedClass = classes.find((item) => item.class_id === selectedClassId);
  const pendingConsentCount = consents.filter((item) => item.state === "pending").length;
  const revokedConsentCount = consents.filter((item) => item.state === "revoked").length;
  const changeSelectedClass = (classId: string) => {
    selectedClassIdRef.current = classId;
    setSelectedClassId(classId);
    setPendingRevoke(null);
    setConsentActionError("");
    setConsentActionMessage("");
    setProfileCount(null);
    setConsents([]);
    setProfileError("");
    setConsentError("");
    setProfileState(classId ? "loading" : "idle");
    setConsentState(classId ? "loading" : "idle");
  };

  const reloadConsents = async (classId: string) => {
    const next = await managerBusinessService.consents(classId);
    if (selectedClassIdRef.current === classId) {
      setConsents(next);
      setConsentState("loaded");
      setConsentError("");
    }
  };

  const confirmRevoke = async () => {
    if (!pendingRevoke || revocationLockRef.current) return;
    const { classId, consentId } = pendingRevoke;
    revocationLockRef.current = true;
    setRevokingConsentId(consentId);
    setConsentActionError("");
    setConsentActionMessage("");
    try {
      await managerBusinessService.revokeConsent(classId, consentId);
      setConsentActionMessage("Đã thu hồi bản ghi.");
      try {
        await reloadConsents(classId);
      } catch {
        if (selectedClassIdRef.current === classId) {
          setConsentState("error");
          setConsentError("Đã thu hồi bản ghi nhưng không tải lại được danh sách.");
        }
      }
    } catch (cause) {
      const status = cause instanceof AdminBe1Error ? cause.status : 0;
      setConsentActionError(status === 404 ? "Không tìm thấy bản ghi"
        : status === 403 ? "Không có quyền"
        : status === 0 ? "Chưa rõ kết quả, hãy tải lại"
        : "Không thể thu hồi bản ghi. Hãy tải lại danh sách.");
      if (status === 404) {
        try { await reloadConsents(classId); } catch { /* Keep the safe not-found message visible. */ }
      }
    } finally {
      revocationLockRef.current = false;
      setRevokingConsentId(null);
      setPendingRevoke(null);
    }
  };

  return (
    <div className="s2l-page manager-business-page">
      <PageHeading
        eyebrow="School Manager · BE1"
        title="Roster & consent"
        description="Chỉ hiển thị trường tối thiểu backend trả về; màn này không đọc ảnh, media hoặc story."
        action={
          <button
            type="button"
            className="manager-business-button"
            onClick={() => {
              setClassError("");
              setClassState("loading");
              setProfileCount(null);
              setConsents([]);
              setProfileError("");
              setConsentError("");
              setProfileState(selectedClassId ? "loading" : "idle");
              setConsentState(selectedClassId ? "loading" : "idle");
              setReloadCount((value) => value + 1);
            }}
            disabled={classState === "loading"}
          >
            <RefreshCw size={16} aria-hidden="true" />
            Làm mới
          </button>
        }
      />

      {classError && <Alert role="alert" tone="danger">{classError}</Alert>}

      <section className="manager-business-card cozy-form-card cozy-form-card--wide cozy-form-stack">
        {classState === "loading" ? (
          <Alert role="status">Đang tải lớp được cấp quyền…</Alert>
        ) : classState === "error" ? (
          <Alert role="status" tone="warning">Không thể chọn lớp khi danh sách BE1 chưa tải được.</Alert>
        ) : classes.length === 0 ? (
          <EmptyState title="Organization chưa có lớp được cấp quyền. Roster và consent chỉ tải sau khi chọn một lớp." />
        ) : (
          <div className="cozy-form-grid">
            <FormField
              className="cozy-span-3"
              label="Lớp đang xem"
              htmlFor="manager-roster-class"
            >
              <Select
                id="manager-roster-class"
                value={selectedClassId}
                onChange={(event) => changeSelectedClass(event.target.value)}
              >
                {classes.map((item) => (
                  <option value={item.class_id} key={item.class_id}>{item.display_name}</option>
                ))}
              </Select>
            </FormField>
            {selectedClass && (
              <div className="cozy-span-3 cozy-form-field" style={{ alignSelf: "end" }}>
                <p className="s2l-note" style={{ margin: 0 }}>
                  Trạng thái lớp từ BE1: {classStateLabel(selectedClass.state)}
                  {selectedClass.state === "suspended" ? " · Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ." : ""}
                  {selectedClass.state === "archived" ? " · Lớp đã lưu trữ; chỉ School Manager còn xem được." : ""}
                </p>
              </div>
            )}
          </div>
        )}
      </section>

      {selectedClassId && <>
        <section className="manager-business-stats manager-business-roster-stats" aria-label="Thống kê hồ sơ và consent">
          <StatCard label="Hồ sơ đang hoạt động" value={profileCount ?? "—"} accent="primary" loading={profileState === "loading"} />
          <StatCard label="Đang chờ xác nhận" value={consentState === "loaded" ? pendingConsentCount : "—"} accent="butter" loading={consentState === "loading"} />
          <StatCard label="Đã thu hồi" value={consentState === "loaded" ? revokedConsentCount : "—"} accent="coral" loading={consentState === "loading"} />
        </section>

        <section className="manager-business-grid manager-business-grid-two" aria-label="Dữ liệu lớp">
          <article className="manager-business-card">
            <div className="manager-business-card-heading">
              <div>
                <p className="manager-business-eyebrow">GET · BE1</p>
                <h2><Users size={18} aria-hidden="true" /> Tóm tắt roster</h2>
              </div>
            </div>
            {profileState === "loading" ? (
              <Alert role="status">Đang kiểm tra quyền và tải tóm tắt roster…</Alert>
            ) : profileState === "error" ? (
              <Alert role="alert" tone="danger">{profileError}</Alert>
            ) : profileState === "loaded" && profileCount !== null ? (
              <p className="manager-business-roster-count">
                <strong>{profileCount}</strong> hồ sơ đang hoạt động trong lớp
              </p>
            ) : (
              <p className="manager-business-state">Chọn lớp để đọc tóm tắt roster.</p>
            )}
            <p className="manager-business-subtle">School Manager chỉ xem số hồ sơ; không hiển thị tên, tuổi, mã hồ sơ, ảnh, media hoặc nội dung story.</p>
          </article>

          <article className="manager-business-card">
            <div className="manager-business-card-heading">
              <div>
                <p className="manager-business-eyebrow">GET · BE1</p>
                <h2>Trạng thái consent</h2>
              </div>
              {consentState === "loaded" && <span className="manager-business-chip">{consents.length} bản ghi</span>}
            </div>
            {consentActionError && <Alert role="alert" tone="danger">{consentActionError}</Alert>}
            {consentActionMessage && <Alert role="status">{consentActionMessage}</Alert>}
            {consentState === "loading" ? (
              <Alert role="status">Đang tải trạng thái consent…</Alert>
            ) : consentState === "error" ? (
              <Alert role="alert" tone="danger">{consentError}</Alert>
            ) : consentState === "loaded" && consents.length === 0 ? (
              <EmptyState title="BE1 chưa trả bản ghi consent cho lớp này." />
            ) : consentState === "loaded" ? (
              <div className="manager-business-table-wrap">
                <table className="manager-business-table">
                  <thead>
                    <tr><th>Bản ghi</th><th>Trạng thái</th><th>Thao tác</th></tr>
                  </thead>
                  <tbody>
                    {consents.map((consent, index) => (
                      <tr key={consent.consent_id}>
                        <td>Bản ghi {index + 1}</td>
                        <td><StatusBadge tone={consentStateTone(consent.state)} size="sm">{consentStateLabel(consent.state)}</StatusBadge></td>
                        <td>{consent.state === "pending" && (
                          <button
                            type="button"
                            className="manager-business-button"
                            aria-label={`Thu hồi bản ghi ${index + 1}`}
                            disabled={revokingConsentId !== null}
                            onClick={() => {
                              setConsentActionError("");
                              setConsentActionMessage("");
                              setPendingRevoke({ classId: selectedClassId, consentId: consent.consent_id, rowNumber: index + 1 });
                            }}
                          >
                            Thu hồi
                          </button>
                        )}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="manager-business-state">Chọn lớp để đọc trạng thái consent.</p>
            )}
            <p className="manager-business-subtle">Danh sách không nêu trẻ hoặc mục đích. Thu hồi bản ghi đang chờ là vĩnh viễn và không thể hoàn tác.</p>
          </article>
        </section>
      </>}

      {pendingRevoke && (
        <div className="manager-business-confirm-backdrop">
          <section
            className="manager-business-card manager-business-confirm-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="manager-consent-revoke-title"
            aria-describedby="manager-consent-revoke-copy"
          >
            <h2 id="manager-consent-revoke-title">Thu hồi bản ghi {pendingRevoke.rowNumber}?</h2>
            <p id="manager-consent-revoke-copy">Ở màn này không thể xác định bản ghi thuộc trẻ nào. Thu hồi là vĩnh viễn và không thể hoàn tác.</p>
            {revokingConsentId && <p role="status">Đang thu hồi bản ghi…</p>}
            <div className="manager-business-confirm-actions">
              <button type="button" className="manager-business-button" disabled={revokingConsentId !== null} onClick={() => setPendingRevoke(null)}>Hủy</button>
              <button type="button" className="manager-business-button is-primary" disabled={revokingConsentId !== null} onClick={() => void confirmRevoke()}>
                {revokingConsentId ? "Đang thu hồi…" : "Xác nhận thu hồi"}
              </button>
            </div>
          </section>
        </div>
      )}

      <TeacherAssignmentCard
        key={selectedClass?.class_id ?? "none"}
        selectedClass={selectedClass}
        onAssigned={() => setReloadCount((value) => value + 1)}
      />
    </div>
  );
}
