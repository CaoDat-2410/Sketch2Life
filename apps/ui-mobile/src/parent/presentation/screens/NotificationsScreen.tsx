import React from 'react';
import { StyleSheet, Text } from 'react-native';
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
    return <ScreenFrame title="Thông báo" subtitle="Thông tin dành riêng cho tài khoản phụ huynh." onBack={props.onBack}>
      <Notice text="Hộp thư chưa khả dụng vì chưa có hợp đồng dịch vụ được xác nhận. Danh sách chưa tải không có nghĩa là bạn chưa có thông báo; lời nhắc và đóng buổi do máy chủ quản lý." tone="warning" />
    </ScreenFrame>;
  }

  return (
    <ScreenFrame title="Thông báo" subtitle="Thông tin dành riêng cho tài khoản phụ huynh." onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      <Card style={styles.inboxCard}>
        <SectionTitle>HỘP THƯ</SectionTitle>
        {!props.items.length && !props.loading ? <Text style={styles.emptyNotice}>Bạn chưa có thông báo.</Text> : null}
        {props.items.map((item) => <Card key={item.notification_id} style={[styles.notificationCard, { backgroundColor: item.read_at ? palette.white : palette.paleBlue }]}>
          <Text style={styles.notificationTitle}>{item.title}</Text>
          <Text style={styles.notificationDate}>{new Date(item.created_at).toLocaleString('vi-VN')}</Text>
          {!item.read_at ? <TextButton label="Đánh dấu đã đọc" disabled={props.loading} onPress={() => props.onMarkRead(item.notification_id)} /> : null}
        </Card>)}
        {props.items.length ? <Notice text="Thông báo không chứa tên trẻ, tranh, âm thanh, truyện hoặc video." tone="info" /> : null}
        {props.loading ? <Notice text="Đang tải thông báo…" /> : null}
        {!props.items.length ? <PrimaryButton label="Tải thông báo" busy={props.loading} onPress={props.onLoad} /> : null}
        {props.hasMore ? <PrimaryButton label="Xem thêm" busy={props.loading} onPress={props.onLoadMore} /> : null}
      </Card>
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  inboxCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  notificationCard: { gap: 8, minWidth: 0 },
  emptyNotice: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  notificationTitle: { color: palette.ink, fontWeight: '700', fontSize: 12, lineHeight: 16, flexShrink: 1, minWidth: 0 },
  notificationDate: { color: palette.muted, fontSize: 10, lineHeight: 14, flexShrink: 1, minWidth: 0 },
});
