import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
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
    <ScreenFrame title="Rà soát bản chép lời" subtitle="Sửa lại trước khi xác nhận." step={props.stepLabel} onBack={props.onBack} backDisabled={props.busy}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.busy && props.error && !props.transcript ? <Notice text="Không tự gửi lại yêu cầu nhận dạng khi kết quả chưa rõ. Bạn có thể tiếp tục bằng ý tưởng đã nhập hoặc chỉ dùng bức tranh." tone="warning" /> : null}
      {props.transcript ? <Card style={styles.transcriptCard}>
        <Notice text="CẦN XÁC NHẬN" tone="warning" />
        <SectionTitle>Nội dung nhận dạng</SectionTitle>
        <View style={styles.confidenceBadge}><Text style={styles.confidenceText}>Độ tin cậy ngôn ngữ: {Math.round(props.transcript.language_probability * 100)}%</Text></View>
        <Field label="Chỉnh sửa ý tưởng" value={props.text} onChangeText={props.onText} multiline maxLength={500} placeholder="Sửa lại nội dung nếu cần" />
        <PrimaryButton label="Xác nhận bản chép lời đã sửa" busy={props.busy} disabled={!props.text.trim()} onPress={props.onConfirm} />
      </Card> : <Card style={styles.emptyCard}>
        <SectionTitle>Chưa có bản chép lời</SectionTitle>
        {props.busy
          ? <Text style={styles.emptyText}>Đang xử lý bản ghi âm. Nội dung chỉ được dùng sau khi người lớn xem lại.</Text>
          : <Text style={styles.emptyText}>Chuyển giọng nói thành chữ hiện chưa khả dụng. Bạn vẫn có thể tiếp tục bằng ý tưởng đã nhập hoặc chỉ dùng bức tranh.</Text>}
      </Card>}
      <SecondaryButton label="Tiếp tục bằng ý tưởng đã nhập" disabled={props.busy} onPress={props.onContinueWithoutAudio} />
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  transcriptCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  emptyCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  emptyText: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
  confidenceBadge: { alignSelf: 'flex-start', minHeight: 24, justifyContent: 'center', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 12, borderWidth: 1.3, borderColor: palette.outline, backgroundColor: palette.butter },
  confidenceText: { color: palette.ink, fontSize: 9, lineHeight: 13, minWidth: 0, flexShrink: 1 },
});
