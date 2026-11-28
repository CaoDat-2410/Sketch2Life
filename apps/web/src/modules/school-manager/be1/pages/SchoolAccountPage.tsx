import { useEffect, useState } from "react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { authService } from "../services/authService";

type AccountIdentity = {
  displayName: string | null;
  email: string | null;
};

export function SchoolAccountPage() {
  const [account, setAccount] = useState<AccountIdentity | null>(null);

  useEffect(() => authService.observe((user) => {
    setAccount({ displayName: user?.displayName ?? null, email: user?.email ?? null });
  }), []);

  return (
    <div className="s2l-page manager-business-page">
      <PageHeading
        eyebrow="Quản lý trường"
        title="Thông tin tài khoản"
        description="Thông tin của tài khoản đang đăng nhập."
      />
      <section className="manager-business-card" aria-label="Thông tin tài khoản">
        <dl className="manager-business-organization">
          <div>
            <dt>Tên hiển thị</dt>
            <dd>{account?.displayName || "Chưa có tên hiển thị"}</dd>
          </div>
          <div>
            <dt>Thư điện tử</dt>
            <dd>{account?.email || "Chưa có thông tin"}</dd>
          </div>
          <div>
            <dt>Vai trò</dt>
            <dd>Quản lý trường</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
