import { useState, type FormEvent } from "react";
import type {
  CreateSvgGuideRevisionRequestV1,
  SketchStrokeGuidePartV3,
  SketchStrokeGuideStageV3,
  SketchStrokeGuideV3,
  SvgCatalogAssetResponseV1,
  SvgGuideRevisionReceiptV1,
} from "../../../shared/api/teacherSvgCatalogApi";
import { Button, FormField } from "../../../shared/ui";
import { FormActionBar } from "./FormActionBar";

const ID_PATTERN = /^[A-Za-z0-9._:-]{1,96}$/;

interface DraftStage {
  instruction_vi: string;
  new_path_ids: string[];
}

export function validateSvgGuideDraft(guide: SketchStrokeGuideV3, knownPathIds: string[]): string | null {
  const knownPaths = new Set(knownPathIds);
  if (!ID_PATTERN.test(guide.guide_id)) return "Mã hướng dẫn cần dùng chữ, số, dấu chấm, gạch dưới, hai chấm hoặc gạch ngang (tối đa 96 ký tự).";
  if (guide.title_vi.trim().length < 1 || guide.title_vi.length > 300) return "Tên hướng dẫn cần có từ 1 đến 300 ký tự.";
  if (!Number.isInteger(guide.source_asset_version) || guide.source_asset_version < 1) return "Phiên bản SVG nguồn chưa hợp lệ.";
  if (!/^[a-fA-F0-9]{64}$/.test(guide.source_sha256)) return "Mã SHA-256 của SVG nguồn chưa hợp lệ.";
  if (guide.parts.length < 1 || guide.parts.length > 64) return "Hướng dẫn cần có từ 1 đến 64 phần.";
  if (guide.stages.length < 4 || guide.stages.length > 8) return "Hướng dẫn cần có từ 4 đến 8 bước.";
  if (knownPathIds.length < 1) return "SVG chưa có nét để biên soạn hướng dẫn.";
  if (knownPathIds.length > 3200) return "Hướng dẫn hiện hỗ trợ tối đa 3.200 nét trong 8 bước.";

  const partIds = new Set<string>();
  const pathOwners = new Map<string, string>();
  for (const part of guide.parts) {
    if (!ID_PATTERN.test(part.part_id) || partIds.has(part.part_id)) return "Mã phần chưa hợp lệ hoặc bị trùng.";
    partIds.add(part.part_id);
    if (part.label_vi.trim().length < 1 || part.label_vi.length > 300) return "Mỗi phần cần có tên từ 1 đến 300 ký tự.";
    if (part.path_ids.length < 1 || part.path_ids.length > 400) return "Mỗi phần cần có từ 1 đến 400 nét.";
    if (part.depends_on.length > 64) return "Mỗi phần hỗ trợ tối đa 64 phụ thuộc.";
    if (new Set(part.path_ids).size !== part.path_ids.length) return "Một nét bị lặp trong cùng một phần.";
    for (const pathId of part.path_ids) {
      if (!ID_PATTERN.test(pathId) || !knownPaths.has(pathId)) return "Phần có mã nét không tồn tại trong SVG.";
      if (pathOwners.has(pathId)) return "Mỗi nét chỉ được thuộc về một phần.";
      pathOwners.set(pathId, part.part_id);
    }
  }
  for (const part of guide.parts) {
    if (new Set(part.depends_on).size !== part.depends_on.length) return "Danh sách phụ thuộc có mã bị lặp.";
    for (const dependency of part.depends_on) {
      if (!ID_PATTERN.test(dependency) || !partIds.has(dependency) || dependency === part.part_id) return "Phần tham chiếu một phụ thuộc không hợp lệ.";
    }
  }
  for (const pathId of knownPathIds) {
    if (!pathOwners.has(pathId)) return "Hãy thêm mọi nét của SVG vào một phần.";
  }

  const coveredPaths = new Set<string>();
  for (const [index, stage] of guide.stages.entries()) {
    if (stage.step_index !== index + 1) return "Các bước cần được đánh số liên tiếp từ 1.";
    if (stage.instruction_vi.trim().length < 1 || stage.instruction_vi.length > 500) return "Mỗi bước cần có hướng dẫn từ 1 đến 500 ký tự.";
    if (stage.part_ids.length < 1 || stage.part_ids.length > 64) return "Mỗi bước cần tham chiếu từ 1 đến 64 phần.";
    if (stage.new_path_ids.length < 1 || stage.new_path_ids.length > 400) return "Mỗi bước cần thêm từ 1 đến 400 nét mới.";
    if (stage.animation_order.length < 1 || stage.animation_order.length > 400) return "Thứ tự nét cần có từ 1 đến 400 mã.";
    if (new Set(stage.part_ids).size !== stage.part_ids.length || stage.part_ids.some((id) => !ID_PATTERN.test(id) || !partIds.has(id))) {
      return "Bước có tham chiếu một phần không tồn tại.";
    }
    if (new Set(stage.new_path_ids).size !== stage.new_path_ids.length) return "Một nét bị lặp trong bước.";
    for (const pathId of stage.new_path_ids) {
      const owner = pathOwners.get(pathId);
      if (!ID_PATTERN.test(pathId) || !knownPaths.has(pathId) || !owner) return "Bước có mã nét không tồn tại trong SVG.";
      if (!stage.part_ids.includes(owner)) return "Hãy chọn phần chứa các nét mới của mỗi bước.";
      if (coveredPaths.has(pathId)) return "Mỗi nét mới chỉ được giới thiệu một lần.";
      coveredPaths.add(pathId);
    }
    if (new Set(stage.animation_order).size !== stage.animation_order.length) return "Thứ tự nét có mã bị lặp.";
    if (stage.animation_order.some((id) => !ID_PATTERN.test(id) || !stage.new_path_ids.includes(id)) || stage.animation_order.length !== stage.new_path_ids.length) {
      return "Thứ tự nét cần chứa đúng các nét mới của bước.";
    }
  }
  if (coveredPaths.size !== knownPaths.size || [...knownPaths].some((pathId) => !coveredPaths.has(pathId))) {
    return "Các bước cần bao quát mọi nét của SVG.";
  }
  return null;
}

function initialParts(asset: SvgCatalogAssetResponseV1): SketchStrokeGuidePartV3[] {
  const paths = asset.document?.paths ?? [];
  const chunks: SketchStrokeGuidePartV3[] = [];
  for (let index = 0; index < paths.length && chunks.length < 64; index += 400) {
    const partNumber = chunks.length + 1;
    chunks.push({
      part_id: "part-" + partNumber,
      label_vi: "Nhóm " + partNumber,
      path_ids: paths.slice(index, index + 400).map((path) => path.path_id),
      depends_on: [],
    });
  }
  return chunks;
}

function emptyStage(): DraftStage {
  return { instruction_vi: "", new_path_ids: [] };
}

function inputError(cause: unknown): string {
  if (typeof cause === "object" && cause !== null && "code" in cause && cause.code === "SVG_GUIDE_SOURCE_MISMATCH") {
    return "Hướng dẫn cần gắn với đúng phiên bản và mã nguồn của SVG. Hãy tải lại dữ liệu rồi thử lại.";
  }
  return cause instanceof Error ? cause.message : "Không thể tạo hướng dẫn lúc này.";
}

export interface SvgGuideAuthoringProps {
  asset: SvgCatalogAssetResponseV1;
  onCreate: (body: CreateSvgGuideRevisionRequestV1) => Promise<SvgGuideRevisionReceiptV1>;
  onCreated?: (receipt: SvgGuideRevisionReceiptV1) => void;
}

export function SvgGuideAuthoring({ asset, onCreate, onCreated }: SvgGuideAuthoringProps) {
  const paths = asset.document?.paths ?? [];
  const pathIds = paths.map((path) => path.path_id);
  const [guideId, setGuideId] = useState(() => "guide-" + asset.catalog_entry_id.replace(/[^A-Za-z0-9._:-]/g, "-").slice(0, 86));
  const [title, setTitle] = useState(asset.title_vi);
  const [parts, setParts] = useState<SketchStrokeGuidePartV3[]>(() => initialParts(asset));
  const [stages, setStages] = useState<DraftStage[]>([emptyStage(), emptyStage(), emptyStage(), emptyStage()]);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<SvgGuideRevisionReceiptV1 | null>(null);
  const [busy, setBusy] = useState(false);

  function updatePart(index: number, patch: Partial<SketchStrokeGuidePartV3>) {
    setParts((current) => current.map((part, partIndex) => partIndex === index ? { ...part, ...patch } : part));
    setError(null);
  }

  function updateStage(index: number, patch: Partial<DraftStage>) {
    setStages((current) => current.map((stage, stageIndex) => stageIndex === index ? { ...stage, ...patch } : stage));
    setError(null);
  }

  function createGuide(): SketchStrokeGuideV3 {
    const ownerByPath = new Map<string, string>();
    parts.forEach((part) => part.path_ids.forEach((pathId) => ownerByPath.set(pathId, part.part_id)));
    const guideStages: SketchStrokeGuideStageV3[] = stages.map((stage, index) => ({
      step_index: index + 1,
      instruction_vi: stage.instruction_vi,
      part_ids: [...new Set(stage.new_path_ids.map((pathId) => ownerByPath.get(pathId)).filter((id): id is string => Boolean(id)))],
      new_path_ids: stage.new_path_ids,
      animation_order: stage.new_path_ids,
    }));
    return {
      schema_version: "SketchStrokeGuideV3",
      guide_id: guideId.trim(),
      title_vi: title.trim(),
      source_asset_ref: asset.source_asset_ref,
      source_asset_version: asset.source_asset_version,
      source_sha256: asset.source_sha256,
      parts: parts.map((part) => ({
        ...part,
        part_id: part.part_id.trim(),
        label_vi: part.label_vi.trim(),
        depends_on: part.depends_on.map((id) => id.trim()).filter(Boolean),
      })),
      stages: guideStages,
    };
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (asset.readiness !== "STROKE_READY") {
      setError("Chỉ có thể biên soạn hướng dẫn khi hình vẽ đã sẵn sàng tạo từng nét.");
      return;
    }
    const guide = createGuide();
    const validation = validateSvgGuideDraft(guide, pathIds);
    if (validation) {
      setError(validation);
      setCreated(null);
      return;
    }
    setBusy(true);
    setError(null);
    setCreated(null);
    try {
      const receipt = await onCreate({ contract: "CreateSvgGuideRevisionRequestV1", guide });
      setCreated(receipt);
      onCreated?.(receipt);
    } catch (cause) {
      setError(inputError(cause));
    } finally {
      setBusy(false);
    }
  }

  if (!asset.document || paths.length === 0) {
    return <section className="tp-form-column" style={panelStyle}><h3 style={{ margin: 0 }}>Biên soạn hướng dẫn</h3><p style={{ margin: 0 }}>Hình vẽ SVG chưa có nét để biên soạn hướng dẫn.</p></section>;
  }

  if (asset.readiness !== "STROKE_READY") {
    return <section className="tp-form-column" style={panelStyle}><h3 style={{ margin: 0 }}>Biên soạn hướng dẫn</h3><p role="status" style={{ margin: 0 }}>Hình vẽ hiện chưa sẵn sàng để biên soạn hướng dẫn vẽ theo từng nét.</p></section>;
  }

  return (
    <section aria-labelledby="svg-authoring-heading" className="tp-form-column" style={panelStyle}>
      <div>
        <h3 id="svg-authoring-heading" style={{ margin: 0, fontSize: 20 }}>Biên soạn hướng dẫn vẽ</h3>
        <p style={{ margin: "7px 0 0", color: "var(--s2l-ui-ink-soft)" }}>Khóa theo hình vẽ {asset.title_vi} · Phiên bản nguồn {asset.source_asset_version}.</p>
      </div>

      <form onSubmit={(event) => void submit(event)} className="cozy-form-stack">
        <div className="cozy-form-grid">
          <div className="cozy-span-3">
            <FormField label="Mã hướng dẫn" required>
              <input className="cozy-input" required maxLength={96} pattern="[A-Za-z0-9._:-]+" value={guideId} onChange={(event) => { setGuideId(event.currentTarget.value); setError(null); }} />
            </FormField>
          </div>
          <div className="cozy-span-3">
            <FormField label="Tên hướng dẫn" required>
              <input className="cozy-input" required maxLength={300} value={title} onChange={(event) => { setTitle(event.currentTarget.value); setError(null); }} />
            </FormField>
          </div>
        </div>

        <fieldset style={fieldsetStyle}>
          <legend style={legendStyle}>Các phần của hình</legend>
          <p style={{ margin: "0 0 10px", color: "var(--s2l-ui-ink-soft)", fontSize: 13 }}>Chia nét thành nhóm để hướng dẫn theo từng phần. Nét sẽ dùng thứ tự trong SVG khi trình bày.</p>
          <div style={{ display: "grid", gap: 12 }}>
            {parts.map((part, index) => (
              <article key={part.part_id} style={partCardStyle}>
                <div style={{ display: "grid", gridTemplateColumns: "minmax(100px, .7fr) minmax(120px, 1fr) auto", gap: 8, alignItems: "end" }}>
                  <FormField label="Mã phần">
                    <input className="cozy-input" maxLength={96} value={part.part_id} onChange={(event) => updatePart(index, { part_id: event.currentTarget.value })} />
                  </FormField>
                  <FormField label="Tên phần">
                    <input className="cozy-input" maxLength={300} value={part.label_vi} onChange={(event) => updatePart(index, { label_vi: event.currentTarget.value })} />
                  </FormField>
                  <Button type="button" variant="secondary" size="sm" className="tp-quiet-danger" disabled={parts.length <= 1} onClick={() => setParts((current) => current.filter((_, partIndex) => partIndex !== index))}>Xóa phần</Button>
                </div>
                <div style={{ marginTop: 10 }}>
                  <FormField label="Nét thuộc phần">
                    <select className="cozy-input" multiple size={Math.min(8, Math.max(4, paths.length))} value={part.path_ids} onChange={(event) => updatePart(index, { path_ids: [...event.currentTarget.selectedOptions].map((option) => option.value) })} style={{ minHeight: 110 }}>
                      {paths.map((path) => <option key={path.path_id} value={path.path_id}>{path.path_id}</option>)}
                    </select>
                  </FormField>
                </div>
                <div style={{ marginTop: 10 }}>
                  <FormField label="Phần phụ thuộc" labelAction="(không bắt buộc)" help="Nhập mã phần cách nhau bằng dấu phẩy. Ví dụ: part-1">
                    <input className="cozy-input" value={part.depends_on.join(", ")} onChange={(event) => updatePart(index, { depends_on: event.currentTarget.value.split(",") })} />
                  </FormField>
                </div>
              </article>
            ))}
          </div>
          <div style={{ marginTop: 10 }}>
            <Button type="button" variant="secondary" size="sm" disabled={parts.length >= 64} onClick={() => setParts((current) => [...current, { part_id: "part-" + (current.length + 1), label_vi: "Nhóm " + (current.length + 1), path_ids: [], depends_on: [] }])}>+ Thêm phần</Button>
          </div>
        </fieldset>

        <fieldset style={fieldsetStyle}>
          <legend style={legendStyle}>Các bước hướng dẫn</legend>
          <p style={{ margin: "0 0 10px", color: "var(--s2l-ui-ink-soft)", fontSize: 13 }}>Cần từ 4 đến 8 bước. Mỗi nét mới được giới thiệu một lần và hiển thị theo thứ tự nét đã chọn.</p>
          <div style={{ display: "grid", gap: 12 }}>
            {stages.map((stage, index) => (
              <article key={index} style={partCardStyle}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
                  <strong>Bước {index + 1}</strong>
                  <Button type="button" variant="secondary" size="sm" className="tp-quiet-danger" disabled={stages.length <= 4} onClick={() => setStages((current) => current.filter((_, stageIndex) => stageIndex !== index))}>Xóa bước</Button>
                </div>
                <div style={{ marginTop: 10 }}>
                  <FormField label="Hướng dẫn tiếng Việt" required>
                    <textarea className="cozy-textarea" rows={3} required maxLength={500} value={stage.instruction_vi} onChange={(event) => updateStage(index, { instruction_vi: event.currentTarget.value })} />
                  </FormField>
                </div>
                <div style={{ marginTop: 10 }}>
                  <FormField label="Nét mới ở bước này">
                    <select className="cozy-input" multiple size={Math.min(8, Math.max(4, paths.length))} value={stage.new_path_ids} onChange={(event) => updateStage(index, { new_path_ids: [...event.currentTarget.selectedOptions].map((option) => option.value) })} style={{ minHeight: 110 }}>
                      {paths.map((path) => <option key={path.path_id} value={path.path_id}>{path.path_id}</option>)}
                    </select>
                  </FormField>
                </div>
              </article>
            ))}
          </div>
          <div style={{ marginTop: 10 }}>
            <Button type="button" variant="secondary" size="sm" disabled={stages.length >= 8} onClick={() => setStages((current) => [...current, emptyStage()])}>+ Thêm bước</Button>
          </div>
        </fieldset>

        {error && <p role="alert" style={{ margin: 0, color: "#a23b37" }}>{error}</p>}
        {created && (
          <p role="status" className="tw-row tw-wrap" style={{ margin: 0, color: "var(--s2l-ui-primary-hover)", gap: 8 }}>
            <span>Đã tạo phiên bản {created.guide_revision}</span>
          </p>
        )}
        <FormActionBar>
          <Button type="submit" variant="primary" disabled={busy}>{busy ? "Đang lưu…" : "Lưu phiên bản hướng dẫn"}</Button>
        </FormActionBar>
      </form>
    </section>
  );
}

const panelStyle = {
  display: "grid",
  gap: 14,
  padding: 18,
  border: "1px solid var(--s2l-ui-rule)",
  borderRadius: 18,
  background: "var(--s2l-ui-paper)",
  color: "var(--s2l-ui-ink)",
};

const fieldsetStyle = {
  minWidth: 0,
  padding: "0 0 16px",
  border: 0,
  borderBottom: "1px solid var(--s2l-ui-rule)",
  borderRadius: 0,
};

const legendStyle = { display: "block", width: "100%", padding: "0 0 10px", fontWeight: 750, color: "var(--s2l-ui-ink)" };
const partCardStyle = { padding: "0 0 12px", border: 0, borderBottom: "1px solid var(--s2l-ui-rule)", borderRadius: 0, background: "transparent" };
