import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { createParentActionIdentity } from '../../application/ports/ParentPorts';
import type {
  ParentLessonFeedbackReplyPageV1,
  ParentLessonFeedbackStateV1,
  ParentLessonFeedbackV1,
} from '../../domain/types';
import { Notice, PrimaryButton, TextButton, palette } from '../components/ui';

type Props = {
  lessonId: string;
  onLoadThread: (lessonId: string) => Promise<ParentLessonFeedbackStateV1>;
  onLoadReplies: (lessonId: string, cursor?: string | null) => Promise<ParentLessonFeedbackReplyPageV1>;
  onSubmit: (lessonId: string, text: string, actionIdentity: string) => Promise<ParentLessonFeedbackV1>;
};

export function LessonFeedbackSection({ lessonId, onLoadThread, onLoadReplies, onSubmit }: Props): React.JSX.Element {
  const [feedback, setFeedback] = useState<ParentLessonFeedbackV1 | null>(null);
  const [replies, setReplies] = useState<ParentLessonFeedbackReplyPageV1['items']>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const action = useRef<{ signature: string; key: string } | null>(null);
  const characterCount = Array.from(text.trim()).length;

  async function load(): Promise<void> {
    setLoading(true);
    setError('');
    try {
      const [thread, page] = await Promise.all([
        onLoadThread(lessonId),
        onLoadReplies(lessonId, null),
      ]);
      setFeedback(thread.feedback);
      setReplies(page.items);
      setCursor(page.next_cursor);
    } catch (failure) {
      setError(feedbackFailureMessage(failure));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [lessonId]);

  async function loadMore(): Promise<void> {
    if (!cursor || loadingMore) return;
    setLoadingMore(true);
    setError('');
    try {
      const page = await onLoadReplies(lessonId, cursor);
      setReplies((current) => [...current, ...page.items]);
      setCursor(page.next_cursor);
    } catch (failure) {
      setError(feedbackFailureMessage(failure));
    } finally {
      setLoadingMore(false);
    }
  }

  async function send(): Promise<void> {
    const value = text.trim();
    const count = Array.from(value).length;
    if (!value || count > 1200 || submitting) return;
    const signature = JSON.stringify([lessonId, value]);
    if (!action.current || action.current.signature !== signature) {
      action.current = { signature, key: createParentActionIdentity() };
    }
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      const next = await onSubmit(lessonId, value, action.current.key);
      action.current = null;
      setFeedback(next);
      setText('');
      setSuccess('Đã gửi phản hồi. Tin nhắn mới được thêm vào cuộc trò chuyện.');
    } catch (failure) {
      setError(feedbackFailureMessage(failure));
    } finally {
      setSubmitting(false);
    }
  }

  return <View style={styles.section}>
    <View style={styles.heading}>
      <Ionicons name="chatbubble-ellipses-outline" size={18} color="#7435D5" accessible={false} />
      <Text accessibilityRole="header" style={styles.title}>Phản hồi</Text>
    </View>
    <Text style={styles.body}>Gửi nhận xét cho người tạo bài học. Mỗi lần gửi sẽ bổ sung một tin nhắn mới.</Text>
    {loading ? <View style={styles.loading}><ActivityIndicator color="#7435D5" /><Text style={styles.body}>Đang tải cuộc trò chuyện…</Text></View> : null}
    {error ? <Notice variant="creative" text={error} tone="warning" /> : null}
    {!loading && error ? <TextButton label="Thử tải lại" onPress={() => void load()} /> : null}
    {feedback ? <View style={styles.messageCard}>
      <Text style={styles.messageLabel}>Phản hồi gần nhất của bạn</Text>
      <Text selectable style={styles.messageText}>{feedback.feedback_text}</Text>
      <Text style={styles.meta}>Cập nhật {formatDate(feedback.updated_at)}</Text>
    </View> : null}
    {replies.map((reply) => <View key={reply.reply_id} style={styles.replyCard}>
      <Text style={styles.messageLabel}>Phản hồi từ bài học</Text>
      <Text selectable style={styles.messageText}>{reply.reply_text}</Text>
      <Text style={styles.meta}>{formatDate(reply.created_at)}</Text>
    </View>)}
    {cursor ? <TextButton label={loadingMore ? 'Đang tải…' : 'Xem thêm phản hồi'} disabled={loadingMore} onPress={() => void loadMore()} /> : null}
    <TextInput
      accessibilityLabel={feedback ? 'Gửi thêm phản hồi' : 'Nội dung phản hồi'}
      editable={!submitting}
      maxLength={2400}
      multiline
      onChangeText={setText}
      placeholder="Viết phản hồi về bài học"
      style={styles.input}
      textAlignVertical="top"
      value={text}
    />
    <Text style={styles.meta}>{characterCount}/1.200 ký tự</Text>
    {success ? <Text style={styles.success}>{success}</Text> : null}
    <PrimaryButton
      label={submitting ? 'Đang gửi…' : feedback ? 'Gửi bổ sung' : 'Gửi phản hồi'}
      busy={submitting}
      disabled={!characterCount || characterCount > 1200 || submitting}
      onPress={() => void send()}
    />
  </View>;
}

function feedbackFailureMessage(failure: unknown): string {
  if (failure instanceof ParentApplicationError) {
    if (failure.status === 403 || failure.status === 404
      || failure.code === 'RESOURCE_NOT_FOUND' || failure.code.endsWith('_NOT_FOUND')) {
      return 'Bài học này hiện chưa khả dụng.';
    }
    if (failure.status === 503 || failure.code === 'PROVIDER_UNAVAILABLE') {
      return 'Phản hồi hiện chưa khả dụng. Hãy thử lại sau.';
    }
    if (failure.code === 'INVALID_REQUEST' || failure.code === 'LESSON_FEEDBACK_INVALID') {
      return 'Phản hồi cần có từ 1 đến 1.200 ký tự.';
    }
  }
  return 'Chưa tải hoặc gửi được phản hồi. Hãy thử lại sau.';
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('vi-VN');
}

const styles = StyleSheet.create({
  section: { gap: 9, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#EDE4F4' },
  heading: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  title: { color: '#281451', fontSize: 14, lineHeight: 19, fontWeight: '800' },
  body: { color: palette.muted, fontSize: 11, lineHeight: 17, flexShrink: 1 },
  loading: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 6 },
  messageCard: { gap: 5, borderRadius: 14, backgroundColor: '#F7F1FF', padding: 10 },
  replyCard: { gap: 5, borderRadius: 14, backgroundColor: '#F2F8F4', padding: 10 },
  messageLabel: { color: '#60418A', fontSize: 10, lineHeight: 14, fontWeight: '800' },
  messageText: { color: '#332342', fontSize: 12, lineHeight: 18 },
  meta: { color: '#81758A', fontSize: 10, lineHeight: 14 },
  input: { minHeight: 92, borderWidth: 1, borderColor: '#DDD0EC', borderRadius: 14, padding: 11, color: '#332342', fontSize: 13, lineHeight: 19 },
  success: { color: '#397454', fontSize: 11, lineHeight: 16 },
});
