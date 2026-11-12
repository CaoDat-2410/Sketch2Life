import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentField, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

const suggestedActivityLabels: Readonly<Record<string, string>> = {
  'catalog-garden-colors': 'Săn tìm sắc màu',
  'catalog-butterfly': 'Theo dấu cánh bướm',
  'catalog-seed': 'Hạt mầm cần gì?',
  'draft-notice': 'Tìm ba điều khác nhau',
  'draft-draw': 'Vẽ tiếp câu chuyện',
  'draft-talk': 'Kể lại bằng lời của con',
};

const scenes = [
  ['01', 'Một nét vẽ thức dậy', 'Chú bướm nhỏ mở đôi cánh trong khu vườn.'],
  ['02', 'Tìm màu nắng', 'Bạn ấy bay qua những chiếc lá xanh.'],
  ['03', 'Gặp một người bạn', 'Một bông hoa chỉ đường đến luống hoa mới.'],
  ['04', 'Cùng chăm khu vườn', 'Chú bướm và bạn cùng tưới những mầm cây.'],
  ['05', 'Nhà của niềm vui', 'Cả khu vườn rực lên màu sắc của tình bạn.'],
] as const;

export function StoryReviewScreen({state, dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  return (
    <View style={styles.page}>
      <PreviewBanner title="Storyboard mẫu · chưa được AI tạo" body="Nội dung này chỉ minh họa màn duyệt, chưa dựa trên tranh hay hồ sơ thật." />
      <ScreenIntro eyebrow="BƯỚC 5 · BA MẸ DUYỆT" title="Câu chuyện của con" description="Ba mẹ xem toàn bộ kịch bản trước khi xác nhận tạo video." />
      {state.videoReviewReason ? <InfoBanner title="Đang xem lại sau phản hồi video" body={`Lý do: ${state.videoReviewReason}. ${state.videoRegenerationCount}/2 lượt được mô phỏng; video cũ ${state.previousVideoHidden ? 'đã ẩn trong preview' : 'vẫn còn trong preview'}. ${state.videoRegenerationPending ? 'Hãy xem lại kịch bản trước khi mô phỏng kết quả.' : state.videoRegenerationCount >= 2 ? 'Đã đạt giới hạn; không thể mở thêm lượt.' : ''}`} tone="warning"/> : null}
      {state.runCancelPending ? <InfoBanner title="Run đang chờ máy chủ xử lý hủy" body="Kịch bản được giữ nguyên; không thể xác nhận hoặc tạo video mới trong lúc chờ." tone="warning"/> : null}
      {state.suggestedActivityId && suggestedActivityLabels[state.suggestedActivityId] ? <ParentCard tone="muted" style={styles.suggestionSummary}>
        <View style={styles.suggestionIcon}><ParentIcon name="spark" size={16}/></View>
        <View style={styles.suggestionCopy}><Text style={styles.suggestionEyebrow}>Ý TƯỞNG TÙY CHỌN · CHƯA GHIM</Text><Text style={styles.suggestionTitle}>{suggestedActivityLabels[state.suggestedActivityId]}</Text><Text style={styles.suggestionHint}>Không thay đổi giáo án. Ba mẹ có thể bỏ qua hoặc chọn lại trước khi bắt đầu.</Text></View>
      </ParentCard> : null}
      <View style={styles.storyMeta}><ParentPill label="5 cảnh minh họa"/><ParentPill label={`Viết lại ${state.rewriteCount}/3`} tone="gold"/></View>
      <View style={styles.sceneList}>
        {scenes.map(([number, title, description], index) => (
          <ParentCard key={number} style={styles.sceneCard}>
            <View style={[styles.sceneArt, {backgroundColor: index % 2 ? '#E7F0E5' : '#F8EFD5'}]}>
              <View style={styles.sceneOrb}/><View style={styles.sceneMark}/><Text style={styles.sceneNumber}>{number}</Text>
            </View>
            <View style={styles.sceneCopy}><Text style={styles.sceneTitle}>{title}</Text><Text style={styles.sceneDescription}>{description}</Text></View>
          </ParentCard>
        ))}
      </View>
      <ParentCard style={styles.rewriteCard}>
        <Text style={styles.rewriteTitle}>Muốn đổi hướng kể?</Text>
        <Text style={styles.rewriteHint}>Ba mẹ gợi ý bằng lời; không sửa trực tiếp từng cảnh.</Text>
        <ParentField
          label="Gợi ý cho AI · chưa gửi"
          value={state.rewritePrompt}
          onChangeText={(value) => dispatch({type: 'SET_REWRITE_PROMPT', value})}
          placeholder="Ví dụ: kể vui hơn và thêm bạn ong"
        />
        <ParentButton title="Yêu cầu AI viết lại" variant="secondary" disabled={state.rewriteCount >= 3} onPress={() => {
          dispatch({type: 'REQUEST_REWRITE_PREVIEW'});
          onNotice('AI chưa kết nối; yêu cầu chưa gửi và bộ đếm không đổi.');
        }} />
      </ParentCard>
      <InfoBanner title="Revision cũ có thể không còn hợp lệ" body="Bản thật sẽ kiểm tra đúng revision tranh, context, lesson và storyboard. Nếu dữ liệu thay đổi, ba mẹ cần xem bản mới trước khi xác nhận." tone="warning" />
      <InfoBanner title="Xác nhận kịch bản là cổng bắt buộc" body="Sau khi xác nhận trong sản phẩm thật, mới được gửi yêu cầu tạo video. Mọi revision đều cần xem lại." />
      <ParentButton title="Quay lại duyệt chủ thể" variant="quiet" onPress={() => onNavigate('understanding')} />
      <ParentButton title="Xác nhận kịch bản · xem luồng mẫu" icon="check" disabled={state.runCancelPending || (state.videoReviewReason.length > 0 && state.videoRegenerationCount >= 2 && !state.videoRegenerationPending)} onPress={() => {
        dispatch({type: 'CONFIRM_STORY'});
        onNavigate('generation');
      }} />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 16},
  storyMeta: {flexDirection: 'row', gap: 8},
  suggestionSummary: {flexDirection: 'row', alignItems: 'flex-start', gap: 9, padding: 12},
  suggestionIcon: {width: 32, height: 32, alignItems: 'center', justifyContent: 'center', borderRadius: 11, backgroundColor: sketchColors.white},
  suggestionCopy: {flex: 1, gap: 3},
  suggestionEyebrow: {color: sketchColors.muted, fontSize: 7, fontWeight: '900', letterSpacing: 0.8},
  suggestionTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '900'},
  suggestionHint: {color: sketchColors.muted, fontSize: 9, lineHeight: 14},
  sceneList: {gap: 9},
  sceneCard: {flexDirection: 'row', gap: 12, alignItems: 'center', padding: 10},
  sceneArt: {width: 58, height: 58, overflow: 'hidden', alignItems: 'center', justifyContent: 'center', borderRadius: 16},
  sceneOrb: {position: 'absolute', top: 8, right: 8, width: 15, height: 15, borderRadius: 8, backgroundColor: '#E8BE5C'},
  sceneMark: {width: 24, height: 20, borderLeftWidth: 3, borderBottomWidth: 3, borderColor: '#5C936F', transform: [{rotate: '-35deg'}]},
  sceneNumber: {position: 'absolute', left: 7, bottom: 5, color: '#567566', fontSize: 8, fontWeight: '900'},
  sceneCopy: {flex: 1, gap: 4},
  sceneTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  sceneDescription: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
  rewriteCard: {gap: 10},
  rewriteTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  rewriteHint: {color: sketchColors.muted, fontSize: 10},
});
