import React, { useState } from 'react';
import { ScrollView, Text, TouchableOpacity, View } from 'react-native';
import type { ConsentPolicy, ParentProfile } from '../../domain/types';
import { CHILD_AGE_RANGE_MESSAGE, isSupportedChildAge } from '../../domain/profileRules';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SectionTitle, SecondaryButton, palette } from '../components/ui';

type Props = {
  mode: 'create' | 'edit';
  profile?: ParentProfile | null;
  policy: ConsentPolicy | null;
  busy: boolean;
  error: string;
  onCreate: (input: { displayName: string; ageMonths: number; interests: string }) => Promise<ParentProfile>;
  onUpdate: (input: { ageMonths: number; displayName: string; interests: string }) => Promise<ParentProfile>;
  onBack: () => void;
};

export function ProfileFormScreen({ mode, profile = null, policy, busy, error, onCreate, onUpdate, onBack }: Props): React.JSX.Element {
  const [displayName, setDisplayName] = useState(profile?.current_revision.display_name ?? '');
  const [ageMonths, setAgeMonths] = useState(String(profile?.current_revision.age_months ?? 72));
  const [interests, setInterests] = useState(profile?.current_revision.interests_summary ?? '');
  const [accepted, setAccepted] = useState(false);
  const isCreate = mode === 'create';
  const parsedAge = Number(ageMonths);
  const ageValid = isSupportedChildAge(parsedAge);

  return (
    <ScreenFrame
      title={isCreate ? 'Tạo hồ sơ' : 'Cập nhật hồ sơ'}
      subtitle={isCreate ? 'Thông tin giúp cá nhân hóa từng buổi cùng con.' : 'Lưu thay đổi thành một phiên bản hồ sơ mới.'}
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
        {!ageValid ? <Notice text={CHILD_AGE_RANGE_MESSAGE} tone="warning" /> : null}
        <Field
          label="Tuổi (tháng, từ 36 đến 120)"
          value={ageMonths}
          onChangeText={setAgeMonths}
          keyboardType="number-pad"
        />
        <Field
          label="Sở thích (tùy chọn)"
          value={interests}
          onChangeText={setInterests}
          placeholder="Thiên nhiên, côn trùng…"
        />
      </Card>

      <Card>
        {isCreate ? <>
        <SectionTitle>Quyền xử lý dữ liệu</SectionTitle>
        <Text style={{ color: palette.muted, fontSize: 13 }}>Phiên bản {policy?.policy_version ?? 'đang tải'}</Text>
        <ScrollView
          nestedScrollEnabled
          style={{ maxHeight: 190, borderColor: palette.border, borderWidth: 1, borderRadius: 12, padding: 12 }}
        >
          <Text style={{ color: palette.ink, fontSize: 13, lineHeight: 19 }}>
            {policy?.consent_text ?? 'Đang tải nội dung quyền xử lý…'}
          </Text>
        </ScrollView>
        <TouchableOpacity
          accessibilityRole="checkbox"
          accessibilityState={{ checked: accepted }}
          onPress={() => setAccepted((value) => !value)}
          style={{ flexDirection: 'row', gap: 10, alignItems: 'center', paddingVertical: 4 }}
        >
          <View
            style={{
              width: 22,
              height: 22,
              borderRadius: 6,
              borderWidth: 1,
              borderColor: accepted ? palette.blue : '#A8B5C5',
              backgroundColor: accepted ? palette.blue : palette.white,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {accepted ? <Text style={{ color: palette.white, fontWeight: '900' }}>✓</Text> : null}
          </View>
          <Text style={{ color: palette.ink, flex: 1, fontSize: 13, lineHeight: 18 }}>
            Tôi là người lớn có trách nhiệm và đồng ý theo nội dung trên.
          </Text>
        </TouchableOpacity>
        </> : <Notice text={`Phiên bản hiện tại: ${profile?.current_revision.revision ?? '—'}. Lịch sử không bị ghi đè.`} />}
        {error ? <Notice text={error} tone="error" /> : null}
        <PrimaryButton
          label={isCreate ? 'Lưu hồ sơ' : 'Lưu thay đổi'}
          busy={busy}
          disabled={!displayName.trim() || !ageValid || (isCreate && (!accepted || !policy))}
          onPress={() => {
            const input = { displayName, ageMonths: Number(ageMonths), interests };
            if (isCreate) void onCreate(input).catch(() => undefined);
            else void onUpdate(input).catch(() => undefined);
          }}
        />
        <SecondaryButton label="Quay lại hồ sơ" onPress={onBack} />
      </Card>
    </ScreenFrame>
  );
}
