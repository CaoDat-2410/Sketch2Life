import React, { useState } from 'react';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SecondaryButton } from '../components/ui';
import type { ParentProfileViewV1 } from '../../domain/types';
import { CHILD_AGE_RANGE_MESSAGE, isSupportedChildAge } from '../../domain/profileRules';
import type { ProfileFieldMessages } from '../navigation/parentFlowV1';

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

export function ProfileFormScreen({ mode, profile = null, busy, error, fieldErrors, onCreate, onUpdate, onBack }: Props): React.JSX.Element {
  const [displayName, setDisplayName] = useState(profile?.display_name ?? '');
  const [ageMonths, setAgeMonths] = useState(String(profile?.age_months ?? 72));
  const [interests, setInterests] = useState(profile?.interests_summary ?? '');
  const isCreate = mode === 'create';
  const parsedAge = Number(ageMonths);
  const ageValid = isSupportedChildAge(parsedAge);

  function submit(): void {
    const input = { displayName, ageMonths: parsedAge, interests };
    const action = isCreate ? onCreate : onUpdate;
    void action(input).catch(() => undefined);
  }

  return (
    <ScreenFrame
      title={isCreate ? 'Tạo hồ sơ' : 'Cập nhật hồ sơ'}
      subtitle={isCreate ? 'Lưu thông tin để chọn hồ sơ cho buổi học.' : 'Cập nhật tên gọi, tuổi và sở thích.'}
      onBack={onBack}
    >
      <Card>
        <Field
          label="Tên gọi trong ứng dụng"
          value={displayName}
          onChangeText={setDisplayName}
          placeholder="Ví dụ: Bé Mây"
          autoCapitalize="words"
        />
        {fieldErrors.display_name ? <Notice text={fieldErrors.display_name} tone="error" /> : null}
        <Field
          label="Tuổi (tháng, từ 36 đến 120)"
          value={ageMonths}
          onChangeText={setAgeMonths}
          keyboardType="number-pad"
        />
        {!ageValid ? <Notice text={CHILD_AGE_RANGE_MESSAGE} tone="warning" /> : null}
        {fieldErrors.age_months ? <Notice text={fieldErrors.age_months} tone="error" /> : null}
        <Field
          label="Sở thích (tùy chọn)"
          value={interests}
          onChangeText={setInterests}
          placeholder="Thiên nhiên, côn trùng…"
        />
        {fieldErrors.interests_summary ? <Notice text={fieldErrors.interests_summary} tone="error" /> : null}
      </Card>

      <Card>
        {error ? <Notice text={error} tone="error" /> : null}
        <PrimaryButton
          label={isCreate ? 'Lưu hồ sơ' : 'Lưu thay đổi'}
          busy={busy}
          disabled={!displayName.trim() || !ageValid}
          onPress={submit}
        />
        <SecondaryButton label="Quay lại hồ sơ" disabled={busy} onPress={onBack} />
      </Card>
    </ScreenFrame>
  );
}
