import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

const sampleActivities = [
  {number: '01', title: 'Săn tìm sắc màu', materials: '3 vật có màu khác nhau', steps: 'Cùng con tìm màu trong sân hoặc công viên, rồi để con kể vì sao chọn chúng.', note: 'Đi cùng người lớn; tránh hái cây lạ.'},
  {number: '02', title: 'Vườn nhỏ của bé', materials: 'Cốc giấy, đất sạch, hạt dễ trồng', steps: 'Trang trí cốc, gieo hạt và quan sát mỗi ngày.', note: 'Người lớn chuẩn bị đất và nước.'},
];

export function ActivityRecommendationsScreen({onNavigate}: ParentFlowProps): React.JSX.Element {
  return (
    <View style={styles.page}>
      <PreviewBanner title="Hoạt động minh họa" body="Chưa tải danh sách từ lesson đã ghim. Đây là bản mẫu để xem nội dung sau video." />
      <ScreenIntro eyebrow="CÙNG CON RỜI MÀN HÌNH" title="Tiếp tục khám phá" description="Hoạt động ngoài trời sẽ chỉ xuất hiện sau video playable và lấy từ đúng phiên bản giáo án." />
      <View style={styles.activities}>
        {sampleActivities.map((activity, index) => (
          <ParentCard key={activity.number} style={styles.activityCard}>
            <View style={styles.activityHeader}><View style={[styles.numberBlock, index ? styles.numberAlt : undefined]}><Text style={styles.numberText}>{activity.number}</Text></View><View style={styles.headerCopy}><ParentPill label="MẪU · CHƯA ĐƯỢC DUYỆT" tone="gold"/><Text style={styles.activityTitle}>{activity.title}</Text></View></View>
            <View style={styles.infoRow}><View style={styles.infoIcon}><ParentIcon name="plus" size={15}/></View><View style={styles.infoCopy}><Text style={styles.infoLabel}>CẦN CHUẨN BỊ</Text><Text style={styles.infoText}>{activity.materials}</Text></View></View>
            <View style={styles.infoRow}><View style={styles.infoIcon}><ParentIcon name="arrow" size={15}/></View><View style={styles.infoCopy}><Text style={styles.infoLabel}>CÁCH LÀM</Text><Text style={styles.infoText}>{activity.steps}</Text></View></View>
            <View style={styles.note}><ParentIcon name="help" size={14} color="#806218"/><Text style={styles.noteText}>{activity.note}</Text></View>
          </ParentCard>
        ))}
      </View>
      <InfoBanner title="Không có nút hoàn thành hoạt động" body="SRS hiện không yêu cầu theo dõi việc hoàn thành ngoài trời trong ứng dụng Parent." />
      <ParentButton title="Xong · kết thúc bản xem trước" icon="check" onPress={() => onNavigate('completion')} />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  activities: {gap: 11},
  activityCard: {gap: 13, padding: 14},
  activityHeader: {flexDirection: 'row', alignItems: 'center', gap: 11},
  numberBlock: {width: 43, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: sketchColors.greenSoft},
  numberAlt: {backgroundColor: sketchColors.goldSoft},
  numberText: {color: sketchColors.greenDark, fontSize: 13, fontWeight: '900'},
  headerCopy: {flex: 1, gap: 6},
  activityTitle: {color: sketchColors.ink, fontSize: 14, fontWeight: '900'},
  infoRow: {flexDirection: 'row', alignItems: 'flex-start', gap: 9},
  infoIcon: {width: 28, height: 28, alignItems: 'center', justifyContent: 'center', borderRadius: 10, backgroundColor: '#F0F4EE'},
  infoCopy: {flex: 1, gap: 3},
  infoLabel: {color: sketchColors.muted, fontSize: 8, fontWeight: '900', letterSpacing: 1},
  infoText: {color: sketchColors.inkSoft, fontSize: 11, lineHeight: 16},
  note: {flexDirection: 'row', alignItems: 'flex-start', gap: 7, padding: 10, borderRadius: 12, backgroundColor: sketchColors.goldSoft},
  noteText: {flex: 1, color: '#705A24', fontSize: 10, lineHeight: 15},
});
