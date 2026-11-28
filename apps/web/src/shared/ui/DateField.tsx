import { forwardRef, useState, type InputHTMLAttributes } from "react";
import { cn } from "./cn";
import { formatDateEcho } from "./dateFormat";

export type DateFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  type?: "date" | "datetime-local";
  placeholderText?: string;
  echoSelected?: boolean;
};

/** Native date / datetime-local input wrapped with a Vietnamese placeholder and dd/mm/yyyy echo. */
export const DateField = forwardRef<HTMLInputElement, DateFieldProps>(({
  type = "date",
  placeholderText,
  echoSelected = true,
  className,
  value,
  defaultValue,
  onFocus,
  onBlur,
  onChange,
  ...props
}, ref) => {
  const [focused, setFocused] = useState(false);
  const [internalValue, setInternalValue] = useState(() => (defaultValue !== undefined ? String(defaultValue) : ""));
  const currentValue = value !== undefined ? String(value) : internalValue;
  const isEmpty = currentValue.trim() === "";
  const echo = echoSelected ? formatDateEcho(currentValue, type) : null;
  const resolvedPlaceholder = placeholderText
    ?? (type === "datetime-local" ? "Chọn ngày và giờ (ngày/tháng/năm)" : "Chọn ngày (ngày/tháng/năm)");

  return (
    <div className="s2l-date-field-wrap">
      <div className={cn("s2l-date-field", isEmpty && !focused && "is-empty-idle")}>
        <input
          ref={ref}
          type={type}
          value={value}
          defaultValue={value === undefined ? defaultValue : undefined}
          {...props}
          className={cn("cozy-input s2l-date-input", className)}
          onFocus={(event) => {
            setFocused(true);
            onFocus?.(event);
          }}
          onBlur={(event) => {
            setFocused(false);
            onBlur?.(event);
          }}
          onChange={(event) => {
            if (value === undefined) setInternalValue(event.target.value);
            onChange?.(event);
          }}
        />
        {isEmpty && !focused && (
          <span aria-hidden="true" className="s2l-date-placeholder">
            {resolvedPlaceholder}
          </span>
        )}
      </div>
      {echo && <p className="cozy-form-hint s2l-date-echo">{echo}</p>}
    </div>
  );
});

DateField.displayName = "DateField";
