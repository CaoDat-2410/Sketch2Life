import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BackendApiError } from "../backendApi";
import {
  createSvgCatalogAsset,
  createSvgGuideRevision,
  getSvgCatalogAsset,
  listSvgCatalogAssets,
  listSvgGuideRevisions,
  reviewSvgCatalogSource,
  reviewSvgGuide,
  type SvgCatalogAssetCreateRequestV1,
  type SketchStrokeGuideV3,
} from "../teacherSvgCatalogApi";

function response(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "response-1" }),
    text: async () => JSON.stringify(body),
  } as Response;
}

function setup(replies: Response[]) {
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

function call(fetcher: ReturnType<typeof setup>, index = 0) {
  const [input, init] = fetcher.mock.calls[index];
  return {
    url: new URL(input),
    init,
    headers: new Headers(init.headers),
    body: init.body ? JSON.parse(String(init.body)) as Record<string, unknown> : undefined,
  };
}

const assetBody: SvgCatalogAssetCreateRequestV1 = {
  contract: "SvgCatalogAssetCreateRequestV1",
  title_vi: "Con mèo",
  topic_key: "animals",
  alt_text_vi: "Một chú mèo",
  source_uri: "https://example.test/cat.svg",
  license_id: "CC0-1.0",
  license_uri: "https://example.test/license",
  source_svg: "<svg/>",
};

const guide: SketchStrokeGuideV3 = {
  schema_version: "SketchStrokeGuideV3",
  guide_id: "cat-guide",
  title_vi: "Vẽ con mèo",
  source_asset_ref: "catalog/cat",
  source_asset_version: 1,
  source_sha256: "a".repeat(64),
  parts: [{ part_id: "body", label_vi: "Thân", path_ids: ["p1"], depends_on: [] }],
  stages: [
    { step_index: 1, instruction_vi: "Vẽ thân.", part_ids: ["body"], new_path_ids: [], animation_order: [] },
    { step_index: 2, instruction_vi: "Thêm tai.", part_ids: ["body"], new_path_ids: [], animation_order: [] },
    { step_index: 3, instruction_vi: "Thêm chân.", part_ids: ["body"], new_path_ids: [], animation_order: [] },
    { step_index: 4, instruction_vi: "Hoàn tất.", part_ids: ["body"], new_path_ids: ["p1"], animation_order: ["p1"] },
  ],
};

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "configured-org" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

describe("Teacher SVG catalog routes", () => {
  it("GETs organization assets, one asset, and guide revisions with bounded limits and encoded ids", async () => {
    const fetcher = setup([response(200, { items: [] }), response(200, { catalog_entry_id: "asset/2" }), response(200, { items: [] })]);
    await listSvgCatalogAssets("org/1", { limit: 12 });
    await getSvgCatalogAsset("org/1", "asset/2");
    await listSvgGuideRevisions("org/1", "asset/2", { limit: 8 });

    expect(call(fetcher).url.pathname).toBe("/api/svg-catalog/v1/organizations/org%2F1/assets");
    expect(call(fetcher).url.search).toBe("?limit=12");
    expect(call(fetcher).init.method).toBe("GET");
    expect(call(fetcher, 1).init.method).toBe("GET");
    expect(call(fetcher, 1).url.pathname).toBe("/api/svg-catalog/v1/organizations/org%2F1/assets/asset%2F2");
    expect(call(fetcher, 2).init.method).toBe("GET");
    expect(call(fetcher, 2).url.pathname).toBe("/api/svg-catalog/v1/organizations/org%2F1/assets/asset%2F2/guide-revisions");
    expect(call(fetcher, 2).url.search).toBe("?limit=8");
    expect([...fetcher.mock.calls]).toHaveLength(3);
  });

  it("POSTs create and review requests without write-only concurrency headers", async () => {
    const fetcher = setup([
      response(201, { catalog_entry_id: "asset-1" }),
      response(201, { guide_revision_id: "rev-1", review_state: "PENDING" }),
      response(200, { review_id: "source-review" }),
      response(200, { review_id: "guide-review" }),
    ]);
    const sourceReview = { contract: "SvgSourceReviewRequestV1" as const, source_sha256: "a".repeat(64), decision: "APPROVE" as const };
    const guideReview = {
      contract: "SvgGuideReviewRequestV1" as const,
      source_sha256: "a".repeat(64),
      guide_sha256: "b".repeat(64),
      decision: "REJECT" as const,
      reason: "Cần chỉnh lại hướng dẫn.",
    };

    await createSvgCatalogAsset("org", assetBody);
    await createSvgGuideRevision("org", "asset", { contract: "CreateSvgGuideRevisionRequestV1", guide });
    await reviewSvgCatalogSource("org", "asset", sourceReview);
    await reviewSvgGuide("org", "asset", "rev/1", guideReview);

    expect(call(fetcher).url.pathname).toBe("/api/svg-catalog/v1/organizations/org/assets");
    expect(call(fetcher).init.method).toBe("POST");
    expect(call(fetcher).body).toEqual(assetBody);
    expect(call(fetcher, 1).url.pathname).toBe("/api/svg-catalog/v1/organizations/org/assets/asset/guide-revisions");
    expect(call(fetcher, 1).body).toEqual({ contract: "CreateSvgGuideRevisionRequestV1", guide });
    expect(call(fetcher, 2).url.pathname).toBe("/api/svg-catalog/v1/organizations/org/assets/asset/source-reviews");
    expect(call(fetcher, 2).body).toEqual(sourceReview);
    expect(call(fetcher, 3).url.pathname).toBe("/api/svg-catalog/v1/organizations/org/assets/asset/guide-revisions/rev%2F1/educator-reviews");
    expect(call(fetcher, 3).body).toEqual(guideReview);

    for (let index = 0; index < fetcher.mock.calls.length; index += 1) {
      const headers = call(fetcher, index).headers;
      expect(headers.has("Idempotency-Key")).toBe(false);
      expect(headers.has("If-Match")).toBe(false);
      expect(headers.has("If-None-Match")).toBe(false);
      expect(headers.has("ETag")).toBe(false);
    }
  });

  it("bounds page limits to 1 through 100", async () => {
    await expect(listSvgCatalogAssets("org", { limit: 0 })).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    await expect(listSvgGuideRevisions("org", "asset", { limit: 101 })).rejects.toMatchObject({ code: "INVALID_REQUEST" });
  });

  it("maps nested FastAPI errors for 404, 403, 422, and 503", async () => {
    const fetcher = setup([
      response(404, { detail: { code: "SVG_CATALOG_ITEM_NOT_FOUND", message: "not found" } }),
      response(403, { detail: { code: "TEACHER_ASSIGNMENT_REQUIRED", message: "assignment required" } }),
      response(403, { detail: { code: "INDEPENDENT_REVIEW_REQUIRED", message: "self review" } }),
      response(422, { detail: { code: "SVG_PROVENANCE_URL_INVALID", message: "bad source" } }),
      response(503, { detail: { code: "DEPENDENCY_UNAVAILABLE", message: "offline" } }),
    ]);

    await expect(listSvgCatalogAssets("org")).rejects.toMatchObject({
      status: 404,
      code: "SVG_CATALOG_ITEM_NOT_FOUND",
      message: "Không tìm thấy nội dung hoặc bạn không có quyền truy cập. Hãy làm mới danh sách.",
    });
    await expect(listSvgCatalogAssets("org")).rejects.toMatchObject({
      status: 403,
      code: "TEACHER_ASSIGNMENT_REQUIRED",
      message: "Bạn cần được phân công vào lớp trước khi tạo buổi dạy.",
    });
    await expect(reviewSvgCatalogSource("org", "asset", {
      contract: "SvgSourceReviewRequestV1", source_sha256: "a".repeat(64), decision: "APPROVE",
    })).rejects.toMatchObject({
      status: 403,
      code: "INDEPENDENT_REVIEW_REQUIRED",
      message: "Người tạo nội dung không thể tự duyệt. Hãy nhờ một giáo viên khác.",
    });
    await expect(createSvgCatalogAsset("org", assetBody)).rejects.toMatchObject({
      status: 422,
      code: "SVG_PROVENANCE_URL_INVALID",
      message: "Liên kết nguồn và giấy phép phải là URL HTTPS hợp lệ.",
    });
    await expect(listSvgGuideRevisions("org", "asset")).rejects.toMatchObject({
      status: 503,
      code: "DEPENDENCY_UNAVAILABLE",
      message: "Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.",
    });
    expect(fetcher).toHaveBeenCalledTimes(5);
  });

  it("parses both flat and nested error bodies", async () => {
    const fetcher = setup([
      response(422, { detail: { code: "SVG_SOURCE_INVALID", message: "bad svg" } }),
      response(422, {
        code: "SVG_GUIDE_SOURCE_MISMATCH",
        message: "source mismatch",
        correlation_id: "corr-1",
        retryable: false,
      }),
    ]);
    await expect(createSvgCatalogAsset("org", assetBody)).rejects.toMatchObject({
      code: "SVG_SOURCE_INVALID",
      message: "SVG không hợp lệ hoặc chứa nội dung không được chấp nhận. Hãy kiểm tra lại tệp.",
    });
    await expect(createSvgGuideRevision("org", "asset", {
      contract: "CreateSvgGuideRevisionRequestV1", guide,
    })).rejects.toMatchObject({
      code: "SVG_GUIDE_SOURCE_MISMATCH",
      message: "Guide cần gắn với đúng phiên bản và mã nguồn của SVG.",
    });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("rejects unconfigured organizations before making a request", async () => {
    const fetcher = setup([]);
    await expect(listSvgCatalogAssets("   ")).rejects.toBeInstanceOf(BackendApiError);
    expect(fetcher).not.toHaveBeenCalled();
  });
});
