import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, configure, fireEvent, render, screen, waitFor } from "@testing-library/react";
import * as backendApi from "../../../../shared/api/backendApi";
import { authService } from "../services/authService";
import { TeacherInvitationsPanel } from "../pages/TeacherInvitationsPanel";

configure({ asyncUtilTimeout: 8000 });

interface FetchCall {
  url: string;
  init: RequestInit;
}

const createdInvitation = {
  account_ref: "account-reference-123456",
  status: "PENDING_VERIFICATION" as const,
};

let requests: FetchCall[];
let queuedResponses: Array<Response | Error>;
let idempotencySequence: number;

function response(body: unknown, status = 202): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function queueJson(body: unknown, status = 202): void {
  queuedResponses.push(response(body, status));
}

function queueApiError(code: string, message: string, status: number): void {
  queueJson({ detail: { code, message } }, status);
}

function emailInput(): HTMLInputElement {
  return screen.getByRole("textbox", { name: "Email giáo viên" }) as HTMLInputElement;
}

function enterEmail(value = "mai@example.com"): void {
  fireEvent.change(emailInput(), { target: { value } });
}

function submitInvite(): void {
  fireEvent.click(screen.getByRole("button", { name: "Gửi lời mời" }));
}

function idempotencyKey(call: FetchCall): string | null {
  return new Headers(call.init.headers).get("Idempotency-Key");
}

beforeEach(() => {
  requests = [];
  queuedResponses = [];
  idempotencySequence = 0;
  vi.stubEnv("VITE_BE1_BASE_URL", "https://be1.example.test/");
  vi.stubEnv("VITE_BE1_ORGANIZATION_ID", "org-qa");
  vi.spyOn(authService, "getIdToken").mockResolvedValue("test-token");
  vi.spyOn(backendApi, "createIdempotencyKey").mockImplementation(
    () => `invitation-test-key-${++idempotencySequence}`,
  );
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    requests.push({ url: String(input), init });
    const next = queuedResponses.shift() ?? response(createdInvitation);
    if (next instanceof Error) throw next;
    return next;
  }));
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("TeacherInvitationsPanel", () => {
  it("sends the exact invite body and idempotency header", async () => {
    queueJson(createdInvitation);
    render(<TeacherInvitationsPanel />);
    enterEmail("mai@example.com");
    submitInvite();

    expect(await screen.findByText(/Đã gửi lời mời\. Trạng thái: chờ xác minh\./)).toBeTruthy();
    expect(requests).toHaveLength(1);
    expect(requests[0].url).toBe("https://be1.example.test/api/be1/v1/organizations/org-qa/teacher-invitations");
    expect(requests[0].init.method).toBe("POST");
    expect(JSON.parse(String(requests[0].init.body))).toEqual({ email: "mai@example.com" });
    expect(idempotencyKey(requests[0])).toBe("invitation-test-key-1");
  });

  it("blocks an invalid email before sending", () => {
    render(<TeacherInvitationsPanel />);
    enterEmail("not-an-email");
    expect(screen.getByText("Nhập email hợp lệ, từ 3 đến 254 ký tự.")).toBeTruthy();
    submitInvite();
    expect(requests).toHaveLength(0);
  });

  it("maps setup conflict without revealing whether an account exists", async () => {
    queueApiError("ACCOUNT_SETUP_UNAVAILABLE", "An account already exists for mai@example.com", 409);
    render(<TeacherInvitationsPanel />);
    enterEmail("mai@example.com");
    submitInvite();

    expect(await screen.findByText("Không thể gửi lời mời đến email này.")).toBeTruthy();
    expect(screen.queryByText(/already exists|account exists/i)).toBeNull();
  });

  it("rotates the key after an idempotency mismatch", async () => {
    queueApiError("INVALID_IDEMPOTENCY_KEY", "raw server message", 400);
    queueJson(createdInvitation);
    render(<TeacherInvitationsPanel />);
    enterEmail("mai@example.com");
    submitInvite();
    expect(await screen.findByText(/tạo khóa mới/)).toBeTruthy();

    submitInvite();
    expect(await screen.findByText(/Đã gửi lời mời\. Trạng thái: chờ xác minh\./)).toBeTruthy();
    expect(requests).toHaveLength(2);
    expect(idempotencyKey(requests[0])).toBe("invitation-test-key-1");
    expect(idempotencyKey(requests[1])).toBe("invitation-test-key-2");
  });

  it("keeps the key after a 503 and allows retry", async () => {
    queueApiError("IDENTITY_PROVIDER_UNAVAILABLE", "raw provider message", 503);
    queueJson(createdInvitation);
    render(<TeacherInvitationsPanel />);
    enterEmail("mai@example.com");
    submitInvite();
    expect(await screen.findByText("Dịch vụ đang tạm gián đoạn. Hãy thử lại cùng thao tác.")).toBeTruthy();

    submitInvite();
    expect(await screen.findByText(/Đã gửi lời mời\. Trạng thái: chờ xác minh\./)).toBeTruthy();
    expect(requests).toHaveLength(2);
    expect(idempotencyKey(requests[1])).toBe(idempotencyKey(requests[0]));
  });

  it("resends an invitation from this session with an empty body", async () => {
    queueJson(createdInvitation);
    queueJson(createdInvitation);
    render(<TeacherInvitationsPanel />);
    enterEmail("mai@example.com");
    submitInvite();
    await screen.findByText(/Đã gửi lời mời\. Trạng thái: chờ xác minh\./);

    fireEvent.click(screen.getByRole("button", { name: "Gửi lại lời mời" }));
    expect(await screen.findByText(/Đã gửi lại lời mời\. Trạng thái: chờ xác minh\./)).toBeTruthy();
    expect(requests).toHaveLength(2);
    expect(requests[1].url).toBe(
      "https://be1.example.test/api/be1/v1/organizations/org-qa/teacher-invitations/account-reference-123456/resend",
    );
    expect(requests[1].init.method).toBe("POST");
    expect(requests[1].init.body).toBeUndefined();
    expect(idempotencyKey(requests[1])).toBe("invitation-test-key-2");
    expect(requests[1].url).not.toContain("mai@example.com");
  });

  it("sends only once on a double click", async () => {
    let finishRequest!: (value: Response) => void;
    const pendingResponse = new Promise<Response>((resolve) => { finishRequest = resolve; });
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init: RequestInit = {}) => {
      requests.push({ url: String(input), init });
      return pendingResponse;
    }));
    render(<TeacherInvitationsPanel />);
    enterEmail("mai@example.com");
    const button = screen.getByRole("button", { name: "Gửi lời mời" });
    fireEvent.click(button);
    fireEvent.click(button);

    await waitFor(() => expect(requests).toHaveLength(1));
    finishRequest(response(createdInvitation));
    expect(await screen.findByText(/Đã gửi lời mời\. Trạng thái: chờ xác minh\./)).toBeTruthy();
    expect(requests).toHaveLength(1);
  });

  it("clears the email after success and shows only its masked form and a short reference", async () => {
    queueJson(createdInvitation);
    render(<TeacherInvitationsPanel />);
    enterEmail("mai@example.com");
    submitInvite();

    expect(await screen.findByText(/Đã gửi lời mời\. Trạng thái: chờ xác minh\./)).toBeTruthy();
    expect(emailInput().value).toBe("");
    expect(screen.getByText("Email: m…@example.com")).toBeTruthy();
    expect(screen.getByText("Mã lời mời:")).toBeTruthy();
    expect(screen.getByText("account-…3456")).toBeTruthy();
    expect(screen.queryByText(createdInvitation.account_ref)).toBeNull();
    expect(screen.queryByText("mai@example.com")).toBeNull();
    expect(screen.getByRole("button", { name: "Gửi lại lời mời" })).toBeTruthy();
  });
});
