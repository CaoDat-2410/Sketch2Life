import {useMemo, useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

type RunStatus = 'Chờ ba mẹ' | 'Đang xử lý' | 'Video sẵn sàng' | 'Cần khôi phục' | 'Đang chờ xóa';
type PreviewRun = Readonly<{id: string; title: string; child: string; date: string; status: RunStatus; lesson: string; version: string; note: string}>;
const examples: readonly PreviewRun[] = [
  {id: 'RUN-DEMO-018', title: 'Chú bướm tìm nhà', child: 'Bé Mây', date: '12/11 · Bản mẫu', status: 'Video sẵn sàng', lesson: 'Khám phá khu vườn', version: 'v1.4', note: 'Chờ người lớn hoàn tất hoặc tạo lại.'},
  {id: 'RUN-DEMO-017', title: 'Chiếc lá bay xa', child: 'Bé An', date: '10/11 · Bản mẫu', status: 'Cần khôi phục', lesson: 'Thế giới thiên nhiên', version: 'v2.0', note: 'Cần đọc lỗi an toàn và hướng xử lý từ server.'},
  {id: 'RUN-DEMO-016', title: 'Khu vườn tí hon', child: 'Bé Mây', date: '08/11 · Bản mẫu', status: 'Đang xử lý', lesson: 'Khám phá khu vườn', version: 'v1.4', note: 'Không tạo request mới khi server chưa xác nhận.'},
  {id: 'RUN-DEMO-015', title: 'Mặt trời thức dậy', child: 'Bé An', date: '05/11 · Bản mẫu', status: 'Chờ ba mẹ', lesson: 'Kể chuyện tự do', version: '—', note: 'Có bước duyệt đang chờ người lớn.'},
  {id: 'RUN-DEMO-014', title: 'Đám mây nhỏ', child: 'Bé Mây', date: '02/11 · Bản mẫu', status: 'Đang chờ xóa', lesson: 'Kể chuyện tự do', version: '—', note: 'Run và media giữ khóa đến khi lifecycle xác nhận.'},
];
const filters = ['Tất cả', 'Chờ ba mẹ', 'Đang xử lý', 'Video sẵn sàng', 'Cần khôi phục', 'Đang chờ xóa'] as const;

export function RunHistoryScreen({onNavigate}: ParentFlowProps): React.JSX.Element {
  const [filter, setFilter] = useState<(typeof filters)[number]>('Tất cả');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [pendingIds, setPendingIds] = useState<readonly string[]>([]);
  const runs = useMemo(() => examples.map((run) => pendingIds.includes(run.id) ? {...run, status: 'Đang chờ xóa' as const} : run).filter((run) => filter === 'Tất cả' || run.status === filter), [filter, pendingIds]);
  const selected = runs.find((run) => run.id === selectedId) ?? null;

  return (
    <View style={styles.page}>
      <PreviewBanner title="Lịch sử mẫu · không lấy từ máy chủ" body="Các hàng bên dưới chỉ minh họa trạng thái, không đại diện cho hoạt động thật của gia đình." />
      <ScreenIntro eyebrow="GIA ĐÌNH" title="Câu chuyện đã tạo" description="Xem trạng thái, phiên bản giáo án và bước tiếp theo của từng run." />

      <View style={styles.filterWrap} accessibilityRole="radiogroup" accessibilityLabel="Lọc lịch sử">
        {filters.map((item) => <Pressable key={item} accessibilityRole="radio" accessibilityState={{selected: filter === item}} onPress={() => { setFilter(item); setSelectedId(null); setConfirmId(null); }} style={[styles.filterChip, filter === item ? styles.filterSelected : undefined]}><Text style={[styles.filterText, filter === item ? styles.filterTextSelected : undefined]}>{item}</Text></Pressable>)}
      </View>

      <View style={styles.runList}>
        {runs.map((run) => {
          const selectedRow = selectedId === run.id;
          const awaitingDelete = confirmId === run.id;
          return (
            <Pressable key={run.id} accessibilityRole="button" accessibilityState={{selected: selectedRow}} accessibilityLabel={`${run.title}, ${run.status}`} onPress={() => { setSelectedId(selectedRow ? null : run.id); setConfirmId(null); }}>
              <ParentCard style={[styles.runCard, selectedRow ? styles.runSelected : undefined]}>
                <View style={[styles.runMark, run.status === 'Cần khôi phục' ? styles.runMarkError : run.status === 'Video sẵn sàng' ? styles.runMarkReady : undefined]}><ParentIcon name={run.status === 'Video sẵn sàng' ? 'play' : run.status === 'Cần khôi phục' ? 'help' : run.status === 'Đang chờ xóa' ? 'lock' : 'clock'} size={18}/></View>
                <View style={styles.runCopy}><View style={styles.runTitleRow}><Text style={styles.runTitle}>{run.title}</Text><StatusPill status={run.status}/></View><Text style={styles.runMeta}>{run.child} · {run.date}</Text></View>
                <ParentIcon name="arrow" size={15}/>
                {selectedRow ? (
                  <View style={styles.runDetail}>
                    <View style={styles.detailDivider}/>
                    <Text style={styles.detailEyebrow}>CHI TIẾT RUN · MẪU</Text>
                    <View style={styles.detailPair}><Text style={styles.detailLabel}>Mã</Text><Text style={styles.detailValue}>{run.id}</Text></View>
                    <View style={styles.detailPair}><Text style={styles.detailLabel}>Giáo án đã ghim</Text><Text style={styles.detailValue}>{run.lesson} · {run.version}</Text></View>
                    <Text style={styles.detailNote}>{run.note}</Text>
                    {run.status !== 'Đang chờ xóa' ? <Pressable accessibilityRole="button" onPress={(event) => { event.stopPropagation(); setConfirmId(run.id); }} style={styles.deleteAction}><ParentIcon name="lock" size={14}/><Text style={styles.deleteLabel}>Xem trạng thái yêu cầu xóa</Text></Pressable> : <View style={styles.pendingBox}><ParentIcon name="clock" size={14}/><Text style={styles.pendingText}>DELETE_PENDING · preview · chưa gửi lên BE</Text></View>}
                    {awaitingDelete ? <View style={styles.confirmBox}><Text style={styles.confirmText}>Đưa run mẫu này vào trạng thái DELETE_PENDING?</Text><Text style={styles.confirmHint}>Chỉ cập nhật giao diện preview; không xóa hay gửi request thật.</Text><View style={styles.confirmButtons}><Pressable accessibilityRole="button" onPress={(event) => { event.stopPropagation(); setConfirmId(null); }}><Text style={styles.keepText}>Quay lại</Text></Pressable><Pressable accessibilityRole="button" onPress={(event) => { event.stopPropagation(); setPendingIds((current) => current.includes(run.id) ? current : [...current, run.id]); setConfirmId(null); }}><Text style={styles.deleteLabel}>Đánh dấu mẫu</Text></Pressable></View></View> : null}
                  </View>
                ) : null}
              </ParentCard>
            </Pressable>
          );
        })}
        {runs.length === 0 ? <ParentCard style={styles.empty}><ParentIcon name="history" size={23}/><Text style={styles.emptyTitle}>Không có run ở trạng thái này</Text><Text style={styles.emptyBody}>Thử bộ lọc khác để xem ví dụ.</Text></ParentCard> : null}
      </View>

      <InfoBanner title="Lịch sử thật cần API và quyền hồ sơ" body="Thời hạn lưu còn mở. DELETE_PENDING chỉ kết thúc khi server xác nhận lifecycle xóa." tone="warning"/>
      <View style={styles.actions}><ParentButton title="Bắt đầu câu chuyện" icon="plus" onPress={() => onNavigate('run-setup')}/><ParentButton title="Thông tin lượt tạo" icon="quota" variant="secondary" onPress={() => onNavigate('quota')}/></View>
      {selected ? <Text accessibilityLiveRegion="polite" style={styles.selectedHint}>Đang xem {selected.id} · dữ liệu mẫu</Text> : null}
    </View>
  );
}

function StatusPill({status}: Readonly<{status: RunStatus}>): React.JSX.Element {
  const tone = status === 'Video sẵn sàng' ? 'green' : status === 'Cần khôi phục' ? 'coral' : status === 'Đang chờ xóa' ? 'gray' : status === 'Đang xử lý' ? 'blue' : 'gold';
  return <ParentPill label={status} tone={tone}/>;
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 13},
  filterWrap: {flexDirection: 'row', flexWrap: 'wrap', gap: 7},
  filterChip: {minHeight: 38, justifyContent: 'center', paddingHorizontal: 11, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 999, backgroundColor: sketchColors.surface},
  filterSelected: {borderColor: sketchColors.green, backgroundColor: sketchColors.greenSoft},
  filterText: {color: sketchColors.muted, fontSize: 9, fontWeight: '700'},
  filterTextSelected: {color: sketchColors.greenDark, fontWeight: '900'},
  runList: {gap: 8},
  runCard: {flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 9, padding: 12, borderWidth: 1},
  runSelected: {borderColor: sketchColors.green},
  runMark: {width: 38, height: 38, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: sketchColors.goldSoft},
  runMarkReady: {backgroundColor: sketchColors.greenSoft},
  runMarkError: {backgroundColor: sketchColors.coralSoft},
  runCopy: {flex: 1, minWidth: 160, gap: 5},
  runTitleRow: {flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 6},
  runTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '900'},
  runMeta: {color: sketchColors.muted, fontSize: 9},
  runDetail: {width: '100%', gap: 9, paddingTop: 4},
  detailDivider: {height: 1, marginBottom: 2, backgroundColor: sketchColors.line},
  detailEyebrow: {color: sketchColors.muted, fontSize: 8, fontWeight: '900', letterSpacing: 1},
  detailPair: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10},
  detailLabel: {color: sketchColors.muted, fontSize: 9},
  detailValue: {flex: 1, color: sketchColors.ink, fontSize: 9, fontWeight: '800', textAlign: 'right'},
  detailNote: {padding: 10, borderRadius: 10, backgroundColor: sketchColors.surfaceMuted, color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  deleteAction: {minHeight: 42, flexDirection: 'row', alignItems: 'center', gap: 7, alignSelf: 'flex-start', paddingHorizontal: 11, borderRadius: 11, backgroundColor: sketchColors.coralSoft},
  deleteLabel: {color: '#8B4E40', fontSize: 9, fontWeight: '900'},
  pendingBox: {minHeight: 40, flexDirection: 'row', alignItems: 'center', gap: 7, padding: 9, borderRadius: 10, backgroundColor: sketchColors.goldSoft},
  pendingText: {flex: 1, color: '#755D20', fontSize: 9, fontWeight: '800'},
  confirmBox: {gap: 6, padding: 11, borderRadius: 11, borderWidth: 1, borderColor: '#E8D89B', backgroundColor: '#FFFAE9'},
  confirmText: {color: sketchColors.ink, fontSize: 10, fontWeight: '900'},
  confirmHint: {color: sketchColors.muted, fontSize: 9, lineHeight: 14},
  confirmButtons: {flexDirection: 'row', justifyContent: 'flex-end', gap: 18, marginTop: 3},
  keepText: {color: sketchColors.muted, fontSize: 9, fontWeight: '800'},
  empty: {alignItems: 'center', gap: 7, padding: 17},
  emptyTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  emptyBody: {color: sketchColors.muted, fontSize: 10},
  actions: {gap: 8},
  selectedHint: {color: sketchColors.muted, fontSize: 9, textAlign: 'center'},
});
