import React from 'react';
import { Text } from 'react-native';
import type { ParentProfileDeletePendingV1, ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { isProfileDeletionPending, selectProfileById } from '../navigation/parentFlowV1';
import { Card, ChoiceRow, ConfirmButton, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';

type Props = {
  profiles: ParentProfileViewV1[];
  pendingDeletions: ParentProfileDeletePendingV1[];
  selectedProfileId: string;
  activeRun: ParentStoryRunV1 | null;
  error: string;
  busy: string;
  pendingDeletionLoadingId: string;
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

  return (
    <ScreenFrame title="Hồ sơ của bé" subtitle="Chọn hồ sơ cho buổi học." onBack={onBackHome}>
      <Card>
        <SectionTitle>Danh sách hồ sơ</SectionTitle>
        {profiles.length === 0 ? <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 20 }}>
          Chưa có hồ sơ nào. Tạo hồ sơ để bắt đầu.
        </Text> : profiles.map((profile) => (
          <ChoiceRow
            key={profile.profile_id}
            title={profile.display_name}
            detail={`${Math.floor(profile.age_months / 12)} tuổi · ${profile.age_months} tháng`}
            selected={selectedProfileId === profile.profile_id}
            onPress={() => onSelect(profile)}
          />
        ))}
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
        <PrimaryButton label="Tiếp tục buổi đang mở" onPress={onResumeRun} />
      </Card> : selected ? <Card>
        <PrimaryButton label="Dùng hồ sơ này" onPress={() => onContinue(selected)} />
      </Card> : null}

      {selected ? <Card>
        <SecondaryButton label="Chỉnh sửa hồ sơ" disabled={Boolean(busy)} onPress={() => onEdit(selected)} />
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
