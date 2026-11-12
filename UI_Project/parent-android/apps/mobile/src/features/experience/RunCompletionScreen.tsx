import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

export function RunCompletionScreen({dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  return (
    <View style={styles.page}>
      <PreviewBanner title="Run chưa được lưu" body="Không có lịch sử hoàn tất thật; chưa gửi lệnh hoàn tất hay xóa lên máy chủ." />
      <View style={styles.celebration} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <View style={styles.confettiA}/><View style={styles.confettiB}/><View style={styles.confettiC}/><View style={styles.star}><ParentIcon name="check" size={28} color={sketchColors.greenDark}/></View>
      </View>
      <ScreenIntro eyebrow="KẾT THÚC LUỒNG MẪU" title="Một câu chuyện thật đẹp" description="Bản thật sẽ giữ run đến khi ba mẹ chọn hoàn tất hoặc tạo lại video." />
      <ParentCard style={styles.summary}>
        <View style={styles.summaryRow}><ParentIcon name="child"/><Text style={styles.summaryLabel}>Hồ sơ</Text><Text style={styles.summaryValue}>Được giữ riêng</Text></View>
        <View style={styles.summaryRow}><ParentIcon name="lock"/><Text style={styles.summaryLabel}>Chia sẻ</Text><Text style={styles.summaryValue}>Riêng tư</Text></View>
        <View style={styles.summaryRow}><ParentIcon name="history"/><Text style={styles.summaryLabel}>Lịch sử</Text><ParentPill label="Chưa kết nối" tone="gray"/></View>
      </ParentCard>
      <InfoBanner title="Xóa dữ liệu cần xác nhận riêng" body="Run, ảnh và media có lifecycle xóa riêng. Bản xem trước không chứa media và không thực hiện xóa thật." />
      <ParentButton title="Chia sẻ cảm nhận · tùy chọn" icon="heart" variant="secondary" onPress={() => onNavigate('session-feedback')} />
      <ParentButton title="Kết thúc · về trang chủ" icon="home" onPress={() => {
        dispatch({type: 'RESET_RUN'});
        onNavigate('home');
      }} />
      <ParentButton title="Xem lịch sử" variant="quiet" onPress={() => onNavigate('history')} />
      <ParentButton title="Tìm hiểu xóa dữ liệu" variant="quiet" onPress={() => onNotice('Hủy và xóa run cần API riêng; không có dữ liệu nào bị xóa trong bản này.')} />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  celebration: {position: 'relative', height: 96, alignItems: 'center', justifyContent: 'center'},
  star: {width: 67, height: 67, alignItems: 'center', justifyContent: 'center', borderRadius: 25, backgroundColor: sketchColors.goldSoft, transform: [{rotate: '-7deg'}]},
  confettiA: {position: 'absolute', top: 21, left: '22%', width: 10, height: 18, borderRadius: 5, backgroundColor: '#79A88A', transform: [{rotate: '25deg'}]},
  confettiB: {position: 'absolute', top: 29, right: '24%', width: 9, height: 16, borderRadius: 5, backgroundColor: '#E7BD5B', transform: [{rotate: '-28deg'}]},
  confettiC: {position: 'absolute', bottom: 8, right: '35%', width: 8, height: 14, borderRadius: 5, backgroundColor: '#D8937A', transform: [{rotate: '31deg'}]},
  summary: {gap: 13},
  summaryRow: {minHeight: 29, flexDirection: 'row', alignItems: 'center', gap: 9},
  summaryLabel: {flex: 1, color: sketchColors.inkSoft, fontSize: 11, fontWeight: '700'},
  summaryValue: {color: sketchColors.ink, fontSize: 10, fontWeight: '800'},
});
