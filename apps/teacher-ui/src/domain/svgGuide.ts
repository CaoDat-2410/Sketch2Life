export type SvgPathV1 = Readonly<{
  path_id: string
  d: string
  fill: string
  stroke: string
  stroke_width: number
}>

export type SvgDocumentV1 = Readonly<{
  schema_version: 'SvgDocumentV1'
  view_box: string
  paths: ReadonlyArray<SvgPathV1>
}>

export type TeacherSvgIllustrationDraftRequestV1 = Readonly<{
  contract: 'TeacherSvgIllustrationDraftRequestV1'
  topic: string
  target_age_months: number
  visual_style: 'warm_storybook' | 'simple_classroom' | 'clean_outline'
}>

export type TeacherSvgIllustrationDraftV1 = Readonly<{
  contract: 'TeacherSvgIllustrationDraftV1'
  request_id: string
  modal_call_id: string
  status: 'DRAFT'
  review_required: true
  persisted: false
  model: Readonly<{ id: string; revision: string }>
  title_vi: string
  alt_text_vi: string
  document: SvgDocumentV1
  document_sha256: string
  path_count: number
}>

export type SketchStrokeGuideV3 = Readonly<{
  schema_version: 'SketchStrokeGuideV3'
  guide_id: string
  title_vi: string
  source_asset_ref: string
  source_asset_version: number
  source_sha256: string
  parts: ReadonlyArray<Readonly<{
    part_id: string
    label_vi: string
    path_ids: ReadonlyArray<string>
    depends_on: ReadonlyArray<string>
  }>>
  stages: ReadonlyArray<Readonly<{
    step_index: number
    instruction_vi: string
    part_ids: ReadonlyArray<string>
    new_path_ids: ReadonlyArray<string>
    animation_order: ReadonlyArray<string>
  }>>
}>

export type SvgTopicStrokeGuideV1 = Readonly<{
  schema_version: 'SvgTopicStrokeGuideV1'
  guide_id: string
  title_vi: string
  parts: ReadonlyArray<Readonly<{
    part_id: string
    label_vi: string
    path_ids: ReadonlyArray<string>
    depends_on: ReadonlyArray<string>
  }>>
  stages: ReadonlyArray<Readonly<{
    step_index: number
    instruction_vi: string
    part_ids: ReadonlyArray<string>
    new_path_ids: ReadonlyArray<string>
    animation_order: ReadonlyArray<string>
  }>>
}>

export type ProgressiveStrokeGuideV1 = Pick<SvgTopicStrokeGuideV1, 'guide_id' | 'title_vi' | 'stages'> & Readonly<{
  schema_version: 'SketchStrokeGuideV3' | 'SvgTopicStrokeGuideV1'
}>

export type SvgTopicStrokeGuideDraftV1 = Readonly<{
  contract: 'SvgTopicStrokeGuideDraftV1'
  request_id: string
  modal_call_id: string
  topic: string
  status: 'DRAFT'
  review_required: true
  persisted: false
  model: Readonly<{ id: string; revision: string }>
  reference_source: SvgReferenceSourceProvenanceV1 | null
  document: SvgDocumentV1
  document_sha256: string
  guide: SvgTopicStrokeGuideV1
  path_count: number
  stage_count: number
  quality_gates_passed: ReadonlyArray<string>
}>

export type SvgReferenceSourceProvenanceV1 = Readonly<{
  asset_id: string
  dataset_name: string
  dataset_revision: string
  dataset_doi: string | null
  dataset_uri: string | null
  source_sha256: string
  license_id: string
  license_uri: string
}>

export type SvgCatalogAssetV1 = Readonly<{
  contract: 'SvgCatalogAssetResponseV1'
  catalog_entry_id: string
  source_asset_ref: string
  source_asset_version: number
  canonical_asset_ref: string
  canonical_asset_version: number
  source_sha256: string
  canonical_sha256: string
  topic_key: string
  title_vi: string
  alt_text_vi: string
  source_uri: string
  license_id: string
  license_uri: string
  visibility_scope: 'PLATFORM' | 'ORGANIZATION'
  organization_id: string | null
  created_by: string
  readiness: 'STROKE_READY' | 'REQUIRES_MANUAL_AUTHORING' | 'STATIC_ONLY'
  readiness_reasons: string[]
  structural_facts: Record<string, number>
  review_state: 'PENDING_EDUCATOR_REVIEW' | 'PENDING_CURATOR_REVIEW' | 'APPROVED' | 'REJECTED' | 'ARCHIVED'
  document: SvgDocumentV1 | null
}>

export type SvgGuideRevisionV1 = Readonly<{
  contract: 'SvgGuideRevisionReceiptV1'
  guide_revision_id: string
  guide_ref: string
  guide_revision: number
  source_sha256: string
  guide_sha256: string
  guide: SketchStrokeGuideV3
  authored_by: string
  visibility_scope: 'PLATFORM' | 'ORGANIZATION'
  organization_id: string | null
  review_state: 'PENDING' | 'APPROVED' | 'REJECTED'
}>

export type LessonSummaryV1 = Readonly<{
  lesson_id: string
  title: string
  topic: string
  current_version_no: number
  review_state: string
  visibility: string
  activity_count: number
  updated_at: string
}>

export type LessonPresentationSlideV1 = Readonly<{
  slide_id: string
  kind: 'drawing_guide'
  title_vi: string
  body_vi: string
  guide: SketchStrokeGuideV3
}>

export type LessonContentV1 = {
  locale: 'vi-VN'
  title: string
  topic: string
  target_age_band_ref: string
  target_age_band_version: number
  objectives: string[]
  drawing_subject: string
  drawing_steps_text: string
  subject_learning_notes: string
  script_direction: string | null
  script_following_allowed: boolean
  activities: Array<Record<string, unknown>>
  presentation?: { schema_version: 'LessonPresentationV1'; slides: LessonPresentationSlideV1[] } | null
}

export type LessonDetailV1 = Readonly<{
  lesson_id: string
  organization_id: string
  revision: number
  current_version: {
    version_id: string
    version_no: number
    content: LessonContentV1
  }
}>

export type SvgGuideRevisionDraft = {
  path_id: string
  part_id: string
  label_vi: string
  stage_index: number | null
}

export function orderedVisiblePathIds(guide: ProgressiveStrokeGuideV1, stageIndex: number): string[] {
  return guide.stages.slice(0, stageIndex + 1).flatMap((stage) => stage.animation_order)
}
