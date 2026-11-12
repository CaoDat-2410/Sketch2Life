import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPage, ParentPill, ParentSectionHeading} from '../../shared/ui/ParentCard';
import {sketchColors, sketchRadius, sketchSpace} from '../../shared/ui/SketchTokens';

const lessons = [
  {id: 'lesson-garden', title: 'Khu vườn tí hon', area: 'Thiên nhiên', age: 'Mầm non', color: '#DDEBDD', version: 'Bản xem trước · v1', source: 'Công khai'},
  {id: 'lesson-sky', title: 'Chuyến đi trên mây', area: 'Tưởng tượng', age: 'Mầm non', color: '#E1ECF3', version: 'Bản xem trước · v1', source: 'Được chia sẻ'},
  {id: 'lesson-colors', title: 'Sắc màu quanh em', area: 'Mỹ thuật', age: 'Mầm non', color: '#F8E8DC', version: 'Bản xem trước · v1', source: 'Từng học'},
];
const categories = ['Tất cả', 'Công khai', 'Được chia sẻ', 'Từng học'] as const;

export function ParentLessonLibraryScreen({state, dispatch, onNavigate}: ParentFlowProps): React.JSX.Element {
  const [category, setCategory] = useState<(typeof categories)[number]>('Tất cả');
  const visibleLessons = category === 'Tất cả' ? lessons : lessons.filter((lesson) => lesson.source === category);
  return (
    <ParentPage>
      <PreviewBanner title="Thư viện minh họa" body="Chưa tải giáo án từ máy chủ; các thẻ dưới đây là dữ liệu mẫu." />
      {state.activeRunChild ? <InfoBanner title="Phiên bản đang được ghim" body="Không thể đổi giáo án giữa run; hãy hoàn tất hoặc hủy run trước." tone="warning" /> : null}
      <ParentSectionHeading eyebrow="CẢM HỨNG CHO BÉ" title="Thư viện giáo án" />
      <Text style={styles.subtitle}>Chọn một hướng kể chuyện. Phiên bản gốc được giữ nguyên.</Text>
      <View accessibilityRole="tabbar" style={styles.filters}>
        {categories.map((item) => <Pressable key={item} accessibilityRole="tab" accessibilityState={{selected: category === item}} onPress={() => setCategory(item)} style={[styles.filter, category === item ? styles.filterActive : undefined]}><Text style={[styles.filterText, category === item ? styles.filterTextActive : undefined]}>{item}</Text></Pressable>)}
      </View>
      <View style={styles.list}>
        {visibleLessons.map((lesson, index) => {
          const isSelected = (state.activeRunLesson?.id ?? state.lessonId) === lesson.id;
          return (
            <Pressable
              key={lesson.id}
              disabled={Boolean(state.activeRunChild)}
              accessibilityRole="button"
              accessibilityLabel={`Xem giáo án ${lesson.title}`}
              onPress={() => {
                dispatch({type: 'SELECT_LESSON', id: lesson.id, title: lesson.title, version: lesson.version});
                onNavigate('lesson-detail');
              }}
              style={({pressed}) => [styles.cardPress, pressed ? styles.pressed : undefined]}>
              <ParentCard style={[styles.lessonCard, isSelected ? styles.selected : undefined]}>
                <View style={[styles.art, {backgroundColor: lesson.color}]}>
                  <View style={[styles.artCircle, {right: 13 + index * 3}]} />
                  <View style={[styles.artLeaf, {transform: [{rotate: `${-16 + index * 16}deg`}]}]} />
                  <View style={styles.artGround} />
                  <Text style={styles.artNumber}>{String(index + 1).padStart(2, '0')}</Text>
                </View>
                <View style={styles.cardBody}>
                  <View style={styles.cardTitleRow}>
                    <Text style={styles.lessonTitle}>{lesson.title}</Text>
                    <ParentIcon name="arrow" size={17} />
                  </View>
                  <Text style={styles.meta}>{lesson.area} · {lesson.age}</Text>
                  <View style={styles.badges}><ParentPill label={lesson.version} tone="gray" /><ParentPill label={lesson.source} tone="gold" /></View>
                </View>
              </ParentCard>
            </Pressable>
          );
        })}
      </View>
      <ParentButton title="Tiếp tục không chọn giáo án" variant="quiet" disabled={Boolean(state.activeRunChild)} onPress={() => onNavigate('run-setup')} />
    </ParentPage>
  );
}

const styles = StyleSheet.create({
  subtitle: {color: sketchColors.muted, fontSize: 12, lineHeight: 18, marginTop: -10},
  filters: {flexDirection: 'row', flexWrap: 'wrap', gap: 7},
  filter: {minHeight: 44, justifyContent: 'center', paddingHorizontal: 12, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 14, backgroundColor: sketchColors.surface},
  filterActive: {borderColor: sketchColors.green, backgroundColor: sketchColors.greenSoft},
  filterText: {color: sketchColors.muted, fontSize: 10, fontWeight: '700'},
  filterTextActive: {color: sketchColors.greenDark, fontWeight: '900'},
  list: {gap: 12},
  cardPress: {borderRadius: sketchRadius.md},
  pressed: {opacity: 0.86},
  lessonCard: {padding: 0, overflow: 'hidden'},
  selected: {borderColor: sketchColors.green, borderWidth: 2},
  art: {height: 136, overflow: 'hidden', position: 'relative'},
  artCircle: {position: 'absolute', top: 15, width: 48, height: 48, borderRadius: 30, backgroundColor: '#F0C75E'},
  artLeaf: {position: 'absolute', top: 53, left: '45%', width: 25, height: 37, borderRadius: 22, backgroundColor: '#8DB697'},
  artGround: {position: 'absolute', left: -18, right: -18, bottom: -55, height: 94, borderRadius: 70, backgroundColor: '#9CBFA1'},
  artNumber: {position: 'absolute', left: 16, top: 12, color: '#33584B', fontSize: 10, fontWeight: '900', letterSpacing: 1.4},
  cardBody: {padding: sketchSpace.lg, gap: 8},
  cardTitleRow: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8},
  lessonTitle: {color: sketchColors.ink, fontSize: 15, fontWeight: '900'},
  meta: {color: sketchColors.muted, fontSize: 11},
  badges: {flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 2},
});
