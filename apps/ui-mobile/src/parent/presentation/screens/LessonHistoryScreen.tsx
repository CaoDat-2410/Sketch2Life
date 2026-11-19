import React, { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import type { ParentLessonDelivery } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, palette } from '../components/ui';

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
    return <ScreenFrame title="Bài giáo viên đã dạy" subtitle="Bài học được chia sẻ với hồ sơ của bé." onBack={props.onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']} contentCentered>
      <View style={styles.unavailableCard}>
        <View style={styles.unavailableIcon}><Ionicons name="book-outline" size={24} color="#7435D5" accessible={false} /></View>
        <Text style={styles.stateTitle}>Bài đã dạy chưa khả dụng</Text>
      </View>
    </ScreenFrame>;
  }

  return (
    <ScreenFrame title="Bài giáo viên đã dạy" subtitle="Bài học được chia sẻ với hồ sơ của bé." onBack={props.onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']}>
      <View style={styles.introCard}>
        <View style={styles.introIcon}><Ionicons name="school-outline" size={21} color="#7435D5" accessible={false} /></View>
        <View style={styles.introCopy}>
          <Text style={styles.introTitle}>Hành trình học tập</Text>
          <Text style={styles.introText}>Bài và phản hồi hiển thị theo dữ liệu giáo viên đã chia sẻ.</Text>
        </View>
      </View>

      {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
      {props.error ? <PrimaryButton variant="creative" label="Thử tải lại" busy={props.loading} onPress={props.onLoad} /> : null}
      {!props.deliveries.length && !props.loading && !props.error ? <View style={styles.emptyCard}>
        <View style={styles.emptyIcon}><Ionicons name="book-outline" size={24} color="#7435D5" accessible={false} /></View>
        <Text style={styles.stateTitle}>Chưa có bài học được chia sẻ</Text>
        <Text style={styles.stateDescription}>Khi giáo viên ghi nhận buổi dạy cho hồ sơ này, nội dung sẽ xuất hiện tại đây.</Text>
        <PrimaryButton variant="creative" label="Tải lại danh sách" onPress={props.onLoad} />
      </View> : null}
      {props.deliveries.map((delivery) => <DeliveryCard key={delivery.occurrence_id} delivery={delivery} loading={props.loading} onSubmit={props.onSubmitFeedback} />)}
      {props.loading && !props.deliveries.length ? <View style={styles.loadingCard}><ActivityIndicator color="#7435D5" /><Text style={styles.loadingText}>Đang tải bài học…</Text></View> : null}
      {props.loading && props.deliveries.length ? <View style={styles.loadingFooter}><ActivityIndicator color="#7435D5" /><Text style={styles.loadingText}>Đang cập nhật…</Text></View> : null}
      {props.hasMore && !props.error ? <PrimaryButton variant="creative" label="Xem thêm bài học" busy={props.loading} onPress={props.onLoadMore} /> : null}
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
    <View style={styles.deliveryHeading}>
      <View style={styles.deliveryIcon}><Ionicons name="book-outline" size={19} color="#7435D5" accessible={false} /></View>
      <View style={styles.deliveryTitleBlock}>
        <Text style={styles.eyebrow}>BÀI ĐÃ CHIA SẺ</Text>
        <Text style={styles.deliveryTitle}>{delivery.title}</Text>
      </View>
    </View>
    <View style={styles.deliveryMetaRow}>
      <View style={styles.metaPill}><Ionicons name="pricetag-outline" size={13} color="#685080" accessible={false} /><Text style={styles.deliveryMeta}>{delivery.topic}</Text></View>
      <View style={styles.metaPill}><Ionicons name="calendar-outline" size={13} color="#685080" accessible={false} /><Text style={styles.deliveryMeta}>{formatDate(delivery.delivered_at)}</Text></View>
    </View>

    {delivery.feedback ? <View style={styles.conversationBlock}>
      <View style={styles.conversationHeading}><Ionicons name="chatbubble-ellipses-outline" size={16} color="#7435D5" accessible={false} /><Text style={styles.feedbackHeading}>Góp ý của gia đình</Text></View>
      <Text style={styles.feedbackText}>{delivery.feedback.feedback_text}</Text>
    </View> : null}
    {delivery.replies.map((reply) => <View key={reply.reply_id} style={styles.replyBlock}>
      <View style={styles.conversationHeading}><Ionicons name="chatbubble-outline" size={16} color="#47836A" accessible={false} /><Text style={styles.feedbackHeading}>Phản hồi của giáo viên</Text></View>
      <Text style={styles.feedbackText}>{reply.reply_text}</Text>
    </View>)}
    <Field label={delivery.feedback ? 'Cập nhật góp ý' : 'Góp ý về bài học'} value={feedback} onChangeText={setFeedback} multiline maxLength={1200} placeholder="Chia sẻ nhận xét với giáo viên" />
    {error ? <Notice variant="creative" text={error} tone="error" /> : null}
    <PrimaryButton variant="creative" label={delivery.feedback ? 'Cập nhật góp ý' : 'Gửi góp ý'} busy={loading} disabled={!feedback.trim()} onPress={() => void send()} />
  </Card>;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Ngày chưa xác định' : date.toLocaleDateString('vi-VN');
}

const styles = StyleSheet.create({
  introCard: { flexDirection: 'row', alignItems: 'center', gap: 11, padding: 13, borderRadius: 20, borderWidth: 1.2, borderColor: '#E5D7F2', backgroundColor: '#FFFEFF' },
  introIcon: { width: 42, height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  introCopy: { flex: 1, minWidth: 0, gap: 3 },
  introTitle: { color: '#281451', fontSize: 14, lineHeight: 19, fontWeight: '800' },
  introText: { color: '#70667C', fontSize: 11, lineHeight: 16, flexShrink: 1 },
  unavailableCard: { alignItems: 'center', gap: 11, paddingHorizontal: 21, paddingVertical: 24, borderRadius: 24, borderWidth: 1.2, borderColor: '#E5D7F2', backgroundColor: '#FFFEFF' },
  unavailableIcon: { width: 58, height: 58, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  emptyCard: { alignItems: 'center', gap: 10, padding: 18, borderRadius: 22, borderWidth: 1.2, borderColor: '#E5D7F2', backgroundColor: '#FFFEFF' },
  emptyIcon: { width: 52, height: 52, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  stateTitle: { color: '#281451', fontSize: 17, lineHeight: 23, fontWeight: '800', textAlign: 'center' },
  stateDescription: { color: '#70667C', fontSize: 12, lineHeight: 18, textAlign: 'center', flexShrink: 1 },
  deliveryCard: { backgroundColor: '#FFFEFF', gap: 12, minWidth: 0, borderColor: '#E5D7F2', borderWidth: 1.3, borderRadius: 22 },
  deliveryHeading: { flexDirection: 'row', alignItems: 'center', gap: 10, minWidth: 0 },
  deliveryIcon: { width: 40, height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  deliveryTitleBlock: { flex: 1, minWidth: 0, gap: 2 },
  eyebrow: { color: '#806C91', fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.55 },
  deliveryTitle: { color: '#281451', fontSize: 15, lineHeight: 20, fontWeight: '800', flexShrink: 1 },
  deliveryMetaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  metaPill: { minHeight: 27, flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 9, borderRadius: 14, backgroundColor: '#F5F0FA' },
  deliveryMeta: { color: '#675979', fontSize: 10, lineHeight: 14, fontWeight: '700', flexShrink: 1 },
  conversationBlock: { padding: 11, borderRadius: 15, backgroundColor: '#F7F2FD', gap: 6 },
  replyBlock: { padding: 11, borderRadius: 15, backgroundColor: '#EEF7F1', gap: 6 },
  conversationHeading: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  feedbackHeading: { color: '#49305F', fontSize: 12, lineHeight: 17, fontWeight: '800' },
  feedbackText: { color: palette.muted, fontSize: 12, lineHeight: 18, flexShrink: 1 },
  loadingCard: { minHeight: 78, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, borderRadius: 18, backgroundColor: '#FFFEFF' },
  loadingFooter: { minHeight: 46, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  loadingText: { color: '#70667C', fontSize: 12, lineHeight: 17 },
});
