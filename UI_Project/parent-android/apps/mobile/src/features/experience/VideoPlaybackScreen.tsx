import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchRadius, sketchSpace} from '../../shared/ui/SketchTokens';

export function VideoPlaybackScreen({state, onNavigate}: ParentFlowProps): React.JSX.Element {
  const childName = state.activeRunChild?.name ?? state.childName;
  const lessonTitle = state.activeRunLesson?.title ?? state.lessonTitle;
  return (
    <View style={styles.page}>
      <PreviewBanner title="Không có video để phát" body="Đây là khung trình phát minh họa. Chưa có artifact hoặc xác nhận safety từ máy chủ." />
      <ScreenIntro eyebrow="MỘT CÂU CHUYỆN RIÊNG" title={`Khoảnh khắc của ${childName}`} description="Bản thật phát riêng tư cho gia đình sau khi video vượt qua kiểm tra kỹ thuật và an toàn." />
      {state.previousVideoHidden ? <InfoBanner title="Video cũ đang ẩn trong preview" body="Yêu cầu tạo lại đã được mô phỏng là chấp nhận. Chưa có media hoặc thay đổi thật trên máy chủ." tone="warning"/> : null}
      <ParentCard style={styles.playerCard}>
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.landscape}>
          <View style={styles.sun}/><View style={styles.cloud}/><View style={styles.hillBack}/><View style={styles.hillFront}/>
          <View style={styles.playButton}><ParentIcon name="play" size={23} color={sketchColors.white}/></View>
          <View style={styles.playerLabel}><Text style={styles.playerLabelText}>KHUNG VIDEO · CHƯA CÓ MEDIA</Text></View>
        </View>
        <View style={styles.playerMeta}><View><Text style={styles.videoTitle}>{lessonTitle ?? 'Chuyện của con'}</Text><Text style={styles.videoSubtitle}>{childName} · xem riêng tư</Text></View><View style={styles.videoBadges}><ParentPill label="BẢN DEMO" tone="gold"/><ParentPill label={`Tạo lại ${state.videoRegenerationCount}/2`} tone="gray"/></View></View>
      </ParentCard>
      <ParentCard style={styles.privacyCard}>
        <View style={styles.privacyIcon}><ParentIcon name="lock" size={18}/></View>
        <View style={styles.privacyCopy}><Text style={styles.privacyTitle}>Video luôn gắn với một hồ sơ</Text><Text style={styles.privacyBody}>Bản thật không dùng lại video của trẻ khác. Yêu cầu tạo lại sẽ ẩn video cũ khỏi playback khi được máy chủ chấp nhận.</Text></View>
      </ParentCard>
      {state.previousVideoHidden ? <InfoBanner title="Trình phát cũ đã khóa" body="Xem lại kịch bản và chờ kết quả mới trước khi mở trình phát." tone="warning" /> : <InfoBanner title="Cổng phát đang khóa" body="Điều hướng xem mẫu bên dưới chỉ mở bố cục sau video; nó không xác nhận video thật đã sẵn sàng." tone="warning" />}
      <ParentButton title="Xem hoạt động sau video · mẫu" icon="arrow" disabled={state.previousVideoHidden} onPress={() => onNavigate('activities')} />
      <ParentButton title="Video chưa phù hợp?" variant="secondary" disabled={state.previousVideoHidden || state.runCancelPending} onPress={() => onNavigate('video-review')} />
      <ParentButton title="Quay lại trạng thái" variant="quiet" onPress={() => onNavigate('generation')} />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  playerCard: {padding: 9, overflow: 'hidden'},
  landscape: {position: 'relative', height: 210, overflow: 'hidden', alignItems: 'center', justifyContent: 'center', borderRadius: sketchRadius.md, backgroundColor: '#DFEDE6'},
  sun: {position: 'absolute', top: 24, right: 38, width: 38, height: 38, borderRadius: 20, backgroundColor: '#EEC968'},
  cloud: {position: 'absolute', top: 52, left: 34, width: 60, height: 17, borderRadius: 12, backgroundColor: '#FFFFFFAA'},
  hillBack: {position: 'absolute', bottom: -50, right: -15, width: 240, height: 128, borderRadius: 100, backgroundColor: '#A9CDB3'},
  hillFront: {position: 'absolute', bottom: -67, left: -45, width: 300, height: 140, borderRadius: 120, backgroundColor: '#83B495'},
  playButton: {width: 58, height: 58, alignItems: 'center', justifyContent: 'center', borderRadius: 22, borderWidth: 1, borderColor: '#FFFFFF99', backgroundColor: '#173F35CC', elevation: 4},
  playerLabel: {position: 'absolute', bottom: 12, left: 12, paddingHorizontal: 9, paddingVertical: 6, borderRadius: 99, backgroundColor: '#183D35DD'},
  playerLabelText: {color: sketchColors.white, fontSize: 8, fontWeight: '900', letterSpacing: 1},
  playerMeta: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8, padding: 11},
  videoBadges: {alignItems: 'flex-end', gap: 6},
  videoTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  videoSubtitle: {color: sketchColors.muted, fontSize: 10, marginTop: 3},
  privacyCard: {flexDirection: 'row', alignItems: 'flex-start', gap: 10},
  privacyIcon: {width: 35, height: 35, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: sketchColors.greenSoft},
  privacyCopy: {flex: 1, gap: 4},
  privacyTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '900'},
  privacyBody: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
});
