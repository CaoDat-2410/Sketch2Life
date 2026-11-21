import type { ReactNode } from "react";
import { cn } from "./cn";

/** A compact page title row with an optional description and actions. */
export function PageHeader({
  title,
  description,
  actions,
  className,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("box-border flex min-w-0 flex-wrap items-center justify-between gap-4", className)}>
      <div className="min-w-0">
        <h1 className="m-0 font-ui text-2xl font-bold leading-tight tracking-tight text-ink sm:text-3xl">{title}</h1>
        {description && <p className="mb-0 mt-2 max-w-3xl font-ui text-sm leading-6 text-ink-soft">{description}</p>}
      </div>
      {actions && <div className="flex min-w-0 shrink-0 items-center gap-2 max-[620px]:w-full max-[620px]:justify-end">{actions}</div>}
    </header>
  );
}
