import { describe, expect, it } from "vitest";
import { fallbackMessage, parseApiError } from "../errorEnvelope";

const conv1Body = {
  code: "INVALID_IDEMPOTENCY_KEY",
  message: "Khóa yêu cầu trùng với một yêu cầu có nội dung khác.",
  correlation_id: "corr-1",
  retryable: false,
  retry_after_seconds: null,
  field_errors: [{ field: "Idempotency-Key", code: "INVALID_FORMAT" }, { field: 3 }],
  request_id: "corr-1",
};

describe("API error envelope parsing", () => {
  it("reads the CONV-1 envelope and keeps the Vietnamese server message", () => {
    const error = parseApiError(conv1Body, 400);
    expect(error.conv1).toBe(true);
    expect(error.code).toBe("INVALID_IDEMPOTENCY_KEY");
    expect(error.message).toBe(conv1Body.message);
    expect(error.requestId).toBe("corr-1");
    expect(error.retryable).toBe(false);
    expect(error.fieldErrors).toEqual([{ field: "Idempotency-Key", code: "INVALID_FORMAT" }]);
  });

  it("reads the retry hints of a rate limit envelope", () => {
    const error = parseApiError(
      { ...conv1Body, code: "RATE_LIMITED", retryable: true, retry_after_seconds: 30 },
      429,
    );
    expect(error.retryable).toBe(true);
    expect(error.retryAfterSeconds).toBe(30);
  });

  it("never shows the English message of a detail-wrapped body", () => {
    const error = parseApiError(
      { detail: { code: "INVALID_IDEMPOTENCY_KEY", message: "Idempotency-Key was already used for another request" } },
      400,
      "header-id",
    );
    expect(error.conv1).toBe(false);
    expect(error.code).toBe("INVALID_IDEMPOTENCY_KEY");
    expect(error.message).toBe("Khóa yêu cầu trùng với một yêu cầu có nội dung khác.");
    expect(error.requestId).toBe("header-id");
  });

  it("falls back by status for an unknown code, a validation array or an empty body", () => {
    expect(parseApiError({ detail: { code: "SOMETHING_NEW", message: "English" } }, 409).message).toBe(
      "Yêu cầu xung đột với trạng thái hiện tại.",
    );
    expect(parseApiError({ detail: [{ msg: "field required" }] }, 422)).toMatchObject({
      code: "HTTP_422",
      message: "Yêu cầu chưa đáp ứng điều kiện nghiệp vụ.",
    });
    expect(parseApiError(null, 503)).toMatchObject({ code: "HTTP_503", retryable: true });
    expect(parseApiError("not an object", 500).message).toBe("Máy chủ chưa thể hoàn tất yêu cầu.");
  });

  it("does not trust a top-level body that lacks the correlation id", () => {
    const error = parseApiError({ code: "INVALID_REQUEST", message: "English text from another envelope" }, 400);
    expect(error.conv1).toBe(false);
    expect(error.message).toBe("Yêu cầu không hợp lệ.");
  });

  it("does not trust a blank, oversized or non-finite value of an envelope", () => {
    expect(parseApiError({ ...conv1Body, message: "   " }, 400).conv1).toBe(false);
    expect(parseApiError({ ...conv1Body, message: "x".repeat(501) }, 400).conv1).toBe(false);
    expect(parseApiError({ ...conv1Body, retry_after_seconds: Infinity }, 429).retryAfterSeconds).toBeUndefined();
  });

  it("rejects a malformed code and keeps the status code instead", () => {
    expect(parseApiError({ detail: { code: "bad code!", message: "x" } }, 404).code).toBe("HTTP_404");
  });

  it("has a Vietnamese fallback for every status family", () => {
    for (const status of [400, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 502, 503, 504]) {
      expect(fallbackMessage("UNKNOWN_CODE", status)).toMatch(/[ạảãàáâấầẩẫậăắằẳẵặẹẻẽèéêếềểễệịỉĩìíọỏõòóôốồổỗộơớờởỡợụủũùúưứừửữựỳỷỹýđ]|Không|Yêu|Máy/);
    }
  });
});
