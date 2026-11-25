import { useCallback, useEffect, useRef, useState } from "react";
import { Gauge, RefreshCw } from "lucide-react";
import { createIdempotencyKey } from "../../../../shared/api/backendApi";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { Button } from "../../../../shared/ui";
import { AdminBe1Error } from "../services/be1Client";
import { capacityService, type Be1OrganizationCapacity, type CapacityCommand } from "../services/capacityService";
import { classService, type Be1Class } from "../services/classService";
import { managerBusinessService, type Be1Organization } from "../services/managerBusinessService";

type ConfirmAction = "cancel_renewal" | "downgrade" | null;
type CapacityPageData = { organization: Be1Organization; capacity: Be1OrganizationCapacity };

function number(value: number) {
  return new Intl.NumberFormat("vi-VN").format(value);
}

function formatDate(value: string | null, withTime = false) {
  if (!value || !Number.isFinite(Date.parse(value))) return "Chưa có thông tin";
  return new Date(value).toLocaleString("vi-VN", withTime
    ? { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }
    : { day: "2-digit", month: "2-digit", year: "numeric" });
}

function subscriptionLabel(state: string) {
  const labels: Record<string, string> = {
    NONE: "Chưa có gói",
    ACTIVE: "Đang hoạt động",
    GRACE: "Đang trong thời gian gia hạn",
    CANCEL_AT_PERIOD_END: "Đã tắt gia hạn cuối kỳ",
  };
  return labels[state] ?? "Trạng thái chưa xác định";
}

function errorText(cause: unknown) {
  if (cause instanceof AdminBe1Error) {
    if (cause.status === 403 || cause.status === 404) return "Không có quyền hoặc không tìm thấy thông tin sức chứa.";
    if (cause.code === "STALE_REVISION") return "Thông tin sức chứa đã thay đổi. Hãy xem lại trước khi xác nhận.";
    if (cause.code === "SUBSCRIPTION_PERIOD_ENDED") return "Kỳ gói đã kết thúc. Hãy tải lại thông tin sức chứa.";
    if (cause.code === "CLASS_SELECTION_REQUIRED") return "Hãy chọn đủ số lớp cần tạm ngưng trước khi xác nhận.";
    if (cause.code === "INVALID_CAPACITY_DOWNGRADE") return "Mức sức chứa hoặc danh sách lớp chưa hợp lệ. Hãy kiểm tra lại lựa chọn.";
    if (cause.code === "INVALID_IDEMPOTENCY_KEY") return "Không thể gửi thao tác này. Hãy thử lại.";
    if (cause.status === 503 || cause.code === "DEPENDENCY_UNAVAILABLE") return "Dịch vụ thanh toán đang tạm thời chưa sẵn sàng. Hãy thử lại sau.";
    if (cause.status === 400 || cause.status === 422) return "Yêu cầu chưa hợp lệ. Hãy kiểm tra lại lựa chọn.";
  }
  return "Không thể tải hoặc cập nhật sức chứa lúc này. Hãy thử lại sau.";
}

function emptyCapacityMessage(cause: unknown) {
  return cause instanceof AdminBe1Error
    ? errorText(cause)
    : "Không thể tải hoặc cập nhật sức chứa lúc này. Hãy thử lại sau.";
}

export function CapacityPage() {
  const [pageData, setPageData] = useState<CapacityPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [commandError, setCommandError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);
  const [downgradeOpen, setDowngradeOpen] = useState(false);
  const [loadingClasses, setLoadingClasses] = useState(false);
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [classLoadError, setClassLoadError] = useState("");
  const [addonSlots, setAddonSlots] = useState("");
  const [selectedClassRefs, setSelectedClassRefs] = useState<string[]>([]);
  const actionKeys = useRef(new Map<string, string>());

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const organization = await managerBusinessService.organization(signal);
      const result = await capacityService.getCapacity(organization.organization_id, signal);
      if (!signal?.aborted) {
        setPageData({ organization, capacity: result.data });
        setError("");
      }
    } catch (cause) {
      if (!signal?.aborted) {
        setPageData(null);
        setError(emptyCapacityMessage(cause));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const refresh = () => {
    setLoading(true);
    setError("");
    setCommandError("");
    setNotice("");
    void load();
  };

  const clearActionKeys = () => actionKeys.current.clear();
  const data = pageData?.capacity ?? null;
  const organization = pageData?.organization ?? null;
  const hasSubscription = Boolean(data?.subscription_id && data.subscription_state !== "NONE");
  const canManageRenewal = data?.subscription_state === "ACTIVE" || data?.subscription_state === "GRACE";
  const canResumeRenewal = data?.subscription_state === "CANCEL_AT_PERIOD_END";

  const activeAddonValue = addonSlots.trim() !== "" && /^\d+$/.test(addonSlots) ? Number(addonSlots) : null;
  const targetCapacity = activeAddonValue === null ? null : 10 + activeAddonValue;
  const validDowngrade = Boolean(
    data
    && activeAddonValue !== null
    && activeAddonValue <= 1000
    && targetCapacity !== null
    && targetCapacity < data.capacity,
  );
  const classesToSuspend = validDowngrade && data && targetCapacity !== null
    ? Math.max(0, data.active_class_count - targetCapacity)
    : 0;
  const hasEnoughClasses = classes.length >= (data?.active_class_count ?? 0);
  const exactSelection = selectedClassRefs.length === classesToSuspend;

  const loadActiveClasses = async () => {
    setLoadingClasses(true);
    setClassLoadError("");
    try {
      const result = await classService.listClasses("active");
      setClasses(result.filter((item) => item.state === "active"));
    } catch {
      setClassLoadError("Không tải được danh sách lớp. Hãy thử lại.");
    } finally {
      setLoadingClasses(false);
    }
  };

  const openDowngrade = () => {
    if (!data) return;
    setAddonSlots(String(Math.max(0, Math.min(1000, data.capacity - 11))));
    setSelectedClassRefs([]);
    setClasses([]);
    setClassLoadError("");
    setCommandError("");
    setNotice("");
    setConfirmAction(null);
    setDowngradeOpen(true);
    clearActionKeys();
    void loadActiveClasses();
  };

  const reloadAfterStale = async () => {
    setConfirmAction(null);
    setDowngradeOpen(false);
    setClasses([]);
    setSelectedClassRefs([]);
    setLoading(true);
    setError("");
    await load();
    setCommandError("Thông tin sức chứa đã thay đổi. Hãy xem lại trước khi xác nhận.");
  };

  const configure = async (action: "cancel_renewal" | "resume_renewal" | "downgrade") => {
    if (!data || !organization || busy) return;
    let body: CapacityCommand;
    let signature: string;
    if (action === "downgrade") {
      if (!validDowngrade || !exactSelection || !hasEnoughClasses || activeAddonValue === null) return;
      const refs = classes.filter((item) => selectedClassRefs.includes(item.class_id)).map((item) => item.class_id);
      body = { action, addon_slots: activeAddonValue, suspend_class_refs: refs };
      signature = "downgrade:" + JSON.stringify([activeAddonValue, refs]);
    } else {
      body = { action };
      signature = action;
    }
    const key = actionKeys.current.get(signature) ?? createIdempotencyKey();
    actionKeys.current.set(signature, key);
    setBusy(true);
    setCommandError("");
    setNotice("");
    try {
      const result = await capacityService.configureCapacity(organization.organization_id, data.revision, body, key);
      actionKeys.current.delete(signature);
      setPageData((current) => current ? { ...current, capacity: result.data } : current);
      setConfirmAction(null);
      setDowngradeOpen(false);
      setSelectedClassRefs([]);
      setNotice(action === "cancel_renewal"
        ? "Đã tắt gia hạn. Gói hiện tại còn hiệu lực đến hết kỳ."
        : action === "resume_renewal"
          ? "Đã bật lại gia hạn cho kỳ tiếp theo."
          : "Đã lên lịch hạ sức chứa vào cuối kỳ.");
    } catch (cause) {
      if (cause instanceof AdminBe1Error && cause.status >= 400 && cause.status < 500) {
        actionKeys.current.delete(signature);
      }
      if (cause instanceof AdminBe1Error && cause.code === "STALE_REVISION") {
        actionKeys.current.delete(signature);
        await reloadAfterStale();
      } else {
        setCommandError(errorText(cause));
      }
    } finally {
      setBusy(false);
    }
  };

  const toggleClass = (classId: string, checked: boolean) => {
    clearActionKeys();
    setCommandError("");
    setNotice("");
    setConfirmAction(null);
    setSelectedClassRefs((current) => checked
      ? current.includes(classId) || current.length >= classesToSuspend ? current : [...current, classId]
      : current.filter((item) => item !== classId));
  };

  const updateAddonSlots = (value: string) => {
    clearActionKeys();
    setCommandError("");
    setNotice("");
    setConfirmAction(null);
    setSelectedClassRefs([]);
    setAddonSlots(value);
  };

  return (
    <div className="s2l-page manager-business-page manager-capacity-page">
      <PageHeading
        eyebrow="School Manager · BE1"
        title="Sức chứa lớp"
        description={organization?.display_name ?? "Theo dõi sức chứa và trạng thái gói của trường."}
        action={<button type="button" className="manager-business-button" onClick={refresh} disabled={loading || busy}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>}
      />

      {error && <section className="manager-quota-alert" role="alert"><strong>Không tải được sức chứa</strong><span>{error}</span><button type="button" onClick={refresh} disabled={loading}>Thử lại</button></section>}
      {commandError && <p className="manager-business-alert" role="alert">{commandError}</p>}
      {notice && <p className="manager-quota-notice" role="status">{notice}</p>}
      {loading && !data && !error && <section className="manager-business-card" role="status">Đang tải sức chứa của trường…</section>}

      {data && <>
        <section className="manager-quota-stats" aria-label="Tổng quan sức chứa">
          <article><span>Sức chứa hiện tại</span><strong>{number(data.capacity)}</strong><small>lớp</small></article>
          <article><span>Lớp đang hoạt động</span><strong>{number(data.active_class_count)}</strong><small>lớp</small></article>
          <article><span>Còn chỗ</span><strong>{number(data.available_slots)}</strong><small>lớp</small></article>
          <article><span>Trạng thái gói</span><strong>{subscriptionLabel(data.subscription_state)}</strong></article>
        </section>

        <section className="manager-business-card manager-quota-section">
          <div className="manager-business-card-heading">
            <div><p className="manager-business-eyebrow">Kỳ sức chứa</p><h2><Gauge size={18} />Thông tin gói</h2></div>
            <span className={hasSubscription ? "manager-business-chip" : "manager-business-chip is-pending"}>{subscriptionLabel(data.subscription_state)}</span>
          </div>
          <dl className="s2l-class-details">
            <div><dt>Bắt đầu kỳ</dt><dd>{formatDate(data.period_start)}</dd></div>
            <div><dt>Kết thúc kỳ</dt><dd>{formatDate(data.period_end)}</dd></div>
          </dl>
          {!hasSubscription && <div className="manager-quota-empty">Trường chưa có gói sức chứa. Sức chứa mặc định gồm 10 lớp.</div>}
        </section>

        {data.scheduled_change && <section className="manager-business-card manager-quota-section" aria-label="Thay đổi đã lên lịch">
          <div className="manager-business-card-heading"><div><p className="manager-business-eyebrow">Đã lên lịch</p><h2>Hạ sức chứa vào cuối kỳ</h2></div></div>
          <dl className="s2l-class-details">
            <div><dt>Sức chứa mới</dt><dd>{number(data.scheduled_change.capacity)} lớp</dd></div>
            <div><dt>Slot bổ sung</dt><dd>{number(data.scheduled_change.addon_slots)}</dd></div>
            <div><dt>Thời điểm áp dụng</dt><dd>{formatDate(data.scheduled_change.effective_at, true)}</dd></div>
            <div><dt>Lớp sẽ tạm ngưng</dt><dd>{number(data.scheduled_change.suspend_class_refs.length)} lớp</dd></div>
          </dl>
        </section>}

        {hasSubscription && <section className="manager-business-card manager-quota-section">
          <div className="manager-business-card-heading"><div><p className="manager-business-eyebrow">Thao tác gói</p><h2>Quản lý gia hạn và sức chứa</h2></div></div>
          {canManageRenewal && <div className="cozy-form-actions" style={{ marginTop: 0 }}>
            <Button type="button" variant="secondary" disabled={busy || loading} onClick={() => { setConfirmAction("cancel_renewal"); setCommandError(""); }}>
              Tắt gia hạn
            </Button>
            <Button type="button" variant="secondary" disabled={busy || loading || data.capacity <= 10} onClick={openDowngrade}>
              Lên lịch hạ sức chứa
            </Button>
          </div>}
          {canResumeRenewal && <Button type="button" variant="primary" disabled={busy || loading} onClick={() => void configure("resume_renewal")}>
            {busy ? "Đang cập nhật…" : "Bật lại gia hạn"}
          </Button>}

          {confirmAction === "cancel_renewal" && <div className="cozy-form-section cozy-form-stack" role="group" aria-labelledby="capacity-cancel-confirm">
            <p id="capacity-cancel-confirm" className="manager-business-subtle" style={{ marginTop: 0 }}>
              Gói hiện tại vẫn có hiệu lực đến hết kỳ. Xác nhận tắt gia hạn cho kỳ tiếp theo?
            </p>
            <div className="cozy-form-actions" style={{ marginTop: 0 }}>
              <Button type="button" variant="secondary" disabled={busy} onClick={() => setConfirmAction(null)}>Để sau</Button>
              <Button type="button" variant="primary" loading={busy} disabled={busy} onClick={() => void configure("cancel_renewal")}>
                {busy ? "Đang gửi…" : "Xác nhận tắt gia hạn"}
              </Button>
            </div>
          </div>}

          {downgradeOpen && <div className="cozy-form-section cozy-form-stack" aria-labelledby="capacity-downgrade-heading">
            <h3 id="capacity-downgrade-heading">Chọn sức chứa mới</h3>
            <label htmlFor="capacity-addon-slots">Số slot bổ sung sau khi hạ</label>
            <input
              id="capacity-addon-slots"
              className="cozy-input"
              type="number"
              min={0}
              max={Math.min(1000, data.capacity - 11)}
              step={1}
              value={addonSlots}
              disabled={busy || loadingClasses}
              onChange={(event) => updateAddonSlots(event.target.value)}
            />
            {data.capacity <= 10 && <p className="manager-business-subtle">Sức chứa không thể thấp hơn 10 lớp.</p>}
            {validDowngrade && <p className="manager-business-subtle">
              Sức chứa mới là {number(targetCapacity ?? 10)} lớp. Chọn đúng {number(classesToSuspend)} lớp cần tạm ngưng.
            </p>}
            {classLoadError && <p className="manager-business-alert" role="alert">{classLoadError}</p>}
            {loadingClasses && <p role="status">Đang tải danh sách lớp…</p>}
            {!loadingClasses && !classLoadError && !hasEnoughClasses && <p className="manager-business-alert" role="alert">
              Danh sách lớp đang hoạt động chưa đầy đủ. Hãy tải lại danh sách trước khi tiếp tục.
            </p>}
            {!loadingClasses && !classLoadError && classes.length > 0 && validDowngrade && <fieldset className="manager-quota-product">
              <legend>Lớp đang hoạt động</legend>
              {classes.map((item) => {
                const checked = selectedClassRefs.includes(item.class_id);
                return <label key={item.class_id} className="cozy-form-inline-action">
                  <input
                    type="checkbox"
                    checked={checked}
                    aria-label={"Tạm ngưng lớp " + item.display_name}
                    disabled={busy || classesToSuspend === 0 || (!checked && selectedClassRefs.length >= classesToSuspend)}
                    onChange={(event) => toggleClass(item.class_id, event.target.checked)}
                  />
                  {item.display_name}
                </label>;
              })}
            </fieldset>}
            {confirmAction === "downgrade" && <div className="cozy-form-section cozy-form-stack" role="group" aria-labelledby="capacity-downgrade-confirm">
              <p id="capacity-downgrade-confirm" className="manager-business-subtle" style={{ marginTop: 0 }}>
                Sức chứa sẽ giảm xuống {number(targetCapacity ?? 10)} lớp vào cuối kỳ ({formatDate(data.period_end)}). {number(selectedClassRefs.length)} lớp đã chọn sẽ tạm ngưng khi thay đổi có hiệu lực.
              </p>
              <div className="cozy-form-actions" style={{ marginTop: 0 }}>
                <Button type="button" variant="secondary" disabled={busy} onClick={() => setConfirmAction(null)}>Sửa lựa chọn</Button>
                <Button type="button" variant="primary" loading={busy} disabled={busy || !validDowngrade || !hasEnoughClasses || !exactSelection} onClick={() => void configure("downgrade")}>
                  {busy ? "Đang gửi…" : "Xác nhận hạ sức chứa"}
                </Button>
              </div>
            </div>}
            {classLoadError && <Button type="button" variant="secondary" disabled={loadingClasses || busy} onClick={() => void loadActiveClasses()}>Tải lại danh sách lớp</Button>}
            {!confirmAction && <div className="cozy-form-actions" style={{ marginTop: 0 }}>
              <Button type="button" variant="secondary" disabled={busy} onClick={() => { setDowngradeOpen(false); setSelectedClassRefs([]); clearActionKeys(); }}>Hủy</Button>
              <Button
                type="button"
                variant="primary"
                disabled={busy || loadingClasses || Boolean(classLoadError) || !validDowngrade || !hasEnoughClasses || !exactSelection}
                onClick={() => { setConfirmAction("downgrade"); setCommandError(""); }}
              >
                Xem lại thay đổi
              </Button>
            </div>}
          </div>}

          {!canManageRenewal && !canResumeRenewal && <p className="manager-business-subtle">Thao tác gói hiện chưa khả dụng.</p>}
        </section>}

      </>}
    </div>
  );
}

export default CapacityPage;
