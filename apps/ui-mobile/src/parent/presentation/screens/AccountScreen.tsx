import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
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
  const [feedbackTone, setFeedbackTone] = useState<'info' | 'success' | 'error'>('info');

  async function updatePassword(): Promise<void> {
    setFeedback('');
    try {
      await onChangePassword(currentPassword, nextPassword);
      setCurrentPassword('');
      setNextPassword('');
      setFeedbackTone('success');
      setFeedback('Mật khẩu đã được cập nhật.');
    } catch (cause: unknown) {
      setFeedbackTone('error');
      setFeedback(safeParentIdentityErrorMessage(cause));
    }
  }

  async function resetPassword(): Promise<void> {
    setFeedback('');
    try {
      await onResetPassword();
      setFeedbackTone('info');
      setFeedback('Nếu địa chỉ hợp lệ, hướng dẫn sẽ được gửi. Màn hình không tiết lộ trạng thái đăng ký.');
    } catch (cause: unknown) {
      setFeedbackTone('error');
      setFeedback(safeParentIdentityErrorMessage(cause));
    }
  }

  return (
    <ScreenFrame title="Cài đặt và tài khoản" subtitle="Quản lý đăng nhập phụ huynh." onBack={onBack}>
      <Card style={styles.identityCard}>
        <View style={styles.identityHeading}>
          <Text style={styles.identityBadge}>TÀI KHOẢN</Text>
          <Text style={styles.identityLabel}>TÀI KHOẢN ĐANG ĐĂNG NHẬP</Text>
        </View>
        <View style={styles.emailRow}>
          <View style={styles.identityMark} accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
            <View style={styles.identityDot} />
          </View>
          <Text selectable style={styles.emailValue}>{user?.email || 'Không có email'}</Text>
        </View>
      </Card>

      <Card style={styles.passwordCard}>
        <SectionTitle>Bảo mật tài khoản</SectionTitle>
        <Field
          label="Mật khẩu hiện tại"
          value={currentPassword}
          onChangeText={setCurrentPassword}
          placeholder="Nhập mật khẩu hiện tại"
          secureTextEntry
          autoComplete="current-password"
        />
        <Field
          label="Mật khẩu mới"
          value={nextPassword}
          onChangeText={setNextPassword}
          placeholder="Tạo mật khẩu mới"
          secureTextEntry
          autoComplete="new-password"
        />
        {error ? <Notice text={error} tone="error" /> : null}
        {feedback ? <Notice text={feedback} tone={feedbackTone} /> : null}
        <PrimaryButton label="Đổi mật khẩu" busy={busy} disabled={busy || !currentPassword || nextPassword.length < 6} onPress={() => void updatePassword()} />
        <SecondaryButton label="Gửi email đặt lại mật khẩu" onPress={() => { void resetPassword(); }} />
      </Card>

      <Card style={styles.signOutCard}>
        <Notice text="Đăng xuất sẽ kết thúc phiên này; cần xác thực lại để tiếp tục." tone="info" />
        <SecondaryButton label="Đăng xuất" onPress={onSignOut} />
      </Card>
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  identityCard: { backgroundColor: palette.white, gap: 12 },
  identityHeading: { gap: 6 },
  identityBadge: { alignSelf: 'flex-start', color: palette.ink, fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 0.6, paddingHorizontal: 9, paddingVertical: 5, borderWidth: 1, borderColor: palette.outline, borderRadius: 10, backgroundColor: palette.lilac },
  identityLabel: { color: palette.muted, fontSize: 10, lineHeight: 14, fontWeight: '800', letterSpacing: 0.4, flexShrink: 1 },
  emailRow: { flexDirection: 'row', alignItems: 'center', gap: 10, minWidth: 0, padding: 10, borderRadius: 14, backgroundColor: palette.background },
  identityMark: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 14, borderWidth: 1.5, borderColor: palette.outline, backgroundColor: palette.butter },
  identityDot: { width: 12, height: 12, borderRadius: 6, backgroundColor: palette.blue },
  emailValue: { flex: 1, minWidth: 0, color: palette.ink, fontSize: 15, lineHeight: 20, fontWeight: '700', flexShrink: 1 },
  passwordCard: { backgroundColor: palette.white, gap: 14 },
  signOutCard: { backgroundColor: palette.white, gap: 12 },
});
