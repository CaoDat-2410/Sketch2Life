import {Pressable, StyleSheet, Switch, Text, View} from 'react-native';
import {useState} from 'react';
import type {ReactNode} from 'react';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentIcon, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchSpace} from '../../shared/ui/SketchTokens';

type PushPreviewScenario = 'supported' | 'denied' | 'unsupported' | 'invalid-endpoint';
const pushScenarios: readonly Readonly<{id: PushPreviewScenario; label: string; detail: string}>[] = [
  {id: 'supported', label: 'Hỗ trợ', detail: 'Thiết bị mẫu hỗ trợ; tùy chọn dưới đây chỉ đổi fixture, chưa mở quyền Android.'},
  {id: 'denied', label: 'Bị từ chối', detail: 'Không hỏi lại liên tục. Inbox vẫn nhận notice; đổi quyền trong cài đặt thiết bị khi tích hợp.'},
  {id: 'unsupported', label: 'Chưa hỗ trợ', detail: 'Push chưa khả dụng trên thiết bị mẫu. Inbox vẫn là nguồn thông báo chính.'},
  {id: 'invalid-endpoint', label: 'Endpoint lỗi', detail: 'Endpoint lỗi cần được thu hồi; không retry vô hạn và không lộ token.'},
];

export function ParentSettingsScreen({state, dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  const [pushScenario, setPushScenario] = useState<PushPreviewScenario>('supported');
  const notificationsEnabled = pushScenario === 'supported' && state.pushPreference === 'enabled-preview';
  const currentPushScenario = pushScenarios.find((item) => item.id === pushScenario) ?? pushScenarios[0];
  const notificationStatus = notificationsEnabled
    ? 'Đang bật · preview'
    : state.pushPreference === 'revoked-preview'
      ? 'Đã tắt · preview'
      : 'Chưa bật';
  return (
    <View style={styles.page}>
      <PreviewBanner title="Phiên trải nghiệm trên thiết bị" body="Chưa đăng nhập thật; thoát sẽ quay về màn xác thực." />
      <ScreenIntro eyebrow="TÀI KHOẢN GIA ĐÌNH" title="Cài đặt" description="Quản lý hồ sơ, riêng tư và các tùy chọn của phụ huynh." />
      <ParentCard style={styles.account}>
        <View style={styles.accountIcon}><ParentIcon name="child" size={20}/></View>
        <View style={styles.accountCopy}><Text style={styles.accountName}>Tài khoản Parent</Text><Text style={styles.accountEmail}>Chưa kết nối xác thực</Text></View>
      </ParentCard>
      <View style={styles.group}>
        <Text style={styles.groupLabel}>GIA ĐÌNH</Text>
        <SettingLink title="Hồ sơ của con" detail="Chọn hồ sơ cho run tiếp theo" icon="child" onPress={() => onNavigate('profiles')}/>
        <SettingLink title="Chia sẻ hồ sơ" detail="Lời mời và thu hồi quyền" icon="share" onPress={() => onNavigate('sharing')}/>
      </View>
      <View style={styles.group}>
        <Text style={styles.groupLabel}>ỨNG DỤNG</Text>
        <InfoBanner title="Thông báo chỉ nhắc việc cần xem" body="Không gửi tên trẻ, câu chuyện hoặc video qua push. Ba mẹ có thể tắt lựa chọn bất cứ lúc nào." />
        <ParentCard style={styles.pushScenarioCard}>
          <Text style={styles.linkTitle}>Tình huống thiết bị</Text>
          <View style={styles.pushScenarioOptions}>
            {pushScenarios.map((item) => <Pressable key={item.id} accessibilityRole="button" accessibilityState={{selected: pushScenario === item.id}} onPress={() => setPushScenario(item.id)} style={[styles.pushScenarioOption, pushScenario === item.id ? styles.pushScenarioSelected : undefined]}><Text style={[styles.pushScenarioText, pushScenario === item.id ? styles.pushScenarioTextSelected : undefined]}>{item.label}</Text></Pressable>)}
          </View>
          <Text style={styles.pushScenarioDetail}>{currentPushScenario.detail}</Text>
          {pushScenario === 'denied' ? <ParentButton title="Xem hướng dẫn cài đặt quyền" variant="quiet" onPress={() => onNotice('Preview không mở quyền hệ điều hành. Khi tích hợp, người dùng có thể đổi quyền trong cài đặt thiết bị.')} /> : null}
          {pushScenario === 'invalid-endpoint' ? <ParentButton title="Thu hồi endpoint · preview" variant="quiet" onPress={() => { dispatch({type: 'SET_PUSH_PREFERENCE', value: 'revoked-preview'}); onNotice('Đã mô phỏng thu hồi endpoint; không gửi request hoặc token lên máy chủ.'); }} /> : null}
        </ParentCard>
        <ParentCard style={styles.pushPreference}>
          <View style={styles.pushIcon}><ParentIcon name="notifications" size={17}/></View>
          <View style={styles.pushCopy}>
            <Text style={styles.linkTitle}>Thông báo trên thiết bị</Text>
            <Text style={styles.linkDetail}>{notificationStatus}</Text>
          </View>
          <Switch
            accessibilityRole="switch"
            accessibilityLabel="Cho phép Sketch2Life gửi thông báo"
            accessibilityState={{checked: notificationsEnabled, disabled: pushScenario !== 'supported'}}
            value={notificationsEnabled}
            disabled={pushScenario !== 'supported'}
            onValueChange={(enabled) => dispatch({type: 'SET_PUSH_PREFERENCE', value: enabled ? 'enabled-preview' : 'revoked-preview'})}
            trackColor={{false: sketchColors.line, true: sketchColors.green}}
            thumbColor={sketchColors.white}
          />
        </ParentCard>
        <Text style={styles.pushHint}>Chỉ đổi trạng thái xem trước; chưa mở quyền Android hoặc đăng ký thiết bị với máy chủ. Inbox vẫn khả dụng khi push bị từ chối hoặc không hỗ trợ.</Text>
        <SettingLink title="Hộp thư thông báo" detail="Trạng thái và lời nhắc" icon="notifications" onPress={() => onNavigate('notifications')}/>
        <SettingLink title="Lượt tạo" detail="Quota và thông tin giới hạn" icon="quota" onPress={() => onNavigate('quota')}/>
        <SettingLink title="Phản hồi giáo án" detail="Trao đổi riêng, không gửi media" icon="heart" onPress={() => onNavigate('feedback')}/>
      </View>
      <InfoBanner title="Quyền dữ liệu cần API thật" body="Xuất dữ liệu, xóa tài khoản và tùy chỉnh thời hạn lưu cần được thực hiện an toàn trên máy chủ." />
      <ParentButton title="Thoát bản xem trước" variant="secondary" onPress={() => dispatch({type: 'EXIT_PREVIEW'})} />
      {__DEV__ ? <ParentButton title="Mở fixture kỹ thuật" variant="quiet" onPress={() => onNavigate('fixture')} /> : null}
      <ParentButton title="Liên hệ hỗ trợ" variant="quiet" onPress={() => onNotice('Kênh hỗ trợ sẽ được cấu hình trước khi phát hành.')} />
    </View>
  );
}

function SettingLink({title, detail, icon, onPress}: Readonly<{title: string; detail: string; icon: 'child' | 'share' | 'notifications' | 'quota' | 'heart'; onPress: () => void}>): React.JSX.Element {
  return (
    <ParentButtonRow onPress={onPress} accessibilityLabel={`${title}. ${detail}`}>
      <View style={styles.linkIcon}><ParentIcon name={icon} size={17}/></View>
      <View style={styles.linkCopy}><Text style={styles.linkTitle}>{title}</Text><Text style={styles.linkDetail}>{detail}</Text></View>
      <ParentIcon name="arrow" size={16} color={sketchColors.muted}/>
    </ParentButtonRow>
  );
}

function ParentButtonRow({children, onPress, accessibilityLabel}: Readonly<{children: ReactNode; onPress: () => void; accessibilityLabel: string}>): React.JSX.Element {
  return <Pressable accessibilityRole="button" accessibilityLabel={accessibilityLabel} onPress={onPress} style={({pressed}) => [styles.link, pressed ? styles.pressed : undefined]}>{children}</Pressable>;
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 15},
  account: {flexDirection: 'row', alignItems: 'center', gap: 11},
  accountIcon: {width: 43, height: 43, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: sketchColors.greenSoft},
  accountCopy: {flex: 1, gap: 3},
  accountName: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  accountEmail: {color: sketchColors.muted, fontSize: 10},
  pushPreference: {flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 11, paddingHorizontal: 12},
  pushScenarioCard: {gap: 9, padding: 12},
  pushScenarioOptions: {flexDirection: 'row', flexWrap: 'wrap', gap: 7},
  pushScenarioOption: {minHeight: 44, justifyContent: 'center', paddingHorizontal: 11, borderRadius: 12, backgroundColor: sketchColors.surfaceMuted},
  pushScenarioSelected: {backgroundColor: sketchColors.greenSoft, borderWidth: 1, borderColor: sketchColors.green},
  pushScenarioText: {color: sketchColors.muted, fontSize: 10, fontWeight: '800'},
  pushScenarioTextSelected: {color: sketchColors.greenDark},
  pushScenarioDetail: {color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  pushIcon: {width: 34, height: 34, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: sketchColors.greenSoft},
  pushCopy: {flex: 1, gap: 3},
  pushHint: {paddingHorizontal: 12, color: sketchColors.muted, fontSize: 9, lineHeight: 14},
  group: {gap: 5},
  groupLabel: {color: sketchColors.muted, fontSize: 9, fontWeight: '900', letterSpacing: 1.2, marginBottom: 2},
  link: {minHeight: 66, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 10, borderBottomWidth: 1, borderColor: sketchColors.line},
  pressed: {opacity: 0.72},
  linkIcon: {width: 36, height: 36, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: sketchColors.surfaceMuted},
  linkCopy: {flex: 1, gap: 3},
  linkTitle: {color: sketchColors.ink, fontSize: 11, fontWeight: '800'},
  linkDetail: {color: sketchColors.muted, fontSize: 9},
});
