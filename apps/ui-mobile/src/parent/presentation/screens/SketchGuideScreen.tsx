import React, { useEffect, useState } from 'react';
import { Linking, Text, View } from 'react-native';
import type {
  ParentSvgGuidePageV1,
  ProgressiveStrokeGuideV1,
  SvgDocumentV1,
  SvgTopicStrokeGuideDraftV1,
} from '../../domain/svgGuide';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, palette } from '../components/ui';
import { ProgressiveSvgGuide } from '../components/ProgressiveSvgGuide';

type Props = {
  topic: string;
  layout: ParentSvgGuidePageV1 | null;
  draft: SvgTopicStrokeGuideDraftV1 | null;
  catalogChecked: boolean;
  busy: boolean;
  error: string;
  onFindCatalog: () => void;
  onGenerateDraft: () => void;
  onSkip: () => void;
  onBack: () => void;
};

export function SketchGuideScreen(props: Props): React.JSX.Element {
  const [stageIndex, setStageIndex] = useState(0);
  const [selectedId, setSelectedId] = useState('');
  const [draftAccepted, setDraftAccepted] = useState(false);
  const items = props.layout?.items ?? [];
  const selected = items.find((item) => item.catalog_entry_id === selectedId) ?? items[0] ?? null;
  const guide = (props.draft?.guide ?? selected?.guide ?? null) as ProgressiveStrokeGuideV1 | null;
  const document = (props.draft?.document ?? selected?.document ?? null) as SvgDocumentV1 | null;
  const referenceDraft = props.draft?.contract === 'SvgTopicStrokeGuideSourceDraftV1'
    || props.draft?.contract === 'SvgTopicStrokeGuideConstructionDraftV1'
    ? props.draft
    : null;
  const referenceIllustration = referenceDraft?.reference_illustration;
  const sourceExactPathSequence = props.draft?.contract === 'SvgTopicStrokeGuideSourceDraftV1'
    && (
      props.draft.derivation.method === 'EXACT_SOURCE_PATH_SEQUENCE_V7'
      || props.draft.derivation.method === 'OPENMOJI_SOURCE_SHAPE_TO_PATH_V1'
      || props.draft.derivation.method === 'OPENCLIPART_SOURCE_CONTOUR_TO_DRAW_PATH_V1'
      || props.draft.derivation.method === 'QWEN_OPENCLIPART_SOURCE_PATH_SEQUENCE_V1'
    );
  const isDraft = props.draft !== null;
  const stage = guide?.stages[stageIndex] ?? null;
  const stageCount = guide?.stages.length ?? 0;
  const guideValid = Boolean(
    document
    && (guide?.schema_version === 'SketchStrokeGuideV3' || guide?.schema_version === 'SvgTopicStrokeGuideV1')
    && stageCount >= 4
    && stageCount <= 8
    && stage
    && document.schema_version === 'SvgDocumentV1',
  );

  useEffect(() => {
    setStageIndex(0);
    setSelectedId('');
    setDraftAccepted(false);
  }, [props.topic, props.layout, props.draft?.request_id]);

  const title = props.draft?.guide.title_vi || selected?.title_vi || props.topic || 'Gợi ý nét vẽ';
  const showFinalReferenceAlongside = Boolean(referenceIllustration && stageIndex === stageCount - 1);
  const referenceSource = referenceDraft?.reference_source ?? null;
  const stageLabel = stage?.part_ids
    .map((partId) => guide?.parts.find((part) => part.part_id === partId)?.label_vi)
    .filter((label): label is string => Boolean(label))
    .join(' · ');

  return (
    <ScreenFrame title="Gợi ý nét vẽ" subtitle="Nét vẽ hiện dần theo từng bước" step="Tùy chọn" onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {items.length > 1 ? <Card>
        <Text style={{ color: palette.ink, fontSize: 15, fontWeight: '800', marginBottom: 10 }}>Chọn mẫu đã duyệt</Text>
        <View style={{ gap: 8 }}>
          {items.map((item) => {
            const active = item.catalog_entry_id === selected?.catalog_entry_id;
            return <SecondaryButton
              key={item.catalog_entry_id}
              label={`${active ? '✓ ' : ''}${item.title_vi}`}
              onPress={() => { setSelectedId(item.catalog_entry_id); setStageIndex(0); }}
            />;
          })}
        </View>
      </Card> : null}
      {guideValid && document && guide && stage ? <Card>
        {isDraft ? <View style={{ borderRadius: 12, backgroundColor: '#FFF7E6', padding: 12, marginBottom: 12 }}>
          <Text style={{ color: '#8A4B08', fontWeight: '800' }}>
            {draftAccepted
              ? 'Đã duyệt · trẻ có thể xem'
              : props.draft?.contract === 'SvgTopicStrokeGuideConstructionDraftV1'
                ? 'AI dựng lại nét từ hình mẫu · người lớn xem trước'
                : props.draft?.contract === 'SvgTopicStrokeGuideSourceDraftV1'
                ? props.draft.generation_source === 'QWEN_SOURCE_PATH_DERIVATION'
                  ? 'AI sắp thứ tự nét từ SVG nguồn · người lớn xem trước'
                  : 'Bản nháp từ SVG nguồn · người lớn xem trước'
                : 'Bản nháp AI · người lớn xem trước'}
          </Text>
          <Text style={{ color: '#765226', lineHeight: 20, marginTop: 4 }}>
            Chỉ dùng bản nháp sau khi người lớn kiểm tra hình và thứ tự nét.
          </Text>
          {props.draft?.reference_source ? <Text style={{ color: '#765226', lineHeight: 18, marginTop: 6 }}>
            Tham chiếu: {props.draft.reference_source.dataset_name} · {props.draft.reference_source.license_id}
          </Text> : null}
        </View> : null}
        <Text style={{ color: palette.ink, fontSize: 18, fontWeight: '800', textAlign: 'center' }}>{title}</Text>
        {stageLabel ? <Text style={{
          color: palette.blue,
          fontWeight: '800',
          textAlign: 'center',
          marginTop: 8,
        }}>{stageLabel}</Text> : null}
        <Text style={{ color: palette.muted, textAlign: 'center', lineHeight: 21, marginTop: 6 }}>
          {`Bước ${stageIndex + 1} / ${stageCount} · ${stage.instruction_vi}`}
        </Text>
        <View style={{ marginTop: 16, marginBottom: 12 }}>
          <ProgressiveSvgGuide
            document={document}
            referenceIllustration={referenceIllustration}
            showFinalReferenceAlongside={showFinalReferenceAlongside}
            sourceExactPathSequence={sourceExactPathSequence}
            guide={guide}
            stageIndex={stageIndex}
          />
        </View>
        {showFinalReferenceAlongside && referenceSource ? <Text style={{
          color: palette.muted,
          fontSize: 11,
          lineHeight: 16,
          textAlign: 'center',
          marginTop: -2,
          marginBottom: 12,
        }}>
          Nét vẽ chuyển từ SVG <Text
            accessibilityRole="link"
            onPress={() => { if (referenceSource.dataset_uri) void Linking.openURL(referenceSource.dataset_uri); }}
            style={{ color: palette.blue, textDecorationLine: 'underline' }}
          >{referenceSource.dataset_name}</Text>
          {' · Màu gốc: '}
          <Text
            accessibilityRole="link"
            onPress={() => { if (referenceSource.dataset_uri) void Linking.openURL(referenceSource.dataset_uri); }}
            style={{ color: palette.blue, textDecorationLine: 'underline' }}
          >{referenceSource.dataset_name}</Text>
          {' · '}
          <Text
            accessibilityRole="link"
            onPress={() => { void Linking.openURL(referenceSource.license_uri); }}
            style={{ color: palette.blue, textDecorationLine: 'underline' }}
          >{referenceSource.license_id === 'CC-BY-SA-4.0' ? 'CC BY-SA 4.0' : referenceSource.license_id}</Text>
        </Text> : null}
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <SecondaryButton label="Bước trước" disabled={stageIndex === 0} onPress={() => setStageIndex((index) => Math.max(0, index - 1))} />
          {stageIndex < stageCount - 1
            ? <PrimaryButton label="Bước tiếp" onPress={() => setStageIndex((index) => Math.min(stageCount - 1, index + 1))} />
            : <PrimaryButton label={isDraft && !draftAccepted ? 'Duyệt · cho trẻ xem' : 'Xong · chụp tranh'} onPress={() => {
              if (isDraft && !draftAccepted) setDraftAccepted(true);
              else props.onSkip();
            }} />}
        </View>
      </Card> : <Card>
        <Text style={{ color: palette.ink, fontSize: 17, fontWeight: '800' }}>
          {props.busy
            ? 'Đang tìm hướng dẫn…'
            : props.catalogChecked
              ? props.error ? 'Chưa tải được mẫu đã duyệt' : 'Chưa có mẫu đã duyệt'
              : 'Tìm hướng dẫn có sẵn'}
        </Text>
        <Text style={{ color: palette.muted, lineHeight: 21, marginTop: 8 }}>
          {!props.catalogChecked
            ? 'Ưu tiên mẫu SVG đã được duyệt. Bạn vẫn có thể bỏ qua và chụp tranh.'
            : props.error
              ? 'Thư viện chưa phản hồi. Bạn có thể thử tạo gợi ý nét vẽ hoặc bỏ qua để chụp tranh.'
            : props.topic
              ? `Chưa có mẫu cho “${props.topic}”. Người lớn có thể tạo bản nháp gợi ý nét vẽ.`
              : 'Chọn chủ đề trước nếu muốn tạo gợi ý nét vẽ.'}
        </Text>
        {!props.catalogChecked
          ? <PrimaryButton label="Tìm mẫu đã duyệt" busy={props.busy} onPress={props.onFindCatalog} />
          : props.topic && !props.draft
            ? <PrimaryButton label="Tạo gợi ý nét vẽ" busy={props.busy} onPress={props.onGenerateDraft} />
            : null}
      </Card>}
      <SecondaryButton label="Bỏ qua · chụp tranh" onPress={props.onSkip} />
    </ScreenFrame>
  );
}
