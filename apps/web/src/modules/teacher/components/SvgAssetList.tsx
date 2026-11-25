import { useState, type ChangeEvent, type FormEvent } from "react";
import {
  type SvgCatalogAssetCreateRequestV1,
  type SvgCatalogAssetResponseV1,
  type SvgDocumentV1,
} from "../../../shared/api/teacherSvgCatalogApi";

const MAX_SOURCE_CHARS = 1_000_000;
const TOPIC_KEY = /^[a-z0-9-]+$/;

const readinessLabels: Record<string, string> = {
  STROKE_READY: "Có thể tạo hướng dẫn",
  REQUIRES_MANUAL_AUTHORING: "Cần biên soạn thủ công",
  STATIC_ONLY: "Chỉ có hình tĩnh",
};

const reviewLabels: Record<string, string> = {
  PENDING_EDUCATOR_REVIEW: "Chờ giáo viên duyệt",
  PENDING_CURATOR_REVIEW: "Chờ quản trị nội dung",
  APPROVED: "Đã duyệt",
  REJECTED: "Đã từ chối",
  ARCHIVED: "Đã lưu trữ",
};

const fieldStyle = {
  display: "grid",
  gap: 6,
  color: "#303a31",
  fontSize: 14,
} as const;

const inputStyle = {
  width: "100%",
  boxSizing: "border-box" as const,
  border: "1px solid #cbd5cb",
  borderRadius: 10,
  padding: "10px 12px",
  font: "inherit",
  color: "#263229",
  background: "#fff",
};

const cardStyle = {
  border: "1px solid #d7dfd6",
  borderRadius: 16,
  padding: 16,
  background: "#fff",
  color: "#28342b",
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

function chipStyle(tone: "green" | "amber" | "red" | "neutral") {
  const colors = {
    green: { color: "#1f5b3d", background: "#e8f4eb", borderColor: "#b8d8c0" },
    amber: { color: "#72510c", background: "#fff5d9", borderColor: "#ead99c" },
    red: { color: "#8b3131", background: "#fceaea", borderColor: "#e6bcbc" },
    neutral: { color: "#4c574e", background: "#f0f3f0", borderColor: "#d7dfd6" },
  }[tone];
  return {
    display: "inline-flex",
    alignItems: "center",
    border: "1px solid " + colors.borderColor,
    borderRadius: 999,
    padding: "4px 9px",
    fontSize: 12,
    fontWeight: 650,
    color: colors.color,
    background: colors.background,
  } as const;
}

function readinessTone(value: string): "green" | "amber" | "neutral" {
  if (value === "STROKE_READY") return "green";
  if (value === "REQUIRES_MANUAL_AUTHORING") return "amber";
  return "neutral";
}

function reviewTone(value: string): "green" | "amber" | "red" | "neutral" {
  if (value === "APPROVED") return "green";
  if (value.startsWith("PENDING")) return "amber";
  if (value === "REJECTED") return "red";
  return "neutral";
}

function AssetPreview({ document, title }: { document: SvgDocumentV1 | null; title: string }) {
  if (!document || !document.view_box || document.paths.length === 0) {
    return <div style={{ ...cardStyle, minHeight: 96, display: "grid", placeItems: "center", color: "#667268", background: "#f7f9f6" }}>Chưa có bản xem trước nét SVG.</div>;
  }
  return (
    <div style={{ ...cardStyle, display: "grid", placeItems: "center", minHeight: 112, padding: 12, background: "#f7f9f6" }}>
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
    const validation = validateSvgAssetInput(form);
    if (validation) {
      setError(validation);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onCreate({ contract: "SvgCatalogAssetCreateRequestV1", ...form });
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
        <p style={{ margin: "0 0 4px", color: "#607064", fontSize: 13, fontWeight: 700, letterSpacing: ".04em", textTransform: "uppercase" }}>Thư viện tổ chức</p>
        <h2 id="svg-assets-heading" style={{ margin: 0, fontSize: 22 }}>SVG trong tổ chức</h2>
      </div>
      {assets.length === 0 ? (
        <p style={{ ...cardStyle, margin: 0, color: "#647168" }}>Chưa có SVG nào trong phạm vi tổ chức.</p>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {assets.map((asset) => {
            const readiness = String(asset.readiness ?? "");
            const review = String(asset.review_state ?? "");
            const selected = asset.catalog_entry_id === selectedAssetId;
            return (
              <article
                key={asset.catalog_entry_id}
                style={{
                  ...cardStyle,
                  display: "grid",
                  gap: 11,
                  borderColor: selected ? "#4f8563" : "#d7dfd6",
                  boxShadow: selected ? "0 0 0 2px #d8ebdc" : undefined,
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
                    <small style={{ display: "block", marginTop: 3, color: "#647168" }}>Chủ đề: {asset.topic_key}</small>
                  </span>
                  <span aria-hidden="true" style={{ color: "#68806c" }}>›</span>
                </button>
                <span style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                  <span style={chipStyle(readinessTone(readiness))}>{readinessLabels[readiness] ?? (readiness || "Chưa rõ")}</span>
                  <span style={chipStyle(reviewTone(review))}>{reviewLabels[review] ?? (review || "Chưa rõ")}</span>
                </span>
                <AssetPreview document={asset.document} title={asset.title_vi} />
              </article>
            );
          })}
        </div>
      )}

      <details open style={cardStyle}>
        <summary style={{ cursor: "pointer", fontWeight: 700, marginBottom: 10 }}>Thêm SVG cho tổ chức</summary>
        <form onSubmit={(event) => void submit(event)} style={{ display: "grid", gap: 12, paddingTop: 8 }}>
          <label style={fieldStyle}>Tên tiếng Việt
            <input required maxLength={300} value={form.title_vi} onChange={(event) => update("title_vi", event.currentTarget.value)} style={inputStyle} />
          </label>
          <label style={fieldStyle}>Mã chủ đề
            <input required maxLength={120} pattern="[a-z0-9-]+" value={form.topic_key} onChange={(event) => update("topic_key", event.currentTarget.value)} style={inputStyle} placeholder="animals" />
          </label>
          <label style={fieldStyle}>Mô tả thay thế
            <textarea required maxLength={500} value={form.alt_text_vi} onChange={(event) => update("alt_text_vi", event.currentTarget.value)} style={{ ...inputStyle, minHeight: 74, resize: "vertical" }} />
          </label>
          <label style={fieldStyle}>Liên kết nguồn HTTPS
            <input required type="url" value={form.source_uri} onChange={(event) => update("source_uri", event.currentTarget.value)} style={inputStyle} placeholder="https://…" />
          </label>
          <label style={fieldStyle}>Mã giấy phép
            <input required maxLength={120} value={form.license_id} onChange={(event) => update("license_id", event.currentTarget.value)} style={inputStyle} />
          </label>
          <label style={fieldStyle}>Liên kết giấy phép HTTPS
            <input required type="url" value={form.license_uri} onChange={(event) => update("license_uri", event.currentTarget.value)} style={inputStyle} placeholder="https://…" />
          </label>
          <label style={fieldStyle}>Chọn tệp SVG
            <input type="file" accept=".svg,image/svg+xml" onChange={(event) => void readSvgFile(event)} />
          </label>
          <label style={fieldStyle}>Hoặc dán SVG nguồn (tối đa 1.000.000 ký tự)
            <textarea
              required
              maxLength={MAX_SOURCE_CHARS}
              value={form.source_svg}
              onChange={(event) => update("source_svg", event.currentTarget.value)}
              style={{ ...inputStyle, minHeight: 120, resize: "vertical", fontFamily: "ui-monospace, monospace", fontSize: 12 }}
            />
          </label>
          {error && <p role="alert" style={{ margin: 0, color: "#a23b37" }}>{error}</p>}
          <button type="submit" disabled={busy || creating} style={{ justifySelf: "start", border: 0, borderRadius: 999, padding: "10px 16px", background: "#315f42", color: "#fff", fontWeight: 700, cursor: "pointer" }}>
            {busy || creating ? "Đang tạo…" : "Tạo SVG"}
          </button>
        </form>
      </details>
    </section>
  );
}
