import React from 'react';
import { Text } from 'react-native';
import type { ParentProfile, StoryRun } from '../../domain/types';
import { Card, ChoiceRow, ConfirmButton, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';

type Props = {
  profiles: ParentProfile[];
  selectedProfileId: string;
  activeRun: StoryRun | null;
  error: string;
  busy: string;
  onSelect: (profile: ParentProfile) => void;
  onCreate: () => void;
  onEdit: (profile: ParentProfile) => void;
  onAuthorize: (profile: ParentProfile) => void;
  onRevoke: (profile: ParentProfile) => void;
  onArchive: (profile: ParentProfile) => void;
  onContinue: (profile: ParentProfile) => void;
  onResumeRun: () => void;
  onBackHome: () => void;
};

export function ProfileScreen({
  profiles,
  selectedProfileId,
  activeRun,
  error,
  busy,
  onSelect,
  onCreate,
  onEdit,
  onAuthorize,
  onRevoke,
  onArchive,
  onContinue,
  onResumeRun,
  onBackHome,
}: Props): React.JSX.Element {
  const selected = profiles.find((item) => item.parent_profile_id === selectedProfileId) ?? null;

  return (
    <ScreenFrame title="Hồ sơ của bé" subtitle="Chọn hồ sơ cho buổi học." onBack={onBackHome}>
      <Card>
        <SectionTitle>Danh sách hồ sơ</SectionTitle>
        {profiles.length === 0 ? (
          <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 20 }}>
            Chưa có hồ sơ nào. Tạo hồ sơ riêng để bắt đầu.
          </Text>
        ) : profiles.map((profile) => (
          <ChoiceRow
            key={profile.parent_profile_id}
            title={profile.current_revision.display_name}
            detail={`${Math.floor(profile.current_revision.age_months / 12)} tuổi · ${profile.authorization_current ? 'Đã cấp quyền' : 'Cần xác nhận quyền'}`}
            selected={selectedProfileId === profile.parent_profile_id}
            onPress={() => onSelect(profile)}
          />
        ))}
      </Card>

      {activeRun ? (
        <Card>
          <Notice text={`Đang có buổi học chưa hoàn tất (${activeRun.run_state}).`} tone="warning" />
          <PrimaryButton label="Tiếp tục buổi đang mở" onPress={onResumeRun} />
        </Card>
      ) : selected && !selected.authorization_current ? (
        <Card>
          <Notice text="Hồ sơ chưa có quyền xử lý dữ liệu còn hiệu lực." tone="warning" />
          <PrimaryButton
            label="Xác nhận quyền xử lý dữ liệu"
            busy={busy === 'authorize'}
            onPress={() => onAuthorize(selected)}
          />
        </Card>
      ) : selected?.authorization_current ? (
        <Card><PrimaryButton label="Dùng hồ sơ này" onPress={() => onContinue(selected)} /></Card>
      ) : null}

      {selected ? (
        <Card>
          <SecondaryButton label="Chỉnh sửa hồ sơ" onPress={() => onEdit(selected)} />
          {selected.authorization_current ? <ConfirmButton
            label="Thu hồi quyền xử lý dữ liệu"
            title="Thu hồi quyền xử lý?"
            message="Các buổi mới sẽ bị chặn cho đến khi người lớn cấp quyền lại."
            confirmLabel="Thu hồi quyền"
            destructive
            onConfirm={() => onRevoke(selected)}
          /> : null}
          <ConfirmButton
            label="Lưu trữ hồ sơ"
            title="Lưu trữ hồ sơ này?"
            message="Hồ sơ sẽ không còn xuất hiện trong danh sách hoạt động. Dữ liệu lịch sử không bị xóa."
            confirmLabel="Lưu trữ"
            destructive
            onConfirm={() => onArchive(selected)}
          />
        </Card>
      ) : null}

      {error ? <Notice text={error} tone="error" /> : null}
      <SecondaryButton label="Tạo hồ sơ mới" onPress={onCreate} />
    </ScreenFrame>
  );
}
