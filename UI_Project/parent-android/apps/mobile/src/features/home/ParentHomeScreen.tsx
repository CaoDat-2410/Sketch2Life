import {useEffect, useRef, useState} from 'react';
import {AccessibilityInfo, Animated, Easing, ScrollView, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {EmptyState, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchRadius, sketchShadow, sketchSpace} from '../../shared/ui/SketchTokens';

export function ParentHomeScreen({state, onNavigate}: ParentFlowProps): React.JSX.Element {
  const [reduceMotion, setReduceMotion] = useState(false);
  const paperMotion = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let mounted = true;
    let animation: ReturnType<typeof Animated.loop> | undefined;
    const syncMotion = async (preference?: boolean): Promise<void> => {
      let reduced = preference;
      if (typeof reduced !== 'boolean') {
        try {
          reduced = await AccessibilityInfo.isReduceMotionEnabled();
        } catch {
          reduced = true;
        }
      }
      if (!mounted) return;
      animation?.stop();
      setReduceMotion(reduced);
      paperMotion.setValue(0);
      if (reduced) return;
      animation = Animated.loop(Animated.sequence([
        Animated.timing(paperMotion, {toValue: 1, duration: 2600, easing: Easing.inOut(Easing.sin), useNativeDriver: true}),
        Animated.timing(paperMotion, {toValue: 0, duration: 2600, easing: Easing.inOut(Easing.sin), useNativeDriver: true}),
      ]));
      animation.start();
    };

    void syncMotion();
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', (enabled) => { void syncMotion(enabled); });
    return () => {
      mounted = false;
      animation?.stop();
      subscription.remove();
    };
  }, [paperMotion]);

  return (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <PreviewBanner />
      <View style={styles.greeting}>
        <Text style={styles.greetingSmall}>Mỗi ngày là một câu chuyện mới</Text>
        <Text accessibilityRole="header" style={styles.title}>Chào ba mẹ!</Text>
      </View>

      <View style={styles.hero}>
        <View style={styles.heroCopy}>
          <Text style={styles.heroEyebrow}>CÙNG CON SÁNG TẠO</Text>
          <Text style={styles.heroTitle}>Bức tranh hôm nay sẽ kể chuyện gì?</Text>
          <Text style={styles.heroBody}>Bắt đầu từ nét vẽ của con, ba mẹ đồng hành qua từng bước.</Text>
          <ParentButton title="Bắt đầu kể chuyện" icon="arrow" onPress={() => onNavigate('run-setup')} />
        </View>
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.heroArt}>
          <View style={styles.heroOrb} />
          <Animated.View style={[styles.paper, reduceMotion ? undefined : {transform: [
            {perspective: 900},
            {rotateY: paperMotion.interpolate({inputRange: [0, 1], outputRange: ['-3deg', '3deg']})},
            {translateY: paperMotion.interpolate({inputRange: [0, 1], outputRange: [0, -4]})},
            {rotateZ: '8deg'},
          ]}]}>
            <View style={styles.paperSun} />
            <View style={styles.paperStem} />
            <View style={styles.paperWingLeft} />
            <View style={styles.paperWingRight} />
            <View style={styles.paperDot} />
          </Animated.View>
          <View style={styles.heroSpark}><ParentIcon name="spark" color={sketchColors.gold} size={20} /></View>
        </View>
      </View>

      <View style={styles.sectionHeader}>
        <View><Text style={styles.sectionEyebrow}>HỒ SƠ ĐANG CHỌN</Text><Text style={styles.sectionTitle}>Bé nhà mình</Text></View>
        <ParentButton title="Đổi hồ sơ" variant="quiet" icon="arrow" onPress={() => onNavigate('profiles')} />
      </View>
      <ParentCard style={styles.childCard}>
        <View style={styles.childAvatar}><Text style={styles.childInitial}>{state.childName.replace(/^Bé\s*/, '').charAt(0)}</Text><View style={styles.avatarDot} /></View>
        <View style={styles.childCopy}>
          <Text style={styles.childName}>{state.childName}</Text>
          <Text style={styles.childMeta}>{state.childAge} · Hồ sơ minh họa</Text>
        </View>
        <ParentPill label="Đang chọn" />
      </ParentCard>

      <View style={styles.sectionHeader}>
        <View><Text style={styles.sectionEyebrow}>KHÁM PHÁ</Text><Text style={styles.sectionTitle}>Một chút cảm hứng</Text></View>
        <ParentButton title="Thư viện" variant="quiet" icon="arrow" onPress={() => onNavigate('lesson-library')} />
      </View>
      <ParentCard tone="gold" style={styles.inspirationCard}>
        <View style={styles.inspirationIcon}><ParentIcon name="book" size={23} color="#8B6B22" /></View>
        <View style={styles.inspirationCopy}>
          <Text style={styles.inspirationTitle}>Chọn một giáo án làm điểm khởi đầu</Text>
          <Text style={styles.inspirationBody}>Giữ đúng phiên bản và chủ đề ba mẹ đã chọn.</Text>
        </View>
        <ParentButton title="Mở thư viện" variant="secondary" onPress={() => onNavigate('lesson-library')} />
      </ParentCard>

      <View style={styles.sectionHeader}>
        <View><Text style={styles.sectionEyebrow}>GẦN ĐÂY</Text><Text style={styles.sectionTitle}>Câu chuyện của con</Text></View>
        <ParentButton title="Lịch sử" variant="quiet" icon="arrow" onPress={() => onNavigate('history')} />
      </View>
      <EmptyState
        icon="history"
        title="Chưa có lịch sử trên máy chủ"
        description="Khi API lịch sử được kết nối, các lần kể chuyện của gia đình sẽ xuất hiện ở đây."
        action="Xem giao diện lịch sử"
        onAction={() => onNavigate('history')}
      />

      <View style={styles.quickLinks}>
        <QuickLink title="Chia sẻ hồ sơ" icon="share" onPress={() => onNavigate('sharing')} />
        <QuickLink title="Lượt tạo" icon="quota" onPress={() => onNavigate('quota')} />
        <QuickLink title="Gửi phản hồi" icon="heart" onPress={() => onNavigate('feedback')} />
      </View>
      <Text style={styles.footerNote}>Ba mẹ luôn xem lại và xác nhận trước mỗi bước quan trọng.</Text>
    </ScrollView>
  );
}

function QuickLink({title, icon, onPress}: Readonly<{title: string; icon: 'share' | 'quota' | 'heart'; onPress: () => void}>): React.JSX.Element {
  return (
    <ParentCard style={styles.quickLink}>
      <View style={styles.quickIcon}><ParentIcon name={icon} size={18} /></View>
      <Text style={styles.quickTitle}>{title}</Text>
      <ParentButton title="Mở" variant="quiet" onPress={onPress} />
    </ParentCard>
  );
}

const styles = StyleSheet.create({
  content: {padding: sketchSpace.lg, paddingBottom: 28, gap: 17},
  greeting: {gap: 3, marginTop: 2},
  greetingSmall: {color: sketchColors.muted, fontSize: 12, fontWeight: '600'},
  title: {color: sketchColors.ink, fontSize: 27, lineHeight: 33, fontWeight: '900', letterSpacing: -0.6},
  hero: {position: 'relative', minHeight: 255, justifyContent: 'center', overflow: 'hidden', padding: 20, borderRadius: sketchRadius.lg, backgroundColor: sketchColors.greenDark, ...sketchShadow},
  heroCopy: {maxWidth: 245, zIndex: 2, gap: 9},
  heroEyebrow: {color: '#D9E8D8', fontSize: 9, fontWeight: '900', letterSpacing: 1.3},
  heroTitle: {color: sketchColors.white, fontSize: 22, lineHeight: 27, fontWeight: '900', letterSpacing: -0.4},
  heroBody: {maxWidth: 240, color: '#D7E7DC', fontSize: 11, lineHeight: 17, marginBottom: 3},
  heroArt: {position: 'absolute', top: 0, right: -8, bottom: 0, width: 145, alignItems: 'center', justifyContent: 'center'},
  heroOrb: {position: 'absolute', width: 142, height: 142, right: 0, top: 39, borderRadius: 72, backgroundColor: '#FFFFFF12'},
  paper: {position: 'absolute', right: 18, top: 69, width: 84, height: 111, borderRadius: 12, backgroundColor: '#FFFDF4', transform: [{rotate: '8deg'}], shadowColor: '#102E24', shadowOpacity: 0.22, shadowRadius: 10, shadowOffset: {width: 0, height: 6}, elevation: 5},
  paperSun: {position: 'absolute', right: 14, top: 12, width: 20, height: 20, borderRadius: 11, backgroundColor: '#F0C75E'},
  paperStem: {position: 'absolute', left: 40, top: 42, width: 4, height: 46, borderRadius: 3, backgroundColor: '#4E926C'},
  paperWingLeft: {position: 'absolute', left: 13, top: 39, width: 28, height: 35, borderRadius: 20, backgroundColor: '#E99177', transform: [{rotate: '-25deg'}]},
  paperWingRight: {position: 'absolute', right: 12, top: 39, width: 28, height: 35, borderRadius: 20, backgroundColor: '#9BB5D5', transform: [{rotate: '25deg'}]},
  paperDot: {position: 'absolute', left: 39, top: 49, width: 6, height: 6, borderRadius: 4, backgroundColor: sketchColors.ink},
  heroSpark: {position: 'absolute', right: 112, top: 36},
  sectionHeader: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', gap: 10, marginTop: 3},
  sectionEyebrow: {color: sketchColors.muted, fontSize: 9, fontWeight: '900', letterSpacing: 1.1},
  sectionTitle: {color: sketchColors.ink, fontSize: 17, fontWeight: '900', marginTop: 3},
  childCard: {flexDirection: 'row', alignItems: 'center', gap: 12, padding: 13},
  childAvatar: {position: 'relative', width: 49, height: 49, justifyContent: 'center', alignItems: 'center', borderRadius: 17, backgroundColor: '#DCEBDD'},
  childInitial: {color: sketchColors.greenDark, fontSize: 19, fontWeight: '900'},
  avatarDot: {position: 'absolute', right: 2, top: 2, width: 10, height: 10, borderRadius: 6, backgroundColor: sketchColors.gold, borderWidth: 2, borderColor: sketchColors.white},
  childCopy: {flex: 1, gap: 3},
  childName: {color: sketchColors.ink, fontSize: 14, fontWeight: '900'},
  childMeta: {color: sketchColors.muted, fontSize: 10},
  inspirationCard: {flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 12, padding: 14},
  inspirationIcon: {width: 43, height: 43, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: '#F7E9B8'},
  inspirationCopy: {flex: 1, minWidth: 160, gap: 4},
  inspirationTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  inspirationBody: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
  quickLinks: {flexDirection: 'row', flexWrap: 'wrap', gap: 9},
  quickLink: {flex: 1, minWidth: 145, gap: 7, padding: 12},
  quickIcon: {width: 34, height: 34, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: sketchColors.greenSoft},
  quickTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '800'},
  footerNote: {alignSelf: 'center', maxWidth: 340, color: sketchColors.muted, fontSize: 10, lineHeight: 15, textAlign: 'center'},
});
