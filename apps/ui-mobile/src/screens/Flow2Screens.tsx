import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import * as Crypto from 'expo-crypto';
import WebView, { type WebViewMessageEvent } from 'react-native-webview';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { Kid3DButton } from '../components/Kid3DButton';
import { RiveMascot } from '../components/RiveMascot';
import {
  CatDrawingArtwork,
  CraftButterflyArtwork,
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
import {
  ART_RENDERER_PROTOCOL_VERSION,
  MAX_RENDERER_MESSAGE_BYTES,
  RendererBootstrapSchema,
  RendererLoadCommandSchema,
  RendererPlaybackEventEnvelopeSchema,
} from '../../../../packages/art-renderer/src/protocol';
import { API_BASE_URL } from '../demo/api';

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

function rendererObject(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null ? value as Record<string, unknown> : {};
}

function rendererText(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function utf8ByteLength(value: string): number {
  return encodeURIComponent(value).replace(/%[0-9A-F]{2}/g, 'U').length;
}

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
    workflowError,
    workflowNotice,
    narrationMode,
  } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Xử lý câu chuyện</Text>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Đang hiểu bức tranh...</Text>
        <Text style={styles.headingSubtitle}>
          Backend sẽ xử lý ảnh tổng hợp của bé {selectedChild.name}
          {narrationMode === 'audio' ? ' và chạy faster-whisper cho lời kể' : narrationMode === 'text' ? ' cùng nội dung lời kể đã nhập' : ''}. Video chưa nằm trong phạm vi demo.
        </Text>
      </View>

      {/* Robot Mascot with SparkleRing rotating around it — magical loading feel! */}
      <View style={[styles.robotCenterBox, { alignItems: 'center', justifyContent: 'center' }]}>
        <SparkleRing size={180} />
        <Image
          source={require('../../assets/images/robot_ai.png')}
          style={{ width: 150, height: 150, resizeMode: 'contain' }}
        />
      </View>

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressLabelRow}>
          <Text style={styles.progressLabel}>Tiến độ xử lý AI</Text>
          <Text style={styles.progressPercent}>{aiProgress}%</Text>
        </View>
        <View style={styles.progressBarTrack}>
          <View style={[styles.progressBarFill, { width: `${aiProgress}%` }]} />
        </View>
      </View>

      {/* 4 Pipeline Checklist Items */}
      <View style={styles.checklistCard}>
        <View style={styles.checkItem}>
          <View style={[styles.checkCircle, { backgroundColor: colors.greenDeep }]}>
            <Ionicons name="checkmark" size={12} color={colors.white} />
          </View>
          <Text style={styles.checkTextDone}>Kiểm tra admission ảnh</Text>
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
            Gọi ASR (nếu có audio) rồi gửi ảnh + context tới Vision...
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
            Giữ ảnh gốc cho preview/Pixi
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
          {workflowBusy === 'Phân tích ảnh' ? 'Đang gửi một request tới Lightning...' : 'Chạm để phân tích ảnh thật trên backend ✨'}
        </Text>
      </TouchableOpacity>
      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginTop: 10 }}>{workflowNotice}</Text>}
      {workflowError && <Text style={{ color: '#B91C1C', textAlign: 'center', marginTop: 10 }}>{workflowError}</Text>}
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
    selectedClaimIds,
    primaryClaimId,
    toggleAnalysisClaim,
    setPrimaryClaim,
    correction,
    setCorrection,
    confirmGateA,
    workflowBusy,
    workflowError,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <View style={styles.aiSuccessBadge}>
          <Ionicons name="sparkles" size={13} color="#7C3AED" />
          <Text style={styles.aiSuccessBadgeText}>AI PHÂN TÍCH THÔNG MINH</Text>
        </View>
        <TouchableOpacity onPress={() => nav('dashboard')} style={styles.backBtn}>
          <Ionicons name="home-outline" size={18} color={colors.textBody} />
        </TouchableOpacity>
      </View>

      {/* Main Heading */}
      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Đã hiểu câu chuyện của con! 🎨</Text>
        <Text style={styles.headingSubtitle}>
          Sketch2Life đã nhận diện trọn vẹn thế giới tưởng tượng từ bức vẽ và giọng kể của bé {selectedChild.name}:
        </Text>
      </View>

      {/* 1. ARTWORK SPOTLIGHT CARD — Mini Polaroid with Floating AI Scan Pins */}
      <View style={styles.artworkSpotlightCard}>
        <View style={styles.tapeHeader}>
          <View style={styles.washiTape} />
        </View>
        <View style={styles.artworkInnerWrap}>
          <Image
            source={selectedDrawing ? { uri: selectedDrawing.uri } : require('../../assets/images/photo_cat_paper.png')}
            style={styles.artworkThumbImg}
          />
          {/* 3D Animated Laser Scanning Beam */}
          <MagicScanBeam containerHeight={140} />

          {/* Floating AI Scan Badges */}
          <View style={[styles.aiScanPin, { top: 12, left: 14 }]}>
            <View style={[styles.aiScanDot, { backgroundColor: '#A855F7' }]} />
            <Text style={styles.aiScanPinText}>{sceneData.entities[0]?.icon || '✨'} {sceneData.entities[0]?.name || 'Đang đọc ảnh'}</Text>
          </View>
          <View style={[styles.aiScanPin, { bottom: 14, right: 14 }]}>
            <View style={[styles.aiScanDot, { backgroundColor: '#F43F5E' }]} />
            <Text style={styles.aiScanPinText}>{sceneData.entities[1]?.icon || '✨'} {sceneData.entities[1]?.name || 'Chi tiết ảnh'}</Text>
          </View>
          <View style={[styles.aiScanPin, { top: 14, right: 14 }]}>
            <View style={[styles.aiScanDot, { backgroundColor: '#F59E0B' }]} />
            <Text style={styles.aiScanPinText}>{sceneData.entities[2]?.icon || '✨'} {sceneData.entities[2]?.name || 'Bối cảnh ảnh'}</Text>
          </View>
        </View>
        <View style={styles.artworkCaptionRow}>
          <Ionicons name="sparkles" size={13} color="#2563EB" />
          <Text style={styles.artworkCaptionText}>
            Ảnh gốc từ phiên backend • {sceneData.entities.length} thực thể/nhãn được đề xuất
          </Text>
        </View>
      </View>

      {/* 2. DETECTED ENTITIES SECTION — 2x2 Tactile 3D Animated Cards */}
      <View style={styles.sectionHeaderRow}>
        <Text style={styles.sectionHeadingSmall}>Các nhân vật & chi tiết nhận diện được</Text>
        <View style={styles.countBadge}>
          <Text style={styles.countBadgeText}>{sceneData.entities.length} Thực thể</Text>
        </View>
      </View>

      <View style={styles.entitiesGridNew}>
        {analysisClaims.map((claim) => (
          <TouchableOpacity
            key={claim.observation_id}
            activeOpacity={0.86}
            onPress={() => toggleAnalysisClaim(claim.observation_id)}
            style={[styles.entityCardNew, {
              backgroundColor: selectedClaimIds.includes(claim.observation_id) ? '#F0FDF4' : '#FFFFFF',
              borderColor: primaryClaimId === claim.observation_id ? '#2563EB' : '#CBD5E1',
              borderWidth: primaryClaimId === claim.observation_id ? 2 : 1,
            }]}
          >
            <Text style={styles.entityNameNew}>{claim.label.value}</Text>
            <Text style={styles.entityDetailText}>{claim.kind} · {Math.round(claim.confidence * 100)}% confidence</Text>
            <Text style={styles.entityBadgeTextNew}>
              {primaryClaimId === claim.observation_id ? 'Chủ đề chính' : selectedClaimIds.includes(claim.observation_id) ? 'Đã chọn' : 'Bỏ chọn'}
            </Text>
            <TouchableOpacity onPress={() => setPrimaryClaim(claim.observation_id)}>
              <Text style={{ color: '#2563EB', fontWeight: '800', marginTop: 8 }}>Chọn làm chủ đề</Text>
            </TouchableOpacity>
          </TouchableOpacity>
        ))}
      </View>

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
            Bé {selectedChild.name} diễn đạt rất tự nhiên và tràn đầy cảm xúc! Bức vẽ đã sẵn sàng biến thành phim hoạt hình! ✨
          </Text>
        </View>
      </View>

      <TextInput
        value={correction}
        onChangeText={setCorrection}
        placeholder="Nếu cần, sửa nhãn chủ đề cho AI (không bắt buộc)"
        placeholderTextColor="#94A3B8"
        style={styles.gateCorrectionInput}
        maxLength={200}
      />

      {/* 5. PRIMARY 3D CTA BUTTON */}
      <View style={[styles.actionBottom, { marginTop: 14 }]}>
        <PulseGlow>
          <Kid3DButton
            title={workflowBusy === 'Xác nhận Gate A' ? 'Đang xác nhận...' : 'Xác nhận Gate A & tiếp tục'}
            color="blue"
            size="lg"
            disabled={!!workflowBusy || !primaryClaimId || selectedClaimIds.length === 0}
            onPress={async () => {
              if (await confirmGateA()) nav('story_preview');
            }}
          />
        </PulseGlow>
      </View>
      {workflowError && <Text style={{ color: '#B91C1C', textAlign: 'center', marginTop: 10 }}>{workflowError}</Text>}
    </ScrollView>
  );
};

// ==========================================
// 3. STORY PREVIEW (Image 1 - Screen 3)
// ==========================================
export const StoryPreviewScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild, selectedDrawing } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Xem trước câu chuyện</Text>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Câu chuyện đã sẵn sàng!</Text>
        <Text style={styles.headingSubtitle}>
          Cùng xem thế giới từ bức vẽ của bé {selectedChild.name} đã trở nên sống động như thế nào nhé!
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

      {/* 3 Scene Thumbnails underneath — crisp vector illustrations with BounceIn */}
      <View style={styles.sceneThumbnailsRow}>
        <BounceInView delay={0} style={{ flex: 1 }}>
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={() => nav('activity_recommend')}
            style={[styles.sceneThumbnail, { backgroundColor: '#FAF5FF', borderColor: '#C4B5FD' }]}
          >
            <View style={[styles.sceneIconCircle, { backgroundColor: '#EDE9FE' }]}>
              <ButterflyIconSvg size={24} />
            </View>
            <Text style={styles.sceneNumberText}>Cảnh 1</Text>
            <Text numberOfLines={1} style={styles.sceneActionText}>Thức dậy</Text>
          </TouchableOpacity>
        </BounceInView>

        <BounceInView delay={100} style={{ flex: 1 }}>
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={() => nav('activity_recommend')}
            style={[styles.sceneThumbnail, { backgroundColor: '#FFFBEB', borderColor: '#FDE68A' }]}
          >
            <View style={[styles.sceneIconCircle, { backgroundColor: '#FEF3C7' }]}>
              <FlowerIconSvg size={24} />
            </View>
            <Text style={styles.sceneNumberText}>Cảnh 2</Text>
            <Text numberOfLines={1} style={styles.sceneActionText}>Bay lượn</Text>
          </TouchableOpacity>
        </BounceInView>

        <BounceInView delay={200} style={{ flex: 1 }}>
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={() => nav('activity_recommend')}
            style={[styles.sceneThumbnail, { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' }]}
          >
            <View style={[styles.sceneIconCircle, { backgroundColor: '#DCFCE7' }]}>
              <SunIconSvg size={24} />
            </View>
            <Text style={styles.sceneNumberText}>Cảnh 3</Text>
            <Text numberOfLines={1} style={styles.sceneActionText}>Hút mật</Text>
          </TouchableOpacity>
        </BounceInView>
      </View>


      <Text style={styles.storyQuoteCaption}>
        "Preview tĩnh từ ảnh gốc; video chưa nằm trong phạm vi demo. ♡"
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
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
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
          source={require('../../assets/images/video_scene_only.png')}
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
    selectedActivity,
    contextOptions,
    selectedBackendActivity,
    prepareActivityWorkflow,
    workflowBusy,
    workflowError,
    workflowNotice,
  } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <ScrollView contentContainerStyle={[styles.screenContainer, { backgroundColor: '#FFFBF0' }]} showsVerticalScrollIndicator={false}>
      {/* Floating particles background decoration */}
      <FloatingParticles count={5} style={{ top: 80, height: 60 }} />

      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
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

      {/* Age Badge */}
      <BounceInView delay={0}>
        <View style={styles.ageBadgeRow}>
          <Text style={styles.ageBadgeText}>
            ⭐ {contextOptions ? 'Backend đã lọc theo anchor + độ tuổi' : 'Chưa gọi catalog backend'}
          </Text>
        </View>
      </BounceInView>

      {/* Featured Activity Card — PulseGlow wrapper */}
      <PulseGlow>
        <View style={[styles.featuredActivityCard, { borderWidth: 2, borderColor: '#FDE68A', shadowColor: '#F59E0B', shadowOpacity: 0.3, shadowRadius: 10, elevation: 6 }]}>
          <CraftButterflyArtwork height={130} />
          <Text style={styles.featuredActivityTitle}>{contextOptions ? selectedActivity.title : 'Hoạt động từ catalog backend'}</Text>
          <Text style={styles.featuredActivitySub}>
            {contextOptions ? selectedActivity.subtitle : 'Bấm nút để backend chọn activity đúng anchor và độ tuổi, không dùng dữ liệu mock.'}
          </Text>
          <Kid3DButton
            title={workflowBusy === 'Chuẩn bị hoạt động' ? 'Đang lọc hoạt động...' : 'Tạo gợi ý thật >'}
            color="blue"
            size="sm"
            style={{ marginTop: 10 }}
            disabled={!!workflowBusy}
            onPress={async () => {
              if (await prepareActivityWorkflow()) nav('activity_detail');
            }}
          />
        </View>
      </PulseGlow>
      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginTop: 10 }}>{workflowNotice}</Text>}
      {workflowError && <Text style={{ color: '#B91C1C', textAlign: 'center', marginTop: 10 }}>{workflowError}</Text>}

      {/* Other Activities */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Nguồn lựa chọn</Text>
      </View>

      <View style={styles.backendSourceCard}>
        <Ionicons name="server-outline" size={22} color={colors.blueDeep} />
        <View style={{ flex: 1 }}>
          <Text style={styles.otherActTitle}>Không dùng activity mock để bàn giao</Text>
          <Text style={styles.otherActAge}>
            {selectedBackendActivity
              ? `Backend đã chọn ${selectedBackendActivity.activity_ref.id} v${selectedBackendActivity.activity_ref.version}.`
              : 'Activity chỉ hiện sau khi Gate A được xác nhận và backend lọc theo catalog.'}
          </Text>
        </View>
      </View>
    </ScrollView>
  );
};


// ==========================================
// 6. ACTIVITY DETAIL (Image 1 - Screen 6)
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
    approveActivity,
    completeActivityHandoff,
    rendererLaunch,
    sessionState,
    workflowBusy,
    workflowError,
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
  const rendererInstanceId = useState(() => Crypto.randomUUID())[0];
  const rendererWebViewRef = useRef<WebView>(null);
  const rendererCommandSent = useRef(false);
  const [rendererStatus, setRendererStatus] = useState<string | null>(null);
  const [rendererError, setRendererError] = useState<string | null>(null);
  const rendererPageUrl = rendererLaunch
    ? `${API_BASE_URL}/renderer/mobile.html?rendererInstanceId=${encodeURIComponent(rendererInstanceId)}`
    : null;

  const handleRendererMessage = (event: WebViewMessageEvent) => {
    const serialized = event.nativeEvent.data;
    if (!serialized || utf8ByteLength(serialized) > MAX_RENDERER_MESSAGE_BYTES) {
      setRendererError('Pixi trả message rỗng hoặc vượt giới hạn 4 KB.');
      return;
    }
    let value: unknown;
    try {
      value = JSON.parse(serialized);
    } catch {
      setRendererError('Pixi trả JSON không hợp lệ.');
      return;
    }
    const bootstrap = RendererBootstrapSchema.safeParse(value);
    if (bootstrap.success) {
      if (bootstrap.data.rendererInstanceId !== rendererInstanceId || !rendererLaunch) {
        setRendererError('Pixi instance không khớp launch hiện tại.');
        return;
      }
      if (rendererCommandSent.current) return;
      const launch = rendererObject(rendererLaunch);
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
      });
      if (!command.success) {
        setRendererError('Backend launch không qua validation Pixi protocol v1.');
        return;
      }
      const loadMessage = JSON.stringify(command.data);
      if (utf8ByteLength(loadMessage) > MAX_RENDERER_MESSAGE_BYTES || !rendererWebViewRef.current) {
        setRendererError('Pixi launch không thể gửi qua bridge.');
        return;
      }
      rendererCommandSent.current = true;
      rendererWebViewRef.current.postMessage(loadMessage);
      setRendererStatus('Đã bắt tay Pixi protocol v1; đang reveal ảnh gốc.');
      return;
    }
    const playback = RendererPlaybackEventEnvelopeSchema.safeParse(value);
    if (playback.success) {
      setRendererStatus(rendererText(rendererObject(playback.data.event).type, 'Pixi đã phát event.'));
    }
  };

  const finishActivity = async () => {
    if (sessionState === 'HANDOFF_READY') {
      nav('feedback');
      return;
    }
    if (sessionState === 'GATE_B_PENDING') {
      await approveActivity();
      return;
    }
    if (sessionState !== 'EXPERIENCE_READY') return;
    if (await completeActivityHandoff()) {
      rendererCommandSent.current = false;
      setRendererStatus('Đã bàn giao; Pixi đang sẵn sàng.');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header matching Image 2 Screen 6 */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
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
          <ButterflyIconSvg size={36} />
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

      {rendererPageUrl && sessionState === 'HANDOFF_READY' && (
        <View style={styles.pixiCard}>
          <Text style={styles.pixiTitle}>PixiJS · reveal ảnh gốc</Text>
          <Text style={styles.pixiSubtitle}>Không gọi video/generation; renderer nhận manifest có hash và đọc ảnh qua capability ngắn hạn.</Text>
          <View style={styles.pixiViewport}>
            <WebView
              ref={rendererWebViewRef}
              source={{ uri: rendererPageUrl }}
              originWhitelist={[API_BASE_URL]}
              javaScriptEnabled
              domStorageEnabled={false}
              mixedContentMode="never"
              thirdPartyCookiesEnabled={false}
              sharedCookiesEnabled={false}
              setSupportMultipleWindows={false}
              onMessage={handleRendererMessage}
              onLoadStart={() => setRendererStatus('Đang mở Pixi từ backend…')}
              onLoadEnd={() => setRendererStatus((value) => value ?? 'Pixi đã tải; chờ handshake.')}
              onError={() => setRendererError('Không mở được Pixi renderer từ backend.')}
              style={styles.pixiWebView}
            />
          </View>
          {rendererStatus && <Text style={styles.pixiStatus}>{rendererStatus}</Text>}
          {rendererError && <Text style={styles.pixiError}>{rendererError}</Text>}
        </View>
      )}

      {/* Finish Session -> Go to Step 8 Feedback Loop */}
      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginBottom: 8 }}>{workflowNotice}</Text>}
      {workflowError && <Text style={{ color: '#B91C1C', textAlign: 'center', marginBottom: 8 }}>{workflowError}</Text>}
      <View style={styles.actionBottom}>
        <Kid3DButton
          title={workflowBusy || (sessionState === 'GATE_B_PENDING' ? 'Duyệt Gate B' : sessionState === 'EXPERIENCE_READY' ? 'Bàn giao hoạt động & mở Pixi' : sessionState === 'HANDOFF_READY' ? 'Ghi feedback cho phiên này' : 'Hoàn thành hoạt động ✨')}
          color="green"
          size="lg"
          icon={<Ionicons name="checkmark-done-circle" size={18} color={colors.white} />}
          disabled={!!workflowBusy || (sessionState !== 'GATE_B_PENDING' && sessionState !== 'EXPERIENCE_READY' && sessionState !== 'HANDOFF_READY')}
          onPress={() => void finishActivity()}
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
    selectedChild,
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
  } = useAppContext();
  const nav = onNavigate || navigate;

  const fineMotorTags = [
    { label: 'Tự tay dán cánh', emoji: '✂️' },
    { label: 'Nhớ vòi bướm hút mật', emoji: '🦋' },
    { label: 'Biết bướm có 6 chân', emoji: '🐛' },
  ];

  const cognitiveTags = [
    { label: 'Hỏi nhiều về hoa', emoji: '🌸' },
    { label: 'Muốn làm thêm bướm xanh', emoji: '🎨' },
    { label: 'Nhờ mẹ hỗ trợ kéo', emoji: '🤝' },
  ];

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
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
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
          Ghi nhận ngắn giúp AI thấu hiểu sở thích và cá nhân hóa trải nghiệm tranh vẽ tiếp theo.
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
          <Text style={styles.feedbackOptionSub}>Bé làm xong chú bướm</Text>
        </JellyBounceView>

        {/* Option 2: Một phần */}
        <JellyBounceView
          containerStyle={{ flex: 1 }}
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
            <Text style={styles.metricTitle}>Mức độ hứng thú (Interest)</Text>
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
            <Text style={styles.metricTitle}>Tính tự lập (Independence)</Text>
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

      {/* Group A: Fine Motor */}
      <Text style={styles.tagCategoryLabel}>✂️ Kỹ năng vận động tinh (Fine Motor):</Text>
      <View style={styles.quickTagsGrid}>
        {fineMotorTags.map((item) => {
          const isSel = selectedObservationTags.includes(item.label);
          return (
            <JellyBounceView
              key={item.label}
              onPress={() => toggleObservationTag(item.label)}
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
          const isSel = selectedObservationTags.includes(item.label);
          return (
            <JellyBounceView
              key={item.label}
              onPress={() => toggleObservationTag(item.label)}
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

      {/* Section 4: Parent Scrapbook Note Input */}
      <View style={styles.parentNoteCardNew}>
        <View style={styles.parentNoteHeader}>
          <Text style={{ fontSize: 16 }}>💌</Text>
          <Text style={styles.parentNoteTitle}>Sổ tay cảm xúc &amp; Lời nhắn gửi từ Ba Mẹ:</Text>
        </View>
        <TextInput
          value={parentNotes}
          onChangeText={setParentNotes}
          multiline
          placeholder="Ghi lại khoảnh khắc đáng nhớ hoặc câu nói ngộ nghĩnh của bé hôm nay..."
          placeholderTextColor="#94A3B8"
          style={styles.parentNoteInputNew}
        />
      </View>

      {/* Section 5: History Update Card */}
      <View style={styles.historyUpdateCardNew}>
        <View style={styles.historyIconCircleNew}>
          <Ionicons name="sync" size={20} color="#15803D" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.historyTitleNew}>Đồng bộ tiến độ học tập</Text>
          <Text style={styles.historySubNew}>
            Dữ liệu quan sát đã được lưu vào hồ sơ bé {selectedChild.name} ({selectedChild.age} tuổi) để tối ưu hoạt động tiếp theo.
          </Text>
        </View>
      </View>

      {/* Save & Return to Dashboard CTA */}
      <View style={[styles.actionBottom, { marginTop: 14 }]}>
        <PulseGlow>
          <Kid3DButton
            title={isSavingFeedback ? 'Đang lưu nhật ký...' : 'Lưu nhật ký & Về trang chủ 🏠'}
            color="blue"
            size="lg"
            onPress={saveFeedback}
          />
        </PulseGlow>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
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
    width: 32,
    height: 32,
    borderRadius: 16,
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
    fontSize: 10.5,
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
  pixiStatus: {
    fontSize: 10.5,
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
  adviceTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.blueDeep,
  },
  adviceText: {
    fontSize: 10,
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
