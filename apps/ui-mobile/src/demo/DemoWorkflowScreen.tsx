import React, { useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import * as Crypto from 'expo-crypto';
import * as ImagePicker from 'expo-image-picker';
import WebView, { type WebViewMessageEvent } from 'react-native-webview';
import {
  ART_RENDERER_PROTOCOL_VERSION,
  MAX_RENDERER_MESSAGE_BYTES,
  RendererBootstrapSchema,
  RendererLoadCommandSchema,
  RendererPlaybackEventEnvelopeSchema,
} from '../../../../packages/art-renderer/src/protocol';

import {
  API_BASE_URL,
  createDemoApi,
  DemoApiError,
  MAX_IMAGE_BYTES,
  type P1ContextOption,
  type P1ContextOptions,
  type WorkflowResult,
} from './api';

type JsonObject = Record<string, unknown>;
type SelectedImage = {
  uri: string;
  fileName: string;
  mimeType: string;
  fileSize?: number;
};
type Claim = {
  observation_id: string;
  label: { value: string };
  confidence: number;
  kind: 'subject' | 'action' | 'story';
};
type FeedbackCompletion = 'COMPLETED' | 'PARTIAL' | 'NOT_ATTEMPTED';

function utf8ByteLength(value: string): number {
  return encodeURIComponent(value).replace(/%[0-9A-F]{2}/g, 'U').length;
}

const api = createDemoApi();

function asObject(value: unknown): JsonObject {
  return typeof value === 'object' && value !== null ? (value as JsonObject) : {};
}

function textValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function numberValue(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function readClaims(raw: JsonObject | null): Claim[] {
  if (!raw) return [];
  const buckets: Array<[unknown, Claim['kind']]> = [
    [raw.entities, 'subject'],
    [raw.actions, 'action'],
    [raw.themes, 'story'],
  ];
  return buckets.flatMap(([items, kind]) => {
    if (!Array.isArray(items)) return [];
    return items.flatMap((item) => {
      const value = asObject(item);
      const label = asObject(value.label);
      if (
        typeof value.observation_id !== 'string' ||
        typeof label.value !== 'string' ||
        typeof value.confidence !== 'number'
      ) return [];
      return [{
        observation_id: value.observation_id,
        label: { value: label.value },
        confidence: value.confidence,
        kind,
      }];
    });
  });
}

function uniqueStrings(values: string[]): string[] {
  return [...new Set(values)].sort((left, right) => left.localeCompare(right));
}

export default function DemoWorkflowScreen() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionVersion, setSessionVersion] = useState(0);
  const [sessionState, setSessionState] = useState('NOT_STARTED');
  const [selectedImage, setSelectedImage] = useState<SelectedImage | null>(null);
  const [syntheticConfirmed, setSyntheticConfirmed] = useState(false);
  const [admission, setAdmission] = useState<JsonObject | null>(null);
  const [understanding, setUnderstanding] = useState<JsonObject | null>(null);
  const [confirmedAnchor, setConfirmedAnchor] = useState<JsonObject | null>(null);
  const [selectedClaims, setSelectedClaims] = useState<string[]>([]);
  const [primaryClaim, setPrimaryClaim] = useState<string | null>(null);
  const [correction, setCorrection] = useState('');
  const [ageYears, setAgeYears] = useState('');
  const [ageMonths, setAgeMonths] = useState('0');
  const [contextOptions, setContextOptions] = useState<P1ContextOptions | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<P1ContextOption | null>(null);
  const [readiness, setReadiness] = useState<string[]>([]);
  const [completedActivities, setCompletedActivities] = useState<string[]>([]);
  const [availableMaterials, setAvailableMaterials] = useState<string[]>([]);
  const [safetyConditions, setSafetyConditions] = useState<string[]>([]);
  const [supervision, setSupervision] = useState<'NONE' | 'NEARBY' | 'DIRECT' | null>(null);
  const [p1Filter, setP1Filter] = useState<JsonObject | null>(null);
  const [experience, setExperience] = useState<JsonObject | null>(null);
  const [gateB, setGateB] = useState<JsonObject | null>(null);
  const [handoff, setHandoff] = useState<JsonObject | null>(null);
  const [rendererLaunch, setRendererLaunch] = useState<JsonObject | null>(null);
  const [rendererInstanceId, setRendererInstanceId] = useState<string | null>(null);
  const [rendererStatus, setRendererStatus] = useState<string | null>(null);
  const [rendererEvents, setRendererEvents] = useState<JsonObject[]>([]);
  const [rendererError, setRendererError] = useState<string | null>(null);
  const [completion, setCompletion] = useState<FeedbackCompletion>('NOT_ATTEMPTED');
  const [interest, setInterest] = useState<number | null>(null);
  const [independence, setIndependence] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<JsonObject | null>(null);
  const [gallery, setGallery] = useState<JsonObject | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const claims = useMemo(() => readClaims(understanding), [understanding]);
  const webViewRef = useRef<WebView>(null);
  const rendererCommandSent = useRef<string | null>(null);
  const rendererEventSequence = useRef(0);
  const parsedYears = Number(ageYears);
  const parsedExtraMonths = Number(ageMonths);
  const ageMonthsTotal = parsedYears * 12 + parsedExtraMonths;
  const isAgeValid = ageYears !== '' && Number.isInteger(parsedYears) && Number.isInteger(parsedExtraMonths)
    && parsedYears >= 0 && parsedExtraMonths >= 0 && parsedExtraMonths <= 11
    && ageMonthsTotal <= 155;

  async function runStep<T extends JsonObject>(
    label: string,
    action: () => Promise<WorkflowResult<T>>,
    onSuccess?: (result: WorkflowResult<T>) => void,
  ) {
    if (!sessionId || busy) return;
    setBusy(label);
    setError(null);
    setNotice(null);
    try {
      const result = await action();
      setSessionVersion(result.observed_session_version);
      if (onSuccess) onSuccess(result);
      if (result.status === 'BLOCKED') {
        const payload = asObject(result.payload);
        setNotice(textValue(payload.guidance, 'Backend đã chặn bước này; xem mã/lý do trong kết quả bên dưới.'));
      }
    } catch (caught) {
      if (caught instanceof DemoApiError) {
        setError({ code: caught.code, message: caught.message });
      } else {
        setError({ code: 'UNEXPECTED_CLIENT_ERROR', message: 'Ứng dụng gặp lỗi khi xử lý thao tác.' });
      }
    } finally {
      setBusy(null);
    }
  }

  async function createSession() {
    if (busy) return;
    setBusy('Tạo phiên');
    setError(null);
    setNotice(null);
    try {
      const result = await api.createSession();
      const snapshot = asObject(result.payload);
      setSessionId(result.session_id);
      setSessionVersion(result.observed_session_version);
      setSessionState(textValue(snapshot.state, 'CREATED'));
      setAdmission(null);
      setUnderstanding(null);
      setConfirmedAnchor(null);
      setContextOptions(null);
      setP1Filter(null);
      setExperience(null);
      setGateB(null);
      setHandoff(null);
      setFeedback(null);
      setGallery(null);
      clearRenderer();
      setNotice('Phiên chạy tạm đã tạo. Backend restart hoặc hết hạn sẽ xóa phiên này.');
    } catch (caught) {
      if (caught instanceof DemoApiError) setError({ code: caught.code, message: caught.message });
      else setError({ code: 'NETWORK_ERROR', message: 'Không tạo được phiên với backend.' });
    } finally {
      setBusy(null);
    }
  }

  async function chooseImage() {
    setError(null);
    setNotice(null);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: false,
        allowsMultipleSelection: false,
        exif: false,
        quality: 1,
      });
      if (result.canceled || !result.assets[0]) return;
      const asset = result.assets[0];
      if (asset.fileSize !== undefined && asset.fileSize > MAX_IMAGE_BYTES) {
        setError({ code: 'IMAGE_TOO_LARGE', message: 'Ảnh vượt giới hạn demo 5 MB. Hãy chọn ảnh nhỏ hơn.' });
        return;
      }
      const extension = asset.fileName?.split('.').pop()?.toLowerCase();
      const mimeByExtension: Record<string, string> = {
        jpg: 'image/jpeg',
        jpeg: 'image/jpeg',
        png: 'image/png',
      };
      const mimeType = asset.mimeType?.toLowerCase() || mimeByExtension[extension || ''];
      if (mimeType !== 'image/jpeg' && mimeType !== 'image/png') {
        setError({
          code: 'UNSUPPORTED_IMAGE_TYPE',
          message: 'Demo chỉ nhận ảnh PNG hoặc JPEG. Hãy xuất/chuyển ảnh tổng hợp sang một trong hai định dạng này.',
        });
        return;
      }
      setSelectedImage({
        uri: asset.uri,
        fileName: asset.fileName || `synthetic-${Date.now()}.${mimeType === 'image/png' ? 'png' : 'jpg'}`,
        mimeType,
        fileSize: asset.fileSize,
      });
      setSyntheticConfirmed(false);
      setAdmission(null);
      setUnderstanding(null);
      setConfirmedAnchor(null);
      setContextOptions(null);
      setP1Filter(null);
      setExperience(null);
      setGateB(null);
      setHandoff(null);
      setFeedback(null);
      setGallery(null);
      clearRenderer();
    } catch {
      setError({ code: 'IMAGE_PICKER_FAILED', message: 'Không mở được bộ chọn ảnh. Có thể thử lại bằng nút chọn ảnh.' });
    }
  }

  function toggle(list: string[], setter: (next: string[]) => void, value: string) {
    setter(list.includes(value) ? list.filter((item) => item !== value) : [...list, value]);
  }

  async function refreshSession() {
    if (!sessionId || busy) return;
    setBusy('Đọc phiên');
    setError(null);
    try {
      const result = await api.refreshSession(sessionId, sessionVersion);
      const snapshot = asObject(result.payload);
      setSessionVersion(result.observed_session_version);
      setSessionState(textValue(snapshot.state, sessionState));
      setNotice(`Backend trả trạng thái ${textValue(snapshot.state, 'không rõ')} ở version ${result.observed_session_version}.`);
    } catch (caught) {
      if (caught instanceof DemoApiError) setError({ code: caught.code, message: caught.message });
      else setError({ code: 'NETWORK_ERROR', message: 'Không đọc được trạng thái phiên.' });
    } finally {
      setBusy(null);
    }
  }

  async function loadContextOptions() {
    if (!sessionId || !isAgeValid || busy) return;
    setBusy('Đọc lựa chọn P1');
    setError(null);
    try {
      const result = await api.readContextOptions(sessionId, sessionVersion, ageMonthsTotal);
      const payload = result.payload;
      if (!payload) throw new DemoApiError('Backend returned no P1 options.', 'INVALID_RESPONSE', 200);
      setContextOptions(payload);
      setSelectedActivity(payload.options[0] ?? null);
      setReadiness([]);
      setCompletedActivities([]);
      setAvailableMaterials([]);
      setSafetyConditions([]);
      setSupervision(null);
      setP1Filter(null);
      setExperience(null);
      setGateB(null);
      setNotice(payload.options.length
        ? `Backend tìm thấy ${payload.options.length} lựa chọn catalog cho nhãn “${payload.confirmed_anchor_label}” và tuổi đã nhập.`
        : 'Không có hoạt động P1 khớp với nhãn và độ tuổi này; không tự tạo hoạt động thay thế.');
    } catch (caught) {
      if (caught instanceof DemoApiError) setError({ code: caught.code, message: caught.message });
      else setError({ code: 'NETWORK_ERROR', message: 'Không tải được lựa chọn P1.' });
    } finally {
      setBusy(null);
    }
  }

  function clearRenderer() {
    rendererCommandSent.current = null;
    rendererEventSequence.current = 0;
    setRendererLaunch(null);
    setRendererInstanceId(null);
    setRendererStatus(null);
    setRendererEvents([]);
    setRendererError(null);
  }

  function openPixiRenderer() {
    if (!sessionId || busy) return;
    clearRenderer();
    const instanceId = Crypto.randomUUID();
    void runStep('Pixi launch', () => api.prepareRenderer(sessionId, sessionVersion), (result) => {
      const payload = asObject(result.payload);
      const launch = asObject(payload.renderer_launch);
      if (launch.contractName !== 'PixiRendererLaunchV1') {
        setRendererError('Backend không trả PixiRendererLaunchV1 hợp lệ.');
        return;
      }
      setRendererLaunch(launch);
      setRendererInstanceId(instanceId);
      setRendererStatus('Đang tải trang renderer…');
      setRendererError(null);
    });
  }

  function handleRendererMessage(event: WebViewMessageEvent) {
    const serialized = event.nativeEvent.data;
    if (!serialized || utf8ByteLength(serialized) > MAX_RENDERER_MESSAGE_BYTES) {
      setRendererError('Renderer message vượt giới hạn 4 KB hoặc rỗng.');
      return;
    }
    let value: unknown;
    try {
      value = JSON.parse(serialized);
    } catch {
      setRendererError('Renderer trả JSON không hợp lệ.');
      return;
    }

    const bootstrap = RendererBootstrapSchema.safeParse(value);
    if (bootstrap.success) {
      if (!rendererInstanceId || bootstrap.data.rendererInstanceId !== rendererInstanceId) {
        setRendererError('Renderer instance không khớp phiên hiện tại.');
        return;
      }
      if (rendererCommandSent.current === rendererInstanceId) return;
      if (!rendererLaunch) {
        setRendererError('Launch Pixi đã hết hiệu lực; hãy mở renderer lại từ app.');
        return;
      }
      const command = RendererLoadCommandSchema.safeParse({
        contractName: 'RendererLoadCommandV1',
        contractVersion: '1.0',
        protocolVersion: ART_RENDERER_PROTOCOL_VERSION,
        sequence: 1,
        rendererInstanceId,
        sessionId: rendererLaunch.sessionId,
        expectedSessionVersion: rendererLaunch.expectedSessionVersion,
        experienceSpecRef: rendererLaunch.experienceSpecRef,
        sourceReadEndpoint: rendererLaunch.sourceReadEndpoint,
        sourceReadCapability: rendererLaunch.sourceReadCapability,
        assetManifest: rendererLaunch.assetManifest,
        animationPlan: rendererLaunch.animationPlan,
      });
      if (!command.success) {
        setRendererError('Backend launch không qua validation contract Pixi v1.');
        return;
      }
      const loadMessage = JSON.stringify(command.data);
      if (utf8ByteLength(loadMessage) > MAX_RENDERER_MESSAGE_BYTES) {
        setRendererError('Pixi launch lớn hơn giới hạn bridge 4 KB.');
        return;
      }
      if (!webViewRef.current) {
        setRendererError('WebView chưa sẵn sàng; đóng và mở Pixi lại thủ công.');
        return;
      }
      rendererCommandSent.current = rendererInstanceId;
      setRendererStatus('Đã bắt tay protocol v1; gửi plan gốc cho Pixi.');
      webViewRef.current.postMessage(loadMessage);
      return;
    }

    const playback = RendererPlaybackEventEnvelopeSchema.safeParse(value);
    if (!playback.success || !rendererLaunch || !rendererInstanceId) {
      setRendererError('Renderer event không khớp contract v1; bridge đã từ chối.');
      return;
    }
    const data = playback.data;
    const activeSpec = asObject(rendererLaunch.experienceSpecRef);
    const eventSpec = asObject(data.experienceSpecRef);
    const animationPlan = asObject(rendererLaunch.animationPlan);
    const rendererPlan = asObject(animationPlan.plan);
    if (
      data.rendererInstanceId !== rendererInstanceId ||
      data.sessionId !== sessionId ||
      data.sequence !== rendererEventSequence.current + 1 ||
      eventSpec.id !== activeSpec.id ||
      eventSpec.version !== activeSpec.version ||
      asObject(data.event).planId !== rendererPlan.planId
    ) {
      setRendererError('Renderer event sai session/spec/sequence; bridge đã từ chối.');
      return;
    }
    rendererEventSequence.current = data.sequence;
    setRendererEvents((items) => [...items.slice(-4), asObject(data)]);
    setRendererStatus(textValue(asObject(data.event).type, 'Pixi event received'));
  }

  const rendererPageUrl = rendererInstanceId
    ? `${api.baseUrl}/renderer/mobile.html?rendererInstanceId=${encodeURIComponent(rendererInstanceId)}`
    : null;

  const matchingOptions = contextOptions?.options ?? [];
  const readinessChoices = uniqueStrings(matchingOptions.flatMap((item) => item.readiness_ids));
  const prerequisiteChoices = uniqueStrings(matchingOptions.flatMap((item) => item.prerequisite_activity_ids));
  const materialChoices = uniqueStrings(matchingOptions.flatMap((item) => item.material_option_ids));
  const safetyChoices = uniqueStrings(matchingOptions.flatMap((item) => item.policy_constraints));
  const activityChoices = [...new Map(matchingOptions.map((item) => [
    `${item.activity_ref.id}:${item.activity_ref.version}`,
    item,
  ])).values()];

  return (
    <View style={styles.root}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.brandRow}>
          <View style={styles.brandMark}><Text style={styles.brandMarkText}>S</Text></View>
          <View style={styles.brandWords}>
            <Text style={styles.brandTitle}>Sketch2Life</Text>
            <Text style={styles.brandSubtitle}>DEMO • IMAGE-ONLY • BACKEND LIVE</Text>
          </View>
          <Pressable style={styles.smallButton} onPress={() => void refreshSession()} disabled={!sessionId || !!busy}>
            <Text style={styles.smallButtonText}>Làm mới</Text>
          </Pressable>
        </View>

        <View style={styles.heroCard}>
          <Text style={styles.eyebrow}>ANDROID EMULATOR TEST</Text>
          <Text style={styles.heroTitle}>Từ tranh đến hoạt động</Text>
          <Text style={styles.heroText}>
            Chỉ ảnh tổng hợp/không phải của trẻ. App gọi backend; chỉ nút “Gửi phân tích” mới yêu cầu Lightning.
          </Text>
          <View style={styles.badgeRow}>
            <Badge label="Không audio" />
            <Badge label="Không video" />
            <Badge label="Không tự retry" />
          </View>
        </View>

        <View style={styles.noticeCard}>
          <Text style={styles.noticeTitle}>Quota và dữ liệu</Text>
          <Text style={styles.noticeText}>
            Bạn tự theo dõi tối đa 25 credit hiện có của Lightning. Một lần bấm phân tích = tối đa một request từ backend; nếu timeout, không có retry nền. Phiên/ảnh chỉ nằm trong RAM và sẽ mất khi backend restart/hết TTL. Chưa đăng nhập, chưa lưu lâu dài.
          </Text>
          <Text style={styles.endpointText}>Backend: {API_BASE_URL}</Text>
        </View>

        {error && (
          <View style={styles.errorCard}>
            <Text style={styles.errorCode}>{error.code}</Text>
            <Text style={styles.errorText}>{error.message}</Text>
            {error.code === 'STALE_SESSION_VERSION' && (
              <Text style={styles.errorHint}>Dùng “Làm mới” rồi tiếp tục theo trạng thái backend; không gửi lại tự động.</Text>
            )}
          </View>
        )}
        {notice && <View style={styles.noticeInline}><Text style={styles.noticeInlineText}>{notice}</Text></View>}

        <Section number="01" title="Phiên tạm" subtitle="Không cần tài khoản trong demo; giữ đường nối token cho auth tương lai.">
          {!sessionId ? (
            <ActionButton title="Tạo phiên thử nghiệm" onPress={() => void createSession()} loading={busy === 'Tạo phiên'} />
          ) : (
            <View style={styles.sessionSummary}>
              <Text style={styles.sessionValue}>Phiên {sessionId.slice(0, 8)}…</Text>
              <Text style={styles.sessionMeta}>v{sessionVersion} · {sessionState} · chỉ lưu trong phiên chạy</Text>
            </View>
          )}
        </Section>

        <Section number="02" title="Chọn và gửi ảnh" subtitle="Dùng bộ chọn ảnh của Android; không xin quyền microphone/camera.">
          <Pressable style={styles.secondaryButton} onPress={() => void chooseImage()}>
            <Text style={styles.secondaryButtonText}>{selectedImage ? 'Chọn ảnh khác' : 'Chọn ảnh tổng hợp'}</Text>
          </Pressable>
          {selectedImage && (
            <View style={styles.imageCard}>
              <Image source={{ uri: selectedImage.uri }} style={styles.previewImage} resizeMode="contain" />
              <Text style={styles.imageCaption}>{selectedImage.fileName} · tối đa 5 MB</Text>
            </View>
          )}
          <Pressable
            style={styles.checkboxRow}
            onPress={() => setSyntheticConfirmed((value) => !value)}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: syntheticConfirmed }}
          >
            <View style={[styles.checkbox, syntheticConfirmed && styles.checkboxChecked]}>
              {syntheticConfirmed && <Text style={styles.checkboxTick}>✓</Text>}
            </View>
            <Text style={styles.checkboxLabel}>Tôi xác nhận đây là ảnh tổng hợp/ảnh do người lớn tạo, không có trẻ em hay dữ liệu nhận diện.</Text>
          </Pressable>
          <ActionButton
            title="Tải ảnh lên backend để kiểm tra"
            disabled={!sessionId || !selectedImage || !syntheticConfirmed || !!busy}
            loading={busy === 'Tải ảnh'}
            onPress={() => {
              if (!sessionId || !selectedImage) return;
              void runStep('Tải ảnh', () => api.uploadImage(sessionId, sessionVersion, selectedImage), (result) => {
                const payload = asObject(result.payload);
                setAdmission(payload);
                setSessionState(result.status === 'SUCCEEDED' ? 'CREATED' : textValue(payload.decision, 'MEDIA_RECAPTURE'));
                setUnderstanding(null);
                setConfirmedAnchor(null);
                setP1Filter(null);
                setExperience(null);
                setGateB(null);
                setHandoff(null);
                setFeedback(null);
                setGallery(null);
                setNotice(textValue(payload.guidance, 'Backend đã xử lý quyết định nhận ảnh.'));
              });
            }}
          />
          {admission && <ResultLine title="Kiểm tra ảnh" value={`${textValue(admission.decision, 'UNKNOWN')} · ${textValue(admission.content_type, 'không nhận')} · ${numberValue(admission.byte_length)} bytes`} />}
        </Section>

        <Section number="03" title="Phân tích ảnh (live)" subtitle="Chỉ gửi khi bạn chủ động bấm. Không dùng dữ liệu mẫu thay cho lỗi thật.">
          <View style={styles.liveWarning}>
            <Text style={styles.liveWarningTitle}>Request có thể dùng credit Lightning</Text>
            <Text style={styles.liveWarningText}>Chỉ tiếp tục nếu backend đã cấu hình Lightning và bạn muốn tiêu credit cho ảnh tổng hợp vừa chọn.</Text>
          </View>
          <ActionButton
            title="Gửi phân tích ảnh tới Lightning"
            disabled={!sessionId || admission?.decision !== 'ADMITTED' || !!busy}
            loading={busy === 'Phân tích'}
            onPress={() => {
              if (!sessionId) return;
              void runStep('Phân tích', () => api.runUnderstanding(sessionId, sessionVersion), (result) => {
                const payload = asObject(result.payload);
                setUnderstanding(payload);
                setSessionState(result.status === 'SUCCEEDED' ? 'GATE_A_PENDING' : 'CREATED');
                setConfirmedAnchor(null);
                setSelectedClaims([]);
                setPrimaryClaim(null);
                setContextOptions(null);
                setP1Filter(null);
                setExperience(null);
                setGateB(null);
                setHandoff(null);
                setFeedback(null);
                setNotice(result.status === 'SUCCEEDED'
                  ? 'Đã nhận kết quả backend. Hãy tự kiểm tra và xác nhận đúng/sai trước khi đi tiếp.'
                  : 'Backend không trả kết quả thành công. Không thay bằng mock; chỉ thử lại nếu bạn chủ động chọn.');
              });
            }}
          />
          {understanding && (
            <View style={styles.resultCard}>
              <Text style={styles.resultTitle}>Đề xuất từ ảnh · {textValue(understanding.contract_name, 'RawUnderstandingResultV1')}</Text>
              <Text style={styles.resultMeta}>Kể chuyện: {textValue(understanding.narration_status, 'NOT_SUPPLIED')} · các nhãn dưới đây cần người lớn xem lại.</Text>
              {claims.length === 0 ? <Text style={styles.muted}>Không có chi tiết để xác nhận.</Text> : claims.map((claim) => (
                <Pressable
                  key={claim.observation_id}
                  style={styles.claimRow}
                  onPress={() => {
                    toggle(selectedClaims, setSelectedClaims, claim.observation_id);
                    if (primaryClaim === claim.observation_id) setPrimaryClaim(null);
                  }}
                >
                  <View style={[styles.checkbox, selectedClaims.includes(claim.observation_id) && styles.checkboxChecked]}>
                    {selectedClaims.includes(claim.observation_id) && <Text style={styles.checkboxTick}>✓</Text>}
                  </View>
                  <View style={styles.claimCopy}>
                    <Text style={styles.claimLabel}>{claim.label.value}</Text>
                    <Text style={styles.claimMeta}>{claim.kind} · {Math.round(claim.confidence * 100)}% · {claim.observation_id}</Text>
                  </View>
                  <Pressable
                    style={[styles.primaryPill, primaryClaim === claim.observation_id && styles.primaryPillActive]}
                    onPress={() => {
                      if (!selectedClaims.includes(claim.observation_id)) setSelectedClaims((items) => [...items, claim.observation_id]);
                      setPrimaryClaim(claim.observation_id);
                    }}
                  >
                    <Text style={[styles.primaryPillText, primaryClaim === claim.observation_id && styles.primaryPillTextActive]}>
                      {primaryClaim === claim.observation_id ? 'Chủ đề' : 'Chọn chính'}
                    </Text>
                  </Pressable>
                </Pressable>
              ))}
              <TextInput
                value={correction}
                onChangeText={setCorrection}
                placeholder="Nếu cần, sửa nhãn chủ đề (không bắt buộc)"
                placeholderTextColor="#94A3B8"
                style={styles.input}
                maxLength={500}
              />
              <ActionButton
                title="Xác nhận Gate A"
                disabled={!sessionId || !primaryClaim || selectedClaims.length === 0 || !!busy || !!confirmedAnchor}
                loading={busy === 'Gate A'}
                onPress={() => {
                  if (!sessionId || !primaryClaim) return;
                  void runStep('Gate A', () => api.confirmGateA(
                    sessionId,
                    sessionVersion,
                    selectedClaims,
                    primaryClaim,
                    correction.trim() || null,
                  ), (result) => {
                    const payload = asObject(result.payload);
                    setConfirmedAnchor(payload);
                    setSessionState('UNDERSTANDING_PROPOSED');
                    setP1Filter(null);
                    setExperience(null);
                    setGateB(null);
                    setNotice('Gate A đã được xác nhận bởi người lớn; ảnh gốc vẫn được giữ nguyên.');
                  });
                }}
              />
              {sessionId && sessionState === 'GATE_A_PENDING' && (
                <Pressable
                  style={styles.textButton}
                  onPress={() => void runStep('Yêu cầu chọn lại ảnh', () => api.requestRetake(
                    sessionId,
                    sessionVersion,
                  ), (result) => {
                    setSessionState('MEDIA_RECAPTURE');
                    setAdmission(null);
                    setUnderstanding(null);
                    setConfirmedAnchor(null);
                    setNotice(`Retake được ghi nhận ở version ${result.observed_session_version}; chọn/tải ảnh lại thủ công.`);
                  })}
                >
                  <Text style={styles.textButtonText}>Không đúng tranh? Yêu cầu retake và chọn ảnh khác</Text>
                </Pressable>
              )}
            </View>
          )}
        </Section>

        {confirmedAnchor && (
          <Section number="04" title="Người lớn nhập bối cảnh P1" subtitle="Không suy tuổi/kỹ năng từ ảnh. Chỉ chọn thông tin bạn biết và điều kiện thực tế.">
            <View style={styles.inputRow}>
              <Field label="Tuổi (năm)" value={ageYears} onChangeText={setAgeYears} keyboardType="number-pad" placeholder="vd. 5" />
              <Field label="Tháng thêm" value={ageMonths} onChangeText={setAgeMonths} keyboardType="number-pad" placeholder="0–11" />
            </View>
            <ActionButton title="Tải lựa chọn phù hợp từ backend" disabled={!isAgeValid || !!busy} loading={busy === 'Đọc lựa chọn P1'} onPress={() => void loadContextOptions()} />
            {contextOptions && (
              <View style={styles.optionPanel}>
                <Text style={styles.resultTitle}>Kết quả theo “{contextOptions.confirmed_anchor_label}” · {contextOptions.age_months} tháng</Text>
                {activityChoices.length === 0 ? (
                  <Text style={styles.muted}>Không có lựa chọn phù hợp trong catalog này. Ảnh gốc vẫn có thể xem; backend không bịa hoạt động.</Text>
                ) : (
                  <>
                    <Text style={styles.fieldLabel}>Chọn hoạt động mà người lớn muốn cân nhắc</Text>
                    {activityChoices.map((option) => {
                      const active = selectedActivity?.activity_ref.id === option.activity_ref.id && selectedActivity.activity_ref.version === option.activity_ref.version;
                      return (
                        <ChoiceRow
                          key={`${option.activity_ref.id}:${option.activity_ref.version}`}
                          label={`${option.activity_ref.id} v${option.activity_ref.version}`}
                          detail={`Template ${option.template_ref.id} · tuổi ${option.age_months_min}–${option.age_months_max} tháng`}
                          selected={active}
                          onPress={() => setSelectedActivity(option)}
                        />
                      );
                    })}
                    <ChoiceGroup title="Kỹ năng/readiness đã quan sát được" values={readinessChoices} selected={readiness} setSelected={setReadiness} emptyHint="Không có yêu cầu readiness trong lựa chọn hiện tại." />
                    <ChoiceGroup title="Hoạt động tiên quyết đã hoàn tất" values={prerequisiteChoices} selected={completedActivities} setSelected={setCompletedActivities} emptyHint="Không có hoạt động tiên quyết bắt buộc." />
                    <ChoiceGroup title="Vật liệu thật sự có sẵn" values={materialChoices} selected={availableMaterials} setSelected={setAvailableMaterials} emptyHint="Chưa có vật liệu phù hợp — bộ lọc sẽ không đề xuất hoạt động." />
                    <ChoiceGroup title="Điều kiện an toàn có thể đáp ứng" values={safetyChoices} selected={safetyConditions} setSelected={setSafetyConditions} emptyHint="Không có điều kiện an toàn bổ sung trong lựa chọn hiện tại." />
                    <Text style={styles.fieldLabel}>Mức giám sát người lớn có thể duy trì</Text>
                    <View style={styles.pillRow}>
                      {(['NONE', 'NEARBY', 'DIRECT'] as const).map((value) => (
                        <ChoicePill key={value} label={value} selected={supervision === value} onPress={() => setSupervision(value)} />
                      ))}
                    </View>
                    <ActionButton
                      title="Lưu bối cảnh người lớn"
                      disabled={!sessionId || !selectedActivity || !supervision || !!busy}
                      loading={busy === 'Lưu bối cảnh'}
                      onPress={() => {
                        if (!sessionId || !selectedActivity || !supervision) return;
                        void runStep('Lưu bối cảnh', () => api.setP1Context(sessionId, sessionVersion, {
                          age_months: ageMonthsTotal,
                          readiness_ids: readiness,
                          completed_activity_ids: completedActivities,
                          available_material_option_ids: availableMaterials,
                          supervision_level: supervision,
                          policy_flags: safetyConditions,
                          candidate_status: 'ACTIVE_FIXTURE',
                          selected_activity_id: selectedActivity.activity_ref.id,
                          selected_activity_version: selectedActivity.activity_ref.version,
                        }), (result) => {
                          const payload = asObject(result.payload);
                          setSessionState(textValue(payload.missing_fields && Array.isArray(payload.missing_fields) && payload.missing_fields.length ? 'CONTEXT_REQUIRED' : 'UNDERSTANDING_PROPOSED', 'UNDERSTANDING_PROPOSED'));
                          setP1Filter(null);
                          setExperience(null);
                        });
                      }}
                    />
                    <ActionButton
                      title="Lọc hoạt động P1"
                      disabled={!sessionId || !supervision || !selectedActivity || !!busy}
                      loading={busy === 'Lọc P1'}
                      secondary
                      onPress={() => {
                        if (!sessionId) return;
                        void runStep('Lọc P1', () => api.runP1Filter(sessionId, sessionVersion), (result) => {
                          const payload = asObject(result.payload);
                          const filtered = asObject(payload.filter_result);
                          setP1Filter(filtered);
                          setSessionState(textValue(filtered.status) === 'VALID_CANDIDATE' ? 'CANDIDATES_READY' : 'UNDERSTANDING_PROPOSED');
                          setNotice(textValue(filtered.status) === 'VALID_CANDIDATE'
                            ? 'P1 tìm được hoạt động phù hợp với các thông tin người lớn đã nhập.'
                            : `P1 không tìm được lựa chọn đạt điều kiện (${textValue(filtered.status, 'BLOCKED')}); xem mã lý do trong phản hồi.`);
                        });
                      }}
                    />
                    {p1Filter && <ResultLine title="P1 filter" value={`${textValue(p1Filter.status)} · ${(Array.isArray(p1Filter.reason_codes) ? p1Filter.reason_codes : []).join(', ')}`} />}
                  </>
                )}
              </View>
            )}
          </Section>
        )}

        {p1Filter?.status === 'VALID_CANDIDATE' && (
          <Section number="05" title="ExperienceSpec và Gate B" subtitle="Backend dựng một trải nghiệm có danh tính/version rõ ràng; người lớn duyệt chính xác trước khi tiếp tục.">
            {!experience ? (
              <ActionButton title="Chuẩn bị trải nghiệm để duyệt" disabled={!sessionId || !!busy} loading={busy === 'Chuẩn bị trải nghiệm'} onPress={() => {
                if (!sessionId) return;
                void runStep('Chuẩn bị trải nghiệm', () => api.prepareExperience(sessionId, sessionVersion), (result) => {
                  const payload = asObject(result.payload);
                  setExperience(payload);
                  setSessionState('GATE_B_PENDING');
                });
              }} />
            ) : (
              <View style={styles.resultCard}>
                <ExperienceSummary experience={experience} />
                <Text style={styles.muted}>Chưa có video/ảnh sinh mới. Nội dung hoạt động hiển thị theo template P1 đã chọn.</Text>
                {!gateB && <ActionButton title="Người lớn duyệt đúng hoạt động này (Gate B)" disabled={!sessionId || !!busy} loading={busy === 'Duyệt Gate B'} onPress={() => {
                  if (!sessionId) return;
                  void runStep('Duyệt Gate B', () => api.approveGateB(sessionId, sessionVersion), (result) => {
                    const payload = asObject(result.payload);
                    setGateB(payload);
                    setSessionState('EXPERIENCE_READY');
                  });
                }} />}
              </View>
            )}
            {gateB && <ResultLine title="Gate B / P4" value={`${textValue(asObject(gateB.gate_b).status, 'APPROVED')} · ${textValue(asObject(gateB.learning_media).status)} · ${textValue(asObject(gateB.learning_media).fallback_type, 'media details in response')} · generation_called=${String(gateB.generation_called)}`} />}
          </Section>
        )}

        {gateB && (
          <Section number="P3" title="PixiJS · giữ nguyên tranh gốc" subtitle="Backend phát manifest/plan có hash; WebView lấy đúng bytes qua capability ngắn hạn. Không gửi ảnh qua bridge.">
            <View style={styles.liveWarning}>
              <Text style={styles.liveWarningTitle}>Chỉ source-only reveal</Text>
              <Text style={styles.liveWarningText}>Hiện 144 asset bổ sung chưa được duyệt để runtime dùng. Pixi chỉ reveal toàn ảnh gốc; nếu renderer lỗi, preview gốc bên dưới vẫn còn.</Text>
            </View>
            {selectedImage && <Image source={{ uri: selectedImage.uri }} style={styles.previewImage} resizeMode="contain" />}
            {!rendererLaunch ? (
              <ActionButton
                title="Chuẩn bị Pixi cho ảnh gốc (không gọi AI)"
                disabled={!sessionId || !!busy}
                loading={busy === 'Pixi launch'}
                onPress={openPixiRenderer}
              />
            ) : (
              <>
                {rendererPageUrl && (
                  <View style={styles.webRendererWrap}>
                    <WebView
                      ref={webViewRef}
                      source={{ uri: rendererPageUrl }}
                      originWhitelist={[api.baseUrl]}
                      javaScriptEnabled
                      domStorageEnabled={false}
                      mixedContentMode="never"
                      thirdPartyCookiesEnabled={false}
                      sharedCookiesEnabled={false}
                      setSupportMultipleWindows={false}
                      onMessage={handleRendererMessage}
                      onLoadStart={() => setRendererStatus('Đang mở Pixi từ backend…')}
                      onLoadEnd={() => setRendererStatus((value) => value ?? 'Trang Pixi đã tải; chờ handshake.')}
                      onError={() => setRendererError('Không mở được trang Pixi. Hãy build renderer rồi khởi động lại backend.')}
                      onHttpError={(event) => setRendererError(`Trang renderer trả HTTP ${event.nativeEvent.statusCode}. Hãy build renderer rồi khởi động lại backend.`)}
                      style={styles.webRenderer}
                    />
                  </View>
                )}
                {rendererStatus && <ResultLine title="Pixi bridge" value={rendererStatus} />}
                {rendererError && <Text style={styles.rendererError}>{rendererError}</Text>}
                {rendererEvents.map((item, index) => {
                  const event = asObject(item.event);
                  return <ResultLine key={`${String(item.sequence)}-${index}`} title={`Event ${String(item.sequence)}`} value={textValue(event.type)} />;
                })}
                <ActionButton title="Đóng Pixi / capability hiện tại" secondary onPress={clearRenderer} />
              </>
            )}
          </Section>
        )}

        {gateB && (
          <Section number="06" title="Handoff, feedback, gallery" subtitle="Giữ đúng identity hoạt động; feedback tối giản, không có tên/ghi chú định danh và không lưu bền vững.">
            {!handoff ? (
              <ActionButton title="Hoàn tất handoff tới cùng hoạt động" disabled={!sessionId || !!busy} loading={busy === 'Handoff'} onPress={() => {
                if (!sessionId) return;
                void runStep('Handoff', () => api.completeHandoff(sessionId, sessionVersion), (result) => {
                  setHandoff(asObject(result.payload));
                  setSessionState('HANDOFF_READY');
                });
              }} />
            ) : (
              <View style={styles.resultCard}>
                <Text style={styles.resultTitle}>Activity handoff sẵn sàng</Text>
                <Text style={styles.sessionMeta}>Activity, objective, template và spec được giữ cùng identity/version từ Gate B.</Text>
                <Text style={styles.fieldLabel}>Kết quả quan sát</Text>
                <View style={styles.pillRow}>
                  {(['COMPLETED', 'PARTIAL', 'NOT_ATTEMPTED'] as const).map((value) => (
                    <ChoicePill key={value} label={value} selected={completion === value} onPress={() => setCompletion(value)} />
                  ))}
                </View>
                <ScorePicker label="Mức hứng thú (tùy chọn)" value={interest} onChange={setInterest} />
                <ScorePicker label="Mức độc lập (tùy chọn)" value={independence} onChange={setIndependence} />
                {!feedback && <ActionButton title="Gửi feedback không định danh" disabled={!sessionId || !!busy} loading={busy === 'Gửi feedback'} onPress={() => {
                  if (!sessionId) return;
                  void runStep('Gửi feedback', () => api.recordFeedback(sessionId, sessionVersion, completion, interest, independence), (result) => {
                    setFeedback(asObject(result.payload));
                    setSessionState('FEEDBACK_RECORDED');
                  });
                }} />}
                {feedback && <ResultLine title="Feedback" value={`đã ghi trong phiên · durable=${String(feedback.durable)}`} />}
                <ActionButton title="Đọc gallery của phiên này" secondary disabled={!sessionId || !!busy} loading={busy === 'Đọc gallery'} onPress={() => {
                  if (!sessionId) return;
                  void runStep('Đọc gallery', () => api.readGallery(sessionId, sessionVersion), (result) => setGallery(asObject(result.payload)));
                }} />
                {gallery && <ResultLine title="Session gallery" value={`${Array.isArray(gallery.entries) ? gallery.entries.length : 0} sự kiện · media_bytes_included=false · durable=false`} />}
              </View>
            )}
          </Section>
        )}

        <View style={styles.footer}>
          <Text style={styles.footerText}>Demo build only · không dùng ảnh trẻ · không lưu dài hạn · chưa phải bản phát hành</Text>
        </View>
      </ScrollView>
      {busy && (
        <View style={styles.busyBar}>
          <ActivityIndicator size="small" color="#FFFFFF" />
          <Text style={styles.busyText}>{busy}…</Text>
        </View>
      )}
    </View>
  );
}

function Section({ number, title, subtitle, children }: React.PropsWithChildren<{ number: string; title: string; subtitle: string }>) {
  return (
    <View style={styles.section}>
      <View style={styles.sectionHeading}>
        <Text style={styles.sectionNumber}>{number}</Text>
        <View style={styles.sectionCopy}>
          <Text style={styles.sectionTitle}>{title}</Text>
          <Text style={styles.sectionSubtitle}>{subtitle}</Text>
        </View>
      </View>
      {children}
    </View>
  );
}

function Badge({ label }: { label: string }) {
  return <View style={styles.badge}><Text style={styles.badgeText}>{label}</Text></View>;
}

function ActionButton({ title, onPress, disabled = false, loading = false, secondary = false }: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  secondary?: boolean;
}) {
  return (
    <Pressable
      style={[styles.actionButton, secondary && styles.actionButtonSecondary, disabled && styles.actionButtonDisabled]}
      onPress={onPress}
      disabled={disabled || loading}
      accessibilityRole="button"
    >
      {loading ? <ActivityIndicator size="small" color={secondary ? '#334155' : '#FFFFFF'} /> : null}
      <Text style={[styles.actionButtonText, secondary && styles.actionButtonSecondaryText]}>{title}</Text>
    </Pressable>
  );
}

function Field({ label, value, onChangeText, keyboardType, placeholder }: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  keyboardType?: 'default' | 'number-pad';
  placeholder: string;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType}
        placeholder={placeholder}
        placeholderTextColor="#94A3B8"
        style={styles.input}
      />
    </View>
  );
}

function ChoiceGroup({ title, values, selected, setSelected, emptyHint }: {
  title: string;
  values: string[];
  selected: string[];
  setSelected: (next: string[]) => void;
  emptyHint: string;
}) {
  return (
    <View style={styles.choiceGroup}>
      <Text style={styles.fieldLabel}>{title}</Text>
      {values.length === 0 ? <Text style={styles.muted}>{emptyHint}</Text> : values.map((value) => (
        <Pressable key={value} style={styles.checkboxRow} onPress={() => setSelected(selected.includes(value) ? selected.filter((item) => item !== value) : [...selected, value])}>
          <View style={[styles.checkbox, selected.includes(value) && styles.checkboxChecked]}>
            {selected.includes(value) && <Text style={styles.checkboxTick}>✓</Text>}
          </View>
          <Text style={styles.checkboxLabel}>{value}</Text>
        </Pressable>
      ))}
    </View>
  );
}

function ChoiceRow({ label, detail, selected, onPress }: { label: string; detail: string; selected: boolean; onPress: () => void }) {
  return (
    <Pressable style={[styles.activityChoice, selected && styles.activityChoiceSelected]} onPress={onPress}>
      <View style={[styles.radio, selected && styles.radioSelected]} />
      <View style={styles.claimCopy}>
        <Text style={styles.claimLabel}>{label}</Text>
        <Text style={styles.claimMeta}>{detail}</Text>
      </View>
    </Pressable>
  );
}

function ChoicePill({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  return (
    <Pressable style={[styles.choicePill, selected && styles.choicePillSelected]} onPress={onPress}>
      <Text style={[styles.choicePillText, selected && styles.choicePillTextSelected]}>{label}</Text>
    </Pressable>
  );
}

function ScorePicker({ label, value, onChange }: { label: string; value: number | null; onChange: (value: number | null) => void }) {
  return (
    <View style={styles.scoreBlock}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.pillRow}>
        {[1, 2, 3, 4, 5].map((score) => (
          <ChoicePill key={score} label={String(score)} selected={value === score} onPress={() => onChange(value === score ? null : score)} />
        ))}
      </View>
    </View>
  );
}

function ResultLine({ title, value }: { title: string; value: string }) {
  return <View style={styles.resultLine}><Text style={styles.resultLineTitle}>{title}</Text><Text style={styles.resultLineValue}>{value}</Text></View>;
}

function ExperienceSummary({ experience }: { experience: JsonObject }) {
  const spec = asObject(experience.experience_spec);
  const focus = asObject(spec.learning_focus);
  const activityPlan = asObject(spec.activity_plan);
  const activity = asObject(spec.activity_template);
  const steps = Array.isArray(activityPlan.presentation_steps_vi) ? activityPlan.presentation_steps_vi : [];
  const materialIds = Array.isArray(activityPlan.material_option_ids) ? activityPlan.material_option_ids : [];
  const safetyRules = Array.isArray(activityPlan.safety_rule_ids) ? activityPlan.safety_rule_ids : [];
  return (
    <View>
      <Text style={styles.resultTitle}>Trải nghiệm cần duyệt</Text>
      <Text style={styles.experienceGoal}>{textValue(focus.child_facing_goal_vi)}</Text>
      <Text style={styles.sessionMeta}>Spec {textValue(spec.spec_id)} · template {textValue(activity.template_id)} v{numberValue(activity.template_version)}</Text>
      <Text style={styles.fieldLabel}>Vật liệu trong template</Text>
      <Text style={styles.resultMeta}>{materialIds.map(String).join(' · ') || 'Không có'}</Text>
      <Text style={styles.fieldLabel}>Các bước</Text>
      {steps.map((step, index) => <Text key={`${index}-${String(step)}`} style={styles.stepText}>{index + 1}. {String(step)}</Text>)}
      <Text style={styles.fieldLabel}>Quy tắc an toàn</Text>
      <Text style={styles.resultMeta}>{safetyRules.map(String).join(' · ') || 'Theo template'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#F5F7F2' },
  content: { padding: 18, paddingBottom: 44, gap: 14 },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 2 },
  brandMark: { width: 38, height: 38, borderRadius: 13, backgroundColor: '#175D4B', alignItems: 'center', justifyContent: 'center' },
  brandMarkText: { color: '#FFFFFF', fontSize: 21, fontWeight: '900' },
  brandWords: { flex: 1 },
  brandTitle: { color: '#17352B', fontSize: 16, fontWeight: '900' },
  brandSubtitle: { color: '#74857B', fontSize: 9, fontWeight: '800', letterSpacing: 0.7, marginTop: 2 },
  smallButton: { borderRadius: 12, paddingHorizontal: 12, paddingVertical: 9, backgroundColor: '#E4ECE5' },
  smallButtonText: { fontSize: 11, fontWeight: '800', color: '#175D4B' },
  heroCard: { borderRadius: 23, padding: 19, backgroundColor: '#175D4B' },
  eyebrow: { color: '#BFE6CC', fontSize: 9, fontWeight: '900', letterSpacing: 1.5 },
  heroTitle: { color: '#FFFFFF', fontSize: 26, fontWeight: '900', marginTop: 8 },
  heroText: { color: '#E8F3EB', fontSize: 13, lineHeight: 19, marginTop: 7 },
  badgeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 14 },
  badge: { backgroundColor: 'rgba(255,255,255,0.13)', paddingHorizontal: 9, paddingVertical: 6, borderRadius: 20 },
  badgeText: { color: '#FFFFFF', fontSize: 10, fontWeight: '800' },
  noticeCard: { borderRadius: 18, padding: 15, backgroundColor: '#FFF8E9', borderColor: '#F1DFAF', borderWidth: 1 },
  noticeTitle: { color: '#785315', fontSize: 12, fontWeight: '900' },
  noticeText: { color: '#6B5B3E', fontSize: 11, lineHeight: 16, marginTop: 5 },
  endpointText: { color: '#8C7445', fontSize: 9, marginTop: 7 },
  errorCard: { borderRadius: 15, padding: 13, backgroundColor: '#FFF0ED', borderWidth: 1, borderColor: '#F3C5BA' },
  errorCode: { color: '#9F2F20', fontSize: 10, fontWeight: '900', letterSpacing: 0.7 },
  errorText: { color: '#6C3028', fontSize: 12, lineHeight: 17, marginTop: 4 },
  errorHint: { color: '#8B4B36', fontSize: 10, marginTop: 6 },
  noticeInline: { padding: 11, borderRadius: 13, backgroundColor: '#EAF3E9' },
  noticeInlineText: { color: '#315844', fontSize: 11, lineHeight: 16 },
  section: { borderRadius: 20, backgroundColor: '#FFFFFF', padding: 16, borderColor: '#E4E9E2', borderWidth: 1, gap: 10 },
  sectionHeading: { flexDirection: 'row', gap: 10, marginBottom: 2 },
  sectionNumber: { color: '#318064', fontSize: 12, fontWeight: '900', paddingTop: 2 },
  sectionCopy: { flex: 1 },
  sectionTitle: { color: '#20372E', fontSize: 15, fontWeight: '900' },
  sectionSubtitle: { color: '#76847B', fontSize: 10, lineHeight: 15, marginTop: 4 },
  sessionSummary: { padding: 12, borderRadius: 13, backgroundColor: '#F2F6F1' },
  sessionValue: { color: '#264336', fontSize: 12, fontWeight: '800' },
  sessionMeta: { color: '#76847B', fontSize: 10, lineHeight: 15, marginTop: 4 },
  actionButton: { minHeight: 46, borderRadius: 14, paddingHorizontal: 14, paddingVertical: 12, backgroundColor: '#175D4B', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 3 },
  actionButtonText: { color: '#FFFFFF', fontSize: 12, fontWeight: '900', textAlign: 'center' },
  actionButtonSecondary: { backgroundColor: '#EEF3EE', borderWidth: 1, borderColor: '#D8E3D8' },
  actionButtonSecondaryText: { color: '#355B49' },
  actionButtonDisabled: { opacity: 0.45 },
  secondaryButton: { borderRadius: 13, borderWidth: 1, borderColor: '#BCD4C2', backgroundColor: '#F6FAF5', padding: 12, alignItems: 'center' },
  secondaryButtonText: { color: '#24634E', fontSize: 12, fontWeight: '800' },
  imageCard: { borderRadius: 15, borderWidth: 1, borderColor: '#E7ECE6', overflow: 'hidden', backgroundColor: '#FBFCF8' },
  previewImage: { width: '100%', height: 210, backgroundColor: '#F0F1EC' },
  imageCaption: { color: '#738176', fontSize: 9, padding: 9 },
  webRendererWrap: { height: 390, overflow: 'hidden', borderRadius: 15, borderWidth: 1, borderColor: '#DCE7DB', backgroundColor: '#F7FAF6' },
  webRenderer: { flex: 1, backgroundColor: '#F7FAF6' },
  rendererError: { color: '#9F2F20', fontSize: 10, lineHeight: 15 },
  checkboxRow: { flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 7 },
  checkbox: { width: 19, height: 19, borderRadius: 6, borderWidth: 1.5, borderColor: '#A9B9AC', alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { backgroundColor: '#26805E', borderColor: '#26805E' },
  checkboxTick: { color: '#FFFFFF', fontSize: 12, lineHeight: 14, fontWeight: '900' },
  checkboxLabel: { flex: 1, color: '#45574B', fontSize: 10, lineHeight: 15 },
  liveWarning: { borderRadius: 14, backgroundColor: '#FFF6E5', borderColor: '#F0DFB5', borderWidth: 1, padding: 12 },
  liveWarningTitle: { color: '#875816', fontSize: 11, fontWeight: '900' },
  liveWarningText: { color: '#786342', fontSize: 10, lineHeight: 15, marginTop: 4 },
  resultCard: { backgroundColor: '#F7FAF6', borderRadius: 15, padding: 12, borderWidth: 1, borderColor: '#E2EAE1', gap: 7 },
  resultTitle: { color: '#2B4939', fontSize: 12, fontWeight: '900' },
  resultMeta: { color: '#7A887E', fontSize: 9, lineHeight: 14 },
  claimRow: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 7, borderTopWidth: 1, borderTopColor: '#E8EEE7' },
  claimCopy: { flex: 1 },
  claimLabel: { color: '#314A3B', fontSize: 12, fontWeight: '800' },
  claimMeta: { color: '#819087', fontSize: 9, marginTop: 3 },
  primaryPill: { paddingVertical: 6, paddingHorizontal: 8, borderRadius: 16, backgroundColor: '#E9EFE9' },
  primaryPillActive: { backgroundColor: '#D2ECDD' },
  primaryPillText: { color: '#58705F', fontSize: 8, fontWeight: '900' },
  primaryPillTextActive: { color: '#1B6647' },
  input: { borderRadius: 12, borderWidth: 1, borderColor: '#DDE6DE', backgroundColor: '#FFFFFF', paddingHorizontal: 12, paddingVertical: 11, color: '#263D30', fontSize: 12, marginTop: 5 },
  textButton: { paddingVertical: 8, alignItems: 'center' },
  textButtonText: { color: '#7A6250', fontSize: 10, fontWeight: '800', textAlign: 'center' },
  inputRow: { flexDirection: 'row', gap: 10 },
  field: { flex: 1 },
  fieldLabel: { color: '#506458', fontSize: 10, fontWeight: '900', marginTop: 6, marginBottom: 2 },
  optionPanel: { borderRadius: 15, padding: 12, backgroundColor: '#F7FAF6', gap: 7 },
  choiceGroup: { paddingTop: 6 },
  muted: { color: '#849087', fontSize: 10, lineHeight: 15, paddingVertical: 5 },
  activityChoice: { flexDirection: 'row', alignItems: 'center', gap: 9, padding: 10, borderRadius: 12, borderWidth: 1, borderColor: '#E1E8E0', backgroundColor: '#FFFFFF', marginTop: 5 },
  activityChoiceSelected: { borderColor: '#79B591', backgroundColor: '#EFF8F0' },
  radio: { width: 17, height: 17, borderRadius: 9, borderWidth: 1.5, borderColor: '#AAB9AC' },
  radioSelected: { borderWidth: 5, borderColor: '#26805E' },
  pillRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginVertical: 5 },
  choicePill: { borderRadius: 18, paddingHorizontal: 10, paddingVertical: 8, backgroundColor: '#F0F4F0', borderWidth: 1, borderColor: '#E1E9E1' },
  choicePillSelected: { backgroundColor: '#DFF0E4', borderColor: '#84B697' },
  choicePillText: { color: '#64756A', fontSize: 9, fontWeight: '800' },
  choicePillTextSelected: { color: '#226346' },
  resultLine: { padding: 10, borderRadius: 12, backgroundColor: '#EFF5EF', marginTop: 6 },
  resultLineTitle: { color: '#567060', fontSize: 9, fontWeight: '900' },
  resultLineValue: { color: '#345340', fontSize: 10, lineHeight: 14, marginTop: 3 },
  experienceGoal: { color: '#315440', fontSize: 14, fontWeight: '800', lineHeight: 20, marginTop: 4 },
  stepText: { color: '#53675A', fontSize: 10, lineHeight: 15 },
  scoreBlock: { marginTop: 5 },
  footer: { paddingVertical: 8, alignItems: 'center' },
  footerText: { color: '#8B978E', fontSize: 9, textAlign: 'center' },
  busyBar: { position: 'absolute', left: 18, right: 18, bottom: 14, borderRadius: 14, backgroundColor: '#173D32', padding: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  busyText: { color: '#FFFFFF', fontSize: 11, fontWeight: '800' },
});
