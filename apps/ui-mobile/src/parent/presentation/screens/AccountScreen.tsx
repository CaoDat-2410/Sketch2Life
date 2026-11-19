import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentUser } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, palette } from '../components/ui';
import { safeParentIdentityErrorMessage } from '../navigation/workflowTypes';

type Props = {
  user: ParentUser | null;
  busy: boolean;
  error: string;
  onChangePassword: (currentPassword: string, nextPassword: string) => Promise<void>;
  onResetPassword: () => Promise<void>;
  onBack: () => void;
};

export function AccountScreen({ user, busy, error, onChangePassword, onResetPassword, onBack }: Props): React.JSX.Element {
  const [currentPassword, setCurrentPassword] = useState('');
  const [nextPassword, setNextPassword] = useState('');
  const [feedback, setFeedback] = useState('');
  const [feedbackTone, setFeedbackTone] = useState<'info' | 'success' | 'error'>('info');
  const [resetBusy, setResetBusy] = useState(false);

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
    if (resetBusy || busy) return;
    setFeedback('');
    setResetBusy(true);
    try {
      await onResetPassword();
      setFeedbackTone('info');
      setFeedback('Nếu email có tài khoản, hướng dẫn đặt lại mật khẩu sẽ được gửi.');
    } catch (cause: unknown) {
      setFeedbackTone('error');
      setFeedback(safeParentIdentityErrorMessage(cause));
    } finally {
      setResetBusy(false);
    }
  }

  const noticeText = error || feedback;
  const noticeTone = error ? 'error' : feedbackTone;

  return (
    <ScreenFrame title="Tài khoản và bảo mật" subtitle="Quản lý email và mật khẩu phụ huynh." onBack={onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']}>
      <Card variant="creative" style={styles.identityCard}>
        <View style={styles.identityHeading}>
          <View style={styles.identityIcon}>
            <Ionicons name="person-circle-outline" size={25} color={palette.creativePrimary} accessible={false} />
          </View>
          <View style={styles.identityCopy}>
            <Text style={styles.identityTitle}>Tài khoản phụ huynh</Text>
          </View>
        </View>
        <View style={styles.emailRow}>
          <Ionicons name="mail-outline" size={19} color={palette.creativeMuted} accessible={false} />
          <Text selectable style={styles.emailValue}>{user?.email || 'Không có email'}</Text>
        </View>
      </Card>

      <Card variant="creative" style={styles.passwordCard}>
        <View style={styles.sectionHeading}>
          <View style={styles.sectionIcon}><Ionicons name="key-outline" size={19} color={palette.creativePrimary} accessible={false} /></View>
          <View style={styles.sectionCopy}>
            <Text style={styles.sectionTitle}>Đổi mật khẩu</Text>
          </View>
        </View>
        <Field
          variant="creative"
          label="Mật khẩu hiện tại"
          value={currentPassword}
          onChangeText={setCurrentPassword}
          placeholder="Nhập mật khẩu hiện tại"
          editable={!busy && !resetBusy}
          secureTextEntry
          autoComplete="current-password"
        />
        <Field
          variant="creative"
          label="Mật khẩu mới"
          value={nextPassword}
          onChangeText={setNextPassword}
          placeholder="Ít nhất 6 ký tự"
          editable={!busy && !resetBusy}
          secureTextEntry
          autoComplete="new-password"
        />
        {noticeText ? <Notice variant="creative" text={noticeText} tone={noticeTone} /> : null}
        <PrimaryButton variant="creative" label="Đổi mật khẩu" busy={busy} disabled={busy || resetBusy || !currentPassword || nextPassword.length < 6} onPress={() => void updatePassword()} />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Quên mật khẩu? Gửi liên kết đặt lại qua email"
          accessibilityState={{ disabled: busy || resetBusy, busy: resetBusy }}
          disabled={busy || resetBusy}
          onPress={() => { void resetPassword(); }}
          style={({ pressed }) => [styles.resetLink, (busy || resetBusy) && styles.resetLinkDisabled, pressed && styles.resetLinkPressed]}
        >
          {resetBusy ? <ActivityIndicator size="small" color={palette.creativePrimary} /> : <Ionicons name="mail-unread-outline" size={17} color={palette.creativePrimary} accessible={false} />}
          <Text style={styles.resetLinkText}>{resetBusy ? 'Đang gửi hướng dẫn…' : 'Quên mật khẩu? Gửi liên kết đặt lại'}</Text>
        </Pressable>
      </Card>
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  identityCard: { backgroundColor: '#FFFEFF', gap: 10, borderRadius: 22 },
  identityHeading: { flexDirection: 'row', alignItems: 'center', gap: 10, minWidth: 0 },
  identityIcon: { width: 44, height: 44, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  identityCopy: { flex: 1, minWidth: 0, gap: 2 },
  identityTitle: { color: palette.creativeInk, fontSize: 15, lineHeight: 20, fontWeight: '800' },
  emailRow: { flexDirection: 'row', alignItems: 'center', gap: 10, minWidth: 0, minHeight: 46, paddingHorizontal: 12, borderRadius: 14, backgroundColor: palette.creativeLavender },
  emailValue: { flex: 1, minWidth: 0, color: palette.creativeInk, fontSize: 14, lineHeight: 20, fontWeight: '700', flexShrink: 1 },
  passwordCard: { backgroundColor: '#FFFEFF', gap: 13, borderRadius: 22 },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  sectionIcon: { width: 40, height: 40, borderRadius: 14, backgroundColor: '#F1E7FF', alignItems: 'center', justifyContent: 'center' },
  sectionCopy: { flex: 1, minWidth: 0, gap: 2 },
  sectionTitle: { color: palette.creativeInk, fontSize: 16, lineHeight: 21, fontWeight: '800' },
  resetLink: { minHeight: 48, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 14 },
  resetLinkText: { color: palette.creativePrimary, fontSize: 13, lineHeight: 18, fontWeight: '800', textAlign: 'center' },
  resetLinkDisabled: { opacity: 0.62 },
  resetLinkPressed: { backgroundColor: '#F7F1FE' },
});
