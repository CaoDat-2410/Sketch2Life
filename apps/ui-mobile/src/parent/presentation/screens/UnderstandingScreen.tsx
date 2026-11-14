import React from 'react';
import { Text, View } from 'react-native';
import type { ParentCandidate } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  candidate: ParentCandidate;
  stepLabel: string;
  subject: string;
  busy: boolean;
  error: string;
  onSubject: (value: string) => void;
  onConfirm: () => void;
  onBack: () => void;
};

export function UnderstandingScreen(props: Props): React.JSX.Element {
  const confidence = Math.max(0, Math.min(100, Math.round(props.candidate.confidence * 100)));
  return (
    <ScreenFrame title="AI nhìn thấy gì?" subtitle="Đây là gợi ý của AI. Người lớn cần xác nhận hoặc sửa chủ thể." step={props.stepLabel === '5 / 7' ? '4 / 7' : props.stepLabel} onBack={props.onBack}>
      <Card>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}><SectionTitle>Chủ thể dự đoán</SectionTitle><Text style={{ color: palette.blue, fontWeight: '800' }}>{confidence}%</Text></View>
        <Field label="Chủ thể" value={props.subject} onChangeText={props.onSubject} placeholder="Nhập chủ thể trong tranh" />
        <View style={{ gap: 7 }}>
          <Text style={{ color: palette.ink, fontSize: 13, fontWeight: '800' }}>Đặc điểm nhìn thấy</Text>
          {props.candidate.visible_features.map((feature, index) => <Text key={`${index}-${feature}`} style={{ color: palette.muted, fontSize: 14, lineHeight: 20 }}>• {feature}</Text>)}
          {props.candidate.visible_features.length === 0 ? <Text style={{ color: palette.muted, fontSize: 13 }}>AI chưa trả về đặc điểm.</Text> : null}
        </View>
        <Notice text="Bạn có thể sửa tên chủ thể. Bước tiếp theo chỉ chạy sau khi người lớn xác nhận." />
        <Notice text="Chưa có tín hiệu từ máy chủ để xác định chủ đề có khớp với tranh hay không. Người lớn có thể sửa chủ thể; bài học đã ghim được giữ nguyên." tone="warning" />
      </Card>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      <PrimaryButton label="Xác nhận chủ thể" busy={props.busy} disabled={!props.subject.trim()} onPress={props.onConfirm} />
    </ScreenFrame>
  );
}
