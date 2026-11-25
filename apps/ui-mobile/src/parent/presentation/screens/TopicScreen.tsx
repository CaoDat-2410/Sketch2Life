import React from 'react';
import { ActivityIndicator, Image, type ImageSourcePropType, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentTopicCardV1 } from '../../domain/types';
import { Card, PrimaryButton, ScreenFrame, SectionTitle, SecondaryButton, palette } from '../components/ui';

type Props = {
  topic: string; selectedTopicId: string; cards: ReadonlyArray<ParentTopicCardV1>;
  loading: boolean; error: string; canContinue: boolean; stepLabel: string;
  onSelect: (card: ParentTopicCardV1) => void; onTopic: (value: string) => void;
  onRefresh: () => void; onContinue: () => void; onSkip: () => void; onBack: () => void;
};

const topicArtwork: Readonly<Record<string, { image: ImageSourcePropType; color: string }>> = {
  animals: { image: require('../../../../assets/topics/topic-animals-landscape.png'), color: '#80C7F5' },
  nature: { image: require('../../../../assets/topics/topic-nature-landscape.png'), color: '#82C7F5' },
  transport: { image: require('../../../../assets/topics/topic-transport.png'), color: '#B9E0FF' },
  ocean: { image: require('../../../../assets/topics/topic-ocean.png'), color: '#B7EAF7' },
  space: { image: require('../../../../assets/topics/topic-space-landscape.png'), color: '#30206F' },
  'fairy-tale': { image: require('../../../../assets/topics/topic-fairy-tale.png'), color: '#F6D9F2' },
  home: { image: require('../../../../assets/topics/topic-nature-landscape.png'), color: '#F8E2C8' },
};

export function TopicScreen(props: Props): React.JSX.Element {
  return <ScreenFrame title="Chọn chủ đề" subtitle="Ba gợi ý mới cho buổi vẽ này." step={props.stepLabel} onBack={props.onBack} visualTone="creative">
    <Card variant="creative" style={styles.intro}>
      <View style={styles.icon}><Ionicons name="sparkles-outline" size={23} color={palette.creativePrimary} accessible={false} /></View>
      <View style={{ flex: 1, gap: 3 }}>
        <SectionTitle variant="creative">Bé muốn khám phá gì?</SectionTitle>
        <Text style={styles.subcopy}>Chọn một thẻ hoặc nhập chủ đề riêng.</Text>
      </View>
      <Pressable accessibilityRole="button" accessibilityLabel="Đổi ba chủ đề gợi ý" onPress={props.onRefresh} disabled={props.loading} style={styles.refresh}>
        <Ionicons name="shuffle-outline" size={19} color={palette.creativePrimary} accessible={false} />
      </Pressable>
    </Card>
    {props.error ? <Card style={styles.errorCard}><Text style={styles.errorText}>{props.error}</Text></Card> : null}
    {props.loading && props.cards.length === 0 ? <Card style={styles.loading}><ActivityIndicator color={palette.creativePrimary} /><Text style={styles.subcopy}>Đang chọn gợi ý…</Text></Card> : null}
    <View style={styles.grid}>
      {props.cards.map((card) => {
        const art = topicArtwork[card.topic_id] ?? topicArtwork.nature;
        const selected = props.selectedTopicId === card.topic_id && props.topic === card.title_vi;
        return <Pressable key={card.topic_id} accessibilityRole="button" accessibilityState={{ selected }} accessibilityLabel={`${card.title_vi}. ${card.description_vi}`} onPress={() => props.onSelect(card)} style={({ pressed }) => [styles.tile, selected && styles.selected, pressed && { opacity: 0.82 }]}>
          <View style={[styles.imageFrame, { backgroundColor: art.color }]}><Image source={art.image} resizeMode="cover" style={styles.image} accessible={false} /></View>
          <Text style={styles.title} numberOfLines={1}>{card.title_vi}</Text>
          <Text style={styles.description} numberOfLines={2}>{card.description_vi}</Text>
          {selected ? <View style={styles.check}><Ionicons name="checkmark" size={14} color="#fff" accessible={false} /></View> : null}
        </Pressable>;
      })}
    </View>
    <Card variant="creative" style={styles.customCard}>
      <Text style={styles.customTitle}>Chủ đề riêng</Text>
      <View style={styles.inputWrap}>
        <Ionicons name="pencil-outline" size={18} color={palette.creativeMuted} accessible={false} />
        <TextInput accessibilityLabel="Nhập chủ đề riêng" value={props.selectedTopicId === 'custom' ? props.topic : ''} onChangeText={props.onTopic} maxLength={120} placeholder="Ví dụ: Khu vườn phép thuật" placeholderTextColor={palette.creativeMuted} style={styles.input} />
      </View>
      {props.selectedTopicId === 'custom' ? <Text style={styles.subcopy}>Chủ đề chưa nhận diện được? Hãy chọn gợi ý gần nhất hoặc sửa nội dung.</Text> : null}
    </Card>
    <PrimaryButton variant="creative" label="Chọn điều bé muốn vẽ" busy={props.loading} disabled={!props.canContinue} onPress={props.onContinue} />
    <SecondaryButton variant="creative" label="Bỏ qua chủ đề" onPress={props.onSkip} />
  </ScreenFrame>;
}

const styles = StyleSheet.create({
  intro: { alignItems: 'center', backgroundColor: '#FFFEFF', borderColor: palette.creativeBorder, flexDirection: 'row', gap: 10, padding: 12 },
  icon: { alignItems: 'center', backgroundColor: palette.creativeLavender, borderRadius: 14, height: 42, justifyContent: 'center', width: 42 },
  subcopy: { color: palette.creativeMuted, fontSize: 12, lineHeight: 17 },
  refresh: { alignItems: 'center', backgroundColor: '#F7F1FE', borderRadius: 14, height: 40, justifyContent: 'center', width: 40 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 11 },
  tile: { backgroundColor: '#FFFEFF', borderColor: palette.creativeBorder, borderRadius: 18, borderWidth: 1.2, flexBasis: '48%', flexGrow: 1, gap: 4, minWidth: 0, overflow: 'hidden', padding: 8 },
  selected: { borderColor: palette.creativePrimary, borderWidth: 2, backgroundColor: '#F8F1FF' },
  imageFrame: { aspectRatio: 16 / 9, borderRadius: 13, overflow: 'hidden', width: '100%' },
  image: { height: '100%', width: '100%' },
  title: { color: palette.creativeInk, fontSize: 13, fontWeight: '800', marginTop: 4 },
  description: { color: palette.creativeMuted, fontSize: 11, lineHeight: 15, minHeight: 30 },
  check: { alignItems: 'center', backgroundColor: palette.creativePrimary, borderColor: '#fff', borderRadius: 12, borderWidth: 2, height: 24, justifyContent: 'center', position: 'absolute', right: 12, top: 12, width: 24 },
  customCard: { backgroundColor: '#FFFEFF', borderColor: palette.creativeBorder, gap: 8, padding: 13 },
  customTitle: { color: palette.creativeInk, fontSize: 14, fontWeight: '800' },
  inputWrap: { alignItems: 'center', backgroundColor: '#fff', borderColor: palette.creativeBorder, borderRadius: 15, borderWidth: 1.2, flexDirection: 'row', gap: 9, minHeight: 50, paddingHorizontal: 12 },
  input: { color: palette.creativeInk, flex: 1, fontSize: 14, minHeight: 48 },
  errorCard: { backgroundColor: '#FFF6F6', borderColor: '#F3CACA' },
  errorText: { color: '#9A2E2E', fontSize: 13, lineHeight: 19 },
  loading: { alignItems: 'center', flexDirection: 'row', gap: 10 },
});
