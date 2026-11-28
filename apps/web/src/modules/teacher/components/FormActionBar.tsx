import type { ReactNode } from "react";
import { cn } from "../../../shared/ui/cn";

/** Shared Teacher form action bar: hint or destructive action on the left, quiet/secondary then primary on the right. */
export function FormActionBar({
  hint,
  danger,
  children,
  className,
}: {
  hint?: ReactNode;
  danger?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("tp-form-action-bar", className)}>
      {(danger || hint) && (
        <div className="tp-form-action-bar-lead">
          {danger && <div className="tp-form-action-danger">{danger}</div>}
          {hint && <p className="tp-form-action-hint">{hint}</p>}
        </div>
      )}
      <div className="tp-form-action-bar-buttons">{children}</div>
    </div>
  );
}
