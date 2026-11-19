import React from 'react';
import { Image, type ImageSourcePropType, Pressable, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Card, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  topic: string;
  stepLabel: string;
  onTopic: (value: string) => void;
  onContinue: () => void;
  onBack: () => void;
};

type TopicOption = {
  title: string;
  detail: string;
  image: ImageSourcePropType;
  surface: string;
  fit: 'cover' | 'contain';
};

const topicOptions: TopicOption[] = [
  {
    title: 'Khu vườn và thiên nhiên',
    detail: 'Cây xanh, hoa lá và thiên nhiên',
    image: require('../../../../assets/topics/topic-nature-landscape.png'),
    surface: '#82C7F5',
    fit: 'cover',
  },
  {
    title: 'Phương tiện quanh em',
    detail: 'Ô tô, máy bay và tàu thuyền',
    image: require('../../../../assets/topics/topic-transport.png'),
    surface: '#B9E0FF',
    fit: 'cover',
  },
  {
    title: 'Động vật đáng yêu',
    detail: 'Những người bạn động vật',
    image: require('../../../../assets/topics/topic-animals-landscape.png'),
    surface: '#80C7F5',
    fit: 'cover',
  },
  {
    title: 'Đại dương',
    detail: 'Cá, san hô và thế giới biển',
    image: require('../../../../assets/topics/topic-ocean.png'),
    surface: '#B7EAF7',
    fit: 'cover',
  },
  {
    title: 'Vũ trụ kỳ thú',
    detail: 'Hành tinh, ngôi sao và tên lửa',
    image: require('../../../../assets/topics/topic-space-landscape.png'),
    surface: '#30206F',
    fit: 'cover',
  },
  {
    title: 'Thế giới cổ tích',
    detail: 'Lâu đài, phép màu và nhân vật',
    image: require('../../../../assets/topics/topic-fairy-tale.png'),
    surface: '#F6D9F2',
    fit: 'cover',
  },
] as const;

const selectedTopicPurple = '#9333EA';

export function TopicScreen(props: Props): React.JSX.Element {
  const { width } = useWindowDimensions();
  const heroWidth = Math.min(width - 30, 440);
  const heroHeight = heroWidth * (520 / 1280);
  const heroImageHeight = heroWidth * (640 / 1280);

  return (
    <ScreenFrame
      title="Chọn chủ đề"
      subtitle="Hôm nay bé muốn khám phá gì?"
      step={props.stepLabel}
      onBack={props.onBack}
      visualTone="creative"
    >
      <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={[styles.heroArtwork, { width: heroWidth, height: heroHeight }]}>
        <Image
          source={require('../../../../assets/topics/topic-hero-girl-cat-castle.png')}
          resizeMode="contain"
          style={[styles.heroImage, { height: heroImageHeight }]}
        />
      </View>

      <Card variant="creative" style={styles.introCard}>
        <View style={styles.introIcon}>
          <Ionicons name="color-palette-outline" size={24} color={palette.creativePrimary} accessible={false} />
        </View>
        <View style={styles.introCopy}>
          <SectionTitle variant="creative">Bé thích chủ đề nào?</SectionTitle>
          <Text style={styles.introText}>Chọn một chủ đề hoặc tự nhập ý tưởng của bé.</Text>
        </View>
      </Card>

      <View accessibilityLabel="Các chủ đề gợi ý" style={styles.topicGrid}>
        {topicOptions.map((option) => {
          const selected = props.topic === option.title;
          return (
            <TopicCard
              key={option.title}
              option={option}
              selected={selected}
              onPress={() => props.onTopic(option.title)}
            />
          );
        })}
      </View>

      <Card variant="creative" style={styles.customCard}>
        <View style={styles.customHeading}>
          <View style={styles.customIcon}>
            <Ionicons name="pencil-outline" size={19} color={palette.creativePrimary} accessible={false} />
          </View>
          <View style={styles.customCopy}>
            <SectionTitle variant="creative">Chủ đề khác của bé</SectionTitle>
            <Text style={styles.customHint}>Tự nghĩ một ý tưởng cho buổi vẽ.</Text>
          </View>
        </View>
        <View style={styles.topicInputWrap}>
          <Ionicons name="pencil-outline" size={18} color={palette.creativeMuted} accessible={false} />
          <TextInput
            accessibilityLabel="Chủ đề riêng của bé"
            value={props.topic}
            onChangeText={props.onTopic}
            placeholder="Ví dụ: Khu vườn phép thuật"
            placeholderTextColor={palette.creativeMuted}
            selectionColor={palette.creativePrimary}
            returnKeyType="done"
            style={styles.topicInput}
          />
        </View>
      </Card>

      <PrimaryButton variant="creative" label="Tiếp tục" onPress={props.onContinue} />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Bỏ qua chủ đề"
        onPress={() => { props.onTopic(''); props.onContinue(); }}
        style={({ pressed }) => [styles.skipButton, pressed && styles.pressed]}
      >
        <Text style={styles.skipText}>Bỏ qua chủ đề</Text>
      </Pressable>
    </ScreenFrame>
  );
}

function TopicCard({
  option,
  selected,
  onPress,
}: {
  option: TopicOption;
  selected: boolean;
  onPress: () => void;
}): React.JSX.Element {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${option.title}. ${option.detail}${selected ? '. Đã chọn' : ''}`}
      accessibilityState={{ selected }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.topicTile,
        selected && styles.topicTileSelected,
        pressed && styles.pressed,
      ]}
    >
      <View style={[styles.topicImageFrame, { backgroundColor: option.surface }]}>
        <Image source={option.image} resizeMode={option.fit} style={styles.topicImage} accessible={false} />
        {selected ? (
          <View style={styles.selectedMark}>
            <Ionicons name="checkmark" size={14} color="#FFFFFF" accessible={false} />
          </View>
        ) : null}
      </View>
      <View style={styles.topicCopy}>
        <Text style={styles.topicTitle} numberOfLines={2}>{option.title}</Text>
        <Text style={styles.topicDetail} numberOfLines={2}>{option.detail}</Text>
      </View>
      {selected ? <View pointerEvents="none" style={styles.selectedOutline} /> : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  heroArtwork: { alignSelf: 'center', marginTop: -4, marginBottom: -12, overflow: 'hidden' },
  heroImage: { width: '100%' },
  introCard: { alignItems: 'center', backgroundColor: '#FFFEFF', borderColor: palette.creativeBorder, flexDirection: 'row', gap: 10, minWidth: 0, paddingHorizontal: 12, paddingVertical: 10 },
  introIcon: { alignItems: 'center', backgroundColor: palette.creativeLavender, borderRadius: 15, height: 42, justifyContent: 'center', width: 42 },
  introCopy: { flex: 1, gap: 3, minWidth: 0 },
  introText: { color: palette.creativeMuted, fontSize: 13, lineHeight: 18, flexShrink: 1 },
  topicGrid: { width: '100%', flexDirection: 'row', flexWrap: 'wrap', columnGap: 12, rowGap: 12 },
  topicTile: { flexGrow: 1, flexBasis: '48%', minWidth: 0, padding: 8, gap: 7, borderRadius: 20, borderWidth: 1.3, borderColor: palette.creativeBorder, backgroundColor: '#FFFEFF', shadowColor: '#492474', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.055, shadowRadius: 10, elevation: 1 },
  topicTileSelected: { backgroundColor: '#F8F1FF', shadowColor: selectedTopicPurple, shadowOpacity: 0.13, elevation: 3 },
  selectedOutline: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, borderWidth: 2, borderColor: selectedTopicPurple, borderRadius: 20 },
  topicImageFrame: { width: '100%', aspectRatio: 16 / 9, borderTopLeftRadius: 16, borderTopRightRadius: 16, borderBottomLeftRadius: 12, borderBottomRightRadius: 12, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  topicImage: { width: '100%', height: '100%' },
  selectedMark: { position: 'absolute', top: 7, right: 7, width: 24, height: 24, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: selectedTopicPurple, borderWidth: 2, borderColor: '#FFFFFF' },
  topicCopy: { gap: 3, minWidth: 0, paddingHorizontal: 2, paddingBottom: 2 },
  topicTitle: { color: palette.creativeInk, fontSize: 13, fontWeight: '800', lineHeight: 17, minHeight: 34, flexShrink: 1 },
  topicDetail: { color: palette.creativeMuted, fontSize: 12, lineHeight: 16, minHeight: 32, flexShrink: 1 },
  customCard: { backgroundColor: '#FFFEFF', borderColor: palette.creativeBorder, gap: 9, minWidth: 0, padding: 12 },
  customHeading: { alignItems: 'center', flexDirection: 'row', gap: 10, minWidth: 0 },
  customIcon: { width: 38, height: 38, borderRadius: 13, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.creativeLavender },
  customCopy: { flex: 1, minWidth: 0, gap: 2 },
  customHint: { color: palette.creativeMuted, fontSize: 12, lineHeight: 17 },
  topicInputWrap: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10, borderWidth: 1.3, borderColor: palette.creativeBorder, borderRadius: 17, backgroundColor: '#FFFEFF', paddingHorizontal: 14 },
  topicInput: { flex: 1, minWidth: 0, minHeight: 50, paddingVertical: 10, color: palette.creativeInk, fontSize: 14 },
  skipButton: { minHeight: 48, alignSelf: 'center', alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  skipText: { color: palette.creativePrimary, fontSize: 13, fontWeight: '700' },
  pressed: { opacity: 0.82 },
});
