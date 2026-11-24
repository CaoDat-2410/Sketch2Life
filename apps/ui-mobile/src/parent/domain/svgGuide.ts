export type SvgPathV1 = Readonly<{
  path_id: string;
  d: string;
  fill: string;
  stroke: string;
  stroke_width: number;
}>;

export type SvgDocumentV1 = Readonly<{
  schema_version: 'SvgDocumentV1';
  view_box: string;
  paths: ReadonlyArray<SvgPathV1>;
}>;

export type SvgReferenceIllustrationPathV1 = Readonly<{
  path_id: string;
  d: string;
  fill: string;
  stroke: string;
  stroke_width: number;
  stroke_linecap: 'butt' | 'round' | 'square';
  stroke_linejoin: 'miter' | 'round' | 'bevel';
  stroke_miterlimit: number;
}>;

export type SvgReferenceIllustrationDocumentV1 = Readonly<{
  schema_version: 'SvgReferenceIllustrationV1';
  view_box: string;
  paths: ReadonlyArray<SvgReferenceIllustrationPathV1>;
}>;

export type SketchStrokeGuideV3 = Readonly<{
  schema_version: 'SketchStrokeGuideV3';
  guide_id: string;
  title_vi: string;
  source_asset_ref: string;
  source_asset_version: number;
  source_sha256: string;
  parts: ReadonlyArray<Readonly<{
    part_id: string;
    label_vi: string;
    path_ids: ReadonlyArray<string>;
    depends_on: ReadonlyArray<string>;
  }>>;
  stages: ReadonlyArray<Readonly<{
    step_index: number;
    instruction_vi: string;
    part_ids: ReadonlyArray<string>;
    new_path_ids: ReadonlyArray<string>;
    animation_order: ReadonlyArray<string>;
  }>>;
}>;

export type SvgTopicStrokeGuideV1 = Readonly<{
  schema_version: 'SvgTopicStrokeGuideV1';
  guide_id: string;
  title_vi: string;
  parts: ReadonlyArray<Readonly<{
    part_id: string;
    label_vi: string;
    path_ids: ReadonlyArray<string>;
    depends_on: ReadonlyArray<string>;
  }>>;
  stages: ReadonlyArray<Readonly<{
    step_index: number;
    instruction_vi: string;
    part_ids: ReadonlyArray<string>;
    new_path_ids: ReadonlyArray<string>;
    animation_order: ReadonlyArray<string>;
  }>>;
}>;

export type ProgressiveStrokeGuideV1 = Pick<SvgTopicStrokeGuideV1, 'guide_id' | 'title_vi' | 'parts' | 'stages'> & Readonly<{
  schema_version: 'SketchStrokeGuideV3' | 'SvgTopicStrokeGuideV1';
}>;

export type SvgTopicStrokeGuideModalDraftV1 = Readonly<{
  contract: 'SvgTopicStrokeGuideDraftV1';
  request_id: string;
  modal_call_id: string;
  topic: string;
  intended_subject?: string | null;
  status: 'DRAFT';
  review_required: true;
  persisted: false;
  model: Readonly<{ id: string; revision: string }>;
  reference_source: SvgReferenceSourceProvenanceV1 | null;
  document: SvgDocumentV1;
  document_sha256: string;
  guide: SvgTopicStrokeGuideV1;
  path_count: number;
  stage_count: number;
  quality_gates_passed: ReadonlyArray<string>;
}>;

export type SvgTopicStrokeGuideSourceDraftV1 = Readonly<{
  contract: 'SvgTopicStrokeGuideSourceDraftV1';
  request_id: string;
  topic: string;
  intended_subject?: string | null;
  status: 'DRAFT';
  review_required: true;
  persisted: false;
  generation_source: 'CURATED_SOURCE_DERIVATION' | 'QWEN_SOURCE_PATH_DERIVATION';
  model?: Readonly<{ id: string; revision: string }> | null;
  modal_call_id?: string | null;
  derivation: Readonly<{
    engine_id: string;
    engine_revision: string;
    source_guide_uri?: string | null;
    source_guide_sha256?: string | null;
    method: 'MANUAL_HEN_DRAWING_SEQUENCE_V5' | 'REFERENCE_ALIGNED_CHILD_DRAWING_SEQUENCE_V6' | 'EXACT_SOURCE_PATH_SEQUENCE_V7' | 'OPENMOJI_SOURCE_SHAPE_TO_PATH_V1' | 'OPENCLIPART_SOURCE_CONTOUR_TO_DRAW_PATH_V1' | 'QWEN_OPENCLIPART_SOURCE_PATH_SEQUENCE_V1';
    source_path_count: number;
    path_lineage: ReadonlyArray<Readonly<{
      derived_path_id: string;
      source_path_ids: ReadonlyArray<string>;
      feature_vi: string;
      operation: 'MANUAL_HEN_DRAWING_SEQUENCE_V5' | 'REFERENCE_ALIGNED_CHILD_DRAWING_SEQUENCE_V6' | 'EXACT_SOURCE_PATH_SEQUENCE_V7' | 'OPENMOJI_SOURCE_SHAPE_TO_PATH_V1' | 'OPENCLIPART_SOURCE_CONTOUR_TO_DRAW_PATH_V1' | 'QWEN_OPENCLIPART_SOURCE_PATH_SEQUENCE_V1';
    }>>;
  }>;
  reference_source: SvgReferenceSourceProvenanceV1;
  reference_illustration: SvgReferenceIllustrationDocumentV1;
  document: SvgDocumentV1;
  document_sha256: string;
  guide: SvgTopicStrokeGuideV1;
  path_count: number;
  stage_count: number;
  quality_gates_passed: ReadonlyArray<string>;
}>;

export type SvgTopicStrokeGuideConstructionDraftV1 = Readonly<{
  contract: 'SvgTopicStrokeGuideConstructionDraftV1';
  request_id: string;
  topic: string;
  intended_subject?: string | null;
  status: 'DRAFT';
  review_required: true;
  persisted: false;
  generation_source: 'QWEN_REFERENCE_CONDITIONED_CONSTRUCTION';
  model: Readonly<{ id: string; revision: string }>;
  modal_call_id: string;
  derivation: Readonly<{
    engine_id: string;
    engine_revision: string;
    method: 'QWEN_REFERENCE_CONDITIONED_CONSTRUCTION_V1';
    source_path_count: number;
    path_lineage: ReadonlyArray<Readonly<{
      derived_path_id: string;
      source_path_ids: ReadonlyArray<string>;
      feature_vi: string;
      role: 'construction' | 'outline' | 'feature';
    }>>;
  }>;
  reference_source: SvgReferenceSourceProvenanceV1;
  reference_illustration: SvgReferenceIllustrationDocumentV1;
  document: SvgDocumentV1;
  document_sha256: string;
  guide: SvgTopicStrokeGuideV1;
  path_count: number;
  stage_count: number;
  quality_gates_passed: ReadonlyArray<string>;
}>;

export type SvgTopicStrokeGuideDraftV1 =
  | SvgTopicStrokeGuideModalDraftV1
  | SvgTopicStrokeGuideSourceDraftV1
  | SvgTopicStrokeGuideConstructionDraftV1;

export type SvgReferenceSourceProvenanceV1 = Readonly<{
  asset_id: string;
  dataset_name: string;
  dataset_revision: string;
  dataset_doi: string | null;
  dataset_uri: string | null;
  source_sha256: string;
  license_id: string;
  license_uri: string;
}>;

export type ParentSvgGuideItemV1 = Readonly<{
  catalog_entry_id: string;
  topic_key: string;
  title_vi: string;
  alt_text_vi: string;
  source_sha256: string;
  guide_sha256: string;
  document: SvgDocumentV1;
  guide: SketchStrokeGuideV3;
}>;

export type ParentSvgGuidePageV1 = Readonly<{
  contract: 'SvgGuideCatalogPageV1';
  items: ReadonlyArray<ParentSvgGuideItemV1>;
}>;

export function orderedVisiblePathIds(guide: ProgressiveStrokeGuideV1, stageIndex: number): string[] {
  return guide.stages.slice(0, stageIndex + 1).flatMap((stage) => stage.animation_order);
}

export function estimateSvgPathLength(pathData: string): number {
  const tokens = pathData.match(/[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?/g) ?? [];
  if (!tokens.length || tokens.join('') !== pathData.replace(/[\s,]+/g, '')) return 1;

  let tokenIndex = 0;
  let command = '';
  let x = 0;
  let y = 0;
  let startX = 0;
  let startY = 0;
  let length = 0;
  let cubicControl: Readonly<{ x: number; y: number }> | null = null;
  let quadraticControl: Readonly<{ x: number; y: number }> | null = null;
  let previousCommand = '';

  const distance = (x1: number, y1: number, x2: number, y2: number): number => Math.hypot(x2 - x1, y2 - y1);
  const point = (values: ReadonlyArray<number>, offset: number, relative: boolean) => ({
    x: values[offset] + (relative ? x : 0),
    y: values[offset + 1] + (relative ? y : 0),
  });
  const sampleCurve = (evaluate: (t: number) => Readonly<{ x: number; y: number }>): number => {
    let result = 0;
    let previous = evaluate(0);
    for (let sample = 1; sample <= 16; sample += 1) {
      const next = evaluate(sample / 16);
      result += distance(previous.x, previous.y, next.x, next.y);
      previous = next;
    }
    return result;
  };
  const arcLength = (
    x1: number, y1: number, inputRx: number, inputRy: number,
    rotationDegrees: number, largeArc: number, sweep: number, x2: number, y2: number,
  ): number => {
    let rx = Math.abs(inputRx);
    let ry = Math.abs(inputRy);
    if (rx === 0 || ry === 0 || (x1 === x2 && y1 === y2)) return distance(x1, y1, x2, y2);
    const phi = (rotationDegrees * Math.PI) / 180;
    const cosPhi = Math.cos(phi);
    const sinPhi = Math.sin(phi);
    const halfX = (x1 - x2) / 2;
    const halfY = (y1 - y2) / 2;
    const xPrime = cosPhi * halfX + sinPhi * halfY;
    const yPrime = -sinPhi * halfX + cosPhi * halfY;
    const scale = xPrime ** 2 / rx ** 2 + yPrime ** 2 / ry ** 2;
    if (scale > 1) {
      const multiplier = Math.sqrt(scale);
      rx *= multiplier;
      ry *= multiplier;
    }
    const numerator = Math.max(0, rx ** 2 * ry ** 2 - rx ** 2 * yPrime ** 2 - ry ** 2 * xPrime ** 2);
    const denominator = rx ** 2 * yPrime ** 2 + ry ** 2 * xPrime ** 2;
    const coefficient = denominator === 0
      ? 0
      : (largeArc === sweep ? -1 : 1) * Math.sqrt(numerator / denominator);
    const centerXPrime = coefficient * ((rx * yPrime) / ry);
    const centerYPrime = coefficient * (-(ry * xPrime) / rx);
    const centerX = cosPhi * centerXPrime - sinPhi * centerYPrime + (x1 + x2) / 2;
    const centerY = sinPhi * centerXPrime + cosPhi * centerYPrime + (y1 + y2) / 2;
    const ux = (xPrime - centerXPrime) / rx;
    const uy = (yPrime - centerYPrime) / ry;
    const vx = (-xPrime - centerXPrime) / rx;
    const vy = (-yPrime - centerYPrime) / ry;
    const thetaStart = Math.atan2(uy, ux);
    let thetaDelta = Math.atan2(ux * vy - uy * vx, ux * vx + uy * vy);
    if (!sweep && thetaDelta > 0) thetaDelta -= 2 * Math.PI;
    if (sweep && thetaDelta < 0) thetaDelta += 2 * Math.PI;
    const steps = Math.max(12, Math.ceil(Math.abs(thetaDelta) * 24));
    let result = 0;
    let previous = { x: x1, y: y1 };
    for (let sample = 1; sample <= steps; sample += 1) {
      const theta = thetaStart + (thetaDelta * sample) / steps;
      const ellipseX = rx * Math.cos(theta);
      const ellipseY = ry * Math.sin(theta);
      const next = {
        x: centerX + cosPhi * ellipseX - sinPhi * ellipseY,
        y: centerY + sinPhi * ellipseX + cosPhi * ellipseY,
      };
      result += distance(previous.x, previous.y, next.x, next.y);
      previous = next;
    }
    return result;
  };

  while (tokenIndex < tokens.length) {
    if (/^[A-Za-z]$/.test(tokens[tokenIndex])) command = tokens[tokenIndex++];
    if (!command) return Math.max(length, 1);
    const upper = command.toUpperCase();
    const relative = command !== upper;
    if (upper === 'Z') {
      length += distance(x, y, startX, startY);
      x = startX;
      y = startY;
      command = '';
      previousCommand = 'Z';
      cubicControl = null;
      quadraticControl = null;
      continue;
    }

    const arity: Record<string, number> = { M: 2, L: 2, H: 1, V: 1, C: 6, S: 4, Q: 4, T: 2, A: 7 };
    const count = arity[upper];
    if (!count || tokenIndex + count > tokens.length) return Math.max(length, 1);
    const values: number[] = [];
    for (let offset = 0; offset < count; offset += 1) {
      const value = tokens[tokenIndex + offset];
      if (/^[A-Za-z]$/.test(value)) return Math.max(length, 1);
      values.push(Number(value));
    }
    tokenIndex += count;
    const x0 = x;
    const y0 = y;

    if (upper === 'M' || upper === 'L') {
      const next = point(values, 0, relative);
      if (upper === 'M') {
        x = next.x;
        y = next.y;
        startX = x;
        startY = y;
        command = relative ? 'l' : 'L';
      } else {
        length += distance(x, y, next.x, next.y);
        x = next.x;
        y = next.y;
      }
    } else if (upper === 'H') {
      const nextX = values[0] + (relative ? x : 0);
      length += distance(x, y, nextX, y);
      x = nextX;
    } else if (upper === 'V') {
      const nextY = values[0] + (relative ? y : 0);
      length += distance(x, y, x, nextY);
      y = nextY;
    } else if (upper === 'C') {
      const first = point(values, 0, relative);
      const second = point(values, 2, relative);
      const end = point(values, 4, relative);
      length += sampleCurve((t) => {
        const inverse = 1 - t;
        return {
          x: inverse ** 3 * x0 + 3 * inverse ** 2 * t * first.x + 3 * inverse * t ** 2 * second.x + t ** 3 * end.x,
          y: inverse ** 3 * y0 + 3 * inverse ** 2 * t * first.y + 3 * inverse * t ** 2 * second.y + t ** 3 * end.y,
        };
      });
      x = end.x;
      y = end.y;
      cubicControl = second;
      quadraticControl = null;
    } else if (upper === 'S') {
      const first = previousCommand === 'C' || previousCommand === 'S'
        ? { x: 2 * x0 - (cubicControl?.x ?? x0), y: 2 * y0 - (cubicControl?.y ?? y0) }
        : { x: x0, y: y0 };
      const second = point(values, 0, relative);
      const end = point(values, 2, relative);
      length += sampleCurve((t) => {
        const inverse = 1 - t;
        return {
          x: inverse ** 3 * x0 + 3 * inverse ** 2 * t * first.x + 3 * inverse * t ** 2 * second.x + t ** 3 * end.x,
          y: inverse ** 3 * y0 + 3 * inverse ** 2 * t * first.y + 3 * inverse * t ** 2 * second.y + t ** 3 * end.y,
        };
      });
      x = end.x;
      y = end.y;
      cubicControl = second;
      quadraticControl = null;
    } else if (upper === 'Q') {
      const control = point(values, 0, relative);
      const end = point(values, 2, relative);
      length += sampleCurve((t) => {
        const inverse = 1 - t;
        return {
          x: inverse ** 2 * x0 + 2 * inverse * t * control.x + t ** 2 * end.x,
          y: inverse ** 2 * y0 + 2 * inverse * t * control.y + t ** 2 * end.y,
        };
      });
      x = end.x;
      y = end.y;
      quadraticControl = control;
      cubicControl = null;
    } else if (upper === 'T') {
      const control: Readonly<{ x: number; y: number }> = previousCommand === 'Q' || previousCommand === 'T'
        ? { x: 2 * x0 - (quadraticControl?.x ?? x0), y: 2 * y0 - (quadraticControl?.y ?? y0) }
        : { x: x0, y: y0 };
      const end = point(values, 0, relative);
      length += sampleCurve((t) => {
        const inverse = 1 - t;
        return {
          x: inverse ** 2 * x0 + 2 * inverse * t * control.x + t ** 2 * end.x,
          y: inverse ** 2 * y0 + 2 * inverse * t * control.y + t ** 2 * end.y,
        };
      });
      x = end.x;
      y = end.y;
      quadraticControl = control;
      cubicControl = null;
    } else if (upper === 'A') {
      const end = point(values, 5, relative);
      length += arcLength(x0, y0, values[0], values[1], values[2], values[3], values[4], end.x, end.y);
      x = end.x;
      y = end.y;
      cubicControl = null;
      quadraticControl = null;
    }

    if (upper !== 'C' && upper !== 'S') cubicControl = null;
    if (upper !== 'Q' && upper !== 'T') quadraticControl = null;
    previousCommand = upper;
  }

  return Number.isFinite(length) ? Math.max(length, 1) : 1;
}
