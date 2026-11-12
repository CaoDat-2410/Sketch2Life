import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {EmptyState, InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentSectionHeading} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

export function NotificationInboxScreen({state, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  const preferenceCopy = state.pushPreference === 'enabled-preview'
    ? 'Đang bật trong preview; quyền hệ điều hành và thiết bị chưa đăng ký.'
    : state.pushPreference === 'revoked-preview'
      ? 'Đã tắt trong preview; máy chủ chưa có endpoint nào để thu hồi.'
      : 'Chưa bật; ba mẹ có thể xem lý do và đổi lựa chọn trong Cài đặt.';
  return (
    <View style={styles.page}>
      <PreviewBanner title="Hộp thư chưa kết nối" body="Không có push notification hoặc trạng thái giả được tạo." />
      <ParentSectionHeading eyebrow="CẬP NHẬT CHO BA MẸ" title="Thông báo" />
      <InfoBanner title="Nhắc việc có giới hạn" body="Bản thật có thể nhắc khi cần ba mẹ xem lại; hệ thống không gửi nội dung riêng tư trong push." />
      <InfoBanner title={state.pushPreference === 'enabled-preview' ? 'Tùy chọn đang bật trong preview' : 'Tùy chọn thông báo'} body={preferenceCopy} />
      <EmptyState icon="notifications" title="Bạn đang cập nhật" description="Khi có thông báo thuộc hồ sơ được phép xem, chúng sẽ xuất hiện ở đây." />
      <ParentCard style={styles.reminderCard}>
        <Text style={styles.reminderTitle}>Các trạng thái cần theo dõi</Text>
        <Reminder icon="clock" title="Chờ ba mẹ xem" detail="Có thể nhắc ở mốc 144 giờ theo cấu hình server." />
        <Reminder icon="spark" title="Job lỗi hoặc bị chặn" detail="Thông báo lỗi cần đường khôi phục rõ ràng." />
        <Reminder icon="lock" title="Run tự đóng" detail="Idle closeout 168 giờ thuộc logic máy chủ." />
      </ParentCard>
      <ParentButton title="Cài đặt thông báo" variant="secondary" onPress={() => onNavigate('settings')} />
      <ParentButton title="Tải lại" variant="quiet" onPress={() => onNotice('Notification API chưa kết nối; không có lệnh tải lại được gửi.')} />
    </View>
  );
}

function Reminder({icon, title, detail}: Readonly<{icon: 'clock' | 'spark' | 'lock'; title: string; detail: string}>): React.JSX.Element {
  return <ParentCard tone="muted" style={styles.reminder}><ParentIcon name={icon} size={17}/><View style={styles.copy}><Text style={styles.title}>{title}</Text><Text style={styles.detail}>{detail}</Text></View></ParentCard>;
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  reminderCard: {gap: 12},
  reminderTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  reminder: {flexDirection: 'row', alignItems: 'center', gap: 9, padding: 11, borderRadius: 14, shadowOpacity: 0, elevation: 0},
  copy: {flex: 1, gap: 3},
  title: {color: sketchColors.ink, fontSize: 10, fontWeight: '800'},
  detail: {color: sketchColors.muted, fontSize: 9, lineHeight: 14},
});
