import React from "react";

/** Sketch2Life mark: a fresh drawing page with a stroke that turns into a story spark. */
export function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" focusable="false">
      <rect x="1" y="1" width="46" height="46" rx="13" fill="var(--brand-primary, #315efb)" />
      <path d="M12 10.5h17.2l7 7v19H12a2 2 0 0 1-2-2v-22a2 2 0 0 1 2-2Z" fill="#fff" />
      <path d="M29 10.5v6a1 1 0 0 0 1 1h6" fill="none" stroke="#c8d8ff" strokeWidth="1.7" />
      <path d="M15.5 28.5c2.5-4.3 4.5 4.2 7.4 0s4.2-5.1 7.2-2.3" fill="none" stroke="var(--brand-primary, #315efb)" strokeWidth="2.8" strokeLinecap="round" />
      <path d="m33.3 20.1 1.3 2.8 2.9 1.3-2.9 1.2-1.3 2.9-1.2-2.9-2.9-1.2 2.9-1.3 1.2-2.8Z" fill="var(--brand-warm, #f4c84e)" />
    </svg>
  );
}

export function BrandWordmark({ size = 28, iconOnly = false }: { size?: number; iconOnly?: boolean }) {
  return (
    <span className="s2l-wordmark" aria-label="Sketch2Life" style={{ fontSize: Math.round(size * 0.58) }}>
      <BrandMark size={size} />
      {!iconOnly && <span>Sketch2Life</span>}
    </span>
  );
}
