import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Platform, Pressable, Share, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import { createParentActionIdentity } from '../../application/ports/ParentPorts';
import type {
  ParentProfileViewV1,
  ParentShareDeliveryPageV1,
  ParentShareField,
  ParentShareGrantCreatedV1,
  ParentShareGrantV1,
} from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, TextButton, palette } from '../components/ui';

type Props = {
  profile: ParentProfileViewV1 | null;
  grants: ParentShareGrantV1[];
  nextCursor: string | null;
  loading: boolean;
  error: string;
  capability: ParentCapabilityState;
  onLoad: (profileId: string, cursor?: string | null) => Promise<unknown>;
  onCreate: (profileId: string, fields: ParentShareField[], actionIdentity: string) => Promise<ParentShareGrantCreatedV1>;
  onGetGrant: (grantId: string) => Promise<ParentShareGrantV1>;
  onRevoke: (grantId: string, revision: number, actionIdentity: string) => Promise<ParentShareGrantV1>;
  onListDeliveries: (grantId: string, cursor?: string | null) => Promise<ParentShareDeliveryPageV1>;
  onOpenConsentPolicy: () => void;
  onBack: () => void;
};

const fieldOptions: { value: ParentShareField; label: string; detail: string }[] = [
  { value: 'DISPLAY_NAME', label: 'Tên hiển thị', detail: 'Tên gọi trong hồ sơ' },
  { value: 'AGE_BAND', label: 'Nhóm tuổi', detail: 'Nhóm tuổi, không gồm số tháng tuổi' },
  { value: 'INTERESTS_SUMMARY', label: 'Sở thích', detail: 'Tóm tắt sở thích trong hồ sơ' },
];

export function ProfileShareScreen(props: Props): React.JSX.Element {
  const profileId = props.profile?.profile_id ?? '';
  const canShare = props.capability.state === 'available'
    && props.profile?.data_origin === 'SYNTHETIC_DEV';
  const [fields, setFields] = useState<ParentShareField[]>(['DISPLAY_NAME']);
  const [busy, setBusy] = useState(false);
  const [formMessage, setFormMessage] = useState('');
  const [invitationCode, setInvitationCode] = useState<string | null>(null);
  const [copyMessage, setCopyMessage] = useState('');
  const [confirmingGrantId, setConfirmingGrantId] = useState<string | null>(null);
  const [selectedGrant, setSelectedGrant] = useState<ParentShareGrantV1 | null>(null);
  const [detailBusy, setDetailBusy] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [deliveries, setDeliveries] = useState<ParentShareDeliveryPageV1 | null>(null);
  const [deliveryBusy, setDeliveryBusy] = useState(false);
  const createAction = useRef<{ signature: string; key: string } | null>(null);
  const revokeActions = useRef(new Map<string, string>());

  useEffect(() => {
    if (profileId && canShare) void props.onLoad(profileId, null);
  }, [profileId, canShare]);

  function toggleField(value: ParentShareField): void {
    setFields((current) => current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value]);
  }

  async function createGrant(): Promise<void> {
    if (!profileId || !fields.length || busy) return;
    const sortedFields = [...fields].sort();
    const signature = JSON.stringify([profileId, sortedFields]);
    if (!createAction.current || createAction.current.signature !== signature) {
      createAction.current = { signature, key: createParentActionIdentity() };
    }
    setBusy(true);
    setFormMessage('');
    setInvitationCode(null);
    try {
      const created = await props.onCreate(profileId, sortedFields, createAction.current.key);
      createAction.current = null;
      setInvitationCode(created.invitation_code);
      setCopyMessage('');
      setFormMessage(created.invitation_code
        ? ''
        : 'Mã chỉ hiển thị một lần. Nếu chưa lưu mã, hãy thu hồi lời mời và tạo lời mời mới.');
      void props.onLoad(profileId, null);
    } catch {
      setFormMessage('Chưa tạo được lời mời. Hãy kiểm tra trạng thái trước khi gửi lại.');
    } finally {
      setBusy(false);
    }
  }

  async function copyInvitationCode(): Promise<void> {
    if (!invitationCode) return;
    try {
      if (Platform.OS === 'web' && globalThis.navigator?.clipboard) {
        await globalThis.navigator.clipboard.writeText(invitationCode);
        setCopyMessage('Đã sao chép mã. Hãy gửi riêng cho giáo viên bạn chọn.');
        return;
      }
      await Share.share({ title: 'Mã chia sẻ hồ sơ', message: invitationCode });
      setCopyMessage('Mã đang hiển thị. Chọn Sao chép trong bảng chia sẻ để gửi riêng.');
    } catch {
      setCopyMessage('Mã đang hiển thị. Hãy chọn và sao chép mã để gửi riêng.');
    }
  }

  async function openGrant(grant: ParentShareGrantV1): Promise<void> {
    setDetailBusy(true);
    setDetailError('');
    setSelectedGrant(null);
    setDeliveries(null);
    try {
      const detail = await props.onGetGrant(grant.share_grant_id);
      setSelectedGrant(detail);
      const page = await props.onListDeliveries(grant.share_grant_id, null);
      setDeliveries(page);
    } catch {
      setDetailError('Thông tin chia sẻ hiện chưa khả dụng.');
    } finally {
      setDetailBusy(false);
    }
  }

  async function loadMoreDeliveries(): Promise<void> {
    if (!selectedGrant || !deliveries?.next_cursor || deliveryBusy) return;
    setDeliveryBusy(true);
    setDetailError('');
    try {
      const page = await props.onListDeliveries(selectedGrant.share_grant_id, deliveries.next_cursor);
      setDeliveries((current) => current ? {
        ...page,
        items: [...current.items, ...page.items],
      } : page);
    } catch {
      setDetailError('Chưa tải được nội dung đã nhận. Hãy thử lại sau.');
    } finally {
      setDeliveryBusy(false);
    }
  }

  async function revoke(grant: ParentShareGrantV1): Promise<void> {
    const actionSignature = `${grant.share_grant_id}:${grant.revision}`;
    const key = revokeActions.current.get(actionSignature) ?? createParentActionIdentity();
    revokeActions.current.set(actionSignature, key);
    setBusy(true);
    try {
      const revoked = await props.onRevoke(grant.share_grant_id, grant.revision, key);
      revokeActions.current.delete(actionSignature);
      setConfirmingGrantId(null);
      if (selectedGrant?.share_grant_id === revoked.share_grant_id) setSelectedGrant(revoked);
      if (profileId) void props.onLoad(profileId, null);
    } catch {
      setFormMessage('Chưa thu hồi được quyền chia sẻ. Trạng thái đã được kiểm tra lại.');
    } finally {
      setBusy(false);
    }
  }

  return <ScreenFrame
    title="Chia sẻ hồ sơ"
    subtitle={props.profile?.display_name ?? 'Chọn hồ sơ của bé trước.'}
    onBack={props.onBack}
    visualTone="creative"
    safeAreaEdges={['top', 'right', 'left']}
  >
    <Card variant="creative" style={styles.introCard}>
      <View style={styles.introHeading}>
        <View style={styles.introIcon}><Ionicons name="people-outline" size={20} color="#7435D5" accessible={false} /></View>
        <View style={styles.introCopy}>
          <Text accessibilityRole="header" style={styles.title}>Bạn chọn nội dung được chia sẻ</Text>
          <Text style={styles.body}>Chỉ gửi mã mời riêng cho giáo viên bạn chọn. Ứng dụng không tìm hoặc chọn giáo viên thay bạn.</Text>
        </View>
      </View>
      <TextButton label="Chính sách đồng ý" onPress={props.onOpenConsentPolicy} />
    </Card>

    {!props.profile ? <Notice variant="creative" text="Hãy chọn hồ sơ của bé trước khi chia sẻ." tone="info" /> : null}
    {props.profile && !canShare ? <Notice variant="creative" text="Chia sẻ hiện chỉ khả dụng với hồ sơ dữ liệu minh họa." tone="warning" /> : null}
    {props.capability.state === 'unavailable' ? <Notice variant="creative" text="Chia sẻ hồ sơ hiện chưa khả dụng. Hãy thử lại sau." tone="warning" /> : null}
    {props.error ? <Notice variant="creative" text={props.error} tone="warning" /> : null}

    {canShare ? <Card variant="creative" style={styles.card}>
      <Text accessibilityRole="header" style={styles.title}>Chọn thông tin được chia sẻ</Text>
      <Text style={styles.body}>Bạn có thể chọn một hoặc nhiều mục. Có thể thu hồi quyền bất cứ lúc nào.</Text>
      {fieldOptions.map((option) => {
        const selected = fields.includes(option.value);
        return <Pressable
          key={option.value}
          accessibilityRole="checkbox"
          accessibilityState={{ checked: selected }}
          onPress={() => toggleField(option.value)}
          style={[styles.fieldRow, selected && styles.fieldRowSelected]}
        >
          <View style={[styles.checkbox, selected && styles.checkboxSelected]}>
            {selected ? <Ionicons name="checkmark" size={14} color="#FFFFFF" accessible={false} /> : null}
          </View>
          <View style={styles.fieldCopy}>
            <Text style={styles.fieldTitle}>{option.label}</Text>
            <Text style={styles.fieldDetail}>{option.detail}</Text>
          </View>
        </Pressable>;
      })}
      {formMessage ? <Notice variant="creative" text={formMessage} tone="warning" /> : null}
      <PrimaryButton label={busy ? 'Đang tạo lời mời…' : 'Tạo mã mời'} busy={busy} disabled={!fields.length || busy} onPress={() => void createGrant()} />
      {invitationCode ? <View style={styles.codePanel}>
        <View style={styles.codeHeading}>
          <Ionicons name="key-outline" size={19} color="#397454" accessible={false} />
          <Text style={styles.codeTitle}>Mã mời · chỉ hiển thị lần này</Text>
        </View>
        <Text selectable accessibilityLabel="Mã mời dùng một lần" style={styles.code}>{invitationCode}</Text>
        <Text style={styles.body}>Trao mã riêng cho giáo viên bạn chọn. Mã không được lưu trong hồ sơ.</Text>
        <PrimaryButton label="Sao chép mã" onPress={() => void copyInvitationCode()} />
        {copyMessage ? <Text style={styles.successText}>{copyMessage}</Text> : null}
        <TextButton label="Ẩn mã" onPress={() => { setInvitationCode(null); setCopyMessage(''); }} />
      </View> : null}
    </Card> : null}

    {canShare ? <Card variant="creative" style={styles.card}>
      <View style={styles.listHeading}>
        <Text accessibilityRole="header" style={styles.title}>Quyền chia sẻ</Text>
        {props.loading ? <ActivityIndicator size="small" color="#7435D5" /> : null}
      </View>
      {!props.loading && props.grants.length === 0 ? <Text style={styles.body}>Chưa có lời mời chia sẻ nào.</Text> : null}
      {props.grants.map((grant) => <View key={grant.share_grant_id} style={styles.grantCard}>
        <View style={styles.grantTop}>
          <View style={styles.grantIcon}><Ionicons name="person-outline" size={17} color="#7435D5" accessible={false} /></View>
          <View style={styles.grantCopy}>
            <Text style={styles.fieldTitle}>{shareStateLabel(grant.state)}</Text>
            <Text style={styles.fieldDetail}>Tạo ngày {formatDate(grant.created_at)}</Text>
          </View>
          <View style={[styles.statePill, grant.state === 'ACTIVE' ? styles.stateActive : grant.state === 'INVITED' ? styles.stateInvited : styles.stateEnded]}>
            <Text style={styles.stateText}>{shareStateLabel(grant.state)}</Text>
          </View>
        </View>
        <Text style={styles.fieldDetail}>Được chia sẻ: {grant.granted_fields.map(shareFieldLabel).join(', ')}</Text>
        <TextButton label="Chi tiết và nội dung đã nhận" disabled={detailBusy} onPress={() => void openGrant(grant)} />
        {grant.state === 'INVITED' || grant.state === 'ACTIVE' ? confirmingGrantId === grant.share_grant_id ? <View style={styles.confirmBox}>
          <Text style={styles.body}>Thu hồi quyền này? Giáo viên sẽ không xem được nội dung mới.</Text>
          <View style={styles.confirmActions}>
            <TextButton label="Xác nhận thu hồi" disabled={busy} onPress={() => void revoke(grant)} />
            <TextButton label="Hủy" disabled={busy} onPress={() => setConfirmingGrantId(null)} />
          </View>
        </View> : <TextButton label="Thu hồi quyền chia sẻ" disabled={busy} onPress={() => setConfirmingGrantId(grant.share_grant_id)} /> : null}
      </View>)}
      {props.nextCursor ? <TextButton label="Xem thêm quyền chia sẻ" disabled={props.loading} onPress={() => void props.onLoad(profileId, props.nextCursor)} /> : null}
    </Card> : null}

    {detailBusy ? <View style={styles.loading}><ActivityIndicator color="#7435D5" /><Text style={styles.body}>Đang tải chi tiết…</Text></View> : null}
    {detailError ? <Notice variant="creative" text={detailError} tone="warning" /> : null}
    {selectedGrant ? <Card variant="creative" style={styles.card}>
      <Text accessibilityRole="header" style={styles.title}>Chi tiết quyền chia sẻ</Text>
      <Text style={styles.body}>Trạng thái: {shareStateLabel(selectedGrant.state)}</Text>
      <Text style={styles.body}>Ngày tạo: {formatDate(selectedGrant.created_at)}</Text>
      {selectedGrant.state === 'INVITED' ? <Text style={styles.body}>Lời mời có hiệu lực đến {formatDate(selectedGrant.invitation_expires_at)}</Text> : null}
      {selectedGrant.state === 'ACTIVE' && selectedGrant.expires_at ? <Text style={styles.body}>Quyền có hiệu lực đến {formatDate(selectedGrant.expires_at)}</Text> : null}
      {selectedGrant.revoked_at ? <Text style={styles.body}>Đã thu hồi ngày {formatDate(selectedGrant.revoked_at)}</Text> : null}
      <Text style={styles.body}>Thông tin được chia sẻ: {selectedGrant.granted_fields.map(shareFieldLabel).join(', ')}</Text>
    </Card> : null}
    {selectedGrant && deliveries ? <Card variant="creative" style={styles.card}>
      <Text accessibilityRole="header" style={styles.title}>Nội dung giáo viên đã nhận</Text>
      <Text style={styles.body}>Trạng thái: {deliveries.content_access === 'AVAILABLE' ? 'Đang khả dụng' : 'Đã kết thúc'}</Text>
      {deliveries.items.length === 0 ? <Text style={styles.body}>Chưa có nội dung đã nhận.</Text> : deliveries.items.map((item, index) => <View key={`${item.delivered_at}-${index}`} style={styles.deliveryItem}>
        <Ionicons name="book-outline" size={16} color="#7435D5" accessible={false} />
        <View style={styles.deliveryCopy}>
          <Text style={styles.fieldTitle}>{deliveries.content_access === 'AVAILABLE' && item.title ? item.title : 'Bài học đã gửi'}</Text>
          <Text style={styles.fieldDetail}>{formatDate(item.delivered_at)}</Text>
        </View>
      </View>)}
      {deliveries.next_cursor ? <TextButton label={deliveryBusy ? 'Đang tải…' : 'Xem thêm nội dung'} disabled={deliveryBusy} onPress={() => void loadMoreDeliveries()} /> : null}
    </Card> : null}
  </ScreenFrame>;
}

function shareStateLabel(state: ParentShareGrantV1['state']): string {
  if (state === 'INVITED') return 'Đang chờ chấp nhận';
  if (state === 'ACTIVE') return 'Đang chia sẻ';
  if (state === 'REVOKED') return 'Đã thu hồi';
  return 'Đã hết hạn';
}

function shareFieldLabel(field: ParentShareField): string {
  return fieldOptions.find((option) => option.value === field)?.label ?? 'Thông tin hồ sơ';
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('vi-VN');
}

const styles = StyleSheet.create({
  introCard: { gap: 11, backgroundColor: '#FFFEFF', borderColor: '#E5D7F2', borderWidth: 1.2, borderRadius: 22 },
  introHeading: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  introIcon: { width: 40, height: 40, borderRadius: 14, backgroundColor: '#F1E7FF', alignItems: 'center', justifyContent: 'center' },
  introCopy: { flex: 1, gap: 3 },
  card: { gap: 12, backgroundColor: '#FFFEFF', borderColor: '#E5D7F2', borderWidth: 1.2, borderRadius: 22 },
  title: { color: '#281451', fontSize: 15, lineHeight: 20, fontWeight: '800' },
  body: { color: '#70667C', fontSize: 12, lineHeight: 18, flexShrink: 1 },
  fieldRow: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 58, borderWidth: 1, borderColor: '#ECE2F5', borderRadius: 15, padding: 10 },
  fieldRowSelected: { borderColor: '#BCA2E2', backgroundColor: '#FBF8FF' },
  checkbox: { width: 22, height: 22, borderRadius: 7, borderWidth: 1.5, borderColor: '#B9A9C7', alignItems: 'center', justifyContent: 'center' },
  checkboxSelected: { borderColor: '#7435D5', backgroundColor: '#7435D5' },
  fieldCopy: { flex: 1, gap: 2 },
  fieldTitle: { color: '#332342', fontSize: 12, lineHeight: 17, fontWeight: '800' },
  fieldDetail: { color: '#81758A', fontSize: 10, lineHeight: 15 },
  codePanel: { gap: 9, padding: 12, borderRadius: 17, borderWidth: 1, borderColor: '#CFE5D6', backgroundColor: '#F2FAF4' },
  codeHeading: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  codeTitle: { color: '#315E42', fontSize: 12, lineHeight: 17, fontWeight: '800' },
  code: { color: '#1D3928', fontSize: 21, lineHeight: 29, fontWeight: '800', letterSpacing: 1.2, textAlign: 'center' },
  successText: { color: '#397454', fontSize: 11, lineHeight: 16 },
  listHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  grantCard: { gap: 9, padding: 11, borderRadius: 17, borderWidth: 1, borderColor: '#ECE2F5', backgroundColor: '#FCFAFF' },
  grantTop: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  grantIcon: { width: 34, height: 34, borderRadius: 12, backgroundColor: '#F1E7FF', alignItems: 'center', justifyContent: 'center' },
  grantCopy: { flex: 1, gap: 2 },
  statePill: { minHeight: 24, paddingHorizontal: 8, borderRadius: 13, justifyContent: 'center' },
  stateActive: { backgroundColor: '#E5F3EA' },
  stateInvited: { backgroundColor: '#FFF3D1' },
  stateEnded: { backgroundColor: '#F1EDF3' },
  stateText: { color: '#554466', fontSize: 9, lineHeight: 13, fontWeight: '800' },
  confirmBox: { gap: 7, padding: 10, borderRadius: 13, backgroundColor: '#FFF8E8' },
  confirmActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  loading: { flexDirection: 'row', alignItems: 'center', gap: 9, padding: 9 },
  deliveryItem: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 6 },
  deliveryCopy: { flex: 1, gap: 2 },
});
