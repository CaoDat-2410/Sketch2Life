import React from 'react';
import { Text } from 'react-native';
import type { ParentProfileDeletePendingV1, ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { isProfileDeletionPending, selectProfileById } from '../navigation/parentFlowV1';
import { canStartProfileLearning, parentProfileAgeEligibility } from '../navigation/workflowTypes';
import type { ParentConsentUiState } from '../navigation/workflowTypes';
import { Card, ChoiceRow, ConfirmButton, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';

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
  onResumeRun: () => void;
  onBackHome: () => void;
};

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
  onResumeRun,
  onBackHome,
}: Props): React.JSX.Element {
  const selected = selectProfileById(profiles, selectedProfileId);
  const selectedAgeEligibility = selected ? parentProfileAgeEligibility(selected) : 'unavailable';
  const mayContinue = Boolean(selected)
    && canStartProfileLearning(selectedAgeEligibility, consentState.status)
    && !isProfileDeletionPending(selected!.profile_id, pendingDeletions);

  return (
    <ScreenFrame title="Hồ sơ của bé" subtitle="Chọn hồ sơ cho buổi học." onBack={onBackHome}>
      <Card>
        <SectionTitle>Danh sách hồ sơ</SectionTitle>
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
        {pendingDeletions.map((pending) => <Card key={pending.profile_id} style={{ backgroundColor: '#FFF8E8' }}>
          <Notice text="Hồ sơ đang chờ xử lý yêu cầu xóa. Hồ sơ chưa được xác nhận là đã xóa." tone="warning" />
          <SecondaryButton
            label={pendingDeletionLoadingId === pending.profile_id ? 'Đang kiểm tra…' : 'Kiểm tra trạng thái'}
            disabled={Boolean(pendingDeletionLoadingId) || Boolean(busy)}
            onPress={() => onRefreshPendingDeletion(pending.profile_id)}
          />
        </Card>)}
      </Card> : null}

      {activeRun ? <Card>
        <Notice text={`Đang có buổi học chưa hoàn tất (${activeRun.run_state}).`} tone="warning" />
        <PrimaryButton label="Tiếp tục buổi đang mở" disabled={!mayContinue} onPress={onResumeRun} />
      </Card> : selected ? <Card>
        <PrimaryButton label="Dùng hồ sơ này" disabled={!mayContinue} onPress={() => onContinue(selected)} />
      </Card> : null}

      {selected ? <Card>
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
    </ScreenFrame>
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
  return <Card>
    <SectionTitle>Quyền xử lý dữ liệu</SectionTitle>
    <Notice text={message} tone={state.status.state === 'confirmed' ? 'info' : 'warning'} />
    <Text style={{ color: palette.muted, fontSize: 13 }}>
      Ghi nhận: {operationStateLabel(state.capture)} · Thu hồi: {operationStateLabel(state.revoke)}
    </Text>
  </Card>;
}

function operationStateLabel(state: ParentConsentUiState['capture']): string {
  if (state.state === 'confirmed') return 'đã được máy chủ xác nhận';
  if (state.state === 'pending') return 'đang chờ máy chủ';
  if (state.state === 'reconciling') return 'đang kiểm tra trạng thái';
  if (state.state === 'unavailable') return 'chưa khả dụng';
  if (state.state === 'failed') return 'chưa hoàn tất';
  return 'chưa bắt đầu';
}
