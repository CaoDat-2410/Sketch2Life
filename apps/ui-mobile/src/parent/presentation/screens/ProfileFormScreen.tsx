import React, { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Field, Notice, ScreenFrame, SecondaryButton } from '../components/ui';
import type { ParentProfileViewV1 } from '../../domain/types';
import { CHILD_AGE_RANGE_MESSAGE, isSupportedChildAge } from '../../domain/profileRules';
import type { ProfileFieldMessages } from '../navigation/parentFlowV1';
import { toParentProfileMutationInput } from '../navigation/workflowTypes';
import type { ChildGenderDraft } from '../navigation/workflowTypes';

type ProfileFormInput = { displayName: string; ageMonths: number; interests: string };

type Props = {
  mode: 'create' | 'edit';
  profile?: ParentProfileViewV1 | null;
  busy: boolean;
  error: string;
  fieldErrors: ProfileFieldMessages;
  onCreate: (input: ProfileFormInput) => Promise<ParentProfileViewV1>;
  onUpdate: (input: ProfileFormInput) => Promise<ParentProfileViewV1>;
  onBack: () => void;
};

const formColors = {
  ink: '#35204B',
  purple: '#7435D5',
  purpleDark: '#54228E',
  lilac: '#F3EAFE',
  lilacLine: '#E5D6F2',
  cream: '#FFFBF5',
  white: '#FFFFFF',
  muted: '#776A7D',
} as const;

const GENDER_OPTIONS: { value: ChildGenderDraft; label: string }[] = [
  { value: 'boy', label: 'Bé trai' },
  { value: 'girl', label: 'Bé gái' },
  { value: 'prefer_not_to_say', label: 'Không muốn chia sẻ' },
];

export function ProfileFormScreen({ mode, profile = null, busy, error, fieldErrors, onCreate, onUpdate, onBack }: Props): React.JSX.Element {
  const [displayName, setDisplayName] = useState(profile?.display_name ?? '');
  const [ageMonths, setAgeMonths] = useState(profile ? String(profile.age_months) : '');
  const [interests, setInterests] = useState(profile?.interests_summary ?? '');
  const [childGender, setChildGender] = useState<ChildGenderDraft>('');
  const isCreate = mode === 'create';
  const parsedAge = Number(ageMonths);
  const ageValid = isSupportedChildAge(parsedAge);
  const previewName = displayName.trim() || (isCreate ? 'Bé nhà mình' : profile?.display_name ?? 'Hồ sơ của bé');
  const previewAge = ageValid ? `${Math.floor(parsedAge / 12)} tuổi` : 'Từ 3 đến 10 tuổi';
  const submitDisabled = !displayName.trim() || !ageValid || busy;

  function submit(): void {
    if (submitDisabled) return;
    const input = toParentProfileMutationInput({ displayName, ageMonths: parsedAge, interests, childGender });
    if (isCreate) {
      void onCreate(input).catch(() => undefined);
    } else {
      void onUpdate(input).catch(() => undefined);
    }
  }

  return (
    <ScreenFrame
      title={isCreate ? 'Tạo hồ sơ của bé' : 'Chỉnh sửa hồ sơ'}
      subtitle={isCreate ? 'Lưu những điều bé yêu thích.' : 'Cập nhật thông tin hồ sơ của bé.'}
      onBack={onBack}
      backDisabled={busy}
      visualTone="creative"
    >
      <View style={styles.profilePreview}>
        <View style={styles.previewAvatar}>
          <Ionicons name="person-outline" size={27} color={formColors.purple} accessible={false} />
        </View>
        <View style={styles.previewCopy}>
          <Text style={styles.previewName} numberOfLines={1}>{previewName}</Text>
          <Text style={styles.previewDetail}>{previewAge} · Hồ sơ riêng của bé</Text>
        </View>
        <View style={styles.previewSparkle}>
          <Ionicons name="sparkles-outline" size={17} color={formColors.purple} accessible={false} />
        </View>
      </View>

      <View style={styles.fieldsCard}>
        <Text style={styles.formBadge}>HỒ SƠ</Text>
        <View style={styles.formHeading}>
          <View style={styles.formHeadingIcon}>
            <Ionicons name="create-outline" size={19} color={formColors.purple} accessible={false} />
          </View>
          <View style={styles.formHeadingCopy}>
            <Text style={styles.formTitle}>{isCreate ? 'Thông tin của bé' : 'Thông tin hồ sơ'}</Text>
            <Text style={styles.formSubtitle}>Các mục có dấu tùy chọn có thể để trống.</Text>
          </View>
        </View>

        <View style={styles.fieldGroup}>
          <Field
            label="Tên hiển thị"
            value={displayName}
            onChangeText={setDisplayName}
            placeholder="Nhập tên hiển thị"
            autoCapitalize="words"
            style={styles.profileInput}
            returnKeyType="next"
          />
          {fieldErrors.display_name ? <Notice text={fieldErrors.display_name} tone="error" /> : null}
        </View>

        <View style={styles.fieldGroup}>
          <Field
            label="Tuổi (tháng)"
            value={ageMonths}
            onChangeText={setAgeMonths}
            keyboardType="number-pad"
            placeholder="Ví dụ: 48"
            style={styles.profileInput}
          />
          <View style={styles.ageHintRow}>
            <Ionicons name="information-circle-outline" size={15} color={formColors.purple} accessible={false} />
            <Text style={styles.fieldHint}>Độ tuổi phù hợp: 36–120 tháng (3–10 tuổi).</Text>
          </View>
          {ageMonths.trim().length > 0 && !ageValid ? <Notice text={CHILD_AGE_RANGE_MESSAGE} tone="warning" /> : null}
          {fieldErrors.age_months ? <Notice text={fieldErrors.age_months} tone="error" /> : null}
        </View>

        <View style={styles.genderGroup}>
          <Text style={styles.fieldLabel}>Giới tính của trẻ (tùy chọn)</Text>
          <View style={styles.genderGrid}>
            {GENDER_OPTIONS.map((option) => (
              <GenderOption
                key={option.value}
                label={option.label}
                selected={childGender === option.value}
                onPress={() => setChildGender((current) => current === option.value ? '' : option.value)}
              />
            ))}
          </View>
        </View>

        <View style={styles.fieldGroup}>
          <Field
            label="Sở thích"
            value={interests}
            onChangeText={setInterests}
            placeholder="Ví dụ: vẽ, khủng long, vũ trụ"
            multiline
            style={[styles.profileInput, styles.interestsInput]}
          />
          {fieldErrors.interests_summary ? <Notice text={fieldErrors.interests_summary} tone="error" /> : null}
        </View>
      </View>

      <Notice
        text="Giới tính chỉ là bản nháp trên thiết bị, không dùng tạo câu chuyện."
        tone="info"
      />
      {error ? <Notice text={error} tone="error" /> : null}

      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel={isCreate ? 'Tạo hồ sơ' : 'Lưu thay đổi'}
        accessibilityState={{ disabled: submitDisabled, busy }}
        disabled={submitDisabled}
        onPress={submit}
        activeOpacity={0.88}
        style={styles.saveButtonOuter}
      >
        <LinearGradient
          colors={submitDisabled ? ['#DCD2E8', '#CFC2DF'] : [formColors.purple, formColors.purpleDark]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.saveButton}
        >
          {busy ? <ActivityIndicator color={formColors.white} /> : (
            <>
              <Ionicons name={isCreate ? 'person-add-outline' : 'checkmark-circle-outline'} size={19} color={formColors.white} accessible={false} />
              <Text style={styles.saveButtonLabel}>{isCreate ? 'Tạo hồ sơ' : 'Lưu thay đổi'}</Text>
              <Ionicons name="arrow-forward" size={17} color={formColors.white} accessible={false} />
            </>
          )}
        </LinearGradient>
      </TouchableOpacity>

      <SecondaryButton label="Quay lại danh sách" disabled={busy} onPress={onBack} />
    </ScreenFrame>
  );
}

function GenderOption({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }): React.JSX.Element {
  return (
    <TouchableOpacity
      accessibilityRole="radio"
      accessibilityLabel={label}
      accessibilityState={{ checked: selected, selected }}
      onPress={onPress}
      activeOpacity={0.86}
      style={[styles.genderOption, selected && styles.genderOptionSelected]}
    >
      <View style={[styles.genderRadio, selected && styles.genderRadioSelected]}>
        {selected ? <View style={styles.genderRadioDot} /> : null}
      </View>
      <Text style={styles.genderOptionLabel}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  profilePreview: { minHeight: 74, padding: 11, borderRadius: 20, borderWidth: 1, borderColor: formColors.lilacLine, backgroundColor: formColors.lilac, flexDirection: 'row', alignItems: 'center', gap: 10 },
  previewAvatar: { width: 49, height: 49, borderRadius: 18, backgroundColor: formColors.white, alignItems: 'center', justifyContent: 'center' },
  previewCopy: { flex: 1, minWidth: 0, gap: 3 },
  previewName: { color: formColors.ink, fontSize: 15, lineHeight: 20, fontWeight: '800' },
  previewDetail: { color: formColors.muted, fontSize: 10, lineHeight: 14, flexShrink: 1 },
  previewSparkle: { width: 32, height: 32, borderRadius: 12, backgroundColor: '#E9DBFA', alignItems: 'center', justifyContent: 'center' },
  fieldsCard: { padding: 14, gap: 13, borderWidth: 1.2, borderColor: formColors.lilacLine, borderRadius: 22, backgroundColor: formColors.white, shadowColor: '#49335C', shadowOffset: { width: 0, height: 5 }, shadowOpacity: 0.08, shadowRadius: 13, elevation: 2, minWidth: 0 },
  formBadge: { alignSelf: 'flex-start', minHeight: 22, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999, backgroundColor: formColors.lilac, color: formColors.purpleDark, fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.45, overflow: 'hidden' },
  formHeading: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 1 },
  formHeadingIcon: { width: 37, height: 37, borderRadius: 14, backgroundColor: formColors.lilac, alignItems: 'center', justifyContent: 'center' },
  formHeadingCopy: { flex: 1, minWidth: 0, gap: 2 },
  formTitle: { color: formColors.ink, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  formSubtitle: { color: formColors.muted, fontSize: 10, lineHeight: 14, flexShrink: 1 },
  fieldGroup: { gap: 5, minWidth: 0 },
  profileInput: { minHeight: 50, borderRadius: 15, backgroundColor: formColors.cream, color: formColors.ink, paddingHorizontal: 12, fontSize: 13, lineHeight: 18 },
  interestsInput: { minHeight: 78, paddingTop: 12, textAlignVertical: 'top' },
  ageHintRow: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 2 },
  fieldHint: { color: formColors.muted, fontSize: 10, lineHeight: 14, flex: 1, flexShrink: 1 },
  genderGroup: { gap: 6, minWidth: 0 },
  fieldLabel: { color: formColors.ink, fontSize: 12, lineHeight: 16, fontWeight: '700', flexShrink: 1 },
  genderGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  genderOption: { flexGrow: 1, flexBasis: '48%', minWidth: 0, minHeight: 46, paddingHorizontal: 9, paddingVertical: 7, borderWidth: 1.2, borderColor: formColors.lilacLine, borderRadius: 14, backgroundColor: formColors.cream, flexDirection: 'row', alignItems: 'center', gap: 7 },
  genderOptionSelected: { borderWidth: 1.6, borderColor: formColors.purple, backgroundColor: formColors.lilac },
  genderRadio: { width: 18, height: 18, borderRadius: 9, borderWidth: 1.4, borderColor: '#A99BB2', backgroundColor: formColors.white, alignItems: 'center', justifyContent: 'center' },
  genderRadioSelected: { borderColor: formColors.purple },
  genderRadioDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: formColors.purple },
  genderOptionLabel: { color: formColors.ink, fontSize: 11, lineHeight: 15, fontWeight: '700', flex: 1, minWidth: 0, flexShrink: 1 },
  saveButtonOuter: { minHeight: 54, borderRadius: 17, overflow: 'hidden', shadowColor: formColors.purpleDark, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.19, shadowRadius: 8, elevation: 3 },
  saveButton: { flex: 1, minHeight: 54, paddingHorizontal: 15, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  saveButtonLabel: { color: formColors.white, fontSize: 14, lineHeight: 19, fontWeight: '800' },
});
