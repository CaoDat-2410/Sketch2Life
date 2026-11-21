import { useId, useRef, type KeyboardEvent } from "react";
import { cn } from "./cn";

export type TabItem = { value: string; label: string; disabled?: boolean };

/** An accessible horizontal tab list with roving focus and arrow-key navigation. */
export function Tabs({
  items,
  value,
  onValueChange,
  label = "Sections",
  className,
}: {
  items: readonly TabItem[];
  value: string;
  onValueChange: (value: string) => void;
  label?: string;
  className?: string;
}) {
  const baseId = useId();
  const refs = useRef<Array<HTMLButtonElement | null>>([]);

  function moveFocus(event: KeyboardEvent<HTMLButtonElement>, currentIndex: number) {
    let targetIndex: number | undefined;
    const enabled = items.map((item, index) => item.disabled ? -1 : index).filter((index) => index >= 0);
    const position = enabled.indexOf(currentIndex);
    if (event.key === "ArrowRight") targetIndex = enabled[(position + 1) % enabled.length];
    if (event.key === "ArrowLeft") targetIndex = enabled[(position - 1 + enabled.length) % enabled.length];
    if (event.key === "Home") targetIndex = enabled[0];
    if (event.key === "End") targetIndex = enabled[enabled.length - 1];
    if (targetIndex === undefined) return;
    event.preventDefault();
    refs.current[targetIndex]?.focus();
    onValueChange(items[targetIndex].value);
  }

  return (
    <div role="tablist" aria-label={label} className={cn("box-border flex w-fit max-w-full items-center gap-1 overflow-x-auto rounded-xl border border-rule bg-paper-muted p-1", className)}>
      {items.map((item, index) => {
        const selected = item.value === value;
        return (
          <button
            ref={(node) => { refs.current[index] = node; }}
            key={item.value}
            type="button"
            role="tab"
            id={`${baseId}-tab-${index}`}
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            disabled={item.disabled}
            onClick={() => onValueChange(item.value)}
            onKeyDown={(event) => moveFocus(event, index)}
            className={cn(
              "box-border m-0 min-h-10 shrink-0 appearance-none rounded-control border-0 bg-transparent px-3 py-2 font-ui text-sm font-semibold leading-5 text-ink-soft transition-colors duration-150 hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-primary disabled:pointer-events-none disabled:opacity-50 motion-reduce:transition-none",
              selected && "bg-paper text-primary-ink shadow-cozy",
            )}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
