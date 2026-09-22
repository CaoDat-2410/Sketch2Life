import React, { createContext, useContext, useRef, useState } from 'react';
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
  confidence: number;
  kind: 'subject' | 'action' | 'story';
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
  selectedClaimIds: string[];
  primaryClaimId: string | null;
  toggleAnalysisClaim: (claimId: string) => void;
  setPrimaryClaim: (claimId: string) => void;
  correction: string;
  setCorrection: (value: string) => void;
  confirmGateA: () => Promise<boolean>;

  // Montessori Activity
  activitiesList: MontessoriActivity[];
  selectedActivity: MontessoriActivity;
  setSelectedActivity: (activity: MontessoriActivity) => void;
  contextOptions: P1ContextOptions | null;
  selectedBackendActivity: P1ContextOption | null;
  prepareActivityWorkflow: () => Promise<boolean>;
  approveActivity: () => Promise<boolean>;
  completeActivityHandoff: () => Promise<boolean>;
  rendererLaunch: Record<string, unknown> | null;
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

function readAnalysisClaims(payload: JsonObject): AnalysisClaim[] {
  const buckets: Array<[unknown, AnalysisClaim['kind']]> = [
    [payload.entities, 'subject'],
    [payload.actions, 'action'],
    [payload.themes, 'story'],
  ];
  return buckets.flatMap(([items, kind]) => objectArray(items).flatMap((item) => {
    const label = asObject(item.label);
    if (
      typeof item.observation_id !== 'string'
      || typeof label.value !== 'string'
      || typeof item.confidence !== 'number'
    ) return [];
    return [{
      observation_id: item.observation_id,
      label: { value: label.value },
      confidence: item.confidence,
      kind,
    }];
  }));
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
  return {
    storyId: sessionId,
    entities,
    voiceTranscript: textValue(narration.transcript, 'Không có lời kể trong phiên này.'),
    complimentTitle: 'AI đã đọc được bức tranh!',
    complimentSub: 'Đây là đề xuất từ ảnh thật vừa gửi lên backend; người lớn vẫn cần xác nhận Gate A.',
    storyTitle: 'Câu chuyện từ ' + primary,
    storySubtitle: 'Bản xem trước tĩnh từ ảnh gốc; video chưa nằm trong phạm vi demo.',
  };
}

function workflowFailure(result: WorkflowResult<Record<string, unknown>>, fallback: string): Error {
  const payload = asObject(result.payload);
  const nestedFailure = asObject(payload.failure);
  const narration = asObject(payload.narration);
  const asr = asObject(narration.asr);
  const nestedCode = textValue(nestedFailure.code, textValue(asr.error_code));
  const nestedDetail = textValue(nestedFailure.upstream_detail, textValue(asr.error_detail));
  const nestedMessage = nestedCode
    ? `Backend phân tích thất bại (${nestedCode}${nestedDetail ? `: ${nestedDetail}` : ''}).`
    : '';
  return new DemoApiError(
    textValue(result.failure?.safe_message, textValue(payload.guidance, nestedMessage || fallback)),
    textValue(result.failure?.code, nestedCode || 'WORKFLOW_BLOCKED'),
    409,
    result.failure?.retryable === true || nestedFailure.retryable === true,
  );
}

function materialTypeForId(id: string): 'paper' | 'scissors' | 'crayon' | 'glue' | 'general' {
  const value = id.toLowerCase();
  if (value.includes('paper') || value.includes('giấy')) return 'paper';
  if (value.includes('scissor') || value.includes('kéo')) return 'scissors';
  if (value.includes('crayon') || value.includes('color') || value.includes('màu')) return 'crayon';
  if (value.includes('glue') || value.includes('keo')) return 'glue';
  return 'general';
}

function mapExperienceToActivity(payload: JsonObject): MontessoriActivity {
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
    title: textValue(template.template_id, 'Hoạt động từ catalog backend'),
    subtitle: textValue(bridge.sentence_vi, 'Hoạt động được chọn từ anchor đã được người lớn xác nhận.'),
    ageGroup: String(minAge / 12) + '–' + String(maxAge / 12) + ' tuổi',
    durationMinutes: 30,
    category: textValue(focus.child_facing_goal_vi, 'Montessori'),
    materials: materials.map((value, index) => {
      const id = textValue(value, 'material-' + String(index + 1));
      return { id, name: id.replace(/[-_]/g, ' '), type: materialTypeForId(id), isReady: false };
    }),
    steps: steps.map((value, index) => ({ stepNumber: index + 1, title: textValue(value, 'Bước ' + String(index + 1)), isDone: false })),
    safetyNotes: safety.map((value) => textValue(value)),
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
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [workflowNotice, setWorkflowNotice] = useState<string | null>(null);
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
      setWorkflowNotice('Đã ghi lời kể. Nút tiếp tục sẽ upload audio rồi mới gọi ASR.');
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
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Backend không nhận được lời kể.');
      updateSessionVersion(result.observed_session_version);
      setSelectedNarrationAudio((previous) => previous ? {
        ...previous,
        artifactRef: textValue(payload.artifact_ref),
        sha256: textValue(payload.sha256),
        byteLength: numberValue(payload.byte_length),
        contentType: textValue(payload.content_type, previous.mimeType),
      } : previous);
      setWorkflowNotice('Lời kể đã được upload trong phiên tạm. Chưa gọi ASR cho tới nút phân tích.');
      return true;
    } catch (error) {
      setWorkflowError(error instanceof DemoApiError ? error.message : 'Backend không nhận được lời kể.');
      return false;
    } finally {
      setWorkflowBusy(null);
    }
  };

  // AI Pipeline
  const [aiProgress, setAiProgress] = useState<number>(0);
  const [sceneData, setSceneData] = useState<SceneUnderstandingResponse>(MOCK_SCENE_UNDERSTANDING);
  const [analysisClaims, setAnalysisClaims] = useState<AnalysisClaim[]>([]);
  const [selectedClaimIds, setSelectedClaimIds] = useState<string[]>([]);
  const [primaryClaimId, setPrimaryClaimId] = useState<string | null>(null);
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
      setSelectedClaimIds([]);
      setPrimaryClaimId(null);
      setGateAConfirmed(false);
      setContextOptions(null);
      setSelectedBackendActivity(null);
      setRendererLaunch(null);
      setAiProgress(0);
      setWorkflowNotice('Đã tạo phiên tạm trên backend. Chưa gửi ảnh hay tiêu tốn credit.');
      navigate('capture');
      return true;
    } catch (error) {
      setWorkflowError(error instanceof DemoApiError ? error.message : 'Không tạo được phiên backend.');
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
        throw workflowFailure(result, 'Backend yêu cầu chọn lại ảnh.');
      }
      setSessionState('CREATED');
      setWorkflowNotice('Ảnh đã qua admission. Chỉ nút phân tích tiếp theo mới gọi Lightning.');
      return true;
    } catch (error) {
      setWorkflowError(error instanceof DemoApiError ? error.message : 'Backend không nhận ảnh.');
      return false;
    } finally {
      setWorkflowBusy(null);
    }
  };

  const runAiSimulation = async (): Promise<boolean> => {
    if (!sessionId || !admission || workflowBusy) return false;
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
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Backend không trả kết quả phân tích.');
      const claims = readAnalysisClaims(payload);
      setAnalysisClaims(claims);
      setSelectedClaimIds(claims.map((claim) => claim.observation_id));
      setPrimaryClaimId(claims[0]?.observation_id ?? null);
      setSceneData(mapScenePayload(payload, sessionId));
      const narrationPayload = asObject(payload.narration);
      setVoiceTranscript(textValue(narrationPayload.transcript));
      setSessionState('GATE_A_PENDING');
      setAiProgress(100);
      setWorkflowNotice('Đã nhận kết quả Lightning/backend. Hãy kiểm tra và xác nhận Gate A.');
      navigate('scene_understanding');
      return true;
    } catch (error) {
      setAiProgress(0);
      setWorkflowError(error instanceof DemoApiError ? error.message : 'Không phân tích được ảnh.');
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
      const result = await workflowApi.confirmGateA(
        sessionId,
        sessionVersion,
        selectedClaimIds,
        primaryClaimId,
        correction.trim() || null,
      );
      updateSessionVersion(result.observed_session_version);
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Backend chưa nhận Gate A.');
      setGateAConfirmed(true);
      setSessionState('UNDERSTANDING_PROPOSED');
      setWorkflowNotice('Gate A đã được người lớn xác nhận; có thể tạo lựa chọn hoạt động.');
      return true;
    } catch (error) {
      setWorkflowError(error instanceof DemoApiError ? error.message : 'Không xác nhận được Gate A.');
      return false;
    } finally {
      setWorkflowBusy(null);
    }
  };

  const prepareActivityWorkflow = async (): Promise<boolean> => {
    if (!sessionId || !gateAConfirmed || workflowBusy) return false;
    setWorkflowBusy('Chuẩn bị hoạt động');
    setWorkflowError(null);
    try {
      const ageMonths = Math.min(155, Math.max(0, selectedChild.age * 12));
      const optionsResult = await workflowApi.readContextOptions(sessionId, sessionVersion, ageMonths);
      const options = optionsResult.payload;
      if (!options || options.options.length === 0) throw new Error('Backend không có hoạt động phù hợp với anchor/độ tuổi.');
      setContextOptions(options);
      const option = options.options[0];
      setSelectedBackendActivity(option);
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
      if (experienceResult.status !== 'SUCCEEDED') throw workflowFailure(experienceResult, 'Không tạo được ExperienceSpec.');
      const activity = mapExperienceToActivity(asObject(experienceResult.payload));
      setActivitiesList([activity]);
      setSelectedActivity(activity);
      setMaterialsChecklist(Object.fromEntries(activity.materials.map((material) => [material.id, false])));
      setStepsChecklist(Object.fromEntries(activity.steps.map((step) => [step.stepNumber, false])));
      setSessionState('GATE_B_PENDING');
      setWorkflowNotice('Backend đã chuẩn bị hoạt động và ExperienceSpec. Hãy xem rồi duyệt Gate B.');
      return true;
    } catch (error) {
      setWorkflowError(error instanceof DemoApiError ? error.message : error instanceof Error ? error.message : 'Không chuẩn bị được hoạt động.');
      return false;
    } finally {
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
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Backend chưa nhận Gate B.');
      setSessionState('EXPERIENCE_READY');
      setWorkflowNotice('Gate B đã duyệt. Video không được gọi; learning media dùng fallback/Pixi original-art.');
      return true;
    } catch (error) {
      setWorkflowError(error instanceof DemoApiError ? error.message : 'Không duyệt được Gate B.');
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
      const rendererResult = await workflowApi.prepareRenderer(sessionId, sessionVersion);
      if (rendererResult.status !== 'SUCCEEDED') throw workflowFailure(rendererResult, 'Pixi renderer chưa sẵn sàng.');
      setRendererLaunch(asObject(rendererResult.payload).renderer_launch as JsonObject);
      const handoffResult = await workflowApi.completeHandoff(sessionId, sessionVersion);
      updateSessionVersion(handoffResult.observed_session_version);
      if (handoffResult.status !== 'SUCCEEDED') throw workflowFailure(handoffResult, 'Chưa thể bàn giao hoạt động.');
      setSessionState('HANDOFF_READY');
      setWorkflowNotice('Hoạt động đã được bàn giao; có thể ghi feedback phiên chạy.');
      return true;
    } catch (error) {
      setWorkflowError(error instanceof DemoApiError ? error.message : 'Không thể bàn giao hoạt động.');
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
  const [rendererLaunch, setRendererLaunch] = useState<JsonObject | null>(null);

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
    'completed'
  );
  const [interestScore, setInterestScore] = useState<number>(5);
  const [independenceScore, setIndependenceScore] = useState<number>(4);
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
      setWorkflowError('Backend chưa ở trạng thái bàn giao; feedback chưa được gửi.');
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
      if (result.status !== 'SUCCEEDED') throw workflowFailure(result, 'Backend không nhận feedback.');
      setSessionState('FEEDBACK_RECORDED');
      setToastMessage('✨ Đã ghi feedback cho phiên chạy tạm.');
      setTimeout(() => {
        setToastMessage(null);
        resetTo('dashboard');
      }, 1200);
      return true;
    } catch (error) {
      setWorkflowError(error instanceof DemoApiError ? error.message : 'Feedback chưa được lưu.');
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
        selectedClaimIds,
        primaryClaimId,
        toggleAnalysisClaim,
        setPrimaryClaim,
        correction,
        setCorrection,
        confirmGateA,

        activitiesList,
        selectedActivity,
        setSelectedActivity,
        contextOptions,
        selectedBackendActivity,
        prepareActivityWorkflow,
        approveActivity,
        completeActivityHandoff,
        rendererLaunch,
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
