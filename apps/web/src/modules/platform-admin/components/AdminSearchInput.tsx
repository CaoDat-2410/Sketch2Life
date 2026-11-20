import { useId } from "react";
import { Search } from "lucide-react";

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
    <label className={`pa-search-control ${className}`} htmlFor={id} data-disabled={disabled || undefined}>
      <span className="pa-search-label">{label}</span>
      <Search size={19} strokeWidth={1.8} aria-hidden="true" />
      <input id={id} className="pa-search-input" type="search" value={value}
        placeholder={placeholder} disabled={disabled} maxLength={maxLength}
        onChange={(event) => onValueChange(event.target.value)} />
    </label>
  );
}
