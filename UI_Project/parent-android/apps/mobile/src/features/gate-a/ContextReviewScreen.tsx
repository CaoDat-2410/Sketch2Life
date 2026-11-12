import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps, ParentProfileContext} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

export function ContextReviewScreen({state, dispatch, onNavigate}: ParentFlowProps): React.JSX.Element {
  const profile = state.childProfiles.find((item) => item.id === (state.activeRunChild?.id ?? state.childId));
  const contextItems = ([
    {key: 'interests', title: 'Sở thích', detail: profile?.context.interests ?? ''},
    {key: 'observations', title: 'Quan sát', detail: profile?.context.observations ?? ''},
    {key: 'achievements', title: 'Điều con đã làm được', detail: profile?.context.achievements ?? ''},
    {key: 'outsideAppExperiences', title: 'Trải nghiệm ngoài ứng dụng', detail: profile?.context.outsideAppExperiences ?? ''},
  ] as const).filter((item) => item.detail.trim().length > 0);
  return (
    <View style={styles.page}>
      <PreviewBanner title="Chọn thông tin cho run này" body="Lựa chọn chỉ nằm trong preview; chưa tạo context snapshot hoặc gửi lên máy chủ." />
      <ScreenIntro eyebrow="BƯỚC 4 · QUYỀN RIÊNG TƯ" title="Ba mẹ duyệt ngữ cảnh" description={`${profile?.name ?? state.childName} · ${profile?.age ?? state.childAge}`} />
      <ParentCard style={styles.summary}>
        <View style={styles.summaryHeader}><View style={styles.lockIcon}><ParentIcon name="lock" size={20}/></View><View style={styles.summaryCopy}><Text style={styles.summaryTitle}>Chỉ dùng điều cần thiết</Text><Text style={styles.summaryBody}>Thông tin hồ sơ không tự động đi vào câu chuyện.</Text></View></View>
        <View style={styles.divider}/>
        {contextItems.length > 0 ? contextItems.map((item) => <ContextLine key={item.key} title={item.title} detail={item.detail} included={state.contextIncludedFields.includes(item.key)} onPress={() => dispatch({type: 'SET_CONTEXT_FIELD_INCLUDED', field: item.key, included: !state.contextIncludedFields.includes(item.key)})}/>) : <Text style={styles.emptyContext}>Hồ sơ chưa có thông tin bổ sung. Ba mẹ có thể tiếp tục mà không đưa thêm dữ liệu vào run.</Text>}
        <ContextLine title="Nhu cầu hỗ trợ hoặc chẩn đoán" detail="Không đưa vào snapshot này" included={false} disabled/>
      </ParentCard>
      <InfoBanner title="Chọn từng mục nếu cần" body={state.contextIncludedFields.length ? `${state.contextIncludedFields.length} mục được chọn cho preview.` : 'Hiện không có thông tin bổ sung nào được chọn.'} />
      {state.contextApproved ? <ParentPill label="Đã xem trong bản preview" /> : null}
      <ParentButton
        title="Xác nhận lựa chọn · preview"
        icon="check"
        onPress={() => {
          dispatch({type: 'APPROVE_CONTEXT'});
          onNavigate('activity-suggestions');
        }}
      />
    </View>
  );
}

function ContextLine({title, detail, included, onPress, disabled = false}: Readonly<{title: string; detail: string; included: boolean; onPress?: () => void; disabled?: boolean}>): React.JSX.Element {
  const content = <>
      <View style={[styles.statusDot, included ? styles.included : styles.excluded]}><ParentIcon name={included ? 'check' : 'close'} size={12} color={included ? sketchColors.greenDark : sketchColors.coral}/></View>
      <View style={styles.contextCopy}><Text style={styles.contextTitle}>{title}</Text><Text style={styles.contextDetail}>{detail}</Text></View>
      {onPress ? <ParentIcon name={included ? 'check' : 'plus'} size={16} color={sketchColors.greenDark}/> : null}
  </>;
  return onPress ? <Pressable accessibilityRole="checkbox" accessibilityState={{checked: included}} onPress={onPress} style={({pressed}) => [styles.contextLine, pressed ? styles.pressed : undefined]}>{content}</Pressable> : <View accessibilityRole="text" style={[styles.contextLine, disabled ? styles.contextDisabled : undefined]}>{content}</View>;
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 16},
  summary: {gap: 14},
  summaryHeader: {flexDirection: 'row', alignItems: 'center', gap: 10},
  lockIcon: {width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: sketchColors.greenSoft},
  summaryCopy: {flex: 1, gap: 3},
  summaryTitle: {color: sketchColors.ink, fontSize: 14, fontWeight: '900'},
  summaryBody: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
  divider: {height: 1, backgroundColor: sketchColors.line},
  contextLine: {minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 5},
  contextDisabled: {opacity: 0.72},
  pressed: {opacity: 0.7},
  statusDot: {width: 30, height: 30, alignItems: 'center', justifyContent: 'center', borderRadius: 11},
  included: {backgroundColor: sketchColors.greenSoft},
  excluded: {backgroundColor: sketchColors.coralSoft},
  contextCopy: {flex: 1, gap: 2},
  contextTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '800'},
  contextDetail: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
  emptyContext: {color: sketchColors.muted, fontSize: 10, lineHeight: 15},
});
