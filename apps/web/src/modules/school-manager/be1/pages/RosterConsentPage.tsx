import { useEffect, useRef, useState } from "react";
import { RefreshCw, Users } from "lucide-react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { classService, classStateLabel, type Be1Class } from "../services/classService";
import { AdminBe1Error } from "../services/be1Client";
import { TeacherAssignmentCard } from "./TeacherAssignmentCard";
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
  // The backend stores lower-case states; compare case-insensitively.
  const key = state.toUpperCase();
  if (key === "ACTIVE" || key === "EFFECTIVE") return "Đã ghi nhận";
  if (key === "PENDING") return "Đang chờ xác nhận";
  if (key === "REVOKED") return "Đã thu hồi";
  return state;
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
  const changeSelectedClass = (classId: string) => {
    selectedClassIdRef.current = classId;
    setSelectedClassId(classId);
    setProfileCount(null);
    setConsents([]);
    setProfileError("");
    setConsentError("");
    setProfileState(classId ? "loading" : "idle");
    setConsentState(classId ? "loading" : "idle");
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

      {classError && <p className="manager-business-alert" role="alert">{classError}</p>}

      <section className="manager-business-card manager-business-class-picker">
        <label htmlFor="manager-roster-class">Lớp đang xem</label>
        {classState === "loading" ? (
          <p className="manager-business-state" role="status">Đang tải lớp được cấp quyền…</p>
        ) : classState === "error" ? (
          <p className="manager-business-state" role="status">Không thể chọn lớp khi danh sách BE1 chưa tải được.</p>
        ) : classes.length === 0 ? (
          <p className="manager-business-state" role="status">
            Organization chưa có lớp được cấp quyền. Roster và consent chỉ tải sau khi chọn một lớp.
          </p>
        ) : (
          <select
            id="manager-roster-class"
            value={selectedClassId}
            onChange={(event) => changeSelectedClass(event.target.value)}
          >
            {classes.map((item) => (
              <option value={item.class_id} key={item.class_id}>{item.display_name}</option>
            ))}
          </select>
        )}
        {selectedClass && (
          <p className="manager-business-subtle">
            Trạng thái lớp từ BE1: {classStateLabel(selectedClass.state)}
            {selectedClass.state === "suspended" ? " · Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ." : ""}
            {selectedClass.state === "archived" ? " · Lớp đã lưu trữ; chỉ School Manager còn xem được." : ""}
          </p>
        )}
      </section>

      {selectedClassId && (
        <section className="manager-business-grid manager-business-grid-two" aria-label="Dữ liệu lớp">
          <article className="manager-business-card">
            <div className="manager-business-card-heading">
              <div>
                <p className="manager-business-eyebrow">GET · BE1</p>
                <h2><Users size={18} aria-hidden="true" /> Tóm tắt roster</h2>
              </div>
            </div>
            {profileState === "loading" ? (
              <p className="manager-business-state" role="status">Đang kiểm tra quyền và tải tóm tắt roster…</p>
            ) : profileState === "error" ? (
              <p className="manager-business-alert" role="alert">{profileError}</p>
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
            {consentState === "loading" ? (
              <p className="manager-business-state" role="status">Đang tải trạng thái consent…</p>
            ) : consentState === "error" ? (
              <p className="manager-business-alert" role="alert">{consentError}</p>
            ) : consentState === "loaded" && consents.length === 0 ? (
              <p className="manager-business-state">BE1 chưa trả bản ghi consent cho lớp này.</p>
            ) : consentState === "loaded" ? (
              <div className="manager-business-table-wrap">
                <table className="manager-business-table">
                  <thead>
                    <tr><th>Bản ghi</th><th>Trạng thái</th><th>Hiệu lực</th></tr>
                  </thead>
                  <tbody>
                    {consents.map((consent, index) => (
                      <tr key={consent.consent_id}>
                        <td>Bản ghi {index + 1}</td>
                        <td>{consentStateLabel(consent.state)}</td>
                        <td>{consent.effective ? "Có" : "Không"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="manager-business-state">Chọn lớp để đọc trạng thái consent.</p>
            )}
            <p className="manager-business-subtle">Màn này chỉ đọc; yêu cầu cấp hoặc thu hồi consent vẫn chờ policy phù hợp.</p>
          </article>
        </section>
      )}

      <TeacherAssignmentCard
        key={selectedClass?.class_id ?? "none"}
        selectedClass={selectedClass}
        onAssigned={() => setReloadCount((value) => value + 1)}
      />
    </div>
  );
}
