import { useCallback, useEffect, useState } from "react";
import { Alert, Button, Card, PageHeader, Section, Select, StatusBadge } from "../ui";
import { BackendApiError, backendMessage } from "../api/backendApi";
import { getPreferences, updatePreferences, type AccountPreferences } from "../api/accountPreferencesApi";
import "./AccountSettingsPage.css";

type AccountSettingsRole = "Teacher" | "School Manager";

function PreferenceForm({
  value,
  saving,
  onSave,
}: {
  value: AccountPreferences;
  saving: boolean;
  onSave: (enabled: boolean) => void;
}) {
  const [enabled, setEnabled] = useState(value.email_notifications);

  return (
    <form
      className="grid min-w-0 gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        onSave(enabled);
      }}
    >
      <div className="grid min-w-0 gap-2">
        <label htmlFor="account-email-notifications" className="font-ui text-sm font-semibold text-ink">
          Thông báo qua email
        </label>
        <Select
          id="account-email-notifications"
          value={String(enabled)}
          disabled={saving}
          onChange={(event) => setEnabled(event.target.value === "true")}
        >
          <option value="true">Nhận thông báo</option>
          <option value="false">Tắt thông báo tùy chọn</option>
        </Select>
        <p className="m-0 font-ui text-xs leading-5 text-ink-soft">
          Email bảo mật và thiết lập tài khoản vẫn được gửi.
        </p>
      </div>
      <div className="cozy-form-actions">
        <Button
          type="submit"
          variant="primary"
          loading={saving}
          disabled={saving || enabled === value.email_notifications}
          className="account-settings-save w-full sm:w-auto"
        >
          Lưu tùy chọn
        </Button>
      </div>
    </form>
  );
}

function isConflict(cause: unknown): boolean {
  return cause instanceof BackendApiError
    && (cause.status === 409 || cause.code === "STALE_SESSION_REVISION" || cause.code === "RESOURCE_CONFLICT");
}

export function AccountSettingsPage({ role }: { role: AccountSettingsRole }) {
  const [preferences, setPreferences] = useState<AccountPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saved, setSaved] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setPreferences(null);
    setLoadError("");
    setSaveError("");
    setSaved(false);
    try {
      setPreferences(await getPreferences());
    } catch (cause) {
      setLoadError(backendMessage(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const save = async (emailNotifications: boolean) => {
    if (!preferences) return;
    setSaving(true);
    setSaved(false);
    setSaveError("");
    try {
      const updated = await updatePreferences({
        locale: preferences.locale,
        email_notifications: emailNotifications,
        expected_revision: preferences.revision,
      });
      setPreferences(updated);
      setSaved(true);
    } catch (cause) {
      setSaveError(backendMessage(cause));
      if (isConflict(cause)) {
        setLoading(true);
        setPreferences(null);
        setLoadError("");
        try {
          setPreferences(await getPreferences());
        } catch (reloadCause) {
          setLoadError(backendMessage(reloadCause));
        } finally {
          setLoading(false);
        }
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="s2l-page account-settings-page grid min-w-0 gap-6">
      <PageHeader
        eyebrow={`${role.toUpperCase()} · CÀI ĐẶT`}
        title="Cài đặt"
        description="Quản lý thông báo cho tài khoản của bạn."
      />

      <div className="grid min-w-0 gap-3" aria-live={saveError || loadError ? "assertive" : "polite"} aria-atomic="true">
        {saved && <Alert tone="success">Đã lưu thay đổi.</Alert>}
        {saveError && <Alert tone="danger">{saveError}</Alert>}
        {loadError && <Alert tone="danger">{loadError}</Alert>}
      </div>

      <Card className="w-full max-w-3xl">
        <Section
          title="Thông báo cá nhân"
          variant="plain"
          actions={preferences ? <StatusBadge tone={saving ? "info" : saved ? "success" : "neutral"}>{saving ? "Đang lưu" : saved ? "Đã lưu" : "Đã tải"}</StatusBadge> : undefined}
        >
          {loading ? (
            <div className="grid min-w-0 gap-4" role="status" aria-label="Đang tải cài đặt" aria-busy="true">
              <span className="h-4 w-40 max-w-full animate-pulse rounded bg-neutral-soft" />
              <span className="h-11 w-full animate-pulse rounded-control bg-neutral-soft" />
              <span className="h-4 w-72 max-w-full animate-pulse rounded bg-neutral-soft" />
            </div>
          ) : preferences ? (
            <PreferenceForm key={preferences.revision} value={preferences} saving={saving} onSave={save} />
          ) : (
            <div className="grid min-w-0 gap-3">
              <p className="m-0 font-ui text-sm leading-6 text-ink-soft">Không tải được tùy chọn tài khoản.</p>
              <Button type="button" onClick={() => void reload()} disabled={loading} className="w-full sm:w-auto">
                Làm mới
              </Button>
            </div>
          )}
        </Section>
      </Card>
    </div>
  );
}
