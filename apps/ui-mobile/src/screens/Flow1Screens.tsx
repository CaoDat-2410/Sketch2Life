import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { Kid3DButton } from '../components/Kid3DButton';
import { RiveMascot } from '../components/RiveMascot';
import {
  LogoSketch2Life,
  CatDrawingArtwork,
  RainbowFishArtwork,
  StoryRobotArtwork,
  SplashHeroIllustration,
  OnboardingHeroIllustration,
  VoiceGirlMicIllustration,
  MomAvatarImage,
  SunIconSvg,
  ChildAvatarImage,
  FloatingParticles,
  BounceInView,
  PulseGlow,
  CuteStarIconSvg,
} from '../components/ArtworkCards';

import type { ScreenId } from '../types';
import { useAppContext } from '../context/AppContext';

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

// ==========================================
// 1. SPLASH SCREEN (Image 2 - Screen 1)
// ==========================================
export const SplashScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;

  useEffect(() => {
    const timer = setTimeout(() => {
      nav('onboarding');
    }, 3000);
    return () => clearTimeout(timer);
  }, [nav]);

  return (
    <TouchableOpacity
      activeOpacity={0.96}
      onPress={() => nav('onboarding')}
      style={{
        flex: 1,
        backgroundColor: '#FFFFFF',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 36,
        paddingHorizontal: 20,
      }}
    >
      {/* Top Brand Logo & Tagline — 100% Crisp Native Vector */}
      <View style={{ alignItems: 'center', marginTop: 16 }}>
        <LogoSketch2Life size="lg" showTagline={false} />
        <Text style={{ fontSize: 13, fontWeight: '700', color: '#1E40AF', marginTop: 6, textAlign: 'center' }}>
          Mỗi nét vẽ đều có một câu chuyện đang chờ được kể...
        </Text>
      </View>

      {/* Center Hero: Crisp HD Girl + Dino Artwork with Floating Animation */}
      <View style={{ width: '100%', flex: 1, justifyContent: 'center', alignItems: 'center', marginVertical: 8 }}>
        <SplashHeroIllustration height={340} />
      </View>

      {/* Bottom Inspiration Quote — 100% Crisp Native Vector, Never Cropped */}
      <View style={{ alignItems: 'center', marginBottom: 8 }}>
        <Text style={{ fontSize: 13, fontWeight: '800', color: '#1E3A8A', textAlign: 'center' }}>Vẽ hôm nay</Text>
        <Text style={{ fontSize: 12, fontWeight: '600', color: '#2563EB', textAlign: 'center', marginTop: 3 }}>
          Một thế giới diệu kỳ ngày mai ♡
        </Text>
      </View>
    </TouchableOpacity>
  );
};

// ==========================================
// 2. ONBOARDING SCREEN (Image 2 - Screen 2)
// ==========================================
export const OnboardingScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header with ONLY "Bỏ qua" on right matching Image 2 */}
      <View style={[styles.topHeader, { justifyContent: 'flex-end' }]}>
        <TouchableOpacity onPress={() => nav('dashboard')}>
          <Text style={styles.skipBtn}>Bỏ qua</Text>
        </TouchableOpacity>
      </View>

      {/* Main Heading */}
      <View style={styles.headingBox}>
        <Text style={[styles.headingTitle, { fontSize: 24, color: '#1E40AF', lineHeight: 30 }]}>{"Nét vẽ của con\ncó thể sống dậy!"}</Text>
        <Text style={styles.headingSubtitle}>
          Sketch2Life biến những bức vẽ thành câu chuyện hoạt hình sinh động và gợi ý hoạt động ngoài màn hình phù hợp với độ tuổi.
        </Text>
      </View>

      {/* Center Illustration: Girl & Dino hugging with sparkles */}
      <View style={styles.centerIllustration}>
        <OnboardingHeroIllustration height={220} />
      </View>

      {/* 3 Value Propositions matching Image 2 */}
      <View style={styles.valuePropsList}>
        <View style={[styles.valuePropCard, { backgroundColor: '#F0F9FF', borderColor: '#BAE6FD' }]}>
          <View style={[styles.valueIconOrb, { backgroundColor: '#38BDF8' }]}>
            <Ionicons name="sparkles" size={18} color={colors.white} />
          </View>
          <Text style={styles.valuePropText}>Biến tranh vẽ thành câu chuyện và nhân vật hoạt hình</Text>
        </View>

        <View style={[styles.valuePropCard, { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' }]}>
          <View style={[styles.valueIconOrb, { backgroundColor: '#22C55E' }]}>
            <Ionicons name="mic" size={18} color={colors.white} />
          </View>
          <Text style={styles.valuePropText}>Khuyến khích con kể chuyện bằng giọng nói</Text>
        </View>

        <View style={[styles.valuePropCard, { backgroundColor: '#FFF7ED', borderColor: '#FED7AA' }]}>
          <View style={[styles.valueIconOrb, { backgroundColor: '#FB923C' }]}>
            <Ionicons name="compass" size={18} color={colors.white} />
          </View>
          <Text style={styles.valuePropText}>Gợi ý hoạt động thực tế để con khám phá thế giới quanh mình</Text>
        </View>
      </View>

      {/* Pagination Dots matching Image 2 Screen 2 */}
      <View style={{ flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6, marginVertical: 8 }}>
        <View style={{ width: 22, height: 6, borderRadius: 3, backgroundColor: '#3B82F6' }} />
        <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: '#CBD5E1' }} />
        <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: '#CBD5E1' }} />
      </View>

      {/* CTA Button matching Image 2 */}
      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Bắt đầu hành trình nào!"
          color="blue"
          size="lg"
          onPress={() => nav('dashboard')}
        />
      </View>
    </ScrollView>
  );
};

// ==========================================
// 3. HOME DASHBOARD (Image 2 - Screen 3)
// ==========================================
export const DashboardScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <View style={{ flex: 1, backgroundColor: '#F0F9FF' }}>
      {/* Decorative floating particles top */}
      <FloatingParticles count={7} style={{ top: 60, height: 80, zIndex: 0 }} />

      <ScrollView contentContainerStyle={[styles.screenContainer, { backgroundColor: 'transparent' }]} showsVerticalScrollIndicator={false}>
        {/* Header Greeting */}
        <View style={styles.dashboardHeader}>
          <View style={{ flex: 1, minWidth: 0, paddingRight: 8 }}>
            <Text style={styles.greetingTitle}>Chào chị Lan! 👋</Text>
            <Text style={styles.greetingSub}>Cùng bé {selectedChild.name} biến những ý tưởng nhỏ thành câu chuyện lớn nhé!</Text>
          </View>
          <View style={styles.headerIcons}>
            <View style={styles.bellBtn}>
              <Ionicons name="notifications-outline" size={20} color={colors.textBody} />
              <View style={styles.notifDot} />
            </View>
            {/* Mom avatar crisp vector */}
            <View style={[styles.avatarBorder, { overflow: 'hidden' }]}>
              <MomAvatarImage size={28} />
            </View>
          </View>
        </View>

        {/* Big Yellow Action Banner — PulseGlow so it calls for attention */}
        <PulseGlow style={{ marginHorizontal: 0 }}>
          <TouchableOpacity
            activeOpacity={0.9}
            onPress={() => nav('profile')}
            style={[styles.createStoryCard, { shadowColor: '#F59E0B', shadowOpacity: 0.35, shadowRadius: 12, elevation: 8 }]}
          >
            <View style={styles.createIconOrb}>
              <Ionicons name="add" size={28} color={colors.yellowDeep} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.createStoryTitle}>+ Tạo câu chuyện mới</Text>
              <Text style={styles.createStorySub}>Từ một bức vẽ của bé {selectedChild.name}</Text>
            </View>
            <Text style={{ fontSize: 24 }}>✨</Text>
          </TouchableOpacity>
        </PulseGlow>

        {/* Recent Stories */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Câu chuyện gần đây</Text>
          <TouchableOpacity onPress={() => nav('story_preview')}>
            <Text style={styles.sectionLink}>Xem tất cả &gt;</Text>
          </TouchableOpacity>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.recentStoriesRow}>
          {/* Card 1: Rainbow Fish — BounceIn with delay 0 */}
          <BounceInView delay={0} style={styles.storyCard}>
            <TouchableOpacity activeOpacity={0.88} onPress={() => nav('story_preview')} style={{ flex: 1 }}>
              <RainbowFishArtwork height={85} />
              <Text numberOfLines={1} style={styles.storyCardTitle}>Chú cá cầu vồng và đại dương rực rỡ</Text>
              <Text style={styles.storyCardDate}>12 Tháng 4, 2025</Text>
            </TouchableOpacity>
          </BounceInView>

          {/* Card 2: Robot — BounceIn with delay 150ms */}
          <BounceInView delay={150} style={styles.storyCard}>
            <TouchableOpacity activeOpacity={0.88} onPress={() => nav('story_preview')} style={{ flex: 1 }}>
              <StoryRobotArtwork height={85} />
              <Text numberOfLines={1} style={styles.storyCardTitle}>Robot khám phá thiên nhiên</Text>
              <Text style={styles.storyCardDate}>8 Tháng 4, 2025</Text>
            </TouchableOpacity>
          </BounceInView>
        </ScrollView>

        {/* Today's Recommended Activity */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Hoạt động gợi ý hôm nay</Text>
        </View>

        <BounceInView delay={300}>
          <TouchableOpacity
            activeOpacity={0.9}
            onPress={() => nav('activity_recommend')}
            style={[styles.todayActivityCard, { borderWidth: 2, borderColor: '#FEF08A' }]}
          >
            {/* Animated sun icon */}
            <View style={[styles.todaySunOrb, { backgroundColor: '#FEF3C7', alignItems: 'center', justifyContent: 'center' }]}>
              <SunIconSvg size={32} />
            </View>
            <View style={{ flex: 1, marginLeft: 12 }}>
              <Text style={styles.todayActTitle}>Cùng trồng một hạt mầm 🌱</Text>
              <Text style={styles.todayActSub}>Giúp bé khám phá thiên nhiên qua những điều nhỏ bé.</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
          </TouchableOpacity>
        </BounceInView>

        {/* Decorative bottom row of floating emojis */}
        <View style={{ height: 16 }} />
      </ScrollView>

      {/* Bottom Navigation Bar */}
      <View style={styles.bottomNav}>
        <TouchableOpacity style={styles.navItem}>
          <Ionicons name="home" size={22} color={colors.blueDeep} />
          <Text style={[styles.navText, { color: colors.blueDeep, fontWeight: '800' }]}>Trang chủ</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => nav('story_preview')}>
          <Ionicons name="book-outline" size={22} color={colors.textLight} />
          <Text style={styles.navText}>Thư viện</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => nav('activity_recommend')}>
          <Ionicons name="compass-outline" size={22} color={colors.textLight} />
          <Text style={styles.navText}>Khám phá</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => nav('feedback')}>
          <Ionicons name="settings-outline" size={22} color={colors.textLight} />
          <Text style={styles.navText}>Cài đặt</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// ==========================================
// 4. CHILD PROFILE (Image 2 - Screen 4)
// ==========================================
export const ChildProfileScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    childrenList,
    selectedChild,
    setSelectedChild,
    selectedAgeGroup,
    setSelectedAgeGroup,
    beginWorkflow,
    workflowBusy,
    workflowError,
  } = useAppContext();
  const nav = onNavigate || navigate;

  const ageList = [
    { id: '3-4', title: '3 – 4 tuổi', desc: 'Khám phá thế giới qua sắc màu', icon: 'color-palette', bg: '#DCFCE7', color: '#16A34A' },
    { id: '5-6', title: '5 – 6 tuổi', desc: 'Kể chuyện sáng tạo, phát triển ngôn ngữ', icon: 'brush', bg: '#DBEAFE', color: '#2563EB' },
    { id: '7-8', title: '7 – 8 tuổi', desc: 'Mở rộng trí tưởng tượng, tư duy logic', icon: 'rocket', bg: '#FFEDD5', color: '#EA580C' },
    { id: '9+', title: '9+ tuổi', desc: 'Thử thách ý tưởng, khám phá sâu hơn', icon: 'bulb', bg: '#F3E8FF', color: '#9333EA' },
  ];

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Hồ sơ của bé</Text>
        <TouchableOpacity onPress={() => nav('capture')}>
          <Text style={styles.skipBtn}>Bỏ qua</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Bé là ai nhỉ?</Text>
        <Text style={styles.headingSubtitle}>
          Chọn hồ sơ hoặc tạo mới để cá nhân hóa trải nghiệm phù hợp với độ tuổi.
        </Text>
      </View>

      {/* Profiles Row */}
      <View style={styles.profilesRow}>
        {/* An */}
        <TouchableOpacity
          onPress={() => {
            const kid = childrenList.find((c) => c.name.toLowerCase() === 'an') || childrenList[0];
            setSelectedChild(kid);
            setSelectedAgeGroup(kid.ageGroup);
          }}
          style={[styles.profileItem, selectedChild.name === 'An' && styles.profileItemSelected]}
        >
          <View style={[styles.avatarCircle, selectedChild.name === 'An' && styles.avatarSelected, { overflow: 'visible', position: 'relative' }]}>
            <ChildAvatarImage childName="An" size={54} />
            {selectedChild.name === 'An' && (
              <View style={{ position: 'absolute', bottom: -1, right: -1, width: 18, height: 18, borderRadius: 9, backgroundColor: '#3B82F6', alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: '#fff' }}>
                <Ionicons name="checkmark" size={11} color="#fff" />
              </View>
            )}
          </View>
          <Text style={styles.kidName}>An</Text>
          <Text style={styles.kidAge}>5 tuổi</Text>
        </TouchableOpacity>

        {/* Bảo */}
        <TouchableOpacity
          onPress={() => {
            const kid = childrenList.find((c) => c.name.toLowerCase() === 'bảo') || childrenList[1];
            setSelectedChild(kid);
            setSelectedAgeGroup(kid.ageGroup);
          }}
          style={[styles.profileItem, selectedChild.name === 'Bảo' && styles.profileItemSelected]}
        >
          <View style={[styles.avatarCircle, selectedChild.name === 'Bảo' && styles.avatarSelected, { overflow: 'hidden' }]}>
            <ChildAvatarImage childName="Bảo" size={54} />
          </View>
          <Text style={styles.kidName}>Bảo</Text>
          <Text style={styles.kidAge}>7 tuổi</Text>
        </TouchableOpacity>

        {/* Add Child */}
        <TouchableOpacity style={styles.profileItem}>
          <View style={[styles.avatarCircle, styles.addKidCircle]}>
            <Ionicons name="add" size={28} color={colors.textLight} />
          </View>
          <Text style={[styles.kidName, { color: colors.textLight }]}>Thêm bé</Text>
          <Text style={styles.kidAge}> </Text>
        </TouchableOpacity>
      </View>

      {/* Age Selection */}
      <Text style={styles.formSectionTitle}>Độ tuổi của bé</Text>
      <View style={styles.ageList}>
        {ageList.map((item) => {
          const isSelected = selectedAgeGroup === item.id;
          return (
            <TouchableOpacity
              key={item.id}
              activeOpacity={0.88}
              onPress={() => setSelectedAgeGroup(item.id)}
              style={[styles.ageCard, isSelected && styles.ageCardSelected]}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 }}>
                <View style={{ width: 34, height: 34, borderRadius: 10, backgroundColor: item.bg, alignItems: 'center', justifyContent: 'center' }}>
                  <Ionicons name={item.icon as any} size={18} color={item.color} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.ageTitle, isSelected && styles.ageTitleSelected]}>{item.title}</Text>
                  <Text style={styles.ageDesc}>{item.desc}</Text>
                </View>
              </View>
              <View style={[styles.radioCircle, isSelected && styles.radioCircleSelected]}>
                {isSelected && <View style={styles.radioInnerDot} />}
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* CTA */}
      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Tiếp tục"
          color="blue"
          size="lg"
          rightIcon={<CuteStarIconSvg size={28} />}
          onPress={() => {
            void beginWorkflow();
          }}
          disabled={!!workflowBusy}
        />
      </View>
      {workflowError && <Text style={{ color: '#B91C1C', textAlign: 'center', marginTop: 10 }}>{workflowError}</Text>}
    </ScrollView>
  );
};

// ==========================================
// 5. CAPTURE / UPLOAD (Image 2 - Screen 5)
// ==========================================
export const CaptureScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    selectedDrawing,
    pickDrawingImage,
    uploadDrawing,
    admission,
    narrationMode,
    setNarrationMode,
    narrationText,
    setNarrationText,
    selectedNarrationAudio,
    isRecording,
    startRecording,
    stopRecording,
    uploadNarration,
    workflowBusy,
    workflowError,
    workflowNotice,
  } = useAppContext();
  const nav = onNavigate || navigate;

  const handlePickImage = async () => {
    await pickDrawingImage();
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Thêm bức vẽ của bé</Text>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Chụp hoặc tải lên bức vẽ</Text>
        <Text style={styles.headingSubtitle}>
          Bức vẽ của bé {selectedChild.name} có thể là tranh trên giấy, sổ tay hay bất cứ đâu. Mọi nét vẽ đều đặc biệt!
        </Text>
      </View>

      {/* Drawing Preview Card with Cat drawing */}
      <View style={styles.drawingCardWrap}>
        {selectedDrawing ? (
          <Image source={{ uri: selectedDrawing.uri }} style={{ width: '100%', height: 180 }} resizeMode="contain" />
        ) : (
          <CatDrawingArtwork height={180} />
        )}
      </View>

      {/* Two Action Buttons */}
      <View style={styles.actionGridRow}>
        <TouchableOpacity
          activeOpacity={0.9}
          onPress={handlePickImage}
          style={[styles.halfBtn, { backgroundColor: colors.blue }]}
        >
          <Ionicons name="images" size={24} color={colors.white} />
          <Text style={styles.halfBtnText}>Chọn ảnh tổng hợp</Text>
        </TouchableOpacity>

        <TouchableOpacity
          activeOpacity={0.9}
          onPress={handlePickImage}
          style={[styles.halfBtn, { backgroundColor: colors.greenDeep }]}
        >
          <Ionicons name="images" size={24} color={colors.white} />
          <Text style={styles.halfBtnText}>Đổi ảnh đã chọn</Text>
        </TouchableOpacity>
      </View>

      <View style={{ marginTop: 14, padding: 14, borderRadius: 18, backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#DBEAFE' }}>
        <Text style={{ fontSize: 15, fontWeight: '900', color: colors.textHeading }}>Lời kể (không bắt buộc)</Text>
        <Text style={{ fontSize: 12, color: colors.textSoft, lineHeight: 17, marginTop: 4 }}>
          Ảnh là bắt buộc. Nếu không nói được, bạn có thể nhập nội dung bằng chữ; chữ sẽ đi thẳng vào AI, không qua TTS.
        </Text>
        <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
          {([
            ['none', 'Không thêm'],
            ['text', 'Nhập chữ'],
            ['audio', 'Ghi âm'],
          ] as const).map(([mode, label]) => (
            <TouchableOpacity
              key={mode}
              onPress={() => setNarrationMode(mode)}
              style={{ flex: 1, minHeight: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: narrationMode === mode ? colors.blue : '#FFFFFF', borderWidth: 1, borderColor: narrationMode === mode ? colors.blue : '#CBD5E1' }}
            >
              <Text style={{ fontSize: 11, fontWeight: '800', color: narrationMode === mode ? colors.white : colors.textBody }}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {narrationMode === 'text' && (
          <TextInput
            value={narrationText}
            onChangeText={setNarrationText}
            placeholder="Ví dụ: Con mèo đang đi tìm hoa..."
            placeholderTextColor="#94A3B8"
            multiline
            maxLength={2000}
            style={{ minHeight: 86, marginTop: 10, padding: 12, borderRadius: 12, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#BFDBFE', color: colors.textBody, textAlignVertical: 'top', fontSize: 13 }}
          />
        )}
        {narrationMode === 'audio' && (
          <View style={{ marginTop: 10, alignItems: 'center' }}>
            <TouchableOpacity
              onPress={() => void (isRecording ? stopRecording() : startRecording())}
              style={{ minWidth: 180, minHeight: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: isRecording ? '#DC2626' : colors.greenDeep }}
            >
              <Text style={{ color: colors.white, fontWeight: '900' }}>{isRecording ? 'Dừng ghi âm' : 'Bắt đầu ghi âm'}</Text>
            </TouchableOpacity>
            <Text style={{ marginTop: 8, fontSize: 12, color: colors.textSoft }}>
              {selectedNarrationAudio ? `Đã có bản ghi (${Math.round((selectedNarrationAudio.durationMs || 0) / 1000)} giây)` : 'M4A/WAV/WebM/Ogg · tối đa 3 phút'}
            </Text>
          </View>
        )}
      </View>

      <Kid3DButton
        title={workflowBusy === 'Tải ảnh' ? 'Đang kiểm tra ảnh...' : workflowBusy === 'Tải lời kể' ? 'Đang lưu lời kể...' : 'Gửi ảnh & tiếp tục'}
        color="blue"
        size="lg"
        disabled={!selectedDrawing || !!workflowBusy || isRecording || (narrationMode === 'text' && !narrationText.trim()) || (narrationMode === 'audio' && !selectedNarrationAudio)}
        onPress={async () => {
          const imageAlreadyAdmitted = admission?.decision === 'ADMITTED';
          if ((!imageAlreadyAdmitted && !(await uploadDrawing())) || !(await uploadNarration())) return;
          nav('ai_processing');
        }}
      />

      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginTop: 10 }}>{workflowNotice}</Text>}
      {workflowError && <Text style={{ color: '#B91C1C', textAlign: 'center', marginTop: 10 }}>{workflowError}</Text>}

      {/* Tips Box */}
      <View style={styles.tipsBox}>
        <Text style={styles.tipsHeading}>💡 Một số gợi ý:</Text>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Chọn PNG/JPEG tổng hợp, tối đa 5 MB</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Không dùng ảnh trẻ em hoặc dữ liệu nhận diện</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Chỉ bước “Phân tích ảnh” mới gửi request Lightning</Text>
        </View>
      </View>
    </ScrollView>
  );
};

// ==========================================
// 6. VOICE RECORDING (Image 2 - Screen 6)
// ==========================================
export const VoiceScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    isRecording,
    toggleRecording,
    voiceDuration,
    setVoiceDuration,
    stopRecording,
    uploadNarration,
    runAiSimulation,
  } = useAppContext();
  const nav = onNavigate || navigate;

  useEffect(() => {
    if (!isRecording) return;
    const interval = setInterval(() => {
      setVoiceDuration(voiceDuration < 180 ? voiceDuration + 1 : voiceDuration);
    }, 1000);
    return () => clearInterval(interval);
  }, [isRecording, voiceDuration, setVoiceDuration]);

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleFinishVoice = async () => {
    if (isRecording) {
      await stopRecording();
      return;
    }
    if (await uploadNarration() && await runAiSimulation()) nav('ai_processing');
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Kể chuyện bằng giọng nói</Text>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Giờ hãy kể về bức vẽ của bé {selectedChild.name} nhé!</Text>
        <Text style={styles.headingSubtitle}>
          Bé muốn nhân vật của mình làm gì? Hãy kể bất cứ điều gì. Chúng tôi sẽ biến giọng nói thành một câu chuyện thật sống động!
        </Text>
      </View>

      {/* Girl Mascot with Mic matching Image 2 Screen 6 */}
      <View style={styles.centerIllustration}>
        <VoiceGirlMicIllustration height={160} />
      </View>

      {/* Waveform Card */}
      <View style={[styles.waveformCard, { backgroundColor: '#FFFFFF', borderColor: '#BAE6FD' }]}>
        <Image
          source={require('../../assets/images/voice_waveform.png')}
          style={{ width: '92%', height: 42, resizeMode: 'contain', marginVertical: 6 }}
        />
        <Text style={[styles.waveformTimer, isRecording && { color: '#EF4444' }]}>
          {isRecording ? `Đang ghi âm...  ${formatTime(voiceDuration)} / 03:00` : `${formatTime(voiceDuration)} / 03:00`}
        </Text>
      </View>

      {/* Recording Controls matching Image 2 Screen 6 */}
      <View style={styles.recordControlsRow}>
        <TouchableOpacity
          onPress={toggleRecording}
          style={styles.auxRecordBtn}
        >
          <Ionicons name={isRecording ? 'pause' : 'play'} size={20} color={colors.textBody} />
          <Text style={styles.auxRecordText}>{isRecording ? 'Tạm dừng' : 'Ghi âm'}</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={handleFinishVoice}
          style={styles.mainRecordBtn}
        >
          <View style={styles.recordInnerSquare} />
        </TouchableOpacity>

        <TouchableOpacity
          onPress={goBack}
          style={styles.auxRecordBtn}
        >
          <Ionicons name="close" size={20} color={colors.textLight} />
          <Text style={styles.auxRecordText}>Hủy</Text>
        </TouchableOpacity>
      </View>
      {isRecording && (
        <Text style={[styles.recordingLabel, { color: '#EF4444', fontWeight: '700' }]}>
          Đang ghi âm... Chạm nút đỏ để hoàn tất
        </Text>
      )}
      {!isRecording && (
        <TouchableOpacity onPress={handleFinishVoice}>
          <Text style={styles.recordingLabel}>
            Chạm nút đỏ ở giữa để tiếp tục
          </Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  centerContainer: {
    flexGrow: 1,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  screenContainer: {
    padding: 16,
    paddingBottom: 24,
    width: '100%',
    alignItems: 'stretch',
  },
  topHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  brandTitle: {
    fontSize: 20,
    fontWeight: '900',
    color: colors.blue,
  },
  screenHeaderTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.textHeading,
  },
  skipBtn: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textLight,
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
    marginVertical: 6,
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
    fontSize: 12,
    color: colors.textSoft,
    textAlign: 'center',
    lineHeight: 16,
    paddingHorizontal: 8,
  },
  centerIllustration: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 10,
    position: 'relative',
  },
  valuePropsList: {
    gap: 8,
    marginVertical: 10,
  },
  valuePropCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: 10,
  },
  valueIconOrb: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  valuePropText: {
    flex: 1,
    fontSize: 12,
    fontWeight: '700',
    color: colors.textBody,
    lineHeight: 16,
  },
  actionBottom: {
    marginTop: 14,
    marginBottom: 6,
  },
  dashboardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  greetingTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: colors.textHeading,
  },
  greetingSub: {
    fontSize: 11,
    color: colors.textSoft,
    marginTop: 2,
    maxWidth: 240,
  },
  headerIcons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  bellBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.lineSoft,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  notifDot: {
    position: 'absolute',
    top: 6,
    right: 7,
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.coral,
  },
  avatarBorder: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.blueSoft,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.blue,
  },
  createStoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF08A',
    borderColor: '#FACC15',
    borderWidth: 1.5,
    borderRadius: radius.lg,
    padding: 14,
    marginBottom: 16,
    gap: 12,
    ...shadows.card,
  },
  createIconOrb: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
  },
  createStoryTitle: {
    fontSize: 16,
    fontWeight: '900',
    color: colors.yellowDeep,
  },
  createStorySub: {
    fontSize: 11,
    fontWeight: '600',
    color: '#854D0E',
    marginTop: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
    marginTop: 6,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '900',
    color: colors.textHeading,
  },
  sectionLink: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.blueDeep,
  },
  recentStoriesRow: {
    gap: 12,
    paddingBottom: 6,
  },
  storyCard: {
    width: 170,
    backgroundColor: colors.white,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 10,
    ...shadows.card,
  },
  robotStoryBox: {
    height: 85,
    borderRadius: radius.sm,
    backgroundColor: '#F0FDF4',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  robotStoryTag: {
    position: 'absolute',
    bottom: 4,
    fontSize: 9,
    fontWeight: '800',
    color: '#15803D',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 6,
  },
  storyCardTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 6,
  },
  storyCardDate: {
    fontSize: 9,
    color: colors.textLight,
    marginTop: 2,
  },
  todayActivityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFBEB',
    borderColor: '#FDE68A',
    borderWidth: 1,
    borderRadius: radius.md,
    padding: 12,
    marginTop: 4,
    marginBottom: 10,
  },
  todaySunOrb: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  todayActTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#92400E',
  },
  todayActSub: {
    fontSize: 10,
    color: '#B45309',
    marginTop: 2,
  },
  bottomNav: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: colors.line,
    backgroundColor: colors.white,
    paddingVertical: 8,
    width: '100%',
  },
  navItem: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
  },
  navText: {
    fontSize: 10,
    color: colors.textLight,
    fontWeight: '600',
  },
  profilesRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginVertical: 12,
  },
  profileItem: {
    alignItems: 'center',
    padding: 6,
  },
  profileItemSelected: {
    transform: [{ scale: 1.05 }],
  },
  avatarCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.lineSoft,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  avatarSelected: {
    borderColor: colors.blue,
    backgroundColor: colors.blueSoft,
    ...shadows.card,
  },
  addKidCircle: {
    borderStyle: 'dashed',
    borderColor: colors.line,
    borderWidth: 2,
    backgroundColor: colors.white,
  },
  kidName: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 6,
  },
  kidAge: {
    fontSize: 10,
    color: colors.textSoft,
  },
  formSectionTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 8,
    marginBottom: 6,
  },
  ageList: {
    gap: 8,
    marginBottom: 10,
  },
  ageCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: 10,
  },
  ageCardSelected: {
    borderColor: colors.blue,
    backgroundColor: colors.blueSoft,
  },
  ageTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
  },
  ageTitleSelected: {
    color: colors.blueDeep,
  },
  ageDesc: {
    fontSize: 10,
    color: colors.textSoft,
    marginTop: 2,
  },
  radioCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 1.5,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioCircleSelected: {
    borderColor: colors.blueDeep,
  },
  radioInnerDot: {
    width: 9,
    height: 9,
    borderRadius: 4.5,
    backgroundColor: colors.blueDeep,
  },
  drawingCardWrap: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 12,
    alignItems: 'center',
    marginVertical: 10,
    overflow: 'visible',
    ...shadows.card,
  },
  drawingBubble: {
    backgroundColor: '#FEF9C3',
    borderColor: '#FDE047',
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginBottom: 8,
  },
  drawingBubbleText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#854D0E',
  },
  actionGridRow: {
    flexDirection: 'row',
    gap: 10,
    marginVertical: 8,
  },
  halfBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: radius.md,
    gap: 6,
    ...shadows.card,
  },
  halfBtnText: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.white,
  },
  tipsBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 10,
    marginTop: 8,
    gap: 4,
  },
  tipsHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textHeading,
    marginBottom: 2,
  },
  tipRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tipText: {
    fontSize: 10,
    color: colors.textSoft,
  },
  bubbleVoiceWrapper: {
    backgroundColor: '#FEF08A',
    borderColor: '#FACC15',
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginBottom: 6,
    position: 'relative',
  },
  bubbleVoiceText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#854D0E',
  },
  bubblePointer: {
    position: 'absolute',
    bottom: -5,
    left: '50%',
    marginLeft: -5,
    width: 0,
    height: 0,
    borderLeftWidth: 5,
    borderRightWidth: 5,
    borderTopWidth: 5,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: '#FACC15',
  },
  waveformCard: {
    backgroundColor: '#F0F9FF',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: '#BAE6FD',
    padding: 12,
    alignItems: 'center',
    marginVertical: 10,
  },
  waveformBars: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 50,
    gap: 4,
  },
  waveBar: {
    width: 4,
    borderRadius: 2,
  },
  waveformTimer: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.blueDeep,
    marginTop: 8,
  },
  recordControlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    marginVertical: 8,
  },
  auxRecordBtn: {
    alignItems: 'center',
    gap: 2,
    minWidth: 54,
  },
  auxRecordText: {
    fontSize: 10,
    color: colors.textSoft,
    fontWeight: '600',
  },
  mainRecordBtn: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#EF4444',
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.card,
    borderWidth: 3,
    borderColor: '#FEE2E2',
  },
  recordInnerSquare: {
    width: 22,
    height: 22,
    borderRadius: 4,
    backgroundColor: colors.white,
  },
  recordingLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textLight,
    textAlign: 'center',
    marginTop: 4,
  },
  quoteCard: {
    backgroundColor: colors.white,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: 'center',
    marginVertical: 4,
    ...shadows.card,
  },
  quoteText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textBody,
  },
});
