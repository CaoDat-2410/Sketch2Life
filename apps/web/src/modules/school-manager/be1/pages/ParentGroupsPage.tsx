import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowLeft, ArrowRight, Plus, RefreshCw } from "lucide-react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { Alert, Button, FormField } from "../../../../shared/ui";
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

  const revokeMember = async (member: ParentGroupMember) => {
    if (!selectedGroupId || revokingSignature) return;
    const shortId = shortMembershipId(member.membership_id);
    if (!window.confirm(`Thu hồi membership ${shortId}?`)) return;
    const signature = membershipSignature(selectedGroupId, member);
    const idempotencyKey = revokeKeys.current.get(signature) ?? createIdempotencyKey();
    revokeKeys.current.set(signature, idempotencyKey);
    setRevokingSignature(signature);
    setMemberError("");
    setMemberSuccess("");
    try {
      await managerBusinessService.revokeParentGroupMember(selectedGroupId, member.membership_id, member.revision, idempotencyKey);
      revokeKeys.current.delete(signature);
      setRetryRevokeSignatures((current) => {
        const updated = new Set(current);
        updated.delete(signature);
        return updated;
      });
      setMemberSuccess(`Đã thu hồi membership ${shortId}.`);
      await loadMemberPage(selectedGroupId, memberFilter);
    } catch (cause: unknown) {
      const code = failureCode(cause);
      if (code === "STALE_REVISION" || code === "INVALID_STATE_TRANSITION") {
        revokeKeys.current.delete(signature);
        setRetryRevokeSignatures((current) => {
          const updated = new Set(current);
          updated.delete(signature);
          return updated;
        });
        await loadMemberPage(selectedGroupId, memberFilter);
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
  const inviteFormDisabled = !selectedGroup || selectedGroup.state === "ARCHIVED" || inviting;

  return (
    <div className="s2l-page manager-business-page">
      <PageHeading
        eyebrow="School Manager · Lesson Library"
        title="Nhóm phụ huynh"
        description="Danh sách và tạo nhóm được xác minh theo organization hiện hành."
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

      <div className="manager-business-split">
        <section className="manager-business-card cozy-form-card cozy-form-card--wide cozy-form-stack">
          <div className="manager-business-card-heading">
            <div>
              <p className="manager-business-eyebrow">POST · Idempotency-Key</p>
              <h2>Tạo nhóm trong trường</h2>
            </div>
            <span className="manager-business-chip">school_admin</span>
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

        <section className="manager-business-card">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">GET · Lesson Library</p>
            <h2>Nhóm đã tạo</h2>
          </div>
          {groups.length > 0 && <span className="manager-business-chip">{groups.length} nhóm</span>}
        </div>
        {loading ? (
          <p className="manager-business-state" role="status">Đang tải danh sách nhóm…</p>
        ) : groups.length === 0 ? (
          <p className="manager-business-state">Organization chưa có nhóm phụ huynh nào.</p>
        ) : (
          <ul className="manager-business-group-list">
            {groups.map((group) => (
              <li key={group.parent_group_id}>
                <button
                  type="button"
                  className="manager-business-button"
                  style={{ width: "100%", justifyContent: "flex-start", textAlign: "left" }}
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
        <div className="manager-business-pagination">
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
      </section>
      </div>

      <section className="manager-business-card" aria-labelledby="parent-group-members-heading">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">GET · DELETE · revision có điều kiện</p>
            <h2 id="parent-group-members-heading">Thành viên nhóm</h2>
          </div>
          {selectedGroup && <span className="manager-business-chip">{selectedGroup.display_name}</span>}
          {selectedGroupId && <button type="button" className="manager-business-button" disabled={membersLoading || inviting} onClick={() => void loadMemberPage(selectedGroupId, memberFilter)}>Làm mới</button>}
        </div>
        {!selectedGroupId ? (
          <p className="manager-business-state">Chọn một nhóm để xem membership.</p>
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
                <option value="INVITED">INVITED · Đã mời</option>
                <option value="ACCEPTED">ACCEPTED · Đã chấp nhận</option>
                <option value="DECLINED">DECLINED · Đã từ chối</option>
                <option value="REVOKED">REVOKED · Đã thu hồi</option>
                <option value="EXPIRED">EXPIRED · Hết hạn</option>
              </select>
            </FormField>
            {memberCounts && (
              <dl aria-label="Số lượng membership theo trạng thái" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: 8 }}>
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
            <form className="cozy-form-stack" onSubmit={(event) => void inviteParent(event)}>
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
            {membersLoading && members.length === 0 ? (
              <p className="manager-business-state" role="status">Đang tải membership…</p>
            ) : members.length === 0 ? (
              <p className="manager-business-state">Không có membership trong trạng thái này.</p>
            ) : (
              <ul className="manager-business-group-list">
                {members.map((member) => {
                  const signature = membershipSignature(selectedGroupId, member);
                  const expiredInvite = member.state === "INVITED" && member.expires_at !== null && Date.parse(member.expires_at) < clockNow;
                  const canRevoke = member.state === "INVITED" || member.state === "ACCEPTED";
                  return (
                    <li key={member.membership_id}>
                      <div style={{ display: "grid", width: "100%", gap: 8 }}>
                        <div className="manager-business-group-copy">
                          <strong>{shortMembershipId(member.membership_id)}</strong>
                          <small>{expiredInvite ? "Hết hạn · INVITED" : member.state}</small>
                          <small>Mời: {formatTimestamp(member.invited_at)} · Hết hạn: {formatTimestamp(member.expires_at)}</small>
                          <small>Chấp nhận: {formatTimestamp(member.accepted_at)}</small>
                        </div>
                        {canRevoke && (
                          <button
                            type="button"
                            className="manager-business-button"
                            disabled={revokingSignature !== null}
                            onClick={() => void revokeMember(member)}
                          >
                            {revokingSignature === signature ? "Đang thu hồi…" : retryRevokeSignatures.has(signature) ? "Xác nhận và thử lại" : "Thu hồi membership"}
                          </button>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
            {memberCursor && <button type="button" className="manager-business-button" disabled={membersLoading || inviting} onClick={() => void loadMemberPage(selectedGroupId, memberFilter, memberCursor, true)}>{membersLoading ? "Đang tải…" : "Tải thêm membership"}</button>}
          </>
        )}
      </section>
    </div>
  );
}
