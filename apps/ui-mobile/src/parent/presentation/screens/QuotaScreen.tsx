import React from 'react';
import { Text } from 'react-native';
import type { ParentVideoQuota } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = { quota: ParentVideoQuota | null; loading: boolean; error: string; onLoad: () => void; onBack: () => void };

export function QuotaScreen({ quota, loading, error, onLoad, onBack }: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Lượt tạo video" subtitle="Số lượt sử dụng theo tài khoản." onBack={onBack}>
      {error ? <Notice text={error} tone="error" /> : null}
      <Card>
        {!quota || quota.configuration_state === 'NOT_CONFIGURED' ? <>
          <SectionTitle>Chưa cấu hình lượt dùng</SectionTitle>
          <Notice text="Tài khoản chưa có gói lượt tạo video được cấu hình. Chưa có số liệu để hiển thị." tone="warning" />
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
