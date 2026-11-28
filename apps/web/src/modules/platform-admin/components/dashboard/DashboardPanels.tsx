import type { ReactNode } from "react";
import { Activity, Database, Server } from "lucide-react";
import type { Operations, OrganizationSummary } from "../../services/adminService";
import { Empty } from "../AdminUI";
import { date, money } from "../adminHooks";
import {
  buildCashFlowBuckets,
  integerAxis,
  sharePercentage,
  type AccountRoleCount,
  type CashFlowRange,
  type PaymentRecord,
} from "./dashboardData";

const number = (value: number) => value.toLocaleString("vi-VN");
const percent = (value: number) => `${value.toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`;

const schoolStates = [
  { key: "active", label: "Đang hoạt động" },
  { key: "paused", label: "Tạm dừng" },
  { key: "disabled", label: "Đã ngừng" },
  { key: "other", label: "Trạng thái khác" },
] as const;

type ChartColumn = { key: string; label: string; value: number; share: number };

/**
 * Vertical columns in one hue. Every column carries its value; a zero keeps its slot as a
 * labelled empty column. The figures are repeated as text in the list or table next to it.
 */
function ColumnChart({ columns, summary, unit }: { columns: ChartColumn[]; summary: string; unit: string }) {
  const axis = integerAxis(Math.max(0, ...columns.map((column) => column.value)));
  return (
    <div className="pa-columns" role="img" aria-label={summary}>
      <ol className="pa-columns-axis" aria-hidden="true">
        {[...axis.ticks].reverse().map((tick) => <li key={tick}>{number(tick)}</li>)}
      </ol>
      <div className="pa-columns-plot" aria-hidden="true">
        {columns.map((column) => (
          <div
            className={"pa-columns-item" + (column.value === 0 ? " is-empty" : "")}
            key={column.key}
            title={`${column.label}: ${number(column.value)} ${unit}`}
          >
            <div className="pa-columns-area" style={{ backgroundSize: `100% ${100 / (axis.ticks.length - 1)}%` }}>
              <div className="pa-columns-bar" style={{ height: `${column.value / axis.max * 100}%` }}><b>{number(column.value)}</b></div>
            </div>
            <small>{column.label}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function ColumnLegend({ columns, label }: { columns: ChartColumn[]; label: string }) {
  return (
    <ul className="pa-columns-legend" aria-label={label}>
      {columns.map((column) => (
        <li key={column.key}><span>{column.label}</span><strong>{number(column.value)}</strong><small>{percent(column.share)}</small></li>
      ))}
    </ul>
  );
}

const columnSummary = (title: string, columns: ChartColumn[]) =>
  `${title}: ${columns.map((column) => `${column.label} ${number(column.value)}`).join(", ")}`;

export function OrganizationStateOverview({ summary }: { summary: OrganizationSummary }) {
  if (summary.total <= 0) {
    return (
      <div className="pa-dashboard-state-overview">
        <div className="pa-dashboard-gauge-empty">
          <Empty text="Chưa có trường học" detail="Tỷ lệ sẽ xuất hiện khi có dữ liệu trường học." />
        </div>
      </div>
    );
  }
  const columns = schoolStates.map((state) => ({
    key: state.key,
    label: state.label,
    value: summary[state.key],
    share: sharePercentage(summary[state.key], summary.total),
  }));
  return (
    <div className="pa-columns-panel pa-school-status">
      <p className="pa-columns-summary">
        <strong>{percent(sharePercentage(summary.active, summary.total))}</strong> trường hoạt động · {number(summary.active)} / {number(summary.total)} trường
      </p>
      <div className="pa-school-stack" role="img" aria-label={`Trường đang hoạt động chiếm ${percent(sharePercentage(summary.active, summary.total))} trong tổng số ${number(summary.total)} trường. ${columnSummary("Số trường theo trạng thái", columns)}`}>
        {columns.filter((column) => column.value > 0).map((column) => (
          <span key={column.key} className={"is-" + column.key} style={{ flex: column.value }} aria-hidden="true" />
        ))}
      </div>
      <ColumnLegend columns={columns} label="Số trường theo trạng thái" />
    </div>
  );
}

export function AccountRoleOverview({
  total,
  rows,
  consistent,
}: {
  total: number;
  rows: AccountRoleCount[];
  consistent: boolean;
}) {
  if (total === 0) {
    return <Empty text="Chưa có tài khoản" detail="Tỷ lệ theo vai trò sẽ xuất hiện khi có dữ liệu." />;
  }
  if (!consistent) {
    return <p className="pa-dashboard-data-note" role="alert">Số lượng theo vai trò chưa khớp tổng số tài khoản. Hãy tải lại để xem tỷ lệ.</p>;
  }
  const columns = rows.map((row) => ({ key: row.label, label: row.label, value: row.count, share: row.percentage }));
  return (
    <>
    <span role="img" aria-label={columnSummary("Số tài khoản theo vai trò", columns)} />
    <ul className="pa-role-bars" aria-label="Tỷ lệ tài khoản theo vai trò">
      {columns.map((column) => (
        <li key={column.key}>
          <span>{column.label}</span>
          <span className="pa-role-bars-track" aria-hidden="true"><i style={{ width: `${column.share}%` }} /></span>
          <strong>{number(column.value)}</strong>
          <small>{percent(column.share)}</small>
        </li>
      ))}
    </ul>
    </>
  );
}

const rangeLabels: Record<CashFlowRange, string> = {
  "7d": "7 ngày",
  "30d": "30 ngày",
  "12m": "12 tháng",
};

function compactMoney(value: number) {
  return `${new Intl.NumberFormat("vi-VN", { notation: "compact", maximumFractionDigits: 1 }).format(value)} ₫`;
}

export function CashFlowChart({
  events,
  range,
  onRangeChange,
  now,
}: {
  events: PaymentRecord[];
  range: CashFlowRange;
  onRangeChange: (range: CashFlowRange) => void;
  now?: Date;
}) {
  const buckets = buildCashFlowBuckets(events, range, now);
  const total = buckets.at(-1)?.cumulativeVnd ?? 0;
  const periodLabel = rangeLabels[range];
  if (total <= 0) {
    return (
      <div className="pa-dashboard-chart-empty">
        <div className="pa-dashboard-range-picker" aria-label="Khoảng thời gian biểu đồ">
          {Object.entries(rangeLabels).map(([key, label]) => (
            <button
              type="button"
              key={key}
              aria-pressed={range === key}
              onClick={() => onRangeChange(key as CashFlowRange)}
            >
              {label}
            </button>
          ))}
        </div>
        <Empty text="Chưa có khoản thu trong khoảng thời gian này" detail="Biểu đồ sẽ xuất hiện khi có giao dịch thành công." />
      </div>
    );
  }

  const viewWidth = 760;
  const viewHeight = 286;
  const left = 70;
  const right = 64;
  const top = 18;
  const bottom = 50;
  const plotWidth = viewWidth - left - right;
  const plotHeight = viewHeight - top - bottom;
  const step = plotWidth / buckets.length;
  const barWidth = Math.max(4, step * 0.52);
  const maxDaily = Math.max(...buckets.map((bucket) => bucket.amountVnd), 1);
  const yBottom = top + plotHeight;
  const points = buckets.map((bucket, index) => {
    const x = left + step * (index + 0.5);
    const y = yBottom - (bucket.cumulativeVnd / total) * plotHeight;
    return `${x},${y}`;
  }).join(" ");
  const labelStep = buckets.length > 20 ? 5 : buckets.length > 10 ? 2 : 1;
  const chartName = `Khoản thu thành công trong ${periodLabel}, các cột theo kỳ và đường cộng dồn`;

  return (
    <div className="pa-dashboard-chart-content">
      <div className="pa-dashboard-chart-toolbar">
        <div className="pa-dashboard-chart-legend" aria-label="Chú giải biểu đồ">
          <span><i className="is-bar" aria-hidden="true" />Khoản thu</span>
          <span><i className="is-line" aria-hidden="true" />Cộng dồn</span>
        </div>
        <div className="pa-dashboard-range-picker" aria-label="Khoảng thời gian biểu đồ">
          {Object.entries(rangeLabels).map(([key, label]) => (
            <button
              type="button"
              key={key}
              aria-pressed={range === key}
              onClick={() => onRangeChange(key as CashFlowRange)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <figure className="pa-dashboard-cash-chart">
        <svg viewBox={`0 0 ${viewWidth} ${viewHeight}`} role="img" aria-label={chartName}>
          <title>{chartName}</title>
          <desc>Cột dùng thang đo bên trái để thể hiện khoản thu trong kỳ. Đường liền dùng thang đo bên phải để thể hiện tổng tiền cộng dồn. Bảng bên dưới có số liệu cho từng kỳ.</desc>
          {[0, 0.5, 1].map((fraction) => {
            const y = yBottom - fraction * plotHeight;
            return (
              <g key={fraction}>
                <line className="pa-dashboard-chart-grid" x1={left} x2={viewWidth - right} y1={y} y2={y} />
                <text className="pa-dashboard-chart-y-label" x={left - 9} y={y + 4} textAnchor="end">
                  {compactMoney(maxDaily * fraction)}
                </text>
                <text className="pa-dashboard-chart-y-label" x={viewWidth - right + 8} y={y + 4} textAnchor="start">
                  {compactMoney(total * fraction)}
                </text>
              </g>
            );
          })}
          {buckets.map((bucket, index) => {
            const x = left + step * index + (step - barWidth) / 2;
            const height = (bucket.amountVnd / maxDaily) * plotHeight;
            const showLabel = index === 0 || index === buckets.length - 1 || index % labelStep === 0;
            return (
              <g key={bucket.key}>
                <rect
                  className="pa-dashboard-chart-bar"
                  x={x}
                  y={yBottom - height}
                  width={barWidth}
                  height={height}
                  rx={Math.min(5, barWidth / 2)}
                />
                {showLabel && (
                  <text className="pa-dashboard-chart-x-label" x={left + step * (index + 0.5)} y={yBottom + 23} textAnchor="middle">
                    {bucket.label}
                  </text>
                )}
              </g>
            );
          })}
          <polyline className="pa-dashboard-chart-line" points={points} />
          {buckets.map((bucket, index) => (
            <circle
              className="pa-dashboard-chart-point"
              key={bucket.key}
              cx={left + step * (index + 0.5)}
              cy={yBottom - (bucket.cumulativeVnd / total) * plotHeight}
              r="3"
            />
          ))}
        </svg>
        <figcaption className="pa-dashboard-chart-caption">
          Tổng khoản thu trong {periodLabel}: <strong>{money(total)}</strong>
        </figcaption>
      </figure>
      <details className="pa-dashboard-chart-table-details">
        <summary>Xem bảng số liệu biểu đồ</summary>
        <div className="pa-dashboard-chart-table-wrap">
          <table>
            <caption>{`Khoản thu thành công trong ${periodLabel}`}</caption>
            <thead><tr><th scope="col">Kỳ</th><th scope="col">Khoản thu</th><th scope="col">Cộng dồn</th></tr></thead>
            <tbody>{buckets.map((bucket) => (
              <tr key={bucket.key}>
                <th scope="row">{bucket.label}</th>
                <td>{money(bucket.amountVnd)}</td>
                <td>{money(bucket.cumulativeVnd)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

function paymentOutcomeLabel(outcome: string) {
  if (outcome === "PAID") return "Thành công";
  if (outcome === "FAILED") return "Thất bại";
  if (outcome === "CANCELED") return "Đã hủy";
  return "Khác";
}

export function RecentPaymentEvents({ events }: { events: PaymentRecord[] }) {
  const recent = [...events]
    .sort((left, right) => new Date(right.created_at ?? "").getTime() - new Date(left.created_at ?? "").getTime())
    .slice(0, 6);
  if (recent.length === 0) {
    return <Empty text="Chưa có giao dịch" detail="Các giao dịch mới nhất sẽ xuất hiện tại đây." />;
  }
  return (
    <ol className="pa-dashboard-payment-list">
      {recent.map((event, index) => (
        <li key={event.event_id ?? `${event.created_at ?? "empty"}-${index}`}>
          <span className={`pa-dashboard-payment-state ${event.outcome === "PAID" ? "is-success" : event.outcome === "FAILED" ? "is-failed" : "is-neutral"}`}>
            {paymentOutcomeLabel(event.outcome)}
          </span>
          <strong>{money(event.amount_vnd)}</strong>
          <time dateTime={event.created_at ?? undefined}>{date(event.created_at)}</time>
        </li>
      ))}
    </ol>
  );
}

function healthLabel(status: string) {
  if (status === "healthy") return "Đang hoạt động";
  if (status === "unavailable") return "Chưa khả dụng";
  if (status === "not_configured") return "Chưa cấu hình";
  return "Chưa xác định";
}

function healthTone(status: string) {
  if (status === "healthy") return "is-healthy";
  if (status === "unavailable") return "is-error";
  return "is-pending";
}

const deliveryLabels: Record<string, string> = {
  pending: "Đang chờ gửi",
  sending: "Đang gửi",
  sent: "Đã gửi",
  failed: "Thất bại",
};

function deliveryLabel(state: string) {
  return deliveryLabels[state] ?? "Trạng thái khác";
}

function HealthCard({
  title,
  status,
  value,
  detail,
  icon,
}: {
  title: string;
  status: string;
  value: string;
  detail: string;
  icon: ReactNode;
}) {
  return (
    <section className="pa-panel pa-dashboard-health-card">
      <div className="pa-dashboard-health-icon" aria-hidden="true">{icon}</div>
      <div className="pa-dashboard-health-copy">
        <h3>{title}</h3>
        <p className={`pa-dashboard-health-label ${healthTone(status)}`}>{healthLabel(status)}</p>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </section>
  );
}

function QueueCount({ label, value }: { label: string; value: number }) {
  return (
    <div className="pa-dashboard-queue-count">
      <span>{label}</span>
      <strong>{number(value)}</strong>
    </div>
  );
}

export function OperationsOverview({
  operations,
  children,
}: {
  operations: Operations;
  children: ReactNode;
}) {
  const broker = operations.broker;
  const emailRows = [...operations.email].sort((left, right) => left.state.localeCompare(right.state));
  return (
    <div className="pa-dashboard-operations">
      <div className="pa-dashboard-health-grid">
        <HealthCard
          title="Kho dữ liệu"
          status={operations.database.status}
          value={operations.database.response_ms == null ? "—" : `${number(operations.database.response_ms)} ms`}
          detail={operations.database.response_ms == null ? "Thời gian phản hồi chưa có." : "Thời gian phản hồi."}
          icon={<Database size={19} />}
        />
        <HealthCard
          title="Hàng chờ xử lý"
          status={broker.status}
          value={broker.queue_count == null ? "—" : number(broker.queue_count)}
          detail="Số mục hiện có trong hàng chờ."
          icon={<Server size={19} />}
        />
        <section className="pa-panel pa-dashboard-health-card pa-dashboard-active-workers">
          <div className="pa-dashboard-health-icon" aria-hidden="true"><Activity size={19} /></div>
          <div className="pa-dashboard-health-copy">
            <h3>Tiến trình xử lý đang chạy</h3>
            <p className={`pa-dashboard-health-label ${broker.active_workers == null ? "is-pending" : "is-healthy"}`}>
              {broker.active_workers == null ? "Chưa có số liệu" : "Số liệu hiện tại"}
            </p>
            <strong>{broker.active_workers == null ? "—" : number(broker.active_workers)}</strong>
            <small>Số tiến trình đang phản hồi.</small>
          </div>
        </section>
      </div>

      <section className="pa-panel pa-dashboard-queue-panel" aria-labelledby="pa-dashboard-queue-title">
        <div className="pa-dashboard-panel-heading">
          <div><h2 id="pa-dashboard-queue-title">Công việc đang xử lý</h2><p>Số lượng hiện tại theo trạng thái.</p></div>
        </div>
        <div className="pa-dashboard-queue-counts">
          <QueueCount label="Đang chờ" value={operations.queue.queued_jobs} />
          <QueueCount label="Đang chạy" value={operations.queue.running_jobs} />
          <QueueCount label="Thất bại" value={operations.queue.failed_jobs} />
        </div>
      </section>

      <div className="pa-dashboard-operations-lower">
        <section className="pa-panel pa-dashboard-deliveries" aria-labelledby="pa-dashboard-delivery-title">
          <div className="pa-dashboard-panel-heading">
            <div><h2 id="pa-dashboard-delivery-title">Thư điện tử</h2><p>Số lần gửi theo trạng thái.</p></div>
          </div>
          {emailRows.length ? (
            <ul className="pa-dashboard-delivery-list">
              {emailRows.map((row) => (
                <li key={row.state}>
                  <span>{deliveryLabel(row.state)}</span>
                  <strong>{number(row.count)}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <Empty text="Chưa có lần gửi thư điện tử" detail="Số liệu sẽ xuất hiện sau khi có lượt gửi." />
          )}
        </section>
        {children}
      </div>
    </div>
  );
}

export function ProcessingDistribution({ operations }: { operations: Operations }) {
  const groups = [
    { key: "jobs", title: "Tác vụ xử lý", rows: operations.jobs },
    { key: "email", title: "Thư điện tử", rows: operations.email },
    { key: "core_outbox", title: "Sự kiện đã ghi nhận", rows: operations.core_outbox },
    { key: "lifecycle", title: "Yêu cầu dữ liệu", rows: operations.lifecycle },
  ].map((group) => ({ ...group, count: group.rows.reduce((sum, row) => sum + row.count, 0) }));
  const total = groups.reduce((sum, group) => sum + group.count, 0);
  if (total <= 0) {
    return <Empty text="Chưa có bản ghi xử lý" detail="Biểu đồ sẽ xuất hiện khi có số liệu." />;
  }
  const columns = groups.map((group) => ({ key: group.key, label: group.title, value: group.count, share: group.count / total * 100 }));
  return (
    <div className="pa-columns-panel pa-columns-panel-wide">
      <div>
        <p className="pa-columns-summary"><strong>{number(total)}</strong> Tổng bản ghi</p>
        <ColumnChart columns={columns} summary={`Phân bố ${number(total)} bản ghi; chi tiết trong bảng bên dưới`} unit="bản ghi" />
      </div>
      <table className="pa-columns-table" aria-label="Số bản ghi theo nhóm">
        <thead><tr><th scope="col">Nhóm</th><th scope="col">Số lượng</th><th scope="col">Tỷ trọng</th></tr></thead>
        <tbody>{columns.map((column) => <tr key={column.key}>
          <th scope="row">{column.label}</th>
          <td>{number(column.value)}</td>
          <td>{percent(column.share)}</td>
        </tr>)}</tbody>
      </table>
    </div>
  );
}
