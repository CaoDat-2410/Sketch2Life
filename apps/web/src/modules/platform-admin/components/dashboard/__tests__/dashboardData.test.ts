import { describe, expect, it } from "vitest";
import {
  buildAccountRoleCounts,
  buildCashFlowBuckets,
  cappedSourceNote,
  isTestPaymentMode,
  summarizeInvoices,
  summarizePayments,
  type PaymentRecord,
} from "../dashboardData";

describe("platform overview data helpers", () => {
  it("sums successful payment events and pending or unsuccessful invoices separately", () => {
    const paymentSummary = summarizePayments([
      { outcome: "PAID", amount_vnd: 120_000, created_at: null },
      { outcome: "FAILED", amount_vnd: 80_000, created_at: null },
      { outcome: "PAID", amount_vnd: 30_000, created_at: null },
    ]);
    expect(paymentSummary).toEqual({ amountVnd: 150_000, count: 2 });

    const invoiceSummary = summarizeInvoices([
      { state: "PENDING", amount_vnd: 70_000 },
      { state: "FAILED", amount_vnd: 50_000 },
      { state: "CANCELED", amount_vnd: 25_000 },
      { state: "PAID", amount_vnd: 150_000 },
    ]);
    expect(invoiceSummary).toEqual({
      pendingAmountVnd: 70_000,
      pendingCount: 1,
      unsuccessfulAmountVnd: 75_000,
      unsuccessfulCount: 2,
    });
  });

  it("buckets daily payments by the Ho Chi Minh calendar date", () => {
    const events: PaymentRecord[] = [
      { outcome: "PAID", amount_vnd: 100, created_at: "2026-11-25T17:30:00Z" },
      { outcome: "PAID", amount_vnd: 200, created_at: "2026-11-26T16:30:00Z" },
      { outcome: "PAID", amount_vnd: 999, created_at: "2026-11-26T17:30:00Z" },
      { outcome: "FAILED", amount_vnd: 500, created_at: "2026-11-26T10:00:00Z" },
    ];
    const sevenDays = buildCashFlowBuckets(events, "7d", new Date("2026-11-26T10:00:00Z"));
    expect(sevenDays).toHaveLength(7);
    expect(sevenDays.at(-1)?.key).toBe("2026-11-26");
    expect(sevenDays.at(-1)?.amountVnd).toBe(300);
    expect(sevenDays.at(-1)?.cumulativeVnd).toBe(300);

    const thirtyDays = buildCashFlowBuckets([
      { outcome: "PAID", amount_vnd: 50, created_at: "2026-10-27T17:30:00Z" },
      { outcome: "PAID", amount_vnd: 70, created_at: "2026-10-27T16:30:00Z" },
    ], "30d", new Date("2026-11-26T10:00:00Z"));
    expect(thirtyDays).toHaveLength(30);
    expect(thirtyDays[0].key).toBe("2026-10-28");
    expect(thirtyDays[0].amountVnd).toBe(50);
  });

  it("buckets twelve months in local time and keeps cumulative totals ordered", () => {
    const buckets = buildCashFlowBuckets([
      { outcome: "PAID", amount_vnd: 100, created_at: "2025-12-31T16:59:00Z" },
      { outcome: "PAID", amount_vnd: 250, created_at: "2026-11-26T10:00:00Z" },
      { outcome: "PAID", amount_vnd: 900, created_at: "2025-11-30T16:30:00Z" },
    ], "12m", new Date("2026-11-26T10:00:00Z"));
    expect(buckets).toHaveLength(12);
    expect(buckets[0]).toMatchObject({ key: "2025-12", amountVnd: 100, cumulativeVnd: 100 });
    expect(buckets.at(-1)).toMatchObject({ key: "2026-11", amountVnd: 250, cumulativeVnd: 350 });
  });

  it("returns honest empty values without non-finite chart values", () => {
    expect(summarizePayments([])).toEqual({ amountVnd: 0, count: 0 });
    expect(summarizeInvoices([])).toEqual({
      pendingAmountVnd: 0,
      pendingCount: 0,
      unsuccessfulAmountVnd: 0,
      unsuccessfulCount: 0,
    });
    const buckets = buildCashFlowBuckets([], "7d", new Date("2026-11-26T10:00:00Z"));
    expect(buckets.every((bucket) => bucket.amountVnd === 0 && bucket.cumulativeVnd === 0)).toBe(true);
    expect(buckets.every((bucket) => Number.isFinite(bucket.amountVnd + bucket.cumulativeVnd))).toBe(true);
  });

  it("reports capped sources and derives only the unassigned account remainder", () => {
    expect(cappedSourceNote(501, 500, "giao dịch")).toContain("chỉ tính trên 500 bản ghi gần nhất");
    expect(cappedSourceNote(2, 2, "hóa đơn")).toBeNull();

    const roles = buildAccountRoleCounts(10, [2, 3, 1, 1]);
    expect(roles.consistent).toBe(true);
    expect(roles.rows.at(-1)).toMatchObject({ label: "Chưa phân vai trò", count: 3, percentage: 30 });
    expect(buildAccountRoleCounts(5, [2, 2, 2, 0]).consistent).toBe(false);
  });

  it("marks payment data as experimental whenever real collection is off or any sandbox is on", () => {
    expect(isTestPaymentMode({ real_payments_enabled: false, billing_sandbox_enabled: false })).toBe(true);
    expect(isTestPaymentMode({ real_payments_enabled: true, momo_sandbox_enabled: true })).toBe(true);
    expect(isTestPaymentMode({ real_payments_enabled: true, billing_sandbox_enabled: false })).toBe(false);
  });
});
