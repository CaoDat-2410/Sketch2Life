import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "./cn";

export type CardTone = "default" | "subtle" | "success" | "warn" | "danger" | "info";

const tones: Record<CardTone, string> = {
  default: "border-rule bg-paper text-ink",
  subtle: "border-rule bg-paper-muted text-ink",
  success: "border-mint-soft bg-mint-soft text-mint-ink",
  warn: "border-butter-soft bg-butter-soft text-butter-ink",
  danger: "border-coral-soft bg-coral-soft text-coral-ink",
  info: "border-sky-soft bg-sky-soft text-sky-ink",
};

/** A warm surface with optional header and footer regions. */
export function Card({
  children,
  header,
  footer,
  tone = "default",
  className,
  ...props
}: HTMLAttributes<HTMLElement> & {
  children: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  tone?: CardTone;
}) {
  return (
    <article className={cn("box-border min-w-0 overflow-hidden rounded-cozy border shadow-cozy", tones[tone], className)} {...props}>
      {header != null && <div className="box-border border-b border-rule px-5 py-4">{header}</div>}
      <div className="box-border min-w-0 p-5">{children}</div>
      {footer != null && <div className="box-border border-t border-rule px-5 py-4">{footer}</div>}
    </article>
  );
}
