import type { ReactNode } from "react";
import { cn } from "./cn";

export type DataTableColumn<Row> = {
  key: string;
  header: ReactNode;
  render: (row: Row) => ReactNode;
  numeric?: boolean;
  className?: string;
};

/** A typed, responsive table with caption, empty state, loading rows, and density options. */
export function DataTable<Row>({
  columns,
  rows,
  getRowKey,
  caption,
  density = "comfortable",
  stickyHeader = false,
  emptyState,
  loading = false,
  className,
}: {
  columns: readonly DataTableColumn<Row>[];
  rows: readonly Row[];
  getRowKey: (row: Row) => string | number;
  caption: string;
  density?: "dense" | "comfortable";
  stickyHeader?: boolean;
  emptyState?: ReactNode;
  loading?: boolean;
  className?: string;
}) {
  const cellPadding = density === "dense" ? "px-3 py-2.5" : "px-4 py-3.5";
  return (
    <div aria-busy={loading || undefined} className={cn("box-border w-full max-w-full min-w-0 overflow-x-auto overscroll-x-contain", className)}>
      <table className="s2l-admin-table box-border min-w-[34rem] w-full border-separate border-spacing-0 font-ui text-sm tabular-nums">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" className={cn(
                "box-border border-b border-rule bg-cream px-4 py-2.5 text-left font-ui text-xs font-semibold tracking-wide text-ink-soft",
                stickyHeader && "sticky top-0 z-10",
                column.numeric && "text-right",
                cellPadding,
              )}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? Array.from({ length: 3 }, (_, rowIndex) => (
            <tr key={`skeleton-${rowIndex}`} aria-hidden="true">
              {columns.map((column) => <td key={column.key} className={cn("box-border border-b border-rule px-4 py-3", cellPadding)}><span className="block h-4 w-3/4 animate-pulse rounded bg-paper-muted motion-reduce:animate-none" /></td>)}
            </tr>
          )) : rows.length ? rows.map((row) => (
            <tr key={getRowKey(row)} className="last:[&>td]:border-b-0 hover:bg-paper-muted/45">
              {columns.map((column) => <td key={column.key} className={cn(
                "box-border border-b border-rule font-ui text-sm leading-5 text-ink",
                cellPadding,
                column.numeric && "text-right tabular-nums",
                column.className,
              )}>{column.render(row)}</td>)}
            </tr>
          )) : (
            <tr>
              <td colSpan={Math.max(1, columns.length)} className="box-border p-0 align-middle">
                {emptyState}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
