import { useId, type ReactNode } from "react";
import { cn } from "./cn";
import { ScribbleUnderline } from "./illustrations";

/** A titled content section with optional supporting copy and actions. */
export function Section({
  title,
  description,
  actions,
  children,
  variant = "surface",
  className,
}: {
  title: ReactNode;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  variant?: "surface" | "plain";
  className?: string;
}) {
  const headingId = useId();
  const plain = variant === "plain";
  return (
    <section aria-labelledby={headingId} className={cn(
      "box-border w-full min-w-0 max-w-full",
      plain ? "overflow-visible" : "overflow-hidden rounded-cozy border border-rule bg-paper shadow-cozy",
      className,
    )}>
      <header className={cn(
        "box-border flex min-w-0 items-start justify-between gap-4",
        plain ? "pb-3" : "border-b border-rule bg-paper-muted/60 px-5 py-4",
      )}>
        <div className="min-w-0">
          <h2 id={headingId} className="m-0 font-ui text-base font-bold leading-6 text-ink">{title}</h2>
          <ScribbleUnderline className="mt-1 h-2 w-11 text-butter" />
          {description && <p className="mb-0 mt-1 font-ui text-sm leading-5 text-ink-soft">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
      </header>
      <div className="box-border min-w-0">{children}</div>
    </section>
  );
}
