import { useEffect, useRef, useState, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { authService } from "../../modules/school-manager/be1/services/authService";
import { clearAiWorkflowSession } from "../../modules/teacher/services/aiWorkflowSession";
import { clearSvgDraftRequests } from "../../modules/teacher/services/svgDraftRequests";
import { AccessibleDialog } from "../components/ui";
import { usePortalSession } from "./PortalSessionContext";

const IDLE = 30 * 60_000;
const MAX_AGE = 12 * 60 * 60_000;
const LEASE = 75_000;
const SLEEP_GAP = 120_000;
export const EXPIRY_NOTICE_EVENT = "s2l-session-expiry";
const NOTICE = "s2l-session-expiry-notice";
export const expiryMessages = {
  idle: "Bạn đã được đăng xuất vì không hoạt động trong 30 phút. Vui lòng đăng nhập lại.",
  age: "Phiên đăng nhập đã quá 12 giờ. Vui lòng đăng nhập lại.",
} as const;
type Reason = keyof typeof expiryMessages;
const tabId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
const memory = new Map<string, string>();
function get(key: string) { try { return localStorage.getItem(key) ?? memory.get(key) ?? null; } catch { return memory.get(key) ?? null; } }
function put(key: string, value: string) { memory.set(key, value); try { localStorage.setItem(key, value); } catch { /* storage can be unavailable */ } }
function entries(prefix: string): [string, string][] {
  const values = new Map(memory);
  try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k?.startsWith(prefix)) { const v = localStorage.getItem(k); if (v !== null) values.set(k, v); } } } catch { /* use local memory */ }
  return [...values].filter(([k]) => k.startsWith(prefix));
}
function saveNotice(reason: Reason) { try { sessionStorage.setItem(NOTICE, reason); } catch { memory.set(NOTICE, reason); } window.dispatchEvent(new Event(EXPIRY_NOTICE_EVENT)); }
export function takeExpiryNotice() {
  let value: string | null = null;
  try { value = sessionStorage.getItem(NOTICE); sessionStorage.removeItem(NOTICE); } catch { value = memory.get(NOTICE) ?? null; memory.delete(NOTICE); }
  return value === "idle" || value === "age" ? expiryMessages[value] : "";
}
export function sessionStatus(now: number, signedIn: number, activity: number, leaseEnds: number[]) {
  const protectedNow = leaseEnds.some((end) => end > now);
  const last = Math.max(signedIn, activity, ...leaseEnds.map((end) => Math.min(now, end)));
  if (!protectedNow && now - signedIn >= MAX_AGE) return { reason: "age" as const, remaining: 0 };
  if (!protectedNow && now - last >= IDLE) return { reason: "idle" as const, remaining: 0 };
  return { reason: null, remaining: protectedNow ? IDLE : IDLE - (now - last) };
}
function roleForPath(path: string) { return path.startsWith("/school") ? "manager" : path.startsWith("/platform") ? "admin" : "teacher"; }
function presenting() {
  return !!document.querySelector('[data-s2l-presenting="true"]') || [...document.querySelectorAll("video")].some((video) => !video.paused && !video.ended);
}

export function SessionLimitGuard({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = usePortalSession();
  const [readyEpoch, setReadyEpoch] = useState(0);
  const portalEpoch = useRef(0);
  const wasPortal = useRef(false);
  const pathRef = useRef(location.pathname); pathRef.current = location.pathname;
  const navigateRef = useRef(navigate); navigateRef.current = navigate;
  const logoutRef = useRef(logout); logoutRef.current = logout;
  const [remaining, setRemaining] = useState(IDLE);
  const isPortal = /^\/(teacher|school|platform)(\/|$)/.test(location.pathname) && !/\/(login|sign-in)$/.test(location.pathname);
  if (isPortal && !wasPortal.current) portalEpoch.current++;
  wasPortal.current = isPortal;
  const epoch = portalEpoch.current;
  useEffect(() => {
    if (!isPortal) { setRemaining(IDLE); return; }
    let cleanup = () => {};
    let active = true;
    let checkPreviousExpiry = () => {};
    let generation = 0;
    const unsubscribe = authService.observe((user) => {
      const current = ++generation;
      cleanup();
      cleanup = () => {};
      if (!active) return;
      if (!user) { checkPreviousExpiry(); setReadyEpoch(epoch); return; }
      void (async () => {
      let signedIn: number;
      try {
        signedIn = Date.parse((await user.getIdTokenResult()).authTime);
        if (!Number.isFinite(signedIn)) throw new Error("Invalid auth time");
      } catch { signedIn = Date.parse(user.metadata.lastSignInTime ?? ""); }
      if (!active || current !== generation) return;
      const start = Number.isFinite(signedIn) ? signedIn : 0;
      const prefix = `s2l-limit:${encodeURIComponent(user.uid)}:${start}:`;
      const activityPrefix = `${prefix}activity:`;
      const leasePrefix = `${prefix}lease:`;
      const eventKey = `${prefix}expired`;
      const activityKey = activityPrefix + tabId;
      const leaseKey = leasePrefix + tabId;
      let stopped = false;
      let lastWrite = 0;
      let hadLease = false;
      let lastLeaseWrite = 0;
      let lastEvaluation = -Infinity;
      let pendingActivity = false;
      const force = (reason: Reason, broadcast: boolean) => {
        if (stopped) return;
        stopped = true;
        if (broadcast) put(eventKey, reason);
        saveNotice(reason);
        clearAiWorkflowSession();
        clearSvgDraftRequests();
        logoutRef.current();
        if (!window.sketch2lifeAuth?.signOut) void authService.logout().catch(() => undefined);
        navigateRef.current(`/login?role=${roleForPath(pathRef.current)}`, { replace: true });
      };
      checkPreviousExpiry = () => {
        const reason = get(eventKey);
        if (reason === "idle" || reason === "age") force(reason, false);
      };
      const check = (activity = false) => {
        if (stopped) return;
        activity ||= pendingActivity;
        pendingActivity = false;
        const existing = get(eventKey);
        if (existing === "idle" || existing === "age") { force(existing, false); return; }
        const now = Date.now();
        lastEvaluation = now;
        const slept = hadLease && now - lastLeaseWrite > SLEEP_GAP;
        if (slept) { put(leaseKey, String(lastLeaseWrite)); hadLease = false; }
        const activities = entries(activityPrefix).map(([, v]) => Number(v)).filter(Number.isFinite);
        const leases = entries(leasePrefix).map(([, v]) => Number(v)).filter(Number.isFinite);
        const protectedHere = presenting();
        const status = sessionStatus(now, start, Math.max(start, ...activities), hadLease ? [...leases, now + 1] : leases);
        if (status.reason) { force(status.reason, true); return; }
        if (protectedHere) {
          if (!hadLease || now - lastLeaseWrite >= 1000) { put(leaseKey, String(now + LEASE)); lastLeaseWrite = now; }
          hadLease = true;
        } else if (hadLease) {
          put(leaseKey, String(now)); hadLease = false;
          const afterEnd = sessionStatus(now, start, Math.max(start, ...activities), entries(leasePrefix).map(([, v]) => Number(v)).filter(Number.isFinite));
          if (afterEnd.reason) { force(afterEnd.reason, true); return; }
          put(activityKey, String(now));
        }
        if (activity && now - lastWrite >= 1000) { put(activityKey, String(now)); lastWrite = now; }
        setRemaining(Math.ceil((protectedHere || activity ? IDLE : status.remaining) / 1000) * 1000);
        setReadyEpoch(epoch);
      };
      const onActivity = (event: Event) => {
        if (["pointermove", "scroll", "wheel", "touchmove"].includes(event.type) && Date.now() - lastEvaluation < 1000) { pendingActivity = true; return; }
        check(true);
      };
      const releaseLease = () => { if (hadLease) { put(leaseKey, String(Date.now())); hadLease = false; } };
      const onCheck = () => check();
      const onStorage = (event: StorageEvent) => { if (event.key?.startsWith(prefix)) check(); };
      const events = ["pointerdown", "pointermove", "keydown", "wheel", "scroll", "touchstart", "touchmove"] as const;
      check();
      if (stopped) return;
      events.forEach((event) => window.addEventListener(event, onActivity, { passive: true }));
      window.addEventListener("focus", onCheck); window.addEventListener("pageshow", onCheck); window.addEventListener("pagehide", releaseLease); window.addEventListener("storage", onStorage);
      document.addEventListener("visibilitychange", onCheck);
      document.addEventListener("play", onCheck, true); document.addEventListener("pause", onCheck, true); document.addEventListener("ended", onCheck, true);
      const observer = new MutationObserver(onCheck); observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["data-s2l-presenting"] });
      const timer = window.setInterval(onCheck, 1000);
      cleanup = () => {
        window.clearInterval(timer); observer.disconnect();
        events.forEach((event) => window.removeEventListener(event, onActivity));
        window.removeEventListener("focus", onCheck); window.removeEventListener("pageshow", onCheck); window.removeEventListener("pagehide", releaseLease); window.removeEventListener("storage", onStorage);
        document.removeEventListener("visibilitychange", onCheck); document.removeEventListener("play", onCheck, true); document.removeEventListener("pause", onCheck, true); document.removeEventListener("ended", onCheck, true);
        releaseLease();
      };
      })();
    });
    return () => { active = false; unsubscribe(); cleanup(); };
  }, [isPortal, epoch]);
  if (isPortal && readyEpoch !== epoch) return <main role="status">Đang kiểm tra phiên đăng nhập…</main>;
  return <>{children}<AccessibleDialog open={isPortal && remaining <= 60_000} onOpenChange={() => {}} title="Phiên đăng nhập sắp hết hạn" description="Phiên sẽ kết thúc nếu bạn không hoạt động." showTitle showDescription showClose={false}>
    <p aria-live="polite">Bạn sẽ được đăng xuất sau {Math.ceil(remaining / 1000)} giây.</p>
    <button type="button" className="s2l-button is-primary" onClick={() => window.dispatchEvent(new Event("pointerdown"))}>Tiếp tục đăng nhập</button>
  </AccessibleDialog></>;
}
