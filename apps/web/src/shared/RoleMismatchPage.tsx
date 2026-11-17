
export function RoleMismatchPage({
  roleLabel,
  onLogout,
}: {
  roleLabel: string;
  onLogout: () => void;
}) {
  return (
    <main className="s2l-access-state">
      <section className="s2l-access-card" role="alert" aria-labelledby="s2l-access-title">
        <span className="s2l-access-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3.5 20 7v5.5c0 4.2-3.2 7.2-8 9-4.8-1.8-8-4.8-8-9V7l8-3.5Z" />
            <path d="m9 9 6 6m0-6-6 6" />
          </svg>
        </span>
        <p className="s2l-access-kicker">PHIÊN ĐĂNG NHẬP</p>
        <h1 id="s2l-access-title">Không thể mở cổng {roleLabel}</h1>
        <p className="s2l-access-copy">
          Phiên hiện tại chưa được xác nhận cho cổng này. Đăng xuất rồi đăng nhập lại bằng tài khoản có quyền phù hợp.
        </p>
        <button className="s2l-access-action" type="button" onClick={onLogout}>
          Đăng xuất và quay lại
        </button>
      </section>
    </main>
  );
}
