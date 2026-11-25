import {
  useState,
  useId,
  isValidElement,
  cloneElement,
  type ReactElement,
  type ReactNode,
  type FormEvent,
} from "react";
import { ArrowLeft, ArrowRight, CircleAlert, RefreshCw } from "lucide-react";
import {
  Button as CozyButton,
  DataTable,
  EmptyState,
  PageHeader,
  StatusBadge,
  type StatusTone,
} from "../../../shared/ui";
import { CrayonStub } from "../../../shared/ui/illustrations";
import { AdminSearchInput } from "./AdminSearchInput";
import { label } from "./adminHooks";

const successfulStates = new Set([
  "active", "approved", "approve", "available", "completed", "enabled", "healthy", "paid", "public", "published", "received", "sent",
]);
const warningStates = new Set([
  "awaiting_external_purge", "cancel_at_period_end", "changes_requested", "draft", "grace", "identity_check", "inactive", "paused", "pending", "pending_review", "pending_verification", "private", "recall", "recalled", "request_changes", "requested", "scope_review", "suspended", "top_up",
]);
const dangerStates = new Set([
  "blocked", "cancelled", "canceled", "disabled", "error", "exception", "failed", "hidden", "overdue", "rejected", "restricted",
]);
const informationalStates = new Set([
  "included", "processing", "running", "sending",
]);

function statusTone(value: string): StatusTone {
  const normalized = value.toLowerCase();
  if (successfulStates.has(normalized)) return "success";
  if (warningStates.has(normalized)) return "warn";
  if (dangerStates.has(normalized)) return "danger";
  if (informationalStates.has(normalized)) return "info";
  return "neutral";
}

export function Status({ value }: { value: string }) {
  return <StatusBadge className="s2l-admin-status" tone={statusTone(value)} size="sm" dot>{label(value)}</StatusBadge>;
}
export function Heading({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return <PageHeader
    title={title}
    description={description}
    actions={children ? <div className="flex min-w-0 flex-wrap items-center gap-2">{children}</div> : undefined}
    className="pa-admin-page-header mb-1"
  />;
}
export function Button({
  children,
  onClick,
  disabled,
  primary = false,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  primary?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <CozyButton
      type={type}
      variant={primary ? "primary" : "secondary"}
      size="sm"
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </CozyButton>
  );
}
export function Refresh({
  onClick,
  disabled,
}: {
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <Button onClick={onClick} disabled={disabled}>
      <RefreshCw size={15} />
      Tải lại
    </Button>
  );
}
export function Field({
  label: title,
  hint,
  children,
}: {
  label: string;
  hint?: ReactNode;
  children: ReactNode;
}) {
  const id = useId();
  const hintId = id + "-hint";
  return (
    <div className="s2l-admin-field grid min-w-0 gap-2 font-ui text-sm font-semibold text-ink">
      <label className="leading-5" htmlFor={id}>{title}</label>
      {isValidElement(children)
        ? cloneElement(
            children as ReactElement<{ id?: string; "aria-describedby"?: string }>,
            {
              id,
              ...(hint ? { "aria-describedby": hintId } : {}),
            },
          )
        : children}
      {hint && (
        <p id={hintId} className="pa-field-hint m-0 font-normal text-xs leading-5 text-ink-soft">
          {hint}
        </p>
      )}
    </div>
  );
}
export function Form({
  children,
  onSubmit,
}: {
  children: ReactNode;
  onSubmit: () => void;
}) {
  return (
    <form
      className="pa-form grid min-w-0 gap-4"
      onSubmit={(e: FormEvent) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      {children}
    </form>
  );
}
export function Feedback({
  error,
  notice,
}: {
  error?: string;
  notice?: string;
}) {
  return (
    <>
      {error && (
      <div className="s2l-admin-feedback flex min-w-0 items-start gap-2 rounded-xl border border-coral-soft bg-coral-soft/70 px-4 py-3 font-ui text-sm leading-5 text-coral-ink" role="alert" aria-live="assertive">
          <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          {error}
        </div>
      )}
      {notice && (
        <div className="s2l-admin-feedback rounded-xl border border-mint-soft bg-mint-soft/70 px-4 py-3 font-ui text-sm leading-5 text-mint-ink" role="status" aria-live="polite">
          {notice}
        </div>
      )}
    </>
  );
}
export function LoadBoundary({
  loading,
  error,
  reload,
  children,
}: {
  loading: boolean;
  error: string;
  reload: () => void;
  children: ReactNode;
}) {
  if (loading)
    return (
      <div className="s2l-admin-loading flex min-w-0 items-center gap-4 rounded-cozy border border-rule bg-paper p-5 shadow-cozy" role="status" aria-label="Đang tải dữ liệu" aria-busy="true">
        <div aria-hidden="true" className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary-soft text-primary-ink">
          <RefreshCw className="size-5 animate-spin motion-reduce:animate-none" />
        </div>
        <div className="grid min-w-0 flex-1 gap-2">
          <span className="font-ui text-sm font-semibold text-ink">Đang tải dữ liệu…</span>
          <span aria-hidden="true" className="h-2.5 w-3/4 animate-pulse rounded-full bg-paper-muted motion-reduce:animate-none" />
          <span aria-hidden="true" className="h-2.5 w-1/2 animate-pulse rounded-full bg-paper-muted motion-reduce:animate-none" />
        </div>
      </div>
    );
  if (error)
    return (
      <section className="s2l-admin-load-error flex min-w-0 flex-wrap items-center gap-4 rounded-cozy border border-coral-soft bg-paper p-5 shadow-cozy" aria-labelledby="admin-load-error-title">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-coral-soft text-coral-ink" aria-hidden="true"><CircleAlert size={22} /></span>
        <div className="min-w-0 flex-1">
          <h2 id="admin-load-error-title" className="m-0 font-ui text-base font-bold text-ink">Không tải được dữ liệu</h2>
          <p className="mb-0 mt-1 font-ui text-sm leading-5 text-ink-soft" role="alert">{error}</p>
        </div>
        <Refresh onClick={reload} />
      </section>
    );
  return <>{children}</>;
}
export function Empty({
  text = "Chưa có dữ liệu",
  detail = "",
  action,
}: {
  text?: string;
  detail?: string;
  action?: ReactNode;
}) {
  return <EmptyState title={text} description={detail || undefined} action={action} illustration={<CrayonStub />} />;
}
export function Table<T>({
  items,
  columns,
  rowKey,
  emptyText = "Chưa có dữ liệu",
  emptyDetail = "",
  caption = "Danh sách dữ liệu",
  className,
}: {
  items: T[];
  columns: { title: string; render: (row: T) => ReactNode }[];
  rowKey: (row: T) => string;
  emptyText?: string;
  emptyDetail?: string;
  caption?: string;
  className?: string;
}) {
  return <DataTable
    className={className}
    caption={caption}
    rows={items}
    getRowKey={rowKey}
    columns={columns.map((column) => ({ key: column.title, header: column.title, render: column.render }))}
    density="dense"
    emptyState={<Empty text={emptyText} detail={emptyDetail} />}
  />;
}
export function CursorPager({
  page,
  nextCursor,
  onNext,
  onPrevious,
  total,
  count,
  disabled,
}: {
  page: number;
  nextCursor?: string | null;
  onNext: (cursor: string | null | undefined) => void;
  onPrevious: () => void;
  total?: number;
  count: number;
  disabled?: boolean;
}) {
  if (count === 0 && page === 0) return null;
  const start = page * 25 + 1;
  const end = page * 25 + count;
  return (
    <footer className="s2l-admin-pager flex min-w-0 flex-wrap items-center justify-between gap-3 border-t border-rule px-4 py-3 font-ui text-sm text-ink-soft">
      <span className="tabular-nums">
        {count ? `${start}–${end}` : "0"}
        {total === undefined ? " kết quả" : ` / ${total} kết quả`}
      </span>
      <div className="flex items-center gap-2">
        <Button
          disabled={disabled || page === 0}
          onClick={onPrevious}
        >
          <ArrowLeft size={15} />
          Trước
        </Button>
        <Button
          disabled={disabled || !nextCursor}
          onClick={() => onNext(nextCursor)}
        >
          Tiếp
          <ArrowRight size={15} />
        </Button>
      </div>
    </footer>
  );
}
export function SearchForm({
  onSearch,
  placeholder = "Tìm kiếm",
  initialValue = "",
  controls,
}: {
  onSearch: (value: string) => void;
  placeholder?: string;
  initialValue?: string;
  controls?: ReactNode;
}) {
  const [value, setValue] = useState(initialValue);
  return (
    <form
      className="pa-search-form flex min-w-0 flex-wrap items-end gap-3"
      onSubmit={(e) => {
        e.preventDefault();
        onSearch(value.trim());
      }}
    >
      <AdminSearchInput
        label={placeholder}
        placeholder={placeholder}
        value={value}
        maxLength={120}
        onValueChange={setValue}
      />
      {controls}
      <Button type="submit">Tìm kiếm</Button>
    </form>
  );
}
