import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import type { ParentLessonDelivery } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  capability: ParentCapabilityState;
  deliveries: ParentLessonDelivery[];
  loading: boolean;
  error: string;
  hasMore: boolean;
  onLoad: () => void;
  onLoadMore: () => void;
  onSubmitFeedback: (occurrenceId: string, text: string) => Promise<void>;
  onBack: () => void;
};

export function LessonHistoryScreen(props: Props): React.JSX.Element {
  if (props.capability.state === 'unavailable') {
    return <ScreenFrame title="Bài học đã xem" subtitle="Trạng thái tính năng" onBack={props.onBack}>
      <Notice text="Lịch sử bài đã học, tải nội dung và gửi góp ý chưa khả dụng vì chưa có hợp đồng dịch vụ được xác nhận. Không có dữ liệu rỗng hoặc thao tác gửi nào được suy ra." tone="warning" />
    </ScreenFrame>;
  }

  return (
    <ScreenFrame title="Bài học đã xem" subtitle="Lịch sử trong 30 ngày từ lần mở đầu." onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.deliveries.length && !props.loading ? <Card>
        <SectionTitle>Chưa có bài học để xem</SectionTitle>
        <Text style={styles.emptyDescription}>Bài sẽ hiện khi giáo viên đã chia sẻ hồ sơ và ghi nhận buổi dạy.</Text>
        <PrimaryButton label="Tải lại" onPress={props.onLoad} />
      </Card> : null}
      {props.deliveries.map((delivery) => <DeliveryCard key={delivery.occurrence_id} delivery={delivery} loading={props.loading} onSubmit={props.onSubmitFeedback} />)}
      {props.loading ? <Notice text="Đang tải bài đã học…" /> : null}
      {props.hasMore ? <PrimaryButton label="Xem thêm" busy={props.loading} onPress={props.onLoadMore} /> : null}
    </ScreenFrame>
  );
}

function DeliveryCard({ delivery, loading, onSubmit }: {
  delivery: ParentLessonDelivery;
  loading: boolean;
  onSubmit: (occurrenceId: string, text: string) => Promise<void>;
}): React.JSX.Element {
  const [feedback, setFeedback] = useState(delivery.feedback?.feedback_text ?? '');
  const [error, setError] = useState('');
  async function send(): Promise<void> {
    setError('');
    try {
      await onSubmit(delivery.occurrence_id, feedback);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không gửi được góp ý.');
    }
  }

  return <Card style={styles.deliveryCard}>
    <SectionTitle>{delivery.title}</SectionTitle>
    <Text style={styles.deliveryMeta}>{delivery.topic} · {new Date(delivery.delivered_at).toLocaleDateString('vi-VN')}</Text>
    {delivery.feedback ? <View style={{ gap: 8 }}>
      <Text style={styles.feedbackHeading}>Góp ý của bạn</Text>
      <Text style={styles.feedbackText}>{delivery.feedback.feedback_text}</Text>
    </View> : null}
    {delivery.replies.map((reply) => <View key={reply.reply_id} style={{ borderLeftWidth: 1.3, borderLeftColor: '#CFC3B3', paddingLeft: 8, gap: 4 }}>
      <Text style={styles.feedbackHeading}>Phản hồi của giáo viên</Text>
      <Text style={styles.feedbackText}>{reply.reply_text}</Text>
    </View>)}
    <Field label={delivery.feedback ? 'Cập nhật góp ý' : 'Góp ý về bài học'} value={feedback} onChangeText={setFeedback} multiline maxLength={1200} placeholder="Chia sẻ nhận xét với giáo viên" />
    {error ? <Notice text={error} tone="error" /> : null}
    <PrimaryButton label={delivery.feedback ? 'Cập nhật góp ý' : 'Gửi góp ý'} busy={loading} disabled={!feedback.trim()} onPress={() => void send()} />
  </Card>;
}

const styles = StyleSheet.create({
  deliveryCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  deliveryMeta: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  emptyDescription: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  feedbackHeading: { color: palette.ink, fontSize: 13, lineHeight: 19, fontWeight: '700', flexShrink: 1, minWidth: 0 },
  feedbackText: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
});
