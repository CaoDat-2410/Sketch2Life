import React from 'react';
import { StyleSheet, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentProfileDeletePendingV1, ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { isProfileDeletionPending, selectProfileById } from '../navigation/parentFlowV1';
import { canStartProfileLearning, parentProfileAgeEligibility } from '../navigation/workflowTypes';
import type { ParentConsentUiState } from '../navigation/workflowTypes';
import { Card, ChoiceRow, ConfirmButton, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, TextButton, palette } from '../components/ui';

type Props = {
  profiles: ParentProfileViewV1[];
  pendingDeletions: ParentProfileDeletePendingV1[];
  selectedProfileId: string;
  activeRun: ParentStoryRunV1 | null;
  error: string;
  busy: string;
  pendingDeletionLoadingId: string;
  consentState: ParentConsentUiState;
  onSelect: (profile: ParentProfileViewV1) => void;
  onCreate: () => void;
  onEdit: (profile: ParentProfileViewV1) => void;
  onRequestDeletion: (profile: ParentProfileViewV1) => void;
  onRefreshPendingDeletion: (profileId: string) => void;
  onContinue: (profile: ParentProfileViewV1) => void;
  onOpenAccount?: () => void;
  onOpenSettings?: () => void;
  onOpenNotifications?: () => void;
  onOpenQuota?: () => void;
  onOpenHistory?: () => void;
  onOpenSharing?: () => void;
  onOpenDeliveredLessons?: () => void;
  onSignOut?: () => void;
  onResumeRun?: () => void;
  onBackHome?: () => void;
};

const ignoreFamilyAction = (): void => undefined;

export function ProfileScreen({
  profiles,
  pendingDeletions,
  selectedProfileId,
  activeRun,
  error,
  busy,
  pendingDeletionLoadingId,
  consentState,
  onSelect,
  onCreate,
  onEdit,
  onRequestDeletion,
  onRefreshPendingDeletion,
  onContinue,
  onOpenAccount = ignoreFamilyAction,
  onOpenSettings = ignoreFamilyAction,
  onOpenNotifications = ignoreFamilyAction,
  onOpenQuota = ignoreFamilyAction,
  onOpenHistory = ignoreFamilyAction,
  onOpenSharing = ignoreFamilyAction,
  onOpenDeliveredLessons = ignoreFamilyAction,
  onSignOut = ignoreFamilyAction,
}: Props): React.JSX.Element {
  const selected = selectProfileById(profiles, selectedProfileId);
  const selectedAgeEligibility = selected ? parentProfileAgeEligibility(selected) : 'unavailable';
  const mayStartRun = Boolean(selected)
    && canStartProfileLearning(selectedAgeEligibility, consentState.status)
    && !isProfileDeletionPending(selected!.profile_id, pendingDeletions);

  return (
    <ScreenFrame title="Không gian gia đình" subtitle="Quản lý hồ sơ và hoạt động của gia đình.">
      <Notice text="Mỗi buổi học chỉ gắn với một hồ sơ trẻ." tone="info" />
      <Card style={styles.profileListCard}>
        <SectionTitle>Hồ sơ của bé</SectionTitle>
        {profiles.length === 0 ? <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 20 }}>
          Chưa có hồ sơ nào. Tạo hồ sơ để bắt đầu.
        </Text> : profiles.map((profile) => {
          const ageEligibility = parentProfileAgeEligibility(profile);
          const ageLabel = `${Math.floor(profile.age_months / 12)} tuổi · ${profile.age_months} tháng`;
          const ageBandRef = profile.age_band_ref?.trim() ?? '';
          const ageBandVersion = profile.age_band_version?.trim() ?? '';
          const hasAgeBandRef = ageBandRef.length > 0;
          const hasAgeBandVersion = ageBandVersion.length > 0;
          const hasIncompleteAgeBand = hasAgeBandRef !== hasAgeBandVersion;
          const versionLabel = hasAgeBandRef && hasAgeBandVersion
            ? `Nhóm ${ageBandRef}, phiên bản ${ageBandVersion}`
            : hasIncompleteAgeBand
              ? 'Chưa xác nhận được nhóm tuổi và phiên bản của hồ sơ. Hãy kiểm tra lại trước khi tiếp tục.'
              : ageEligibility === 'supported' ? 'Nhóm tuổi chưa khả dụng' : '';
          const eligibilityLabel = ageEligibility === 'legacy-read-only'
            ? 'Hồ sơ cũ, chỉ xem hoặc xóa'
            : ageEligibility === 'unavailable' && !hasIncompleteAgeBand ? 'Chưa thể xác nhận điều kiện tuổi' : '';
          return <ChoiceRow
            key={profile.profile_id}
            title={profile.display_name}
            detail={[ageLabel, versionLabel, eligibilityLabel].filter(Boolean).join(' · ')}
            selected={selectedProfileId === profile.profile_id}
            onPress={() => onSelect(profile)}
          />;
        })}
      </Card>

      {pendingDeletions.length ? <Card>
        <SectionTitle>Yêu cầu xóa đang chờ</SectionTitle>
        {pendingDeletions.map((pending) => <Card key={pending.profile_id} style={styles.pendingDeletionCard}>
          <Notice text="Hồ sơ đang chờ xử lý yêu cầu xóa. Hồ sơ chưa được xác nhận là đã xóa." tone="warning" />
          <SecondaryButton
            label={pendingDeletionLoadingId === pending.profile_id ? 'Đang kiểm tra…' : 'Kiểm tra trạng thái'}
            disabled={Boolean(pendingDeletionLoadingId) || Boolean(busy)}
            onPress={() => onRefreshPendingDeletion(pending.profile_id)}
          />
        </Card>)}
      </Card> : null}

      {!activeRun && selected ? <Card>
        <PrimaryButton label="Dùng hồ sơ này" disabled={!mayStartRun} onPress={() => onContinue(selected)} />
      </Card> : null}

      {selected ? <Card style={styles.selectedActionsCard}>
        <ConsentStatus state={consentState} />
        <SecondaryButton
          label="Chỉnh sửa hồ sơ"
          disabled={Boolean(busy) || selectedAgeEligibility !== 'supported'}
          onPress={() => onEdit(selected)}
        />
        {!isProfileDeletionPending(selected.profile_id, pendingDeletions) ? <ConfirmButton
          label="Yêu cầu xóa hồ sơ"
          title="Gửi yêu cầu xóa hồ sơ này?"
          message="Hồ sơ sẽ được hiển thị trong mục yêu cầu đang chờ cho đến khi có trạng thái mới."
          confirmLabel="Gửi yêu cầu"
          destructive
          onConfirm={() => onRequestDeletion(selected)}
        /> : null}
      </Card> : null}

      {error ? <Notice text={error} tone="error" /> : null}
      <SecondaryButton label="Tạo hồ sơ mới" disabled={Boolean(busy)} onPress={onCreate} />

      <Card style={styles.familyMenuCard}>
        <SectionTitle>Không gian của gia đình</SectionTitle>
        {!selected ? <Notice text="Chọn hồ sơ trẻ để xem bài đã dạy hoặc quản lý chia sẻ." tone="info" /> : null}

        <Text style={styles.menuGroupLabel}>TÀI KHOẢN</Text>
        <FamilyMenuRow label="Tài khoản và bảo mật" icon="shield-checkmark-outline" onPress={onOpenAccount} />

        <Text style={styles.menuGroupLabel}>CÀI ĐẶT</Text>
        <FamilyMenuRow label="Cài đặt" icon="settings-outline" onPress={onOpenSettings} />
        <FamilyMenuRow label="Thông báo" icon="notifications-outline" onPress={onOpenNotifications} />

        <Text style={styles.menuGroupLabel}>HOẠT ĐỘNG VÀ SỬ DỤNG</Text>
        <FamilyMenuRow label="Lượt tạo video" icon="videocam-outline" onPress={onOpenQuota} />
        <FamilyMenuRow label="Lịch sử hoạt động" icon="time-outline" onPress={onOpenHistory} />
        <FamilyMenuRow label="Bài giáo viên đã dạy" icon="book-outline" disabled={!selected} onPress={onOpenDeliveredLessons} />

        <Text style={styles.menuGroupLabel}>CHIA SẺ</Text>
        <FamilyMenuRow label="Chia sẻ hồ sơ với giáo viên" icon="share-social-outline" disabled={!selected} onPress={onOpenSharing} />
      </Card>
      <TextButton label="Đăng xuất" onPress={onSignOut} />
    </ScreenFrame>
  );
}

function FamilyMenuRow({
  label,
  icon,
  disabled = false,
  onPress,
}: {
  label: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  disabled?: boolean;
  onPress: () => void;
}): React.JSX.Element {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      activeOpacity={0.86}
      style={[styles.familyMenuRow, disabled && styles.disabledFamilyMenuRow]}
    >
      <Ionicons name={icon} size={19} color={disabled ? palette.muted : palette.ink} accessible={false} />
      <Text style={styles.familyMenuLabel}>{label}</Text>
      <Ionicons name="chevron-forward" size={18} color={palette.muted} accessible={false} />
    </TouchableOpacity>
  );
}

function ConsentStatus({ state }: { state: ParentConsentUiState }): React.JSX.Element {
  const message = state.status.state === 'unavailable'
    ? 'Chưa thể xác nhận trạng thái đồng ý qua máy chủ. Ghi nhận hoặc thu hồi đồng ý hiện chưa khả dụng; trạng thái này không ngăn bạn tiếp tục với hồ sơ đủ điều kiện.'
    : state.status.state === 'pending'
      ? 'Yêu cầu đồng ý đang chờ máy chủ xác nhận.'
      : state.status.state === 'revoked'
        ? 'Quyền xử lý đã bị thu hồi theo trạng thái máy chủ.'
        : state.status.state === 'confirmed'
          ? 'Máy chủ đã xác nhận đồng ý cho phiên bản chính sách được ghi nhận.'
          : 'Chưa có trạng thái đồng ý được máy chủ xác nhận.';
  return <>
    <SectionTitle>Quyền xử lý dữ liệu</SectionTitle>
    <Notice text={message} tone={state.status.state === 'confirmed' ? 'info' : 'warning'} />
    <Text style={styles.consentOperations}>
      Ghi nhận: {operationStateLabel(state.capture)} · Thu hồi: {operationStateLabel(state.revoke)}
    </Text>
  </>;
}

function operationStateLabel(state: ParentConsentUiState['capture']): string {
  if (state.state === 'confirmed') return 'đã được máy chủ xác nhận';
  if (state.state === 'pending') return 'đang chờ máy chủ';
  if (state.state === 'reconciling') return 'đang kiểm tra trạng thái';
  if (state.state === 'unavailable') return 'chưa khả dụng';
  if (state.state === 'failed') return 'chưa hoàn tất';
  return 'chưa bắt đầu';
}

const styles = StyleSheet.create({
  profileListCard: { backgroundColor: palette.white, gap: 14 },
  pendingDeletionCard: { backgroundColor: palette.paleAmber },
  selectedActionsCard: { backgroundColor: palette.white },
  consentOperations: { color: palette.muted, fontSize: 11, lineHeight: 15, minWidth: 0, flexShrink: 1 },
  familyMenuCard: { backgroundColor: palette.white, gap: 8 },
  menuGroupLabel: { color: palette.muted, fontSize: 10, lineHeight: 14, fontWeight: '800', letterSpacing: 0.6, marginTop: 4 },
  familyMenuRow: { minHeight: 48, minWidth: 0, paddingHorizontal: 8, borderRadius: 10, flexDirection: 'row', alignItems: 'center', gap: 10 },
  disabledFamilyMenuRow: { opacity: 0.62 },
  familyMenuLabel: { color: palette.ink, fontSize: 13, lineHeight: 18, fontWeight: '700', flex: 1, minWidth: 0, flexShrink: 1 },
});
