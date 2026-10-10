import React, { useRef, useState, useEffect, useMemo } from 'react';
import {
  ActivityIndicator,
  View,
  Text,
  Image,
  StyleSheet,
  ScrollView,
  Modal,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  type GestureResponderEvent,
} from 'react-native';
import * as Crypto from 'expo-crypto';
import * as NavigationBar from 'expo-navigation-bar';
import * as ScreenOrientation from 'expo-screen-orientation';
import { StatusBar } from 'expo-status-bar';
import { ResizeMode, Video } from 'expo-av';
import WebView, { type WebViewMessageEvent } from 'react-native-webview';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { Kid3DButton } from '../components/Kid3DButton';
import { RiveMascot } from '../components/RiveMascot';
import {
  CatDrawingArtwork,
  AnimatedMeadowScene,
  PlantSproutCard,
  NatureDiaryCard,
  MaterialIconSvg,
  ButterflyIconSvg,
  FlowerIconSvg,
  SunIconSvg,
  GrassIconSvg,
  FlappingButterflySvg,
  SpinningSunSvg,
  SwayingFlowerSvg,
  RipplingGrassSvg,
  MagicScanBeam,
  LivingAudioEqualizer,
  JellyBounceView,
  MomAvatarImage,
  GirlFeedbackAvatarImage,
  BounceInView,
  FloatingParticles,
  PulseGlow,
  SparkleRing,
  CuteStarIconSvg,
  RobotAiIllustration,
} from '../components/ArtworkCards';

import type { ScreenId } from '../types';
import { useAppContext } from '../context/AppContext';
import { FEEDBACK_OBSERVATIONS } from '../context/workflowSafety';
import { rendererWatchdogDeadline } from '../context/rendererPlaybackWatchdog.mjs';
import {
  ART_RENDERER_PROTOCOL_VERSION,
  createNativeBridgeInjection,
  MAX_RENDERER_MESSAGE_BYTES,
  RendererBootstrapSchema,
  RendererControlCommandSchema,
  RendererLoadCommandSchema,
  RendererLoadCommandV2Schema,
  RendererLoadCommandV3Schema,
  PixiRendererShowEnvelopeV1Schema,
  PixiRendererShowEnvelopeV2Schema,
  PixiRendererShowEnvelopeV3Schema,
  PixiRendererShowEnvelopeV4Schema,
  RendererLoadCommandV4Schema,
  RendererLoadCommandV5Schema,
  RendererLoadCommandV6Schema,
  RendererPlaybackEventEnvelopeSchema,
  RendererPlaybackStateEnvelopeSchema,
  normalizeRendererFailureCode,
} from '../../../../packages/art-renderer/src/protocol';
import { API_BASE_URL, createDemoApi, type StoryVideoJobStatus } from '../demo/api';

const storyVideoApi = createDemoApi();

function readyStoryVideoUrl(sessionId: string | null, job: StoryVideoJobStatus | null): string | null {
  if (!sessionId || !job || job.session_id !== sessionId || job.state !== 'READY'
    || !job.video_artifact_ref) return null;
  try {
    const url = new URL(job.video_artifact_ref);
    const api = new URL(API_BASE_URL);
    const expectedPath = `/v1/sessions/${encodeURIComponent(sessionId)}`
      + `/story-video/${encodeURIComponent(job.job_id)}/file`;
    return url.origin === api.origin && url.pathname === expectedPath ? url.toString() : null;
  } catch {
    return null;
  }
}

function storyVideoMessage(
  job: StoryVideoJobStatus | null,
  videoUrl: string | null,
  pollError: boolean,
  playbackError: boolean,
): string {
  if (pollError) return 'Chưa đọc được trạng thái video. Vui lòng kiểm tra kết nối.';
  if (playbackError) return 'Video đã tạo nhưng chưa phát được. Vui lòng thử lại sau.';
  if (!job) return 'Phiên này chưa có video câu chuyện. Vui lòng chờ quy trình tạo và kiểm tra hoàn tất.';
  if (job.state === 'READY') {
    return videoUrl
      ? 'Video đã sẵn sàng. Xem xong, người lớn có thể tiếp tục hoạt động.'
      : 'Liên kết video không hợp lệ. Vui lòng kiểm tra lại trước khi tiếp tục.';
  }
  if (['FAILED', 'BLOCKED', 'RETRYABLE_FAILURE', 'EXPIRED', 'CANCELLED', 'STALE_INPUT'].includes(job.state)) {
    return 'Tạo video chưa thành công. Vui lòng kiểm tra lại trước khi tiếp tục.';
  }
  return `Đang tạo video: ${job.progress_percent}%. Vui lòng chờ.`;
}

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

function rendererObject(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null ? value as Record<string, unknown> : {};
}

function rendererText(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function buildRendererLoadMessage(value: unknown, rendererInstanceId: string): string | null {
  const launch = rendererObject(value);
  if (launch.contractName === 'PixiRendererShowEnvelopeV4') {
    const envelope = PixiRendererShowEnvelopeV4Schema.safeParse(launch);
    if (!envelope.success) return null;
    const base = envelope.data.rendererLaunchV2;
    const command = RendererLoadCommandV6Schema.safeParse({
      contractName: 'RendererLoadCommandV6',
      contractVersion: '6.0',
      protocolVersion: '6',
      sequence: 1,
      rendererInstanceId,
      sessionId: base.sessionId,
      expectedSessionVersion: base.expectedSessionVersion,
      experienceSpecRef: base.experienceSpecRef,
      sourceReadEndpoint: base.sourceReadEndpoint,
      sourceReadCapability: base.sourceReadCapability,
      sourceSha256: base.sourceSha256,
      packageReadEndpoint: base.packageReadEndpoint,
      packageReadCapability: base.packageReadCapability,
      packageSha256: base.packageSha256,
      ...(base.maskReadEndpoint === undefined ? {} : {maskReadEndpoint: base.maskReadEndpoint}),
      ...(base.maskReadCapability === undefined ? {} : {maskReadCapability: base.maskReadCapability}),
      ...(base.maskSha256 === undefined ? {} : {maskSha256: base.maskSha256}),
      partMaskReads: base.partMaskReads,
      rigParts: base.rigParts,
      animationPlan: base.animationPlan,
      showPlan: envelope.data.showPlan,
      assetReads: envelope.data.assetReads,
      spriteCycleStatus: envelope.data.spriteCycleStatus,
      ...(envelope.data.spriteCycleReasonCode === undefined ? {} : {spriteCycleReasonCode: envelope.data.spriteCycleReasonCode}),
      ...(envelope.data.spriteCycle === undefined ? {} : {spriteCycle: envelope.data.spriteCycle}),
    });
    return command.success ? JSON.stringify(command.data) : null;
  }
  if (launch.contractName === 'PixiRendererShowEnvelopeV3') {
    const envelope = PixiRendererShowEnvelopeV3Schema.safeParse(launch);
    if (!envelope.success) return null;
    const base = envelope.data.rendererLaunchV2;
    const command = RendererLoadCommandV5Schema.safeParse({
      contractName: 'RendererLoadCommandV5',
      contractVersion: '5.0',
      protocolVersion: '5',
      sequence: 1,
      rendererInstanceId,
      sessionId: base.sessionId,
      expectedSessionVersion: base.expectedSessionVersion,
      experienceSpecRef: base.experienceSpecRef,
      sourceReadEndpoint: base.sourceReadEndpoint,
      sourceReadCapability: base.sourceReadCapability,
      sourceSha256: base.sourceSha256,
      packageReadEndpoint: base.packageReadEndpoint,
      packageReadCapability: base.packageReadCapability,
      packageSha256: base.packageSha256,
      ...(base.maskReadEndpoint === undefined ? {} : {maskReadEndpoint: base.maskReadEndpoint}),
      ...(base.maskReadCapability === undefined ? {} : {maskReadCapability: base.maskReadCapability}),
      ...(base.maskSha256 === undefined ? {} : {maskSha256: base.maskSha256}),
      partMaskReads: base.partMaskReads,
      rigParts: base.rigParts,
      animationPlan: base.animationPlan,
      showPlan: envelope.data.showPlan,
      assetReads: envelope.data.assetReads,
      spriteCycleStatus: envelope.data.spriteCycleStatus,
      ...(envelope.data.spriteCycleReasonCode === undefined ? {} : {spriteCycleReasonCode: envelope.data.spriteCycleReasonCode}),
      ...(envelope.data.spriteCycle === undefined ? {} : {spriteCycle: envelope.data.spriteCycle}),
    });
    return command.success ? JSON.stringify(command.data) : null;
  }
  if (launch.contractName === 'PixiRendererShowEnvelopeV2') {
    const envelope = PixiRendererShowEnvelopeV2Schema.safeParse(launch);
    if (!envelope.success) return null;
    const base = envelope.data.rendererLaunchV2;
    const command = RendererLoadCommandV4Schema.safeParse({
      contractName: 'RendererLoadCommandV4',
      contractVersion: '4.0',
      protocolVersion: '4',
      sequence: 1,
      rendererInstanceId,
      sessionId: base.sessionId,
      expectedSessionVersion: base.expectedSessionVersion,
      experienceSpecRef: base.experienceSpecRef,
      sourceReadEndpoint: base.sourceReadEndpoint,
      sourceReadCapability: base.sourceReadCapability,
      sourceSha256: base.sourceSha256,
      packageReadEndpoint: base.packageReadEndpoint,
      packageReadCapability: base.packageReadCapability,
      packageSha256: base.packageSha256,
      ...(base.maskReadEndpoint === undefined ? {} : {maskReadEndpoint: base.maskReadEndpoint}),
      ...(base.maskReadCapability === undefined ? {} : {maskReadCapability: base.maskReadCapability}),
      ...(base.maskSha256 === undefined ? {} : {maskSha256: base.maskSha256}),
      partMaskReads: base.partMaskReads,
      rigParts: base.rigParts,
      animationPlan: base.animationPlan,
      showPlan: envelope.data.showPlan,
      assetReads: envelope.data.assetReads,
      spriteCycleStatus: envelope.data.spriteCycleStatus,
      ...(envelope.data.spriteCycleReasonCode === undefined ? {} : {spriteCycleReasonCode: envelope.data.spriteCycleReasonCode}),
      ...(envelope.data.spriteCycle === undefined ? {} : {spriteCycle: envelope.data.spriteCycle}),
    });
    return command.success ? JSON.stringify(command.data) : null;
  }
  if (launch.contractName === 'PixiRendererShowEnvelopeV1') {
    const envelope = PixiRendererShowEnvelopeV1Schema.safeParse(launch);
    if (!envelope.success) return null;
    const base = envelope.data.rendererLaunchV2;
    const command = RendererLoadCommandV3Schema.safeParse({
      contractName: 'RendererLoadCommandV3',
      contractVersion: '3.0',
      protocolVersion: '3',
      sequence: 1,
      rendererInstanceId,
      sessionId: base.sessionId,
      expectedSessionVersion: base.expectedSessionVersion,
      experienceSpecRef: base.experienceSpecRef,
      sourceReadEndpoint: base.sourceReadEndpoint,
      sourceReadCapability: base.sourceReadCapability,
      sourceSha256: base.sourceSha256,
      packageReadEndpoint: base.packageReadEndpoint,
      packageReadCapability: base.packageReadCapability,
      packageSha256: base.packageSha256,
      ...(base.maskReadEndpoint === undefined ? {} : {maskReadEndpoint: base.maskReadEndpoint}),
      ...(base.maskReadCapability === undefined ? {} : {maskReadCapability: base.maskReadCapability}),
      ...(base.maskSha256 === undefined ? {} : {maskSha256: base.maskSha256}),
      partMaskReads: base.partMaskReads,
      rigParts: base.rigParts,
      animationPlan: base.animationPlan,
      showPlan: envelope.data.showPlan,
      assetReads: envelope.data.assetReads,
    });
    return command.success ? JSON.stringify(command.data) : null;
  }
  if (launch.contractName === 'PixiRendererLaunchV2') {
    const command = RendererLoadCommandV2Schema.safeParse({
      contractName: 'RendererLoadCommandV2',
      contractVersion: '2.0',
      protocolVersion: '2',
      sequence: 1,
      rendererInstanceId,
      sessionId: rendererText(launch.sessionId),
      expectedSessionVersion: launch.expectedSessionVersion,
      experienceSpecRef: launch.experienceSpecRef,
      sourceReadEndpoint: launch.sourceReadEndpoint,
      sourceReadCapability: launch.sourceReadCapability,
      sourceSha256: launch.sourceSha256,
      packageReadEndpoint: launch.packageReadEndpoint,
      packageReadCapability: launch.packageReadCapability,
      packageSha256: launch.packageSha256,
      ...(launch.maskReadEndpoint === undefined ? {} : {maskReadEndpoint: launch.maskReadEndpoint}),
      ...(launch.maskReadCapability === undefined ? {} : {maskReadCapability: launch.maskReadCapability}),
      ...(launch.maskSha256 === undefined ? {} : {maskSha256: launch.maskSha256}),
      partMaskReads: launch.partMaskReads ?? [],
      rigParts: launch.rigParts ?? [],
      animationPlan: launch.animationPlan,
    });
    return command.success ? JSON.stringify(command.data) : null;
  }
  const command = RendererLoadCommandSchema.safeParse({
    contractName: 'RendererLoadCommandV1',
    contractVersion: '1.0',
    protocolVersion: ART_RENDERER_PROTOCOL_VERSION,
    sequence: 1,
    rendererInstanceId,
    sessionId: rendererText(launch.sessionId),
    expectedSessionVersion: launch.expectedSessionVersion,
    experienceSpecRef: launch.experienceSpecRef,
    sourceReadEndpoint: launch.sourceReadEndpoint,
    sourceReadCapability: launch.sourceReadCapability,
    assetManifest: launch.assetManifest,
    animationPlan: launch.animationPlan,
    sceneExplorationPlan: launch.sceneExplorationPlan,
    sceneFocusPlan: launch.sceneFocusPlan,
  });
  return command.success ? JSON.stringify(command.data) : null;
}

function utf8ByteLength(value: string): number {
  return encodeURIComponent(value).replace(/%[0-9A-F]{2}/g, 'U').length;
}

function rendererBridgeFailureCode(error: unknown): string {
  if (error instanceof Error && error.message === 'RENDERER_COMMAND_TOO_LARGE') {
    return 'RENDERER_COMMAND_TOO_LARGE';
  }
  if (error instanceof Error && error.message === 'RENDERER_MESSAGE_INVALID_JSON') {
    return 'RENDERER_MESSAGE_INVALID_JSON';
  }
  return 'RENDERER_BRIDGE_INJECTION_FAILED';
}

const FlowPrerequisiteNotice: React.FC<{
  title: string;
  message: string;
  action: string;
  onAction: () => void;
}> = ({ title, message, action, onAction }) => (
  <ScrollView contentContainerStyle={styles.screenContainer}>
    <View style={styles.topHeader}>
      <Text style={styles.screenHeaderTitle}>Bước tiếp theo</Text>
      <View style={{ width: 30 }} />
    </View>
    <View style={[styles.topicSummaryCard, { marginTop: 28 }]}>
      <Ionicons name="lock-closed" size={26} color="#2563EB" />
      <View style={{ flex: 1 }}>
        <Text style={styles.topicSummaryText}>{title}</Text>
        <Text style={styles.activityChoiceSummary}>{message}</Text>
      </View>
    </View>
    <Kid3DButton title={action} color="blue" size="md" onPress={onAction} />
  </ScrollView>
);

// ==========================================
// 1. AI PROCESSING (Image 1 - Screen 1)
// ==========================================
export const AiProcessingScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    aiProgress,
    selectedChild,
    runAiSimulation,
    workflowBusy,
    workflowNotice,
    narrationMode,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (workflowBusy !== 'Phân tích ảnh') return;
    const timer = setInterval(() => setElapsedSeconds((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, [workflowBusy]);

  const loadingStage = elapsedSeconds < 3
    ? 'Đang kiểm tra ảnh'
    : elapsedSeconds < 8
      ? narrationMode === 'none' ? 'Đang tìm nhân vật và hành động' : 'Đang ghép tranh với lời kể'
      : elapsedSeconds < 18
        ? 'Đang tạo các hướng câu chuyện'
        : 'Bước này cần thêm một chút thời gian';

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Xử lý câu chuyện</Text>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Đang hiểu bức tranh...</Text>
        <Text style={styles.headingSubtitle}>
          Mình đang xem tranh của bé {selectedChild.name}
          {narrationMode === 'none' ? '.' : ' và lắng nghe lời kể để hiểu đúng hơn.'}
        </Text>
      </View>

      {/* Robot Mascot with SparkleRing rotating around it — magical loading feel! */}
      <View style={[styles.robotCenterBox, { alignItems: 'center', justifyContent: 'center' }]}>
        <SparkleRing size={180} />
        <Image
          source={require('../../assets/images/robot_ai.jpg')}
          style={{ width: 150, height: 150, resizeMode: 'contain' }}
        />
      </View>

      {/* Stage-aware loading: do not invent a percentage while inference is synchronous. */}
      <View style={styles.progressContainer}>
        <View style={styles.progressLabelRow}>
          <Text style={styles.progressLabel}>{workflowBusy === 'Phân tích ảnh' ? loadingStage : 'Sẵn sàng khám phá'}</Text>
          <Ionicons name={workflowBusy === 'Phân tích ảnh' ? 'sparkles' : 'checkmark-circle'} size={18} color={colors.blueDeep} />
        </View>
        <View style={styles.progressBarTrack}>
          <View style={[styles.progressBarFill, { width: workflowBusy === 'Phân tích ảnh' ? '68%' : aiProgress >= 100 ? '100%' : '12%' }]} />
        </View>
        {elapsedSeconds >= 18 && workflowBusy === 'Phân tích ảnh' && (
          <Text style={styles.pixiSubtitle}>AI vẫn đang làm việc; bạn có thể quay lại nếu không muốn chờ.</Text>
        )}
      </View>

      {/* 4 Pipeline Checklist Items */}
      <View style={styles.checklistCard}>
        <View style={styles.checkItem}>
          <View style={[styles.checkCircle, { backgroundColor: colors.greenDeep }]}>
            <Ionicons name="checkmark" size={12} color={colors.white} />
          </View>
          <Text style={styles.checkTextDone}>Ảnh đã sẵn sàng</Text>
        </View>

        <View style={styles.checkItem}>
          <View style={[styles.checkCircle, aiProgress >= 20 ? { backgroundColor: colors.greenDeep } : { borderColor: colors.blue, borderWidth: 2, backgroundColor: colors.blueSoft }]}>
            <Ionicons name={aiProgress >= 20 ? 'checkmark' : 'sync'} size={12} color={aiProgress >= 20 ? colors.white : colors.blueDeep} />
          </View>
          <Text style={[styles.checkTextDone, aiProgress < 20 && { color: colors.blueDeep }]}>Chuẩn bị lời kể theo lựa chọn của người lớn</Text>
        </View>

        <View style={styles.checkItem}>
          <View
            style={[
              styles.checkCircle,
              aiProgress >= 70
                ? { backgroundColor: colors.greenDeep }
                : { borderColor: colors.blue, borderWidth: 2, backgroundColor: colors.blueSoft },
            ]}
          >
            <Ionicons
              name={aiProgress >= 70 ? 'checkmark' : 'sync'}
              size={12}
              color={aiProgress >= 70 ? colors.white : colors.blueDeep}
            />
          </View>
          <Text style={[styles.checkTextDone, aiProgress < 70 && { color: colors.blueDeep }]}>
            Ghép chi tiết trong tranh với lời kể
          </Text>
        </View>

        <View style={styles.checkItem}>
          <View
            style={[
              styles.checkCircle,
              aiProgress >= 100
                ? { backgroundColor: colors.greenDeep }
                : { borderColor: colors.line, borderWidth: 1.5, backgroundColor: colors.white },
            ]}
          >
            {aiProgress >= 100 && <Ionicons name="checkmark" size={12} color={colors.white} />}
          </View>
          <Text style={aiProgress >= 100 ? styles.checkTextDone : styles.checkTextPending}>
            Chuẩn bị kết quả để người lớn kiểm tra
          </Text>
        </View>
      </View>

      {/* Bottom Ribbon */}
      <TouchableOpacity
        activeOpacity={0.9}
        disabled={workflowBusy === 'Phân tích ảnh'}
        onPress={() => {
          void runAiSimulation();
        }}
        style={styles.ribbonBanner}
      >
        <Text style={styles.ribbonText}>
          {workflowBusy === 'Phân tích ảnh' ? 'Đang đọc bức tranh...' : 'Bắt đầu khám phá ✨'}
        </Text>
      </TouchableOpacity>
      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginTop: 10 }}>{workflowNotice}</Text>}
    </ScrollView>
  );
};

// ==========================================
// 2. SCENE UNDERSTANDING (Image 1 - Screen 2 / Gate A)
// ==========================================
export const SceneUnderstandingScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    selectedDrawing,
    sceneData,
    analysisClaims,
    topicDirections,
    selectedTopicDirectionId,
    selectTopicDirection,
    selectedClaimIds,
    primaryClaimId,
    correction,
    setCorrection,
    confirmGateA,
    requerySubject,
    directionRequeryUsed,
    workflowNotice,
    workflowBusy,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const [showEvidence, setShowEvidence] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const selectedDirection = topicDirections.find((direction) => direction.direction_id === selectedTopicDirectionId);
  const canRequeryCurrentTopic = Boolean(correction.trim() || selectedDirection?.requires_requery);
  const needsAdultSubject = analysisClaims.length === 0 && topicDirections.length === 0;

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <View style={styles.aiSuccessBadge}>
          <Ionicons name="sparkles" size={13} color="#7C3AED" />
          <Text style={styles.aiSuccessBadgeText}>GỢI Ý TỪ ẢNH & LỜI KỂ</Text>
        </View>
        <TouchableOpacity onPress={() => nav('dashboard')} style={styles.backBtn}>
          <Ionicons name="home-outline" size={18} color={colors.textBody} />
        </TouchableOpacity>
      </View>

      {/* Main Heading */}
      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>
          {needsAdultSubject ? 'Người lớn giúp mình chọn chủ thể 🎨' : 'Mình tìm thấy những chi tiết này 🎨'}
        </Text>
        <Text style={styles.headingSubtitle}>
          {needsAdultSubject
            ? 'AI chưa nhận ra chủ thể lần này. Bạn có thể nhập chủ thể bên dưới, phân tích lại một lần hoặc tiếp tục với xác nhận của mình.'
            : 'Người lớn hãy kiểm tra và chọn chủ đề chính trước khi tiếp tục.'}
        </Text>
      </View>

      {/* 1. ARTWORK SPOTLIGHT CARD — the image is evidence, not a tap target. */}
      <View style={styles.artworkSpotlightCard}>
        <View style={styles.tapeHeader}>
          <View style={styles.washiTape} />
        </View>
        <View style={styles.artworkInnerWrap}>
          <Image
            source={selectedDrawing ? { uri: selectedDrawing.uri } : require('../../assets/images/photo_cat_paper.jpg')}
            style={styles.artworkThumbImg}
          />
          {!needsAdultSubject && <MagicScanBeam containerHeight={140} />}

          {/* Short, non-interactive labels keep the child-facing preview lively. */}
          {sceneData.entities[0] && <View style={[styles.aiScanPin, { top: 12, left: 14 }]}>
            <View style={[styles.aiScanDot, { backgroundColor: '#A855F7' }]} />
            <Text style={styles.aiScanPinText}>{sceneData.entities[0].icon} {sceneData.entities[0].name}</Text>
          </View>}
          {sceneData.entities[1] && <View style={[styles.aiScanPin, { bottom: 14, right: 14 }]}>
            <View style={[styles.aiScanDot, { backgroundColor: '#F43F5E' }]} />
            <Text style={styles.aiScanPinText}>{sceneData.entities[1].icon} {sceneData.entities[1].name}</Text>
          </View>}
          {sceneData.entities[2] && <View style={[styles.aiScanPin, { top: 14, right: 14 }]}>
            <View style={[styles.aiScanDot, { backgroundColor: '#F59E0B' }]} />
            <Text style={styles.aiScanPinText}>{sceneData.entities[2].icon} {sceneData.entities[2].name}</Text>
          </View>}
        </View>
        <View style={styles.artworkCaptionRow}>
          <Ionicons name="sparkles" size={13} color="#2563EB" />
          <Text style={styles.artworkCaptionText}>
            {needsAdultSubject
              ? 'Ảnh gốc • chưa có chủ thể AI đề xuất'
              : `Ảnh gốc • ${sceneData.entities.length} chi tiết được đề xuất`}
          </Text>
        </View>
      </View>

      {/* Topic directions are generated by the single semantic understanding request. */}
      <View style={styles.sectionHeaderRow}>
        <Text style={styles.sectionHeadingSmall}>Con muốn kể câu chuyện nào?</Text>
        <View style={styles.countBadge}>
          <Text style={styles.countBadgeText}>{topicDirections.length} hướng</Text>
        </View>
      </View>
      <View style={styles.entitiesGridNew}>
        {topicDirections.map((direction) => {
          const selected = selectedTopicDirectionId === direction.direction_id;
          return (
            <TouchableOpacity
              key={direction.direction_id}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              accessibilityLabel={`Hướng ${direction.priority}: ${direction.title_vi}`}
              activeOpacity={0.86}
              onPress={() => selectTopicDirection(direction.direction_id)}
              style={[styles.entityCardNew, {
                backgroundColor: selected ? '#F0FDF4' : '#FFFFFF',
                borderColor: selected ? '#2563EB' : '#CBD5E1',
                borderWidth: selected ? 2 : 1,
              }]}
            >
              <Text style={styles.entityNameNew}>{direction.title_vi}</Text>
              <Text style={styles.entityDetailText}>{direction.summary_vi}</Text>
              <Text style={[styles.entityBadgeTextNew, { marginTop: 8, color: selected ? '#15803D' : '#64748B' }]}>
                {selected ? '✓ Đang chọn' : 'Chọn chủ đề này'}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <TouchableOpacity
        accessibilityRole="button"
        accessibilityState={{ expanded: showEvidence }}
        onPress={() => setShowEvidence((value) => !value)}
        style={styles.adultDetailsToggle}
      >
        <Text style={styles.adultDetailsTitle}>Chi tiết AI nhận ra</Text>
        <Ionicons name={showEvidence ? 'chevron-up' : 'chevron-down'} size={20} color={colors.blueDeep} />
      </TouchableOpacity>
      {showEvidence && (
        <View style={styles.evidenceChipWrap}>
          {analysisClaims.map((claim) => (
            <View key={claim.observation_id} style={styles.evidenceChip}>
              <Text style={styles.evidenceChipText}>{claim.label.value}</Text>
            </View>
          ))}
        </View>
      )}

      <View style={[styles.entitiesGridNew, { display: 'none' }]}>
        {/* Row 1: Con bướm + Bông hoa */}
        <View style={styles.entityRowNew}>
          <BounceInView delay={0} style={{ flex: 1 }}>
            <JellyBounceView>
              <View style={[styles.entityCardNew, { backgroundColor: '#FAF5FF', borderColor: '#E9D5FF' }]}>
                <View style={styles.cardTagCorner}>
                  <Text style={[styles.cardTagText, { color: '#7E22CE', backgroundColor: '#F3E8FF' }]}>
                    Chính 🌟
                  </Text>
                </View>
                <View style={[styles.entityOrbNew, { backgroundColor: '#EDE9FE' }]}>
                  <FlappingButterflySvg size={42} />
                </View>
                <Text style={[styles.entityNameNew, { color: '#581C87' }]}>Con bướm</Text>
                <Text style={styles.entityDetailText}>1 nhân vật biết bay</Text>
                <View style={[styles.entityBadgeNew, { backgroundColor: '#F3E8FF' }]}>
                  <Text style={[styles.entityBadgeTextNew, { color: '#7E22CE' }]}>🦋 Đập cánh 3D & bay lượn</Text>
                </View>
              </View>
            </JellyBounceView>
          </BounceInView>

          <BounceInView delay={100} style={{ flex: 1 }}>
            <JellyBounceView>
              <View style={[styles.entityCardNew, { backgroundColor: '#FFF1F2', borderColor: '#FECDD3' }]}>
                <View style={styles.cardTagCorner}>
                  <Text style={[styles.cardTagText, { color: '#BE123C', backgroundColor: '#FFE4E6' }]}>
                    Chi tiết 🌸
                  </Text>
                </View>
                <View style={[styles.entityOrbNew, { backgroundColor: '#FFE4E6' }]}>
                  <SwayingFlowerSvg size={42} />
                </View>
                <Text style={[styles.entityNameNew, { color: '#881337' }]}>Bông hoa</Text>
                <Text style={styles.entityDetailText}>2 bông cúc rực rỡ</Text>
                <View style={[styles.entityBadgeNew, { backgroundColor: '#FFE4E6' }]}>
                  <Text style={[styles.entityBadgeTextNew, { color: '#BE123C' }]}>🌸 Đung đưa trong gió</Text>
                </View>
              </View>
            </JellyBounceView>
          </BounceInView>
        </View>

        {/* Row 2: Mặt trời + Bãi cỏ */}
        <View style={styles.entityRowNew}>
          <BounceInView delay={200} style={{ flex: 1 }}>
            <JellyBounceView>
              <View style={[styles.entityCardNew, { backgroundColor: '#FFFBEB', borderColor: '#FDE68A' }]}>
                <View style={styles.cardTagCorner}>
                  <Text style={[styles.cardTagText, { color: '#B45309', backgroundColor: '#FEF3C7' }]}>
                    Thiên nhiên ☀️
                  </Text>
                </View>
                <View style={[styles.entityOrbNew, { backgroundColor: '#FEF3C7' }]}>
                  <SpinningSunSvg size={42} />
                </View>
                <Text style={[styles.entityNameNew, { color: '#78350F' }]}>Mặt trời</Text>
                <Text style={styles.entityDetailText}>1 ông mặt trời ấm áp</Text>
                <View style={[styles.entityBadgeNew, { backgroundColor: '#FEF3C7' }]}>
                  <Text style={[styles.entityBadgeTextNew, { color: '#B45309' }]}>☀️ Tỏa nắng xoay tròn</Text>
                </View>
              </View>
            </JellyBounceView>
          </BounceInView>

          <BounceInView delay={300} style={{ flex: 1 }}>
            <JellyBounceView>
              <View style={[styles.entityCardNew, { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' }]}>
                <View style={styles.cardTagCorner}>
                  <Text style={[styles.cardTagText, { color: '#15803D', backgroundColor: '#DCFCE7' }]}>
                    Bối cảnh 🌿
                  </Text>
                </View>
                <View style={[styles.entityOrbNew, { backgroundColor: '#DCFCE7' }]}>
                  <RipplingGrassSvg size={42} />
                </View>
                <Text style={[styles.entityNameNew, { color: '#14532D' }]}>Bãi cỏ xanh</Text>
                <Text style={styles.entityDetailText}>1 thảm cỏ sân vườn</Text>
                <View style={[styles.entityBadgeNew, { backgroundColor: '#DCFCE7' }]}>
                  <Text style={[styles.entityBadgeTextNew, { color: '#15803D' }]}>🌱 Rung rinh gợn sóng</Text>
                </View>
              </View>
            </JellyBounceView>
          </BounceInView>
        </View>

        {/* More details banner */}
        <BounceInView delay={380}>
          <TouchableOpacity activeOpacity={0.85} style={styles.moreEntitiesPill}>
            <Ionicons name="sparkles" size={14} color="#6366F1" />
            <Text style={styles.moreEntitiesPillText}>+ Khám phá thêm 8 chi tiết vi diệu khác từ tranh vẽ</Text>
            <Ionicons name="chevron-down" size={14} color="#6366F1" />
          </TouchableOpacity>
        </BounceInView>
      </View>

      {/* 3. VOICE TRANSCRIPT BOX — Interactive Waveform Player Bubble */}
      <View style={styles.sectionHeaderRow}>
        <Text style={styles.sectionHeadingSmall}>Giọng kể sinh động của con</Text>
        <View style={styles.audioDurationPill}>
          <Text style={styles.audioDurationText}>00:12</Text>
        </View>
      </View>

      <View style={styles.voiceAudioCard}>
        <View style={styles.voiceAudioHeader}>
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => setIsPlayingAudio(!isPlayingAudio)}
            style={styles.voicePlayBtn}
          >
            <Ionicons
              name={isPlayingAudio ? 'pause' : 'play'}
              size={18}
              color={colors.white}
              style={isPlayingAudio ? {} : { marginLeft: 2 }}
            />
          </TouchableOpacity>

          <View style={{ flex: 1 }}>
            <Text style={styles.voiceAudioTitle}>Giọng kể của bé {selectedChild.name}</Text>
            <Text style={styles.voiceAudioDuration}>
              {isPlayingAudio ? 'Đang phát âm thanh...' : 'Chạm nút play để nghe lại'}
            </Text>
          </View>

          {/* Living Animated Equalizer Waveform */}
          <LivingAudioEqualizer isPlaying={isPlayingAudio} />
        </View>

        <View style={styles.voiceQuoteDivider} />

        {/* Speech Bubble Quote */}
        <View style={styles.speechQuoteBox}>
          <Text style={styles.speechQuoteIcon}>“</Text>
          <Text style={styles.voiceQuoteText}>
            {sceneData.voiceTranscript}
          </Text>
          <Text style={styles.speechQuoteIconEnd}>”</Text>
        </View>
      </View>

      {/* 4. MASCOT COMPLIMENT CARD */}
      <View style={styles.complimentCard}>
        <View style={styles.complimentAvatar}>
          <GirlFeedbackAvatarImage size={42} />
        </View>
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Text style={styles.complimentTitle}>{sceneData.complimentTitle}</Text>
            <Text style={{ fontSize: 15 }}>🎉</Text>
          </View>
          <Text style={styles.complimentSub}>
            Mình đã ghép gợi ý từ bức tranh và lời kể. Người lớn vẫn là người quyết định chủ đề nhé.
          </Text>
        </View>
      </View>

      <TextInput
        value={correction}
        onChangeText={setCorrection}
        placeholder="Sửa hoặc nhập chủ thể chính, ví dụ: con chim"
        placeholderTextColor="#94A3B8"
        style={styles.gateCorrectionInput}
        maxLength={200}
      />
      <Text style={styles.gateSubjectOriginHint}>
        Chủ thể nhập tại đây được ghi nhận là xác nhận của người lớn, không giả thành kết quả AI.
      </Text>
      {topicDirections.length === 0 && (
        <Text style={styles.gateSubjectRecoveryHint}>
          AI chưa đưa ra chủ thể. Nhập chủ thể bạn nhìn thấy để tiếp tục; có thể yêu cầu AI phân tích lại một lần.
        </Text>
      )}
      <TouchableOpacity
        accessibilityRole="button"
        disabled={directionRequeryUsed || !canRequeryCurrentTopic || !!workflowBusy}
        onPress={() => { void requerySubject(); }}
        style={[
          styles.gateSubjectRequeryButton,
          (directionRequeryUsed || !correction.trim() || !!workflowBusy) && styles.gateSubjectRequeryButtonDisabled,
        ]}
      >
        <Text style={styles.gateSubjectRequeryText}>
          {workflowBusy === 'Phân tích lại chủ thể'
            ? 'Đang phân tích lại…'
            : directionRequeryUsed
              ? 'Đã dùng lượt phân tích lại'
              : correction.trim()
                ? 'Phân tích lại theo chủ thể này (tối đa 1 lần)'
                : 'Phân tích lại theo hướng này (tối đa 1 lần)'}
        </Text>
      </TouchableOpacity>
      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginTop: 9 }}>{workflowNotice}</Text>}

      {/* 5. PRIMARY 3D CTA BUTTON */}
      <View style={[styles.actionBottom, { marginTop: 14 }]}>
        <PulseGlow>
          <Kid3DButton
            title={workflowBusy === 'Xác nhận Gate A'
              ? 'Đang chuẩn bị chuyển động...'
              : correction.trim() ? 'Xác nhận chủ thể này, tiếp tục' : 'Đúng rồi, tiếp tục'}
            color="blue"
            size="lg"
            disabled={!!workflowBusy || (!correction.trim() && (!primaryClaimId || selectedClaimIds.length === 0))}
            onPress={async () => {
              if (await confirmGateA()) nav('story_preview');
            }}
          />
        </PulseGlow>
      </View>
      <Modal
        visible={workflowBusy === 'Xác nhận Gate A' || workflowBusy === 'Phân tích lại chủ thể'}
        transparent
        animationType="fade"
        statusBarTranslucent
        onRequestClose={() => undefined}
      >
        <View style={styles.rigPreparationBackdrop}>
          <View style={styles.rigPreparationCard}>
            <ActivityIndicator size="large" color="#2563EB" />
            <Text accessibilityRole="header" style={styles.rigPreparationTitle}>
              {workflowBusy === 'Phân tích lại chủ thể' ? 'Đang kiểm tra lại chủ thể' : 'Đang chuẩn bị chuyển động'}
            </Text>
            <Text style={styles.rigPreparationText} accessibilityLiveRegion="polite">
              {workflowBusy === 'Phân tích lại chủ thể'
                ? 'Đang gửi đúng một yêu cầu phân tích lại. Ảnh gốc vẫn được giữ nguyên.'
                : 'Mình đang phân tích chủ thể và tách nét vẽ. Ảnh gốc vẫn được giữ nguyên.'}
            </Text>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

// ==========================================
// 3. STORY PREVIEW (Image 1 - Screen 3)
// ==========================================
export const StoryPreviewScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild, selectedDrawing, sceneData } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Xem trước câu chuyện</Text>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Chủ đề đã sẵn sàng!</Text>
        <Text style={styles.headingSubtitle}>
          Từ bức tranh của bé {selectedChild.name}, mình sẽ tìm hoạt động ngoài đời phù hợp.
        </Text>
      </View>

      {/* Meadow Animation Viewport */}
      <View style={styles.meadowContainer}>
        <View style={styles.durationBadge}>
          <Text style={styles.durationText}>ẢNH GỐC</Text>
        </View>
        {selectedDrawing ? (
          <Image source={{ uri: selectedDrawing.uri }} style={styles.storySourceImage} resizeMode="contain" />
        ) : (
          <AnimatedMeadowScene height={190} showPlayButton={false} />
        )}
      </View>

      <Text style={[styles.storyQuoteCaption, { marginBottom: 12 }]}>“{sceneData.storyTitle}”</Text>

      <View style={styles.sceneThumbnailsRow}>
        {sceneData.entities.slice(0, 3).map((entity, index) => (
          <BounceInView key={entity.id} delay={index * 100} style={{ flex: 1 }}>
            <View style={[styles.sceneThumbnail, { backgroundColor: '#F8FAFC', borderColor: '#DBEAFE' }]}>
              <View style={[styles.sceneIconCircle, { backgroundColor: '#EFF6FF' }]}>
                <Text style={{ fontSize: 24 }}>{entity.icon}</Text>
              </View>
              <Text style={styles.sceneNumberText}>Chi tiết {index + 1}</Text>
              <Text numberOfLines={2} style={styles.sceneActionText}>{entity.name}</Text>
            </View>
          </BounceInView>
        ))}
      </View>


      <Text style={styles.storyQuoteCaption}>
        Ảnh gốc luôn được giữ nguyên trong phiên này. ♡
      </Text>

      {/* Primary 3D Button matching Image 1 */}
      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Xem hoạt động phù hợp ->"
          color="blue"
          size="lg"
          onPress={() => nav('activity_recommend')}
        />
      </View>
    </ScrollView>
  );
};

// ==========================================
// 4. FULL VIDEO PLAYER (Image 1 - Screen 4)
// ==========================================
export const VideoPlayerScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const [isPlaying, setIsPlaying] = useState(true);

  return (
    <View style={{ flex: 1, backgroundColor: colors.white }}>
      {/* Top Header matching Image 1 */}
      <View style={[styles.topHeader, { paddingHorizontal: 16, paddingTop: 10, paddingBottom: 6 }]}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <View style={{ alignItems: 'center' }}>
          <Text style={styles.screenHeaderTitle}>Giấc mơ của chú bướm</Text>
          <Text style={{ fontSize: 10, color: colors.textSoft }}>Một câu chuyện từ bức vẽ của bé {selectedChild.name}</Text>
        </View>
        <TouchableOpacity style={styles.backBtn}>
          <Ionicons name="share-social-outline" size={18} color={colors.textBody} />
        </TouchableOpacity>
      </View>

      {/* Video Viewport matching Image 1 */}
      <View style={[styles.videoPlayerBox, { flex: 1, overflow: 'hidden' }]}>
        <Image
          source={require('../../assets/images/video_scene_only.jpg')}
          style={{ width: '100%', height: '100%', resizeMode: 'cover' }}
        />
        {/* Play/Pause overlay hint at center bottom of video */}
        <View style={{ position: 'absolute', bottom: 12, left: 16, right: 16, flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <TouchableOpacity onPress={() => setIsPlaying(!isPlaying)} style={{ width: 28, height: 28, alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name={isPlaying ? 'pause' : 'play'} size={20} color="rgba(255,255,255,0.9)" />
          </TouchableOpacity>
          {/* Scrubber */}
          <View style={{ flex: 1, height: 3, backgroundColor: 'rgba(255,255,255,0.35)', borderRadius: 2 }}>
            <View style={{ width: '37%', height: '100%', backgroundColor: '#FFFFFF', borderRadius: 2 }} />
          </View>
          <Text style={{ fontSize: 11, color: 'rgba(255,255,255,0.9)', fontWeight: '700' }}>00:18 / 00:48</Text>
        </View>
      </View>

      {/* 3 Circular Action Buttons below video matching Image 1 Screen 4 */}
      <View style={styles.videoActionsRow}>
        <View style={styles.videoActionCol}>
          <TouchableOpacity style={styles.videoCircleBtn} onPress={() => setIsPlaying(true)}>
            <Ionicons name="refresh" size={22} color={colors.textBody} />
          </TouchableOpacity>
          <Text style={styles.videoActionLabel}>Xem lại</Text>
        </View>

        <View style={styles.videoActionCol}>
          <TouchableOpacity style={styles.videoCircleBtn}>
            <Ionicons name="share-outline" size={22} color={colors.textBody} />
          </TouchableOpacity>
          <Text style={styles.videoActionLabel}>Chia sẻ</Text>
        </View>

        <View style={styles.videoActionCol}>
          <TouchableOpacity style={styles.videoCircleBtn} onPress={() => nav('activity_recommend')}>
            <Ionicons name="download-outline" size={22} color={colors.textBody} />
          </TouchableOpacity>
          <Text style={styles.videoActionLabel}>Lưu video</Text>
        </View>
      </View>
    </View>
  );
};

// ==========================================
// 5. ACTIVITY RECOMMENDATION (Image 1 - Screen 5 / Gate B)
// ==========================================
export const ActivityRecommendScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    selectedAgeMonths,
    sceneData,
    contextOptions,
    selectedChildLearningProfile,
    selectedBackendActivity,
    activityRecommendationCards,
    rankedActivityIds,
    activityRankingStatus,
    selectBackendActivity,
    prepareActivityWorkflow,
    sessionState,
    sessionId,
    gateAConfirmed,
    workflowBusy,
    workflowError,
    workflowNotice,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const autoLoadKeyRef = useRef<string | null>(null);
  const [showAllActivities, setShowAllActivities] = useState(false);
  const emptyActivityMessage = contextOptions?.empty_reason === 'TOPIC_UNMAPPED'
    ? 'Chủ đề này chưa được nối với hoạt động nào trong danh mục đã duyệt. Hãy quay lại kiểm tra chủ thể hoặc chọn một hướng khác.'
    : contextOptions?.empty_reason === 'NO_RELEVANT_ACTIVITY_FOR_AGE'
      ? 'Danh mục hiện chưa có hoạt động phù hợp với chủ đề này ở độ tuổi của bé. Hãy quay lại chọn hướng khác; bộ lọc tuổi vẫn được giữ.'
      : contextOptions?.empty_reason === 'RELEVANT_ACTIVITY_BLOCKED_BY_SAFETY_OR_ADULT_PRESENCE'
        ? 'Các hoạt động liên quan hiện không đáp ứng điều kiện an toàn hoặc người lớn đồng hành. Hãy kiểm tra lại điều kiện cùng bé.'
        : contextOptions?.empty_reason === 'CATALOG_CARD_NOT_DISPLAYABLE'
          ? 'Có hoạt động khớp chủ đề nhưng thông tin hiển thị trong danh mục chưa đầy đủ. Không có mục nào được chọn tự động; hãy thử lại sau.'
          : 'Máy chủ chưa cung cấp lý do cho danh sách rỗng. Hãy thử tải lại hoặc quay lại chủ đề.';
  const hasPreparedActivity = Boolean(
    contextOptions
    && selectedBackendActivity
    && ['GATE_B_PENDING', 'EXPERIENCE_READY'].includes(sessionState),
  );
  const activityFlowReady = Boolean(
    sessionId
    && gateAConfirmed
    && ['UNDERSTANDING_PROPOSED', 'GATE_B_PENDING', 'EXPERIENCE_READY']
      .includes(sessionState),
  );
  const autoLoadKey = `${sessionId || ''}:${selectedChild.id}:${selectedAgeMonths}:${selectedChildLearningProfile?.profile_recorded_at || ''}`;
  useEffect(() => {
    setShowAllActivities(false);
  }, [autoLoadKey, sceneData.storyTitle]);
  const visibleActivityCards = showAllActivities
    ? activityRecommendationCards
    : activityRecommendationCards.slice(0, 3);
  const selectedOutsidePreview = selectedBackendActivity && !visibleActivityCards.some(
    (card) => card.activity_id === selectedBackendActivity.activity_id,
  );
  useEffect(() => {
    if (!activityFlowReady || hasPreparedActivity || contextOptions || workflowBusy || !sessionId) return;
    if (autoLoadKeyRef.current === autoLoadKey) return;
    autoLoadKeyRef.current = autoLoadKey;
    void prepareActivityWorkflow();
  }, [
    activityFlowReady,
    autoLoadKey,
    contextOptions,
    hasPreparedActivity,
    prepareActivityWorkflow,
    sessionId,
    workflowBusy,
  ]);

  if (!activityFlowReady) {
    return (
      <FlowPrerequisiteNotice
        title="Trước tiên, hãy cùng xem lại chủ đề từ bức vẽ"
        message="Hoạt động được gợi ý sau khi người lớn xác nhận chủ đề ở bước trước."
        action="Bắt đầu từ hồ sơ của bé"
        onAction={() => nav('profile')}
      />
    );
  }

  return (
    <ScrollView contentContainerStyle={[styles.screenContainer, { backgroundColor: '#FFFBF0' }]} showsVerticalScrollIndicator={false}>
      {/* Floating particles background decoration */}
      <FloatingParticles count={5} style={{ top: 80, height: 60 }} />

      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Cùng khám phá ngoài đời thật! 🌍</Text>
        <Text style={styles.headingSubtitle}>
          Dựa trên câu chuyện của con, đây là hoạt động thú vị chúng mình gợi ý:
        </Text>
      </View>

      <View style={styles.topicSummaryCard}>
        <Ionicons name="sparkles" size={24} color="#7C3AED" />
        <View style={{ flex: 1 }}>
          <Text style={styles.topicSummaryLabel}>Từ bức tranh và lời kể</Text>
          <Text style={styles.topicSummaryText}>{sceneData.storyTitle}</Text>
        </View>
      </View>

      {!contextOptions ? (
        <View style={styles.emptyActivityCard}>
          {workflowError ? <Ionicons name="alert-circle" size={34} color="#D97706" /> : <ActivityIndicator size="large" color="#2563EB" />}
          <Text style={styles.featuredActivityTitle}>{workflowError ? 'Chưa tải được hoạt động' : 'Đang tìm hoạt động phù hợp…'}</Text>
          <Text style={styles.featuredActivitySub}>
            {workflowError || 'Mình đang tìm toàn bộ hoạt động đã duyệt, đúng chủ đề và độ tuổi; sở thích của bé giúp sắp xếp danh sách.'}
          </Text>
          {workflowError && <>
            <Kid3DButton
              title="Thử lại"
              color="blue"
              size="sm"
              style={{ marginTop: 12 }}
              disabled={!!workflowBusy}
              onPress={() => void prepareActivityWorkflow()}
            />
            <TouchableOpacity accessibilityRole="button" onPress={() => nav('profile')} style={{ padding: 12 }}>
              <Text style={{ color: '#2563EB', fontWeight: '700' }}>Quay lại hồ sơ ban đầu</Text>
            </TouchableOpacity>
          </>}
        </View>
      ) : activityRecommendationCards.length === 0 ? (
        <View style={styles.emptyActivityCard}>
          <Text style={styles.emptyActivityEmoji}>🌱</Text>
          <Text style={styles.featuredActivityTitle}>Chưa có hoạt động để chọn</Text>
          <Text style={styles.featuredActivitySub}>
            {emptyActivityMessage}
          </Text>
          <Kid3DButton title="Kiểm tra chủ đề khác" color="blue" size="sm" style={{ marginTop: 12 }} onPress={goBack} />
        </View>
      ) : (
        <View style={styles.activityChoiceList}>
          <Text style={styles.headingSubtitle}>{contextOptions.total_count} hoạt động phù hợp chủ đề và độ tuổi</Text>
        {activityRankingStatus === 'PENDING' && (
          <Text style={styles.activityChoiceReason}>AI đang chọn 3 gợi ý; bạn có thể chọn hoạt động ngay.</Text>
        )}
        {activityRankingStatus === 'COMPLETE' && (
          <Text style={styles.activityChoiceReason}>AI đã làm nổi bật 3 gợi ý. Danh sách đầy đủ vẫn được giữ nguyên.</Text>
        )}
        {activityRankingStatus === 'UNAVAILABLE' && (
          <Text style={styles.activityChoiceReason}>AI chưa xếp hạng được; danh sách đầy đủ vẫn dùng được.</Text>
        )}
          {visibleActivityCards.map((card) => {
            const selected = selectedBackendActivity?.activity_id === card.activity_id;
          const aiRank = rankedActivityIds.indexOf(card.activity_id);
            return (
              <TouchableOpacity
                key={card.activity_id}
                accessibilityRole="radio"
                accessibilityState={{ selected }}
                accessibilityLabel={`Ưu tiên ${card.priority}: ${card.title_vi}`}
                onPress={() => selectBackendActivity(card.activity_id)}
                style={[styles.activityChoiceCard, selected && styles.activityChoiceCardSelected]}
              >
                <View style={styles.activityPriorityBadge}>
                  <Text style={styles.activityPriorityText}>{aiRank >= 0 ? `AI ${aiRank + 1}` : card.priority}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.activityChoiceTitle}>{card.title_vi}</Text>
                  <Text style={styles.activityChoiceSummary}>{card.summary_vi}</Text>
                  <Text style={styles.activityChoiceReason}>{card.match_reason_vi}</Text>
                  <View style={styles.activityChoiceMeta}>
                    <Text style={styles.activityMetaPill}>⏱ {card.duration_minutes} phút</Text>
                    <Text style={styles.activityMetaPill}>👤 {card.supervision_label_vi}</Text>
                  </View>
                </View>
                <Ionicons
                  name={selected ? 'checkmark-circle' : 'ellipse-outline'}
                  size={25}
                  color={selected ? '#2563EB' : '#94A3B8'}
                />
              </TouchableOpacity>
            );
          })}
          {!showAllActivities && activityRecommendationCards.length > 3 && (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="Xem thêm hoạt động phù hợp"
              onPress={() => setShowAllActivities(true)}
              style={{ padding: 14, alignItems: 'center' }}
            >
              <Text style={{ color: '#2563EB', fontWeight: '700' }}>
                Xem thêm ({activityRecommendationCards.length - 3} hoạt động)
              </Text>
            </TouchableOpacity>
          )}
          {selectedOutsidePreview && (
            <Text style={styles.activityChoiceReason}>Đang chọn: {selectedBackendActivity.title_vi}</Text>
          )}
          <Kid3DButton
            title={hasPreparedActivity ? 'Xem hướng dẫn' : workflowBusy ? 'Đang chuẩn bị...' : 'Chọn hoạt động này'}
            color="green"
            size="md"
            disabled={!!workflowBusy || !selectedBackendActivity}
            onPress={async () => {
              if (await prepareActivityWorkflow()) nav('experience_review');
            }}
          />
        </View>
      )}
      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginTop: 10 }}>{workflowNotice}</Text>}
    </ScrollView>
  );
};


// ==========================================
// 6. ADULT EXPERIENCE REVIEW / GATE B
// ==========================================
export const ExperienceReviewScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedActivity, approveActivity, sessionState, workflowBusy } = useAppContext();
  const nav = onNavigate || navigate;
  const approveAndContinue = async () => {
    if (sessionState === 'EXPERIENCE_READY' || await approveActivity()) nav('pixi_intro');
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      <View style={styles.topHeader}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Người lớn xem lại</Text>
        <View style={{ width: 48 }} />
      </View>
      <View style={[styles.topicSummaryCard, { marginTop: 14 }]}>
        <Ionicons name="shield-checkmark" size={28} color="#2563EB" />
        <View style={{ flex: 1 }}>
          <Text style={styles.topicSummaryLabel}>Hoạt động đã chọn</Text>
          <Text style={styles.topicSummaryText}>{selectedActivity.title}</Text>
          <Text style={styles.activityChoiceSummary}>{selectedActivity.subtitle}</Text>
        </View>
      </View>
      <View style={styles.activityHeroCard}>
        <View style={{ flex: 1 }}>
          <Text style={styles.activityHeroTitle}>Trước khi bắt đầu</Text>
          <Text style={styles.activityHeroSub}>Kiểm tra thời gian, vật liệu và cách đồng hành cùng con.</Text>
          <View style={styles.tagsRow}>
            <Text style={styles.activityMetaPill}>⏱ {selectedActivity.durationMinutes} phút</Text>
            <Text style={styles.activityMetaPill}>👤 {selectedActivity.ageGroup}</Text>
            <Text style={styles.activityMetaPill}>🧺 {selectedActivity.materials.length} vật liệu</Text>
          </View>
        </View>
      </View>
      <View style={styles.adviceBox}>
        <Text style={styles.adviceTitle}>Dành cho người lớn</Text>
        <Text style={styles.adviceText}>Lần xác nhận này khóa đúng hoạt động và mục tiêu. Hoạt động ngoài trời sẽ bắt đầu sau phần tranh chuyển động và màn video giới thiệu.</Text>
      </View>
      <View style={styles.actionBottom}>
        <Kid3DButton
          title={workflowBusy ? 'Đang chuẩn bị tranh chuyển động...' : sessionState === 'EXPERIENCE_READY' ? 'Xem tranh chuyển động' : 'Xác nhận & xem tranh'}
          color="green"
          size="lg"
          disabled={!!workflowBusy}
          onPress={() => void approveAndContinue()}
        />
      </View>
      <Modal
        visible={workflowBusy === 'Duyệt Gate B'}
        transparent
        animationType="fade"
        statusBarTranslucent
        onRequestClose={() => undefined}
      >
        <View style={styles.rigPreparationBackdrop}>
          <View style={styles.rigPreparationCard}>
            <ActivityIndicator size="large" color="#16A34A" />
            <Text accessibilityRole="header" style={styles.rigPreparationTitle}>Đang mở sân khấu Pixi</Text>
            <Text style={styles.rigPreparationText} accessibilityLiveRegion="polite">
              Hoạt động đã được xác nhận. Mình đang chuẩn bị ảnh và chuyển động trước khi mở.
            </Text>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

function formatPlaybackTime(value: number): string {
  const seconds = Math.max(0, Math.round(value));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}

// ==========================================
// 7. LANDSCAPE PIXI STORY INTRO
// ==========================================
export const PixiIntroScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedDrawing,
    sceneData,
    rendererLaunch,
    pixiIntroStoryboard,
    prepareRendererIntro,
    workflowBusy,
    workflowError,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const [rendererInstanceId, setRendererInstanceId] = useState(() => Crypto.randomUUID());
  const rendererWebViewRef = useRef<WebView>(null);
  const rendererPendingCommand = useRef<string | null>(null);
  const rendererPreparationAttempted = useRef(false);
  const controlSequence = useRef(1);
  const [rendererAttempt, setRendererAttempt] = useState(0);
  const [rendererFailed, setRendererFailed] = useState(false);
  const [rendererPreparationFailed, setRendererPreparationFailed] = useState(false);
  const [rendererHandshakeReceived, setRendererHandshakeReceived] = useState(false);
  const [rendererCommandAccepted, setRendererCommandAccepted] = useState(false);
  const [rendererHeartbeatAt, setRendererHeartbeatAt] = useState(() => Date.now());
  const [rendererStatus, setRendererStatus] = useState('Đang chuẩn bị bức vẽ…');
  const [discoveredLabel, setDiscoveredLabel] = useState<string | null>(null);
  const [chromeVisible, setChromeVisible] = useState(true);
  const chromeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const progressTrackWidth = useRef(1);
  const [playback, setPlayback] = useState({
    position: 0,
    duration: 0,
    state: 'READY',
    interactionPhase: 'INTRO_LOADING',
  });
  const rendererPageUrl = rendererLaunch
    ? `${API_BASE_URL}/renderer/mobile.html?rendererInstanceId=${encodeURIComponent(rendererInstanceId)}&rendererAttempt=${rendererAttempt}`
    : null;
  const rendererSource = useMemo(() => rendererPageUrl ? { uri: rendererPageUrl } : undefined, [rendererPageUrl]);
  const rendererOrigins = useMemo(() => [API_BASE_URL], []);

  const beats = Array.isArray(pixiIntroStoryboard?.beats)
    ? pixiIntroStoryboard.beats.map(rendererObject)
    : [];
  const activeBeat = beats.find((beat) => (
    playback.position >= Number(beat.start_seconds || 0)
    && playback.position < Number(beat.end_seconds || Number.MAX_SAFE_INTEGER)
  ));
  const caption = rendererText(
    activeBeat?.caption_vi,
    playback.interactionPhase === 'DISCOVERY_READY' || playback.interactionPhase === 'DISCOVERY_FOCUSED'
      ? 'Bức vẽ của con đã chuyển động và sẵn sàng bước tiếp.'
      : sceneData.storyTitle,
  );
  const canContinue = rendererFailed
    || playback.interactionPhase === 'DISCOVERY_READY'
    || playback.interactionPhase === 'DISCOVERY_FOCUSED'
    || playback.interactionPhase === 'FALLBACK';

  const clearChromeTimer = () => {
    if (chromeTimer.current !== null) {
      clearTimeout(chromeTimer.current);
      chromeTimer.current = null;
    }
  };

  const armChromeAutoHide = () => {
    clearChromeTimer();
    if (playback.interactionPhase === 'INTRO_LOADING' || playback.state !== 'PLAYING') return;
    chromeTimer.current = setTimeout(() => setChromeVisible(false), 3000);
  };

  const showChrome = () => {
    setChromeVisible(true);
    armChromeAutoHide();
  };

  const toggleChrome = () => {
    if (chromeVisible) {
      clearChromeTimer();
      setChromeVisible(false);
    } else {
      showChrome();
    }
  };

  const restoreSystemUi = async () => {
    await NavigationBar.setVisibilityAsync('visible').catch(() => undefined);
    await NavigationBar.setPositionAsync('relative').catch(() => undefined);
    await NavigationBar.setBackgroundColorAsync('#FFFFFF').catch(() => undefined);
    await ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.PORTRAIT_UP).catch(() => undefined);
  };

  useEffect(() => {
    let mounted = true;
    void (async () => {
      await ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.LANDSCAPE);
      await NavigationBar.setPositionAsync('absolute');
      await NavigationBar.setBackgroundColorAsync('#00000000');
      await NavigationBar.setBehaviorAsync('overlay-swipe');
      await NavigationBar.setVisibilityAsync('hidden');
    })().catch(() => {
      if (mounted) setRendererStatus('Màn hình chưa mở toàn cảnh; câu chuyện vẫn có thể tiếp tục.');
    });
    return () => {
      mounted = false;
      clearChromeTimer();
      void restoreSystemUi();
    };
  }, []);

  useEffect(() => {
    if (rendererLaunch || workflowBusy || rendererPreparationAttempted.current) return;
    if (workflowError) {
      rendererPreparationAttempted.current = true;
      setRendererPreparationFailed(true);
      setRendererStatus(workflowError);
      return;
    }
    rendererPreparationAttempted.current = true;
    void prepareRendererIntro().then((succeeded) => {
      if (!succeeded) {
        setRendererPreparationFailed(true);
        setRendererStatus('Chưa thể mở câu chuyện. Hãy thử lại khi kết nối đã sẵn sàng.');
      }
    });
  }, [rendererLaunch, workflowBusy, workflowError, prepareRendererIntro]);

  useEffect(() => {
    const deadline = rendererWatchdogDeadline({
      pageActive: Boolean(rendererPageUrl),
      failed: rendererFailed,
      handshakeReceived: rendererHandshakeReceived,
      commandAccepted: rendererCommandAccepted,
      durationSeconds: playback.duration,
      state: playback.state,
      lastProgressAt: rendererHeartbeatAt,
    });
    if (deadline === null) return;
    const timeout = setTimeout(() => {
      setRendererFailed(true);
      setRendererStatus(deadline.stage === 'HANDSHAKE'
        ? 'Pixi chưa phản hồi. Hãy kiểm tra kết nối rồi thử lại; ảnh gốc vẫn an toàn.'
        : deadline.stage === 'PREPARATION'
          ? 'Pixi chưa nạp xong ảnh và mask. Hãy thử mở lại; ảnh gốc vẫn an toàn.'
          : deadline.stage === 'STARTUP'
            ? 'Pixi đã nạp nhưng chưa bắt đầu chuyển động. Hãy thử mở lại; ảnh gốc vẫn an toàn.'
            : 'Chuyển động Pixi bị ngắt. Hãy thử mở lại; ảnh gốc vẫn an toàn.');
    }, deadline.remainingMs);
    return () => clearTimeout(timeout);
  }, [rendererPageUrl, rendererFailed, playback.duration, playback.state, rendererHandshakeReceived, rendererCommandAccepted, rendererHeartbeatAt, rendererAttempt]);

  useEffect(() => {
    if (playback.state !== 'PLAYING') {
      clearChromeTimer();
      setChromeVisible(true);
      return;
    }
    if (playback.interactionPhase !== 'INTRO_LOADING' && chromeVisible) armChromeAutoHide();
  }, [playback.interactionPhase, playback.state]);

  const postControl = (action: 'PLAY' | 'PAUSE' | 'REPLAY' | 'SEEK_RELATIVE_SECONDS' | 'SEEK_TO_SECONDS', seconds?: number) => {
    if (!rendererWebViewRef.current) return;
    const parsed = RendererControlCommandSchema.safeParse({
      protocolVersion: ART_RENDERER_PROTOCOL_VERSION,
      rendererInstanceId,
      sequence: controlSequence.current++,
      type: 'PLAYBACK_CONTROL',
      action,
      ...(seconds === undefined ? {} : { seconds }),
    });
    if (parsed.success) {
      try {
        rendererWebViewRef.current.injectJavaScript(createNativeBridgeInjection(JSON.stringify(parsed.data)));
      } catch (error) {
        console.warn('[pixi-bridge] playback control injection rejected', rendererBridgeFailureCode(error));
        setRendererStatus('Pixi chưa nhận được điều khiển. Hãy thử mở lại; ảnh gốc vẫn an toàn.');
      }
    }
  };

  const seekFromProgressEvent = (event: GestureResponderEvent) => {
    if (playback.duration <= 0) return;
    const ratio = Math.min(1, Math.max(0, event.nativeEvent.locationX / progressTrackWidth.current));
    setPlayback((current) => ({ ...current, position: ratio * current.duration }));
    postControl('SEEK_TO_SECONDS', ratio * playback.duration);
    setChromeVisible(true);
  };

  const handleRendererMessage = (event: WebViewMessageEvent) => {
    const serialized = event.nativeEvent.data;
    if (!serialized || utf8ByteLength(serialized) > MAX_RENDERER_MESSAGE_BYTES) return;
    let value: unknown;
    try { value = JSON.parse(serialized); } catch { return; }
    const bootstrap = RendererBootstrapSchema.safeParse(value);
    if (bootstrap.success && rendererLaunch) {
      if (bootstrap.data.rendererInstanceId !== rendererInstanceId) return;
      setRendererHandshakeReceived(true);
      setRendererHeartbeatAt(Date.now());
      let commandMessage = rendererPendingCommand.current;
      if (commandMessage === null) {
        commandMessage = buildRendererLoadMessage(rendererLaunch, rendererInstanceId);
        if (commandMessage === null) {
          setRendererFailed(true);
          setRendererStatus('Bức tranh chưa sẵn sàng. Ảnh gốc vẫn được giữ nguyên.');
          return;
        }
        rendererPendingCommand.current = commandMessage;
      }
      if (!rendererWebViewRef.current) return;
      // The renderer repeats its bootstrap once WebGL startup finishes. Replay
      // the exact same bounded launch then; the page gate suppresses duplicates.
      try {
        rendererWebViewRef.current.injectJavaScript(createNativeBridgeInjection(commandMessage));
        setRendererStatus('Pixi đã kết nối; đang gửi lệnh mở sân khấu…');
      } catch (error) {
        console.warn('[pixi-bridge] launch injection rejected', rendererBridgeFailureCode(error), utf8ByteLength(commandMessage));
        setRendererFailed(true);
        setRendererStatus('Không gửi được lệnh mở Pixi. Ảnh gốc vẫn an toàn; hãy thử lại.');
      }
      return;
    }
    const state = RendererPlaybackStateEnvelopeSchema.safeParse(value);
    if (state.success && state.data.rendererInstanceId === rendererInstanceId) {
      setRendererHeartbeatAt(Date.now());
      setRendererCommandAccepted(true);
      setRendererFailed(false);
      setPlayback({
        position: state.data.positionSeconds,
        duration: state.data.durationSeconds,
        state: state.data.state,
        interactionPhase: state.data.interactionPhase,
      });
      setRendererStatus(
        state.data.interactionPhase === 'DISCOVERY_READY'
          ? 'Bức vẽ chuyển động đã sẵn sàng.'
          : state.data.interactionPhase === 'FALLBACK'
            ? 'Một vài chi tiết chưa tách được; ảnh gốc vẫn an toàn.'
            : state.data.state === 'COMPLETED'
              ? 'Phần mở đầu đã sẵn sàng.'
              : state.data.state === 'PLAYING'
                ? 'Bức vẽ của con đang chuyển động.'
                : state.data.state === 'PAUSED'
                  ? 'Câu chuyện đang tạm dừng.'
                  : 'Đang mở bức vẽ của con…',
      );
      return;
    }
    const lifecycle = RendererPlaybackEventEnvelopeSchema.safeParse(value);
    if (lifecycle.success) {
      if (lifecycle.data.rendererInstanceId !== rendererInstanceId) return;
      setRendererHeartbeatAt(Date.now());
      setRendererCommandAccepted(true);
      const lifecycleEvent = lifecycle.data.event;
      switch (lifecycleEvent.type) {
        case 'DISCOVERED_ENTITY':
          setDiscoveredLabel(lifecycleEvent.labelVi);
          setRendererStatus(`Con vừa khám phá ${lifecycleEvent.labelVi}.`);
          break;
        case 'CANVAS_TAPPED':
          toggleChrome();
          break;
        case 'INTRO_COMPLETED':
          setRendererStatus('Chuyển động từ bức vẽ đã hoàn thành.');
          break;
        case 'DISCOVERY_READY':
          setRendererStatus('Bức vẽ chuyển động đã sẵn sàng.');
          setChromeVisible(true);
          armChromeAutoHide();
          break;
        case 'FALLBACK_APPLIED':
          setPlayback((current) => ({
            ...current,
            duration: lifecycleEvent.durationSeconds ?? current.duration,
            state: 'PLAYING',
            interactionPhase: 'FALLBACK',
          }));
          setRendererStatus('Một vài chi tiết chưa tách được; đang dùng chuyển động an toàn.');
          setChromeVisible(true);
          break;
        case 'PLAYBACK_FAILED':
          {
            const failureCode = normalizeRendererFailureCode(lifecycleEvent.reason);
            if (__DEV__) {
              console.warn('[pixi-bridge] renderer playback failed', failureCode);
              setRendererStatus(`Pixi lỗi: ${failureCode}. Ảnh gốc vẫn an toàn.`);
            } else {
              setRendererStatus('Chuyển động chưa mở được. Ảnh gốc vẫn an toàn.');
            }
          }
          setRendererFailed(true);
          setChromeVisible(true);
          break;
        default:
          break;
      }
    }
  };

  const retry = () => {
    if (workflowBusy) return;
    rendererPendingCommand.current = null;
    setRendererHandshakeReceived(false);
    setRendererCommandAccepted(false);
    setRendererHeartbeatAt(Date.now());
    setPlayback({ position: 0, duration: 0, state: 'READY', interactionPhase: 'INTRO_LOADING' });
    setChromeVisible(true);
    setRendererStatus('Đang làm mới quyền mở Pixi…');
    void prepareRendererIntro(true).then((succeeded) => {
      if (!succeeded) {
        setRendererFailed(true);
        setRendererStatus('Chưa làm mới được lệnh mở Pixi. Hãy thử lại; ảnh gốc vẫn an toàn.');
        return;
      }
      setRendererInstanceId(Crypto.randomUUID());
      setRendererAttempt((value) => value + 1);
      setRendererFailed(false);
      setRendererStatus('Đang kết nối sân khấu Pixi…');
    });
  };

  const retryRendererPreparation = async () => {
    if (workflowBusy) return;
    setRendererPreparationFailed(false);
    const succeeded = await prepareRendererIntro();
    if (!succeeded) {
      setRendererPreparationFailed(true);
      setRendererStatus('Chưa thể mở câu chuyện. Hãy kiểm tra kết nối rồi thử lại.');
    }
  };

  const returnToReview = async () => {
    await restoreSystemUi();
    goBack();
  };

  const continueToVideo = async () => {
    if (!canContinue) return;
    await restoreSystemUi();
    nav('video_placeholder');
  };

  return (
    <View style={styles.pixiIntroScreen}>
      <StatusBar hidden />
      <View style={styles.pixiIntroStage}>
        {rendererFailed || !rendererPageUrl ? (
          selectedDrawing ? (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <Image source={{ uri: selectedDrawing.uri }} style={styles.pixiIntroFallback} resizeMode="contain" />
              <Text style={styles.sourceFallbackText}>Bức vẽ gốc của con vẫn an toàn ở đây.</Text>
            </View>
          ) : null
        ) : (
          <WebView
            key={rendererAttempt}
            ref={rendererWebViewRef}
            source={rendererSource}
            originWhitelist={rendererOrigins}
            javaScriptEnabled
            domStorageEnabled={false}
            mixedContentMode="never"
            onMessage={handleRendererMessage}
            onLoadStart={() => setRendererStatus('Đang kết nối sân khấu Pixi…')}
            onError={() => { setRendererFailed(true); setRendererStatus('Chưa mở được chuyển động. Ảnh gốc vẫn an toàn.'); }}
            onHttpError={() => { setRendererFailed(true); setRendererStatus('Chưa tải được sân khấu. Ảnh gốc vẫn an toàn.'); }}
            style={styles.pixiIntroWebView}
          />
        )}
        {!rendererFailed && !rendererPreparationFailed && playback.duration <= 0 && (
          <View style={styles.pixiLoadingOverlay} pointerEvents="none">
            <View style={styles.pixiLoadingCard}>
              <ActivityIndicator size="large" color="#2563EB" />
              <Text accessibilityRole="header" style={styles.pixiLoadingTitle}>Đang dựng chuyển động từ tranh</Text>
              <Text style={styles.pixiLoadingText} accessibilityLiveRegion="polite">{rendererStatus}</Text>
              <Text style={styles.pixiLoadingHint}>Bước này có thể mất thêm thời gian; ảnh gốc vẫn an toàn.</Text>
            </View>
          </View>
        )}
        {chromeVisible && (
          <View style={styles.pixiChromeLayer} pointerEvents="box-none">
            <View style={styles.pixiIntroHeader} pointerEvents="box-none">
              <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={() => void returnToReview()} style={styles.pixiControlButton}>
                <Ionicons name="arrow-back" size={22} color="#FFFFFF" />
              </TouchableOpacity>
              <View style={{ flex: 1 }}>
                <Text style={styles.pixiIntroTitle}>Bức vẽ bước vào câu chuyện ✨</Text>
                <Text style={styles.pixiIntroStatus}>{rendererStatus}</Text>
              </View>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="Tiếp tục đến video"
                disabled={!canContinue}
                onPress={() => void continueToVideo()}
                style={[styles.pixiContinueButton, !canContinue && styles.pixiContinueButtonDisabled]}
              >
                <Text style={styles.pixiContinueText}>{canContinue ? 'Tiếp tục' : 'Đang mở…'}</Text>
                <Ionicons name="arrow-forward" size={18} color="#172033" />
              </TouchableOpacity>
            </View>
            <View style={styles.pixiCaptionOverlay} pointerEvents="none">
              <Text style={styles.pixiCaptionText}>{caption}</Text>
            </View>
            <View style={styles.pixiTimelineBar}>
              <TouchableOpacity disabled={playback.duration <= 0} accessibilityLabel="Tua lại 3 giây" onPress={() => { showChrome(); postControl('SEEK_RELATIVE_SECONDS', -3); }} style={styles.pixiControlButton}>
                <Ionicons name="play-back" size={22} color="#FFFFFF" />
              </TouchableOpacity>
              <TouchableOpacity
                disabled={playback.duration <= 0}
                accessibilityLabel={playback.state === 'PLAYING' ? 'Tạm dừng' : 'Phát'}
                onPress={() => { showChrome(); postControl(playback.state === 'PLAYING' ? 'PAUSE' : 'PLAY'); }}
                style={[styles.pixiControlButton, styles.pixiPlayButton]}
              >
                <Ionicons name={playback.state === 'PLAYING' ? 'pause' : 'play'} size={26} color="#172033" />
              </TouchableOpacity>
              <TouchableOpacity disabled={playback.duration <= 0} accessibilityLabel="Tua tới 3 giây" onPress={() => { showChrome(); postControl('SEEK_RELATIVE_SECONDS', 3); }} style={styles.pixiControlButton}>
                <Ionicons name="play-forward" size={22} color="#FFFFFF" />
              </TouchableOpacity>
              <View
                accessibilityRole="adjustable"
                accessibilityLabel="Thanh thời gian chuyển động"
                onLayout={(event) => { progressTrackWidth.current = Math.max(1, event.nativeEvent.layout.width); }}
                onStartShouldSetResponder={() => playback.duration > 0}
                onMoveShouldSetResponder={() => playback.duration > 0}
                onResponderGrant={seekFromProgressEvent}
                onResponderMove={seekFromProgressEvent}
                style={styles.pixiProgressTrack}
              >
                <View style={[styles.pixiProgressFill, { width: `${playback.duration > 0 ? Math.min(100, playback.position / playback.duration * 100) : 0}%` }]} />
              </View>
              <Text style={styles.pixiTimeText}>{playback.duration > 0 ? `${formatPlaybackTime(playback.position)} / ${formatPlaybackTime(playback.duration)}` : 'Đang mở…'}</Text>
              <TouchableOpacity disabled={playback.duration <= 0} accessibilityLabel="Xem lại từ đầu" onPress={() => { showChrome(); postControl('REPLAY'); }} style={styles.pixiControlButton}>
                <Ionicons name="refresh" size={22} color="#FFFFFF" />
              </TouchableOpacity>
              {rendererFailed && (
                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel="Thử mở lại"
                  accessibilityState={{disabled: Boolean(workflowBusy), busy: Boolean(workflowBusy)}}
                  disabled={Boolean(workflowBusy)}
                  onPress={retry}
                  style={styles.pixiRetryButton}
                >
                  <Text style={styles.pixiContinueText}>{workflowBusy ? 'Đang làm mới…' : 'Thử lại'}</Text>
                </TouchableOpacity>
              )}
              {rendererPreparationFailed && !rendererLaunch && (
                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel="Thử chuẩn bị câu chuyện lại"
                  accessibilityState={{ disabled: Boolean(workflowBusy), busy: Boolean(workflowBusy) }}
                  disabled={Boolean(workflowBusy)}
                  onPress={() => void retryRendererPreparation()}
                  style={styles.pixiRetryButton}
                >
                  <Text style={styles.pixiContinueText}>{workflowBusy ? 'Đang thử…' : 'Thử lại'}</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        )}
        {!chromeVisible && discoveredLabel && (
          <View style={styles.pixiDiscoveredToast} pointerEvents="none">
            <Text style={styles.pixiDiscoveredText}>✨ {discoveredLabel}</Text>
          </View>
        )}
      </View>
    </View>
  );
};

// ==========================================
// 8. LANDSCAPE STORY VIDEO
// ==========================================
export const VideoPlaceholderScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, sceneData, selectedDrawing, sessionId, completeActivityHandoff, workflowBusy } = useAppContext();
  const nav = onNavigate || navigate;
  const [job, setJob] = useState<StoryVideoJobStatus | null>(null);
  const [pollError, setPollError] = useState(false);
  const [playbackReady, setPlaybackReady] = useState(false);
  const [playbackError, setPlaybackError] = useState(false);
  const videoUrl = readyStoryVideoUrl(sessionId, job);
  useEffect(() => {
    void ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.LANDSCAPE).catch(() => undefined);
  }, []);
  useEffect(() => {
    let mounted = true;
    let polling = false;
    setJob(null);
    setPlaybackReady(false);
    setPollError(false);
    if (!sessionId) return () => { mounted = false; };
    const refresh = async () => {
      if (polling) return;
      polling = true;
      try {
        const jobs = await storyVideoApi.listStoryVideoJobs(sessionId);
        if (mounted) {
          setJob(jobs.length ? jobs[jobs.length - 1] : null);
          setPollError(false);
        }
      } catch {
        if (mounted) setPollError(true);
      } finally {
        polling = false;
      }
    };
    void refresh();
    const timer = setInterval(() => { void refresh(); }, 4_000);
    return () => { mounted = false; clearInterval(timer); };
  }, [sessionId]);
  useEffect(() => {
    setPlaybackReady(false);
    setPlaybackError(false);
  }, [videoUrl]);

  const returnToIntro = () => {
    goBack();
  };

  const continueOutside = async () => {
    if (!videoUrl || !playbackReady || playbackError || pollError) return;
    if (await completeActivityHandoff()) {
      await ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.PORTRAIT_UP).catch(() => undefined);
      nav('activity_detail');
    }
  };

  return (
    <View style={styles.videoPlaceholderScreen}>
      <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={returnToIntro} style={[styles.pixiControlButton, { position: 'absolute', top: 18, left: 18, zIndex: 3 }]}>
        <Ionicons name="arrow-back" size={22} color="#FFFFFF" />
      </TouchableOpacity>
      <View style={styles.videoPlaceholderVisual}>
        {videoUrl ? (
          <Video
            source={{ uri: videoUrl }}
            style={styles.videoPlayback}
            resizeMode={ResizeMode.CONTAIN}
            useNativeControls
            shouldPlay
            onLoad={() => setPlaybackReady(true)}
            onError={() => { setPlaybackReady(false); setPlaybackError(true); }}
          />
        ) : (
          <>
            {selectedDrawing && <Image source={{ uri: selectedDrawing.uri }} style={styles.videoPlaceholderImage} resizeMode="cover" />}
            <View style={styles.videoPlaceholderShade} />
            <View style={styles.videoPlaceholderBadge}><Ionicons name="videocam" size={24} color="#7C3AED" /><Text style={styles.videoPlaceholderBadgeText}>VIDEO ĐANG CHỜ</Text></View>
          </>
        )}
      </View>
      <View style={styles.videoPlaceholderCopy}>
        <Text style={styles.videoPlaceholderTitle}>{sceneData.storyTitle}</Text>
        <Text style={styles.videoPlaceholderText}>
          {storyVideoMessage(job, videoUrl, pollError, playbackError)}
        </Text>
        <Kid3DButton
          title={workflowBusy ? 'Đang chuẩn bị...' : 'Tiếp tục hoạt động ngoài trời'}
          color="green"
          size="md"
          disabled={!!workflowBusy || !videoUrl || !playbackReady || playbackError || pollError}
          onPress={() => void continueOutside()}
        />
      </View>
    </View>
  );
};


// ==========================================
// 9. OUTDOOR ACTIVITY DETAIL
// ==========================================
export const ActivityDetailScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    selectedActivity,
    materialsChecklist,
    toggleMaterialCheck,
    stepsChecklist,
    toggleStepCheck,
    sessionState,
    workflowNotice,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const materials = selectedActivity.materials.length > 0
    ? selectedActivity.materials
    : [
        { id: 'm1', name: 'Giấy màu', type: 'paper' as const },
        { id: 'm2', name: 'Kéo an toàn', type: 'scissors' as const },
        { id: 'm3', name: 'Bút màu', type: 'crayon' as const },
        { id: 'm4', name: 'Keo dán', type: 'glue' as const },
      ];
  const steps = selectedActivity.steps.length > 0
    ? selectedActivity.steps
    : [
        { stepNumber: 1, title: 'Chuẩn bị nguyên liệu' },
        { stepNumber: 2, title: 'Thực hiện hoạt động cùng bé' },
        { stepNumber: 3, title: 'Cùng nhau quan sát và trò chuyện' },
      ];
  const [showAdultDetails, setShowAdultDetails] = useState(false);

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header matching Image 2 Screen 6 */}
      <View style={styles.topHeader}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Hướng dẫn hoạt động</Text>
        <TouchableOpacity style={styles.backBtn}>
          <Ionicons name="heart" size={18} color={colors.coralDeep} />
        </TouchableOpacity>
      </View>

      {/* Hero Card matching Image 2 Screen 6 */}
      <View style={styles.activityHeroCard}>
        <View style={[styles.activityHeroIcon, { backgroundColor: '#EDE9FE', alignItems: 'center', justifyContent: 'center' }]}>
          <Ionicons name="sparkles-outline" size={36} color="#6D28D9" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.activityHeroTitle}>{selectedActivity.title}</Text>
          <Text style={styles.activityHeroSub}>{selectedActivity.subtitle}</Text>
          <View style={styles.tagsRow}>
            <Text style={[styles.tagPill, { backgroundColor: colors.blueSoft, color: colors.blueDeep }]}>👤 {selectedActivity.ageGroup}</Text>
            <Text style={[styles.tagPill, { backgroundColor: colors.yellowSoft, color: colors.yellowDeep }]}>⏱️ Khoảng {selectedActivity.durationMinutes} phút</Text>
            <Text style={[styles.tagPill, { backgroundColor: colors.greenSoft, color: colors.greenDeep }]}>📊 {selectedActivity.category}</Text>
          </View>
        </View>
      </View>

      {/* Preparation Materials matching Image 2 Screen 6 */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Chuẩn bị nguyên liệu</Text>
        <Text style={styles.sectionLink}>Xem gợi ý mua &gt;</Text>
      </View>

      <View style={styles.materialsGrid}>
        {materials.map((mat) => {
          const isReady = materialsChecklist[mat.id];
          return (
            <TouchableOpacity
              key={mat.id}
              activeOpacity={0.8}
              onPress={() => toggleMaterialCheck(mat.id)}
              style={[styles.materialTile, isReady && styles.materialTileChecked]}
            >
              <MaterialIconSvg type={mat.type === 'general' ? 'paper' : mat.type} size={36} />
              <Text style={styles.materialName}>{mat.name}</Text>
              <View style={[styles.materialCheckBadge, isReady && styles.materialCheckBadgeActive]}>
                <Ionicons
                  name={isReady ? 'checkmark' : 'ellipse-outline'}
                  size={12}
                  color={isReady ? colors.white : '#94A3B8'}
                />
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Execution Steps matching Image 2 Screen 6 */}
      <Text style={styles.sectionHeaderTitleStep}>Các bước thực hiện</Text>
      <View style={styles.stepsList}>
        {steps.map((step) => {
          const stepNum = step.stepNumber;
          const isDone = stepsChecklist[stepNum];
          return (
            <TouchableOpacity
              key={step.stepNumber}
              activeOpacity={0.85}
              onPress={() => toggleStepCheck(stepNum)}
              style={[styles.stepItemCard, isDone && styles.stepItemCardDone]}
            >
              <View style={[styles.stepNumberCircle, isDone && styles.stepNumberCircleDone]}>
                <Text style={[styles.stepNumberText, isDone && styles.stepNumberTextDone]}>
                  {isDone ? '✓' : stepNum}
                </Text>
              </View>
              <Text style={[styles.stepItemText, isDone && styles.stepItemTextDone]}>{step.title}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Safety & Parent Advice */}
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel={showAdultDetails ? 'Ẩn hướng dẫn dành cho người lớn' : 'Mở hướng dẫn dành cho người lớn'}
        accessibilityState={{ expanded: showAdultDetails }}
        onPress={() => setShowAdultDetails((value) => !value)}
        style={styles.adultDetailsToggle}
      >
        <View style={{ flex: 1 }}>
          <Text style={styles.adultDetailsTitle}>Dành cho người lớn</Text>
          <Text style={styles.adultDetailsSubtitle}>An toàn và cách đồng hành cùng con</Text>
        </View>
        <Ionicons name={showAdultDetails ? 'chevron-up' : 'chevron-down'} size={20} color={colors.blueDeep} />
      </TouchableOpacity>

      {showAdultDetails && (
        <>
          <View style={styles.adviceBox}>
            <Text style={styles.adviceTitle}>⚠️ Lưu ý an toàn</Text>
            {(selectedActivity.safetyNotes.length > 0 ? selectedActivity.safetyNotes : ['Nên có sự đồng hành của người lớn', 'Sử dụng dụng cụ đúng độ tuổi']).map((note) => (
              <Text key={note} style={[styles.adviceText, { marginTop: 4 }]}>• {note}</Text>
            ))}
          </View>

          <View style={[styles.adviceBox, { backgroundColor: '#FEF9C3', borderColor: '#FDE047' }]}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <View style={{ width: 22, height: 22, borderRadius: 11, overflow: 'hidden' }}>
                <MomAvatarImage size={22} />
              </View>
              <Text style={[styles.adviceTitle, { color: '#B45309' }]}>Gợi ý cho ba mẹ:</Text>
            </View>
            <Text style={[styles.adviceText, { color: '#78350F' }]}>
              {selectedActivity.parentTips || `Hãy cùng bé ${selectedChild.name} trò chuyện và quan sát trong khi làm nhé! ♡`}
            </Text>
          </View>
        </>
      )}

      {/* Outdoor activity is intentionally separate from Gate B and Pixi. */}
      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginBottom: 8 }}>{workflowNotice}</Text>}
      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Hoàn thành & ghi lại buổi khám phá"
          color="green"
          size="lg"
          icon={<Ionicons name="checkmark-done-circle" size={18} color={colors.white} />}
          disabled={sessionState !== 'HANDOFF_READY'}
          onPress={() => nav('feedback')}
        />
      </View>
    </ScrollView>
  );
};

// ==========================================
// 7. FEEDBACK LOOP (Image 3 - Step 8)
// ==========================================
export const FeedbackLoopScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    sessionId,
    sessionState,
    selectedChild,
    selectedActivity,
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
  } = useAppContext();
  const nav = onNavigate || navigate;

  if (!sessionId || !['HANDOFF_READY', 'FEEDBACK_RECORDED'].includes(sessionState)) {
    return (
      <FlowPrerequisiteNotice
        title="Phản hồi sẽ mở sau hoạt động"
        message="Hãy đi qua bước chọn và xác nhận hoạt động, rồi ghi nhận nhận xét ở đây."
        action="Bắt đầu từ hồ sơ của bé"
        onAction={() => nav('profile')}
      />
    );
  }

  if (sessionState === 'FEEDBACK_RECORDED') {
    return (
      <FlowPrerequisiteNotice
        title="Đã ghi nhận buổi khám phá"
        message="Các lựa chọn phản hồi đã được ghi trong phiên hiện tại."
        action="Về trang chủ"
        onAction={() => nav('dashboard')}
      />
    );
  }

  const fineMotorTags = FEEDBACK_OBSERVATIONS.filter((item) => item.group === 'fineMotor');
  const cognitiveTags = FEEDBACK_OBSERVATIONS.filter((item) => item.group === 'cognitive');

  const interestFeedback = [
    '',
    '🥺 Bé còn hơi bỡ ngỡ, cần mẹ khích lệ thêm',
    '🙂 Bé tham gia nhưng còn đôi chút phân tâm',
    '😊 Bé vui vẻ, tích cực trải nghiệm cùng mẹ',
    '😃 Rất hào hứng! Thích thú khám phá từng bước',
    '🤩 Siêu say mê! Hoàn toàn đắm chìm suốt buổi học!',
  ];

  const independenceFeedback = [
    '',
    '🤲 Cần ba mẹ cầm tay hướng dẫn từng chi tiết',
    '🧭 Bé làm theo từng bước mẹ nhắc nhở',
    '🤝 Bé tự làm 50%, chủ động hỏi khi cần trợ giúp',
    '🌟 Rất tự giác! Tự thao tác 80% hoạt động',
    '👑 Tự chủ 100% & sáng tạo thêm nhiều chi tiết mới!',
  ];

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 12 : 0}
    >
    <ScrollView
      contentContainerStyle={styles.screenContainer}
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
    >
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <View style={styles.workflowTagRow}>
          <Ionicons name="sparkles" size={13} color="#0369A1" />
          <Text style={styles.workflowTagText}>NHẬT KÝ QUAN SÁT MONTESSORI</Text>
        </View>
        <TouchableOpacity onPress={() => nav('dashboard')} style={styles.backBtn}>
          <Ionicons name="home-outline" size={18} color={colors.textBody} />
        </TouchableOpacity>
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Buổi học của bé {selectedChild.name} thế nào? 🌟</Text>
        <Text style={styles.headingSubtitle}>
          Ghi vài điều bạn quan sát được để xem lại sau này.
        </Text>
      </View>

      {/* Section 1: Completion Status - 3 Rich 3D Cards */}
      <View style={styles.sectionHeaderRow}>
        <Text style={styles.sectionHeadingSmall}>1. Mức độ hoàn thành hoạt động thực tế:</Text>
      </View>
      <View style={styles.feedbackOptionGrid}>
        {/* Option 1: Hoàn thành */}
        <JellyBounceView
          containerStyle={{ flex: 1 }}
          accessibilityRole="radio"
          accessibilityLabel="Đã hoàn thành hoạt động"
          accessibilityState={{ selected: completionStatus === 'completed' }}
          onPress={() => setCompletionStatus('completed')}
          style={[
            styles.feedbackOptionCard,
            completionStatus === 'completed' && styles.feedbackOptionCardActiveGreen,
          ]}
        >
          <View style={[styles.statusIconCircle, { backgroundColor: completionStatus === 'completed' ? '#DCFCE7' : '#F1F5F9' }]}>
            <Ionicons name="checkmark-circle" size={24} color={completionStatus === 'completed' ? '#16A34A' : '#94A3B8'} />
          </View>
          <Text style={[styles.feedbackOptionTitle, completionStatus === 'completed' && { color: '#15803D' }]}>
            Đã hoàn thành
          </Text>
          <View style={[styles.statusBadge, { backgroundColor: completionStatus === 'completed' ? '#DCFCE7' : '#F1F5F9' }]}>
            <Text style={[styles.statusBadgeText, { color: completionStatus === 'completed' ? '#16A34A' : '#64748B' }]}>
              {completionStatus === 'completed' ? '✓ Đạt mục tiêu' : 'Hoàn tất'}
            </Text>
          </View>
          <Text style={styles.feedbackOptionSub}>Đã xong {selectedActivity.title.toLowerCase()}</Text>
        </JellyBounceView>

        {/* Option 2: Một phần */}
        <JellyBounceView
          containerStyle={{ flex: 1 }}
          accessibilityRole="radio"
          accessibilityLabel="Hoàn thành một phần"
          accessibilityState={{ selected: completionStatus === 'partial' }}
          onPress={() => setCompletionStatus('partial')}
          style={[
            styles.feedbackOptionCard,
            completionStatus === 'partial' && styles.feedbackOptionCardActiveYellow,
          ]}
        >
          <View style={[styles.statusIconCircle, { backgroundColor: completionStatus === 'partial' ? '#FEF3C7' : '#F1F5F9' }]}>
            <Ionicons name="time" size={24} color={completionStatus === 'partial' ? '#D97706' : '#94A3B8'} />
          </View>
          <Text style={[styles.feedbackOptionTitle, completionStatus === 'partial' && { color: '#B45309' }]}>
            Một phần
          </Text>
          <View style={[styles.statusBadge, { backgroundColor: completionStatus === 'partial' ? '#FEF3C7' : '#F1F5F9' }]}>
            <Text style={[styles.statusBadgeText, { color: completionStatus === 'partial' ? '#D97706' : '#64748B' }]}>
              {completionStatus === 'partial' ? '⏳ Cần thêm giờ' : 'Đang làm'}
            </Text>
          </View>
          <Text style={styles.feedbackOptionSub}>Đang làm rất say mê</Text>
        </JellyBounceView>

        {/* Option 3: Chưa làm */}
        <JellyBounceView
          containerStyle={{ flex: 1 }}
          accessibilityRole="radio"
          accessibilityLabel="Chưa thực hiện hoạt động"
          accessibilityState={{ selected: completionStatus === 'not_attempted' }}
          onPress={() => setCompletionStatus('not_attempted')}
          style={[
            styles.feedbackOptionCard,
            completionStatus === 'not_attempted' && styles.feedbackOptionCardActiveBlue,
          ]}
        >
          <View style={[styles.statusIconCircle, { backgroundColor: completionStatus === 'not_attempted' ? '#E0F2FE' : '#F1F5F9' }]}>
            <Ionicons name="calendar-outline" size={24} color={completionStatus === 'not_attempted' ? '#0284C7' : '#94A3B8'} />
          </View>
          <Text style={[styles.feedbackOptionTitle, completionStatus === 'not_attempted' && { color: '#0369A1' }]}>
            Chưa làm
          </Text>
          <View style={[styles.statusBadge, { backgroundColor: completionStatus === 'not_attempted' ? '#E0F2FE' : '#F1F5F9' }]}>
            <Text style={[styles.statusBadgeText, { color: completionStatus === 'not_attempted' ? '#0284C7' : '#64748B' }]}>
              {completionStatus === 'not_attempted' ? '📅 Dịp sau' : 'Lưu lại'}
            </Text>
          </View>
          <Text style={styles.feedbackOptionSub}>Sẽ làm vào dịp sau</Text>
        </JellyBounceView>
      </View>

      {/* Section 2: Montessori Observation Record */}
      <View style={[styles.sectionHeaderRow, { marginTop: 14 }]}>
        <Text style={styles.sectionHeadingSmall}>2. Thang đo quan sát Montessori:</Text>
      </View>

      {/* Card A: Mức độ hứng thú */}
      <View style={[styles.metricCard, { borderColor: '#FDE68A', backgroundColor: '#FFFDF5' }]}>
        <View style={styles.metricHeaderRow}>
          <View style={[styles.metricIconCircle, { backgroundColor: '#FEF3C7' }]}>
            <Text style={{ fontSize: 18 }}>💛</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.metricTitle}>Mức độ hứng thú</Text>
            <Text style={styles.metricSubtitle}>Sự hào hứng và say mê của con</Text>
          </View>
          <View style={styles.scorePercentPillYellow}>
            <Text style={styles.scorePercentTextYellow}>{interestScore * 20}%</Text>
          </View>
        </View>

        {/* 5 Big Gold Stars with dynamic touch */}
        <View style={styles.starsSelectRow}>
          {[1, 2, 3, 4, 5].map((star) => (
            <JellyBounceView
              key={star}
              accessibilityRole="radio"
              accessibilityLabel={`Mức độ hứng thú ${star} trên 5`}
              accessibilityState={{ selected: interestScore === star }}
              onPress={() => setInterestScore(star)}
              style={[
                styles.starTouchArea,
                star <= interestScore && styles.starTouchAreaActiveYellow,
              ]}
            >
              <Ionicons
                name={star <= interestScore ? 'star' : 'star-outline'}
                size={30}
                color={star <= interestScore ? '#F59E0B' : '#CBD5E1'}
              />
            </JellyBounceView>
          ))}
        </View>

        {/* Dynamic Pedagogy Feedback Pill */}
        <View style={[styles.metricFeedbackPill, { backgroundColor: '#FEF3C7' }]}>
          <Text style={[styles.metricFeedbackText, { color: '#92400E' }]}>
            {interestFeedback[interestScore]}
          </Text>
        </View>
      </View>

      {/* Card B: Tính tự lập */}
      <View style={[styles.metricCard, { borderColor: '#BAE6FD', backgroundColor: '#F8FAFC', marginTop: 12 }]}>
        <View style={styles.metricHeaderRow}>
          <View style={[styles.metricIconCircle, { backgroundColor: '#E0F2FE' }]}>
            <Text style={{ fontSize: 18 }}>🌱</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.metricTitle}>Tính tự lập</Text>
            <Text style={styles.metricSubtitle}>Khả năng tự giác và chủ động của con</Text>
          </View>
          <View style={styles.scorePercentPillBlue}>
            <Text style={styles.scorePercentTextBlue}>Cấp {independenceScore}/5</Text>
          </View>
        </View>

        {/* 5 Big Cyan Sparkles with dynamic touch */}
        <View style={styles.starsSelectRow}>
          {[1, 2, 3, 4, 5].map((spark) => (
            <JellyBounceView
              key={spark}
              accessibilityRole="radio"
              accessibilityLabel={`Mức độ tự lập ${spark} trên 5`}
              accessibilityState={{ selected: independenceScore === spark }}
              onPress={() => setIndependenceScore(spark)}
              style={[
                styles.starTouchArea,
                spark <= independenceScore && styles.starTouchAreaActiveBlue,
              ]}
            >
              <Ionicons
                name={spark <= independenceScore ? 'sparkles' : 'sparkles-outline'}
                size={28}
                color={spark <= independenceScore ? '#0284C7' : '#CBD5E1'}
              />
            </JellyBounceView>
          ))}
        </View>

        {/* Dynamic Pedagogy Feedback Pill */}
        <View style={[styles.metricFeedbackPill, { backgroundColor: '#E0F2FE' }]}>
          <Text style={[styles.metricFeedbackText, { color: '#0369A1' }]}>
            {independenceFeedback[independenceScore]}
          </Text>
        </View>
      </View>

      {/* Section 3: Categorized Sticker Chips */}
      <View style={[styles.sectionHeaderRow, { marginTop: 14 }]}>
        <Text style={styles.sectionHeadingSmall}>3. Ghi chú quan sát nhanh của con:</Text>
      </View>

      {/* Group A: fine-motor observations */}
      <Text style={styles.tagCategoryLabel}>✂️ Kỹ năng vận động tinh:</Text>
      <View style={styles.quickTagsGrid}>
        {fineMotorTags.map((item) => {
          const isSel = selectedObservationTags.includes(item.code);
          return (
            <JellyBounceView
              key={item.code}
              accessibilityLabel={item.label}
              accessibilityState={{ selected: isSel }}
              onPress={() => toggleObservationTag(item.code)}
              style={[styles.quickTagChipNew, isSel && styles.quickTagChipNewActive]}
            >
              <Text style={{ fontSize: 13, marginRight: 4 }}>{item.emoji}</Text>
              <Text style={[styles.quickTagChipTextNew, isSel && styles.quickTagChipTextNewActive]}>
                {item.label}
              </Text>
              {isSel && (
                <Ionicons name="checkmark-circle" size={15} color="#1D4ED8" style={{ marginLeft: 5 }} />
              )}
            </JellyBounceView>
          );
        })}
      </View>

      {/* Group B: Cognitive */}
      <Text style={[styles.tagCategoryLabel, { marginTop: 6 }]}>💡 Tư duy, Ngôn ngữ &amp; Sáng tạo:</Text>
      <View style={styles.quickTagsGrid}>
        {cognitiveTags.map((item) => {
          const isSel = selectedObservationTags.includes(item.code);
          return (
            <JellyBounceView
              key={item.code}
              accessibilityLabel={item.label}
              accessibilityState={{ selected: isSel }}
              onPress={() => toggleObservationTag(item.code)}
              style={[styles.quickTagChipNew, isSel && styles.quickTagChipNewActive]}
            >
              <Text style={{ fontSize: 13, marginRight: 4 }}>{item.emoji}</Text>
              <Text style={[styles.quickTagChipTextNew, isSel && styles.quickTagChipTextNewActive]}>
                {item.label}
              </Text>
              {isSel && (
                <Ionicons name="checkmark-circle" size={15} color="#1D4ED8" style={{ marginLeft: 5 }} />
              )}
            </JellyBounceView>
          );
        })}
      </View>

      {/* Free-text notes are deliberately excluded by FeedbackV1. */}
      <View style={styles.parentNoteCardNew}>
        <View style={styles.parentNoteHeader}>
          <Text style={{ fontSize: 16 }}>🔒</Text>
          <Text style={styles.parentNoteTitle}>Ghi chú riêng</Text>
        </View>
        <Text style={styles.parentNoteInputNew}>
          Bản thử nghiệm chỉ lưu các lựa chọn quan sát ở trên; ghi chú tự do chưa được lưu.
        </Text>
      </View>

      {/* Section 5: History Update Card */}
      <View style={styles.historyUpdateCardNew}>
        <View style={styles.historyIconCircleNew}>
          <Ionicons name="sync" size={20} color="#15803D" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.historyTitleNew}>Ghi nhận trong phiên này</Text>
          <Text style={styles.historySubNew}>
            Nhận xét của bé {selectedChild.name} được giữ trong phiên hiện tại. Tính năng lưu vào hồ sơ sẽ có sau khi đăng nhập được bổ sung.
          </Text>
        </View>
      </View>

      {/* Save & Return to Dashboard CTA */}
      <View style={[styles.actionBottom, { marginTop: 14 }]}>
        <PulseGlow>
          <Kid3DButton
            title={isSavingFeedback ? 'Đang ghi nhận...' : 'Ghi nhận & Về trang chủ 🏠'}
            color="blue"
            size="lg"
            disabled={isSavingFeedback || interestScore === 0 || independenceScore === 0}
            onPress={saveFeedback}
          />
        </PulseGlow>
      </View>
    </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  evidenceChipWrap: {
    flexDirection: 'row', flexWrap: 'wrap', gap: 8, padding: 12,
    backgroundColor: '#F8FAFC', borderRadius: 16, marginBottom: 10,
  },
  evidenceChip: { backgroundColor: '#E0F2FE', borderRadius: 14, paddingHorizontal: 10, paddingVertical: 6 },
  evidenceChipText: { color: '#075985', fontSize: 12, fontWeight: '700' },
  pixiIntroScreen: { flex: 1, backgroundColor: '#10162A' },
  pixiChromeLayer: { ...StyleSheet.absoluteFillObject, zIndex: 3, justifyContent: 'space-between', padding: 12 },
  pixiIntroHeader: {
    flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 58,
    paddingHorizontal: 8, paddingVertical: 6, borderRadius: 30,
    backgroundColor: 'rgba(15,23,42,0.82)',
  },
  pixiIntroTitle: { color: '#FFFFFF', fontSize: 20, fontWeight: '900' },
  pixiIntroStatus: { color: '#BFDBFE', fontSize: 12, marginTop: 2 },
  pixiContinueButton: {
    minHeight: 46, paddingHorizontal: 16, borderRadius: 23, backgroundColor: '#FDE68A',
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
  },
  pixiContinueButtonDisabled: { opacity: 0.62 },
  pixiContinueText: { color: '#172033', fontSize: 14, fontWeight: '900' },
  pixiIntroStage: {
    flex: 1, overflow: 'hidden', backgroundColor: '#FFFEF9', position: 'relative',
  },
  pixiIntroWebView: { flex: 1, backgroundColor: '#FFFEF9' },
  pixiLoadingOverlay: {
    ...StyleSheet.absoluteFillObject, zIndex: 2, alignItems: 'center', justifyContent: 'center',
    padding: 24, backgroundColor: 'rgba(248,250,252,0.36)',
  },
  pixiLoadingCard: {
    width: '100%', maxWidth: 380, alignItems: 'center', gap: 12, padding: 24,
    borderRadius: 24, backgroundColor: 'rgba(255,255,255,0.96)',
    borderWidth: 1, borderColor: '#DBEAFE', ...shadows.card,
  },
  pixiLoadingTitle: { color: '#172033', fontSize: 18, fontWeight: '900', textAlign: 'center' },
  pixiLoadingText: { color: '#1D4ED8', fontSize: 14, fontWeight: '800', textAlign: 'center' },
  pixiLoadingHint: { color: '#64748B', fontSize: 12, textAlign: 'center' },
  rigPreparationBackdrop: {
    flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24,
    backgroundColor: 'rgba(15,23,42,0.56)',
  },
  rigPreparationCard: {
    width: '100%', maxWidth: 380, alignItems: 'center', gap: 12, padding: 26,
    borderRadius: 24, backgroundColor: '#FFFFFF', ...shadows.card,
  },
  rigPreparationTitle: { color: '#172033', fontSize: 18, fontWeight: '900', textAlign: 'center' },
  rigPreparationText: { color: '#475569', fontSize: 14, lineHeight: 21, textAlign: 'center' },
  pixiIntroFallback: { width: '100%', flex: 1, backgroundColor: '#FFFEF9' },
  pixiDiscoverPanel: {
    position: 'absolute', left: 16, top: 14, right: 16, alignItems: 'center',
  },
  pixiDiscoverHint: {
    color: '#172033', backgroundColor: 'rgba(255,255,255,0.92)', paddingHorizontal: 12,
    paddingVertical: 6, borderRadius: 14, fontSize: 12, fontWeight: '800',
  },
  pixiDiscoverChips: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 8, marginTop: 8 },
  pixiDiscoverChip: {
    backgroundColor: 'rgba(219,234,254,0.95)', borderColor: '#93C5FD', borderWidth: 1,
    borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6,
  },
  pixiDiscoverChipActive: { backgroundColor: '#FDE68A', borderColor: '#F59E0B' },
  pixiDiscoverChipText: { color: '#1E3A8A', fontSize: 12, fontWeight: '800' },
  pixiDiscoveredText: {
    marginTop: 6, color: '#047857', backgroundColor: 'rgba(236,253,245,0.95)',
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, fontSize: 12, fontWeight: '800',
  },
  pixiDiscoveredToast: { position: 'absolute', top: 18, left: 0, right: 0, alignItems: 'center', zIndex: 2 },
  pixiCaptionOverlay: {
    position: 'absolute', left: 20, right: 20, bottom: 16, alignItems: 'center',
  },
  pixiCaptionText: {
    color: '#FFFFFF', backgroundColor: 'rgba(15,23,42,0.82)', paddingHorizontal: 18,
    paddingVertical: 10, borderRadius: 16, fontSize: 17, fontWeight: '800', textAlign: 'center',
  },
  pixiTimelineBar: {
    minHeight: 62, flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingHorizontal: 10, paddingVertical: 7, borderRadius: 31,
    backgroundColor: 'rgba(15,23,42,0.88)',
  },
  pixiControlButton: {
    width: 48, height: 48, borderRadius: 24, backgroundColor: 'rgba(30,41,59,0.94)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.28)', alignItems: 'center', justifyContent: 'center',
  },
  pixiPlayButton: { backgroundColor: '#FDE68A' },
  pixiRetryButton: {
    minHeight: 44, paddingHorizontal: 14, borderRadius: 22, backgroundColor: '#FDE68A',
    alignItems: 'center', justifyContent: 'center',
  },
  pixiProgressTrack: { flex: 1, height: 12, borderRadius: 6, backgroundColor: 'rgba(255,255,255,0.3)', overflow: 'hidden' },
  pixiProgressFill: { height: '100%', borderRadius: 4, backgroundColor: '#60A5FA' },
  pixiTimeText: { minWidth: 78, color: '#FFFFFF', fontSize: 12, fontWeight: '700', textAlign: 'center' },
  videoPlaceholderScreen: { flex: 1, flexDirection: 'row', backgroundColor: '#111827', padding: 18, gap: 20 },
  videoPlaceholderVisual: { flex: 1.35, borderRadius: 22, overflow: 'hidden', backgroundColor: '#1E293B' },
  videoPlaceholderImage: { width: '100%', height: '100%', opacity: 0.72 },
  videoPlayback: { width: '100%', height: '100%' },
  videoPlaceholderShade: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(15,23,42,0.28)' },
  videoPlaceholderBadge: {
    position: 'absolute', alignSelf: 'center', top: '42%', backgroundColor: 'rgba(255,255,255,0.94)',
    borderRadius: 18, paddingHorizontal: 18, paddingVertical: 12, flexDirection: 'row', gap: 8, alignItems: 'center',
  },
  videoPlaceholderBadgeText: { color: '#5B21B6', fontWeight: '900', letterSpacing: 0.8 },
  videoPlaceholderCopy: { flex: 1, justifyContent: 'center', gap: 16, paddingRight: 18 },
  videoPlaceholderTitle: { color: '#FFFFFF', fontSize: 26, lineHeight: 33, fontWeight: '900' },
  videoPlaceholderText: { color: '#CBD5E1', fontSize: 16, lineHeight: 24 },
  localModalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  localModalCard: {
    width: '100%',
    maxWidth: 350,
    borderRadius: 24,
    backgroundColor: '#FFFFFF',
    padding: 24,
    alignItems: 'center',
  },
  localModalEmoji: { fontSize: 42 },
  localModalTitle: { fontSize: 19, fontWeight: '900', color: '#172033', marginTop: 8 },
  localModalText: { fontSize: 15, lineHeight: 22, color: '#475569', textAlign: 'center', marginTop: 8 },
  localModalActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 18,
  },
  localModalButton: {
    minHeight: 48,
    minWidth: 126,
    borderRadius: 24,
    backgroundColor: '#2563EB',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  localModalButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '800' },
  localModalSecondaryButton: {
    backgroundColor: '#EFF6FF',
    borderWidth: 1,
    borderColor: '#93C5FD',
  },
  localModalSecondaryText: { color: '#1D4ED8', fontSize: 15, fontWeight: '800' },
  topicSummaryCard: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
    backgroundColor: '#F5F3FF',
    borderRadius: 18,
    padding: 16,
    marginBottom: 14,
  },
  topicSummaryLabel: { fontSize: 12, fontWeight: '700', color: '#7C3AED', marginBottom: 3 },
  topicSummaryText: { fontSize: 17, lineHeight: 23, fontWeight: '900', color: '#312E81' },
  emptyActivityCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 22,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#FDE68A',
  },
  emptyActivityEmoji: { fontSize: 44, marginBottom: 8 },
  activityChoiceList: { gap: 12, paddingBottom: 12 },
  activityChoiceCard: {
    minHeight: 132,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: '#DBEAFE',
    padding: 14,
  },
  activityChoiceCardSelected: { borderColor: '#2563EB', backgroundColor: '#EFF6FF' },
  activityPriorityBadge: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FDE68A',
  },
  activityPriorityText: { fontSize: 14, fontWeight: '900', color: '#92400E' },
  activityChoiceTitle: { fontSize: 16, fontWeight: '900', color: '#172033', lineHeight: 21 },
  activityChoiceSummary: { fontSize: 13, color: '#475569', lineHeight: 18, marginTop: 4 },
  activityChoiceReason: { fontSize: 12, color: '#047857', lineHeight: 17, marginTop: 5 },
  activityChoiceMeta: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  activityMetaPill: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
    backgroundColor: '#F1F5F9',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  screenContainer: {
    padding: 16,
    paddingBottom: 28,
    width: '100%',
    maxWidth: '100%',
    overflow: 'hidden',
  },
  topHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  screenHeaderTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.textHeading,
  },
  backBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.lineSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headingBox: {
    alignItems: 'center',
    marginVertical: 4,
    textAlign: 'center',
  },
  headingTitle: {
    fontSize: 17,
    fontWeight: '900',
    color: colors.textHeading,
    textAlign: 'center',
    marginBottom: 4,
  },
  headingSubtitle: {
    fontSize: 11,
    color: colors.textSoft,
    textAlign: 'center',
    lineHeight: 16,
    paddingHorizontal: 12,
  },
  robotCenterBox: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 10,
  },
  progressContainer: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.line,
    marginVertical: 8,
    ...shadows.card,
  },
  progressLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  progressLabel: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
  },
  progressPercent: {
    fontSize: 12,
    fontWeight: '900',
    color: colors.blueDeep,
  },
  progressBarTrack: {
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.lineSoft,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 5,
    backgroundColor: colors.blue,
  },
  checklistCard: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 12,
    marginVertical: 8,
    gap: 10,
    ...shadows.card,
  },
  checkItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  checkCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkTextDone: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textHeading,
  },
  checkTextPending: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textLight,
  },
  ribbonBanner: {
    backgroundColor: '#FFF1F2',
    borderColor: '#FECDD3',
    borderWidth: 1,
    borderRadius: radius.md,
    paddingVertical: 10,
    paddingHorizontal: 14,
    alignItems: 'center',
    marginVertical: 12,
  },
  ribbonText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#E11D48',
  },
  sectionHeadingSmall: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 8,
    marginBottom: 6,
  },
  aiSuccessBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#F3E8FF',
    borderColor: '#E9D5FF',
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  aiSuccessBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#7E22CE',
    letterSpacing: 0.3,
  },
  artworkSpotlightCard: {
    backgroundColor: '#FFFDF7',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 20,
    padding: 10,
    marginVertical: 8,
    ...shadows.card,
  },
  tapeHeader: {
    alignItems: 'center',
    marginBottom: 6,
    marginTop: -18,
  },
  washiTape: {
    width: 90,
    height: 18,
    backgroundColor: '#FEF08A',
    borderRadius: 4,
    opacity: 0.9,
    borderWidth: 1,
    borderColor: '#FDE047',
    borderStyle: 'dashed',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  artworkInnerWrap: {
    position: 'relative',
    height: 140,
    borderRadius: 14,
    overflow: 'hidden',
    backgroundColor: '#FEF9C3',
    borderWidth: 1,
    borderColor: '#FEF08A',
  },
  artworkThumbImg: {
    width: '100%',
    height: '100%',
    resizeMode: 'contain',
  },
  subjectHotspot: {
    position: 'absolute',
    minWidth: 34,
    minHeight: 28,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'rgba(37, 99, 235, 0.72)',
    backgroundColor: 'rgba(219, 234, 254, 0.16)',
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 2,
  },
  subjectHotspotSelected: {
    borderColor: '#059669',
    borderWidth: 3,
    backgroundColor: 'rgba(167, 243, 208, 0.24)',
  },
  subjectHotspotLabel: {
    maxWidth: 120,
    color: '#1E3A8A',
    backgroundColor: 'rgba(255,255,255,0.94)',
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
    fontSize: 9,
    fontWeight: '900',
  },
  subjectPickerFallback: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 44,
    backgroundColor: 'rgba(239, 246, 255, 0.62)',
  },
  subjectPickerFallbackText: {
    marginTop: 4,
    color: '#1D4ED8',
    fontSize: 11,
    fontWeight: '800',
    textAlign: 'center',
  },
  subjectPickerHint: {
    marginBottom: 8,
    color: '#64748B',
    fontSize: 12,
    lineHeight: 17,
  },
  selectedSubjectCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
    padding: 12,
    marginBottom: 8,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#A7F3D0',
    backgroundColor: '#ECFDF5',
  },
  selectedSubjectTitle: { color: '#047857', fontSize: 12, fontWeight: '900' },
  selectedSubjectSentence: { color: '#065F46', fontSize: 13, lineHeight: 18, marginTop: 3 },
  aiScanPin: {
    position: 'absolute',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: 'rgba(226, 232, 240, 0.9)',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 4,
    elevation: 3,
  },
  aiScanDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 4,
  },
  aiScanPinText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#1E293B',
  },
  artworkCaptionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 8,
  },
  artworkCaptionText: {
    fontSize: 10.5,
    fontWeight: '700',
    color: '#2563EB',
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 10,
    marginBottom: 6,
  },
  countBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  countBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#475569',
  },
  entitiesGridNew: {
    gap: 10,
    marginVertical: 4,
  },
  entityRowNew: {
    flexDirection: 'row',
    gap: 10,
  },
  entityCardNew: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 8,
    borderRadius: 18,
    borderWidth: 1.5,
    position: 'relative',
    ...shadows.card,
  },
  cardTagCorner: {
    position: 'absolute',
    top: 8,
    right: 8,
    zIndex: 2,
  },
  cardTagText: {
    fontSize: 9,
    fontWeight: '800',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  entityOrbNew: {
    width: 58,
    height: 58,
    borderRadius: 29,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  entityNameNew: {
    fontSize: 13,
    fontWeight: '800',
    textAlign: 'center',
  },
  entityDetailText: {
    fontSize: 10,
    color: colors.textSoft,
    textAlign: 'center',
    marginTop: 1,
  },
  entityBadgeNew: {
    marginTop: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  entityBadgeTextNew: {
    fontSize: 10,
    fontWeight: '700',
  },
  moreEntitiesPill: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#F8FAFC',
    borderColor: '#E2E8F0',
    borderWidth: 1,
    borderStyle: 'dashed',
    borderRadius: 14,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  moreEntitiesPillText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
  },
  audioDurationPill: {
    backgroundColor: '#E0F2FE',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  audioDurationText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0369A1',
  },
  voiceAudioCard: {
    backgroundColor: '#F0F9FF',
    borderColor: '#BAE6FD',
    borderWidth: 1.5,
    borderRadius: 18,
    padding: 14,
    marginVertical: 4,
    ...shadows.card,
  },
  voiceAudioHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  voicePlayBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#0284C7',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#0284C7',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.35,
    shadowRadius: 5,
    elevation: 4,
  },
  voiceAudioTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#0369A1',
  },
  voiceAudioDuration: {
    fontSize: 10,
    color: '#0284C7',
    marginTop: 1,
  },
  equalizerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2.5,
    height: 34,
    paddingHorizontal: 4,
  },
  equalizerBar: {
    width: 3,
    borderRadius: 1.5,
  },
  voiceQuoteDivider: {
    height: 1,
    backgroundColor: '#BAE6FD',
    marginVertical: 10,
    opacity: 0.6,
  },
  speechQuoteBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 4,
  },
  speechQuoteIcon: {
    fontSize: 22,
    color: '#0284C7',
    fontWeight: '900',
    lineHeight: 20,
  },
  speechQuoteIconEnd: {
    fontSize: 22,
    color: '#0284C7',
    fontWeight: '900',
    lineHeight: 20,
    alignSelf: 'flex-end',
  },
  voiceQuoteText: {
    flex: 1,
    fontSize: 11.5,
    color: '#075985',
    lineHeight: 18,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  complimentCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF1F2',
    borderColor: '#FFE4E6',
    borderWidth: 1,
    borderRadius: radius.md,
    padding: 12,
    gap: 10,
    marginTop: 10,
  },
  complimentAvatar: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#FFE4E6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  complimentTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.coralDeep,
  },
  complimentSub: {
    fontSize: 10,
    color: '#9F1239',
    marginTop: 2,
  },
  gateCorrectionInput: {
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: colors.textBody,
    backgroundColor: '#FFFFFF',
    marginTop: 12,
  },
  gateSubjectOriginHint: {
    color: '#64748B',
    fontSize: 10,
    lineHeight: 15,
    marginHorizontal: 4,
    marginTop: 5,
  },
  gateSubjectRecoveryHint: {
    color: '#334155',
    backgroundColor: '#EFF6FF',
    borderColor: '#BFDBFE',
    borderWidth: 1,
    borderRadius: 12,
    fontSize: 12,
    lineHeight: 18,
    padding: 11,
    marginTop: 10,
  },
  gateSubjectRequeryButton: {
    minHeight: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderColor: '#93C5FD',
    borderWidth: 1,
    borderRadius: 12,
    backgroundColor: '#F8FBFF',
    paddingHorizontal: 12,
    marginTop: 8,
  },
  gateSubjectRequeryButtonDisabled: {
    borderColor: '#D1D5DB',
    backgroundColor: '#F8FAFC',
  },
  gateSubjectRequeryText: {
    color: '#1D4ED8',
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
  meadowContainer: {
    borderRadius: radius.md,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.line,
    marginVertical: 8,
    position: 'relative',
    ...shadows.card,
  },
  durationBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    zIndex: 10,
  },
  durationText: {
    color: colors.white,
    fontSize: 10,
    fontWeight: '700',
  },
  storySourceImage: {
    width: '100%',
    height: 190,
    backgroundColor: '#FEF9C3',
  },
  sceneThumbnailsRow: {
    flexDirection: 'row',
    gap: 8,
    marginVertical: 10,
    width: '100%',
  },
  sceneThumbnail: {
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 4,
    borderRadius: radius.md,
    borderWidth: 1.5,
    ...shadows.card,
  },
  sceneIconCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  sceneNumberText: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textHeading,
    textAlign: 'center',
  },
  sceneActionText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.textSoft,
    textAlign: 'center',
    marginTop: 1,
  },
  storyQuoteCaption: {
    fontSize: 11,
    fontStyle: 'italic',
    color: colors.textSoft,
    textAlign: 'center',
    marginVertical: 6,
  },
  videoPlayerBox: {
    width: '100%',
    position: 'relative',
    backgroundColor: '#000',
  },
  inVideoQuoteBox: {
    position: 'absolute',
    top: 12,
    left: 12,
    right: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderRadius: radius.sm,
    paddingHorizontal: 10,
    paddingVertical: 6,
    zIndex: 5,
  },
  inVideoQuoteText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.textHeading,
    textAlign: 'center',
  },
  videoControlsOverlay: {
    position: 'absolute',
    bottom: 8,
    left: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    gap: 8,
  },
  timecodeText: {
    fontSize: 10,
    color: colors.white,
    fontWeight: '700',
  },
  scrubberTrack: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 2,
  },
  scrubberFill: {
    height: '100%',
    backgroundColor: colors.blue,
    borderRadius: 2,
  },
  videoActionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  videoActionCol: {
    alignItems: 'center',
    gap: 4,
  },
  videoCircleBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.lineSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  videoActionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textBody,
  },
  ageBadgeRow: {
    alignSelf: 'center',
    backgroundColor: '#EFF6FF',
    borderColor: '#BFDBFE',
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 4,
    marginVertical: 6,
  },
  ageBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#1D4ED8',
  },
  featuredActivityCard: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 12,
    alignItems: 'center',
    marginVertical: 8,
    ...shadows.card,
  },
  featuredActivityTitle: {
    fontSize: 15,
    fontWeight: '900',
    color: colors.textHeading,
    marginTop: 8,
  },
  featuredActivitySub: {
    fontSize: 11,
    color: colors.textSoft,
    textAlign: 'center',
    marginTop: 4,
    paddingHorizontal: 12,
  },
  backendSourceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#EFF6FF',
    borderWidth: 1,
    borderColor: '#BFDBFE',
    borderRadius: radius.md,
    padding: 12,
    marginTop: 8,
  },
  pixiCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: '#BFDBFE',
    padding: 12,
    marginTop: 12,
    ...shadows.card,
  },
  pixiTitle: {
    fontSize: 13,
    fontWeight: '900',
    color: colors.blueDeep,
  },
  pixiSubtitle: {
    fontSize: 12,
    color: colors.textSoft,
    lineHeight: 15,
    marginTop: 4,
  },
  pixiViewport: {
    height: 190,
    marginTop: 10,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: '#DBEAFE',
  },
  pixiWebView: {
    flex: 1,
    backgroundColor: colors.white,
  },
  sourceFallbackWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
  },
  sourceFallbackImage: {
    width: '100%',
    flex: 1,
  },
  sourceFallbackText: {
    fontSize: 11,
    color: colors.textSoft,
    paddingVertical: 6,
  },
  pixiStatus: {
    fontSize: 12,
    color: colors.greenDeep,
    marginTop: 6,
  },
  pixiError: {
    fontSize: 10.5,
    color: '#B91C1C',
    marginTop: 6,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 12,
    marginBottom: 6,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '900',
    color: colors.textHeading,
  },
  sectionLink: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.blueDeep,
  },
  otherActivitiesGrid: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 6,
  },
  otherActivityCard: {
    flex: 1,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: 10,
    alignItems: 'center',
    ...shadows.card,
  },
  otherActTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 6,
    textAlign: 'center',
  },
  otherActAge: {
    fontSize: 10,
    color: colors.textSoft,
    marginTop: 2,
  },
  activityHeroCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: 12,
    gap: 10,
    marginVertical: 6,
  },
  activityHeroIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.line,
  },
  activityHeroTitle: {
    fontSize: 15,
    fontWeight: '900',
    color: colors.textHeading,
  },
  activityHeroSub: {
    fontSize: 10,
    color: colors.textSoft,
    marginTop: 2,
  },
  tagsRow: {
    flexDirection: 'row',
    gap: 4,
    marginTop: 6,
  },
  tagPill: {
    fontSize: 9,
    fontWeight: '700',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  materialsGrid: {
    flexDirection: 'row',
    gap: 8,
    marginVertical: 6,
  },
  materialTile: {
    flex: 1,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    ...shadows.card,
  },
  materialTileChecked: {
    borderColor: colors.greenDeep,
    backgroundColor: '#F0FDF4',
  },
  materialName: {
    fontSize: 10,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 4,
  },
  materialCheckBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  materialCheckBadgeActive: {
    backgroundColor: colors.greenDeep,
  },
  sectionHeaderTitleStep: {
    fontSize: 13,
    fontWeight: '900',
    color: colors.textHeading,
    marginTop: 10,
    marginBottom: 6,
  },
  stepsList: {
    gap: 6,
    marginVertical: 4,
  },
  stepItemCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.sm,
    padding: 10,
    gap: 10,
  },
  stepItemCardDone: {
    backgroundColor: '#F0FDF4',
    borderColor: '#BBF7D0',
  },
  stepNumberCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.blueSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumberCircleDone: {
    backgroundColor: colors.greenDeep,
  },
  stepNumberText: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.blueDeep,
  },
  stepNumberTextDone: {
    color: colors.white,
  },
  stepItemText: {
    flex: 1,
    fontSize: 11,
    fontWeight: '700',
    color: colors.textBody,
  },
  stepItemTextDone: {
    color: '#15803D',
    textDecorationLine: 'line-through',
  },
  adviceBox: {
    backgroundColor: '#EFF6FF',
    borderColor: '#BFDBFE',
    borderWidth: 1,
    borderRadius: radius.md,
    padding: 10,
    marginTop: 8,
  },
  adultDetailsToggle: {
    minHeight: 56,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: radius.md,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginTop: 10,
  },
  adultDetailsTitle: {
    fontSize: 14,
    fontWeight: '900',
    color: colors.textHeading,
  },
  adultDetailsSubtitle: {
    fontSize: 11,
    color: colors.textSoft,
    marginTop: 2,
  },
  adviceTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.blueDeep,
  },
  adviceText: {
    fontSize: 12,
    lineHeight: 17,
    color: colors.textBody,
    marginTop: 2,
  },
  workflowTagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#E0F2FE',
    alignSelf: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginVertical: 6,
  },
  workflowTagText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0369A1',
    letterSpacing: 0.3,
  },
  feedbackOptionGrid: {
    flexDirection: 'row',
    gap: 8,
    marginVertical: 6,
  },
  feedbackOptionCard: {
    flex: 1,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: 8,
    alignItems: 'center',
    ...shadows.card,
  },
  feedbackOptionCardActiveGreen: {
    borderColor: '#16A34A',
    backgroundColor: '#F0FDF4',
    borderWidth: 2,
  },
  feedbackOptionCardActiveYellow: {
    borderColor: '#D97706',
    backgroundColor: '#FEFCE8',
    borderWidth: 2,
  },
  feedbackOptionCardActiveGray: {
    borderColor: '#64748B',
    backgroundColor: '#F8FAFC',
    borderWidth: 2,
  },
  feedbackOptionCardActiveBlue: {
    borderColor: '#0284C7',
    backgroundColor: '#F0F9FF',
    borderWidth: 2,
  },
  statusIconCircle: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  feedbackOptionTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textHeading,
    textAlign: 'center',
  },
  feedbackOptionSub: {
    fontSize: 9.5,
    color: colors.textSoft,
    textAlign: 'center',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    marginTop: 4,
    marginBottom: 2,
  },
  statusBadgeText: {
    fontSize: 9.5,
    fontWeight: '800',
  },
  metricCard: {
    borderRadius: radius.md,
    borderWidth: 1.5,
    padding: 14,
    ...shadows.card,
  },
  metricHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  scorePercentPillYellow: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  scorePercentTextYellow: {
    fontSize: 11,
    fontWeight: '900',
    color: '#B45309',
  },
  scorePercentPillBlue: {
    backgroundColor: '#E0F2FE',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  scorePercentTextBlue: {
    fontSize: 11,
    fontWeight: '900',
    color: '#0369A1',
  },
  metricIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.textHeading,
  },
  metricSubtitle: {
    fontSize: 11,
    color: colors.textSoft,
    marginTop: 2,
  },
  starsSelectRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 8,
    marginVertical: 4,
  },
  starTouchArea: {
    padding: 6,
    borderRadius: 14,
  },
  starTouchAreaActiveYellow: {
    backgroundColor: '#FEF3C7',
  },
  starTouchAreaActiveBlue: {
    backgroundColor: '#E0F2FE',
  },
  metricFeedbackPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginTop: 6,
    alignItems: 'center',
  },
  metricFeedbackText: {
    fontSize: 11,
    fontWeight: '700',
    textAlign: 'center',
  },
  tagCategoryLabel: {
    fontSize: 11,
    fontWeight: '800',
    color: '#475569',
    marginTop: 6,
    marginBottom: 4,
  },
  quickTagsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginVertical: 4,
  },
  quickTagChipNew: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  quickTagChipNewActive: {
    backgroundColor: '#EFF6FF',
    borderColor: '#3B82F6',
  },
  quickTagChipTextNew: {
    fontSize: 11.5,
    fontWeight: '600',
    color: colors.textBody,
  },
  quickTagChipTextNewActive: {
    color: '#1D4ED8',
    fontWeight: '800',
  },
  parentNoteCardNew: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: radius.md,
    padding: 12,
    marginTop: 12,
    ...shadows.card,
  },
  parentNoteHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  parentNoteTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
  },
  parentNoteInputNew: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: radius.sm,
    padding: 10,
    fontSize: 11.5,
    color: colors.textBody,
    lineHeight: 18,
    minHeight: 64,
    textAlignVertical: 'top',
  },
  historyUpdateCardNew: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    borderWidth: 1.5,
    borderColor: '#86EFAC',
    borderRadius: radius.md,
    padding: 12,
    gap: 10,
    marginTop: 14,
    ...shadows.card,
  },
  historyIconCircleNew: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  historyTitleNew: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#15803D',
  },
  historySubNew: {
    fontSize: 10.5,
    color: '#166534',
    marginTop: 2,
    lineHeight: 15,
  },
  gateAlertBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F0FDF4',
    borderColor: '#86EFAC',
    borderWidth: 1,
    borderRadius: radius.md,
    padding: 10,
    gap: 8,
    marginVertical: 8,
  },
  gateAlertTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: '#15803D',
  },
  gateAlertDesc: {
    fontSize: 10,
    color: '#166534',
    marginTop: 2,
    lineHeight: 14,
  },
  gateAlertBoxBlue: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#EFF6FF',
    borderColor: '#93C5FD',
    borderWidth: 1,
    borderRadius: radius.md,
    padding: 10,
    gap: 8,
    marginVertical: 8,
  },
  gateAlertBlueTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: '#1D4ED8',
  },
  gateAlertBlueDesc: {
    fontSize: 10,
    color: '#1E40AF',
    marginTop: 2,
    lineHeight: 14,
  },
  learningObjectiveBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#EFF6FF',
    borderColor: '#BFDBFE',
    borderWidth: 1,
    borderRadius: radius.md,
    padding: 10,
    gap: 8,
  },
  learningObjectiveTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: '#1D4ED8',
  },
  learningObjectiveText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#1E40AF',
    marginTop: 2,
  },
  bridgeBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FEF3C7',
    borderColor: '#FDE68A',
    borderWidth: 1,
    borderRadius: radius.md,
    padding: 10,
    gap: 8,
    marginVertical: 6,
  },
  bridgeTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: '#B45309',
  },
  bridgeText: {
    fontSize: 10,
    color: '#92400E',
    marginTop: 2,
    lineHeight: 14,
  },
  actionBottom: {
    marginTop: 12,
    marginBottom: 6,
  },
});
