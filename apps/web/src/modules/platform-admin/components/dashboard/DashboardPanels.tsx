import type { ReactNode } from "react";
import { Activity, Database, Server } from "lucide-react";
import type { Operations, OrganizationSummary } from "../../services/adminService";
import { Empty } from "../AdminUI";
import { date, money } from "../adminHooks";
import {
  buildCashFlowBuckets,
  sharePercentage,
  type AccountRoleCount,
  type CashFlowRange,
  type PaymentRecord,
} from "./dashboardData";

const number = (value: number) => value.toLocaleString("vi-VN");
const percent = (value: number) => `${value.toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`;

const schoolStates = [
  { key: "active", label: "Đang hoạt động", color: "var(--pa-success)" },
  { key: "paused", label: "Tạm dừng", color: "var(--pa-warning)" },
  { key: "disabled", label: "Đã ngừng", color: "var(--pa-danger)" },
  { key: "other", label: "Trạng thái khác", color: "var(--pa-muted-strong)" },
] as const;

export function OrganizationStateOverview({ summary }: { summary: OrganizationSummary }) {
  const activeShare = sharePercentage(summary.active, summary.total);
  const arcLength = Math.PI * 86;
  return (
    <div className="pa-dashboard-state-overview">
      {summary.total > 0 ? (
        <div className="pa-dashboard-gauge-wrap">
          <svg
            className="pa-dashboard-gauge"
            viewBox="0 0 224 132"
            role="img"
            aria-label={`Trường đang hoạt động chiếm ${percent(activeShare)} trong tổng số ${number(summary.total)} trường`}
          >
            <title>Tỷ lệ trường đang hoạt động</title>
            <desc>{`${number(summary.active)} trong ${number(summary.total)} trường đang hoạt động.`}</desc>
            <path className="pa-dashboard-gauge-track" d="M 26 108 A 86 86 0 0 1 198 108" />
            <path
              className="pa-dashboard-gauge-value"
              d="M 26 108 A 86 86 0 0 1 198 108"
              strokeDasharray={`${arcLength * activeShare / 100} ${arcLength}`}
            />
            <text className="pa-dashboard-gauge-percent" x="112" y="92" textAnchor="middle">{percent(activeShare)}</text>
            <text className="pa-dashboard-gauge-caption" x="112" y="115" textAnchor="middle">trường hoạt động</text>
          </svg>
          <p className="pa-dashboard-gauge-total">{number(summary.active)} / {number(summary.total)} trường</p>
        </div>
      ) : (
        <div className="pa-dashboard-gauge-empty">
          <Empty text="Chưa có trường học" detail="Tỷ lệ sẽ xuất hiện khi có dữ liệu trường học." />
        </div>
      )}
      {summary.total > 0 && (
        <div className="pa-dashboard-share-list" aria-label="Số trường theo trạng thái">
          {schoolStates.map((state) => {
            const count = summary[state.key];
            const ratio = sharePercentage(count, summary.total);
            return (
              <div className="pa-dashboard-share-row" key={state.key}>
                <div className="pa-dashboard-share-heading">
                  <span><i style={{ backgroundColor: state.color }} aria-hidden="true" />{state.label}</span>
                  <strong>{number(count)} <small>{percent(ratio)}</small></strong>
                </div>
                <div className="pa-dashboard-share-track" role="img" aria-label={`${state.label}: ${number(count)} trường, ${percent(ratio)}`}>
                  <span style={{ width: `${ratio}%`, backgroundColor: state.color }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
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
  return (
    <div className="pa-dashboard-share-list pa-dashboard-role-list" aria-label="Tỷ lệ tài khoản theo vai trò">
      {rows.map((row, index) => {
        const color = index === 0
          ? "var(--pa-primary)"
          : index === 1
            ? "var(--pa-success)"
            : index === 2
              ? "var(--pa-warning)"
              : "var(--pa-chart-email)";
        return (
          <div className="pa-dashboard-share-row" key={row.label}>
            <div className="pa-dashboard-share-heading">
              <span><i style={{ backgroundColor: color }} aria-hidden="true" />{row.label}</span>
              <strong>{number(row.count)} <small>{percent(row.percentage)}</small></strong>
            </div>
            <div className="pa-dashboard-share-track" role="img" aria-label={`${row.label}: ${number(row.count)} tài khoản, ${percent(row.percentage)}`}>
              <span style={{ width: `${row.percentage}%`, backgroundColor: color }} />
            </div>
          </div>
        );
      })}
    </div>
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
    { key: "jobs", title: "Tác vụ xử lý", color: "var(--pa-chart-ai)", rows: operations.jobs },
    { key: "email", title: "Thư điện tử", color: "var(--pa-chart-email)", rows: operations.email },
    { key: "core_outbox", title: "Sự kiện đã ghi nhận", color: "var(--pa-chart-event)", rows: operations.core_outbox },
    { key: "lifecycle", title: "Yêu cầu dữ liệu", color: "var(--pa-chart-lifecycle)", rows: operations.lifecycle },
  ].map((group) => ({ ...group, count: group.rows.reduce((sum, row) => sum + row.count, 0) }));
  const total = groups.reduce((sum, group) => sum + group.count, 0);
  if (total <= 0) {
    return <Empty text="Chưa có bản ghi xử lý" detail="Biểu đồ sẽ xuất hiện khi có số liệu." />;
  }
  let end = 0;
  const segments = groups.map((group) => {
    const start = end;
    end += group.count / total * 100;
    return group.color + " " + start + "% " + end + "%";
  });
  return (
    <div className="pa-donut-layout">
      <div
        className="pa-donut"
        role="img"
        aria-label={`Phân bố ${number(total)} bản ghi; chi tiết trong bảng bên cạnh`}
        style={{ background: `conic-gradient(${segments.join(",")})` }}
      >
        <div><strong>{number(total)}</strong><span>Tổng bản ghi</span></div>
      </div>
      <table className="pa-donut-legend" aria-label="Số bản ghi theo nhóm">
        <thead><tr><th scope="col">Nhóm</th><th scope="col">Số lượng</th><th scope="col">Tỷ trọng</th></tr></thead>
        <tbody>{groups.map((group) => <tr key={group.key}>
          <th scope="row"><span style={{ background: group.color }} aria-hidden="true" />{group.title}</th>
          <td>{number(group.count)}</td>
          <td>{percent(group.count / total * 100)}</td>
        </tr>)}</tbody>
      </table>
    </div>
  );
}
