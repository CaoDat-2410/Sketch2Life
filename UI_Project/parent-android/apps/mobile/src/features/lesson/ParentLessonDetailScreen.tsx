import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

export function ParentLessonDetailScreen({state, dispatch, onNavigate}: ParentFlowProps): React.JSX.Element {
  const title = state.activeRunLesson?.title ?? state.lessonTitle ?? 'Khu vườn tí hon';
  const id = state.activeRunLesson?.id ?? state.lessonId ?? 'lesson-garden';
  const version = state.activeRunLesson?.version ?? state.lessonVersion ?? 'Bản xem trước · v1';

  return (
    <View style={styles.page}>
      <PreviewBanner title="Chi tiết minh họa" body="Nguồn chia sẻ, quyền truy cập và phiên bản thật cần được máy chủ xác nhận." />
      <ScreenIntro eyebrow="GIÁO ÁN" title={title} description="Một điểm khởi đầu nhẹ nhàng để con quan sát, vẽ và kể chuyện." />
      <ParentCard tone="green" style={styles.cover}>
        <View style={styles.coverSun} /><View style={styles.coverHill} /><View style={styles.coverHillFront} />
        <Text style={styles.coverLabel}>CÙNG CON KHÁM PHÁ</Text>
      </ParentCard>
      <View style={styles.tags}><ParentPill label={version} /><ParentPill label="Thiên nhiên" tone="gold" /></View>
      <ParentCard style={styles.detailCard}>
        <Text style={styles.detailTitle}>Gợi ý trong bài</Text>
        <Text style={styles.detailBody}>Quan sát một điều con thích, để con vẽ theo cách riêng và tự đặt tên cho câu chuyện.</Text>
        <View style={styles.divider} />
        <Text style={styles.detailTitle}>Hoạt động sau video</Text>
        <Text style={styles.detailBody}>Bản thật sẽ hiển thị vật liệu, cách làm và ghi chú của từng hoạt động sau khi video đủ điều kiện phát.</Text>
      </ParentCard>
      <InfoBanner title="Phiên bản được ghim" body="Khi dùng giáo án, run sẽ tham chiếu đúng phiên bản này; bản cá nhân hóa không sửa giáo án gốc." />
      <ParentButton
        title="Dùng giáo án này"
        disabled={Boolean(state.activeRunChild)}
        onPress={() => {
          dispatch({type: 'SELECT_LESSON', id, title, version});
          onNavigate('run-setup');
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 16},
  cover: {position: 'relative', height: 150, overflow: 'hidden', justifyContent: 'flex-end', padding: 18},
  coverSun: {position: 'absolute', top: 19, right: 34, width: 48, height: 48, borderRadius: 30, backgroundColor: sketchColors.gold},
  coverHill: {position: 'absolute', right: -10, bottom: -55, width: 250, height: 115, borderRadius: 100, backgroundColor: '#C3DEC6'},
  coverHillFront: {position: 'absolute', left: -48, bottom: -78, width: 290, height: 112, borderRadius: 100, backgroundColor: '#A7C9AC'},
  coverLabel: {zIndex: 1, color: sketchColors.greenDark, fontSize: 10, fontWeight: '900', letterSpacing: 1.3},
  tags: {flexDirection: 'row', gap: 8},
  detailCard: {gap: 8},
  detailTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  detailBody: {color: sketchColors.muted, fontSize: 12, lineHeight: 18},
  divider: {height: 1, backgroundColor: sketchColors.line, marginVertical: 5},
});
