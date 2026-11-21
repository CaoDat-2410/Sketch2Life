import type { ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { cn } from "./cn";
import type { StatusTone } from "./StatusBadge";

export type StatAccent = "primary" | "sky" | "mint" | "butter" | "coral" | "neutral";
export type TrendDirection = "up" | "down" | "flat";

const accents: Record<StatAccent, string> = {
  primary: "bg-primary-soft text-primary-ink",
  sky: "bg-sky-soft text-sky-ink",
  mint: "bg-mint-soft text-mint-ink",
  butter: "bg-butter-soft text-butter-ink",
  coral: "bg-coral-soft text-coral-ink",
  neutral: "bg-neutral-soft text-neutral-ink",
};

const trendTones: Record<StatusTone, string> = {
  success: "text-mint-ink",
  warn: "text-butter-ink",
  danger: "text-coral-ink",
  info: "text-sky-ink",
  neutral: "text-ink-soft",
};

/** A compact metric tile with an icon chip, optional trend, helper, and loading state. */
export function StatCard({
  label,
  value,
  icon,
  accent = "primary",
  badge,
  trend,
  helperText,
  loading = false,
  className,
}: {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  accent?: StatAccent;
  badge?: ReactNode;
  trend?: { direction: TrendDirection; delta: string; tone?: StatusTone };
  helperText?: string;
  loading?: boolean;
  className?: string;
}) {
  const TrendIcon = trend?.direction === "up" ? ArrowUpRight : trend?.direction === "down" ? ArrowDownRight : Minus;
  const numericValue = typeof value === "number"
    || (typeof value === "string" && /^[\d.,\s\u00a0]+$/u.test(value.trim()));
  return (
    <article aria-busy={loading || undefined} className={cn("pa-stat-card box-border flex w-full min-w-0 max-w-full flex-col gap-4 rounded-cozy border border-rule bg-paper p-4 shadow-cozy transition-[box-shadow,transform] duration-200 ease-out hover:shadow-cozy-hover motion-reduce:transition-none", className)}>
      <div className="flex min-w-0 flex-col items-start gap-2">
        <div className="flex min-w-0 items-center gap-3">
          {icon && <span aria-hidden="true" className={cn("pa-stat-icon grid size-10 shrink-0 place-items-center rounded-xl", accents[accent])}>{icon}</span>}
          <p className="m-0 min-w-0 font-ui text-sm font-semibold leading-5 text-ink-soft">{label}</p>
        </div>
        {badge}
      </div>
      <div className="min-w-0">
        {loading ? (
          <div aria-hidden="true" className="h-8 w-24 animate-pulse rounded-lg bg-paper-muted motion-reduce:animate-none" />
        ) : (
          <div className="flex min-w-0 flex-wrap items-baseline justify-between gap-2">
            <p className={cn(
              "pa-stat-value m-0 min-w-0 break-words font-ui tabular-nums text-ink",
              numericValue ? "text-2xl font-bold leading-8" : "text-lg font-semibold leading-6",
            )}>{value}</p>
            {trend && <span className={cn("inline-flex shrink-0 items-center gap-1 font-ui text-xs font-semibold", trendTones[trend.tone ?? "neutral"])}>
              <TrendIcon aria-hidden="true" className="size-4" />{trend.delta}
            </span>}
          </div>
        )}
        {helperText && <p className="mb-0 mt-2 font-ui text-xs leading-5 text-ink-soft">{helperText}</p>}
      </div>
    </article>
  );
}
