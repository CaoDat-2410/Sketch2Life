import React from 'react';
import { StyleSheet, Switch, Text, View } from 'react-native';
import { Card, Notice, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';

type Props = {
  sketchGuideEnabled: boolean;
  onSketchGuideEnabled: (enabled: boolean) => void;
  onOpenAccount: () => void;
  onOpenProfiles: () => void;
  onOpenNotifications: () => void;
  onOpenQuota: () => void;
  onOpenHistory: () => void;
  onOpenSharing: () => void;
  onOpenDeliveredLessons: () => void;
  onBack: () => void;
};

export function SettingsScreen(props: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Cài đặt và tài khoản" subtitle="Quản lý đăng nhập phụ huynh." onBack={props.onBack}>
      <Card style={styles.languageCard}>
        <SectionTitle>Ngôn ngữ</SectionTitle>
        <View style={styles.languageRow}>
          <View style={styles.languageValue}><Text style={styles.valueText}>Tiếng Việt</Text></View>
        </View>
      </Card>

      <Card style={styles.guideCard}>
        <SectionTitle>Gợi ý trong buổi vẽ</SectionTitle>
        <View style={styles.guideToggleRow}>
          <Text style={styles.guideDescription}>Chỉ tạo gợi ý nét vẽ khi người lớn bật tùy chọn này trong buổi học.</Text>
          <Switch value={props.sketchGuideEnabled} onValueChange={props.onSketchGuideEnabled} accessibilityLabel="Bật gợi ý nét vẽ trong phiên hiện tại" />
        </View>
        <Notice text="Lựa chọn này chỉ áp dụng trong phiên đang mở, không lưu thành cài đặt tài khoản." />
      </Card>

      <Card style={styles.managementCard}>
        <SectionTitle>Quản lý</SectionTitle>
        <SecondaryButton label="Tài khoản và bảo mật" onPress={props.onOpenAccount} />
        <SecondaryButton label="Hồ sơ trẻ và quyền xử lý" onPress={props.onOpenProfiles} />
        <SecondaryButton label="Thông báo" onPress={props.onOpenNotifications} />
        <SecondaryButton label="Lượt tạo video" onPress={props.onOpenQuota} />
        <SecondaryButton label="Lịch sử hoạt động" onPress={props.onOpenHistory} />
        <SecondaryButton label="Bài giáo viên đã dạy" onPress={props.onOpenDeliveredLessons} />
        <SecondaryButton label="Chia sẻ hồ sơ với giáo viên" onPress={props.onOpenSharing} />
      </Card>
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  languageCard: { backgroundColor: palette.white, gap: 12 },
  languageRow: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 8, padding: 8, borderRadius: 14, backgroundColor: palette.background },
  languageValue: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 12, borderRadius: 14, borderWidth: 1.5, borderColor: palette.outline, backgroundColor: palette.butter },
  valueText: { color: palette.ink, fontSize: 12, lineHeight: 16, fontWeight: '700' },
  guideCard: { backgroundColor: palette.white, gap: 12 },
  guideToggleRow: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10, padding: 8, borderRadius: 14, backgroundColor: palette.background },
  guideDescription: { flex: 1, minWidth: 0, color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1 },
  managementCard: { backgroundColor: palette.white, gap: 10 },
});
