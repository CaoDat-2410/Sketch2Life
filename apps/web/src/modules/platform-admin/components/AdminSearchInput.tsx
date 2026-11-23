import { useId } from "react";
import { Search } from "lucide-react";
import { cn } from "../../../shared/ui/cn";

export function AdminSearchInput({
  value, onValueChange, label, placeholder, disabled = false, maxLength = 120, className = "",
}: {
  value: string;
  onValueChange: (value: string) => void;
  label: string;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
  className?: string;
}) {
  const id = useId();
  return (
    <label className={cn("pa-search-control grid min-w-0 flex-1 gap-1.5 font-ui text-sm font-semibold text-ink-soft", className)} htmlFor={id} data-disabled={disabled || undefined}>
      <span className="pa-search-label">{label}</span>
      <span className="pa-search-box flex min-h-11 min-w-0 w-full items-center gap-2.5 rounded-xl border border-rule bg-paper px-3.5 shadow-cozy transition-colors">
      <Search size={18} strokeWidth={1.8} className="shrink-0 text-ink-soft" aria-hidden="true" />
      <input id={id} className="pa-search-input min-w-0 flex-1 border-0 bg-transparent p-0 font-ui text-sm font-medium text-ink outline-none placeholder:text-ink-soft focus:outline-none disabled:cursor-not-allowed" type="search" value={value}
        placeholder={placeholder} disabled={disabled} maxLength={maxLength}
        onChange={(event) => onValueChange(event.target.value)} />
      </span>
    </label>
  );
}
