import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { clearSessionScopedDrafts, useSessionScopedDraft, type SessionDraftAuth } from "./useSessionScopedDraft";

type Draft = { name: string };

function authHarness(initialUser: { uid: string } | null = null) {
  let currentUser = initialUser;
  let listener: ((user: { uid: string } | null) => void) | undefined;
  const auth: SessionDraftAuth = {
    getCurrentUser: () => currentUser,
    observe: (callback) => {
      listener = callback;
      return () => { if (listener === callback) listener = undefined; };
    },
  };
  return {
    auth,
    emit(user: { uid: string } | null) {
      currentUser = user;
      act(() => listener?.(user));
    },
  };
}

function DraftProbe({ auth, organizationId }: { auth: SessionDraftAuth; organizationId: string | null }) {
  const [draft, setDraft, clearDraft] = useSessionScopedDraft<Draft>("manager:test", { name: "" }, auth, organizationId);
  return <>
    <label>Name<input aria-label="Draft name" value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} /></label>
    <button type="button" onClick={clearDraft}>Clear draft</button>
  </>;
}

beforeEach(() => {
  window.sessionStorage.clear();
  clearSessionScopedDrafts();
});

afterEach(() => {
  cleanup();
  clearSessionScopedDrafts();
  window.sessionStorage.clear();
  vi.restoreAllMocks();
});

describe("useSessionScopedDraft", () => {
  it("keeps an early field edit while auth resolves and restores it for the same account and organization", () => {
    const key = "sketch2life:session-draft:v1:manager%3Atest:manager-one:school-one";
    window.sessionStorage.setItem(key, JSON.stringify({ name: "Saved account draft" }));
    const session = authHarness();
    const view = render(<DraftProbe auth={session.auth} organizationId="school-one" />);

    fireEvent.change(screen.getByLabelText("Draft name"), { target: { value: "Typed before auth resolves" } });
    session.emit({ uid: "manager-one" });
    expect((screen.getByLabelText("Draft name") as HTMLInputElement).value).toBe("Typed before auth resolves");
    expect(JSON.parse(window.sessionStorage.getItem(key) ?? "{}")).toEqual({ name: "Typed before auth resolves" });

    view.unmount();
    render(<DraftProbe auth={session.auth} organizationId="school-one" />);
    expect((screen.getByLabelText("Draft name") as HTMLInputElement).value).toBe("Typed before auth resolves");
  });

  it("does not show a draft under another organization and clears it on account change or sign-out", () => {
    const session = authHarness({ uid: "manager-one" });
    const view = render(<DraftProbe auth={session.auth} organizationId="school-one" />);
    fireEvent.change(screen.getByLabelText("Draft name"), { target: { value: "School one draft" } });
    const schoolOneKey = "sketch2life:session-draft:v1:manager%3Atest:manager-one:school-one";
    expect(window.sessionStorage.getItem(schoolOneKey)).toContain("School one draft");

    view.rerender(<DraftProbe auth={session.auth} organizationId="school-two" />);
    expect((screen.getByLabelText("Draft name") as HTMLInputElement).value).toBe("");
    session.emit({ uid: "manager-two" });
    expect((screen.getByLabelText("Draft name") as HTMLInputElement).value).toBe("");
    expect(Array.from({ length: window.sessionStorage.length }, (_, index) => window.sessionStorage.key(index) ?? "")
      .some((key) => key.startsWith("sketch2life:session-draft:v1:"))).toBe(false);

    fireEvent.change(screen.getByLabelText("Draft name"), { target: { value: "Manager two draft" } });
    session.emit(null);
    expect((screen.getByLabelText("Draft name") as HTMLInputElement).value).toBe("");
    expect(window.sessionStorage.length).toBe(0);
  });

  it("keeps editing available when sessionStorage operations throw and clears on cancel", () => {
    const session = authHarness({ uid: "manager-one" });
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("storage blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("storage blocked"); });
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => { throw new Error("storage blocked"); });
    render(<DraftProbe auth={session.auth} organizationId="school-one" />);

    fireEvent.change(screen.getByLabelText("Draft name"), { target: { value: "Still editable" } });
    expect((screen.getByLabelText("Draft name") as HTMLInputElement).value).toBe("Still editable");
    fireEvent.click(screen.getByRole("button", { name: "Clear draft" }));
    expect((screen.getByLabelText("Draft name") as HTMLInputElement).value).toBe("");
  });
});
