import { useState, type ChangeEvent, type FormEvent } from "react";
import {
  type SvgCatalogAssetCreateRequestV1,
  type SvgCatalogAssetResponseV1,
  type SvgDocumentV1,
} from "../../../shared/api/teacherSvgCatalogApi";
import { Button, FormField, StatusBadge } from "../../../shared/ui";
import { FormActionBar } from "./FormActionBar";
import { teacherStatusMeta } from "../services/teacherStatus";

const MAX_SOURCE_CHARS = 1_000_000;
const TOPIC_KEY = /^[a-z0-9-]+$/;

const cardStyle = {
  border: "1px solid var(--s2l-ui-rule)",
  borderRadius: 18,
  padding: 16,
  background: "var(--s2l-ui-paper)",
  color: "var(--s2l-ui-ink)",
};

export function validateSvgAssetInput(input: Omit<SvgCatalogAssetCreateRequestV1, "contract">): string | null {
  if (input.title_vi.trim().length < 1 || input.title_vi.trim().length > 300) return "Tên SVG cần có từ 1 đến 300 ký tự.";
  if (input.topic_key.trim().length < 1 || input.topic_key.trim().length > 120 || !TOPIC_KEY.test(input.topic_key.trim())) {
    return "Chủ đề dùng 1–120 ký tự thường, số hoặc dấu gạch ngang.";
  }
  if (input.alt_text_vi.trim().length < 1 || input.alt_text_vi.trim().length > 500) return "Mô tả thay thế cần có từ 1 đến 500 ký tự.";
  if (input.source_uri.trim().length < 1 || input.source_uri.length > 2048 || !isHttpsUrl(input.source_uri)) {
    return "Liên kết nguồn phải là URL HTTPS hợp lệ, tối đa 2.048 ký tự.";
  }
  if (input.license_id.trim().length < 1 || input.license_id.trim().length > 120) return "Mã giấy phép cần có từ 1 đến 120 ký tự.";
  if (!isHttpsUrl(input.license_uri)) return "Liên kết giấy phép phải là URL HTTPS hợp lệ.";
  if (input.source_svg.length < 1 || input.source_svg.length > MAX_SOURCE_CHARS) return "SVG nguồn cần có từ 1 đến 1.000.000 ký tự.";
  return null;
}

function isHttpsUrl(value: string): boolean {
  try {
    return new URL(value.trim()).protocol === "https:";
  } catch {
    return false;
  }
}

function AssetPreview({ document, title }: { document: SvgDocumentV1 | null; title: string }) {
  if (!document || !document.view_box || document.paths.length === 0) {
    return <div style={{ ...cardStyle, border: 0, minHeight: 96, display: "grid", placeItems: "center", color: "var(--s2l-ui-ink-soft)", background: "var(--s2l-ui-paper-muted)" }}>Chưa có bản xem trước nét SVG.</div>;
  }
  return (
    <div style={{ ...cardStyle, border: 0, display: "grid", placeItems: "center", minHeight: 112, padding: 12, background: "var(--s2l-ui-paper-muted)" }}>
      <svg viewBox={document.view_box} role="img" aria-label={"Bản xem trước: " + title} style={{ width: "100%", maxWidth: 250, height: 120 }}>
        {document.paths.map((path) => (
          <path
            key={path.path_id}
            d={path.d}
            fill={path.fill ?? "none"}
            stroke={path.stroke ?? "currentColor"}
            strokeWidth={path.stroke_width ?? 1}
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
    </div>
  );
}

interface AssetForm {
  title_vi: string;
  topic_key: string;
  alt_text_vi: string;
  source_uri: string;
  license_id: string;
  license_uri: string;
  source_svg: string;
}

const emptyForm: AssetForm = {
  title_vi: "",
  topic_key: "",
  alt_text_vi: "",
  source_uri: "",
  license_id: "",
  license_uri: "",
  source_svg: "",
};

export interface SvgAssetListProps {
  assets: SvgCatalogAssetResponseV1[];
  selectedAssetId: string | null;
  onSelect: (asset: SvgCatalogAssetResponseV1) => void;
  onCreate: (body: SvgCatalogAssetCreateRequestV1) => Promise<void>;
  creating?: boolean;
}

export function SvgAssetList({ assets, selectedAssetId, onSelect, onCreate, creating = false }: SvgAssetListProps) {
  const [form, setForm] = useState<AssetForm>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update(field: keyof AssetForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setError(null);
  }

  async function readSvgFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".svg") && file.type !== "image/svg+xml") {
      setError("Hãy chọn một tệp SVG.");
      event.currentTarget.value = "";
      return;
    }
    try {
      const contents = await file.text();
      if (contents.length > MAX_SOURCE_CHARS) {
        setError("SVG nguồn vượt quá giới hạn 1.000.000 ký tự.");
        return;
      }
      update("source_svg", contents);
    } catch {
      setError("Không thể đọc tệp SVG. Hãy chọn lại tệp.");
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = {
      ...form,
      title_vi: form.title_vi.trim(),
      topic_key: form.topic_key.trim(),
      alt_text_vi: form.alt_text_vi.trim(),
      source_uri: form.source_uri.trim(),
      license_id: form.license_id.trim(),
      license_uri: form.license_uri.trim(),
    };
    const validation = validateSvgAssetInput(normalized);
    if (validation) {
      setError(validation);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onCreate({ contract: "SvgCatalogAssetCreateRequestV1", ...normalized });
      setForm(emptyForm);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể tạo SVG lúc này.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="svg-assets-heading" style={{ display: "grid", gap: 14 }}>
      <div>
        <h2 id="svg-assets-heading" style={{ margin: 0, fontSize: 22 }}>SVG hiện có</h2>
      </div>
      {assets.length === 0 ? (
        <p style={{ ...cardStyle, margin: 0, padding: 20, border: "1px dashed var(--s2l-ui-rule)", background: "var(--s2l-ui-paper-muted)", color: "var(--s2l-ui-ink-soft)", lineHeight: 1.55, textAlign: "center" }}>Chưa có hình vẽ SVG nào. Thêm hình vẽ nguồn bằng biểu mẫu bên dưới.</p>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {assets.map((asset) => {
            const readinessMeta = teacherStatusMeta(asset.readiness);
            const selected = asset.catalog_entry_id === selectedAssetId;
            return (
              <article
                key={asset.catalog_entry_id}
                style={{
                  ...cardStyle,
                  display: "grid",
                  gap: 11,
                  borderColor: selected ? "var(--s2l-ui-primary-400)" : "var(--s2l-ui-rule)",
                  boxShadow: selected ? "0 0 0 2px var(--s2l-ui-primary-soft)" : undefined,
                }}
              >
                <button
                  type="button"
                  aria-pressed={selected}
                  onClick={() => onSelect(asset)}
                  style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "start", width: "100%", padding: 0, border: 0, background: "transparent", color: "inherit", textAlign: "left", cursor: "pointer" }}
                >
                  <span>
                    <strong style={{ display: "block", fontSize: 17 }}>{asset.title_vi}</strong>
                    <small style={{ display: "block", marginTop: 3, color: "var(--s2l-ui-ink-soft)" }}>Chủ đề: {asset.topic_key}</small>
                  </span>
                  <span aria-hidden="true" style={{ color: "var(--s2l-ui-ink-soft)" }}>›</span>
                </button>
                <span style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                  <StatusBadge tone={readinessMeta.tone}>{readinessMeta.label}</StatusBadge>
                </span>
                <AssetPreview document={asset.document} title={asset.title_vi} />
              </article>
            );
          })}
        </div>
      )}

      <details className="tw-card tp-collapsible tp-form-column" style={{ padding: 20 }}>
        <summary style={{ cursor: "pointer", fontSize: 16, fontWeight: 750, minHeight: 28 }}>Thêm SVG cho tổ chức</summary>
        <form onSubmit={(event) => void submit(event)} className="cozy-form-stack" style={{ paddingTop: 16, marginTop: 12, borderTop: "1px solid var(--s2l-ui-rule)" }}>
          <section className="cozy-form-stack">
            <div className="tp-form-section-intro">
              <h3>1. Nội dung</h3>
            </div>
            <div className="cozy-form-grid">
              <div className="cozy-span-3">
                <FormField label="Tên tiếng Việt" htmlFor="svg-asset-title" required>
                  <input id="svg-asset-title" className="cozy-input" required maxLength={300} value={form.title_vi} onChange={(event) => update("title_vi", event.currentTarget.value)} />
                </FormField>
              </div>
              <div className="cozy-span-3">
                <FormField label="Mã chủ đề" htmlFor="svg-asset-topic" required help="Chữ thường, số và dấu gạch ngang. Ví dụ: dong-vat">
                  <input id="svg-asset-topic" className="cozy-input" required maxLength={120} pattern="[a-z0-9\-]+" value={form.topic_key} onChange={(event) => update("topic_key", event.currentTarget.value)} />
                </FormField>
              </div>
              <div className="cozy-span-6">
                <FormField label="Mô tả thay thế" htmlFor="svg-asset-alt" required>
                  <textarea id="svg-asset-alt" className="cozy-textarea" rows={3} required maxLength={500} value={form.alt_text_vi} onChange={(event) => update("alt_text_vi", event.currentTarget.value)} />
                </FormField>
              </div>
            </div>
          </section>

          <section className="cozy-form-stack">
            <div className="tp-form-section-intro">
              <h3>2. Nguồn và giấy phép</h3>
            </div>
            <div className="cozy-form-grid">
              <div className="cozy-span-6">
                <FormField label="Liên kết nguồn HTTPS" htmlFor="svg-asset-source-uri" required>
                  <input id="svg-asset-source-uri" className="cozy-input" required type="url" value={form.source_uri} onChange={(event) => update("source_uri", event.currentTarget.value)} />
                </FormField>
              </div>
              <div className="cozy-span-3">
                <FormField label="Mã giấy phép" htmlFor="svg-asset-license-id" required>
                  <input id="svg-asset-license-id" className="cozy-input" required maxLength={120} value={form.license_id} onChange={(event) => update("license_id", event.currentTarget.value)} />
                </FormField>
              </div>
              <div className="cozy-span-3">
                <FormField label="Liên kết giấy phép HTTPS" htmlFor="svg-asset-license-uri" required>
                  <input id="svg-asset-license-uri" className="cozy-input" required type="url" value={form.license_uri} onChange={(event) => update("license_uri", event.currentTarget.value)} />
                </FormField>
              </div>
            </div>
          </section>

          <section className="cozy-form-stack">
            <div className="tp-form-section-intro">
              <h3>3. Tệp</h3>
            </div>
            <div className="cozy-form-grid">
              <div className="teacher-file-field cozy-span-6">
                <span className="cozy-form-label">Chọn tệp SVG</span>
                <label className="teacher-file-picker">
                  <span className="teacher-file-picker-button">Chọn tệp SVG</span>
                  <span className="teacher-file-picker-name">{form.source_svg ? "Đã chọn tệp SVG" : "Chưa chọn tệp"}</span>
                  <input className="teacher-file-picker-input" type="file" accept=".svg,image/svg+xml" onChange={(event) => void readSvgFile(event)} />
                </label>
              </div>
              <div className="cozy-span-6">
                <FormField label="Hoặc dán SVG nguồn (tối đa 1.000.000 ký tự)" htmlFor="svg-asset-source-svg" required>
                  <textarea
                    id="svg-asset-source-svg"
                    className="cozy-textarea"
                    rows={4}
                    required
                    maxLength={MAX_SOURCE_CHARS}
                    value={form.source_svg}
                    onChange={(event) => update("source_svg", event.currentTarget.value)}
                    style={{ fontFamily: "ui-monospace, monospace", fontSize: 12 }}
                  />
                </FormField>
              </div>
            </div>
          </section>

          {error && <p role="alert" className="s2l-alert" style={{ margin: 0 }}>{error}</p>}
          <FormActionBar>
            <Button type="submit" variant="primary" disabled={busy || creating}>
              {busy || creating ? "Đang tạo…" : "Tạo SVG"}
            </Button>
          </FormActionBar>
        </form>
      </details>
    </section>
  );
}
