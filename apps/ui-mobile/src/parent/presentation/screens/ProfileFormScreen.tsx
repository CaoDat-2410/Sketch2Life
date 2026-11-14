import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SecondaryButton, palette } from '../components/ui';
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

  function submit(): void {
    const input = toParentProfileMutationInput({ displayName, ageMonths: parsedAge, interests, childGender });
    const action = isCreate ? onCreate : onUpdate;
    void action(input).catch(() => undefined);
  }

  return (
    <ScreenFrame
      title="Tạo / chỉnh sửa hồ sơ"
      subtitle="Dùng cùng biểu mẫu khi thêm hoặc cập nhật hồ sơ."
      onBack={onBack}
      backDisabled={busy}
    >
      <Card style={styles.fieldsCard}>
        <Text style={styles.formBadge}>HỒ SƠ</Text>
        <Field
          label="Tên gọi trong ứng dụng"
          value={displayName}
          onChangeText={setDisplayName}
          placeholder="Nhập tên hiển thị"
          autoCapitalize="words"
        />
        {fieldErrors.display_name ? <Notice text={fieldErrors.display_name} tone="error" /> : null}
        <Field
          label="Tuổi (tháng)"
          value={ageMonths}
          onChangeText={setAgeMonths}
          keyboardType="number-pad"
        />
        <Text style={styles.fieldHint}>Hãy nhập tuổi được hệ thống hỗ trợ.</Text>
        {ageMonths.trim().length > 0 && !ageValid ? <Notice text={CHILD_AGE_RANGE_MESSAGE} tone="warning" /> : null}
        {fieldErrors.age_months ? <Notice text={fieldErrors.age_months} tone="error" /> : null}

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
        <Field
          label="Sở thích (tùy chọn)"
          value={interests}
          onChangeText={setInterests}
        />
        {fieldErrors.interests_summary ? <Notice text={fieldErrors.interests_summary} tone="error" /> : null}
      </Card>

      <Notice
        text="Lựa chọn giới tính chỉ là bản nháp trên thiết bị; chưa được gửi, lưu hoặc dùng để tạo câu chuyện."
        tone="info"
      />
      {error ? <Notice text={error} tone="error" /> : null}
      <PrimaryButton
        label="Lưu hồ sơ"
        busy={busy}
        disabled={!displayName.trim() || !ageValid}
        onPress={submit}
      />
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
  fieldsCard: { backgroundColor: palette.white, gap: 10, minWidth: 0 },
  fieldLabel: { color: palette.ink, fontSize: 12, lineHeight: 16, fontWeight: '700', flexShrink: 1 },
  fieldHint: { color: palette.muted, fontSize: 11, lineHeight: 15, flexShrink: 1 },
  genderGroup: { gap: 6, minWidth: 0 },
  formBadge: { alignSelf: 'flex-start', minHeight: 24, color: palette.ink, fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 0.5, paddingHorizontal: 7, paddingVertical: 3, borderWidth: 1, borderColor: palette.outline, borderRadius: 999, backgroundColor: palette.lilac, flexShrink: 1 },
  genderGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  genderOption: { flexGrow: 1, flexBasis: '48%', minWidth: 0, minHeight: 44, paddingHorizontal: 8, paddingVertical: 6, borderWidth: 1.3, borderColor: palette.outline, borderRadius: 11, backgroundColor: palette.white, flexDirection: 'row', alignItems: 'center', gap: 7 },
  genderOptionSelected: { borderWidth: 2, backgroundColor: palette.mint },
  genderRadio: { width: 19, height: 19, borderRadius: 10, borderWidth: 1.3, borderColor: palette.outline, backgroundColor: palette.white, alignItems: 'center', justifyContent: 'center' },
  genderRadioSelected: { borderWidth: 2 },
  genderRadioDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: palette.action },
  genderOptionLabel: { color: palette.ink, fontSize: 12, lineHeight: 16, fontWeight: '700', flex: 1, minWidth: 0, flexShrink: 1 },
});
