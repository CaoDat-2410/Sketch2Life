import {
  useState,
  useId,
  isValidElement,
  cloneElement,
  type ReactElement,
  type ReactNode,
  type FormEvent,
} from "react";
import { ArrowLeft, ArrowRight, RefreshCw, Inbox, CircleAlert } from "lucide-react";
import { AdminSearchInput } from "./AdminSearchInput";
import { label } from "./adminHooks";

export function Status({ value }: { value: string }) {
  return (
    <span className={"pa-status pa-status-" + value.toLowerCase()}>
      {label(value)}
    </span>
  );
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
  return (
    <header className={"pa-heading" + (description ? " has-description" : " is-compact")}>
      <div>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      <div className="pa-actions">{children}</div>
    </header>
  );
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
    <button
      type={type}
      className={"pa-button" + (primary ? " is-primary" : "")}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
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
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <div className="pa-field">
      <label htmlFor={id}>{title}</label>
      {isValidElement(children)
        ? cloneElement(children as ReactElement<{ id?: string }>, { id })
        : children}
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
      className="pa-form"
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
        <p className="pa-alert" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="pa-notice" role="status">
          {notice}
        </p>
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
      <div className="pa-data-loading" role="status" aria-label="Đang tải dữ liệu" aria-busy="true">
        <div className="pa-loading-symbol" />
        <div className="pa-loading-lines"><span /><span /><span /></div>
        <span className="pa-loading-label">Đang tải dữ liệu…</span>
      </div>
    );
  if (error)
    return (
      <section className="pa-data-state is-error">
        <span className="pa-data-state-icon" aria-hidden="true"><CircleAlert size={24} /></span>
        <div className="pa-data-state-copy">
          <h2>Không tải được dữ liệu</h2>
          <p role="alert">{error}</p>
        </div>
        <div className="pa-data-state-actions"><Refresh onClick={reload} /></div>
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
  return (
    <div className="pa-data-state">
      <span className="pa-data-state-icon" aria-hidden="true"><Inbox size={24} /></span>
      <div className="pa-data-state-copy"><h2>{text}</h2>{detail && <p>{detail}</p>}</div>
      {action && <div className="pa-data-state-actions">{action}</div>}
    </div>
  );
}
export function Table<T>({
  items,
  columns,
  rowKey,
  emptyText = "Chưa có dữ liệu",
  emptyDetail = "",
}: {
  items: T[];
  columns: { title: string; render: (row: T) => ReactNode }[];
  rowKey: (row: T) => string;
  emptyText?: string;
  emptyDetail?: string;
}) {
  return items.length ? (
    <div className="pa-table-scroll">
      <table className="pa-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.title} scope="col">
                {c.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((c) => (
                <td key={c.title}>{c.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <Empty text={emptyText} detail={emptyDetail} />
  );
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
    <footer className="pa-pager">
      <span>
        {count ? `${start}–${end}` : "0"}
        {total === undefined ? " kết quả" : ` / ${total} kết quả`}
      </span>
      <div>
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
      className="pa-search-form"
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
