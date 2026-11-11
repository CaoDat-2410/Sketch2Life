import React from 'react';
import { Image, Text, View } from 'react-native';
import type { LessonDetail, ParentProfile } from '../../domain/types';
import type { SelectedPhoto } from '../navigation/workflowTypes';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  profile: ParentProfile;
  policyVersion: string;
  topic: string;
  idea: string;
  lesson: LessonDetail | null;
  photo: SelectedPhoto;
  stepLabel: string;
  busy: boolean;
  error: string;
  onConfirm: () => void;
  onBack: () => void;
};

export function ContextScreen(props: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Xác nhận trước khi tiếp tục" subtitle="Người lớn kiểm tra đúng hồ sơ và bức tranh trước khi tạo buổi học." step={props.stepLabel} onBack={props.onBack}>
      <Card>
        <SectionTitle>Hồ sơ được chọn</SectionTitle>
        <Text style={{ color: palette.ink, fontSize: 16, fontWeight: '700' }}>{props.profile.current_revision.display_name} · {props.profile.current_revision.age_months} tháng</Text>
        <Text style={{ color: palette.muted, fontSize: 13 }}>Quyền xử lý: {props.policyVersion} · revision {props.profile.current_revision.revision}</Text>
      </Card>
      <Card>
        <View style={{ width: '100%', height: 220, borderRadius: 13, backgroundColor: '#F2F6FB', overflow: 'hidden' }}><Image source={{ uri: props.photo.uri }} resizeMode="contain" style={{ width: '100%', height: '100%' }} /></View>
        <SectionTitle>Chủ đề và gợi ý</SectionTitle>
        <Text style={{ color: palette.ink, fontSize: 14 }}>Chủ đề: {props.topic.trim() || 'để AI tìm hiểu từ tranh'}</Text>
        {props.idea.trim() ? <Text style={{ color: palette.muted, fontSize: 14 }}>Ý tưởng: {props.idea.trim()}</Text> : null}
        {props.lesson ? <Notice text={`Giáo án đã pin: ${props.lesson.title} · phiên bản ${props.lesson.version_no}`} tone="success" /> : <Text style={{ color: palette.muted, fontSize: 13 }}>Không dùng giáo án mẫu.</Text>}
      </Card>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      <PrimaryButton label="Xác nhận và phân tích tranh" busy={props.busy} onPress={props.onConfirm} />
      <Text style={{ color: palette.muted, textAlign: 'center', fontSize: 12, lineHeight: 18 }}>Ảnh chỉ được gửi sau khi bạn xác nhận màn này.</Text>
    </ScreenFrame>
  );
}
