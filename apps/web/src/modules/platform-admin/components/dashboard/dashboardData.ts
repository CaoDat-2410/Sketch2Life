export type CashFlowRange = "7d" | "30d" | "12m";

export type PaymentRecord = {
  event_id?: string;
  outcome: string;
  amount_vnd: number;
  created_at: string | null;
};

export type InvoiceRecord = {
  state: string;
  amount_vnd: number;
};

export const ACCOUNT_ROLE_DEFINITIONS = [
  { role: "parent", label: "Phụ huynh" },
  { role: "teacher", label: "Giáo viên" },
  { role: "school_manager", label: "Quản lý trường" },
  { role: "platform_admin", label: "Quản trị nền tảng" },
] as const;

export type AccountRoleCount = {
  label: string;
  count: number;
  percentage: number;
};

export function safeAmount(value: number): number {
  return Number.isFinite(value) && value > 0 ? value : 0;
}

export function sharePercentage(count: number, total: number): number {
  if (!Number.isFinite(count) || !Number.isFinite(total) || total <= 0) return 0;
  return Math.min(100, Math.max(0, (count / total) * 100));
}

export function buildAccountRoleCounts(
  totalValue: number,
  counts: readonly number[],
): { total: number; rows: AccountRoleCount[]; consistent: boolean } {
  const total = Number.isFinite(totalValue) ? Math.max(0, totalValue) : 0;
  const roleRows: { label: string; count: number }[] = ACCOUNT_ROLE_DEFINITIONS.map((definition, index) => ({
    label: definition.label,
    count: Math.max(0, Number.isFinite(counts[index]) ? counts[index] : 0),
  }));
  const roleTotal = roleRows.reduce((sum, row) => sum + row.count, 0);
  const consistent = roleTotal <= total;
  if (consistent && total > roleTotal) {
    roleRows.push({ label: "Chưa phân vai trò", count: total - roleTotal });
  }
  return {
    total,
    consistent,
    rows: roleRows.map((row) => ({
      ...row,
      percentage: sharePercentage(row.count, total),
    })),
  };
}

export function summarizePayments(events: readonly PaymentRecord[]) {
  return events.reduce(
    (summary, event) => {
      if (event.outcome === "PAID") {
        summary.amountVnd += safeAmount(event.amount_vnd);
        summary.count += 1;
      }
      return summary;
    },
    { amountVnd: 0, count: 0 },
  );
}

export function summarizeInvoices(invoices: readonly InvoiceRecord[]) {
  return invoices.reduce(
    (summary, invoice) => {
      if (invoice.state === "PENDING") {
        summary.pendingAmountVnd += safeAmount(invoice.amount_vnd);
        summary.pendingCount += 1;
      } else if (invoice.state === "FAILED" || invoice.state === "CANCELED") {
        summary.unsuccessfulAmountVnd += safeAmount(invoice.amount_vnd);
        summary.unsuccessfulCount += 1;
      }
      return summary;
    },
    {
      pendingAmountVnd: 0,
      pendingCount: 0,
      unsuccessfulAmountVnd: 0,
      unsuccessfulCount: 0,
    },
  );
}

function dateParts(date: Date) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const value = (type: string) => parts.find((part) => part.type === type)?.value ?? "00";
  return { year: Number(value("year")), month: Number(value("month")), day: Number(value("day")) };
}

function localDayKey(date: Date): string {
  const { year, month, day } = dateParts(date);
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function localMonthKey(date: Date): string {
  const { year, month } = dateParts(date);
  return `${year}-${String(month).padStart(2, "0")}`;
}

function shiftDay(key: string, amount: number): string {
  const [year, month, day] = key.split("-").map(Number);
  const shifted = new Date(Date.UTC(year, month - 1, day + amount));
  return `${shifted.getUTCFullYear()}-${String(shifted.getUTCMonth() + 1).padStart(2, "0")}-${String(shifted.getUTCDate()).padStart(2, "0")}`;
}

function shiftMonth(key: string, amount: number): string {
  const [year, month] = key.split("-").map(Number);
  const index = year * 12 + month - 1 + amount;
  return `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, "0")}`;
}

function bucketLabel(key: string, range: CashFlowRange): string {
  const dayKey = range === "12m" ? `${key}-01` : key;
  const parsed = new Date(`${dayKey}T12:00:00.000Z`);
  return new Intl.DateTimeFormat("vi-VN", {
    timeZone: "Asia/Ho_Chi_Minh",
    ...(range === "12m" ? { month: "short" as const, year: "numeric" as const } : { day: "numeric" as const, month: "short" as const }),
  }).format(parsed);
}

export type CashFlowBucket = {
  key: string;
  label: string;
  amountVnd: number;
  cumulativeVnd: number;
  paymentCount: number;
};

export function buildCashFlowBuckets(
  events: readonly PaymentRecord[],
  range: CashFlowRange,
  now: Date = new Date(),
): CashFlowBucket[] {
  let keys: string[];
  if (range === "12m") {
    const currentMonth = localMonthKey(now);
    keys = Array.from({ length: 12 }, (_, index) => shiftMonth(currentMonth, index - 11));
  } else {
    const length = range === "7d" ? 7 : 30;
    const today = localDayKey(now);
    keys = Array.from({ length }, (_, index) => shiftDay(today, index - length + 1));
  }

  const totals = new Map(keys.map((key) => [key, { amountVnd: 0, paymentCount: 0 }]));
  for (const event of events) {
    if (event.outcome !== "PAID" || !event.created_at) continue;
    const createdAt = new Date(event.created_at);
    if (!Number.isFinite(createdAt.getTime())) continue;
    const key = range === "12m" ? localMonthKey(createdAt) : localDayKey(createdAt);
    const bucket = totals.get(key);
    if (!bucket) continue;
    bucket.amountVnd += safeAmount(event.amount_vnd);
    bucket.paymentCount += 1;
  }

  let cumulativeVnd = 0;
  return keys.map((key) => {
    const bucket = totals.get(key) ?? { amountVnd: 0, paymentCount: 0 };
    cumulativeVnd += bucket.amountVnd;
    return {
      key,
      label: bucketLabel(key, range),
      amountVnd: bucket.amountVnd,
      cumulativeVnd,
      paymentCount: bucket.paymentCount,
    };
  });
}

export function cappedSourceNote(
  total: number | undefined,
  itemCount: number,
  sourceLabel: string,
): string | null {
  if (total === undefined || !Number.isFinite(total) || total <= itemCount) return null;
  return `Có ${total.toLocaleString("vi-VN")} ${sourceLabel}; số liệu dưới đây chỉ tính trên ${itemCount.toLocaleString("vi-VN")} bản ghi gần nhất đã tải.`;
}

export function isTestPaymentMode(settings: {
  real_payments_enabled: boolean;
  momo_sandbox_enabled?: boolean;
  vnpay_sandbox_enabled?: boolean;
  billing_sandbox_enabled?: boolean;
}): boolean {
  return !settings.real_payments_enabled
    || settings.momo_sandbox_enabled === true
    || settings.vnpay_sandbox_enabled === true
    || settings.billing_sandbox_enabled === true;
}

/** Whole-number axis from zero: the smallest 1/2/5 step that needs at most four intervals. */
export function integerAxis(maxValue: number) {
  const top = Math.max(1, Math.ceil(maxValue));
  let step = 1;
  for (let magnitude = 1; top / step > 4; magnitude *= 10) {
    step = [1, 2, 5, 10].map((base) => base * magnitude).find((candidate) => top / candidate <= 4) ?? 10 * magnitude;
  }
  const intervals = Math.ceil(top / step);
  return { max: intervals * step, ticks: Array.from({ length: intervals + 1 }, (_, index) => index * step) };
}
