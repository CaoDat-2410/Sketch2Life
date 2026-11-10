import React, {useMemo, useState} from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import WebView from 'react-native-webview';

import type {AuthSessionPort} from '../../infrastructure/auth/AuthSessionPort';
import {ParentWorkflowApi, type ParentCandidate, type ParentAiReceipt} from '../../infrastructure/api/parentWorkflowApi';

type Props = Readonly<{auth: AuthSessionPort}>;

const CANVAS_HTML = `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><style>
*{box-sizing:border-box}body{margin:0;padding:8px;background:#fffaf0;font-family:Arial,sans-serif}.bar{display:flex;justify-content:space-between;gap:8px;margin-bottom:8px}button{border:1px solid #ded7c9;border-radius:10px;background:#fff;padding:9px 12px;font-size:14px;color:#4b453a}canvas{display:block;width:100%;height:258px;border:1px solid #ded7c9;border-radius:14px;background:#fff;touch-action:none}
</style></head><body><div class="bar"><button onclick="clearCanvas()">Xóa nét</button><button onclick="sendDrawing()">Dùng tranh này</button></div><canvas id="paper" width="900" height="640"></canvas><script>
const c=document.getElementById('paper'),x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);x.strokeStyle='#24211c';x.lineWidth=8;x.lineCap='round';x.lineJoin='round';let drawing=false;
function point(e){const r=c.getBoundingClientRect();return{x:(e.clientX-r.left)*c.width/r.width,y:(e.clientY-r.top)*c.height/r.height}}
c.addEventListener('pointerdown',e=>{drawing=true;c.setPointerCapture(e.pointerId);const p=point(e);x.beginPath();x.moveTo(p.x,p.y)});c.addEventListener('pointermove',e=>{if(!drawing)return;const p=point(e);x.lineTo(p.x,p.y);x.stroke()});c.addEventListener('pointerup',()=>drawing=false);c.addEventListener('pointercancel',()=>drawing=false);
function clearCanvas(){x.clearRect(0,0,c.width,c.height);x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height)}function sendDrawing(){window.ReactNativeWebView.postMessage(c.toDataURL('image/png'))}
</script></body></html>`;

export function ParentWorkflowScreen({auth}: Props): React.JSX.Element {
  const api = useMemo(() => new ParentWorkflowApi(auth), [auth]);
  const [topic, setTopic] = useState('');
  const [ageMonths, setAgeMonths] = useState('');
  const [guideEnabled, setGuideEnabled] = useState(false);
  const [guide, setGuide] = useState<string | null>(null);
  const [drawingDataUri, setDrawingDataUri] = useState<string | null>(null);
  const [candidate, setCandidate] = useState<ParentCandidate | null>(null);
  const [drawingSha256, setDrawingSha256] = useState('');
  const [confirmedSubject, setConfirmedSubject] = useState('');
  const [story, setStory] = useState<Record<string, unknown> | null>(null);
  const [storyConfirmed, setStoryConfirmed] = useState(false);
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [lastRequestId, setLastRequestId] = useState('');

  const visibleFeatures = candidate?.visible_features ?? [];
  const imageBase64 = drawingDataUri?.split(',')[1] ?? '';

  async function createGuide() {
    setError('');
    setNotice('');
    if (!topic.trim()) {
      setError('Nhập chủ đề trước khi tạo gợi ý vẽ.');
      return;
    }
    setBusy('guide');
    try {
      const response = await api.generateSketchGuide({
        topic: topic.trim(),
        difficulty: 'beginner',
        step_count: 3,
      });
      setGuide(response.image_base64 ?? null);
      setLastRequestId(response.request_id);
      setNotice('Gợi ý line sketch đã tạo thành bản nháp. Người lớn hướng dẫn nếu thấy phù hợp.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể tạo gợi ý vẽ.');
    } finally {
      setBusy('');
    }
  }

  async function analyzeDrawing() {
    setError('');
    setNotice('');
    const age = Number(ageMonths);
    if (!imageBase64 || !Number.isInteger(age) || age < 36 || age > 120) {
      setError('Vẽ và gửi tranh, đồng thời nhập tuổi từ 36–120 tháng.');
      return;
    }
    setBusy('drawing');
    try {
      const response = await api.analyzeDrawing(imageBase64);
      if (!response.candidate || response.candidate.adult_confirmation_required !== true) {
        throw new Error('Backend không trả về đề xuất cần người lớn xác nhận.');
      }
      setCandidate(response.candidate);
      setDrawingSha256(response.drawing_sha256 ?? '');
      setConfirmedSubject(response.candidate.candidate_subject ?? '');
      setLastRequestId(response.request_id);
      setNotice('Qwen đã phân tích tranh. Hãy tự xác nhận hoặc sửa chủ thể trước khi tiếp tục.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể phân tích tranh.');
    } finally {
      setBusy('');
    }
  }

  async function generateStory() {
    setError('');
    setNotice('');
    const age = Number(ageMonths);
    if (!candidate || !confirmedSubject.trim() || !candidate.visible_features?.length || !/^[0-9a-f]{64}$/.test(drawingSha256)) {
      setError('Xác nhận chủ thể và các đặc điểm nhìn thấy trước.');
      return;
    }
    setBusy('story');
    try {
      const response: ParentAiReceipt<Record<string, unknown>> = await api.generateStory({
        confirmed_subject: confirmedSubject.trim(),
        visible_features: candidate.visible_features,
        child_age_months: age,
        drawing_sha256: drawingSha256,
        understanding_revision: 1,
        context_revision: 1,
        adult_confirmed_idea: '',
      });
      if (!response.story || !response.review_required) {
        throw new Error('Backend không trả về kịch bản chờ người lớn duyệt.');
      }
      setStory(response.story);
      setStoryConfirmed(false);
      setLastRequestId(response.request_id);
      setNotice('Qwen đã tạo kịch bản. Đọc lại rồi xác nhận để kết thúc luồng trước video.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể tạo kịch bản.');
    } finally {
      setBusy('');
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.eyebrow}>SKETCH2LIFE · PHỤ HUYNH</Text>
            <Text style={styles.title}>Từ nét vẽ đến câu chuyện</Text>
            <Text style={styles.subtitle}>Người lớn đồng hành, xác nhận chủ thể và duyệt kịch bản.</Text>
          </View>
          <View style={styles.statusPill}><Text style={styles.statusText}>Modal AI</Text></View>
        </View>

        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        {notice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text> : null}

        <View style={styles.card}>
          <Text style={styles.step}>1 · CHUẨN BỊ VẼ</Text>
          <Text style={styles.label}>Chủ đề</Text>
          <TextInput accessibilityLabel="Chủ đề" value={topic} onChangeText={setTopic} placeholder="Ví dụ: con bướm" style={styles.input} />
          <Text style={[styles.label, styles.labelSpaced]}>Tuổi trẻ (tháng)</Text>
          <TextInput accessibilityLabel="Tuổi trẻ theo tháng" value={ageMonths} onChangeText={setAgeMonths} keyboardType="number-pad" placeholder="36–120" style={styles.input} />
          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}>
              <Text style={styles.label}>Gợi ý line sketch</Text>
              <Text style={styles.helper}>Tùy chọn. Chỉ gửi chủ đề và độ khó để tạo gợi ý chung.</Text>
            </View>
            <Switch accessibilityLabel="Bật gợi ý line sketch" value={guideEnabled} onValueChange={(value) => { setGuideEnabled(value); if (!value) setGuide(null); }} trackColor={{false: '#d5d0c7', true: '#85b5a0'}} thumbColor={guideEnabled ? '#2f7259' : '#fff'} />
          </View>
          {guideEnabled ? <ActionButton testID="parent-guide-button" disabled={busy !== ''} label={busy === 'guide' ? 'Đang tạo gợi ý…' : 'Tạo gợi ý line sketch'} onPress={() => void createGuide()} /> : null}
          {guide ? <Image accessibilityLabel="Gợi ý line sketch do AI tạo" source={{uri: `data:image/png;base64,${guide}`}} style={styles.guideImage} resizeMode="contain" /> : null}
          <Text style={[styles.step, styles.drawLabel]}>VẼ TRÊN KHUNG GIẤY</Text>
          <View style={styles.canvasShell}>
            <WebView
              accessibilityLabel="Khung vẽ tranh"
              originWhitelist={['*']}
              source={{html: CANVAS_HTML}}
              javaScriptEnabled
              onMessage={(event) => {
                const value = event.nativeEvent.data;
                if (value.startsWith('data:image/png;base64,')) {
                  setDrawingDataUri(value);
                  setCandidate(null);
                  setDrawingSha256('');
                  setStory(null);
                  setStoryConfirmed(false);
                  setNotice('Đã nhận tranh từ khung vẽ.');
                }
              }}
              style={styles.webview}
            />
          </View>
          {drawingDataUri ? <Image accessibilityLabel="Tranh vừa vẽ" source={{uri: drawingDataUri}} style={styles.drawingPreview} resizeMode="contain" /> : null}
          <ActionButton testID="parent-analyze-button" disabled={busy !== '' || !drawingDataUri} label={busy === 'drawing' ? 'Qwen đang xem tranh…' : 'Chụp tranh và nhận diện'} onPress={() => void analyzeDrawing()} />
        </View>

        {candidate ? (
          <View style={styles.card}>
            <Text style={styles.step}>2 · NGƯỜI LỚN XÁC NHẬN</Text>
            <Text style={styles.helper}>Đề xuất AI không thay thế lựa chọn của trẻ. Bạn có thể đổi chủ thể.</Text>
            <Text style={[styles.label, styles.labelSpaced]}>Chủ thể đã xác nhận</Text>
            <TextInput accessibilityLabel="Xác nhận chủ thể" value={confirmedSubject} onChangeText={setConfirmedSubject} style={styles.input} />
            <Text style={[styles.label, styles.labelSpaced]}>Đặc điểm nhìn thấy</Text>
            {visibleFeatures.map((feature, index) => <Text key={`${index}-${feature}`} style={styles.feature}>• {feature}</Text>)}
            <Text style={styles.helper}>Qwen {candidate.confidence === undefined ? '' : `· độ tin cậy ${Math.round(candidate.confidence * 100)}%`} · cần người lớn xác nhận</Text>
            <ActionButton testID="parent-story-button" disabled={busy !== ''} label={busy === 'story' ? 'Qwen đang tạo kịch bản…' : 'Xác nhận chủ thể và tạo kịch bản'} onPress={() => void generateStory()} />
          </View>
        ) : null}

        {story ? (
          <View style={styles.card}>
            <Text style={styles.step}>3 · DUYỆT KỊCH BẢN</Text>
            <Text style={styles.storyTitle}>{String(story.title ?? 'Kịch bản gợi ý')}</Text>
            <Text style={styles.storyBody}>{JSON.stringify(story, null, 2)}</Text>
            {!storyConfirmed ? <ActionButton testID="parent-confirm-story-button" disabled={busy !== ''} label="Tôi xác nhận kịch bản này" onPress={() => setStoryConfirmed(true)} /> : <Text style={styles.confirmed}>Đã xác nhận kịch bản. Luồng dừng trước bước video.</Text>}
          </View>
        ) : null}

        {busy ? <View style={styles.busyRow}><ActivityIndicator color="#2f7259" /><Text style={styles.busyText}>{busy === 'guide' ? 'Đang tạo gợi ý…' : busy === 'drawing' ? 'Đang phân tích tranh…' : 'Đang viết kịch bản…'}</Text></View> : null}
        {lastRequestId ? <Text style={styles.footer}>Mã yêu cầu gần nhất: {lastRequestId}</Text> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

function ActionButton({testID, disabled, label, onPress}: Readonly<{testID: string; disabled: boolean; label: string; onPress: () => void}>): React.JSX.Element {
  return <Pressable testID={testID} accessibilityRole="button" disabled={disabled} onPress={onPress} style={[styles.button, disabled && styles.buttonDisabled]}><Text style={styles.buttonText}>{label}</Text></Pressable>;
}

const styles = StyleSheet.create({
  safeArea: {flex: 1, backgroundColor: '#f7f3eb'},
  container: {padding: 18, paddingBottom: 44, gap: 14},
  header: {flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 3},
  headerText: {flex: 1},
  eyebrow: {color: '#826b4d', fontSize: 10, letterSpacing: 1.4, fontWeight: '700'},
  title: {color: '#2c372f', fontSize: 23, fontWeight: '800', marginTop: 5},
  subtitle: {color: '#756f65', fontSize: 12, marginTop: 5, lineHeight: 17},
  statusPill: {backgroundColor: '#e4efe7', borderRadius: 14, paddingHorizontal: 10, paddingVertical: 6},
  statusText: {color: '#2f7259', fontSize: 11, fontWeight: '800'},
  card: {backgroundColor: '#fffdf9', borderColor: '#e5ddcf', borderWidth: 1, borderRadius: 18, padding: 15, gap: 9},
  step: {color: '#94744a', fontSize: 10, letterSpacing: 1.1, fontWeight: '800'},
  label: {color: '#3f4038', fontSize: 13, fontWeight: '700'},
  labelSpaced: {marginTop: 3},
  input: {backgroundColor: '#fff', borderColor: '#ddd5c9', borderWidth: 1, borderRadius: 11, minHeight: 42, paddingHorizontal: 12, color: '#2c302b'},
  toggleRow: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12, borderTopColor: '#eee7dc', borderTopWidth: 1, paddingTop: 10, marginTop: 3},
  toggleCopy: {flex: 1, gap: 3},
  helper: {color: '#777267', fontSize: 11, lineHeight: 16},
  guideImage: {width: '100%', height: 180, backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#eee7dc'},
  drawLabel: {marginTop: 6},
  canvasShell: {height: 300, overflow: 'hidden', borderRadius: 14, borderWidth: 1, borderColor: '#ded7c9'},
  webview: {flex: 1, backgroundColor: '#fffaf0'},
  drawingPreview: {width: '100%', height: 170, backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#eee7dc'},
  button: {backgroundColor: '#2f7259', borderRadius: 12, minHeight: 44, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 12, marginTop: 4},
  buttonDisabled: {opacity: 0.45},
  buttonText: {color: '#fff', fontSize: 13, fontWeight: '800', textAlign: 'center'},
  error: {backgroundColor: '#fff0eb', borderColor: '#edb8a7', borderWidth: 1, color: '#9c3e2b', borderRadius: 12, padding: 10, fontSize: 12},
  notice: {backgroundColor: '#e8f3eb', borderColor: '#c8dfcf', borderWidth: 1, color: '#335d43', borderRadius: 12, padding: 10, fontSize: 12},
  feature: {color: '#4f5149', fontSize: 12, lineHeight: 18},
  storyTitle: {color: '#2b3d32', fontSize: 18, fontWeight: '800'},
  storyBody: {color: '#4e5048', backgroundColor: '#f7f4ed', padding: 10, borderRadius: 10, fontSize: 10, lineHeight: 15},
  confirmed: {color: '#2f7259', fontSize: 13, fontWeight: '800', paddingVertical: 8},
  busyRow: {flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 9, paddingVertical: 8},
  busyText: {color: '#5f685f', fontSize: 12},
  footer: {color: '#938c7e', textAlign: 'center', fontSize: 9},
});
