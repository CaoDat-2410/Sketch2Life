import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

const reasons = [
  'Chưa giống câu chuyện ba mẹ đã duyệt',
  'Nhân vật hoặc hình ảnh chưa phù hợp',
  'Chất lượng video chưa ổn',
  'Lý do khác',
] as const;

export function VideoSuitabilityReviewScreen({state, dispatch, onNavigate}: ParentFlowProps): React.JSX.Element {
  const canRegenerate = state.videoRegenerationCount < 2;
  const chooseReason = (value: string): void => dispatch({type: 'SET_VIDEO_REVIEW_REASON', value});

  return (
    <View style={styles.page}>
      <PreviewBanner title="Phản hồi video · bản xem trước" body="Chưa gửi đánh giá hoặc yêu cầu tạo lại lên máy chủ." />
      <ScreenIntro eyebrow="XEM LẠI KẾT QUẢ" title="Điều gì chưa ổn?" description="Ý kiến của ba mẹ giúp chọn đúng bước tiếp theo." />

      <ParentCard style={styles.reasonCard}>
        <View style={styles.progressRow}>
          <View><Text style={styles.counterLabel}>Lượt tạo lại</Text><Text style={styles.counterValue}>{state.videoRegenerationCount}/2</Text></View>
          <ParentPill label={canRegenerate ? 'CÒN LƯỢT' : 'ĐÃ ĐẠT GIỚI HẠN'} tone={canRegenerate ? 'green' : 'gold'} />
        </View>
        <View style={styles.reasonList} accessibilityRole="radiogroup">
          {reasons.map((reason) => {
            const selected = state.videoReviewReason === reason;
            return <Pressable key={reason} accessibilityRole="radio" accessibilityLabel={reason} accessibilityState={{selected}} onPress={() => chooseReason(reason)} style={[styles.reasonRow, selected ? styles.reasonSelected : undefined]}>
              <View style={[styles.radio, selected ? styles.radioSelected : undefined]}>{selected ? <View style={styles.radioDot}/> : null}</View>
              <Text style={[styles.reasonText, selected ? styles.reasonTextSelected : undefined]}>{reason}</Text>
              {selected ? <ParentIcon name="check" size={15} color={sketchColors.greenDark}/> : null}
            </Pressable>;
          })}
        </View>
      </ParentCard>

      <InfoBanner title="Video cũ chỉ ẩn khi được chấp nhận" body="Trong bản thật, máy chủ xác nhận yêu cầu trước khi video cũ bị ẩn. Nút dưới mô phỏng riêng trạng thái đã được chấp nhận." tone="warning" />

      {canRegenerate ? (
        <ParentButton title="Mô phỏng chấp nhận · xem lại kịch bản" icon="arrow" disabled={!state.videoReviewReason} onPress={() => dispatch({type: 'ACCEPT_VIDEO_REGEN_PREVIEW'})} />
      ) : (
        <>
          <InfoBanner title="Đã dùng hết hai lượt tạo lại" body="Ba mẹ vẫn có thể xem lại kịch bản, nhưng preview sẽ không mở thêm lượt tạo video." tone="warning" />
          <ParentButton title="Quay lại kịch bản" icon="arrow" disabled={!state.videoReviewReason} onPress={() => dispatch({type: 'RETURN_TO_STORY_AFTER_LIMIT'})} />
        </>
      )}
      <ParentButton title="Giữ video và quay lại" variant="quiet" onPress={() => onNavigate('video-player')} />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 14},
  reasonCard: {gap: 14, padding: 15},
  progressRow: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, paddingBottom: 12, borderBottomWidth: 1, borderColor: sketchColors.line},
  counterLabel: {color: sketchColors.muted, fontSize: 10, fontWeight: '700'},
  counterValue: {marginTop: 3, color: sketchColors.ink, fontSize: 20, fontWeight: '900'},
  reasonList: {gap: 7},
  reasonRow: {minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 10, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 13, backgroundColor: sketchColors.white},
  reasonSelected: {borderColor: sketchColors.green, backgroundColor: sketchColors.greenSoft},
  radio: {width: 20, height: 20, alignItems: 'center', justifyContent: 'center', borderWidth: 1.5, borderColor: sketchColors.line, borderRadius: 10},
  radioSelected: {borderColor: sketchColors.greenDark},
  radioDot: {width: 10, height: 10, borderRadius: 5, backgroundColor: sketchColors.greenDark},
  reasonText: {flex: 1, color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  reasonTextSelected: {color: sketchColors.greenDark, fontWeight: '800'},
});
