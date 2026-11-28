import { useCallback, useEffect, useLayoutEffect, useRef, type ChangeEvent, type TextareaHTMLAttributes } from "react";

type Props = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "onChange" | "value"> & {
  value: string;
  onValueChange: (value: string) => void;
  /** A value that is one line on the wire: pasted or typed line breaks become spaces. */
  singleLine?: boolean;
};

/** A textarea that grows with its text, so nothing is clipped at any screen width. */
export function AutoGrowTextarea({ value, onValueChange, singleLine = false, className = "cozy-textarea", style, rows = 1, ...rest }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const fit = useCallback(() => {
    const element = ref.current;
    if (!element) return;
    element.style.height = "auto";
    if (element.scrollHeight > 0) element.style.height = `${element.scrollHeight + element.offsetHeight - element.clientHeight}px`;
  }, []);
  useLayoutEffect(() => { fit(); }, [value, fit]);
  useEffect(() => {
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, [fit]);
  const change = (event: ChangeEvent<HTMLTextAreaElement>) => {
    onValueChange(singleLine ? event.target.value.replace(/[\r\n]+/g, " ") : event.target.value);
  };
  return (
    <textarea
      {...rest}
      ref={ref}
      rows={rows}
      className={className}
      value={value}
      onChange={change}
      onKeyDown={singleLine ? (event) => { if (event.key === "Enter") event.preventDefault(); } : undefined}
      style={{ minHeight: 44, overflow: "hidden", resize: "none", ...style }}
    />
  );
}
