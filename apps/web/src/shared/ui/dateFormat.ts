const ISO_DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;
const LOCAL_DATETIME = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2})?$/;

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

/** Format an ISO date or timestamp into Vietnamese dd/mm/yyyy without timezone drift on date-only strings. */
export function formatDateDdMmYyyy(value: string | Date | null | undefined, fallback = "Chưa có ngày"): string {
  if (!value) return fallback;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return fallback;
    const dateOnly = ISO_DATE_ONLY.exec(trimmed);
    if (dateOnly) {
      return `${dateOnly[3]}/${dateOnly[2]}/${dateOnly[1]}`;
    }
    const localDt = LOCAL_DATETIME.exec(trimmed);
    if (localDt) {
      return `${localDt[3]}/${localDt[2]}/${localDt[1]}`;
    }
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return fallback;
  return `${pad2(date.getDate())}/${pad2(date.getMonth() + 1)}/${date.getFullYear()}`;
}

/** Format an ISO timestamp or local datetime string into dd/mm/yyyy HH:mm. */
export function formatDateTimeDdMmYyyy(value: string | Date | null | undefined, fallback = "Chưa có ngày"): string {
  if (!value) return fallback;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return fallback;
    const localDt = LOCAL_DATETIME.exec(trimmed);
    if (localDt) {
      return `${localDt[3]}/${localDt[2]}/${localDt[1]} ${localDt[4]}:${localDt[5]}`;
    }
    const dateOnly = ISO_DATE_ONLY.exec(trimmed);
    if (dateOnly) {
      return `${dateOnly[3]}/${dateOnly[2]}/${dateOnly[1]}`;
    }
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return fallback;
  return `${pad2(date.getDate())}/${pad2(date.getMonth() + 1)}/${date.getFullYear()} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}

/** Build the selected-date echo text shown below DateField. */
export function formatDateEcho(value: string, type: "date" | "datetime-local"): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const formatted = type === "datetime-local"
    ? formatDateTimeDdMmYyyy(trimmed, "")
    : formatDateDdMmYyyy(trimmed, "");
  return formatted ? `Đã chọn: ${formatted}` : null;
}
