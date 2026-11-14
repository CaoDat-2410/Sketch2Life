import React from 'react';
import { StyleSheet, Text } from 'react-native';
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
    return <ScreenFrame title="Lượt tạo video" subtitle="Tóm tắt từ dữ liệu máy chủ." onBack={onBack}>
      <Notice text="Chưa có tóm tắt hạn mức được máy chủ xác nhận. Không hiển thị số liệu ước tính và chưa có thao tác mua." tone="warning" />
    </ScreenFrame>;
  }

  return (
    <ScreenFrame title="Lượt tạo video" subtitle="Tóm tắt từ dữ liệu máy chủ." onBack={onBack}>
      {error ? <Notice text={error} tone="error" /> : null}
      <Card style={styles.quotaCard}>
        <SectionTitle>Tóm tắt lượt dùng</SectionTitle>
        {!quota ? <>
          <Notice text="Chưa có số liệu để hiển thị." tone="warning" />
        </> : quota.configuration_state === 'NOT_CONFIGURED' ? <>
          <Notice text="CHƯA CẤU HÌNH · Máy chủ xác nhận chưa có cấu hình lượt tạo video." tone="warning" />
          <Text style={styles.quotaHint}>Số dư và kỳ sử dụng phải đến từ máy chủ.</Text>
        </> : <>
          <Text style={styles.quotaTotal}>Còn {quota.available} lượt</Text>
          <Text style={styles.quotaValue}>Đã dùng {quota.used} / {quota.granted}</Text>
          <Text style={styles.quotaHint}>Số dư và kỳ sử dụng phải đến từ máy chủ.</Text>
          <Text style={styles.quotaHint}>Kỳ sử dụng: {new Date(quota.period_start).toLocaleDateString('vi-VN')} – {new Date(quota.period_end).toLocaleDateString('vi-VN')}</Text>
        </>}
        <PrimaryButton label="Cập nhật số liệu" busy={loading} onPress={onLoad} />
      </Card>
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  quotaCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  quotaTotal: { color: palette.ink, fontSize: 16, lineHeight: 20, fontWeight: '800', flexShrink: 1, minWidth: 0 },
  quotaValue: { color: palette.ink, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  quotaHint: { color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1, minWidth: 0 },
});
