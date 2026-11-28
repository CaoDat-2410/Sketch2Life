import { createPortal, flushSync } from "react-dom";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";

export interface SlidePresenterRenderState {
  isPresenting: boolean;
  trigger: ReactNode;
}

interface SlidePresenterProps {
  revisionLabel: string;
  slideIndex: number;
  slideCount: number;
  onPrevious: () => void;
  onNext: () => void;
  children: (state: SlidePresenterRenderState) => ReactNode;
}

function getFocusableElements(root: HTMLElement): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(
    'button:not(:disabled):not([tabindex="-1"]), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), iframe, [tabindex]:not([tabindex="-1"])',
  )).filter((element) => !element.closest('[aria-hidden="true"]'));
}

export function SlidePresenter({ revisionLabel, slideIndex, slideCount, onPrevious, onNext, children }: SlidePresenterProps) {
  const [isPresenting, setIsPresenting] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const placeholderRef = useRef<HTMLDivElement>(null);
  const [portalHost] = useState(() => { const host = document.createElement("div"); host.style.display = "contents"; return host; });

  useLayoutEffect(() => {
    (isPresenting ? document.body : placeholderRef.current)?.appendChild(portalHost);
    return () => { portalHost.remove(); };
  }, [isPresenting, portalHost]);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const exitRef = useRef<HTMLButtonElement>(null);
  const openRef = useRef(false);
  const enteredFullscreenRef = useRef(false);

  const close = useCallback(() => {
    openRef.current = false;
    setIsPresenting(false);
    const root = rootRef.current;
    if (root && document.fullscreenElement === root && document.exitFullscreen) {
      void document.exitFullscreen().catch(() => undefined);
    }
    window.setTimeout(() => triggerRef.current?.focus(), 0);
  }, []);

  const open = () => {
    if (slideCount === 0 || openRef.current) return;
    openRef.current = true;
    enteredFullscreenRef.current = false;
    flushSync(() => setIsPresenting(true));
    const root = rootRef.current;
    root?.classList.add("is-open");
    if (!root?.requestFullscreen) return;
    try {
      const request = root.requestFullscreen();
      void request.then(() => {
        if (!openRef.current && document.fullscreenElement === root && document.exitFullscreen) {
          return document.exitFullscreen().catch(() => undefined);
        }
        return undefined;
      }).catch(() => undefined);
    } catch {
      // The fixed full-window presentation remains usable when fullscreen is unavailable.
    }
  };

  useLayoutEffect(() => {
    if (isPresenting) exitRef.current?.focus();
  }, [isPresenting]);

  useEffect(() => {
    if (!isPresenting) return undefined;
    const root = rootRef.current;
    if (!root) return undefined;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return;
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        if (slideIndex > 0) onPrevious();
        return;
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        if (slideIndex < slideCount - 1) onNext();
        return;
      }
      if (event.key !== "Tab") return;

      const focusable = getFocusableElements(root);
      if (focusable.length === 0) {
        event.preventDefault();
        root.focus();
        return;
      }
      const activeIndex = focusable.indexOf(document.activeElement as HTMLElement);
      event.preventDefault();
      if (event.shiftKey) focusable[activeIndex <= 0 ? focusable.length - 1 : activeIndex - 1]?.focus();
      else focusable[activeIndex < 0 || activeIndex >= focusable.length - 1 ? 0 : activeIndex + 1]?.focus();
    };

    const onFocusIn = (event: FocusEvent) => {
      if (!root.contains(event.target as Node)) exitRef.current?.focus();
    };

    const onFullscreenChange = () => {
      if (document.fullscreenElement === root) enteredFullscreenRef.current = true;
      else if (enteredFullscreenRef.current && openRef.current) close();
    };

    document.addEventListener("keydown", onKeyDown, true);
    document.addEventListener("focusin", onFocusIn, true);
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => {
      document.removeEventListener("keydown", onKeyDown, true);
      document.removeEventListener("focusin", onFocusIn, true);
      document.removeEventListener("fullscreenchange", onFullscreenChange);
    };
  }, [close, isPresenting, onNext, onPrevious, slideCount, slideIndex]);

  useEffect(() => () => {
    const root = rootRef.current;
    if (root && document.fullscreenElement === root && document.exitFullscreen) {
      void document.exitFullscreen().catch(() => undefined);
    }
  }, []);

  const content = (
    <div
      ref={rootRef}
      className={`tp-presenter-root${isPresenting ? " is-open" : ""}`}
      role={isPresenting ? "dialog" : undefined}
      aria-modal={isPresenting || undefined}
      aria-label={isPresenting ? `Trình chiếu · ${revisionLabel}` : undefined}
      tabIndex={isPresenting ? -1 : undefined}
    >
      {isPresenting && (
        <>
          <div className="tp-slide-presenter-topbar">
            <h2>Trình chiếu · {revisionLabel}</h2>
            <button ref={exitRef} type="button" className="s2l-button" onClick={close}>Thoát</button>
          </div>
          <div className="tp-slide-presenter-controls">
            <button type="button" className="s2l-button" disabled={slideIndex <= 0} onClick={onPrevious}>Slide trước</button>
            <span aria-live="polite">Slide {slideIndex + 1} / {slideCount}</span>
            <button type="button" className="s2l-button" disabled={slideIndex >= slideCount - 1} onClick={onNext}>Slide sau</button>
          </div>
        </>
      )}
      {children({
        isPresenting,
        trigger: (
          <button
            ref={triggerRef}
            type="button"
            className="s2l-button tp-presenter-trigger"
            aria-hidden={isPresenting || undefined}
            tabIndex={isPresenting ? -1 : undefined}
            disabled={slideCount === 0}
            onClick={open}
          >
            Trình chiếu
          </button>
        ),
      })}
    </div>
  );
  return <><div ref={placeholderRef} style={{ display: "contents" }} />{createPortal(content, portalHost)}</>;
}
