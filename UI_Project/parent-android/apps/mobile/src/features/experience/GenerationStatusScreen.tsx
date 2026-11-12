import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {GenerationPreviewState, ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

type RecoveryPreviewState = 'loading' | 'denied' | 'stale' | 'retryable' | 'blocked' | 'reconciling' | 'deleting' | 'empty';
const recoveryPreviewStates: readonly Readonly<{value: RecoveryPreviewState; label: string; title: string; body: string; action?: string}>[] = [
  {value: 'loading', label: 'Đang tải', title: 'Đang tải trạng thái run', body: 'Giữ nguyên màn hình và bản nháp; chờ server trả revision mới nhất.'},
  {value: 'denied', label: 'Không đủ quyền', title: 'Không thể mở run này', body: 'Không hiển thị dữ liệu. Quay về danh sách hoặc đăng nhập bằng vai trò được cấp.'},
  {value: 'stale', label: 'Revision cũ', title: 'Run đã thay đổi', body: 'Giữ nội dung đang nhập; xem phiên bản mới trước khi tiếp tục.', action: 'Xem revision mới · preview'},
  {value: 'retryable', label: 'Có thể thử lại', title: 'Dịch vụ đang bận', body: 'Chỉ thử lại khi server xác nhận retryable và đã hết thời gian chờ.', action: 'Mô phỏng thử lại'},
  {value: 'blocked', label: 'Không thể thử lại', title: 'Yêu cầu cần hỗ trợ', body: 'Giữ run và dữ liệu. Không gửi lại cùng thao tác khi server báo lỗi không thể thử lại.'},
  {value: 'reconciling', label: 'Đối soát', title: 'Đang xác minh kết quả', body: 'Không gửi request mới; giữ cùng mã idempotency đến khi có kết quả cuối.'},
  {value: 'deleting', label: 'Đang xóa', title: 'Yêu cầu xóa đang chờ', body: 'Hồ sơ bị khóa cho run mới đến khi lifecycle xác nhận; không hiển thị phần trăm giả.'},
  {value: 'empty', label: 'Danh sách trống', title: 'Chưa có run nào', body: 'Bắt đầu từ một buổi học hợp lệ hoặc xem lại bộ lọc; không tạo bản ghi mẫu.'},
];

export function GenerationStatusScreen({state, dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [recoveryPreviewOpen, setRecoveryPreviewOpen] = useState(false);
  const [recoveryPreviewState, setRecoveryPreviewState] = useState<RecoveryPreviewState>('loading');
  const stateCopy = generationCopy[state.generationState];
  const isError = ['failed', 'admission-rejected', 'quota-blocked', 'rate-limited', 'provider-unavailable'].includes(state.generationState);
  const regenerationLimitReached = state.videoReviewReason.length > 0 && state.videoRegenerationCount >= 2 && !state.videoRegenerationPending;
  return (
    <View style={styles.page}>
      <PreviewBanner title="Chưa gửi yêu cầu tạo video" body="Không có job, chi phí hay trạng thái xử lý thật trong bản xem trước." />
      <ScreenIntro eyebrow="BƯỚC 6 · TRẠNG THÁI" title={isError ? 'Cùng tìm bước tiếp theo' : 'Chuẩn bị tạo video'} description="Màn này minh họa các trạng thái; không hiển thị phần trăm giả hoặc thời gian hoàn tất." />
      {state.runCancelPending ? <InfoBanner title="Yêu cầu hủy đang chờ xác nhận" body="Run vẫn được giữ để chờ kết quả từ máy chủ. Không tạo lại, mở trình phát hay xóa trạng thái trong lúc này." tone="warning"/> : null}
      {state.videoRegenerationPending && !state.runCancelPending ? <InfoBanner title="Yêu cầu tạo lại đã được chấp nhận · preview" body={state.storyConfirmed ? `Kịch bản đã được duyệt trong preview; đang chờ kết quả mô phỏng lượt ${state.videoRegenerationCount}/2.` : `Hãy xem lại kịch bản trước khi mô phỏng kết quả lượt ${state.videoRegenerationCount}/2.`} tone="warning"/> : null}
      {regenerationLimitReached && !state.runCancelPending ? <InfoBanner title="Đã dùng hết 2 lượt tạo lại" body="Run hiện tại vẫn có thể hoàn tất; sau kết quả mới, preview sẽ khóa yêu cầu tạo lại tiếp theo." tone="warning"/> : null}
      <ParentCard tone={isError ? 'gold' : 'green'} style={styles.statusCard}>
        <View style={styles.statusIcon}><ParentIcon name={stateCopy.icon} size={24} color={isError ? '#806218' : sketchColors.greenDark}/></View>
        <ParentPill label={stateCopy.badge} tone={isError ? 'gold' : 'green'} />
        <Text style={styles.statusTitle}>{stateCopy.title}</Text>
        <Text style={styles.statusBody}>{stateCopy.body}</Text>
      </ParentCard>
      <ParentCard style={styles.stages}>
        <Text style={styles.cardTitle}>Các chặng hệ thống</Text>
        <StageRow label="Tiếp nhận yêu cầu" note={state.generationState === 'reconciling' ? 'Đang đối soát trạng thái callback' : 'Chưa kết nối backend'} state="idle"/>
        <StageRow label="Tạo các cảnh và lời kể" note="Chưa bắt đầu trong bản preview" state="idle"/>
        <StageRow label="Kiểm tra kỹ thuật và an toàn" note="Cần đạt cả hai cổng" state="locked"/>
        <StageRow label="Cho phép phát riêng tư" note="Chỉ sau khi đạt cổng" state="locked"/>
      </ParentCard>
      {isError || state.generationState === 'reconciling' ? (
        <InfoBanner title={stateCopy.recoveryTitle} body={stateCopy.recoveryBody} tone="warning" />
      ) : null}
      {isError && state.generationState === 'quota-blocked' ? <ParentButton title="Xem giới hạn lượt tạo" icon="quota" variant="secondary" onPress={() => onNavigate('quota')} /> : null}
      {state.generationState === 'admission-rejected' ? <ParentButton title="Quay lại xem kịch bản" icon="arrow" variant="secondary" onPress={() => onNavigate('story-review')} /> : null}
      {state.generationState === 'reconciling' ? <ParentButton title="Không gửi lại khi đang đối soát" disabled onPress={() => undefined} /> : null}
      {isError && state.generationState !== 'quota-blocked' && state.generationState !== 'admission-rejected' ? <ParentButton title="Thử lại · chưa kết nối" icon="arrow" variant="secondary" onPress={() => onNotice('Backend chưa kết nối; không gửi lệnh thử lại.')} /> : null}
      {!state.runCancelPending ? <View style={styles.previewStates}>
        <Text style={styles.cardTitle}>Xem trạng thái mẫu</Text>
        <View style={styles.stateChips}>
          {previewStates.map((item) => (
            <Pressable key={item.value} accessibilityRole="button" onPress={() => dispatch({type: 'PREVIEW_GENERATION_STATE', value: item.value})} style={styles.stateChip}>
              <Text style={styles.stateChipText}>{item.label}</Text>
            </Pressable>
          ))}
        </View>
      </View> : null}
      <ParentButton title={recoveryPreviewOpen ? 'Ẩn tình huống khôi phục' : 'Xem tình huống khôi phục'} variant="quiet" onPress={() => setRecoveryPreviewOpen((current) => !current)} accessibilityHint={recoveryPreviewOpen ? 'Thu gọn các trạng thái phục hồi minh họa.' : 'Mở các trạng thái phục hồi minh họa.'} />
      {recoveryPreviewOpen ? <ParentCard style={styles.recoveryPreviewCard}>
        <Text style={styles.cardTitle}>Trạng thái giao diện · preview</Text>
        <Text style={styles.recoveryPreviewIntro}>Chọn một tình huống để xem cách màn hình phản hồi. Không gọi API.</Text>
        <View style={styles.stateChips}>{recoveryPreviewStates.map((item) => <Pressable key={item.value} accessibilityRole="button" accessibilityState={{selected: recoveryPreviewState === item.value}} onPress={() => setRecoveryPreviewState(item.value)} style={[styles.stateChip, recoveryPreviewState === item.value ? styles.stateChipSelected : undefined]}><Text style={styles.stateChipText}>{item.label}</Text></Pressable>)}</View>
        {(() => { const preview = recoveryPreviewStates.find((item) => item.value === recoveryPreviewState) ?? recoveryPreviewStates[0]; return <View style={[styles.recoveryVariant, recoveryPreviewState === 'denied' || recoveryPreviewState === 'blocked' ? styles.recoveryVariantWarning : undefined]} accessibilityLiveRegion="polite"><ParentPill label={`${preview.label} · PREVIEW`} tone={recoveryPreviewState === 'denied' || recoveryPreviewState === 'blocked' ? 'gold' : 'green'}/><Text style={styles.recoveryVariantTitle}>{preview.title}</Text><Text style={styles.recoveryVariantBody}>{preview.body}</Text>{recoveryPreviewState === 'loading' ? <View style={styles.loadingLines} accessibilityLabel="Đang tải dữ liệu minh họa"><View style={styles.loadingLine}/><View style={[styles.loadingLine, styles.loadingLineMedium]}/><View style={[styles.loadingLine, styles.loadingLineShort]}/></View> : null}{recoveryPreviewState === 'deleting' ? <View style={styles.pendingTrack}><View style={styles.pendingTrackFill}/></View> : null}{preview.action ? <ParentButton title={preview.action} variant="secondary" onPress={() => onNotice('Preview không gửi request; hành động thật cần trạng thái và quyền do server xác nhận.')} /> : null}</View>; })()}
      </ParentCard> : null}
      {!state.runCancelPending && <ParentButton title="Xem giao diện trình phát mẫu" icon="play" disabled={!state.storyConfirmed || regenerationLimitReached} onPress={() => dispatch({type: 'PREVIEW_VIDEO_READY'})} />}
      {state.runCancelPending ? (
        <ParentCard tone="gold" style={styles.cancelCard}>
          <Text style={styles.cancelTitle}>Run đang được giữ an toàn</Text>
          <Text style={styles.cancelBody}>Bản xem trước không thể xác nhận máy chủ đã hủy. Khi API sẵn sàng, trạng thái này sẽ được thay bằng kết quả cuối.</Text>
        </ParentCard>
      ) : confirmCancel ? (
        <ParentCard tone="gold" style={styles.cancelCard}>
          <Text style={styles.cancelTitle}>Gửi yêu cầu hủy run?</Text>
          <Text style={styles.cancelBody}>Run và tiến độ sẽ được giữ lại trong khi chờ máy chủ xác nhận. Đây chỉ là mô phỏng, không gửi yêu cầu thật.</Text>
          <View style={styles.cancelActions}>
            <ParentButton title="Tiếp tục run" variant="secondary" onPress={() => setConfirmCancel(false)} />
            <ParentButton title="Xác nhận hủy · preview" variant="danger" onPress={() => { setConfirmCancel(false); dispatch({type: 'SET_RUN_CANCEL_PENDING', value: true}); }} />
          </View>
        </ParentCard>
      ) : (
        <ParentButton title="Hủy run" variant="quiet" onPress={() => setConfirmCancel(true)} accessibilityHint="Mở xác nhận trước khi giữ run ở trạng thái chờ máy chủ." />
      )}
    </View>
  );
}

const previewStates: readonly Readonly<{value: Exclude<GenerationPreviewState, 'not-requested' | 'ready-preview'>; label: string}>[] = [
  {value: 'waiting', label: 'Đang chờ'},
  {value: 'admission-rejected', label: 'Bị từ chối'},
  {value: 'quota-blocked', label: 'Giới hạn lượt'},
  {value: 'rate-limited', label: 'Thử quá nhanh'},
  {value: 'provider-unavailable', label: 'Dịch vụ lỗi'},
  {value: 'reconciling', label: 'Đối soát'},
];

const generationCopy: Record<GenerationPreviewState, Readonly<{icon: 'clock' | 'help' | 'quota' | 'spark' | 'lock' | 'play'; badge: string; title: string; body: string; recoveryTitle: string; recoveryBody: string}>> = {
  'not-requested': {icon: 'clock', badge: 'CHƯA GỬI YÊU CẦU', title: 'Kịch bản đã xem trong preview', body: 'Bản thật chỉ bắt đầu xử lý sau khi server nhận yêu cầu hợp lệ.', recoveryTitle: '', recoveryBody: ''},
  waiting: {icon: 'clock', badge: 'ĐANG CHỜ · MẪU', title: 'Đang chờ phản hồi máy chủ', body: 'Không có job thật hoặc thời gian hoàn tất để hiển thị.', recoveryTitle: 'Chờ kết quả xác nhận', recoveryBody: 'Không tạo yêu cầu khác trong khi server chưa xác nhận request đầu.'},
  failed: {icon: 'help', badge: 'LỖI · MẪU', title: 'Yêu cầu chưa được gửi', body: 'Đây là trạng thái lỗi minh họa. Không phát sinh video hoặc chi phí.', recoveryTitle: 'Khôi phục không tự gửi lại', recoveryBody: 'Thử lại, hủy hoặc liên hệ hỗ trợ sẽ gọi backend khi tích hợp.'},
  'admission-rejected': {icon: 'help', badge: 'CHƯA ĐƯỢC TIẾP NHẬN · MẪU', title: 'Cần xem lại kịch bản', body: 'Khi backend từ chối request, run quay về bước người lớn có thể xử lý.', recoveryTitle: 'Không tạo lại video', recoveryBody: 'Xem lại bản kịch bản hiện hành trước khi gửi một request mới.'},
  'quota-blocked': {icon: 'quota', badge: 'GIỚI HẠN LƯỢT · MẪU', title: 'Chưa thể gửi yêu cầu', body: 'Không hiển thị số dư hay chi phí giả khi dữ liệu quota chưa tải.', recoveryTitle: 'Xem thông tin lượt tạo', recoveryBody: 'Số dư, gói và chính sách thanh toán cần API chính thức.'},
  'rate-limited': {icon: 'clock', badge: 'THỬ QUÁ NHANH · MẪU', title: 'Hãy chờ trước khi thử lại', body: 'Backend sẽ trả thời gian thử lại nếu giới hạn tốc độ được áp dụng.', recoveryTitle: 'Đừng gửi liên tục', recoveryBody: 'Bản preview không có countdown; khi tích hợp sẽ dùng thời gian server trả về.'},
  'provider-unavailable': {icon: 'help', badge: 'DỊCH VỤ TẠM NGỪNG · MẪU', title: 'Nội dung vẫn được giữ', body: 'Không hiển thị chi tiết kỹ thuật hoặc prompt của nhà cung cấp.', recoveryTitle: 'Có thể thử lại sau', recoveryBody: 'Chỉ thử lại khi backend cho phép; lỗi kỹ thuật không đảm bảo hoàn quota.'},
  reconciling: {icon: 'clock', badge: 'ĐANG ĐỐI SOÁT · MẪU', title: 'Đang kiểm tra kết quả cuối', body: 'Callback có thể đến trễ. UI chờ nguồn backend trước khi cho thử lại.', recoveryTitle: 'Không gửi request trùng', recoveryBody: 'Chưa có callback thật trong preview; giữ nguyên trạng thái và chờ backend.'},
  'ready-preview': {icon: 'play', badge: 'TRÌNH PHÁT MẪU', title: 'Chưa có video đạt kiểm tra', body: 'Nhãn này chỉ mở bố cục preview, không phải trạng thái VIDEO_READY từ server.', recoveryTitle: '', recoveryBody: ''},
};

function StageRow({label, note, state}: Readonly<{label: string; note: string; state: 'idle' | 'locked'}>): React.JSX.Element {
  return (
    <View style={styles.stageRow}>
      <View style={[styles.stageMarker, state === 'locked' ? styles.lockedMarker : undefined]}><ParentIcon name={state === 'locked' ? 'lock' : 'clock'} size={12} color={state === 'locked' ? sketchColors.muted : sketchColors.green}/></View>
      <View style={styles.stageCopy}><Text style={styles.stageTitle}>{label}</Text><Text style={styles.stageNote}>{note}</Text></View>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  statusCard: {alignItems: 'center', gap: 9, padding: 20},
  statusIcon: {width: 56, height: 56, alignItems: 'center', justifyContent: 'center', borderRadius: 20, backgroundColor: '#FFFFFFB8'},
  statusTitle: {color: sketchColors.ink, fontSize: 16, fontWeight: '900', textAlign: 'center'},
  statusBody: {maxWidth: 290, color: sketchColors.inkSoft, fontSize: 11, lineHeight: 17, textAlign: 'center'},
  stages: {gap: 14},
  cardTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900', marginBottom: 2},
  stageRow: {flexDirection: 'row', alignItems: 'center', gap: 10},
  stageMarker: {width: 30, height: 30, alignItems: 'center', justifyContent: 'center', borderRadius: 11, backgroundColor: sketchColors.greenSoft},
  lockedMarker: {backgroundColor: '#EEF0EB'},
  stageCopy: {flex: 1, gap: 2},
  stageTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '800'},
  stageNote: {color: sketchColors.muted, fontSize: 10},
  previewStates: {gap: 9, padding: 13, borderRadius: 16, borderWidth: 1, borderColor: sketchColors.line, backgroundColor: sketchColors.surface},
  stateChips: {flexDirection: 'row', flexWrap: 'wrap', gap: 7},
  stateChip: {minHeight: 48, justifyContent: 'center', paddingHorizontal: 11, borderRadius: 13, backgroundColor: sketchColors.surfaceMuted},
  stateChipSelected: {backgroundColor: sketchColors.greenSoft, borderWidth: 1, borderColor: sketchColors.green},
  stateChipText: {color: sketchColors.greenDark, fontSize: 10, fontWeight: '800'},
  recoveryPreviewCard: {gap: 10, padding: 13},
  recoveryPreviewIntro: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
  recoveryVariant: {gap: 8, padding: 12, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 14, backgroundColor: sketchColors.surface},
  recoveryVariantWarning: {borderColor: '#E5C8A0', backgroundColor: sketchColors.goldSoft},
  recoveryVariantTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  recoveryVariantBody: {color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  loadingLines: {gap: 7},
  loadingLine: {height: 9, width: '100%', borderRadius: 99, backgroundColor: sketchColors.surfaceMuted},
  loadingLineMedium: {width: '78%'},
  loadingLineShort: {width: '56%'},
  pendingTrack: {height: 6, overflow: 'hidden', borderRadius: 6, backgroundColor: sketchColors.surfaceMuted},
  pendingTrackFill: {width: '36%', height: '100%', borderRadius: 6, backgroundColor: sketchColors.green},
  cancelCard: {gap: 9},
  cancelTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  cancelBody: {color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  cancelActions: {gap: 7, marginTop: 3},
});
