import {
  DEMO_CONTEXT,
  DEMO_DEFAULT_SUBJECT,
  DEMO_DEFAULT_TRANSCRIPT,
  DEMO_GUIDE_STEPS,
  DEMO_OUTDOOR_ACTIVITY,
  DEMO_PROFILES,
  DEMO_QUOTA,
  DEMO_REMINDER,
  DEMO_STORY_SCENES,
  DEMO_STORY_TITLES,
  createDemoRun,
} from './parentDemoFixtures';
import type {
  ParentProfile,
  ParentRun,
  ParentRunStage,
  ParentScreen,
  ParentWorkflowCommand,
  ParentWorkflowPort,
  ParentWorkflowSnapshot,
} from '../../features/parent-flow/parentWorkflowPort';

const initialSnapshot: ParentWorkflowSnapshot = {
  screen: 'sign-in',
  signedIn: false,
  parentEmail: null,
  parentDisplayName: null,
  workflowContent: {
    pinnedContext: DEMO_CONTEXT,
    guideSteps: DEMO_GUIDE_STEPS,
    postVideoActivity: DEMO_OUTDOOR_ACTIVITY,
    quotaPeriodLabel: DEMO_QUOTA.periodLabel,
    reminder: DEMO_REMINDER,
  },
  profiles: DEMO_PROFILES,
  selectedProfileId: null,
  runs: [],
  activeRunId: null,
  selectedRunId: null,
  guideRequested: false,
  cameraDenied: false,
  microphoneDenied: false,
  quotaRemaining: DEMO_QUOTA.remaining,
  quotaTotal: DEMO_QUOTA.total,
  message: 'Đang ở chế độ demo. Thao tác không gửi dữ liệu tới backend.',
};

const stageScreen: Record<ParentRunStage, ParentScreen> = {
  drawing: 'drawing',
  upload: 'upload',
  'transcript-review': 'transcript-review',
  'subject-review': 'subject-review',
  'context-review': 'context-review',
  'story-review': 'story-review',
  'video-status': 'video-status',
  'video-playback': 'video-playback',
  activities: 'activities',
  completed: 'video-status',
  cancelled: 'home',
};

const menuScreens = new Set<ParentScreen>(['home', 'history', 'notifications', 'quota', 'settings']);

export class ParentDemoWorkflowAdapter implements ParentWorkflowPort {
  private snapshot = initialSnapshot;
  private readonly listeners = new Set<() => void>();
  private runSequence = 1;
  private profileSequence = DEMO_PROFILES.length + 1;

  getSnapshot(): ParentWorkflowSnapshot {
    return this.snapshot;
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  async dispatch(command: ParentWorkflowCommand): Promise<void> {
    switch (command.type) {
      case 'NAVIGATE':
        this.navigate(command.screen);
        break;
      case 'BACK':
        this.goBack();
        break;
      case 'SIGN_IN':
        if (!command.email.trim()) {
          this.setMessage('Nhập email để tiếp tục trong bản demo.');
          break;
        }
        this.snapshot = {
          ...this.snapshot,
          signedIn: true,
          parentEmail: command.email.trim(),
          screen: 'profiles',
          parentDisplayName: null,
          message: 'Đăng nhập demo thành công. Đây chưa phải phiên Firebase.',
        };
        this.emit();
        break;
      case 'REGISTER_DEMO':
        if (!command.email.trim()) {
          this.setMessage('Nhập email để xem luồng đăng ký demo.');
          break;
        }
        this.snapshot = {
          ...this.snapshot,
          signedIn: true,
          parentEmail: command.email.trim(),
          screen: 'profiles',
          parentDisplayName: command.displayName.trim() || 'Phụ huynh demo',
          message: 'Tài khoản này chỉ tồn tại trong demo; chưa tạo tài khoản thật.',
        };
        this.emit();
        break;
      case 'RECOVER_PASSWORD_DEMO':
        this.setMessage(
          command.email.trim()
            ? 'Demo chưa gửi email. Luồng khôi phục thật cần API/auth adapter.'
            : 'Nhập email để xem trạng thái khôi phục demo.',
        );
        break;
      case 'UPDATE_PARENT_ACCOUNT': {
        const displayName = command.displayName.trim();
        const email = command.email.trim();
        if (!displayName || !email) {
          this.setMessage('Nhập tên và email để cập nhật hồ sơ demo.');
          break;
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
          this.setMessage('Email demo chưa đúng định dạng.');
          break;
        }
        this.snapshot = {
          ...this.snapshot,
          parentDisplayName: displayName,
          parentEmail: email,
          message: 'Đã cập nhật thông tin tài khoản trong phiên demo này.',
        };
        this.emit();
        break;
      }
      case 'SIGN_OUT':
        this.runSequence = 1;
        this.profileSequence = DEMO_PROFILES.length + 1;
        this.snapshot = {
          ...this.snapshot,
          signedIn: false,
          parentEmail: null,
          parentDisplayName: null,
          profiles: DEMO_PROFILES,
          selectedProfileId: null,
          runs: [],
          activeRunId: null,
          selectedRunId: null,
          guideRequested: false,
          cameraDenied: false,
          microphoneDenied: false,
          quotaRemaining: DEMO_QUOTA.remaining,
          quotaTotal: DEMO_QUOTA.total,
          screen: 'sign-in',
          message: 'Đã thoát phiên demo.',
        };
        this.emit();
        break;
      case 'SELECT_PROFILE':
        if (!this.snapshot.profiles.some((profile) => profile.id === command.profileId)) {
          this.setMessage('Không tìm thấy hồ sơ demo này.');
          break;
        }
        this.snapshot = {
          ...this.snapshot,
          selectedProfileId: command.profileId,
          screen: 'home',
          message: null,
        };
        this.emit();
        break;
      case 'CREATE_PROFILE':
        this.createProfile(command.label, command.ageMonths, command.gender);
        break;
      case 'START_RUN':
        this.startRun();
        break;
      case 'CONTINUE_RUN':
        this.continueRun();
        break;
      case 'TOGGLE_GUIDE':
        this.snapshot = {
          ...this.snapshot,
          guideRequested: command.enabled,
          message: command.enabled
            ? 'Guide demo đã sẵn sàng. Không gửi thông tin hồ sơ hoặc tranh.'
            : 'Đã bỏ qua guide; có thể tiếp tục capture.',
        };
        this.emit();
        break;
      case 'SIMULATE_CAMERA_DENIAL':
        this.snapshot = {...this.snapshot, cameraDenied: command.denied, message: command.denied ? 'Camera bị từ chối trong demo; có thể chọn ảnh thư viện.' : 'Camera demo đã bật lại.'};
        this.emit();
        break;
      case 'SIMULATE_MICROPHONE_DENIAL':
        this.snapshot = {...this.snapshot, microphoneDenied: command.denied, message: command.denied ? 'Microphone bị từ chối trong demo; vẫn có thể nhập chữ.' : 'Microphone demo đã bật lại.'};
        this.emit();
        break;
      case 'SIMULATE_UPLOAD_INTERRUPTION':
        this.simulateUploadInterruption();
        break;
      case 'RESUME_UPLOAD':
        this.resumeUpload();
        break;
      case 'COMPLETE_UPLOAD':
        this.completeUpload();
        break;
      case 'SAVE_IDEA':
        this.updateCurrentRun((run) => ({
          ...run,
          ideaText: command.text,
          transcript: command.text.trim() || DEMO_DEFAULT_TRANSCRIPT,
          hasVoiceIdea: command.hasVoiceIdea,
        }));
        break;
      case 'CAPTURE_DRAWING':
        if (command.source === 'camera-demo' && this.snapshot.cameraDenied) {
          this.setMessage('Camera demo bị từ chối. Hãy chọn tranh từ thư viện.');
          break;
        }
        this.updateCurrentRun(
          (run) => ({...run, drawingSource: command.source, uploadInterrupted: false, uploadResumeCount: 0, transcript: run.ideaText.trim() || DEMO_DEFAULT_TRANSCRIPT, transcriptConfirmed: false, subject: DEMO_DEFAULT_SUBJECT, subjectRevision: 1, subjectConfirmed: false, contextApproved: false, title: DEMO_STORY_TITLES[0], storyTitle: DEMO_STORY_TITLES[0], storyScenes: DEMO_STORY_SCENES, storyRevision: 1, rewriteCount: 0, scriptConfirmed: false, videoRequested: false, videoReady: false, videoError: false, videoVisible: false, replacementRequested: false, stage: 'upload'}),
          'upload',
          'Tranh demo đã chọn. Mô phỏng upload chưa bắt đầu.',
        );
        break;
      case 'CONFIRM_TRANSCRIPT':
        if (!this.requireActiveStage('transcript-review', 'Mở bước rà soát ý tưởng trước khi xác nhận.')) break;
        if (!command.transcript.trim()) {
          this.setMessage('Cần có nội dung ý tưởng trước khi xác nhận.');
          break;
        }
        this.updateCurrentRun(
          (run) => ({
            ...run,
            transcript: command.transcript.trim(),
            transcriptConfirmed: true,
            subjectConfirmed: command.transcript.trim() === run.transcript ? run.subjectConfirmed : false,
            contextApproved: command.transcript.trim() === run.transcript ? run.contextApproved : false,
            scriptConfirmed: command.transcript.trim() === run.transcript ? run.scriptConfirmed : false,
            videoRequested: command.transcript.trim() === run.transcript ? run.videoRequested : false,
            videoReady: command.transcript.trim() === run.transcript ? run.videoReady : false,
            videoError: command.transcript.trim() === run.transcript ? run.videoError : false,
            videoVisible: command.transcript.trim() === run.transcript ? run.videoVisible : false,
            replacementRequested: command.transcript.trim() === run.transcript ? run.replacementRequested : false,
            stage: 'subject-review',
          }),
          'subject-review',
          'Đã xác nhận ý tưởng demo. Tiếp theo là rà soát chủ thể tranh.',
        );
        break;
      case 'CONFIRM_SUBJECT':
        if (!this.requireActiveStage('subject-review', 'Mở bước rà soát chủ thể trước khi xác nhận.')) break;
        this.confirmSubject(command.subject);
        break;
      case 'CONFIRM_CONTEXT':
        if (!this.requireActiveStage('context-review', 'Mở bước rà soát context trước khi xác nhận.')) break;
        this.updateCurrentRun(
          (run) => ({...run, contextApproved: true, stage: 'story-review'}),
          'story-review',
          'Context demo tối thiểu đã được xác nhận.',
        );
        break;
      case 'REWRITE_STORY':
        this.rewriteStory();
        break;
      case 'REQUEST_VIDEO':
        this.requestVideo();
        break;
      case 'APPROVE_AND_REQUEST_VIDEO':
        this.approveAndRequestVideo();
        break;
      case 'COMPLETE_VIDEO_DEMO':
        this.completeVideoDemo();
        break;
      case 'SIMULATE_VIDEO_ERROR':
        this.simulateVideoError();
        break;
      case 'SIMULATE_TOP_UP':
        this.snapshot = {
          ...this.snapshot,
          quotaRemaining: this.snapshot.quotaRemaining + command.units,
          quotaTotal: this.snapshot.quotaTotal + command.units,
          message: `Đã mô phỏng thêm ${command.units} lượt. Không phát sinh giao dịch thật.`,
        };
        this.emit();
        break;
      case 'PLAY_VIDEO':
        if (!this.selectedVideoIsReady()) break;
        this.updateCurrentRun(
          (run) => run.videoReady && run.videoVisible ? {...run, stage: 'video-playback'} : run,
          'video-playback',
          'Đã mở placeholder video demo; không có media thật.',
          false,
          false,
        );
        break;
      case 'CONTINUE_AFTER_VIDEO':
        if (!this.requireActiveStage('video-playback', 'Mở video demo trước khi tiếp tục hoạt động.')) break;
        if (!this.selectedVideoIsReady()) break;
        this.updateCurrentRun(
          (run) => ({...run, stage: 'activities'}),
          'activities',
          'Đã chuyển đến hoạt động sau video.',
        );
        break;
      case 'MARK_UNSUITABLE':
        this.markUnsuitable();
        break;
      case 'COMPLETE_RUN':
        if (!this.requireActiveStage('activities', 'Chỉ hoàn tất run sau khi mở hoạt động sau video.')) break;
        this.updateCurrentRun(
          (run) => ({...run, status: 'completed', stage: 'completed'}),
          'home',
          'Run demo đã hoàn tất.',
          true,
        );
        break;
      case 'CANCEL_RUN':
        this.updateCurrentRun(
          (run) => ({...run, status: 'cancelled', stage: 'cancelled'}),
          'home',
          'Run demo đã được hủy.',
          true,
        );
        break;
      case 'OPEN_RUN':
        this.openRun(command.runId);
        break;
      case 'DELETE_RUN':
        this.deleteRun(command.runId);
        break;
      case 'CLEAR_MESSAGE':
        this.snapshot = {...this.snapshot, message: null};
        this.emit();
        break;
      default:
        break;
    }
  }

  private navigate(screen: ParentScreen): void {
    if (!this.snapshot.signedIn && menuScreens.has(screen)) {
      this.setMessage('Đăng nhập demo trước khi mở khu vực này.');
      return;
    }
    if ((screen === 'register' || screen === 'recover' || screen === 'sign-in') && !this.snapshot.signedIn) {
      this.snapshot = {...this.snapshot, screen, message: null};
      this.emit();
      return;
    }
    if ((screen === 'profiles' || screen === 'profile-create') && this.snapshot.signedIn) {
      this.snapshot = {...this.snapshot, screen, message: null};
      this.emit();
      return;
    }
    if (menuScreens.has(screen)) {
      this.snapshot = {...this.snapshot, screen, message: null};
      this.emit();
    }
  }

  private createProfile(label: string, ageMonths: number, gender: ParentProfile['gender']): void {
    if (!Number.isInteger(ageMonths) || ageMonths < 36 || ageMonths > 120) {
      this.setMessage('Độ tuổi demo nằm trong khoảng 36–120 tháng.');
      return;
    }
    const profile: ParentProfile = {
      id: `demo-profile-${String(this.profileSequence++).padStart(2, '0')}`,
      label: label.trim() || 'Hồ sơ demo mới',
      ageMonths,
      gender,
    };
    this.snapshot = {
      ...this.snapshot,
      profiles: [...this.snapshot.profiles, profile],
      selectedProfileId: profile.id,
      screen: 'home',
      message: 'Hồ sơ chỉ được lưu trong bộ nhớ demo.',
    };
    this.emit();
  }

  private startRun(): void {
    const selectedProfileId = this.snapshot.selectedProfileId;
    if (!selectedProfileId) {
      this.snapshot = {...this.snapshot, screen: 'profiles', message: 'Chọn hồ sơ demo trước.'};
      this.emit();
      return;
    }
    const activeRun = this.activeRun();
    if (activeRun) {
      this.snapshot = {
        ...this.snapshot,
        selectedProfileId: activeRun.childProfileId,
        selectedRunId: activeRun.id,
        screen: stageScreen[activeRun.stage],
        message: 'Đang có một run demo cần tiếp tục.',
      };
      this.emit();
      return;
    }
    const run = createDemoRun(`demo-run-${String(this.runSequence++).padStart(3, '0')}`, selectedProfileId);
    this.snapshot = {
      ...this.snapshot,
      runs: [run, ...this.snapshot.runs],
      activeRunId: run.id,
      selectedRunId: run.id,
      guideRequested: false,
      screen: 'drawing',
      message: 'Run mới là dữ liệu demo; chưa có yêu cầu nào gửi tới API.',
    };
    this.emit();
  }

  private continueRun(): void {
    const run = this.activeRun();
    if (!run) {
      this.setMessage('Không có run demo đang hoạt động.');
      return;
    }
    this.snapshot = {...this.snapshot, selectedProfileId: run.childProfileId, selectedRunId: run.id, screen: stageScreen[run.stage], message: null};
    this.emit();
  }

  private simulateUploadInterruption(): void {
    const run = this.activeRun();
    if (!run || run.stage !== 'upload') {
      this.setMessage('Mô phỏng upload chỉ khả dụng sau khi chọn tranh.');
      return;
    }
    this.updateCurrentRun(
      (current) => ({...current, uploadInterrupted: true}),
      'upload',
      'Mạng demo bị ngắt. Session được giữ để thử tiếp tục upload.',
    );
  }

  private resumeUpload(): void {
    const run = this.activeRun();
    if (!run || run.stage !== 'upload' || !run.uploadInterrupted) {
      this.setMessage('Không có upload demo bị ngắt để tiếp tục.');
      return;
    }
    this.updateCurrentRun(
      (current) => ({...current, uploadInterrupted: false, uploadResumeCount: current.uploadResumeCount + 1}),
      'upload',
      'Đã tiếp tục session upload demo. Chưa truyền bytes thật.',
    );
  }

  private completeUpload(): void {
    const run = this.activeRun();
    if (!run || run.stage !== 'upload' || run.uploadInterrupted) {
      this.setMessage('Tiếp tục upload demo trước khi sang bước rà soát.');
      return;
    }
    this.updateCurrentRun(
      (current) => ({...current, stage: 'transcript-review'}),
      'transcript-review',
      'Upload demo hoàn tất. Asset chưa được tạo hoặc gửi tới API.',
    );
  }

  private confirmSubject(subject: string): void {
    if (!subject.trim()) {
      this.setMessage('Nhập hoặc xác nhận chủ thể tranh trước khi tiếp tục.');
      return;
    }
    this.updateCurrentRun(
      (run) => ({
        ...run,
        subject: subject.trim(),
        subjectRevision: subject.trim() === run.subject ? run.subjectRevision : run.subjectRevision + 1,
        subjectConfirmed: true,
        contextApproved: subject.trim() === run.subject ? run.contextApproved : false,
        scriptConfirmed: subject.trim() === run.subject ? run.scriptConfirmed : false,
        videoRequested: subject.trim() === run.subject ? run.videoRequested : false,
        videoReady: subject.trim() === run.subject ? run.videoReady : false,
        videoError: subject.trim() === run.subject ? run.videoError : false,
        videoVisible: subject.trim() === run.subject ? run.videoVisible : false,
        replacementRequested: subject.trim() === run.subject ? run.replacementRequested : false,
        stage: 'context-review',
      }),
      'context-review',
      'Đã xác nhận chủ thể demo. Chỉnh sửa tạo revision demo mới.',
    );
  }

  private rewriteStory(): void {
    const run = this.activeRun();
    if (!run || run.stage !== 'story-review') {
      this.setMessage('Mở bước rà soát story trước khi viết lại.');
      return;
    }
    if (run.rewriteCount >= 3) {
      this.setMessage('Đã dùng hết ba lần viết lại demo.');
      return;
    }
    const rewriteCount = run.rewriteCount + 1;
    const title = DEMO_STORY_TITLES[rewriteCount % DEMO_STORY_TITLES.length];
    this.updateCurrentRun(
      (current) => ({
        ...current,
        title,
        storyTitle: title,
        storyRevision: current.storyRevision + 1,
        rewriteCount,
        scriptConfirmed: false,
      }),
      'story-review',
      `Đã tạo bản viết lại demo ${rewriteCount} / 3.`,
    );
  }

  private approveAndRequestVideo(): void {
    const run = this.activeRun();
    if (!run || run.stage !== 'story-review') {
      this.setMessage('Mở bước rà soát kịch bản trước khi xác nhận tạo video.');
      return;
    }
    if (run.videoRequested && !run.replacementRequested) {
      this.setMessage('Yêu cầu video đã được nhận. Hãy tiếp tục theo dõi trạng thái.');
      return;
    }
    if (this.snapshot.quotaRemaining <= 0) {
      this.setMessage('Đã hết lượt demo. Kịch bản chưa được duyệt và chưa gửi yêu cầu video.');
      return;
    }
    if (run.replacementRequested && run.regenerationCount >= 2) {
      this.setMessage('Đã hết hai lượt tạo lại demo.');
      return;
    }
    this.updateCurrentRun(
      (current) => ({
        ...current,
        stage: 'video-status',
        scriptConfirmed: true,
        videoRequested: true,
        videoReady: false,
        videoError: false,
        videoVisible: false,
        replacementRequested: false,
        regenerationCount: current.replacementRequested
          ? current.regenerationCount + 1
          : current.regenerationCount,
      }),
      'video-status',
      'Kịch bản đã được duyệt và yêu cầu demo đã nhận. Đang kiểm tra trạng thái video.',
      false,
      true,
      1,
    );
  }

  private requestVideo(): void {
    const run = this.activeRun();
    if (!run || run.stage !== 'video-status' || !run.scriptConfirmed) {
      this.setMessage('Xác nhận script trước khi tạo video demo.');
      return;
    }
    if (run.videoReady) {
      this.setMessage('Video demo đã sẵn sàng.');
      return;
    }
    if (run.videoRequested && !run.videoError) {
      this.setMessage('Yêu cầu video đã được nhận. Không gửi thêm yêu cầu cho cùng run.');
      return;
    }
    if (!run.videoRequested && this.snapshot.quotaRemaining <= 0) {
      this.setMessage('Đã hết quota demo. Chưa gửi yêu cầu tạo video.');
      return;
    }
    if (run.replacementRequested && run.regenerationCount >= 2) {
      this.setMessage('Đã hết hai lượt tạo lại demo.');
      return;
    }
    this.updateCurrentRun(
      (current) => ({
        ...current,
        stage: 'video-status',
        videoRequested: true,
        videoReady: false,
        videoError: false,
        videoVisible: false,
        replacementRequested: false,
        regenerationCount: current.replacementRequested
          ? current.regenerationCount + 1
          : current.regenerationCount,
      }),
      'video-status',
      'Đã tiếp tục xử lý video demo. Không phát sinh yêu cầu trùng cho run này.',
      false,
      true,
      run.videoRequested ? 0 : 1,
    );
  }

  private completeVideoDemo(): void {
    const run = this.activeRun();
    if (!run || run.stage !== 'video-status' || !run.videoRequested || run.videoError) {
      this.setMessage('Chỉ mô phỏng VIDEO_READY sau khi yêu cầu video được tiếp nhận.');
      return;
    }
    this.updateCurrentRun(
      (current) => ({...current, videoReady: true, videoVisible: true, videoError: false}),
      'video-status',
      'Kiểm tra demo hoàn tất. Video placeholder đã sẵn sàng để mở.',
    );
  }

  private simulateVideoError(): void {
    const run = this.activeRun();
    if (!run || run.stage !== 'video-status' || !run.videoRequested || run.videoReady) {
      this.setMessage('Mô phỏng lỗi chỉ khả dụng trước khi video demo sẵn sàng.');
      return;
    }
    this.updateCurrentRun(
      (current) => ({...current, videoError: true}),
      'video-status',
      'Video demo gặp lỗi sau khi đã nhận yêu cầu. Có thể thử lại trong run này; không tạo yêu cầu trùng.',
    );
  }

  private markUnsuitable(): void {
    const run = this.activeRun();
    if (!run || (run.stage !== 'video-status' && run.stage !== 'video-playback') || !run.videoReady) {
      this.setMessage('Chỉ có thể đánh dấu video demo sau khi trạng thái sẵn sàng.');
      return;
    }
    if (run.regenerationCount >= 2) {
      this.setMessage('Đã hết hai lượt tạo lại demo.');
      return;
    }
    this.updateCurrentRun(
      (current) => ({...current, stage: 'story-review', scriptConfirmed: false, videoRequested: false, videoReady: false, videoVisible: false, replacementRequested: true}),
      'story-review',
      'Đã quay lại rà soát story. Video cũ sẽ bị ẩn khi yêu cầu thay thế được nhận.',
    );
  }

  private openRun(runId: string): void {
    const run = this.snapshot.runs.find((candidate) => candidate.id === runId);
    if (!run) {
      this.setMessage('Không tìm thấy run demo này.');
      return;
    }
    this.snapshot = {
      ...this.snapshot,
      activeRunId: run.status === 'active' ? run.id : null,
      selectedRunId: run.id,
      selectedProfileId: run.childProfileId,
      screen: stageScreen[run.stage],
      message: null,
    };
    this.emit();
  }

  private deleteRun(runId: string): void {
    const wasActive = this.snapshot.activeRunId === runId;
    this.snapshot = {
      ...this.snapshot,
      runs: this.snapshot.runs.filter((run) => run.id !== runId),
      activeRunId: wasActive ? null : this.snapshot.activeRunId,
      selectedRunId: this.snapshot.selectedRunId === runId ? null : this.snapshot.selectedRunId,
      screen: wasActive ? 'home' : this.snapshot.screen,
      message: 'Đã xóa run khỏi lịch sử demo.',
    };
    this.emit();
  }

  private goBack(): void {
    const backTarget: Partial<Record<ParentScreen, ParentScreen>> = {
      register: 'sign-in',
      recover: 'sign-in',
      profiles: 'sign-in',
      'profile-create': 'profiles',
      home: 'home',
      drawing: 'home',
      upload: 'drawing',
      'transcript-review': 'upload',
      'subject-review': 'transcript-review',
      'context-review': 'subject-review',
      'story-review': 'context-review',
      'video-status': 'story-review',
      'video-playback': 'video-status',
      activities: 'video-playback',
      history: 'home',
      notifications: 'home',
      quota: 'home',
      settings: 'home',
    };
    const runScreens: readonly ParentScreen[] = ['drawing', 'upload', 'transcript-review', 'subject-review', 'context-review', 'story-review', 'video-status', 'video-playback', 'activities'];
    const selectedRun = this.selectedRun();
    const returnToHistory = selectedRun?.status === 'completed' && runScreens.includes(this.snapshot.screen);
    const nextScreen = returnToHistory ? 'history' : backTarget[this.snapshot.screen] ?? 'home';
    const stageForScreen: Partial<Record<ParentScreen, ParentRunStage>> = {
      drawing: 'drawing',
      upload: 'upload',
      'transcript-review': 'transcript-review',
      'subject-review': 'subject-review',
      'context-review': 'context-review',
      'story-review': 'story-review',
      'video-status': 'video-status',
      'video-playback': 'video-playback',
      activities: 'activities',
    };
    const activeRun = this.activeRun();
    const nextStage = stageForScreen[nextScreen];
    const preserveAcceptedVideoRequest = Boolean(
      activeRun?.videoRequested && activeRun.stage === 'video-status' && nextScreen === 'story-review',
    );
    this.snapshot = {
      ...this.snapshot,
      runs: activeRun && nextStage && !preserveAcceptedVideoRequest
        ? this.snapshot.runs.map((run) => run.id === activeRun.id ? {...run, stage: nextStage} : run)
        : this.snapshot.runs,
      screen: nextScreen,
      message: null,
    };
    this.emit();
  }

  private updateCurrentRun(
    update: (run: ParentRun) => ParentRun,
    screen?: ParentScreen,
    message?: string,
    closeActive = false,
    requireActive = true,
    quotaCost = 0,
  ): void {
    const run = requireActive ? this.activeRun() : this.selectedRun();
    if (!run) {
      this.setMessage('Không có run demo đang mở.');
      return;
    }
    this.snapshot = {
      ...this.snapshot,
      runs: this.snapshot.runs.map((candidate) => candidate.id === run.id ? update(candidate) : candidate),
      activeRunId: closeActive ? null : this.snapshot.activeRunId,
      quotaRemaining: Math.max(0, this.snapshot.quotaRemaining - quotaCost),
      screen: screen ?? this.snapshot.screen,
      message: message ?? null,
    };
    this.emit();
  }

  private requireActiveStage(stage: ParentRunStage, message: string): boolean {
    const run = this.activeRun();
    if (!run || run.stage !== stage) {
      this.setMessage(message);
      return false;
    }
    return true;
  }

  private selectedVideoIsReady(): boolean {
    const run = this.selectedRun();
    if (!run || !run.videoReady || !run.videoVisible) {
      this.setMessage('Video demo chưa sẵn sàng để mở playback.');
      return false;
    }
    return true;
  }

  private activeRun(): ParentRun | undefined {
    if (!this.snapshot.activeRunId) return undefined;
    return this.snapshot.runs.find((run) => run.id === this.snapshot.activeRunId && run.status === 'active');
  }

  private selectedRun(): ParentRun | undefined {
    if (!this.snapshot.selectedRunId) return undefined;
    return this.snapshot.runs.find((run) => run.id === this.snapshot.selectedRunId);
  }

  private setMessage(message: string): void {
    this.snapshot = {...this.snapshot, message};
    this.emit();
  }

  private emit(): void {
    for (const listener of this.listeners) listener();
  }
}
