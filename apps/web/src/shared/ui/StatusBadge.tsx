import type { ReactNode } from "react";
import { cn } from "./cn";

export type StatusTone = "success" | "warn" | "danger" | "info" | "neutral";
export type StatusBadgeSize = "sm" | "md";

const tones: Record<StatusTone, { badge: string; dot: string }> = {
  success: { badge: "border-mint-soft bg-mint-soft text-mint-ink", dot: "bg-mint" },
  warn: { badge: "border-butter-soft bg-butter-soft text-butter-ink", dot: "bg-butter" },
  danger: { badge: "border-coral-soft bg-coral-soft text-coral-ink", dot: "bg-coral" },
  info: { badge: "border-sky-soft bg-sky-soft text-sky-ink", dot: "bg-sky" },
  neutral: { badge: "border-rule bg-neutral-soft text-neutral-ink", dot: "bg-neutral-base" },
};

/** A readable status label whose tone is never its only signal. */
export function StatusBadge({
  children,
  tone,
  dot = false,
  icon,
  size = "md",
  className,
}: {
  children: ReactNode;
  tone: StatusTone;
  dot?: boolean;
  icon?: ReactNode;
  size?: StatusBadgeSize;
  className?: string;
}) {
  const palette = tones[tone];
  return (
    <span data-tone={tone} className={cn(
      "s2l-status-badge box-border inline-flex w-fit max-w-full shrink-0 items-center gap-1.5 whitespace-nowrap rounded-cozy-pill border font-ui font-semibold leading-4",
      palette.badge,
      size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs",
      className,
    )}>
      {icon}
      {dot && !icon && <span aria-hidden="true" className={cn("size-1.5 shrink-0 rounded-full", palette.dot)} />}
      <span className="min-w-0 shrink-0 whitespace-nowrap">{children}</span>
    </span>
  );
}
