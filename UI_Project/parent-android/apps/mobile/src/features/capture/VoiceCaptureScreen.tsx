import {StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentField, ParentIcon, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

export function VoiceCaptureScreen({state, dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  return (
    <View style={styles.page}>
      <PreviewBanner title="Ghi âm chưa kết nối" body="Không có audio nào được ghi hoặc tải lên trong bản này." />
      <ScreenIntro eyebrow="Ý TƯỞNG BẰNG GIỌNG NÓI" title="Ba mẹ kể ý tưởng" description="Có thể dùng chữ, giọng nói hoặc cả hai. Giọng nói tối đa 2 phút / 20 MB." />
      <ParentCard tone="green" style={styles.recorder}>
        <View style={styles.micCircle}><ParentIcon name="voice" size={28} color={sketchColors.greenDark}/></View>
        <Text style={styles.recorderTitle}>Sẵn sàng lắng nghe</Text>
        <Text style={styles.recorderBody}>Trong bản thật, ba mẹ có thể bắt đầu, tạm dừng và nghe lại trước khi gửi.</Text>
        <ParentButton title="Bắt đầu ghi âm" icon="voice" onPress={() => onNotice('Micro và lưu audio chưa được nối; chưa bắt đầu ghi âm.')} />
      </ParentCard>
      <InfoBanner title="Sau ghi âm: xem transcript trước" body="Whisper sẽ tạo bản chép thô; ba mẹ cần sửa hoặc xác nhận. Bản preview bên dưới chỉ minh họa vùng chỉnh transcript." />
      <ParentField
        label="Transcript minh họa · ba mẹ có thể sửa"
        multiline
        numberOfLines={4}
        value={state.transcript}
        onChangeText={(value) => dispatch({type: 'SET_TRANSCRIPT', value})}
        placeholder="Chưa có transcript"
      />
      <ParentCard style={styles.revisionCard}>
        <Text style={styles.revisionTitle}>Hai bản được tách biệt</Text>
        <Text style={styles.revisionBody}>Transcript thô và bản ba mẹ xác nhận được lưu thành hai revision riêng khi backend được tích hợp.</Text>
      </ParentCard>
      <ParentButton title="Xác nhận transcript xem trước" icon="check" onPress={() => onNavigate('understanding')} />
      <ParentButton title="Bỏ qua giọng nói" variant="quiet" onPress={() => onNavigate('understanding')} />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 16},
  recorder: {alignItems: 'center', gap: 11, padding: 19},
  micCircle: {width: 64, height: 64, alignItems: 'center', justifyContent: 'center', borderRadius: 24, backgroundColor: '#FFFFFFB8'},
  recorderTitle: {color: sketchColors.ink, fontSize: 16, fontWeight: '900'},
  recorderBody: {maxWidth: 280, color: sketchColors.inkSoft, fontSize: 11, lineHeight: 17, textAlign: 'center'},
  revisionCard: {gap: 5},
  revisionTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  revisionBody: {color: sketchColors.muted, fontSize: 11, lineHeight: 17},
});
