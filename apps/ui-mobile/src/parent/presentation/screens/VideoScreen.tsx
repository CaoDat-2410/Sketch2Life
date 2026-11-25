import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { ResizeMode, Video } from 'expo-av';
import type { ParentPlaybackSourceV1, ParentVideoQuota, ParentVideoReasonCodeV1 } from '../../domain/types';
import { VIDEO_REASON_CODES, VIDEO_REASON_LABELS, type VideoPanel } from '../../application/parentPhaseB';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, palette } from '../components/ui';
import { ACTIVITY_COPY } from './ActivityScreen';

type Props = {
  stepLabel: string;
  panel: VideoPanel;
  /** What the app is doing now: '', 'video-request', 'video-playback', 'video-unsuitable' or 'video-complete'. */
  busy: string;
  error: string;
  quotaExceeded: boolean;
  quotaSummary: ParentVideoQuota | null;
  playback: ParentPlaybackSourceV1 | null;
  reason: ParentVideoReasonCodeV1 | null;
  markingUnsuitable: boolean;
  onReason: (reason: ParentVideoReasonCodeV1) => void;
  onRequest: () => void;
  onPlay: () => void;
  onPlaybackError: () => void;
  onStartUnsuitable: () => void;
  onCancelUnsuitable: () => void;
  onConfirmUnsuitable: () => void;
  onComplete: () => void;
  onBackToStory: () => void;
  onOpenHistory: () => void;
  onRefresh: () => void;
  onOpenQuota: () => void;
  onBack: () => void;
};

/**
 * Video step (SRS l.395, l.1670-1676): request, follow the server, play the ready video, mark it unsuitable
 * or finish the run. The player gets the stream address and headers only; no token is ever shown or logged.
 */
export function VideoScreen(props: Props): React.JSX.Element {
  const { panel } = props;
  const working = props.busy !== '';
  const needsReason = (panel.canRequest && panel.requiresReason) || props.markingUnsuitable;
  const reasonMissing = needsReason && props.reason === null;
  const remainingByGrantKind = props.quotaSummary?.grants.reduce((remaining, grant) => {
    if (grant.kind === 'INCLUDED') remaining.included += grant.available;
    if (grant.kind === 'TOP_UP') remaining.topUp += grant.available;
    return remaining;
  }, { included: 0, topUp: 0 }) ?? null;
  return (
    <ScreenFrame
      title="Video của bé"
      subtitle="Video chỉ được phát sau khi qua kiểm tra."
      step={props.stepLabel}
      onBack={props.onBack}
      backDisabled={props.busy === 'video-request' || props.busy === 'video-unsuitable' || props.busy === 'video-complete'}
      visualTone="creative"
    >
      {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}

      <Card variant="creative" style={styles.statusCard}>
        <Notice variant="creative" text={panel.headline} tone={panel.tone} />
        {panel.detail ? <Text style={styles.bodyText}>{panel.detail}</Text> : null}
        {props.quotaSummary ? <Text style={styles.metaText}>Còn {props.quotaSummary.available_units} lượt tạo video trong tài khoản.</Text> : null}
        {panel.requestsRemaining !== null && !panel.closed ? (
          <Text style={styles.metaText}>Còn {panel.requestsRemaining} lượt tạo video cho buổi học này.</Text>
        ) : null}
        {panel.scenes.length > 0 ? (
          <View style={styles.sceneList}>
            {panel.scenes.map((scene) => (
              <Text key={scene.index} style={styles.sceneRow}>Cảnh {scene.index}: {scene.label}</Text>
            ))}
          </View>
        ) : null}
        {panel.inFlight ? <SecondaryButton variant="creative" label="Kiểm tra lại" disabled={working} onPress={props.onRefresh} /> : null}
        {props.quotaExceeded && remainingByGrantKind ? (
          <Text style={styles.metaText}>Lượt tháng còn {remainingByGrantKind.included} · lượt mua thêm còn {remainingByGrantKind.topUp}.</Text>
        ) : null}
        {props.quotaExceeded ? <SecondaryButton variant="creative" label="Mua thêm lượt" disabled={working} onPress={props.onOpenQuota} /> : null}
      </Card>

      {panel.canPlay ? (
        <Card variant="creative" style={styles.playerCard}>
          <SectionTitle variant="creative">Xem video</SectionTitle>
          {props.playback ? (
            <Video
              accessibilityLabel="Video câu chuyện của bé"
              source={{ uri: props.playback.uri, headers: props.playback.headers }}
              style={styles.player}
              resizeMode={ResizeMode.CONTAIN}
              useNativeControls
              shouldPlay
              onError={props.onPlaybackError}
            />
          ) : (
            <PrimaryButton variant="creative" label="Mở video" busy={props.busy === 'video-playback'} disabled={working} onPress={props.onPlay} />
          )}
          {props.playback ? <SecondaryButton variant="creative" label="Mở lại video" disabled={working} onPress={props.onPlay} /> : null}
        </Card>
      ) : null}

      {panel.postVideoActivities && panel.postVideoActivities.length > 0 ? (
        <Card variant="creative" style={styles.playerCard}>
          <SectionTitle variant="creative">Hoạt động sau khi xem</SectionTitle>
          {panel.postVideoActivities.map((activity, index) => (
            <View key={`${activity.activity_ref?.lesson_id ?? 'ai-draft'}-${activity.activity_ref?.version_id ?? 'draft'}-${activity.activity_ref?.activity_index ?? index}-${index}`} style={styles.activityRow}>
              <Text style={styles.activityTitle}>{activity.is_main ? 'Hoạt động chính' : 'Hoạt động gợi ý'} · {activity.title}</Text>
              <Text style={styles.bodyText}>{activity.objective}</Text>
              {activity.source === 'AI_DRAFT' ? (
                <>
                  <Text style={styles.metaText}>{ACTIVITY_COPY.aiSuggestionLabel}</Text>
                  <Text style={styles.bodyText}>{ACTIVITY_COPY.aiReviewed}</Text>
                </>
              ) : null}
            </View>
          ))}
        </Card>
      ) : null}

      {needsReason ? (
        <Card variant="creative" style={styles.reasonCard}>
          <SectionTitle variant="creative">{props.markingUnsuitable ? 'Video chưa phù hợp vì sao?' : 'Vì sao tạo lại video?'}</SectionTitle>
          {VIDEO_REASON_CODES.map((code) => (
            <TouchableOpacity
              key={code}
              accessibilityRole="radio"
              accessibilityState={{ selected: props.reason === code }}
              onPress={() => props.onReason(code)}
              style={[styles.reasonRow, props.reason === code ? styles.reasonRowSelected : null]}
            >
              <Text style={styles.reasonLabel}>{VIDEO_REASON_LABELS[code]}</Text>
            </TouchableOpacity>
          ))}
        </Card>
      ) : null}

      {panel.canRequest ? (
        <PrimaryButton
          variant="creative"
          label={panel.requiresReason ? 'Tạo lại video' : 'Tạo video'}
          busy={props.busy === 'video-request'}
          disabled={working || reasonMissing}
          onPress={props.onRequest}
        />
      ) : null}

      {props.markingUnsuitable ? (
        <>
          <PrimaryButton variant="creative" label="Đánh dấu video chưa phù hợp" busy={props.busy === 'video-unsuitable'} disabled={working || reasonMissing} onPress={props.onConfirmUnsuitable} />
          <SecondaryButton variant="creative" label="Không đánh dấu" disabled={working} onPress={props.onCancelUnsuitable} />
        </>
      ) : (
        <>
          {panel.canComplete ? (
            <PrimaryButton variant="creative" label="Hoàn tất buổi học" busy={props.busy === 'video-complete'} disabled={working} onPress={props.onComplete} />
          ) : null}
          {panel.canMarkUnsuitable ? (
            <SecondaryButton variant="creative" label="Video chưa phù hợp" disabled={working} onPress={props.onStartUnsuitable} />
          ) : null}
        </>
      )}

      {panel.needsScriptReview ? (
        <SecondaryButton variant="creative" label="Xem lại kịch bản" disabled={working} onPress={props.onBackToStory} />
      ) : null}
      {panel.closed ? <SecondaryButton variant="creative" label="Xem lịch sử buổi học" onPress={props.onOpenHistory} /> : null}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  statusCard: { gap: 11, minWidth: 0 },
  playerCard: { gap: 11, minWidth: 0 },
  reasonCard: { gap: 9, minWidth: 0 },
  bodyText: { color: palette.creativeMuted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  metaText: { color: palette.creativeMuted, fontSize: 11, lineHeight: 16, flexShrink: 1, minWidth: 0 },
  sceneList: { gap: 4 },
  sceneRow: { color: palette.creativeInk, fontSize: 12, lineHeight: 17 },
  activityRow: { gap: 4, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#EEE5F8' },
  activityTitle: { color: palette.creativeInk, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  player: { width: '100%', aspectRatio: 16 / 9, backgroundColor: '#000000', borderRadius: 14 },
  reasonRow: { minHeight: 44, justifyContent: 'center', borderRadius: 14, borderWidth: 1.2, borderColor: palette.creativeBorder, paddingHorizontal: 12, backgroundColor: palette.white },
  reasonRowSelected: { borderColor: palette.creativePrimary, backgroundColor: palette.creativeLavender },
  reasonLabel: { color: palette.creativeInk, fontSize: 13, lineHeight: 18, fontWeight: '700' },
});
