import React, { useState } from 'react';
import { Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { CatDrawingArtwork } from '../components/ArtworkCards';
import { colors, shadows } from '../theme';
import { useAppContext } from '../context/AppContext';
import type { ScreenId } from '../types';
import {
  ParentFlowHeader as Header,
  ParentFlowProgress as Progress,
  ParentFlowPrimary as Primary,
  ParentFlowNotice as SoftNotice,
} from '../components/ParentFlowShell';

interface ScreenProps { onNavigate?: (screen: ScreenId) => void; }

export const ActivitySelectionScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const [selected, setSelected] = useState('park');
  const activities = [['ball', 'Chơi bóng', '15 phút', 'football-outline'], ['bike', 'Đạp xe', '20 phút', 'bicycle-outline'], ['kite', 'Thả diều', '25 phút', 'paper-plane-outline'], ['park', 'Dạo công viên', '20 phút', 'leaf-outline']];
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Chọn hoạt động" onBack={goBack} /><Progress label="Bước 1 / 3 · Hoạt động ngoài trời" percent={33} />
    <Text style={styles.title}>Hoạt động nào hợp với câu chuyện?</Text><Text style={styles.subtitle}>Chỉ hiển thị hoạt động ngoài trời đã được duyệt cho độ tuổi của {selectedChild.name}.</Text>
    <View style={styles.activityGrid}>{activities.map(([id, name, duration, icon]) => <TouchableOpacity key={id} accessibilityRole="radio" accessibilityState={{ selected: selected === id }} activeOpacity={0.84} onPress={() => setSelected(id)} style={[styles.activityCard, selected === id && styles.activityCardActive]}><View style={[styles.activityEmoji, selected === id && styles.activityEmojiActive]}><Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={25} color={selected === id ? colors.blueDeep : colors.yellowDeep} /></View><Text style={styles.activityTitle}>{name}</Text><Text style={styles.activityMeta}>{duration} · An toàn đã duyệt</Text>{selected === id && <View style={styles.selectedMark}><Ionicons name="checkmark" size={12} color={colors.white} /></View>}</TouchableOpacity>)}</View>
    <SoftNotice icon="shield-checkmark-outline" tone="green">Danh mục và giới hạn an toàn được quản lý bởi hệ thống. Phụ huynh không nhập hoạt động riêng trong flow này.</SoftNotice>
    <Primary label="Tiếp tục duyệt ngữ cảnh" onPress={() => nav('activity_context_review')} />
  </ScrollView>;
};

export const ActivityContextReviewScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const rows = [['Hồ sơ trẻ', `${selectedChild.name} · ${selectedChild.age} tuổi`], ['Chủ thể', 'Mèo, quả bóng'], ['Hoạt động', 'Dạo công viên'], ['Bối cảnh', 'Công viên gần nhà'], ['Phong cách', 'Vui vẻ, khám phá']];
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Duyệt ngữ cảnh" onBack={goBack} /><Progress label="Bước 2 / 3 · Context snapshot" percent={66} />
    <Text style={styles.title}>Kiểm tra thông tin trước khi tạo story</Text><Text style={styles.subtitle}>Snapshot tối thiểu này sẽ được ghim cho run hiện tại. Bạn có thể quay lại sửa trước khi AI tạo nội dung.</Text>
    <View style={styles.contextCard}>{rows.map(([label, value]) => <View key={label} style={styles.contextRow}><View style={styles.contextIcon}><Ionicons name={label === 'Hồ sơ trẻ' ? 'person-outline' : label === 'Hoạt động' ? 'walk-outline' : 'sparkles-outline'} size={16} color={colors.blueDeep} /></View><View style={{ flex: 1 }}><Text style={styles.contextLabel}>{label}</Text><Text style={styles.contextValue}>{value}</Text></View><Ionicons name="checkmark-circle" size={18} color={colors.greenDeep} /></View>)}</View>
    <SoftNotice icon="lock-closed-outline">Không gửi tên, ghi chú nhạy cảm hoặc dữ liệu ngoài phạm vi snapshot cho model.</SoftNotice>
    <Primary label="Xác nhận và tạo story" onPress={() => nav('ai_processing')} />
  </ScrollView>;
};

export const ParentAiProcessingScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Đang hiểu tranh" onBack={goBack} /><Progress label="Xử lý bất đồng bộ · Bạn có thể rời màn hình" percent={62} />
    <View style={styles.processingHero}><View style={styles.processingOrb}><Ionicons name="sparkles" size={34} color={colors.yellowDeep} /></View><Text style={styles.processingTitle}>Đang tạo câu chuyện cho {selectedChild.name}</Text><Text style={styles.processingSubtitle}>Hệ thống đang kết hợp tranh, transcript, chủ thể và context đã xác nhận.</Text></View>
    <View style={styles.stageList}>{[['checkmark-circle', 'Hiểu chủ thể trong tranh', 'Đã hoàn tất'], ['checkmark-circle', 'Tạo story và storyboard', 'Đã hoàn tất'], ['ellipse-outline', 'Chuẩn bị bản duyệt script', 'Đang xử lý'], ['ellipse-outline', 'Chờ phụ huynh xác nhận', 'Tiếp theo']].map(([icon, label, status], index) => <View key={label} style={styles.stageRow}><Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={20} color={index < 2 ? colors.greenDeep : colors.blueDeep} /><View style={{ flex: 1 }}><Text style={styles.stageTitle}>{label}</Text><Text style={styles.stageStatus}>{status}</Text></View></View>)}</View>
    <SoftNotice icon="notifications-outline" tone="amber">Khi backend hoạt động, bạn có thể đóng app và quay lại từ thông báo. Hiện tại nút dưới đây mô phỏng kết quả.</SoftNotice>
    <Primary label="Mở bản story để duyệt" onPress={() => nav('story_review')} />
  </ScrollView>;
};

export const StoryReviewScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Nội dung câu chuyện" onBack={goBack} /><Progress label="Bước 3 / 3 · Story draft" percent={100} />
    <Text style={styles.title}>Cùng chú mèo dạo công viên</Text><Text style={styles.subtitle}>Bản đầu tiên do AI tạo từ tranh và ý tưởng đã xác nhận. Bạn có thể yêu cầu viết lại, không sửa trực tiếp từng scene.</Text>
    <View style={styles.storyCard}><Text style={styles.storyText}>Chú mèo nhỏ ôm quả bóng bước vào công viên. Gió thổi qua những tán cây, còn chú thì tìm một người bạn để cùng chơi. Một ngày mới bắt đầu bằng một chuyến phiêu lưu thật vui.</Text><View style={styles.storyFooter}><Text style={styles.revisionText}>Revision 1 / 4</Text><Text style={styles.sceneCount}>5 cảnh dự kiến</Text></View></View>
    <TouchableOpacity accessibilityRole="button" onPress={() => {}} style={styles.rewriteButton}><Ionicons name="refresh-outline" size={18} color={colors.blueDeep} /><Text style={styles.rewriteText}>Yêu cầu AI viết lại theo gợi ý</Text></TouchableOpacity>
    <SoftNotice icon="information-circle-outline">Bạn chỉ cần duyệt hướng kể. Text và scene sẽ được xác nhận ở bước storyboard/script.</SoftNotice>
    <Primary label="Xem storyboard" onPress={() => nav('storyboard')} />
  </ScrollView>;
};

export const StoryboardScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;
  const scenes = [['Cảnh 1', 'Bước vào công viên', 'Chú mèo ôm quả bóng đi qua cổng xanh.'], ['Cảnh 2', 'Gặp người bạn mới', 'Một chú chim nhỏ đáp xuống bên cạnh.'], ['Cảnh 3', 'Cùng chơi bóng', 'Hai người bạn chuyền bóng dưới tán cây.'], ['Cảnh 4', 'Cơn gió bất ngờ', 'Quả bóng bay lên và cả hai cùng chạy theo.'], ['Cảnh 5', 'Một ngày thật vui', 'Chú mèo mang câu chuyện về kể cho gia đình.']];
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Storyboard" onBack={goBack} action={<Text style={styles.headerMeta}>5 / 5</Text>} /><Text style={styles.title}>Duyệt 5 cảnh của câu chuyện</Text><Text style={styles.subtitle}>Storyboard có thể từ 5 đến 15 cảnh. Đây là bản xem trước trước khi xác nhận script.</Text>
    <View style={styles.storyboardList}>{scenes.map(([number, title, body]) => <View key={number} style={styles.sceneCard}><View style={styles.sceneThumb}><Text style={styles.sceneNumber}>{number}</Text><Ionicons name="image-outline" size={25} color={colors.blueDeep} /></View><View style={{ flex: 1 }}><Text style={styles.sceneTitle}>{title}</Text><Text style={styles.sceneBody}>{body}</Text></View></View>)}</View>
    <Primary label="Xác nhận storyboard" onPress={() => nav('script_confirm')} />
  </ScrollView>;
};

export const ScriptConfirmScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;
  const [confirmed, setConfirmed] = useState(false);
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Xác nhận kịch bản" onBack={goBack} /><Text style={styles.title}>Sẵn sàng tạo video?</Text><Text style={styles.subtitle}>Đây là cổng xác nhận cuối trước khi hệ thống nhận job video. Không có bước duyệt video cuối riêng.</Text>
    <View style={styles.approvalCard}><View style={styles.approvalHeader}><Ionicons name="book-outline" size={22} color={colors.blueDeep} /><View><Text style={styles.approvalTitle}>Cùng chú mèo dạo công viên</Text><Text style={styles.approvalMeta}>Revision 1 · 5 cảnh · 30–90 giây</Text></View></View><Text style={styles.approvalBody}>Lời kể tiếng Việt, phụ đề đồng bộ, không nhạc nền. Video chỉ mở playback sau technical check và safety gate.</Text></View>
    <TouchableOpacity accessibilityRole="checkbox" accessibilityState={{ checked: confirmed }} onPress={() => setConfirmed((value) => !value)} style={styles.confirmCheckRow}><View style={[styles.confirmBox, confirmed && styles.confirmBoxActive]}>{confirmed && <Ionicons name="checkmark" size={14} color={colors.white} />}</View><Text style={styles.confirmCheckText}>Tôi đã xem và xác nhận revision kịch bản/storyboard này.</Text></TouchableOpacity>
    <SoftNotice icon="pie-chart-outline" tone="amber">Mỗi request tạo video được tính một unit quota và không hoàn lại, kể cả khi lỗi kỹ thuật.</SoftNotice>
    <Primary label="Xác nhận và tạo video" disabled={!confirmed} onPress={() => nav('video_processing')} />
  </ScrollView>;
};

export const ParentVideoProcessingScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;
  const stages = [['checkmark-circle', 'Chuẩn bị Character Bible'], ['checkmark-circle', 'Tạo clip theo từng scene'], ['ellipse-outline', 'Ghép video và tạo lời kể'], ['ellipse-outline', 'Kiểm tra an toàn đầu ra']];
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Đang tạo video" onBack={goBack} /><Progress label="Video job · Không cần giữ app mở" percent={68} /><View style={styles.processingHero}><View style={styles.videoOrb}><Ionicons name="videocam-outline" size={32} color={colors.white} /></View><Text style={styles.processingTitle}>Video đang được tạo</Text><Text style={styles.processingSubtitle}>Các scene đang được xử lý tuần tự. Bạn sẽ chỉ thấy playback khi toàn bộ kiểm tra đạt.</Text></View>
    <View style={styles.stageList}>{stages.map(([icon, label], index) => <View key={label} style={styles.stageRow}><Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={20} color={index < 2 ? colors.greenDeep : colors.blueDeep} /><View style={{ flex: 1 }}><Text style={styles.stageTitle}>{label}</Text><Text style={styles.stageStatus}>{index < 2 ? 'Đã hoàn tất' : index === 2 ? 'Đang xử lý' : 'Chờ xử lý'}</Text></View></View>)}</View><SoftNotice icon="time-outline">Đây là trạng thái mô phỏng. Backend sau này sẽ cập nhật job qua polling/push.</SoftNotice><Primary label="Mô phỏng video đã sẵn sàng" onPress={() => nav('safety_gate')} />
  </ScrollView>;
};

export const SafetyGateScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Kiểm tra an toàn" onBack={goBack} /><Text style={styles.title}>Video đã qua các cổng kiểm tra</Text><Text style={styles.subtitle}>Playback chỉ mở sau khi technical quality và output safety đều đạt.</Text>
    <View style={styles.gateCard}>{[['checkmark-circle', 'Technical quality', 'MP4 · 720p · 16:9'], ['checkmark-circle', 'Lời kể và phụ đề', 'Tiếng Việt · đã đồng bộ'], ['checkmark-circle', 'Output safety', 'Đã kiểm tra tự động']].map(([icon, title, body]) => <View key={title} style={styles.gateRow}><Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={22} color={colors.greenDeep} /><View><Text style={styles.gateTitle}>{title}</Text><Text style={styles.gateBody}>{body}</Text></View></View>)}</View>
    <SoftNotice icon="lock-closed-outline" tone="green">Video an toàn mới được cấp playback token. Không có URL tải xuống hoặc gallery công khai.</SoftNotice><Primary label="Mở playback" onPress={() => nav('playback')} />
  </ScrollView>;
};

export const PlaybackScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
    <Header title="Video hoàn thành" onBack={goBack} /><View style={styles.videoFrame}><CatDrawingArtwork height={190} /><View style={styles.playButton}><Ionicons name="play" size={29} color={colors.white} /></View><Text style={styles.videoDuration}>0:00 / 1:02</Text></View><Text style={styles.title}>Cùng chú mèo dạo công viên</Text><Text style={styles.subtitle}>Video riêng tư của run hiện tại · đã qua safety gate.</Text>
    <View style={styles.playbackActions}><TouchableOpacity accessibilityRole="button" onPress={() => nav('script_confirm')} style={styles.outlineAction}><Ionicons name="flag-outline" size={17} color={colors.coralDeep} /><Text style={styles.outlineActionText}>Không phù hợp</Text></TouchableOpacity><TouchableOpacity accessibilityRole="button" onPress={() => nav('completion')} style={styles.primaryAction}><Ionicons name="checkmark" size={17} color={colors.white} /><Text style={styles.primaryActionText}>Hoàn tất</Text></TouchableOpacity></View>
    <SoftNotice icon="shield-checkmark-outline">Nếu yêu cầu tạo lại, video cũ sẽ ẩn khỏi playback ngay khi request mới được nhận.</SoftNotice>
  </ScrollView>;
};

export const CompletionScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}><View style={styles.completeHero}><View style={styles.completeIcon}><Ionicons name="checkmark" size={35} color={colors.white} /></View><Text style={styles.completeTitle}>Đã lưu câu chuyện</Text><Text style={styles.completeSubtitle}>Run của {selectedChild.name} đã hoàn tất. Bạn có thể xem lại trong lịch sử hoặc bắt đầu một câu chuyện mới.</Text></View><TouchableOpacity accessibilityRole="button" onPress={() => nav('history')} style={styles.primary}><Text style={styles.primaryText}>Mở lịch sử video</Text><Ionicons name="arrow-forward" size={18} color={colors.white} /></TouchableOpacity><TouchableOpacity accessibilityRole="button" onPress={() => nav('parent_home')} style={styles.textButton}><Text style={styles.textButtonText}>Tạo câu chuyện mới</Text></TouchableOpacity><SoftNotice icon="trash-outline" tone="amber">Bạn có thể yêu cầu xóa run đã hoàn tất trong phần quản lý dữ liệu. Quota đã dùng không được hoàn lại.</SoftNotice></ScrollView>;
};

export const HistoryScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const items = [['Cùng chú mèo dạo công viên', 'Hôm nay · 1:02'], ['Chuyến phiêu lưu trong rừng', '12/10/2026 · 0:48'], ['Cùng bạn đến trường', '05/10/2026 · 0:55']];
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}><Header title="Lịch sử video" onBack={() => nav('parent_home')} /><Text style={styles.title}>Những câu chuyện của {selectedChild.name}</Text><Text style={styles.subtitle}>Video riêng tư, chỉ hiển thị trong tài khoản phụ huynh.</Text><View style={styles.historyList}>{items.map(([title, meta]) => <TouchableOpacity key={title} accessibilityRole="button" onPress={() => nav('playback')} style={styles.historyRow}><View style={styles.historyThumb}><Ionicons name="play" size={18} color={colors.blueDeep} /></View><View style={{ flex: 1 }}><Text style={styles.historyTitle}>{title}</Text><Text style={styles.historyMeta}>{meta}</Text></View><Ionicons name="chevron-forward" size={18} color={colors.textLight} /></TouchableOpacity>)}</View><SoftNotice icon="information-circle-outline">Lịch sử không cho phép export hoặc chia sẻ công khai theo SRS.</SoftNotice></ScrollView>;
};

export const QuotaScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}><Header title="Quota tháng này" onBack={() => nav('parent_home')} /><Text style={styles.title}>Theo dõi lượt tạo video</Text><Text style={styles.subtitle}>Quota tính theo tháng dương lịch Asia/Ho_Chi_Minh.</Text><View style={styles.quotaCard}><View style={styles.quotaTop}><View><Text style={styles.quotaLabel}>ĐÃ SỬ DỤNG</Text><Text style={styles.quotaValue}>1 / 3 lượt</Text></View><Ionicons name="leaf-outline" size={35} color={colors.greenDeep} /></View><View style={styles.quotaTrack}><View style={styles.quotaFill} /></View><Text style={styles.quotaRemaining}>Còn lại 2 lượt trong tháng này</Text></View><View style={styles.quotaRow}><Ionicons name="lock-closed-outline" size={19} color={colors.blueDeep} /><Text style={styles.quotaRowText}>Lịch sử và video cũ vẫn xem được khi hết quota.</Text></View><TouchableOpacity accessibilityRole="button" onPress={() => {}} style={styles.outlineAction}><Ionicons name="add-circle-outline" size={17} color={colors.blueDeep} /><Text style={styles.outlineActionText}>Mua thêm quota (sắp nối billing)</Text></TouchableOpacity></ScrollView>;
};

export const NotificationsSettingsScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;
  const rows = [['notifications-outline', 'Thông báo', 'Video hoàn tất, nhắc run đang chờ'], ['settings-outline', 'Cài đặt', 'Ngôn ngữ và quyền thiết bị'], ['folder-open-outline', 'Quản lý dữ liệu', 'Xóa run và hồ sơ đã hoàn tất'], ['help-circle-outline', 'Trợ giúp', 'Câu hỏi thường gặp và hỗ trợ']];
  return <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}><Header title="Thông báo & cài đặt" onBack={() => nav('parent_home')} /><Text style={styles.title}>Giữ quyền kiểm soát dữ liệu</Text><Text style={styles.subtitle}>Inbox là nơi chuẩn để theo dõi trạng thái run; push/email chỉ là kênh hỗ trợ.</Text><View style={styles.settingsList}>{rows.map(([icon, title, body]) => <TouchableOpacity key={title} accessibilityRole="button" onPress={() => {}} style={styles.settingsRow}><View style={styles.settingsIcon}><Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={19} color={colors.blueDeep} /></View><View style={{ flex: 1 }}><Text style={styles.settingsTitle}>{title}</Text><Text style={styles.settingsBody}>{body}</Text></View><Ionicons name="chevron-forward" size={18} color={colors.textLight} /></TouchableOpacity>)}</View><SoftNotice icon="shield-checkmark-outline" tone="green">Không đưa tên trẻ, media hoặc nội dung story vào payload thông báo.</SoftNotice></ScrollView>;
};

const styles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingTop: Platform.OS === 'web' ? 56 : 20, paddingBottom: 36, backgroundColor: '#F8FAFC', minHeight: '100%' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 21 },
  backButton: { width: 40, height: 40, borderRadius: 14, backgroundColor: '#F4F7FB', alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 15, fontWeight: '900', color: colors.textHeading },
  headerMeta: { fontSize: 11, fontWeight: '800', color: colors.textSoft },
  progressWrap: { marginBottom: 20 },
  progressTrack: { height: 5, borderRadius: 4, backgroundColor: '#E7EDF6', overflow: 'hidden' },
  progressFill: { height: 5, borderRadius: 4, backgroundColor: colors.blueDeep },
  progressLabel: { fontSize: 10, fontWeight: '800', color: colors.textSoft, marginTop: 8 },
  title: { fontSize: 26, lineHeight: 32, fontWeight: '900', color: colors.textHeading, letterSpacing: -0.6 },
  subtitle: { fontSize: 14, lineHeight: 20, color: colors.textBody, marginTop: 6 },
  primary: { minHeight: 56, borderRadius: 18, backgroundColor: colors.blueDeep, borderBottomWidth: 4, borderBottomColor: '#1D4ED8', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 22, paddingHorizontal: 16, ...shadows.button },
  primaryDisabled: { backgroundColor: '#CBD5E1' },
  primaryText: { fontSize: 15, fontWeight: '900', color: colors.white },
  notice: { flexDirection: 'row', gap: 8, alignItems: 'flex-start', padding: 13, borderRadius: 16, marginTop: 15 },
  noticeBlue: { backgroundColor: '#EFF6FF' }, noticeGreen: { backgroundColor: '#F0FDF4' }, noticeAmber: { backgroundColor: '#FFFBEB' },
  noticeText: { flex: 1, fontSize: 11, lineHeight: 16, color: colors.textBody },
  activityGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 20 },
  activityCard: { width: '48%', minHeight: 148, padding: 14, borderRadius: 21, borderWidth: 1, borderColor: '#E8E1D6', backgroundColor: colors.white, position: 'relative' },
  activityCardActive: { borderColor: '#60A5FA', backgroundColor: '#F3F8FF', ...shadows.soft },
  activityEmoji: { width: 46, height: 46, borderRadius: 15, backgroundColor: '#FFF7E2', alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  activityEmojiActive: { backgroundColor: '#DBEAFE' },
  activityEmojiText: { fontSize: 23 }, activityTitle: { fontSize: 13, fontWeight: '900', color: colors.textHeading }, activityMeta: { fontSize: 10, color: colors.textSoft, marginTop: 5 },
  selectedMark: { position: 'absolute', top: 10, right: 10, width: 19, height: 19, borderRadius: 10, backgroundColor: colors.blueDeep, alignItems: 'center', justifyContent: 'center' },
  contextCard: { borderRadius: 20, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white, padding: 8, marginTop: 20, ...shadows.soft },
  contextRow: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 10, borderBottomWidth: 1, borderBottomColor: '#EEF2F7' },
  contextIcon: { width: 32, height: 32, borderRadius: 11, backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center' }, contextLabel: { fontSize: 10, color: colors.textSoft }, contextValue: { fontSize: 13, fontWeight: '800', color: colors.textHeading, marginTop: 3 },
  processingHero: { alignItems: 'center', paddingVertical: 27 }, processingOrb: { width: 82, height: 82, borderRadius: 41, backgroundColor: '#FEF3C7', alignItems: 'center', justifyContent: 'center' }, videoOrb: { width: 82, height: 82, borderRadius: 41, backgroundColor: colors.blueDeep, alignItems: 'center', justifyContent: 'center' }, processingTitle: { fontSize: 19, fontWeight: '900', color: colors.textHeading, textAlign: 'center', marginTop: 16 }, processingSubtitle: { fontSize: 12, lineHeight: 17, color: colors.textSoft, textAlign: 'center', marginTop: 6, maxWidth: 300 },
  stageList: { borderRadius: 20, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white, padding: 7, ...shadows.soft }, stageRow: { flexDirection: 'row', alignItems: 'center', gap: 11, padding: 11, borderBottomWidth: 1, borderBottomColor: '#EEF2F7' }, stageTitle: { fontSize: 12, fontWeight: '800', color: colors.textHeading }, stageStatus: { fontSize: 10, color: colors.textSoft, marginTop: 3 },
  storyCard: { padding: 16, borderRadius: 20, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white, marginTop: 20, ...shadows.soft }, storyText: { fontSize: 14, lineHeight: 22, color: colors.textBody }, storyFooter: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 16, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#EEF2F7' }, revisionText: { fontSize: 10, fontWeight: '800', color: colors.blueDeep }, sceneCount: { fontSize: 10, color: colors.textSoft }, rewriteButton: { minHeight: 48, borderRadius: 15, backgroundColor: '#EFF6FF', flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8, marginTop: 12 }, rewriteText: { fontSize: 12, fontWeight: '800', color: colors.blueDeep },
  storyboardList: { gap: 9, marginTop: 20 }, sceneCard: { flexDirection: 'row', alignItems: 'center', gap: 11, padding: 11, borderRadius: 17, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white }, sceneThumb: { width: 62, height: 62, borderRadius: 14, backgroundColor: '#EAF4FF', alignItems: 'center', justifyContent: 'center' }, sceneNumber: { position: 'absolute', left: 7, top: 6, fontSize: 9, fontWeight: '900', color: colors.blueDeep }, sceneTitle: { fontSize: 12, fontWeight: '900', color: colors.textHeading }, sceneBody: { fontSize: 10, lineHeight: 15, color: colors.textSoft, marginTop: 4 },
  approvalCard: { padding: 16, borderRadius: 20, backgroundColor: '#F8FBFF', borderWidth: 1, borderColor: '#D8EAFE', marginTop: 20 }, approvalHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 }, approvalTitle: { fontSize: 14, fontWeight: '900', color: colors.textHeading }, approvalMeta: { fontSize: 10, color: colors.textSoft, marginTop: 3 }, approvalBody: { fontSize: 12, lineHeight: 18, color: colors.textBody, marginTop: 14 },
  confirmCheckRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 18 }, confirmBox: { width: 24, height: 24, borderRadius: 7, borderWidth: 1.5, borderColor: '#CBD5E1', alignItems: 'center', justifyContent: 'center' }, confirmBoxActive: { backgroundColor: colors.blueDeep, borderColor: colors.blueDeep }, confirmCheckText: { flex: 1, fontSize: 12, lineHeight: 17, color: colors.textBody },
  gateCard: { borderRadius: 20, borderWidth: 1, borderColor: '#D1FAE5', backgroundColor: '#F0FDF4', padding: 8, marginTop: 20 }, gateRow: { flexDirection: 'row', alignItems: 'center', gap: 11, padding: 12, borderBottomWidth: 1, borderBottomColor: '#DCFCE7' }, gateTitle: { fontSize: 13, fontWeight: '900', color: '#166534' }, gateBody: { fontSize: 10, color: '#4D7C5A', marginTop: 3 },
  videoFrame: { height: 250, borderRadius: 23, backgroundColor: '#DCEEFF', overflow: 'hidden', alignItems: 'center', justifyContent: 'center', marginTop: 20, position: 'relative' }, playButton: { position: 'absolute', width: 60, height: 60, borderRadius: 30, backgroundColor: 'rgba(37,99,235,0.92)', alignItems: 'center', justifyContent: 'center' }, videoDuration: { position: 'absolute', bottom: 12, right: 12, paddingHorizontal: 8, paddingVertical: 5, borderRadius: 8, backgroundColor: 'rgba(15,23,42,0.72)', color: colors.white, fontSize: 10 }, playbackActions: { flexDirection: 'row', gap: 10, marginTop: 18 }, outlineAction: { flex: 1, minHeight: 48, borderRadius: 15, borderWidth: 1, borderColor: '#FCA5A5', backgroundColor: '#FFF1F2', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 }, outlineActionText: { fontSize: 11, fontWeight: '800', color: colors.coralDeep }, primaryAction: { flex: 1, minHeight: 48, borderRadius: 15, backgroundColor: colors.blueDeep, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 }, primaryActionText: { fontSize: 11, fontWeight: '900', color: colors.white },
  completeHero: { alignItems: 'center', paddingVertical: 45 }, completeIcon: { width: 78, height: 78, borderRadius: 39, backgroundColor: colors.greenDeep, alignItems: 'center', justifyContent: 'center' }, completeTitle: { fontSize: 24, fontWeight: '900', color: colors.textHeading, marginTop: 18 }, completeSubtitle: { fontSize: 13, lineHeight: 19, color: colors.textSoft, textAlign: 'center', marginTop: 7 }, textButton: { alignItems: 'center', paddingVertical: 15 }, textButtonText: { fontSize: 12, fontWeight: '800', color: colors.blueDeep },
  historyList: { gap: 9, marginTop: 20 }, historyRow: { flexDirection: 'row', alignItems: 'center', gap: 11, minHeight: 72, padding: 12, borderRadius: 17, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white }, historyThumb: { width: 47, height: 47, borderRadius: 14, backgroundColor: '#EAF4FF', alignItems: 'center', justifyContent: 'center' }, historyTitle: { fontSize: 12, fontWeight: '900', color: colors.textHeading }, historyMeta: { fontSize: 10, color: colors.textSoft, marginTop: 4 },
  quotaCard: { padding: 18, borderRadius: 22, backgroundColor: '#F0FDF4', borderWidth: 1, borderColor: '#BBF7D0', marginTop: 20 }, quotaTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, quotaLabel: { fontSize: 10, fontWeight: '900', letterSpacing: 0.8, color: '#4D7C5A' }, quotaValue: { fontSize: 25, fontWeight: '900', color: '#166534', marginTop: 4 }, quotaTrack: { height: 11, borderRadius: 7, backgroundColor: '#DCFCE7', overflow: 'hidden', marginTop: 18 }, quotaFill: { width: '33%', height: 11, borderRadius: 7, backgroundColor: colors.greenDeep }, quotaRemaining: { fontSize: 11, color: '#4D7C5A', marginTop: 8 }, quotaRow: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 13, borderRadius: 15, backgroundColor: '#EFF6FF', marginTop: 14 }, quotaRowText: { flex: 1, fontSize: 11, color: colors.textBody },
  settingsList: { gap: 9, marginTop: 20 }, settingsRow: { flexDirection: 'row', alignItems: 'center', gap: 11, padding: 13, borderRadius: 17, borderWidth: 1, borderColor: '#E5EAF2', backgroundColor: colors.white }, settingsIcon: { width: 38, height: 38, borderRadius: 13, backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center' }, settingsTitle: { fontSize: 13, fontWeight: '900', color: colors.textHeading }, settingsBody: { fontSize: 10, color: colors.textSoft, marginTop: 3 },
});
