import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Audio } from 'expo-av';
import type { ScreenId } from '../types';
import type {
  ChildProfile,
  SceneEntity,
  SceneUnderstandingResponse,
  MontessoriActivity,
} from '../services/api.types';
import {
  MOCK_CHILDREN,
  MOCK_SCENE_UNDERSTANDING,
  MOCK_ACTIVITIES,
} from '../services/mockData';
import {
  createDemoApi,
  DemoApiError,
  type ActivityRecommendationCardV2,
  type ActivityContextCandidateSet,
  type ActivityRecommendationSetV3,
  type P1ContextOptions,
  type ChildLearningProfileInput,
  type ChildPreferenceClassification,
  type WorkflowResult,
} from '../demo/api';
import {
  acquireSingleFlight,
  prepareNarration,
  releaseSingleFlight,
  type FeedbackObservationCode,
} from './workflowSafety';
import { imageIntakeErrorMessage, preparePickedImage } from './imageIntake';
import { resetSessionBoundProfileAnswers } from '../demo/sessionProfileAnswers.mjs';

export interface SelectedDrawing {
  uri: string;
  uploadUri?: string;
  fileName: string;
  mimeType: string;
  fileSize?: number;
  sourceMimeType?: string;
  normalizationPolicy?: string;
}

export interface SelectedNarrationAudio {
  uri: string;
  fileName: string;
  mimeType: string;
  durationMs?: number;
  artifactRef?: string;
  sha256?: string;
  byteLength?: number;
  contentType?: string;
}

export interface AnalysisClaim {
  observation_id: string;
  label: { value: string };
  rawLabel?: string;
  confidence: number;
  kind: 'subject' | 'action' | 'story';
}

export interface TopicDirection {
  direction_id: string;
  priority: number;
  title_vi: string;
  summary_vi: string;
  primary_claim_id: string;
  source_claim_ids: string[];
  confidence_band: 'HIGH' | 'MEDIUM' | 'LOW';
  requires_requery: boolean;
}

export interface SubjectTarget {
  candidateId: string;
  labelVi: string;
  confidence: number;
  confidenceBand: 'HIGH' | 'MEDIUM' | 'LOW';
  region: { x: number; y: number; width: number; height: number };
}

interface AppContextType {
  // Navigation
  currentScreen: ScreenId;
  navigate: (screen: ScreenId) => void;
  goBack: () => void;
  resetTo: (screen: ScreenId) => void;
  canGoBack: boolean;

  // Child Profile
  childrenList: ChildProfile[];
  selectedChild: ChildProfile;
  setSelectedChild: (child: ChildProfile) => void;
  selectedAgeMonths: number;
  setSelectedAgeMonths: (ageMonths: number) => void;
  selectedChildLearningProfile: ChildLearningProfileInput | null;
  updateSelectedChildLearningProfile: (patch: Partial<ChildLearningProfileInput>) => void;
  resetSelectedChildLearningProfile: () => void;
  classifySelectedChildPreferences: (
    interestText?: string,
    avoidText?: string,
  ) => Promise<ChildPreferenceClassification | null>;
  profileClassificationBusy: boolean;

  // Drawing
  drawingImage: string;
  setDrawingImage: (img: string) => void;
  selectedDrawing: SelectedDrawing | null;
  pickDrawingImage: () => Promise<boolean>;
  uploadDrawing: () => Promise<boolean>;
  workflowBusy: string | null;
  workflowError: string | null;
  dismissWorkflowError: () => void;
  workflowNotice: string | null;
  sessionId: string | null;
  sessionVersion: number;
  sessionState: string;
  admission: Record<string, unknown> | null;
  beginWorkflow: () => Promise<boolean>;

  // Voice
  narrationMode: 'none' | 'text' | 'audio';
  setNarrationMode: (mode: 'none' | 'text' | 'audio') => void;
  narrationText: string;
  setNarrationText: (text: string) => void;
  selectedNarrationAudio: SelectedNarrationAudio | null;
  startRecording: () => Promise<boolean>;
  stopRecording: () => Promise<boolean>;
  cancelRecording: () => Promise<void>;
  uploadNarration: () => Promise<boolean>;
  isRecording: boolean;
  isRecordingStarting: boolean;
  voiceDuration: number;
  toggleRecording: () => void;
  voiceTranscript: string;

  // AI Pipeline
  aiProgress: number;
  sceneData: SceneUnderstandingResponse;
  runAiSimulation: () => Promise<boolean>;
  requerySubject: () => Promise<boolean>;
  directionRequeryUsed: boolean;
  analysisClaims: AnalysisClaim[];
  topicDirections: TopicDirection[];
  selectedTopicDirectionId: string | null;
  selectTopicDirection: (directionId: string) => void;
  selectedClaimIds: string[];
  primaryClaimId: string | null;
  toggleAnalysisClaim: (claimId: string) => void;
  setPrimaryClaim: (claimId: string) => void;
  correction: string;
  setCorrection: (value: string) => void;
  confirmGateA: () => Promise<boolean>;
  gateAConfirmed: boolean;
  subjectTargets: SubjectTarget[];
  selectedSubjectId: string | null;
  selectedSubjectSentence: string;
  selectSubject: (target: SubjectTarget) => Promise<boolean>;

  // Montessori Activity
  activitiesList: MontessoriActivity[];
  selectedActivity: MontessoriActivity;
  setSelectedActivity: (activity: MontessoriActivity) => void;
  contextOptions: ActivityRecommendationSetV3 | null;
  contextCandidates: ActivityContextCandidateSet | null;
  selectedBackendActivity: ActivityRecommendationCardV2 | null;
  activityRecommendation: P1ContextOptions['recommendation'] | null;
  activityRecommendationCards: ActivityRecommendationCardV2[];
  rankedActivityIds: string[];
  activityRankingStatus: 'IDLE' | 'PENDING' | 'COMPLETE' | 'UNAVAILABLE';
  selectBackendActivity: (activityId: string) => void;
  prepareActivityWorkflow: () => Promise<boolean>;
  approveActivity: () => Promise<boolean>;
  prepareRendererIntro: (refreshLaunch?: boolean) => Promise<boolean>;
  completeActivityHandoff: () => Promise<boolean>;
  rendererLaunch: Record<string, unknown> | null;
  pixiIntroStoryboard: Record<string, unknown> | null;
  materialsChecklist: Record<string, boolean>;
  toggleMaterialCheck: (id: string) => void;
  stepsChecklist: Record<number, boolean>;
  toggleStepCheck: (stepNumber: number) => void;

  // Feedback Loop
  completionStatus: 'completed' | 'partial' | 'not_attempted';
  setCompletionStatus: (status: 'completed' | 'partial' | 'not_attempted') => void;
  interestScore: number;
  setInterestScore: (score: number) => void;
  independenceScore: number;
  setIndependenceScore: (score: number) => void;
  selectedObservationTags: FeedbackObservationCode[];
  toggleObservationTag: (tag: FeedbackObservationCode) => void;
  isSavingFeedback: boolean;
  saveFeedback: () => Promise<boolean>;
  toastMessage: string | null;
  clearToast: () => void;
}

const AppContext = createContext<AppContextType | null>(null);
const workflowApi = createDemoApi();
type JsonObject = Record<string, unknown>;

function asObject(value: unknown): JsonObject {
  return typeof value === 'object' && value !== null ? value as JsonObject : {};
}

function textValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function numberValue(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function objectArray(value: unknown): JsonObject[] {
  return Array.isArray(value) ? value.map(asObject) : [];
}

const DISPLAY_LABELS_VI: Record<string, string> = {
  butterfly: 'con bướm',
  grass: 'bãi cỏ',
  flower: 'bông hoa',
  flowers: 'bông hoa',
  plant: 'cây',
  tree: 'cây',
  sun: 'mặt trời',
  sky: 'bầu trời',
  flying: 'bay',
  fly: 'bay',
  moving: 'chuyển động',
  nature: 'thiên nhiên',
  garden: 'khu vườn',
  animal: 'động vật',
  bird: 'con chim',
  parrot: 'con vẹt',
  sparrow: 'chim sẻ',
  eagle: 'đại bàng',
  duck: 'con vịt',
  chicken: 'con gà',
  robin: 'chim cổ đỏ',
  branch: 'cành cây',
  leaf: 'chiếc lá',
  leaves: 'những chiếc lá',
  perching: 'đậu trên cành',
  'bird on branch': 'con chim đậu trên cành cây',
  'outdoor scene': 'khung cảnh ngoài trời',
  cat: 'con mèo',
  dog: 'con chó',
  fish: 'con cá',
  rabbit: 'con thỏ',
  turtle: 'con rùa',
  frog: 'con ếch',
};

const BACKGROUND_LABELS = new Set([
  'grass', 'ground', 'nature', 'background', 'sky', 'cỏ', 'bãi cỏ', 'thiên nhiên', 'bầu trời',
]);
const WHOLE_SUBJECT_LABELS = new Set([
  'bird', 'parrot', 'sparrow', 'eagle', 'duck', 'chicken', 'robin', 'cat', 'dog', 'fish',
  'rabbit', 'turtle', 'frog', 'butterfly', 'con chim', 'con vẹt', 'chim sẻ', 'đại bàng',
  'con vịt', 'con gà', 'con mèo', 'con chó', 'con cá', 'con thỏ', 'con rùa', 'con ếch', 'con bướm',
]);
const SUBJECT_PART_LABELS = new Set([
  'branch', 'twig', 'leaf', 'leaves', 'stem', 'petal', 'wing', 'beak', 'grass', 'ground',
  'background', 'sky', 'cành cây', 'cành', 'nhánh', 'chiếc lá', 'những chiếc lá', 'lá',
  'thân cây', 'cánh', 'mỏ', 'bãi cỏ', 'bầu trời',
]);

function displayLabelVi(value: string): string {
  const cleaned = value.trim();
  const translated = DISPLAY_LABELS_VI[cleaned.toLowerCase()];
  if (translated) return translated;
  return cleaned;
}

function topicFromClaims(claims: AnalysisClaim[]): string {
  const primary = claims[0];
  if (!primary) return 'Khám phá bức tranh';
  const action = claims.find((claim) => claim.kind === 'action');
  const context = claims.find((claim) => claim.kind === 'story' && claim.observation_id !== primary.observation_id);
  const subject = primary.kind === 'subject' ? primary.label.value : null;
  if (subject && action) {
    if (context?.label.value.includes(subject) && context.label.value.includes(action.label.value.split(' ')[0])) {
      return `Cùng khám phá ${context.label.value}!`;
    }
    return `Cùng khám phá ${subject} đang ${action.label.value}${context ? ` giữa ${context.label.value}` : ''}!`;
  }
  if (subject && context) return `Khám phá ${subject} trong ${context.label.value}`;
  if (primary.kind === 'action') return `Khám phá hoạt động ${primary.label.value}`;
  return `Khám phá ${primary.label.value}`;
}

function readAnalysisClaims(payload: JsonObject): AnalysisClaim[] {
  const buckets: Array<[unknown, AnalysisClaim['kind']]> = [
    [payload.entities, 'subject'],
    [payload.actions, 'action'],
    [payload.themes, 'story'],
  ];
  const claims = buckets.flatMap(([items, kind]) => objectArray(items).flatMap((item) => {
    const label = asObject(item.label);
    if (
      typeof item.observation_id !== 'string'
      || typeof label.value !== 'string'
      || typeof item.confidence !== 'number'
    ) return [];
    return [{
      observation_id: item.observation_id,
      label: { value: displayLabelVi(label.value) },
      rawLabel: label.value,
      confidence: item.confidence,
      kind,
    }];
  }));
  const ranked = claims.sort((left, right) => {
    const leftLabel = (left.rawLabel || left.label.value).toLowerCase();
    const rightLabel = (right.rawLabel || right.label.value).toLowerCase();
    const leftBackground = BACKGROUND_LABELS.has(leftLabel) ? 1 : 0;
    const rightBackground = BACKGROUND_LABELS.has(rightLabel) ? 1 : 0;
    const subjectRank = (claim: AnalysisClaim, label: string) => claim.kind !== 'subject'
      ? 0
      : WHOLE_SUBJECT_LABELS.has(label) ? 0 : SUBJECT_PART_LABELS.has(label) ? 2 : 1;
    const kindRank = { subject: 0, action: 1, story: 2 };
    return leftBackground - rightBackground
      || subjectRank(left, leftLabel) - subjectRank(right, rightLabel)
      || kindRank[left.kind] - kindRank[right.kind]
      || right.confidence - left.confidence
      || left.observation_id.localeCompare(right.observation_id);
  });
  const seen = new Set<string>();
  return ranked.filter((claim) => {
    const key = `${claim.kind}:${claim.label.value.toLowerCase()}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function readTopicDirections(payload: JsonObject, claims: AnalysisClaim[]): TopicDirection[] {
  const parsed = objectArray(payload.topic_directions).flatMap((item) => {
    const sourceClaimIds = Array.isArray(item.source_claim_ids)
      ? item.source_claim_ids.filter((value): value is string => typeof value === 'string')
      : [];
    if (
      typeof item.direction_id !== 'string'
      || typeof item.title_vi !== 'string'
      || typeof item.primary_claim_id !== 'string'
      || sourceClaimIds.length === 0
    ) return [];
    return [{
      direction_id: item.direction_id,
      priority: numberValue(item.priority, 1),
      title_vi: item.title_vi,
      summary_vi: textValue(item.summary_vi, 'Được ghép từ bức tranh và lời kể của con.'),
      primary_claim_id: item.primary_claim_id,
      source_claim_ids: sourceClaimIds,
      confidence_band: ['HIGH', 'MEDIUM', 'LOW'].includes(textValue(item.confidence_band))
        ? textValue(item.confidence_band) as TopicDirection['confidence_band']
        : 'MEDIUM',
      requires_requery: item.requires_requery === true,
    }];
  });
  if (parsed.length > 0) return parsed.slice(0, 3);
  if (claims.length === 0) return [];
  const fallbackTitle = claims[0].label.value === 'chi tiết trong tranh'
    ? 'Cùng khám phá câu chuyện trong bức tranh!'
    : topicFromClaims(claims);
  return [{
    direction_id: 'topic-direction-1',
    priority: 1,
    title_vi: fallbackTitle,
    summary_vi: 'Được ghép từ những chi tiết rõ nhất trong bức tranh.',
    primary_claim_id: claims[0].observation_id,
    source_claim_ids: claims.slice(0, 3).map((claim) => claim.observation_id),
    confidence_band: claims[0].confidence >= 0.8 ? 'HIGH' : 'MEDIUM',
    requires_requery: false,
  }];
}

function readSubjectTargets(payload: JsonObject): SubjectTarget[] {
  const regions = asObject(payload.subject_regions);
  return objectArray(payload.subject_candidates).flatMap((item) => {
    const candidateId = textValue(item.candidate_id);
    const labelVi = textValue(item.label_vi, 'chi tiết trong tranh');
    const region = asObject(regions[candidateId]);
    const x = numberValue(region.x, -1);
    const y = numberValue(region.y, -1);
    const width = numberValue(region.width, -1);
    const height = numberValue(region.height, -1);
    if (!candidateId || !labelVi || x < 0 || y < 0 || width <= 0 || height <= 0
      || x + width > 1 || y + height > 1) return [];
    const confidence = numberValue(item.confidence, 0);
    const confidenceBand = ['HIGH', 'MEDIUM', 'LOW'].includes(textValue(item.confidence_band))
      ? textValue(item.confidence_band) as SubjectTarget['confidenceBand']
      : confidence >= 0.8 ? 'HIGH' : confidence >= 0.55 ? 'MEDIUM' : 'LOW';
    return [{
      candidateId,
      labelVi,
      confidence,
      confidenceBand,
      region: { x, y, width, height },
    }];
  }).slice(0, 3);
}

function iconForLabel(label: string): string {
  const value = label.toLowerCase();
  if (value.includes('bướm') || value.includes('butterfly')) return '🦋';
  if (value.includes('hoa') || value.includes('flower')) return '🌸';
  if (value.includes('mặt trời') || value.includes('sun')) return '☀️';
  if (value.includes('cỏ') || value.includes('grass')) return '🌿';
  if (value.includes('cây') || value.includes('plant')) return '🌱';
  return '✨';
}

function mapScenePayload(payload: JsonObject, sessionId: string): SceneUnderstandingResponse {
  const claims = readAnalysisClaims(payload);
  const entities: SceneEntity[] = claims.map((claim) => ({
    id: claim.observation_id,
    name: claim.label.value,
    count: 1,
    icon: iconForLabel(claim.label.value),
    category: claim.kind === 'subject' ? 'animal' : claim.kind === 'story' ? 'nature' : 'object',
  }));
  const primary = claims[0]?.label.value || 'bức tranh';
  const narration = asObject(payload.narration);
  const progress = asObject(payload.understanding_progress);
  const topic = asObject(progress.topic);
  return {
    storyId: sessionId,
    entities,
    voiceTranscript: textValue(narration.transcript, 'Không có lời kể trong phiên này.'),
    complimentTitle: 'AI đã đọc được bức tranh!',
    complimentSub: 'Mời người lớn cùng bé kiểm tra những chi tiết vừa tìm thấy.',
    storyTitle: textValue(topic.text, topicFromClaims(claims)),
    storySubtitle: 'Cùng nhìn lại bức vẽ gốc và câu chuyện của con.',
  };
}

function workflowFailure(result: WorkflowResult<Record<string, unknown>>, fallback: string): Error {
  const payload = asObject(result.payload);
  const nestedFailure = asObject(payload.failure);
  const narration = asObject(payload.narration);
  const asr = asObject(narration.asr);
  const nestedCode = textValue(nestedFailure.code, textValue(asr.error_code));
  const mediaReason = textValue(payload.reason, textValue(result.failure?.code, nestedCode));
  const mediaMessages: Record<string, string> = {
    FILE_BYTES_EXCEEDED: 'Ảnh vượt giới hạn 5 MB sau kiểm tra. Hãy chọn ảnh nhỏ hơn hoặc xuất lại ảnh.',
    PIXEL_BUDGET_EXCEEDED: 'Ảnh có quá nhiều điểm ảnh. Hãy giảm kích thước rồi thử lại.',
    LONGEST_EDGE_EXCEEDED: 'Cạnh dài của ảnh vượt giới hạn. Hãy giảm kích thước ảnh rồi thử lại.',
    MULTIPLE_FRAMES: 'Ảnh động chưa được hỗ trợ. Hãy chọn một khung hình tĩnh.',
    UNSUPPORTED_CONTAINER: 'Định dạng ảnh chưa được hỗ trợ. Hãy xuất ảnh tĩnh thành PNG hoặc JPEG.',
    UNSUPPORTED_CODEC: 'Mã hóa ảnh chưa được hỗ trợ. Hãy xuất lại thành PNG hoặc JPEG.',
    UNSUPPORTED_PIXEL_FORMAT: 'Kiểu màu của ảnh chưa được hỗ trợ. Hãy xuất lại thành PNG hoặc JPEG.',
    NOT_AN_IMAGE: 'Tệp đã chọn không phải ảnh hợp lệ. Hãy chọn lại ảnh.',
    CORRUPT_OR_TRUNCATED: 'Ảnh bị lỗi hoặc chưa tải đầy đủ. Hãy tải/lưu ảnh về máy rồi chọn lại.',
    MISSING_SOURCE: 'Không đọc được ảnh đã chọn. Hãy chọn lại ảnh từ thư viện.',
    DECODER_ERROR: 'Thiết bị không giải mã được ảnh. Hãy xuất lại thành PNG hoặc JPEG.',
    INTERNAL_ERROR: 'Hệ thống chưa xử lý được ảnh này. Ảnh trước đó vẫn được giữ.',
  };
  const filterResult = asObject(payload.filter_result);
  const fitEvaluation = asObject(payload.fit_evaluation);
  const gateB = asObject(payload.gate_b);
  const reasonCodes = [
    payload.reason_codes,
    filterResult.reason_codes,
    fitEvaluation.reason_codes,
    gateB.reason_codes,
  ].flatMap((values) => Array.isArray(values)
    ? values.filter((value): value is string => typeof value === 'string')
    : []);
  const safeReason = reasonCodes.includes('NO_GROUNDED_CLAIMS')
    ? 'Mình chưa nhìn rõ đủ chi tiết. Hãy thử ảnh sáng, rõ hơn hoặc đọc lại bức tranh.'
    : reasonCodes.includes('MAPPING_REJECTED')
      ? 'Kết quả vừa nhận chưa đủ tin cậy. Hãy thử đọc lại bức tranh.'
      : reasonCodes.some((code) => [
        'ANCHOR_TEMPLATE_MISMATCH',
        'ANCHOR_KIND_TEMPLATE_MISMATCH',
        'FIT_BELOW_THRESHOLD',
        'NO_ELIGIBLE_ACTIVITY',
        'ACTIVITY_NOT_IN_SEMANTIC_SHORTLIST',
      ].includes(code))
        ? 'Chưa tìm thấy hoạt động phù hợp với chủ đề và độ tuổi. Hãy chọn hướng khác hoặc thử lại.'
        : reasonCodes.some((code) => code.includes('STALE_') || code.includes('VERSION'))
          ? 'Lựa chọn hoạt động đã thay đổi. Hãy tải lại danh sách rồi thử lại.'
          : reasonCodes.some((code) => code.includes('GATE_A') || code.includes('SESSION'))
            ? 'Phiên khám phá đã thay đổi. Hãy quay lại xác nhận chủ đề trước khi chọn hoạt động.'
      : '';
  return new DemoApiError(
    safeReason || mediaMessages[mediaReason] || result.failure?.safe_message || fallback,
    textValue(result.failure?.code, nestedCode || 'WORKFLOW_BLOCKED'),
    409,
    result.failure?.retryable === true || nestedFailure.retryable === true,
  );
}

function friendlyError(error: unknown, fallback: string): string {
  if (!(error instanceof DemoApiError)) return fallback;
  if (error.code === 'NETWORK_ERROR') return 'Chưa kết nối được với máy chủ. Hãy kiểm tra mạng rồi thử lại.';
  if (error.code === 'REQUEST_TIMEOUT') return 'Máy chủ đang xử lý lâu hơn dự kiến. Bạn có thể thử lại.';
  // DemoApiError.message is already a safe, parent-facing message selected from closed
  // reason codes. Preserve it instead of hiding every workflow distinction behind one generic
  // fallback; internal provider codes remain in the non-UI error field.
  return error.message || fallback;
}

function materialTypeForId(id: string): 'paper' | 'scissors' | 'crayon' | 'glue' | 'general' {
  const value = id.toLowerCase();
  if (value.includes('paper') || value.includes('giấy')) return 'paper';
  if (value.includes('scissor') || value.includes('kéo')) return 'scissors';
  if (value.includes('crayon') || value.includes('color') || value.includes('màu')) return 'crayon';
  if (value.includes('glue') || value.includes('keo')) return 'glue';
  return 'general';
}

function mapExperienceToActivity(
  payload: JsonObject,
  display?: ActivityRecommendationCardV2,
): MontessoriActivity {
  const spec = asObject(payload.experience_spec);
  const template = asObject(spec.activity_template);
  const plan = asObject(spec.activity_plan);
  const activityRef = asObject(template.activity_ref);
  const materials = Array.isArray(plan.material_option_ids) ? plan.material_option_ids : [];
  const steps = Array.isArray(plan.presentation_steps_vi)
    ? plan.presentation_steps_vi
    : Array.isArray(template.steps_vi) ? template.steps_vi : [];
  const safety = Array.isArray(plan.safety_rule_ids)
    ? plan.safety_rule_ids
    : Array.isArray(template.safety_rule_ids) ? template.safety_rule_ids : [];
  const focus = asObject(spec.learning_focus);
  const bridge = asObject(spec.bridge_sentence);
  const minAge = numberValue(template.age_months_min);
  const maxAge = numberValue(template.age_months_max);
  return {
    id: textValue(activityRef.id, 'backend-activity'),
    title: display?.title_vi || 'Hoạt động khám phá',
    subtitle: display?.summary_vi || textValue(bridge.sentence_vi, 'Hoạt động được chọn từ chủ đề đã xác nhận.'),
    ageGroup: display?.age_label_vi || String(Math.floor(minAge / 12)) + '–' + String(Math.ceil((maxAge + 1) / 12)) + ' tuổi',
    durationMinutes: display?.duration_minutes || 15,
    category: textValue(focus.child_facing_goal_vi, 'Montessori'),
    materials: materials.map((value, index) => {
      const id = textValue(value, 'material-' + String(index + 1));
      return {
        id,
        name: display?.material_labels_vi[index] || 'Vật liệu quen thuộc',
        type: materialTypeForId(id),
        isReady: false,
      };
    }),
    steps: steps.map((value, index) => ({ stepNumber: index + 1, title: textValue(value, 'Bước ' + String(index + 1)), isDone: false })),
    safetyNotes: safety.length > 0
      ? ['Người lớn kiểm tra vật liệu và ở gần trong suốt hoạt động.']
      : [],
    parentTips: textValue(bridge.sentence_vi, 'Người lớn đồng hành và giữ đúng điều kiện an toàn đã chọn.'),
  };
}

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Navigation Stack
  const getInitialScreen = (): ScreenId => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const s = params.get('screen') as ScreenId;
      if (s) return s;
    }
    return 'splash';
  };

  const [currentScreen, setCurrentScreen] = useState<ScreenId>(getInitialScreen);
  const [history, setHistory] = useState<ScreenId[]>([getInitialScreen()]);

  const navigate = (screen: ScreenId) => {
    setCurrentScreen(screen);
    setHistory((prev) => [...prev, screen]);
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.history) {
      const url = new URL(window.location.href);
      url.searchParams.set('screen', screen);
      window.history.replaceState({}, '', url.toString());
    }
  };

  const goBack = () => {
    if (history.length > 1) {
      const newHistory = [...history];
      newHistory.pop(); // Remove current
      const prevScreen = newHistory[newHistory.length - 1];
      setHistory(newHistory);
      setCurrentScreen(prevScreen);
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.history) {
        const url = new URL(window.location.href);
        url.searchParams.set('screen', prevScreen);
        window.history.replaceState({}, '', url.toString());
      }
    } else {
      navigate('dashboard');
    }
  };

  const resetTo = (screen: ScreenId) => {
    setHistory([screen]);
    setCurrentScreen(screen);
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.history) {
      const url = new URL(window.location.href);
      url.searchParams.set('screen', screen);
      window.history.replaceState({}, '', url.toString());
    }
  };

  // Child Profile
  const [childrenList] = useState<ChildProfile[]>(MOCK_CHILDREN);
  const [selectedChild, setSelectedChildState] = useState<ChildProfile>(MOCK_CHILDREN[0]);
  const [childAgeMonthsById, setChildAgeMonthsById] = useState<Record<string, number>>(
    () => Object.fromEntries(MOCK_CHILDREN.map((child) => [child.id, child.age * 12])),
  );
  const selectedAgeMonths = childAgeMonthsById[selectedChild.id] ?? selectedChild.age * 12;
  const [childLearningProfiles, setChildLearningProfiles] = useState<
    Record<string, ChildLearningProfileInput>
  >({});
  const selectedChildLearningProfile = childLearningProfiles[selectedChild.id] || null;
  const [profileClassificationBusy, setProfileClassificationBusy] = useState(false);
  const profileClassifierLockRef = useRef(false);
  const invalidateP1Selection = () => {
    setContextOptions(null);
    setContextCandidates(null);
    setSelectedBackendActivity(null);
    setActivityRecommendation(null);
    setActivityRecommendationCards([]);
    setRankedActivityIds([]);
    setActivityRankingStatus('IDLE');
  };
  const setSelectedChild = (child: ChildProfile) => {
    setSelectedChildState(child);
    invalidateP1Selection();
  };
  const setSelectedAgeMonths = (ageMonths: number) => {
    if (!Number.isFinite(ageMonths)) return;
    const boundedAgeMonths = Math.max(0, Math.min(155, Math.trunc(ageMonths)));
    setChildAgeMonthsById((current) => ({
      ...current,
      [selectedChild.id]: boundedAgeMonths,
    }));
    invalidateP1Selection();
  };
  const updateSelectedChildLearningProfile = (patch: Partial<ChildLearningProfileInput>) => {
    const contextOnlyPatch = Object.keys(patch).every((key) => (
      key === 'readiness_ids' || key === 'available_material_option_ids'
    ));
    setChildLearningProfiles((current) => {
      const previous = current[selectedChild.id] || {
        profile_declared_by: 'CAREGIVER' as const,
        profile_recorded_at: new Date().toISOString(),
        interest_text: '',
        avoid_text: '',
        proposed_interest_tags: [],
        proposed_avoid_tags: [],
        preference_tags_confirmed: false,
        interests: [],
        dislikes: [],
        readiness_ids: null,
        available_material_option_ids: null,
        adult_participating: null,
        caregiver_participating: null,
        learning_support_ids: [],
      };
      return {
        ...current,
        [selectedChild.id]: {
          ...previous,
          ...patch,
          profile_recorded_at: new Date().toISOString(),
        },
      };
    });
    setContextOptions(null);
    if (!contextOnlyPatch) setContextCandidates(null);
    setSelectedBackendActivity(null);
    setActivityRecommendation(null);
    setActivityRecommendationCards([]);
    setRankedActivityIds([]);
    setActivityRankingStatus('IDLE');
  };
  const classifySelectedChildPreferences = async (
    interestTextDraft?: string,
    avoidTextDraft?: string,
  ): Promise<ChildPreferenceClassification | null> => {
    const profile = childLearningProfiles[selectedChild.id];
    const interestText = (interestTextDraft ?? profile?.interest_text ?? '').trim().slice(0, 240);
    const avoidText = (avoidTextDraft ?? profile?.avoid_text ?? '').trim().slice(0, 240);
    if ((!interestText && !avoidText) || profileClassifierLockRef.current) return null;
    profileClassifierLockRef.current = true;
    setProfileClassificationBusy(true);
    try {
      return await workflowApi.classifyChildPreferences(interestText, avoidText);
    } finally {
      profileClassifierLockRef.current = false;
      setProfileClassificationBusy(false);
    }
  };
  const resetSelectedChildLearningProfile = () => {
    setChildLearningProfiles((current) => {
      const next = { ...current };
      delete next[selectedChild.id];
      return next;
    });
    setContextOptions(null);
    setContextCandidates(null);
    setSelectedBackendActivity(null);
    setActivityRecommendation(null);
    setActivityRecommendationCards([]);
    setRankedActivityIds([]);
    setActivityRankingStatus('IDLE');
  };

  // Drawing
  const [drawingImage, setDrawingImage] = useState<string>('cat-drawing-sample');
  const [selectedDrawing, setSelectedDrawing] = useState<SelectedDrawing | null>(null);
  const [workflowBusy, setWorkflowBusy] = useState<string | null>(null);
  const sessionMutationLockRef = useRef(false);
  const imagePickerLockRef = useRef(false);
  const recordingStartLockRef = useRef(false);
  const recordingStopLockRef = useRef(false);
  const recordingCancelRequestedRef = useRef(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [workflowNotice, setWorkflowNotice] = useState<string | null>(null);
  useEffect(() => {
    setWorkflowNotice(null);
  }, [currentScreen]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionVersion, setSessionVersion] = useState(0);
  const sessionVersionRef = useRef(0);
  const updateSessionVersion = (version: number) => {
    sessionVersionRef.current = version;
    setSessionVersion(version);
  };
  const [sessionState, setSessionState] = useState('NOT_STARTED');
  const [admission, setAdmission] = useState<JsonObject | null>(null);

  // Narration: optional NONE/TEXT/AUDIO input, while the image remains mandatory.
  const [narrationMode, setNarrationMode] = useState<'none' | 'text' | 'audio'>('none');
  const [narrationText, setNarrationText] = useState('');
  const [selectedNarrationAudio, setSelectedNarrationAudio] = useState<SelectedNarrationAudio | null>(null);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isRecordingStarting, setIsRecordingStarting] = useState(false);
  const [voiceDuration, setVoiceDuration] = useState<number>(0);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const recordingRef = useRef<Audio.Recording | null>(null);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recordingElapsedSecondsRef = useRef(0);

  const clearRecordingTimer = () => {
    if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    recordingTimerRef.current = null;
  };

  const startRecording = async (): Promise<boolean> => {
    if (workflowBusy || sessionMutationLockRef.current || isRecording || recordingRef.current
      || recordingStartLockRef.current || recordingStopLockRef.current) return false;
    recordingStartLockRef.current = true;
    setIsRecordingStarting(true);
    recordingCancelRequestedRef.current = false;
    let pendingRecording: Audio.Recording | null = null;
    const discardPendingRecording = async () => {
      const pending = pendingRecording;
      pendingRecording = null;
      if (!pending) return;
      try {
        await pending.stopAndUnloadAsync();
      } catch {
        // A permission/cancel race may leave the recorder only partially prepared.
      }
    };
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (recordingCancelRequestedRef.current) return false;
      if (!permission.granted) {
        setWorkflowError('Cần cấp quyền micro để ghi lời kể, hoặc chọn Nhập chữ.');
        return false;
      }
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      if (recordingCancelRequestedRef.current) return false;
      pendingRecording = new Audio.Recording();
      await pendingRecording.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      if (recordingCancelRequestedRef.current) {
        await discardPendingRecording();
        return false;
      }
      await pendingRecording.startAsync();
      if (recordingCancelRequestedRef.current) {
        await discardPendingRecording();
        return false;
      }
      recordingRef.current = pendingRecording;
      pendingRecording = null;
      setNarrationMode('audio');
      setSelectedNarrationAudio(null);
      recordingElapsedSecondsRef.current = 0;
      setVoiceDuration(0);
      setIsRecording(true);
      recordingTimerRef.current = setInterval(() => {
        const elapsed = Math.min(180, recordingElapsedSecondsRef.current + 1);
        recordingElapsedSecondsRef.current = elapsed;
        setVoiceDuration(elapsed);
        if (elapsed >= 180) void stopRecording();
      }, 1000);
      setWorkflowError(null);
      setWorkflowNotice('Đang ghi lời kể. Chạm Dừng khi nói xong, tối đa 3 phút.');
      return true;
    } catch {
      const cancelled = recordingCancelRequestedRef.current;
      clearRecordingTimer();
      await discardPendingRecording();
      recordingRef.current = null;
      recordingElapsedSecondsRef.current = 0;
      setIsRecording(false);
      if (!cancelled) setWorkflowError('Không thể mở micro trên emulator. Bạn có thể dùng ô Nhập chữ.');
      return false;
    } finally {
      recordingStartLockRef.current = false;
      setIsRecordingStarting(false);
      recordingCancelRequestedRef.current = false;
    }
  };

  const stopRecording = async (): Promise<boolean> => {
    const recording = recordingRef.current;
    if (!recording || recordingStopLockRef.current) return false;
    recordingStopLockRef.current = true;
    clearRecordingTimer();
    try {
      await recording.stopAndUnloadAsync();
      const status = await recording.getStatusAsync();
      const durationMs = status.durationMillis ?? undefined;
      const uri = recording.getURI();
      recordingRef.current = null;
      setIsRecording(false);
      if (!uri) throw new Error('recording-uri-missing');
      setSelectedNarrationAudio({
        uri,
        fileName: `narration-${Date.now()}.m4a`,
        mimeType: 'audio/mp4',
        durationMs,
      });
      const durationSeconds = Math.min(180, Math.round((durationMs ?? 0) / 1000));
      recordingElapsedSecondsRef.current = durationSeconds;
      setVoiceDuration(durationSeconds);
      setWorkflowNotice('Đã ghi lời kể. Chạm tiếp tục khi bạn đã sẵn sàng.');
      return true;
    } catch {
      recordingRef.current = null;
      setIsRecording(false);
      setSelectedNarrationAudio(null);
      setWorkflowError('Không lưu được bản ghi. Hãy thử lại hoặc nhập lời kể bằng chữ.');
      return false;
    } finally {
      clearRecordingTimer();
      recordingStopLockRef.current = false;
    }
  };

  const cancelRecording = async (): Promise<void> => {
    if (recordingStartLockRef.current) {
      recordingCancelRequestedRef.current = true;
      clearRecordingTimer();
      recordingElapsedSecondsRef.current = 0;
      setVoiceDuration(0);
      setIsRecording(false);
      setSelectedNarrationAudio(null);
      return;
    }
    if (recordingStopLockRef.current) return;
    recordingStopLockRef.current = true;
    clearRecordingTimer();
    const recording = recordingRef.current;
    recordingRef.current = null;
    try {
      if (recording) await recording.stopAndUnloadAsync();
    } catch {
      // Discard is best-effort; the local recording must not keep its timer or state alive.
    } finally {
      recordingElapsedSecondsRef.current = 0;
      setVoiceDuration(0);
      setIsRecording(false);
      setSelectedNarrationAudio(null);
      recordingStopLockRef.current = false;
    }
  };

  const toggleRecording = () => {
    void (isRecording ? stopRecording() : startRecording());
  };

  const uploadNarration = async (): Promise<boolean> => {
    if (!sessionId || workflowBusy) return false;
    if (narrationMode === 'none') return true;
    if (narrationMode === 'text') {
      if (!narrationText.trim()) {
        setWorkflowError('Hãy nhập lời kể hoặc chọn Không thêm lời kể.');
        return false;
      }
      return true;
    }
    if (!selectedNarrationAudio) {
      setWorkflowError('Hãy ghi lời kể trước khi tiếp tục.');
      return false;
    }
    if (selectedNarrationAudio.artifactRef && selectedNarrationAudio.sha256 && selectedNarrationAudio.byteLength) {
      return true;
    }
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Tải lời kể');
    setWorkflowError(null);
    try {
      const result = await workflowApi.uploadAudio(sessionId, sessionVersionRef.current, selectedNarrationAudio);
      const payload = asObject(result.payload);
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Chưa nhận được lời kể.');
      updateSessionVersion(result.observed_session_version);
      setSelectedNarrationAudio((previous) => previous ? {
        ...previous,
        artifactRef: textValue(payload.artifact_ref),
        sha256: textValue(payload.sha256),
        byteLength: numberValue(payload.byte_length),
        contentType: textValue(payload.content_type, previous.mimeType),
      } : previous);
      setWorkflowNotice('Lời kể đã sẵn sàng trong phiên khám phá này.');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa gửi được lời kể. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  // AI Pipeline
  const [aiProgress, setAiProgress] = useState<number>(0);
  const [sceneData, setSceneData] = useState<SceneUnderstandingResponse>(MOCK_SCENE_UNDERSTANDING);
  const [analysisClaims, setAnalysisClaims] = useState<AnalysisClaim[]>([]);
  const [topicDirections, setTopicDirections] = useState<TopicDirection[]>([]);
  const [selectedTopicDirectionId, setSelectedTopicDirectionId] = useState<string | null>(null);
  const [selectedClaimIds, setSelectedClaimIds] = useState<string[]>([]);
  const [primaryClaimId, setPrimaryClaimId] = useState<string | null>(null);
  const [subjectTargets, setSubjectTargets] = useState<SubjectTarget[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  const [selectedSubjectSentence, setSelectedSubjectSentence] = useState('');
  const [understandingProgress, setUnderstandingProgress] = useState<JsonObject | null>(null);
  const [directionRequeryUsed, setDirectionRequeryUsed] = useState(false);
  const [correction, setCorrection] = useState('');
  const [gateAConfirmed, setGateAConfirmed] = useState(false);

  const beginWorkflow = async (): Promise<boolean> => {
    if (workflowBusy || imagePickerLockRef.current || !acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Tạo phiên');
    setWorkflowError(null);
    setWorkflowNotice(null);
    try {
      if (recordingStartLockRef.current || recordingStopLockRef.current) {
        setWorkflowError('Hãy dừng ghi âm hiện tại trước khi bắt đầu phiên mới.');
        return false;
      }
      if (recordingRef.current && !(await stopRecording())) return false;
      const result = await workflowApi.createSession();
      const snapshot = asObject(result.payload);
      setSessionId(result.session_id);
      updateSessionVersion(result.observed_session_version);
      setSessionState(textValue(snapshot.state, 'CREATED'));
      setAdmission(null);
      setSelectedDrawing(null);
      setDrawingImage('cat-drawing-sample');
      setNarrationMode('none');
      setNarrationText('');
      setSelectedNarrationAudio(null);
      setVoiceTranscript('');
      setIsRecording(false);
      recordingElapsedSecondsRef.current = 0;
      clearRecordingTimer();
      setVoiceDuration(0);
      setSceneData(MOCK_SCENE_UNDERSTANDING);
      setAnalysisClaims([]);
      setTopicDirections([]);
      setSelectedTopicDirectionId(null);
      setSelectedClaimIds([]);
      setPrimaryClaimId(null);
      setSubjectTargets([]);
      setSelectedSubjectId(null);
      setSelectedSubjectSentence('');
      setUnderstandingProgress(null);
      setDirectionRequeryUsed(false);
      setCorrection('');
      setGateAConfirmed(false);
      setContextOptions(null);
      setContextCandidates(null);
      setSelectedBackendActivity(null);
      setActivityRecommendation(null);
      setActivityRecommendationCards([]);
      setActivitiesList(MOCK_ACTIVITIES);
      setSelectedActivity(MOCK_ACTIVITIES[0]);
      setMaterialsChecklist({});
      setStepsChecklist({});
      setRendererLaunch(null);
      setPixiIntroStoryboard(null);
      setAiProgress(0);
      setCompletionStatus('not_attempted');
      setInterestScore(0);
      setIndependenceScore(0);
      setSelectedObservationTags([]);
      setIsSavingFeedback(false);
      setToastMessage(null);
      setWorkflowNotice('Phiên khám phá đã sẵn sàng. Hãy chọn bức vẽ của con.');
      navigate('capture');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa bắt đầu được phiên mới. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const pickDrawingImage = async (): Promise<boolean> => {
    if (workflowBusy || sessionMutationLockRef.current || imagePickerLockRef.current) return false;
    imagePickerLockRef.current = true;
    setWorkflowError(null);
    setWorkflowNotice(null);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: false,
        allowsMultipleSelection: false,
        exif: false,
        quality: 1,
      });
      if (result.canceled || !result.assets[0]) return false;
      const asset = result.assets[0];
      const prepared = await preparePickedImage(asset);
      const selected: SelectedDrawing = {
        ...prepared,
      };
      setSelectedDrawing(selected);
      setDrawingImage(selected.uri);
      setAdmission(null);
      setWorkflowNotice('Đã chọn ảnh. Chỉ dùng ảnh tổng hợp/ảnh do người lớn tạo cho demo.');
      return true;
    } catch (error) {
      const code = error && typeof error === 'object' && 'code' in error
        ? String(error.code)
        : 'IMAGE_PICKER_FAILED';
      setWorkflowError(code === 'IMAGE_PICKER_FAILED'
        ? 'Không mở được bộ chọn ảnh. Hãy thử lại; ảnh trước đó vẫn được giữ.'
        : imageIntakeErrorMessage(code));
      return false;
    } finally {
      imagePickerLockRef.current = false;
    }
  };

  const uploadDrawing = async (): Promise<boolean> => {
    if (!sessionId || !selectedDrawing || workflowBusy || imagePickerLockRef.current
      || !acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Tải ảnh');
    setWorkflowError(null);
    setWorkflowNotice(null);
    try {
      const result = await workflowApi.uploadImage(sessionId, sessionVersionRef.current, selectedDrawing);
      updateSessionVersion(result.observed_session_version);
      const payload = asObject(result.payload);
      setAdmission(payload);
      if (result.status !== 'SUCCEEDED' || textValue(payload.decision) !== 'ADMITTED') {
        throw workflowFailure(result, 'Ảnh này chưa dùng được. Hãy chọn lại ảnh.');
      }
      setSessionState('CREATED');
      setWorkflowNotice('Ảnh đã sẵn sàng. Chạm tiếp tục để khám phá bức tranh.');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa gửi được ảnh. Hãy chọn ảnh và thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const runAiSimulation = async (): Promise<boolean> => {
    if (!sessionId || !admission || workflowBusy) return false;
    const preparedNarration = prepareNarration(narrationMode, narrationText, selectedNarrationAudio);
    if (!preparedNarration.ok) {
      setWorkflowError(preparedNarration.message);
      return false;
    }
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Phân tích ảnh');
    setWorkflowError(null);
    setWorkflowNotice(null);
    setAiProgress(20);
    try {
      const result = await workflowApi.runUnderstanding(sessionId, sessionVersionRef.current, preparedNarration.narration);
      updateSessionVersion(result.observed_session_version);
      const payload = asObject(result.payload);
      const claims = readAnalysisClaims(payload);
      const progress = asObject(payload.understanding_progress);
      if (claims.length === 0 || progress.gate_a_ready !== true) {
        if (result.status !== 'SUCCEEDED' && !progress.stage) {
          throw workflowFailure(result, 'Chưa đọc được bức tranh.');
        }
        setAnalysisClaims([]);
        setTopicDirections([]);
        setSelectedTopicDirectionId(null);
        setSelectedClaimIds([]);
        setPrimaryClaimId(null);
        setUnderstandingProgress(progress);
        setDirectionRequeryUsed(false);
        setCorrection('');
        setSceneData(mapScenePayload(payload, sessionId));
        setSessionState('GATE_A_PENDING');
        setAiProgress(100);
        setWorkflowNotice('AI chưa nhận ra chủ thể rõ ràng. Người lớn có thể nhập chủ thể, yêu cầu phân tích lại một lần hoặc xác nhận chủ thể đã biết.');
        navigate('scene_understanding');
        return true;
      }
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Chưa đọc được bức tranh.');
      setAnalysisClaims(claims);
      const directions = readTopicDirections(payload, claims);
      setTopicDirections(directions);
      setSelectedTopicDirectionId(directions[0]?.direction_id ?? null);
      setUnderstandingProgress(progress);
      setDirectionRequeryUsed(false);
      setSelectedClaimIds(directions[0]?.source_claim_ids ?? (claims.length > 0 ? [claims[0].observation_id] : []));
      setPrimaryClaimId(directions[0]?.primary_claim_id ?? claims[0]?.observation_id ?? null);
      setSubjectTargets([]);
      setSelectedSubjectId(null);
      setSelectedSubjectSentence('');
      setSceneData(mapScenePayload(payload, sessionId));
      const narrationPayload = asObject(payload.narration);
      setVoiceTranscript(textValue(narrationPayload.transcript));
      setSessionState('GATE_A_PENDING');
      setAiProgress(100);
      setWorkflowNotice('Đã tìm thấy các chủ đề từ bức tranh. Mời người lớn kiểm tra cùng con.');
      navigate('scene_understanding');
      return true;
    } catch (error) {
      setAiProgress(0);
      setWorkflowError(friendlyError(error, 'Chưa đọc được bức tranh. Hãy thử lại với ảnh rõ hơn.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const requerySubject = async (): Promise<boolean> => {
    const selectedDirection = topicDirections.find(
      (direction) => direction.direction_id === selectedTopicDirectionId,
    );
    const subject = correction.trim()
      || (selectedDirection?.requires_requery ? selectedDirection.title_vi : '');
    if (!sessionId || !subject || directionRequeryUsed || workflowBusy) return false;
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Phân tích lại chủ thể');
    setWorkflowError(null);
    setWorkflowNotice(null);
    setDirectionRequeryUsed(true);
    try {
      const progress = understandingProgress || {};
      const result = await workflowApi.requeryUnderstanding(sessionId, sessionVersionRef.current, {
        priorRunId: textValue(progress.run_id, 'manual-subject-recovery'),
        direction: subject,
        revision: numberValue(progress.direction_revision, 0) + 1,
        correction: correction.trim(),
      });
      updateSessionVersion(result.observed_session_version);
      const payload = asObject(result.payload);
      const claims = readAnalysisClaims(payload);
      const directions = readTopicDirections(payload, claims);
      const nextProgress = asObject(payload.understanding_progress);
      setAnalysisClaims(claims);
      setTopicDirections(directions);
      setSelectedTopicDirectionId(directions[0]?.direction_id ?? null);
      setSelectedClaimIds(directions[0]?.source_claim_ids ?? []);
      setPrimaryClaimId(directions[0]?.primary_claim_id ?? null);
      setUnderstandingProgress(nextProgress);
      setSceneData(mapScenePayload(payload, sessionId));
      setSessionState('GATE_A_PENDING');
      if (result.status !== 'SUCCEEDED' || claims.length === 0 || nextProgress.gate_a_ready !== true) {
        setWorkflowNotice(`AI vẫn chưa xác nhận được “${subject}”. Chủ thể này sẽ được ghi rõ là do người lớn nhập và bạn vẫn có thể tiếp tục.`);
        return true;
      }
      setWorkflowNotice(`Đã phân tích lại theo “${subject}”. Hãy kiểm tra chủ thể rồi tiếp tục.`);
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Không phân tích lại được. Bạn vẫn có thể tiếp tục với chủ thể người lớn đã nhập.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const selectSubject = async (target: SubjectTarget): Promise<boolean> => {
    if (!sessionId || workflowBusy || !subjectTargets.some((item) => item.candidateId === target.candidateId)) {
      return false;
    }
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Đang chọn chủ thể');
    setWorkflowError(null);
    try {
      const result = await workflowApi.selectSubject(
        sessionId,
        sessionVersionRef.current,
        target.candidateId,
        target.labelVi,
      );
      updateSessionVersion(result.observed_session_version);
      if (result.status !== 'SUCCEEDED') {
        throw workflowFailure(result, 'Chưa chọn được chủ thể. Hãy thử lại.');
      }
      const payload = asObject(result.payload);
      const selection = asObject(payload.subject_selection);
      const claims = readAnalysisClaims(payload);
      const supportIds = Array.isArray(selection.support_claim_ids)
        ? selection.support_claim_ids.filter((value): value is string => typeof value === 'string')
        : [target.candidateId];
      const selectedId = textValue(selection.selected_subject_id, target.candidateId);
      const sentence = textValue(selection.sentence_vi, `Cùng khám phá ${target.labelVi}!`);
      setAnalysisClaims(claims.length > 0 ? claims : analysisClaims);
      setSubjectTargets(readSubjectTargets(payload).length > 0 ? readSubjectTargets(payload) : subjectTargets);
      setSelectedSubjectId(selectedId);
      setSelectedSubjectSentence(sentence);
      setSelectedClaimIds(Array.from(new Set([selectedId, ...supportIds])));
      setPrimaryClaimId(selectedId);
      setTopicDirections([]);
      setSelectedTopicDirectionId(null);
      setUnderstandingProgress(asObject(payload.understanding_progress));
      setSceneData({ ...mapScenePayload(payload, sessionId), storyTitle: sentence });
      setWorkflowNotice('Đã chọn chủ thể. Mời người lớn kiểm tra câu chuyện.');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa chọn được chủ thể. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const confirmGateA = async (): Promise<boolean> => {
    const adultSubject = correction.trim();
    if (
      !sessionId
      || workflowBusy
      || (!adultSubject && (!primaryClaimId || selectedClaimIds.length === 0))
    ) return false;
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Xác nhận Gate A');
    setWorkflowError(null);
    try {
      const result = await workflowApi.confirmGateA(
        sessionId,
        sessionVersion,
        selectedClaimIds,
        adultSubject ? null : primaryClaimId,
        adultSubject || null,
      );
      updateSessionVersion(result.observed_session_version);
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Chưa xác nhận được chủ đề.');
      setGateAConfirmed(true);
      setSessionState('UNDERSTANDING_PROPOSED');
      setWorkflowNotice('Người lớn đã xác nhận chủ đề. Giờ mình cùng chọn hoạt động nhé.');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa xác nhận được chủ đề. Hãy kiểm tra lựa chọn rồi thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const requestActivityRankingInBackground = (
    session: string,
    version: number,
    ageMonths: number,
    profile: ChildLearningProfileInput,
    cards: ActivityRecommendationCardV2[],
  ) => {
    if (!cards.length) {
      setActivityRankingStatus('IDLE');
      return;
    }
    const token = {};
    activityRankingTokenRef.current = token;
    setRankedActivityIds([]);
    setActivityRankingStatus('PENDING');
    void workflowApi.rankActivitySuggestions(session, version, ageMonths, profile)
      .then((response) => {
        if (activityRankingTokenRef.current !== token) return;
        const result = response.payload;
        const eligibleIds = new Set(cards.map((card) => card.activity_id));
        const rankedIds = result?.ranked_activity_ids;
        if (
          response.status !== 'SUCCEEDED'
          || !rankedIds
          || rankedIds.length !== Math.min(3, cards.length)
          || new Set(rankedIds).size !== rankedIds.length
          || rankedIds.some((id) => !eligibleIds.has(id))
        ) {
          setActivityRankingStatus('UNAVAILABLE');
          return;
        }
        const rankIndex = new Map(rankedIds.map((id, index) => [id, index]));
        const ordered = [...cards].sort((left, right) => (
          (rankIndex.get(left.activity_id) ?? Number.MAX_SAFE_INTEGER)
          - (rankIndex.get(right.activity_id) ?? Number.MAX_SAFE_INTEGER)
          || left.priority - right.priority
        ));
        setRankedActivityIds(rankedIds);
        setActivityRecommendationCards(ordered.map((card, index) => ({
          ...card,
          priority: index + 1,
        })));
        setActivityRankingStatus('COMPLETE');
      })
      .catch(() => {
        if (activityRankingTokenRef.current === token) {
          setActivityRankingStatus('UNAVAILABLE');
        }
      });
  };

  const prepareActivityWorkflow = async (): Promise<boolean> => {
    const hasPreparedActivity = Boolean(
      contextOptions
      && selectedBackendActivity
      && ['GATE_B_PENDING', 'EXPERIENCE_READY', 'HANDOFF_READY', 'COMPLETED'].includes(sessionState),
    );
    if (hasPreparedActivity) {
      setWorkflowError(null);
      setWorkflowNotice('Hoạt động đã sẵn sàng để xem lại.');
      return true;
    }
    if (
      !sessionId
      || !gateAConfirmed
      || sessionState !== 'UNDERSTANDING_PROPOSED'
      || workflowBusy
    ) return false;
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Chuẩn bị hoạt động');
    setWorkflowError(null);
    setWorkflowNotice(null);
    try {
      const ageMonths = selectedAgeMonths;
      if (!contextOptions) {
        const profile = selectedChildLearningProfile;
        if (!profile || profile.adult_participating !== true) {
          throw new Error('Cần xác nhận người lớn sẽ đồng hành trong hoạt động.');
        }
        if (ageMonths < 36 && profile.caregiver_participating !== true) {
          throw new Error('Trẻ dưới 3 tuổi cần có người chăm sóc đồng hành trực tiếp.');
        }
        const optionsResult = await workflowApi.readActivitySuggestions(
          sessionId,
          sessionVersion,
          ageMonths,
          profile,
        );
        const suggestions = optionsResult.payload;
        if (!suggestions) {
          throw new Error('Máy chủ chưa trả danh sách hoạt động phù hợp.');
        }
        setContextOptions(suggestions);
        setSelectedBackendActivity(null);
        setActivityRecommendation(null);
        setActivityRecommendationCards(suggestions.options);
        setRankedActivityIds([]);
        setWorkflowNotice('Đã tải toàn bộ hoạt động phù hợp chủ đề và độ tuổi. Sở thích đã xác nhận được dùng để sắp xếp danh sách.');
        requestActivityRankingInBackground(
          sessionId,
          sessionVersion,
          ageMonths,
          profile,
          suggestions.options,
        );
        return false;
      }

      const options = contextOptions;
      const option = selectedBackendActivity;
      if (!option) {
        throw new Error('Hãy chọn một hoạt động trước khi tiếp tục.');
      }
      const contextResult = await workflowApi.setP1Context(sessionId, sessionVersion, {
        age_months: ageMonths,
        complete_activity_discovery_flow: true,
        readiness_ids: null,
        completed_activity_ids: null,
        available_material_option_ids: null,
        supervision_level: null,
        policy_flags: null,
        candidate_status: null,
        adult_participating: true,
        caregiver_participating: selectedChildLearningProfile?.caregiver_participating === true,
        selected_activity_id: option.activity_id,
        selected_activity_version: option.activity_version,
      });
      updateSessionVersion(contextResult.observed_session_version);
      if (contextResult.status !== 'SUCCEEDED') throw workflowFailure(contextResult, 'Bối cảnh người lớn chưa đủ.');
      const filterResult = await workflowApi.runP1Filter(sessionId, contextResult.observed_session_version);
      updateSessionVersion(filterResult.observed_session_version);
      if (filterResult.status !== 'SUCCEEDED') throw workflowFailure(filterResult, 'Không tìm thấy hoạt động đạt điều kiện.');
      const experienceResult = await workflowApi.prepareExperience(sessionId, filterResult.observed_session_version);
      updateSessionVersion(experienceResult.observed_session_version);
      if (experienceResult.status !== 'SUCCEEDED') {
        throw workflowFailure(experienceResult, 'Chưa chuẩn bị được hoạt động phù hợp.');
      }
      const display = options.options.find((item) => item.activity_id === option.activity_id);
      const activity = mapExperienceToActivity(asObject(experienceResult.payload), display);
      setActivitiesList([activity]);
      setSelectedActivity(activity);
      setContextOptions(options);
      setSelectedBackendActivity(option);
      setActivityRecommendation(null);
      setMaterialsChecklist(Object.fromEntries(activity.materials.map((material) => [material.id, false])));
      setStepsChecklist(Object.fromEntries(activity.steps.map((step) => [step.stepNumber, false])));
      setSessionState('GATE_B_PENDING');
      setWorkflowNotice('Hoạt động đã được chuẩn bị. Mời người lớn xem và xác nhận.');
      return true;
    } catch (error) {
      setWorkflowError(error instanceof Error && !(error instanceof DemoApiError)
        ? error.message
        : friendlyError(error, 'Chưa chuẩn bị được hoạt động phù hợp. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const approveActivity = async (): Promise<boolean> => {
    if (!sessionId || sessionState !== 'GATE_B_PENDING' || workflowBusy) return false;
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Duyệt Gate B');
    setWorkflowError(null);
    try {
      const result = await workflowApi.approveGateB(sessionId, sessionVersion);
      updateSessionVersion(result.observed_session_version);
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Chưa xác nhận được hoạt động.');
      setSessionState('EXPERIENCE_READY');
      setWorkflowNotice('Đã xác nhận hoạt động. Đang chuẩn bị sân khấu chuyển động…');
      try {
        const rendererResult = await workflowApi.prepareRenderer(sessionId, result.observed_session_version);
        updateSessionVersion(rendererResult.observed_session_version);
        if (rendererResult.status !== 'SUCCEEDED') {
          throw workflowFailure(rendererResult, 'Chưa chuẩn bị xong sân khấu chuyển động.');
        }
        const payload = asObject(rendererResult.payload);
        const renderer = payload.renderer_mode === 'PIXI_SHOW_V2'
          ? payload.renderer_show_envelope_v2
          : payload.renderer_mode === 'PIXI_SHOW_V1'
            ? payload.renderer_show_envelope_v1
          : payload.renderer_launch_v2 ?? (
            payload.renderer_mode === 'LEGACY_V1' ? payload.renderer_launch : null
          );
        if (!renderer) throw new Error('Máy chủ chưa trả gói mở Pixi.');
        setRendererLaunch(asObject(renderer));
        setPixiIntroStoryboard(asObject(payload.pixi_intro_storyboard));
        setWorkflowNotice('Sân khấu đã chuẩn bị xong. Đang mở bức vẽ gốc.');
      } catch (error) {
        setWorkflowError(friendlyError(error, 'Chủ đề đã được duyệt; sân khấu sẽ tiếp tục chuẩn bị khi mở.'));
      }
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa xác nhận được hoạt động. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const prepareRendererIntro = async (refreshLaunch = false): Promise<boolean> => {
    if (!sessionId || sessionState !== 'EXPERIENCE_READY' || workflowBusy) return false;
    if (rendererLaunch && !refreshLaunch) return true;
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Mở câu chuyện');
    setWorkflowError(null);
    try {
      const rendererResult = await workflowApi.prepareRenderer(sessionId, sessionVersion);
      updateSessionVersion(rendererResult.observed_session_version);
      if (rendererResult.status !== 'SUCCEEDED') {
        throw workflowFailure(rendererResult, 'Bức tranh chuyển động chưa sẵn sàng.');
      }
      const payload = asObject(rendererResult.payload);
      const renderer = payload.renderer_mode === 'PIXI_SHOW_V2'
        ? payload.renderer_show_envelope_v2
        : payload.renderer_mode === 'PIXI_SHOW_V1'
          ? payload.renderer_show_envelope_v1
        : payload.renderer_launch_v2 ?? (
          payload.renderer_mode === 'LEGACY_V1' ? payload.renderer_launch : null
        );
      if (!renderer) throw new Error('Máy chủ chưa trả gói Pixi hợp lệ.');
      setRendererLaunch(asObject(renderer));
      setPixiIntroStoryboard(asObject(payload.pixi_intro_storyboard));
      setWorkflowNotice('Bức vẽ đã sẵn sàng bước vào câu chuyện.');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa thể mở bức tranh chuyển động. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const completeActivityHandoff = async (): Promise<boolean> => {
    if (!sessionId || sessionState !== 'EXPERIENCE_READY' || workflowBusy) return false;
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setWorkflowBusy('Bàn giao hoạt động');
    setWorkflowError(null);
    try {
      const handoffResult = await workflowApi.completeHandoff(sessionId, sessionVersion);
      updateSessionVersion(handoffResult.observed_session_version);
      if (handoffResult.status !== 'SUCCEEDED') throw workflowFailure(handoffResult, 'Chưa thể bàn giao hoạt động.');
      setSessionState('HANDOFF_READY');
      setWorkflowNotice('Hoạt động đã sẵn sàng. Sau khi hoàn thành, hãy ghi lại vài nhận xét.');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa thể mở phần trải nghiệm. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  // Montessori Activities
  const [activitiesList, setActivitiesList] = useState<MontessoriActivity[]>(MOCK_ACTIVITIES);
  const [selectedActivity, setSelectedActivity] = useState<MontessoriActivity>(MOCK_ACTIVITIES[0]);
  const [contextOptions, setContextOptions] = useState<ActivityRecommendationSetV3 | null>(null);
  const [contextCandidates, setContextCandidates] = useState<ActivityContextCandidateSet | null>(null);
  const [selectedBackendActivity, setSelectedBackendActivity] = useState<ActivityRecommendationCardV2 | null>(null);
  const [activityRecommendation, setActivityRecommendation] = useState<P1ContextOptions['recommendation'] | null>(null);
  const [activityRecommendationCards, setActivityRecommendationCards] = useState<ActivityRecommendationCardV2[]>([]);
  const [rankedActivityIds, setRankedActivityIds] = useState<string[]>([]);
  const [activityRankingStatus, setActivityRankingStatus] = useState<
    'IDLE' | 'PENDING' | 'COMPLETE' | 'UNAVAILABLE'
  >('IDLE');
  const activityRankingTokenRef = useRef<object | null>(null);
  useEffect(() => {
    if (!contextOptions) {
      activityRankingTokenRef.current = null;
      setRankedActivityIds([]);
      setActivityRankingStatus('IDLE');
    }
  }, [contextOptions]);
  const [rendererLaunch, setRendererLaunch] = useState<JsonObject | null>(null);
  const [pixiIntroStoryboard, setPixiIntroStoryboard] = useState<JsonObject | null>(null);

  // Checklists
  const [materialsChecklist, setMaterialsChecklist] = useState<Record<string, boolean>>({});

  const toggleMaterialCheck = (id: string) => {
    setMaterialsChecklist((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const [stepsChecklist, setStepsChecklist] = useState<Record<number, boolean>>({});

  const toggleStepCheck = (stepNumber: number) => {
    setStepsChecklist((prev) => ({
      ...prev,
      [stepNumber]: !prev[stepNumber],
    }));
  };

  // Feedback State
  const [completionStatus, setCompletionStatus] = useState<'completed' | 'partial' | 'not_attempted'>(
    'not_attempted'
  );
  const [interestScore, setInterestScore] = useState<number>(0);
  const [independenceScore, setIndependenceScore] = useState<number>(0);
  const [selectedObservationTags, setSelectedObservationTags] = useState<FeedbackObservationCode[]>([]);
  const [isSavingFeedback, setIsSavingFeedback] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const toggleObservationTag = (tag: FeedbackObservationCode) => {
    setSelectedObservationTags((prev) => prev.includes(tag)
      ? prev.filter((current) => current !== tag)
      : [...prev, tag]);
  };

  const clearToast = () => setToastMessage(null);

  const saveFeedback = async (): Promise<boolean> => {
    if (!sessionId || sessionState !== 'HANDOFF_READY' || workflowBusy) {
      setWorkflowError('Hoạt động chưa hoàn tất. Hãy quay lại bước hướng dẫn trước khi ghi nhận xét.');
      return false;
    }
    if (!acquireSingleFlight(sessionMutationLockRef)) return false;
    setIsSavingFeedback(true);
    setWorkflowBusy('Lưu feedback');
    setWorkflowError(null);
    try {
      const result = await workflowApi.recordFeedback(
        sessionId,
        sessionVersion,
        completionStatus === 'completed' ? 'COMPLETED' : completionStatus === 'partial' ? 'PARTIAL' : 'NOT_ATTEMPTED',
        interestScore || null,
        independenceScore || null,
        selectedObservationTags,
      );
      updateSessionVersion(result.observed_session_version);
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Chưa ghi nhận được nhận xét.');
      if (selectedChildLearningProfile) {
        updateSelectedChildLearningProfile(
          resetSessionBoundProfileAnswers(selectedChildLearningProfile),
        );
      }
      setSessionState('FEEDBACK_RECORDED');
      setToastMessage('✨ Đã ghi nhận nhận xét trong phiên này.');
      setTimeout(() => {
        setToastMessage(null);
        resetTo('dashboard');
      }, 1200);
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa lưu được phản hồi. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
      setIsSavingFeedback(false);
      releaseSingleFlight(sessionMutationLockRef);
    }
  };

  const toggleAnalysisClaim = (claimId: string) => {
    setSelectedClaimIds((previous) => previous.includes(claimId)
      ? previous.filter((id) => id !== claimId)
      : [...previous, claimId]);
  };

  const setPrimaryClaim = (claimId: string) => {
    setPrimaryClaimId(claimId);
    setSelectedClaimIds((previous) => previous.includes(claimId) ? previous : [...previous, claimId]);
  };

  const selectTopicDirection = (directionId: string) => {
    const direction = topicDirections.find((item) => item.direction_id === directionId);
    if (!direction) return;
    setSelectedTopicDirectionId(directionId);
    setPrimaryClaimId(direction.primary_claim_id);
    setSelectedClaimIds(direction.source_claim_ids);
    setSceneData((previous) => ({...previous, storyTitle: direction.title_vi}));
  };

  const selectBackendActivity = (activityId: string) => {
    const option = contextOptions?.options.find((item) => item.activity_id === activityId) || null;
    setSelectedBackendActivity(option);
  };

  return (
    <AppContext.Provider
      value={{
        currentScreen,
        navigate,
        goBack,
        resetTo,
        canGoBack: history.length > 1,

        childrenList,
        selectedChild,
        setSelectedChild,
        selectedAgeMonths,
        setSelectedAgeMonths,
        selectedChildLearningProfile,
        updateSelectedChildLearningProfile,
        resetSelectedChildLearningProfile,
        classifySelectedChildPreferences,
        profileClassificationBusy,

        drawingImage,
        setDrawingImage,
        selectedDrawing,
        pickDrawingImage,
        uploadDrawing,
        workflowBusy,
        workflowError,
        dismissWorkflowError: () => setWorkflowError(null),
        workflowNotice,
        sessionId,
        sessionVersion,
        sessionState,
        admission,
        beginWorkflow,

        narrationMode,
        setNarrationMode,
        narrationText,
        setNarrationText,
        selectedNarrationAudio,
        startRecording,
        stopRecording,
        cancelRecording,
        uploadNarration,
        isRecording,
        isRecordingStarting,
        voiceDuration,
        toggleRecording,
        voiceTranscript,

        aiProgress,
        sceneData,
        runAiSimulation,
        requerySubject,
        directionRequeryUsed,
        analysisClaims,
        topicDirections,
        selectedTopicDirectionId,
        selectTopicDirection,
        selectedClaimIds,
        primaryClaimId,
        toggleAnalysisClaim,
        setPrimaryClaim,
        correction,
        setCorrection,
        confirmGateA,
        gateAConfirmed,
        subjectTargets,
        selectedSubjectId,
        selectedSubjectSentence,
        selectSubject,

        activitiesList,
        selectedActivity,
        setSelectedActivity,
        contextOptions,
        contextCandidates,
        selectedBackendActivity,
        activityRecommendation,
        activityRecommendationCards,
        rankedActivityIds,
        activityRankingStatus,
        selectBackendActivity,
        prepareActivityWorkflow,
        approveActivity,
        prepareRendererIntro,
        completeActivityHandoff,
        rendererLaunch,
        pixiIntroStoryboard,
        materialsChecklist,
        toggleMaterialCheck,
        stepsChecklist,
        toggleStepCheck,

        completionStatus,
        setCompletionStatus,
        interestScore,
        setInterestScore,
        independenceScore,
        setIndependenceScore,
        selectedObservationTags,
        toggleObservationTag,
        isSavingFeedback,
        saveFeedback,
        toastMessage,
        clearToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
