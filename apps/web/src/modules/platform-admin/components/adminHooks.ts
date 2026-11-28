import { useEffect, useRef, useState } from 'react'
import { BackendApiError, backendMessage } from '../../../shared/api/backendApi'
import { commandClient } from '../services/adminService'

export function useAdminQuery<T>(load: () => Promise<T>, identity: string) {
  const loader = useRef(load);
  useEffect(() => {
    loader.current = load;
  });
  const [version, bump] = useState(0);
  const [result, setResult] = useState<{
    identity: string;
    version: number;
    data: T | null;
    error: string;
    loading: boolean;
  }>(() => ({ identity, version: 0, data: null, error: "", loading: true }));
  useEffect(() => {
    let active = true;
    loader
      .current()
      .then((value) => {
        if (active) setResult({ identity, version, data: value, error: "", loading: false });
      })
      .catch((cause) => {
        if (active) setResult({ identity, version, data: null, error: adminError(cause), loading: false });
      });
    return () => {
      active = false;
    };
  }, [identity, version]);
  const current = result.identity === identity && result.version === version;
  return {
    data: current ? result.data : null,
    error: current ? result.error : "",
    loading: !current || result.loading,
    reload: () => bump((value) => value + 1),
  };
}
export function adminError(cause: unknown) {
  if (cause instanceof BackendApiError) {
    if (cause.status === 401)
      return "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
    if (cause.status === 403)
      return "Bạn chưa có quyền thực hiện thao tác này.";
    if (cause.status === 409)
      return "Dữ liệu đã thay đổi hoặc thao tác không còn phù hợp. Tải lại trước khi tiếp tục; nội dung bạn nhập vẫn được giữ.";
    if ([502, 503, 504].includes(cause.status))
      return "Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử tải lại sau ít phút.";
  }
  return backendMessage(cause);
}
export function useAdminCommand() {
  const [send] = useState(commandClient);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const locked = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  async function run<T>(work: () => Promise<T>, success?: (value: T) => void) {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await work();
      if (mounted.current) {
        success?.(result);
        setNotice("Đã lưu thay đổi.");
      }
    } catch (cause) {
      if (mounted.current) setError(adminError(cause));
    } finally {
      locked.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  function clear() {
    setError("");
    setNotice("");
  }
  return { send, busy, run, error, notice, clear };
}
export function useAdminCursor(identity: string) {
  const [stored, setStored] = useState<{
    identity: string;
    cursor: string | null;
    previous: Array<string | null>;
    page: number;
  }>({ identity, cursor: null, previous: [], page: 0 });
  const current = stored.identity === identity
    ? stored
    : { identity, cursor: null, previous: [] as Array<string | null>, page: 0 };
  return {
    cursor: current.cursor ?? undefined,
    page: current.page,
    hasPrevious: current.previous.length > 0,
    next: (nextCursor: string | null | undefined) => {
      if (!nextCursor) return;
      setStored({
        identity,
        cursor: nextCursor,
        previous: [...current.previous, current.cursor],
        page: current.page + 1,
      });
    },
    back: () => {
      if (!current.previous.length) return;
      setStored({
        identity,
        cursor: current.previous[current.previous.length - 1],
        previous: current.previous.slice(0, -1),
        page: Math.max(0, current.page - 1),
      });
    },
    reset: () => setStored({ identity, cursor: null, previous: [], page: 0 }),
  };
}
export const date = (value?: string | null) =>
  value
    ? new Intl.DateTimeFormat("vi-VN", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "Asia/Ho_Chi_Minh",
      }).format(new Date(value))
    : "—";
export const money = (value: number) =>
  new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(value);
export const short = (value: string) =>
  value.length > 20 ? value.slice(0, 8) + "…" + value.slice(-4) : value;
const labels: Record<string, string> = {
  active: "Hoạt động",
  ACTIVE: "Hoạt động",
  paused: "Tạm dừng",
  PAUSED: "Tạm dừng",
  suspended: "Tạm dừng",
  SUSPENDED: "Tạm dừng",
  inactive: "Ngừng hoạt động",
  INACTIVE: "Ngừng hoạt động",
  disabled: "Đã khóa",
  pending_verification: "Chờ xác minh",
  DRAFT: "Bản nháp",
  draft: "Bản nháp",
  PENDING_REVIEW: "Chờ duyệt",
  submitted: "Chờ duyệt",
  APPROVED: "Đã duyệt",
  approved: "Đã duyệt",
  CHANGES_REQUESTED: "Cần chỉnh sửa",
  changes_requested: "Cần chỉnh sửa",
  PUBLIC: "Công khai",
  PRIVATE: "Riêng tư",
  published: "Đã xuất bản",
  recalled: "Đã thu hồi",
  archived: "Đã lưu trữ",
  HIDDEN: "Đã ẩn",
  PAID: "Đã thanh toán",
  PENDING: "Chờ thanh toán",
  FAILED: "Thất bại",
  sent: "Đã gửi",
  pending: "Đang chờ",
  failed: "Thất bại",
  sending: "Đang gửi",
  received: "Đã tiếp nhận",
  identity_check: "Xác minh danh tính",
  scope_review: "Rà soát phạm vi",
  running: "Đang xử lý",
  requested: "Đang chờ xử lý",
  awaiting_external_purge: "Chờ xóa ở dịch vụ ngoài",
  completed: "Hoàn tất",
  exception: "Cần xử lý thủ công",
  canceled: "Đã hủy",
  partially_completed: "Hoàn tất một phần",
  rejected: "Đã từ chối",
  cancelled: "Đã hủy",
  INCLUDED: "Hạn mức tháng",
  TOP_UP: "Mua thêm",
  MONTHLY: "Gói tháng",
  ORGANIZATION: "Trường học",
  PARENT_ACCOUNT: "Phụ huynh",
  export: "Xuất dữ liệu",
  delete: "Xóa dữ liệu",
  GRACE: "Gia hạn bổ sung",
  RESTRICTED: "Bị hạn chế",
  CANCEL_AT_PERIOD_END: "Dừng khi hết kỳ",
  CANCELED: "Đã dừng",
  safety: "An toàn",
  pedagogical: "Sư phạm",
  approve: "Đồng ý",
  request_changes: "Cần chỉnh sửa",
};
export const label = (value: string) =>
  labels[value] ?? value.replaceAll("_", " ");
