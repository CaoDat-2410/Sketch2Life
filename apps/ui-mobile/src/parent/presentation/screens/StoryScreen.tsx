import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentCapabilityState, ParentJobStageState } from '../../application/ports/ParentCapabilityPorts';
import type { StoryDraft } from '../../domain/types';
import type { ParentVideoCandidateV1 } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, SecondaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';
import { ParentAiLoadingState } from '../components/ParentAiLoadingState';

export type StoryBusyOperation = 'generating' | 'rewriting' | 'confirming' | null;

type Props = {
  storyRunId?: string;
  videoCapability: ParentCapabilityState;
  jobStage: ParentJobStageState;
  stepLabel: string;
  story: StoryDraft | null;
  storyCurrent?: boolean;
  failedGeneration?: boolean;
  serverPending?: boolean;
  reconciliationRequired?: boolean;
  storyReady: boolean;
  blockedReason: string;
  rewriteCount: number;
  rewriteInstruction: string;
  busy: boolean;
  busyOperation?: StoryBusyOperation;
  attempted: boolean;
  canConfirm: boolean;
  error: string;
  confirmed: boolean;
  videoCandidate?: ParentVideoCandidateV1 | null;
  onOpenVideo?: () => void;
  onRewriteInstruction: (value: string) => void;
  onGenerate: () => void;
  /** Kept optional for the non-interactive preview harness; never rendered as a retry action. */
  onRetry?: () => void;
  onRewrite: () => void;
  onConfirm: () => void;
  onBack?: () => void;
  onOpenHistory?: () => void;
};

export function StoryScreen(props: Props): React.JSX.Element {
  const [detailsVisible, setDetailsVisible] = useState(false);
  const storyCurrent = props.storyCurrent ?? true;
  const serverPending = props.serverPending ?? false;
  const reconciliationRequired = props.reconciliationRequired ?? false;
  const failedGeneration = props.failedGeneration ?? false;
  const requestPending = props.busy || serverPending;
  const currentVideoCandidate = props.videoCandidate
    && (!props.storyRunId || props.videoCandidate.story_run_id === props.storyRunId)
    ? props.videoCandidate
    : null;
  const videoStateMessage = props.videoCapability.state === 'unavailable'
    ? 'Tạo video chưa khả dụng vì dịch vụ chưa được xác nhận.'
    : jobStageMessage(props.jobStage);

  return (
    <ScreenFrame
      title="Câu chuyện của bé"
      subtitle="Cùng xem lại câu chuyện từ bức tranh."
      step={props.stepLabel}
      onBack={props.onBack}
      visualTone="creative"
    >
      {!props.storyReady ? (
        <Notice variant="creative" text={props.blockedReason} tone="warning" />
      ) : null}
      {props.error && !props.busy ? <Notice variant="creative" text={props.error} tone="error" /> : null}

      {!props.story || !storyCurrent ? (
        <>
        {requestPending ? (
          <ParentAiLoadingState
            testID="parent-story-ai-loading"
            title={storyBusyTitle(props.busyOperation, serverPending, reconciliationRequired)}
            description={storyBusyDescription(props.busyOperation, serverPending, reconciliationRequired)}
            statusLabel={storyBusyStatusLabel(props.busyOperation, serverPending, reconciliationRequired)}
            note={storyLoadingNote(reconciliationRequired)}
            mode={reconciliationRequired ? 'reconciliation' : 'processing'}
            showElapsed={!serverPending}
            prominent={requestPending && !reconciliationRequired}
          />
        ) : null}
        {serverPending && props.onOpenHistory ? (
          <SecondaryButton variant="creative" label="Mở lịch sử để kiểm tra buổi đang xử lý" onPress={props.onOpenHistory} />
        ) : null}
        {(!props.story || !storyCurrent) && !requestPending ? (
        <Card variant="creative" style={styles.generationCard}>
          <View style={styles.storyArtwork}>
            <StoryIllustration />
          </View>
          <View style={styles.generationCopy}>
            <Text style={styles.eyebrow}>TỪ BỨC TRANH CỦA BÉ</Text>
            <SectionTitle variant="creative">
              {failedGeneration ? 'Bản nháp chưa đạt yêu cầu' : 'Sẵn sàng mở ra một câu chuyện?'}
            </SectionTitle>
            <Text style={styles.bodyText}>
              {failedGeneration
                ? 'AI chưa tạo được kịch bản đạt yêu cầu. Bản lỗi không thể xác nhận; hãy gửi một gợi ý mới để tạo bản khác.'
                : 'Kịch bản sẽ được tạo từ bức tranh và chủ thể người lớn đã xác nhận.'}
            </Text>
          </View>
          {failedGeneration ? (
            <>
              <Notice variant="creative" text="Bản trước chưa đạt kiểm tra nội dung. Tranh, chủ thể và hoạt động đã chọn vẫn được giữ." tone="warning" />
              {props.rewriteCount < 3 ? (
                <>
                  <Field
                    variant="creative"
                    label={`Gợi ý để AI viết lại · còn ${Math.max(0, 3 - props.rewriteCount)} lần`}
                    value={props.rewriteInstruction}
                    onChangeText={props.onRewriteInstruction}
                    placeholder="Ví dụ: viết câu ngắn, đầy đủ; giữ nguyên con rùa và hoạt động đã chọn"
                    multiline
                    editable={props.storyReady && !props.busy}
                  />
                  <SecondaryButton
                    variant="creative"
                    label="Gửi gợi ý để viết lại"
                    disabled={!props.storyReady || props.busy || !props.rewriteInstruction.trim()}
                    onPress={props.onRewrite}
                  />
                </>
              ) : (
                <Notice variant="creative" text="Bạn đã dùng hết số lần viết lại cho câu chuyện này." tone="info" />
              )}
            </>
          ) : props.attempted ? (
            <>
              <Notice variant="creative" text="Chưa có bản nháp được máy chủ xác nhận. Hãy kiểm tra trạng thái buổi học trước khi gửi yêu cầu mới." tone="warning" />
              {props.onOpenHistory ? (
                <SecondaryButton variant="creative" label="Mở lịch sử buổi học" onPress={props.onOpenHistory} />
              ) : null}
            </>
          ) : (
            <PrimaryButton variant="creative" label="Tạo câu chuyện" disabled={!props.storyReady} onPress={props.onGenerate} />
          )}
        </Card>
        ) : null}
        {props.story && !storyCurrent && !requestPending ? (
          <Card variant="creative" style={styles.revisionCard}>
            <SectionTitle variant="creative">Bản nháp trước chưa được xác nhận</SectionTitle>
            <Notice
              variant="creative"
              text="Lượt cập nhật chưa hoàn tất. Nội dung cũ được giữ trong buổi học nhưng không thể xem hoặc xác nhận như bản hiện hành."
              tone="warning"
            />
          </Card>
        ) : null}
        </>
      ) : (
        <>
          {requestPending ? (
            <ParentAiLoadingState
              testID="parent-story-ai-loading"
              title={storyBusyTitle(props.busyOperation, serverPending, reconciliationRequired)}
              description={storyBusyDescription(props.busyOperation, serverPending, reconciliationRequired)}
              statusLabel={storyBusyStatusLabel(props.busyOperation, serverPending, reconciliationRequired)}
              note={storyLoadingNote(reconciliationRequired)}
              mode={reconciliationRequired ? 'reconciliation' : 'processing'}
              showElapsed={!serverPending}
              prominent={requestPending && !reconciliationRequired}
            />
          ) : null}
          {serverPending && props.onOpenHistory ? (
            <SecondaryButton variant="creative" label="Mở lịch sử để kiểm tra buổi đang xử lý" onPress={props.onOpenHistory} />
          ) : null}
          <Card variant="creative" style={styles.storyCard}>
            <View style={styles.storyHeading}>
              <View style={styles.storyIcon}>
                <Ionicons name="book-outline" size={21} color={palette.creativePrimary} />
              </View>
              <View style={styles.storyHeadingCopy}>
                  <Text style={styles.eyebrow}>{props.confirmed ? 'ĐÃ XÁC NHẬN' : 'BẢN NHÁP'} · {storyLanguageLabel(props.story.language)}</Text>
                <Text style={styles.storyTitle}>{props.story.title}</Text>
              </View>
            </View>
            <View style={styles.storySection}>
              <Text style={styles.storyBody}>{props.story.story.opening}</Text>
              <Text style={styles.storyBody}>{props.story.story.middle}</Text>
              <Text style={styles.storyBody}>{props.story.story.ending}</Text>
            </View>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={detailsVisible ? 'Ẩn thông tin phiên bản' : 'Xem thông tin phiên bản'}
              accessibilityState={{ expanded: detailsVisible }}
              onPress={() => setDetailsVisible((visible) => !visible)}
              style={styles.detailsToggle}
            >
              <Text style={styles.detailsLabel}>Thông tin bản nội dung</Text>
              <Ionicons name={detailsVisible ? 'chevron-up' : 'chevron-down'} size={16} color={palette.creativePrimary} />
            </TouchableOpacity>
            {detailsVisible ? (
              <View style={styles.metadata}>
                <Text style={styles.metadataText}>Phiên bản {props.story.revisionNo ?? 'chưa có'}</Text>
                <Text style={styles.metadataText}>Mã bản: {props.story.revisionId ?? 'chưa có'}</Text>
                <Text selectable style={styles.metadataText}>SHA-256: {props.story.sha256 ?? 'chưa có'}</Text>
              </View>
            ) : null}
          </Card>

          <Card variant="creative" style={styles.scenesCard}>
            <SectionTitle variant="creative">Các cảnh trong câu chuyện</SectionTitle>
            {props.story.scenes.map((scene) => (
              <View key={scene.scene_index} style={styles.scene}>
                <View style={styles.sceneNumber}><Text style={styles.sceneNumberText}>{scene.scene_index}</Text></View>
                <View style={styles.sceneCopy}>
                  <Text style={styles.sceneTitle}>{scene.title}</Text>
                  <Text style={styles.sceneBody}>{scene.action}</Text>
                  <Text style={styles.sceneNarration}>{scene.narration}</Text>
                </View>
              </View>
            ))}
          </Card>

          {!props.confirmed ? (
            <Card variant="creative" style={styles.revisionCard}>
              <SectionTitle variant="creative">Muốn đổi một chi tiết?</SectionTitle>
              <Text style={styles.bodyText}>Thêm gợi ý để tạo bản câu chuyện mới.</Text>
              {props.rewriteCount < 3 ? (
                <>
                  <Field
                    variant="creative"
                    label={`Gợi ý viết lại · còn ${Math.max(0, 3 - props.rewriteCount)}`}
                    value={props.rewriteInstruction}
                    onChangeText={props.onRewriteInstruction}
                    placeholder="Ví dụ: thêm một người bạn mới"
                    multiline
                    editable={props.storyReady && storyCurrent && !props.busy}
                  />
                  <SecondaryButton
                    variant="creative"
                    label="Viết lại câu chuyện"
                    disabled={!props.storyReady || !storyCurrent || !props.rewriteInstruction.trim() || requestPending}
                    onPress={props.onRewrite}
                  />
                </>
              ) : <Notice variant="creative" text="Bạn đã dùng hết số lần viết lại cho câu chuyện này." tone="info" />}
              <PrimaryButton
                variant="creative"
                label="Xác nhận câu chuyện này"
                disabled={requestPending || !props.storyReady || !storyCurrent || !props.canConfirm || !props.story.revisionId || !props.story.sha256}
                onPress={props.onConfirm}
              />
            </Card>
          ) : (
            <Notice variant="creative" text="Câu chuyện này đã được người lớn xác nhận." tone="success" />
          )}
        </>
      )}

      {props.story && storyCurrent && props.confirmed && props.onOpenVideo ? (
        <Card variant="creative" style={styles.videoCard}>
          <SectionTitle variant="creative">Video từ tranh của bé</SectionTitle>
          <Notice
            variant="creative"
            text={currentVideoCandidate?.state === 'CANDIDATE_READY'
              ? 'Đã có bản xem thử kỹ thuật. Bản này chưa qua kiểm tra an toàn và chưa phải video hoàn tất.'
              : videoStateMessage}
            tone={currentVideoCandidate?.state === 'CANDIDATE_READY' ? 'success' : props.jobStage.state === 'failed' ? 'warning' : 'info'}
          />
          <SecondaryButton
            variant="creative"
            label={currentVideoCandidate ? 'Mở trạng thái video' : 'Tạo video xem thử'}
            disabled={props.videoCapability.state === 'unavailable'}
            onPress={props.onOpenVideo}
          />
        </Card>
      ) : null}
    </ScreenFrame>
  );
}

function storyBusyTitle(operation: StoryBusyOperation | undefined, serverPending = false, reconciliationRequired = false): string {
  if (reconciliationRequired) return 'Chưa xác nhận được kết quả';
  if (serverPending) return 'Máy chủ đang tạo câu chuyện';
  if (operation === 'rewriting') return 'Đang viết bản mới theo góp ý';
  if (operation === 'confirming') return 'Đang lưu xác nhận';
  return 'Đang tạo câu chuyện từ tranh';
}

function storyBusyDescription(operation: StoryBusyOperation | undefined, serverPending = false, reconciliationRequired = false): string {
  if (reconciliationRequired) return 'Máy chủ chưa xác nhận Modal đã nhận yêu cầu hay chưa. Ứng dụng đã dừng chờ và sẽ không tự gửi lại.';
  if (serverPending) return 'Máy chủ đang xử lý yêu cầu. Ứng dụng sẽ cập nhật khi nhận được kết quả chính thức.';
  if (operation === 'rewriting') return 'AI đang dùng gợi ý của người lớn để tạo một bản nháp mới.';
  if (operation === 'confirming') return 'Đang lưu đúng phiên bản kịch bản đã được người lớn duyệt.';
  return 'AI đang dựa trên tranh, chủ thể đã xác nhận và hoạt động đã chọn để viết bản nháp.';
}

function storyBusyStatusLabel(operation: StoryBusyOperation | undefined, serverPending = false, reconciliationRequired = false): string {
  if (reconciliationRequired) return 'Cần kiểm tra trạng thái';
  if (serverPending) return 'Đang chờ kết quả máy chủ';
  if (operation === 'rewriting') return 'Đang viết bản mới';
  if (operation === 'confirming') return 'Đang lưu bản đã duyệt';
  return 'Đang tạo bản nháp';
}

function storyLoadingNote(reconciliationRequired: boolean): string {
  return reconciliationRequired
    ? 'Mở lịch sử để xem trạng thái mới nhất. Không gửi lại lượt này để tránh tạo yêu cầu trùng.'
    : 'Bạn có thể quay lại sau; ứng dụng sẽ cập nhật khi máy chủ có kết quả.';
}

function StoryIllustration(): React.JSX.Element {
  return (
    <View style={styles.illustrationCanvas}>
      <View style={styles.illustrationGlow} />
      <View style={styles.bookBack} />
      <View style={styles.bookPage}>
        <View style={styles.bookSun} />
        <View style={styles.bookLineLong} />
        <View style={styles.bookLineShort} />
        <View style={styles.bookHill} />
      </View>
      <View style={styles.sparkleTop}><Ionicons name="sparkles" size={19} color="#E8A900" /></View>
      <View style={styles.storyIconTile}><Ionicons name="book" size={29} color="#FFFFFF" /></View>
    </View>
  );
}

const styles = StyleSheet.create({
  generationCard: { gap: 13 },
  storyArtwork: { width: '100%', aspectRatio: 1.55, borderRadius: 20, overflow: 'hidden' },
  generationCopy: { gap: 8, paddingHorizontal: 2 },
  eyebrow: { color: palette.creativePrimary, fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.5 },
  bodyText: { color: palette.creativeMuted, fontSize: 13, lineHeight: 19 },
  storyCard: { gap: 13 },
  storyHeading: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  storyIcon: { width: 42, height: 42, borderRadius: 15, backgroundColor: palette.creativeLavender, alignItems: 'center', justifyContent: 'center' },
  storyHeadingCopy: { flex: 1, minWidth: 0, gap: 4 },
  storyTitle: { color: palette.creativeInk, fontSize: 19, lineHeight: 25, fontWeight: '800', flexShrink: 1 },
  storySection: { gap: 11, borderRadius: 17, padding: 13, backgroundColor: '#FBF8FF' },
  storyBody: { color: palette.creativeInk, fontSize: 14, lineHeight: 22 },
  detailsToggle: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 3 },
  detailsLabel: { color: palette.creativePrimary, fontSize: 12, lineHeight: 17, fontWeight: '700' },
  metadata: { gap: 5, padding: 11, borderRadius: 13, backgroundColor: '#F7F0FF' },
  metadataText: { color: palette.creativeMuted, fontSize: 10, lineHeight: 15 },
  scenesCard: { gap: 12 },
  scene: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#EEE5F8' },
  sceneNumber: { width: 26, height: 26, borderRadius: 9, backgroundColor: palette.creativeLavender, alignItems: 'center', justifyContent: 'center' },
  sceneNumberText: { color: palette.creativePrimary, fontSize: 11, lineHeight: 15, fontWeight: '800' },
  sceneCopy: { flex: 1, minWidth: 0, gap: 5 },
  sceneTitle: { color: palette.creativeInk, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  sceneBody: { color: palette.creativeInk, fontSize: 12, lineHeight: 17 },
  sceneNarration: { color: palette.creativeMuted, fontSize: 12, lineHeight: 17, fontStyle: 'italic' },
  revisionCard: { gap: 12 },
  videoCard: { gap: 10 },
  illustrationCanvas: { flex: 1, backgroundColor: '#F2E9FF', alignItems: 'center', justifyContent: 'center' },
  illustrationGlow: { position: 'absolute', width: 170, height: 170, borderRadius: 85, backgroundColor: '#E4D2FF', opacity: 0.85 },
  bookBack: { position: 'absolute', width: 100, height: 112, borderRadius: 12, backgroundColor: '#8D54D8', transform: [{ rotate: '8deg' }], marginLeft: 28, marginTop: 8 },
  bookPage: { width: 98, height: 108, borderRadius: 10, backgroundColor: '#FFFEFF', borderWidth: 1.5, borderColor: '#DCC8F2', transform: [{ rotate: '-8deg' }], overflow: 'hidden' },
  bookSun: { position: 'absolute', right: 17, top: 18, width: 15, height: 15, borderRadius: 8, backgroundColor: '#FFD77A' },
  bookLineLong: { position: 'absolute', top: 50, left: 16, width: 58, height: 5, borderRadius: 3, backgroundColor: '#B79BE5' },
  bookLineShort: { position: 'absolute', top: 61, left: 16, width: 42, height: 5, borderRadius: 3, backgroundColor: '#D0C0ED' },
  bookHill: { position: 'absolute', bottom: -17, left: 3, width: 100, height: 46, borderRadius: 30, backgroundColor: '#C5EADD' },
  sparkleTop: { position: 'absolute', top: '18%', right: '25%' },
  storyIconTile: { position: 'absolute', right: '26%', bottom: '19%', width: 48, height: 48, borderRadius: 17, backgroundColor: palette.creativePrimary, alignItems: 'center', justifyContent: 'center' },
});

function storyLanguageLabel(language: string): string {
  const normalized = language.trim().toLowerCase();
  if (normalized === 'vi' || normalized === 'vi-vn' || normalized === 'vietnamese') return 'Tiếng Việt';
  if (normalized === 'en' || normalized === 'en-us' || normalized === 'english') return 'Tiếng Anh';
  return 'Ngôn ngữ khác';
}

function jobStageMessage(stage: ParentJobStageState): string {
  if (stage.state === 'idle') return 'Chưa có tác vụ video.';
  if (stage.state === 'pending') return 'Video đang được xử lý.';
  if (stage.state === 'reconciling') return 'Đang kiểm tra trạng thái video.';
  if (stage.state === 'confirmed') return 'Máy chủ xác nhận tác vụ video hoàn tất.';
  if (stage.state === 'failed') return 'Tác vụ video thất bại.';
  return 'Trạng thái tác vụ video chưa khả dụng.';
}
