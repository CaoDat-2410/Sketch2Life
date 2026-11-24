import React, { useEffect, useRef, useState } from 'react';
import { Video, ResizeMode, type AVPlaybackStatus } from 'expo-av';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentVideoCandidateV1 } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';
import { videoCandidateProgressFor } from './videoCandidateProgress';
import { ParentAiLoadingState } from '../components/ParentAiLoadingState';

type Props = {
  runId: string;
  storyRevision: number | null;
  storySha256: string;
  storyConfirmed: boolean;
  candidate: ParentVideoCandidateV1 | null;
  busy: boolean;
  requestAttempted: boolean;
  error: string;
  previewSource: { uri: string; headers: Record<string, string> } | null;
  onStart: () => void | Promise<unknown>;
  onRefresh: () => void | Promise<unknown>;
  onPreview: () => void | Promise<unknown>;
  onBack: () => void;
};

export function VideoCandidateScreen(props: Props): React.JSX.Element {
  const polling = props.candidate !== null
    && ['STAGING', 'DISPATCHING', 'QUEUED', 'GENERATING'].includes(props.candidate.state);
  const refreshRef = useRef(props.onRefresh);
  refreshRef.current = props.onRefresh;
  const videoRef = useRef<Video | null>(null);
  const [playback, setPlayback] = useState<PlaybackState>(initialPlaybackState);
  const [playbackError, setPlaybackError] = useState('');
  const [previewAttempt, setPreviewAttempt] = useState(0);

  useEffect(() => {
    setPlayback(initialPlaybackState);
    setPlaybackError('');
  }, [props.previewSource?.uri, previewAttempt]);

  useEffect(() => {
    if (!props.runId) return;
    void props.onRefresh();
  }, [props.runId]);

  useEffect(() => {
    if (!polling) return undefined;
    let active = true;
    let inFlight = false;
    let remainingPolls = 70;
    const timer = setInterval(() => {
      if (!active || inFlight) return;
      if (remainingPolls <= 0) {
        clearInterval(timer);
        return;
      }
      remainingPolls -= 1;
      inFlight = true;
      Promise.resolve(refreshRef.current()).finally(() => { inFlight = false; });
    }, 30_000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [polling]);

  const candidate = props.candidate;
  const noCandidateAfterAttempt = !candidate && props.requestAttempted;
  const status = candidate ? candidateStatus(candidate.state) : null;
  const progress = candidate ? videoCandidateProgressFor(candidate.state) : null;
  const canStart = props.storyConfirmed
    && props.storyRevision !== null
    && /^[a-f0-9]{64}$/.test(props.storySha256)
    && !props.busy
    && !candidate
    && !props.requestAttempted;

  return (
    <ScreenFrame
      title="Video xem thử"
      subtitle="Từ tranh của bé"
      step="8 / 8"
      onBack={props.onBack}
      visualTone="creative"
    >
      <Notice
        variant="creative"
        text="Bản thử nghiệm · Chưa kiểm tra an toàn."
        tone="warning"
      />

      {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}

      {!candidate ? (
        <Card variant="creative" style={styles.card}>
          <SectionTitle variant="creative">Video từ tranh và câu chuyện</SectionTitle>
          {!props.busy ? <Text style={styles.body}>Tạo một bản xem thử im lặng từ tranh và kịch bản đã xác nhận.</Text> : null}
          {props.busy ? (
            <ParentAiLoadingState
              testID="parent-video-ai-loading"
              title={props.requestAttempted ? 'Đang gửi yêu cầu tạo video' : 'Đang kiểm tra trạng thái video'}
              description={props.requestAttempted
                ? 'Đang chuyển ảnh tranh và kịch bản đã xác nhận sang bộ xử lý video.'
                : 'Đang tìm yêu cầu video đã có của buổi học này; chưa tạo yêu cầu mới.'}
              note={props.requestAttempted
                ? 'Không bấm tạo lại. Trạng thái sẽ được kiểm tra sau khi máy chủ phản hồi.'
                : 'Chưa gửi yêu cầu tạo video.'}
            />
          ) : noCandidateAfterAttempt ? (
            <>
              <Notice variant="creative" text="Yêu cầu trước chưa có kết quả xác nhận. Hãy kiểm tra trạng thái; không gửi request tạo mới." tone="warning" />
              <SecondaryButton variant="creative" label="Kiểm tra trạng thái" disabled={props.busy} onPress={props.onRefresh} />
            </>
          ) : (
            <PrimaryButton
              variant="creative"
              label="Tạo video xem thử"
              busy={props.busy}
              disabled={!canStart}
              onPress={props.onStart}
            />
          )}
          {!props.storyConfirmed ? <Text style={styles.muted}>Cần người lớn xác nhận kịch bản trước.</Text> : null}
        </Card>
      ) : (
        <Card variant="creative" style={styles.card}>
          <SectionTitle variant="creative">{candidate.state === 'CANDIDATE_READY' ? 'Video đã sẵn sàng' : status?.title}</SectionTitle>
          {candidate.state !== 'CANDIDATE_READY' ? <Text style={styles.body}>{status?.description}</Text> : null}
          {polling && progress ? (
            <VideoProgressPanel steps={progress} />
          ) : null}
          {candidate.state === 'FAILED' && candidate.safe_failure_code ? (
            <Text selectable style={styles.code}>Mã lỗi an toàn: {candidate.safe_failure_code}</Text>
          ) : null}
          {candidate.state === 'CANDIDATE_READY' && candidate.metadata ? (
            <>
              {props.previewSource ? (
                <>
                  <View style={styles.playerFrame}>
                    <Video
                      key={`${props.previewSource.uri}:${previewAttempt}`}
                      ref={videoRef}
                      source={{ uri: props.previewSource.uri, headers: props.previewSource.headers }}
                      style={styles.player}
                      useNativeControls={false}
                      resizeMode={ResizeMode.CONTAIN}
                      isMuted
                      onPlaybackStatusUpdate={handlePlaybackStatus}
                      onError={handlePlaybackError}
                    />
                    {!playback.isLoaded && !playbackError ? (
                      <View style={styles.loadingOverlay}>
                        <ActivityIndicator size="large" color="#FFFFFF" />
                        <Text style={styles.loadingText}>Đang tải video…</Text>
                      </View>
                    ) : null}
                  </View>
                  {playbackError ? (
                    <Notice variant="creative" text={playbackError} tone="error" />
                  ) : null}
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={playback.isPlaying ? 'Tạm dừng video' : playback.didJustFinish ? 'Phát lại video' : 'Phát video'}
                    accessibilityState={{ disabled: !playback.isLoaded || props.busy }}
                    disabled={!playback.isLoaded || props.busy}
                    onPress={() => { void togglePlayback(); }}
                    style={({ pressed }) => [styles.playControl, (!playback.isLoaded || props.busy) && styles.playControlDisabled, pressed && styles.playControlPressed]}
                  >
                    <Ionicons
                      name={playback.isPlaying ? 'pause' : playback.didJustFinish ? 'refresh' : 'play'}
                      size={20}
                      color="#FFFFFF"
                      accessible={false}
                    />
                    <Text style={styles.playControlText}>
                      {playback.isPlaying ? 'Tạm dừng' : playback.didJustFinish ? 'Phát lại' : 'Phát video'}
                    </Text>
                    {playback.isBuffering ? <ActivityIndicator color="#FFFFFF" size="small" /> : null}
                  </Pressable>
                  {playbackError ? (
                    <SecondaryButton
                      variant="creative"
                      label={props.busy ? 'Đang tải…' : 'Tải lại video'}
                      disabled={props.busy}
                      onPress={() => { void reloadPreview(); }}
                    />
                  ) : null}
                  <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: playback.durationMillis || 1, now: playback.positionMillis }} style={styles.timeline}>
                    <View style={styles.timelineTrack}>
                      <View style={[styles.timelineFill, { width: `${progressPercent(playback)}%` }]} />
                    </View>
                    <View style={styles.timeLabels}>
                      <Text style={styles.timeText}>{formatTime(playback.positionMillis)}</Text>
                      <Text style={styles.timeText}>{formatTime(playback.durationMillis || Math.round(candidate.metadata.duration_seconds * 1000))}</Text>
                    </View>
                  </View>
                </>
              ) : (
                <PrimaryButton variant="creative" label={props.busy ? 'Đang tải video…' : 'Mở video'} disabled={!candidate.preview_available || props.busy} busy={props.busy} onPress={props.onPreview} />
              )}
              <Text style={styles.compactMeta}>
                {Math.round(candidate.metadata.duration_seconds)} giây · {candidate.metadata.scene_count} cảnh · Không có âm thanh
              </Text>
            </>
          ) : null}
          {candidate.state === 'AWAITING_RECONCILIATION' ? (
            <Notice variant="creative" text="Chưa xác minh được video đã hoàn tất hay chưa. Hệ thống không gửi lại yêu cầu; hãy kiểm tra trạng thái trước." tone="warning" />
          ) : null}
          {candidate.state !== 'FAILED' && candidate.state !== 'CANDIDATE_READY' ? (
            <SecondaryButton variant="creative" label={props.busy ? 'Đang cập nhật…' : 'Kiểm tra trạng thái'} disabled={props.busy} onPress={props.onRefresh} />
          ) : null}
        </Card>
      )}
    </ScreenFrame>
  );

  async function togglePlayback(): Promise<void> {
    const player = videoRef.current;
    if (!player || !playback.isLoaded) return;
    try {
      const status = playback.isPlaying
        ? await player.pauseAsync()
        : playback.didJustFinish
          ? await player.replayAsync()
          : await player.playAsync();
      handlePlaybackStatus(status);
      setPlaybackError('');
    } catch {
      setPlaybackError('Video chưa phát được. Hãy tải lại để thử.');
    }
  }

  async function reloadPreview(): Promise<void> {
    setPlayback(initialPlaybackState);
    setPlaybackError('');
    setPreviewAttempt((attempt) => attempt + 1);
    await props.onPreview();
  }

  function handlePlaybackStatus(status: AVPlaybackStatus): void {
    if (!status.isLoaded) {
      setPlayback(initialPlaybackState);
      if (status.error) setPlaybackError('Video chưa phát được. Hãy tải lại để thử.');
      return;
    }
    setPlayback({
      isLoaded: true,
      isPlaying: status.isPlaying,
      isBuffering: status.isBuffering,
      positionMillis: status.positionMillis,
      durationMillis: status.durationMillis ?? 0,
      didJustFinish: status.didJustFinish,
    });
  }

  function handlePlaybackError(_error: string): void {
    setPlaybackError('Video chưa phát được. Hãy tải lại để thử.');
  }
}

type PlaybackState = {
  isLoaded: boolean;
  isPlaying: boolean;
  isBuffering: boolean;
  positionMillis: number;
  durationMillis: number;
  didJustFinish: boolean;
};

const initialPlaybackState: PlaybackState = {
  isLoaded: false,
  isPlaying: false,
  isBuffering: false,
  positionMillis: 0,
  durationMillis: 0,
  didJustFinish: false,
};

function formatTime(milliseconds: number): string {
  const seconds = Math.max(0, Math.floor(milliseconds / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}

function progressPercent(playback: PlaybackState): number {
  if (!playback.durationMillis) return 0;
  return Math.min(100, Math.max(0, (playback.positionMillis / playback.durationMillis) * 100));
}

function VideoProgressPanel({
  steps,
}: {
  steps: NonNullable<ReturnType<typeof videoCandidateProgressFor>>;
}): React.JSX.Element {
  return (
    <View style={styles.progressPanel} accessibilityLiveRegion="polite">
      <View style={styles.progressHeader}>
        <View style={styles.progressSpinner}>
          <ActivityIndicator size="small" color={palette.creativePrimary} />
        </View>
        <View style={styles.dispatchCopy}>
          <Text style={styles.progressTitle} accessibilityRole="text">Đang xử lý yêu cầu video</Text>
          <Text style={styles.progressHint}>Khi màn hình đang mở, trạng thái tự cập nhật khoảng mỗi 30 giây.</Text>
        </View>
      </View>
      <View style={styles.progressSteps}>
        {steps.map((step) => (
          <View key={step.id} style={styles.progressStep}>
            <View style={styles.progressMarker}>
              {step.state === 'complete' ? (
                <Ionicons name="checkmark-circle" size={19} color={palette.creativePrimary} accessible={false} />
              ) : step.state === 'current' ? (
                <View style={styles.currentMarker} />
              ) : (
                <View style={styles.upcomingMarker} />
              )}
            </View>
            <Text style={[styles.progressStepLabel, step.state === 'current' && styles.currentStepLabel]}>
              {step.label}
            </Text>
            {step.state === 'current' ? <Text style={styles.currentStepHint}>Đang thực hiện</Text> : null}
          </View>
        ))}
      </View>
      <Text style={styles.progressHint}>Bạn có thể rời màn hình. Mở lại buổi học để xem trạng thái mới nhất.</Text>
    </View>
  );
}

function candidateStatus(state: ParentVideoCandidateV1['state']): { title: string; description: string } {
  const labels: Record<ParentVideoCandidateV1['state'], { title: string; description: string }> = {
    STAGING: { title: 'Đang chuẩn bị video', description: 'Đang kiểm tra tranh và câu chuyện đã xác nhận.' },
    DISPATCHING: { title: 'Đang chuyển yêu cầu', description: 'Yêu cầu tạo video đang được chuyển đi.' },
    QUEUED: { title: 'Đang chờ xử lý', description: 'Yêu cầu đang chờ đến lượt tạo video.' },
    GENERATING: { title: 'Đang tạo chuyển động', description: 'AI đang tạo các cảnh theo ảnh tranh và câu chuyện.' },
    CANDIDATE_READY: { title: 'Đã có video xem thử', description: 'Video đã được lưu riêng tư để phụ huynh xem thử.' },
    FAILED: { title: 'Chưa tạo được video', description: 'Yêu cầu này chưa có video xem thử.' },
    AWAITING_RECONCILIATION: { title: 'Đang xác minh kết quả', description: 'Yêu cầu đã gửi nhưng chưa có kết quả xác nhận.' },
  };
  return labels[state];
}

const styles = StyleSheet.create({
  card: { gap: 12 },
  body: { color: palette.creativeInk, fontSize: 14, lineHeight: 20 },
  muted: { color: palette.creativeMuted, fontSize: 12, lineHeight: 18 },
  dispatchCopy: { flex: 1, minWidth: 0, gap: 5 },
  progressPanel: { gap: 12, padding: 14, borderRadius: 16, borderWidth: 1, borderColor: palette.creativeBorder, backgroundColor: '#FBF8FF' },
  progressHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  progressSpinner: { width: 28, height: 28, alignItems: 'center', justifyContent: 'center' },
  progressTitle: { color: palette.creativeInk, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  progressHint: { color: palette.creativeMuted, fontSize: 11, lineHeight: 16 },
  progressSteps: { gap: 10, paddingVertical: 2 },
  progressStep: { minHeight: 23, flexDirection: 'row', alignItems: 'center', gap: 8 },
  progressMarker: { width: 20, alignItems: 'center', justifyContent: 'center' },
  currentMarker: { width: 11, height: 11, borderRadius: 6, backgroundColor: palette.creativePrimary, borderWidth: 3, borderColor: '#DCC5FF' },
  upcomingMarker: { width: 9, height: 9, borderRadius: 5, backgroundColor: '#D8CFDF' },
  progressStepLabel: { flex: 1, color: palette.creativeMuted, fontSize: 12, lineHeight: 17 },
  currentStepLabel: { color: palette.creativeInk, fontWeight: '700' },
  currentStepHint: { color: palette.creativePrimary, fontSize: 10, lineHeight: 14, fontWeight: '700' },
  playerFrame: { width: '100%', aspectRatio: 16 / 9, overflow: 'hidden', borderRadius: 16, backgroundColor: '#17131F' },
  player: { ...StyleSheet.absoluteFillObject },
  loadingOverlay: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: 'rgba(23,19,31,0.58)' },
  loadingText: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },
  playControl: { minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, paddingHorizontal: 18, borderRadius: 15, backgroundColor: palette.creativePrimary },
  playControlDisabled: { opacity: 0.52 },
  playControlPressed: { opacity: 0.84 },
  playControlText: { color: '#FFFFFF', fontSize: 15, lineHeight: 20, fontWeight: '800' },
  timeline: { gap: 5 },
  timelineTrack: { height: 5, overflow: 'hidden', borderRadius: 3, backgroundColor: '#E5D9F1' },
  timelineFill: { height: '100%', borderRadius: 3, backgroundColor: palette.creativePrimary },
  timeLabels: { flexDirection: 'row', justifyContent: 'space-between' },
  timeText: { color: palette.creativeMuted, fontSize: 11, lineHeight: 16, fontVariant: ['tabular-nums'] },
  compactMeta: { alignSelf: 'center', color: palette.creativeMuted, fontSize: 12, lineHeight: 17 },
  code: { color: palette.creativeMuted, fontSize: 11, lineHeight: 16 },
});
