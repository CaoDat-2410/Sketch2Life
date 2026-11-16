import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

export type WebPortalRole = "TEACHER" | "MANAGER" | "ADMIN";
export type SessionToastKind = "ok" | "info" | "warn" | "err";
export type SessionToast = { kind: SessionToastKind; text: string };

interface PortalSessionValue {
  currentRole: WebPortalRole;
  isAuthenticated: boolean;
  toast: SessionToast | null;
  loginAsRole: (role: WebPortalRole) => void;
  logout: () => void;
  showToast: (text: string, kind?: SessionToastKind) => void;
  clearToast: () => void;
}

const ROLE_STORAGE_KEY = "s2l-web-role";
const AUTH_STORAGE_KEY = "s2l-web-authenticated";
const SESSION_SOURCE_KEY = "s2l-web-session-source";
const VERIFIED_SESSION_SOURCE = "firebase-role-verified-v1";
const PortalSessionContext = createContext<PortalSessionValue | null>(null);

function isPortalRole(value: string | null): value is WebPortalRole {
  return value === "TEACHER" || value === "MANAGER" || value === "ADMIN";
}

function readSession() {
  if (typeof window === "undefined") return { role: "TEACHER" as WebPortalRole, authenticated: false };
  const role = window.sessionStorage.getItem(ROLE_STORAGE_KEY);
  const verified = isPortalRole(role)
    && window.sessionStorage.getItem(AUTH_STORAGE_KEY) === "true"
    && window.sessionStorage.getItem(SESSION_SOURCE_KEY) === VERIFIED_SESSION_SOURCE;
  if (!verified) {
    window.sessionStorage.removeItem(ROLE_STORAGE_KEY);
    window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
    window.sessionStorage.removeItem(SESSION_SOURCE_KEY);
    return { role: "TEACHER" as WebPortalRole, authenticated: false };
  }
  return { role, authenticated: true };
}

function roleLabel(role: WebPortalRole) {
  if (role === "TEACHER") return "Giáo viên";
  if (role === "MANAGER") return "School Manager";
  return "Platform Admin";
}

export function PortalSessionProvider({ children }: { children: React.ReactNode }) {
  const [initial] = useState(readSession);
  const [currentRole, setCurrentRole] = useState<WebPortalRole>(initial.role);
  const [isAuthenticated, setIsAuthenticated] = useState(initial.authenticated);
  const [toast, setToast] = useState<SessionToast | null>(null);

  const clearToast = useCallback(() => setToast(null), []);
  const showToast = useCallback((text: string, kind: SessionToastKind = "info") => {
    setToast({ kind, text });
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timeout = window.setTimeout(() => setToast(null), 4200);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  const loginAsRole = useCallback((role: WebPortalRole) => {
    setCurrentRole(role);
    setIsAuthenticated(true);
    window.sessionStorage.setItem(ROLE_STORAGE_KEY, role);
    window.sessionStorage.setItem(AUTH_STORAGE_KEY, "true");
    window.sessionStorage.setItem(SESSION_SOURCE_KEY, VERIFIED_SESSION_SOURCE);
    showToast("Phiên " + roleLabel(role) + " đã được xác minh.", "ok");
  }, [showToast]);

  const logout = useCallback(() => {
    setIsAuthenticated(false);
    window.sessionStorage.removeItem(ROLE_STORAGE_KEY);
    window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
    window.sessionStorage.removeItem(SESSION_SOURCE_KEY);
    const signOut = window.sketch2lifeAuth?.signOut;
    if (signOut) void signOut().catch(() => undefined);
    showToast("Đã đăng xuất.", "info");
  }, [showToast]);

  const value = useMemo(() => ({
    currentRole,
    isAuthenticated,
    toast,
    loginAsRole,
    logout,
    showToast,
    clearToast,
  }), [currentRole, isAuthenticated, toast, loginAsRole, logout, showToast, clearToast]);

  return <PortalSessionContext.Provider value={value}>{children}</PortalSessionContext.Provider>;
}

export function usePortalSession() {
  const value = useContext(PortalSessionContext);
  if (!value) throw new Error("usePortalSession must be used inside PortalSessionProvider.");
  return value;
}