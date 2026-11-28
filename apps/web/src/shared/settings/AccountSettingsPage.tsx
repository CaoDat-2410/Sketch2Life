import { useCallback, useEffect, useState } from "react";
import { Alert, Button, Card, FormField, PageHeader, Section, Select, StatusBadge } from "../ui";
import { PageHeading } from "../components/FeatureAvailability";
import { BackendApiError, backendMessage } from "../api/backendApi";
import { getPreferences, updatePreferences, type AccountPreferences } from "../api/accountPreferencesApi";
import "./AccountSettingsPage.css";

type AccountSettingsRole = "Teacher" | "School Manager";

function PreferenceForm({
  isTeacher,
  value,
  saving,
  saveError,
  onSave,
}: {
  isTeacher: boolean;
  value: AccountPreferences;
  saving: boolean;
  saveError: string;
  onSave: (enabled: boolean) => void;
}) {
  const [enabled, setEnabled] = useState(value.email_notifications);
  const unchanged = enabled === value.email_notifications;
  const disabledHint = !saving && unchanged ? "Thay đổi lựa chọn ở trên để bật nút lưu." : null;

  return (
    <form
      className="cozy-form-stack"
      onSubmit={(event) => {
        event.preventDefault();
        onSave(enabled);
      }}
    >
      <FormField
        label="Thông báo qua email"
        htmlFor="account-email-notifications"
        help="Email bảo mật và thiết lập tài khoản vẫn được gửi."
      >
        <Select
          id="account-email-notifications"
          value={String(enabled)}
          disabled={saving}
          onChange={(event) => setEnabled(event.target.value === "true")}
        >
          <option value="true">Nhận thông báo</option>
          <option value="false">Tắt thông báo tùy chọn</option>
        </Select>
      </FormField>
      {saveError && <Alert tone="danger" role="alert">{saveError}</Alert>}
      {isTeacher ? (
        <div className="tp-form-action-bar">
          <div className="tp-form-action-bar-lead">
            {disabledHint && <p className="tp-form-action-hint">{disabledHint}</p>}
          </div>
          <div className="tp-form-action-bar-buttons">
            <Button
              type="submit"
              variant="primary"
              loading={saving}
              disabled={saving || unchanged}
            >
              Lưu tùy chọn
            </Button>
          </div>
        </div>
      ) : (
        <>
          {disabledHint && (
            <p className="cozy-form-disabled-hint">{disabledHint}</p>
          )}
          <div className="cozy-form-actions" style={{ marginTop: 0 }}>
            <Button
              type="submit"
              variant="primary"
              loading={saving}
              disabled={saving || unchanged}
            >
              Lưu tùy chọn
            </Button>
          </div>
        </>
      )}
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

  const isTeacher = role === "Teacher";
  const roleLabel = isTeacher ? "Giáo viên" : "Quản lý trường";

  return (
    <div className="s2l-page account-settings-page grid min-w-0 gap-6">
      {isTeacher ? (
        <PageHeading eyebrow="Tài khoản" title="Cài đặt" description="Quản lý thông báo cho tài khoản của bạn." />
      ) : (
        <PageHeader eyebrow={`${roleLabel.toLocaleUpperCase("vi-VN")} · CÀI ĐẶT`} title="Cài đặt" description="Quản lý thông báo cho tài khoản của bạn." />
      )}

      <div className="grid min-w-0 gap-3" aria-live={loadError ? "assertive" : "polite"} aria-atomic="true">
        {saved && <Alert tone="success">Đã lưu thay đổi.</Alert>}
        {loadError && <Alert tone="danger">{loadError}</Alert>}
      </div>

      <Card tone="subtle" className="w-full">
        <Section
          title="Thông báo cá nhân"
          variant="plain"
          actions={preferences && (saving || saved)
            ? <StatusBadge tone={saving ? "info" : "success"}>{saving ? "Đang lưu" : "Đã lưu"}</StatusBadge>
            : undefined}
        >
          {loading ? (
            <div className="grid min-w-0 gap-4" role="status" aria-label="Đang tải cài đặt" aria-busy="true">
              <span className="h-4 w-40 max-w-full animate-pulse rounded bg-neutral-soft" />
              <span className="h-11 w-full animate-pulse rounded-control bg-neutral-soft" />
              <span className="h-4 w-72 max-w-full animate-pulse rounded bg-neutral-soft" />
            </div>
          ) : preferences ? (
            <PreferenceForm key={preferences.revision} isTeacher={isTeacher} value={preferences} saving={saving} saveError={saveError} onSave={save} />
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
