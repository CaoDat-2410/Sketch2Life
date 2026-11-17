import React, { useEffect, useState } from 'react';
import { Image, Switch, Text, View } from 'react-native';
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
  onTopic: (value: string) => void;
  onIdea: (value: string) => void;
  onAudio: (audio: SelectedAudio | null) => void;
  onGuideToggle: (value: boolean) => void;
  onGenerateGuide: () => void;
  onOpenLessons: () => void;
  onContinue: () => void;
  onBack: () => void;
};

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
      if (!permission.granted) throw new Error('Cần cho phép dùng micro để ghi ý tưởng.');
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const result = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      setRecording(result.recording);
      setRecordingSeconds(0);
    } catch (cause) {
      setRecordingError(cause instanceof Error ? cause.message : 'Không thể bắt đầu ghi âm.');
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
      setRecordingError(cause instanceof Error ? cause.message : 'Không thể hoàn tất bản ghi.');
      setRecording(null);
    } finally {
      setRecordingBusy(false);
      await Audio.setAudioModeAsync({ allowsRecordingIOS: false, playsInSilentModeIOS: true }).catch(() => undefined);
    }
  }

  return (
    <ScreenFrame title="Chọn chủ đề" subtitle="Bạn có thể để trống. Ảnh tranh vẫn là bước bắt buộc." step={props.stepLabel} onBack={props.onBack}>
      <Card>
        <Field label="Chủ đề (tùy chọn)" value={props.topic} onChangeText={props.onTopic} placeholder="Ví dụ: con bướm" />
        <Field label="Ý tưởng của người lớn (tùy chọn)" value={props.idea} onChangeText={props.onIdea} placeholder="Điều bé đang tò mò…" multiline />
        <SectionTitle>Hoặc ghi âm ý tưởng</SectionTitle>
        <Text style={{ color: palette.muted, fontSize: 13 }}>Tối đa 2 phút. Transcript sẽ được người lớn xem và sửa trước khi dùng.</Text>
        {recording ? <>
          <Notice text={`Đang ghi âm · ${Math.floor(recordingSeconds / 60)}:${String(recordingSeconds % 60).padStart(2, '0')} / 2:00`} tone="warning" />
          <PrimaryButton label="Dừng ghi âm" busy={recordingBusy} onPress={() => void finishRecording()} />
        </> : props.audio ? <>
          <Notice text="Đã lưu bản ghi âm cho buổi này." tone="success" />
          <SecondaryButton label="Ghi âm lại" disabled={recordingBusy} onPress={() => void startRecording()} />
          <SecondaryButton label="Bỏ bản ghi" disabled={recordingBusy} onPress={() => props.onAudio(null)} />
        </> : <SecondaryButton label="Bắt đầu ghi âm" disabled={recordingBusy} onPress={() => void startRecording()} />}
        {recordingError ? <Notice text={recordingError} tone="error" /> : null}
      </Card>
      <Card>
        <SectionTitle>Giáo án mẫu</SectionTitle>
        {props.lesson ? <Notice text={`Đã chọn: ${props.lesson.title}`} tone="success" /> : <Text style={{ color: palette.muted, fontSize: 14 }}>Không chọn giáo án cũng được.</Text>}
        <SecondaryButton label={props.lesson ? 'Đổi giáo án' : 'Chọn giáo án (tùy chọn)'} onPress={props.onOpenLessons} />
      </Card>
      <Card>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <View style={{ flex: 1 }}><SectionTitle>Gợi ý nét vẽ</SectionTitle><Text style={{ color: palette.muted, fontSize: 13, lineHeight: 19, marginTop: 5 }}>Chỉ tạo khi bạn bật. Dùng chủ đề chung, không gửi ảnh hay hồ sơ trẻ.</Text></View>
          <Switch value={props.guideEnabled} onValueChange={props.onGuideToggle} trackColor={{ true: palette.blue }} />
        </View>
        {props.guideEnabled ? <PrimaryButton label="Tạo gợi ý nét vẽ" busy={props.guideBusy} disabled={!props.topic.trim()} onPress={props.onGenerateGuide} /> : null}
        {props.guideError ? <Notice text={props.guideError} tone="error" /> : null}
        {props.guideBase64 ? <Image accessibilityLabel="Gợi ý line sketch được tạo bởi AI" source={{ uri: `data:image/png;base64,${props.guideBase64}` }} resizeMode="contain" style={{ width: '100%', height: 240, backgroundColor: '#fff', borderRadius: 12 }} /> : null}
      </Card>
      <PrimaryButton label="Tiếp tục đến chụp tranh" disabled={props.guideBusy} onPress={props.onContinue} />
    </ScreenFrame>
  );
}
