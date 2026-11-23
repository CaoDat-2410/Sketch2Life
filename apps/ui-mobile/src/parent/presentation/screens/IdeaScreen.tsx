import React, { useEffect, useState } from 'react';
import { StyleSheet, Switch, Text, TouchableOpacity, View } from 'react-native';
import { Audio } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import type { LessonDetail } from '../../domain/types';
import type { SelectedAudio } from '../navigation/workflowTypes';
import { Card, Field, Notice, PrimaryButton, SecondaryButton, ScreenFrame, palette } from '../components/ui';

type Props = {
  topic: string;
  idea: string;
  audio: SelectedAudio | null;
  guideEnabled: boolean;
  guideBase64: string;
  guideBusy: boolean;
  guideError: string;
  lesson: LessonDetail | null;
  stepLabel: string;
  canContinue: boolean;
  error: string;
  onIdea: (value: string) => void;
  onAudio: (audio: SelectedAudio | null) => void;
  onGuideToggle: (value: boolean) => void;
  onGenerateGuide: () => void;
  onOpenLessons: () => void;
  onContinue: () => void;
  onBack: () => void;
};

export function IdeaScreen(props: Props): React.JSX.Element {
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [recordingBusy, setRecordingBusy] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [recordingError, setRecordingError] = useState('');

  useEffect(() => {
    if (!recording) return undefined;
    const timer = setInterval(() => {
      void recording.getStatusAsync().then((status) => {
        const seconds = Math.min(Math.floor(status.durationMillis / 1000), 120);
        setRecordingSeconds(seconds);
        if (status.durationMillis >= 120_000) void finishRecording(recording);
      }).catch(() => setRecordingError('Không đọc được trạng thái ghi âm.'));
    }, 1000);
    return () => clearInterval(timer);
  }, [recording]);

  async function startRecording(): Promise<void> {
    setRecordingError('');
    setRecordingBusy(true);
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        setRecordingError('Micro chưa được cấp quyền. Bạn vẫn có thể nhập ý tưởng bằng chữ.');
        return;
      }
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const result = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      setRecording(result.recording);
      setRecordingSeconds(0);
    } catch (cause) {
      void cause;
      setRecordingError('Chưa thể bắt đầu ghi âm. Bạn vẫn có thể nhập ý tưởng bằng chữ.');
    } finally {
      setRecordingBusy(false);
    }
  }

  async function finishRecording(target = recording): Promise<void> {
    if (!target || recordingBusy) return;
    setRecordingBusy(true);
    try {
      await target.stopAndUnloadAsync();
      const uri = target.getURI();
      if (!uri) throw new Error('Không lưu được bản ghi âm.');
      const isWave = uri.toLowerCase().endsWith('.wav');
      props.onAudio({ uri, fileName: isWave ? 'parent-idea.wav' : 'parent-idea.m4a', mediaType: isWave ? 'audio/wav' : 'audio/mp4' });
      setRecording(null);
      setRecordingSeconds(0);
    } catch (cause) {
      void cause;
      setRecordingError('Chưa thể lưu bản ghi âm. Hãy thử lại hoặc nhập ý tưởng bằng văn bản.');
      setRecording(null);
    } finally {
      setRecordingBusy(false);
      await Audio.setAudioModeAsync({ allowsRecordingIOS: false, playsInSilentModeIOS: true }).catch(() => undefined);
    }
  }

  return (
    <ScreenFrame
      title="Ý tưởng buổi vẽ"
      subtitle="Thêm điều bé muốn có trong câu chuyện."
      step={props.stepLabel}
      onBack={props.onBack}
      visualTone="creative"
    >
      {props.topic ? <View style={styles.topicPill}>
        <Ionicons name="sparkles-outline" size={15} color={palette.creativePrimary} accessible={false} />
        <Text style={styles.topicPillLabel}>Chủ đề</Text>
        <Text style={styles.topicPillValue} numberOfLines={1}>{props.topic}</Text>
      </View> : null}

      <Card variant="creative" style={styles.ideaCard}>
        <View style={styles.cardHeading}>
          <View style={styles.sectionIcon}>
            <Ionicons name="chatbubble-ellipses-outline" size={21} color={palette.creativePrimary} accessible={false} />
          </View>
          <View style={styles.headingCopy}>
            <Text accessibilityRole="header" style={styles.sectionTitle}>Ý tưởng của gia đình</Text>
            <Text style={styles.mutedText}>Gợi mở câu chuyện cho bé.</Text>
          </View>
          <Text style={styles.optionalBadge}>TÙY CHỌN</Text>
        </View>
        <Field
          variant="creative"
          label="Điều bé muốn vẽ hoặc khám phá"
          value={props.idea}
          onChangeText={props.onIdea}
          placeholder="Ví dụ: một chú thỏ tìm đường về nhà"
          multiline
        />
        <View style={styles.audioSection}>
          <View style={styles.audioHeader}>
            <View style={styles.audioIcon}>
              <Ionicons name="mic-outline" size={18} color={palette.creativePrimary} accessible={false} />
            </View>
            <View style={styles.headingCopy}>
              <Text accessibilityRole="header" style={styles.subsectionTitle}>Thêm ý tưởng bằng giọng nói</Text>
              <Text style={styles.mutedText}>Tối đa 2 phút; có thể dùng cùng phần chữ.</Text>
            </View>
          </View>
          {recording ? <>
            <Notice variant="creative" text={`Đang ghi âm · ${Math.floor(recordingSeconds / 60)}:${String(recordingSeconds % 60).padStart(2, '0')} / 2:00`} tone="warning" />
            <PrimaryButton variant="creative" label="Dừng ghi âm" busy={recordingBusy} onPress={() => void finishRecording()} />
          </> : props.audio ? <>
            <Notice variant="creative" text="Đã lưu bản ghi cho buổi này." tone="success" />
            <SecondaryButton variant="creative" label="Ghi âm lại" disabled={recordingBusy} onPress={() => void startRecording()} />
            <SecondaryButton variant="creative" label="Bỏ bản ghi" disabled={recordingBusy} onPress={() => props.onAudio(null)} />
          </> : <SecondaryButton variant="creative" label={recordingBusy ? 'Đang chuẩn bị micro…' : 'Bắt đầu ghi âm'} disabled={recordingBusy} onPress={() => void startRecording()} />}
          {recordingError ? <Notice variant="creative" text={recordingError} tone="error" /> : null}
        </View>
      </Card>

      <Card variant="creative" style={styles.lessonCard}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={props.lesson ? `Đổi bài học tham khảo. Đang chọn ${props.lesson.title}` : 'Chọn bài học tham khảo từ thư viện'}
          activeOpacity={0.84}
          onPress={props.onOpenLessons}
          style={styles.lessonAction}
        >
          <View style={[styles.sectionIcon, styles.bookIcon]}>
            <Ionicons name="book-outline" size={21} color={palette.creativePrimary} accessible={false} />
          </View>
          <View style={styles.headingCopy}>
            <Text accessibilityRole="header" style={styles.sectionTitle}>Bài học tham khảo</Text>
            <Text style={styles.mutedText} numberOfLines={2}>
              {props.lesson ? `Đang chọn · ${props.lesson.title}` : 'Có thể ghim một bài học từ thư viện.'}
            </Text>
          </View>
          <View style={styles.lessonActionMark}>
            <Text style={styles.lessonActionLabel}>{props.lesson ? 'Đổi' : 'Chọn'}</Text>
            <Ionicons name="chevron-forward" size={15} color={palette.creativePrimary} accessible={false} />
          </View>
        </TouchableOpacity>
      </Card>

      <Card variant="creative" style={styles.guideCard}>
        <View style={styles.guideHeading}>
          <View style={styles.guideIcon}>
            <Ionicons name="color-wand-outline" size={19} color={palette.creativePrimary} accessible={false} />
          </View>
          <View style={styles.headingCopy}>
            <Text accessibilityRole="header" style={styles.sectionTitle}>Gợi ý nét vẽ</Text>
            <Text style={styles.mutedText}>Tùy chọn, có thể bỏ qua.</Text>
          </View>
          <Switch
            accessibilityLabel="Bật gợi ý nét vẽ"
            value={props.guideEnabled}
            onValueChange={props.onGuideToggle}
            trackColor={{ true: '#B995ED', false: '#DDD7E5' }}
            thumbColor={props.guideEnabled ? palette.creativePrimary : '#F7F4FA'}
          />
        </View>
        {props.guideEnabled ? <PrimaryButton variant="creative" label="Mở gợi ý nét vẽ" busy={props.guideBusy} disabled={!props.topic.trim()} onPress={props.onGenerateGuide} /> : null}
        {props.guideError ? <Notice variant="creative" text={props.guideError} tone="warning" /> : null}
      </Card>

      {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
      <PrimaryButton
        variant="creative"
        label={props.guideError ? 'Tiếp tục không cần gợi ý' : 'Tiếp tục đến bức tranh'}
        disabled={!props.canContinue || props.guideBusy}
        onPress={props.onContinue}
      />
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  topicPill: { alignItems: 'center', alignSelf: 'flex-start', backgroundColor: '#F8F2FF', borderColor: palette.creativeBorder, borderRadius: 999, borderWidth: 1, flexDirection: 'row', gap: 6, maxWidth: '100%', minHeight: 34, paddingHorizontal: 11 },
  topicPillLabel: { color: palette.creativeMuted, fontSize: 11, fontWeight: '700' },
  topicPillValue: { color: palette.creativeInk, flexShrink: 1, fontSize: 11, fontWeight: '800' },
  ideaCard: { backgroundColor: palette.white, gap: 15, minWidth: 0, padding: 15 },
  lessonCard: { backgroundColor: palette.white, minWidth: 0, padding: 8 },
  guideCard: { backgroundColor: palette.white, gap: 11, minWidth: 0, padding: 14 },
  cardHeading: { alignItems: 'center', flexDirection: 'row', gap: 10, minWidth: 0 },
  sectionIcon: { alignItems: 'center', backgroundColor: palette.creativeLavender, borderRadius: 14, height: 42, justifyContent: 'center', width: 42 },
  bookIcon: { backgroundColor: '#FFF2DD' },
  headingCopy: { flex: 1, gap: 4, minWidth: 0 },
  sectionTitle: { color: palette.creativeInk, fontSize: 16, lineHeight: 21, fontWeight: '800', flexShrink: 1 },
  subsectionTitle: { color: palette.creativeInk, fontSize: 14, lineHeight: 19, fontWeight: '800', flexShrink: 1 },
  optionalBadge: { borderColor: palette.creativeBorder, borderRadius: 999, borderWidth: 1, color: palette.creativeMuted, flexShrink: 0, fontSize: 9, fontWeight: '800', lineHeight: 13, paddingHorizontal: 8, paddingVertical: 4, backgroundColor: '#FBF8FF' },
  mutedText: { color: palette.creativeMuted, flexShrink: 1, fontSize: 12, lineHeight: 18, minWidth: 0 },
  audioSection: { backgroundColor: '#FAF6FF', borderColor: '#EEE5F8', borderWidth: 1, borderRadius: 16, gap: 10, minWidth: 0, padding: 11 },
  audioHeader: { alignItems: 'center', flexDirection: 'row', gap: 9, minWidth: 0 },
  audioIcon: { alignItems: 'center', backgroundColor: '#F0E6FC', borderRadius: 12, height: 36, justifyContent: 'center', width: 36 },
  lessonAction: { alignItems: 'center', borderRadius: 18, flexDirection: 'row', gap: 11, minHeight: 70, paddingHorizontal: 7, paddingVertical: 7 },
  lessonActionMark: { alignItems: 'center', backgroundColor: '#F5EEFD', borderRadius: 13, flexDirection: 'row', gap: 2, height: 34, justifyContent: 'center', paddingHorizontal: 9 },
  lessonActionLabel: { color: palette.creativePrimary, fontSize: 11, fontWeight: '800' },
  guideIcon: { alignItems: 'center', backgroundColor: '#FFF2DD', borderRadius: 13, height: 38, justifyContent: 'center', width: 38 },
  guideHeading: { alignItems: 'center', flexDirection: 'row', gap: 10, minHeight: 48, minWidth: 0 },
});
