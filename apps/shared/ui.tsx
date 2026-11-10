import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import * as AccordionPrimitive from "@radix-ui/react-accordion";

type AccessibleDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  className?: string;
  showClose?: boolean;
  container?: HTMLElement | null;
  children: React.ReactNode;
};

export function AccessibleDialog({
  open,
  onOpenChange,
  title,
  description,
  className = "",
  showClose = true,
  container,
  children,
}: AccessibleDialogProps) {
  const returnFocusRef = React.useRef<HTMLElement | null>(null);

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal container={container ?? undefined}>
        <DialogPrimitive.Overlay className={`s2l-dialog-overlay ${className.includes("is-sheet") ? "is-sheet" : ""}`.trim()} />
        <DialogPrimitive.Content
          className={`s2l-dialog-content ${className}`.trim()}
          onOpenAutoFocus={() => {
            returnFocusRef.current = document.activeElement instanceof HTMLElement
              ? document.activeElement
              : null;
          }}
          onCloseAutoFocus={(event) => {
            const returnTarget = returnFocusRef.current;
            if (!returnTarget?.isConnected) return;
            event.preventDefault();
            returnTarget.focus();
          }}
        >
          <DialogPrimitive.Title className="s2l-sr-only">{title}</DialogPrimitive.Title>
          {description && <DialogPrimitive.Description className="s2l-sr-only">{description}</DialogPrimitive.Description>}
          {showClose && (
            <DialogPrimitive.Close className="s2l-dialog-close" aria-label="Đóng">
              <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
                <path d="m5 5 10 10M15 5 5 15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </DialogPrimitive.Close>
          )}
          {children}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

export const Accordion = AccordionPrimitive.Root;
export const AccordionItem = AccordionPrimitive.Item;
export const AccordionHeader = AccordionPrimitive.Header;
export const AccordionTrigger = AccordionPrimitive.Trigger;
export const AccordionContent = AccordionPrimitive.Content;
