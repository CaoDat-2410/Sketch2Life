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
  KeyboardAvoidingView,
  Platform,
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
import type { ChildLearningProfileInput } from '../demo/api';

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

const PROFILE_INTERESTS = [
  ['ANIMAL_BUTTERFLY', 'Bướm'],
  ['ANIMAL_GENERIC', 'Động vật'],
  ['ANIMAL_MOVEMENT', 'Chuyển động'],
  ['PLANT_FLOWER', 'Hoa'],
  ['PLANT_STRUCTURE', 'Cây và lá'],
  ['SUN_LIGHT', 'Mặt trời, ánh sáng'],
  ['NATURE_OBSERVATION', 'Thiên nhiên'],
  ['SCIENCE_OBSERVATION', 'Khám phá khoa học'],
  ['COUNTING_NUMBER', 'Số và đếm'],
  ['LANGUAGE_PRINT', 'Chữ và kể chuyện'],
] as const;

const PROFILE_READINESS = [
  ['READY_SEARCH_PARTLY_HIDDEN', 'Tìm vật bị che một phần'],
  ['READY_STABLE_SEATED_TRANSFER', 'Ngồi vững, đặt vật vào hộp'],
  ['READY_FOLLOWS_WASH_SEQUENCE', 'Làm theo trình tự rửa tay'],
  ['READY_NOTICES_SMALL_SPILL', 'Nhìn thấy và lau vết nước'],
  ['READY_CARRIES_SMALL_CONTAINER', 'Mang cốc nhỏ an toàn'],
  ['READY_CONTROLLED_TWO_HAND_POUR', 'Rót bằng hai tay có kiểm soát'],
  ['READY_PINCH_AND_ALIGN_BUTTON', 'Cài nút lớn bằng hai ngón'],
  ['READY_CARRIES_PLACE_SETTING', 'Mang và sắp bàn ăn'],
  ['READY_MATCHES_IDENTICAL_COLOR', 'Ghép màu giống nhau'],
  ['READY_TRIPOD_OR_FUNCTIONAL_GRIP', 'Cầm bút và tô vùng rộng'],
  ['READY_HANDLES_PLANT_SAMPLE', 'Cầm và quan sát mẫu cây'],
  ['READY_RECORDS_CHANGES_OVER_TIME', 'Theo dõi thay đổi theo thời gian'],
  ['READY_PLACE_VALUE_TO_THOUSANDS', 'Biểu diễn số đến hàng nghìn'],
  ['READY_IDENTIFIES_NOUN_VERB', 'Nhận biết danh từ và động từ'],
  ['READY_ESTIMATES_SHORT_TASK', 'Ước lượng việc 10–20 phút'],
  ['READY_TABLE_AND_BAR_GRAPH', 'Đọc bảng và biểu đồ cột'],
  ['READY_COMPARE_OBSERVABLE_TRAITS', 'So sánh đặc điểm nhìn thấy'],
  ['READY_MODELS_LIGHT_AND_SHADOW', 'Khám phá ánh sáng và bóng'],
  ['READY_DISTINGUISHES_CLAIM_EVIDENCE', 'Phân biệt ý kiến và dữ kiện'],
  ['READY_MANAGES_RESEARCH_MILESTONE', 'Hoàn thành mốc nghiên cứu'],
] as const;

const PROFILE_MATERIALS = [
  ['GMAT-0004-PRIMARY', 'Khăn voan và bóng vải'],
  ['GMAT-0004-SUBSTITUTE', 'Khăn cotton và thú vải'],
  ['GMAT-0016-PRIMARY', 'Bát silicone và bóng vải'],
  ['GMAT-0016-SUBSTITUTE', 'Hộp nhựa và tất cuộn'],
  ['GMAT-0019-PRIMARY', 'Chậu thấp, xà phòng, khăn'],
  ['GMAT-0019-SUBSTITUTE', 'Bồn rửa và khăn riêng'],
  ['GMAT-0020-PRIMARY', 'Khay, nước và khăn cotton'],
  ['GMAT-0020-SUBSTITUTE', 'Tấm lót, cốc đo, vải'],
  ['GMAT-0023-PRIMARY', 'Cây không độc, ca nhỏ, khay'],
  ['GMAT-0023-SUBSTITUTE', 'Rau thơm và cốc rót'],
  ['GMAT-0026-PRIMARY', 'Bình quai và viên gỗ lớn'],
  ['GMAT-0026-SUBSTITUTE', 'Cốc quai và khay nhựa'],
  ['GMAT-0030-PRIMARY', 'Khung cài nút lớn'],
  ['GMAT-0030-SUBSTITUTE', 'Áo khoác có nút lớn'],
  ['GMAT-0033-PRIMARY', 'Bộ đồ ăn và khăn vải'],
  ['GMAT-0033-SUBSTITUTE', 'Bộ đồ ăn nhựa và bìa'],
  ['GMAT-0039-PRIMARY', 'Bảng màu và thảm xám'],
  ['GMAT-0039-SUBSTITUTE', 'Thẻ màu ép plastic'],
  ['GMAT-0046-PRIMARY', 'Khung hình và bút chì màu'],
  ['GMAT-0046-SUBSTITUTE', 'Khuôn nhựa và bút sáp'],
  ['GMAT-0055-PRIMARY', 'Cây rau, kính lúp, thẻ cây'],
  ['GMAT-0055-SUBSTITUTE', 'Hành lá có rễ, kính lúp'],
  ['GMAT-0058-PRIMARY', 'Hộp trong, nước, đá, nhiệt kế'],
  ['GMAT-0058-SUBSTITUTE', 'Bát inox, đá, nhiệt kế'],
  ['GMAT-0061-PRIMARY', 'Bộ stamp game và thẻ phép tính'],
  ['GMAT-0061-SUBSTITUTE', 'Thẻ hàng và khay màu'],
  ['GMAT-0067-PRIMARY', 'Ký hiệu ngữ pháp và thẻ câu'],
  ['GMAT-0067-SUBSTITUTE', 'Ký hiệu giấy và phong bì đáp án'],
  ['GMAT-0074-PRIMARY', 'Bảng tuần, thẻ việc, đồng hồ'],
  ['GMAT-0074-SUBSTITUTE', 'Lịch giấy và đồng hồ bếp'],
  ['GMAT-0085-PRIMARY', 'Phiếu dữ liệu và giấy biểu đồ'],
  ['GMAT-0085-SUBSTITUTE', 'Thẻ dữ liệu tổng hợp'],
  ['GMAT-0087-PRIMARY', 'Thẻ ảnh và khóa phân loại'],
  ['GMAT-0087-SUBSTITUTE', 'Đồ vật gia dụng an toàn'],
  ['GMAT-0091-PRIMARY', 'Đèn LED, quả cầu và phiếu ghi'],
  ['GMAT-0091-SUBSTITUTE', 'Đèn pin, bóng bàn, băng giấy'],
  ['GMAT-0097-PRIMARY', 'Nguồn in và phiếu lập luận'],
  ['GMAT-0097-SUBSTITUTE', 'Bài đọc và giấy ba cột'],
  ['GMAT-0099-PRIMARY', 'Planner, nguồn và vật liệu trình bày'],
  ['GMAT-0099-SUBSTITUTE', 'Bìa hồ sơ, lịch và tài liệu in'],
] as const;

const PROFILE_PROGRESS = [
  { activity_id: 'ACT-0055', objective_id: 'OBJ_SCIENTIFIC_OBSERVATION', label: 'Quan sát cấu tạo cây' },
  { activity_id: 'ACT-0058', objective_id: 'OBJ_SCIENTIFIC_INQUIRY', label: 'Khám phá vòng tuần hoàn nước' },
  { activity_id: 'ACT-0091', objective_id: 'OBJ_SCIENTIFIC_OBSERVATION', label: 'Quan sát ánh sáng và bóng' },
] as const;

const PROFILE_SUPPORTS = [
  ['HANDS_ON', 'Thích tự tay thao tác'],
  ['MOVEMENT', 'Thích hoạt động có vận động'],
  ['VISUAL_SEQUENCE', 'Hợp với các bước trực quan'],
  ['OBSERVATION', 'Thích quan sát, khám phá'],
] as const;

const PROFILE_SUPERVISION = [
  ['NONE', 'Không có người lớn giám sát'],
  ['NEARBY', 'Người lớn ở gần'],
  ['DIRECT', 'Người lớn hướng dẫn trực tiếp'],
] as const;

const ChoiceChip: React.FC<{
  label: string;
  selected: boolean;
  disabled?: boolean;
  onPress: () => void;
}> = ({ label, selected, disabled, onPress }) => (
  <TouchableOpacity
    accessibilityRole="checkbox"
    accessibilityState={{ checked: selected, disabled: Boolean(disabled) }}
    onPress={onPress}
    disabled={disabled}
    style={{
      borderRadius: 18,
      borderWidth: 1,
      borderColor: selected ? '#2563EB' : '#CBD5E1',
      backgroundColor: selected ? '#DBEAFE' : '#FFFFFF',
      opacity: disabled ? 0.45 : 1,
      paddingHorizontal: 11,
      paddingVertical: 8,
    }}
  >
    <Text style={{ color: selected ? '#1D4ED8' : '#475569', fontSize: 12, fontWeight: '700' }}>
      {selected ? '✓ ' : ''}{label}
    </Text>
  </TouchableOpacity>
);

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
          Sketch2Life giúp hiểu chủ đề trong tranh và gợi ý hoạt động ngoài màn hình phù hợp với độ tuổi.
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
          <Text style={styles.valuePropText}>Khám phá chủ đề từ tranh vẽ và lời kể</Text>
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
            accessibilityRole="button"
            accessibilityLabel="Tạo câu chuyện mới"
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
          <Text style={styles.sectionTitle}>Câu chuyện mẫu</Text>
          <TouchableOpacity accessibilityRole="button" accessibilityLabel="Xem các câu chuyện mẫu" onPress={() => nav('story_preview')}>
            <Text style={styles.sectionLink}>Xem tất cả &gt;</Text>
          </TouchableOpacity>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.recentStoriesRow}>
          {/* Card 1: Rainbow Fish — BounceIn with delay 0 */}
          <BounceInView delay={0} style={styles.storyCard}>
            <TouchableOpacity accessibilityRole="button" accessibilityLabel="Mở câu chuyện mẫu Chú cá cầu vồng" activeOpacity={0.88} onPress={() => nav('story_preview')} style={{ flex: 1 }}>
              <RainbowFishArtwork height={85} />
              <Text numberOfLines={1} style={styles.storyCardTitle}>Chú cá cầu vồng và đại dương rực rỡ</Text>
              <Text style={styles.storyCardDate}>12 Tháng 4, 2025</Text>
            </TouchableOpacity>
          </BounceInView>

          {/* Card 2: Robot — BounceIn with delay 150ms */}
          <BounceInView delay={150} style={styles.storyCard}>
            <TouchableOpacity accessibilityRole="button" accessibilityLabel="Mở câu chuyện mẫu Robot khám phá thiên nhiên" activeOpacity={0.88} onPress={() => nav('story_preview')} style={{ flex: 1 }}>
              <StoryRobotArtwork height={85} />
              <Text numberOfLines={1} style={styles.storyCardTitle}>Robot khám phá thiên nhiên</Text>
              <Text style={styles.storyCardDate}>8 Tháng 4, 2025</Text>
            </TouchableOpacity>
          </BounceInView>
        </ScrollView>

        {/* Today's Recommended Activity */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Hoạt động mẫu hôm nay</Text>
        </View>

        <BounceInView delay={300}>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Mở hoạt động mẫu Cùng trồng một hạt mầm"
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
        <TouchableOpacity style={styles.navItem} onPress={() => nav('profile')}>
          <Ionicons name="settings-outline" size={22} color={colors.textLight} />
          <Text style={styles.navText}>Hồ sơ</Text>
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
    selectedChildLearningProfile,
    updateSelectedChildLearningProfile,
    resetSelectedChildLearningProfile,
    beginWorkflow,
    workflowBusy,
    sessionState,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const [profileMaterialQuery, setProfileMaterialQuery] = useState('');
  const profile = selectedChildLearningProfile;
  const progressConfirmedBy = profile?.profile_declared_by || 'CAREGIVER';
  const profileEditable = sessionState === 'NOT_STARTED' || sessionState === 'FEEDBACK_RECORDED';
  const profileRequiresAdultInputs = Boolean(
    profile && (profile.readiness_ids === null || profile.available_material_option_ids === null),
  );
  const visibleProfileMaterials = PROFILE_MATERIALS.filter(([id, label]) => (
    `${id} ${label}`.toLocaleLowerCase().includes(profileMaterialQuery.trim().toLocaleLowerCase())
  )).slice(0, 10);

  const toggleProfileConcept = (field: 'interests' | 'dislikes', conceptId: string) => {
    const currentValues = profile?.[field] || [];
    const updated = currentValues.includes(conceptId)
      ? currentValues.filter((item) => item !== conceptId)
      : [...currentValues, conceptId];
    const opposite = field === 'interests' ? 'dislikes' : 'interests';
    updateSelectedChildLearningProfile({
      [field]: updated,
      [opposite]: (profile?.[opposite] || []).filter((item) => item !== conceptId),
    });
  };

  const toggleProfileProgress = (item: (typeof PROFILE_PROGRESS)[number]) => {
    const progress = profile?.adult_confirmed_progress || [];
    const exists = progress.some((entry) => entry.activity_id === item.activity_id);
    updateSelectedChildLearningProfile({
      adult_confirmed_progress: exists
        ? progress.filter((entry) => entry.activity_id !== item.activity_id)
        : [...progress, {
          activity_id: item.activity_id,
          objective_id: item.objective_id,
          confirmed_at: new Date().toISOString().slice(0, 10),
          confirmed_by: progressConfirmedBy,
        }],
    });
  };

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
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Hồ sơ của bé</Text>
        <View style={{ width: 48 }} />
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

      <View style={{ marginTop: 18, borderWidth: 1, borderColor: '#BFDBFE', borderRadius: 18, padding: 16, backgroundColor: '#F8FBFF' }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: '#172554' }}>Hồ sơ thử nghiệm cho bé</Text>
            <Text style={{ fontSize: 12, lineHeight: 17, color: '#64748B', marginTop: 4 }}>
              Chỉ giữ trong phiên ứng dụng hiện tại; chưa lưu lâu dài. Các lựa chọn chỉ ảnh hưởng bộ gợi ý Montessori, không huấn luyện hay gọi Qwen thêm.
            </Text>
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Xóa hồ sơ thử nghiệm"
            onPress={resetSelectedChildLearningProfile}
            disabled={!profileEditable || !profile}
            style={{ padding: 8, opacity: profileEditable && profile ? 1 : 0.4 }}
          >
            <Text style={{ color: '#B91C1C', fontSize: 12, fontWeight: '800' }}>Xóa thử</Text>
          </TouchableOpacity>
        </View>

        {profile && (
          <Text style={{ color: '#64748B', fontSize: 11, lineHeight: 16, marginTop: 8 }}>
            Khai báo bởi {profile.profile_declared_by === 'CAREGIVER' ? 'cha mẹ/người chăm sóc' : 'Guide'} · cập nhật {new Date(profile.profile_recorded_at).toLocaleString('vi-VN')} · tự xóa khi đóng ứng dụng.
          </Text>
        )}

        {!profileEditable ? (
          <Text style={{ color: '#B45309', fontSize: 13, marginTop: 12 }}>
            Hồ sơ bị khóa trong lúc đang có hoạt động. Có thể chỉnh lại sau khi kết thúc phiên.
          </Text>
        ) : (
          <>
            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 16, marginBottom: 8 }}>Mức người lớn có thể giám sát</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
              {PROFILE_SUPERVISION.map(([id, label]) => (
                <ChoiceChip
                  key={id}
                  label={label}
                  selected={profile ? profile.adult_supervision_available === id : id === 'NEARBY'}
                  onPress={() => updateSelectedChildLearningProfile({ adult_supervision_available: id })}
                />
              ))}
            </View>

            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 16, marginBottom: 8 }}>Sở thích bé đã thể hiện</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
              {PROFILE_INTERESTS.map(([id, label]) => (
                <ChoiceChip key={`interest-${id}`} label={label} selected={Boolean(profile?.interests.includes(id))} onPress={() => toggleProfileConcept('interests', id)} />
              ))}
            </View>
            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 14, marginBottom: 8 }}>Chủ đề bé không thích / muốn tránh</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
              {PROFILE_INTERESTS.map(([id, label]) => (
                <ChoiceChip key={`dislike-${id}`} label={label} selected={Boolean(profile?.dislikes.includes(id))} onPress={() => toggleProfileConcept('dislikes', id)} />
              ))}
            </View>

            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 14, marginBottom: 7 }}>Tiến trình người lớn đã xác nhận</Text>
            <Text style={{ color: '#64748B', fontSize: 11, marginBottom: 7 }}>Chọn người lớn khai báo hồ sơ này; tiến trình bên dưới cũng ghi riêng người xác nhận và ngày xác nhận.</Text>
            <View style={{ flexDirection: 'row', gap: 8, marginBottom: 8 }}>
              {(['CAREGIVER', 'GUIDE'] as const).map((source) => (
                <ChoiceChip key={source} label={source === 'CAREGIVER' ? 'Cha mẹ/người chăm sóc' : 'Guide'} selected={progressConfirmedBy === source} onPress={() => updateSelectedChildLearningProfile({ profile_declared_by: source })} />
              ))}
            </View>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
              {PROFILE_PROGRESS.map((item) => (
                <ChoiceChip key={item.activity_id} label={item.label} selected={Boolean(profile?.adult_confirmed_progress.some((entry) => entry.activity_id === item.activity_id))} onPress={() => toggleProfileProgress(item)} />
              ))}
            </View>
            {profile?.adult_confirmed_progress.map((entry) => {
              const milestone = PROFILE_PROGRESS.find((item) => item.activity_id === entry.activity_id);
              return milestone ? (
                <Text key={`${entry.activity_id}-${entry.objective_id}`} style={{ color: '#64748B', fontSize: 11, marginTop: 4 }}>
                  {milestone.label} · {entry.confirmed_by === 'CAREGIVER' ? 'Cha mẹ/người chăm sóc' : 'Guide'} · {entry.confirmed_at}
                </Text>
              ) : null;
            })}
            <Text style={{ color: '#64748B', fontSize: 11, marginTop: 5 }}>Ngày và người xác nhận được ghi tự động; chỉ dùng tiến trình do người lớn xác nhận, không coi việc hoàn thành đơn thuần là đã thành thạo.</Text>

            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 14, marginBottom: 8 }}>Sẵn sàng hiện tại (điều kiện lọc)</Text>
            <ChoiceChip
              label={profile?.readiness_ids === null || !profile ? 'Chọn mục người lớn đã xác nhận' : `Đã chọn ${profile.readiness_ids.length} mục sẵn sàng`}
              selected={Boolean(profile && profile.readiness_ids !== null)}
              onPress={() => updateSelectedChildLearningProfile({ readiness_ids: profile?.readiness_ids === null || !profile ? [] : null })}
            />
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 8 }}>
              {PROFILE_READINESS.map(([id, label]) => (
                <ChoiceChip key={id} label={label} disabled={profile?.readiness_ids === null || !profile} selected={Boolean(profile?.readiness_ids?.includes(id))} onPress={() => {
                  const values = profile?.readiness_ids || [];
                  updateSelectedChildLearningProfile({ readiness_ids: values.includes(id) ? values.filter((value) => value !== id) : [...values, id] });
                }} />
              ))}
            </View>

            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 14, marginBottom: 8 }}>Vật liệu đang có (điều kiện lọc)</Text>
            <ChoiceChip
              label={profile?.available_material_option_ids === null || !profile ? 'Chọn vật liệu người lớn xác nhận đang có' : `Đã chọn ${profile.available_material_option_ids.length} vật liệu`}
              selected={Boolean(profile && profile.available_material_option_ids !== null)}
              onPress={() => updateSelectedChildLearningProfile({ available_material_option_ids: profile?.available_material_option_ids === null || !profile ? [] : null })}
            />
            <TextInput
              value={profileMaterialQuery}
              onChangeText={setProfileMaterialQuery}
              placeholder="Tìm trong 40 lựa chọn vật liệu…"
              accessibilityLabel="Tìm vật liệu trong catalog"
              style={{ borderWidth: 1, borderColor: '#CBD5E1', borderRadius: 10, backgroundColor: '#FFFFFF', paddingHorizontal: 12, paddingVertical: 9, marginTop: 9, fontSize: 12 }}
            />
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 8 }}>
              {visibleProfileMaterials.map(([id, label]) => (
                <ChoiceChip key={id} label={label} disabled={profile?.available_material_option_ids === null || !profile} selected={Boolean(profile?.available_material_option_ids?.includes(id))} onPress={() => {
                  const values = profile?.available_material_option_ids || [];
                  updateSelectedChildLearningProfile({ available_material_option_ids: values.includes(id) ? values.filter((value) => value !== id) : [...values, id] });
                }} />
              ))}
            </View>
            <Text style={{ color: '#64748B', fontSize: 11, marginTop: 5 }}>Đang hiện {visibleProfileMaterials.length} kết quả; tìm theo tên hoặc mã GMAT. Danh sách trống nghĩa là không có hoạt động nào được xác nhận là đủ vật liệu.</Text>

            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 14, marginBottom: 8 }}>Cách học người lớn đã chọn cho bé</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
              {PROFILE_SUPPORTS.map(([id, label]) => (
                <ChoiceChip key={id} label={label} selected={Boolean(profile?.learning_support_ids.includes(id))} onPress={() => {
                  const values = profile?.learning_support_ids || [];
                  updateSelectedChildLearningProfile({ learning_support_ids: values.includes(id) ? values.filter((value) => value !== id) : [...values, id] as ChildLearningProfileInput['learning_support_ids'] });
                }} />
              ))}
            </View>
            {profileRequiresAdultInputs && (
              <Text style={{ color: '#B45309', fontSize: 12, lineHeight: 18, marginTop: 14 }}>
                Để dùng profile an toàn, hãy mở cả hai bộ lọc và xác nhận readiness/vật liệu trước khi bắt đầu. Chọn rỗng là xác nhận hiện chưa có mục nào; hoạt động cần các mục đó sẽ không được gợi ý.
              </Text>
            )}
          </>
        )}
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
          disabled={!!workflowBusy || profileRequiresAdultInputs}
        />
      </View>
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
    isRecordingStarting,
    startRecording,
    stopRecording,
    cancelRecording,
    uploadNarration,
    workflowBusy,
    workflowNotice,
  } = useAppContext();
  const nav = onNavigate || navigate;

  const handlePickImage = async () => {
    await pickDrawingImage();
  };

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
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Quay lại"
          onPress={() => { if (isRecording || isRecordingStarting) void cancelRecording().then(goBack); else goBack(); }}
          style={styles.backBtn}
        >
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

      <View style={styles.actionGridRow}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={selectedDrawing ? 'Chọn ảnh khác' : 'Chọn ảnh'}
          activeOpacity={0.9}
          onPress={handlePickImage}
          style={[styles.halfBtn, { flex: 1, backgroundColor: colors.blue }]}
        >
          <Ionicons name="images" size={24} color={colors.white} />
          <Text style={styles.halfBtnText}>{selectedDrawing ? 'Chọn ảnh khác' : 'Chọn ảnh'}</Text>
        </TouchableOpacity>
      </View>

      <View style={{ marginTop: 14, padding: 14, borderRadius: 18, backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#DBEAFE' }}>
        <Text style={{ fontSize: 15, fontWeight: '900', color: colors.textHeading }}>Lời kể (không bắt buộc)</Text>
        <Text style={{ fontSize: 12, color: colors.textSoft, lineHeight: 17, marginTop: 4 }}>
          Ảnh là bắt buộc. Bạn có thể kể bằng giọng nói, nhập chữ hoặc bỏ qua lời kể.
        </Text>
        <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
          {([
            ['none', 'Không thêm'],
            ['text', 'Nhập chữ'],
            ['audio', 'Ghi âm'],
          ] as const).map(([mode, label]) => (
            <TouchableOpacity
              key={mode}
              accessibilityRole="radio"
              accessibilityLabel={label}
              accessibilityState={{ selected: narrationMode === mode }}
              disabled={Boolean(workflowBusy) || isRecording || isRecordingStarting}
              onPress={() => setNarrationMode(mode)}
              style={{ flex: 1, minHeight: 48, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: narrationMode === mode ? colors.blue : '#FFFFFF', borderWidth: 1, borderColor: narrationMode === mode ? colors.blue : '#CBD5E1' }}
            >
              <Text style={{ fontSize: 11, fontWeight: '800', color: narrationMode === mode ? colors.white : colors.textBody }}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {narrationMode === 'text' && (
          <TextInput
            value={narrationText}
            onChangeText={setNarrationText}
            editable={!workflowBusy && !isRecording && !isRecordingStarting}
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
              accessibilityRole="button"
              accessibilityLabel={isRecording ? 'Dừng ghi âm' : isRecordingStarting ? 'Đang mở micro' : 'Bắt đầu ghi âm'}
              accessibilityState={{ busy: isRecording || isRecordingStarting, disabled: isRecordingStarting }}
              disabled={isRecordingStarting}
              onPress={() => void (isRecording ? stopRecording() : startRecording())}
              style={{ minWidth: 180, minHeight: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: isRecording ? '#DC2626' : colors.greenDeep }}
            >
              <Text style={{ color: colors.white, fontWeight: '900' }}>
                {isRecording ? 'Dừng ghi âm' : isRecordingStarting ? 'Đang mở micro…' : 'Bắt đầu ghi âm'}
              </Text>
            </TouchableOpacity>
            <Text style={{ marginTop: 8, fontSize: 12, color: colors.textSoft }}>
              {selectedNarrationAudio ? `Đã có bản ghi (${Math.round((selectedNarrationAudio.durationMs || 0) / 1000)} giây)` : 'Có thể ghi tối đa 3 phút'}
            </Text>
          </View>
        )}
      </View>

      <Kid3DButton
        title={workflowBusy === 'Tải ảnh' ? 'Đang kiểm tra ảnh...' : workflowBusy === 'Tải lời kể' ? 'Đang lưu lời kể...' : 'Gửi ảnh & tiếp tục'}
        color="blue"
        size="lg"
        disabled={!selectedDrawing || !!workflowBusy || isRecording || isRecordingStarting || (narrationMode === 'text' && !narrationText.trim()) || (narrationMode === 'audio' && !selectedNarrationAudio)}
        onPress={async () => {
          const imageAlreadyAdmitted = admission?.decision === 'ADMITTED';
          if ((!imageAlreadyAdmitted && !(await uploadDrawing())) || !(await uploadNarration())) return;
          nav('ai_processing');
        }}
      />

      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginTop: 10 }}>{workflowNotice}</Text>}

      {/* Tips Box */}
      <View style={styles.tipsBox}>
        <Text style={styles.tipsHeading}>💡 Một số gợi ý:</Text>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Chọn ảnh rõ, đủ sáng và không quá 5 MB</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Chỉ dùng tranh vẽ, không dùng ảnh có khuôn mặt trẻ em</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Ảnh chỉ được dùng để tạo gợi ý trong phiên này</Text>
        </View>
      </View>
    </ScrollView>
    </KeyboardAvoidingView>
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
    isRecordingStarting,
    toggleRecording,
    voiceDuration,
    selectedNarrationAudio,
    cancelRecording,
    uploadNarration,
  } = useAppContext();
  const nav = onNavigate || navigate;

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleFinishVoice = async () => {
    if (isRecording || !selectedNarrationAudio) return;
    if (await uploadNarration()) nav('ai_processing');
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Quay lại"
          onPress={() => { if (isRecording || isRecordingStarting) void cancelRecording().then(goBack); else goBack(); }}
          style={styles.backBtn}
        >
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
          {isRecordingStarting ? 'Đang mở micro…' : `${isRecording ? 'Đang ghi âm...  ' : ''}${formatTime(voiceDuration)} / 03:00`}
        </Text>
      </View>

      {/* Recording Controls */}
      <View style={styles.recordControlsRow}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={isRecording ? 'Dừng ghi âm' : isRecordingStarting ? 'Đang mở micro' : selectedNarrationAudio ? 'Ghi lại lời kể' : 'Bắt đầu kể'}
          accessibilityState={{ busy: isRecording || isRecordingStarting, disabled: isRecordingStarting }}
          disabled={isRecordingStarting}
          onPress={toggleRecording}
          style={styles.mainRecordBtn}
        >
          <Ionicons name={isRecording ? 'stop' : 'mic'} size={28} color={colors.white} />
        </TouchableOpacity>

        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Hủy ghi âm"
          onPress={() => void cancelRecording().then(goBack)}
          style={styles.auxRecordBtn}
        >
          <Ionicons name="close" size={20} color={colors.textLight} />
          <Text style={styles.auxRecordText}>Hủy</Text>
        </TouchableOpacity>
      </View>
      {isRecordingStarting && (
        <Text style={styles.recordingLabel}>Đang xin quyền và mở micro…</Text>
      )}
      {isRecording && (
        <Text style={[styles.recordingLabel, { color: '#EF4444', fontWeight: '700' }]}>
          Đang ghi âm... Chạm nút đỏ để dừng
        </Text>
      )}
      {!isRecording && !isRecordingStarting && !selectedNarrationAudio && (
        <Text style={styles.recordingLabel}>Chạm nút micro để bắt đầu kể</Text>
      )}
      {!isRecording && selectedNarrationAudio && (
        <View style={styles.actionBottom}>
          <Kid3DButton
            title="Dùng lời kể này"
            color="blue"
            size="lg"
            onPress={() => void handleFinishVoice()}
          />
        </View>
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
    width: 48,
    height: 48,
    borderRadius: 24,
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
