import React, { useState } from 'react';
import { Text, View } from 'react-native';
import type { ParentUser } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';
import { safeParentIdentityErrorMessage } from '../navigation/workflowTypes';

type Props = {
  user: ParentUser | null;
  busy: boolean;
  error: string;
  onChangePassword: (currentPassword: string, nextPassword: string) => Promise<void>;
  onResetPassword: () => Promise<void>;
  onSignOut: () => void;
  onBack: () => void;
};

export function AccountScreen({ user, busy, error, onChangePassword, onResetPassword, onSignOut, onBack }: Props): React.JSX.Element {
  const [currentPassword, setCurrentPassword] = useState('');
  const [nextPassword, setNextPassword] = useState('');
  const [feedback, setFeedback] = useState('');

  async function updatePassword(): Promise<void> {
    setFeedback('');
    try {
      await onChangePassword(currentPassword, nextPassword);
      setCurrentPassword('');
      setNextPassword('');
      setFeedback('Mật khẩu đã được cập nhật trên Firebase Authentication.');
    } catch (cause) {
      setFeedback(safeParentIdentityErrorMessage(cause));
    }
  }

  return (
    <ScreenFrame title="Tài khoản" subtitle="Thông tin đăng nhập và bảo mật." onBack={onBack}>
      <Card>
        <SectionTitle>Thông tin đăng nhập</SectionTitle>
        <View style={{ gap: 4 }}>
          <Text style={{ color: palette.muted, fontSize: 13 }}>Email</Text>
          <Text selectable style={{ color: palette.ink, fontSize: 16, fontWeight: '700' }}>{user?.email || 'Không có email'}</Text>
        </View>
        <View style={{ gap: 4 }}>
          <Text style={{ color: palette.muted, fontSize: 13 }}>Vai trò</Text>
          <Text style={{ color: palette.ink, fontSize: 15, fontWeight: '700' }}>Phụ huynh · do máy chủ xác nhận</Text>
        </View>
      </Card>
      <Card>
        <SectionTitle>Đổi mật khẩu</SectionTitle>
        <Field label="Mật khẩu hiện tại" value={currentPassword} onChangeText={setCurrentPassword} secureTextEntry autoComplete="current-password" />
        <Field label="Mật khẩu mới" value={nextPassword} onChangeText={setNextPassword} secureTextEntry autoComplete="new-password" />
        {error ? <Notice text={error} tone="error" /> : null}
        {feedback ? <Notice text={feedback} tone={feedback.includes('đã được cập nhật') ? 'success' : 'error'} /> : null}
        <PrimaryButton label="Cập nhật mật khẩu" busy={busy} disabled={!currentPassword || nextPassword.length < 6} onPress={() => void updatePassword()} />
        <SecondaryButton label="Gửi email đặt lại mật khẩu" onPress={() => { setFeedback(''); void onResetPassword().then(() => setFeedback('Nếu email đã đăng ký, hướng dẫn đặt lại mật khẩu sẽ được gửi tới hộp thư.')).catch((cause: unknown) => setFeedback(safeParentIdentityErrorMessage(cause))); }} />
      </Card>
      <SecondaryButton label="Đăng xuất" onPress={onSignOut} />
    </ScreenFrame>
  );
}
