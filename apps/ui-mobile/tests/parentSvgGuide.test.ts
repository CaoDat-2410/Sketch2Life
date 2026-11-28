import { describe, expect, it } from 'vitest';
import {
  estimateSvgPathLength,
  isValidSvgViewBox,
  isSafeSvgTopicStrokeGuideSourceDraft,
  orderedVisiblePathIds,
  svgGuideFailureMessage,
  type SvgTopicStrokeGuideSourceDraftV1,
} from '../src/parent/domain/svgGuide';

function guideDraft(pathData = 'M0 0 L3 4'): SvgTopicStrokeGuideSourceDraftV1 {
  const stages = [1, 2, 3, 4].map((stepIndex) => ({
    step_index: stepIndex,
    instruction_vi: `Bước ${stepIndex}`,
    part_ids: ['outline'],
    new_path_ids: ['path-1'],
    animation_order: ['path-1'],
  }));
  return {
    contract: 'SvgTopicStrokeGuideSourceDraftV1',
    request_id: 'request-1',
    topic: 'Động vật',
    intended_subject: 'con mèo',
    status: 'DRAFT',
    review_required: true,
    persisted: false,
    generation_source: 'CURATED_SOURCE_DERIVATION',
    derivation: {
      engine_id: 'svg-engine', engine_revision: '1', method: 'MANUAL_HEN_DRAWING_SEQUENCE_V5',
      source_path_count: 1,
      path_lineage: [{ derived_path_id: 'path-1', source_path_ids: ['source-1'], feature_vi: 'Nét ngoài', operation: 'MANUAL_HEN_DRAWING_SEQUENCE_V5' }],
    },
    reference_source: {
      asset_id: 'asset-1', dataset_name: 'catalog', dataset_revision: '1', dataset_doi: null,
      dataset_uri: null, source_sha256: 'a'.repeat(64), license_id: 'CC0', license_uri: 'https://example.test/license',
    },
    reference_illustration: {
      schema_version: 'SvgReferenceIllustrationV1', view_box: '0 0 100 100',
      paths: [{ path_id: 'reference-1', d: 'M0 0 L3 4', fill: 'none', stroke: '#000000', stroke_width: 1, stroke_linecap: 'round', stroke_linejoin: 'round', stroke_miterlimit: 4 }],
    },
    document: {
      schema_version: 'SvgDocumentV1', view_box: '0 0 100 100',
      paths: [{ path_id: 'path-1', d: pathData, fill: 'none', stroke: '#000000', stroke_width: 2 }],
    },
    document_sha256: 'b'.repeat(64),
    guide: {
      schema_version: 'SvgTopicStrokeGuideV1', guide_id: 'guide-1', title_vi: 'Hướng dẫn',
      parts: [{ part_id: 'outline', label_vi: 'Đường viền', path_ids: ['path-1'], depends_on: [] }],
      stages,
    },
    path_count: 1,
    stage_count: 4,
    quality_gates_passed: ['schema', 'paths', 'stages', 'safety'],
  };
}

describe('progressive SVG guide', () => {
  it('keeps the shared view-box validator positive and bounded', () => {
    expect(isValidSvgViewBox('0 0 100 100')).toBe(true);
    expect(isValidSvgViewBox('0 0 100 -1')).toBe(false);
  });

  it('reveals paths stage by stage and estimates simple path length', () => {
    expect(orderedVisiblePathIds(guideDraft().guide, 1)).toEqual(['path-1', 'path-1']);
    expect(estimateSvgPathLength('M0 0 L3 4')).toBe(5);
  });

  it('rejects unsafe path data before it reaches the SVG renderer', () => {
    expect(isSafeSvgTopicStrokeGuideSourceDraft(guideDraft())).toBe(true);
    expect(isSafeSvgTopicStrokeGuideSourceDraft(guideDraft('<script />'))).toBe(false);
  });

  it('lets the adult continue when the topic has no approved guide', () => {
    expect(svgGuideFailureMessage('CURATED_SVG_GUIDE_NOT_FOUND')).toBe(
      'Chưa có hướng dẫn nét vẽ cho chủ đề này. Bạn vẫn có thể tiếp tục chụp tranh mà không cần gợi ý.',
    );
  });
});
