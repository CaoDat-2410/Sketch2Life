import React from 'react';
import { Text, View } from 'react-native';
import type { StoryDraft } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, SecondaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
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
  return (
    <ScreenFrame title="Câu chuyện từ bức vẽ" subtitle="Đọc lại nội dung. Bạn có thể gửi gợi ý viết lại, không sửa trực tiếp từng cảnh." step={props.stepLabel} onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.story ? <Card><Text style={{ color: palette.muted, fontSize: 14, lineHeight: 21 }}>Kịch bản được cá nhân hóa theo tranh và chủ thể đã xác nhận.</Text>{props.attempted ? <>
        <Notice text="Yêu cầu chưa có kết quả hiển thị. Không tự gửi lại; bạn có thể chọn gửi lại cùng yêu cầu." tone="warning" />
        <SecondaryButton label="Gửi lại cùng yêu cầu" disabled={props.busy} onPress={props.onRetry} />
      </> : <PrimaryButton label="Tạo kịch bản bằng AI" busy={props.busy} onPress={props.onGenerate} />}</Card> : (
        <>
          <Card>
            <Text style={{ color: palette.blue, fontSize: 12, fontWeight: '800' }}>BẢN NHÁP · {props.story.language.toUpperCase()}</Text>
            <Text style={{ color: palette.ink, fontSize: 22, lineHeight: 28, fontWeight: '800' }}>{props.story.title}</Text>
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
            <PrimaryButton label="Xác nhận kịch bản này" busy={props.busy} disabled={!props.canConfirm} onPress={props.onConfirm} />
          </Card> : <Notice text="Kịch bản đã được người lớn xác nhận." tone="success" />}
        </>
      )}
    </ScreenFrame>
  );
}
