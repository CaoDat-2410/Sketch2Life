import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentField, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

const quickNotes = ['Con thích câu chuyện', 'Con muốn xem lại', 'Cần ba mẹ hỗ trợ'];

export function SessionFeedbackScreen({dispatch, onNavigate}: ParentFlowProps): React.JSX.Element {
  const [rating, setRating] = useState(0);
  const [selectedNotes, setSelectedNotes] = useState<string[]>([]);
  const [note, setNote] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const finish = (): void => {
    dispatch({type: 'RESET_RUN'});
    onNavigate('home');
  };

  return (
    <View style={styles.page}>
      <PreviewBanner title="Phản hồi phiên · chưa gửi" body="Màn này độc lập với phản hồi giáo án; chưa có API lưu nhận xét sau video." />
      <ScreenIntro eyebrow="SAU KHI XEM VIDEO" title="Khoảnh khắc này thế nào?" description="Không bắt buộc. Một chạm cũng đủ để ba mẹ ghi lại cảm nhận." />

      {submitted ? (
        <ParentCard tone="green" style={styles.doneCard}>
          <View style={styles.doneIcon}><ParentIcon name="check" size={22}/></View>
          <Text style={styles.doneTitle}>Đã ghi nhận trong phiên mẫu</Text>
          <Text style={styles.doneBody}>Chưa gửi lên máy chủ. Phản hồi giáo án vẫn nằm riêng ở mục Giáo án.</Text>
          <ParentButton title="Xong · về trang chủ" icon="home" onPress={finish}/>
        </ParentCard>
      ) : (
        <>
          <ParentCard style={styles.ratingCard}>
            <View style={styles.promptRow}><View style={styles.promptIcon}><ParentIcon name="heart" size={18}/></View><View style={styles.promptCopy}><Text style={styles.promptTitle}>Ba mẹ đánh giá trải nghiệm</Text><Text style={styles.promptHint}>Một đến năm sao</Text></View><ParentPill label="TÙY CHỌN" tone="gray"/></View>
            <View accessibilityRole="radiogroup" style={styles.ratingRow}>
              {[1, 2, 3, 4, 5].map((value) => (
                <Pressable key={value} accessibilityRole="radio" accessibilityLabel={`${value} trên 5 sao`} accessibilityState={{selected: rating === value}} onPress={() => setRating(value)} style={[styles.ratingButton, rating === value ? styles.ratingSelected : undefined]}>
                  <Text style={[styles.star, rating >= value ? styles.starSelected : undefined]}>★</Text>
                  <Text style={[styles.ratingNumber, rating === value ? styles.ratingNumberSelected : undefined]}>{value}</Text>
                </Pressable>
              ))}
            </View>
          </ParentCard>

          <ParentCard style={styles.notesCard}>
            <Text style={styles.promptTitle}>Bạn muốn ghi lại điều gì?</Text>
            <View style={styles.chipGroup}>
              {quickNotes.map((label) => {
                const selected = selectedNotes.includes(label);
                return <Pressable key={label} accessibilityRole="checkbox" accessibilityState={{checked: selected}} onPress={() => setSelectedNotes((current) => selected ? current.filter((item) => item !== label) : [...current, label])} style={[styles.noteChip, selected ? styles.noteChipSelected : undefined]}><Text style={[styles.noteChipText, selected ? styles.noteChipTextSelected : undefined]}>{label}</Text></Pressable>;
              })}
            </View>
            <ParentField label="Lời nhắn thêm · không bắt buộc" value={note} onChangeText={setNote} placeholder="Một điều nhỏ ba mẹ muốn chia sẻ…" multiline numberOfLines={3} maxLength={240}/>
            <Text style={styles.characterCount}>{note.length}/240</Text>
          </ParentCard>

          <InfoBanner title="Không gửi ảnh hay giọng nói của trẻ" body="Phản hồi ở đây chỉ dành cho trải nghiệm phiên. Nội dung thực tế sẽ được xác định khi API và chính sách lưu phản hồi sẵn sàng." />
          <ParentButton title="Ghi nhận · bản preview" icon="check" disabled={rating === 0 && selectedNotes.length === 0 && note.trim().length === 0} onPress={() => setSubmitted(true)} />
          <ParentButton title="Bỏ qua phản hồi" variant="secondary" onPress={finish}/>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 14},
  ratingCard: {gap: 15, padding: 15},
  promptRow: {flexDirection: 'row', alignItems: 'center', gap: 9},
  promptIcon: {width: 38, height: 38, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: sketchColors.coralSoft},
  promptCopy: {flex: 1, gap: 3},
  promptTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  promptHint: {color: sketchColors.muted, fontSize: 10},
  ratingRow: {flexDirection: 'row', justifyContent: 'space-between', gap: 7},
  ratingButton: {flex: 1, minHeight: 62, alignItems: 'center', justifyContent: 'center', gap: 2, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 14, backgroundColor: sketchColors.white},
  ratingSelected: {borderColor: sketchColors.green, backgroundColor: sketchColors.greenSoft},
  star: {color: '#B9C3BA', fontSize: 21, lineHeight: 24},
  starSelected: {color: '#D7A93D'},
  ratingNumber: {color: sketchColors.muted, fontSize: 9, fontWeight: '800'},
  ratingNumberSelected: {color: sketchColors.greenDark},
  notesCard: {gap: 12, padding: 15},
  chipGroup: {flexDirection: 'row', flexWrap: 'wrap', gap: 7},
  noteChip: {minHeight: 40, justifyContent: 'center', paddingHorizontal: 11, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 999, backgroundColor: sketchColors.white},
  noteChipSelected: {borderColor: sketchColors.green, backgroundColor: sketchColors.greenSoft},
  noteChipText: {color: sketchColors.inkSoft, fontSize: 10, fontWeight: '700'},
  noteChipTextSelected: {color: sketchColors.greenDark},
  characterCount: {alignSelf: 'flex-end', marginTop: -8, color: sketchColors.muted, fontSize: 9},
  doneCard: {alignItems: 'center', gap: 10, padding: 20},
  doneIcon: {width: 55, height: 55, alignItems: 'center', justifyContent: 'center', borderRadius: 20, backgroundColor: '#FFFFFFA8'},
  doneTitle: {color: sketchColors.ink, fontSize: 15, fontWeight: '900', textAlign: 'center'},
  doneBody: {color: sketchColors.inkSoft, fontSize: 11, lineHeight: 17, textAlign: 'center'},
});
