import React from 'react';
import { Switch, Text } from 'react-native';
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
    <ScreenFrame title="Cài đặt" subtitle="Các tùy chọn dành cho người lớn." onBack={props.onBack}>
      <Card>
        <SectionTitle>Ngôn ngữ</SectionTitle>
        <Text style={{ color: palette.ink, fontSize: 15 }}>Tiếng Việt</Text>
      </Card>
      <Card>
        <SectionTitle>Gợi ý trong buổi vẽ</SectionTitle>
        <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 20 }}>Chỉ tạo line-sketch khi người lớn bật tùy chọn này trong buổi học.</Text>
        <Switch value={props.sketchGuideEnabled} onValueChange={props.onSketchGuideEnabled} accessibilityLabel="Bật gợi ý line-sketch trong phiên hiện tại" />
        <Notice text="Lựa chọn này chỉ áp dụng trong phiên đang mở, không lưu thành cài đặt tài khoản." />
      </Card>
      <Card>
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
