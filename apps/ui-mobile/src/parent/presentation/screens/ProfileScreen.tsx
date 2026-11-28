import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentProfileDeletePendingV1, ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { isProfileDeletionPending, selectProfileById } from '../navigation/parentFlowV1';
import { canStartProfileLearning, isSyntheticProfileDataOrigin, parentProfileAgeEligibility } from '../navigation/workflowTypes';
import type { ParentConsentUiState } from '../navigation/workflowTypes';
import { Card, ConfirmButton, Notice, ScreenFrame, SecondaryButton } from '../components/ui';
import type { CreateParentContextEntryRequest, ParentContextEntryEnvelope, ParentContextEntryListView } from '../../domain/types';
import { ProfileContextEntriesSection } from './ProfileContextEntriesSection';

type Props = {
  profiles: ParentProfileViewV1[];
  pendingDeletions: ParentProfileDeletePendingV1[];
  selectedProfileId: string;
  activeRun: ParentStoryRunV1 | null;
  error: string;
  busy: string;
  pendingDeletionLoadingId: string;
  consentState: ParentConsentUiState;
  onSelect: (profile: ParentProfileViewV1) => void;
  onCreate: () => void;
  onEdit: (profile: ParentProfileViewV1) => void;
  onRequestDeletion: (profile: ParentProfileViewV1) => void;
  onRefreshPendingDeletion: (profileId: string) => void;
  onContinue: (profile: ParentProfileViewV1) => void;
  onOpenAccount?: () => void;
  onOpenSettings?: () => void;
  onOpenNotifications?: () => void;
  onOpenQuota?: () => void;
  onOpenHistory?: () => void;
  onOpenSharing?: () => void;
  onOpenConsentPolicy?: () => void;
  onOpenDeliveredLessons?: () => void;
  onOpenSupportNeeds?: () => void;
  newActionIdentity?: () => string;
  onListContextEntries?: (profileId: string, cursor?: string | null) => Promise<ParentContextEntryListView>;
  onCreateContextEntry?: (profileId: string, input: CreateParentContextEntryRequest, actionIdentity: string) => Promise<ParentContextEntryEnvelope>;
  onSignOut?: () => void;
  onResumeRun?: () => void;
  onBackHome?: () => void;
};

const familyAccent = {
  ink: '#35204B',
  purple: '#7435D5',
  lilac: '#F3EAFE',
  lilacStrong: '#E7D6FA',
  cream: '#FFFBF5',
  white: '#FFFFFF',
  muted: '#776A7D',
  line: '#E9DDF0',
  amber: '#B66A00',
  amberWash: '#FFF3CF',
  red: '#B84651',
  redWash: '#FFF0EF',
  mint: '#E8F5EE',
} as const;

const ignoreFamilyAction = (): void => undefined;

function FamilyHeaderDecoration(): React.JSX.Element {
  return (
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.familyHeaderBadge}>
      <Ionicons name="people-outline" size={23} color={familyAccent.purple} accessible={false} />
      <View style={styles.familyHeaderSparkle}>
        <Ionicons name="sparkles" size={9} color="#C17A00" accessible={false} />
      </View>
    </View>
  );
}

export function ProfileScreen({
  profiles,
  pendingDeletions,
  selectedProfileId,
  activeRun,
  error,
  busy,
  pendingDeletionLoadingId,
  consentState,
  onSelect,
  onCreate,
  onEdit,
  onRequestDeletion,
  onRefreshPendingDeletion,
  onContinue,
  onOpenAccount = ignoreFamilyAction,
  onOpenSettings = ignoreFamilyAction,
  onOpenNotifications = ignoreFamilyAction,
  onOpenQuota = ignoreFamilyAction,
  onOpenHistory = ignoreFamilyAction,
  onOpenSharing = ignoreFamilyAction,
  onOpenConsentPolicy = ignoreFamilyAction,
  onOpenDeliveredLessons = ignoreFamilyAction,
  onOpenSupportNeeds = ignoreFamilyAction,
  newActionIdentity = () => 'preview-action',
  onListContextEntries = async () => ({ context_entries: [], next_cursor: null, limit: 25 }),
  onCreateContextEntry = async () => ({ context_entry: {
    context_entry_id: 'preview-entry', entry_kind: 'OBSERVATION', short_text: '', source_kind: 'PARENT_ENTERED',
    approximate_date: null, created_at: '2026-11-24T00:00:00Z',
  } }),
  onSignOut = ignoreFamilyAction,
}: Props): React.JSX.Element {
  const selected = selectProfileById(profiles, selectedProfileId);
  const selectedAgeEligibility = selected ? parentProfileAgeEligibility(selected) : 'unavailable';
  const mayStartRun = Boolean(selected)
    && canStartProfileLearning(selectedAgeEligibility, consentState.status, selected!.data_origin)
    && !isProfileDeletionPending(selected!.profile_id, pendingDeletions);

  return (
    <ScreenFrame
      title="Không gian gia đình"
      subtitle="Hồ sơ và hoạt động của gia đình."
      visualTone="creative"
      brandAdornment={<FamilyHeaderDecoration />}
      safeAreaEdges={['top', 'right', 'left']}
    >
      <Card style={styles.profileListCard}>
        <View style={styles.sectionHeadingRow}>
          <View style={styles.sectionHeadingCopy}>
            <Text style={styles.sectionTitle}>Hồ sơ của bé</Text>
            <Text style={styles.sectionCaption}>
              {profiles.length === 0 ? 'Thêm hồ sơ để cá nhân hóa hành trình.' : `${profiles.length} hồ sơ trong gia đình`}
            </Text>
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Thêm bé"
            accessibilityState={{ disabled: Boolean(busy) }}
            disabled={Boolean(busy)}
            onPress={onCreate}
            activeOpacity={0.84}
            style={[styles.addProfileButton, Boolean(busy) && styles.disabledControl]}
          >
            <Ionicons name="add" size={20} color={familyAccent.white} accessible={false} />
            <Text style={styles.addProfileLabel}>Thêm bé</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.profileHelper}>
          <Ionicons name="information-circle-outline" size={16} color="#28618B" accessible={false} />
          <Text style={styles.profileHelperText}>Mỗi buổi học gắn với một hồ sơ trẻ.</Text>
        </View>

        {profiles.length === 0 && !error ? (
          <View style={styles.emptyProfiles}>
            <View style={styles.emptyIconWrap}>
              <Ionicons name="people-outline" size={25} color={familyAccent.purple} accessible={false} />
            </View>
            <View style={styles.emptyCopy}>
              <Text style={styles.emptyTitle}>Chưa có hồ sơ nào</Text>
              <Text style={styles.emptyDetail}>Tạo hồ sơ của bé để bắt đầu.</Text>
            </View>
          </View>
        ) : (
          <View style={styles.profileRows}>
            {profiles.map((profile, index) => {
              const ageEligibility = parentProfileAgeEligibility(profile);
              const years = Math.floor(profile.age_months / 12);
              const remainingMonths = profile.age_months % 12;
              const ageLabel = remainingMonths > 0 ? `${years} tuổi ${remainingMonths} tháng` : `${years} tuổi`;
              const ageBandRef = profile.age_band_ref?.trim() ?? '';
              const ageBandVersion = profile.age_band_version?.trim() ?? '';
              const hasAgeBandRef = ageBandRef.length > 0;
              const hasAgeBandVersion = ageBandVersion.length > 0;
              const hasIncompleteAgeBand = hasAgeBandRef !== hasAgeBandVersion;
              const versionLabel = hasAgeBandRef && hasAgeBandVersion
                ? `Nhóm ${ageBandRef}, phiên bản ${ageBandVersion}`
                : hasIncompleteAgeBand
                  ? 'Chưa xác nhận được nhóm tuổi và phiên bản của hồ sơ. Hãy kiểm tra lại trước khi tiếp tục.'
                  : ageEligibility === 'supported' ? 'Nhóm tuổi chưa khả dụng' : '';
              const eligibilityLabel = ageEligibility === 'legacy-read-only'
                ? 'Hồ sơ cũ, chỉ xem hoặc xóa'
                : ageEligibility === 'unavailable' && !hasIncompleteAgeBand ? 'Chưa thể xác nhận điều kiện tuổi' : '';
              const detail = [ageLabel, versionLabel, eligibilityLabel].filter(Boolean).join(' · ');
              return (
                <ProfileChoice
                  key={profile.profile_id}
                  profile={profile}
                  detail={detail}
                  selected={selectedProfileId === profile.profile_id}
                  tintIndex={index}
                  onPress={() => onSelect(profile)}
                />
              );
            })}
          </View>
        )}
      </Card>

      {pendingDeletions.length > 0 ? (
        <View style={styles.pendingCard}>
          <View style={styles.pendingHeading}>
            <View style={styles.pendingIcon}>
              <Ionicons name="time-outline" size={18} color={familyAccent.amber} accessible={false} />
            </View>
            <View style={styles.pendingCopy}>
              <Text style={styles.pendingTitle}>Yêu cầu xóa đang chờ</Text>
              <Text style={styles.pendingDetail}>Đang chờ máy chủ xác nhận.</Text>
            </View>
          </View>
          {pendingDeletions.map((pending) => (
            <View key={pending.profile_id} style={styles.pendingRow}>
              <SecondaryButton
                label={pendingDeletionLoadingId === pending.profile_id ? 'Đang kiểm tra…' : 'Kiểm tra trạng thái'}
                disabled={Boolean(pendingDeletionLoadingId) || Boolean(busy)}
                onPress={() => onRefreshPendingDeletion(pending.profile_id)}
              />
            </View>
          ))}
        </View>
      ) : null}

      {!activeRun && selected ? (
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Dùng hồ sơ này"
          accessibilityState={{ disabled: !mayStartRun }}
          disabled={!mayStartRun}
          onPress={() => onContinue(selected)}
          activeOpacity={0.86}
          style={[styles.continueButton, !mayStartRun && styles.continueButtonDisabled]}
        >
          <View style={styles.continueIcon}>
            <Ionicons name="color-wand-outline" size={19} color={familyAccent.purple} accessible={false} />
          </View>
          <View style={styles.continueCopy}>
            <Text style={[styles.continueLabel, !mayStartRun && styles.disabledText]}>Dùng hồ sơ này</Text>
            <Text style={[styles.continueHint, !mayStartRun && styles.disabledText]}>Tiếp tục hành trình sáng tạo</Text>
          </View>
          <Ionicons name="arrow-forward" size={19} color={mayStartRun ? familyAccent.purple : familyAccent.muted} accessible={false} />
        </TouchableOpacity>
      ) : null}

      {selected ? (
        <View style={styles.selectedActionsCard}>
          <ConsentStatus state={consentState} dataOrigin={selected.data_origin} />
          <View style={styles.actionDivider} />
          <View style={styles.profileActionRow}>
            <View style={styles.profileActionCell}>
              <SecondaryButton
                label="Chỉnh sửa hồ sơ"
                disabled={Boolean(busy) || selectedAgeEligibility !== 'supported'}
                onPress={() => onEdit(selected)}
              />
            </View>
            {!isProfileDeletionPending(selected.profile_id, pendingDeletions) ? (
              <View style={styles.profileActionCell}>
                <ConfirmButton
                  label="Yêu cầu xóa hồ sơ"
                  title="Gửi yêu cầu xóa hồ sơ này?"
                  message="Hồ sơ sẽ chuyển sang mục yêu cầu đang chờ."
                  confirmLabel="Gửi yêu cầu"
                  destructive
                  onConfirm={() => onRequestDeletion(selected)}
                />
              </View>
            ) : null}
          </View>
        </View>
      ) : null}

      {selected && !isProfileDeletionPending(selected.profile_id, pendingDeletions) ? <ProfileContextEntriesSection
        key={selected.profile_id}
        profileId={selected.profile_id}
        newActionIdentity={newActionIdentity}
        onList={onListContextEntries}
        onCreate={onCreateContextEntry}
      /> : null}

      {error ? <Notice text={error} tone="error" /> : null}

      <View style={styles.familyMenuCard}>
        <View style={styles.menuTitleRow}>
          <View style={styles.menuTitleCopy}>
            <Text style={styles.sectionTitle}>Cài đặt gia đình</Text>
          </View>
        </View>
        {!selected ? <Notice text="Chọn hồ sơ trẻ để xem bài đã dạy hoặc quản lý chia sẻ." tone="info" /> : null}

        <MenuGroup title="Tài khoản">
          <FamilyMenuRow label="Tài khoản và bảo mật" hint="Thông tin đăng nhập" icon="shield-checkmark-outline" onPress={onOpenAccount} />
        </MenuGroup>
        <MenuGroup title="Ứng dụng">
          <FamilyMenuRow label="Cài đặt" hint="Tùy chỉnh trải nghiệm" icon="settings-outline" onPress={onOpenSettings} />
          <FamilyMenuRow label="Thông báo" hint="Tin mới dành cho phụ huynh" icon="notifications-outline" onPress={onOpenNotifications} />
        </MenuGroup>
        <MenuGroup title="Học tập & chia sẻ">
          <FamilyMenuRow
            label="Nhu cầu hỗ trợ"
            hint="Thông tin do người lớn nhập"
            icon="heart-outline"
            disabled={!selected || isProfileDeletionPending(selected.profile_id, pendingDeletions)}
            onPress={onOpenSupportNeeds}
          />
          <FamilyMenuRow label="Lượt tạo video" icon="videocam-outline" onPress={onOpenQuota} />
          <FamilyMenuRow label="Lịch sử hoạt động" icon="time-outline" onPress={onOpenHistory} />
          <FamilyMenuRow label="Bài giáo viên đã dạy" icon="book-outline" disabled={!selected} onPress={onOpenDeliveredLessons} />
          <FamilyMenuRow label="Chia sẻ hồ sơ với giáo viên" icon="share-social-outline" disabled={!selected} onPress={onOpenSharing} />
          <FamilyMenuRow label="Chính sách đồng ý" hint="Xem chính sách do dịch vụ cung cấp" icon="document-text-outline" onPress={onOpenConsentPolicy} />
        </MenuGroup>
      </View>

      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="Đăng xuất"
        onPress={onSignOut}
        activeOpacity={0.84}
        style={styles.signOutButton}
      >
        <Ionicons name="log-out-outline" size={18} color={familyAccent.red} accessible={false} />
        <Text style={styles.signOutLabel}>Đăng xuất</Text>
      </TouchableOpacity>
    </ScreenFrame>
  );
}

function ProfileChoice({
  profile,
  detail,
  selected,
  tintIndex,
  onPress,
}: {
  profile: ParentProfileViewV1;
  detail: string;
  selected: boolean;
  tintIndex: number;
  onPress: () => void;
}): React.JSX.Element {
  const avatarStyle = tintIndex % 3 === 0
    ? styles.profileAvatarLilac
    : tintIndex % 3 === 1 ? styles.profileAvatarBlue : styles.profileAvatarPeach;

  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={`${profile.display_name}. ${detail}`}
      accessibilityState={{ selected }}
      onPress={onPress}
      activeOpacity={0.86}
      style={[styles.profileChoice, selected && styles.profileChoiceSelected]}
    >
      <View style={[styles.profileAvatar, avatarStyle]}>
        <Ionicons name="person-outline" size={22} color={familyAccent.purple} accessible={false} />
      </View>
      <View style={styles.profileChoiceCopy}>
        <Text style={styles.profileName} numberOfLines={1}>{profile.display_name}</Text>
        <Text style={styles.profileDetail}>{detail}</Text>
      </View>
      {selected ? (
        <View style={styles.selectedMark}>
          <Ionicons name="checkmark" size={14} color={familyAccent.white} accessible={false} />
        </View>
      ) : (
        <Ionicons name="chevron-forward" size={17} color={familyAccent.muted} accessible={false} />
      )}
    </TouchableOpacity>
  );
}

function MenuGroup({ title, children }: React.PropsWithChildren<{ title: string }>): React.JSX.Element {
  return (
    <View style={styles.menuGroup}>
      <Text style={styles.menuGroupLabel}>{title}</Text>
      <View style={styles.menuGroupContent}>{children}</View>
    </View>
  );
}

function FamilyMenuRow({
  label,
  hint,
  icon,
  disabled = false,
  onPress,
}: {
  label: string;
  hint?: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  disabled?: boolean;
  onPress: () => void;
}): React.JSX.Element {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={hint ? `${label}. ${hint}` : label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      activeOpacity={0.86}
      style={[styles.familyMenuRow, disabled && styles.disabledFamilyMenuRow]}
    >
      <View style={styles.menuRowIcon}>
        <Ionicons name={icon} size={18} color={disabled ? familyAccent.muted : familyAccent.purple} accessible={false} />
      </View>
      <View style={styles.menuRowCopy}>
        <Text style={styles.familyMenuLabel}>{label}</Text>
        {hint ? <Text style={styles.familyMenuHint}>{hint}</Text> : null}
      </View>
      <Ionicons name="chevron-forward" size={17} color={familyAccent.muted} accessible={false} />
    </TouchableOpacity>
  );
}

function ConsentStatus({ state, dataOrigin }: { state: ParentConsentUiState; dataOrigin?: string | null }): React.JSX.Element {
  const synthetic = isSyntheticProfileDataOrigin(dataOrigin);
  const message = synthetic
    ? 'Hồ sơ dữ liệu mô phỏng nên không cần đồng ý xử lý dữ liệu.'
    : state.status.state === 'unavailable'
    ? 'Chưa xác nhận được trạng thái đồng ý từ máy chủ nên chưa thể bắt đầu buổi học. Ghi nhận và thu hồi hiện chưa khả dụng.'
    : state.status.state === 'pending'
      ? 'Yêu cầu đồng ý đang chờ máy chủ xác nhận.'
      : state.status.state === 'revoked'
        ? 'Quyền xử lý đã bị thu hồi theo trạng thái máy chủ.'
        : state.status.state === 'confirmed'
          ? 'Máy chủ đã xác nhận đồng ý cho phiên bản chính sách được ghi nhận.'
          : 'Chưa có trạng thái đồng ý được máy chủ xác nhận.';
  const confirmed = state.status.state === 'confirmed' || synthetic;
  const unavailable = state.status.state === 'unavailable' && !synthetic;
  const statusLabel = synthetic
    ? 'Không cần'
    : state.status.state === 'confirmed'
    ? 'Đã xác nhận'
    : state.status.state === 'pending'
      ? 'Đang chờ'
      : state.status.state === 'revoked'
        ? 'Đã thu hồi'
        : state.status.state === 'unavailable'
          ? 'Chưa khả dụng'
          : 'Chưa ghi nhận';

  return (
    <View style={styles.consentContent}>
      <View style={styles.consentHeading}>
        <View style={[styles.consentIcon, confirmed ? styles.consentIconConfirmed : styles.consentIconPending]}>
          <Ionicons name={confirmed ? 'shield-checkmark-outline' : 'shield-outline'} size={18} color={confirmed ? '#3B7657' : familyAccent.amber} accessible={false} />
        </View>
        <View style={styles.consentCopy}>
          <Text style={styles.consentTitle}>Quyền xử lý dữ liệu</Text>
        </View>
        <View style={[
          styles.consentStatePill,
          confirmed ? styles.consentPillConfirmed : state.status.state === 'revoked' ? styles.consentPillRevoked : styles.consentPillPending,
        ]}>
          <Text style={[styles.consentStatePillText, confirmed && styles.consentStatusConfirmed]}>{statusLabel}</Text>
        </View>
      </View>
      <Text style={[styles.consentMessage, unavailable && styles.consentMessageWarning]}>{message}</Text>
      <View style={styles.consentOperationsRow}>
        <Text style={styles.consentOperations}>Ghi nhận: {operationStateLabel(state.capture)}</Text>
        <View style={styles.consentOperationsDivider} />
        <Text style={styles.consentOperations}>Thu hồi: {operationStateLabel(state.revoke)}</Text>
      </View>
    </View>
  );
}

function operationStateLabel(state: ParentConsentUiState['capture']): string {
  if (state.state === 'confirmed') return 'Đã xác nhận';
  if (state.state === 'pending') return 'Đang chờ';
  if (state.state === 'reconciling') return 'Đang kiểm tra';
  if (state.state === 'unavailable') return 'Chưa khả dụng';
  if (state.state === 'failed') return 'Chưa hoàn tất';
  return 'Chưa bắt đầu';
}

const styles = StyleSheet.create({
  familyHeaderBadge: { width: 46, height: 46, borderRadius: 17, borderWidth: 1, borderColor: '#E8D8F7', backgroundColor: '#F3EAFE', alignItems: 'center', justifyContent: 'center' },
  familyHeaderSparkle: { position: 'absolute', top: -4, right: -4, width: 17, height: 17, borderRadius: 9, borderWidth: 1.5, borderColor: '#FFF9ED', backgroundColor: '#FFF3CF', alignItems: 'center', justifyContent: 'center' },
  profileListCard: { backgroundColor: familyAccent.white, padding: 14, gap: 10, borderColor: familyAccent.line, borderWidth: 1.2, borderRadius: 22, shadowColor: familyAccent.ink, shadowOffset: { width: 0, height: 5 }, shadowOpacity: 0.07, shadowRadius: 13, elevation: 2 },
  sectionHeadingRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  sectionHeadingCopy: { flex: 1, minWidth: 0, gap: 2 },
  sectionCaption: { color: familyAccent.muted, fontSize: 11, lineHeight: 15, flexShrink: 1 },
  sectionTitle: { color: familyAccent.ink, fontSize: 16, lineHeight: 21, fontWeight: '800' },
  addProfileButton: { minHeight: 44, paddingHorizontal: 12, borderRadius: 15, backgroundColor: familyAccent.purple, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 3 },
  addProfileLabel: { color: familyAccent.white, fontSize: 12, lineHeight: 16, fontWeight: '800' },
  profileHelper: { minHeight: 28, paddingHorizontal: 2, flexDirection: 'row', alignItems: 'center', gap: 6 },
  profileHelperText: { color: '#28618B', fontSize: 10, lineHeight: 14, fontWeight: '600' },
  disabledControl: { opacity: 0.55 },
  emptyProfiles: { minHeight: 94, padding: 13, borderRadius: 18, borderWidth: 1, borderColor: familyAccent.line, backgroundColor: familyAccent.cream, flexDirection: 'row', alignItems: 'center', gap: 12 },
  emptyIconWrap: { width: 48, height: 48, borderRadius: 17, backgroundColor: familyAccent.lilac, alignItems: 'center', justifyContent: 'center' },
  emptyCopy: { flex: 1, minWidth: 0, gap: 3 },
  emptyTitle: { color: familyAccent.ink, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  emptyDetail: { color: familyAccent.muted, fontSize: 12, lineHeight: 17, flexShrink: 1 },
  profileRows: { gap: 8 },
  profileChoice: { minHeight: 72, padding: 9, borderWidth: 1, borderColor: familyAccent.line, borderRadius: 18, backgroundColor: familyAccent.cream, flexDirection: 'row', alignItems: 'center', gap: 10 },
  profileChoiceSelected: { backgroundColor: familyAccent.lilac, borderColor: familyAccent.lilacStrong, borderWidth: 1.6 },
  profileAvatar: { width: 48, height: 48, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  profileAvatarLilac: { backgroundColor: '#EDE1FF' },
  profileAvatarBlue: { backgroundColor: '#E2F1FF' },
  profileAvatarPeach: { backgroundColor: '#FFE9DD' },
  profileChoiceCopy: { flex: 1, minWidth: 0, gap: 3 },
  profileName: { color: familyAccent.ink, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  profileDetail: { color: familyAccent.muted, fontSize: 10, lineHeight: 14, flexShrink: 1 },
  selectedMark: { width: 23, height: 23, borderRadius: 12, backgroundColor: familyAccent.purple, alignItems: 'center', justifyContent: 'center' },
  pendingCard: { backgroundColor: familyAccent.amberWash, borderColor: '#F0D897', borderWidth: 1.2, borderRadius: 20, padding: 13, gap: 10, shadowColor: familyAccent.ink, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.05, shadowRadius: 9, elevation: 1 },
  pendingHeading: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  pendingIcon: { width: 36, height: 36, borderRadius: 13, backgroundColor: '#FFF8E8', alignItems: 'center', justifyContent: 'center' },
  pendingCopy: { flex: 1, minWidth: 0, gap: 2 },
  pendingTitle: { color: familyAccent.ink, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  pendingDetail: { color: familyAccent.muted, fontSize: 11, lineHeight: 15, flexShrink: 1 },
  pendingRow: { gap: 8 },
  continueButton: { minHeight: 64, padding: 10, borderRadius: 19, borderWidth: 1.3, borderColor: familyAccent.lilacStrong, backgroundColor: familyAccent.white, flexDirection: 'row', alignItems: 'center', gap: 10 },
  continueButtonDisabled: { backgroundColor: '#F1EDF3', borderColor: familyAccent.line },
  continueIcon: { width: 42, height: 42, borderRadius: 15, backgroundColor: familyAccent.lilac, alignItems: 'center', justifyContent: 'center' },
  continueCopy: { flex: 1, minWidth: 0, gap: 2 },
  continueLabel: { color: familyAccent.ink, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  continueHint: { color: familyAccent.muted, fontSize: 10, lineHeight: 14 },
  disabledText: { color: familyAccent.muted },
  selectedActionsCard: { backgroundColor: familyAccent.white, padding: 13, gap: 10, borderColor: familyAccent.line, borderWidth: 1.2, borderRadius: 22, shadowColor: familyAccent.ink, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.06, shadowRadius: 11, elevation: 1 },
  consentContent: { gap: 7 },
  consentHeading: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  consentIcon: { width: 36, height: 36, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  consentIconConfirmed: { backgroundColor: familyAccent.mint },
  consentIconPending: { backgroundColor: familyAccent.amberWash },
  consentCopy: { flex: 1, minWidth: 0, gap: 2 },
  consentTitle: { color: familyAccent.ink, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  consentStatusLabel: { color: familyAccent.amber, fontSize: 10, lineHeight: 14, fontWeight: '700' },
  consentStatusConfirmed: { color: '#3B7657' },
  consentStatePill: { minHeight: 25, paddingHorizontal: 9, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  consentPillConfirmed: { backgroundColor: familyAccent.mint },
  consentPillPending: { backgroundColor: familyAccent.amberWash },
  consentStatePillText: { color: familyAccent.amber, fontSize: 9, lineHeight: 13, fontWeight: '800' },
  consentMessage: { color: familyAccent.muted, fontSize: 10, lineHeight: 15, flexShrink: 1 },
  consentMessageWarning: { color: '#805316' },
  consentPillRevoked: { backgroundColor: familyAccent.redWash },
  consentOperationsRow: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', columnGap: 8, rowGap: 3 },
  consentOperations: { color: familyAccent.muted, fontSize: 9, lineHeight: 13, flexShrink: 1 },
  consentOperationsDivider: { width: 3, height: 3, borderRadius: 2, backgroundColor: familyAccent.lilacStrong },
  actionDivider: { height: 1, backgroundColor: familyAccent.line },
  profileActionRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  profileActionCell: { flex: 1, minWidth: 0 },
  familyMenuCard: { backgroundColor: familyAccent.white, padding: 14, gap: 10, borderColor: familyAccent.line, borderWidth: 1.2, borderRadius: 22, shadowColor: familyAccent.ink, shadowOffset: { width: 0, height: 5 }, shadowOpacity: 0.07, shadowRadius: 13, elevation: 2 },
  menuTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  menuTitleCopy: { flex: 1, minWidth: 0, gap: 1 },
  menuGroup: { gap: 3 },
  menuGroupLabel: { color: familyAccent.muted, fontSize: 10, lineHeight: 14, fontWeight: '700', paddingHorizontal: 2 },
  menuGroupContent: { borderRadius: 12, backgroundColor: 'transparent', overflow: 'hidden' },
  familyMenuRow: { minHeight: 48, minWidth: 0, paddingHorizontal: 4, paddingVertical: 4, flexDirection: 'row', alignItems: 'center', gap: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: familyAccent.line },
  disabledFamilyMenuRow: { opacity: 0.58 },
  menuRowIcon: { width: 28, height: 28, borderRadius: 9, backgroundColor: familyAccent.lilac, alignItems: 'center', justifyContent: 'center' },
  menuRowCopy: { flex: 1, minWidth: 0, gap: 1 },
  familyMenuLabel: { color: familyAccent.ink, fontSize: 12, lineHeight: 16, fontWeight: '700', flexShrink: 1 },
  familyMenuHint: { color: familyAccent.muted, fontSize: 9, lineHeight: 12, flexShrink: 1 },
  signOutButton: { minHeight: 48, borderRadius: 16, borderWidth: 1, borderColor: '#F0D5D5', backgroundColor: familyAccent.redWash, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  signOutLabel: { color: familyAccent.red, fontSize: 12, lineHeight: 17, fontWeight: '800' },
});
