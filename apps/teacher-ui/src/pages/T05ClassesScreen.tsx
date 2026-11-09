import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTeacher } from "../context/TeacherContext";
import { ClassRosterRow, TeacherAssignedClassInfo } from "../data/mockTeacherData";
import { Icon } from "../components/Icon";
import { IconTile, PageHead } from "./T01WorkspaceScreen";
import {
  BackendApiError,
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
  isLocalPreview,
  type Be1Class,
} from "../../../shared/backendApi";

function TeacherApiClassesPage() {
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
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "teacher")) {
          throw new BackendApiError("Tài khoản không có assignment teacher trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return backendApi.classes(organizationId);
      })
      .then((page) => { if (active) setClasses(page.items); })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reload]);

  return (
    <div className="tw-page">
      <PageHead title="Lớp được phân công" hint="Danh sách lấy từ assignment và phạm vi lớp của tài khoản Teacher." right={<button type="button" className="tw-btn is-ghost is-sm" disabled={loading} onClick={() => setReload((value) => value + 1)}>Tải lại</button>} />
      <BackendModeNotice roleLabel="Giáo viên" />
      {loading && <BackendNotice title="Đang tải lớp">Đang xác nhận assignment Teacher.</BackendNotice>}
      {error && <BackendNotice title="Không thể tải lớp" tone="error">{error}</BackendNotice>}
      {!loading && !error && classes.length === 0 && <BackendNotice title="Chưa có lớp được phân công">BE không trả về lớp nào trong phạm vi quyền của tài khoản này.</BackendNotice>}
      {classes.map((item) => <button key={item.class_id} type="button" className="tw-card is-lift tw-row tw-between tw-wrap" style={{ width: "100%", textAlign: "left", marginBottom: 12 }} onClick={() => navigate(`/t05-classes-and-children/${encodeURIComponent(item.class_id)}`)}>
        <span><strong className="tw-h2">{item.display_name}</strong><span className="tw-meta" style={{ display: "block", marginTop: 6 }}>class_id: {item.class_id} · {item.state}</span></span><span className="tw-btn is-sm">Xem hồ sơ &amp; consent <Icon name="arrow-right" size={16} /></span>
      </button>)}
      <BackendNotice title="Hồ sơ trẻ được bảo vệ theo consent" tone="warn">BE trả hồ sơ trẻ chỉ khi consent tương ứng đang có hiệu lực. Nếu consent chưa effective, API trả 409 CONSENT_NOT_EFFECTIVE và UI sẽ không hiển thị dữ liệu trẻ.</BackendNotice>
    </div>
  );
}

function TeacherApiClassDetailPage({ classId }: { classId: string }) {
  const navigate = useNavigate();
  const [classItem, setClassItem] = useState<Be1Class | null>(null);
  const [profiles, setProfiles] = useState<Array<{ child_id: string; display_name: string; age_months: number }>>([]);
  const [consents, setConsents] = useState<Array<{ consent_id: string; child_id: string; purpose_ref: string; state: string; effective: boolean }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
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
    backendApi.assignments(organizationId)
      .then(async (identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "teacher")) {
          throw new BackendApiError("Tài khoản không có assignment teacher.", "ROLE_MISMATCH", 403);
        }
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
        else setError(backendMessage(consentResult.reason));
        if (profileResult.status === "fulfilled") setProfiles(profileResult.value.items);
        else setProfileError(backendMessage(profileResult.reason));
      })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [classId, reload]);

  return (
    <div className="tw-page">
      <div className="tw-row tw-between tw-wrap"><div><button type="button" className="tw-btn is-ghost is-sm" onClick={() => navigate("/t05-classes-and-children")}>← Danh sách lớp</button><PageHead title={classItem?.display_name ?? "Chi tiết lớp"} hint={`class_id: ${classId}`} /></div><button type="button" className="tw-btn is-ghost is-sm" disabled={loading} onClick={() => setReload((value) => value + 1)}>Tải lại</button></div>
      <BackendModeNotice roleLabel="Giáo viên" />
      {loading && <BackendNotice title="Đang tải dữ liệu lớp">Đang đọc hồ sơ và consent trong phạm vi được phân công.</BackendNotice>}
      {error && <BackendNotice title="Không thể đọc dữ liệu lớp" tone="error">{error}</BackendNotice>}
      {profileError && <BackendNotice title="Hồ sơ trẻ đang bị khóa" tone="warn">{profileError}</BackendNotice>}
      {classItem && <section className="tw-card">
        <h2 className="tw-h2">Hồ sơ trẻ</h2>
        {!profileError && profiles.length === 0 && <p className="tw-sub">API không trả hồ sơ trẻ cho lớp này.</p>}
        {profiles.map((profile) => <div className="tw-item tw-row tw-between tw-wrap" key={profile.child_id}><span><strong>{profile.display_name}</strong><span className="tw-meta" style={{ display: "block" }}>{profile.age_months} tháng · child_id: {profile.child_id}</span></span><span className="tw-chip is-mint">Consent effective</span></div>)}
      </section>}
      {classItem && <section className="tw-card">
        <h2 className="tw-h2">Consent được API trả về</h2>
        {consents.length === 0 && !loading && <p className="tw-sub">Không có bản ghi consent trong phản hồi.</p>}
        {consents.map((consent) => <div className="tw-item tw-row tw-between tw-wrap" key={consent.consent_id}><span><strong>{consent.purpose_ref}</strong><span className="tw-meta" style={{ display: "block" }}>child_id: {consent.child_id}</span></span><span className={`tw-chip ${consent.effective ? "is-mint" : "is-amber"}`}>{consent.state} · {consent.effective ? "effective" : "chưa effective"}</span></div>)}
        <p className="tw-meta" style={{ marginBottom: 0 }}>Consent chỉ được đọc; màn này không giả lập ký hoặc tự cấp consent.</p>
      </section>}
    </div>
  );
}

function rbacLabel(state: TeacherAssignedClassInfo["rbacState"]): string {
  switch (state) {
    case "ACTIVE":
      return "Đang phụ trách";
    case "TRANSFER_PENDING":
      return "Chờ bàn giao";
    case "SUSPENDED_READONLY":
      return "Chỉ xem";
    case "UNASSIGNED_403":
      return "Chưa phân quyền";
  }
}

function rbacChipTone(state: TeacherAssignedClassInfo["rbacState"]): string {
  switch (state) {
    case "ACTIVE":
      return "is-mint";
    case "TRANSFER_PENDING":
      return "is-amber";
    case "SUSPENDED_READONLY":
      return "is-gray";
    case "UNASSIGNED_403":
      return "is-rose";
  }
}

/* ───────────── TRANG 1: /t05-classes-and-children — Danh sách lớp học chữ to rõ ràng ───────────── */
export function T05ClassesAndChildrenPage() {
  const navigate = useNavigate();
  const {
    assignedClasses,
    activeClassId,
    setActiveClassId,
    roster,
    forceCloseConflictAndCompleteTransfer,
  } = useTeacher();

  if (!isLocalPreview()) return <TeacherApiClassesPage />;

  const handleOpenClass = (cls: TeacherAssignedClassInfo) => {
    setActiveClassId(cls.id);
    navigate(`/t05-classes-and-children/${cls.id}`);
  };

  return (
    <div className="tw-page">
      <PageHead
        title="Lớp học"
        right={
          <span className="tw-chip is-mint">
            <Icon name="users" size={15} /> {assignedClasses.length} lớp
          </span>
        }
      />

      <div className="tw-grid-2" style={{ gap: 22 }}>
        {assignedClasses.map((cls) => {
          const isCurrent = cls.id === activeClassId;
          const activeRosterCount = roster.filter(
            (r) => r.enrollmentStatus !== "DELETED" && r.className === cls.className
          ).length;
          const displayCount = Math.max(cls.studentCount, activeRosterCount);

          return (
            <div
              key={cls.id}
              role="button"
              tabIndex={0}
              onClick={() => handleOpenClass(cls)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  handleOpenClass(cls);
                }
              }}
              className={"tw-card is-lift" + (isCurrent ? " is-sky" : "")}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 16,
                padding: 26,
              }}
            >
              <div className="tw-row tw-between tw-wrap" style={{ alignItems: "flex-start" }}>
                <div className="tw-row" style={{ gap: 14 }}>
                  <span
                    className={"tw-ico " + (cls.rbacState === "ACTIVE" ? "is-mint" : "is-amber")}
                    style={{ width: 56, height: 56, borderRadius: 18 }}
                    aria-hidden="true"
                  >
                    <Icon name="users" size={26} />
                  </span>
                  <div>
                    <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>{cls.className}</h2>
                    <div className="tw-meta" style={{ fontSize: 15, marginTop: 3 }}>
                      <strong className="tw-strong">{cls.ownerTeacher}</strong>
                    </div>
                  </div>
                </div>

                <span className={"tw-chip " + rbacChipTone(cls.rbacState)}>
                  {rbacLabel(cls.rbacState)}
                </span>
              </div>

              <div className="tw-row tw-wrap" style={{ gap: 8 }}>
                <span className="tw-chip is-gray" title="Sĩ số lớp">{displayCount} học sinh</span>
                <span className="tw-chip is-gray" title="Hồ sơ đã nhập">{activeRosterCount} hồ sơ</span>
                <span className="tw-chip is-gray" title="Độ tuổi">{cls.ageRangeLabel.split(" (")[0]}</span>
              </div>
              {cls.hasActiveRunConflict && (
                <div
                  className="tw-item is-amber tw-row tw-between tw-wrap"
                  onClick={(e) => e.stopPropagation()}
                  style={{ gap: 10 }}
                >
                  <div style={{ fontSize: 14 }}>
                    <strong>Bàn giao cho {cls.pendingTargetTeacher}</strong>
                  </div>
                  <button
                    type="button"
                    className="tw-btn is-amber is-sm"
                    onClick={() =>
                      forceCloseConflictAndCompleteTransfer(
                        cls.id,
                        "Đóng phiên chạy cũ để bàn giao lớp đầu tuần"
                      )
                    }
                  >
                    Hoàn tất
                  </button>
                </div>
              )}

              <div className="tw-row tw-between tw-wrap" style={{ marginTop: "auto", paddingTop: 4 }}>

                <span className="tw-btn is-sm">
                  Mở lớp <Icon name="arrow-right" size={16} />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ───────────── TRANG 2: /t05-classes-and-children/:classId — Chi tiết lớp & Danh sách học sinh ───────────── */
export function T05ClassDetailPage() {
  const { classId } = useParams<{ classId: string }>();
  if (!isLocalPreview()) return <TeacherApiClassDetailPage classId={classId ?? ""} />;
  return <TeacherMockClassDetailPage />;
}

function TeacherMockClassDetailPage() {
  const navigate = useNavigate();
  const { classId } = useParams<{ classId: string }>();
  const {
    assignedClasses,
    activeClassId,
    setActiveClassId,
    roster,
    addRosterChild,
    updateRosterChild,
    transferChildClass,
    deleteRosterChildLifecycle,
    showToast,
  } = useTeacher();

  const resolvedClass =
    assignedClasses.find((c) => c.id === classId) ||
    assignedClasses.find((c) => c.id === activeClassId) ||
    assignedClasses[0];

  useEffect(() => {
    if (classId && assignedClasses.some((c) => c.id === classId) && activeClassId !== classId) {
      setActiveClassId(classId);
    }
  }, [classId, assignedClasses, activeClassId, setActiveClassId]);

  const [search, setSearch] = useState("");
  const [studentModalOpen, setStudentModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<ClassRosterRow | null>(null);

  // Student Modal Form Fields
  const [nameInput, setNameInput] = useState("");
  const [monthsInput, setMonthsInput] = useState("60");
  const [interestsInput, setInterestsInput] = useState("Vẽ tranh, Động vật, Thiên nhiên");
  const [learningNotesInput, setLearningNotesInput] = useState(
    "Bé hào hứng quan sát tranh minh họa và thích phối hợp màu sáp tươi sáng."
  );
  const [supportNoteInput, setSupportNoteInput] = useState(
    "Chỉ hiển thị với giáo viên; không gửi vào AI."
  );

  useEffect(() => {
    if (!studentModalOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setStudentModalOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [studentModalOpen]);

  const openAddStudentModal = () => {
    setEditingStudent(null);
    setNameInput("");
    setMonthsInput("60");
    setInterestsInput("Khám phá thiên nhiên, Vẽ màu sáp, Kể chuyện");
    setLearningNotesInput("Bé tích cực tham gia giờ vẽ trên giấy A4 cùng các bạn.");
    setSupportNoteInput("Chỉ hiển thị với giáo viên; không gửi vào AI.");
    setStudentModalOpen(true);
  };

  const openEditStudentModal = (row: ClassRosterRow) => {
    setEditingStudent(row);
    setNameInput(row.displayLabel.replace(/\s*·\s*\d+\s*tuổi$/i, "").trim());
    setMonthsInput(String(row.ageMonths));
    setInterestsInput(row.interests.join(", "));
    setLearningNotesInput(row.learningNotes);
    setSupportNoteInput(row.supportNeedsNote);
    setStudentModalOpen(true);
  };

  const handleSaveStudent = (e: React.FormEvent) => {
    e.preventDefault();
    const months = Number(monthsInput);
    if (!nameInput.trim()) {
      showToast("Vui lòng nhập tên hiển thị của học sinh.", "warn");
      return;
    }
    if (!Number.isFinite(months) || months < 36 || months > 155) {
      showToast("Độ tuổi phải nằm trong khoảng 36 đến 155 tháng.", "err");
      return;
    }
    const parsedInterests = interestsInput
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    const finalInterests =
      parsedInterests.length > 0 ? parsedInterests : ["Vẽ màu sáp", "Thiên nhiên"];

    if (editingStudent) {
      updateRosterChild(editingStudent.id, {
        label: nameInput.trim(),
        ageMonths: months,
        interests: finalInterests,
        learningNotes: learningNotesInput.trim(),
        supportNeedsNote: supportNoteInput.trim() || "Chỉ hiển thị với giáo viên; không gửi vào AI.",
      });
    } else {
      addRosterChild(
        nameInput.trim(),
        months,
        finalInterests,
        learningNotesInput.trim(),
        supportNoteInput.trim() || "Chỉ hiển thị với giáo viên; không gửi vào AI.",
        resolvedClass.className
      );
    }
    setStudentModalOpen(false);
  };

  const rows = roster
    .filter((r) => r.enrollmentStatus !== "DELETED" && r.className === resolvedClass.className)
    .filter((r) => {
      const q = search.trim().toLowerCase();
      if (!q) return true;
      return (
        r.displayLabel.toLowerCase().includes(q) ||
        r.interests.join(" ").toLowerCase().includes(q) ||
        r.learningNotes.toLowerCase().includes(q)
      );
    });

  const isReadOnly =
    resolvedClass.rbacState === "SUSPENDED_READONLY" ||
    resolvedClass.rbacState === "UNASSIGNED_403";

  return (
    <div className="tw-page">
      {/* Thanh điều hướng quay lại + Tiêu đề lớp 30px + Nút + Thêm học sinh */}
      <div className="tw-row tw-between tw-wrap" style={{ gap: 16 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <button
              type="button"
              className="tw-btn is-ghost is-sm"
              onClick={() => navigate("/t05-classes-and-children")}
            >
              <Icon name="arrow-left" size={16} /> Quay lại danh sách lớp
            </button>
          </div>

          <h1 className="tw-title" style={{ fontSize: 30 }}>
            {resolvedClass.className} · Danh sách học sinh
          </h1>

          <div className="tw-row tw-wrap" style={{ gap: 8 }}>
            <span className={"tw-chip " + rbacChipTone(resolvedClass.rbacState)}>
              {rbacLabel(resolvedClass.rbacState)}
            </span>
            <span className="tw-chip">{resolvedClass.ageRangeLabel}</span>
            <span className="tw-chip is-mint">{rows.length} học sinh</span>
            <span className="tw-chip is-gray">{resolvedClass.ownerTeacher}</span>
            <span className="tw-chip is-amber">Ghi chú ẩn với AI</span>
          </div>
        </div>

        <button
          type="button"
          className="tw-btn is-lg"
          disabled={isReadOnly}
          onClick={openAddStudentModal}
        >
          <Icon name="plus" size={20} /> Thêm học sinh
        </button>
      </div>

      {isReadOnly && (
        <div className="tw-card is-amber tw-row">
          <IconTile name="lock" tone="is-amber" />
          <div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>
              Chế độ chỉ xem
            </h2>
            <p className="tw-meta" style={{ marginTop: 2 }}>
              Chuyển sang lớp được phân công để sửa hồ sơ.
            </p>
          </div>
        </div>
      )}

      {/* Bảng danh sách học sinh toàn chiều ngang, cỡ chữ lớn 15px–16px */}
      <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 16, padding: 24 }}>
        <div className="tw-row tw-between tw-wrap" style={{ gap: 12 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>
            Học sinh
          </h2>
          <input
            className="tw-input"
            style={{ maxWidth: 360 }}
            placeholder="Tìm học sinh"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Tìm học sinh trong lớp"
          />
        </div>

        <div className="tw-table-wrap">
          <table className="tw-table is-lg">
            <thead>
              <tr>
                <th>Học sinh</th>
                <th>Tuổi</th>
                <th>Sở thích &amp; ghi chú</th>
                <th>Hỗ trợ</th>
                <th>Chuyển lớp</th>
                <th style={{ textAlign: "right" }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="tw-row" style={{ gap: 12 }}>
                      <span className="tw-avatar is-sm is-mint" aria-hidden="true">
                        <Icon name="user" size={18} />
                      </span>
                      <div>
                        <div className="tw-strong" style={{ fontSize: 16 }}>{r.displayLabel}</div>
                        <div className="tw-meta" style={{ fontSize: 13 }}>
                          {r.enrollmentStatus === "DELETE_PENDING"
                            ? "Đang thu hồi dữ liệu..."
                            : r.previousClassHistory || "Đang học"}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td>
                    <span className="tw-chip" style={{ fontSize: 14 }}>
                      {r.ageText}
                    </span>
                  </td>

                  <td style={{ maxWidth: 320 }}>
                    <div style={{ fontSize: 15 }}>
                      <strong className="tw-strong">Sở thích:</strong> {r.interests.join(", ")}
                    </div>
                    <div className="tw-meta" style={{ fontSize: 14, marginTop: 4 }}>
                      {r.learningNotes}
                    </div>
                  </td>

                  <td style={{ maxWidth: 250 }}>
                    <div style={{ fontSize: 14.5 }}>{r.supportNeedsNote}</div>
                    <span className="tw-chip is-gray" style={{ marginTop: 6, fontSize: 12 }}>
                      <Icon name="eye-off" size={13} /> Ẩn với AI
                    </span>
                  </td>

                  <td>
                    <select
                      className="tw-input"
                      style={{ minWidth: 148, padding: "8px 12px", fontSize: 14.5 }}
                      aria-label={`Chuyển lớp cho ${r.displayLabel}`}
                      value={r.className}
                      disabled={isReadOnly}
                      onChange={(e) => transferChildClass(r.id, e.target.value)}
                    >
                      {assignedClasses.map((c) => (
                        <option key={c.id} value={c.className}>
                          {c.className}
                        </option>
                      ))}
                    </select>
                  </td>

                  <td style={{ textAlign: "right" }}>
                    <div className="tw-row" style={{ justifyContent: "flex-end", gap: 8 }}>
                      <button
                        type="button"
                        className="tw-btn is-ghost is-sm"
                        disabled={isReadOnly}
                        onClick={() => openEditStudentModal(r)}
                      >
                        <Icon name="edit" size={15} /> Sửa
                      </button>
                      <button
                        type="button"
                        className="tw-btn is-danger is-sm"
                        disabled={isReadOnly}
                        aria-label={`Xóa hồ sơ ${r.displayLabel}`}
                        onClick={() => deleteRosterChildLifecycle(r.id)}
                      >
                        <Icon name="trash" size={15} /> Xóa
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {rows.length === 0 && (
          <div className="tw-item is-sky" style={{ textAlign: "center", padding: 26 }}>
            <div className="tw-strong" style={{ fontSize: 17 }}>
              Chưa có học sinh nào khớp bộ lọc trong {resolvedClass.className}
            </div>
            <p className="tw-meta" style={{ marginTop: 4 }}>
              Nhấn nút “+ Thêm học sinh” ở góc phải phía trên để tạo hồ sơ học sinh mới cho lớp.
            </p>
          </div>
        )}
      </div>

      {/* ── MODAL: Thêm mới / Chỉnh sửa Hồ sơ Học sinh (BR-07, BR-18, BR-20) ── */}
      {studentModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="student-modal-title"
          className="tw-modal-backdrop"
          onClick={() => setStudentModalOpen(false)}
        >
          <form
            onSubmit={handleSaveStudent}
            className="tw-modal is-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="tw-row tw-between">
              <div className="tw-row">
                <IconTile
                  name={editingStudent ? "edit" : "plus"}
                  tone={editingStudent ? "is-amber" : "is-mint"}
                />
                <div>
                  <h2 id="student-modal-title" style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>
                    {editingStudent
                      ? `Chỉnh sửa hồ sơ · ${editingStudent.displayLabel}`
                      : `Thêm học sinh mới vào ${resolvedClass.className}`}
                  </h2>
                  <div className="tw-meta">
                    Thông tin chỉ dùng trong hồ sơ lớp.
                  </div>
                </div>
              </div>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={() => setStudentModalOpen(false)}
              >
                <Icon name="close" size={16} /> Đóng
              </button>
            </div>

            <div className="tw-grid-2">
              <label className="tw-label">
                Tên hiển thị hoặc ký hiệu của bé
                <input
                  className="tw-input"
                  placeholder="Ví dụ: Bé An hoặc Bé M.K"
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  required
                />
              </label>

              <label className="tw-label">
                Tuổi theo tháng (36–155 tháng)
                <input
                  className="tw-input"
                  type="number"
                  min={36}
                  max={155}
                  value={monthsInput}
                  onChange={(e) => setMonthsInput(e.target.value)}
                  required
                />
              </label>
            </div>

            <label className="tw-label">
              Sở thích cá nhân (phân tách bằng dấu phẩy)
              <input
                className="tw-input"
                placeholder="Ví dụ: Thích vẽ động vật, Màu sắc tươi sáng, Khám phá cây xanh"
                value={interestsInput}
                onChange={(e) => setInterestsInput(e.target.value)}
              />
            </label>

            <label className="tw-label">
              Quan sát học tập &amp; trải nghiệm trên lớp
              <textarea
                className="tw-input"
                rows={2}
                value={learningNotesInput}
                onChange={(e) => setLearningNotesInput(e.target.value)}
              />
            </label>

            <label className="tw-label">
              Ghi chú hỗ trợ · Ẩn với AI
              <textarea
                className="tw-input"
                rows={2}
                value={supportNoteInput}
                onChange={(e) => setSupportNoteInput(e.target.value)}
              />
            </label>

            <div className="tw-item is-mint tw-row" style={{ gap: 10 }}>
              <Icon name="shield" size={18} />
              <span style={{ fontSize: 13.5 }}>
                Tên và ghi chú của trẻ chỉ hiển thị với giáo viên, không gửi vào AI.
              </span>
            </div>

            <div className="tw-row tw-between tw-wrap">
              <button
                type="button"
                className="tw-btn is-ghost"
                onClick={() => setStudentModalOpen(false)}
              >
                Hủy bỏ
              </button>
              <button type="submit" className="tw-btn">
                <Icon name="check" size={18} />{" "}
                {editingStudent ? "Lưu cập nhật hồ sơ" : "Thêm học sinh vào lớp"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
