import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { LoaderCircle } from "lucide-react";
import { cn } from "./cn";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const variants: Record<ButtonVariant, string> = {
  primary: "border-transparent bg-primary text-on-primary shadow-cozy enabled:hover:bg-primary-hover disabled:border-rule disabled:bg-primary-soft disabled:text-neutral-ink disabled:shadow-none",
  secondary: "border-rule bg-paper text-ink enabled:hover:bg-paper-muted disabled:bg-primary-soft disabled:text-ink-soft",
  ghost: "border-transparent bg-transparent text-ink-soft enabled:hover:bg-paper-muted enabled:hover:text-ink disabled:bg-neutral-soft disabled:text-neutral-ink",
  danger: "border-transparent bg-danger-base text-on-primary shadow-cozy enabled:hover:bg-coral-700 disabled:border-coral-soft disabled:bg-coral-soft disabled:text-coral-ink disabled:shadow-none",
};

const sizes: Record<ButtonSize, string> = {
  sm: "min-h-11 px-3 text-xs",
  md: "min-h-11 px-4 text-sm",
  lg: "min-h-12 px-5 text-sm",
};

/** A native button with shared variants, icon slots, ref forwarding, and loading behavior. */
export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  iconLeft?: ReactNode;
  iconRight?: ReactNode;
}>(({ children, variant = "secondary", size = "md", loading = false, iconLeft, iconRight, className, disabled, type = "button", ...props }, ref) => (
  <button
    ref={ref}
    type={type}
    disabled={disabled || loading}
    aria-busy={loading || undefined}
    className={cn(
      "s2l-ui-button box-border m-0 inline-flex appearance-none items-center justify-center gap-2 rounded-control border font-ui font-semibold leading-5 transition-[background-color,border-color,color,box-shadow,transform] duration-200 ease-out focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:pointer-events-none disabled:cursor-not-allowed motion-reduce:transition-none",
      variants[variant],
      sizes[size],
      className,
    )}
    {...props}
  >
    {loading ? <LoaderCircle aria-hidden="true" className="size-4 animate-spin motion-reduce:animate-none" /> : iconLeft}
    <span className="inline-flex min-w-0 items-center gap-2">{children}</span>
    {!loading && iconRight}
  </button>
));

Button.displayName = "Button";
