import type { ReactNode } from "react";
import { cn } from "./cn";
import { CrayonStub } from "./illustrations";

/** A compact empty state with a small decorative crayon and an optional action. */
export function EmptyState({
  title,
  description,
  action,
  illustration = <CrayonStub />,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  illustration?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("s2l-empty-state box-border flex min-w-0 items-center gap-4 px-4 py-5", className)}>
      {illustration && <span aria-hidden="true" className="grid size-12 shrink-0 place-items-center rounded-xl bg-butter-soft/70">{illustration}</span>}
      <div className="min-w-0 flex-1">
        <h3 className="m-0 font-ui text-sm font-bold leading-5 text-ink">{title}</h3>
        {description && <p className="mb-0 mt-1 font-ui text-xs leading-5 text-ink-soft">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
