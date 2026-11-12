import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentField, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

export function LessonFeedbackScreen({state, dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  const lessonTitle = state.activeRunLesson?.title ?? state.lessonTitle;
  const [previewEntry, setPreviewEntry] = useState<Readonly<{rating: number; note: string}> | null>(null);
  const canSubmit = Boolean(lessonTitle) && (state.feedbackRating > 0 || state.feedbackNote.trim().length > 0);
  return (
    <View style={styles.page}>
      <PreviewBanner title="Chưa gửi phản hồi" body="Chưa có API, giáo án thật hoặc phản hồi của giáo viên được tải." />
      <ScreenIntro eyebrow="PHẢN HỒI RIÊNG TƯ" title="Gửi lời nhắn về giáo án" description="Phản hồi gắn với lesson và hồ sơ được chia sẻ; đây không phải cuộc trò chuyện." />
      <ParentCard style={styles.lessonRef}>
        <View style={styles.bookIcon}><ParentIcon name="book" size={20}/></View>
        <View style={styles.lessonCopy}><Text style={styles.lessonLabel}>GIÁO ÁN ĐANG CHỌN</Text><Text style={styles.lessonTitle}>{lessonTitle ?? 'Chưa chọn giáo án'}</Text></View>
      </ParentCard>
      {!lessonTitle ? <InfoBanner title="Chưa chọn giáo án" body="Chọn giáo án trước để phản hồi gắn đúng nội dung và phiên bản." tone="warning"/> : null}
      {previewEntry ? <ParentCard tone="green" style={styles.previewEntry}>
        <View style={styles.previewEntryHead}><View><Text style={styles.previewEntryEyebrow}>BẢN NHÁP TRONG PHIÊN</Text><Text style={styles.previewEntryTitle}>Đã ghi nhận phản hồi mẫu</Text></View><ParentPill label="CHƯA GỬI" tone="gold"/></View>
        <Text style={styles.previewEntryBody}>Đánh giá: {previewEntry.rating ? `${previewEntry.rating}/5` : 'Chưa chấm sao'}</Text>
        {previewEntry.note ? <Text style={styles.previewEntryBody}>{previewEntry.note}</Text> : null}
        <Text style={styles.previewEntryFoot}>Chưa gửi đến giáo viên hoặc lưu trên máy chủ.</Text>
        <ParentButton title="Chỉnh sửa phản hồi" variant="secondary" onPress={() => setPreviewEntry(null)}/>
      </ParentCard> : null}
      <ParentCard style={styles.form}>
        <Text style={styles.formTitle}>Ba mẹ thấy thế nào?</Text>
        <View accessibilityRole="radiogroup" style={styles.ratingRow}>
          {[1, 2, 3, 4, 5].map((rating) => (
            <Pressable
              key={rating}
              accessibilityRole="radio"
              accessibilityLabel={`${rating} trên 5`}
              accessibilityState={{selected: state.feedbackRating === rating}}
              onPress={() => dispatch({type: 'SET_FEEDBACK_RATING', value: rating})}
              style={[styles.ratingButton, state.feedbackRating === rating ? styles.ratingSelected : undefined]}>
              <Text style={[styles.ratingText, state.feedbackRating === rating ? styles.ratingTextSelected : undefined]}>{rating}</Text>
            </Pressable>
          ))}
        </View>
        <ParentField
          label="Điều ba mẹ muốn chia sẻ"
          multiline
          numberOfLines={4}
          value={state.feedbackNote}
          onChangeText={(value) => dispatch({type: 'SET_FEEDBACK_NOTE', value})}
          placeholder="Nội dung có ích cho lần sau..."
        />
        <ParentButton title="Lưu phản hồi mẫu" icon="send" disabled={!canSubmit} onPress={() => {
          setPreviewEntry({rating: state.feedbackRating, note: state.feedbackNote.trim()});
          onNotice('Đã ghi nhận phản hồi trong phiên preview; chưa gửi đến giáo viên.');
        }} />
        {!lessonTitle ? <ParentButton title="Chọn giáo án" variant="quiet" icon="book" onPress={() => onNavigate('lesson-library')}/> : null}
      </ParentCard>
      <InfoBanner title="Phản hồi không gửi tranh của con" body="Bản thật không dùng feedback để gửi media trẻ em và không tạo chat trực tiếp." />
      <ParentCard style={styles.replyCard}>
        <View style={styles.replyIcon}><ParentIcon name="notifications" size={18}/></View>
        <View style={styles.replyCopy}><Text style={styles.replyTitle}>Theo dõi hồi đáp</Text><Text style={styles.replyBody}>Trạng thái và hồi đáp của giáo viên sẽ hiển thị tại đây khi dịch vụ sẵn sàng.</Text></View>
      </ParentCard>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  lessonRef: {flexDirection: 'row', alignItems: 'center', gap: 10},
  bookIcon: {width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: sketchColors.greenSoft},
  lessonCopy: {flex: 1, gap: 4},
  lessonLabel: {color: sketchColors.muted, fontSize: 8, fontWeight: '900', letterSpacing: 1},
  lessonTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  form: {gap: 13},
  formTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  ratingRow: {flexDirection: 'row', justifyContent: 'space-between', gap: 8},
  ratingButton: {width: 45, height: 45, alignItems: 'center', justifyContent: 'center', borderRadius: 15, borderWidth: 1, borderColor: sketchColors.line, backgroundColor: sketchColors.white},
  ratingSelected: {borderColor: sketchColors.green, backgroundColor: sketchColors.greenSoft},
  ratingText: {color: sketchColors.muted, fontSize: 15, fontWeight: '800'},
  ratingTextSelected: {color: sketchColors.greenDark},
  replyCard: {flexDirection: 'row', alignItems: 'center', gap: 10},
  previewEntry: {gap: 9, padding: 13},
  previewEntryHead: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8},
  previewEntryEyebrow: {color: sketchColors.greenDark, fontSize: 8, fontWeight: '900', letterSpacing: 1},
  previewEntryTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900', marginTop: 3},
  previewEntryBody: {color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  previewEntryFoot: {color: sketchColors.muted, fontSize: 9, lineHeight: 14},
  replyIcon: {width: 36, height: 36, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: sketchColors.blueSoft},
  replyCopy: {flex: 1, gap: 4},
  replyTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '900'},
  replyBody: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
});
