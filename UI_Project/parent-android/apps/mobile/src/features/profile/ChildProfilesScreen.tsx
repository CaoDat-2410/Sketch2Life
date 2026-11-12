import {useState} from 'react';
import {Pressable, ScrollView, StyleSheet, Text, View} from 'react-native';

import type {ParentChildProfile, ParentFlowProps, ParentProfileContext} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentField, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

const ages = ['3 tuổi', '4 tuổi', '5 tuổi', '6 tuổi'];
const emptyContext: ParentProfileContext = {interests: '', observations: '', achievements: '', outsideAppExperiences: ''};
const contextInputs: readonly Readonly<{key: keyof ParentProfileContext; label: string; placeholder: string}>[] = [
  {key: 'interests', label: 'Sở thích', placeholder: 'Điều con thích tìm hiểu'},
  {key: 'observations', label: 'Quan sát của gia đình', placeholder: 'Điều người lớn quan sát được'},
  {key: 'achievements', label: 'Điều con đã làm được', placeholder: 'Một kỹ năng hoặc cột mốc nhỏ'},
  {key: 'outsideAppExperiences', label: 'Trải nghiệm ngoài ứng dụng', placeholder: 'Hoạt động gia đình đã cùng làm'},
];

export function ChildProfilesScreen({state, dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  const [listMode, setListMode] = useState<'active' | 'archived' | 'pending'>('active');
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftName, setDraftName] = useState('');
  const [draftAge, setDraftAge] = useState('5 tuổi');
  const [draftContext, setDraftContext] = useState<ParentProfileContext>(emptyContext);
  const [contextExpanded, setContextExpanded] = useState(false);
  const [formError, setFormError] = useState('');
  const [archiveId, setArchiveId] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const locked = Boolean(state.activeRunChild);
  const visibleProfiles = state.childProfiles.filter((profile) => listMode === 'pending' ? profile.lifecycle === 'delete-pending' : profile.lifecycle === listMode);

  const openCreate = (): void => {
    setEditingId(null);
    setDraftName('');
    setDraftAge('5 tuổi');
    setDraftContext({...emptyContext});
    setContextExpanded(false);
    setFormError('');
    setFormOpen(true);
  };
  const openEdit = (profile: ParentChildProfile): void => {
    setEditingId(profile.id);
    setDraftName(profile.name);
    setDraftAge(profile.age);
    setDraftContext({...profile.context});
    setContextExpanded(Object.values(profile.context).some((value) => value.trim().length > 0));
    setFormError('');
    setFormOpen(true);
  };
  const saveProfile = (): void => {
    const name = draftName.trim();
    if (!name) { setFormError('Nhập tên gọi để tiếp tục.'); return; }
    const existing = editingId ? state.childProfiles.find((profile) => profile.id === editingId) : undefined;
    const id = existing?.id ?? `child-preview-${Date.now()}`;
    const profile: ParentChildProfile = {id, name, age: draftAge, color: existing?.color ?? '#E8EEF5', lifecycle: 'active', context: draftContext};
    dispatch({type: 'SAVE_CHILD_PROFILE', profile});
    if (!existing) dispatch({type: 'SELECT_CHILD', id, name, age: draftAge});
    onNotice(existing ? 'Đã cập nhật hồ sơ trong phiên preview; chưa lưu lên máy chủ.' : 'Đã thêm hồ sơ mẫu trong phiên preview; chưa tạo hồ sơ trên máy chủ.');
    setFormOpen(false);
  };
  const updateContext = (key: keyof ParentProfileContext, value: string): void => setDraftContext((current) => ({...current, [key]: value}));

  const requestProfileDeletion = (profile: ParentChildProfile): void => {
    dispatch({type: 'REQUEST_CHILD_PROFILE_DELETE', id: profile.id});
    setDeleteId(null);
    onNotice('Yêu cầu được ghi nhận trong preview; máy chủ chưa xóa dữ liệu.');
  };

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
      <PreviewBanner title="Hồ sơ mẫu · chỉ lưu trong phiên" body="Tạo, sửa, ẩn hoặc yêu cầu xóa để xem luồng. Chưa có thay đổi nào gửi lên backend." />
      {locked ? <><InfoBanner title="Run đang mở" body={`Run hiện tại gắn với ${state.activeRunChild?.name}. Có thể yêu cầu xóa hồ sơ; run liên quan sẽ chờ xử lý lifecycle.`} tone="warning"/><ParentButton title="Quay lại trạng thái run" variant="secondary" icon="arrow" onPress={() => onNavigate('generation')}/></> : null}
      <ScreenIntro eyebrow="GIA ĐÌNH" title="Hồ sơ của con" description="Chọn một hồ sơ cho câu chuyện đang bắt đầu." />

      <View style={styles.toolbar}>
        <Text style={styles.listHeading}>{listMode === 'active' ? 'Đang hoạt động' : listMode === 'archived' ? 'Hồ sơ đã ẩn' : 'Yêu cầu xóa'}</Text>
      </View>
      <View style={styles.filters} accessibilityRole="tablist">
        {([{key: 'active', label: 'Đang dùng'}, {key: 'archived', label: 'Đã ẩn'}, {key: 'pending', label: 'Đang xóa'}] as const).map((item) => <Pressable key={item.key} accessibilityRole="tab" accessibilityState={{selected: listMode === item.key}} onPress={() => setListMode(item.key)} style={[styles.filter, listMode === item.key ? styles.filterSelected : undefined]}><Text style={[styles.filterText, listMode === item.key ? styles.filterTextSelected : undefined]}>{item.label}</Text></Pressable>)}
      </View>

      <View style={styles.profileList}>
        {visibleProfiles.length === 0 ? <ParentCard style={styles.emptyCard}><ParentIcon name="child" size={24}/><Text style={styles.emptyTitle}>{listMode === 'active' ? 'Chưa có hồ sơ đang dùng' : listMode === 'archived' ? 'Chưa có hồ sơ đã ẩn' : 'Không có yêu cầu đang chờ'}</Text><Text style={styles.emptyBody}>{listMode === 'active' ? 'Thêm hồ sơ để bắt đầu câu chuyện.' : listMode === 'archived' ? 'Hồ sơ được ẩn có thể khôi phục.' : 'Trạng thái lifecycle sẽ xuất hiện ở đây.'}</Text></ParentCard> : visibleProfiles.map((profile) => {
          const selected = profile.id === (state.activeRunChild?.id ?? state.childId);
          const pendingArchive = archiveId === profile.id;
          const pendingDelete = deleteId === profile.id;
          const cannotArchiveLastSelected = selected && state.childProfiles.filter((item) => item.lifecycle === 'active' && item.id !== profile.id).length === 0;
          return (
            <ParentCard key={profile.id} style={[styles.profileCard, selected ? styles.selectedCard : undefined, profile.lifecycle !== 'active' ? styles.archivedCard : undefined]}>
              <View style={[styles.avatar, {backgroundColor: profile.color}]}><Text style={styles.avatarText}>{profile.name.replace(/^Bé\s*/, '').charAt(0).toLocaleUpperCase('vi')}</Text></View>
              <View style={styles.profileCopy}>
                <View style={styles.nameRow}><Text style={styles.profileName}>{profile.name}</Text>{selected ? <ParentPill label={state.activeRunChild ? 'Đã ghim' : 'Đang chọn'}/> : null}</View>
                <Text style={styles.profileAge}>{profile.age} · Hồ sơ minh họa</Text>
                {profile.lifecycle === 'archived' ? <ParentPill label="ĐÃ ẨN · PREVIEW" tone="gray"/> : null}
                {profile.lifecycle === 'delete-pending' ? <ParentPill label="DELETE_PENDING · PREVIEW" tone="gold"/> : null}
              </View>
              {profile.lifecycle === 'active' ? (
                <View style={styles.profileActions}>
                  {!selected ? <Pressable accessibilityRole="button" disabled={locked} onPress={() => { dispatch({type: 'SELECT_CHILD', id: profile.id, name: profile.name, age: profile.age}); onNotice('Lựa chọn chỉ có hiệu lực trong phiên preview.'); }} style={[styles.actionButton, locked ? styles.actionDisabled : undefined]}><Text style={styles.actionLabel}>Chọn</Text></Pressable> : null}
                  <Pressable accessibilityRole="button" disabled={locked} onPress={() => openEdit(profile)} style={[styles.actionButton, locked ? styles.actionDisabled : undefined]}><Text style={styles.actionLabel}>Sửa</Text></Pressable>
                  <Pressable accessibilityRole="button" accessibilityHint={cannotArchiveLastSelected ? 'Cần giữ lại ít nhất một hồ sơ đang hoạt động.' : undefined} disabled={locked || cannotArchiveLastSelected} onPress={() => setArchiveId(profile.id)} style={[styles.actionButton, styles.actionQuiet, locked || cannotArchiveLastSelected ? styles.actionDisabled : undefined]}><Text style={styles.actionLabelQuiet}>Ẩn</Text></Pressable>
                  <Pressable accessibilityRole="button" onPress={() => setDeleteId(profile.id)} style={[styles.actionButton, styles.actionDanger]}><Text style={styles.actionDangerText}>Yêu cầu xóa</Text></Pressable>
                </View>
              ) : profile.lifecycle === 'archived' ? <Pressable accessibilityRole="button" disabled={locked} onPress={() => dispatch({type: 'RESTORE_CHILD_PROFILE', id: profile.id})} style={[styles.actionButton, locked ? styles.actionDisabled : undefined]}><Text style={styles.actionLabel}>Khôi phục</Text></Pressable> : <View style={styles.pendingBox}><ParentIcon name="clock" size={14}/><Text style={styles.pendingText}>Hồ sơ bị khóa cho run mới đến khi máy chủ xác nhận xóa.</Text></View>}
              {pendingArchive ? (
                <View style={styles.confirmBox}>
                  <Text style={styles.confirmText}>Ẩn {profile.name} khỏi danh sách đang dùng?</Text>
                  <View style={styles.confirmActions}><Pressable accessibilityRole="button" onPress={() => setArchiveId(null)}><Text style={styles.actionLabelQuiet}>Giữ lại</Text></Pressable><Pressable accessibilityRole="button" onPress={() => { const next = state.childProfiles.find((item) => item.id !== profile.id && item.lifecycle === 'active'); dispatch({type: 'ARCHIVE_CHILD_PROFILE', id: profile.id}); if (state.childId === profile.id && next) dispatch({type: 'SELECT_CHILD', id: next.id, name: next.name, age: next.age}); setArchiveId(null); onNotice('Đã ẩn trong phiên preview; dữ liệu chưa bị xóa.'); }}><Text style={styles.archiveConfirm}>Ẩn hồ sơ</Text></Pressable></View>
                </View>
              ) : null}
              {pendingDelete ? <View style={styles.confirmBox}><Text style={styles.confirmText}>Yêu cầu xóa {profile.name}? Run liên quan có thể cần hủy qua lifecycle. Nội dung chưa bị xóa khi yêu cầu còn chờ.</Text><View style={styles.confirmActions}><Pressable accessibilityRole="button" onPress={() => setDeleteId(null)}><Text style={styles.actionLabelQuiet}>Quay lại</Text></Pressable><Pressable accessibilityRole="button" onPress={() => requestProfileDeletion(profile)}><Text style={styles.archiveConfirm}>Xác nhận yêu cầu</Text></Pressable></View></View> : null}
            </ParentCard>
          );
        })}
      </View>

      {formOpen ? (
        <ParentCard style={styles.formCard}>
          <View style={styles.formHeading}><View><Text style={styles.eyebrow}>{editingId ? 'CHỈNH SỬA' : 'HỒ SƠ MỚI'}</Text><Text style={styles.formTitle}>{editingId ? 'Cập nhật hồ sơ' : 'Thêm hồ sơ trẻ'}</Text></View><Pressable accessibilityRole="button" accessibilityLabel="Đóng biểu mẫu" onPress={() => setFormOpen(false)} style={styles.closeButton}><ParentIcon name="close" size={17}/></Pressable></View>
          <ParentField label="Tên gọi của con" value={draftName} onChangeText={setDraftName} placeholder="Ví dụ: Bé Mây" maxLength={40} returnKeyType="done"/>
          <Text style={styles.fieldTitle}>Nhóm tuổi</Text>
          <View style={styles.ageOptions}>{ages.map((age) => <Pressable key={age} accessibilityRole="radio" accessibilityState={{selected: draftAge === age}} onPress={() => setDraftAge(age)} style={[styles.ageOption, draftAge === age ? styles.ageOptionSelected : undefined]}><Text style={[styles.ageText, draftAge === age ? styles.ageTextSelected : undefined]}>{age}</Text></Pressable>)}</View>
          <Pressable accessibilityRole="button" accessibilityState={{expanded: contextExpanded}} onPress={() => setContextExpanded((value) => !value)} style={styles.contextToggle}><Text style={styles.contextToggleText}>{contextExpanded ? 'Ẩn thông tin bổ sung' : 'Thêm thông tin bổ sung · tùy chọn'}</Text><ParentIcon name={contextExpanded ? 'close' : 'arrow'} size={14}/></Pressable>
          {contextExpanded ? <View style={styles.contextFields}><Text style={styles.contextHint}>Chỉ ghi điều người lớn quan sát được. Không nhập chẩn đoán hoặc thông tin nhạy cảm.</Text>{contextInputs.map((field) => <ParentField key={field.key} label={field.label} value={draftContext[field.key]} onChangeText={(value) => updateContext(field.key, value)} placeholder={field.placeholder} multiline numberOfLines={2} maxLength={240}/>)}</View> : null}
          {formError ? <Text accessibilityRole="alert" style={styles.formError}>{formError}</Text> : null}
          <InfoBanner title="Hồ sơ chứa dữ liệu trẻ" body="Bản thật cần xác thực người giám hộ và quyền truy cập trước khi lưu." tone="warning"/>
          <View style={styles.formActions}><ParentButton title="Hủy" variant="quiet" onPress={() => setFormOpen(false)}/><ParentButton title="Lưu bản xem trước" icon="check" onPress={saveProfile}/></View>
        </ParentCard>
      ) : (
        <ParentButton title="Thêm hồ sơ trẻ" icon="plus" variant="secondary" disabled={locked || listMode !== 'active'} onPress={openCreate}/>
      )}

      <ParentCard tone="muted" style={styles.privacyCard}>
        <View style={styles.privacyIcon}><ParentIcon name="lock" size={20}/></View>
        <View style={styles.privacyCopy}><Text style={styles.privacyTitle}>Riêng tư theo từng hồ sơ</Text><Text style={styles.privacyBody}>Một run gắn với một trẻ. Trải nghiệm ngoài ứng dụng được giữ riêng với lịch sử run.</Text></View>
      </ParentCard>
      <ParentButton title="Quản lý chia sẻ hồ sơ" variant="quiet" icon="share" onPress={() => onNavigate('sharing')}/>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {padding: sketchSpace.lg, paddingBottom: 28, gap: 14},
  toolbar: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8},
  listHeading: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  filters: {flexDirection: 'row', gap: 6, padding: 4, borderRadius: 13, backgroundColor: sketchColors.surfaceMuted},
  filter: {flex: 1, minHeight: 42, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 6, borderRadius: 10},
  filterSelected: {backgroundColor: sketchColors.white},
  filterText: {color: sketchColors.muted, fontSize: 9, fontWeight: '800'},
  filterTextSelected: {color: sketchColors.greenDark},
  textAction: {minHeight: 42, flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 4},
  textActionLabel: {color: sketchColors.greenDark, fontSize: 10, fontWeight: '800'},
  profileList: {gap: 10},
  profileCard: {flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 10, padding: 13},
  selectedCard: {borderColor: sketchColors.green, borderWidth: 1.5},
  archivedCard: {opacity: 0.8},
  avatar: {width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 17},
  avatarText: {color: sketchColors.ink, fontSize: 20, fontWeight: '900'},
  profileCopy: {flex: 1, minWidth: 112, gap: 4},
  nameRow: {flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 6},
  profileName: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  profileAge: {color: sketchColors.muted, fontSize: 10},
  profileActions: {width: '100%', flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'flex-end', gap: 7, paddingTop: 8, borderTopWidth: 1, borderColor: sketchColors.line},
  actionButton: {minWidth: 61, minHeight: 40, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 11, borderRadius: 12, backgroundColor: sketchColors.greenSoft},
  actionQuiet: {backgroundColor: sketchColors.surfaceMuted},
  actionDisabled: {opacity: 0.42},
  actionLabel: {color: sketchColors.greenDark, fontSize: 10, fontWeight: '900'},
  actionLabelQuiet: {color: sketchColors.muted, fontSize: 10, fontWeight: '800'},
  actionDanger: {backgroundColor: sketchColors.coralSoft},
  actionDangerText: {color: '#8B4E40', fontSize: 9, fontWeight: '900'},
  confirmBox: {width: '100%', gap: 8, marginTop: 4, padding: 11, borderRadius: 12, backgroundColor: sketchColors.goldSoft},
  confirmText: {color: sketchColors.ink, fontSize: 10, lineHeight: 15, fontWeight: '700'},
  confirmActions: {flexDirection: 'row', justifyContent: 'flex-end', gap: 18},
  archiveConfirm: {color: '#8B4E40', fontSize: 10, fontWeight: '900'},
  pendingBox: {width: '100%', flexDirection: 'row', alignItems: 'flex-start', gap: 7, padding: 10, borderRadius: 12, backgroundColor: sketchColors.goldSoft},
  pendingText: {flex: 1, color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  emptyCard: {alignItems: 'center', gap: 7, padding: 19},
  emptyTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  emptyBody: {color: sketchColors.muted, fontSize: 10, textAlign: 'center'},
  formCard: {gap: 12, padding: 14},
  formHeading: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'},
  eyebrow: {color: sketchColors.muted, fontSize: 8, fontWeight: '900', letterSpacing: 1},
  formTitle: {color: sketchColors.ink, fontSize: 14, fontWeight: '900', marginTop: 3},
  closeButton: {width: 40, height: 40, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: sketchColors.surfaceMuted},
  fieldTitle: {color: sketchColors.inkSoft, fontSize: 10, fontWeight: '800'},
  ageOptions: {flexDirection: 'row', flexWrap: 'wrap', gap: 7},
  ageOption: {minWidth: 56, minHeight: 42, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 12, backgroundColor: sketchColors.white},
  ageOptionSelected: {borderColor: sketchColors.green, backgroundColor: sketchColors.greenSoft},
  ageText: {color: sketchColors.muted, fontSize: 10, fontWeight: '700'},
  ageTextSelected: {color: sketchColors.greenDark, fontWeight: '900'},
  contextToggle: {minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 11, borderRadius: 12, backgroundColor: sketchColors.surfaceMuted},
  contextToggleText: {color: sketchColors.greenDark, fontSize: 10, fontWeight: '800'},
  contextFields: {gap: 9, padding: 10, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 13, backgroundColor: sketchColors.surface},
  contextHint: {color: sketchColors.muted, fontSize: 9, lineHeight: 14},
  formError: {color: '#9A4D3D', fontSize: 10, fontWeight: '700'},
  formActions: {flexDirection: 'row', gap: 8},
  privacyCard: {flexDirection: 'row', gap: 11, alignItems: 'flex-start'},
  privacyIcon: {width: 38, height: 38, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: sketchColors.greenSoft},
  privacyCopy: {flex: 1, gap: 4},
  privacyTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  privacyBody: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
});
