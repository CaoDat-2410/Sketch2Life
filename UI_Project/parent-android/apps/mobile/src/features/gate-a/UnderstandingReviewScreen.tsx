import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentField, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

export function UnderstandingReviewScreen({state, dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  return (
    <View style={styles.page}>
      <PreviewBanner title="Kết quả nhận diện minh họa" body="Chưa phân tích ảnh; tên chủ thể bên dưới là dữ liệu mẫu để xem cổng duyệt." />
      <ScreenIntro eyebrow="BƯỚC 3 · BA MẸ DUYỆT" title="Con đã vẽ gì nhỉ?" description="Xem chủ thể gợi ý rồi sửa nếu chưa đúng với tranh của con." />
      <ParentCard style={styles.artCard}>
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.imageMock}>
          <View style={styles.imageSun}/><View style={styles.imageWingLeft}/><View style={styles.imageWingRight}/><View style={styles.imageBody}/><View style={styles.imageFlower}/><View style={styles.imageGrass}/>
        </View>
        <View style={styles.imageCaption}><ParentIcon name="camera" size={17}/><Text style={styles.imageCaptionText}>Ảnh tranh · bản mẫu</Text></View>
      </ParentCard>
      <ParentCard tone="green" style={styles.subjectCard}>
        <View style={styles.subjectHeader}><Text style={styles.fieldLabel}>CHỦ THỂ ĐƯỢC GỢI Ý</Text><ParentPill label="Cần ba mẹ xác nhận" tone="gold"/></View>
        <ParentField
          label="Tên chủ thể"
          value={state.subject}
          onChangeText={(value) => dispatch({type: 'SET_SUBJECT', value})}
          placeholder="Ví dụ: chú bướm"
        />
        <Text style={styles.hint}>Độ chắc chắn sẽ được hiển thị khi có kết quả từ hệ thống.</Text>
      </ParentCard>
      <InfoBanner title="Sửa chủ thể sẽ tạo revision mới" body="Bản thật sẽ chạy lại bước hiểu tranh. Không tự chuyển qua nếu ba mẹ chưa xem." />
      <ParentButton title="Xác nhận chủ thể xem trước" icon="check" onPress={() => onNavigate('context')} />
      <ParentButton title="Yêu cầu hiểu lại tranh" variant="secondary" onPress={() => onNotice('Bước phân tích tranh chưa kết nối; chưa tạo revision mới.')} />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  artCard: {padding: 9},
  imageMock: {height: 193, overflow: 'hidden', alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: '#F2F1E7'},
  imageSun: {position: 'absolute', top: 28, right: 45, width: 34, height: 34, borderRadius: 18, backgroundColor: '#EFC65D'},
  imageWingLeft: {position: 'absolute', width: 60, height: 40, left: '25%', top: 78, borderRadius: 36, backgroundColor: '#D88F7A', transform: [{rotate: '-20deg'}]},
  imageWingRight: {position: 'absolute', width: 60, height: 40, right: '25%', top: 78, borderRadius: 36, backgroundColor: '#9BB8D1', transform: [{rotate: '20deg'}]},
  imageBody: {position: 'absolute', top: 78, width: 10, height: 60, borderRadius: 8, backgroundColor: '#496F5D'},
  imageFlower: {position: 'absolute', bottom: 31, left: '27%', width: 21, height: 21, borderRadius: 13, backgroundColor: '#E7BD5B'},
  imageGrass: {position: 'absolute', bottom: 25, width: '68%', height: 2, backgroundColor: '#89AA8D'},
  imageCaption: {flexDirection: 'row', alignItems: 'center', gap: 7, padding: 10},
  imageCaptionText: {color: sketchColors.muted, fontSize: 10, fontWeight: '700'},
  subjectCard: {gap: 10},
  subjectHeader: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 6},
  fieldLabel: {color: sketchColors.muted, fontSize: 9, fontWeight: '900', letterSpacing: 1},
  hint: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
});
