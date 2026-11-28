import { useEffect, useRef } from "react";
import { AccessibleDialog } from "../components/ui";
import { Button } from "./Button";
import { cn } from "./cn";
import "./ConfirmDialog.css";

export type ConfirmDialogTone = "primary" | "danger";

export type ConfirmDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  tone?: ConfirmDialogTone;
  busy?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
  container?: HTMLElement | null;
  className?: string;
};

/** Shared accessible confirmation modal for irreversible or high-impact actions. */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  cancelLabel = "Hủy",
  tone = "primary",
  busy = false,
  onConfirm,
  onCancel,
  container,
  className,
}: ConfirmDialogProps) {
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const openerRef = useRef<HTMLElement | null>(null);
  const confirmedRef = useRef(false);

  useEffect(() => {
    confirmedRef.current = false;
  }, [open]);

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      if (busy) return;
      if (!confirmedRef.current) onCancel?.();
      onOpenChange(false);
      return;
    }
    onOpenChange(true);
  };

  const handleCancel = () => {
    if (busy) return;
    onCancel?.();
    onOpenChange(false);
  };

  const handleConfirm = () => {
    if (busy || confirmedRef.current) return;
    confirmedRef.current = true;
    onOpenChange(false);
    void onConfirm();
  };

  return (
    <AccessibleDialog
      open={open}
      onOpenChange={handleOpenChange}
      title={title}
      description={description}
      showTitle
      showDescription
      showClose={!busy}
      container={container}
      className={cn("s2l-confirm-dialog", className)}
      onOpenAutoFocus={(event) => {
        event.preventDefault();
        openerRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        cancelButtonRef.current?.focus();
      }}
      onCloseAutoFocus={(event) => {
        const opener = openerRef.current;
        openerRef.current = null;
        if (opener && opener.isConnected) {
          event.preventDefault();
          opener.focus();
        }
      }}
    >
      <div className="s2l-confirm-actions">
        <Button
          ref={cancelButtonRef}
          type="button"
          variant="secondary"
          className="s2l-confirm-cancel"
          disabled={busy}
          onClick={handleCancel}
        >
          {cancelLabel}
        </Button>
        <Button
          type="button"
          variant={tone === "danger" ? "danger" : "primary"}
          className={cn("s2l-confirm-action", tone === "danger" ? "is-danger" : "is-primary")}
          loading={busy}
          disabled={busy}
          onClick={handleConfirm}
        >
          {confirmLabel}
        </Button>
      </div>
    </AccessibleDialog>
  );
}
