import React, { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Image, ImageBackground, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFonts } from 'expo-font';
import { colors, radius, shadows } from '../theme';
import { CatDrawingArtwork, ChildAvatarImage, LogoSketch2Life } from '../components/ArtworkCards';
import type { ScreenId } from '../types';
import { useAppContext } from '../context/AppContext';
import { ParentFlowHeader } from '../components/ParentFlowShell';
import type { ChildProfile } from '../services/api.types';

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

const EntryHeader: React.FC<{
  title: string;
  onBack?: () => void;
  action?: React.ReactNode;
}> = ({ title, onBack, action }) => (
  <ParentFlowHeader title={title} onBack={onBack} action={action} />
);

// Reuse the project's existing child-friendly illustrations instead of
// drawing generic geometric placeholders for the topic cards.
const topicArtSources = {
  animals: require('../../assets/images/topics/topic-animals.png'),
  nature: require('../../assets/images/topics/topic-nature.png'),
  family: require('../../assets/images/topics/topic-family.png'),
  vehicles: require('../../assets/images/topics/topic-vehicles.png'),
  space: require('../../assets/images/topics/topic-space.png'),
  free: require('../../assets/images/topics/topic-free.png'),
} as const;

// Small, transparent doodles cropped from the supplied hand-drawn sprite sheet.
// They sit behind the content at low opacity so the screen stays light and readable.
const topicDecorSources = {
  sun: require('../../assets/images/topic-decor/topic-decor-sun.png'),
  cloud: require('../../assets/images/topic-decor/topic-decor-cloud.png'),
  heart: require('../../assets/images/topic-decor/topic-decor-heart.png'),
  star: require('../../assets/images/topic-decor/topic-decor-star.png'),
  leaves: require('../../assets/images/topic-decor/topic-decor-leaves.png'),
} as const;

const dashboardStoryHero = require('../../assets/images/dashboard/dashboard_story_hero.png');

const AgeLabel: React.FC<{ age: number }> = ({ age }) => (
  <Text style={styles.ageLabel}>{age} tuổi</Text>
);

const useReducedMotionPreference = () => {
  const [reducedMotion, setReducedMotion] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    AccessibilityInfo.isReduceMotionEnabled()
      .then((enabled) => {
        if (!active) return;
        setReducedMotion(enabled);
        setReady(true);
      })
      .catch(() => {
        if (active) setReady(true);
      });

    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReducedMotion);
    return () => {
      active = false;
      subscription.remove();
    };
  }, []);

  return { reducedMotion, motionPreferenceReady: ready };
};

const PrivacyNotice: React.FC = () => (
  <View style={styles.profileNoticeCard}>
    <View style={styles.profileNoticeIcon}>
      <Ionicons name="lock-closed-outline" size={18} color={colors.blueDeep} />
    </View>
    <Text style={styles.profileNoticeText}>Hồ sơ của con chỉ hiển thị với tài khoản phụ huynh này.</Text>
  </View>
);

const CrayonRainbow: React.FC = () => (
  <View pointerEvents="none" style={styles.profileRainbow}>
    <View style={[styles.profileRainbowArc, styles.profileRainbowOuter]} />
    <View style={[styles.profileRainbowArc, styles.profileRainbowMiddle]} />
    <View style={[styles.profileRainbowArc, styles.profileRainbowInner]} />
  </View>
);

const ChildProfileCard: React.FC<{
  child: ChildProfile;
  selected: boolean;
  onPress: () => void;
  entranceDelay: number;
  reducedMotion: boolean;
  motionPreferenceReady: boolean;
}> = ({ child, selected, onPress, entranceDelay, reducedMotion, motionPreferenceReady }) => {
  const entrance = useRef(new Animated.Value(0)).current;
  const pressScale = useRef(new Animated.Value(1)).current;
  const selectionProgress = useRef(new Animated.Value(selected ? 1 : 0)).current;
  const hasEntered = useRef(false);

  useEffect(() => {
    if (!motionPreferenceReady || hasEntered.current) return;
    hasEntered.current = true;
    if (reducedMotion) {
      entrance.setValue(1);
      return;
    }
    Animated.timing(entrance, {
      toValue: 1,
      duration: 300,
      delay: entranceDelay,
      useNativeDriver: true,
    }).start();
  }, [entrance, entranceDelay, motionPreferenceReady, reducedMotion]);

  useEffect(() => {
    if (reducedMotion) {
      selectionProgress.setValue(selected ? 1 : 0);
      return;
    }
    Animated.timing(selectionProgress, {
      toValue: selected ? 1 : 0,
      duration: 180,
      useNativeDriver: false,
    }).start();
  }, [reducedMotion, selected, selectionProgress]);

  const cardBackground = selectionProgress.interpolate({
    inputRange: [0, 1],
    outputRange: ['#FFFDF7', '#F8FBFF'],
  });
  const cardBorder = selectionProgress.interpolate({
    inputRange: [0, 1],
    outputRange: ['#F0E3C9', '#8EC5FF'],
  });

  return (
    <Animated.View
      style={{
        opacity: entrance,
        transform: [{ translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [12, 0] }) }],
      }}
    >
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Mở hồ sơ ${child.name}`}
        accessibilityState={{ selected }}
        onPressIn={() => Animated.spring(pressScale, { toValue: 0.97, useNativeDriver: true, speed: 24, bounciness: 2 }).start()}
        onPressOut={() => Animated.spring(pressScale, { toValue: 1, useNativeDriver: true, speed: 20, bounciness: 8 }).start()}
        onPress={onPress}
      >
        <Animated.View style={[styles.profileCard, { backgroundColor: cardBackground, borderColor: cardBorder, transform: [{ scale: pressScale }] }]}>
          <View style={styles.avatarFrame}>
            <ChildAvatarImage childName={child.name} size={70} />
          </View>
          <View style={styles.profileMain}>
            <View style={styles.profileNameRow}>
              <Text style={styles.profileName}>{child.name}</Text>
              {selected && <Text style={styles.selectedBadge}>Đang chọn</Text>}
            </View>
            <AgeLabel age={child.age} />
            <Text style={styles.profileMeta}>{child.recentStoriesCount || 0} câu chuyện đã tạo</Text>
          </View>
          <Ionicons name="chevron-forward" size={21} color={colors.textLight} />
        </Animated.View>
      </Pressable>
    </Animated.View>
  );
};

const AddChildProfileButton: React.FC<{
  onPress: () => void;
  reducedMotion: boolean;
}> = ({ onPress, reducedMotion }) => {
  const pressScale = useRef(new Animated.Value(1)).current;
  const plusScale = useRef(new Animated.Value(1)).current;

  const pressIn = () => {
    if (reducedMotion) return;
    Animated.parallel([
      Animated.spring(pressScale, { toValue: 0.98, useNativeDriver: true, speed: 24, bounciness: 2 }),
      Animated.spring(plusScale, { toValue: 1.12, useNativeDriver: true, speed: 22, bounciness: 5 }),
    ]).start();
  };
  const pressOut = () => {
    if (reducedMotion) return;
    Animated.parallel([
      Animated.spring(pressScale, { toValue: 1, useNativeDriver: true, speed: 20, bounciness: 8 }),
      Animated.spring(plusScale, { toValue: 1, useNativeDriver: true, speed: 20, bounciness: 8 }),
    ]).start();
  };

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Thêm hồ sơ trẻ"
      onPressIn={pressIn}
      onPressOut={pressOut}
      onPress={onPress}
    >
      <Animated.View style={[styles.addProfileButton, { transform: [{ scale: pressScale }] }]}>
        <View style={styles.addProfileCopy}>
          <Animated.View style={{ transform: [{ scale: plusScale }] }}>
            <Ionicons name="add" size={34} color={colors.blueDeep} />
          </Animated.View>
          <Text style={styles.addProfileText}>Thêm hồ sơ trẻ</Text>
        </View>
        <CrayonRainbow />
      </Animated.View>
    </Pressable>
  );
};

/** Parent entry surface: owned child profiles, before starting a story run. */
export const ParentProfileListScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, childrenList, selectedChild, setSelectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const { reducedMotion, motionPreferenceReady } = useReducedMotionPreference();
  const headerEntrance = useRef(new Animated.Value(0)).current;
  const heroEntrance = useRef(new Animated.Value(0)).current;
  const hasStartedEntrance = useRef(false);
  useFonts({
    MaliBold: require('../../assets/fonts/Mali-Bold.ttf'),
    MaliSemiBold: require('../../assets/fonts/Mali-SemiBold.ttf'),
    ItimRegular: require('../../assets/fonts/Itim-Regular.ttf'),
  });

  useEffect(() => {
    if (!motionPreferenceReady || hasStartedEntrance.current) return;
    hasStartedEntrance.current = true;
    if (reducedMotion) {
      headerEntrance.setValue(1);
      heroEntrance.setValue(1);
      return;
    }
    Animated.stagger(70, [
      Animated.timing(headerEntrance, { toValue: 1, duration: 280, useNativeDriver: true }),
      Animated.timing(heroEntrance, { toValue: 1, duration: 320, useNativeDriver: true }),
    ]).start();
  }, [headerEntrance, heroEntrance, motionPreferenceReady, reducedMotion]);

  const openProfile = (child: (typeof childrenList)[number]) => {
    setSelectedChild(child);
    nav('profile_detail');
  };

  return (
    <ImageBackground
      source={require('../../assets/images/login/background_paper.png')}
      resizeMode="cover"
      style={styles.profileBackground}
      imageStyle={styles.profileBackgroundImage}
    >
      <View pointerEvents="none" style={styles.profileDoodleLayer}>
        <Ionicons name="sunny-outline" size={42} color={colors.yellowDeep} style={styles.profileDoodleSun} />
        <Ionicons name="star-outline" size={28} color={colors.blue} style={styles.profileDoodleStarLeft} />
        <Ionicons name="heart-outline" size={25} color={colors.coralDeep} style={styles.profileDoodleHeartRight} />
        <Ionicons name="sparkles-outline" size={20} color={colors.coralDeep} style={styles.profileDoodleTopRight} />
        <Ionicons name="leaf-outline" size={28} color={colors.greenDeep} style={styles.profileDoodleLeafBottomLeft} />
        <Ionicons name="leaf-outline" size={25} color={colors.greenDeep} style={styles.profileDoodleLeafBottomRight} />
        <Ionicons name="star-outline" size={24} color={colors.yellowDeep} style={styles.profileDoodleStarBottomRight} />
        <View style={styles.profileDoodleStrokeTop} />
        <View style={styles.profileDoodleStrokeBottom} />
      </View>
      <ScrollView contentContainerStyle={styles.profileContainer} showsVerticalScrollIndicator={false}>
        <Animated.View style={{ opacity: headerEntrance, transform: [{ translateY: headerEntrance.interpolate({ inputRange: [0, 1], outputRange: [-5, 0] }) }] }}>
          <View style={styles.profileTopBar}>
            <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.profileBackButton}>
              <Ionicons name="arrow-back" size={23} color={styles.profileInk.color} />
            </TouchableOpacity>
            <Text style={styles.profileTopTitle}>Hồ sơ của con</Text>
            <View style={styles.profileTopBarSpacer} />
          </View>
        </Animated.View>
        <Animated.View style={{ opacity: heroEntrance, transform: [{ translateY: heroEntrance.interpolate({ inputRange: [0, 1], outputRange: [8, 0] }) }] }}>
          <View style={styles.profileHero}>
            <Text style={styles.profilePageTitle}>Chọn hồ sơ để bắt đầu</Text>
            <View style={styles.profileTitleUnderline} />
            <Text style={styles.profilePageSubtitle}>Mỗi câu chuyện đều bắt đầu từ một họa sĩ nhỏ.</Text>
          </View>
        </Animated.View>

        <PrivacyNotice />

        <View style={styles.profileSectionHeader}>
          <View style={styles.profileSectionHeading}>
            <View>
              <Text style={styles.profileSectionTitle}>Hồ sơ đang có</Text>
              <View style={styles.profileSectionUnderline} />
            </View>
          </View>
          <Text style={styles.profileSectionCount}>{childrenList.length} hồ sơ</Text>
        </View>

      {childrenList.map((child, index) => (
        <ChildProfileCard
          key={child.id}
          child={child}
          selected={child.id === selectedChild.id}
          onPress={() => openProfile(child)}
          entranceDelay={Math.min(index, 9) * 65}
          reducedMotion={reducedMotion}
          motionPreferenceReady={motionPreferenceReady}
        />
      ))}

        <View style={styles.addProfileSection}>
          <AddChildProfileButton reducedMotion={reducedMotion} onPress={() => nav('profile_create')} />
        </View>

        <View style={styles.profileFooterNote}>
          <Ionicons name="information-circle-outline" size={16} color={colors.textSoft} />
          <Text style={styles.profileFooterNoteText}>Bạn có thể đổi hồ sơ bất cứ lúc nào.</Text>
        </View>
      </ScrollView>
    </ImageBackground>
  );
};

type ProfileFormMode = 'create' | 'edit';

/** Create/edit profile UI. Local state is intentionally used until the Parent profile API is connected. */
export const ParentProfileCreateScreen: React.FC<ScreenProps & { mode?: ProfileFormMode }> = ({ onNavigate, mode = 'create' }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    selectedAgeMonths,
    selectedChildLearningProfile,
    createChildProfile,
    updateChildProfile,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const isEdit = mode === 'edit';
  const [name, setName] = useState(isEdit ? selectedChild.name : '');
  const [ageMonths, setAgeMonths] = useState(String(isEdit ? selectedAgeMonths : 60));
  const [interestText, setInterestText] = useState(selectedChildLearningProfile?.interest_text || '');
  const [avoidText, setAvoidText] = useState(selectedChildLearningProfile?.avoid_text || '');
  const [adultParticipation, setAdultParticipation] = useState<'together' | 'independent' | ''>(
    selectedChildLearningProfile?.adult_participating === false ? 'independent' : selectedChildLearningProfile?.adult_participating ? 'together' : '',
  );
  const [learningSupportIds, setLearningSupportIds] = useState<Array<'HANDS_ON' | 'MOVEMENT' | 'VISUAL_SEQUENCE' | 'OBSERVATION'>>(selectedChildLearningProfile?.learning_support_ids || []);
  const [errors, setErrors] = useState<{ name?: string; age?: string }>({});

  const supportOptions = [
    ['HANDS_ON', 'Thích tự tay thao tác'],
    ['MOVEMENT', 'Thích vận động'],
    ['VISUAL_SEQUENCE', 'Hợp với hướng dẫn trực quan'],
  ] as const;
  const ageOptions = [
    ['3–4 tuổi', 48],
    ['5–6 tuổi', 72],
    ['7–8 tuổi', 96],
    ['9+ tuổi', 120],
  ] as const;

  const toggleSupport = (id: 'HANDS_ON' | 'MOVEMENT' | 'VISUAL_SEQUENCE' | 'OBSERVATION') => {
    setLearningSupportIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  };

  const submit = () => {
    const trimmedName = name.trim();
    const parsedAge = Number(ageMonths);
    const nextErrors: { name?: string; age?: string } = {};
    if (!trimmedName) nextErrors.name = 'Hãy nhập tên hiển thị của bé.';
    else if (trimmedName.length > 40) nextErrors.name = 'Tên hiển thị tối đa 40 ký tự.';
    if (!Number.isInteger(parsedAge) || parsedAge < 36 || parsedAge > 155) {
      nextErrors.age = 'Tuổi của hồ sơ cần nằm trong khoảng 36–155 tháng.';
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    const payload = {
      name: trimmedName,
      ageMonths: parsedAge,
      interestText,
      avoidText,
      adultParticipating: adultParticipation === '' ? null : adultParticipation === 'together',
      learningSupportIds,
    };
    if (isEdit) updateChildProfile(selectedChild.id, payload);
    else createChildProfile(payload);
    nav('profile_detail');
  };

  return (
    <ImageBackground
      source={require('../../assets/images/login/background_paper.png')}
      resizeMode="cover"
      style={styles.profileBackground}
      imageStyle={styles.profileBackgroundImage}
    >
      <View pointerEvents="none" style={styles.profileDoodleLayer}>
        <Ionicons name="sunny-outline" size={42} color={colors.yellowDeep} style={styles.profileDoodleSun} />
        <Ionicons name="heart-outline" size={25} color={colors.coralDeep} style={styles.profileDoodleHeartRight} />
        <Ionicons name="star-outline" size={26} color={colors.blue} style={styles.profileDoodleStarLeft} />
        <Ionicons name="leaf-outline" size={28} color={colors.greenDeep} style={styles.profileDoodleLeafBottomRight} />
      </View>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.profileFormKeyboard}>
        <ScrollView contentContainerStyle={styles.profileFormContainer} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={styles.profileTopBar}>
            <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.profileBackButton}>
              <Ionicons name="arrow-back" size={23} color={styles.profileInk.color} />
            </TouchableOpacity>
            <Text style={styles.profileTopTitle}>{isEdit ? 'Chỉnh sửa hồ sơ' : 'Thêm hồ sơ trẻ'}</Text>
            <View style={styles.profileTopBarSpacer} />
          </View>

          <View style={styles.profileFormIntro}>
            <View style={styles.profileFormIcon}><Ionicons name={isEdit ? 'pencil-outline' : 'sparkles-outline'} size={24} color={colors.blueDeep} /></View>
            <Text style={styles.profileFormTitle}>{isEdit ? 'Cập nhật một chút nhé' : 'Bắt đầu với họa sĩ nhỏ'}</Text>
            <Text style={styles.profileFormSubtitle}>Thông tin này giúp câu chuyện phù hợp hơn với bé. Bạn có thể thay đổi sau.</Text>
          </View>

          <View style={styles.profileFormCard}>
            <Text style={styles.profileFormLabel}>Tên hiển thị</Text>
            <View style={[styles.profileFormInput, errors.name && styles.profileFormInputError]}>
              <Ionicons name="person-outline" size={20} color={colors.textSoft} />
              <TextInput
                accessibilityLabel="Tên hiển thị của bé"
                value={name}
                onChangeText={(value) => { setName(value); if (errors.name) setErrors((current) => ({ ...current, name: undefined })); }}
                placeholder="Ví dụ: An, Bảo..."
                placeholderTextColor="#8B9AB0"
                maxLength={40}
                style={styles.profileFormTextInput}
              />
            </View>
            {errors.name && <Text accessibilityRole="alert" style={styles.profileFormError}>{errors.name}</Text>}

            <Text style={[styles.profileFormLabel, styles.profileFormLabelSpaced]}>Tuổi của bé (tháng)</Text>
            <View style={[styles.profileFormInput, errors.age && styles.profileFormInputError]}>
              <Ionicons name="calendar-outline" size={20} color={colors.textSoft} />
              <TextInput
                accessibilityLabel="Tuổi của bé theo tháng"
                value={ageMonths}
                onChangeText={(value) => { setAgeMonths(value.replace(/[^0-9]/g, '')); if (errors.age) setErrors((current) => ({ ...current, age: undefined })); }}
                keyboardType="number-pad"
                placeholder="Từ 36 đến 155 tháng"
                placeholderTextColor="#8B9AB0"
                maxLength={3}
                style={styles.profileFormTextInput}
              />
            </View>
            {errors.age && <Text accessibilityRole="alert" style={styles.profileFormError}>{errors.age}</Text>}
            <View style={styles.profileAgeChips}>
              {ageOptions.map(([label, value]) => {
                const active = Number(ageMonths) >= value - 12 && Number(ageMonths) <= value + 11;
                return <Pressable key={label} accessibilityRole="button" onPress={() => setAgeMonths(String(value))} style={[styles.profileAgeChip, active && styles.profileAgeChipActive]}><Text style={[styles.profileAgeChipText, active && styles.profileAgeChipTextActive]}>{label}</Text></Pressable>;
              })}
            </View>

            <Text style={[styles.profileFormLabel, styles.profileFormLabelSpaced]}>Bé thích điều gì?</Text>
            <TextInput
              accessibilityLabel="Sở thích của bé"
              value={interestText}
              onChangeText={(value) => setInterestText(value.slice(0, 240))}
              placeholder="Ví dụ: vẽ con vật, chơi ngoài trời..."
              placeholderTextColor="#8B9AB0"
              multiline
              maxLength={240}
              style={[styles.profileFormInput, styles.profileFormMultiline]}
            />

            <Text style={[styles.profileFormLabel, styles.profileFormLabelSpaced]}>Điều cần lưu ý</Text>
            <TextInput
              accessibilityLabel="Điều cần lưu ý về bé"
              value={avoidText}
              onChangeText={(value) => setAvoidText(value.slice(0, 240))}
              placeholder="Ví dụ: không thích tiếng ồn..."
              placeholderTextColor="#8B9AB0"
              multiline
              maxLength={240}
              style={[styles.profileFormInput, styles.profileFormMultiline]}
            />

            <Text style={[styles.profileFormLabel, styles.profileFormLabelSpaced]}>Mức đồng hành của người lớn</Text>
            <View style={styles.profileChoiceRow}>
              <Pressable accessibilityRole="radio" accessibilityState={{ selected: adultParticipation === 'together' }} onPress={() => setAdultParticipation('together')} style={[styles.profileChoice, adultParticipation === 'together' && styles.profileChoiceActive]}>
                <Ionicons name="people-outline" size={18} color={adultParticipation === 'together' ? colors.blueDeep : colors.textSoft} />
                <Text style={[styles.profileChoiceText, adultParticipation === 'together' && styles.profileChoiceTextActive]}>Cùng con</Text>
              </Pressable>
              <Pressable accessibilityRole="radio" accessibilityState={{ selected: adultParticipation === 'independent' }} onPress={() => setAdultParticipation('independent')} style={[styles.profileChoice, adultParticipation === 'independent' && styles.profileChoiceActive]}>
                <Ionicons name="happy-outline" size={18} color={adultParticipation === 'independent' ? colors.blueDeep : colors.textSoft} />
                <Text style={[styles.profileChoiceText, adultParticipation === 'independent' && styles.profileChoiceTextActive]}>Con tự khám phá</Text>
              </Pressable>
            </View>

            <Text style={[styles.profileFormLabel, styles.profileFormLabelSpaced]}>Cách bé học tốt hơn (không bắt buộc)</Text>
            <View style={styles.profileSupportWrap}>
              {supportOptions.map(([id, label]) => {
                const active = learningSupportIds.includes(id);
                return <Pressable key={id} accessibilityRole="checkbox" accessibilityState={{ checked: active }} onPress={() => toggleSupport(id)} style={[styles.profileSupportChip, active && styles.profileSupportChipActive]}><Ionicons name={active ? 'checkmark-circle' : 'ellipse-outline'} size={16} color={active ? colors.greenDeep : colors.textLight} /><Text style={[styles.profileSupportText, active && styles.profileSupportTextActive]}>{label}</Text></Pressable>;
              })}
            </View>

            <View style={styles.profileFormPrivacy}><Ionicons name="lock-closed-outline" size={17} color={colors.greenDeep} /><Text style={styles.profileFormPrivacyText}>Thông tin chỉ thuộc tài khoản phụ huynh này và có thể chỉnh sửa bất cứ lúc nào.</Text></View>

            <Pressable accessibilityRole="button" accessibilityLabel={isEdit ? 'Lưu thay đổi hồ sơ' : 'Tạo hồ sơ trẻ'} onPress={submit} style={({ pressed }) => [styles.primaryButton, pressed && styles.loginButtonPressed]}>
              <Text style={styles.primaryButtonText}>{isEdit ? 'Lưu thay đổi' : 'Tạo hồ sơ trẻ'}</Text>
              <Ionicons name="arrow-forward" size={19} color={colors.white} />
            </Pressable>
            <TouchableOpacity accessibilityRole="button" onPress={goBack} style={styles.textButton}><Text style={styles.textButtonLabel}>Để sau</Text></TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </ImageBackground>
  );
};

/** Parent profile detail/review surface before entering the home. */
export const ParentProfileDetailScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    selectedAgeMonths,
    selectedChildLearningProfile,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const profile = selectedChildLearningProfile;
  const ageYears = Math.floor(selectedAgeMonths / 12);
  const ageMonths = selectedAgeMonths % 12;
  const ageText = ageMonths ? `${ageYears} tuổi ${ageMonths} tháng` : `${ageYears} tuổi`;
  const interests = profile?.interest_text?.trim() || 'Chưa thêm sở thích';

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <EntryHeader title="Chi tiết hồ sơ" onBack={goBack} />
      <View style={styles.detailHero}>
        <View style={styles.detailAvatar}>
          <ChildAvatarImage childName={selectedChild.name} size={88} />
        </View>
        <Text style={styles.detailName}>{selectedChild.name}</Text>
        <Text style={styles.detailAge}>{ageText} · hồ sơ riêng của gia đình</Text>
      </View>

      <View style={styles.detailCard}>
        <Text style={styles.sectionTitle}>Thông tin dùng cho câu chuyện</Text>
        <View style={styles.detailRow}>
          <View style={styles.detailRowIcon}><Ionicons name="calendar-outline" size={17} color={colors.blueDeep} /></View>
          <View style={styles.detailRowCopy}>
            <Text style={styles.detailRowLabel}>Độ tuổi hiện tại</Text>
            <Text style={styles.detailRowValue}>{ageText}</Text>
          </View>
        </View>
        <View style={styles.detailDivider} />
        <View style={styles.detailRow}>
          <View style={styles.detailRowIcon}><Ionicons name="sparkles-outline" size={17} color={colors.blueDeep} /></View>
          <View style={styles.detailRowCopy}>
            <Text style={styles.detailRowLabel}>Sở thích đã khai báo</Text>
            <Text style={styles.detailRowValue}>{interests}</Text>
          </View>
        </View>
      </View>

      <View style={styles.privacyCard}>
        <Ionicons name="shield-checkmark-outline" size={20} color={colors.greenDeep} />
        <Text style={styles.privacyText}>Chỉ context tối thiểu đã được phụ huynh xác nhận mới được dùng cho story.</Text>
      </View>

      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="Lưu hồ sơ và mở trang chủ"
        onPress={() => nav('parent_home')}
        style={styles.primaryButton}
      >
        <Text style={styles.primaryButtonText}>Lưu và tiếp tục</Text>
        <Ionicons name="arrow-forward" size={18} color={colors.white} />
      </TouchableOpacity>
      <TouchableOpacity accessibilityRole="button" onPress={() => nav('profile_edit')} style={styles.detailEditButton}>
        <Ionicons name="pencil-outline" size={16} color={colors.blueDeep} />
        <Text style={styles.detailEditButtonText}>Chỉnh sửa hồ sơ</Text>
      </TouchableOpacity>
      <TouchableOpacity accessibilityRole="button" onPress={goBack} style={styles.textButton}>
        <Text style={styles.textButtonLabel}>Chọn hồ sơ khác</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

/** Parent home: a calm launchpad for the story creation flow. */
export const ParentHomeScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const recentStories = [
    ['Mèo con khám phá', 'animals', topicArtSources.animals],
    ['Khu vườn sắc màu', 'nature', topicArtSources.nature],
    ['Chuyến bay lên trời', 'space', topicArtSources.space],
    ['Ngày hội gia đình', 'family', topicArtSources.family],
  ] as const;
  useFonts({
    MaliBold: require('../../assets/fonts/Mali-Bold.ttf'),
    MaliSemiBold: require('../../assets/fonts/Mali-SemiBold.ttf'),
    ItimRegular: require('../../assets/fonts/Itim-Regular.ttf'),
  });

  return (
    <ScrollView contentContainerStyle={styles.homeContainer} showsVerticalScrollIndicator={false}>
      <View pointerEvents="none" style={styles.homeDecorLayer}>
        <Image source={topicDecorSources.sun} resizeMode="contain" style={[styles.homeDecorImage, styles.homeDecorSun]} />
        <Image source={topicDecorSources.cloud} resizeMode="contain" style={[styles.homeDecorImage, styles.homeDecorCloud]} />
        <Image source={topicDecorSources.heart} resizeMode="contain" style={[styles.homeDecorImage, styles.homeDecorHeart]} />
        <Image source={topicDecorSources.leaves} resizeMode="contain" style={[styles.homeDecorImage, styles.homeDecorLeaves]} />
      </View>
      <View style={styles.homeHeader}>
        <View style={styles.homeHeaderCopy}>
          <Text style={styles.homeEyebrow}>KHÔNG GIAN PHỤ HUYNH</Text>
          <Text accessibilityRole="header" style={styles.homeGreeting}>Xin chào, Mẹ Lan</Text>
          <Text style={styles.homeSubtitle}>Hôm nay mình kể câu chuyện gì cho {selectedChild.name}?</Text>
        </View>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Mở thông báo" onPress={() => nav('notifications_settings')} style={styles.notificationButton}>
          <Ionicons name="notifications-outline" size={21} color={colors.textBody} />
          <View style={styles.notificationDot} />
        </TouchableOpacity>
      </View>

      <View style={styles.homeBrandStrip}>
        <LogoSketch2Life size="sm" showTagline={false} />
        <View style={styles.homeBrandBadge}>
          <Ionicons name="sparkles-outline" size={15} color={colors.orangeDeep} />
          <Text style={styles.homeBrandBadgeText}>Mỗi nét vẽ đều có chuyện để kể</Text>
        </View>
      </View>

      <View style={styles.childSummaryCard}>
        <View style={styles.summaryAvatar}><ChildAvatarImage childName={selectedChild.name} size={66} /></View>
        <View style={{ flex: 1 }}>
          <Text style={styles.summaryLabel}>HỒ SƠ ĐANG DÙNG</Text>
          <Text style={styles.summaryName}>{selectedChild.name}</Text>
          <Text style={styles.summaryMeta}>{selectedChild.age} tuổi · {selectedChild.recentStoriesCount || 0} câu chuyện</Text>
        </View>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Đổi hồ sơ" onPress={() => nav('profile_list')}>
          <Text style={styles.changeText}>Đổi</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="Tạo câu chuyện mới"
        activeOpacity={0.9}
        onPress={() => nav('topic_selection')}
        style={styles.createCard}
      >
        <Image source={dashboardStoryHero} resizeMode="contain" style={styles.createHeroImage} />
        <View style={styles.createCopy}>
          <View style={styles.createBadge}>
            <Ionicons name="color-palette-outline" size={14} color={colors.yellowDeep} />
            <Text style={styles.createEyebrow}>CÂU CHUYỆN MỚI</Text>
          </View>
          <Text style={styles.createTitle}>Biến nét vẽ thành một câu chuyện</Text>
          <Text style={styles.createText}>Chọn chủ đề, để bé vẽ, rồi cùng xem thế giới trong tranh sống dậy.</Text>
          <View style={styles.createCta}>
            <Text style={styles.createCtaText}>Bắt đầu ngay</Text>
            <Ionicons name="arrow-forward" size={17} color={colors.white} />
          </View>
        </View>
      </TouchableOpacity>

      <View style={styles.homeSectionHeader}>
        <Text style={styles.homeSectionTitle}>Truy cập nhanh</Text>
        <Text style={styles.homeSectionHint}>Mở lại trong một chạm</Text>
      </View>
      <View style={styles.quickGrid}>
        {[
          ['time-outline', 'Lịch sử', 'Xem các run đã tạo', 'history'],
          ['pie-chart-outline', 'Quota', 'Theo dõi lượt dùng', 'quota'],
          ['settings-outline', 'Cài đặt', 'Quyền riêng tư', 'notifications_settings'],
        ].map(([icon, title, subtitle, route]) => (
          <TouchableOpacity key={title} accessibilityRole="button" onPress={() => nav(route as ScreenId)} style={styles.quickCard}>
            <View style={styles.quickIcon}><Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={18} color={colors.blueDeep} /></View>
            <Text style={styles.quickTitle}>{title}</Text>
            <Text style={styles.quickSubtitle}>{subtitle}</Text>
            <Ionicons name="arrow-forward" size={15} color={colors.blueDeep} style={styles.quickArrow} />
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.homeSectionHeader}>
        <Text style={styles.homeSectionTitle}>Câu chuyện gần đây</Text>
        <TouchableOpacity accessibilityRole="button" onPress={() => nav('history')} style={styles.recentSeeAll}>
          <Text style={styles.recentSeeAllText}>Xem tất cả</Text>
          <Ionicons name="chevron-forward" size={15} color={colors.blueDeep} />
        </TouchableOpacity>
      </View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.recentStoriesRow}>
        {recentStories.map(([title, id, source]) => (
          <TouchableOpacity key={id} accessibilityRole="button" accessibilityLabel={`Mở ${title}`} onPress={() => nav('history')} style={styles.recentStoryCard}>
            <Image source={source} resizeMode="cover" style={styles.recentStoryImage} />
            <Text style={styles.recentStoryTitle} numberOfLines={1}>{title}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={styles.bottomNav}>
        <View style={[styles.bottomNavItem, styles.bottomNavItemActive]}><Ionicons name="home" size={20} color={colors.blueDeep} /><Text style={styles.bottomNavActiveText}>Trang chủ</Text></View>
        <View style={styles.bottomNavItem}><Ionicons name="time-outline" size={20} color={colors.textLight} /><Text style={styles.bottomNavText}>Lịch sử</Text></View>
        <TouchableOpacity accessibilityRole="button" onPress={() => nav('profile_list')} style={styles.bottomNavItem}><Ionicons name="people-outline" size={20} color={colors.textLight} /><Text style={styles.bottomNavText}>Hồ sơ</Text></TouchableOpacity>
      </View>
    </ScrollView>
  );
};

/** Topic gate before the optional, generic AI line-sketch guide. */
export const TopicSelectionScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const [selectedTopic, setSelectedTopic] = useState('animals');
  const [difficulty, setDifficulty] = useState('simple');
  const topics = [
    ['animals', 'Động vật', 'paw-outline', 'Mèo, chó, chim và những người bạn nhỏ', 'animals', '#FFF7D9'],
    ['nature', 'Thiên nhiên', 'leaf-outline', 'Cây cối, khu vườn và bầu trời', 'nature', '#EEF8E3'],
    ['family', 'Gia đình', 'home-outline', 'Những khoảnh khắc thân quen', 'family', '#FFEAF0'],
    ['vehicles', 'Phương tiện', 'bicycle-outline', 'Xe đạp, tàu bay và chuyến đi', 'vehicles', '#EAF5FF'],
    ['space', 'Khám phá', 'planet-outline', 'Vũ trụ, đại dương và điều kỳ thú', 'space', '#F0ECFF'],
    ['free', 'Tự chọn', 'color-wand-outline', 'Để bé tự nghĩ ra thế giới riêng', 'free', '#FFF5DF'],
  ] as const;

  return (
    <ScrollView contentContainerStyle={[styles.container, styles.topicContainer]} showsVerticalScrollIndicator={false}>
      <View pointerEvents="none" style={styles.topicDoodleLayer}>
        <Image source={topicDecorSources.sun} resizeMode="contain" style={[styles.topicDecorImage, styles.topicDecorSun]} />
        <Image source={topicDecorSources.cloud} resizeMode="contain" style={[styles.topicDecorImage, styles.topicDecorCloud]} />
        <Image source={topicDecorSources.heart} resizeMode="contain" style={[styles.topicDecorImage, styles.topicDecorHeart]} />
        <Image source={topicDecorSources.star} resizeMode="contain" style={[styles.topicDecorImage, styles.topicDecorStar]} />
        <Image source={topicDecorSources.leaves} resizeMode="contain" style={[styles.topicDecorImage, styles.topicDecorLeavesLeft]} />
        <Image source={topicDecorSources.leaves} resizeMode="contain" style={[styles.topicDecorImage, styles.topicDecorLeavesRight, { transform: [{ scaleX: -1 }] }]} />
      </View>

      <EntryHeader title="Chọn chủ đề" onBack={goBack} />
      <View style={styles.flowProgress}><View style={[styles.flowProgressActive, styles.topicProgressActive]} /><View style={styles.flowProgressTrack} /><Text style={styles.flowProgressLabel}>1 / 4 · Chuẩn bị cho bé vẽ</Text></View>
      <View style={styles.topicHero}>
        <View style={styles.topicEyebrow}><Ionicons name="sparkles-outline" size={14} color={colors.orangeDeep} /><Text style={styles.topicEyebrowText}>BẮT ĐẦU TỪ MỘT Ý TƯỞNG NHỎ</Text></View>
        <Text style={styles.pageTitle}>Hôm nay bé muốn vẽ gì?</Text>
        <View style={styles.topicTitleUnderline} />
        <Text style={styles.pageSubtitle}>Chủ đề chỉ để khởi động ý tưởng. Bé vẫn tự do vẽ theo cách của mình.</Text>
      </View>

      <View style={styles.topicGrid} accessibilityRole="radiogroup" accessibilityLabel="Chủ đề cho câu chuyện">
        {topics.map(([id, title, icon, summary, artKey, artTint]) => {
          const active = selectedTopic === id;
          return (
            <Pressable
              key={id}
              accessibilityRole="radio"
              accessibilityLabel={`${title}: ${summary}`}
              accessibilityState={{ selected: active }}
              onPress={() => setSelectedTopic(id)}
              hitSlop={4}
              style={({ pressed }) => [styles.topicCard, { backgroundColor: artTint }, active && styles.topicCardActive, pressed && styles.topicCardPressed]}
            >
              <View style={styles.topicArtFrame}>
                {artKey ? (
                  <Image source={topicArtSources[artKey]} style={styles.topicArtworkImage} resizeMode="cover" />
                ) : (
                  <Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={25} color={active ? colors.blueDeep : colors.yellowDeep} />
                )}
              </View>
              <View style={styles.topicCardCopy}>
                <Text style={styles.topicTitle}>{title}</Text>
                <Text style={styles.topicSummary}>{summary}</Text>
              </View>
              {active && <View style={styles.topicCheck}><Ionicons name="checkmark" size={12} color={colors.white} /></View>}
            </Pressable>
          );
        })}
      </View>

      <View style={styles.topicDifficultyHeader}><Text style={styles.sectionTitle}>Độ khó gợi ý</Text><Text style={styles.topicDifficultyHint}>Bé có thể đổi sau</Text></View>
      <View style={styles.segmentedControl} accessibilityRole="radiogroup" accessibilityLabel="Độ khó gợi ý">
        {[
          ['simple', 'Đơn giản', 'Ít nét, dễ bắt đầu'],
          ['free', 'Tự do', 'Bé tự chọn cách vẽ'],
        ].map(([id, title, subtitle]) => {
          const active = difficulty === id;
          return <Pressable key={id} accessibilityRole="radio" accessibilityLabel={`${title}: ${subtitle}`} accessibilityState={{ selected: active }} onPress={() => setDifficulty(id)} hitSlop={4} style={({ pressed }) => [styles.segment, active && styles.segmentActive, pressed && styles.segmentPressed]}><Text style={[styles.segmentTitle, active && styles.segmentTitleActive]}>{title}</Text><Text style={[styles.segmentSubtitle, active && styles.segmentSubtitleActive]}>{subtitle}</Text>{active && <Ionicons name="checkmark-circle" size={16} color={colors.blueDeep} style={styles.segmentCheck} />}</Pressable>;
        })}
      </View>

      <View style={styles.guideInfoCard}><Ionicons name="bulb-outline" size={21} color={colors.yellowDeep} /><Text style={styles.guideInfoText}>Bạn có thể xem hướng dẫn nét vẽ AI 3–5 bước cho chủ đề này, hoặc bỏ qua để bé vẽ ngay.</Text></View>
      <Pressable accessibilityRole="button" accessibilityLabel="Xem hướng dẫn nét vẽ" onPress={() => nav('sketch_guide')} style={({ pressed }) => [styles.primaryButton, pressed && styles.loginButtonPressed]}><Ionicons name="sparkles-outline" size={18} color={colors.white} /><Text style={styles.primaryButtonText}>Xem hướng dẫn nét vẽ</Text></Pressable>
      <Pressable accessibilityRole="button" accessibilityLabel="Bỏ qua hướng dẫn và bắt đầu vẽ" onPress={() => nav('capture')} style={({ pressed }) => [styles.textButton, pressed && styles.topicSkipPressed]}><Text style={styles.textButtonLabel}>Bỏ qua, để bé vẽ ngay</Text></Pressable>
      <Text style={styles.flowFootnote}>Đang chuẩn bị cho hồ sơ của {selectedChild.name} · chưa gửi dữ liệu lên AI</Text>
    </ScrollView>
  );
};

/** Optional generic guide: topic/difficulty only, with a clear skip path. */
export const SketchGuideScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;
  const [step, setStep] = useState(1);
  const steps = [
    ['Bắt đầu bằng hình tròn', 'Vẽ một vòng tròn lớn cho phần đầu hoặc mặt trời.'],
    ['Thêm hình chính', 'Thêm thân, cánh hoặc những nét lớn mà bé nhìn thấy.'],
    ['Thêm chi tiết vui', 'Cho bé thêm mắt, lá, mây hoặc bất kỳ điều gì bé thích.'],
    ['Tô màu theo ý bé', 'Không cần giống mẫu. Mỗi bức vẽ đều là một câu chuyện riêng.'],
  ];
  const current = steps[step - 1];
  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <EntryHeader title="Hướng dẫn nét vẽ" onBack={goBack} action={<TouchableOpacity accessibilityRole="button" onPress={() => nav('capture')}><Text style={styles.skipText}>Bỏ qua</Text></TouchableOpacity>} />
      <View style={styles.flowProgress}><View style={[styles.flowProgressActive, { width: `${Math.round((step / steps.length) * 100)}%` }]} /><View style={styles.flowProgressTrack} /><Text style={styles.flowProgressLabel}>Bước {step} / {steps.length}</Text></View>
      <Text style={styles.pageTitle}>Vẽ từng nét một</Text>
      <Text style={styles.pageSubtitle}>Gợi ý chung theo chủ đề, không dùng ảnh hay thông tin hồ sơ của bé.</Text>
      <View style={styles.guideCanvas}><View style={styles.guideCanvasBadge}><Ionicons name="sparkles" size={14} color={colors.yellowDeep} /><Text style={styles.guideCanvasBadgeText}>AI guide · line sketch</Text></View><CatDrawingArtwork height={210} /><View style={styles.stepNumber}><Text style={styles.stepNumberText}>{step}</Text></View></View>
      <View style={styles.guideCopyCard}><Text style={styles.guideStepTitle}>{current[0]}</Text><Text style={styles.guideStepText}>{current[1]}</Text></View>
      <View style={styles.guideDots}>{steps.map((_, index) => <View key={index} style={[styles.guideDot, index + 1 === step && styles.guideDotActive]} />)}</View>
      <View style={styles.guideActions}><TouchableOpacity accessibilityRole="button" disabled={step === 1} onPress={() => setStep((value) => Math.max(1, value - 1))} style={[styles.outlineButton, step === 1 && styles.outlineButtonDisabled]}><Ionicons name="arrow-back" size={17} color={step === 1 ? colors.textLight : colors.blueDeep} /></TouchableOpacity><TouchableOpacity accessibilityRole="button" onPress={() => step < steps.length ? setStep((value) => value + 1) : nav('capture')} style={styles.primaryButtonInline}><Text style={styles.primaryButtonText}>{step < steps.length ? 'Tiếp tục' : 'Bắt đầu vẽ'}</Text><Ionicons name="arrow-forward" size={17} color={colors.white} /></TouchableOpacity></View>
      <Text style={styles.flowFootnote}>Hướng dẫn chỉ là gợi ý; bỏ qua hoặc lỗi guide không chặn bước chụp tranh.</Text>
    </ScrollView>
  );
};

/** Local-only capture surface. Camera/upload adapters will be connected later. */
export const ParentCaptureScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const [source, setSource] = useState<'sample' | 'camera' | 'library'>('sample');
  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <EntryHeader title="Chụp hoặc tải tranh" onBack={goBack} />
      <View style={styles.flowProgress}><View style={[styles.flowProgressActive, { width: '75%' }]} /><View style={styles.flowProgressTrack} /><Text style={styles.flowProgressLabel}>Bước 3 / 4 · Tranh của bé</Text></View>
      <Text style={styles.pageTitle}>Một bức vẽ của {selectedChild.name}</Text>
      <Text style={styles.pageSubtitle}>Chụp rõ toàn bộ tranh trên nền phẳng, hoặc chọn ảnh có sẵn trong máy.</Text>
      <View style={styles.captureCanvas}><CatDrawingArtwork height={220} />{source === 'sample' && <View style={styles.sampleTag}><Text style={styles.sampleTagText}>Ảnh mẫu để xem UI</Text></View>}</View>
      <View style={styles.captureOptions}>{[['camera', 'camera-outline', 'Chụp ảnh'], ['library', 'images-outline', 'Tải từ máy']].map(([id, icon, label]) => { const active = source === id; return <TouchableOpacity key={id} accessibilityRole="button" onPress={() => setSource(id as 'camera' | 'library')} style={[styles.captureOption, active && styles.captureOptionActive]}><Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={22} color={active ? colors.blueDeep : colors.textBody} /><Text style={[styles.captureOptionText, active && styles.captureOptionTextActive]}>{label}</Text></TouchableOpacity>; })}</View>
      <View style={styles.captureHint}><Ionicons name="shield-checkmark-outline" size={18} color={colors.greenDeep} /><Text style={styles.captureHintText}>Ảnh chỉ gắn với một hồ sơ và sẽ được kiểm tra trước khi phân tích.</Text></View>
      <TouchableOpacity accessibilityRole="button" onPress={() => nav('voice')} style={styles.primaryButton}><Text style={styles.primaryButtonText}>Tiếp tục với bức tranh</Text><Ionicons name="arrow-forward" size={18} color={colors.white} /></TouchableOpacity>
      <Text style={styles.flowFootnote}>Đây là mock UI; camera và upload thật sẽ nối sau khi chốt giao diện.</Text>
    </ScrollView>
  );
};

/** Story idea input. Text/audio are mocked until the device adapters are connected. */
export const StoryInputScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild, narrationText, setNarrationText } = useAppContext();
  const nav = onNavigate || navigate;
  const [mode, setMode] = useState<'text' | 'audio'>('text');
  const [recording, setRecording] = useState(false);
  const draft = narrationText || 'Đây là chú mèo của con. Chú mèo đang chơi bóng trong công viên.';
  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        <EntryHeader title="Ý tưởng câu chuyện" onBack={goBack} />
        <View style={styles.flowProgress}><View style={[styles.flowProgressActive, { width: '100%' }]} /><View style={styles.flowProgressTrack} /><Text style={styles.flowProgressLabel}>Bước 4 / 4 · Kể ý tưởng cho bé</Text></View>
        <Text style={styles.pageTitle}>Bức tranh này đang kể gì?</Text>
        <Text style={styles.pageSubtitle}>Bạn có thể gõ vài câu hoặc ghi âm tối đa 2 phút. Không bắt buộc phải có lời kể.</Text>
        <View style={styles.inputModeTabs}>
          <TouchableOpacity accessibilityRole="tab" accessibilityState={{ selected: mode === 'text' }} onPress={() => setMode('text')} style={[styles.inputModeTab, mode === 'text' && styles.inputModeTabActive]}><Ionicons name="create-outline" size={18} color={mode === 'text' ? colors.blueDeep : colors.textSoft} /><Text style={[styles.inputModeText, mode === 'text' && styles.inputModeTextActive]}>Nhập bằng văn bản</Text></TouchableOpacity>
          <TouchableOpacity accessibilityRole="tab" accessibilityState={{ selected: mode === 'audio' }} onPress={() => setMode('audio')} style={[styles.inputModeTab, mode === 'audio' && styles.inputModeTabActive]}><Ionicons name="mic-outline" size={18} color={mode === 'audio' ? colors.blueDeep : colors.textSoft} /><Text style={[styles.inputModeText, mode === 'audio' && styles.inputModeTextActive]}>Ghi âm</Text></TouchableOpacity>
        </View>
        {mode === 'text' ? (
          <TextInput
            accessibilityLabel="Ý tưởng câu chuyện"
            multiline
            textAlignVertical="top"
            value={draft}
            onChangeText={setNarrationText}
            placeholder="Ví dụ: Chú mèo đi dạo trong công viên và gặp một người bạn mới..."
            placeholderTextColor={colors.textLight}
            style={styles.storyInput}
          />
        ) : (
          <View style={styles.recordCard}>
            <View style={[styles.recordOrb, recording && styles.recordOrbActive]}><Ionicons name={recording ? 'stop' : 'mic'} size={28} color={recording ? colors.coralDeep : colors.blueDeep} /></View>
            <Text style={styles.recordTitle}>{recording ? 'Đang ghi âm ý tưởng…' : 'Kể bằng giọng nói của bạn'}</Text>
            <Text style={styles.recordText}>Bản ghi âm sẽ được chuyển thành chữ để bạn xem lại trước khi tạo story.</Text>
            <TouchableOpacity accessibilityRole="button" onPress={() => setRecording((value) => !value)} style={[styles.recordButton, recording && styles.recordButtonActive]}><Text style={styles.recordButtonText}>{recording ? 'Dừng ghi âm' : 'Bắt đầu ghi âm'}</Text></TouchableOpacity>
          </View>
        )}
        <View style={styles.privacyCard}><Ionicons name="lock-closed-outline" size={17} color={colors.blueDeep} /><Text style={styles.privacyText}>Ý tưởng chỉ được dùng cho run của {selectedChild.name}; bạn luôn được xem và sửa trước khi tiếp tục.</Text></View>
        <TouchableOpacity accessibilityRole="button" onPress={() => { if (mode === 'text' && !narrationText.trim()) setNarrationText(draft); nav(mode === 'audio' || draft.trim() ? 'transcript_review' : 'scene_understanding'); }} style={styles.primaryButton}><Text style={styles.primaryButtonText}>Tiếp tục rà soát</Text><Ionicons name="arrow-forward" size={18} color={colors.white} /></TouchableOpacity>
        <TouchableOpacity accessibilityRole="button" onPress={() => nav('scene_understanding')} style={styles.textButton}><Text style={styles.textButtonLabel}>Bỏ qua lời kể</Text></TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

/** Transcript review gate. It is intentionally explicit before subject review. */
export const TranscriptReviewScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, narrationText, setNarrationText, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const [draft, setDraft] = useState(narrationText || 'Đây là chú mèo của con. Chú mèo đang chơi bóng trong công viên.');
  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <EntryHeader title="Rà soát lời kể" onBack={goBack} />
      <View style={styles.flowProgress}><View style={[styles.flowProgressActive, { width: '100%' }]} /><View style={styles.flowProgressTrack} /><Text style={styles.flowProgressLabel}>Kiểm tra trước khi hiểu tranh</Text></View>
      <Text style={styles.pageTitle}>Bạn muốn kể câu chuyện thế nào?</Text>
      <Text style={styles.pageSubtitle}>Hãy sửa lại câu chữ nếu cần. Đây là bản transcript sẽ được dùng làm gợi ý cho story.</Text>
      <View style={styles.transcriptCard}><View style={styles.transcriptHeader}><View style={styles.transcriptBadge}><Ionicons name="mic-outline" size={14} color={colors.blueDeep} /><Text style={styles.transcriptBadgeText}>Transcript tiếng Việt</Text></View><Text style={styles.transcriptCount}>{draft.length}/500</Text></View><TextInput accessibilityLabel="Nội dung transcript" multiline textAlignVertical="top" value={draft} onChangeText={setDraft} style={styles.transcriptInput} /></View>
      <View style={styles.confirmHint}><Ionicons name="checkmark-circle-outline" size={19} color={colors.greenDeep} /><Text style={styles.confirmHintText}>Bạn đang xác nhận nội dung cho hồ sơ {selectedChild.name}. Không có prompt hay thông tin kỹ thuật AI hiển thị ở đây.</Text></View>
      <TouchableOpacity accessibilityRole="button" onPress={() => { setNarrationText(draft.trim()); nav('scene_understanding'); }} style={styles.primaryButton}><Text style={styles.primaryButtonText}>Xác nhận lời kể</Text><Ionicons name="arrow-forward" size={18} color={colors.white} /></TouchableOpacity>
      <TouchableOpacity accessibilityRole="button" onPress={() => nav('voice')} style={styles.textButton}><Text style={styles.textButtonLabel}>Quay lại chỉnh ý tưởng</Text></TouchableOpacity>
    </ScrollView>
  );
};

/** VLM subject review gate after capture, never before it. */
export const ParentSubjectReviewScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const [subject, setSubject] = useState('cat');
  const subjects = [['cat', 'Mèo', 'Chủ thể chính', '92%'], ['ball', 'Quả bóng', 'Vật thể phụ', '78%'], ['park', 'Công viên', 'Bối cảnh', '84%']];
  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <EntryHeader title="Xác nhận nội dung tranh" onBack={goBack} />
      <View style={styles.flowProgress}><View style={[styles.flowProgressActive, { width: '100%' }]} /><View style={styles.flowProgressTrack} /><Text style={styles.flowProgressLabel}>Chủ thể được nhận diện sau khi chụp</Text></View>
      <Text style={styles.pageTitle}>Mình nhìn thấy gì trong tranh?</Text>
      <Text style={styles.pageSubtitle}>Chọn hoặc sửa các chủ thể để story giữ đúng điều bé đã vẽ.</Text>
      <View style={styles.subjectPreview}><CatDrawingArtwork height={205} /><View style={styles.previewOverlay}><Ionicons name="scan-outline" size={17} color={colors.blueDeep} /><Text style={styles.previewOverlayText}>Ảnh tranh của {selectedChild.name}</Text></View></View>
      <Text style={[styles.sectionTitle, { marginTop: 20 }]}>Gợi ý từ hệ thống</Text>
      <View style={styles.subjectList}>{subjects.map(([id, title, kind, confidence]) => { const active = subject === id; return <TouchableOpacity key={id} accessibilityRole="checkbox" accessibilityState={{ checked: active }} onPress={() => setSubject(id)} style={[styles.subjectRow, active && styles.subjectRowActive]}><View style={[styles.subjectCheck, active && styles.subjectCheckActive]}>{active && <Ionicons name="checkmark" size={13} color={colors.white} />}</View><View style={styles.subjectCopy}><Text style={styles.subjectTitle}>{title}</Text><Text style={styles.subjectKind}>{kind}</Text></View><Text style={styles.subjectConfidence}>{confidence}</Text></TouchableOpacity>; })}</View>
      <TouchableOpacity accessibilityRole="button" onPress={() => nav('activity_selection')} style={styles.primaryButton}><Text style={styles.primaryButtonText}>Xác nhận chủ thể</Text><Ionicons name="arrow-forward" size={18} color={colors.white} /></TouchableOpacity>
      <Text style={styles.flowFootnote}>Nếu gợi ý chưa đúng, bạn có thể chọn lại; việc chỉnh sửa sẽ tạo một bản hiểu tranh mới.</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingTop: Platform.OS === 'web' ? 56 : 20, paddingBottom: 36, backgroundColor: '#F8FAFC', minHeight: '100%' },
  profileBackground: { flex: 1, backgroundColor: '#FFF8EA' },
  profileBackgroundImage: { opacity: 0.86 },
  profileContainer: { paddingHorizontal: 18, paddingTop: 52, paddingBottom: 46, backgroundColor: 'transparent', minHeight: '100%' },
  profileDoodleLayer: { ...StyleSheet.absoluteFillObject },
  profileDoodleSun: { position: 'absolute', top: 84, right: 14, opacity: 0.46, transform: [{ rotate: '10deg' }] },
  profileDoodleStarLeft: { position: 'absolute', top: 232, left: 10, opacity: 0.52, transform: [{ rotate: '-12deg' }] },
  profileDoodleHeartRight: { position: 'absolute', top: 246, right: 14, opacity: 0.48, transform: [{ rotate: '12deg' }] },
  profileDoodleTopRight: { position: 'absolute', top: 154, right: 24, opacity: 0.52, transform: [{ rotate: '12deg' }] },
  profileDoodleLeafBottomLeft: { position: 'absolute', bottom: 34, left: 18, opacity: 0.42, transform: [{ rotate: '-26deg' }] },
  profileDoodleLeafBottomRight: { position: 'absolute', bottom: 32, right: 18, opacity: 0.42, transform: [{ rotate: '28deg' }] },
  profileDoodleStarBottomRight: { position: 'absolute', bottom: 28, right: 70, opacity: 0.5, transform: [{ rotate: '14deg' }] },
  profileDoodleStrokeTop: { position: 'absolute', top: 286, left: 18, width: 28, height: 5, borderRadius: 5, backgroundColor: '#F4BD47', opacity: 0.58, transform: [{ rotate: '-24deg' }] },
  profileDoodleStrokeBottom: { position: 'absolute', bottom: 102, right: 18, width: 32, height: 5, borderRadius: 5, backgroundColor: '#70C6A1', opacity: 0.52, transform: [{ rotate: '-18deg' }] },
  profileInk: { color: '#5B2E1F' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 22 },
  headerIcon: { width: 42, height: 42, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.white, borderWidth: 1, borderColor: '#F0E7D8' },
  headerTitle: { fontSize: 16, fontWeight: '900', color: colors.textHeading },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 24 },
  brandCopy: { flex: 1 },
  eyebrow: { fontSize: 11, fontWeight: '900', letterSpacing: 0.5, color: colors.blueDeep },
  pageTitle: { fontSize: 26, lineHeight: 32, fontWeight: '900', letterSpacing: -0.6, color: colors.textHeading, marginTop: 4 },
  pageSubtitle: { fontSize: 14, lineHeight: 20, color: colors.textBody, marginTop: 6 },
  noticeCard: { flexDirection: 'row', gap: 10, alignItems: 'center', padding: 14, borderRadius: 18, backgroundColor: '#F2F8FF', borderWidth: 1, borderColor: '#D8EAFE', marginBottom: 24 },
  noticeIcon: { width: 34, height: 34, borderRadius: 12, backgroundColor: '#DBEAFE', alignItems: 'center', justifyContent: 'center' },
  noticeTitle: { fontSize: 13, fontWeight: '800', color: colors.textHeading },
  noticeText: { fontSize: 11, lineHeight: 16, color: colors.textSoft, marginTop: 2 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  sectionTitle: { fontSize: 16, fontWeight: '900', color: colors.textHeading },
  sectionCount: { fontSize: 11, color: colors.textSoft },
  profileCard: { flexDirection: 'row', alignItems: 'center', gap: 11, padding: 12, borderRadius: 23, backgroundColor: '#FFFDF7', borderWidth: 1.5, borderStyle: 'dashed', borderColor: '#F0D7A7', marginBottom: 9, ...shadows.soft },
  profileCardSelected: { borderColor: '#8EC5FF', backgroundColor: '#F8FBFF', ...shadows.card },
  avatarFrame: { width: 72, height: 72, borderRadius: 26, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF4D7', borderWidth: 1, borderColor: '#F6DFA7' },
  profileMain: { flex: 1 },
  profileNameRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  profileName: { fontFamily: 'MaliBold', fontSize: 20, color: '#5B2E1F' },
  selectedBadge: { fontFamily: 'MaliSemiBold', fontSize: 10, color: colors.blueDeep, backgroundColor: '#DCEBFF', paddingHorizontal: 9, paddingVertical: 5, borderRadius: 12 },
  ageLabel: { fontFamily: 'MaliSemiBold', fontSize: 14, color: colors.textBody, marginTop: 4 },
  profileMeta: { fontFamily: 'ItimRegular', fontSize: 13, color: colors.textSoft, marginTop: 4 },
  addProfileSection: { marginTop: 5 },
  addProfileButton: { minHeight: 88, borderRadius: 24, borderWidth: 1.5, borderStyle: 'dashed', borderColor: '#69B7FF', backgroundColor: 'rgba(255, 253, 247, 0.76)', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, overflow: 'hidden' },
  addProfileText: { fontFamily: 'MaliBold', fontSize: 16, color: colors.blueDeep },
  addProfileCopy: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  profileRainbow: { position: 'absolute', right: 28, bottom: 10, width: 62, height: 40, overflow: 'hidden' },
  profileRainbowArc: { position: 'absolute', alignSelf: 'center', borderTopLeftRadius: 999, borderTopRightRadius: 999, borderWidth: 4, borderBottomWidth: 0 },
  profileRainbowOuter: { width: 58, height: 35, top: 5, borderColor: '#F472B6' },
  profileRainbowMiddle: { width: 45, height: 27, top: 10, borderColor: '#FBBF24' },
  profileRainbowInner: { width: 32, height: 19, top: 15, borderColor: '#38BDF8' },
  inlineNotice: { fontSize: 11, lineHeight: 16, color: '#92400E', backgroundColor: '#FFFBEB', borderRadius: 12, padding: 10, marginTop: 8 },
  footerNote: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 22 },
  footerNoteText: { fontSize: 10, color: colors.textSoft },
  profileTopBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 },
  profileBackButton: { width: 48, height: 48, borderRadius: 24, borderWidth: 1.5, borderStyle: 'dashed', borderColor: '#7B4A33', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255, 253, 247, 0.46)' },
  profileTopTitle: { fontFamily: 'MaliBold', fontSize: 24, color: '#5B2E1F' },
  profileTopBarSpacer: { width: 48, height: 48 },
  profileHero: { alignItems: 'center', paddingHorizontal: 12, marginBottom: 16 },
  profilePageTitle: { fontFamily: 'MaliBold', fontSize: 29, lineHeight: 35, textAlign: 'center', color: '#5B2E1F' },
  profileTitleUnderline: { width: 190, height: 6, borderRadius: 6, backgroundColor: '#F4BD47', opacity: 0.72, marginTop: 3, transform: [{ rotate: '-1deg' }] },
  profilePageSubtitle: { fontFamily: 'ItimRegular', fontSize: 16, lineHeight: 21, textAlign: 'center', color: '#5A7192', marginTop: 7, maxWidth: 310 },
  profileNoticeCard: { flexDirection: 'row', gap: 10, alignItems: 'center', padding: 11, borderRadius: 20, backgroundColor: '#EEF7FF', borderWidth: 1.5, borderColor: '#C7E2FF', marginBottom: 18 },
  profileNoticeIcon: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#D8EAFE', alignItems: 'center', justifyContent: 'center' },
  profileNoticeText: { flex: 1, fontFamily: 'ItimRegular', fontSize: 14, lineHeight: 20, color: '#5A7192' },
  profileSectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 9 },
  profileSectionHeading: { flexDirection: 'row', alignItems: 'center' },
  profileSectionTitle: { fontFamily: 'MaliBold', fontSize: 23, lineHeight: 28, color: '#5B2E1F' },
  profileSectionUnderline: { width: 108, height: 4, borderRadius: 4, backgroundColor: '#F4BD47', opacity: 0.65, marginTop: 2, transform: [{ rotate: '-1deg' }] },
  profileSectionCount: { fontFamily: 'MaliSemiBold', fontSize: 15, color: '#5A7192' },
  profileInlineNotice: { fontFamily: 'ItimRegular', fontSize: 12, lineHeight: 17, color: colors.yellowText, backgroundColor: '#FFF3C4', borderRadius: 13, padding: 10, marginTop: 8 },
  profileFooterNote: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 12 },
  profileFooterNoteText: { fontFamily: 'ItimRegular', fontSize: 11, color: colors.textSoft },
  profileFormKeyboard: { flex: 1 },
  profileFormContainer: { paddingHorizontal: 18, paddingTop: 52, paddingBottom: 44 },
  profileFormIntro: { alignItems: 'center', paddingHorizontal: 20, marginBottom: 15 },
  profileFormIcon: { width: 52, height: 52, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: '#E2F0FF', borderWidth: 1, borderColor: '#BBDFFF', marginBottom: 8 },
  profileFormTitle: { fontFamily: 'MaliBold', fontSize: 25, lineHeight: 31, textAlign: 'center', color: '#5B2E1F' },
  profileFormSubtitle: { fontFamily: 'ItimRegular', fontSize: 14, lineHeight: 20, textAlign: 'center', color: '#5A7192', marginTop: 5, maxWidth: 320 },
  profileFormCard: { padding: 16, borderRadius: 25, backgroundColor: 'rgba(255, 253, 247, 0.9)', borderWidth: 1.5, borderColor: '#F0D7A7', ...shadows.soft },
  profileFormLabel: { fontFamily: 'MaliSemiBold', fontSize: 15, color: '#5B2E1F', marginBottom: 7 },
  profileFormLabelSpaced: { marginTop: 16 },
  profileFormInput: { minHeight: 51, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 16, borderWidth: 1.5, borderColor: '#CFD9E8', backgroundColor: '#FFFDFC', paddingHorizontal: 13, color: colors.textHeading },
  profileFormInputError: { borderColor: '#E35D6A', backgroundColor: '#FFF8F8' },
  profileFormTextInput: { flex: 1, minHeight: 48, paddingVertical: 0, fontFamily: 'ItimRegular', fontSize: 15, color: colors.textHeading },
  profileFormError: { fontFamily: 'ItimRegular', fontSize: 12, lineHeight: 16, color: '#B42318', marginTop: 5 },
  profileAgeChips: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 9 },
  profileAgeChip: { paddingHorizontal: 10, paddingVertical: 7, borderRadius: 12, borderWidth: 1, borderColor: '#E7DCC8', backgroundColor: '#FFFDF7' },
  profileAgeChipActive: { borderColor: '#7DBBFA', backgroundColor: '#EAF4FF' },
  profileAgeChipText: { fontFamily: 'MaliSemiBold', fontSize: 11, color: colors.textSoft },
  profileAgeChipTextActive: { color: colors.blueDeep },
  profileFormMultiline: { minHeight: 78, alignItems: 'flex-start', paddingTop: 12, paddingBottom: 10, fontFamily: 'ItimRegular', fontSize: 14 },
  profileChoiceRow: { flexDirection: 'row', gap: 8 },
  profileChoice: { flex: 1, minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingHorizontal: 8, borderRadius: 14, borderWidth: 1, borderColor: '#E7DCC8', backgroundColor: '#FFFDF7' },
  profileChoiceActive: { borderColor: '#7DBBFA', backgroundColor: '#EAF4FF' },
  profileChoiceText: { fontFamily: 'MaliSemiBold', fontSize: 11, color: colors.textSoft },
  profileChoiceTextActive: { color: colors.blueDeep },
  profileSupportWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  profileSupportChip: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 9, paddingVertical: 8, borderRadius: 13, borderWidth: 1, borderColor: '#E7DCC8', backgroundColor: '#FFFDF7' },
  profileSupportChipActive: { borderColor: '#99D6B8', backgroundColor: '#EFFBF4' },
  profileSupportText: { fontFamily: 'ItimRegular', fontSize: 11, color: colors.textSoft },
  profileSupportTextActive: { color: colors.greenDeep },
  profileFormPrivacy: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, padding: 11, borderRadius: 15, backgroundColor: '#F0FDF4', marginTop: 17 },
  profileFormPrivacyText: { flex: 1, fontFamily: 'ItimRegular', fontSize: 11, lineHeight: 16, color: '#166534' },
  detailEditButton: { minHeight: 46, borderRadius: 16, borderWidth: 1, borderColor: '#A9D1FF', backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 7, marginTop: 10 },
  detailEditButtonText: { fontFamily: 'MaliSemiBold', fontSize: 13, color: colors.blueDeep },
  detailHero: { alignItems: 'center', paddingVertical: 8, marginBottom: 22 },
  detailAvatar: { width: 116, height: 116, borderRadius: 38, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF4D7', marginBottom: 12 },
  detailName: { fontSize: 27, fontWeight: '900', letterSpacing: -0.6, color: colors.textHeading },
  detailAge: { fontSize: 12, color: colors.textSoft, marginTop: 4 },
  detailCard: { padding: 16, borderRadius: 20, backgroundColor: colors.white, borderWidth: 1, borderColor: '#E5EAF2', ...shadows.soft },
  detailRow: { flexDirection: 'row', alignItems: 'center', gap: 11, paddingVertical: 10 },
  detailRowIcon: { width: 34, height: 34, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#EFF6FF' },
  detailRowCopy: { flex: 1 },
  detailRowLabel: { fontSize: 11, color: colors.textSoft },
  detailRowValue: { fontSize: 14, fontWeight: '800', color: colors.textHeading, marginTop: 3 },
  detailDivider: { height: 1, backgroundColor: '#EEF2F7' },
  privacyCard: { flexDirection: 'row', gap: 9, padding: 13, borderRadius: 16, backgroundColor: '#F0FDF4', marginTop: 14 },
  privacyText: { flex: 1, fontSize: 11, lineHeight: 16, color: '#166534' },
  primaryButton: { minHeight: 56, borderRadius: 18, backgroundColor: colors.blueDeep, borderBottomWidth: 4, borderBottomColor: '#1D4ED8', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 24, ...shadows.button },
  loginButtonPressed: { opacity: 0.9, transform: [{ scale: 0.985 }] },
  primaryButtonText: { color: colors.white, fontSize: 16, fontWeight: '900' },
  textButton: { alignItems: 'center', paddingVertical: 14 },
  textButtonLabel: { fontSize: 12, fontWeight: '800', color: colors.blueDeep },
  homeContainer: { paddingHorizontal: 18, paddingTop: Platform.OS === 'web' ? 56 : 18, paddingBottom: 38, backgroundColor: '#FFF8EA', minHeight: '100%', position: 'relative' },
  homeDecorLayer: { ...StyleSheet.absoluteFillObject, zIndex: 0 },
  homeDecorImage: { position: 'absolute', opacity: 0.22 },
  homeDecorSun: { width: 66, height: 66, top: 86, right: 9 },
  homeDecorCloud: { width: 94, height: 44, top: 194, right: -17, opacity: 0.2 },
  homeDecorHeart: { width: 35, height: 35, top: 308, left: 1, opacity: 0.18 },
  homeDecorLeaves: { width: 82, height: 78, bottom: 34, left: -18, opacity: 0.16 },
  homeHeader: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 },
  homeHeaderCopy: { flex: 1, paddingRight: 12 },
  homeEyebrow: { fontFamily: 'MaliSemiBold', fontSize: 11, letterSpacing: 0.6, color: colors.orangeDeep },
  homeGreeting: { fontFamily: 'MaliBold', fontSize: 26, lineHeight: 32, color: colors.textHeading, marginTop: 3 },
  homeSubtitle: { fontFamily: 'ItimRegular', fontSize: 14, lineHeight: 20, color: colors.textBody, marginTop: 5 },
  notificationButton: { width: 44, height: 44, borderRadius: 16, backgroundColor: '#FFFDF7', borderWidth: 1, borderColor: '#F0DDB8', alignItems: 'center', justifyContent: 'center', ...shadows.soft },
  notificationDot: { position: 'absolute', top: 8, right: 9, width: 7, height: 7, borderRadius: 4, backgroundColor: colors.coralDeep, borderWidth: 1, borderColor: '#FFFDF7' },
  homeBrandStrip: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 12, paddingVertical: 8, marginBottom: 13, borderRadius: 18, backgroundColor: '#FFFDF7', borderWidth: 1, borderColor: '#F5E7CB' },
  homeBrandBadge: { flexDirection: 'row', alignItems: 'center', gap: 5, maxWidth: 180 },
  homeBrandBadgeText: { fontFamily: 'ItimRegular', fontSize: 11, lineHeight: 15, color: colors.textBody },
  childSummaryCard: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14, borderRadius: 22, backgroundColor: '#FFF0C9', borderWidth: 1, borderColor: '#F8D98A', marginBottom: 14 },
  summaryAvatar: { width: 72, height: 72, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFFDF7', borderWidth: 1, borderColor: '#F6DFA7' },
  summaryLabel: { fontFamily: 'MaliSemiBold', fontSize: 10, letterSpacing: 0.5, color: colors.yellowText },
  summaryName: { fontFamily: 'MaliBold', fontSize: 18, color: colors.textHeading, marginTop: 3 },
  summaryMeta: { fontFamily: 'ItimRegular', fontSize: 12, color: colors.textBody, marginTop: 3 },
  changeText: { fontFamily: 'MaliSemiBold', fontSize: 12, color: colors.blueDeep },
  createCard: { minHeight: 236, overflow: 'hidden', borderRadius: 27, padding: 20, backgroundColor: colors.blueDeep, borderWidth: 1, borderColor: '#1D4ED8', flexDirection: 'row', ...shadows.button },
  createHeroImage: { position: 'absolute', width: 250, height: 141, right: -8, bottom: -3, zIndex: 0 },
  createCopy: { flex: 1, zIndex: 2 },
  createBadge: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 9, paddingVertical: 5, borderRadius: 10, backgroundColor: '#FFF3B0' },
  createEyebrow: { fontFamily: 'MaliSemiBold', fontSize: 10, letterSpacing: 0.4, color: colors.yellowText },
  createTitle: { fontFamily: 'MaliBold', fontSize: 22, lineHeight: 27, color: colors.white, marginTop: 10, maxWidth: 205 },
  createText: { fontFamily: 'ItimRegular', fontSize: 13, lineHeight: 18, color: '#E8F3FF', marginTop: 8, maxWidth: 205 },
  createCta: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 13, backgroundColor: '#0F4DBA', marginTop: 17 },
  createCtaText: { fontFamily: 'MaliBold', fontSize: 12, color: colors.white },
  homeSectionHeader: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', marginTop: 23, marginBottom: 10 },
  homeSectionTitle: { fontFamily: 'MaliBold', fontSize: 17, color: colors.textHeading },
  homeSectionHint: { fontFamily: 'ItimRegular', fontSize: 11, color: colors.textSoft },
  recentSeeAll: { flexDirection: 'row', alignItems: 'center', gap: 2, paddingVertical: 4 },
  recentSeeAllText: { fontFamily: 'MaliSemiBold', fontSize: 11, color: colors.blueDeep },
  recentStoriesRow: { gap: 10, paddingBottom: 2 },
  recentStoryCard: { width: 126, padding: 6, borderRadius: 17, backgroundColor: '#FFFDF7', borderWidth: 1, borderColor: '#F0E3C9', ...shadows.soft },
  recentStoryImage: { width: '100%', height: 78, borderRadius: 12, backgroundColor: '#EAF5FF' },
  recentStoryTitle: { fontFamily: 'MaliSemiBold', fontSize: 11, color: colors.textHeading, marginTop: 6, paddingHorizontal: 2, paddingBottom: 2 },
  quickGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  quickCard: { width: '48%', minHeight: 118, padding: 12, borderRadius: 18, borderWidth: 1, borderColor: '#F0E3C9', backgroundColor: '#FFFDF7', ...shadows.soft },
  quickIcon: { width: 32, height: 32, borderRadius: 11, backgroundColor: '#E7F3FF', alignItems: 'center', justifyContent: 'center', marginBottom: 8 },
  quickTitle: { fontFamily: 'MaliSemiBold', fontSize: 13, color: colors.textHeading },
  quickSubtitle: { fontFamily: 'ItimRegular', fontSize: 11, lineHeight: 15, color: colors.textSoft, marginTop: 3, maxWidth: 120 },
  quickArrow: { position: 'absolute', right: 12, bottom: 12 },
  bottomNav: { flexDirection: 'row', justifyContent: 'space-around', paddingTop: 18, marginTop: 23, borderTopWidth: 1, borderTopColor: '#F0E3C9' },
  bottomNavItem: { alignItems: 'center', gap: 4, paddingHorizontal: 13 },
  bottomNavItemActive: { borderBottomWidth: 2, borderBottomColor: colors.blueDeep, paddingBottom: 7 },
  bottomNavText: { fontFamily: 'ItimRegular', fontSize: 11, color: colors.textSoft },
  bottomNavActiveText: { fontFamily: 'MaliSemiBold', fontSize: 11, color: colors.blueDeep },
  topicContainer: { backgroundColor: '#FFF8EA', position: 'relative' },
  topicDoodleLayer: { ...StyleSheet.absoluteFillObject, zIndex: 0 },
  topicDecorImage: { position: 'absolute', opacity: 0.34 },
  topicDecorSun: { width: 54, height: 54, top: 84, right: 7 },
  topicDecorCloud: { width: 82, height: 40, top: 230, left: -16 },
  topicDecorHeart: { width: 32, height: 32, top: 282, right: 8, opacity: 0.28 },
  topicDecorStar: { width: 30, height: 30, top: 150, right: 20, opacity: 0.33 },
  topicDecorLeavesLeft: { width: 66, height: 64, bottom: 18, left: -13, opacity: 0.28 },
  topicDecorLeavesRight: { width: 66, height: 64, bottom: 18, right: -13, opacity: 0.28 },
  topicProgressActive: { width: '25%' },
  topicHero: { alignItems: 'center', paddingHorizontal: 8, marginTop: 4, marginBottom: 2 },
  topicEyebrow: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12, backgroundColor: '#FFF1C5', marginBottom: 9 },
  topicEyebrowText: { fontFamily: 'MaliSemiBold', fontSize: 9, letterSpacing: 0.45, color: colors.orangeDeep },
  topicTitleUnderline: { width: 156, height: 5, borderRadius: 5, backgroundColor: '#F4BD47', opacity: 0.7, marginTop: 2, transform: [{ rotate: '-1deg' }] },
  topicDifficultyHeader: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', marginTop: 22, marginBottom: 10 },
  topicDifficultyHint: { fontFamily: 'ItimRegular', fontSize: 11, color: colors.textSoft },
  skipText: { fontSize: 12, fontWeight: '800', color: colors.blueDeep },
  flowProgress: { position: 'relative', marginBottom: 20 },
  flowProgressActive: { height: 4, width: '25%', borderRadius: 4, backgroundColor: colors.blueDeep, zIndex: 1 },
  flowProgressTrack: { position: 'absolute', left: 0, right: 0, top: 0, height: 4, borderRadius: 4, backgroundColor: '#E8EEF7' },
  flowProgressLabel: { fontSize: 10, fontWeight: '800', color: colors.textSoft, marginTop: 8 },
  topicGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 11, marginTop: 18, zIndex: 1 },
  topicCard: { width: '48%', minHeight: 198, padding: 10, borderRadius: 22, backgroundColor: '#FFFDF7', borderWidth: 1.5, borderStyle: 'dashed', borderColor: '#E8D7B9', position: 'relative', ...shadows.soft },
  topicCardActive: { borderStyle: 'solid', borderColor: '#69B7FF', ...shadows.card },
  topicCardPressed: { opacity: 0.88, transform: [{ scale: 0.985 }] },
  topicArtFrame: { width: '100%', height: 112, alignItems: 'center', justifyContent: 'center', backgroundColor: 'transparent', marginBottom: 8 },
  topicArtworkImage: { width: '100%', height: '100%' },
  topicCardCopy: { flex: 1 },
  topicEmojiText: { fontSize: 21 },
  topicTitle: { fontFamily: 'MaliSemiBold', fontSize: 14, color: '#5B2E1F' },
  topicSummary: { fontFamily: 'ItimRegular', fontSize: 11, lineHeight: 15, color: colors.textSoft, marginTop: 4, paddingRight: 4 },
  topicCheck: { position: 'absolute', top: 9, right: 9, width: 20, height: 20, borderRadius: 10, backgroundColor: colors.blueDeep, alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: '#FFFFFF' },
  segmentedControl: { flexDirection: 'row', gap: 9, marginTop: 0 },
  segment: { flex: 1, minHeight: 68, padding: 12, borderRadius: 17, borderWidth: 1.5, borderStyle: 'dashed', borderColor: '#E8D7B9', backgroundColor: '#FFFDF7', position: 'relative' },
  segmentActive: { borderStyle: 'solid', borderColor: '#69B7FF', backgroundColor: '#F3F8FF' },
  segmentPressed: { opacity: 0.86, transform: [{ scale: 0.985 }] },
  segmentCheck: { position: 'absolute', top: 10, right: 10 },
  segmentTitle: { fontFamily: 'MaliSemiBold', fontSize: 13, color: '#5B2E1F' },
  segmentTitleActive: { color: colors.blueDeep },
  segmentSubtitle: { fontFamily: 'ItimRegular', fontSize: 11, color: colors.textSoft, marginTop: 4, paddingRight: 14 },
  segmentSubtitleActive: { color: '#1D4ED8' },
  topicSkipPressed: { opacity: 0.72, transform: [{ scale: 0.98 }] },
  guideInfoCard: { flexDirection: 'row', alignItems: 'center', gap: 9, padding: 13, borderRadius: 16, backgroundColor: '#FFFBEB', marginTop: 18 },
  guideInfoText: { flex: 1, fontSize: 11, lineHeight: 16, color: '#92400E' },
  flowFootnote: { fontSize: 10, lineHeight: 15, color: colors.textSoft, textAlign: 'center', marginTop: 14 },
  guideCanvas: { minHeight: 292, borderRadius: 24, backgroundColor: '#F7FBFF', borderWidth: 1, borderColor: '#D8EAFE', alignItems: 'center', justifyContent: 'center', marginTop: 20, overflow: 'hidden', position: 'relative' },
  guideCanvasBadge: { position: 'absolute', left: 14, top: 13, flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 9, paddingVertical: 6, borderRadius: 10, backgroundColor: '#FFF7D6' },
  guideCanvasBadgeText: { fontSize: 9, fontWeight: '800', color: colors.yellowText },
  stepNumber: { position: 'absolute', right: 16, bottom: 14, width: 33, height: 33, borderRadius: 17, backgroundColor: colors.blueDeep, alignItems: 'center', justifyContent: 'center' },
  stepNumberText: { fontSize: 15, fontWeight: '900', color: colors.white },
  guideCopyCard: { padding: 15, borderRadius: 18, backgroundColor: colors.white, borderWidth: 1, borderColor: '#E5EAF2', marginTop: 12, ...shadows.soft },
  guideStepTitle: { fontSize: 16, fontWeight: '900', color: colors.textHeading },
  guideStepText: { fontSize: 12, lineHeight: 18, color: colors.textSoft, marginTop: 5 },
  guideDots: { flexDirection: 'row', justifyContent: 'center', gap: 6, marginTop: 15 },
  guideDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#CBD5E1' },
  guideDotActive: { width: 20, backgroundColor: colors.blueDeep },
  guideActions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 18 },
  outlineButton: { width: 52, height: 52, borderRadius: 17, borderWidth: 1, borderColor: '#BFDBFE', backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center' },
  outlineButtonDisabled: { borderColor: '#E5EAF2', backgroundColor: '#F8FAFC' },
  primaryButtonInline: { flex: 1, minHeight: 52, borderRadius: 17, backgroundColor: colors.blueDeep, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, ...shadows.button },
  captureCanvas: { minHeight: 280, borderRadius: 24, backgroundColor: '#FFFDF7', borderWidth: 1, borderColor: '#F3E6B3', alignItems: 'center', justifyContent: 'center', marginTop: 20, position: 'relative', overflow: 'hidden' },
  sampleTag: { position: 'absolute', top: 12, right: 12, paddingHorizontal: 9, paddingVertical: 6, borderRadius: 10, backgroundColor: '#FEF3C7' },
  sampleTagText: { fontSize: 9, fontWeight: '800', color: colors.yellowText },
  captureOptions: { flexDirection: 'row', gap: 10, marginTop: 14 },
  captureOption: { flex: 1, minHeight: 58, borderRadius: 16, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  captureOptionActive: { borderColor: '#60A5FA', backgroundColor: '#EFF6FF' },
  captureOptionText: { fontSize: 12, fontWeight: '800', color: colors.textBody },
  captureOptionTextActive: { color: colors.blueDeep },
  captureHint: { flexDirection: 'row', gap: 8, alignItems: 'center', padding: 13, borderRadius: 16, backgroundColor: '#F0FDF4', marginTop: 14 },
  captureHintText: { flex: 1, fontSize: 11, lineHeight: 16, color: '#166534' },
  inputModeTabs: { flexDirection: 'row', gap: 8, marginTop: 20 },
  inputModeTab: { flex: 1, minHeight: 48, borderRadius: 14, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  inputModeTabActive: { borderColor: '#60A5FA', backgroundColor: '#EFF6FF' },
  inputModeText: { fontSize: 11, fontWeight: '800', color: colors.textSoft },
  inputModeTextActive: { color: colors.blueDeep },
  storyInput: { minHeight: 165, borderRadius: 20, borderWidth: 1, borderColor: '#CBD5E1', backgroundColor: colors.white, padding: 15, color: colors.textHeading, fontSize: 14, lineHeight: 21, marginTop: 12 },
  recordCard: { minHeight: 285, borderRadius: 22, borderWidth: 1, borderColor: '#D8EAFE', backgroundColor: '#F7FBFF', alignItems: 'center', justifyContent: 'center', padding: 22, marginTop: 12 },
  recordOrb: { width: 74, height: 74, borderRadius: 37, backgroundColor: '#DBEAFE', alignItems: 'center', justifyContent: 'center' },
  recordOrbActive: { backgroundColor: '#FFE4E6' },
  recordTitle: { fontSize: 16, fontWeight: '900', color: colors.textHeading, marginTop: 14 },
  recordText: { fontSize: 12, lineHeight: 17, color: colors.textSoft, textAlign: 'center', marginTop: 6, maxWidth: 270 },
  recordButton: { minHeight: 44, paddingHorizontal: 17, borderRadius: 14, backgroundColor: colors.blueDeep, alignItems: 'center', justifyContent: 'center', marginTop: 18 },
  recordButtonActive: { backgroundColor: colors.coralDeep },
  recordButtonText: { fontSize: 12, fontWeight: '900', color: colors.white },
  transcriptCard: { borderRadius: 20, borderWidth: 1, borderColor: '#D8EAFE', backgroundColor: colors.white, padding: 14, marginTop: 20, ...shadows.soft },
  transcriptHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  transcriptBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 9, paddingVertical: 6, borderRadius: 10, backgroundColor: '#EFF6FF' },
  transcriptBadgeText: { fontSize: 10, fontWeight: '800', color: colors.blueDeep },
  transcriptCount: { fontSize: 10, color: colors.textSoft },
  transcriptInput: { minHeight: 170, paddingTop: 14, color: colors.textHeading, fontSize: 14, lineHeight: 21 },
  confirmHint: { flexDirection: 'row', gap: 8, alignItems: 'flex-start', padding: 13, borderRadius: 16, backgroundColor: '#F0FDF4', marginTop: 14 },
  confirmHintText: { flex: 1, fontSize: 11, lineHeight: 16, color: '#166534' },
  subjectPreview: { minHeight: 255, borderRadius: 22, borderWidth: 1, borderColor: '#F3E6B3', backgroundColor: '#FFFDF7', alignItems: 'center', justifyContent: 'center', marginTop: 20, position: 'relative', overflow: 'hidden' },
  previewOverlay: { position: 'absolute', left: 12, bottom: 12, flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 9, paddingVertical: 6, borderRadius: 10, backgroundColor: '#EFF6FF' },
  previewOverlayText: { fontSize: 9, fontWeight: '800', color: colors.blueDeep },
  subjectList: { gap: 8, marginTop: 10 },
  subjectRow: { minHeight: 58, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 16, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white, paddingHorizontal: 12 },
  subjectRowActive: { borderColor: '#60A5FA', backgroundColor: '#F3F8FF' },
  subjectCheck: { width: 22, height: 22, borderRadius: 7, borderWidth: 1.5, borderColor: '#CBD5E1', alignItems: 'center', justifyContent: 'center' },
  subjectCheckActive: { borderColor: colors.blueDeep, backgroundColor: colors.blueDeep },
  subjectCopy: { flex: 1 },
  subjectTitle: { fontSize: 13, fontWeight: '900', color: colors.textHeading },
  subjectKind: { fontSize: 10, color: colors.textSoft, marginTop: 2 },
  subjectConfidence: { fontSize: 11, fontWeight: '800', color: colors.blueDeep },
});
