import { ModalPortal } from "../../../../shared/ui/ModalPortal";
import { useEffect, useRef, useState } from "react";
import { RefreshCw, Users } from "lucide-react";
import { createIdempotencyKey } from "../../../../shared/api/backendApi";
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

interface ProfileMoveAttempt {
  classId: string;
  childId: string;
  targetClassId: string;
  sourceClassRevision: number;
  targetClassRevision: number;
  idempotencyKey: string;
  rowNumber: number;
}

function errorMessage(cause: unknown, fallback: string) {
  return cause instanceof Error ? cause.message : fallback;
}

function rosterErrorMessage(cause: unknown, fallback: string) {
  if (cause instanceof AdminBe1Error && cause.status === 403 && cause.code === "ACTION_NOT_ALLOWED") {
    return "Bạn không có quyền xem hồ sơ trẻ trong lớp này.";
  }
  return errorMessage(cause, fallback);
}

function profileRefsErrorMessage(cause: unknown) {
  if (cause instanceof AdminBe1Error) {
    if (cause.status === 403) return "Tài khoản không có quyền xem mã tham chiếu hồ sơ trong lớp này.";
    if (cause.status === 404) return "Không tìm thấy lớp hoặc tài khoản không có quyền truy cập.";
    if (cause.status === 0) return "Không kết nối được để tải mã tham chiếu hồ sơ.";
  }
  return "Không tải được mã tham chiếu hồ sơ.";
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
  const [unplaced, setUnplaced] = useState<string[]>([]);
  const [unplacedState, setUnplacedState] = useState<LoadState>("loading");
  const [placeTarget, setPlaceTarget] = useState("");
  const [placePrompt, setPlacePrompt] = useState<{ childId: string; rowNumber: number } | null>(null);
  const [placeAttempt, setPlaceAttempt] = useState<{ childId: string; classId: string; revision: number; key: string } | null>(null);
  const [placeBusy, setPlaceBusy] = useState(false);
  const [placeMessage, setPlaceMessage] = useState("");
  const placeLock = useRef(false);
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
  const [profileRefs, setProfileRefs] = useState<string[]>([]);
  const [profileRefsState, setProfileRefsState] = useState<LoadState>("idle");
  const [profileRefsError, setProfileRefsError] = useState("");
  const [targetClassId, setTargetClassId] = useState("");
  const [movePrompt, setMovePrompt] = useState<{ childId: string; rowNumber: number } | null>(null);
  const [moveAttempt, setMoveAttempt] = useState<ProfileMoveAttempt | null>(null);
  const [moveLoading, setMoveLoading] = useState(false);
  const [moveActionError, setMoveActionError] = useState("");
  const [moveActionMessage, setMoveActionMessage] = useState("");
  const moveLockRef = useRef(false);
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
        const selectionChanged = selected !== nextSelected;
        selectedClassIdRef.current = nextSelected;
        setSelectedClassId(nextSelected);
        setProfileCount(null);
        setProfileRefs([]);
        setProfileRefsState(nextSelected ? "loading" : "idle");
        setProfileRefsError("");
        setConsents([]);
        setProfileError("");
        setConsentError("");
        setPendingRevoke(null);
        setConsentActionError("");
        setConsentActionMessage("");
        if (selectionChanged) {
          setTargetClassId("");
          setMovePrompt(null);
          setMoveAttempt(null);
          setMoveActionError("");
          setMoveActionMessage("");
        }
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
        setProfileRefs([]);
        setProfileRefsState("idle");
        setProfileRefsError("");
        setClassError(errorMessage(cause, "Không tải được danh sách lớp."));
        setProfileState("idle");
        setConsentState("idle");
        setClassState("error");
      });
    return () => { current = false; };
  }, [reloadCount]);

  useEffect(() => {
    const controller = new AbortController();
    managerBusinessService.unplacedProfileRefs(controller.signal).then((items) => {
      if (!controller.signal.aborted) { setUnplaced(items.map((item) => item.child_id)); setUnplacedState("loaded"); }
    }).catch(() => {
      if (!controller.signal.aborted) { setUnplaced([]); setUnplacedState("error"); }
    });
    return () => controller.abort();
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
          setProfileError(rosterErrorMessage(cause, "Không tải được danh sách."));
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
          setConsentError(errorMessage(cause, "Không tải được trạng thái đồng ý."));
          setConsentState("error");
        }
      });

    managerBusinessService.profileRefs(selectedClassId, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setProfileRefs(result.map((item) => item.child_id));
          setProfileRefsState("loaded");
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setProfileRefs([]);
          setProfileRefsError(profileRefsErrorMessage(cause));
          setProfileRefsState("error");
        }
      });

    return () => controller.abort();
  }, [reloadCount, selectedClassId]);

  const selectedClass = classes.find((item) => item.class_id === selectedClassId);
  const targetClasses = classes.filter(
    (item) => item.class_id !== selectedClassId && item.state === "active",
  );
  const pendingConsentCount = consents.filter((item) => item.state === "pending").length;
  const revokedConsentCount = consents.filter((item) => item.state === "revoked").length;
  const changeSelectedClass = (classId: string) => {
    // Picking the class already shown must not reset to "loading": nothing would fetch again.
    if (classId === selectedClassId) return;
    selectedClassIdRef.current = classId;
    setSelectedClassId(classId);
    setPendingRevoke(null);
    setConsentActionError("");
    setConsentActionMessage("");
    setProfileCount(null);
    setProfileRefs([]);
    setProfileRefsState(classId ? "loading" : "idle");
    setProfileRefsError("");
    setTargetClassId("");
    setConsents([]);
    setProfileError("");
    setConsentError("");
    setProfileState(classId ? "loading" : "idle");
    setConsentState(classId ? "loading" : "idle");
    setMovePrompt(null);
    setMoveAttempt(null);
    setMoveActionError("");
    setMoveActionMessage("");
  };

  const beginMove = (childId: string, rowNumber: number) => {
    if (moveAttempt || movePrompt || classState !== "loaded" || !selectedClass || selectedClass.state !== "active") return;
    const target = targetClasses.find((item) => item.class_id === targetClassId);
    if (!target || !Number.isInteger(selectedClass.class_revision) || !Number.isInteger(target.class_revision)) {
      setMoveActionError("Chưa tải được phiên bản của hai lớp. Hãy làm mới danh sách lớp.");
      return;
    }
    setMoveActionError("");
    setMoveActionMessage("");
    setMovePrompt({ childId, rowNumber });
  };

  const confirmMove = async () => {
    if (!movePrompt || moveLockRef.current) return;
    if (!moveAttempt && classState !== "loaded") {
      setMoveActionError("Đang tải lại danh sách lớp. Hãy chờ tải xong rồi xác nhận chuyển.");
      return;
    }
    const source = selectedClass;
    const target = classes.find((item) => item.class_id === targetClassId);
    const attempt = moveAttempt ?? (
      source && target && source.state === "active" && target.state === "active"
        && Number.isInteger(source.class_revision) && Number.isInteger(target.class_revision)
        ? {
          classId: source.class_id,
          childId: movePrompt.childId,
          targetClassId: target.class_id,
          sourceClassRevision: source.class_revision as number,
          targetClassRevision: target.class_revision as number,
          idempotencyKey: createIdempotencyKey(),
          rowNumber: movePrompt.rowNumber,
        }
        : null
    );
    if (!attempt) {
      setMoveActionError("Chưa tải được phiên bản của hai lớp. Hãy làm mới danh sách lớp.");
      return;
    }

    moveLockRef.current = true;
    setMoveAttempt(attempt);
    setMoveLoading(true);
    setMoveActionError("");
    setMoveActionMessage("");
    try {
      await managerBusinessService.moveProfile(
        attempt.classId,
        attempt.childId,
        attempt.targetClassId,
        attempt.sourceClassRevision,
        attempt.targetClassRevision,
        attempt.idempotencyKey,
      );
      setMoveActionMessage(
        `Đã chuyển Hồ sơ ${attempt.rowNumber} sang ${target?.display_name ?? "lớp đã chọn"}. Đang làm mới sĩ số và mã tham chiếu.`,
      );
      setMovePrompt(null);
      setMoveAttempt(null);
      setTargetClassId("");
      setProfileState("loading");
      setProfileRefsState("loading");
      setConsentState("loading");
      setReloadCount((value) => value + 1);
    } catch (cause) {
      const status = cause instanceof AdminBe1Error ? cause.status : 0;
      const code = cause instanceof AdminBe1Error ? cause.code : "";
      if (code === "STALE_REVISION") {
        setMoveAttempt(null);
        setMovePrompt(null);
        setMoveActionMessage("Phiên bản lớp đã thay đổi. Đang tải lại; hãy kiểm tra danh sách rồi xác nhận chuyển lại.");
        setClassState("loading");
        setProfileState("loading");
        setProfileRefsState("loading");
        setReloadCount((value) => value + 1);
      } else if (status === 409) {
        // BE1 replaces server messages by code, so one copy covers every 409 cause.
        setMoveAttempt(null);
        setMovePrompt(null);
        setMoveActionError("Chưa chuyển được: hồ sơ đang trong buổi học chưa kết thúc, lớp không còn hoạt động hoặc hồ sơ không còn ở lớp nguồn. Danh sách đang được tải lại.");
        setClassState("loading");
        setProfileState("loading");
        setProfileRefsState("loading");
        setReloadCount((value) => value + 1);
      } else if (status === 403) {
        setMoveAttempt(null);
        setMovePrompt(null);
        setMoveActionError("Tài khoản không có quyền chuyển hồ sơ trong lớp này.");
      } else if (status === 404) {
        setMoveAttempt(null);
        setMovePrompt(null);
        setMoveActionError("Không tìm thấy lớp hoặc hồ sơ, hoặc tài khoản không có quyền truy cập. Danh sách đang được tải lại.");
        setClassState("loading");
        setProfileState("loading");
        setProfileRefsState("loading");
        setReloadCount((value) => value + 1);
      } else if (status === 0 || status >= 500 || (cause instanceof AdminBe1Error && cause.retryable)) {
        // Keep the exact attempt and key: the server may have committed before the response was lost.
        setMoveActionError("Chưa rõ kết quả. Hãy gửi lại cùng thao tác để kiểm tra; mã chống lặp được giữ nguyên.");
      } else {
        setMoveAttempt(null);
        setMovePrompt(null);
        setMoveActionError("Không thể chuyển hồ sơ với yêu cầu hiện tại. Hãy tải lại danh sách.");
      }
    } finally {
      moveLockRef.current = false;
      setMoveLoading(false);
    }
  };

  const confirmPlace = async () => {
    if (!placePrompt || placeLock.current) return;
    const target = classes.find((item) => item.class_id === placeTarget && item.state === "active");
    const attempt = placeAttempt ?? (target && Number.isInteger(target.class_revision) ? {
      childId: placePrompt.childId, classId: target.class_id, revision: target.class_revision as number, key: createIdempotencyKey(),
    } : null);
    if (!attempt) { setPlaceMessage("Hãy chọn lớp đang hoạt động và tải lại phiên bản lớp."); return; }
    placeLock.current = true;
    setPlaceAttempt(attempt); setPlaceBusy(true); setPlaceMessage("");
    try {
      await managerBusinessService.placeProfile(attempt.classId, attempt.childId, attempt.revision, attempt.key);
      setPlacePrompt(null); setPlaceAttempt(null); setPlaceTarget("");
      setPlaceMessage("Đã xếp hồ sơ. Danh sách và sĩ số đang được làm mới.");
      setUnplaced([]);
      setClassState("loading");
      setReloadCount((value) => value + 1);
    } catch (cause) {
      const status = cause instanceof AdminBe1Error ? cause.status : 0;
      const code = cause instanceof AdminBe1Error ? cause.code : "";
      if (status === 0 || status >= 500 || (cause instanceof AdminBe1Error && cause.retryable)) {
        setPlaceMessage("Chưa rõ kết quả. Hãy gửi lại cùng thao tác; mã chống lặp được giữ nguyên.");
      } else {
        setPlaceAttempt(null); setPlacePrompt(null);
        setPlaceMessage(code === "STALE_REVISION" ? "Phiên bản lớp đã thay đổi. Hãy kiểm tra và xác nhận lại." : status === 409 ? "Không thể xếp hồ sơ trong trạng thái hiện tại. Hãy kiểm tra lại danh sách." : status === 403 ? "Tài khoản không có quyền xếp hồ sơ." : status === 404 ? "Không tìm thấy lớp hoặc hồ sơ, hoặc tài khoản không có quyền truy cập." : "Không thể xếp hồ sơ. Hãy tải lại danh sách.");
        setUnplaced([]);
        setClassState("loading");
        setReloadCount((value) => value + 1);
      }
    } finally { placeLock.current = false; setPlaceBusy(false); }
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
      if (status !== 403 && status !== 0) {
        try { await reloadConsents(classId); } catch { /* Keep the safe not-found message visible. */ }
      }
    } finally {
      revocationLockRef.current = false;
      setRevokingConsentId(null);
      setPendingRevoke(null);
    }
  };

  return (
    <div className="s2l-page manager-business-page koi-manager-roster">
      <PageHeading
        eyebrow="Quản lý trường"
        title="Danh sách lớp & đồng ý"
        description="Hiển thị sĩ số, mã tham chiếu ẩn danh và trạng thái xác nhận tối thiểu theo lớp; không đọc nội dung hồ sơ."
        action={
          <button
            type="button"
            className="manager-business-button"
            onClick={() => {
              setClassError("");
              setClassState("loading");
              setProfileCount(null);
              setProfileRefsState(selectedClassId ? "loading" : "idle");
              setProfileRefsError("");
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

      <section className="manager-business-card cozy-form-card cozy-form-card--wide cozy-form-stack koi-roster-unplaced" aria-labelledby="unplaced-title">
        <h2 id="unplaced-title">Hồ sơ chưa được xếp lớp</h2>
        <p className="manager-business-subtle">Những hồ sơ này được giữ để xem xét và không bao giờ được xếp lớp tự động. Sự đồng ý không được sao chép khi xếp lớp.</p>
        {unplacedState === "loading" && <Alert role="status">Đang tải mã tham chiếu…</Alert>}
        {unplacedState === "error" && <Alert role="alert" tone="danger">Không tải được mã tham chiếu hồ sơ chưa xếp lớp.</Alert>}
        {placeMessage && <Alert role="status">{placeMessage}</Alert>}
        {unplacedState === "loaded" && <p>Số hồ sơ cần xem xét: {unplaced.length}</p>}
        <FormField label="Lớp để xếp hồ sơ" htmlFor="unplaced-target">
          <Select id="unplaced-target" value={placeTarget} disabled={placePrompt !== null || placeBusy} onChange={(event) => setPlaceTarget(event.target.value)}>
            <option value="">Chọn lớp đang hoạt động</option>
            {classes.filter((item) => item.state === "active").map((item) => <option key={item.class_id} value={item.class_id}>{item.display_name}</option>)}
          </Select>
        </FormField>
        {unplaced.length > 0 && <div className="manager-business-table-wrap koi-unplaced-table"><table className="manager-business-table">
          <thead><tr><th>Hồ sơ</th><th>Mã tham chiếu</th><th>Thao tác</th></tr></thead>
          <tbody>{unplaced.map((childId, index) => <tr key={childId}>
            <td>Hồ sơ {index + 1}</td><td><code>{childId}</code></td>
            <td><button type="button" className="manager-business-button" aria-label={`Xếp lớp Hồ sơ ${index + 1}`} disabled={!placeTarget || placePrompt !== null || classState !== "loaded"} onClick={() => { setPlaceMessage(""); setPlacePrompt({ childId, rowNumber: index + 1 }); }}>Xếp lớp</button></td>
          </tr>)}</tbody>
        </table></div>}
        {placePrompt && <ModalPortal><div className="manager-business-confirm-backdrop"><div className="manager-business-card manager-business-confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="place-confirm-title">
          <h2 id="place-confirm-title">Xếp Hồ sơ {placePrompt.rowNumber}?</h2>
          <p>Xác nhận xếp một hồ sơ vào lớp đã chọn. Sự đồng ý không được sao chép.</p>
          <div className="manager-business-confirm-actions">
            {!placeAttempt && <button type="button" className="manager-business-button" disabled={placeBusy} onClick={() => setPlacePrompt(null)}>Hủy</button>}
            <button type="button" className="manager-business-button is-primary" disabled={placeBusy} onClick={() => void confirmPlace()}>{placeAttempt ? "Gửi lại" : "Xác nhận"}</button>
          </div>
        </div></div></ModalPortal>}
      </section>

      <section className="manager-business-card cozy-form-card cozy-form-card--wide cozy-form-stack koi-roster-class">
        {classState === "loading" ? (
          <Alert role="status">Đang tải lớp được cấp quyền…</Alert>
        ) : classState === "error" ? (
          <Alert role="status" tone="warning">Không thể chọn lớp khi chưa tải được danh sách lớp.</Alert>
        ) : classes.length === 0 ? (
          <EmptyState title="Trường chưa có lớp nào được cấp quyền. Sĩ số và xác nhận chỉ tải sau khi chọn một lớp." />
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
                disabled={moveAttempt !== null || movePrompt !== null}
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
                  Trạng thái lớp: {classStateLabel(selectedClass.state)}
                  {selectedClass.state === "suspended" ? " · Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ." : ""}
                  {selectedClass.state === "archived" ? " · Lớp đã lưu trữ; chỉ Quản lý trường còn xem được." : ""}
                </p>
              </div>
            )}
          </div>
        )}
        {selectedClassId && <div className="manager-business-stats manager-business-roster-stats" aria-label="Thống kê hồ sơ và đồng ý">
          <StatCard label="Hồ sơ đang hoạt động" value={profileCount ?? "—"} accent="primary" loading={profileState === "loading"} />
          <StatCard label="Đang chờ xác nhận" value={consentState === "loaded" ? pendingConsentCount : "—"} accent="butter" loading={consentState === "loading"} />
          <StatCard label="Đã thu hồi" value={consentState === "loaded" ? revokedConsentCount : "—"} accent="coral" loading={consentState === "loading"} />
        </div>}
      </section>

      {selectedClassId && <>

        <section className="manager-business-card cozy-form-card cozy-form-card--wide cozy-form-stack koi-roster-move" aria-label="Sắp xếp hồ sơ trong lớp">
          <div className="manager-business-card-heading">
            <div>
              <p className="manager-business-eyebrow">Xếp lớp</p>
              <h2>Chuyển hồ sơ giữa các lớp</h2>
            </div>
          </div>
          <p className="manager-business-subtle">
            Tên và tuổi bị ẩn khỏi Quản lý trường theo thiết kế. Danh sách này chỉ có mã tham chiếu ẩn danh; không hiển thị ảnh, video, mục đích đồng ý, nhu cầu hỗ trợ hoặc nguồn dữ liệu.
          </p>
          {selectedClass && selectedClass.state !== "active" && (
            <Alert role="status" tone="warning">Lớp nguồn đang tạm ngưng hoặc đã lưu trữ; không thể chuyển hồ sơ.</Alert>
          )}
          {moveActionError && <Alert role="alert" tone="danger">{moveActionError}</Alert>}
          {moveActionMessage && <Alert role="status">{moveActionMessage}</Alert>}
          <FormField label="Lớp đích" htmlFor="manager-profile-target-class">
            <Select
              id="manager-profile-target-class"
              value={targetClassId}
              disabled={classState !== "loaded" || movePrompt !== null || moveAttempt !== null || moveLoading || targetClasses.length === 0}
              onChange={(event) => {
                setTargetClassId(event.target.value);
                setMoveActionError("");
                setMoveActionMessage("");
              }}
            >
              <option value="">Chọn lớp đang hoạt động</option>
              {targetClasses.map((item) => (
                <option value={item.class_id} key={item.class_id}>{item.display_name}</option>
              ))}
            </Select>
          </FormField>
          {targetClasses.length === 0 && (
            <p className="manager-business-state">Không có lớp đang hoạt động khác để chuyển hồ sơ.</p>
          )}
          {profileRefsState === "loading" ? (
            <Alert role="status">Đang tải mã tham chiếu hồ sơ…</Alert>
          ) : profileRefsState === "error" ? (
            <Alert role="alert" tone="danger">{profileRefsError}</Alert>
          ) : profileRefsState === "loaded" && profileRefs.length === 0 ? (
            <EmptyState title="Chưa có mã hồ sơ nào để chuyển trong lớp này." />
          ) : profileRefsState === "loaded" ? (
            <div className="manager-business-table-wrap">
              <table className="manager-business-table">
                <thead><tr><th>Hồ sơ</th><th>Mã tham chiếu</th><th>Thao tác</th></tr></thead>
                <tbody>
                  {profileRefs.map((childId, index) => {
                    const rowNumber = index + 1;
                    const shortRef = childId.length > 16
                      ? `${childId.slice(0, 8)}…${childId.slice(-4)}`
                      : childId;
                    const canMove = classState === "loaded"
                      && selectedClass?.state === "active"
                      && Boolean(targetClassId)
                      && Number.isInteger(selectedClass.class_revision)
                      && Boolean(targetClasses.find((item) => item.class_id === targetClassId
                        && Number.isInteger(item.class_revision)))
                      && moveAttempt === null && !moveLoading;
                    return (
                      <tr key={childId}>
                        <td>Hồ sơ {rowNumber}</td>
                        <td>
                          <code>{shortRef}</code>
                          <details>
                            <summary>Xem mã tham chiếu đầy đủ</summary>
                            <code>{childId}</code>
                          </details>
                        </td>
                        <td>
                          <button
                            type="button"
                            className="manager-business-button"
                            aria-label={`Chuyển Hồ sơ ${rowNumber}`}
                            disabled={!canMove}
                            onClick={() => beginMove(childId, rowNumber)}
                          >
                            Chuyển hồ sơ
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="manager-business-state">Chọn lớp để đọc mã tham chiếu hồ sơ.</p>
          )}
        </section>

        <section className="manager-business-grid manager-business-grid-two" aria-label="Dữ liệu lớp">
          <article className="manager-business-card">
            <div className="manager-business-card-heading">
              <div>
                <p className="manager-business-eyebrow">Sĩ số lớp</p>
                <h2><Users size={18} aria-hidden="true" /> Tóm tắt danh sách</h2>
              </div>
            </div>
            {profileState === "loading" ? (
              <Alert role="status">Đang kiểm tra quyền và tải tóm tắt danh sách…</Alert>
            ) : profileState === "error" ? (
              <Alert role="alert" tone="danger">{profileError}</Alert>
            ) : profileState === "loaded" && profileCount !== null ? (
              <p className="manager-business-roster-count">
                <strong>{profileCount}</strong> hồ sơ đang hoạt động trong lớp
              </p>
            ) : (
              <p className="manager-business-state">Chọn lớp để đọc tóm tắt danh sách.</p>
            )}
            <p className="manager-business-subtle">Quản lý trường chỉ xem số hồ sơ; không hiển thị tên, tuổi, mã hồ sơ, ảnh, video hoặc nội dung câu chuyện.</p>
          </article>

          <article className="manager-business-card">
            <div className="manager-business-card-heading">
              <div>
                <p className="manager-business-eyebrow">Xác nhận phụ huynh</p>
                <h2>Trạng thái đồng ý</h2>
              </div>
              {consentState === "loaded" && <span className="manager-business-chip">{consents.length} bản ghi</span>}
            </div>
            {consentActionError && <Alert role="alert" tone="danger">{consentActionError}</Alert>}
            {consentActionMessage && <Alert role="status">{consentActionMessage}</Alert>}
            {consentState === "loading" ? (
              <Alert role="status">Đang tải trạng thái đồng ý…</Alert>
            ) : consentState === "error" ? (
              <Alert role="alert" tone="danger">{consentError}</Alert>
            ) : consentState === "loaded" && consents.length === 0 ? (
              <EmptyState title="Chưa có bản ghi đồng ý cho lớp này." />
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
              <p className="manager-business-state">Chọn lớp để đọc trạng thái đồng ý.</p>
            )}
            <p className="manager-business-subtle">Danh sách không nêu trẻ hoặc mục đích. Thu hồi bản ghi đang chờ là vĩnh viễn và không thể hoàn tác.</p>
          </article>
        </section>
      </>}

      {pendingRevoke && (
        <ModalPortal><div className="manager-business-confirm-backdrop">
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
        </div></ModalPortal>
      )}

      {movePrompt && (
        <ModalPortal><div className="manager-business-confirm-backdrop">
          <section
            className="manager-business-card manager-business-confirm-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="manager-profile-move-title"
            aria-describedby="manager-profile-move-copy"
          >
            <h2 id="manager-profile-move-title">Chuyển Hồ sơ {movePrompt.rowNumber}?</h2>
            <p id="manager-profile-move-copy">
              Chuyển từ {selectedClass?.display_name ?? "lớp đang xem"} sang {classes.find((item) => item.class_id === (moveAttempt?.targetClassId ?? targetClassId))?.display_name ?? "lớp đã chọn"}. Hệ thống sẽ giữ lại lượt xếp lớp cũ.
            </p>
            {moveAttempt && (
              <Alert role="status" tone="warning">
                Phản hồi trước chưa rõ kết quả. Hãy gửi lại đúng thao tác này để kiểm tra; mã chống lặp sẽ được giữ nguyên.
              </Alert>
            )}
            {moveLoading && <p role="status">Đang chuyển hồ sơ…</p>}
            <div className="manager-business-confirm-actions">
              <button
                type="button"
                className="manager-business-button"
                disabled={moveLoading || moveAttempt !== null}
                onClick={() => setMovePrompt(null)}
              >
                Hủy
              </button>
              <button
                type="button"
                className="manager-business-button is-primary"
                disabled={moveLoading}
                onClick={() => void confirmMove()}
              >
                {moveLoading ? "Đang chuyển…" : moveAttempt ? "Gửi lại cùng thao tác" : "Xác nhận chuyển"}
              </button>
            </div>
          </section>
        </div></ModalPortal>
      )}

      <TeacherAssignmentCard
        key={selectedClass?.class_id ?? "none"}
        selectedClass={selectedClass}
        onAssigned={() => setReloadCount((value) => value + 1)}
      />
    </div>
  );
}
