import { StrictMode, useEffect } from "react";
import { WebPortalLoginPage } from "./WebPortalLoginPage";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, Link, useLocation } from "react-router-dom";
import { SessionLimitGuard, expiryMessages, takeExpiryNotice } from "./SessionLimitGuard";

type TestUser = { uid: string; metadata: { lastSignInTime: string }; getIdTokenResult: () => Promise<{ authTime: string }> };
const mocks = vi.hoisted(() => ({ user: null as TestUser | null, logout: vi.fn(), firebaseLogout: vi.fn(async () => {}), ai: vi.fn(), svg: vi.fn(), observer: null as null | ((user: TestUser | null) => void), deferred: false }));
vi.mock("../../modules/school-manager/be1/services/authService", () => ({ authService: { observe: (cb: (user: typeof mocks.user) => void) => { mocks.observer = cb; if (!mocks.deferred) cb(mocks.user); return () => {}; }, logout: mocks.firebaseLogout } }));
vi.mock("../../modules/teacher/services/aiWorkflowSession", () => ({ clearAiWorkflowSession: mocks.ai }));
vi.mock("../../modules/teacher/services/svgDraftRequests", () => ({ clearSvgDraftRequests: mocks.svg }));
vi.mock("./PortalSessionContext", () => ({ usePortalSession: () => ({ logout: mocks.logout }) }));
const base = Date.parse("2026-11-28T00:00:00Z");
let serial = 0;
function Login() { const location = useLocation(); return <div>login{location.search}</div>; }
async function mount(path = "/teacher/home", signedIn = base) {
  mocks.user = { uid: `test-${serial++}`, metadata: { lastSignInTime: new Date(signedIn).toUTCString() }, getIdTokenResult: async () => ({ authTime: new Date(signedIn).toUTCString() }) };
  await act(async () => { render(<MemoryRouter initialEntries={[path]}><SessionLimitGuard><Routes><Route path="/login" element={<Login />} /><Route path="*" element={<div>portal</div>} /></Routes></SessionLimitGuard></MemoryRouter>); });
}
function jump(ms: number, event = "focus") { act(() => { vi.setSystemTime(base + ms); window.dispatchEvent(new Event(event)); }); }
beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(base); localStorage.clear(); sessionStorage.clear(); vi.clearAllMocks(); mocks.deferred = false; mocks.observer = null; });
afterEach(() => { cleanup(); vi.useRealTimers(); });

describe("session limits", () => {

  it("waits on portal entry and preserves the mounted page during navigation", async () => {
    mocks.deferred = true;
    mocks.user = { uid: `nav-${serial++}`, metadata: { lastSignInTime: new Date(base).toUTCString() }, getIdTokenResult: async () => ({ authTime: new Date(base).toUTCString() }) };
    let mounts = 0;
    function Page() { useEffect(() => { mounts++; }, []); return <><span>persistent page</span><Link to="/teacher/other">next</Link></>; }
    render(<MemoryRouter initialEntries={["/login"]}><SessionLimitGuard><Routes><Route path="/login" element={<Link to="/teacher/home">enter</Link>} /><Route path="/teacher/*" element={<Page />} /></Routes></SessionLimitGuard></MemoryRouter>);
    fireEvent.click(screen.getByText("enter"));
    expect(screen.queryByText("persistent page")).toBeNull();
    expect(screen.getByRole("status")).toBeTruthy();
    await act(async () => { mocks.observer!(mocks.user); });
    expect(mounts).toBe(1);
    fireEvent.click(screen.getByText("next"));
    expect(mounts).toBe(1); expect(screen.queryByRole("status")).toBeNull();
  });
  it("uses token auth time instead of account metadata and falls back offline", async () => {
    mocks.deferred = true; vi.setSystemTime(base + 31 * 60_000);
    render(<MemoryRouter initialEntries={["/teacher/home"]}><SessionLimitGuard><Routes><Route path="/login" element={<div>login</div>} /><Route path="*" element={<div>portal</div>} /></Routes></SessionLimitGuard></MemoryRouter>);
    const user = { uid: `auth-${serial++}`, metadata: { lastSignInTime: new Date(base + 31 * 60_000).toUTCString() }, getIdTokenResult: async () => ({ authTime: new Date(base).toUTCString() }) };
    await act(async () => { mocks.observer!(user); });
    expect(screen.getByText(/^login/)).toBeTruthy();
    cleanup(); sessionStorage.clear();
    render(<MemoryRouter initialEntries={["/teacher/home"]}><SessionLimitGuard><div>portal</div></SessionLimitGuard></MemoryRouter>);
    await act(async () => { mocks.observer!({ ...user, uid: `offline-${serial++}`, getIdTokenResult: async () => { throw Error("offline"); } }); });
    expect(screen.getByText("portal")).toBeTruthy();
  });
  it("ignores a stale token result after the observed user changes", async () => {
    mocks.deferred = true; let resolve!: (value: { authTime: string }) => void;
    const pending = new Promise<{ authTime: string }>(r => { resolve = r; });
    render(<MemoryRouter initialEntries={["/teacher/home"]}><SessionLimitGuard><div>portal</div></SessionLimitGuard></MemoryRouter>);
    const user = { uid: `change-${serial++}`, metadata: { lastSignInTime: new Date(base).toUTCString() }, getIdTokenResult: () => pending };
    await act(async () => { mocks.observer!(user); mocks.observer!({ ...user, uid: `new-${serial++}`, getIdTokenResult: async () => ({ authTime: new Date(base).toUTCString() }) }); });
    await act(async () => { resolve({ authTime: new Date(base - 3600_000).toUTCString() }); });
    expect(screen.getByText("portal")).toBeTruthy(); expect(mocks.logout).not.toHaveBeenCalled();
  });
  it("expires after sleep even while a presentation remains open", async () => {
    await mount(); const marker = document.createElement("div"); marker.dataset.s2lPresenting = "true";
    act(() => { document.body.appendChild(marker); window.dispatchEvent(new Event("focus")); });
    jump(31 * 60_000); expect(screen.getByText(/^login/)).toBeTruthy(); marker.remove();
  });
  it("renews a 75 second lease and releases it on pagehide", async () => {
    await mount(); const marker = document.createElement("div"); marker.dataset.s2lPresenting = "true";
    act(() => { document.body.appendChild(marker); window.dispatchEvent(new Event("focus")); });
    const key = Object.keys(localStorage).find(k => k.includes(":lease:"))!;
    expect(Number(localStorage.getItem(key))).toBe(base + 75_000);
    act(() => { vi.advanceTimersByTime(60_000); }); expect(Number(localStorage.getItem(key))).toBe(base + 135_000);
    act(() => { window.dispatchEvent(new Event("pagehide")); }); expect(Number(localStorage.getItem(key))).toBe(base + 60_000); marker.remove();
  });
  it.each(["idle", "age"] as const)("shows the %s reason once on the real login page in StrictMode", async reason => {
    const start = reason === "age" ? base - 12 * 60 * 60_000 : base - 31 * 60_000;
    mocks.user = { uid: `notice-${serial++}`, metadata: { lastSignInTime: new Date(start).toUTCString() }, getIdTokenResult: async () => ({ authTime: new Date(start).toUTCString() }) };
    await act(async () => { render(<StrictMode><MemoryRouter initialEntries={["/teacher/home"]}><SessionLimitGuard><Routes><Route path="/login" element={<WebPortalLoginPage portalRole="TEACHER" onRoleChange={() => {}} onAuthenticate={async () => {}} onResetPassword={async () => {}} />} /><Route path="*" element={<div>portal</div>} /></Routes></SessionLimitGuard></MemoryRouter></StrictMode>); });
    expect(screen.getAllByText(expiryMessages[reason])).toHaveLength(1); expect(takeExpiryNotice()).toBe("");
  });

  it("shows a formatted countdown and focuses the continue button", async () => {
    await mount(); jump(29 * 60_000);
    const dialog = screen.getByRole("dialog", { name: "Phiên đăng nhập sắp hết hạn", description: "Bạn đã không thao tác một lúc. Phiên sẽ tự đăng xuất khi hết giờ." });
    expect(dialog.textContent).toContain("1:00");
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Tiếp tục đăng nhập" }));
    expect(screen.getByRole("button", { name: "Đăng xuất" })).toBeTruthy();
    jump(29 * 60_000 + 51_000); expect(dialog.textContent).toContain("0:09");
  });
  it.each([["/teacher/home", "teacher"], ["/school/classes", "manager"], ["/platform/accounts", "admin"]])("manually signs out from %s after pointer down", async (path, role) => {
    await mount(path); jump(29 * 60_000);
    const button = screen.getByRole("button", { name: "Đăng xuất" });
    fireEvent.pointerDown(button); expect(screen.getByRole("dialog")).toBeTruthy();
    fireEvent.click(button);
    expect(screen.getByText(`login?role=${role}`)).toBeTruthy();
    expect(mocks.logout).toHaveBeenCalledOnce(); expect(mocks.firebaseLogout).toHaveBeenCalledOnce();
    expect(mocks.ai).toHaveBeenCalledOnce(); expect(mocks.svg).toHaveBeenCalledOnce(); expect(takeExpiryNotice()).toBe("");
  });
  it("keeps the dialog open for keyboard activation of manual sign-out", async () => {
    await mount(); jump(29 * 60_000);
    const button = screen.getByRole("button", { name: "Đăng xuất" });
    button.focus(); fireEvent.keyDown(button, { key: "Enter", code: "Enter" });
    expect(screen.getByRole("dialog")).toBeTruthy();
    fireEvent.click(button); fireEvent.keyUp(button, { key: "Enter", code: "Enter" });
    expect(screen.getByText("login?role=teacher")).toBeTruthy(); expect(takeExpiryNotice()).toBe("");
  });
  it("warns at 29 minutes, accepts activity and signs out after 30 minutes", async () => {
    await mount(); jump(29 * 60_000); expect(screen.getByRole("dialog")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Tiếp tục đăng nhập" })); expect(screen.queryByRole("dialog")).toBeNull();
    jump(59 * 60_000); expect(screen.getByText(/^login/)).toBeTruthy(); expect(mocks.logout).toHaveBeenCalled(); expect(mocks.firebaseLogout).toHaveBeenCalled(); expect(mocks.ai).toHaveBeenCalled(); expect(takeExpiryNotice()).toBe(expiryMessages.idle);
  });
  it.each(["/teacher/home", "/school/classes", "/platform/accounts"])("expires %s at startup before displaying the portal", async (path) => {
    vi.setSystemTime(base + 31 * 60_000); await mount(path); expect(screen.queryByText("portal")).toBeNull(); expect(screen.getByText(/^login/)).toBeTruthy(); expect(takeExpiryNotice()).toBe(expiryMessages.idle);
  });
  it("uses other-tab activity and detects sleep before the first mouse movement", async () => {
    await mount(); const prefix = `s2l-limit:${mocks.user!.uid}:${base}:`; localStorage.setItem(`${prefix}activity:other`, String(base + 25 * 60_000));
    jump(31 * 60_000); expect(screen.getByText("portal")).toBeTruthy();
    act(() => { vi.setSystemTime(base + 56 * 60_000); window.dispatchEvent(new Event("pointermove")); }); expect(screen.getByText(/^login/)).toBeTruthy();
  });
  it("pauses for a presentation and expires the maximum age after it closes", async () => {
    await mount(); const marker = document.createElement("div"); marker.dataset.s2lPresenting = "true"; act(() => { document.body.appendChild(marker); window.dispatchEvent(new Event("focus")); });
    act(() => { vi.advanceTimersByTime(12 * 60 * 60_000); });
    expect(screen.getByText("portal")).toBeTruthy();
    act(() => { marker.remove(); window.dispatchEvent(new Event("focus")); }); expect(screen.getByText(/^login/)).toBeTruthy(); expect(takeExpiryNotice()).toBe(expiryMessages.age);
  });
  it("honors another tab's lease and expiry reason", async () => {
    await mount(); const prefix = `s2l-limit:${mocks.user!.uid}:${base}:`; localStorage.setItem(`${prefix}lease:other`, String(base + 31 * 60_000 + 5000)); jump(31 * 60_000); expect(screen.getByText("portal")).toBeTruthy();
    act(() => { localStorage.setItem(`${prefix}expired`, "age"); window.dispatchEvent(new StorageEvent("storage", { key: `${prefix}expired`, newValue: "age" })); });
    expect(screen.getByText(/^login/)).toBeTruthy(); expect(takeExpiryNotice()).toBe(expiryMessages.age); expect(takeExpiryNotice()).toBe("");
  });
  it("keeps a playing video active and enforces the age limit when it pauses", async () => {
    await mount(); const video = document.createElement("video"); let paused = false;
    Object.defineProperty(video, "paused", { get: () => paused });
    act(() => { document.body.appendChild(video); video.dispatchEvent(new Event("play")); });
    act(() => { vi.advanceTimersByTime(12 * 60 * 60_000); }); expect(screen.getByText("portal")).toBeTruthy();
    act(() => { paused = true; video.dispatchEvent(new Event("pause")); });
    expect(screen.getByText(/^login/)).toBeTruthy(); expect(takeExpiryNotice()).toBe(expiryMessages.age); video.remove();
  });
  it("pauses idle time while a video plays and resumes after it pauses", async () => {
    await mount(); const video = document.createElement("video"); let paused = false;
    Object.defineProperty(video, "paused", { get: () => paused });
    act(() => { document.body.appendChild(video); video.dispatchEvent(new Event("play")); });
    act(() => { vi.advanceTimersByTime(31 * 60_000); }); expect(screen.getByText("portal")).toBeTruthy();
    act(() => { paused = true; video.dispatchEvent(new Event("pause")); });
    jump(60 * 60_000); expect(screen.getByRole("dialog")).toBeTruthy();
    jump(61 * 60_000); expect(screen.getByText(/^login/)).toBeTruthy(); video.remove();
  });
  it("defers the maximum age while another tab has a live lease", async () => {
    await mount(); const prefix = `s2l-limit:${mocks.user!.uid}:${base}:`; const age = 12 * 60 * 60_000;
    localStorage.setItem(`${prefix}lease:other`, String(base + age + 5000));
    jump(age); expect(screen.getByText("portal")).toBeTruthy();
    jump(age + 5000); expect(screen.getByText(/^login/)).toBeTruthy(); expect(takeExpiryNotice()).toBe(expiryMessages.age);
  });
  it("throttles continuous activity while retaining it for the next check", async () => {
    await mount(); jump(20 * 60_000);
    const getter = vi.spyOn(Storage.prototype, "getItem");
    for (let i = 0; i < 20; i++) fireEvent.pointerMove(window);
    expect(getter).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(1000); });
    jump(48 * 60_000); expect(screen.queryByRole("dialog")).toBeNull();
    getter.mockRestore();
  });
  it("keeps the warning open while the user moves or tabs towards a button", async () => {
    await mount(); jump(29 * 60_000);
    fireEvent.pointerMove(window); fireEvent.wheel(window); fireEvent.keyDown(window, { key: "Tab" }); fireEvent.keyDown(window, { key: "Shift" });
    act(() => { vi.advanceTimersByTime(2000); });
    expect(screen.getByRole("dialog")).toBeTruthy();
  });
  it("resets the warning on keyboard activity", async () => {
    await mount(); jump(29 * 60_000); fireEvent.keyDown(window, { key: "a" }); expect(screen.queryByRole("dialog")).toBeNull();
    jump(58 * 60_000); expect(screen.getByRole("dialog")).toBeTruthy();
  });
  it("checks hidden-tab wake-up before accepting a key press", async () => {
    await mount(); act(() => { vi.setSystemTime(base + 31 * 60_000); document.dispatchEvent(new Event("visibilitychange")); });
    expect(screen.getByText(/^login/)).toBeTruthy();
  });
  it("expires at 12 hours despite recent activity", async () => {
    await mount(); const prefix = `s2l-limit:${mocks.user!.uid}:${base}:`; localStorage.setItem(`${prefix}activity:other`, String(base + 12 * 60 * 60_000 - 1000));
    jump(12 * 60 * 60_000); expect(screen.getByText(/^login/)).toBeTruthy(); expect(takeExpiryNotice()).toBe(expiryMessages.age);
  });
  it("continues locally when storage throws", async () => {
    const getter = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    const setter = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    await mount(); jump(29 * 60_000); expect(screen.getByRole("dialog")).toBeTruthy();
    getter.mockRestore(); setter.mockRestore();
  });
  it("does not apply an old sign-in's records to a new sign-in", async () => {
    localStorage.setItem(`s2l-limit:test-${serial}:${base - 3600_000}:expired`, "idle"); await mount(); expect(screen.getByText("portal")).toBeTruthy();
  });
});
