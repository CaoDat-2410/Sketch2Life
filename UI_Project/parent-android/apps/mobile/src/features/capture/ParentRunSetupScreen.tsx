import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ParentToggleRow, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchRadius, sketchSpace} from '../../shared/ui/SketchTokens';

export function ParentRunSetupScreen({state, dispatch, onNavigate}: ParentFlowProps): React.JSX.Element {
  const childName = state.activeRunChild?.name ?? state.childName;
  const childAge = state.activeRunChild?.age ?? state.childAge;
  const lessonTitle = state.activeRunLesson?.title ?? state.lessonTitle;
  const lessonVersion = state.activeRunLesson?.version ?? state.lessonVersion;
  const scriptChoice = state.activeRunLesson?.scriptFollowingChoice ?? state.scriptFollowingChoice;
  return (
    <View style={styles.page}>
      <PreviewBanner title="Chuẩn bị một câu chuyện" body="Bản xem trước giữ thay đổi trong bộ nhớ phiên này; chưa tạo run trên máy chủ." />
      <ScreenIntro eyebrow="BƯỚC 1 · CHUẨN BỊ" title="Sẵn sàng vẽ chưa?" description="Chỉ chọn một hồ sơ trẻ cho mỗi lần kể chuyện." />
      <ParentCard style={styles.child}>
        <View style={styles.avatar}><Text style={styles.avatarLetter}>{childName.replace(/^Bé\s*/, '').charAt(0)}</Text></View>
        <View style={styles.childCopy}><Text style={styles.childName}>{childName}</Text><Text style={styles.muted}>{childAge} · {state.activeRunChild ? 'Đã ghim cho run' : 'Hồ sơ đang chọn'}</Text></View>
        {!state.activeRunChild ? <ParentButton title="Đổi" variant="secondary" onPress={() => onNavigate('profiles')} /> : null}
      </ParentCard>
      <ParentCard style={styles.lesson}>
        <View style={styles.lessonIcon}><ParentIcon name="book" size={22} /></View>
        <View style={styles.lessonCopy}>
          <Text style={styles.label}>HƯỚNG KỂ CHUYỆN</Text>
          <Text style={styles.lessonTitle}>{lessonTitle ?? 'Chưa chọn giáo án'}</Text>
          <Text style={styles.muted}>{lessonVersion ?? 'Ba mẹ có thể bắt đầu từ ý tưởng của con'}</Text>
        </View>
        {!state.activeRunChild ? <ParentButton title={state.lessonId ? 'Đổi' : 'Chọn'} variant="quiet" onPress={() => onNavigate('lesson-library')} /> : null}
      </ParentCard>
      {lessonTitle ? (
        <ParentCard style={styles.scriptCard}>
          <Text style={styles.scriptTitle}>Hướng kể chuyện</Text>
          <Text style={styles.muted}>SRS chưa đặt mặc định. Ba mẹ chọn cách dùng giáo án cho run này.</Text>
          <View style={styles.scriptChoices}>
            <ScriptChoice
              selected={scriptChoice === 'follow-lesson'}
              title="Theo hướng giáo án"
              detail="Dùng lesson làm định hướng"
              onPress={() => dispatch({type: 'SET_SCRIPT_FOLLOWING', value: 'follow-lesson'})}
            />
            <ScriptChoice
              selected={scriptChoice === 'free-story'}
              title="Kể tự do"
              detail="Không theo kịch bản giáo án"
              onPress={() => dispatch({type: 'SET_SCRIPT_FOLLOWING', value: 'free-story'})}
            />
          </View>
        </ParentCard>
      ) : null}
      <ParentCard tone="gold" style={styles.paperCard}>
        <View style={styles.paperHead}><ParentPill label="CHUẨN BỊ" tone="gold"/><ParentIcon name="sun" color="#806218" size={22}/></View>
        <Text style={styles.paperTitle}>Giấy và bút màu</Text>
        <Text style={styles.paperBody}>Để con tự vẽ trước. Khi con xong, ba mẹ chụp một bức tranh của riêng con.</Text>
        <View style={styles.stepLine}><View style={styles.stepDotActive}/><View style={styles.stepConnector}/><View style={styles.stepDot}/><View style={styles.stepConnector}/><View style={styles.stepDot}/></View>
        <Text style={styles.stepText}>Vẽ tự do  →  Chụp tranh  →  Cùng kể chuyện</Text>
      </ParentCard>
      <ParentCard tone="muted" style={styles.guideCard}>
        <View style={styles.guideHeader}><View style={styles.guideIcon}><ParentIcon name="spark" size={18}/></View><Text style={styles.guideTitle}>Gợi ý nét vẽ · tùy chọn</Text></View>
        <ParentToggleRow
          title="Bật line-sketch khi con vẽ"
          description="Chỉ dùng chủ đề chung và độ khó đơn giản; không gửi hồ sơ, tuổi cụ thể, giọng nói hay tranh của con."
          value={state.lineSketchEnabled}
          onValueChange={(enabled) => dispatch({type: 'SET_LINE_SKETCH', enabled})}
        />
        {state.lineSketchEnabled ? <Text style={styles.guideNote}>Đã bật trong bản preview. Dịch vụ chưa kết nối; bỏ qua vẫn tiếp tục được.</Text> : null}
      </ParentCard>
      <InfoBanner title="Ba mẹ kiểm soát mọi cổng duyệt" body="Chủ thể, ngữ cảnh và kịch bản đều cần được xem lại trước khi gửi xử lý." />
      <InfoBanner title="Mỗi ba mẹ chỉ có một run đang hoạt động" body="Nếu backend báo đang có run khác, bản thật sẽ đưa ba mẹ về run hiện tại thay vì tạo run trùng." tone="warning" />
      <ParentButton title={state.activeRunChild ? 'Tiếp tục chụp tranh' : 'Bắt đầu giờ vẽ'} icon="arrow" disabled={Boolean(lessonTitle && scriptChoice === 'unset' && !state.activeRunChild)} onPress={() => {
        if (!state.activeRunChild) dispatch({type: 'BEGIN_RUN_PREVIEW'});
        onNavigate('capture');
      }} />
      <Text style={styles.footnote}>Gợi ý nét vẽ AI là tùy chọn và không cần thiết để tiếp tục.</Text>
    </View>
  );
}

function ScriptChoice({selected, title, detail, onPress}: Readonly<{selected: boolean; title: string; detail: string; onPress: () => void}>): React.JSX.Element {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{selected}}
      onPress={onPress}
      style={[styles.scriptChoice, selected ? styles.scriptChoiceSelected : undefined]}>
      <View style={[styles.radio, selected ? styles.radioSelected : undefined]}>{selected ? <View style={styles.radioDot}/> : null}</View>
      <View style={styles.scriptCopy}><Text style={styles.scriptChoiceTitle}>{title}</Text><Text style={styles.scriptChoiceDetail}>{detail}</Text></View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 16},
  child: {flexDirection: 'row', alignItems: 'center', gap: 11, padding: 12},
  avatar: {width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 17, backgroundColor: '#DCEBDD'},
  avatarLetter: {color: sketchColors.greenDark, fontSize: 20, fontWeight: '900'},
  childCopy: {flex: 1, gap: 3},
  childName: {color: sketchColors.ink, fontSize: 14, fontWeight: '900'},
  muted: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
  lesson: {flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12},
  lessonIcon: {width: 41, height: 41, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: sketchColors.greenSoft},
  lessonCopy: {flex: 1, gap: 3},
  label: {color: sketchColors.muted, fontSize: 9, fontWeight: '900', letterSpacing: 1},
  lessonTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  scriptCard: {gap: 10},
  scriptTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  scriptChoices: {gap: 8, marginTop: 2},
  scriptChoice: {minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 10, padding: 10, borderWidth: 1, borderColor: sketchColors.line, borderRadius: 14, backgroundColor: sketchColors.surface},
  scriptChoiceSelected: {borderColor: sketchColors.green, backgroundColor: sketchColors.greenSoft},
  radio: {width: 20, height: 20, alignItems: 'center', justifyContent: 'center', borderWidth: 1.5, borderColor: sketchColors.muted, borderRadius: 10},
  radioSelected: {borderColor: sketchColors.green},
  radioDot: {width: 10, height: 10, borderRadius: 5, backgroundColor: sketchColors.green},
  scriptCopy: {flex: 1, gap: 2},
  scriptChoiceTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '800'},
  scriptChoiceDetail: {color: sketchColors.muted, fontSize: 10},
  paperCard: {gap: 11, padding: 16, borderRadius: sketchRadius.lg},
  paperHead: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'},
  paperTitle: {color: sketchColors.ink, fontSize: 18, fontWeight: '900'},
  paperBody: {color: sketchColors.inkSoft, fontSize: 12, lineHeight: 18},
  stepLine: {flexDirection: 'row', alignItems: 'center', marginTop: 4},
  stepDotActive: {width: 12, height: 12, borderRadius: 8, backgroundColor: sketchColors.green},
  stepDot: {width: 10, height: 10, borderRadius: 8, backgroundColor: '#C4D0C5'},
  stepConnector: {height: 2, flex: 1, backgroundColor: '#C4D0C5'},
  stepText: {color: sketchColors.muted, fontSize: 10, fontWeight: '700'},
  footnote: {color: sketchColors.muted, fontSize: 10, textAlign: 'center'},
  guideCard: {gap: 12},
  guideHeader: {flexDirection: 'row', alignItems: 'center', gap: 9},
  guideIcon: {width: 32, height: 32, alignItems: 'center', justifyContent: 'center', borderRadius: 11, backgroundColor: sketchColors.white},
  guideTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '900'},
  guideNote: {color: sketchColors.greenDark, fontSize: 10, lineHeight: 15},
});
