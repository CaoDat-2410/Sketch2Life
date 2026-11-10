import React from "react";
import brandArtworkUrl from "./assets/sketch2life-brand-art-20261110.jpg";

export function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <img
      className="s2l-brandmark"
      src={brandArtworkUrl}
      width={size}
      height={size}
      alt="Vẽ cùng Heo 3D — Sketch2Life"
      decoding="async"
      draggable={false}
    />
  );
}

export function BrandWordmark({ size = 28, iconOnly = false }: { size?: number; iconOnly?: boolean }) {
  const artworkSize = Math.min(84, Math.max(iconOnly ? 48 : 56, size * (iconOnly ? 1.6 : 2)));
  return (
    <span className={"s2l-wordmark" + (iconOnly ? " is-icon-only" : "")}>
      <BrandMark size={artworkSize} />
    </span>
  );
}