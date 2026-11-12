import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentFlowProps} from '../../app/navigation/parentRoutes';
import {InfoBanner, PreviewBanner} from '../../shared/ui/FeedbackState';
import {ParentButton, ParentCard, ParentField, ParentIcon, ParentPill, ScreenIntro} from '../../shared/ui/ParentCard';
import {sketchColors, sketchRadius, sketchSpace} from '../../shared/ui/SketchTokens';

export function ParentCaptureScreen({state, dispatch, onNavigate, onNotice}: ParentFlowProps): React.JSX.Element {
  const [guideIndex, setGuideIndex] = useState(0);
  const [guideVisible, setGuideVisible] = useState(state.lineSketchEnabled);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const guides = [
    {title: 'Bông hoa trong vườn', steps: ['Vẽ một vòng tròn nhỏ ở giữa.', 'Thêm 5 cánh hoa thật to.', 'Vẽ thân và hai chiếc lá xanh.']},
    {title: 'Chú bướm vui vẻ', steps: ['Vẽ một nét cong làm thân.', 'Thêm hai đôi cánh tròn.', 'Cho bướm một khuôn mặt vui.']},
    {title: 'Mặt trời buổi sáng', steps: ['Vẽ một hình tròn ở giữa.', 'Thêm các tia nắng ngắn.', 'Vẽ đám mây bên cạnh.']},
  ] as const;
  const guide = guides[guideIndex];
  return (
    <View style={styles.page}>
      <PreviewBanner title="Ảnh mẫu chưa được tải lên" body="Camera và thư viện ảnh chưa nối adapter. Bản này chỉ cho xem bố cục bước chụp." />
      <ScreenIntro eyebrow="BƯỚC 2 · TRANH CỦA CON" title="Con vẽ xong rồi?" description="Chụp rõ toàn bộ tranh, đủ sáng và chỉ dùng tranh của hồ sơ đang chọn." />
      <ParentCard style={styles.profileLock}>
        <View style={styles.profileMark}><ParentIcon name="lock" size={17}/></View>
        <View style={styles.profileText}><Text style={styles.profileName}>Ảnh của {state.activeRunChild?.name ?? state.childName}</Text><Text style={styles.profileHint}>Run gắn với đúng một hồ sơ trẻ</Text></View>
      </ParentCard>

      <ParentCard style={styles.drawing}>
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.artwork}>
          <View style={styles.artSun}/><View style={styles.artCloud}/><View style={styles.artStem}/><View style={styles.artLeaf}/><View style={styles.artFlower}/><View style={styles.artGround}/>
          <View style={styles.paperEdge}/>
        </View>
        <View style={styles.artCaption}><Text style={styles.artTitle}>Khung ảnh tranh</Text><Text style={styles.artHint}>Tỉ lệ khung hình được giữ ổn định</Text></View>
      </ParentCard>

      <View style={styles.captureActions}>
        <ParentButton title="Mở camera" icon="camera" onPress={() => { setPhotoError('Camera chưa được cấp quyền trong preview. Cho phép camera hoặc chọn ảnh từ thư viện khi ứng dụng thật sẵn sàng.'); onNotice('Camera chưa được nối; chưa chụp ảnh nào.'); }} />
        <ParentButton title="Chọn từ thư viện" icon="plus" variant="secondary" onPress={() => { setPhotoError('Thư viện chưa có adapter. Chưa có tệp nào được tải hoặc kiểm tra.'); onNotice('Thư viện ảnh chưa được nối; chưa có tệp nào được chọn.'); }} />
      </View>
      {photoError ? <View style={styles.photoError} accessibilityRole="alert"><View style={styles.errorIcon}><ParentIcon name="help" size={15} color="#8B4E40"/></View><View style={styles.errorCopy}><Text style={styles.errorTitle}>Chưa có ảnh hợp lệ</Text><Text style={styles.errorText}>{photoError}</Text></View><Pressable accessibilityRole="button" accessibilityLabel="Đóng thông báo ảnh" onPress={() => setPhotoError(null)} style={styles.errorClose}><ParentIcon name="close" size={15}/></Pressable></View> : null}

      {state.lineSketchEnabled && guideVisible ? (
        <ParentCard tone="gold" style={styles.guideCard}>
          <View style={styles.guideHeading}><View style={styles.guideIcon}><ParentIcon name="spark" size={17}/></View><View style={styles.guideCopy}><Text style={styles.guideEyebrow}>GỢI Ý NÉT VẼ · BẢN TĨNH</Text><Text style={styles.guideTitle}>{guide.title}</Text></View><ParentPill label="TÙY CHỌN" tone="gold"/></View>
          <View accessible accessibilityLabel={`Minh họa: ${guide.steps.join(' ')}`} style={styles.guideIllustration}>
            <View style={styles.guideSun}/><View style={styles.guidePetalTop}/><View style={styles.guidePetalLeft}/><View style={styles.guidePetalRight}/><View style={styles.guideCenter}/><View style={styles.guideStem}/><View style={styles.guideLeaf}/>
          </View>
          <View style={styles.guideSteps}>{guide.steps.map((step, index) => <View key={step} style={styles.guideStep}><Text style={styles.guideStepNumber}>{index + 1}</Text><Text style={styles.guideStepText}>{step}</Text></View>)}</View>
          <Text style={styles.guidePreviewNote}>Ví dụ minh họa · không được tạo bởi AI và không gửi dữ liệu của con.</Text>
          <View style={styles.guideActions}>
            <Pressable accessibilityRole="button" onPress={() => setGuideIndex((current) => (current + 1) % guides.length)} style={styles.guideAction}><ParentIcon name="spark" size={14}/><Text style={styles.guideActionText}>Đổi gợi ý</Text></Pressable>
            <Pressable accessibilityRole="button" onPress={() => setGuideVisible(false)} style={styles.guideAction}><Text style={styles.guideActionQuiet}>Bỏ qua</Text></Pressable>
          </View>
        </ParentCard>
      ) : state.lineSketchEnabled ? (
        <Pressable accessibilityRole="button" onPress={() => setGuideVisible(true)} style={styles.restoreGuide}><ParentIcon name="spark" size={15}/><Text style={styles.restoreGuideText}>Hiện lại gợi ý nét vẽ</Text></Pressable>
      ) : null}

      <ParentCard style={styles.ideaCard}>
        <View style={styles.ideaHead}><View style={styles.ideaIcon}><ParentIcon name="spark"/></View><View style={styles.ideaCopy}><Text style={styles.ideaTitle}>Ý tưởng của ba mẹ</Text><Text style={styles.ideaSub}>Không bắt buộc · có thể nhập chữ hoặc giọng nói</Text></View></View>
        <ParentField
          label="Ý tưởng bằng chữ"
          multiline
          numberOfLines={3}
          value={state.idea}
          onChangeText={(value) => dispatch({type: 'SET_IDEA', value})}
          placeholder="Ví dụ: Chú bướm tìm một khu vườn mới"
        />
        <ParentButton title="Thêm ý tưởng bằng giọng nói" icon="voice" variant="secondary" onPress={() => onNavigate('voice')} />
      </ParentCard>

      <InfoBanner title="Lỗi ảnh sẽ có bước khôi phục" body="Ảnh mờ, sai định dạng, quá dung lượng hoặc tải lỗi sẽ được giải thích và cho chọn lại; chưa có file nào trong bản preview." tone="warning"/>

      <ParentButton title="Xem bước duyệt chủ thể · mẫu" icon="arrow" onPress={() => onNavigate('understanding')} />
      <Text style={styles.footnote}>Trong sản phẩm thật, nút tiếp theo cần có ảnh hợp lệ từ đúng một hồ sơ.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {padding: sketchSpace.lg, gap: 16},
  drawing: {padding: 8, overflow: 'hidden'},
  profileLock: {flexDirection: 'row', alignItems: 'center', gap: 9, padding: 11},
  profileMark: {width: 33, height: 33, alignItems: 'center', justifyContent: 'center', borderRadius: 11, backgroundColor: sketchColors.greenSoft},
  profileText: {flex: 1, gap: 3},
  profileName: {color: sketchColors.ink, fontSize: 11, fontWeight: '900'},
  profileHint: {color: sketchColors.muted, fontSize: 9},
  artwork: {height: 208, overflow: 'hidden', alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: '#F5F2E7'},
  paperEdge: {position: 'absolute', top: 11, right: 11, bottom: 11, left: 11, borderRadius: 12, borderWidth: 1, borderColor: '#DCE2D1'},
  artSun: {position: 'absolute', top: 28, right: 57, width: 32, height: 32, borderRadius: 18, backgroundColor: '#EFC65D'},
  artCloud: {position: 'absolute', top: 45, left: 45, width: 57, height: 19, borderRadius: 15, backgroundColor: '#D4E6E6'},
  artStem: {position: 'absolute', bottom: 50, width: 5, height: 70, borderRadius: 4, backgroundColor: '#6F9C72'},
  artLeaf: {position: 'absolute', bottom: 92, left: '42%', width: 28, height: 17, borderRadius: 20, backgroundColor: '#8FB58B', transform: [{rotate: '-26deg'}]},
  artFlower: {position: 'absolute', bottom: 112, width: 25, height: 25, borderRadius: 15, backgroundColor: '#D9937E', borderWidth: 6, borderColor: '#EBC3A0'},
  artGround: {position: 'absolute', bottom: 36, left: 31, right: 31, height: 2, backgroundColor: '#9AB59A'},
  artCaption: {padding: 12, gap: 2},
  artTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  artHint: {color: sketchColors.muted, fontSize: 10},
  captureActions: {gap: 9},
  photoError: {flexDirection: 'row', alignItems: 'flex-start', gap: 9, padding: 11, borderRadius: 13, backgroundColor: sketchColors.coralSoft},
  errorIcon: {width: 29, height: 29, alignItems: 'center', justifyContent: 'center', borderRadius: 10, backgroundColor: '#FFFFFFB0'},
  errorCopy: {flex: 1, gap: 3},
  errorTitle: {color: '#8B4E40', fontSize: 10, fontWeight: '900'},
  errorText: {color: '#8B4E40', fontSize: 9, lineHeight: 14},
  errorClose: {width: 30, height: 30, alignItems: 'center', justifyContent: 'center', borderRadius: 9},
  guideCard: {gap: 11, padding: 13},
  guideHeading: {flexDirection: 'row', alignItems: 'center', gap: 8},
  guideIcon: {width: 34, height: 34, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: '#FFFFFFAA'},
  guideCopy: {flex: 1, gap: 2},
  guideEyebrow: {color: '#806218', fontSize: 7, fontWeight: '900', letterSpacing: 1},
  guideTitle: {color: sketchColors.ink, fontSize: 12, fontWeight: '900'},
  guideIllustration: {position: 'relative', height: 112, overflow: 'hidden', alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: '#FFFDF4'},
  guideSun: {position: 'absolute', top: 13, right: 22, width: 18, height: 18, borderRadius: 10, backgroundColor: '#F0CA68'},
  guidePetalTop: {position: 'absolute', top: 25, width: 26, height: 34, borderRadius: 15, backgroundColor: '#E7A28B'},
  guidePetalLeft: {position: 'absolute', top: 40, left: '39%', width: 27, height: 33, borderRadius: 15, backgroundColor: '#E9BE63', transform: [{rotate: '-42deg'}]},
  guidePetalRight: {position: 'absolute', top: 40, right: '39%', width: 27, height: 33, borderRadius: 15, backgroundColor: '#E9BE63', transform: [{rotate: '42deg'}]},
  guideCenter: {position: 'absolute', top: 43, width: 20, height: 20, borderRadius: 12, backgroundColor: '#F7E6A8'},
  guideStem: {position: 'absolute', bottom: 11, width: 4, height: 34, borderRadius: 3, backgroundColor: '#7CA27B'},
  guideLeaf: {position: 'absolute', bottom: 17, left: '47%', width: 20, height: 12, borderRadius: 14, backgroundColor: '#A7C68F', transform: [{rotate: '-28deg'}]},
  guideSteps: {gap: 7},
  guideStep: {flexDirection: 'row', alignItems: 'center', gap: 8},
  guideStepNumber: {width: 22, height: 22, textAlign: 'center', textAlignVertical: 'center', borderRadius: 8, overflow: 'hidden', backgroundColor: '#FFFFFFB5', color: '#806218', fontSize: 9, fontWeight: '900'},
  guideStepText: {flex: 1, color: sketchColors.inkSoft, fontSize: 10, lineHeight: 15},
  guidePreviewNote: {color: '#806218', fontSize: 8, lineHeight: 13},
  guideActions: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderTopWidth: 1, borderColor: '#E9DCA8', paddingTop: 7},
  guideAction: {minWidth: 76, minHeight: 40, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingHorizontal: 9, borderRadius: 11, backgroundColor: '#FFFFFF9E'},
  guideActionText: {color: sketchColors.greenDark, fontSize: 9, fontWeight: '900'},
  guideActionQuiet: {color: sketchColors.muted, fontSize: 9, fontWeight: '800'},
  restoreGuide: {minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 12, backgroundColor: sketchColors.goldSoft},
  restoreGuideText: {color: '#806218', fontSize: 10, fontWeight: '800'},
  ideaCard: {gap: 13},
  ideaHead: {flexDirection: 'row', alignItems: 'center', gap: 10},
  ideaIcon: {width: 37, height: 37, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: sketchColors.goldSoft},
  ideaCopy: {flex: 1, gap: 3},
  ideaTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  ideaSub: {color: sketchColors.muted, fontSize: 10},
  footnote: {color: sketchColors.muted, fontSize: 10, lineHeight: 15, textAlign: 'center'},
});
