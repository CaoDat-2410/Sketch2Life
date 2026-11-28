import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";

const STORAGE_KEY_PREFIX = "sketch2life:session-draft:v1:";

export type SessionDraftAuth = {
  getCurrentUser: () => { uid: string } | null;
  observe: (callback: (user: { uid: string } | null) => void) => () => void;
};

let lastKnownOwner: string | null | undefined;

function sessionStorageOrNull(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

function ownerId(auth: SessionDraftAuth): string | null {
  try {
    const value = auth.getCurrentUser()?.uid;
    return typeof value === "string" && value ? value : null;
  } catch {
    return null;
  }
}

function storageKey(namespace: string, owner: string | null, organizationId?: string | null): string | null {
  if (!owner || organizationId === null) return null;
  const organizationPart = organizationId === undefined ? "" : `:${encodeURIComponent(organizationId)}`;
  return `${STORAGE_KEY_PREFIX}${encodeURIComponent(namespace)}:${encodeURIComponent(owner)}${organizationPart}`;
}

function memoryScopeKey(namespace: string, owner: string | null, authResolved: boolean, organizationId?: string | null): string {
  const identity = owner ? `account:${owner}` : authResolved ? "signed-out" : "auth-pending";
  const organization = organizationId === undefined ? "no-organization" : organizationId ?? "organization-unavailable";
  return `${namespace}\u0000${identity}\u0000${organization}`;
}

function copyDraft<T extends Record<string, unknown>>(value: T): T {
  return { ...value };
}

function readDraft<T extends Record<string, unknown>>(key: string | null, initial: T): T {
  const storage = sessionStorageOrNull();
  if (!key || !storage) return copyDraft(initial);
  try {
    const raw = storage.getItem(key);
    if (!raw) return copyDraft(initial);
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return copyDraft(initial);
    return { ...initial, ...(parsed as Partial<T>) };
  } catch {
    return copyDraft(initial);
  }
}

function writeDraft<T extends Record<string, unknown>>(key: string | null, value: T): void {
  const storage = sessionStorageOrNull();
  if (!key || !storage) return;
  try {
    storage.setItem(key, JSON.stringify(value));
  } catch {
    // Keep the form usable when browser storage is blocked or full.
  }
}

function removeDraft(key: string | null): void {
  const storage = sessionStorageOrNull();
  if (!key || !storage) return;
  try {
    storage.removeItem(key);
  } catch {
    // Ignore unavailable browser storage.
  }
}

/** Clear saved form drafts before a session ends or changes accounts. */
export function clearSessionScopedDrafts(): void {
  lastKnownOwner = null;
  const storage = sessionStorageOrNull();
  if (!storage) return;
  try {
    for (let index = storage.length - 1; index >= 0; index -= 1) {
      const key = storage.key(index);
      if (key?.startsWith(STORAGE_KEY_PREFIX)) storage.removeItem(key);
    }
  } catch {
    // Ignore unavailable browser storage.
  }
}

/** Retain a non-secret form draft for this account, and optionally this organization, in this tab. */
export function useSessionScopedDraft<T extends Record<string, unknown>>(
  namespace: string,
  initial: T,
  auth: SessionDraftAuth,
  organizationId?: string | null,
): [T, Dispatch<SetStateAction<T>>, () => void] {
  const initialRef = useRef<T>(copyDraft(initial));
  const organizationRef = useRef(organizationId);
  organizationRef.current = organizationId;

  const [owner, setOwner] = useState<string | null>(() => {
    const seededOwner = ownerId(auth);
    if (seededOwner && lastKnownOwner !== undefined && lastKnownOwner !== seededOwner) {
      clearSessionScopedDrafts();
    }
    if (seededOwner) lastKnownOwner = seededOwner;
    return seededOwner;
  });
  const ownerRef = useRef(owner);
  ownerRef.current = owner;
  const authResolvedRef = useRef(owner !== null);
  const generationRef = useRef(0);
  const [generation, setGeneration] = useState(0);
  const touchedBeforeAuthRef = useRef(new Set<string>());

  const scopeKey = memoryScopeKey(namespace, owner, authResolvedRef.current, organizationId);
  const [storedDraft, setStoredDraft] = useState(() => ({
    scopeKey,
    value: readDraft(storageKey(namespace, owner, organizationId), initialRef.current),
  }));
  const value = storedDraft.scopeKey === scopeKey
    ? storedDraft.value
    : readDraft(storageKey(namespace, owner, organizationId), initialRef.current);
  const valueRef = useRef(value);
  valueRef.current = value;

  useEffect(() => {
    let active = true;
    let unsubscribe: () => void = () => undefined;
    try {
      unsubscribe = auth.observe((user) => {
        if (!active) return;
        const nextOwner = user?.uid && typeof user.uid === "string" ? user.uid : null;
        const previousOwner = ownerRef.current;
        const wasResolved = authResolvedRef.current;
        const resolvingInitialOwner = previousOwner === null && !wasResolved;

        if (nextOwner === previousOwner) {
          if (nextOwner) {
            authResolvedRef.current = true;
            lastKnownOwner = nextOwner;
            return;
          }
          if (!wasResolved) {
            clearSessionScopedDrafts();
            authResolvedRef.current = true;
            touchedBeforeAuthRef.current.clear();
            valueRef.current = copyDraft(initialRef.current);
            setStoredDraft({
              scopeKey: memoryScopeKey(namespace, null, true, organizationRef.current),
              value: valueRef.current,
            });
            generationRef.current += 1;
            setGeneration(generationRef.current);
          }
          return;
        }

        if (!nextOwner) {
          clearSessionScopedDrafts();
          ownerRef.current = null;
          authResolvedRef.current = true;
          touchedBeforeAuthRef.current.clear();
          valueRef.current = copyDraft(initialRef.current);
          setOwner(null);
          setStoredDraft({
            scopeKey: memoryScopeKey(namespace, null, true, organizationRef.current),
            value: valueRef.current,
          });
          generationRef.current += 1;
          setGeneration(generationRef.current);
          return;
        }

        const organization = organizationRef.current;
        let nextValue: T;
        if (resolvingInitialOwner) {
          const priorOwner = lastKnownOwner;
          if (priorOwner !== undefined && priorOwner !== nextOwner) clearSessionScopedDrafts();
          nextValue = readDraft(storageKey(namespace, nextOwner, organization), initialRef.current);
          for (const field of touchedBeforeAuthRef.current) {
            if (Object.prototype.hasOwnProperty.call(valueRef.current, field)) {
              nextValue[field as keyof T] = valueRef.current[field as keyof T];
            }
          }
        } else {
          clearSessionScopedDrafts();
          nextValue = copyDraft(initialRef.current);
        }

        ownerRef.current = nextOwner;
        authResolvedRef.current = true;
        lastKnownOwner = nextOwner;
        const shouldPersistEarlyEdits = resolvingInitialOwner && touchedBeforeAuthRef.current.size > 0;
        touchedBeforeAuthRef.current.clear();
        valueRef.current = nextValue;
        if (shouldPersistEarlyEdits) writeDraft(storageKey(namespace, nextOwner, organization), nextValue);
        setOwner(nextOwner);
        setStoredDraft({
          scopeKey: memoryScopeKey(namespace, nextOwner, true, organization),
          value: nextValue,
        });
        generationRef.current += 1;
        setGeneration(generationRef.current);
      });
    } catch {
      // An unavailable auth observer should not prevent editing the form.
    }
    return () => {
      active = false;
      unsubscribe();
    };
  }, [auth, namespace]);

  const setDraft = useCallback<Dispatch<SetStateAction<T>>>((next) => {
    if (generationRef.current !== generation) return;
    const previous = valueRef.current;
    const updated = typeof next === "function"
      ? (next as (current: T) => T)(previous)
      : next;
    const currentOwner = ownerRef.current;
    const authResolved = authResolvedRef.current;
    if (currentOwner === null && !authResolved) {
      const keys = new Set([...Object.keys(previous), ...Object.keys(updated)]);
      for (const key of keys) {
        if (!Object.is(previous[key], updated[key])) touchedBeforeAuthRef.current.add(key);
      }
    }
    valueRef.current = updated;
    const currentScope = memoryScopeKey(namespace, currentOwner, authResolved, organizationRef.current);
    setStoredDraft({ scopeKey: currentScope, value: updated });
    writeDraft(storageKey(namespace, currentOwner, organizationRef.current), updated);
  }, [generation, namespace]);

  const clearDraft = useCallback(() => {
    if (generationRef.current !== generation) return;
    const currentOwner = ownerRef.current;
    const currentOrganization = organizationRef.current;
    removeDraft(storageKey(namespace, currentOwner, currentOrganization));
    touchedBeforeAuthRef.current.clear();
    valueRef.current = copyDraft(initialRef.current);
    setStoredDraft({
      scopeKey: memoryScopeKey(namespace, currentOwner, authResolvedRef.current, currentOrganization),
      value: valueRef.current,
    });
  }, [generation, namespace]);

  return [value, setDraft, clearDraft];
}
