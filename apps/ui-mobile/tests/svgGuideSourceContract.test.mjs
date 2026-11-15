import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const domainSource = readFileSync(
  new URL('../src/parent/domain/svgGuide.ts', import.meta.url),
  'utf8',
);
const guideScreenSource = readFileSync(
  new URL('../src/parent/presentation/screens/SketchGuideScreen.tsx', import.meta.url),
  'utf8',
);
const apiSource = readFileSync(
  new URL('../src/parent/infrastructure/http/ParentApi.ts', import.meta.url),
  'utf8',
);
const progressiveGuideSource = readFileSync(
  new URL('../src/parent/presentation/components/ProgressiveSvgGuide.tsx', import.meta.url),
  'utf8',
);

describe('Parent source-derived SVG guide contract', () => {
  it('accepts the truthful source-derived response alongside the Modal response', () => {
    expect(domainSource).toContain("contract: 'SvgTopicStrokeGuideSourceDraftV1'");
    expect(domainSource).toContain("generation_source: 'CURATED_SOURCE_DERIVATION'");
    expect(domainSource).toContain('SvgTopicStrokeGuideModalDraftV1');
    expect(domainSource).toContain('| SvgTopicStrokeGuideSourceDraftV1');
    expect(domainSource).toContain("'EXACT_SOURCE_PATH_SEQUENCE_V7'");
    expect(domainSource).toContain("contract: 'SvgTopicStrokeGuideConstructionDraftV1'");
    expect(domainSource).toContain("'QWEN_REFERENCE_CONDITIONED_CONSTRUCTION_V1'");
    expect(apiSource).toContain('request<SvgTopicStrokeGuideDraftV1>');
  });

  it('labels source provenance and preserves adult review before drawing', () => {
    expect(guideScreenSource).toContain('Bản nháp từ SVG nguồn');
    expect(guideScreenSource).toContain('Chỉ dùng bản nháp sau khi người lớn kiểm tra hình và thứ tự nét.');
    expect(guideScreenSource).toContain('Duyệt · cho trẻ xem');
    expect(guideScreenSource).toContain('Xong · chụp tranh');
  });

  it('keeps construction strokes separate from the optional finished illustration', () => {
    expect(domainSource).toContain("schema_version: 'SvgReferenceIllustrationV1'");
    expect(domainSource).toContain('reference_illustration: SvgReferenceIllustrationDocumentV1');
    expect(progressiveGuideSource).toContain('referenceIllustration.paths.map');
    expect(progressiveGuideSource).toContain('fill={path.fill}');
    expect(progressiveGuideSource).toContain('showFinalReferenceAlongside && referenceImage');
    expect(progressiveGuideSource).not.toContain('REFERENCE_UNDERLAY_OPACITY');
    expect(progressiveGuideSource).not.toContain('Hình gà mái làm mẫu mờ bên dưới nét vẽ');
    expect(progressiveGuideSource).toContain('strokeDashoffset={getDashOffset(path.path_id)}');
    expect(progressiveGuideSource).toContain('stroke={CURRENT_STROKE}');
    expect(progressiveGuideSource).toContain('stroke={COMPLETED_STROKE}');
    expect(progressiveGuideSource).toContain('currentStage?.animation_order');
    expect(progressiveGuideSource).toContain('sourceExactPathSequence');
    expect(progressiveGuideSource).toContain('completedStages');
    expect(progressiveGuideSource).toContain('strokeLinecap={strokeLinecap}');
    expect(progressiveGuideSource).toContain('duration: sourceExactPathSequence ? 850 : 950');
    expect(progressiveGuideSource).toContain('delay: index * (sourceExactPathSequence ? 65 : 220)');
    expect(guideScreenSource).toContain("props.draft.derivation.method === 'EXACT_SOURCE_PATH_SEQUENCE_V7'");
    expect(guideScreenSource).toContain('sourceExactPathSequence={sourceExactPathSequence}');
    expect(guideScreenSource).toContain('const showFinalReferenceAlongside = Boolean(referenceIllustration && stageIndex === stageCount - 1)');
    expect(guideScreenSource).toContain('AI dựng lại nét từ hình mẫu · người lớn xem trước');
    expect(guideScreenSource).toContain('stageLabel');
    expect(domainSource).toContain("'construction' | 'outline' | 'feature'");
  });
});
