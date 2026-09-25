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
  MAX_IMAGE_BYTES,
  type NarrationInput,
  type ActivityRecommendationCard,
  type P1ContextOption,
  type P1ContextOptions,
  type WorkflowResult,
} from '../demo/api';

export interface SelectedDrawing {
  uri: string;
  fileName: string;
  mimeType: string;
  fileSize?: number;
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
  selectedAgeGroup: string;
  setSelectedAgeGroup: (ageGroup: string) => void;

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
  uploadNarration: () => Promise<boolean>;
  isRecording: boolean;
  voiceDuration: number;
  toggleRecording: () => void;
  setVoiceDuration: (dur: number) => void;
  voiceTranscript: string;

  // AI Pipeline
  aiProgress: number;
  sceneData: SceneUnderstandingResponse;
  runAiSimulation: () => Promise<boolean>;
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
  subjectTargets: SubjectTarget[];
  selectedSubjectId: string | null;
  selectedSubjectSentence: string;
  selectSubject: (target: SubjectTarget) => Promise<boolean>;

  // Montessori Activity
  activitiesList: MontessoriActivity[];
  selectedActivity: MontessoriActivity;
  setSelectedActivity: (activity: MontessoriActivity) => void;
  contextOptions: P1ContextOptions | null;
  selectedBackendActivity: P1ContextOption | null;
  activityRecommendation: P1ContextOptions['recommendation'] | null;
  activityRecommendationCards: ActivityRecommendationCard[];
  selectBackendActivity: (activityId: string) => void;
  prepareActivityWorkflow: () => Promise<boolean>;
  approveActivity: () => Promise<boolean>;
  prepareRendererIntro: () => Promise<boolean>;
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
  selectedObservationTags: string[];
  toggleObservationTag: (tag: string) => void;
  parentNotes: string;
  setParentNotes: (notes: string) => void;
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
  branch: 'cành cây',
  leaf: 'chiếc lá',
  leaves: 'những chiếc lá',
  perching: 'đậu trên cành',
  'bird on branch': 'con chim đậu trên cành cây',
  'outdoor scene': 'khung cảnh ngoài trời',
  cat: 'con mèo',
  dog: 'con chó',
};

const BACKGROUND_LABELS = new Set([
  'grass', 'ground', 'nature', 'background', 'sky', 'cỏ', 'bãi cỏ', 'thiên nhiên', 'bầu trời',
]);

function displayLabelVi(value: string): string {
  const cleaned = value.trim();
  const translated = DISPLAY_LABELS_VI[cleaned.toLowerCase()];
  if (translated) return translated;
  return /^[A-Za-z][A-Za-z\s-]*$/.test(cleaned) ? 'chi tiết trong tranh' : cleaned;
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
    const leftBackground = BACKGROUND_LABELS.has((left.rawLabel || left.label.value).toLowerCase()) ? 1 : 0;
    const rightBackground = BACKGROUND_LABELS.has((right.rawLabel || right.label.value).toLowerCase()) ? 1 : 0;
    const kindRank = { subject: 0, action: 1, story: 2 };
    return leftBackground - rightBackground
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
    safeReason || fallback,
    textValue(result.failure?.code, nestedCode || 'WORKFLOW_BLOCKED'),
    409,
    result.failure?.retryable === true || nestedFailure.retryable === true,
  );
}

function friendlyError(error: unknown, fallback: string): string {
  if (!(error instanceof DemoApiError)) return fallback;
  if (error.code === 'NETWORK_ERROR') return 'Chưa kết nối được với máy chủ. Hãy kiểm tra mạng rồi thử lại.';
  if (error.code === 'REQUEST_TIMEOUT') return 'Máy chủ đang xử lý lâu hơn dự kiến. Bạn có thể thử lại.';
  return fallback;
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
  display?: ActivityRecommendationCard,
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
  const [selectedChild, setSelectedChild] = useState<ChildProfile>(MOCK_CHILDREN[0]);
  const [selectedAgeGroup, setSelectedAgeGroup] = useState<string>('5-6');

  // Drawing
  const [drawingImage, setDrawingImage] = useState<string>('cat-drawing-sample');
  const [selectedDrawing, setSelectedDrawing] = useState<SelectedDrawing | null>(null);
  const [workflowBusy, setWorkflowBusy] = useState<string | null>(null);
  const activityWorkflowLockRef = useRef(false);
  const understandingRequestLockRef = useRef(false);
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
  const [voiceDuration, setVoiceDuration] = useState<number>(0);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const recordingRef = useRef<Audio.Recording | null>(null);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startRecording = async (): Promise<boolean> => {
    if (workflowBusy || isRecording) return false;
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        setWorkflowError('Cần cấp quyền micro để ghi lời kể, hoặc chọn Nhập chữ.');
        return false;
      }
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      await recording.startAsync();
      recordingRef.current = recording;
      setNarrationMode('audio');
      setSelectedNarrationAudio(null);
      setVoiceDuration(0);
      setIsRecording(true);
      recordingTimerRef.current = setInterval(() => {
        setVoiceDuration((current) => {
          if (current >= 180) {
            void stopRecording();
            return current;
          }
          return current + 1;
        });
      }, 1000);
      setWorkflowError(null);
      setWorkflowNotice('Đang ghi lời kể. Chạm Dừng khi nói xong, tối đa 3 phút.');
      return true;
    } catch {
      recordingRef.current = null;
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
      setIsRecording(false);
      setWorkflowError('Không thể mở micro trên emulator. Bạn có thể dùng ô Nhập chữ.');
      return false;
    }
  };

  const stopRecording = async (): Promise<boolean> => {
    const recording = recordingRef.current;
    if (!recording) return false;
    try {
      await recording.stopAndUnloadAsync();
      const status = await recording.getStatusAsync();
      const durationMs = status.durationMillis ?? undefined;
      const uri = recording.getURI();
      recordingRef.current = null;
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
      setIsRecording(false);
      if (!uri) throw new Error('recording-uri-missing');
      setSelectedNarrationAudio({
        uri,
        fileName: `narration-${Date.now()}.m4a`,
        mimeType: 'audio/mp4',
        durationMs,
      });
      setVoiceDuration(Math.round((durationMs ?? 0) / 1000));
      setWorkflowNotice('Đã ghi lời kể. Chạm tiếp tục khi bạn đã sẵn sàng.');
      return true;
    } catch {
      recordingRef.current = null;
      setIsRecording(false);
      setWorkflowError('Không lưu được bản ghi. Hãy thử lại hoặc nhập lời kể bằng chữ.');
      return false;
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
    if (workflowBusy) return false;
    setWorkflowBusy('Tạo phiên');
    setWorkflowError(null);
    setWorkflowNotice(null);
    try {
      const result = await workflowApi.createSession();
      const snapshot = asObject(result.payload);
      setSessionId(result.session_id);
      updateSessionVersion(result.observed_session_version);
      setSessionState(textValue(snapshot.state, 'CREATED'));
      setAdmission(null);
      setNarrationMode('none');
      setNarrationText('');
      setSelectedNarrationAudio(null);
      setVoiceTranscript('');
      setIsRecording(false);
      setVoiceDuration(0);
      setAnalysisClaims([]);
      setTopicDirections([]);
      setSelectedTopicDirectionId(null);
      setSelectedClaimIds([]);
      setPrimaryClaimId(null);
      setSubjectTargets([]);
      setSelectedSubjectId(null);
      setSelectedSubjectSentence('');
      setGateAConfirmed(false);
      setContextOptions(null);
      setSelectedBackendActivity(null);
      setActivityRecommendation(null);
      setRendererLaunch(null);
      setPixiIntroStoryboard(null);
      setAiProgress(0);
      setWorkflowNotice('Phiên khám phá đã sẵn sàng. Hãy chọn bức vẽ của con.');
      navigate('capture');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa bắt đầu được phiên mới. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
    }
  };

  const pickDrawingImage = async (): Promise<boolean> => {
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
      if (asset.fileSize !== undefined && asset.fileSize > MAX_IMAGE_BYTES) {
        setWorkflowError('Ảnh vượt giới hạn demo 5 MB.');
        return false;
      }
      const isPng = asset.fileName?.toLowerCase().endsWith('.png') || asset.mimeType === 'image/png';
      const selected: SelectedDrawing = {
        uri: asset.uri,
        fileName: asset.fileName || `sketch-${Date.now()}${isPng ? '.png' : '.jpg'}`,
        mimeType: isPng ? 'image/png' : 'image/jpeg',
        fileSize: asset.fileSize,
      };
      setSelectedDrawing(selected);
      setDrawingImage(selected.uri);
      setAdmission(null);
      setWorkflowNotice('Đã chọn ảnh. Chỉ dùng ảnh tổng hợp/ảnh do người lớn tạo cho demo.');
      return true;
    } catch {
      setWorkflowError('Không mở được bộ chọn ảnh Android.');
      return false;
    }
  };

  const uploadDrawing = async (): Promise<boolean> => {
    if (!sessionId || !selectedDrawing || workflowBusy) return false;
    setWorkflowBusy('Tải ảnh');
    setWorkflowError(null);
    setWorkflowNotice(null);
    try {
      const result = await workflowApi.uploadImage(sessionId, sessionVersion, selectedDrawing);
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
    }
  };

  const runAiSimulation = async (): Promise<boolean> => {
    if (!sessionId || !admission || workflowBusy || understandingRequestLockRef.current) return false;
    understandingRequestLockRef.current = true;
    let narration: NarrationInput = { kind: 'NONE' };
    if (narrationMode === 'text') {
      const text = narrationText.trim();
      if (!text) {
        setWorkflowError('Hãy nhập lời kể hoặc chọn Không thêm lời kể.');
        return false;
      }
      narration = { kind: 'TEXT', text, language: 'vi', provenance: 'TEXT_TYPED' };
    } else if (narrationMode === 'audio') {
      if (!selectedNarrationAudio?.artifactRef || !selectedNarrationAudio.sha256 || !selectedNarrationAudio.byteLength) {
        setWorkflowError('Lời kể chưa được upload. Quay lại bước ảnh và thử lại.');
        return false;
      }
      narration = {
        kind: 'AUDIO',
        artifact_ref: selectedNarrationAudio.artifactRef,
        sha256: selectedNarrationAudio.sha256,
        content_type: selectedNarrationAudio.contentType || selectedNarrationAudio.mimeType,
        byte_length: selectedNarrationAudio.byteLength,
        provenance: 'RECORDED_AUDIO',
      };
    }
    setWorkflowBusy('Phân tích ảnh');
    setWorkflowError(null);
    setWorkflowNotice(null);
    setAiProgress(20);
    try {
      const result = await workflowApi.runUnderstanding(sessionId, sessionVersion, narration);
      updateSessionVersion(result.observed_session_version);
      const payload = asObject(result.payload);
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Chưa đọc được bức tranh.');
      const claims = readAnalysisClaims(payload);
      const progress = asObject(payload.understanding_progress);
      if (claims.length === 0 || progress.gate_a_ready !== true) {
        throw workflowFailure(
          result,
          'Mình chưa tìm thấy đủ chi tiết đáng tin cậy. Hãy thử lại với ảnh rõ hơn.',
        );
      }
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
      understandingRequestLockRef.current = false;
    }
  };

  const selectSubject = async (target: SubjectTarget): Promise<boolean> => {
    if (!sessionId || workflowBusy || !subjectTargets.some((item) => item.candidateId === target.candidateId)) {
      return false;
    }
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
    }
  };

  const confirmGateA = async (): Promise<boolean> => {
    if (!sessionId || !primaryClaimId || selectedClaimIds.length === 0 || workflowBusy) return false;
    setWorkflowBusy('Xác nhận Gate A');
    setWorkflowError(null);
    try {
      const selectedDirection = topicDirections.find(
        (direction) => direction.direction_id === selectedTopicDirectionId,
      );
      const currentDirection = analysisClaims.find((claim) => claim.observation_id === primaryClaimId);
      const currentProgress = understandingProgress || {};
      const directionChanged = selectedDirection?.requires_requery === true;
      if (!directionRequeryUsed && (directionChanged || correction.trim())) {
        const requery = await workflowApi.requeryUnderstanding(sessionId, sessionVersion, {
          priorRunId: textValue(currentProgress.run_id, 'initial-understanding'),
          direction: selectedDirection?.title_vi || currentDirection?.label.value || correction.trim(),
          revision: numberValue(currentProgress.direction_revision, 0) + 1,
          correction: correction.trim(),
        });
        updateSessionVersion(requery.observed_session_version);
        if (requery.status !== 'SUCCEEDED') {
          throw workflowFailure(requery, 'Chưa tạo lại được đề xuất theo hướng đã chọn.');
        }
        const requeryPayload = asObject(requery.payload);
        const requeryClaims = readAnalysisClaims(requeryPayload);
        const requeryDirections = readTopicDirections(requeryPayload, requeryClaims);
        const requeryProgress = asObject(requeryPayload.understanding_progress);
        if (requeryClaims.length === 0 || requeryProgress.gate_a_ready !== true) {
          throw workflowFailure(requery, 'Chưa tạo được đề xuất mới đủ căn cứ.');
        }
        const matchingClaim = requeryClaims.find(
          (claim) => claim.label.value.toLowerCase() === currentDirection?.label.value.toLowerCase(),
        ) || requeryClaims[0];
        setAnalysisClaims(requeryClaims);
        setTopicDirections(requeryDirections);
        setSelectedTopicDirectionId(requeryDirections[0]?.direction_id ?? null);
        setUnderstandingProgress(requeryProgress);
        setDirectionRequeryUsed(true);
        setSelectedClaimIds(requeryDirections[0]?.source_claim_ids ?? [matchingClaim.observation_id]);
        setPrimaryClaimId(requeryDirections[0]?.primary_claim_id ?? matchingClaim.observation_id);
        setSceneData(mapScenePayload(requeryPayload, sessionId));
        setWorkflowNotice('Đã xem lại theo hướng mới. Mời người lớn xác nhận chủ đề.');
        return false;
      }
      const result = await workflowApi.confirmGateA(
        sessionId,
        sessionVersion,
        selectedClaimIds,
        primaryClaimId,
        correction.trim() || null,
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
    }
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
      || activityWorkflowLockRef.current
    ) return false;
    activityWorkflowLockRef.current = true;
    setWorkflowBusy('Chuẩn bị hoạt động');
    setWorkflowError(null);
    setWorkflowNotice(null);
    try {
      const ageMonths = Math.min(155, Math.max(0, selectedChild.age * 12));
      let options = contextOptions;
      let option = selectedBackendActivity;
      if (!options) {
        const optionsResult = await workflowApi.readContextOptions(sessionId, sessionVersion, ageMonths);
        options = optionsResult.payload;
        if (!options || options.options.length === 0) {
          throw new Error('Chưa tìm thấy hoạt động thật sự phù hợp. Hãy chọn lại chủ đề hoặc thử ảnh rõ hơn.');
        }
        option = options.options[0];
        setContextOptions(options);
        setSelectedBackendActivity(option);
        setActivityRecommendation(options.recommendation || null);
        setActivityRecommendationCards(options.activity_recommendations?.options || []);
        setWorkflowNotice('Đã tìm thấy các hoạt động phù hợp. Người lớn chọn một hoạt động để tiếp tục.');
        return false;
      }
      if (!option) {
        throw new Error('Hãy chọn một hoạt động trước khi tiếp tục.');
      }
      const contextResult = await workflowApi.setP1Context(sessionId, sessionVersion, {
        age_months: ageMonths,
        readiness_ids: option.readiness_ids,
        completed_activity_ids: option.prerequisite_activity_ids,
        available_material_option_ids: option.material_option_ids,
        supervision_level: option.minimum_supervision,
        policy_flags: option.policy_constraints,
        candidate_status: 'ACTIVE_FIXTURE',
        selected_activity_id: option.activity_ref.id,
        selected_activity_version: option.activity_ref.version,
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
      const display = options.activity_recommendations?.options.find(
        (item) => item.activity_id === option?.activity_ref.id,
      );
      const activity = mapExperienceToActivity(asObject(experienceResult.payload), display);
      setActivitiesList([activity]);
      setSelectedActivity(activity);
      setContextOptions(options);
      setSelectedBackendActivity(option);
      setActivityRecommendation(options.recommendation || null);
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
      activityWorkflowLockRef.current = false;
      setWorkflowBusy(null);
    }
  };

  const approveActivity = async (): Promise<boolean> => {
    if (!sessionId || sessionState !== 'GATE_B_PENDING' || workflowBusy) return false;
    setWorkflowBusy('Duyệt Gate B');
    setWorkflowError(null);
    try {
      const result = await workflowApi.approveGateB(sessionId, sessionVersion);
      updateSessionVersion(result.observed_session_version);
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Chưa xác nhận được hoạt động.');
      setSessionState('EXPERIENCE_READY');
      setWorkflowNotice('Hoạt động đã được xác nhận. Bức vẽ gốc vẫn được giữ nguyên.');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa xác nhận được hoạt động. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
    }
  };

  const prepareRendererIntro = async (): Promise<boolean> => {
    if (!sessionId || sessionState !== 'EXPERIENCE_READY' || workflowBusy) return false;
    if (rendererLaunch) return true;
    setWorkflowBusy('Mở câu chuyện');
    setWorkflowError(null);
    try {
      const rendererResult = await workflowApi.prepareRenderer(sessionId, sessionVersion);
      if (rendererResult.status !== 'SUCCEEDED') {
        throw workflowFailure(rendererResult, 'Bức tranh chuyển động chưa sẵn sàng.');
      }
      const payload = asObject(rendererResult.payload);
      setRendererLaunch(asObject(payload.renderer_launch));
      setPixiIntroStoryboard(asObject(payload.pixi_intro_storyboard));
      setWorkflowNotice('Bức vẽ đã sẵn sàng bước vào câu chuyện.');
      return true;
    } catch (error) {
      setWorkflowError(friendlyError(error, 'Chưa thể mở bức tranh chuyển động. Hãy thử lại.'));
      return false;
    } finally {
      setWorkflowBusy(null);
    }
  };

  const completeActivityHandoff = async (): Promise<boolean> => {
    if (!sessionId || sessionState !== 'EXPERIENCE_READY' || workflowBusy) return false;
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
    }
  };

  // Montessori Activities
  const [activitiesList, setActivitiesList] = useState<MontessoriActivity[]>(MOCK_ACTIVITIES);
  const [selectedActivity, setSelectedActivity] = useState<MontessoriActivity>(MOCK_ACTIVITIES[0]);
  const [contextOptions, setContextOptions] = useState<P1ContextOptions | null>(null);
  const [selectedBackendActivity, setSelectedBackendActivity] = useState<P1ContextOption | null>(null);
  const [activityRecommendation, setActivityRecommendation] = useState<P1ContextOptions['recommendation'] | null>(null);
  const [activityRecommendationCards, setActivityRecommendationCards] = useState<ActivityRecommendationCard[]>([]);
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
  const [selectedObservationTags, setSelectedObservationTags] = useState<string[]>([
    'Nhớ vòi bướm hút mật',
    'Tự tay dán cánh',
  ]);
  const [parentNotes, setParentNotes] = useState<string>(
    'Bé An rất vui khi cầm chú bướm giấy tự làm đi quanh nhà vờ như bướm bay hút mật hoa!'
  );
  const [isSavingFeedback, setIsSavingFeedback] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const toggleObservationTag = (tag: string) => {
    setSelectedObservationTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const clearToast = () => setToastMessage(null);

  const saveFeedback = async (): Promise<boolean> => {
    if (!sessionId || sessionState !== 'HANDOFF_READY' || workflowBusy) {
      setWorkflowError('Hoạt động chưa hoàn tất. Hãy quay lại bước hướng dẫn trước khi ghi nhận xét.');
      return false;
    }
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
    const option = contextOptions?.options.find((item) => item.activity_ref.id === activityId) || null;
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
        selectedAgeGroup,
        setSelectedAgeGroup,

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
        uploadNarration,
        isRecording,
        voiceDuration,
        toggleRecording,
        setVoiceDuration,
        voiceTranscript,

        aiProgress,
        sceneData,
        runAiSimulation,
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
        subjectTargets,
        selectedSubjectId,
        selectedSubjectSentence,
        selectSubject,

        activitiesList,
        selectedActivity,
        setSelectedActivity,
        contextOptions,
        selectedBackendActivity,
        activityRecommendation,
        activityRecommendationCards,
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
        parentNotes,
        setParentNotes,
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
