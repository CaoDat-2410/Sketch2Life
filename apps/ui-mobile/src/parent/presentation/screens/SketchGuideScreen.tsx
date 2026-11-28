import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';
import type { SvgGuideCatalogItemV1, SvgTopicStrokeGuideSourceDraftV1 } from '../../domain/svgGuide';
import {
  isSafeSvgGuideCatalogItem,
  isSafeSvgTopicStrokeGuideSourceDraft,
  svgGuideCatalogAttribution,
} from '../../domain/svgGuide';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, palette } from '../components/ui';
import { ParentAiLoadingState } from '../components/ParentAiLoadingState';
import { ProgressiveSvgGuide } from '../components/ProgressiveSvgGuide';

type Props = Readonly<{
  topic: string;
  draft: SvgTopicStrokeGuideSourceDraftV1 | null;
  catalogGuides: SvgGuideCatalogItemV1[];
  selectedCatalogGuide: SvgGuideCatalogItemV1 | null;
  catalogGuidePickerOpen: boolean;
  catalogGuidesLoading: boolean;
  catalogGuidesError: string;
  canCreateGuide: boolean;
  busy: boolean;
  error: string;
  onLoadCatalogGuides: () => void;
  onChooseCatalogGuide: (guide: SvgGuideCatalogItemV1) => void;
  onCreateGuide: () => void;
  onContinue: () => void;
  onSkip: () => void;
  showSkip: boolean;
  skipLabel: string;
  onBack: () => void;
}>;

export function SketchGuideScreen(props: Props): React.JSX.Element {
  const [stageIndex, setStageIndex] = useState(0);
  const [adultApproved, setAdultApproved] = useState(false);
  const validDraft = props.draft && isSafeSvgTopicStrokeGuideSourceDraft(props.draft) ? props.draft : null;
  const validCatalogGuide = props.selectedCatalogGuide && isSafeSvgGuideCatalogItem(props.selectedCatalogGuide)
    ? props.selectedCatalogGuide
    : null;
  const stage = validDraft?.guide.stages[stageIndex] ?? null;
  const stageCount = validDraft?.guide.stages.length ?? 0;
  const catalogStage = validCatalogGuide?.guide.stages[stageIndex] ?? null;
  const catalogStageCount = validCatalogGuide?.guide.stages.length ?? 0;

  useEffect(() => {
    setStageIndex(0);
    setAdultApproved(false);
  }, [props.topic, props.draft?.request_id, props.selectedCatalogGuide?.guide_revision_id]);

  return <ScreenFrame
    title="Gợi ý nét vẽ"
    subtitle={validCatalogGuide
      ? 'Hướng dẫn đã được tuyển chọn và duyệt.'
      : props.catalogGuidePickerOpen && !validDraft
        ? 'Hướng dẫn có sẵn.'
        : 'Người lớn xem bản nháp riêng tư trước khi tiếp tục.'}
    step="Tùy chọn"
    onBack={props.onBack}
    visualTone="creative"
  >
    <Card variant="creative" style={{ gap: 10 }}>
      <Text style={{ color: palette.creativeInk, fontSize: 17, fontWeight: '800' }}>Hướng dẫn có sẵn</Text>
      {props.catalogGuidesLoading ? <View style={{ alignItems: 'center', flexDirection: 'row', gap: 9 }}>
        <ActivityIndicator color={palette.creativeInk} />
        <Text style={{ color: palette.creativeMuted }}>Đang tải hướng dẫn…</Text>
      </View> : null}
      {props.catalogGuidesError ? <Notice
        variant="creative"
        text={`Chưa có hướng dẫn có sẵn. ${props.catalogGuidesError}`}
        tone="warning"
      /> : null}
      {!props.catalogGuidesLoading && !props.catalogGuidesError && props.catalogGuides.length === 0 ? (
        <Text style={{ color: palette.creativeMuted, lineHeight: 21 }}>Chưa có hướng dẫn có sẵn.</Text>
      ) : null}
      {props.catalogGuides.map((guide) => {
        const selected = validCatalogGuide?.guide_revision_id === guide.guide_revision_id;
        return <Pressable
          key={guide.guide_revision_id}
          accessibilityRole="button"
          accessibilityLabel={`${guide.alt_text_vi}, ${guide.guide.stages.length} bước`}
          accessibilityState={{ selected }}
          onPress={() => props.onChooseCatalogGuide(guide)}
          style={({ pressed }) => ({
            backgroundColor: selected ? '#EFE4FF' : '#FFFDFC',
            borderColor: selected ? '#B89AE2' : '#E8DDF0',
            borderRadius: 14,
            borderWidth: 1,
            gap: 3,
            opacity: pressed ? 0.8 : 1,
            padding: 12,
          })}
        >
          <Text style={{ color: palette.creativeInk, fontWeight: '800', lineHeight: 20 }}>{guide.title_vi}</Text>
          <Text style={{ color: palette.creativeMuted, lineHeight: 18 }}>
            {`${guide.guide.stages.length} bước`}
          </Text>
        </Pressable>;
      })}
      {props.canCreateGuide ? <Text style={{ color: palette.creativeMuted, lineHeight: 19 }}>
        Bản nháp AI chỉ được tạo khi người lớn yêu cầu.
      </Text> : null}
      {props.canCreateGuide ? <SecondaryButton
        variant="creative"
        label="Tạo hướng dẫn bằng AI"
        disabled={props.busy}
        onPress={props.onCreateGuide}
      /> : null}
      {props.catalogGuidesError ? <SecondaryButton
        variant="creative"
        label="Thử tải lại"
        disabled={props.catalogGuidesLoading}
        onPress={props.onLoadCatalogGuides}
      /> : null}
    </Card>
    {props.busy ? <ParentAiLoadingState
      title="Đang tải hướng dẫn nét vẽ"
      description="Chỉ chủ đề và đối tượng vẽ được gửi đến máy chủ."
      note="Ảnh tranh, hồ sơ và thông tin của trẻ không được gửi trong yêu cầu này."
      testID="parent-sketch-guide-loading"
    /> : null}
    {props.error ? <Notice variant="creative" text={props.error} tone="warning" /> : null}
    {props.selectedCatalogGuide && !validCatalogGuide ? <Notice
      variant="creative"
      text="Hướng dẫn có sẵn chưa qua kiểm tra hiển thị an toàn."
      tone="error"
    /> : null}
    {props.draft && !validDraft && !props.selectedCatalogGuide ? <Notice
      variant="creative"
      text="Hướng dẫn chưa qua kiểm tra hiển thị an toàn. Bạn có thể tiếp tục chụp tranh mà không cần gợi ý."
      tone="error"
    /> : null}
    {validCatalogGuide && catalogStage ? <Card variant="creative" style={{ gap: 12 }}>
      <Text style={{ color: palette.creativeInk, fontSize: 18, fontWeight: '800', textAlign: 'center' }}>
        {validCatalogGuide.guide.title_vi}
      </Text>
      <Text style={{ color: palette.creativeMuted, lineHeight: 18, textAlign: 'center' }}>
        {svgGuideCatalogAttribution(validCatalogGuide)}
      </Text>
      <Text style={{ color: palette.creativeMuted, lineHeight: 21, textAlign: 'center' }}>
        {`Bước ${stageIndex + 1} / ${catalogStageCount} · ${catalogStage.instruction_vi}`}
      </Text>
      <ProgressiveSvgGuide document={validCatalogGuide.document} guide={validCatalogGuide.guide} stageIndex={stageIndex} />
      <View style={{ flexDirection: 'row', gap: 8 }}>
        <SecondaryButton
          variant="creative"
          label="Bước trước"
          disabled={stageIndex === 0}
          onPress={() => setStageIndex((index) => Math.max(0, index - 1))}
        />
        {stageIndex < catalogStageCount - 1
          ? <PrimaryButton
            variant="creative"
            label="Bước tiếp"
            onPress={() => setStageIndex((index) => Math.min(catalogStageCount - 1, index + 1))}
          />
          : <PrimaryButton variant="creative" label="Tiếp tục chụp tranh" onPress={props.onContinue} />}
      </View>
    </Card> : null}
    {!validCatalogGuide && validDraft && stage ? <Card variant="creative" style={{ gap: 12 }}>
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
    {!validCatalogGuide && !validDraft && !props.busy && !props.error ? <Card variant="creative">
      <Text style={{ color: palette.creativeInk, fontSize: 17, fontWeight: '800' }}>Không có hướng dẫn để hiển thị</Text>
      <Text style={{ color: palette.creativeMuted, lineHeight: 21, marginTop: 8 }}>
        Hướng dẫn là tùy chọn. Bạn vẫn có thể chụp tranh và tiếp tục buổi học.
      </Text>
    </Card> : null}
    {props.showSkip ? <SecondaryButton variant="creative" label={props.skipLabel} onPress={props.onSkip} /> : null}
  </ScreenFrame>;
}
