import React from 'react';
import { Text } from 'react-native';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import type { ParentVideoQuota } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  capability: ParentCapabilityState;
  quota: ParentVideoQuota | null;
  loading: boolean;
  error: string;
  onLoad: () => void;
  onBack: () => void;
};

export function QuotaScreen(props: Props): React.JSX.Element {
  const { quota, loading, error, onLoad, onBack } = props;
  if (props.capability.state === 'unavailable') {
    return <ScreenFrame title="Lượt tạo video" subtitle="Trạng thái tính năng" onBack={onBack}>
      <Notice text="Chưa có tóm tắt hạn mức được máy chủ xác nhận. Không hiển thị số liệu ước tính và chưa có thao tác mua." tone="warning" />
    </ScreenFrame>;
  }

  return (
    <ScreenFrame title="Lượt tạo video" subtitle="Số lượt sử dụng theo tài khoản." onBack={onBack}>
      {error ? <Notice text={error} tone="error" /> : null}
      <Card>
        {!quota ? <>
          <SectionTitle>Chưa tải tóm tắt lượt dùng</SectionTitle>
          <Notice text="Chưa có tóm tắt hạn mức được máy chủ xác nhận." tone="warning" />
        </> : quota.configuration_state === 'NOT_CONFIGURED' ? <>
          <SectionTitle>Chưa cấu hình lượt dùng</SectionTitle>
          <Notice text="Máy chủ xác nhận chưa có cấu hình lượt tạo video." tone="warning" />
        </> : <>
          <SectionTitle>Còn {quota.available} lượt</SectionTitle>
          <Text style={{ color: palette.ink }}>Đã dùng {quota.used} / {quota.granted}</Text>
          <Text style={{ color: palette.muted, fontSize: 13 }}>Kỳ sử dụng: {new Date(quota.period_start).toLocaleDateString('vi-VN')} – {new Date(quota.period_end).toLocaleDateString('vi-VN')}</Text>
        </>}
        <PrimaryButton label="Cập nhật số liệu" busy={loading} onPress={onLoad} />
      </Card>
    </ScreenFrame>
  );
}
