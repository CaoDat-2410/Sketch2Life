import React from 'react';
import { StyleSheet, Text } from 'react-native';
import type { ParentRunTranscriptV1 } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';

type Props = {
  stepLabel: string;
  transcript: ParentRunTranscriptV1 | null;
  /** The server is still turning the recording into text (state PENDING). */
  waiting: boolean;
  text: string;
  /** True when the adult changed the text: it is sent as a correction before the confirmation. */
  edited: boolean;
  busy: boolean;
  error: string;
  onText: (value: string) => void;
  onConfirm: () => void;
  onRefresh: () => void;
  onBack: () => void;
};

/**
 * Transcript review (SRS l.512, l.1665, TD-04): the adult reads what the system heard, may correct it,
 * and confirms exactly that revision. The story is not created from the recording before this.
 */
export function TranscriptReviewScreen(props: Props): React.JSX.Element {
  const failed = props.transcript?.state === 'FAILED';
  const reviewing = props.transcript?.state === 'NEEDS_CONFIRMATION';
  return (
    <ScreenFrame title="Rà soát bản chép lời" subtitle="Sửa lại trước khi xác nhận." step={props.stepLabel} onBack={props.onBack} backDisabled={props.busy}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {props.transcript && !props.waiting ? <Card style={styles.transcriptCard}>
        <Notice text={failed ? 'CHƯA NHẬN DẠNG ĐƯỢC' : 'CẦN XÁC NHẬN'} tone="warning" />
        <SectionTitle>Nội dung nhận dạng</SectionTitle>
        {failed ? <Text style={styles.emptyText}>Chưa chuyển được giọng nói thành chữ. Bạn có thể gõ lại ý tưởng bên dưới.</Text> : null}
        <Field label="Chỉnh sửa ý tưởng" value={props.text} onChangeText={props.onText} multiline maxLength={500} placeholder="Sửa lại nội dung nếu cần" />
        <PrimaryButton
          label={failed ? 'Dùng ý tưởng này' : props.edited ? 'Lưu chỗ sửa và xác nhận' : 'Xác nhận bản chép lời'}
          busy={props.busy}
          disabled={!props.text.trim() || (!reviewing && !failed)}
          onPress={props.onConfirm}
        />
      </Card> : <Card style={styles.emptyCard}>
        <SectionTitle>{props.waiting ? 'Đang chuyển giọng nói thành chữ' : 'Chưa có bản chép lời'}</SectionTitle>
        {props.waiting
          ? <Text style={styles.emptyText}>Việc này có thể mất một lúc. Nội dung chỉ được dùng sau khi người lớn xem lại.</Text>
          : <Text style={styles.emptyText}>{props.error
            ? 'Bạn có thể thử tải lại bản chép lời.'
            : 'Chưa có bản ghi âm nào cho buổi học này.'}</Text>}
        <SecondaryButton label="Tải lại" disabled={props.busy} onPress={props.onRefresh} />
      </Card>}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  transcriptCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  emptyCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  emptyText: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
});
