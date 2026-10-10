// BaoVC Standalone Screen Implementation
import React, { useState, useEffect, useRef } from 'react';
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
import {
  LogoSketch2Life,
  CatDrawingArtwork,
  RainbowFishArtwork,
  StoryRobotArtwork,
  SplashHeroIllustration,
  OnboardingHeroIllustration,
  VoiceGirlMicIllustration,
  MomAvatarImage,
  ChildAvatarImage,
  FloatingParticles,
  BounceInView,
  PulseGlow,
  CuteStarIconSvg,
  ButterflyIconSvg,
  FlowerIconSvg,
  SunIconSvg,
  LiveWaveBars,
} from '../components/ArtworkCards';

import type { ScreenId } from '../types';
import { useAppContext } from '../context/AppContext';

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

// ==========================================
// 01. SPLASH SCREEN (Vibrant Midnight 3D Galaxy)
// ==========================================
export const SplashScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;

  useEffect(() => {
    const timer = setTimeout(() => {
      nav('onboarding');
    }, 3200);
    return () => clearTimeout(timer);
  }, [nav]);

  return (
    <TouchableOpacity
      activeOpacity={0.96}
      onPress={() => nav('onboarding')}
      style={{
        flex: 1,
        backgroundColor: '#0B132B',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 36,
        paddingHorizontal: 20,
      }}
    >
      {/* 3D Floating star particles */}
      <FloatingParticles count={8} style={{ top: 20, height: 180 }} />

      {/* Top Brand Logo */}
      <View style={{ alignItems: 'center', marginTop: 16 }}>
        <PulseGlow>
          <LogoSketch2Life size="lg" showTagline={false} />
        </PulseGlow>
        <Text style={{ fontSize: 13, fontWeight: '700', color: '#BAE6FD', marginTop: 8, textAlign: 'center', letterSpacing: 0.3 }}>
          Mỗi nét vẽ đều có một câu chuyện đang chờ được kể... ✨
        </Text>
      </View>

      {/* Crisp 1024x1024 Hero Illustration */}
      <View style={{ width: '100%', flex: 1, justifyContent: 'center', alignItems: 'center', marginVertical: 10 }}>
        <BounceInView delay={100}>
          <SplashHeroIllustration height={310} />
        </BounceInView>
      </View>

      {/* Bottom Quote & 3D Tactile CTA */}
      <View style={{ width: '100%', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <View style={{ alignItems: 'center' }}>
          <Text style={{ fontSize: 14, fontWeight: '900', color: '#FFFFFF', letterSpacing: 0.5 }}>Vẽ hôm nay 🎨</Text>
          <Text style={{ fontSize: 12, fontWeight: '700', color: '#38BDF8', marginTop: 3 }}>
            Một thế giới diệu kỳ ngày mai ♡
          </Text>
        </View>

        <Kid3DButton
          title="Bắt đầu khám phá ✨"
          color="blue"
          size="md"
          onPress={() => nav('onboarding')}
          style={{ width: '85%', marginTop: 4 }}
        />
      </View>
    </TouchableOpacity>
  );
};

// ==========================================
// 02. ONBOARDING (3 Slides with 3D Depth)
// ==========================================
export const OnboardingScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;
  const [slide, setSlide] = useState(0);

  const slides = [
    {
      title: 'Nét vẽ của con\ncó thể sống dậy!',
      subtitle: 'Biến những bức tranh nhỏ thành câu chuyện và hoạt động đời thật.',
      illustration: (
        <BounceInView delay={0}>
          <Image
            source={require('../../assets/images/onboarding_hero.png')}
            style={{ width: 280, height: 210, resizeMode: 'contain' }}
          />
        </BounceInView>
      ),
    },
    {
      title: 'AI thấu hiểu\nbức tranh của bé',
      subtitle: 'Tự động nhận diện nhân vật, khung cảnh và lắng nghe giọng kể của con.',
      illustration: (
        <BounceInView delay={100}>
          <PulseGlow>
            <Image
              source={require('../../assets/images/robot_ai.png')}
              style={{ width: 220, height: 210, resizeMode: 'contain' }}
            />
          </PulseGlow>
        </BounceInView>
      ),
    },
    {
      title: 'Học tập Montessori\nngoài đời thực',
      subtitle: 'Chuyển cảm hứng từ màn hình thành trải nghiệm thủ công, khám phá thiên nhiên!',
      illustration: (
        <BounceInView delay={100}>
          <Image
            source={require('../../assets/images/photo_craft_butterfly.png')}
            style={{ width: 280, height: 200, borderRadius: 16, resizeMode: 'cover', borderWidth: 2, borderColor: '#FDE68A' }}
          />
        </BounceInView>
      ),
    },
  ];

  const current = slides[slide];

  return (
    <View style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      <ScrollView contentContainerStyle={[styles.screenContainer, { flexGrow: 1, justifyContent: 'space-between' }]} showsVerticalScrollIndicator={false}>
        <View>
          {/* Top Header */}
          <View style={[styles.topHeader, { justifyContent: 'space-between', marginBottom: 4 }]}>
            <Text style={{ fontSize: 12, fontWeight: '800', color: '#2563EB' }}>{slide + 1} / 3</Text>
            <TouchableOpacity onPress={() => nav('dashboard')}>
              <Text style={styles.skipBtn}>Bỏ qua</Text>
            </TouchableOpacity>
          </View>

          {/* Heading */}
          <View style={[styles.headingBox, { marginTop: 6, marginBottom: 8 }]}>
            <Text style={[styles.headingTitle, { fontSize: 24, color: '#1E40AF', lineHeight: 30 }]}>
              {current.title}
            </Text>
            <Text style={[styles.headingSubtitle, { fontSize: 13, lineHeight: 18, marginTop: 6, maxWidth: 310 }]}>
              {current.subtitle}
            </Text>
          </View>

          {/* Center Illustration */}
          <View style={[styles.centerIllustration, { marginVertical: 14, minHeight: 220 }]}>
            {current.illustration}
          </View>
        </View>

        {/* Bottom controls: 3D Dots & Next Button */}
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, paddingHorizontal: 12 }}>
          {/* Dots */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            {[0, 1, 2].map((i) => (
              <TouchableOpacity key={i} onPress={() => setSlide(i)}>
                <View
                  style={{
                    width: i === slide ? 24 : 8,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: i === slide ? '#2563EB' : '#E2E8F0',
                  }}
                />
              </TouchableOpacity>
            ))}
          </View>

          {/* 3D Round / Pill Button */}
          {slide < 2 ? (
            <TouchableOpacity
              activeOpacity={0.88}
              onPress={() => setSlide(slide + 1)}
              style={{
                width: 54,
                height: 54,
                borderRadius: 27,
                backgroundColor: '#2563EB',
                alignItems: 'center',
                justifyContent: 'center',
                borderBottomWidth: 4,
                borderBottomColor: '#1D4ED8',
                ...shadows.card,
              }}
            >
              <Ionicons name="arrow-forward" size={24} color="#FFFFFF" />
            </TouchableOpacity>
          ) : (
            <Kid3DButton
              title="Bắt đầu ngay →"
              color="blue"
              size="md"
              onPress={() => nav('dashboard')}
            />
          )}
        </View>
      </ScrollView>
    </View>
  );
};

// ==========================================
// 03. HOME DASHBOARD (Trang chủ sinh động)
// ==========================================
export const DashboardScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <View style={{ flex: 1, backgroundColor: '#F8FAFC' }}>
      <ScrollView
        contentContainerStyle={[styles.screenContainer, { backgroundColor: 'transparent' }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Header Greeting */}
        <View style={styles.dashboardHeader}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
            <View style={[styles.avatarBorder, { overflow: 'hidden' }]}>
              <MomAvatarImage size={38} />
            </View>
            <View>
              <Text style={{ fontSize: 11, color: colors.textSoft, fontWeight: '600' }}>Xin chào,</Text>
              <Text style={{ fontSize: 16, fontWeight: '900', color: colors.textHeading }}>Ba/Mẹ bé An! 👋</Text>
            </View>
          </View>
          <TouchableOpacity style={styles.bellBtn}>
            <Ionicons name="notifications-outline" size={20} color={colors.textBody} />
            <View style={{ position: 'absolute', top: 6, right: 6, width: 8, height: 8, borderRadius: 4, backgroundColor: '#EF4444' }} />
          </TouchableOpacity>
        </View>

        {/* Big 3D Blue CTA Card (Pulsing Glow) */}
        <PulseGlow>
          <TouchableOpacity
            activeOpacity={0.9}
            onPress={() => nav('profile')}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: '#2563EB',
              borderRadius: radius.lg,
              paddingVertical: 16,
              paddingHorizontal: 20,
              marginBottom: 18,
              borderBottomWidth: 4,
              borderBottomColor: '#1E40AF',
              ...shadows.card,
            }}
          >
            <View style={{ gap: 2 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <Text style={{ fontSize: 16, fontWeight: '900', color: '#FFFFFF' }}>+ Tạo câu chuyện mới</Text>
                <Text style={{ fontSize: 18 }}>✨</Text>
              </View>
              <Text style={{ fontSize: 11, color: '#DBEAFE', fontWeight: '600' }}>Từ một bức vẽ của bé An</Text>
            </View>
            <View style={{ width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(255,255,255,0.25)', alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
            </View>
          </TouchableOpacity>
        </PulseGlow>

        {/* Stories Section Header */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Câu chuyện của bé 📚</Text>
          <TouchableOpacity onPress={() => nav('story_preview')}>
            <Text style={styles.sectionLink}>Xem tất cả &gt;</Text>
          </TouchableOpacity>
        </View>

        {/* Horizontal Carousel of Stories */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 16 }} contentContainerStyle={{ gap: 12 }}>
          {/* Card 1: Chú cá cầu vồng */}
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={() => nav('story_preview')}
            style={{
              width: 170,
              backgroundColor: '#FFFFFF',
              borderRadius: radius.md,
              borderWidth: 1,
              borderColor: colors.line,
              overflow: 'hidden',
              ...shadows.card,
            }}
          >
            <View style={{ height: 100, backgroundColor: '#EFF6FF', overflow: 'hidden' }}>
              <Image
                source={require('../../assets/images/photo_rainbow_fish.png')}
                style={{ width: '100%', height: '100%', resizeMode: 'cover' }}
              />
              <View style={{ position: 'absolute', bottom: 6, right: 6, width: 26, height: 26, borderRadius: 13, backgroundColor: 'rgba(37,99,235,0.85)', alignItems: 'center', justifyContent: 'center' }}>
                <Ionicons name="play" size={14} color="#FFFFFF" />
              </View>
            </View>
            <View style={{ padding: 10 }}>
              <Text numberOfLines={1} style={{ fontSize: 12, fontWeight: '800', color: colors.textHeading }}>Chú cá cầu vồng</Text>
              <Text style={{ fontSize: 10, color: colors.textLight, marginTop: 2 }}>Hôm qua</Text>
              <View style={{ alignSelf: 'flex-start', backgroundColor: '#DCFCE7', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, marginTop: 4 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: '#15803D' }}>Hoàn thành ✅</Text>
              </View>
            </View>
          </TouchableOpacity>

          {/* Card 2: Chú mèo sắc màu */}
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={() => nav('story_preview')}
            style={{
              width: 170,
              backgroundColor: '#FFFFFF',
              borderRadius: radius.md,
              borderWidth: 1,
              borderColor: colors.line,
              overflow: 'hidden',
              ...shadows.card,
            }}
          >
            <View style={{ height: 100, backgroundColor: '#FFFBEB', overflow: 'hidden' }}>
              <Image
                source={require('../../assets/images/photo_cat_paper.png')}
                style={{ width: '100%', height: '100%', resizeMode: 'cover' }}
              />
              <View style={{ position: 'absolute', bottom: 6, right: 6, width: 26, height: 26, borderRadius: 13, backgroundColor: 'rgba(37,99,235,0.85)', alignItems: 'center', justifyContent: 'center' }}>
                <Ionicons name="play" size={14} color="#FFFFFF" />
              </View>
            </View>
            <View style={{ padding: 10 }}>
              <Text numberOfLines={1} style={{ fontSize: 12, fontWeight: '800', color: colors.textHeading }}>Mèo con ngũ sắc</Text>
              <Text style={{ fontSize: 10, color: colors.textLight, marginTop: 2 }}>3 ngày trước</Text>
            </View>
          </TouchableOpacity>

          {/* Card 3: Robot thám hiểm */}
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={() => nav('story_preview')}
            style={{
              width: 170,
              backgroundColor: '#FFFFFF',
              borderRadius: radius.md,
              borderWidth: 1,
              borderColor: colors.line,
              overflow: 'hidden',
              ...shadows.card,
            }}
          >
            <View style={{ height: 100, backgroundColor: '#F0FDF4', overflow: 'hidden' }}>
              <Image
                source={require('../../assets/images/story_robot.png')}
                style={{ width: '100%', height: '100%', resizeMode: 'cover' }}
              />
            </View>
            <View style={{ padding: 10 }}>
              <Text numberOfLines={1} style={{ fontSize: 12, fontWeight: '800', color: colors.textHeading }}>Robot thám hiểm</Text>
              <Text style={{ fontSize: 10, color: colors.textLight, marginTop: 2 }}>1 tuần trước</Text>
            </View>
          </TouchableOpacity>
        </ScrollView>

        {/* Montessori Activity Recommendation Card */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Gợi ý hoạt động hôm nay 🌱</Text>
        </View>

        <TouchableOpacity
          activeOpacity={0.9}
          onPress={() => nav('activity_recommend')}
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            backgroundColor: '#FFFFFF',
            borderRadius: radius.lg,
            borderWidth: 1.5,
            borderColor: '#FDE68A',
            padding: 12,
            gap: 12,
            marginBottom: 20,
            ...shadows.card,
          }}
        >
          <View style={{ width: 50, height: 50, borderRadius: 25, backgroundColor: '#FEF3C7', alignItems: 'center', justifyContent: 'center' }}>
            <SunIconSvg size={32} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 13, fontWeight: '900', color: colors.textHeading }}>Trồng hạt mầm cùng bé 🌱</Text>
            <Text style={{ fontSize: 11, color: colors.textSoft, marginTop: 2 }}>5–10 phút • Trong nhà • Khám phá sinh học</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color="#D97706" />
        </TouchableOpacity>
      </ScrollView>

      {/* Bottom Navigation */}
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
          <Text style={styles.navText}>Hoạt động</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => nav('profile')}>
          <Ionicons name="person-outline" size={22} color={colors.textLight} />
          <Text style={styles.navText}>Hồ sơ</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// ==========================================
// 04. CHILD PROFILE — Hồ sơ bé (Người lớn)
// ==========================================
export const ChildProfileScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;

  const [favLikes, setFavLikes] = useState<string[]>(['Khủng long', 'Vẽ tranh', 'Bươm bướm']);
  const allLikes = ['Khủng long 🦖', 'Bươm bướm 🦋', 'Vẽ tranh 🎨', 'Cây cối 🌿', 'Tên lửa 🚀', 'Động vật 🐾'];

  const toggleLike = (item: string) => {
    if (favLikes.includes(item)) {
      setFavLikes(favLikes.filter((x) => x !== item));
    } else {
      setFavLikes([...favLikes, item]);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Hồ sơ của bé</Text>
        <TouchableOpacity style={{ backgroundColor: '#2563EB', paddingHorizontal: 16, paddingVertical: 6, borderRadius: 10 }}>
          <Text style={{ fontSize: 11, fontWeight: '800', color: '#FFFFFF' }}>LƯU</Text>
        </TouchableOpacity>
      </View>

      {/* 3D Avatar Center */}
      <View style={{ alignItems: 'center', marginVertical: 10 }}>
        <View style={{ position: 'relative' }}>
          <ChildAvatarImage childName="An" size={76} />
          <View style={{ position: 'absolute', bottom: 0, right: 0, width: 24, height: 24, borderRadius: 12, backgroundColor: '#2563EB', alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: '#FFFFFF' }}>
            <Ionicons name="camera" size={12} color="#FFFFFF" />
          </View>
        </View>
        <Text style={{ fontSize: 17, fontWeight: '900', color: colors.textHeading, marginTop: 8 }}>Bé An</Text>
        <View style={{ backgroundColor: '#DBEAFE', paddingHorizontal: 10, paddingVertical: 2, borderRadius: 8, marginTop: 4 }}>
          <Text style={{ fontSize: 11, fontWeight: '700', color: '#1E40AF' }}>4 tuổi 2 tháng</Text>
        </View>
      </View>

      {/* Visual Chips for Likes (No long typing!) */}
      <View style={{ gap: 8, marginVertical: 8 }}>
        <Text style={{ fontSize: 12, fontWeight: '800', color: colors.textHeading }}>Bé thích gì nhất? 🌟</Text>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
          {allLikes.map((item, i) => {
            const isSel = favLikes.includes(item);
            return (
              <TouchableOpacity
                key={i}
                activeOpacity={0.8}
                onPress={() => toggleLike(item)}
                style={{
                  backgroundColor: isSel ? '#EFF6FF' : '#F1F5F9',
                  borderWidth: isSel ? 1.5 : 1,
                  borderColor: isSel ? '#2563EB' : '#E2E8F0',
                  paddingHorizontal: 10,
                  paddingVertical: 6,
                  borderRadius: 14,
                }}
              >
                <Text style={{ fontSize: 11, fontWeight: isSel ? '800' : '600', color: isSel ? '#1D4ED8' : colors.textBody }}>
                  {item} {isSel ? '✓' : ''}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Adult Guidance Dropdown */}
      <View style={{ gap: 6, marginVertical: 6 }}>
        <Text style={{ fontSize: 12, fontWeight: '800', color: colors.textHeading }}>Người lớn sẽ đồng hành?</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#FFFFFF', borderRadius: radius.md, borderWidth: 1, borderColor: colors.line, padding: 12 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Text style={{ fontSize: 16 }}>👨‍👩‍👦</Text>
            <Text style={{ fontSize: 12, fontWeight: '700', color: colors.textBody }}>Có, luôn ở gần hỗ trợ</Text>
          </View>
          <Ionicons name="checkmark-circle" size={18} color="#16A34A" />
        </View>
      </View>

      {/* Privacy Guarantee Card */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#F0FDF4', borderRadius: radius.md, borderWidth: 1, borderColor: '#BBF7D0', padding: 10, marginVertical: 10 }}>
        <Ionicons name="shield-checkmark" size={18} color="#16A34A" />
        <Text style={{ fontSize: 11, color: '#166534', flex: 1, fontWeight: '600', lineHeight: 15 }}>
          Bảo vệ quyền riêng tư: Dữ liệu tranh vẽ không chia sẻ hay lưu trữ nhạy cảm.
        </Text>
      </View>

      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Tiếp tục →"
          color="blue"
          size="lg"
          onPress={() => nav('capture')}
        />
      </View>
    </ScrollView>
  );
};

// ==========================================
// 05. CAPTURE — Chọn tranh của bé
// ==========================================
export const CaptureScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, setDrawingImage } = useAppContext();
  const nav = onNavigate || navigate;

  const handlePickImage = () => {
    setDrawingImage('photo_cat_paper');
    nav('choose_story_method');
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Chọn bức vẽ của bé</Text>
        <View style={{ width: 32 }} />
      </View>

      {/* Drawing Artwork in 3D Framed Card */}
      <View style={{ backgroundColor: '#FFFDF5', borderRadius: radius.lg, borderWidth: 2, borderColor: '#FDE68A', padding: 12, alignItems: 'center', marginVertical: 10, ...shadows.card }}>
        <Image
          source={require('../../assets/images/photo_cat_paper.png')}
          style={{ width: '100%', height: 210, borderRadius: 12, resizeMode: 'cover' }}
        />
        <View style={{ position: 'absolute', top: 18, left: 18, backgroundColor: 'rgba(255,255,255,0.9)', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 }}>
          <Text style={{ fontSize: 10, fontWeight: '800', color: '#2563EB' }}>🎨 Tranh gốc của bé An</Text>
        </View>
      </View>

      {/* 2 Tactile 3D Action Buttons */}
      <View style={{ flexDirection: 'row', gap: 10, marginVertical: 8 }}>
        <TouchableOpacity
          activeOpacity={0.88}
          onPress={handlePickImage}
          style={{
            flex: 1,
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            backgroundColor: '#2563EB',
            borderRadius: radius.md,
            paddingVertical: 12,
            borderBottomWidth: 3,
            borderBottomColor: '#1D4ED8',
          }}
        >
          <Ionicons name="camera" size={18} color="#FFFFFF" />
          <Text style={{ fontSize: 12, fontWeight: '800', color: '#FFFFFF' }}>Chụp ảnh mới</Text>
        </TouchableOpacity>

        <TouchableOpacity
          activeOpacity={0.88}
          onPress={handlePickImage}
          style={{
            flex: 1,
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            backgroundColor: '#16A34A',
            borderRadius: radius.md,
            paddingVertical: 12,
            borderBottomWidth: 3,
            borderBottomColor: '#15803D',
          }}
        >
          <Ionicons name="images" size={18} color="#FFFFFF" />
          <Text style={{ fontSize: 12, fontWeight: '800', color: '#FFFFFF' }}>Từ thư viện</Text>
        </TouchableOpacity>
      </View>

      {/* Yellow Privacy Notice matching Leader Screen 05 */}
      <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 8, backgroundColor: '#FFFBEB', borderRadius: radius.md, borderWidth: 1, borderColor: '#FDE68A', padding: 10, marginVertical: 6 }}>
        <Ionicons name="information-circle" size={16} color="#D97706" style={{ marginTop: 1 }} />
        <Text style={{ fontSize: 10.5, color: '#92400E', flex: 1, lineHeight: 15 }}>
          Chỉ chọn ảnh bức vẽ của bé. Không dùng ảnh có khuôn mặt trẻ em để bảo vệ quyền riêng tư.
        </Text>
      </View>

      {/* Visual Photography Tips Chips */}
      <View style={{ backgroundColor: '#F8FAFC', borderRadius: radius.md, borderWidth: 1, borderColor: colors.line, padding: 10, marginVertical: 4, gap: 6 }}>
        <Text style={{ fontSize: 11, fontWeight: '800', color: colors.textHeading }}>💡 Mẹo chụp tranh đẹp:</Text>
        <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
          <Text style={{ fontSize: 10, color: colors.textSoft }}>☀️ Đủ ánh sáng</Text>
          <Text style={{ fontSize: 10, color: colors.textSoft }}>📐 Thẳng góc chụp</Text>
          <Text style={{ fontSize: 10, color: colors.textSoft }}>🔍 Nét vẽ rõ ràng</Text>
        </View>
      </View>

      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Tiếp tục →"
          color="blue"
          size="lg"
          onPress={handlePickImage}
        />
      </View>
    </ScrollView>
  );
};

// ==========================================
// 06. CHOOSE STORY METHOD — Chọn cách kể
// ==========================================
export const ChooseStoryMethodScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;
  const [selected, setSelected] = useState<'voice' | 'text' | 'skip'>('voice');

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <View style={{ width: 32 }} />
      </View>

      <View style={[styles.headingBox, { marginBottom: 12 }]}>
        <Text style={[styles.headingTitle, { fontSize: 20, lineHeight: 26 }]}>
          Bé có muốn kể về{'\n'}bức tranh không? 🎤
        </Text>
      </View>

      {/* 3 Tactile Visual Cards */}
      <TouchableOpacity
        activeOpacity={0.88}
        onPress={() => setSelected('voice')}
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          backgroundColor: selected === 'voice' ? '#FFF1F2' : '#FFFFFF',
          borderWidth: selected === 'voice' ? 2 : 1,
          borderColor: selected === 'voice' ? '#F43F5E' : '#FECDD3',
          borderRadius: radius.lg,
          padding: 14,
          marginBottom: 10,
          gap: 12,
          borderBottomWidth: selected === 'voice' ? 4 : 1,
          borderBottomColor: selected === 'voice' ? '#E11D48' : '#FECDD3',
          ...shadows.card,
        }}
      >
        <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: '#FFE4E6', alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ fontSize: 24 }}>🎙️</Text>
        </View>
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Text style={{ fontSize: 14, fontWeight: '900', color: colors.textHeading }}>Bé kể bằng giọng nói</Text>
            <View style={{ backgroundColor: '#FEE2E2', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
              <Text style={{ fontSize: 9, fontWeight: '800', color: '#DC2626' }}>Khuyên dùng</Text>
            </View>
          </View>
          <Text style={{ fontSize: 11, color: colors.textSoft, marginTop: 2 }}>Bé tự mô tả tranh theo cảm xúc</Text>
        </View>
      </TouchableOpacity>

      <TouchableOpacity
        activeOpacity={0.88}
        onPress={() => setSelected('text')}
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          backgroundColor: selected === 'text' ? '#FFFBEB' : '#FFFFFF',
          borderWidth: selected === 'text' ? 2 : 1,
          borderColor: selected === 'text' ? '#F59E0B' : '#FDE68A',
          borderRadius: radius.lg,
          padding: 14,
          marginBottom: 10,
          gap: 12,
          borderBottomWidth: selected === 'text' ? 4 : 1,
          borderBottomColor: selected === 'text' ? '#D97706' : '#FDE68A',
          ...shadows.card,
        }}
      >
        <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: '#FEF3C7', alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ fontSize: 24 }}>✍️</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 14, fontWeight: '900', color: colors.textHeading }}>Nhập bằng chữ</Text>
          <Text style={{ fontSize: 11, color: colors.textSoft, marginTop: 2 }}>Ba mẹ gõ lại lời kể giúp con</Text>
        </View>
      </TouchableOpacity>

      <TouchableOpacity
        activeOpacity={0.88}
        onPress={() => setSelected('skip')}
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          backgroundColor: selected === 'skip' ? '#F1F5F9' : '#FFFFFF',
          borderWidth: selected === 'skip' ? 2 : 1,
          borderColor: selected === 'skip' ? '#64748B' : '#E2E8F0',
          borderRadius: radius.lg,
          padding: 14,
          marginBottom: 12,
          gap: 12,
          borderBottomWidth: selected === 'skip' ? 4 : 1,
          borderBottomColor: selected === 'skip' ? '#475569' : '#E2E8F0',
          ...shadows.card,
        }}
      >
        <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: '#E2E8F0', alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ fontSize: 24 }}>🖼️</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 14, fontWeight: '900', color: colors.textHeading }}>Không thêm lời kể</Text>
          <Text style={{ fontSize: 11, color: colors.textSoft, marginTop: 2 }}>Để AI tự phân tích hình ảnh trực tiếp</Text>
        </View>
      </TouchableOpacity>

      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Tiếp tục →"
          color="blue"
          size="lg"
          onPress={() => {
            if (selected === 'voice') nav('voice');
            else nav('ai_processing');
          }}
        />
      </View>
    </ScrollView>
  );
};

// ==========================================
// 07. VOICE RECORDING — Bé kể chuyện (Cho bé)
// ==========================================
export const VoiceScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate, goBack,
    isRecording, toggleRecording, voiceDuration, setVoiceDuration, runAiSimulation,
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

  const handleFinishVoice = () => {
    runAiSimulation();
    nav('ai_processing');
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Bé kể chuyện 🎤</Text>
        <View style={{ width: 32 }} />
      </View>

      {/* Mascot Speech Bubble */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: '#EFF6FF', borderRadius: radius.md, borderWidth: 1.5, borderColor: '#BFDBFE', padding: 12, marginVertical: 6 }}>
        <Text style={{ fontSize: 32 }}>🦕</Text>
        <Text style={{ fontSize: 12, color: '#1E40AF', flex: 1, fontWeight: '700', lineHeight: 16 }}>
          "Con có thể kể bất cứ điều gì con thấy trong bức tranh nhé!" 🌈
        </Text>
      </View>

      {/* Child Drawing Mini Card */}
      <View style={{ alignItems: 'center', marginVertical: 8 }}>
        <Image
          source={require('../../assets/images/photo_cat_paper.png')}
          style={{ width: 140, height: 100, borderRadius: 10, resizeMode: 'cover', borderWidth: 2, borderColor: '#FDE68A' }}
        />
      </View>

      {/* Giant 3D Pulsing Microphone Button */}
      <View style={{ alignItems: 'center', marginVertical: 12 }}>
        <PulseGlow>
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={toggleRecording}
            style={{
              width: 90,
              height: 90,
              borderRadius: 45,
              backgroundColor: isRecording ? '#EF4444' : '#2563EB',
              alignItems: 'center',
              justifyContent: 'center',
              borderWidth: 4,
              borderColor: isRecording ? '#FEE2E2' : '#DBEAFE',
              borderBottomWidth: 6,
              borderBottomColor: isRecording ? '#B91C1C' : '#1D4ED8',
              ...shadows.card,
            }}
          >
            <Ionicons name={isRecording ? 'pause' : 'mic'} size={42} color="#FFFFFF" />
          </TouchableOpacity>
        </PulseGlow>

        {/* Live Audio Visualizer Wave */}
        <View style={{ marginTop: 10, alignItems: 'center' }}>
          <LiveWaveBars isPlaying={isRecording} />
          <Text style={{ fontSize: 18, fontWeight: '900', color: colors.textHeading, marginTop: 4, letterSpacing: 1 }}>
            {formatTime(voiceDuration || 15)}
          </Text>
        </View>
      </View>

      {/* 2 Action Buttons */}
      <View style={{ flexDirection: 'row', gap: 10, marginTop: 4 }}>
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={toggleRecording}
          style={{
            flex: 1,
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            backgroundColor: '#F1F5F9',
            borderRadius: radius.md,
            paddingVertical: 12,
            borderWidth: 1,
            borderColor: colors.line,
          }}
        >
          <Ionicons name="refresh" size={16} color="#475569" />
          <Text style={{ fontSize: 12, fontWeight: '800', color: '#475569' }}>Kể lại</Text>
        </TouchableOpacity>

        <TouchableOpacity
          activeOpacity={0.88}
          onPress={handleFinishVoice}
          style={{
            flex: 1.5,
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            backgroundColor: '#2563EB',
            borderRadius: radius.md,
            paddingVertical: 12,
            borderBottomWidth: 3,
            borderBottomColor: '#1D4ED8',
          }}
        >
          <Text style={{ fontSize: 13, fontWeight: '900', color: '#FFFFFF' }}>Xong rồi →</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

// ===================== STYLES =====================
const styles = StyleSheet.create({
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
  screenHeaderTitle: {
    fontSize: 15,
    fontWeight: '900',
    color: colors.textHeading,
  },
  skipBtn: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textLight,
  },
  backBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.lineSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headingBox: {
    alignItems: 'center',
    marginVertical: 4,
  },
  headingTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: colors.textHeading,
    textAlign: 'center',
    marginBottom: 4,
    lineHeight: 24,
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
    marginVertical: 8,
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
  bellBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarBorder: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: colors.blueSoft,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.blue,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
    marginTop: 4,
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
});


// Flow 2 Screens
// PreviewResultScreen implementation
// AdultConfirmScreen Gate B handover prompt
// ChildTransitionScreen kid mode animation flow
// ChildGuideScreen visual story walkthrough
// ChildStepsScreen step-by-step guidance cards
