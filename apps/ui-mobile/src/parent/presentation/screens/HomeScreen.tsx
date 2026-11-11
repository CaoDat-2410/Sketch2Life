import React from 'react';
import { Text, View } from 'react-native';
import type { ParentProfile, StoryRun } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';

type Props = {
  profiles: ParentProfile[];
  activeRun: StoryRun | null;
  error: string;
  onStart: () => void;
  onManageProfiles: () => void;
  onOpenLessons: () => void;
  onOpenAccount: () => void;
  onOpenSettings: () => void;
  onOpenNotifications: () => void;
  onOpenQuota: () => void;
  onOpenHistory: () => void;
  onOpenSharing: () => void;
  onOpenDeliveredLessons: () => void;
  onResumeRun: () => void;
  onSignOut: () => void;
};

export function HomeScreen({
  profiles,
  activeRun,
  error,
  onStart,
  onManageProfiles,
  onOpenLessons,
  onOpenAccount,
  onOpenSettings,
  onOpenNotifications,
  onOpenQuota,
  onOpenHistory,
  onOpenSharing,
  onOpenDeliveredLessons,
  onResumeRun,
  onSignOut,
}: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Trang chủ" subtitle="Cùng con bắt đầu một hành trình khám phá mới.">
      {error ? <Notice text={error} tone="warning" /> : null}
      {activeRun ? (
        <Card>
          <SectionTitle>Buổi học đang mở</SectionTitle>
          <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 20 }}>
            Hoàn tất buổi hiện tại trước khi bắt đầu buổi mới.
          </Text>
          <PrimaryButton label="Tiếp tục buổi đang mở" onPress={onResumeRun} />
        </Card>
      ) : (
        <Card>
          <SectionTitle>Bắt đầu cùng con</SectionTitle>
          <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 20 }}>
            Chụp bức vẽ của con để khám phá chủ đề, hoạt động và câu chuyện.
          </Text>
          <PrimaryButton label="Bắt đầu buổi vẽ" onPress={onStart} />
        </Card>
      )}

      <Card>
        <SectionTitle>Hồ sơ của bé</SectionTitle>
        <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 20 }}>
          {profiles.length === 0
            ? 'Tạo hồ sơ để lưu độ tuổi và sở thích cho từng buổi.'
            : `${profiles.length} hồ sơ đã sẵn sàng.`}
        </Text>
        <SecondaryButton label="Xem hồ sơ" onPress={onManageProfiles} />
      </Card>

      <Card>
        <SectionTitle>Không gian của gia đình</SectionTitle>
        <SecondaryButton label="Xem bài giảng" onPress={onOpenLessons} />
        <SecondaryButton label="Tài khoản và bảo mật" onPress={onOpenAccount} />
        <SecondaryButton label="Cài đặt" onPress={onOpenSettings} />
        <SecondaryButton label="Thông báo" onPress={onOpenNotifications} />
        <SecondaryButton label="Lượt tạo video" onPress={onOpenQuota} />
        <SecondaryButton label="Lịch sử hoạt động" onPress={onOpenHistory} />
        <SecondaryButton label="Bài giáo viên đã dạy" onPress={onOpenDeliveredLessons} />
        <SecondaryButton label="Chia sẻ hồ sơ với giáo viên" onPress={onOpenSharing} />
      </Card>

      <View style={{ paddingTop: 4 }}>
        <Text
          accessibilityRole="button"
          onPress={onSignOut}
          style={{ color: palette.blue, fontWeight: '700', textAlign: 'center', padding: 12 }}
        >
          Đăng xuất
        </Text>
      </View>
    </ScreenFrame>
  );
}
