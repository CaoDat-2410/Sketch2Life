import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminBe1Error } from "../services/be1Client";
import { ParentGroupsPage } from "../pages/ParentGroupsPage";
import { parseParentPrincipalRefs } from "../pages/parentGroupInvitationBatch";
import { managerBusinessService, type ParentGroupMemberPage, type ParentGroupPage, type ParentGroupInvitation } from "../services/managerBusinessService";

const group = {
  contract: "ParentGroupV1" as const,
  parent_group_id: "group-1",
  organization_id: "org-qa",
  display_name: "Nhóm Lá",
  state: "ACTIVE" as const,
  created_at: "2026-11-17T00:00:00Z",
};

const groupPage: ParentGroupPage = { contract: "ParentGroupPageV1", items: [group], next_cursor: null };
const emptyMemberPage: ParentGroupMemberPage = {
  contract: "ParentGroupMemberListV1",
  items: [],
  counts: { invited: 0, accepted: 0, declined: 0, revoked: 0, expired: 0, total: 0 },
  next_cursor: null,
};

function invitationFor(groupId: string): ParentGroupInvitation {
  return {
    contract: "ParentGroupMembershipV1",
    membership_id: `membership-${groupId}`,
    parent_group_id: groupId,
    state: "INVITED",
    invited_at: "2026-11-25T10:00:00Z",
    expires_at: "2026-12-25T10:00:00Z",
    accepted_at: null,
    revision: 1,
  };
}

const originalClipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard");

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  if (originalClipboard) Object.defineProperty(navigator, "clipboard", originalClipboard);
  else Reflect.deleteProperty(navigator, "clipboard");
  window.sessionStorage.clear();
});

async function renderSelectedGroup() {
  vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue(groupPage);
  const members = vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(emptyMemberPage);
  render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
  const input = await screen.findByLabelText("Mã tài khoản phụ huynh") as HTMLTextAreaElement;
  await waitFor(() => expect(members).toHaveBeenCalledTimes(1));
  return { input, members };
}

function submitInvitationBatch() {
  fireEvent.click(screen.getByRole("button", { name: "Mời phụ huynh" }));
}

function invitationSummaryElement() {
  const summary = document.querySelector(".manager-business-parent-groups-invite-summary");
  if (!summary) throw new Error("Invitation summary was not rendered");
  return summary;
}

describe("Parent group invitation batch parsing", () => {
  it("splits lines, commas, semicolons, and spaces while trimming and dropping duplicates", () => {
    expect(parseParentPrincipalRefs(" parent:a, parent:b;\nparent:a\t parent:c "))
      .toEqual(["parent:a", "parent:b", "parent:c"]);
  });

  it("shows the 50 ID cap and sends nothing when there are 51 unique IDs", async () => {
    const { input, members } = await renderSelectedGroup();
    const invite = vi.spyOn(managerBusinessService, "inviteParentToGroup");
    const refs = Array.from({ length: 51 }, (_, index) => `parent:${index + 1}`);
    fireEvent.change(input, { target: { value: refs.join("\n") } });

    expect(screen.getByText("51 mã duy nhất · Tối đa 50 mã mỗi lần.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Mời phụ huynh" }));

    expect((await screen.findByRole("alert")).textContent).toContain("chưa gửi lời mời nào");
    expect(invite).not.toHaveBeenCalled();
    expect(members).toHaveBeenCalledTimes(1);
    expect(input.value).toBe(refs.join("\n"));
  });
});

describe("Parent group invitation batch behavior", () => {
  it("calls the existing invite service sequentially with a distinct key for each unique ID", async () => {
    let keyIndex = 0;
    vi.stubGlobal("crypto", { randomUUID: () => `batch-key-${++keyIndex}` });
    const { input, members } = await renderSelectedGroup();
    let finishFirst!: (value: ParentGroupInvitation) => void;
    const firstRequest = new Promise<ParentGroupInvitation>((resolve) => { finishFirst = resolve; });
    const invite = vi.spyOn(managerBusinessService, "inviteParentToGroup").mockImplementation((_groupId, ref) =>
      ref === "parent:first" ? firstRequest : Promise.resolve(invitationFor("group-1")),
    );
    fireEvent.change(input, { target: { value: "parent:first, parent:second; parent:first\nparent:third" } });
    submitInvitationBatch();

    await waitFor(() => expect(invite).toHaveBeenCalledTimes(1));
    expect(input.disabled).toBe(true);
    expect(invite.mock.calls[0]).toEqual(["group-1", "parent:first", "batch-key-1"]);
    finishFirst(invitationFor("group-1"));
    await waitFor(() => expect(invite).toHaveBeenCalledTimes(3));

    expect(invite.mock.calls).toEqual([
      ["group-1", "parent:first", "batch-key-1"],
      ["group-1", "parent:second", "batch-key-2"],
      ["group-1", "parent:third", "batch-key-3"],
    ]);
    await waitFor(() => expect(invitationSummaryElement().textContent).toContain("3 lời mời đã gửi"));
    expect(input.value).toBe("");
    expect(members).toHaveBeenCalledTimes(2);
    expect((screen.getByLabelText("Lọc trạng thái") as HTMLSelectElement).value).toBe("INVITED");
  });

  it("reuses a key after an unknown result and replaces it after a definite answer", async () => {
    let keyIndex = 0;
    vi.stubGlobal("crypto", { randomUUID: () => `retry-key-${++keyIndex}` });
    const { input } = await renderSelectedGroup();
    const invite = vi.spyOn(managerBusinessService, "inviteParentToGroup")
      .mockRejectedValueOnce(new AdminBe1Error("raw", 503, "SERVER_ERROR"))
      .mockRejectedValueOnce(new AdminBe1Error("raw", 422, "INVALID_REQUEST"))
      .mockResolvedValueOnce(invitationFor("group-1"));
    fireEvent.change(input, { target: { value: "parent:retry" } });

    submitInvitationBatch();
    fireEvent.click(await screen.findByRole("button", { name: "Gửi lại cùng yêu cầu" }));
    await waitFor(() => expect(invite).toHaveBeenCalledTimes(2));
    fireEvent.click(await screen.findByRole("button", { name: "Mời phụ huynh" }));
    await waitFor(() => expect(invite).toHaveBeenCalledTimes(3));

    expect(invite.mock.calls).toEqual([
      ["group-1", "parent:retry", "retry-key-1"],
      ["group-1", "parent:retry", "retry-key-1"],
      ["group-1", "parent:retry", "retry-key-2"],
    ]);
    expect(await screen.findByText(/Đã gửi lời mời · Hết hạn ngày/)).toBeTruthy();
    expect(input.value).toBe("");
  });

  it("shows per-ID results, removes only sent IDs, and refreshes once at the end", async () => {
    const { input, members } = await renderSelectedGroup();
    vi.spyOn(managerBusinessService, "inviteParentToGroup").mockImplementation(async (groupId, ref) => {
      if (ref === "parent:already") throw new AdminBe1Error("raw", 409, "INVITATION_EXISTS");
      if (ref === "parent:missing") throw new AdminBe1Error("raw", 404, "PARENT_NOT_FOUND");
      if (ref === "parent:bad") throw new AdminBe1Error("raw", 422, "INVALID_REQUEST");
      if (ref === "parent:unknown") throw new AdminBe1Error("raw", 503, "SERVER_ERROR");
      if (ref === "parent:other") throw new AdminBe1Error("raw", 400, "UNEXPECTED_ERROR");
      return invitationFor(groupId);
    });
    fireEvent.change(input, { target: { value: "parent:sent, parent:already; parent:missing\nparent:bad parent:unknown parent:other" } });
    submitInvitationBatch();

    const results = await screen.findByRole("list", { name: "Kết quả lời mời" });
    expect(within(results).getByText("parent:sent")).toBeTruthy();
    expect(within(results).getByText(`Đã gửi lời mời · Hết hạn ngày ${new Date("2026-12-25T10:00:00Z").toLocaleDateString("vi-VN")}`)).toBeTruthy();
    expect(within(results).getByText("Đã được mời hoặc đang là thành viên.")).toBeTruthy();
    expect(within(results).getByText("Không tìm thấy phụ huynh với mã này")).toBeTruthy();
    expect(within(results).getByText("Mã tài khoản phụ huynh chưa hợp lệ.")).toBeTruthy();
    expect(within(results).getByText("Chưa xác định được kết quả. Mã này được giữ lại để thử lại.")).toBeTruthy();
    expect(within(results).getByText("Không thể gửi lời mời cho mã này. Hãy thử lại sau.")).toBeTruthy();
    expect(results.textContent).not.toContain("PARENT_NOT_FOUND");
    expect(input.value).toBe("parent:already\nparent:missing\nparent:bad\nparent:unknown\nparent:other");
    await waitFor(() => expect(invitationSummaryElement().textContent).toContain("Đã xử lý 6 mã: 1 lời mời đã gửi"));
    await waitFor(() => expect(members).toHaveBeenCalledTimes(2));
  });

  it.each([
    { status: 409, code: "INVALID_TRANSITION", message: "Nhóm đã lưu trữ. Đã dừng gửi." },
    { status: 404, code: "RESOURCE_NOT_FOUND", message: "Không tìm thấy nhóm phụ huynh. Đã dừng gửi." },
    { status: 401, code: "AUTH_REQUIRED", message: "Phiên đăng nhập không còn hợp lệ. Đã dừng gửi; hãy đăng nhập lại." },
    { status: 403, code: "ACTION_NOT_ALLOWED", message: "Bạn không có quyền gửi lời mời vào nhóm này. Đã dừng gửi." },
  ])("stops the remaining IDs after a group or authorization failure ($status $code)", async ({ status, code, message }) => {
    const { input, members } = await renderSelectedGroup();
    const invite = vi.spyOn(managerBusinessService, "inviteParentToGroup")
      .mockRejectedValueOnce(new AdminBe1Error("raw server detail", status, code))
      .mockResolvedValueOnce(invitationFor("group-1"));
    fireEvent.change(input, { target: { value: "parent:first parent:second" } });
    submitInvitationBatch();

    await waitFor(() => expect(invitationSummaryElement().textContent).toContain(message));
    expect(invite).toHaveBeenCalledTimes(1);
    expect(input.value).toBe("parent:first\nparent:second");
    expect(screen.getByRole("list", { name: "Kết quả lời mời" }).textContent).toContain("Chưa gửi vì lô đã dừng.");
    expect(document.body.textContent).not.toContain(code);
    await waitFor(() => expect(members).toHaveBeenCalledTimes(2));
  });
});

describe("Parent group ID copy guidance", () => {
  it("copies the selected group ID and shows a short confirmation", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    await renderSelectedGroup();

    expect(screen.getByText("Giáo viên dán mã này tại Giáo án > Chia sẻ > Nhóm phụ huynh.")).toBeTruthy();
    expect(screen.getByText("group-1").className).toContain("manager-business-parent-group-id-value");
    fireEvent.click(screen.getByRole("button", { name: "Sao chép mã nhóm" }));

    expect(await screen.findByText("Đã sao chép mã nhóm.")).toBeTruthy();
    expect(writeText).toHaveBeenCalledWith("group-1");
  });

  it("keeps the ID selectable and explains when clipboard support is missing", async () => {
    Reflect.deleteProperty(navigator, "clipboard");
    await renderSelectedGroup();
    fireEvent.click(screen.getByRole("button", { name: "Sao chép mã nhóm" }));

    expect(await screen.findByText(/Không thể sao chép tự động trên trình duyệt này/)).toBeTruthy();
    expect(screen.getByText("group-1").className).toContain("manager-business-parent-group-id-value");
  });

  it("keeps the ID selectable and explains when clipboard writing is rejected", async () => {
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: vi.fn().mockRejectedValue(new Error("denied")) } });
    await renderSelectedGroup();
    fireEvent.click(screen.getByRole("button", { name: "Sao chép mã nhóm" }));

    expect(await screen.findByText(/Không thể sao chép tự động\. Mã nhóm bên trên vẫn có thể bôi đen/)).toBeTruthy();
    expect(screen.getByText("group-1").className).toContain("manager-business-parent-group-id-value");
  });
});
