import React from 'react';
import { Text } from 'react-native';
import type { ParentAudioTranscription } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';

type Props = {
  stepLabel: string;
  transcript: ParentAudioTranscription | null;
  text: string;
  busy: boolean;
  error: string;
  onText: (value: string) => void;
  onConfirm: () => void;
  onContinueWithoutAudio: () => void;
  onBack: () => void;
};

export function TranscriptReviewScreen(props: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Nghe và sửa ý tưởng" subtitle="Người lớn xác nhận transcript trước khi phân tích tranh." step={props.stepLabel} onBack={props.onBack} backDisabled={props.busy}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.busy && props.error && !props.transcript ? <Notice text="Không tự gửi lại yêu cầu nhận dạng khi kết quả chưa rõ. Bạn có thể tiếp tục bằng ý tưởng đã nhập hoặc chỉ dùng bức tranh." tone="warning" /> : null}
      {props.transcript ? <Card>
        <SectionTitle>Whisper · tiếng Việt</SectionTitle>
        <Text style={{ color: palette.muted, fontSize: 13 }}>Độ tin cậy ngôn ngữ: {Math.round(props.transcript.language_probability * 100)}%</Text>
        <Field label="Nội dung đã nghe" value={props.text} onChangeText={props.onText} multiline maxLength={500} placeholder="Sửa transcript nếu cần" />
        <PrimaryButton label="Xác nhận transcript và tiếp tục" busy={props.busy} disabled={!props.text.trim()} onPress={props.onConfirm} />
      </Card> : <Card>
        <SectionTitle>Chưa có transcript</SectionTitle>
        {props.busy
          ? <Text style={{ color: palette.muted, lineHeight: 20 }}>Đang nhận dạng tiếng Việt. Giữ màn hình này; kết quả sẽ được người lớn xem lại trước khi dùng.</Text>
          : <Text style={{ color: palette.muted, lineHeight: 20 }}>Có thể tiếp tục với ý tưởng đã nhập bằng chữ, hoặc chỉ dùng bức tranh.</Text>}
      </Card>}
      <SecondaryButton label="Tiếp tục không dùng bản ghi âm" disabled={props.busy} onPress={props.onContinueWithoutAudio} />
    </ScreenFrame>
  );
}
