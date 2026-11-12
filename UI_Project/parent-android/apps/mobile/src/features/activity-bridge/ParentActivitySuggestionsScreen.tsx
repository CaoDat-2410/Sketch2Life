import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

const catalogSuggestions = [
  {id: 'catalog-garden-colors', title: 'Săn tìm sắc màu', source: 'Khám phá khu vườn · v1.4', reason: 'Cùng chủ đề thiên nhiên và quan sát màu sắc', time: '10 phút', safety: 'Đi cùng người lớn; không hái cây lạ.'},
  {id: 'catalog-butterfly', title: 'Theo dấu cánh bướm', source: 'Thế giới côn trùng · v2.1', reason: 'Gần với chủ thể con bướm trong câu chuyện', time: '8 phút', safety: 'Quan sát từ xa; không chạm vào côn trùng.'},
  {id: 'catalog-seed', title: 'Hạt mầm cần gì?', source: 'Hành trình của hạt mầm · v1.0', reason: 'Mở rộng chủ đề cây xanh bằng một hoạt động thực tế', time: '12 phút', safety: 'Người lớn chuẩn bị đất và nước.'},
] as const;

const temporaryDrafts = [
  {id: 'draft-notice', title: 'Tìm ba điều khác nhau', reason: 'Quan sát màu, hình và kích thước quanh nhà.'},
  {id: 'draft-draw', title: 'Vẽ tiếp câu chuyện', reason: 'Con thêm một chi tiết mới vào bức tranh.'},
  {id: 'draft-talk', title: 'Kể lại bằng lời của con', reason: 'Ba mẹ lắng nghe và hỏi một câu mở.'},
] as const;

type Mode = 'catalog' | 'fallback-gate' | 'fallback-drafts';

export function ParentActivitySuggestionsScreen({state, dispatch, onNavigate}: ParentFlowProps): React.JSX.Element {
  const [mode, setMode] = useState<Mode>('catalog');
  const [selectedId, setSelectedId] = useState<string | null>(state.suggestedActivityId);
  const [understandsFallback, setUnderstandsFallback] = useState(false);
  const useSuggestion = (id: string): void => {
    dispatch({type: 'SET_ACTIVITY_SUGGESTION', value: id});
    onNavigate('story-review');
  };

  return (
    <View style={styles.page}>
      <PreviewBanner title="Gợi ý trong bản xem trước" body="Danh mục mẫu chưa tải từ máy chủ; gợi ý chỉ xếp hạng nội dung có sẵn, không sửa giáo án." />
      <ScreenIntro eyebrow="TÙY CHỌN · TRƯỚC KỊCH BẢN" title="Chọn một ý tưởng chơi" description="Bước này có thể bỏ qua. Chọn theo giáo án đã chia sẻ, hoặc tiếp tục luôn." />

      {mode === 'catalog' ? (
        <>
          <View style={styles.sectionHeading}><View><Text style={styles.eyebrow}>DANH MỤC ĐÃ DUYỆT</Text><Text style={styles.sectionTitle}>Có thể hợp với con</Text></View><ParentPill label="3 gợi ý mẫu" tone="gray" /></View>
          {catalogSuggestions.map((item, index) => {
            const selected = selectedId === item.id;
            return (
              <Pressable key={item.id} accessibilityRole="radio" accessibilityState={{selected}} onPress={() => setSelectedId(item.id)}>
                <ParentCard style={[styles.suggestionCard, selected ? styles.selectedCard : undefined]}>
                  <View style={[styles.number, index === 1 ? styles.numberGold : undefined]}><Text style={styles.numberText}>0{index + 1}</Text></View>
                  <View style={styles.suggestionCopy}>
                    <View style={styles.titleRow}><Text style={styles.suggestionTitle}>{item.title}</Text>{selected ? <ParentIcon name="check" size={16}/> : null}</View>
                    <Text style={styles.source}>{item.source} · catalog đã chia sẻ · fixture</Text>
                    <Text style={styles.reason}>{item.reason}</Text>
                    <View style={styles.metaRow}><ParentPill label={item.time} tone="blue"/><ParentPill label="Có lưu ý an toàn" tone="green"/></View>
                  </View>
                </ParentCard>
              </Pressable>
            );
          })}
          {selectedId && catalogSuggestions.some((item) => item.id === selectedId) ? (
            <ParentButton title="Dùng ý tưởng này" icon="arrow" onPress={() => useSuggestion(selectedId)} />
          ) : null}
          <ParentButton title="Không có gợi ý phù hợp" variant="quiet" icon="help" onPress={() => { setUnderstandsFallback(false); setMode('fallback-gate'); }} />
          <ParentButton title="Bỏ qua · tiếp tục kịch bản" variant="secondary" onPress={() => { dispatch({type: 'SET_ACTIVITY_SUGGESTION', value: null}); onNavigate('story-review'); }} />
        </>
      ) : null}

      {mode === 'fallback-gate' ? (
        <>
          <ParentCard tone="gold" style={styles.gateCard}>
            <View style={styles.gateIcon}><ParentIcon name="lock" size={19} color="#806218"/></View>
            <Text style={styles.sectionTitle}>Chỉ dùng bản nháp khi danh mục không phù hợp</Text>
            <Text style={styles.body}>Theo hướng dẫn sản phẩm, hệ thống chỉ đề xuất đúng 3 bản tạm. Chúng không thay thế nội dung đã duyệt và phải được người lớn xem lại.</Text>
            <Text style={styles.openNote}>AI chưa kết nối trong preview; nút tiếp theo chỉ mở 3 ví dụ, không tạo nội dung thật.</Text>
            <Pressable accessibilityRole="checkbox" accessibilityState={{checked: understandsFallback}} onPress={() => setUnderstandsFallback((value) => !value)} style={styles.checkRow}>
              <View style={[styles.checkbox, understandsFallback ? styles.checkboxChecked : undefined]}>{understandsFallback ? <ParentIcon name="check" size={13} color={sketchColors.white}/> : null}</View>
              <Text style={styles.checkCopy}>Tôi hiểu đây chỉ là bản nháp tạm và chưa được duyệt.</Text>
            </Pressable>
          </ParentCard>
          <ParentButton title="Xem 3 bản nháp mẫu" icon="spark" disabled={!understandsFallback} onPress={() => setMode('fallback-drafts')} />
          <ParentButton title="Quay lại danh mục" variant="quiet" onPress={() => setMode('catalog')} />
        </>
      ) : null}

      {mode === 'fallback-drafts' ? (
        <>
          <InfoBanner title="3 ví dụ · không phải nội dung AI tạo" body="Chọn một để xem luồng; bản nháp chỉ tồn tại trong phiên preview và không đi vào danh mục." tone="warning" />
          {temporaryDrafts.map((draft, index) => (
            <Pressable key={draft.id} accessibilityRole="radio" accessibilityState={{selected: selectedId === draft.id}} onPress={() => setSelectedId(draft.id)}>
              <ParentCard style={[styles.draftCard, selectedId === draft.id ? styles.selectedCard : undefined]}>
                <View style={styles.draftIndex}><Text style={styles.numberText}>0{index + 1}</Text></View>
                <View style={styles.suggestionCopy}><View style={styles.titleRow}><Text style={styles.suggestionTitle}>{draft.title}</Text>{selectedId === draft.id ? <ParentIcon name="check" size={16}/> : null}</View><Text style={styles.reason}>{draft.reason}</Text><ParentPill label="BẢN NHÁP TẠM · PREVIEW" tone="gold"/></View>
              </ParentCard>
            </Pressable>
          ))}
          {temporaryDrafts.some((draft) => draft.id === selectedId) ? <ParentButton title="Tiếp tục kịch bản" icon="arrow" onPress={() => useSuggestion(selectedId as string)} /> : null}
          <ParentButton title="Trở lại danh mục" variant="secondary" onPress={() => { setSelectedId(null); setMode('catalog'); }} />
        </>
      ) : null}

      <ParentCard style={styles.boundaryCard}>
        <View style={styles.boundaryIcon}><ParentIcon name="book" size={16}/></View>
        <View style={styles.boundaryCopy}><Text style={styles.boundaryTitle}>Không đổi giáo án đã ghim</Text><Text style={styles.boundaryBody}>{state.activeRunLesson?.title ? `${state.activeRunLesson.title} vẫn được giữ nguyên.` : 'Giáo án được chọn cho run vẫn giữ nguyên.'} Hoạt động sau video là một bước khác.</Text></View>
      </ParentCard>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 13},
  sectionHeading: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginTop: 2},
  eyebrow: {color: sketchColors.muted, fontSize: 9, fontWeight: '900', letterSpacing: 1},
  sectionTitle: {color: sketchColors.ink, fontSize: 15, lineHeight: 21, fontWeight: '900'},
  suggestionCard: {flexDirection: 'row', alignItems: 'flex-start', gap: 11, padding: 13, borderWidth: 1},
  selectedCard: {borderColor: sketchColors.green, backgroundColor: '#F1F7EF'},
  number: {width: 38, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: sketchColors.greenSoft},
  numberGold: {backgroundColor: sketchColors.goldSoft},
  numberText: {color: sketchColors.greenDark, fontSize: 12, fontWeight: '900'},
  suggestionCopy: {flex: 1, gap: 5},
  titleRow: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8},
  suggestionTitle: {flex: 1, color: sketchColors.ink, fontSize: 12, lineHeight: 17, fontWeight: '900'},
  source: {color: sketchColors.muted, fontSize: 9, lineHeight: 14},
  reason: {color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  metaRow: {flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 2},
  gateCard: {gap: 10, padding: 16},
  gateIcon: {width: 39, height: 39, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: '#FFFFFFA8'},
  body: {color: sketchColors.inkSoft, fontSize: 11, lineHeight: 17},
  openNote: {padding: 10, borderRadius: 11, backgroundColor: '#FFFFFF9C', color: '#705A24', fontSize: 10, lineHeight: 15},
  checkRow: {minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 10},
  checkbox: {width: 22, height: 22, alignItems: 'center', justifyContent: 'center', borderRadius: 7, borderWidth: 1.5, borderColor: '#A88C4C', backgroundColor: sketchColors.white},
  checkboxChecked: {borderColor: sketchColors.green, backgroundColor: sketchColors.green},
  checkCopy: {flex: 1, color: sketchColors.ink, fontSize: 10, lineHeight: 15, fontWeight: '700'},
  draftCard: {flexDirection: 'row', alignItems: 'flex-start', gap: 10, padding: 12, borderWidth: 1},
  draftIndex: {width: 34, height: 34, alignItems: 'center', justifyContent: 'center', borderRadius: 11, backgroundColor: sketchColors.goldSoft},
  boundaryCard: {flexDirection: 'row', gap: 9, alignItems: 'flex-start', padding: 12},
  boundaryIcon: {width: 31, height: 31, alignItems: 'center', justifyContent: 'center', borderRadius: 10, backgroundColor: sketchColors.greenSoft},
  boundaryCopy: {flex: 1, gap: 3},
  boundaryTitle: {color: sketchColors.ink, fontSize: 10, fontWeight: '900'},
  boundaryBody: {color: sketchColors.muted, fontSize: 9, lineHeight: 14},
});
