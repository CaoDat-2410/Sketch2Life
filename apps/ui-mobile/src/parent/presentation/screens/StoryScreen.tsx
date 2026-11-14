import React from 'react';
import { Text, View } from 'react-native';
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
    <ScreenFrame title="Câu chuyện từ bức vẽ" subtitle="Đọc lại nội dung. Bạn có thể gửi gợi ý viết lại, không sửa trực tiếp từng cảnh." step={props.stepLabel} onBack={props.onBack}>
      <Notice text="Hoạt động chính: chưa khả dụng. Kịch bản vẫn có thể tiếp tục mà không gắn hoạt động." tone="warning" />
      <Notice text={videoStateMessage} tone="warning" />
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.story ? <Card><Text style={{ color: palette.muted, fontSize: 14, lineHeight: 21 }}>Kịch bản được cá nhân hóa theo tranh và chủ thể đã xác nhận.</Text>{props.attempted ? <>
        <Notice text="Yêu cầu chưa có kết quả hiển thị. Không tự gửi lại; bạn có thể chọn gửi lại cùng yêu cầu." tone="warning" />
        <SecondaryButton label="Gửi lại cùng yêu cầu" disabled={props.busy} onPress={props.onRetry} />
      </> : <PrimaryButton label="Tạo kịch bản bằng AI" busy={props.busy} onPress={props.onGenerate} />}</Card> : (
        <>
          <Card>
            <Text style={{ color: palette.blue, fontSize: 12, fontWeight: '800' }}>BẢN NHÁP · {props.story.language.toUpperCase()}</Text>
            <Text style={{ color: palette.ink, fontSize: 22, lineHeight: 28, fontWeight: '800' }}>{props.story.title}</Text>
            <Text style={{ color: palette.muted, fontSize: 12, lineHeight: 18 }}>Mã phiên bản: {props.story.revisionId ?? 'chưa có'}</Text>
            <Text style={{ color: palette.muted, fontSize: 12, lineHeight: 18 }}>Số phiên bản: {props.story.revisionNo ?? 'chưa có'}</Text>
            <Text selectable style={{ color: palette.muted, fontSize: 12, lineHeight: 18 }}>
              SHA-256: {props.story.sha256 ?? 'chưa có'}
            </Text>
            <Text style={{ color: palette.ink, fontSize: 15, lineHeight: 23 }}>{props.story.story.opening}</Text>
            <Text style={{ color: palette.ink, fontSize: 15, lineHeight: 23 }}>{props.story.story.middle}</Text>
            <Text style={{ color: palette.ink, fontSize: 15, lineHeight: 23 }}>{props.story.story.ending}</Text>
          </Card>
          <Card>
            <SectionTitle>Các cảnh</SectionTitle>
            {props.story.scenes.map((scene) => (
              <View key={scene.scene_index} style={{ borderTopWidth: 1, borderTopColor: '#E7EDF4', paddingTop: 10, gap: 4 }}>
                <Text style={{ color: palette.blue, fontSize: 12, fontWeight: '800' }}>CẢNH {scene.scene_index} · {scene.title}</Text>
                <Text style={{ color: palette.ink, fontSize: 13, lineHeight: 19 }}>{scene.action}</Text>
                <Text style={{ color: palette.muted, fontSize: 13, lineHeight: 19 }}>{scene.narration}</Text>
              </View>
            ))}
          </Card>
          {!props.confirmed ? <Card>
            <Field label={`Gợi ý viết lại (còn ${Math.max(0, 3 - props.rewriteCount)} lần)`} value={props.rewriteInstruction} onChangeText={props.onRewriteInstruction} placeholder="Ví dụ: kể chậm hơn, thêm chi tiết về cánh bướm…" multiline editable={props.rewriteCount < 3 && !props.busy} />
            {props.rewriteCount < 3 ? <SecondaryButton label="Gửi gợi ý viết lại" disabled={!props.rewriteInstruction.trim() || props.busy} onPress={props.onRewrite} /> : null}
            <Notice text="Người lớn xem lại và xác nhận kịch bản cuối để hoàn tất bước này." />
            <PrimaryButton label="Xác nhận kịch bản này" busy={props.busy} disabled={!props.canConfirm || !props.story.revisionId || !props.story.sha256} onPress={props.onConfirm} />
          </Card> : <Notice text="Kịch bản đã được người lớn xác nhận." tone="success" />}
        </>
      )}
    </ScreenFrame>
  );
}

function jobStageMessage(stage: ParentJobStageState): string {
  if (stage.state === 'idle') return 'Chưa có tác vụ video.';
  if (stage.state === 'pending') return 'Tác vụ video đang chờ xử lý; trạng thái chưa phải kết quả hoàn tất.';
  if (stage.state === 'reconciling') return 'Đang kiểm tra trạng thái tác vụ video. Không gửi yêu cầu trùng lặp.';
  if (stage.state === 'confirmed') return 'Máy chủ đã xác nhận tác vụ video hoàn tất; chưa có trình phát được nối.';
  if (stage.state === 'failed') return 'Tác vụ video thất bại theo trạng thái máy chủ.';
  return 'Trạng thái tác vụ video chưa khả dụng.';
}
