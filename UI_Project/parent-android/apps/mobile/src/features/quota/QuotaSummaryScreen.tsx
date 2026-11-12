import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

export function QuotaSummaryScreen({onNotice, onNavigate}: ParentFlowProps): React.JSX.Element {
  return (
    <View style={styles.page}>
      <PreviewBanner title="Chưa có số dư lượt tạo" body="Không dùng con số giả hoặc dự đoán gói của tài khoản." />
      <ScreenIntro eyebrow="MINH BẠCH SỬ DỤNG" title="Lượt tạo & giới hạn" description="Thông tin sẽ được đọc từ nguồn tính quota chính thức khi API sẵn sàng." />
      <ParentCard style={styles.balance}>
        <View style={styles.balanceTop}><View style={styles.quotaIcon}><ParentIcon name="quota" size={22}/></View><ParentPill label="CHƯA KẾT NỐI" tone="gray"/></View>
        <Text style={styles.balanceLabel}>Số lượt còn lại</Text>
        <Text style={styles.balanceValue}>—</Text>
        <Text style={styles.balanceHint}>Số dư sẽ hiện ở đây sau khi tải thành công.</Text>
      </ParentCard>
      <ParentCard style={styles.ruleCard}>
        <Text style={styles.ruleTitle}>Điều cần biết</Text>
        <Rule label="Một yêu cầu video được nhận" detail="được tính theo quy tắc billing của hệ thống."/>
        <Rule label="Lỗi kỹ thuật hoặc safety" detail="không tự động hoàn quota theo SRS hiện tại."/>
        <Rule label="Gói, giá và thứ tự trừ" detail="chưa chốt; không mua thêm trong bản này."/>
      </ParentCard>
      <InfoBanner title="Không thực hiện giao dịch" body="Trang này chỉ trình bày vị trí cho số liệu quota; thanh toán và mua gói chưa được tích hợp." tone="warning" />
      <ParentButton title="Tải lại thông tin" icon="arrow" variant="secondary" onPress={() => onNotice('Quota API chưa kết nối; không có yêu cầu tải lại được gửi.')} />
      <ParentButton title="Xem run gần đây" variant="quiet" onPress={() => onNavigate('history')} />
    </View>
  );
}

function Rule({label, detail}: Readonly<{label: string; detail: string}>): React.JSX.Element {
  return <View style={styles.rule}><View style={styles.bullet}/><View style={styles.ruleCopy}><Text style={styles.ruleLabel}>{label}</Text><Text style={styles.ruleDetail}>{detail}</Text></View></View>;
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  balance: {gap: 9, padding: 17},
  balanceTop: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between'},
  quotaIcon: {width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: sketchColors.blueSoft},
  balanceLabel: {color: sketchColors.muted, fontSize: 11, fontWeight: '700', marginTop: 4},
  balanceValue: {color: sketchColors.ink, fontSize: 34, fontWeight: '900', lineHeight: 40},
  balanceHint: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
  ruleCard: {gap: 13},
  ruleTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  rule: {flexDirection: 'row', alignItems: 'flex-start', gap: 9},
  bullet: {width: 7, height: 7, marginTop: 4, borderRadius: 4, backgroundColor: sketchColors.green},
  ruleCopy: {flex: 1, gap: 2},
  ruleLabel: {color: sketchColors.ink, fontSize: 11, fontWeight: '800'},
  ruleDetail: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
});
