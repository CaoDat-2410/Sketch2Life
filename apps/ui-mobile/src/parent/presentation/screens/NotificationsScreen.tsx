import React from 'react';
import { Text } from 'react-native';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import type { ParentNotification } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, TextButton, palette } from '../components/ui';

type Props = {
  capability: ParentCapabilityState;
  items: ParentNotification[];
  loading: boolean;
  error: string;
  hasMore: boolean;
  onLoad: () => void;
  onLoadMore: () => void;
  onMarkRead: (notificationId: string) => void;
  onBack: () => void;
};

export function NotificationsScreen(props: Props): React.JSX.Element {
  if (props.capability.state === 'unavailable') {
    return <ScreenFrame title="Thông báo" subtitle="Trạng thái tính năng" onBack={props.onBack}>
      <Notice text="Hộp thư chưa khả dụng vì chưa có hợp đồng dịch vụ được xác nhận. Danh sách chưa tải không có nghĩa là bạn chưa có thông báo; lời nhắc và đóng buổi do máy chủ quản lý." tone="warning" />
    </ScreenFrame>;
  }

  return (
    <ScreenFrame title="Thông báo" subtitle="Cập nhật trong ứng dụng." onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      <Card>
        <SectionTitle>Hộp thư</SectionTitle>
        {!props.items.length && !props.loading ? <Text style={{ color: palette.muted }}>Bạn chưa có thông báo.</Text> : null}
        {props.items.map((item) => <Card key={item.notification_id} style={{ backgroundColor: item.read_at ? '#F8FAFC' : '#EFF6FF' }}>
          <Text style={{ color: palette.ink, fontWeight: '700' }}>{item.title}</Text>
          <Text style={{ color: palette.muted, fontSize: 12 }}>{new Date(item.created_at).toLocaleString('vi-VN')}</Text>
          {!item.read_at ? <TextButton label="Đánh dấu đã xem" disabled={props.loading} onPress={() => props.onMarkRead(item.notification_id)} /> : null}
        </Card>)}
        {props.loading ? <Notice text="Đang tải thông báo…" /> : null}
        {!props.items.length ? <PrimaryButton label="Tải thông báo" busy={props.loading} onPress={props.onLoad} /> : null}
        {props.hasMore ? <PrimaryButton label="Xem thêm" busy={props.loading} onPress={props.onLoadMore} /> : null}
      </Card>
    </ScreenFrame>
  );
}
