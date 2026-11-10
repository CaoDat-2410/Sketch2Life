import {useEffect, useState} from 'react';
import {Alert, KeyboardAvoidingView, Modal, Platform, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions} from 'react-native';
import type {StyleProp, ViewStyle} from 'react-native';
import type {ChildGender, ParentRun, ParentScreen, ParentWorkflowCommand, ParentWorkflowPort} from './parentWorkflowPort';

type Props = Readonly<{workflow: ParentWorkflowPort; onOpenFixtureLab: () => void}>;
type ButtonProps = Readonly<{label: string; onPress: () => void; kind?: 'primary' | 'secondary' | 'quiet' | 'danger'; disabled?: boolean}>;

export function ParentFlowScreen({workflow, onOpenFixtureLab}: Props): React.JSX.Element {
  const {width} = useWindowDimensions();
  const tablet = width >= 760;
  const [state, setState] = useState(workflow.getSnapshot());
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [profileLabel, setProfileLabel] = useState('');
  const [ageMonths, setAgeMonths] = useState('60');
  const [gender, setGender] = useState<ChildGender>('female');
  const [idea, setIdea] = useState('');
  const [voice, setVoice] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [subject, setSubject] = useState('');
  const [notice, setNotice] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [preflightOpen, setPreflightOpen] = useState(false);
  const [admissionPending, setAdmissionPending] = useState(false);
  const [settingsPanel, setSettingsPanel] = useState<'account' | 'security' | null>(null);
  const [accountNameDraft, setAccountNameDraft] = useState('');
  const [accountEmailDraft, setAccountEmailDraft] = useState('');
  const [accountEditError, setAccountEditError] = useState<string | null>(null);
  const [securityNotice, setSecurityNotice] = useState<string | null>(null);
  const [selectedPack, setSelectedPack] = useState<3 | 5 | 10>(5);
  const [paymentMethod, setPaymentMethod] = useState<'MoMo' | 'VNPAY'>('MoMo');

  useEffect(() => {
    setState(workflow.getSnapshot());
    return workflow.subscribe(() => setState(workflow.getSnapshot()));
  }, [workflow]);

  const run = state.runs.find((item) => item.id === state.selectedRunId) ?? null;
  const activeRun = state.runs.find((item) => item.id === state.activeRunId && item.status === 'active') ?? null;
  const profile = state.profiles.find((item) => item.id === state.selectedProfileId) ?? null;
  const activeRunProfile = activeRun ? state.profiles.find((item) => item.id === activeRun.childProfileId) ?? null : null;
  const runProfile = run ? state.profiles.find((item) => item.id === run.childProfileId) ?? null : profile;
  const parentName = state.parentDisplayName ?? 'Phụ huynh demo';
  const parentInitials = parentName.split(/\s+/).filter(Boolean).slice(-2).map((part) => part[0]).join('').toLocaleUpperCase('vi-VN');
  useEffect(() => {
    if (run) {
      setIdea(run.ideaText);
      setVoice(run.hasVoiceIdea);
      setTranscript(run.transcript);
      setSubject(run.subject);
    }
  }, [run?.id, run?.ideaText, run?.hasVoiceIdea, run?.transcript, run?.subject]);

  const send = (command: ParentWorkflowCommand): void => {
    setFailure(null);
    void workflow.dispatch(command).catch(() => setFailure('Demo chưa xử lý được thao tác này. Hãy thử lại.'));
  };
  const go = (screen: ParentScreen): void => { setNotice(null); send({type: 'NAVIGATE', screen}); };
  const openSettingsPanel = (panel: 'account' | 'security'): void => {
    setAccountEditError(null);
    setSecurityNotice(null);
    if (panel === 'account') {
      setAccountNameDraft(state.parentDisplayName ?? 'Phụ huynh demo');
      setAccountEmailDraft(state.parentEmail ?? '');
    }
    setSettingsPanel(panel);
  };
  const saveParentAccount = async (): Promise<void> => {
    const displayName = accountNameDraft.trim();
    const email = accountEmailDraft.trim();
    if (!displayName || !email) {
      setAccountEditError('Nhập tên và email để cập nhật hồ sơ demo.');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setAccountEditError('Email chưa đúng định dạng.');
      return;
    }
    setAccountEditError(null);
    try {
      await workflow.dispatch({type: 'UPDATE_PARENT_ACCOUNT', displayName, email});
      const next = workflow.getSnapshot();
      if (next.parentDisplayName === displayName && next.parentEmail === email) {
        setSettingsPanel(null);
        setNotice('Đã cập nhật thông tin trong phiên demo này.');
      } else {
        setAccountEditError(next.message ?? 'Chưa lưu được thông tin demo.');
      }
    } catch {
      setAccountEditError('Chưa lưu được thông tin demo. Hãy thử lại.');
    }
  };
  const admitVideo = async (): Promise<void> => {
    if (admissionPending) return;
    setAdmissionPending(true);
    setFailure(null);
    try {
      await workflow.dispatch({type: 'APPROVE_AND_REQUEST_VIDEO'});
      const next = workflow.getSnapshot();
      const nextRun = next.runs.find((item) => item.id === next.selectedRunId);
      if (next.screen === 'video-status' && nextRun?.videoRequested) setPreflightOpen(false);
    } catch {
      setFailure('Chưa gửi được yêu cầu demo. Hãy thử lại.');
    } finally {
      setAdmissionPending(false);
    }
  };
  const capture = (source: 'camera-demo' | 'gallery-demo'): void => {
    send({type: 'SAVE_IDEA', text: idea, hasVoiceIdea: voice && !state.microphoneDenied});
    send({type: 'CAPTURE_DRAWING', source});
  };
  const deleteRun = (runId: string): void => Alert.alert('Xóa run demo?', 'Run sẽ bị xóa khỏi lịch sử demo trên thiết bị này.', [
    {text: 'Giữ lại', style: 'cancel'},
    {text: 'Xóa run', style: 'destructive', onPress: () => send({type: 'DELETE_RUN', runId})},
  ]);

  const content = (() => {
    switch (state.screen) {
      case 'sign-in':
      case 'register':
      case 'recover': {
        const mode = state.screen;
        const title = mode === 'sign-in' ? 'Chào mừng trở lại' : mode === 'register' ? 'Tạo tài khoản demo' : 'Khôi phục mật khẩu';
        return <Row tablet={tablet}>
          <View style={styles.authIntro}>
            <Text style={styles.kicker}>CÙNG TRẺ KỂ CHUYỆN</Text>
            <Text style={styles.hero}>Từ nét vẽ nhỏ đến câu chuyện của riêng mình.</Text>
            <Text style={styles.body}>Các bước sau dùng dữ liệu tổng hợp để bạn xem trọn luồng Parent.</Text>
          </View>
          <Panel style={styles.authPanel}>
            <Text style={styles.title}>{title}</Text>
            {mode === 'register' && <Field label="Tên hiển thị" value={displayName} onChangeText={setDisplayName} placeholder="Tên phụ huynh demo" />}
            <Field label="Email" value={email} onChangeText={setEmail} placeholder="name@example.com" keyboardType="email-address" />
            {mode !== 'recover' && <Field label="Mật khẩu" value={password} onChangeText={setPassword} placeholder="Nhập mật khẩu" secureTextEntry />}
            <Button label={mode === 'sign-in' ? 'Đăng nhập demo' : mode === 'register' ? 'Tạo tài khoản demo' : 'Gửi yêu cầu demo'} onPress={() => send(mode === 'sign-in' ? {type: 'SIGN_IN', email} : mode === 'register' ? {type: 'REGISTER_DEMO', email, displayName} : {type: 'RECOVER_PASSWORD_DEMO', email})} />
            <View style={styles.linkRow}>
              {mode === 'sign-in' && <Link label="Quên mật khẩu?" onPress={() => go('recover')} />}
              {mode === 'sign-in' && <Link label="Tạo tài khoản" onPress={() => go('register')} />}
              {mode !== 'sign-in' && <Link label="Về đăng nhập" onPress={() => go('sign-in')} />}
            </View>
            <Text style={styles.helper}>Dữ liệu chỉ minh họa luồng demo; không gửi email, xác thực mật khẩu hoặc tạo tài khoản thật.</Text>
          </Panel>
        </Row>;
      }
      case 'profiles':
        return <Page kicker="HỒ SƠ CỦA BÉ" title="Ai sẽ kể chuyện hôm nay?" description="Chạm một lần để chọn hồ sơ cho câu chuyện tiếp theo.">
          <Row tablet={tablet}>
            {state.profiles.map((item) => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Chọn ${item.label}, ${item.ageMonths} tháng, ${item.gender === 'male' ? 'bé trai' : 'bé gái'}`} accessibilityState={{selected: item.id === state.selectedProfileId}} onPress={() => send({type: 'SELECT_PROFILE', profileId: item.id})} style={({pressed}) => [styles.profileCard, item.id === state.selectedProfileId && styles.profileCardSelected, pressed && styles.buttonPressed]}>
              <ChildAvatar gender={item.gender} size={62} />
              <Text style={styles.subtitle}>{item.label}</Text>
              <Text style={styles.muted}>{Math.floor(item.ageMonths / 12)} tuổi · hồ sơ demo</Text>
              {item.id === state.selectedProfileId && <View style={styles.selectedPill}><Text style={styles.selectedPillText}>ĐANG CHỌN</Text></View>}
            </Pressable>)}
            <Pressable accessibilityRole="button" accessibilityLabel="Thêm hồ sơ bé" onPress={() => go('profile-create')} style={[styles.profileCard, styles.addProfileCard]}>
              <Text style={styles.addProfileGlyph}>＋</Text><Text style={styles.subtitle}>Thêm hồ sơ</Text><Text style={styles.muted}>Tạo hồ sơ demo mới</Text>
            </Pressable>
          </Row>
          {activeRun && <Notice tone="info">Câu chuyện đang làm thuộc hồ sơ {activeRunProfile?.label ?? 'đã chọn trước đó'}. Bạn có thể tiếp tục, không thể tạo run thứ hai khi run này chưa hoàn tất.</Notice>}
        </Page>;
      case 'profile-create':
        return <Page kicker="HỒ SƠ DEMO" title="Tạo hồ sơ trẻ" description="Tuổi demo trong khoảng 36–120 tháng; chưa lưu lên server.">
          <Panel style={styles.formPanel}>
            <View style={styles.profilePreview}><ChildAvatar gender={gender} size={70} /><Text style={styles.subtitle}>{gender === 'male' ? 'Bé trai' : 'Bé gái'}</Text><Text style={styles.muted}>Avatar đổi theo giới tính đã chọn</Text></View>
            <Field label="Tên hiển thị trong demo" value={profileLabel} onChangeText={setProfileLabel} placeholder="Hồ sơ demo mới" />
            <Field label="Tuổi (tháng)" value={ageMonths} onChangeText={setAgeMonths} keyboardType="numeric" placeholder="36–120" />
            <Text style={styles.fieldLabel}>Giới tính</Text>
            <View style={styles.genderChoices}>
              {(['male', 'female'] as const).map((choice) => <Pressable key={choice} accessibilityRole="radio" accessibilityState={{checked: gender === choice}} onPress={() => setGender(choice)} style={[styles.genderChoice, gender === choice && styles.genderChoiceSelected]}>
                <ChildAvatar gender={choice} size={38} /><Text style={styles.genderChoiceLabel}>{choice === 'male' ? 'Bé trai' : 'Bé gái'}</Text>
              </Pressable>)}
            </View>
            <Button label="Lưu hồ sơ demo" onPress={() => send({type: 'CREATE_PROFILE', label: profileLabel, ageMonths: Number(ageMonths), gender})} />
          </Panel>
        </Page>;
      case 'home': {
        const completeCount = state.runs.filter((item) => item.status === 'completed').length;
        return <Page kicker="KHÔNG GIAN PARENT" title="Tiếp tục câu chuyện" description="Bắt đầu run mới hoặc tiếp tục nơi bạn đã dừng.">
          <Row tablet={tablet}>
            <Panel style={styles.flexPanel}>
              <Text style={styles.kicker}>HỒ SƠ ĐANG CHỌN</Text>
              <View style={styles.currentProfile}><ChildAvatar gender={profile?.gender ?? 'female'} size={58} /><View style={styles.currentProfileCopy}><Text style={styles.title}>{profile?.label ?? 'Chưa chọn hồ sơ'}</Text><Text style={styles.body}>{profile ? `${Math.floor(profile.ageMonths / 12)} tuổi · hồ sơ demo` : 'Chọn hồ sơ trước khi bắt đầu.'}</Text></View><Pressable accessibilityRole="button" accessibilityLabel="Đổi hồ sơ bé" onPress={() => go('profiles')} style={styles.profileSwitch}><Text style={styles.profileSwitchText}>Đổi</Text></Pressable></View>
              {activeRun ? <><Notice>Câu chuyện đang làm của {activeRunProfile?.label ?? 'bé'} vẫn được giữ nguyên.</Notice><Button label={`Tiếp tục câu chuyện của ${activeRunProfile?.label ?? 'bé'}`} onPress={() => send({type: 'CONTINUE_RUN'})} /></> : <Button label="Bắt đầu câu chuyện mới" onPress={() => send({type: 'START_RUN'})} disabled={!profile} />}
            </Panel>
            <Panel style={styles.flexPanel}>
              <Text style={styles.kicker}>TÓM TẮT DEMO</Text>
              <Metric label="Run trong lịch sử" value={String(state.runs.length)} />
              <Metric label="Đã hoàn tất" value={String(completeCount)} />
              <Metric label="Lượt còn lại" value={String(state.quotaRemaining)} />
              <Text style={styles.helper}>Số liệu nằm trong adapter demo.</Text>
            </Panel>
          </Row>
          <Row tablet={tablet}>
            <Tile title="Lịch sử" detail="Mở các run demo" onPress={() => go('history')} />
            <Tile title="Quota" detail="Xem lượt demo còn lại" onPress={() => go('quota')} />
            <Tile title="Cài đặt" detail="Hồ sơ và phiên demo" onPress={() => go('settings')} />
            <Tile title="Thông báo" detail="Run reminder demo" onPress={() => go('notifications')} />
          </Row>
        </Page>;
      }
      case 'drawing':
        return <Page kicker="BƯỚC 1 · TRANH VÀ Ý TƯỞNG" title="Bắt đầu từ bức tranh" description="Chọn đúng một tranh. Chủ thể sẽ được rà soát sau capture.">
          <Row tablet={tablet}>
            <Panel style={styles.flexPanel}>
              <Text style={styles.subtitle}>Line-sketch guide tùy chọn</Text>
              <Text style={styles.body}>Guide mẫu chỉ nhận chủ đề chung; bỏ qua vẫn tiếp tục capture được.</Text>
              <Text style={styles.helper}>{state.guideRequested ? 'Guide demo đang bật.' : 'Guide demo đang tắt.'}</Text>
              <Button label={state.guideRequested ? 'Bỏ qua guide' : 'Thử guide demo'} kind="secondary" onPress={() => send({type: 'TOGGLE_GUIDE', enabled: !state.guideRequested})} />
              {state.guideRequested && <Text style={styles.helper}>{state.workflowContent.guideSteps.map((step, index) => `${index + 1}. ${step}`).join(' · ')}</Text>}
            </Panel>
            <Panel style={styles.flexPanel}>
              <Text style={styles.subtitle}>Ý tưởng của người lớn</Text>
              <Field label="Ý tưởng bằng chữ" value={idea} onChangeText={setIdea} placeholder="Điều trẻ muốn khám phá" multiline />
              <Pressable accessibilityRole="checkbox" accessibilityState={{checked: voice, disabled: state.microphoneDenied}} disabled={state.microphoneDenied} onPress={() => setVoice((value) => !value)} style={styles.checkRow}>
                <View style={[styles.checkbox, voice && styles.checkboxOn]} /><Text style={styles.body}>{voice ? 'Đã thêm ghi âm demo' : 'Thử thêm ghi âm demo · tối đa 2 phút'}</Text>
              </Pressable>
              <Text style={styles.helper}>{state.microphoneDenied ? 'Microphone bị từ chối trong demo; có thể tiếp tục bằng chữ.' : 'Không ghi âm thật; nội dung chỉ nằm trong adapter demo.'}</Text>
            </Panel>
          </Row>
          <Panel>
            <Text style={styles.subtitle}>Quyền thiết bị · demo</Text>
            <Row tablet={tablet}>
              <Button label={state.cameraDenied ? 'Bật camera demo' : 'Mô phỏng từ chối camera'} kind="secondary" onPress={() => send({type: 'SIMULATE_CAMERA_DENIAL', denied: !state.cameraDenied})} />
              <Button label={state.microphoneDenied ? 'Bật microphone demo' : 'Mô phỏng từ chối microphone'} kind="secondary" onPress={() => { if (!state.microphoneDenied) setVoice(false); send({type: 'SIMULATE_MICROPHONE_DENIAL', denied: !state.microphoneDenied}); }} />
            </Row>
            <Notice>{state.cameraDenied ? 'Camera bị từ chối; chọn ảnh thư viện vẫn dùng được.' : 'Quyền camera demo đang sẵn sàng.'}</Notice>
          </Panel>
          <Panel>
            <Text style={styles.subtitle}>Chọn nguồn tranh</Text><DrawingPlaceholder />
            <Row tablet={tablet}>
              <Button label="Chụp tranh · demo" onPress={() => capture('camera-demo')} disabled={state.cameraDenied} />
              <Button label="Chọn thư viện · demo" kind="secondary" onPress={() => capture('gallery-demo')} />
            </Row>
            <Text style={styles.helper}>Camera, thư viện và upload thật sẽ được nối qua adapter riêng khi được duyệt.</Text>
          </Panel>
        </Page>;
      case 'upload':
        return <Page kicker="BƯỚC 1 · TẢI TRANH DEMO" title="Upload tranh" description="Xem trạng thái gửi và thử tiếp tục một session bị gián đoạn.">
          <Panel style={styles.formPanel}>
            <Metric label="Nguồn tranh" value={run?.drawingSource === 'camera-demo' ? 'Camera demo' : 'Thư viện demo'} />
            <Metric label="Session upload" value={run?.uploadInterrupted ? 'Bị gián đoạn' : run?.uploadResumeCount ? `Đã tiếp tục ${run.uploadResumeCount} lần` : 'Đang chờ hoàn tất demo'} />
            {run?.uploadInterrupted && <Notice tone="error">Mạng demo bị ngắt. Session giữ nguyên để có thể tiếp tục.</Notice>}
            {!run?.uploadInterrupted && <Notice>Không truyền bytes hoặc gọi API. Tiến độ không được giả lập bằng phần trăm.</Notice>}
            <Button label="Mô phỏng mất kết nối" kind="secondary" onPress={() => send({type: 'SIMULATE_UPLOAD_INTERRUPTION'})} disabled={Boolean(run?.uploadInterrupted) || run?.stage !== 'upload'} />
            {run?.uploadInterrupted && <Button label="Tiếp tục upload demo" onPress={() => send({type: 'RESUME_UPLOAD'})} />}
            {run?.stage === 'upload' ? <Button label="Hoàn tất upload demo" onPress={() => send({type: 'COMPLETE_UPLOAD'})} disabled={Boolean(run?.uploadInterrupted)} /> : <Button label="Tiếp tục rà soát transcript" kind="secondary" onPress={() => send({type: 'CONTINUE_RUN'})} />}
          </Panel>
        </Page>;
      case 'transcript-review':
        return <Page kicker="BƯỚC 2 · RÀ SOÁT Ý TƯỞNG" title="Nghe lại và xác nhận" description="Người lớn có thể sửa transcript trước khi rà soát chủ thể.">
          <Panel style={styles.formPanel}>
            <Notice>Transcript mẫu; sửa nội dung rồi xác nhận để đi tiếp.</Notice>
            <Field label="Transcript" value={transcript} onChangeText={setTranscript} multiline placeholder="Ý tưởng của người lớn" />
            <Button label="Xác nhận transcript" onPress={() => send({type: 'CONFIRM_TRANSCRIPT', transcript})} disabled={!transcript.trim()} />
          </Panel>
        </Page>;
      case 'subject-review':
        return <Page kicker="BƯỚC 3 · RÀ SOÁT CHỦ THỂ" title="Bức tranh có những gì?" description="Đề xuất demo cần người lớn xác nhận; chỉnh sửa tạo revision mới.">
          <Row tablet={tablet}>
            <Panel style={styles.flexPanel}><DrawingPlaceholder /><Text style={styles.helper}>Tranh tổng hợp chỉ minh họa cho demo.</Text></Panel>
            <Panel style={styles.flexPanel}>
              <Notice>Đây không phải kết quả VLM thật; hãy rà soát như người lớn.</Notice>
              <Field label="Chủ thể đề xuất demo" value={subject} onChangeText={setSubject} placeholder="Mô tả chủ thể" />
              <Button label="Xác nhận chủ thể" onPress={() => send({type: 'CONFIRM_SUBJECT', subject})} disabled={!subject.trim()} />
            </Panel>
          </Row>
        </Page>;
      case 'context-review':
        return <Page kicker="BƯỚC 4 · RÀ SOÁT CONTEXT" title="Xác nhận thông tin sẽ dùng" description="Rà soát context tối thiểu trước khi tạo story demo.">
          <Panel style={styles.formPanel}>
            <Metric label="Hồ sơ" value={runProfile?.label ?? 'Hồ sơ demo'} />
            <Metric label="Độ tuổi" value={`${runProfile?.ageMonths ?? 60} tháng`} />
            <Metric label="Chủ thể đã xác nhận" value={run?.subject ?? 'Chưa xác nhận'} />
            <Metric label="Lesson đã pin" value={state.workflowContent.pinnedContext.lessonLabel} />
            <Metric label="Hướng truyện" value={state.workflowContent.pinnedContext.storyDirection} />
            <Notice>Tên hiển thị không nằm trong context demo. Đây chưa phải snapshot API.</Notice>
            <Button label="Xác nhận context và tạo story demo" onPress={() => send({type: 'CONFIRM_CONTEXT'})} />
          </Panel>
        </Page>;
      case 'story-review':
        return <Page kicker="BƯỚC 5 · DUYỆT KỊCH BẢN" title={run?.storyTitle ?? 'Rà soát kịch bản'} description="Đọc từng cảnh cùng bé. Mỗi bản viết lại cần được người lớn xem và duyệt lại.">
          <View style={[styles.sceneGrid, tablet && styles.sceneGridTablet]}>
            {(run?.storyScenes ?? []).map((scene, index) => <Panel key={scene.id} style={styles.sceneCard}>
              <View style={styles.storySceneHeading}><View style={styles.sceneNumber}><Text style={styles.sceneNumberText}>{index + 1}</Text></View><View style={styles.storySceneCopy}><Text style={styles.kicker}>CẢNH {index + 1} · DEMO</Text><Text style={styles.subtitle}>{scene.title}</Text></View></View><Text style={styles.body}>{scene.narration}</Text><Text style={styles.sceneDuration}>Thời lượng cảnh: 12 giây</Text>
            </Panel>)}
          </View>
          <Panel>
            <View style={styles.panelHeading}><Text style={styles.subtitle}>Nhờ AI viết lại kịch bản</Text><Text style={styles.muted}>Còn {Math.max(0, 3 - (run?.rewriteCount ?? 0))}/3 lượt</Text></View>
            <Metric label="Bản kịch bản hiện tại" value={`#${run?.storyRevision ?? 1}`} />
            {run?.replacementRequested && <Notice>Đang chuẩn bị yêu cầu video thay thế.</Notice>}
            {run?.videoRequested && !run.replacementRequested ? <><Notice tone="success">Yêu cầu tạo video đã được nhận cho bản #{run.storyRevision}. Không cần duyệt hoặc trừ lượt lần nữa.</Notice><Button label="Tiếp tục theo dõi video" onPress={() => send({type: 'CONTINUE_RUN'})} /></> : <>
              <Button label="Viết lại bằng AI · demo" kind="secondary" onPress={() => send({type: 'REWRITE_STORY'})} disabled={!run || run.rewriteCount >= 3} />
              <Button label="Duyệt kịch bản & Tạo video" onPress={() => setPreflightOpen(true)} disabled={!run} />
            </>}
          </Panel>
        </Page>;
      case 'video-status':
        return <Page kicker="BƯỚC 6 · TRẠNG THÁI VIDEO" title={run?.videoReady ? 'Video đã sẵn sàng!' : 'Đang làm video của bé'} description="Màn hình này mô phỏng trạng thái xử lý trong app; không có video thật được tạo.">
          <Panel style={styles.formPanel}>
            <Text style={styles.kicker}>{run?.videoReady ? 'ĐÃ SẴN SÀNG · DEMO' : run?.videoError ? 'CẦN THỬ LẠI · DEMO' : 'ĐANG XỬ LÝ · DEMO'}</Text>
            <View style={styles.videoPlaceholder}>
              <Text style={styles.playGlyph}>{run?.videoReady ? '✓' : '✦'}</Text>
              <Text style={styles.subtitle}>{run?.videoReady ? 'Video demo sẵn sàng' : run?.videoError ? 'Video demo đang tạm dừng' : 'Đang chuẩn bị câu chuyện…'}</Text>
              <Text style={styles.videoStatusCopy}>{run?.videoReady ? 'Các bước kiểm tra demo đã hoàn tất.' : 'Không hiển thị phần trăm giả. Bạn có thể mô phỏng kết quả sẵn sàng bên dưới.'}</Text>
            </View>
            {run?.videoReady ? <>
              <Notice tone="success">Video đạt trạng thái sẵn sàng trong fixture. Giờ mới có thể mở playback.</Notice>
              <Button label="Mở video demo" onPress={() => send({type: 'PLAY_VIDEO'})} disabled={!run.videoVisible} />
              <Button label={`Video chưa phù hợp · làm lại ${run.regenerationCount}/2`} kind="secondary" onPress={() => send({type: 'MARK_UNSUITABLE'})} disabled={!run || run.regenerationCount >= 2 || run.status !== 'active'} />
            </> : run?.videoError ? <>
              <Notice tone="error">Lỗi tạm thời mô phỏng. Không có provider thật; thử lại sẽ tiếp tục cùng yêu cầu demo.</Notice>
              <Button label="Thử lại video demo" onPress={() => send({type: 'REQUEST_VIDEO'})} />
            </> : run?.videoRequested ? <>
              <Notice>Yêu cầu đã được tiếp nhận. Quota demo đã trừ một lượt cho run này.</Notice>
              <Button label="Mô phỏng video sẵn sàng" onPress={() => send({type: 'COMPLETE_VIDEO_DEMO'})} />
              <Button label="Mô phỏng lỗi có thể khôi phục" kind="quiet" onPress={() => send({type: 'SIMULATE_VIDEO_ERROR'})} />
            </> : <>
              <Notice tone="error">Run này chưa có yêu cầu video hợp lệ. Quay lại kịch bản để duyệt trước.</Notice>
              <Button label="Quay lại kịch bản" onPress={() => send({type: 'BACK'})} />
            </>}
            {run?.status === 'completed' && <Notice tone="success">Run hoàn tất; playback chỉ là placeholder demo.</Notice>}
          </Panel>
        </Page>;
      case 'video-playback':
        return <Page kicker="BƯỚC 6 · KẾT QUẢ VIDEO" title="Video demo đã sẵn sàng" description="Đây là playback placeholder; không có video hoặc URL media thật.">
          <Panel style={styles.formPanel}>
            <Text style={styles.kicker}>VIDEO_READY · DEMO</Text>
            <View style={styles.videoPlaceholder}>
              <Text style={styles.playGlyph}>▶</Text>
              <Text style={styles.subtitle}>Placeholder video demo</Text>
              <Text style={styles.muted}>Video chỉ được mô phỏng trong ứng dụng.</Text>
            </View>
            {run?.status === 'active' ? <>
              <Button label="Tiếp tục đến hoạt động sau video" onPress={() => send({type: 'CONTINUE_AFTER_VIDEO'})} disabled={!run.videoReady || !run.videoVisible} />
              <Button label={'Video không phù hợp · tạo lại ' + run.regenerationCount + '/2'} kind="secondary" onPress={() => send({type: 'MARK_UNSUITABLE'})} disabled={run.regenerationCount >= 2} />
            </> : <Button label="Về lịch sử" kind="secondary" onPress={() => go('history')} />}
          </Panel>
        </Page>;
      case 'activities':
        return <Page kicker="SAU VIDEO · HOẠT ĐỘNG" title={state.workflowContent.postVideoActivity.title} description="Hoạt động chỉ xuất hiện sau khi video sẵn sàng.">
          <Row tablet={tablet}>
            <Panel style={styles.flexPanel}>
              <Text style={styles.kicker}>VẬT LIỆU</Text><Text style={styles.body}>{state.workflowContent.postVideoActivity.materials}</Text>
              <Text style={styles.kicker}>CÁCH THỰC HIỆN</Text>
              {state.workflowContent.postVideoActivity.instructions.map((text, index) => <Text key={text} style={styles.listItem}>{index + 1}. {text}</Text>)}
            </Panel>
            <Panel style={styles.flexPanel}>
              <Text style={styles.kicker}>GHI CHÚ AN TOÀN</Text><Text style={styles.body}>{state.workflowContent.postVideoActivity.note}</Text>
              <Notice tone="info">Hoạt động là fixture theo lesson demo; chính sách no-preset vẫn để mở.</Notice>
              {run?.status === 'active' ? <Button label="Hoàn tất run demo" onPress={() => send({type: 'COMPLETE_RUN'})} /> : <Button label="Về lịch sử" kind="secondary" onPress={() => go('history')} />}
            </Panel>
          </Row>
        </Page>;
      case 'history':
        return <Page kicker="LỊCH SỬ" title="Các run Parent" description="Run demo nằm trong adapter đến khi bạn xóa hoặc reset app.">
          {state.runs.length === 0 ? <Panel><Text style={styles.subtitle}>Chưa có run trong lịch sử.</Text><Button label="Tạo run demo" onPress={() => send({type: 'START_RUN'})} /></Panel> : state.runs.map((item) => <Panel key={item.id} style={styles.historyCard}>
            <View style={styles.historyCopy}><Text style={styles.subtitle}>{item.title}</Text><Text style={styles.muted}>{item.id} · {item.createdLabel} · {statusLabel(item.status)}</Text></View>
            <View style={styles.historyActions}>
              <Button label={item.status === 'active' ? 'Tiếp tục' : 'Mở'} kind="secondary" onPress={() => send({type: 'OPEN_RUN', runId: item.id})} />
              <Button label="Xóa" kind="danger" onPress={() => deleteRun(item.id)} />
            </View>
          </Panel>)}
        </Page>;
      case 'notifications':
        return <Page kicker="THÔNG BÁO" title="Hộp thư Parent demo" description="Thông báo minh họa cho vòng đời run.">
          <Panel style={styles.formPanel}>
            <Text style={styles.subtitle}>{state.workflowContent.reminder.title}</Text>
            <Text style={styles.body}>{state.workflowContent.reminder.description}</Text>
            <Notice>{state.workflowContent.reminder.lifecycleNote}</Notice>
            {activeRun && <Button label="Mở run đang chờ" onPress={() => send({type: 'CONTINUE_RUN'})} />}
          </Panel>
        </Page>;
      case 'quota':
        return <Page kicker="LƯỢT TẠO" title="Lượt tạo video" description="Theo dõi lượt demo và xem thử cách mua thêm.">
          <Panel style={[styles.formPanel, styles.quotaHero]}>
            <Text style={styles.quotaCardTitle}>Số dư lượt tạo trong tháng</Text>
            <View style={styles.quotaCount}><Text style={styles.quotaNumber}>{state.quotaRemaining}</Text><Text style={styles.quotaDenominator}>/{state.quotaTotal}</Text></View>
            <Text style={styles.muted}>lượt còn lại · {state.workflowContent.quotaPeriodLabel}</Text>
            <View style={styles.quotaTrack} accessibilityLabel={`${state.quotaRemaining} trên ${state.quotaTotal} lượt còn lại`}><View style={[styles.quotaFill, {flex: Math.max(0, state.quotaRemaining)}]} /><View style={{flex: Math.max(0, state.quotaTotal - state.quotaRemaining)}} /></View>
            <View style={styles.quotaBadgeRow}><View style={styles.quotaBadge}><Text style={styles.quotaBadgeText}>Định kỳ còn {Math.min(state.quotaRemaining, 1)}</Text></View><View style={styles.quotaBadgeWarm}><Text style={styles.quotaBadgeWarmText}>Demo · không thanh toán</Text></View></View>
          </Panel>
          <Panel>
            <View style={styles.panelHeading}><Text style={styles.subtitle}>Mua thêm lượt</Text><Text style={styles.muted}>Chỉ xem thử</Text></View>
            <View style={styles.packRow}>
              {([{units: 3 as const, price: '29.000đ'}, {units: 5 as const, price: '45.000đ'}, {units: 10 as const, price: '79.000đ'}]).map((pack) => <Pressable key={pack.units} accessibilityRole="radio" accessibilityState={{checked: selectedPack === pack.units}} onPress={() => setSelectedPack(pack.units)} style={[styles.packOption, selectedPack === pack.units && styles.packOptionSelected]}><Text style={[styles.packUnits, selectedPack === pack.units && styles.packUnitsSelected]}>+{pack.units}</Text><Text style={styles.packPrice}>{pack.price}</Text></Pressable>)}
            </View>
            <Text style={styles.fieldLabel}>Phương thức mô phỏng</Text>
            <View style={styles.paymentRow}>{(['MoMo', 'VNPAY'] as const).map((method) => <Pressable key={method} accessibilityRole="radio" accessibilityState={{checked: paymentMethod === method}} onPress={() => setPaymentMethod(method)} style={[styles.paymentChip, paymentMethod === method && styles.paymentChipSelected]}><Text style={[styles.paymentText, paymentMethod === method && styles.paymentTextSelected]}>{method}</Text></Pressable>)}</View>
            <Notice tone="warm">Bản xem thử: thanh toán chỉ mô phỏng, không phát sinh giao dịch thật.</Notice>
            <Button label={`Thử mua +${selectedPack} lượt (${selectedPack === 3 ? '29.000đ' : selectedPack === 5 ? '45.000đ' : '79.000đ'})`} onPress={() => send({type: 'SIMULATE_TOP_UP', units: selectedPack})} />
          </Panel>
          <View style={styles.panelHeading}><Text style={styles.subtitle}>Lịch sử sử dụng lượt</Text><Text style={styles.linkText}>Demo</Text></View>
          {state.runs.filter((item) => item.videoRequested).length === 0 ? <Panel><Text style={styles.muted}>Chưa có lượt nào được sử dụng.</Text></Panel> : state.runs.filter((item) => item.videoRequested).map((item) => {
            const child = state.profiles.find((candidate) => candidate.id === item.childProfileId);
            return <Panel key={item.id} style={styles.historyCard}><View style={styles.quotaUsageBadge}><Text style={styles.quotaUsageText}>−{1 + item.regenerationCount} lượt</Text></View><View style={styles.historyCopy}><Text style={styles.subtitle}>{item.storyTitle} · {child?.label ?? 'Hồ sơ demo'}</Text><Text style={styles.muted}>{item.createdLabel} · {statusLabel(item.status)}</Text></View><Text style={styles.muted}>{item.id}</Text></Panel>;
          })}
        </Page>;
      case 'settings':
        return <Page kicker="CÀI ĐẶT" title="Cài đặt" description="Quản lý hồ sơ và quyền riêng tư của gia đình.">
          <Panel style={styles.accountSummaryPanel}>
            <View style={styles.parentAvatar}><Text style={styles.parentAvatarText}>{parentInitials || 'PH'}</Text></View>
            <View style={styles.accountSummaryCopy}>
              <Text numberOfLines={1} style={styles.accountSummaryName}>{parentName}</Text>
              <Text numberOfLines={1} style={styles.accountSummaryEmail}>{state.parentEmail ?? 'Chưa có email trong phiên demo'}</Text>
              <View style={[styles.parentRole, styles.parentRoleInline]}><Text style={styles.parentRoleText}>Phụ huynh</Text></View>
            </View>
            <Pressable accessibilityRole="button" accessibilityLabel="Chỉnh sửa thông tin tài khoản phụ huynh" onPress={() => openSettingsPanel('account')} style={({pressed}) => [styles.parentAccountEditButton, pressed && styles.buttonPressed]}>
              <NativeGlyph name="edit" />
            </Pressable>
          </Panel>
          <Panel style={styles.settingsPanel}>
            <SettingRow icon="child" title="Hồ sơ bé" detail={`${profile?.label ?? 'Chưa chọn'} · chạm để đổi hồ sơ`} onPress={() => go('profiles')} />
          </Panel>
          <View style={styles.settingsGroup}><Text style={styles.settingsGroupTitle}>Tài khoản & Bảo mật</Text><Panel style={styles.settingsPanel}>
            <SettingRow icon="account" title="Tài khoản & cài đặt" detail="Hồ sơ phụ huynh, thông báo, phụ đề & video" onPress={() => openSettingsPanel('account')} />
            <SettingRow icon="shield" title="Bảo mật" detail="Quyền riêng tư, dữ liệu AI & đổi mật khẩu" onPress={() => openSettingsPanel('security')} />
          </Panel></View>
          <Panel style={styles.formPanel}>
            <Notice>Đăng xuất chỉ đóng phiên demo. Firebase và API chưa được nối.</Notice>
            <Button label="Mở fixture lab riêng" kind="secondary" onPress={onOpenFixtureLab} />
            <Button label="Đăng xuất demo" kind="danger" onPress={() => send({type: 'SIGN_OUT'})} />
          </Panel>
        </Page>;
      default:
        return <Page kicker="PARENT DEMO" title="Màn hình chưa sẵn sàng" description="Quay về trang chủ để tiếp tục."><Button label="Trang chủ" onPress={() => go('home')} /></Page>;
    }
  })();

  const showBack = !['sign-in', 'register', 'recover', 'profiles', 'home'].includes(state.screen)
    && !(state.screen === 'story-review' && run?.videoRequested && !run.replacementRequested);
  const showNav = state.signedIn && !['profiles', 'profile-create'].includes(state.screen);
  return <SafeAreaView style={styles.safeArea}>
    <KeyboardAvoidingView style={styles.fill} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={[styles.shell, tablet && styles.shellTablet]}>
          <View style={styles.header}>
            <View><Text style={styles.brand}>Sketch2Life</Text><Text style={styles.muted}>Parent Android · bản demo</Text></View>
            <View style={styles.headerActions}>
              <View style={styles.demoPill}><Text style={styles.demoPillText}>DEMO</Text></View>
              <Link label="Fixture lab" onPress={onOpenFixtureLab} />
            </View>
          </View>
          {state.message && <Notice>{state.message}</Notice>}
          {failure && <Notice tone="error">{failure}</Notice>}
          {notice && <Notice>{notice}</Notice>}
          {content}
          {showBack && <View style={styles.footerActions}>
            <Button label="Quay lại bước trước" kind="quiet" onPress={() => send({type: 'BACK'})} />
            {activeRun && <Button label="Hủy run demo" kind="danger" onPress={() => send({type: 'CANCEL_RUN'})} />}
          </View>}
          <Text style={styles.disclaimer}>Dữ liệu và thao tác chỉ phục vụ demo; chưa kết nối Firebase, API, camera, microphone hoặc dịch vụ tạo video.</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
    {showNav && <View style={styles.fixedNav}><NavigationBar screen={state.screen} onNavigate={go} /></View>}
    <Modal visible={preflightOpen} transparent animationType="slide" statusBarTranslucent onRequestClose={() => setPreflightOpen(false)}>
      <View style={styles.sheetBackdrop}>
        <Pressable accessibilityRole="button" accessibilityLabel="Đóng kiểm tra trước khi tạo video" style={StyleSheet.absoluteFill} onPress={() => setPreflightOpen(false)} />
        <View accessibilityViewIsModal style={[styles.preflightSheet, tablet && styles.preflightSheetTablet]}>
          <View style={styles.sheetHandle} />
          <View style={styles.preflightHeader}>
            <Text style={styles.preflightTitle}>Kiểm tra trước khi tạo video</Text>
            <Pressable accessibilityRole="button" accessibilityLabel="Đóng" onPress={() => setPreflightOpen(false)} style={styles.closeButton}><Text style={styles.closeButtonText}>×</Text></Pressable>
          </View>
          <ScrollView style={styles.preflightScroll} contentContainerStyle={styles.preflightContent} keyboardShouldPersistTaps="handled">
            <PreflightRow title="Bức tranh của bé" detail={runProfile?.label ?? 'Hồ sơ đang chọn'} />
            <PreflightRow title="Nhân vật chính" detail={run?.subject ?? 'Chủ thể đã được người lớn xác nhận'} />
            <PreflightRow title="Ý tưởng câu chuyện" detail={run?.transcriptConfirmed ? 'Transcript đã được xác nhận' : 'Ý tưởng đã nhập trong bản demo'} />
            <PreflightRow title="Kịch bản 5 cảnh" detail={`Bản #${run?.storyRevision ?? 1} · bạn sẽ duyệt bản cuối khi tạo`} />
            {state.quotaRemaining > 0 ? <Notice tone="info">Dùng 1 lượt demo cho yêu cầu này. Còn lại sau khi tạo: {state.quotaRemaining - 1}/{state.quotaTotal} lượt.</Notice> : <Notice tone="error">Tài khoản demo đã hết lượt tạo video. Mở Lượt tạo để mô phỏng thêm lượt trước khi tiếp tục.</Notice>}
          </ScrollView>
          <View style={styles.preflightActions}>
            <Button label={admissionPending ? 'Đang gửi yêu cầu…' : 'Tạo video ngay'} onPress={() => { void admitVideo(); }} disabled={state.quotaRemaining <= 0 || admissionPending || !run} />
            <Button label="Xem lại kịch bản" kind="secondary" onPress={() => setPreflightOpen(false)} />
          </View>
        </View>
      </View>
    </Modal>
    <Modal visible={settingsPanel !== null} transparent animationType="slide" statusBarTranslucent onRequestClose={() => setSettingsPanel(null)}>
      <View style={styles.sheetBackdrop}>
        <Pressable accessibilityRole="button" accessibilityLabel="Đóng cài đặt" style={StyleSheet.absoluteFill} onPress={() => setSettingsPanel(null)} />
        <View accessibilityViewIsModal style={[styles.accountSettingsSheet, tablet && styles.preflightSheetTablet]}>
          <View style={styles.sheetHandle} />
          <View style={styles.preflightHeader}>
            <Text style={styles.preflightTitle}>{settingsPanel === 'account' ? 'Tài khoản & cài đặt' : 'Bảo mật'}</Text>
            <Pressable accessibilityRole="button" accessibilityLabel="Đóng" onPress={() => setSettingsPanel(null)} style={styles.closeButton}><Text style={styles.closeButtonText}>×</Text></Pressable>
          </View>
          <ScrollView style={styles.preflightScroll} contentContainerStyle={styles.preflightContent} keyboardShouldPersistTaps="handled">
            {settingsPanel === 'account' ? <>
              <Notice tone="info">Thông tin chỉ cập nhật trong phiên demo trên thiết bị này.</Notice>
              <Field label="Họ và tên" value={accountNameDraft} onChangeText={setAccountNameDraft} placeholder="Tên phụ huynh" />
              <Field label="Email liên hệ" value={accountEmailDraft} onChangeText={setAccountEmailDraft} placeholder="name@example.com" keyboardType="email-address" />
              {accountEditError && <Notice tone="error">{accountEditError}</Notice>}
            </> : <>
              <Text style={styles.subtitle}>Quyền riêng tư & Dữ liệu AI</Text>
              <Notice tone="info">Bản demo không gửi hồ sơ, tranh hoặc ý tưởng tới dịch vụ AI.</Notice>
              <Panel style={styles.securityInfoPanel}>
                <Text style={styles.settingTitle}>Tài khoản phụ huynh</Text>
                <Text style={styles.body}>Tài khoản phụ huynh tách biệt với tài khoản trường học và giáo viên.</Text>
                <Text style={styles.settingTitle}>Quyền truy cập hồ sơ</Text>
                <Text style={styles.body}>Hồ sơ trẻ thuộc tài khoản phụ huynh trong bản demo này.</Text>
              </Panel>
              <Panel style={styles.settingsPanel}>
                <SettingRow icon="key" title="Đổi mật khẩu" detail="Chức năng này cần xác thực thật" onPress={() => setSecurityNotice('Đổi mật khẩu chưa khả dụng trong phiên demo.')} />
              </Panel>
              {securityNotice && <Notice tone="warm">{securityNotice}</Notice>}
            </>}
          </ScrollView>
          <View style={styles.preflightActions}>
            {settingsPanel === 'account' ? <>
              <Button label="Lưu thông tin" onPress={() => { void saveParentAccount(); }} />
              <Button label="Đóng" kind="secondary" onPress={() => setSettingsPanel(null)} />
            </> : <Button label="Đã hiểu" kind="secondary" onPress={() => setSettingsPanel(null)} />}
          </View>
        </View>
      </View>
    </Modal>
  </SafeAreaView>;
}
type FieldProps = Readonly<{label: string; value: string; onChangeText: (value: string) => void; placeholder?: string; secureTextEntry?: boolean; keyboardType?: 'default' | 'email-address' | 'numeric'; multiline?: boolean}>;
function ChildAvatar({gender, size}: {gender: ChildGender; size: number}): React.JSX.Element {
  const isBoy = gender === 'male';
  return <View accessibilityLabel={isBoy ? 'Avatar minh họa bé trai' : 'Avatar minh họa bé gái'} style={[styles.childAvatar, {width: size, height: size, borderRadius: size / 2}, isBoy ? styles.boyAvatar : styles.girlAvatar]}>
    <Text style={{fontSize: size * 0.59, lineHeight: size * 0.8}}>{isBoy ? '👦🏻' : '👧🏻'}</Text>
  </View>;
}

type NativeIconName = 'account' | 'child' | 'shield' | 'key' | 'edit';

function NativeGlyph({name}: {name: NativeIconName}): React.JSX.Element {
  if (name === 'edit') return <View style={styles.glyphPencil}><View style={styles.glyphPencilBody} /><View style={styles.glyphPencilTip} /></View>;
  if (name === 'shield') return <View style={styles.glyphShield}><View style={styles.glyphShieldCheckA} /><View style={styles.glyphShieldCheckB} /></View>;
  if (name === 'key') return <View style={styles.glyphKey}><View style={styles.glyphKeyRing} /><View style={styles.glyphKeyStem} /></View>;
  return <View style={styles.glyphPerson}><View style={styles.glyphPersonHead} /><View style={styles.glyphPersonShoulders} /></View>;
}

function SettingRow({icon, title, detail, onPress}: {icon: NativeIconName; title: string; detail: string; onPress: () => void}): React.JSX.Element {
  return <Pressable accessibilityRole="button" accessibilityLabel={`${title}. ${detail}`} onPress={onPress} style={styles.settingRow}>
    <View style={styles.settingIcon}><NativeGlyph name={icon} /></View>
    <View style={styles.settingCopy}><Text style={styles.settingTitle}>{title}</Text><Text style={styles.settingDetail}>{detail}</Text></View>
    <Text accessibilityElementsHidden style={styles.settingChevron}>›</Text>
  </Pressable>;
}

function Field({label, value, onChangeText, placeholder, secureTextEntry, keyboardType = 'default', multiline = false}: FieldProps): React.JSX.Element {
  return <View style={styles.field}>
    <Text style={styles.fieldLabel}>{label}</Text>
    <TextInput accessibilityLabel={label} value={value} onChangeText={onChangeText} placeholder={placeholder} placeholderTextColor="#7B8497" secureTextEntry={secureTextEntry} keyboardType={keyboardType} multiline={multiline} textAlignVertical={multiline ? 'top' : 'center'} style={[styles.input, multiline && styles.inputMultiline]} />
  </View>;
}

function Button({label, onPress, kind = 'primary', disabled = false}: ButtonProps): React.JSX.Element {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{disabled}} disabled={disabled} onPress={onPress} style={({pressed}) => [styles.button, kind === 'secondary' && styles.buttonSecondary, kind === 'quiet' && styles.buttonQuiet, kind === 'danger' && styles.buttonDanger, disabled && styles.buttonDisabled, pressed && !disabled && styles.buttonPressed]}>
    <Text style={[styles.buttonText, kind !== 'primary' && styles.buttonTextSecondary, kind === 'danger' && styles.buttonTextDanger]}>{label}</Text>
  </Pressable>;
}

function Link({label, onPress}: {label: string; onPress: () => void}): React.JSX.Element {
  return <Pressable accessibilityRole="button" onPress={onPress} style={styles.link}><Text style={styles.linkText}>{label}</Text></Pressable>;
}

function Panel({children, style}: React.PropsWithChildren<{style?: StyleProp<ViewStyle>}>): React.JSX.Element {
  return <View style={[styles.panel, style]}>{children}</View>;
}

function Page({kicker, title, description, children}: React.PropsWithChildren<{kicker: string; title: string; description: string}>): React.JSX.Element {
  return <View style={styles.page}>
    <View style={styles.pageHeading}><Text style={styles.kicker}>{kicker}</Text><Text style={styles.pageTitle}>{title}</Text><Text style={styles.body}>{description}</Text></View>
    {children}
  </View>;
}

function Row({tablet, children}: React.PropsWithChildren<{tablet: boolean}>): React.JSX.Element {
  return <View style={[styles.row, !tablet && styles.rowStack]}>{children}</View>;
}

function Notice({children, tone = 'info'}: React.PropsWithChildren<{tone?: 'info' | 'error' | 'success' | 'warm'}>): React.JSX.Element {
  return <View accessibilityLiveRegion="polite" style={[styles.notice, tone === 'error' && styles.noticeError, tone === 'success' && styles.noticeSuccess, tone === 'warm' && styles.noticeWarm]}><Text style={styles.noticeText}>{children}</Text></View>;
}

function Metric({label, value}: {label: string; value: string}): React.JSX.Element {
  return <View style={styles.metric}><Text style={styles.metricLabel}>{label}</Text><Text style={styles.metricValue}>{value}</Text></View>;
}

function PreflightRow({title, detail}: {title: string; detail: string}): React.JSX.Element {
  return <View style={styles.preflightRow}>
    <View style={styles.preflightCheck}><Text style={styles.preflightCheckText}>✓</Text></View>
    <View style={styles.preflightRowCopy}><Text style={styles.preflightRowTitle}>{title}</Text><Text style={styles.preflightRowDetail}>{detail}</Text></View>
  </View>;
}

function Tile({title, detail, onPress}: {title: string; detail: string; onPress: () => void}): React.JSX.Element {
  return <Pressable accessibilityRole="button" onPress={onPress} style={styles.tile}><Text style={styles.subtitle}>{title}</Text><Text style={styles.muted}>{detail}</Text></Pressable>;
}

function DrawingPlaceholder(): React.JSX.Element {
  return <View accessibilityLabel="Tranh minh họa tổng hợp trong bản demo" style={styles.drawing}>
    <View style={styles.sun} /><View style={styles.hillBack} /><View style={styles.hillFront} /><View style={styles.flowerOne} /><View style={styles.flowerTwo} />
    <Text style={styles.drawingLabel}>TRANH DEMO</Text>
  </View>;
}

function NavigationBar({screen, onNavigate}: {screen: ParentScreen; onNavigate: (screen: ParentScreen) => void}): React.JSX.Element {
  const items: readonly Readonly<{screen: ParentScreen; label: string}>[] = [
    {screen: 'home', label: 'Trang chủ'}, {screen: 'history', label: 'Lịch sử'}, {screen: 'quota', label: 'Quota'}, {screen: 'settings', label: 'Cài đặt'},
  ];
  return <View style={styles.nav} accessibilityRole="tablist">{items.map((item) => <Pressable key={item.screen} accessibilityRole="tab" accessibilityState={{selected: item.screen === screen}} onPress={() => onNavigate(item.screen)} style={[styles.navItem, item.screen === screen && styles.navItemActive]}>
    <Text style={[styles.navText, item.screen === screen && styles.navTextActive]}>{item.label}</Text>
  </Pressable>)}</View>;
}


function statusLabel(status: ParentRun['status']): string {
  return status === 'completed' ? 'Đã hoàn tất' : status === 'cancelled' ? 'Đã hủy' : 'Đang thực hiện';
}

const styles = StyleSheet.create({
  safeArea: {flex: 1, backgroundColor: '#F5F7FC'},
  fill: {flex: 1},
  scroll: {flexGrow: 1, paddingHorizontal: 16, paddingVertical: 12},
  shell: {width: '100%', maxWidth: 720, alignSelf: 'center', gap: 16, paddingBottom: 28},
  shellTablet: {maxWidth: 1160, gap: 22, paddingHorizontal: 14, paddingTop: 8},
  header: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12, paddingVertical: 8},
  headerActions: {flexDirection: 'row', alignItems: 'center', gap: 8},
  brand: {fontSize: 20, fontWeight: '800', color: '#18233A'},
  demoPill: {borderRadius: 99, backgroundColor: '#FFF1D9', paddingHorizontal: 10, paddingVertical: 6},
  demoPillText: {fontSize: 10, color: '#875918', fontWeight: '900', letterSpacing: 1},
  authIntro: {flex: 1, justifyContent: 'center', gap: 15, padding: 10},
  authPanel: {flex: 1, minWidth: 290},
  formPanel: {width: '100%', maxWidth: 760, alignSelf: 'center'},
  flexPanel: {flex: 1, minWidth: 0},
  page: {gap: 15},
  pageHeading: {gap: 7, marginBottom: 2},
  kicker: {fontSize: 10, fontWeight: '900', letterSpacing: 1.1, color: '#526BA6'},
  hero: {fontSize: 34, lineHeight: 41, fontWeight: '800', color: '#18233A', letterSpacing: -0.8, maxWidth: 560},
  pageTitle: {fontSize: 28, lineHeight: 35, fontWeight: '800', color: '#18233A', letterSpacing: -0.6},
  title: {fontSize: 23, lineHeight: 29, fontWeight: '800', color: '#18233A'},
  subtitle: {fontSize: 16, lineHeight: 22, fontWeight: '800', color: '#202D47'},
  body: {fontSize: 14, lineHeight: 21, color: '#4F5B73'},
  muted: {fontSize: 12, lineHeight: 18, color: '#65718A'},
  helper: {fontSize: 11, lineHeight: 17, color: '#69758D'},
  panel: {backgroundColor: '#FFFFFF', borderRadius: 18, borderWidth: 1, borderColor: '#E0E5F0', padding: 17, gap: 13},
  row: {flexDirection: 'row', alignItems: 'stretch', gap: 14},
  rowStack: {flexDirection: 'column'},
  field: {gap: 7},
  fieldLabel: {fontSize: 12, color: '#394763', fontWeight: '700'},
  input: {minHeight: 50, borderRadius: 12, borderWidth: 1, borderColor: '#CFD7E7', backgroundColor: '#FFFFFF', color: '#1A2740', paddingHorizontal: 14, paddingVertical: 12, fontSize: 14},
  inputMultiline: {minHeight: 106, paddingTop: 12},
  button: {flex: 1, minHeight: 48, borderRadius: 13, paddingHorizontal: 14, paddingVertical: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: '#315FEA'},
  buttonSecondary: {backgroundColor: '#EEF2FF', borderWidth: 1, borderColor: '#CAD5FF'},
  buttonQuiet: {backgroundColor: 'transparent'},
  buttonDanger: {backgroundColor: '#FFF0EF', borderWidth: 1, borderColor: '#F2C9C5'},
  buttonDisabled: {opacity: 0.45},
  buttonPressed: {opacity: 0.82},
  buttonText: {fontSize: 14, fontWeight: '800', textAlign: 'center', color: '#FFFFFF'},
  buttonTextSecondary: {color: '#3153B4'},
  buttonTextDanger: {color: '#A8433B'},
  link: {minHeight: 44, justifyContent: 'center', paddingHorizontal: 4},
  linkText: {fontSize: 13, fontWeight: '700', color: '#315FEA'},
  linkRow: {flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center'},
  notice: {borderRadius: 12, borderWidth: 1, borderColor: '#C9D8FF', backgroundColor: '#EEF3FF', paddingHorizontal: 13, paddingVertical: 11},
  noticeError: {borderColor: '#F0C1BC', backgroundColor: '#FFF0EE'},
  noticeSuccess: {borderColor: '#B7DFC6', backgroundColor: '#ECF8F0'},
  noticeWarm: {borderColor: '#F4D591', backgroundColor: '#FFF7E2'},
  noticeText: {fontSize: 12, lineHeight: 18, color: '#34486F'},
  profileCard: {flex: 1, minWidth: 220, backgroundColor: '#FFFFFF', borderRadius: 18, borderWidth: 1, borderColor: '#E0E5F0', padding: 17, gap: 7},
  profileCardSelected: {borderColor: '#4F73F2', backgroundColor: '#F0F4FF'},
  addProfileCard: {borderStyle: 'dashed', alignItems: 'center', justifyContent: 'center', minHeight: 156},
  addProfileGlyph: {fontSize: 30, color: '#315FEA', fontWeight: '700'},
  childAvatar: {alignItems: 'center', justifyContent: 'center', overflow: 'hidden', borderWidth: 1, borderColor: '#FFFFFF'},
  boyAvatar: {backgroundColor: '#DBEDFF'},
  girlAvatar: {backgroundColor: '#FFE8E2'},
  selectedPill: {alignSelf: 'flex-start', borderRadius: 99, backgroundColor: '#315FEA', paddingHorizontal: 10, paddingVertical: 5, marginTop: 2},
  selectedPillText: {fontSize: 9, fontWeight: '900', letterSpacing: 0.7, color: '#FFFFFF'},
  profilePreview: {alignItems: 'center', paddingVertical: 5, gap: 3},
  genderChoices: {flexDirection: 'row', gap: 10},
  genderChoice: {flex: 1, minHeight: 60, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, borderRadius: 14, borderWidth: 1, borderColor: '#DCE3F0', backgroundColor: '#FFFFFF', padding: 10},
  genderChoiceSelected: {borderColor: '#315FEA', backgroundColor: '#EEF2FF'},
  genderChoiceLabel: {fontSize: 13, fontWeight: '800', color: '#253451'},
  currentProfile: {flexDirection: 'row', alignItems: 'center', gap: 11},
  currentProfileCopy: {flex: 1, gap: 2},
  profileSwitch: {minWidth: 56, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: '#EEF2FF'},
  profileSwitchText: {color: '#315FEA', fontSize: 13, fontWeight: '800'},
  avatar: {width: 44, height: 44, borderRadius: 22, overflow: 'hidden', textAlign: 'center', textAlignVertical: 'center', backgroundColor: '#EAF0FF', color: '#315FEA', fontSize: 19, fontWeight: '800'},
  panelHeading: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12},
  storySceneHeading: {flexDirection: 'row', alignItems: 'center', gap: 10},
  sceneNumber: {width: 32, height: 32, borderRadius: 16, backgroundColor: '#315FEA', alignItems: 'center', justifyContent: 'center'},
  sceneNumberText: {fontSize: 13, fontWeight: '900', color: '#FFFFFF'},
  storySceneCopy: {flex: 1, gap: 2},
  sceneDuration: {fontSize: 11, color: '#65718A'},
  metric: {flexDirection: 'row', justifyContent: 'space-between', gap: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#E5E9F1', paddingVertical: 7},
  metricLabel: {flex: 1, fontSize: 12, color: '#65718A'},
  metricValue: {flex: 1, textAlign: 'right', fontSize: 12, color: '#263653', fontWeight: '800'},
  tile: {flex: 1, minWidth: 170, minHeight: 80, justifyContent: 'center', backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E0E5F0', borderRadius: 15, padding: 15, gap: 5},
  checkRow: {minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 10},
  checkbox: {width: 22, height: 22, borderRadius: 6, borderWidth: 1.5, borderColor: '#8995AD', backgroundColor: '#FFFFFF'},
  checkboxOn: {backgroundColor: '#315FEA', borderColor: '#315FEA'},
  drawing: {minHeight: 180, borderRadius: 15, backgroundColor: '#F0F3FA', overflow: 'hidden', alignItems: 'center', justifyContent: 'center', position: 'relative'},
  sun: {position: 'absolute', width: 43, height: 43, borderRadius: 22, backgroundColor: '#F2CE82', top: 20, right: '17%'},
  hillBack: {position: 'absolute', height: 75, width: '80%', borderRadius: 60, backgroundColor: '#B9D2C3', bottom: 15, left: '-4%', transform: [{rotate: '-8deg'}]},
  hillFront: {position: 'absolute', height: 70, width: '68%', borderRadius: 60, backgroundColor: '#91B6A0', bottom: -7, right: '-5%', transform: [{rotate: '8deg'}]},
  flowerOne: {position: 'absolute', width: 16, height: 40, borderRadius: 9, backgroundColor: '#C86D73', left: '29%', top: '44%'},
  flowerTwo: {position: 'absolute', width: 16, height: 34, borderRadius: 9, backgroundColor: '#D8A350', right: '30%', top: '49%'},
  drawingLabel: {position: 'absolute', bottom: 9, color: '#4F5B73', fontSize: 10, fontWeight: '900', letterSpacing: 1},
  sceneGrid: {gap: 10},
  sceneGridTablet: {flexDirection: 'row', flexWrap: 'wrap'},
  sceneCard: {flex: 1, minWidth: 220},
  videoPlaceholder: {minHeight: 205, borderRadius: 15, backgroundColor: '#17233B', alignItems: 'center', justifyContent: 'center', gap: 9, padding: 20},
  playGlyph: {fontSize: 32, color: '#FFFFFF'},
  videoStatusCopy: {fontSize: 13, lineHeight: 19, textAlign: 'center', color: '#D6DEEE'},
  listItem: {fontSize: 14, lineHeight: 21, color: '#4F5B73', paddingVertical: 3},
  historyCard: {flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between'},
  historyCopy: {flex: 1, minWidth: 190, gap: 4},
  historyActions: {flexDirection: 'row', flexWrap: 'wrap', gap: 7},
  quotaRow: {flexDirection: 'row', alignItems: 'baseline', gap: 9},
  quotaNumber: {fontSize: 44, fontWeight: '900', color: '#315FEA'},
  quotaHero: {alignItems: 'center', paddingVertical: 22, backgroundColor: '#FFFFFF'},
  quotaCardTitle: {fontSize: 16, fontWeight: '800', color: '#253451', textAlign: 'center'},
  quotaCount: {flexDirection: 'row', alignItems: 'baseline', gap: 2},
  quotaDenominator: {fontSize: 24, fontWeight: '800', color: '#77839A'},
  quotaTrack: {width: '88%', height: 12, flexDirection: 'row', overflow: 'hidden', borderRadius: 99, backgroundColor: '#E5EAF5', marginTop: 6},
  quotaFill: {borderRadius: 99, backgroundColor: '#3474F6'},
  quotaBadgeRow: {flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 8, marginTop: 3},
  quotaBadge: {borderRadius: 99, backgroundColor: '#EAF0FF', paddingHorizontal: 12, paddingVertical: 7},
  quotaBadgeText: {fontSize: 11, fontWeight: '700', color: '#315FEA'},
  quotaBadgeWarm: {borderRadius: 99, backgroundColor: '#FFF2D4', paddingHorizontal: 12, paddingVertical: 7},
  quotaBadgeWarmText: {fontSize: 11, fontWeight: '700', color: '#765413'},
  packRow: {flexDirection: 'row', gap: 8},
  packOption: {flex: 1, minHeight: 70, alignItems: 'center', justifyContent: 'center', borderRadius: 15, borderWidth: 1, borderColor: '#DCE3F0', backgroundColor: '#FFFFFF', paddingHorizontal: 4},
  packOptionSelected: {borderColor: '#F4B42A', backgroundColor: '#FFF8E7'},
  packUnits: {fontSize: 20, fontWeight: '900', color: '#315FEA'},
  packUnitsSelected: {color: '#805800'},
  packPrice: {fontSize: 10, fontWeight: '700', color: '#47546D'},
  paymentRow: {flexDirection: 'row', gap: 8},
  paymentChip: {minHeight: 42, minWidth: 86, alignItems: 'center', justifyContent: 'center', borderRadius: 99, borderWidth: 1, borderColor: '#DCE3F0', backgroundColor: '#FFFFFF', paddingHorizontal: 14},
  paymentChipSelected: {borderColor: '#315FEA', backgroundColor: '#EEF2FF'},
  paymentText: {fontSize: 12, color: '#4F5B73', fontWeight: '700'},
  paymentTextSelected: {color: '#315FEA'},
  quotaUsageBadge: {minWidth: 67, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: '#E7F6EF', paddingHorizontal: 8, paddingVertical: 8},
  quotaUsageText: {fontSize: 11, fontWeight: '800', color: '#14805E'},
  accountSummaryPanel: {flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12},
  parentAvatar: {width: 46, height: 46, alignItems: 'center', justifyContent: 'center', borderRadius: 23, borderWidth: 2, borderColor: '#D9E8FF', backgroundColor: '#EAF2FF'},
  parentAvatarText: {fontSize: 15, fontWeight: '900', color: '#315FEA'},
  accountSummaryCopy: {flex: 1, minWidth: 0, gap: 2},
  parentRoleInline: {alignSelf: 'flex-start', marginTop: 4},
  accountSummaryName: {fontSize: 13, lineHeight: 18, fontWeight: '900', color: '#202D47'},
  accountSummaryEmail: {fontSize: 10, lineHeight: 14, color: '#65718A'},
  parentRole: {alignItems: 'center', justifyContent: 'center', minHeight: 28, borderRadius: 99, backgroundColor: '#E6F6F0', paddingHorizontal: 9},
  parentRoleText: {fontSize: 10, fontWeight: '700', color: '#16805D'},
  parentAccountEditButton: {width: 44, height: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 13, borderWidth: 1, borderColor: '#DCE3F0', backgroundColor: '#EEF2FF'},
  glyphPerson: {width: 22, height: 22, alignItems: 'center', justifyContent: 'center'},
  glyphPersonHead: {position: 'absolute', top: 1, width: 8, height: 8, borderRadius: 4, backgroundColor: '#315FEA'},
  glyphPersonShoulders: {position: 'absolute', bottom: 1, width: 18, height: 10, borderTopLeftRadius: 10, borderTopRightRadius: 10, borderWidth: 1.8, borderBottomWidth: 0, borderColor: '#315FEA'},
  glyphShield: {width: 17, height: 21, alignItems: 'center', justifyContent: 'center', borderWidth: 1.8, borderColor: '#16805D', borderTopLeftRadius: 7, borderTopRightRadius: 7, borderBottomLeftRadius: 10, borderBottomRightRadius: 10},
  glyphShieldCheckA: {position: 'absolute', width: 4, height: 1.8, left: 3, top: 10, borderRadius: 2, backgroundColor: '#16805D', transform: [{rotate: '45deg'}]},
  glyphShieldCheckB: {position: 'absolute', width: 7, height: 1.8, left: 5, top: 9, borderRadius: 2, backgroundColor: '#16805D', transform: [{rotate: '-48deg'}]},
  glyphKey: {width: 23, height: 18, flexDirection: 'row', alignItems: 'center'},
  glyphKeyRing: {width: 11, height: 11, borderRadius: 6, borderWidth: 2, borderColor: '#315FEA'},
  glyphKeyStem: {width: 10, height: 2, marginLeft: -1, backgroundColor: '#315FEA'},
  glyphPencil: {width: 22, height: 22, alignItems: 'center', justifyContent: 'center', transform: [{rotate: '42deg'}]},
  glyphPencilBody: {width: 4, height: 17, borderRadius: 2, backgroundColor: '#315FEA'},
  glyphPencilTip: {position: 'absolute', bottom: 1, width: 0, height: 0, borderLeftWidth: 3, borderRightWidth: 3, borderTopWidth: 4, borderLeftColor: 'transparent', borderRightColor: 'transparent', borderTopColor: '#315FEA'},
  settingsGroup: {gap: 8},
  settingsGroupTitle: {fontSize: 14, fontWeight: '800', color: '#253451'},
  settingsPanel: {gap: 0, paddingVertical: 2},
  settingRow: {minHeight: 70, flexDirection: 'row', alignItems: 'center', gap: 11, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#E5E9F1', paddingVertical: 10},
  settingIcon: {width: 40, height: 40, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: '#EEF2FF'},
  settingIconText: {fontSize: 18},
  settingCopy: {flex: 1, gap: 3},
  settingTitle: {fontSize: 13, fontWeight: '800', color: '#253451'},
  settingDetail: {fontSize: 11, lineHeight: 16, color: '#66728A'},
  settingChevron: {fontSize: 24, color: '#71809A'},
  footerActions: {flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 7},
  nav: {flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', backgroundColor: '#E9EEF9', borderRadius: 15, padding: 5, gap: 4},
  fixedNav: {width: '100%', borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: '#DDE4F0', backgroundColor: '#FFFFFF', paddingHorizontal: 16, paddingTop: 7, paddingBottom: 9},
  navItem: {flex: 1, minWidth: 86, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 11, paddingHorizontal: 6},
  navItemActive: {backgroundColor: '#FFFFFF'},
  navText: {fontSize: 12, color: '#61708D', fontWeight: '700'},
  navTextActive: {color: '#244FCF'},
  sheetBackdrop: {flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(18, 27, 46, 0.48)'},
  preflightSheet: {width: '100%', maxHeight: '92%', backgroundColor: '#FFFFFF', borderTopLeftRadius: 25, borderTopRightRadius: 25, paddingHorizontal: 16, paddingTop: 9, paddingBottom: 18, gap: 12},
  preflightSheetTablet: {maxWidth: 560, alignSelf: 'center', borderRadius: 25, marginBottom: 18},
  sheetHandle: {alignSelf: 'center', width: 42, height: 4, borderRadius: 99, backgroundColor: '#D8DFEB'},
  preflightHeader: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12},
  preflightTitle: {flex: 1, fontSize: 17, fontWeight: '900', color: '#1E2B43'},
  closeButton: {width: 44, height: 44, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#DCE3F0', borderRadius: 13},
  closeButtonText: {fontSize: 25, lineHeight: 28, color: '#315FEA'},
  preflightScroll: {flexShrink: 1},
  preflightContent: {gap: 9, paddingBottom: 2},
  preflightRow: {minHeight: 54, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 14, backgroundColor: '#E9F7F0', padding: 10},
  preflightCheck: {width: 28, height: 28, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: '#168364'},
  preflightCheckText: {fontSize: 16, fontWeight: '900', color: '#FFFFFF'},
  preflightRowCopy: {flex: 1, gap: 2},
  preflightRowTitle: {fontSize: 12, fontWeight: '800', color: '#17694F'},
  preflightRowDetail: {fontSize: 11, lineHeight: 16, color: '#365C53'},
  preflightActions: {gap: 8},
  accountSettingsSheet: {width: '100%', maxHeight: '92%', backgroundColor: '#FFFFFF', borderTopLeftRadius: 25, borderTopRightRadius: 25, paddingHorizontal: 16, paddingTop: 9, paddingBottom: 18, gap: 12},
  securityInfoPanel: {gap: 8},
  disclaimer: {textAlign: 'center', fontSize: 10, lineHeight: 15, color: '#758098', paddingHorizontal: 6},
});
