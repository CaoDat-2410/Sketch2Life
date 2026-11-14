import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { ParentCapabilityState, ParentJobStageState } from '../../application/ports/ParentCapabilityPorts';
import type { StoryDraft } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, SecondaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  videoCapability: ParentCapabilityState;
  jobStage: ParentJobStageState;
  stepLabel: string;
  story: StoryDraft | null;
  rewriteCount: number;
  rewriteInstruction: string;
  busy: boolean;
  attempted: boolean;
  canConfirm: boolean;
  error: string;
  confirmed: boolean;
  onRewriteInstruction: (value: string) => void;
  onGenerate: () => void;
  onRetry: () => void;
  onRewrite: () => void;
  onConfirm: () => void;
  onBack: () => void;
};

export function StoryScreen(props: Props): React.JSX.Element {
  const videoStateMessage = props.videoCapability.state === 'unavailable'
    ? 'Tạo video, kiểm tra an toàn và phát video chưa khả dụng vì chưa có hợp đồng dịch vụ được xác nhận. Chưa có yêu cầu tạo video nào được gửi.'
    : jobStageMessage(props.jobStage);

  return (
    <ScreenFrame title="Rà soát kịch bản" subtitle="Xác nhận đúng bản đang hiển thị." step={props.stepLabel} onBack={props.onBack}>
      <Notice text="Hoạt động chính: chưa khả dụng. Kịch bản vẫn có thể tiếp tục mà không gắn hoạt động." tone="warning" />
      <Notice text={videoStateMessage} tone="warning" />
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.story ? <Card style={styles.generationCard}><Text style={styles.bodyText}>Kịch bản được cá nhân hóa theo tranh và chủ thể đã xác nhận.</Text>{props.attempted ? <>
        <Notice text="Yêu cầu chưa có kết quả hiển thị. Không tự gửi lại; bạn có thể chọn gửi lại cùng yêu cầu." tone="warning" />
        <SecondaryButton label="Gửi lại cùng yêu cầu" disabled={props.busy} onPress={props.onRetry} />
      </> : <PrimaryButton label="Tạo kịch bản bằng trí tuệ nhân tạo" busy={props.busy} onPress={props.onGenerate} />}</Card> : (
        <>
          <Card style={styles.storyCard}>
            <Text style={styles.draftLabel}>BẢN NHÁP · {storyLanguageLabel(props.story.language)}</Text>
            <Text style={styles.storyTitle}>{props.story.title}</Text>
            <Text style={styles.metadataText}>Mã phiên bản: {props.story.revisionId ?? 'chưa có'}</Text>
            <Text style={styles.metadataText}>Số phiên bản: {props.story.revisionNo ?? 'chưa có'}</Text>
            <Text selectable style={styles.metadataText}>
              Mã SHA-256: {props.story.sha256 ?? 'chưa có'}
            </Text>
            <Text style={styles.storyBody}>{props.story.story.opening}</Text>
            <Text style={styles.storyBody}>{props.story.story.middle}</Text>
            <Text style={styles.storyBody}>{props.story.story.ending}</Text>
          </Card>
          <Card style={styles.scenesCard}>
            <SectionTitle>Các cảnh</SectionTitle>
            {props.story.scenes.map((scene) => (
              <View key={scene.scene_index} style={styles.scene}>
                <Text style={styles.sceneTitle}>Cảnh {scene.scene_index} · {scene.title}</Text>
                <Text style={styles.sceneBody}>{scene.action}</Text>
                <Text style={styles.sceneNarration}>{scene.narration}</Text>
              </View>
            ))}
          </Card>
          {!props.confirmed ? <Card style={styles.revisionCard}>
            <Text style={styles.revisionHint}>Mọi thay đổi tạo bản nội dung mới; xác nhận cũ không được dùng lại.</Text>
            <Field label={`Gợi ý viết lại · tối đa 3 lần (còn ${Math.max(0, 3 - props.rewriteCount)})`} value={props.rewriteInstruction} onChangeText={props.onRewriteInstruction} placeholder="Nhập gợi ý viết lại" multiline editable={props.rewriteCount < 3 && !props.busy} />
            {props.rewriteCount < 3 ? <SecondaryButton label="Gửi gợi ý viết lại · tối đa 3 lần" disabled={!props.rewriteInstruction.trim() || props.busy} onPress={props.onRewrite} /> : null}
            <Notice text="Người lớn xem lại và xác nhận đúng bản đang hiển thị." />
            <PrimaryButton label="Xác nhận bản nội dung đang xem" busy={props.busy} disabled={!props.canConfirm || !props.story.revisionId || !props.story.sha256} onPress={props.onConfirm} />
          </Card> : <Notice text="Kịch bản đã được người lớn xác nhận." tone="success" />}
        </>
      )}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  generationCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  storyCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  scenesCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  scene: { borderTopWidth: 1.3, borderTopColor: '#CFC3B3', paddingTop: 10, gap: 8, minWidth: 0 },
  revisionCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  bodyText: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  draftLabel: { color: palette.ink, backgroundColor: palette.paleAmber, fontSize: 10, lineHeight: 14, fontWeight: '800', paddingHorizontal: 7, paddingVertical: 3, minHeight: 24, borderWidth: 1, borderColor: palette.outline, borderRadius: 999, alignSelf: 'flex-start', flexShrink: 1, minWidth: 0 },
  storyTitle: { color: palette.ink, fontSize: 16, lineHeight: 20, fontWeight: '800', flexShrink: 1, minWidth: 0 },
  metadataText: { color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1, minWidth: 0 },
  storyBody: { color: palette.ink, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  sceneTitle: { color: palette.blue, fontSize: 11, lineHeight: 15, fontWeight: '800', flexShrink: 1, minWidth: 0 },
  sceneBody: { color: palette.ink, fontSize: 12, lineHeight: 16, flexShrink: 1, minWidth: 0 },
  sceneNarration: { color: palette.muted, fontSize: 12, lineHeight: 16, flexShrink: 1, minWidth: 0 },
  revisionHint: { color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1, minWidth: 0 },
});

function storyLanguageLabel(language: string): string {
  const normalized = language.trim().toLowerCase();
  if (normalized === 'vi' || normalized === 'vi-vn' || normalized === 'vietnamese') return 'Tiếng Việt';
  if (normalized === 'en' || normalized === 'en-us' || normalized === 'english') return 'Tiếng Anh';
  return 'Ngôn ngữ khác';
}

function jobStageMessage(stage: ParentJobStageState): string {
  if (stage.state === 'idle') return 'Chưa có tác vụ video.';
  if (stage.state === 'pending') return 'Tác vụ video đang chờ xử lý; trạng thái chưa phải kết quả hoàn tất.';
  if (stage.state === 'reconciling') return 'Đang kiểm tra trạng thái tác vụ video. Không gửi yêu cầu trùng lặp.';
  if (stage.state === 'confirmed') return 'Máy chủ đã xác nhận tác vụ video hoàn tất; chưa có trình phát được nối.';
  if (stage.state === 'failed') return 'Tác vụ video thất bại theo trạng thái máy chủ.';
  return 'Trạng thái tác vụ video chưa khả dụng.';
}
