import React, { useEffect, useState } from 'react';
import { Image, Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { Audio } from 'expo-av';
import type { LessonDetail } from '../../domain/types';
import type { SelectedAudio } from '../navigation/workflowTypes';
import { Card, Field, Notice, PrimaryButton, SecondaryButton, SectionTitle, ScreenFrame, palette } from '../components/ui';

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
  onTopic: (value: string) => void;
  onIdea: (value: string) => void;
  onAudio: (audio: SelectedAudio | null) => void;
  onGuideToggle: (value: boolean) => void;
  onGenerateGuide: () => void;
  onOpenLessons: () => void;
  onContinue: () => void;
  onBack: () => void;
};

const topicSuggestions = ['Khu vườn và thiên nhiên', 'Phương tiện quanh em'] as const;

export function TopicScreen(props: Props): React.JSX.Element {
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
    <ScreenFrame title="Chọn gợi ý (tùy chọn)" subtitle="Chủ đề có thể bỏ qua; cần ghim một phiên bản bài học chính xác để tiếp tục." step={props.stepLabel} onBack={props.onBack}>
      <Card style={styles.topicCard}>
        <View style={styles.cardHeading}>
          <View style={styles.headingCopy}>
            <SectionTitle>Chủ đề</SectionTitle>
            <Text style={styles.mutedText}>Chủ đề có thể bỏ qua.</Text>
          </View>
          <Text style={styles.optionalBadge}>TÙY CHỌN</Text>
        </View>
        <Field label="Chủ đề" value={props.topic} onChangeText={props.onTopic} placeholder="Viết chủ đề (không bắt buộc)" />
        <View style={styles.topicChoices}>
          {topicSuggestions.map((topic) => {
            const selected = props.topic === topic;
            return <Pressable
              key={topic}
              accessibilityRole="button"
              accessibilityLabel={topic}
              accessibilityState={{ selected }}
              onPress={() => props.onTopic(topic)}
              style={({ pressed }) => [styles.topicChip, selected && styles.topicChipSelected, pressed && styles.pressed]}
            >
              <Text style={[styles.topicChipText, selected && styles.topicChipTextSelected]}>{topic}</Text>
            </Pressable>;
          })}
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Bỏ qua chủ đề"
            accessibilityState={{ selected: !props.topic }}
            onPress={() => props.onTopic('')}
            style={({ pressed }) => [styles.topicChip, !props.topic && styles.topicChipSelected, pressed && styles.pressed]}
          >
            <Text style={[styles.topicChipText, !props.topic && styles.topicChipTextSelected]}>Bỏ qua chủ đề</Text>
          </Pressable>
        </View>
      </Card>

      <Card style={styles.ideaCard}>
        <View style={styles.cardHeading}>
          <View style={styles.headingCopy}>
            <SectionTitle>Ý tưởng của gia đình</SectionTitle>
            <Text style={styles.mutedText}>Viết hoặc nói một ý ngắn.</Text>
          </View>
          <Text style={styles.optionalBadge}>TÙY CHỌN</Text>
        </View>
        <Field label="Ý tưởng (tùy chọn)" value={props.idea} onChangeText={props.onIdea} placeholder="Viết ý tưởng của gia đình" multiline />
        <View style={styles.audioSection}>
          <SectionTitle>Ghi âm ý tưởng</SectionTitle>
          <Text style={styles.mutedText}>Bản ghi tối đa 2 phút. Chuyển giọng nói thành chữ hiện chưa khả dụng; bạn vẫn có thể nhập ý tưởng bằng chữ.</Text>
          {recording ? <>
            <Notice text={`Đang ghi âm · ${Math.floor(recordingSeconds / 60)}:${String(recordingSeconds % 60).padStart(2, '0')} / 2:00`} tone="warning" />
            <PrimaryButton label="Dừng ghi âm" busy={recordingBusy} onPress={() => void finishRecording()} />
          </> : props.audio ? <>
            <Notice text="Bản ghi đã được chọn." tone="info" />
            <SecondaryButton label="Ghi âm lại" disabled={recordingBusy} onPress={() => void startRecording()} />
            <SecondaryButton label="Bỏ bản ghi" disabled={recordingBusy} onPress={() => props.onAudio(null)} />
          </> : <SecondaryButton label="Thử nhập bằng giọng nói" disabled={recordingBusy} onPress={() => void startRecording()} />}
          {recordingError ? <Notice text={recordingError} tone="error" /> : null}
        </View>
      </Card>
      <Card style={styles.lessonCard}>
        <SectionTitle>{props.lesson ? 'Bài học đã ghim' : 'Bài học từ thư viện'}</SectionTitle>
        {props.lesson ? <Notice text={`Đã ghim: ${props.lesson.title} · phiên bản ${props.lesson.version_id} · SHA-256 ${props.lesson.content_sha256}`} tone="success" /> : <Text style={styles.mutedText}>Chỉ tiếp tục sau khi ghim một phiên bản bài học chính xác.</Text>}
        <SecondaryButton label="Mở thư viện" onPress={props.onOpenLessons} />
      </Card>
      <Card style={styles.guideCard}>
        <View style={styles.guideHeading}>
          <View style={styles.guideCopy}>
            <SectionTitle>Gợi ý vẽ (tùy chọn)</SectionTitle>
            <Text style={styles.guideDescription}>Có thể bỏ qua hướng dẫn bất cứ lúc nào. Không ảnh hưởng việc chụp tranh.</Text>
          </View>
          <Switch accessibilityLabel="Gợi ý vẽ (tùy chọn)" value={props.guideEnabled} onValueChange={props.onGuideToggle} trackColor={{ true: palette.blue }} />
        </View>
        {props.guideEnabled ? <PrimaryButton label="Tạo gợi ý nét vẽ" busy={props.guideBusy} disabled={!props.topic.trim()} onPress={props.onGenerateGuide} /> : null}
        {props.guideError ? <Notice text={props.guideError} tone="error" /> : null}
        {props.guideBase64 ? <Image accessibilityLabel="Gợi ý nét vẽ do trí tuệ nhân tạo tạo" source={{ uri: `data:image/png;base64,${props.guideBase64}` }} resizeMode="contain" style={styles.guideImage} /> : null}
      </Card>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      <PrimaryButton label="Tiếp tục" disabled={!props.canContinue || props.guideBusy} onPress={props.onContinue} />
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  topicCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  ideaCard: { backgroundColor: palette.white, gap: 14, minWidth: 0 },
  lessonCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  guideCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  cardHeading: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, minWidth: 0 },
  headingCopy: { flex: 1, minWidth: 0, gap: 6 },
  optionalBadge: { color: palette.ink, fontSize: 9, lineHeight: 13, fontWeight: '800', borderWidth: 1, borderColor: palette.outline, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 4, flexShrink: 0 },
  mutedText: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
  topicChoices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  topicChip: { minHeight: 44, justifyContent: 'center', borderWidth: 1.3, borderColor: palette.outline, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 7, backgroundColor: palette.white },
  topicChipSelected: { borderWidth: 2, backgroundColor: palette.butter },
  topicChipText: { color: palette.muted, fontSize: 9, lineHeight: 13, fontWeight: '700', flexShrink: 1 },
  topicChipTextSelected: { color: palette.ink },
  pressed: { opacity: 0.78 },
  audioSection: { gap: 10, borderTopWidth: 1, borderTopColor: '#CFC3B3', paddingTop: 12, minWidth: 0 },
  guideHeading: { flexDirection: 'row', alignItems: 'center', gap: 12, minWidth: 0 },
  guideCopy: { flex: 1, minWidth: 0, gap: 6 },
  guideDescription: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
  guideImage: { width: '100%', height: 240, backgroundColor: palette.white, borderRadius: 16, borderWidth: 1.5, borderColor: palette.outline },
});
