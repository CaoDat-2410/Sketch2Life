import React, { useState } from 'react';
import { Text, View } from 'react-native';
import type { ParentProfileShareGrant, ParentProfileViewV1 } from '../../domain/types';
import type { ParentCapabilityState, ParentOperationState } from '../../application/ports/ParentCapabilityPorts';
import { parentShareGrantExpiryState, parentShareGrantStateLabel } from '../navigation/workflowTypes';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SectionTitle, TextButton, palette } from '../components/ui';

type Props = {
  profile: ParentProfileViewV1 | null;
  grants: ParentProfileShareGrant[];
  loading: boolean;
  error: string;
  capability: ParentCapabilityState;
  inviteState: ParentOperationState<void>;
  revokeState: ParentOperationState<void>;
  onInvite: (teacherSubject: string) => Promise<ParentOperationState<void>>;
  onRevoke: (grantId: string) => ParentOperationState<void>;
  onBack: () => void;
};

export function ProfileSharingScreen(props: Props): React.JSX.Element {
  const [teacherSubject, setTeacherSubject] = useState('');
  const [formMessage, setFormMessage] = useState('');

  async function submit(): Promise<void> {
    setFormMessage('');
    const result = await props.onInvite(teacherSubject.trim());
    if (result.state === 'confirmed') {
      setTeacherSubject('');
      setFormMessage('Máy chủ đã xác nhận lời mời. Quyền chỉ có hiệu lực sau khi giáo viên chấp nhận.');
      return;
    }
    setFormMessage('Lời mời chưa được gửi. Mã giáo viên vẫn là bản nháp trên thiết bị.');
  }

  return (
    <ScreenFrame title="Chia sẻ hồ sơ" subtitle={props.profile?.display_name ?? 'Chọn hồ sơ của bé trước.'} onBack={props.onBack}>
      {!props.profile ? <Notice text="Chọn một hồ sơ để xem trạng thái chia sẻ." tone="warning" /> : <Card>
        <SectionTitle>Mời giáo viên</SectionTitle>
        <Text style={{ color: palette.muted, lineHeight: 20 }}>
          Lời mời có tên giáo viên, phạm vi 90 ngày và chỉ cấp quyền sau khi giáo viên chấp nhận. Việc thu hồi phải được máy chủ xác nhận.
        </Text>
        <Field
          label="Mã tài khoản giáo viên"
          value={teacherSubject}
          onChangeText={setTeacherSubject}
          autoCapitalize="none"
          autoCorrect={false}
        />
        {formMessage ? <Notice text={formMessage} tone={props.inviteState.state === 'confirmed' ? 'success' : 'warning'} /> : null}
        {props.capability.state === 'unavailable'
          ? <Notice text="Chưa thể gửi lời mời hoặc kiểm tra quyền chia sẻ. Chưa có thay đổi quyền nào được xác nhận." tone="warning" />
          : null}
        <PrimaryButton
          label="Gửi lời mời"
          busy={props.loading}
          disabled={!teacherSubject.trim() || props.loading || props.capability.state === 'unavailable'}
          onPress={() => void submit()}
        />
      </Card>}
      {props.error ? <Notice text="Chưa thể kiểm tra thông tin chia sẻ. Chưa có thay đổi nào được xác nhận." tone="warning" /> : null}
      <Card>
        <SectionTitle>Trạng thái quyền chia sẻ</SectionTitle>
        {props.capability.state === 'unavailable' ? <Notice
          text="Chưa thể xác nhận lời mời đang chờ, đã chấp nhận, bị từ chối, đã hết hạn hoặc đã thu hồi. Danh sách chưa tải được; trạng thái trống không có nghĩa là chưa có quyền."
          tone="warning"
        /> : !props.grants.length ? <Text style={{ color: palette.muted }}>Máy chủ chưa trả về lời mời hoặc quyền chia sẻ.</Text> : null}
        {props.capability.state === 'available'
          ? props.grants.map((grant) => <ViewGrant key={grant.grant_id} grant={grant} loading={props.loading} onRevoke={props.onRevoke} />)
          : null}
        <Text style={{ color: palette.muted, fontSize: 13 }}>
          Trạng thái gửi lời mời: {operationStateLabel(props.inviteState)} · Trạng thái thu hồi: {operationStateLabel(props.revokeState)}
        </Text>
      </Card>
    </ScreenFrame>
  );
}

function ViewGrant({ grant, loading, onRevoke }: {
  grant: ParentProfileShareGrant;
  loading: boolean;
  onRevoke: (id: string) => ParentOperationState<void>;
}): React.JSX.Element {
  const canRevoke = grant.state === 'INVITED' || grant.state === 'ACTIVE';
  const expiryState = parentShareGrantExpiryState(grant.state, grant.expires_at, Date.now());
  const expiryText = expiryState === 'expired'
    ? 'Đã qua thời điểm hết hạn; cần trạng thái mới từ máy chủ.'
    : grant.expires_at
      ? `Có hiệu lực đến ${new Date(grant.expires_at).toLocaleDateString('vi-VN')}`
      : 'Chưa có thời điểm hết hạn trong phản hồi máy chủ.';
  return <Card style={{ backgroundColor: palette.white }}>
    <Text style={{ color: palette.ink, fontWeight: '800' }}>{parentShareGrantStateLabel(grant.state)}</Text>
    <Text style={{ color: palette.muted, fontSize: 13 }}>Giáo viên: {grant.teacher_subject}</Text>
    <Text style={{ color: palette.muted, fontSize: 13 }}>{expiryText}</Text>
    {canRevoke ? <TextButton
      label="Thu hồi quyền chia sẻ"
      disabled={loading}
      onPress={() => { void onRevoke(grant.grant_id); }}
    /> : null}
  </Card>;
}

function operationStateLabel(state: ParentOperationState<void>): string {
  if (state.state === 'confirmed') return 'đã được máy chủ xác nhận';
  if (state.state === 'pending') return 'đang chờ máy chủ';
  if (state.state === 'reconciling') return 'đang kiểm tra trạng thái';
  if (state.state === 'unavailable') return 'chưa khả dụng';
  if (state.state === 'failed') return 'chưa hoàn tất';
  return 'chưa bắt đầu';
}
