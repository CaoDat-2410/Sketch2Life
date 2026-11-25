import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentDrawingSubjectCardV1 } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, palette } from '../components/ui';

type Props = {
  topic: string; cards: ReadonlyArray<ParentDrawingSubjectCardV1>;
  generationSource: 'CURATED_CATALOG' | 'QWEN_DRAFT' | null; selectedSubject: string;
  customSubject: string; loading: boolean; validating: boolean; error: string;
  validationMessage: string; canContinue: boolean;
  onSelect: (card: ParentDrawingSubjectCardV1) => void; onCustomSubject: (value: string) => void;
  onValidate: () => void; onRefresh: () => void; onContinue: () => void; onBack: () => void;
};

export function DrawingSubjectScreen(props: Props): React.JSX.Element {
  return <ScreenFrame title="Bé muốn vẽ gì?" subtitle={`Ba gợi ý thuộc chủ đề ${props.topic}.`} step="2 / 8" onBack={props.onBack} visualTone="creative">
    <Card variant="creative" style={styles.header}>
      <View style={styles.topicIcon}><Ionicons name="leaf-outline" size={22} color={palette.creativePrimary} accessible={false} /></View>
      <View style={{ flex: 1 }}><Text style={styles.topicLabel}>CHỦ ĐỀ</Text><Text style={styles.topic}>{props.topic}</Text></View>
      <Pressable accessibilityRole="button" accessibilityLabel="Đổi ba gợi ý đối tượng" onPress={props.onRefresh} disabled={props.loading} style={styles.shuffle}>
        {props.loading ? <ActivityIndicator size="small" color={palette.creativePrimary} /> : <Ionicons name="shuffle-outline" size={20} color={palette.creativePrimary} accessible={false} />}
      </Pressable>
    </Card>
    {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
    {props.generationSource === 'QWEN_DRAFT' ? <Notice variant="creative" text="Ba thẻ này được AI gợi ý cho chủ đề riêng. Người lớn xem lại rồi chọn trước khi tiếp tục." tone="warning" /> : null}
    <View style={{ gap: 10 }}>
      {props.cards.map((card, index) => {
        const selected = props.selectedSubject === card.guide_subject;
        return <Pressable key={card.subject_id} accessibilityRole="button" accessibilityState={{ selected }} onPress={() => props.onSelect(card)} style={({ pressed }) => [styles.card, selected && styles.selected, pressed && { opacity: 0.8 }]}>
          <View style={[styles.number, selected && styles.numberSelected]}><Text style={[styles.numberText, selected && { color: '#fff' }]}>{index + 1}</Text></View>
          <View style={{ flex: 1, gap: 2 }}><Text style={styles.cardTitle}>{card.title_vi}</Text><Text numberOfLines={2} style={styles.cardSub}>{card.relation_to_topic_vi || 'Gợi ý vẽ theo chủ đề'}</Text></View>
          {selected ? <Ionicons name="checkmark-circle" size={23} color={palette.creativePrimary} accessible={false} /> : <Ionicons name="chevron-forward" size={19} color={palette.creativeMuted} accessible={false} />}
        </Pressable>;
      })}
    </View>
    <Card variant="creative" style={styles.custom}>
      <Text style={styles.customTitle}>Bé muốn vẽ thứ khác?</Text>
      <Text style={styles.customHint}>Nhập tên. Hệ thống sẽ kiểm tra có đúng chủ đề không.</Text>
      <View style={styles.inputWrap}><Ionicons name="pencil-outline" size={18} color={palette.creativeMuted} accessible={false} /><TextInput accessibilityLabel="Nhập đối tượng muốn vẽ" value={props.customSubject} onChangeText={props.onCustomSubject} maxLength={120} placeholder="Ví dụ: con hươu" placeholderTextColor={palette.creativeMuted} style={styles.input} returnKeyType="done" /></View>
      <SecondaryButton variant="creative" label={props.validating ? 'Đang kiểm tra…' : 'Kiểm tra lựa chọn'} disabled={props.validating || props.customSubject.trim().length < 2} onPress={props.onValidate} />
      {props.validationMessage ? <Notice variant="creative" text={props.validationMessage} tone={props.canContinue ? 'success' : 'warning'} /> : null}
    </Card>
    <PrimaryButton variant="creative" label="Tiếp tục" disabled={!props.canContinue || props.loading} onPress={props.onContinue} />
  </ScreenFrame>;
}

const styles = StyleSheet.create({
  header: { alignItems: 'center', backgroundColor: '#FFFEFF', borderColor: palette.creativeBorder, flexDirection: 'row', gap: 10, padding: 12 },
  topicIcon: { alignItems: 'center', backgroundColor: palette.creativeLavender, borderRadius: 14, height: 42, justifyContent: 'center', width: 42 },
  topicLabel: { color: palette.creativeMuted, fontSize: 10, fontWeight: '800', letterSpacing: 1 },
  topic: { color: palette.creativeInk, fontSize: 16, fontWeight: '800', marginTop: 2 },
  shuffle: { alignItems: 'center', backgroundColor: '#F7F1FE', borderRadius: 14, height: 40, justifyContent: 'center', width: 40 },
  card: { alignItems: 'center', backgroundColor: '#FFFEFF', borderColor: palette.creativeBorder, borderRadius: 17, borderWidth: 1.2, flexDirection: 'row', gap: 12, minHeight: 70, paddingHorizontal: 13, paddingVertical: 10 },
  selected: { backgroundColor: '#F8F1FF', borderColor: palette.creativePrimary, borderWidth: 2 },
  number: { alignItems: 'center', backgroundColor: '#F3EDF9', borderRadius: 15, height: 34, justifyContent: 'center', width: 34 },
  numberSelected: { backgroundColor: palette.creativePrimary },
  numberText: { color: palette.creativePrimary, fontSize: 14, fontWeight: '800' },
  cardTitle: { color: palette.creativeInk, fontSize: 15, fontWeight: '800' },
  cardSub: { color: palette.creativeMuted, fontSize: 11 },
  custom: { backgroundColor: '#FFFEFF', borderColor: palette.creativeBorder, gap: 9, padding: 13 },
  customTitle: { color: palette.creativeInk, fontSize: 14, fontWeight: '800' },
  customHint: { color: palette.creativeMuted, fontSize: 12, lineHeight: 17 },
  inputWrap: { alignItems: 'center', backgroundColor: '#fff', borderColor: palette.creativeBorder, borderRadius: 15, borderWidth: 1.2, flexDirection: 'row', gap: 9, minHeight: 50, paddingHorizontal: 12 },
  input: { color: palette.creativeInk, flex: 1, fontSize: 14, minHeight: 48 },
});
