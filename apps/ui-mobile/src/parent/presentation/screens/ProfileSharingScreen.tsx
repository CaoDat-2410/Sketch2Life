import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentProfileShareGrant, ParentProfileViewV1 } from '../../domain/types';
import type { ParentCapabilityState, ParentOperationState } from '../../application/ports/ParentCapabilityPorts';
import { parentShareGrantExpiryState, parentShareGrantStateLabel } from '../navigation/workflowTypes';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, TextButton, palette } from '../components/ui';

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
  const [formMessage, setFormMessage] = useState<{
    text: string;
    tone: 'info' | 'success' | 'warning';
  } | null>(null);
  const sharingUnavailable = props.capability.state === 'unavailable';
  const inviteBusy = props.inviteState.state === 'pending' || props.inviteState.state === 'reconciling';
  const shareStatusMessage = sharingUnavailable
    ? 'Chia sẻ hiện chưa khả dụng. Chưa có thay đổi nào được xác nhận.'
    : props.error
      ? 'Không tải được trạng thái chia sẻ.'
      : '';
  const operationStatuses = [
    { icon: 'paper-plane-outline' as const, label: 'Mời', state: props.inviteState },
    { icon: 'refresh-outline' as const, label: 'Thu hồi', state: props.revokeState },
  ].filter((operation) => operation.state.state !== 'idle');

  async function submit(): Promise<void> {
    setFormMessage(null);
    try {
      const result = await props.onInvite(teacherSubject.trim());
      if (result.state === 'confirmed') {
        setTeacherSubject('');
        setFormMessage({ text: 'Đã gửi lời mời. Giáo viên cần chấp nhận để có hiệu lực.', tone: 'success' });
        return;
      }
      if (result.state === 'pending') {
        setFormMessage({ text: 'Đang gửi lời mời.', tone: 'info' });
        return;
      }
      if (result.state === 'reconciling') {
        setFormMessage({ text: 'Đang kiểm tra trạng thái. Chờ xác nhận trước khi gửi lại.', tone: 'info' });
        return;
      }
      if (result.state === 'unavailable') {
        setFormMessage({ text: 'Gửi lời mời hiện chưa khả dụng.', tone: 'warning' });
        return;
      }
      if (result.state === 'failed') {
        const text = result.retry === 'user-action-required'
          ? 'Chưa gửi được. Kiểm tra mã tài khoản rồi thử lại.'
          : result.retry === 'same-job-check-required'
            ? 'Chưa rõ kết quả. Kiểm tra trạng thái trước khi gửi lại.'
            : 'Lời mời chưa hoàn tất. Xem trạng thái quyền chia sẻ.';
        setFormMessage({ text, tone: 'warning' });
        return;
      }
      setFormMessage({ text: 'Chưa gửi được lời mời.', tone: 'warning' });
    } catch {
      setFormMessage({ text: 'Chưa xác nhận được lời mời. Kiểm tra trạng thái trước khi gửi lại.', tone: 'warning' });
    }
  }

  return (
    <ScreenFrame title="Chia sẻ hồ sơ" subtitle={props.profile?.display_name ?? 'Chọn hồ sơ của bé trước.'} onBack={props.onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']}>
      <View style={styles.introCard}>
        <View style={styles.introIcon}><Ionicons name="people-outline" size={21} color="#7435D5" accessible={false} /></View>
        <View style={styles.introCopy}>
          <Text style={styles.introTitle}>Chia sẻ có kiểm soát</Text>
          <Text style={styles.introDescription}>Chỉ chia sẻ với giáo viên bạn chọn.</Text>
        </View>
      </View>
      {!props.profile ? <View style={styles.stateCard}>
        <View style={styles.stateIcon}><Ionicons name="person-outline" size={22} color="#7435D5" accessible={false} /></View>
        <Text style={styles.stateTitle}>Chưa chọn hồ sơ của bé</Text>
        <Text style={styles.stateDescription}>Chọn hồ sơ bé để quản lý chia sẻ.</Text>
      </View> : !sharingUnavailable ? <Card variant="creative" style={styles.inviteCard}>
        <View style={styles.sectionHeading}>
          <View style={styles.sectionIcon}><Ionicons name="person-add-outline" size={20} color="#7435D5" accessible={false} /></View>
          <View style={styles.sectionCopy}>
            <Text accessibilityRole="header" style={styles.sectionTitle}>Mời giáo viên</Text>
            <Text style={styles.inviteDescription}>Nhập mã tài khoản để gửi lời mời.</Text>
          </View>
        </View>
        <Field
          label="Mã tài khoản giáo viên"
          value={teacherSubject}
          onChangeText={setTeacherSubject}
          autoCapitalize="none"
          autoCorrect={false}
        />
        {formMessage ? <Notice text={formMessage.text} tone={formMessage.tone} /> : null}
        <PrimaryButton
          label="Gửi lời mời"
          busy={props.loading || inviteBusy}
          disabled={!teacherSubject.trim() || props.loading || inviteBusy}
          onPress={() => void submit()}
        />
      </Card> : null}
      {props.profile ? <Card variant="creative" style={styles.statusCard}>
        <View style={styles.sectionHeading}>
          <View style={[styles.sectionIcon, styles.statusSectionIcon]}><Ionicons name="shield-checkmark-outline" size={20} color="#397454" accessible={false} /></View>
          <View style={styles.sectionCopy}>
            <Text accessibilityRole="header" style={styles.sectionTitle}>Quyền chia sẻ</Text>
          </View>
        </View>
        {shareStatusMessage ? <Notice
          variant="creative"
          text={shareStatusMessage}
          tone="warning"
        /> : !props.error && !props.grants.length ? <View style={styles.noGrants}>
          <Ionicons name="mail-open-outline" size={19} color="#826B94" accessible={false} />
          <Text style={styles.noGrantsText}>Chưa có quyền chia sẻ.</Text>
        </View> : null}
        {!sharingUnavailable
          ? props.grants.map((grant) => <ViewGrant key={grant.grant_id} grant={grant} loading={props.loading} onRevoke={props.onRevoke} />)
          : null}
        {!sharingUnavailable && operationStatuses.length > 0 ? <View style={styles.operationsRow}>
          {operationStatuses.map((operation) => <OperationStatus key={operation.label} icon={operation.icon} label={operation.label} state={operationStateLabel(operation.state)} />)}
        </View> : null}
      </Card> : null}
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
    ? 'Đã hết hạn; chờ cập nhật trạng thái.'
    : grant.expires_at
      ? `Có hiệu lực đến ${new Date(grant.expires_at).toLocaleDateString('vi-VN')}`
      : 'Không ghi ngày hết hạn.';
  return <Card variant="creative" style={styles.grantCard}>
    <View style={styles.grantHeading}>
      <View style={styles.teacherIcon}><Ionicons name="school-outline" size={18} color="#7435D5" accessible={false} /></View>
      <View style={styles.grantCopy}>
        <Text style={styles.grantTeacher} numberOfLines={2}>{grant.teacher_subject}</Text>
        <Text style={styles.grantCreated}>Tạo ngày {formatDate(grant.created_at)}</Text>
      </View>
      <View style={[styles.grantStatePill, grant.state === 'ACTIVE' ? styles.grantActive : grant.state === 'DECLINED' || grant.state === 'EXPIRED' || grant.state === 'REVOKED' ? styles.grantInactive : styles.grantPending]}>
        <Text style={styles.grantStateText}>{parentShareGrantStateLabel(grant.state)}</Text>
      </View>
    </View>
    <View style={styles.expiryRow}><Ionicons name="time-outline" size={15} color="#766783" accessible={false} /><Text style={styles.grantExpiry}>{expiryText}</Text></View>
    {canRevoke ? <TextButton
      label="Thu hồi quyền chia sẻ"
      disabled={loading}
      onPress={() => { void onRevoke(grant.grant_id); }}
    /> : null}
  </Card>;
}

function OperationStatus({ icon, label, state }: { icon: React.ComponentProps<typeof Ionicons>['name']; label: string; state: string }): React.JSX.Element {
  return <View style={styles.operationItem}>
    <View style={styles.operationIcon}><Ionicons name={icon} size={15} color="#6A4C83" accessible={false} /></View>
    <View style={styles.operationCopy}><Text style={styles.operationLabel}>{label}</Text><Text style={styles.operationValue}>{state}</Text></View>
  </View>;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('vi-VN');
}

function operationStateLabel(state: ParentOperationState<void>): string {
  if (state.state === 'confirmed') return 'Đã xác nhận';
  if (state.state === 'pending') return 'Đang gửi';
  if (state.state === 'reconciling') return 'Đang kiểm tra';
  if (state.state === 'unavailable') return 'Chưa khả dụng';
  if (state.state === 'failed') return 'Chưa hoàn tất';
  return 'Chưa gửi';
}

const styles = StyleSheet.create({
  introCard: { flexDirection: 'row', alignItems: 'center', gap: 11, padding: 13, borderRadius: 20, borderWidth: 1.2, borderColor: '#E5D7F2', backgroundColor: '#FFFEFF' },
  introIcon: { width: 42, height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  introCopy: { flex: 1, minWidth: 0, gap: 3 },
  introTitle: { color: '#281451', fontSize: 14, lineHeight: 19, fontWeight: '800' },
  introDescription: { color: '#70667C', fontSize: 11, lineHeight: 16, flexShrink: 1 },
  stateCard: { alignItems: 'center', gap: 10, padding: 21, borderRadius: 23, borderWidth: 1.2, borderColor: '#E5D7F2', backgroundColor: '#FFFEFF' },
  stateIcon: { width: 54, height: 54, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  stateTitle: { color: '#281451', fontSize: 17, lineHeight: 23, fontWeight: '800', textAlign: 'center' },
  stateDescription: { color: '#70667C', fontSize: 12, lineHeight: 18, textAlign: 'center' },
  inviteCard: { backgroundColor: '#FFFEFF', gap: 12, borderColor: '#E5D7F2', borderWidth: 1.3, borderRadius: 22 },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', gap: 10, minWidth: 0 },
  sectionIcon: { width: 40, height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  statusSectionIcon: { backgroundColor: '#EAF5EE' },
  sectionCopy: { flex: 1, minWidth: 0, gap: 2 },
  sectionTitle: { color: palette.creativeInk, fontSize: 15, lineHeight: 20, fontWeight: '800' },
  inviteDescription: { color: palette.muted, fontSize: 11, lineHeight: 16, minWidth: 0, flexShrink: 1 },
  statusCard: { backgroundColor: '#FFFEFF', gap: 12, minWidth: 0, borderColor: '#E5D7F2', borderWidth: 1.3, borderRadius: 22 },
  noGrants: { minHeight: 54, flexDirection: 'row', alignItems: 'center', gap: 9, padding: 12, borderRadius: 15, backgroundColor: '#F6F1FA' },
  noGrantsText: { flex: 1, color: '#70667C', fontSize: 12, lineHeight: 17 },
  operationsRow: { flexDirection: 'row', gap: 8 },
  operationItem: { flex: 1, minWidth: 0, minHeight: 58, flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 9, paddingVertical: 8, borderRadius: 15, backgroundColor: '#F6F1FA' },
  operationIcon: { width: 29, height: 29, borderRadius: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: '#EDE3F7' },
  operationCopy: { flex: 1, minWidth: 0, gap: 2 },
  operationLabel: { color: '#665579', fontSize: 10, lineHeight: 14, fontWeight: '700' },
  operationValue: { color: '#332342', fontSize: 11, lineHeight: 15, fontWeight: '800', flexShrink: 1 },
  grantCard: { backgroundColor: '#FCFAFF', gap: 10, minWidth: 0, borderColor: '#ECE2F5', borderWidth: 1, borderRadius: 18, padding: 11 },
  grantHeading: { flexDirection: 'row', alignItems: 'center', gap: 8, minWidth: 0 },
  teacherIcon: { width: 35, height: 35, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  grantCopy: { flex: 1, minWidth: 0, gap: 2 },
  grantTeacher: { color: '#332342', fontSize: 12, lineHeight: 17, fontWeight: '800' },
  grantCreated: { color: '#81758A', fontSize: 10, lineHeight: 14 },
  grantStatePill: { maxWidth: 98, minHeight: 25, paddingHorizontal: 8, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  grantActive: { backgroundColor: '#E5F3EA' },
  grantInactive: { backgroundColor: '#F1EDF3' },
  grantPending: { backgroundColor: '#FFF3D1' },
  grantStateText: { color: '#554466', fontSize: 9, lineHeight: 13, fontWeight: '800', textAlign: 'center' },
  expiryRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 6 },
  grantExpiry: { flex: 1, color: '#70667C', fontSize: 11, lineHeight: 16 },
});
