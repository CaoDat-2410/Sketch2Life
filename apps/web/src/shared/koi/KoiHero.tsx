import { useEffect, useRef, useState, useSyncExternalStore, type CSSProperties } from "react";
import koiModelUrl from "../assets/sketch2life-koi.glb?url";
import koiStillUrl from "../assets/sketch2life-koi-still.webp?url";
import "./KoiHero.css";

const REDUCED_MOTION = "(prefers-reduced-motion: reduce)";
const BUBBLE_COUNT = 14;

function subscribeReducedMotion(onChange: () => void) {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return () => undefined;
  const query = window.matchMedia(REDUCED_MOTION);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

function prefersReducedMotion() {
  return typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(REDUCED_MOTION).matches;
}

function supportsWebGL() {
  return typeof window !== "undefined" && typeof window.WebGLRenderingContext === "function";
}

const BUBBLES: Array<{ far: boolean; style: CSSProperties }> = Array.from({ length: BUBBLE_COUNT }, (_, index) => {
  const size = 5 + ((index * 5) % 13);
  return {
    far: index % 3 === 0,
    style: {
      left: `${8 + ((index * 37) % 86)}%`,
      width: size,
      height: size,
      animationDelay: `${-index * 0.9}s`,
      animationDuration: `${7 + (index % 5)}s`,
    },
  };
});

/**
 * Decorative 3D koi. It fills its positioned parent, never takes pointer events and shows nothing
 * while the model loads. The still picture appears only when motion or WebGL is not available.
 */
export function KoiHero({ className }: { className?: string }) {
  const host = useRef<HTMLDivElement>(null);
  const reducedMotion = useSyncExternalStore(subscribeReducedMotion, prefersReducedMotion, () => false);
  const [failed, setFailed] = useState(false);
  const [live, setLive] = useState(false);
  const still = failed || reducedMotion || !supportsWebGL();

  useEffect(() => {
    const element = host.current;
    if (still || !element) return;
    let cancelled = false;
    let dispose: (() => void) | undefined;
    import("./koiScene")
      .then(({ mountKoiScene }) => {
        if (cancelled) return;
        dispose = mountKoiScene({
          host: element,
          modelUrl: koiModelUrl,
          onReady: () => { if (!cancelled) setLive(true); },
          onFail: () => { if (!cancelled) setFailed(true); },
        });
      })
      .catch(() => { if (!cancelled) setFailed(true); });
    return () => {
      cancelled = true;
      dispose?.();
      setLive(false);
    };
  }, [still]);

  return (
    <div
      ref={host}
      className={"s2l-koi" + (className ? " " + className : "")}
      data-koi-state={still ? "still" : live ? "live" : "loading"}
      aria-hidden="true"
    >
      {still && <img className="s2l-koi-still" src={koiStillUrl} alt="" decoding="async" draggable={false} />}
      {!reducedMotion && BUBBLES.map((bubble, index) => (
        <i key={index} className={bubble.far ? "s2l-koi-bubble is-far" : "s2l-koi-bubble"} style={bubble.style} />
      ))}
    </div>
  );
}

export default KoiHero;
