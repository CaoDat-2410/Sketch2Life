import { BackendApiError, configuredOrganizationId } from "./backendApi";
import { data, enc, request } from "./teacherHttp";

export type SvgReadiness = "STROKE_READY" | "REQUIRES_MANUAL_AUTHORING" | "STATIC_ONLY" | string;
export type SvgAssetReviewState =
  | "PENDING_EDUCATOR_REVIEW"
  | "PENDING_CURATOR_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "ARCHIVED"
  | string;
export type SvgGuideReviewState = "PENDING" | "APPROVED" | "REJECTED" | string;
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

export interface SvgCatalogAssetResponseV1 {
  contract: string;
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

export interface SvgCatalogAssetListV1 {
  items: SvgCatalogAssetResponseV1[];
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

export interface SvgGuideRevisionReceiptV1 {
  contract: string;
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

export interface SvgGuideRevisionListV1 {
  items: SvgGuideRevisionReceiptV1[];
}

export interface CreateSvgGuideRevisionRequestV1 {
  contract: "CreateSvgGuideRevisionRequestV1";
  guide: SketchStrokeGuideV3;
}

export type SvgReviewDecision = "APPROVE" | "REJECT";

export interface SvgSourceReviewRequestV1 {
  contract: "SvgSourceReviewRequestV1";
  source_sha256: string;
  decision: SvgReviewDecision;
  reason?: string;
}

export interface SvgGuideReviewRequestV1 {
  contract: "SvgGuideReviewRequestV1";
  source_sha256: string;
  guide_sha256: string;
  decision: SvgReviewDecision;
  reason?: string;
}

export interface SvgReviewReceiptV1 {
  contract: string;
  review_id: string;
  catalog_entry_id: string;
  review_subject_kind: string;
  review_kind: string;
  decision: SvgReviewDecision;
  source_sha256: string;
  guide_sha256: string | null;
  grouping_allowed: boolean;
  reviewer_ref: string;
  created_at: string;
}

const NO_STORE = "private, no-store";

function validateLimit(limit: number): void {
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
    throw new BackendApiError("Số mục phải nằm trong khoảng từ 1 đến 100.", "INVALID_REQUEST", 400);
  }
}

function organizationPath(organizationId: string): string {
  if (!organizationId.trim()) {
    throw new BackendApiError("Tổ chức chưa được cấu hình.", "INVALID_REQUEST", 400);
  }
  return "/api/svg-catalog/v1/organizations/" + enc(organizationId);
}

function assetPath(organizationId: string, catalogEntryId: string): string {
  return organizationPath(organizationId) + "/assets/" + enc(catalogEntryId);
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  return data(await request<T>(path, { method: "GET", headers: { "Cache-Control": NO_STORE }, signal }));
}

async function post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return data(await request<T>(path, {
    method: "POST",
    headers: { "Cache-Control": NO_STORE },
    body: JSON.stringify(body),
    signal,
  }));
}

export async function listSvgCatalogAssets(
  organizationId = configuredOrganizationId(),
  options: { limit?: number; signal?: AbortSignal } = {},
): Promise<SvgCatalogAssetListV1> {
  const limit = options.limit ?? 50;
  validateLimit(limit);
  return get(organizationPath(organizationId) + "/assets?limit=" + limit, options.signal);
}

export async function getSvgCatalogAsset(
  organizationId: string,
  catalogEntryId: string,
  signal?: AbortSignal,
): Promise<SvgCatalogAssetResponseV1> {
  return get(assetPath(organizationId, catalogEntryId), signal);
}

export async function createSvgCatalogAsset(
  organizationId: string,
  body: SvgCatalogAssetCreateRequestV1,
  signal?: AbortSignal,
): Promise<SvgCatalogAssetResponseV1> {
  return post(organizationPath(organizationId) + "/assets", body, signal);
}

export async function listSvgGuideRevisions(
  organizationId: string,
  catalogEntryId: string,
  options: { limit?: number; signal?: AbortSignal } = {},
): Promise<SvgGuideRevisionListV1> {
  const limit = options.limit ?? 50;
  validateLimit(limit);
  return get(assetPath(organizationId, catalogEntryId) + "/guide-revisions?limit=" + limit, options.signal);
}

export async function createSvgGuideRevision(
  organizationId: string,
  catalogEntryId: string,
  body: CreateSvgGuideRevisionRequestV1,
  signal?: AbortSignal,
): Promise<SvgGuideRevisionReceiptV1> {
  return post(assetPath(organizationId, catalogEntryId) + "/guide-revisions", body, signal);
}

export async function reviewSvgCatalogSource(
  organizationId: string,
  catalogEntryId: string,
  body: SvgSourceReviewRequestV1,
  signal?: AbortSignal,
): Promise<SvgReviewReceiptV1> {
  return post(assetPath(organizationId, catalogEntryId) + "/source-reviews", body, signal);
}

export async function reviewSvgGuide(
  organizationId: string,
  catalogEntryId: string,
  guideRevisionId: string,
  body: SvgGuideReviewRequestV1,
  signal?: AbortSignal,
): Promise<SvgReviewReceiptV1> {
  return post(assetPath(organizationId, catalogEntryId) + "/guide-revisions/" + enc(guideRevisionId) + "/educator-reviews", body, signal);
}

export const teacherSvgCatalogApi = {
  listAssets: listSvgCatalogAssets,
  getAsset: getSvgCatalogAsset,
  createAsset: createSvgCatalogAsset,
  listGuideRevisions: listSvgGuideRevisions,
  createGuideRevision: createSvgGuideRevision,
  reviewSource: reviewSvgCatalogSource,
  reviewGuide: reviewSvgGuide,
};
