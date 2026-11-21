import { afterEach, describe, expect, it, vi } from "vitest";
import { BackendApiError } from "../backendApi";
import { OccurrenceApiError } from "../teacherOccurrenceApi";
import { ABORT_STALE_ATTEMPTS, JOB_POLL_MAX_MS, JOB_POLL_MAX_TRANSIENT_FAILURES, MAX_UPLOAD_PART_BYTES, pollJob, sha256Hex, teacherOccurrenceApi, type JobStatus, type UploadSession } from "../teacherOccurrenceApi";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

function response(status: number, body?: unknown, etag?: string): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ ...(etag ? { ETag: etag } : {}), "X-Request-ID": "response-1" }),
    text: async () => body === undefined ? "" : JSON.stringify(body),
  } as Response;
}

function setup(replies: Response[]) {
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
const call = (fetcher: ReturnType<typeof setup>, index = 0) => {
  const [url, init] = fetcher.mock.calls[index];
  return { url, init, headers: new Headers(init.headers), body: init.body };
};

const session = (overrides: Partial<UploadSession> = {}): UploadSession => ({
  contract: "GenericUploadSessionV1", upload_id: "upl-1", purpose: "OCCURRENCE_DOCUMENT", target_ref: "occ-1", state: "OPEN",
  part_size_bytes: MAX_UPLOAD_PART_BYTES, expected_parts: 1, accepted_parts: [], byte_count: 0, expires_at: "2026-11-21T00:00:00Z",
  revision: 1, asset_ref: null, asset_state: null, error_code: null, ...overrides,
});

const job = (state: JobStatus["state"], extra: Partial<JobStatus> = {}): JobStatus => ({
  job_id: "job-1", target_kind: "LESSON_SOURCE_DOCUMENT", target_ref: "doc-1", job_revision: 1, attempt_number: 1, target_revision: 1,
  input_hash: "a".repeat(64), state, result_disposition: state === "succeeded" ? "accepted" : null, correlation_id: "corr-1",
  created_at: "2026-11-20T00:00:00Z", updated_at: "2026-11-20T00:00:00Z", started_at: null,
  completed_at: state === "succeeded" ? "2026-11-20T00:00:02Z" : null,
  progress: { kind: "unknown", value: null, stage_label: null }, failure: null, result_refs: [], poll_after_ms: null, ...extra,
});

describe("Teacher occurrence API: occurrences", () => {
  it("lists one class with the page limit, state filter and cursor", async () => {
    const fetcher = setup([response(200, { contract: "LessonOccurrencePageV1", items: [], next_cursor: null })]);
    await teacherOccurrenceApi.list("class-1", { state: "DRAFT", cursor: "cur-1" });
    const { url, init } = call(fetcher);
    expect(init.method).toBeUndefined();
    const query = new URL(url).searchParams;
    expect(new URL(url).pathname).toBe("/v1/lesson-occurrences");
    expect(Object.fromEntries(query)).toEqual({ class_id: "class-1", limit: "100", state: "DRAFT", cursor: "cur-1" });
  });

  it("creates an occurrence with the user action key and the exact pinned version reference", async () => {
    const fetcher = setup([response(201, { contract: "LessonOccurrenceV1", occurrence_id: "occ-1" }, '"1"')]);
    await teacherOccurrenceApi.create({
      class_id: "class-1", title: "Art class", scheduled_date: "2026-11-20",
      lesson_version_ref: { lesson_id: "lesson-1", version_id: "version-4", content_sha256: "a".repeat(64) },
    }, "occ-create-1");
    const { url, init, headers } = call(fetcher);
    expect(url).toContain("/v1/lesson-occurrences");
    expect(init.method).toBe("POST");
    expect(headers.get("Idempotency-Key")).toBe("occ-create-1");
    expect(headers.get("Authorization")).toBe("Bearer token-1");
    expect(JSON.parse(String(init.body))).toMatchObject({ class_id: "class-1", scheduled_date: "2026-11-20", lesson_version_ref: { version_id: "version-4" } });
  });

  it("rejects an invalid idempotency key before any request is sent", async () => {
    const fetcher = setup([]);
    await expect(teacherOccurrenceApi.create({ class_id: "c", title: "t" }, "has space")).rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY" });
    await expect(teacherOccurrenceApi.create({ class_id: "c", title: "t" }, "k".repeat(129))).rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY" });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("supports authorized conditional reads and keeps the 304 ETag", async () => {
    const fetcher = setup([response(304, undefined, '"5"')]);
    const result = await teacherOccurrenceApi.get("occ-1", '"5"');
    expect(call(fetcher).headers.get("If-None-Match")).toBe('"5"');
    expect(result).toEqual({ data: null, etag: '"5"', notModified: true });
  });

  it("fails closed with a session error when no ID token is available", async () => {
    const fetcher = setup([]);
    window.sketch2lifeAuth = { getIdToken: vi.fn(async () => { throw new Error("no session"); }) };
    await expect(teacherOccurrenceApi.get("occ-1")).rejects.toMatchObject({ status: 401, code: "AUTHENTICATION_REQUIRED" });
    expect(fetcher).not.toHaveBeenCalled();
  });
});

describe("Teacher occurrence API: error envelope", () => {
  it("maps a cross-scope 404 to the same not-found-or-no-access message", async () => {
    setup([response(404, { code: "RESOURCE_NOT_FOUND", message: "Không có.", correlation_id: "corr-9", retryable: false })]);
    await expect(teacherOccurrenceApi.get("outside-scope")).rejects.toMatchObject({
      status: 404, code: "RESOURCE_NOT_FOUND",
      message: "Không tìm thấy nội dung hoặc bạn không có quyền truy cập. Hãy làm mới danh sách.",
    });
  });

  it("keeps a 403 distinct from a 404 and preserves the code and request id", async () => {
    setup([response(403, { detail: { code: "ACTION_NOT_ALLOWED" } })]);
    const error = await teacherOccurrenceApi.create({ class_id: "c", title: "t" }, "k1").catch((cause: unknown) => cause);
    expect(error).toMatchObject({ status: 403, code: "ACTION_NOT_ALLOWED", message: "Tài khoản không được phép thực hiện thao tác này.", requestId: "response-1" });
  });

  it("keeps the safe field errors of a 400 and drops unsafe entries and the raw body", async () => {
    setup([response(400, { code: "INVALID_REQUEST", message: "Yêu cầu không hợp lệ.", correlation_id: "corr-5", retryable: false, field_errors: [
      { field: "objectives[2]", code: "INVALID_FORMAT" }, { field: "teacher_direction", code: "TOO_LONG" },
      { field: "<script>alert(1)</script>", code: "INVALID_FORMAT" }, { field: "safety_notes", code: "lower-case" },
    ] })]);
    const error = await teacherOccurrenceApi.createPlan("occ-1", { expected_head_revision_no: 0, objectives: ["x"], teacher_direction: "y", activities: [] }, "plan-key-9").catch((cause: unknown) => cause);
    expect(error).toBeInstanceOf(OccurrenceApiError);
    expect(error).toBeInstanceOf(BackendApiError);
    expect((error as OccurrenceApiError).fieldErrors).toEqual([{ field: "objectives[2]", code: "INVALID_FORMAT" }, { field: "teacher_direction", code: "TOO_LONG" }]);
    expect(JSON.stringify(error)).not.toContain("script");
  });

  it("uses the server message of a CONV-1 envelope and never the raw body", async () => {
    setup([response(409, { code: "STALE_REVISION", message: "Bản kế hoạch đã thay đổi.", correlation_id: "corr-2", retryable: false, secret: "do-not-show" })]);
    const error = await teacherOccurrenceApi.confirmPlan("occ-1", 2, "h".repeat(64), "k2").catch((cause: unknown) => cause) as Error;
    expect(error).toMatchObject({ status: 409, code: "STALE_REVISION", message: "Bản kế hoạch đã thay đổi.", requestId: "corr-2" });
    expect(JSON.stringify(error)).not.toContain("do-not-show");
  });

  it("maps the upload-only codes to Vietnamese copy", async () => {
    setup([response(422, { detail: { code: "UPLOAD_CONTENT_MISMATCH" } })]);
    await expect(teacherOccurrenceApi.completeUpload("upl-1", { expected_size_bytes: 1, expected_sha256: "a".repeat(64) }, "k3")).rejects.toMatchObject({
      code: "UPLOAD_CONTENT_MISMATCH", message: "Nội dung tệp không khớp định dạng đã chọn. Hãy chọn tệp khác.",
    });
  });
});

describe("Teacher occurrence API: generic upload sessions", () => {
  it("creates a session with a key and a distinct DTO (upload_id, no lesson-library fields)", async () => {
    const fetcher = setup([response(201, session(), '"1"')]);
    const created = await teacherOccurrenceApi.createUpload({ purpose: "OCCURRENCE_DOCUMENT", target_ref: "occ-1", media_type: "application/pdf", expected_size_bytes: 10, expected_sha256: "c".repeat(64), file_name: "a.pdf" }, "up-create-1");
    const { url, init, headers } = call(fetcher);
    expect(new URL(url).pathname).toBe("/v1/upload-sessions");
    expect(init.method).toBe("POST");
    expect(headers.get("Idempotency-Key")).toBe("up-create-1");
    expect(JSON.parse(String(init.body))).toMatchObject({ purpose: "OCCURRENCE_DOCUMENT", target_ref: "occ-1", file_name: "a.pdf" });
    expect(created.upload_id).toBe("upl-1");
  });

  it("reads one session and sends raw parts with the part hash and no Content-Range", async () => {
    const fetcher = setup([response(200, session()), response(200, { contract: "GenericUploadPartReceiptV1", accepted: true })]);
    await teacherOccurrenceApi.getUpload("upl 1");
    await teacherOccurrenceApi.putPart("upl-1", 3, new Blob([new Uint8Array([1, 2])]), "b".repeat(64));
    expect(new URL(call(fetcher, 0).url).pathname).toBe("/v1/upload-sessions/upl%201");
    const part = call(fetcher, 1);
    expect(new URL(part.url).pathname).toBe("/v1/upload-sessions/upl-1/parts/3");
    expect(part.init.method).toBe("PUT");
    expect(part.headers.get("Content-Type")).toBe("application/octet-stream");
    expect(part.headers.get("Content-Range")).toBeNull();
    expect(part.headers.get("X-Part-SHA256")).toBe("b".repeat(64));
    expect(part.body).toBeInstanceOf(Blob);
  });

  it("completes with the whole-file size and hash under its own key", async () => {
    const fetcher = setup([response(202, session({ contract: "GenericUploadCompletionV1", state: "COMPLETED", asset_ref: "upl_upl-1", asset_state: "READY" }), '"3"')]);
    const done = await teacherOccurrenceApi.completeUpload("upl-1", { expected_size_bytes: 10, expected_sha256: "c".repeat(64) }, "up-complete-1");
    const { url, headers, init } = call(fetcher);
    expect(new URL(url).pathname).toBe("/v1/upload-sessions/upl-1/complete");
    expect(headers.get("Idempotency-Key")).toBe("up-complete-1");
    expect(JSON.parse(String(init.body))).toEqual({ expected_size_bytes: 10, expected_sha256: "c".repeat(64) });
    expect(done.asset_ref).toBe("upl_upl-1");
  });

  it("aborts with a strong If-Match and its own idempotency key", async () => {
    const fetcher = setup([response(202, session({ state: "ABORTED", revision: 5 }))]);
    await teacherOccurrenceApi.abortUpload("upl-1", 4, "abort-key-1");
    const { init, headers } = call(fetcher);
    expect(init.method).toBe("DELETE");
    expect(headers.get("If-Match")).toBe('"4"');
    expect(headers.get("Idempotency-Key")).toBe("abort-key-1");
  });

  it("abortOpenUpload re-reads the session and retries with the new revision after STALE_REVISION", async () => {
    const stale = { code: "STALE_REVISION", message: "Thông tin đã thay đổi.", correlation_id: "c", retryable: false };
    const fetcher = setup([
      response(200, session({ revision: 2 })), response(409, stale),
      response(200, session({ revision: 3 })), response(202, session({ state: "ABORTED", revision: 5 })),
    ]);
    const result = await teacherOccurrenceApi.abortOpenUpload("upl-1", "abort-key-9");
    expect(result.state).toBe("ABORTED");
    expect(call(fetcher, 1).headers.get("If-Match")).toBe('"2"');
    expect(call(fetcher, 3).headers.get("If-Match")).toBe('"3"');
    expect(call(fetcher, 3).headers.get("Idempotency-Key")).toBe("abort-key-9");
  });

  it("abortOpenUpload gives up after a bounded number of stale answers and does not retry other refusals", async () => {
    const stale = { code: "STALE_REVISION", message: "Thông tin đã thay đổi.", correlation_id: "c", retryable: false };
    const fetcher = setup([...Array.from({ length: ABORT_STALE_ATTEMPTS }, (_, index) => [response(200, session({ revision: index + 1 })), response(409, stale)]).flat()]);
    await expect(teacherOccurrenceApi.abortOpenUpload("upl-1", "k")).rejects.toMatchObject({ code: "STALE_REVISION" });
    expect(fetcher).toHaveBeenCalledTimes(ABORT_STALE_ATTEMPTS * 2);
    const gone = setup([response(200, session()), response(410, { detail: { code: "UPLOAD_SESSION_EXPIRED" } })]);
    await expect(teacherOccurrenceApi.abortOpenUpload("upl-1", "k")).rejects.toMatchObject({ status: 410 });
    expect(gone).toHaveBeenCalledTimes(2);
  });

  it("abortOpenUpload reads the current revision first and skips a finished session", async () => {
    const fetcher = setup([response(200, session({ revision: 7 })), response(202, session({ state: "ABORTED", revision: 8 })), response(200, session({ state: "COMPLETED", revision: 9 }))]);
    await teacherOccurrenceApi.abortOpenUpload("upl-1", "abort-key-2");
    expect(call(fetcher, 1).headers.get("If-Match")).toBe('"7"');
    const finished = await teacherOccurrenceApi.abortOpenUpload("upl-1", "abort-key-3");
    expect(finished.state).toBe("COMPLETED");
    expect(fetcher).toHaveBeenCalledTimes(3);
  });
});

describe("Teacher occurrence API: upload chunking", () => {
  const fileOf = (size: number, name = "lesson.pdf") => {
    const bytes = new Uint8Array(size);
    for (let index = 0; index < size; index += 1) bytes[index] = index % 251;
    return { file: new File([bytes], name, { type: "application/pdf" }), bytes };
  };

  it("splits a 9 MiB file into 4 MiB parts, hashes every part and completes with the whole-file hash", async () => {
    const { file, bytes } = fileOf(9 * 1024 * 1024);
    const wholeHash = await sha256Hex(bytes.buffer as ArrayBuffer);
    const parts: Array<{ no: number; size: number; hash: string }> = [];
    vi.spyOn(teacherOccurrenceApi, "createUpload").mockResolvedValue(session({ expected_parts: 3 }));
    vi.spyOn(teacherOccurrenceApi, "getUpload").mockResolvedValue(session({ expected_parts: 3 }));
    vi.spyOn(teacherOccurrenceApi, "putPart").mockImplementation(async (_id, no, blob, hash) => { parts.push({ no, size: blob.size, hash }); return {} as never; });
    const complete = vi.spyOn(teacherOccurrenceApi, "completeUpload").mockResolvedValue(session({ state: "COMPLETED", asset_ref: "upl_upl-1", asset_state: "READY" }));
    const progress: number[] = [];
    const asset = await teacherOccurrenceApi.uploadOccurrenceFile(file, "occ-1", { keys: { create: "key-create", complete: "key-complete" }, onProgress: (done) => progress.push(done) });
    expect(asset).toBe("upl_upl-1");
    expect(parts.map((part) => [part.no, part.size])).toEqual([[1, 4 * 1024 * 1024], [2, 4 * 1024 * 1024], [3, 1024 * 1024]]);
    expect(parts[0].hash).toBe(await sha256Hex(bytes.slice(0, 4 * 1024 * 1024).buffer));
    expect(parts[2].hash).toBe(await sha256Hex(bytes.slice(8 * 1024 * 1024).buffer));
    expect(teacherOccurrenceApi.createUpload).toHaveBeenCalledWith(expect.objectContaining({ purpose: "OCCURRENCE_DOCUMENT", target_ref: "occ-1", expected_size_bytes: file.size, expected_sha256: wholeHash, file_name: "lesson.pdf" }), "key-create");
    expect(complete).toHaveBeenCalledWith("upl-1", { expected_size_bytes: file.size, expected_sha256: wholeHash }, "key-complete");
    expect(progress.at(-1)).toBe(file.size);
  });

  it("resumes from the live session: a replayed create is always OPEN, so accepted parts come from the read-back", async () => {
    const { file } = fileOf(9 * 1024 * 1024);
    vi.spyOn(teacherOccurrenceApi, "createUpload").mockResolvedValue(session({ expected_parts: 3 }));
    vi.spyOn(teacherOccurrenceApi, "getUpload").mockResolvedValue(session({ expected_parts: 3, revision: 3, accepted_parts: [{ part_no: 1, byte_length: 4 * 1024 * 1024, sha256: "a".repeat(64) }, { part_no: 2, byte_length: 4 * 1024 * 1024, sha256: "b".repeat(64) }] }));
    const put = vi.spyOn(teacherOccurrenceApi, "putPart").mockResolvedValue({} as never);
    vi.spyOn(teacherOccurrenceApi, "completeUpload").mockResolvedValue(session({ state: "COMPLETED", asset_ref: "upl_upl-1" }));
    await teacherOccurrenceApi.uploadOccurrenceFile(file, "occ-1");
    expect(put).toHaveBeenCalledTimes(1);
    expect(put.mock.calls[0][1]).toBe(3);
  });

  it("sends the media type that belongs to the extension, not the browser-reported file.type", async () => {
    const odd = new File([new Uint8Array([1, 2, 3])], "bai.docx", { type: "application/x-zip-compressed" });
    const create = vi.spyOn(teacherOccurrenceApi, "createUpload").mockResolvedValue(session({ state: "COMPLETED", asset_ref: "upl_x" }));
    vi.spyOn(teacherOccurrenceApi, "getUpload").mockResolvedValue(session({ state: "COMPLETED", asset_ref: "upl_x" }));
    await teacherOccurrenceApi.uploadOccurrenceFile(odd, "occ-1");
    expect(create.mock.calls[0][0].media_type).toBe("application/vnd.openxmlformats-officedocument.wordprocessingml.document");
  });

  it("passes the abort signal to each part request", async () => {
    const fetcher = setup([response(200, { contract: "GenericUploadPartReceiptV1" })]);
    const controller = new AbortController();
    await teacherOccurrenceApi.putPart("upl-1", 1, new Blob([new Uint8Array([1])]), "b".repeat(64), controller.signal);
    expect(call(fetcher).init.signal).toBe(controller.signal);
  });

  it("returns the asset of a session that completed although the replayed create says OPEN", async () => {
    const { file } = fileOf(1024);
    vi.spyOn(teacherOccurrenceApi, "createUpload").mockResolvedValue(session());
    vi.spyOn(teacherOccurrenceApi, "getUpload").mockResolvedValue(session({ state: "COMPLETED", asset_ref: "upl_done", revision: 3 }));
    const put = vi.spyOn(teacherOccurrenceApi, "putPart");
    await expect(teacherOccurrenceApi.uploadOccurrenceFile(file, "occ-1")).resolves.toBe("upl_done");
    expect(put).not.toHaveBeenCalled();
  });

  it("refuses a part size above 4 MiB, a wrong extension, an empty file and a file over 25 MB before any request", async () => {
    const create = vi.spyOn(teacherOccurrenceApi, "createUpload").mockResolvedValue(session({ part_size_bytes: MAX_UPLOAD_PART_BYTES + 1 }));
    vi.spyOn(teacherOccurrenceApi, "getUpload").mockResolvedValue(session({ part_size_bytes: MAX_UPLOAD_PART_BYTES + 1 }));
    await expect(teacherOccurrenceApi.uploadOccurrenceFile(fileOf(1024).file, "occ-1")).rejects.toMatchObject({ code: "INVALID_UPLOAD_SESSION" });
    create.mockClear();
    await expect(teacherOccurrenceApi.uploadOccurrenceFile(fileOf(1024, "image.png").file, "occ-1")).rejects.toMatchObject({ code: "INVALID_FILE" });
    await expect(teacherOccurrenceApi.uploadOccurrenceFile(new File([], "empty.pdf"), "occ-1")).rejects.toMatchObject({ code: "INVALID_FILE" });
    await expect(teacherOccurrenceApi.uploadOccurrenceFile({ name: "big.pdf", size: 25_000_001 } as File, "occ-1")).rejects.toMatchObject({ code: "INVALID_FILE" });
    expect(create).not.toHaveBeenCalled();
  });

  it("stops between parts when the signal aborts", async () => {
    const { file } = fileOf(9 * 1024 * 1024);
    const controller = new AbortController();
    vi.spyOn(teacherOccurrenceApi, "createUpload").mockResolvedValue(session({ expected_parts: 3 }));
    vi.spyOn(teacherOccurrenceApi, "getUpload").mockResolvedValue(session({ expected_parts: 3 }));
    const put = vi.spyOn(teacherOccurrenceApi, "putPart").mockImplementation(async () => { controller.abort(); return {} as never; });
    await expect(teacherOccurrenceApi.uploadOccurrenceFile(file, "occ-1", { signal: controller.signal })).rejects.toMatchObject({ name: "AbortError" });
    expect(put).toHaveBeenCalledTimes(1);
  });
});

describe("Teacher occurrence API: documents", () => {
  it("attaches the opaque asset ref under a key", async () => {
    const fetcher = setup([response(202, { contract: "LessonSourceDocumentAcceptedV1", source_document_id: "doc-1", job: { job_id: "job-1" } })]);
    await teacherOccurrenceApi.attachDocument("occ-1", "upl_upl-1", "attach-key-1");
    const { url, init, headers } = call(fetcher);
    expect(new URL(url).pathname).toBe("/v1/lesson-occurrences/occ-1/documents");
    expect(headers.get("Idempotency-Key")).toBe("attach-key-1");
    expect(JSON.parse(String(init.body))).toEqual({ asset_ref: "upl_upl-1" });
  });

  it("lists documents, revisions and reads revisions with conditional headers", async () => {
    const fetcher = setup([
      response(200, { items: [], next_cursor: null }), response(200, { items: [], next_cursor: "c2" }),
      response(304, undefined, '"hash.NEEDS_REVIEW"'), response(304, undefined, '"d1"'),
    ]);
    await teacherOccurrenceApi.listDocuments("occ-1");
    await teacherOccurrenceApi.listDocumentRevisions("occ-1", "doc-1", "cursor-1");
    const revision = await teacherOccurrenceApi.getDocumentRevision("occ-1", "doc-1", 2, '"hash.NEEDS_REVIEW"');
    await teacherOccurrenceApi.getDocument("occ-1", "doc-1", '"d1"');
    expect(new URL(call(fetcher, 0).url).search).toBe("?limit=100");
    expect(new URL(call(fetcher, 1).url).pathname).toBe("/v1/lesson-occurrences/occ-1/documents/doc-1/revisions");
    expect(new URL(call(fetcher, 1).url).searchParams.get("cursor")).toBe("cursor-1");
    expect(new URL(call(fetcher, 2).url).pathname).toBe("/v1/lesson-occurrences/occ-1/documents/doc-1/revisions/2");
    expect(call(fetcher, 2).headers.get("If-None-Match")).toBe('"hash.NEEDS_REVIEW"');
    expect(revision.notModified).toBe(true);
    expect(call(fetcher, 3).headers.get("If-None-Match")).toBe('"d1"');
  });

  it("creates an immutable text revision from the head the Teacher edited, under a key", async () => {
    const fetcher = setup([response(201, { contract: "LessonDocumentRevisionV2", revision_no: 3 })]);
    await teacherOccurrenceApi.editDocumentRevision("occ-1", "doc-1", "Văn bản mới", 2, "edit-key-1");
    const { init, headers } = call(fetcher);
    expect(init.method).toBe("POST");
    expect(headers.get("Idempotency-Key")).toBe("edit-key-1");
    expect(JSON.parse(String(init.body))).toEqual({ extracted_text: "Văn bản mới", expected_head_revision_no: 2 });
  });

  it("measures the 2 MiB limit in UTF-8 bytes before sending", async () => {
    const fetcher = setup([]);
    const text = "ệ".repeat(Math.ceil((2 * 1024 * 1024) / 3) + 1);
    await expect(teacherOccurrenceApi.editDocumentRevision("occ-1", "doc-1", text, 1, "edit-key-2")).rejects.toMatchObject({ code: "TEXT_TOO_LARGE" });
    expect(fetcher).not.toHaveBeenCalled();
  });
});

describe("Teacher occurrence API: plan revisions", () => {
  it("creates a plan revision against the head it was edited from, under a key", async () => {
    const fetcher = setup([response(201, { contract: "LessonPlanRevisionV1", revision_no: 2 })]);
    const input = { expected_head_revision_no: 1, document_revision_ref: { document_id: "doc-1", revision_no: 2 }, objectives: ["Vẽ"], teacher_direction: "Hướng dẫn", safety_notes: null, activities: [{ kind: "LESSON" as const, lesson_activity_id: "act-1" }] };
    await teacherOccurrenceApi.createPlan("occ-1", input, "plan-key-1");
    const { url, init, headers } = call(fetcher);
    expect(new URL(url).pathname).toBe("/v1/lesson-occurrences/occ-1/plan-revisions");
    expect(headers.get("Idempotency-Key")).toBe("plan-key-1");
    expect(JSON.parse(String(init.body))).toEqual(input);
  });

  it("lists and reads revisions; the read is conditional", async () => {
    const fetcher = setup([response(200, { items: [], next_cursor: null }), response(304, undefined, '"h.DRAFT"')]);
    await teacherOccurrenceApi.listPlans("occ-1");
    const result = await teacherOccurrenceApi.getPlan("occ-1", 4, '"h.DRAFT"');
    expect(new URL(call(fetcher, 1).url).pathname).toBe("/v1/lesson-occurrences/occ-1/plan-revisions/4");
    expect(call(fetcher, 1).headers.get("If-None-Match")).toBe('"h.DRAFT"');
    expect(result.notModified).toBe(true);
  });

  it("confirms with the selected content hash, an empty checklist and a key", async () => {
    const fetcher = setup([response(200, { contract: "LessonPlanRevisionV1", state: "APPROVED" })]);
    await teacherOccurrenceApi.confirmPlan("occ-1", 4, "d".repeat(64), "confirm-key-1");
    const { url, init, headers } = call(fetcher);
    expect(new URL(url).pathname).toBe("/v1/lesson-occurrences/occ-1/plan-revisions/4/confirm");
    expect(headers.get("Idempotency-Key")).toBe("confirm-key-1");
    expect(JSON.parse(String(init.body))).toEqual({ expected_plan_hash: "d".repeat(64), checklist: [] });
  });
});

describe("Job status poller", () => {
  it("reads one job conditionally", async () => {
    const fetcher = setup([response(200, job("queued"), '"1"')]);
    const result = await teacherOccurrenceApi.getJob("job/1", '"0"');
    expect(new URL(call(fetcher).url).pathname).toBe("/v1/jobs/job%2F1");
    expect(call(fetcher).headers.get("If-None-Match")).toBe('"0"');
    expect(result.etag).toBe('"1"');
  });

  it("backs off 2, 4, 8, 10, 10 seconds, reuses the ETag after a 304 and stops at a terminal state", async () => {
    const replies = [
      { data: job("queued"), etag: '"1"', notModified: false },
      { data: null, etag: '"1"', notModified: true },
      { data: job("running", { job_revision: 2 }), etag: '"2"', notModified: false },
      { data: null, etag: '"2"', notModified: true },
      { data: null, etag: '"2"', notModified: true },
      { data: job("succeeded", { job_revision: 3 }), etag: '"3"', notModified: false },
    ];
    const get = vi.fn(async () => replies.shift()!);
    const waits: number[] = [];
    const updates: string[] = [];
    const result = await pollJob("job-1", (value) => updates.push(value.state), new AbortController().signal, { get, wait: async (ms) => { waits.push(ms); } });
    expect(result.state).toBe("succeeded");
    expect(updates).toEqual(["queued", "running", "succeeded"]);
    expect(waits).toEqual([2_000, 4_000, 8_000, JOB_POLL_MAX_MS, JOB_POLL_MAX_MS]);
    expect(get.mock.calls.map((args) => (args as unknown[])[1])).toEqual([undefined, '"1"', '"1"', '"2"', '"2"', '"2"']);
    expect(get).toHaveBeenCalledTimes(6);
  });

  it.each(["failed_exhausted", "blocked_unsafe", "cancelled"] as const)("stops on the terminal state %s", async (state) => {
    const get = vi.fn(async () => ({ data: job(state, { failure: state === "cancelled" ? null : { code: "X", retryable: false, public_message: "Không xử lý được.", attempts_remaining: 0 } }), etag: '"1"', notModified: false }));
    const wait = vi.fn(async () => undefined);
    const result = await pollJob("job-1", () => undefined, new AbortController().signal, { get, wait });
    expect(result.state).toBe(state);
    expect(wait).not.toHaveBeenCalled();
  });

  it("keeps polling a retryable failure", async () => {
    const replies = [{ data: job("failed_retryable", { failure: { code: "X", retryable: true, public_message: "Thử lại.", attempts_remaining: 2 } }), etag: '"1"', notModified: false }, { data: job("succeeded"), etag: '"2"', notModified: false }];
    const get = vi.fn(async () => replies.shift()!);
    const result = await pollJob("job-1", () => undefined, new AbortController().signal, { get, wait: async () => undefined });
    expect(result.state).toBe("succeeded");
  });

  it("honours a poll_after_ms hint only inside the 2 s to 10 s range", async () => {
    const replies = [
      { data: job("running", { poll_after_ms: 500 }), etag: '"1"', notModified: false },
      { data: job("running", { poll_after_ms: 60_000 }), etag: '"2"', notModified: false },
      { data: job("running", { poll_after_ms: 5_000 }), etag: '"3"', notModified: false },
      { data: job("succeeded"), etag: '"4"', notModified: false },
    ];
    const waits: number[] = [];
    await pollJob("job-1", () => undefined, new AbortController().signal, { get: async () => replies.shift()!, wait: async (ms) => { waits.push(ms); } });
    expect(waits).toEqual([2_000, 10_000, 5_000]);
  });

  it("retries transient failures a bounded number of times with backoff, and never retries a 404", async () => {
    const transient = new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0);
    const replies: Array<() => Promise<{ data: JobStatus | null; etag: string | null; notModified: boolean }>> = [
      async () => { throw transient; },
      async () => { throw new BackendApiError("x", "PROVIDER_UNAVAILABLE", 503); },
      async () => ({ data: job("succeeded"), etag: '"1"', notModified: false }),
    ];
    const waits: number[] = [];
    const result = await pollJob("job-1", () => undefined, new AbortController().signal, { get: async () => replies.shift()!(), wait: async (ms) => { waits.push(ms); } });
    expect(result.state).toBe("succeeded");
    expect(waits).toEqual([2_000, 4_000]);

    const always = vi.fn(async () => { throw transient; });
    await expect(pollJob("job-1", () => undefined, new AbortController().signal, { get: always, wait: async () => undefined })).rejects.toBe(transient);
    expect(always).toHaveBeenCalledTimes(JOB_POLL_MAX_TRANSIENT_FAILURES + 1);

    const missing = new BackendApiError("x", "RESOURCE_NOT_FOUND", 404);
    const gone = vi.fn(async () => { throw missing; });
    await expect(pollJob("job-1", () => undefined, new AbortController().signal, { get: gone, wait: async () => undefined })).rejects.toBe(missing);
    expect(gone).toHaveBeenCalledTimes(1);
  });

  it("stops at once when the signal aborts while waiting (screen unmounted)", async () => {
    const controller = new AbortController();
    const get = vi.fn(async (_id: string, _etag?: string, _signal?: AbortSignal) => ({ data: job("running"), etag: '"1"', notModified: false }));
    const wait = (_ms: number, signal: AbortSignal) => new Promise<void>((_resolve, reject) => {
      signal.addEventListener("abort", () => reject(new DOMException("stop", "AbortError")), { once: true });
      controller.abort();
    });
    await expect(pollJob("job-1", () => undefined, controller.signal, { get, wait })).rejects.toMatchObject({ name: "AbortError" });
    expect(get).toHaveBeenCalledTimes(1);
    expect(get.mock.calls[0][2]).toBe(controller.signal);
  });

  it("does not report a result that arrives after the signal aborted", async () => {
    const controller = new AbortController();
    const onUpdate = vi.fn();
    const get = vi.fn(async () => { controller.abort(); return { data: job("succeeded"), etag: '"1"', notModified: false }; });
    await expect(pollJob("job-1", onUpdate, controller.signal, { get, wait: async () => undefined })).rejects.toMatchObject({ name: "AbortError" });
    expect(onUpdate).not.toHaveBeenCalled();
  });

  it("surfaces a job lookup failure as a safe 404 message", async () => {
    setup([response(404, { code: "RESOURCE_NOT_FOUND", message: "x", correlation_id: "c", retryable: false })]);
    await expect(pollJob("job-9", () => undefined, new AbortController().signal)).rejects.toMatchObject({ status: 404, message: expect.stringContaining("không có quyền truy cập") });
  });
});
