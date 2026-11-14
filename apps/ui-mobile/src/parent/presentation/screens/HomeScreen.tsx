import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import type { ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';
import { PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE } from '../navigation/workflowTypes';

type Props = {
  profiles: ParentProfileViewV1[];
  selectedProfile: ParentProfileViewV1 | null;
  activeRun: ParentStoryRunV1 | null;
  error: string;
  onStart: () => void;
  onManageProfiles: () => void;
  onOpenLessons: () => void;
  onResumeRun: () => void;
  onOpenAccount?: () => void;
  onOpenSettings?: () => void;
  onOpenNotifications?: () => void;
  onOpenQuota?: () => void;
  onOpenHistory?: () => void;
  onOpenSharing?: () => void;
  onOpenDeliveredLessons?: () => void;
  onSignOut?: () => void;
};

export function HomeScreen({
  selectedProfile,
  activeRun,
  error,
  onStart,
  onManageProfiles,
  onOpenLessons,
  onResumeRun,
}: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Trang chủ" subtitle="Cùng con bắt đầu một hành trình khám phá.">
      {error ? <Notice text={error} tone="warning" /> : null}

      <Card style={styles.featureCard}>
        <View style={styles.featureHeading}>
          <Text style={styles.featureTitle}>Bắt đầu cùng con</Text>
          <Text style={styles.stateBadge}>{activeRun ? 'BUỔI HỌC ĐANG MỞ' : 'BUỔI MỚI'}</Text>
        </View>
        <HomeIllustration />
        <Text style={styles.featureDescription}>Minh họa tĩnh bằng nét SVG, không phải tranh của trẻ.</Text>
        <PrimaryButton
          label={activeRun ? 'Tiếp tục buổi đang mở' : 'Bắt đầu buổi vẽ'}
          disabled={!activeRun && error === PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE}
          onPress={activeRun ? onResumeRun : onStart}
        />
      </Card>

      <Card style={styles.profileCard}>
        <SectionTitle>Hồ sơ đang chọn</SectionTitle>
        {selectedProfile ? <View style={styles.selectedProfileBadge}><Text style={styles.selectedProfile}>{selectedProfile.display_name}</Text></View> : <Text style={styles.bodyText}>Chưa có hồ sơ được chọn.</Text>}
        <SecondaryButton label="Quản lý hồ sơ" onPress={onManageProfiles} />
      </Card>

      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="Khám phá bài giảng"
        onPress={onOpenLessons}
        activeOpacity={0.86}
        style={styles.galleryRow}
      >
        <Ionicons name="book-outline" size={19} color={palette.ink} accessible={false} />
        <Text style={styles.galleryLabel}>Khám phá bài giảng</Text>
        <Ionicons name="chevron-forward" size={19} color={palette.muted} accessible={false} />
      </TouchableOpacity>
    </ScreenFrame>
  );
}

function HomeIllustration(): React.JSX.Element {
  return (
    <View accessible={false} style={styles.illustrationWrap}>
      <Svg width="100%" height="100%" viewBox="0 0 280 120" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <Rect x={4} y={4} width={272} height={112} rx={13} fill={palette.white} />
        <Circle cx={226} cy={30} r={14} fill={palette.butter} stroke={palette.outline} strokeWidth={2.4} />
        <Path d="M31 89q39-12 72 0t67 0 75-3" fill="none" stroke={palette.outline} strokeWidth={3} strokeLinecap="round" />
        <Path d="M132 83V47m-1 19q-20-4-21-18 14-6 21 18m1 7q16-16 30-6-4 15-30 6" fill={palette.paleGreen} stroke={palette.outline} strokeWidth={2.5} strokeLinejoin="round" />
        <Circle cx={132} cy={39} r={8} fill={palette.paleRed} stroke={palette.outline} strokeWidth={2} />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  featureCard: { backgroundColor: palette.butter, gap: 11 },
  featureHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, minWidth: 0 },
  featureTitle: { color: palette.ink, fontSize: 16, lineHeight: 20, fontWeight: '800', flex: 1, minWidth: 0, flexShrink: 1 },
  stateBadge: { color: palette.ink, fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 0.5, paddingHorizontal: 7, paddingVertical: 3, borderWidth: 1, borderColor: palette.outline, borderRadius: 999, backgroundColor: palette.white, flexShrink: 1, textAlign: 'center' },
  illustrationWrap: { width: '100%', aspectRatio: 280 / 120, borderWidth: 1, borderColor: palette.outline, borderRadius: 13, overflow: 'hidden', backgroundColor: palette.white },
  featureDescription: { color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1 },
  profileCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  selectedProfileBadge: { alignSelf: 'flex-start', minHeight: 44, justifyContent: 'center', maxWidth: '100%', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 14, borderWidth: 1.5, borderColor: palette.outline, backgroundColor: palette.paleGreen },
  bodyText: { color: palette.muted, fontSize: 12, lineHeight: 17, minWidth: 0, flexShrink: 1 },
  selectedProfile: { color: palette.ink, fontSize: 13, lineHeight: 18, fontWeight: '700', flexShrink: 1 },
  galleryRow: { minHeight: 52, minWidth: 0, padding: 8, borderRadius: 12, borderWidth: 1.3, borderColor: palette.outline, backgroundColor: palette.white, flexDirection: 'row', alignItems: 'center', gap: 8 },
  galleryLabel: { color: palette.ink, fontSize: 12, lineHeight: 16, fontWeight: '700', flex: 1, minWidth: 0, flexShrink: 1 },
});
