import type { SVGProps } from "react";
import { cn } from "./cn";

type DoodleProps = Omit<SVGProps<SVGSVGElement>, "aria-hidden">;

/** A small decorative pencil mark for page headers. */
export function PencilMark({ className, ...props }: DoodleProps) {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 64 64" className={cn("h-12 w-12", className)} {...props}>
      <path className="pencil-body" d="M13 47.5 16.2 35 39.5 11.7a5 5 0 0 1 7.1 0l5.7 5.7a5 5 0 0 1 0 7.1L29 47.8 16.5 51Z" fill="var(--s2l-ui-sky-100)" stroke="var(--s2l-ui-sky-600)" strokeWidth="2.4" strokeLinejoin="round" />
      <path className="pencil-lines" d="m34.8 16.4 12.8 12.8M16.2 35l12.8 12.8" fill="none" stroke="var(--s2l-ui-sky-600)" strokeWidth="2.2" strokeLinecap="round" />
      <path className="platform-pencil-band" d="m29.5 31.5 7.1 7.1" fill="none" stroke="var(--s2l-ui-primary-700)" strokeWidth="4" strokeLinecap="round" display="none" />
      <path className="pencil-tip" d="m13 47.5 3.5 3.5-4.7 1.2Z" fill="var(--s2l-ui-butter-500)" stroke="var(--s2l-ui-butter-600)" strokeWidth="1.5" strokeLinejoin="round" />
      <path className="pencil-spark" d="M9 15c3.2-2.4 6.4-2.4 9.6 0" fill="none" stroke="var(--s2l-ui-coral-600)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** A compact crayon stub for empty states and small decorative slots. */
export function CrayonStub({ className, ...props }: DoodleProps) {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 56 56" className={cn("h-10 w-10", className)} {...props}>
      <path d="m18 8 20 1 4 31-13 8-15-7Z" fill="var(--s2l-ui-butter-200)" stroke="var(--s2l-ui-butter-600)" strokeWidth="2.2" strokeLinejoin="round" />
      <path d="m18 8 7-4 13 5M14 41l15 7 13-8M20 15l18 1" fill="none" stroke="var(--s2l-ui-butter-600)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M24 23c4 2 7 2 11 0" fill="none" stroke="var(--s2l-ui-sky-600)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** A short hand-drawn underline for a calm accent. */
export function ScribbleUnderline({ className, ...props }: DoodleProps) {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 120 12" className={cn("h-3 w-24", className)} {...props}>
      <path d="M3 8c19-5 38 1 57-2 19-3 37-3 57 0" fill="none" stroke="var(--s2l-ui-butter-500)" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

/** A tiny cloud and sun doodle for use in compact empty states. */
export function CloudDoodle({ className, ...props }: DoodleProps) {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 64 48" className={cn("h-10 w-12", className)} {...props}>
      <circle cx="45" cy="14" r="7" fill="var(--s2l-ui-butter-200)" stroke="var(--s2l-ui-butter-600)" strokeWidth="1.8" />
      <path d="M12 36h35a8 8 0 0 0 .2-16 12 12 0 0 0-23-2 9 9 0 0 0-12 8 7 7 0 0 0-.2 10Z" fill="var(--s2l-ui-sky-100)" stroke="var(--s2l-ui-sky-600)" strokeWidth="2" strokeLinejoin="round" />
      <path d="M20 42h20" stroke="var(--s2l-ui-mint-600)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** A hand-drawn star with a short trail for review and permissions headers. */
export function StarScribble({ className, ...props }: DoodleProps) {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 48 48" className={cn("h-10 w-10", className)} {...props}>
      <path d="m24 5 4.7 11.4L41 18l-9.4 7.5 3 12L24 30.8l-10.6 6.7 3-12L7 18l12.3-1.6Z" fill="var(--s2l-ui-butter-200)" stroke="var(--s2l-ui-butter-600)" strokeWidth="2" strokeLinejoin="round" />
      <path d="M5 43c8-3 16-3 23-1m5-1 10-3" fill="none" stroke="var(--s2l-ui-sky-600)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** A small ruled guide mark for data and capacity headers. */
export function RulerDoodle({ className, ...props }: DoodleProps) {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 56 48" className={cn("h-10 w-10", className)} {...props}>
      <path d="m8 32 34-23 7 10-34 23Z" fill="var(--s2l-ui-sky-100)" stroke="var(--s2l-ui-sky-600)" strokeWidth="2" strokeLinejoin="round" />
      <path d="m19 35 4-3m3-5 3 4m3-8 4-3m3-5 3 4" fill="none" stroke="var(--s2l-ui-butter-600)" strokeWidth="2" strokeLinecap="round" />
      <path d="M6 12c3-2 6-2 9 0" fill="none" stroke="var(--s2l-ui-coral-600)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
