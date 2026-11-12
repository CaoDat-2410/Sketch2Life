import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentField, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

type Invite = Readonly<{id: string; email: string; status: 'Bản nháp' | 'Đã thu hồi'}>;

export function ProfileSharingScreen({state, onNotice}: ParentFlowProps): React.JSX.Element {
  const [email, setEmail] = useState('');
  const [invites, setInvites] = useState<readonly Invite[]>([]);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const childName = state.activeRunChild?.name ?? state.childName;
  const validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

  const prepareInvite = (): void => {
    if (!validEmail) { setError('Nhập email hợp lệ để xem bản nháp.'); return; }
    setInvites((current) => [{id: `invite-preview-${Date.now()}`, email: email.trim(), status: 'Bản nháp'}, ...current]);
    setEmail('');
    setError('');
    onNotice('Đã tạo dòng lời mời mẫu trong phiên; chưa gửi email hoặc cấp quyền.');
  };

  return (
    <View style={styles.page}>
      <PreviewBanner title="Chia sẻ · chỉ là bản xem trước" body="Không gửi email, cấp quyền hoặc thay đổi hồ sơ thật." />
      <ScreenIntro eyebrow="AN TOÀN GIA ĐÌNH" title="Chia sẻ hồ sơ trẻ" description={`Hồ sơ đang xem: ${childName}.`} />
      <ParentCard tone="green" style={styles.hero}>
        <View style={styles.heroIcon}><ParentIcon name="share" size={22}/></View>
        <View style={styles.heroCopy}><Text style={styles.heroTitle}>Ba mẹ giữ quyền quyết định</Text><Text style={styles.heroBody}>Người được mời chỉ có quyền sau khi backend xác thực lời mời.</Text></View>
      </ParentCard>

      <ParentCard style={styles.form}>
        <View style={styles.formHeading}><Text style={styles.formTitle}>Mời người thân</Text><ParentPill label="CHƯA GỬI" tone="gray"/></View>
        <ParentField label="Email người nhận" value={email} onChangeText={(value) => { setEmail(value); setError(''); }} placeholder="nguoi-than@email.com" keyboardType="email-address" autoCapitalize="none" maxLength={120}/>
        <View style={styles.scopeRow}><View style={styles.scopeIcon}><ParentIcon name="lock" size={15}/></View><View style={styles.scopeCopy}><Text style={styles.scopeTitle}>Phạm vi xem</Text><Text style={styles.scopeBody}>Đang chờ quyết định sản phẩm</Text></View><ParentPill label="CHƯA CHỐT" tone="gold"/></View>
        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        <ParentButton title="Tạo lời mời mẫu" icon="send" disabled={!email.trim()} onPress={prepareInvite}/>
        <Text style={styles.formFootnote}>Chỉ tạo hàng preview trên màn hình; không phát sinh thư mời thật.</Text>
      </ParentCard>

      <View style={styles.sectionHeading}><View><Text style={styles.eyebrow}>TRẠNG THÁI</Text><Text style={styles.sectionTitle}>Lời mời trong phiên này</Text></View><ParentPill label={`${invites.length} mục`} tone="gray"/></View>
      {invites.length === 0 ? (
        <ParentCard style={styles.emptyCard}><View style={styles.emptyIcon}><ParentIcon name="send" size={20}/></View><Text style={styles.emptyTitle}>Chưa có lời mời mẫu</Text><Text style={styles.emptyBody}>Tạo một dòng preview ở trên để xem trạng thái thu hồi.</Text></ParentCard>
      ) : invites.map((invite) => (
        <ParentCard key={invite.id} style={styles.inviteCard}>
          <View style={styles.inviteIcon}><ParentIcon name={invite.status === 'Đã thu hồi' ? 'lock' : 'clock'} size={17}/></View>
          <View style={styles.inviteCopy}><Text style={styles.inviteEmail}>{invite.email}</Text><Text style={styles.inviteSub}>Lời mời mẫu · chưa gửi</Text></View>
          <ParentPill label={invite.status === 'Đã thu hồi' ? 'ĐÃ THU HỒI · PREVIEW' : 'BẢN NHÁP · PREVIEW'} tone={invite.status === 'Đã thu hồi' ? 'gray' : 'blue'}/>
          {invite.status !== 'Đã thu hồi' ? <Pressable accessibilityRole="button" onPress={() => setConfirmId(invite.id)} style={styles.revokeAction}><Text style={styles.revokeLabel}>Thu hồi mẫu</Text><ParentIcon name="arrow" size={13} color="#8B4E40"/></Pressable> : <Text style={styles.revokedNote}>Trạng thái đã thu hồi chỉ nằm trong phiên này.</Text>}
          {confirmId === invite.id ? <View style={styles.confirmBox}><Text style={styles.confirmTitle}>Đổi trạng thái dòng preview?</Text><Text style={styles.confirmBody}>Không ảnh hưởng lời mời hoặc quyền truy cập thật.</Text><View style={styles.confirmActions}><Pressable accessibilityRole="button" onPress={() => setConfirmId(null)}><Text style={styles.keepText}>Giữ lại</Text></Pressable><Pressable accessibilityRole="button" onPress={() => { setInvites((current) => current.map((item) => item.id === invite.id ? {...item, status: 'Đã thu hồi'} : item)); setConfirmId(null); }}><Text style={styles.revokeConfirm}>Thu hồi mẫu</Text></Pressable></View></View> : null}
        </ParentCard>
      ))}

      <InfoBanner title="Quyền, thời hạn và dữ liệu chia sẻ còn mở" body="Không tự đặt phạm vi trường dữ liệu hay ngày hết hạn. Thu hồi thật cần API và xác nhận trạng thái server." tone="warning"/>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 13},
  hero: {flexDirection: 'row', alignItems: 'center', gap: 11, padding: 14},
  heroIcon: {width: 43, height: 43, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: '#FFFFFFAA'},
  heroCopy: {flex: 1, gap: 4},
  heroTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  heroBody: {color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  form: {gap: 11, padding: 14},
  formHeading: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'},
  formTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  scopeRow: {flexDirection: 'row', alignItems: 'center', gap: 9, padding: 10, borderRadius: 12, backgroundColor: sketchColors.surfaceMuted},
  scopeIcon: {width: 30, height: 30, alignItems: 'center', justifyContent: 'center', borderRadius: 10, backgroundColor: sketchColors.white},
  scopeCopy: {flex: 1, gap: 3},
  scopeTitle: {color: sketchColors.ink, fontSize: 10, fontWeight: '800'},
  scopeBody: {color: sketchColors.muted, fontSize: 9},
  error: {color: '#9A4D3D', fontSize: 10, fontWeight: '700'},
  formFootnote: {color: sketchColors.muted, fontSize: 9, lineHeight: 14, textAlign: 'center'},
  sectionHeading: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8},
  eyebrow: {color: sketchColors.muted, fontSize: 8, fontWeight: '900', letterSpacing: 1},
  sectionTitle: {color: sketchColors.ink, fontSize: 14, fontWeight: '900', marginTop: 2},
  emptyCard: {alignItems: 'center', gap: 7, padding: 18},
  emptyIcon: {width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: sketchColors.greenSoft},
  emptyTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  emptyBody: {color: sketchColors.muted, fontSize: 10, textAlign: 'center'},
  inviteCard: {flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 9, padding: 12},
  inviteIcon: {width: 35, height: 35, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: sketchColors.blueSoft},
  inviteCopy: {flex: 1, minWidth: 140, gap: 3},
  inviteEmail: {color: sketchColors.ink, fontSize: 10, fontWeight: '900'},
  inviteSub: {color: sketchColors.muted, fontSize: 9},
  revokeAction: {width: '100%', minHeight: 41, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6, marginTop: 2, borderRadius: 11, backgroundColor: sketchColors.coralSoft},
  revokeLabel: {color: '#8B4E40', fontSize: 9, fontWeight: '900'},
  revokedNote: {width: '100%', color: sketchColors.muted, fontSize: 9, lineHeight: 14},
  confirmBox: {width: '100%', gap: 5, padding: 10, borderRadius: 10, backgroundColor: '#FFF7F4'},
  confirmTitle: {color: sketchColors.ink, fontSize: 10, fontWeight: '900'},
  confirmBody: {color: sketchColors.muted, fontSize: 9},
  confirmActions: {flexDirection: 'row', justifyContent: 'flex-end', gap: 16, marginTop: 4},
  keepText: {color: sketchColors.muted, fontSize: 9, fontWeight: '800'},
  revokeConfirm: {color: '#8B4E40', fontSize: 9, fontWeight: '900'},
});
