import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';

type Props = {
  profiles: ParentProfileViewV1[];
  selectedProfile: ParentProfileViewV1 | null;
  activeRun: ParentStoryRunV1 | null;
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
  selectedProfile,
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
  const profileSummary = {
    title: 'Hồ sơ của bé',
    description: profiles.length === 0
      ? 'Tạo hồ sơ để lưu độ tuổi và sở thích cho từng buổi.'
      : `${profiles.length} hồ sơ đã sẵn sàng.`,
    actionLabel: 'Xem hồ sơ',
  };

  return (
    <ScreenFrame title="Trang chủ" subtitle="Cùng con bắt đầu một hành trình khám phá mới.">
      {error ? <Notice text={error} tone="warning" /> : null}

      <Card style={styles.featureCard}>
        <View style={styles.featureMark} accessible={false}>
          <Text style={styles.featureMarkText}>{activeRun ? '↗' : '＋'}</Text>
        </View>
        <SectionTitle>{activeRun ? 'Buổi học đang mở' : 'Bắt đầu cùng con'}</SectionTitle>
        <Text style={styles.featureDescription}>
          {activeRun
            ? 'Hoàn tất buổi hiện tại trước khi bắt đầu buổi mới.'
            : 'Chụp bức vẽ của con để khám phá chủ đề, hoạt động và câu chuyện.'}
        </Text>
        <PrimaryButton
          label={activeRun ? 'Tiếp tục buổi đang mở' : 'Bắt đầu buổi vẽ'}
          onPress={activeRun ? onResumeRun : onStart}
        />
      </Card>

      <Card style={styles.profileCard}>
        <SectionTitle>{profileSummary.title}</SectionTitle>
        {selectedProfile ? <Text style={styles.selectedProfile}>Bé đang chọn: {selectedProfile.display_name}</Text> : null}
        <Text style={styles.bodyText}>{profileSummary.description}</Text>
        <SecondaryButton label={profileSummary.actionLabel} onPress={onManageProfiles} />
      </Card>

      <Card style={styles.familyCard}>
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

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Đăng xuất"
        onPress={onSignOut}
        style={styles.signOut}
      >
        <Text style={styles.signOutText}>Đăng xuất</Text>
      </Pressable>
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  featureCard: {
    backgroundColor: palette.paleBlue,
    borderColor: '#D4E5FF',
    padding: 18,
  },
  featureMark: {
    width: 46,
    height: 46,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: palette.white,
  },
  featureMarkText: {
    color: palette.blue,
    fontSize: 27,
    lineHeight: 31,
    fontWeight: '700',
  },
  featureDescription: {
    color: palette.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  profileCard: {
    padding: 18,
  },
  bodyText: {
    color: palette.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  selectedProfile: {
    color: palette.ink,
    fontSize: 14,
    fontWeight: '700',
    lineHeight: 21,
  },
  familyCard: {
    gap: 10,
  },
  signOut: {
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  signOutText: {
    color: palette.blue,
    fontWeight: '700',
    textAlign: 'center',
  },
});
