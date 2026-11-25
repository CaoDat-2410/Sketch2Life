import { backendRequest } from "../../../shared/api/backendApi";

const ASSETS_PATH = "/api/svg-catalog/v1/platform/assets";
const HASH_PATTERN = /^[a-fA-F0-9]{64}$/;

export type SvgReadiness = "STROKE_READY" | "REQUIRES_MANUAL_AUTHORING" | "STATIC_ONLY";
export type SvgAssetReviewState =
  | "PENDING_EDUCATOR_REVIEW"
  | "PENDING_CURATOR_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "ARCHIVED";
export type SvgGuideReviewState = "PENDING" | "APPROVED" | "REJECTED";
export type SvgVisibilityScope = "PLATFORM" | "ORGANIZATION";

export interface SvgPathV1 {
  path_id: string;
  d: string;
  fill: string | null;
  stroke: string | null;
  stroke_width: number | null;
}

export interface SvgDocumentV1 {
  schema_version: string;
  view_box: string;
  paths: SvgPathV1[];
}

export interface SvgCatalogAssetCreateRequestV1 {
  contract: "SvgCatalogAssetCreateRequestV1";
  title_vi: string;
  topic_key: string;
  alt_text_vi: string;
  source_uri: string;
  license_id: string;
  license_uri: string;
  source_svg: string;
}

export interface SvgCatalogAssetResponseV1 {
  contract?: string;
  catalog_entry_id: string;
  source_asset_ref: string;
  source_asset_version: number;
  canonical_asset_ref: string;
  canonical_asset_version: number;
  source_sha256: string;
  canonical_sha256: string;
  topic_key: string;
  title_vi: string;
  alt_text_vi: string;
  source_uri: string;
  license_id: string;
  license_uri: string;
  visibility_scope: SvgVisibilityScope;
  organization_id: string | null;
  created_by: string;
  readiness: SvgReadiness;
  readiness_reasons: string[];
  structural_facts: Record<string, unknown>;
  review_state: SvgAssetReviewState;
  document: SvgDocumentV1 | null;
}

export interface SketchStrokeGuidePartV3 {
  part_id: string;
  label_vi: string;
  path_ids: string[];
  depends_on: string[];
}

export interface SketchStrokeGuideStageV3 {
  step_index: number;
  instruction_vi: string;
  part_ids: string[];
  new_path_ids: string[];
  animation_order: string[];
}

export interface SketchStrokeGuideV3 {
  schema_version: "SketchStrokeGuideV3";
  guide_id: string;
  title_vi: string;
  source_asset_ref: string;
  source_asset_version: number;
  source_sha256: string;
  parts: SketchStrokeGuidePartV3[];
  stages: SketchStrokeGuideStageV3[];
}

export interface CreateSvgGuideRevisionRequestV1 {
  contract: "CreateSvgGuideRevisionRequestV1";
  guide: SketchStrokeGuideV3;
}

export interface SvgGuideRevisionReceiptV1 {
  contract?: string;
  guide_revision_id: string;
  guide_ref: string;
  guide_revision: number;
  source_sha256: string;
  guide_sha256: string;
  guide: SketchStrokeGuideV3;
  authored_by: string;
  visibility_scope: SvgVisibilityScope;
  organization_id: string | null;
  review_state: SvgGuideReviewState;
}

export type SvgCurationDecision = "APPROVE" | "REJECT";
export interface SvgCurationRequestV1 {
  contract: "SvgCurationRequestV1";
  source_sha256: string;
  decision: SvgCurationDecision;
  grouping_allowed: boolean;
  reason?: string;
}

export interface SvgReviewReceiptV1 {
  contract?: string;
  review_id: string;
  catalog_entry_id: string;
  review_subject_kind: string;
  review_kind: "CURATOR";
  decision: SvgCurationDecision;
  source_sha256: string;
  guide_sha256: string | null;
  grouping_allowed: boolean;
  reviewer_ref: string;
  created_at: string;
}

const ERROR_MESSAGES: Record<string, string> = {
  FORBIDDEN: "Tài khoản hiện tại không có quyền quản trị nền tảng.",
  DEPENDENCY_UNAVAILABLE: "Dịch vụ lưu trữ chưa sẵn sàng. Vui lòng thử lại sau.",
  OBJECT_STORAGE_UNAVAILABLE: "Kho lưu trữ tệp chưa được cấu hình. Vui lòng liên hệ quản trị hệ thống.",
  SVG_PROVENANCE_URL_INVALID: "Đường dẫn nguồn phải là địa chỉ HTTPS hợp lệ.",
  SVG_SOURCE_INVALID: "Tệp SVG không hợp lệ hoặc không được hỗ trợ.",
  SVG_METADATA_INVALID: "Thông tin bản quyền hoặc mô tả SVG chưa hợp lệ.",
  SVG_GUIDE_SOURCE_MISMATCH: "Hướng dẫn phải dùng đúng phiên bản và mã nguồn của SVG đã chọn.",
  INDEPENDENT_CURATION_REQUIRED: "Người tạo SVG không thể tự duyệt nội dung này.",
  SVG_CATALOG_ITEM_NOT_FOUND: "Không tìm thấy mục SVG. Hãy kiểm tra mã mục đã nhập.",
  SVG_REVIEW_CONFLICT: "Mục SVG đã được duyệt hoặc từ chối trước đó.",
  SVG_REVIEW_SOURCE_STALE: "Nguồn SVG đã thay đổi. Hãy tải lại mã băm mới trước khi duyệt.",
  SVG_REVIEW_GUIDE_STALE: "Hướng dẫn SVG đã thay đổi. Hãy dùng phiên bản mới nhất.",
  SVG_GUIDE_REVISION_CONFLICT: "Phiên bản hướng dẫn đã thay đổi. Hãy gửi lại nội dung mới nhất.",
  SVG_ASSET_UNAVAILABLE: "Mục SVG hiện không thể sử dụng.",
};

function fail(message: string): never {
  throw new Error(message);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function requiredText(value: unknown, label: string, min: number, max: number): asserts value is string {
  if (typeof value !== "string" || value.trim().length < min || value.length > max) {
    fail(`${label} phải có từ ${min} đến ${max} ký tự.`);
  }
}

function httpsUrl(value: unknown, label: string, max = Number.MAX_SAFE_INTEGER): asserts value is string {
  requiredText(value, label, 1, max);
  try {
    if (new URL(value).protocol !== "https:") fail(`${label} phải dùng HTTPS.`);
  } catch {
    fail(`${label} phải là địa chỉ HTTPS hợp lệ.`);
  }
}

function hash(value: unknown, label: string): asserts value is string {
  if (typeof value !== "string" || !HASH_PATTERN.test(value)) {
    fail(`${label} phải gồm đúng 64 ký tự thập lục phân.`);
  }
}

function stringArray(value: unknown, label: string, max?: number, min = 0): asserts value is string[] {
  if (!Array.isArray(value) || value.length < min || (max !== undefined && value.length > max) || value.some((item) => typeof item !== "string")) {
    fail(`${label} chưa đúng định dạng.`);
  }
}

export function validateSvgAssetRequest(body: SvgCatalogAssetCreateRequestV1): void {
  if (!isRecord(body) || body.contract !== "SvgCatalogAssetCreateRequestV1") fail("Loại yêu cầu SVG không hợp lệ.");
  requiredText(body.title_vi, "Tiêu đề", 1, 300);
  requiredText(body.topic_key, "Chủ đề", 1, 120);
  if (!/^[a-z0-9-]+$/.test(body.topic_key)) fail("Mã chủ đề chỉ gồm chữ thường, số và dấu gạch ngang.");
  requiredText(body.alt_text_vi, "Văn bản thay thế", 1, 500);
  httpsUrl(body.source_uri, "Đường dẫn nguồn", 2048);
  requiredText(body.license_id, "Mã giấy phép", 1, 120);
  httpsUrl(body.license_uri, "Đường dẫn giấy phép");
  requiredText(body.source_svg, "Nội dung SVG", 1, 1_000_000);
}

export function validateSvgGuideRequest(body: CreateSvgGuideRevisionRequestV1): void {
  if (!isRecord(body) || body.contract !== "CreateSvgGuideRevisionRequestV1") fail("Loại yêu cầu hướng dẫn không hợp lệ.");
  const guideValue = body.guide;
  if (!isRecord(guideValue) || guideValue.schema_version !== "SketchStrokeGuideV3") fail("Phiên bản hướng dẫn không hợp lệ.");
  const guide = guideValue as unknown as SketchStrokeGuideV3;
  requiredText(guide.guide_id, "Mã hướng dẫn", 1, Number.MAX_SAFE_INTEGER);
  requiredText(guide.title_vi, "Tiêu đề hướng dẫn", 1, 300);
  requiredText(guide.source_asset_ref, "Mã nguồn SVG", 1, Number.MAX_SAFE_INTEGER);
  if (!Number.isInteger(guide.source_asset_version) || guide.source_asset_version < 1) fail("Phiên bản SVG phải từ 1 trở lên.");
  hash(guide.source_sha256, "Mã băm nguồn");
  if (!Array.isArray(guide.parts) || guide.parts.length < 1 || guide.parts.length > 64) fail("Hướng dẫn cần từ 1 đến 64 phần.");
  for (const part of guide.parts) {
    if (!isRecord(part)) fail("Một phần của hướng dẫn chưa đúng định dạng.");
    requiredText(part.part_id, "Mã phần", 1, Number.MAX_SAFE_INTEGER);
    requiredText(part.label_vi, "Tên phần", 1, Number.MAX_SAFE_INTEGER);
    stringArray(part.path_ids, "Danh sách nét", 400, 1);
    stringArray(part.depends_on, "Danh sách phần phụ thuộc", 64);
  }
  if (!Array.isArray(guide.stages) || guide.stages.length < 4 || guide.stages.length > 8) fail("Hướng dẫn cần từ 4 đến 8 bước.");
  for (const stage of guide.stages) {
    if (!isRecord(stage)) fail("Một bước của hướng dẫn chưa đúng định dạng.");
    if (!Number.isInteger(stage.step_index) || stage.step_index < 1 || stage.step_index > 8) fail("Số thứ tự bước phải từ 1 đến 8.");
    requiredText(stage.instruction_vi, "Hướng dẫn từng bước", 1, 500);
    stringArray(stage.part_ids, "Danh sách phần của bước");
    stringArray(stage.new_path_ids, "Danh sách nét mới");
    stringArray(stage.animation_order, "Thứ tự nét vẽ");
  }
}

export function validateSvgCurationRequest(body: SvgCurationRequestV1): void {
  if (!isRecord(body) || body.contract !== "SvgCurationRequestV1") fail("Loại yêu cầu duyệt SVG không hợp lệ.");
  hash(body.source_sha256, "Mã băm nguồn");
  if (body.decision !== "APPROVE" && body.decision !== "REJECT") fail("Quyết định duyệt không hợp lệ.");
  if (typeof body.grouping_allowed !== "boolean") fail("Cần chọn quyền nhóm nét.");
  if (body.decision === "REJECT" && (typeof body.reason !== "string" || !body.reason.trim())) fail("Cần nêu lý do khi từ chối.");
  if (body.reason !== undefined && (typeof body.reason !== "string" || body.reason.length > 1000)) fail("Lý do không được vượt quá 1000 ký tự.");
  if (body.decision === "REJECT" && body.grouping_allowed) fail("Chỉ được bật nhóm nét khi chấp thuận.");
}

function errorCode(error: unknown): string | undefined {
  if (!error || typeof error !== "object") return undefined;
  const value = error as { code?: unknown; detail?: { code?: unknown }; body?: { detail?: { code?: unknown } } };
  const code = value.code ?? value.detail?.code ?? value.body?.detail?.code;
  return typeof code === "string" ? code : undefined;
}

export function svgCatalogAdminErrorMessage(error: unknown): string {
  const code = errorCode(error);
  if (code && ERROR_MESSAGES[code]) return ERROR_MESSAGES[code];
  return "Không thể hoàn tất thao tác SVG. Vui lòng kiểm tra thông tin và thử lại.";
}

async function post<T>(path: string, body: unknown): Promise<T> {
  try {
    return await backendRequest<T>(path, { method: "POST", body: JSON.stringify(body) });
  } catch (error) {
    throw new Error(svgCatalogAdminErrorMessage(error));
  }
}

export async function createSvgCatalogAsset(body: SvgCatalogAssetCreateRequestV1): Promise<SvgCatalogAssetResponseV1> {
  validateSvgAssetRequest(body);
  return post<SvgCatalogAssetResponseV1>(ASSETS_PATH, body);
}

export async function createSvgGuideRevision(
  catalogEntryId: string,
  body: CreateSvgGuideRevisionRequestV1,
): Promise<SvgGuideRevisionReceiptV1> {
  requiredText(catalogEntryId, "Mã mục SVG", 1, Number.MAX_SAFE_INTEGER);
  validateSvgGuideRequest(body);
  return post<SvgGuideRevisionReceiptV1>(`${ASSETS_PATH}/${encodeURIComponent(catalogEntryId)}/guide-revisions`, body);
}

export async function curateSvgCatalogAsset(
  catalogEntryId: string,
  body: SvgCurationRequestV1,
): Promise<SvgReviewReceiptV1> {
  requiredText(catalogEntryId, "Mã mục SVG", 1, Number.MAX_SAFE_INTEGER);
  validateSvgCurationRequest(body);
  return post<SvgReviewReceiptV1>(`${ASSETS_PATH}/${encodeURIComponent(catalogEntryId)}/curation`, body);
}
