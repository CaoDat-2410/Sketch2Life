import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTeacher } from "../context/TeacherContext";
import { ClassRosterRow, TeacherAssignedClassInfo } from "../data/mockTeacherData";
import { Icon } from "../components/Icon";
import { IconTile, PageHead } from "./T01WorkspaceScreen";

function rbacLabel(state: TeacherAssignedClassInfo["rbacState"]): string {
  switch (state) {
    case "ACTIVE":
      return "Đang phụ trách (Toàn quyền)";
    case "TRANSFER_PENDING":
      return "Đang chờ bàn giao lớp";
    case "SUSPENDED_READONLY":
      return "Chế độ chỉ xem (Read-only)";
    case "UNASSIGNED_403":
      return "Chưa phân quyền phụ trách";
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

  const handleOpenClass = (cls: TeacherAssignedClassInfo) => {
    setActiveClassId(cls.id);
    navigate(`/t05-classes-and-children/${cls.id}`);
  };

  return (
    <div className="tw-page">
      <PageHead
        title="Danh sách lớp học phụ trách"
        hint="Chọn một lớp học bên dưới để mở trang danh sách học sinh toàn chiều ngang, cập nhật hồ sơ cá nhân hóa (BR-07) hoặc chuyển lớp."
        right={
          <span className="tw-chip is-mint">
            <Icon name="users" size={15} /> {assignedClasses.length} lớp trong trường
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
                      Giáo viên phụ trách: <strong className="tw-strong">{cls.ownerTeacher}</strong>
                    </div>
                  </div>
                </div>

                <span className={"tw-chip " + rbacChipTone(cls.rbacState)}>
                  {rbacLabel(cls.rbacState)}
                </span>
              </div>

              <div className="tw-grid-2" style={{ gap: 12 }}>
                <div className="tw-item" style={{ padding: "13px 16px" }}>
                  <div className="tw-meta" style={{ fontSize: 13.5 }}>Sĩ số học sinh</div>
                  <div className="tw-strong" style={{ fontSize: 16, marginTop: 2 }}>
                    {displayCount} học sinh ({activeRosterCount} hồ sơ chi tiết)
                  </div>
                </div>
                <div className="tw-item" style={{ padding: "13px 16px" }}>
                  <div className="tw-meta" style={{ fontSize: 13.5 }}>Khung độ tuổi</div>
                  <div className="tw-strong" style={{ fontSize: 16, marginTop: 2 }}>
                    {cls.ageRangeLabel}
                  </div>
                </div>
              </div>

              {cls.hasActiveRunConflict && (
                <div
                  className="tw-item is-amber tw-row tw-between tw-wrap"
                  onClick={(e) => e.stopPropagation()}
                  style={{ gap: 10 }}
                >
                  <div style={{ fontSize: 14 }}>
                    <strong>Đang chờ bàn giao sang {cls.pendingTargetTeacher}:</strong> Cần đóng phiên chạy xung đột để hoàn tất.
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
                    Hoàn tất bàn giao
                  </button>
                </div>
              )}

              <div className="tw-row tw-between tw-wrap" style={{ marginTop: "auto", paddingTop: 4 }}>
                <span className="tw-meta" style={{ fontSize: 14.5 }}>
                  Quản lý hồ sơ nội bộ trường (BR-03 · BR-07)
                </span>
                <span className="tw-btn is-sm">
                  Mở danh sách học sinh <Icon name="arrow-right" size={16} />
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
    "Mặc định loại khỏi ngữ cảnh AI (BR-20)."
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
    setSupportNoteInput("Mặc định loại khỏi ngữ cảnh AI (BR-20).");
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
      showToast("Độ tuổi theo tháng phải nằm trong khoảng 36 đến 155 tháng (BR-18).", "err");
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
        supportNeedsNote: supportNoteInput.trim() || "Mặc định loại khỏi ngữ cảnh AI (BR-20).",
      });
    } else {
      addRosterChild(
        nameInput.trim(),
        months,
        finalInterests,
        learningNotesInput.trim(),
        supportNoteInput.trim() || "Mặc định loại khỏi ngữ cảnh AI (BR-20).",
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
            <span className="tw-chip is-mint">{rows.length} hồ sơ đang hiển thị</span>
            <span className="tw-chip is-gray">Phụ trách: {resolvedClass.ownerTeacher}</span>
            <span className="tw-chip is-amber">Ghi chú hỗ trợ ẩn khỏi AI (BR-20)</span>
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
              Lớp học đang ở chế độ hạn chế chỉnh sửa ({rbacLabel(resolvedClass.rbacState)})
            </h2>
            <p className="tw-meta" style={{ marginTop: 2 }}>
              Cô có thể tra cứu danh sách học sinh, hoặc chuyển sang Lớp Mầm 2 trên thanh đầu trang để thêm/sửa hồ sơ.
            </p>
          </div>
        </div>
      )}

      {/* Bảng danh sách học sinh toàn chiều ngang, cỡ chữ lớn 15px–16px */}
      <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 16, padding: 24 }}>
        <div className="tw-row tw-between tw-wrap" style={{ gap: 12 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>
            Hồ sơ học sinh trong {resolvedClass.className}
          </h2>
          <input
            className="tw-input"
            style={{ maxWidth: 360 }}
            placeholder="Tìm học sinh theo tên, sở thích, ghi chú..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Tìm học sinh trong lớp"
          />
        </div>

        <div className="tw-table-wrap">
          <table className="tw-table is-lg">
            <thead>
              <tr>
                <th>Tên học sinh</th>
                <th>Tuổi (tháng)</th>
                <th>Sở thích &amp; Quan sát học tập</th>
                <th>Ghi chú hỗ trợ (BR-20 · Ẩn khỏi AI)</th>
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
                            : r.previousClassHistory || "Đang theo học (ACTIVE)"}
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
                      <Icon name="eye-off" size={13} /> Ẩn khỏi AI prompt
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
                    Biểu mẫu nhập hồ sơ có cấu trúc của trường (BR-07 · Khung tuổi 36–155 tháng BR-18).
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
                Tuổi theo tháng (36–155 tháng · BR-18)
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
              Ghi chú nhu cầu hỗ trợ đặc biệt (BR-20 · Tự động ẩn khỏi ngữ cảnh AI)
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
                Quy tắc bảo vệ dữ liệu trẻ em (BR-20, BR-21): Tên thật và ghi chú hỗ trợ đặc biệt chỉ phục vụ giáo viên trên lớp, tuyệt đối không gửi vào AI prompt.
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
