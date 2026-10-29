import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { CatDrawingArtwork, ChildAvatarImage, LogoSketch2Life } from '../components/ArtworkCards';
import type { ScreenId } from '../types';
import { useAppContext } from '../context/AppContext';
import { ParentFlowHeader } from '../components/ParentFlowShell';

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

const AgeLabel: React.FC<{ age: number }> = ({ age }) => (
  <Text style={styles.ageLabel}>{age} tuổi</Text>
);

/** Parent entry surface: owned child profiles, before starting a story run. */
export const ParentProfileListScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, childrenList, selectedChild, setSelectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const [addNotice, setAddNotice] = useState(false);

  const openProfile = (child: (typeof childrenList)[number]) => {
    setSelectedChild(child);
    nav('profile_detail');
  };

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <EntryHeader title="Hồ sơ của con" />
      <View style={styles.brandRow}>
        <LogoSketch2Life size="sm" showTagline={false} />
        <View style={styles.brandCopy}>
          <Text style={styles.eyebrow}>KHU VỰC PHỤ HUYNH</Text>
          <Text style={styles.pageTitle}>Chọn hồ sơ để bắt đầu</Text>
          <Text style={styles.pageSubtitle}>Mỗi câu chuyện chỉ gắn với một hồ sơ trẻ.</Text>
        </View>
      </View>

      <View style={styles.noticeCard}>
        <View style={styles.noticeIcon}>
          <Ionicons name="lock-closed-outline" size={18} color={colors.blueDeep} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.noticeTitle}>Không gian riêng của gia đình</Text>
          <Text style={styles.noticeText}>Hồ sơ và tranh của con chỉ hiển thị với tài khoản phụ huynh này.</Text>
        </View>
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Hồ sơ đang có</Text>
        <Text style={styles.sectionCount}>{childrenList.length} hồ sơ</Text>
      </View>

      {childrenList.map((child) => {
        const isSelected = child.id === selectedChild.id;
        return (
          <TouchableOpacity
            key={child.id}
            accessibilityRole="button"
            accessibilityLabel={`Mở hồ sơ ${child.name}`}
            accessibilityState={{ selected: isSelected }}
            activeOpacity={0.9}
            onPress={() => openProfile(child)}
            style={[styles.profileCard, isSelected && styles.profileCardSelected]}
          >
            <View style={styles.avatarFrame}>
              <ChildAvatarImage childName={child.name} size={62} />
            </View>
            <View style={styles.profileMain}>
              <View style={styles.profileNameRow}>
                <Text style={styles.profileName}>{child.name}</Text>
                {isSelected && <Text style={styles.selectedBadge}>Đang chọn</Text>}
              </View>
              <AgeLabel age={child.age} />
              <Text style={styles.profileMeta}>{child.recentStoriesCount || 0} câu chuyện đã tạo</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.textLight} />
          </TouchableOpacity>
        );
      })}

      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="Thêm hồ sơ trẻ"
        onPress={() => setAddNotice(true)}
        style={styles.addProfileButton}
      >
        <Ionicons name="add" size={20} color={colors.blueDeep} />
        <Text style={styles.addProfileText}>Thêm hồ sơ trẻ</Text>
      </TouchableOpacity>
      {addNotice && (
        <Text accessibilityRole="alert" style={styles.inlineNotice}>
          Màn hình tạo hồ sơ sẽ được bổ sung ở bước tiếp theo; hiện tại đang dùng dữ liệu demo.
        </Text>
      )}

      <View style={styles.footerNote}>
        <Ionicons name="information-circle-outline" size={16} color={colors.textSoft} />
        <Text style={styles.footerNoteText}>Bản hiện tại là giao diện mẫu; dữ liệu chưa lưu vào backend.</Text>
      </View>
    </ScrollView>
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

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.homeHeader}>
        <View>
          <Text style={styles.eyebrow}>SKETCH2LIFE · PARENT</Text>
          <Text accessibilityRole="header" style={styles.homeGreeting}>Xin chào, Mẹ Lan</Text>
          <Text style={styles.pageSubtitle}>Hôm nay mình kể câu chuyện gì cho {selectedChild.name}?</Text>
        </View>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Mở thông báo" onPress={() => nav('notifications_settings')} style={styles.notificationButton}>
          <Ionicons name="notifications-outline" size={21} color={colors.textBody} />
          <View style={styles.notificationDot} />
        </TouchableOpacity>
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
        <View style={styles.createCopy}>
          <Text style={styles.createEyebrow}>BẮT ĐẦU MỘT RUN MỚI</Text>
          <Text style={styles.createTitle}>Biến nét vẽ thành một câu chuyện</Text>
          <Text style={styles.createText}>Chọn chủ đề, để bé vẽ, rồi cùng xem thế giới trong tranh sống dậy.</Text>
          <View style={styles.createCta}>
            <Text style={styles.createCtaText}>Tạo câu chuyện mới</Text>
            <Ionicons name="arrow-forward" size={17} color={colors.white} />
          </View>
        </View>
        <View style={styles.createSparkle}><Ionicons name="sparkles" size={34} color={colors.yellowDeep} /></View>
      </TouchableOpacity>

      <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Truy cập nhanh</Text>
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
            <Text style={styles.comingSoon}>Mở màn hình</Text>
          </TouchableOpacity>
        ))}
      </View>

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
    ['animals', 'Động vật', 'paw-outline', 'Mèo, chó, chim và những người bạn nhỏ'],
    ['nature', 'Thiên nhiên', 'leaf-outline', 'Cây cối, khu vườn và bầu trời'],
    ['family', 'Gia đình', 'home-outline', 'Những khoảnh khắc thân quen'],
    ['vehicles', 'Phương tiện', 'bicycle-outline', 'Xe đạp, tàu bay và chuyến đi'],
    ['space', 'Khám phá', 'planet-outline', 'Vũ trụ, đại dương và điều kỳ thú'],
    ['free', 'Tự chọn', 'color-wand-outline', 'Để bé tự nghĩ ra thế giới riêng'],
  ];

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <EntryHeader title="Chọn chủ đề" onBack={goBack} />
      <View style={styles.flowProgress}><View style={styles.flowProgressActive} /><View style={styles.flowProgressTrack} /><Text style={styles.flowProgressLabel}>1 / 4 · Chuẩn bị cho bé vẽ</Text></View>
      <Text style={styles.pageTitle}>Hôm nay bé muốn vẽ gì?</Text>
      <Text style={styles.pageSubtitle}>Chủ đề chỉ để khởi động ý tưởng. Bé vẫn tự do vẽ theo cách của mình.</Text>

      <View style={styles.topicGrid}>
        {topics.map(([id, title, icon, summary]) => {
          const active = selectedTopic === id;
          return (
            <TouchableOpacity key={id} accessibilityRole="radio" accessibilityState={{ selected: active }} onPress={() => setSelectedTopic(id)} style={[styles.topicCard, active && styles.topicCardActive]}>
              <View style={[styles.topicEmoji, active && styles.topicEmojiActive]}><Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={25} color={active ? colors.blueDeep : colors.yellowDeep} /></View>
              <Text style={styles.topicTitle}>{title}</Text>
              <Text style={styles.topicSummary}>{summary}</Text>
              {active && <View style={styles.topicCheck}><Ionicons name="checkmark" size={12} color={colors.white} /></View>}
            </TouchableOpacity>
          );
        })}
      </View>

      <Text style={[styles.sectionTitle, { marginTop: 22 }]}>Độ khó gợi ý</Text>
      <View style={styles.segmentedControl}>
        {[
          ['simple', 'Đơn giản', 'Ít nét, dễ bắt đầu'],
          ['free', 'Tự do', 'Bé tự chọn cách vẽ'],
        ].map(([id, title, subtitle]) => {
          const active = difficulty === id;
          return <TouchableOpacity key={id} accessibilityRole="radio" accessibilityState={{ selected: active }} onPress={() => setDifficulty(id)} style={[styles.segment, active && styles.segmentActive]}><Text style={[styles.segmentTitle, active && styles.segmentTitleActive]}>{title}</Text><Text style={[styles.segmentSubtitle, active && styles.segmentSubtitleActive]}>{subtitle}</Text></TouchableOpacity>;
        })}
      </View>

      <View style={styles.guideInfoCard}><Ionicons name="bulb-outline" size={21} color={colors.yellowDeep} /><Text style={styles.guideInfoText}>Bạn có thể xem hướng dẫn nét vẽ AI 3–5 bước cho chủ đề này, hoặc bỏ qua để bé vẽ ngay.</Text></View>
      <TouchableOpacity accessibilityRole="button" onPress={() => nav('sketch_guide')} style={styles.primaryButton}><Ionicons name="sparkles-outline" size={18} color={colors.white} /><Text style={styles.primaryButtonText}>Xem hướng dẫn nét vẽ</Text></TouchableOpacity>
      <TouchableOpacity accessibilityRole="button" onPress={() => nav('capture')} style={styles.textButton}><Text style={styles.textButtonLabel}>Bỏ qua, để bé vẽ ngay</Text></TouchableOpacity>
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
  container: { padding: 20, paddingBottom: 36, backgroundColor: '#F8FAFC', minHeight: '100%' },
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
  profileCard: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 13, borderRadius: 20, backgroundColor: colors.white, borderWidth: 1, borderColor: '#E5EAF2', marginBottom: 10, ...shadows.soft },
  profileCardSelected: { borderColor: '#9CCBFF', backgroundColor: '#F8FBFF' },
  avatarFrame: { width: 70, height: 70, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF4D7' },
  profileMain: { flex: 1 },
  profileNameRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  profileName: { fontSize: 17, fontWeight: '900', color: colors.textHeading },
  selectedBadge: { fontSize: 9, fontWeight: '800', color: colors.blueDeep, backgroundColor: '#DBEAFE', paddingHorizontal: 7, paddingVertical: 4, borderRadius: 7 },
  ageLabel: { fontSize: 12, fontWeight: '700', color: colors.textBody, marginTop: 3 },
  profileMeta: { fontSize: 11, color: colors.textSoft, marginTop: 4 },
  addProfileButton: { minHeight: 50, borderRadius: 16, borderWidth: 1, borderStyle: 'dashed', borderColor: '#93C5FD', backgroundColor: '#F8FBFF', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, marginTop: 4 },
  addProfileText: { fontSize: 13, fontWeight: '800', color: colors.blueDeep },
  inlineNotice: { fontSize: 11, lineHeight: 16, color: '#92400E', backgroundColor: '#FFFBEB', borderRadius: 12, padding: 10, marginTop: 8 },
  footerNote: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 22 },
  footerNoteText: { fontSize: 10, color: colors.textSoft },
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
  primaryButtonText: { color: colors.white, fontSize: 16, fontWeight: '900' },
  textButton: { alignItems: 'center', paddingVertical: 14 },
  textButtonLabel: { fontSize: 12, fontWeight: '800', color: colors.blueDeep },
  homeHeader: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 22 },
  homeGreeting: { fontSize: 26, lineHeight: 31, fontWeight: '900', letterSpacing: -0.6, color: colors.textHeading, marginTop: 4 },
  notificationButton: { width: 42, height: 42, borderRadius: 15, backgroundColor: colors.white, borderWidth: 1, borderColor: '#E5EAF2', alignItems: 'center', justifyContent: 'center' },
  notificationDot: { position: 'absolute', top: 9, right: 10, width: 6, height: 6, borderRadius: 3, backgroundColor: colors.coralDeep },
  childSummaryCard: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14, borderRadius: 20, backgroundColor: '#F9F5EA', marginBottom: 14 },
  summaryAvatar: { width: 72, height: 72, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFFDF7' },
  summaryLabel: { fontSize: 11, fontWeight: '900', letterSpacing: 0.4, color: colors.textBody },
  summaryName: { fontSize: 18, fontWeight: '900', color: colors.textHeading, marginTop: 3 },
  summaryMeta: { fontSize: 11, color: colors.textBody, marginTop: 3 },
  changeText: { fontSize: 12, fontWeight: '800', color: colors.blueDeep },
  createCard: { minHeight: 212, overflow: 'hidden', borderRadius: 26, padding: 20, backgroundColor: colors.blueDeep, flexDirection: 'row', ...shadows.soft },
  createCopy: { flex: 1, zIndex: 1 },
  createEyebrow: { fontSize: 11, fontWeight: '900', letterSpacing: 0.4, color: colors.white },
  createTitle: { fontSize: 24, lineHeight: 28, fontWeight: '900', letterSpacing: -0.5, color: colors.white, marginTop: 8, maxWidth: 250 },
  createText: { fontSize: 12, lineHeight: 18, color: colors.white, marginTop: 8, maxWidth: 250 },
  createCta: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 13, paddingVertical: 10, borderRadius: 12, backgroundColor: '#0F4DBA', marginTop: 17 },
  createCtaText: { fontSize: 12, fontWeight: '900', color: colors.white },
  createSparkle: { position: 'absolute', right: 20, top: 24, width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FDE68A' },
  quickGrid: { flexDirection: 'row', gap: 9, marginTop: 11 },
  quickCard: { flex: 1, minHeight: 118, padding: 11, borderRadius: 17, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white },
  quickIcon: { width: 30, height: 30, borderRadius: 10, backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center', marginBottom: 8 },
  quickTitle: { fontSize: 12, fontWeight: '900', color: colors.textHeading },
  quickSubtitle: { fontSize: 11, lineHeight: 15, color: colors.textSoft, marginTop: 3 },
  comingSoon: { fontSize: 11, fontWeight: '800', color: '#B45309', marginTop: 7 },
  bottomNav: { flexDirection: 'row', justifyContent: 'space-around', paddingTop: 20, marginTop: 22, borderTopWidth: 1, borderTopColor: '#EEF2F7' },
  bottomNavItem: { alignItems: 'center', gap: 4, paddingHorizontal: 13 },
  bottomNavItemActive: { borderBottomWidth: 2, borderBottomColor: colors.blueDeep, paddingBottom: 7 },
  bottomNavText: { fontSize: 11, color: colors.textSoft },
  bottomNavActiveText: { fontSize: 11, fontWeight: '800', color: colors.blueDeep },
  skipText: { fontSize: 12, fontWeight: '800', color: colors.blueDeep },
  flowProgress: { position: 'relative', marginBottom: 20 },
  flowProgressActive: { height: 4, width: '25%', borderRadius: 4, backgroundColor: colors.blueDeep, zIndex: 1 },
  flowProgressTrack: { position: 'absolute', left: 0, right: 0, top: 0, height: 4, borderRadius: 4, backgroundColor: '#E8EEF7' },
  flowProgressLabel: { fontSize: 10, fontWeight: '800', color: colors.textSoft, marginTop: 8 },
  topicGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 20 },
  topicCard: { width: '48%', minHeight: 132, padding: 13, borderRadius: 20, backgroundColor: colors.white, borderWidth: 1, borderColor: '#E8E1D6', position: 'relative' },
  topicCardActive: { borderColor: '#60A5FA', backgroundColor: '#F3F8FF', ...shadows.soft },
  topicEmoji: { width: 46, height: 46, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF7E2', marginBottom: 9 },
  topicEmojiActive: { backgroundColor: '#DBEAFE' },
  topicEmojiText: { fontSize: 21 },
  topicTitle: { fontSize: 13, fontWeight: '900', color: colors.textHeading },
  topicSummary: { fontSize: 10, lineHeight: 14, color: colors.textSoft, marginTop: 4 },
  topicCheck: { position: 'absolute', top: 8, right: 8, width: 18, height: 18, borderRadius: 9, backgroundColor: colors.blueDeep, alignItems: 'center', justifyContent: 'center' },
  segmentedControl: { flexDirection: 'row', gap: 8, marginTop: 10 },
  segment: { flex: 1, padding: 12, borderRadius: 15, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white },
  segmentActive: { borderColor: '#60A5FA', backgroundColor: '#EFF6FF' },
  segmentTitle: { fontSize: 12, fontWeight: '900', color: colors.textHeading },
  segmentTitleActive: { color: colors.blueDeep },
  segmentSubtitle: { fontSize: 10, color: colors.textSoft, marginTop: 4 },
  segmentSubtitleActive: { color: '#1D4ED8' },
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
