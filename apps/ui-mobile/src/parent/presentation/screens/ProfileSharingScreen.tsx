import React, { useState } from 'react';
import { Text, View } from 'react-native';
import type { ParentProfileShareGrant, ParentProfileViewV1 } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SectionTitle, TextButton, palette } from '../components/ui';

type Props = {
  profile: ParentProfileViewV1 | null;
  grants: ParentProfileShareGrant[];
  loading: boolean;
  error: string;
  onInvite: (teacherSubject: string) => Promise<void>;
  onRevoke: (grantId: string) => void;
  onBack: () => void;
};

export function ProfileSharingScreen(props: Props): React.JSX.Element {
  const [teacherSubject, setTeacherSubject] = useState('');
  const [formError, setFormError] = useState('');

  async function submit(): Promise<void> {
    setFormError('');
    try {
      await props.onInvite(teacherSubject);
      setTeacherSubject('');
    } catch {
      setFormError('Chưa gửi được lời mời. Vui lòng kiểm tra lại rồi thử sau.');
    }
  }

  return (
    <ScreenFrame title="Chia sẻ hồ sơ" subtitle={props.profile?.display_name ?? 'Chọn hồ sơ của bé trước.'} onBack={props.onBack}>
      {!props.profile ? <Notice text="Chọn một hồ sơ để quản lý việc chia sẻ." tone="warning" /> : <Card>
        <SectionTitle>Mời giáo viên</SectionTitle>
        <Text style={{ color: palette.muted, lineHeight: 20 }}>
          Nhập mã tài khoản giáo viên. Lời mời chỉ có hiệu lực khi giáo viên chấp nhận.
        </Text>
        <Field label="Mã tài khoản giáo viên" value={teacherSubject} onChangeText={setTeacherSubject} autoCapitalize="none" />
        {formError ? <Notice text={formError} tone="error" /> : null}
        <PrimaryButton label="Gửi lời mời" busy={props.loading} disabled={!teacherSubject.trim()} onPress={() => void submit()} />
      </Card>}
      {props.error ? <Notice text="Chưa tải được thông tin chia sẻ. Vui lòng thử lại sau." tone="error" /> : null}
      <Card>
        <SectionTitle>Quyền chia sẻ</SectionTitle>
        {!props.grants.length ? <Text style={{ color: palette.muted }}>Chưa có lời mời hoặc quyền chia sẻ.</Text> : null}
        {props.grants.map((grant) => <ViewGrant key={grant.grant_id} grant={grant} loading={props.loading} onRevoke={props.onRevoke} />)}
      </Card>
    </ScreenFrame>
  );
}

function ViewGrant({ grant, loading, onRevoke }: { grant: ParentProfileShareGrant; loading: boolean; onRevoke: (id: string) => void }): React.JSX.Element {
  const canRevoke = grant.state === 'INVITED' || grant.state === 'ACTIVE';
  return <Card style={{ backgroundColor: '#F8FAFC' }}>
    <Text style={{ color: palette.ink, fontWeight: '800' }}>{shareStateLabel(grant.state)}</Text>
    <Text style={{ color: palette.muted, fontSize: 13 }}>Giáo viên: {grant.teacher_subject}</Text>
    {grant.expires_at ? <Text style={{ color: palette.muted, fontSize: 13 }}>Có hiệu lực đến {new Date(grant.expires_at).toLocaleDateString('vi-VN')}</Text> : null}
    {canRevoke ? <TextButton label="Thu hồi quyền chia sẻ" disabled={loading} onPress={() => onRevoke(grant.grant_id)} /> : null}
  </Card>;
}

function shareStateLabel(state: ParentProfileShareGrant['state']): string {
  const labels: Record<ParentProfileShareGrant['state'], string> = {
    INVITED: 'Đang chờ giáo viên', ACTIVE: 'Đang chia sẻ', DECLINED: 'Đã từ chối', REVOKED: 'Đã thu hồi', EXPIRED: 'Đã hết hạn',
  };
  return labels[state];
}
