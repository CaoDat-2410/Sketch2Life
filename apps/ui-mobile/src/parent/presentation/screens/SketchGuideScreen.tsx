import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import type { SvgTopicStrokeGuideSourceDraftV1 } from '../../domain/svgGuide';
import { isSafeSvgTopicStrokeGuideSourceDraft } from '../../domain/svgGuide';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, palette } from '../components/ui';
import { ParentAiLoadingState } from '../components/ParentAiLoadingState';
import { ProgressiveSvgGuide } from '../components/ProgressiveSvgGuide';

type Props = Readonly<{
  topic: string;
  draft: SvgTopicStrokeGuideSourceDraftV1 | null;
  busy: boolean;
  error: string;
  onContinue: () => void;
  onSkip: () => void;
  onBack: () => void;
}>;

export function SketchGuideScreen(props: Props): React.JSX.Element {
  const [stageIndex, setStageIndex] = useState(0);
  const [adultApproved, setAdultApproved] = useState(false);
  const validDraft = props.draft && isSafeSvgTopicStrokeGuideSourceDraft(props.draft) ? props.draft : null;
  const stage = validDraft?.guide.stages[stageIndex] ?? null;
  const stageCount = validDraft?.guide.stages.length ?? 0;

  useEffect(() => {
    setStageIndex(0);
    setAdultApproved(false);
  }, [props.topic, props.draft?.request_id]);

  return <ScreenFrame title="Gợi ý nét vẽ" subtitle="Người lớn xem bản nháp trước khi tiếp tục." step="Tùy chọn" onBack={props.onBack} visualTone="creative">
    {props.busy ? <ParentAiLoadingState
      title="Đang tải hướng dẫn nét vẽ"
      description="Chỉ chủ đề và đối tượng vẽ được gửi đến máy chủ."
      note="Ảnh tranh, hồ sơ và thông tin của trẻ không được gửi trong yêu cầu này."
      testID="parent-sketch-guide-loading"
    /> : null}
    {props.error ? <Notice variant="creative" text={props.error} tone="warning" /> : null}
    {props.draft && !validDraft ? <Notice
      variant="creative"
      text="Hướng dẫn chưa qua kiểm tra hiển thị an toàn. Bạn có thể tiếp tục chụp tranh mà không cần gợi ý."
      tone="error"
    /> : null}
    {validDraft && stage ? <Card variant="creative" style={{ gap: 12 }}>
      <View style={{ borderRadius: 12, backgroundColor: '#FFF7E6', padding: 12 }}>
        <Text style={{ color: '#8A4B08', fontWeight: '800' }}>Bản nháp riêng tư · người lớn xem trước</Text>
        <Text style={{ color: '#765226', lineHeight: 19, marginTop: 4 }}>
          Hướng dẫn chưa được lưu. Hãy kiểm tra từng bước trước khi cho trẻ xem.
        </Text>
        <Text style={{ color: '#765226', lineHeight: 18, marginTop: 6 }}>
          Nguồn: {validDraft.reference_source.dataset_name} · {validDraft.reference_source.license_id}
        </Text>
      </View>
      <Text style={{ color: palette.creativeInk, fontSize: 18, fontWeight: '800', textAlign: 'center' }}>
        {validDraft.guide.title_vi}
      </Text>
      <Text style={{ color: palette.creativeMuted, lineHeight: 21, textAlign: 'center' }}>
        {`Bước ${stageIndex + 1} / ${stageCount} · ${stage.instruction_vi}`}
      </Text>
      <ProgressiveSvgGuide document={validDraft.document} guide={validDraft.guide} stageIndex={stageIndex} />
      <View style={{ flexDirection: 'row', gap: 8 }}>
        <SecondaryButton
          variant="creative"
          label="Bước trước"
          disabled={stageIndex === 0}
          onPress={() => setStageIndex((index) => Math.max(0, index - 1))}
        />
        {stageIndex < stageCount - 1
          ? <PrimaryButton
            variant="creative"
            label="Bước tiếp"
            onPress={() => setStageIndex((index) => Math.min(stageCount - 1, index + 1))}
          />
          : adultApproved
            ? <PrimaryButton variant="creative" label="Tiếp tục chụp tranh" onPress={props.onContinue} />
            : <PrimaryButton variant="creative" label="Duyệt bản nháp" onPress={() => setAdultApproved(true)} />}
      </View>
    </Card> : null}
    {!validDraft && !props.busy && !props.error ? <Card variant="creative">
      <Text style={{ color: palette.creativeInk, fontSize: 17, fontWeight: '800' }}>Không có hướng dẫn để hiển thị</Text>
      <Text style={{ color: palette.creativeMuted, lineHeight: 21, marginTop: 8 }}>
        Hướng dẫn là tùy chọn. Bạn vẫn có thể chụp tranh và tiếp tục buổi học.
      </Text>
    </Card> : null}
    <SecondaryButton variant="creative" label="Bỏ qua · chụp tranh" onPress={props.onSkip} />
  </ScreenFrame>;
}
