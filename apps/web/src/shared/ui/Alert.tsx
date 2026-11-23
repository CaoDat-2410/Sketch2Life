import type { ReactNode } from "react";
import { cn } from "./cn";

export type AlertTone = "info" | "success" | "warning" | "danger";

const tones: Record<AlertTone, string> = {
  info: "bg-primary-soft text-primary-ink",
  success: "bg-mint-soft text-mint-ink",
  warning: "bg-butter-soft text-butter-ink",
  danger: "bg-coral-soft text-coral-ink",
};

/** A calm, token-based notice with an explicit status or alert role. */
export function Alert({
  children,
  tone = "info",
  role = tone === "danger" ? "alert" : "status",
  icon,
  className,
}: {
  children: ReactNode;
  tone?: AlertTone;
  role?: "alert" | "status";
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <div role={role} className={cn("flex min-w-0 items-start gap-3 rounded-xl border border-rule px-4 py-3 font-ui text-sm leading-6", tones[tone], className)}>
      {icon && <span aria-hidden="true" className="mt-0.5 shrink-0">{icon}</span>}
      <div className="min-w-0">{children}</div>
    </div>
  );
}
