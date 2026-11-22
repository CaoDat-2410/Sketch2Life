import { Children, isValidElement, useId, useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "./cn";
import "./Select.css";

type Option = { value: string; label: ReactNode; disabled?: boolean };
export type SelectChangeEvent = { target: { value: string } };
export type SelectProps = {
  value: string | number;
  onChange: (event: SelectChangeEvent) => void;
  children: ReactNode;
  id?: string;
  disabled?: boolean;
  required?: boolean;
  "aria-label"?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
  "aria-required"?: boolean;
  className?: string;
  style?: CSSProperties;
};

function optionText(value: ReactNode): string {
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(optionText).join("");
  if (isValidElement<{ children?: ReactNode }>(value)) return optionText(value.props.children);
  return "";
}

/** Cozy combobox with a hidden native control for standard form submission and validation. */
export function Select({
  value,
  onChange,
  children,
  id,
  disabled,
  required,
  "aria-label": ariaLabel,
  "aria-describedby": ariaDescribedBy,
  "aria-invalid": ariaInvalid,
  "aria-required": ariaRequired,
  className,
  style,
}: SelectProps) {
  const generated = useId();
  const triggerId = id ?? generated + "-trigger";
  const listId = generated + "-list";
  const trigger = useRef<HTMLButtonElement>(null);
  const popup = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [position, setPosition] = useState({ left: 0, top: 0, width: 0, maxHeight: 280 });
  const search = useRef({ text: "", at: 0 });
  const options: Option[] = [];

  const collect = (nodes: ReactNode) => Children.forEach(nodes, (node) => {
    if (!isValidElement<{ value?: string | number; disabled?: boolean; children?: ReactNode }>(node)) return;
    if (node.type === "option") {
      options.push({ value: String(node.props.value ?? ""), label: node.props.children, disabled: node.props.disabled });
    } else {
      collect(node.props.children);
    }
  });
  collect(children);

  const selected = Math.max(0, options.findIndex((option) => option.value === String(value)));
  const enabledFrom = (start: number, direction: 1 | -1) => {
    if (!options.length) return 0;
    for (let count = 0; count < options.length; count += 1) {
      const index = (start + direction * count + options.length) % options.length;
      if (!options[index].disabled) return index;
    }
    return start;
  };

  function reveal() {
    if (disabled) return;
    setActive(enabledFrom(selected, 1));
    setOpen(true);
  }

  function choose(index: number) {
    const option = options[index];
    if (!option || option.disabled) return;
    onChange({ target: { value: option.value } });
    setOpen(false);
    trigger.current?.focus();
  }

  function move(direction: 1 | -1) {
    if (options.length) setActive(enabledFrom(active + direction, direction));
  }

  useLayoutEffect(() => {
    if (!open) return;
    const place = () => {
      const rect = trigger.current?.getBoundingClientRect();
      if (!rect) return;
      const desiredHeight = Math.min(280, options.length * 40 + 14);
      const roomBelow = Math.max(0, window.innerHeight - rect.bottom - 8);
      const roomAbove = Math.max(0, rect.top - 8);
      const above = roomBelow < Math.min(180, desiredHeight) && roomAbove > roomBelow;
      const available = above ? roomAbove : roomBelow;
      const maxHeight = Math.max(80, Math.min(280, available || desiredHeight));
      const width = Math.min(rect.width, Math.max(0, window.innerWidth - 16));
      const left = Math.max(8, Math.min(rect.left, window.innerWidth - width - 8));
      const height = Math.min(desiredHeight, maxHeight);
      const top = above
        ? Math.max(8, rect.top - height - 6)
        : Math.max(8, Math.min(rect.bottom + 6, window.innerHeight - height - 8));
      setPosition({ left, top, width, maxHeight });
    };
    const outside = (event: PointerEvent) => {
      if (!trigger.current?.contains(event.target as Node) && !popup.current?.contains(event.target as Node)) setOpen(false);
    };
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    document.addEventListener("pointerdown", outside);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
      document.removeEventListener("pointerdown", outside);
    };
  }, [open, options.length]);

  useLayoutEffect(() => {
    if (open) document.getElementById(listId + "-" + active)?.scrollIntoView?.({ block: "nearest" });
  }, [open, active, listId]);

  return (
    <>
      <select
        className="s2l-select-native"
        aria-hidden="true"
        tabIndex={-1}
        value={value}
        required={required}
        disabled={disabled}
        onChange={onChange}
        onInvalid={(event) => { event.preventDefault(); trigger.current?.focus(); }}
      >
        {children}
      </select>
      <button
        id={triggerId}
        ref={trigger}
        type="button"
        role="combobox"
        className={cn("s2l-select-trigger box-border flex min-h-11 w-full min-w-0 items-center justify-between gap-3 rounded-xl border border-rule bg-paper px-3.5 py-2 font-ui text-sm font-medium text-ink shadow-cozy transition-colors disabled:cursor-not-allowed disabled:opacity-55", className)}
        style={style}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-invalid={ariaInvalid || undefined}
        aria-required={required || ariaRequired || undefined}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        aria-activedescendant={open ? listId + "-" + active : undefined}
        disabled={disabled}
        onClick={() => open ? setOpen(false) : reveal()}
        onBlur={(event) => { if (!popup.current?.contains(event.relatedTarget as Node)) setOpen(false); }}
        onKeyDown={(event) => {
          if (event.key === "Tab") { setOpen(false); return; }
          if (event.key === "Escape") { event.preventDefault(); setOpen(false); return; }
          if (["ArrowDown", "ArrowUp", "Home", "End", "Enter", " "].includes(event.key)) {
            event.preventDefault();
            if (!open) { reveal(); return; }
            if (event.key === "Enter" || event.key === " ") choose(active);
            else if (event.key === "ArrowDown" || event.key === "ArrowUp") move(event.key === "ArrowDown" ? 1 : -1);
            else setActive(enabledFrom(event.key === "Home" ? 0 : options.length - 1, event.key === "Home" ? 1 : -1));
          } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
            const now = Date.now();
            search.current.text = (now - search.current.at > 700 ? "" : search.current.text) + event.key.toLocaleLowerCase("vi-VN");
            search.current.at = now;
            const found = options.findIndex((option) => !option.disabled && optionText(option.label).toLocaleLowerCase("vi-VN").startsWith(search.current.text));
            if (found >= 0) { setOpen(true); setActive(found); }
          }
        }}
      >
        <span className="min-w-0 truncate text-left">{options[selected]?.label}</span>
        <ChevronDown size={16} aria-hidden="true" />
      </button>
      {open && createPortal(
        <div
          ref={popup}
          id={listId}
          role="listbox"
          aria-label={ariaLabel}
          aria-labelledby={ariaLabel ? undefined : triggerId}
          className="s2l-select-menu z-[1100] overflow-auto rounded-xl border border-rule bg-paper p-1.5 font-ui text-sm text-ink shadow-cozy-hover"
          style={position}
        >
          {options.map((option, index) => (
            <div
              key={option.value}
              id={listId + "-" + index}
              role="option"
              aria-selected={option.value === String(value)}
              aria-disabled={option.disabled || undefined}
              className={"s2l-select-option flex min-h-10 cursor-pointer items-center justify-between gap-3 rounded-lg px-3 py-2 " + (active === index ? "is-highlighted " : "") + (option.disabled ? "cursor-not-allowed opacity-55" : "")}
              onPointerMove={() => { if (!option.disabled) setActive(index); }}
              onPointerDown={(event) => event.preventDefault()}
              onClick={() => choose(index)}
            >
              <span>{option.label}</span>
              {option.value === String(value) && <Check size={16} aria-hidden="true" />}
            </div>
          ))}
        </div>,
        document.body,
      )}
    </>
  );
}
