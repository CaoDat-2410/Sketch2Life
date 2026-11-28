import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowLeft, ArrowRight, Plus, RefreshCw } from "lucide-react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { Alert, Button, ConfirmDialog, FormField } from "../../../../shared/ui";
import { AdminBe1Error } from "../services/be1Client";
import { managerBusinessService, type ParentGroup, type ParentGroupMember, type ParentGroupMemberCounts, type ParentGroupMemberFilter } from "../services/managerBusinessService";

function errorMessage(cause: unknown) {
  return cause instanceof Error ? cause.message : "Không hoàn tất được yêu cầu nhóm phụ huynh.";
}

function createIdempotencyKey() {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return "manager-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Ngày tạo chưa được cung cấp" : date.toLocaleDateString("vi-VN");
}

function formatTimestamp(value: string | null) {
  if (!value) return "Chưa có";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Không rõ thời gian" : date.toLocaleString("vi-VN");
}

function shortMembershipId(value: string) {
  return value.length > 12 ? `${value.slice(0, 8)}…` : value;
}

function memberStateLabel(state: string) {
  const labels: Record<string, string> = {
    INVITED: "Đã mời",
    ACCEPTED: "Đã chấp nhận",
    DECLINED: "Đã từ chối",
    REVOKED: "Đã thu hồi",
    EXPIRED: "Hết hạn",
  };
  return labels[state] ?? "Trạng thái chưa rõ";
}

function revokeActionLabel(member: ParentGroupMember) {
  return member.state === "INVITED" ? "Thu hồi lời mời" : "Thu hồi thành viên";
}

function membershipSignature(groupId: string, member: ParentGroupMember) {
  return JSON.stringify([groupId, member.membership_id, member.revision]);
}

function failureCode(cause: unknown) {
  return cause && typeof cause === "object" && "code" in cause ? String(cause.code) : "";
}

function failureRetryable(cause: unknown) {
  return cause && typeof cause === "object" && "retryable" in cause && cause.retryable === true;
}

export function ParentGroupsPage() {
  const [groups, setGroups] = useState<ParentGroup[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [cursorHistory, setCursorHistory] = useState<Array<string | undefined>>([undefined]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [creating, setCreating] = useState(false);
  const [creationError, setCreationError] = useState("");
  const [creationSuccess, setCreationSuccess] = useState("");
  const [retryKey, setRetryKey] = useState<string | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [memberFilter, setMemberFilter] = useState<ParentGroupMemberFilter | "ALL">("ALL");
  const [members, setMembers] = useState<ParentGroupMember[]>([]);
  const [memberCounts, setMemberCounts] = useState<ParentGroupMemberCounts | null>(null);
  const [memberCursor, setMemberCursor] = useState<string | null>(null);
  const [membersLoading, setMembersLoading] = useState(false);
  const [memberError, setMemberError] = useState("");
  const [memberSuccess, setMemberSuccess] = useState("");
  const [parentPrincipalRef, setParentPrincipalRef] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteRetryKey, setInviteRetryKey] = useState<string | null>(null);
  const [revokingSignature, setRevokingSignature] = useState<string | null>(null);
  const [pendingRevoke, setPendingRevoke] = useState<{ groupId: string; member: ParentGroupMember } | null>(null);
  const [retryRevokeSignatures, setRetryRevokeSignatures] = useState<Set<string>>(() => new Set());
  const [clockNow, setClockNow] = useState(() => Date.now());
  const revokeKeys = useRef(new Map<string, string>());
  const cursor = cursorHistory[cursorHistory.length - 1];

  const loadMemberPage = useCallback(async (
    groupId: string,
    state: ParentGroupMemberFilter | "ALL",
    pageCursor?: string,
    append = false,
    signal?: AbortSignal,
  ) => {
    setMembersLoading(true);
    setMemberError("");
    try {
      const page = await managerBusinessService.parentGroupMembers(groupId, {
        state: state === "ALL" ? undefined : state,
        cursor: pageCursor,
        signal,
      });
      if (!signal?.aborted) {
        setClockNow(Date.now());
        setMembers((current) => append ? [...current, ...page.items] : page.items);
        setMemberCounts(page.counts);
        setMemberCursor(page.next_cursor);
      }
    } catch (cause: unknown) {
      if (!signal?.aborted) {
        if (!append) {
          setMembers([]);
          setMemberCounts(null);
          setMemberCursor(null);
        }
        setMemberError(errorMessage(cause));
      }
    } finally {
      if (!signal?.aborted) setMembersLoading(false);
    }
  }, []);

  const loadGroups = useCallback(async (pageCursor?: string, signal?: AbortSignal) => {
    try {
      const page = await managerBusinessService.parentGroups(pageCursor, signal);
      if (!signal?.aborted) {
        setGroups(page.items);
        setNextCursor(page.next_cursor);
      }
    } catch (cause: unknown) {
      if (!signal?.aborted) {
        setGroups([]);
        setNextCursor(null);
        setListError(errorMessage(cause));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    managerBusinessService.parentGroups(cursor, controller.signal)
      .then((page) => {
        if (!controller.signal.aborted) {
          setGroups(page.items);
          setNextCursor(page.next_cursor);
          setListError("");
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setGroups([]);
          setNextCursor(null);
          setListError(errorMessage(cause));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [cursor]);

  const createGroup = async (event: FormEvent) => {
    event.preventDefault();
    const name = displayName.trim();
    if (!name || creating) return;
    const idempotencyKey = retryKey ?? createIdempotencyKey();
    setCreating(true);
    setCreationError("");
    setCreationSuccess("");
    try {
      const created = await managerBusinessService.createParentGroup(name, idempotencyKey);
      setDisplayName("");
      setRetryKey(null);
      setCreationSuccess("Đã tạo nhóm “" + created.display_name + "” theo xác nhận của backend.");
      setLoading(true);
      setListError("");
      await loadGroups(cursor);
    } catch (cause: unknown) {
      setCreationError(errorMessage(cause));
      const requestWasRejected = cause instanceof AdminBe1Error
        && cause.status >= 400
        && cause.status < 500
        && cause.status !== 408;
      setRetryKey(requestWasRejected ? null : idempotencyKey);
    } finally {
      setCreating(false);
    }
  };

  const activePendingRevoke = pendingRevoke &&
    selectedGroupId === pendingRevoke.groupId &&
    members.some(
      (item) =>
        item.membership_id === pendingRevoke.member.membership_id &&
        item.revision === pendingRevoke.member.revision &&
        (item.state === "INVITED" || item.state === "ACCEPTED"),
    )
    ? pendingRevoke
    : null;

  if (pendingRevoke && !activePendingRevoke) {
    setPendingRevoke(null);
  }

  const requestRevokeMember = (member: ParentGroupMember) => {
    if (!selectedGroupId || revokingSignature || activePendingRevoke) return;
    setPendingRevoke({ groupId: selectedGroupId, member });
  };

  const revokeMember = async (groupId: string, member: ParentGroupMember) => {
    if (revokingSignature) return;
    const signature = membershipSignature(groupId, member);
    const idempotencyKey = revokeKeys.current.get(signature) ?? createIdempotencyKey();
    revokeKeys.current.set(signature, idempotencyKey);
    setRevokingSignature(signature);
    setMemberError("");
    setMemberSuccess("");
    try {
      await managerBusinessService.revokeParentGroupMember(groupId, member.membership_id, member.revision, idempotencyKey);
      revokeKeys.current.delete(signature);
      setRetryRevokeSignatures((current) => {
        const updated = new Set(current);
        updated.delete(signature);
        return updated;
      });
      setMemberSuccess(member.state === "INVITED" ? "Đã thu hồi lời mời." : "Đã thu hồi thành viên.");
      await loadMemberPage(groupId, memberFilter);
    } catch (cause: unknown) {
      const code = failureCode(cause);
      if (code === "STALE_REVISION" || code === "INVALID_STATE_TRANSITION") {
        revokeKeys.current.delete(signature);
        setRetryRevokeSignatures((current) => {
          const updated = new Set(current);
          updated.delete(signature);
          return updated;
        });
        await loadMemberPage(groupId, memberFilter);
        setMemberError(errorMessage(cause));
      } else if (failureRetryable(cause) || (cause && typeof cause === "object" && "status" in cause && cause.status === 0)) {
        setRetryRevokeSignatures((current) => new Set(current).add(signature));
        setMemberError(errorMessage(cause));
      } else {
        revokeKeys.current.delete(signature);
        setRetryRevokeSignatures((current) => {
          const updated = new Set(current);
          updated.delete(signature);
          return updated;
        });
        setMemberError(errorMessage(cause));
      }
    } finally {
      setRevokingSignature(null);
    }
  };

  const confirmRevokeMember = () => {
    const target = activePendingRevoke;
    if (!target || revokingSignature) return;
    setPendingRevoke(null);
    void revokeMember(target.groupId, target.member);
  };

  const inviteParent = async (event: FormEvent) => {
    event.preventDefault();
    const groupId = selectedGroupId;
    if (!groupId || selectedGroup?.state !== "ACTIVE" || inviting || !parentPrincipalRef.trim()) return;
    const idempotencyKey = inviteRetryKey ?? createIdempotencyKey();
    setInviteRetryKey(idempotencyKey);
    setInviting(true);
    setMemberError("");
    setMemberSuccess("");
    try {
      const invitation = await managerBusinessService.inviteParentToGroup(groupId, parentPrincipalRef, idempotencyKey);
      setInviteRetryKey(null);
      setParentPrincipalRef("");
      setMemberFilter("INVITED");
      setMemberSuccess(`Đã mời, hết hạn ngày ${formatDate(invitation.expires_at)}`);
      await loadMemberPage(groupId, "INVITED");
    } catch (cause: unknown) {
      const outcomeKnown = cause instanceof AdminBe1Error
        && cause.status >= 400
        && cause.status < 500
        && cause.status !== 408;
      setInviteRetryKey(outcomeKnown ? null : idempotencyKey);
      setMemberError(errorMessage(cause));
    } finally {
      setInviting(false);
    }
  };

  const selectGroup = (groupId: string) => {
    setSelectedGroupId(groupId);
    setMemberFilter("ALL");
    setParentPrincipalRef("");
    setInviteRetryKey(null);
    setMembers([]);
    setMemberCounts(null);
    setMemberCursor(null);
    setMemberError("");
    setMemberSuccess("");
    void loadMemberPage(groupId, "ALL");
  };

  const changeMemberFilter = (state: ParentGroupMemberFilter | "ALL") => {
    setMemberFilter(state);
    setMembers([]);
    setMemberCounts(null);
    setMemberCursor(null);
    setMemberError("");
    setMemberSuccess("");
    if (selectedGroupId) void loadMemberPage(selectedGroupId, state);
  };

  const requestOutcomeUnknown = retryKey !== null;
  const pageNumber = cursorHistory.length;
  const selectedGroup = groups.find((group) => group.parent_group_id === selectedGroupId);
  const pendingRevokeMemberIndex = activePendingRevoke
    ? members.findIndex((member) => member.membership_id === activePendingRevoke.member.membership_id)
    : -1;
  const inviteFormDisabled = !selectedGroup || selectedGroup.state === "ARCHIVED" || inviting;

  return (
    <div className="s2l-page manager-business-page manager-business-page--parent-groups">
      <PageHeading
        eyebrow="Quản lý trường"
        title="Nhóm phụ huynh"
        description="Danh sách và tạo nhóm phụ huynh trong phạm vi nhà trường."
        action={
          <button
            type="button"
            className="manager-business-button"
            onClick={() => {
              setLoading(true);
              setListError("");
              void loadGroups(cursor);
            }}
            disabled={loading || inviting}
          >
            <RefreshCw size={16} aria-hidden="true" />
            Làm mới
          </button>
        }
      />

      {listError && <Alert className="manager-business-alert" tone="danger" role="alert">{listError}</Alert>}

      <div className="manager-business-parent-groups-layout">
        <div className="manager-business-parent-groups-master">
        <section className="manager-business-card cozy-form-card cozy-form-card--wide cozy-form-stack manager-business-parent-groups-create">
          <div className="manager-business-card-heading">
            <div>
              <p className="manager-business-eyebrow">Khởi tạo nhóm</p>
              <h2>Tạo nhóm trong trường</h2>
            </div>
            <span className="manager-business-chip">Quản trị trường</span>
          </div>
          <form className="manager-business-create-form cozy-form-stack" onSubmit={(event) => void createGroup(event)}>
            <FormField
              label="Tên nhóm phụ huynh"
              htmlFor="parent-group-name"
              required
              help="Nếu mạng ngắt và kết quả chưa rõ, gửi lại sẽ dùng cùng mã yêu cầu để tránh tạo trùng."
            >
              <input
                id="parent-group-name"
                className="cozy-input"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                minLength={1}
                maxLength={120}
                required
                disabled={creating || requestOutcomeUnknown}
                placeholder="Ví dụ: Phụ huynh lớp Lá 1"
              />
            </FormField>
            {creationError && <Alert role="alert" tone="danger">{creationError}</Alert>}
            {creationSuccess && <Alert role="status" tone="success">{creationSuccess}</Alert>}
            {!creating && !displayName.trim() && (
              <p className="cozy-form-disabled-hint">Nhập tên nhóm phụ huynh để bật nút tạo nhóm.</p>
            )}
            <div className="cozy-form-actions" style={{ marginTop: 0 }}>
              <Button
                type="submit"
                variant="primary"
                loading={creating}
                disabled={creating || !displayName.trim()}
                iconLeft={<Plus size={16} aria-hidden="true" />}
              >
                {creating ? "Đang gửi…" : requestOutcomeUnknown ? "Gửi lại cùng yêu cầu" : "Tạo nhóm"}
              </Button>
            </div>
          </form>
        </section>

        <section className="manager-business-card manager-business-parent-groups-list-card">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">Danh sách</p>
            <h2>Nhóm đã tạo</h2>
          </div>
          {groups.length > 0 && <span className="manager-business-chip">{groups.length} nhóm</span>}
        </div>
        {loading ? (
          <p className="manager-business-state" role="status">Đang tải danh sách nhóm…</p>
        ) : groups.length === 0 ? (
          <p className="manager-business-state">Trường chưa có nhóm phụ huynh nào.</p>
        ) : (
          <ul className="manager-business-group-list manager-business-parent-group-list">
            {groups.map((group) => (
              <li key={group.parent_group_id}>
                <button
                  type="button"
                  className={`manager-business-button manager-business-parent-group-button${selectedGroupId === group.parent_group_id ? " is-selected" : ""}`}
                  aria-pressed={selectedGroupId === group.parent_group_id}
                  disabled={inviting}
                  onClick={() => selectGroup(group.parent_group_id)}
                >
                  <span className="manager-business-avatar" aria-hidden="true">{group.display_name.slice(0, 1).toLocaleUpperCase()}</span>
                  <span className="manager-business-group-copy">
                    <strong>{group.display_name}</strong>
                    <small><time dateTime={group.created_at}>{formatDate(group.created_at)}</time> · {group.state === "ACTIVE" ? "Đang hoạt động" : "Đã lưu trữ"}</small>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {(cursorHistory.length > 1 || nextCursor !== null) && (
        <div className="manager-business-pagination manager-business-parent-groups-pagination">
          <span>Trang {pageNumber}</span>
          <div>
            <button
              type="button"
              className="manager-business-button"
              onClick={() => {
                setLoading(true);
                setListError("");
                setCursorHistory((history) => history.slice(0, -1));
              }}
              disabled={loading || inviting || pageNumber <= 1}
            >
              <ArrowLeft size={15} aria-hidden="true" /> Trước
            </button>
            <button
              type="button"
              className="manager-business-button"
              onClick={() => {
                if (!nextCursor) return;
                setLoading(true);
                setListError("");
                setCursorHistory((history) => [...history, nextCursor]);
              }}
              disabled={loading || inviting || !nextCursor}
            >
              Tiếp <ArrowRight size={15} aria-hidden="true" />
            </button>
          </div>
        </div>
        )}
      </section>
      </div>

      <section className="manager-business-card manager-business-parent-groups-detail" aria-labelledby="parent-group-members-heading">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">Quản lý thành viên</p>
            <h2 id="parent-group-members-heading">Thành viên nhóm</h2>
          </div>
          {selectedGroup && <span className="manager-business-chip">{selectedGroup.display_name}</span>}
          {selectedGroupId && <button type="button" className="manager-business-button" disabled={membersLoading || inviting} onClick={() => void loadMemberPage(selectedGroupId, memberFilter)}>Làm mới</button>}
        </div>
        {!selectedGroupId ? (
          <>
            <p className="manager-business-state manager-business-parent-groups-empty">Chọn một nhóm để xem thành viên và gửi lời mời.</p>
            <ol className="manager-business-parent-groups-guide" aria-label="Cách mời phụ huynh vào nhóm">
              <li><b aria-hidden="true">1</b><div><strong>Chọn nhóm</strong><span>Bấm vào một nhóm đang hoạt động trong danh sách “Nhóm đã tạo”.</span></div></li>
              <li><b aria-hidden="true">2</b><div><strong>Mời phụ huynh</strong><span>Nhập mã tài khoản do phụ huynh sao chép từ tài khoản của họ.</span></div></li>
              <li><b aria-hidden="true">3</b><div><strong>Theo dõi lời mời</strong><span>Xem lời mời đã được chấp nhận, từ chối hay đã thu hồi.</span></div></li>
            </ol>
          </>
        ) : (
          <>
            <FormField label="Lọc trạng thái" htmlFor="parent-group-member-state">
              <select
                id="parent-group-member-state"
                className="cozy-input"
                value={memberFilter}
                disabled={inviting}
                onChange={(event) => changeMemberFilter(event.target.value as ParentGroupMemberFilter | "ALL")}
              >
                <option value="ALL">Tất cả trạng thái</option>
                <option value="INVITED">Đã mời</option>
                <option value="ACCEPTED">Đã chấp nhận</option>
                <option value="DECLINED">Đã từ chối</option>
                <option value="REVOKED">Đã thu hồi</option>
                <option value="EXPIRED">Hết hạn</option>
              </select>
            </FormField>
            {memberCounts && (
              <dl className="manager-business-parent-groups-counts" aria-label="Số lượng thành viên theo trạng thái">
                <div><dt>Đã mời</dt><dd>{memberCounts.invited}</dd></div>
                <div><dt>Đã chấp nhận</dt><dd>{memberCounts.accepted}</dd></div>
                <div><dt>Đã từ chối</dt><dd>{memberCounts.declined}</dd></div>
                <div><dt>Đã thu hồi</dt><dd>{memberCounts.revoked}</dd></div>
                <div><dt>Hết hạn</dt><dd>{memberCounts.expired}</dd></div>
                <div><dt>Tổng</dt><dd>{memberCounts.total}</dd></div>
              </dl>
            )}
            {memberSuccess && <Alert role="status" tone="success">{memberSuccess}</Alert>}
            {memberError && <Alert role="alert" tone="danger">{memberError}</Alert>}
            <div className="manager-business-parent-groups-invite">
              <div className="manager-business-parent-groups-invite-heading">
                <p className="manager-business-eyebrow">Lời mời</p>
                <h3>Mời thêm phụ huynh</h3>
              </div>
              <form className="cozy-form-stack manager-business-parent-groups-invite-form" onSubmit={(event) => void inviteParent(event)}>
              <FormField
                label="Mã tài khoản phụ huynh"
                htmlFor="parent-group-principal-ref"
                required
                help="Không có tra cứu bằng email. Nhập mã tài khoản do Phụ huynh sao chép từ tài khoản của họ."
              >
                <input
                  id="parent-group-principal-ref"
                  className="cozy-input"
                  value={parentPrincipalRef}
                  onChange={(event) => {
                    setParentPrincipalRef(event.target.value);
                    setInviteRetryKey(null);
                    setMemberError("");
                    setMemberSuccess("");
                  }}
                  minLength={1}
                  required
                  autoComplete="off"
                  disabled={inviteFormDisabled}
                />
              </FormField>
              {selectedGroup?.state === "ARCHIVED" && (
                <p className="cozy-form-disabled-hint">Nhóm đã lưu trữ; không thể mời thành viên.</p>
              )}
              <div className="cozy-form-actions" style={{ marginTop: 0 }}>
                <Button
                  type="submit"
                  variant="primary"
                  loading={inviting}
                  disabled={inviteFormDisabled || !parentPrincipalRef.trim()}
                  iconLeft={<Plus size={16} aria-hidden="true" />}
                >
                  {inviting ? "Đang gửi lời mời…" : inviteRetryKey ? "Gửi lại cùng yêu cầu" : "Mời phụ huynh"}
                </Button>
              </div>
              </form>
            </div>
            {membersLoading && members.length === 0 ? (
              <p className="manager-business-state manager-business-parent-groups-empty" role="status">Đang tải danh sách phụ huynh…</p>
            ) : members.length === 0 ? (
              <p className="manager-business-state manager-business-parent-groups-empty">Chưa có phụ huynh trong trạng thái này.</p>
            ) : (
              <ul className="manager-business-group-list manager-business-parent-group-members">
                {members.map((member, index) => {
                  const signature = membershipSignature(selectedGroupId, member);
                  const expiredInvite = member.state === "INVITED" && member.expires_at !== null && Date.parse(member.expires_at) < clockNow;
                  const canRevoke = member.state === "INVITED" || member.state === "ACCEPTED";
                  const actionLabel = revokeActionLabel(member);
                  return (
                    <li key={member.membership_id}>
                      <div className="manager-business-parent-groups-member-row">
                        <div className="manager-business-group-copy">
                          <strong>Phụ huynh {index + 1}</strong>
                          <small className="manager-business-parent-groups-member-id">{shortMembershipId(member.membership_id)}</small>
                          <small>{expiredInvite ? "Hết hạn" : memberStateLabel(member.state)}</small>
                          <small>Mời: {formatTimestamp(member.invited_at)} · Hết hạn: {formatTimestamp(member.expires_at)}</small>
                          <small>Chấp nhận: {formatTimestamp(member.accepted_at)}</small>
                        </div>
                        {canRevoke && (
                          <button
                            type="button"
                            className="manager-business-button manager-business-parent-groups-revoke"
                            disabled={revokingSignature !== null || Boolean(activePendingRevoke)}
                            onClick={() => requestRevokeMember(member)}
                          >
                            {revokingSignature === signature ? "Đang thu hồi…" : retryRevokeSignatures.has(signature) ? `Thử lại: ${actionLabel}` : actionLabel}
                          </button>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
            {memberCursor && <button type="button" className="manager-business-button manager-business-parent-groups-load-more" disabled={membersLoading || inviting} onClick={() => void loadMemberPage(selectedGroupId, memberFilter, memberCursor, true)}>{membersLoading ? "Đang tải…" : "Tải thêm phụ huynh"}</button>}
          </>
        )}
      </section>
      </div>
      <ConfirmDialog
        open={Boolean(activePendingRevoke)}
        onOpenChange={(open) => {
          if (!open) setPendingRevoke(null);
        }}
        title={activePendingRevoke ? `${revokeActionLabel(activePendingRevoke.member)} của Phụ huynh ${pendingRevokeMemberIndex + 1}?` : ""}
        description={activePendingRevoke?.member.state === "INVITED"
          ? "Lời mời này sẽ không còn hiệu lực."
          : activePendingRevoke ? "Phụ huynh này sẽ không còn quyền trong nhóm phụ huynh." : ""}
        confirmLabel={activePendingRevoke ? revokeActionLabel(activePendingRevoke.member) : "Thu hồi"}
        tone="danger"
        onConfirm={confirmRevokeMember}
      />
    </div>
  );
}
