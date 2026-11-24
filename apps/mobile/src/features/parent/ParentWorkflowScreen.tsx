import React, {useEffect, useMemo, useRef, useState} from 'react';
import {
  Alert,
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
import {launchCamera, launchImageLibrary} from 'react-native-image-picker';

import type {AuthSessionPort} from '../../infrastructure/auth/AuthSessionPort';
import {
  ParentWorkflowApi,
  ParentWorkflowApiError,
  type ParentCandidate,
  type ParentActivitySuggestion,
  type ParentAiReceipt,
  type ParentConsentPolicy,
  type ParentLessonDetail,
  type ParentLessonPinSnapshot,
  type ParentLessonSummary,
  type ParentProfile,
  type ParentStoryRun,
} from '../../infrastructure/api/parentWorkflowApi';

type Props = Readonly<{auth: AuthSessionPort}>;
type DrawingMediaType = 'image/jpeg' | 'image/png';
type SelectedDrawing = Readonly<{
  uri: string;
  base64: string;
  mediaType: DrawingMediaType;
}>;
type StoryScene = Readonly<{
  scene_index: number;
  title: string;
  action: string;
  narration: string;
  start_ms: number;
  duration_ms: number;
}>;
type ParentStoryDraft = Readonly<{
  schema_version: 'sketch2life.story-revision.v1';
  language: 'vi';
  title: string;
  story: Readonly<{opening: string; middle: string; ending: string}>;
  duration_ms: number;
  scenes: readonly StoryScene[];
}>;

const MAX_IMAGE_BASE64_CHARS = 6_700_000;
const PICKER_IMAGE_OPTIONS = {
  mediaType: 'photo' as const,
  includeBase64: true,
  maxWidth: 1600,
  maxHeight: 1600,
  quality: 0.8 as const,
};

export function ParentWorkflowScreen({auth}: Props): React.JSX.Element {
  const api = useMemo(() => new ParentWorkflowApi(auth), [auth]);
  const [profiles, setProfiles] = useState<ParentProfile[]>([]);
  const [policy, setPolicy] = useState<ParentConsentPolicy | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState('');
  const [editingProfileId, setEditingProfileId] = useState<string | null>(null);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [ageMonths, setAgeMonths] = useState('72');
  const [interestsSummary, setInterestsSummary] = useState('');
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [reconsentProfileId, setReconsentProfileId] = useState('');
  const [reconsentAccepted, setReconsentAccepted] = useState(false);
  const [topic, setTopic] = useState('');
  const [adultIdea, setAdultIdea] = useState('');
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [lessons, setLessons] = useState<ParentLessonSummary[]>([]);
  const [selectedLesson, setSelectedLesson] = useState<ParentLessonDetail | ParentLessonPinSnapshot | null>(null);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [lessonLoadingId, setLessonLoadingId] = useState('');
  const [guideEnabled, setGuideEnabled] = useState(false);
  const [guide, setGuide] = useState<string | null>(null);
  const [drawing, setDrawing] = useState<SelectedDrawing | null>(null);
  const [run, setRun] = useState<ParentStoryRun | null>(null);
  const [candidate, setCandidate] = useState<ParentCandidate | null>(null);
  const [confirmedSubject, setConfirmedSubject] = useState('');
  const [subjectConfirmed, setSubjectConfirmed] = useState(false);
  const [understandingRevision, setUnderstandingRevision] = useState(0);
  const [story, setStory] = useState<ParentStoryDraft | null>(null);
  const [storySha256, setStorySha256] = useState('');
  const [storyConfirmed, setStoryConfirmed] = useState(false);
  const [activitySuggestions, setActivitySuggestions] = useState<ParentActivitySuggestion[]>([]);
  const [activitySource, setActivitySource] = useState<'PINNED_LESSON' | 'QWEN3_5_MODAL' | ''>('');
  const [activityLoading, setActivityLoading] = useState(false);
  const [activityError, setActivityError] = useState('');
  const [activitySkipped, setActivitySkipped] = useState(false);
  const [activityUnknown, setActivityUnknown] = useState(false);
  const activitySkipRef = useRef(false);
  const [rewriteInstruction, setRewriteInstruction] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [lastRequestId, setLastRequestId] = useState('');

  const selectedProfile = profiles.find((profile) => profile.parent_profile_id === selectedProfileId) ?? null;
  const outcomeUnknown = run?.job_state === 'AWAITING_RECONCILIATION';
  const aiPending = run?.job_state === 'RUNNING' || outcomeUnknown;
  const visibleFeatures = candidate?.visible_features ?? [];

  useEffect(() => {
    let mounted = true;
    void (async () => {
      const [profileResult, policyResult, activeRunResult] = await Promise.allSettled([
        api.listProfiles(),
        api.getConsentPolicy(),
        api.getActiveStoryRun(),
      ]);
      if (!mounted) return;
      if (profileResult.status === 'fulfilled') {
        const activeProfiles = profileResult.value.profiles.filter((profile) => profile.state === 'ACTIVE');
        setProfiles(activeProfiles);
        if (activeProfiles.length > 0) {
          setSelectedProfileId(activeProfiles[0].parent_profile_id);
        } else {
          setShowProfileForm(true);
        }
      } else {
        showFailure(profileResult.reason, 'Không tải được hồ sơ trẻ.');
      }
      if (policyResult.status === 'fulfilled') {
        setPolicy(policyResult.value.policy);
      } else {
        showFailure(policyResult.reason, 'Không tải được thông tin đồng ý xử lý dữ liệu.');
      }
      if (activeRunResult.status === 'fulfilled' && activeRunResult.value.story_run) {
        const savedRun = activeRunResult.value.story_run;
        setRun(savedRun);
        setSelectedProfileId(savedRun.parent_profile_id);
        setTopic(savedRun.context_snapshot.topic);
        setAdultIdea(savedRun.context_snapshot.adult_confirmed_idea);
        setSelectedLesson(savedRun.lesson_pin_snapshot);
        setCandidate(savedRun.candidate);
        setConfirmedSubject(savedRun.subject_label ?? savedRun.candidate?.candidate_subject ?? '');
        setUnderstandingRevision(savedRun.understanding_revision ?? 0);
        setSubjectConfirmed(
          savedRun.run_state === 'PREPARATION_REVIEW'
          || savedRun.run_state === 'SCRIPT_GENERATING'
          || savedRun.run_state === 'SCRIPT_GENERATION_UNKNOWN'
          || savedRun.run_state === 'SCRIPT_REVIEW'
          || savedRun.run_state === 'COMPLETED',
        );
        const restoredStory = parseParentStoryDraft(savedRun.story);
        setStory(restoredStory);
        setStorySha256(savedRun.story_sha256 ?? '');
        setStoryConfirmed(savedRun.story_status === 'CONFIRMED');
        setNotice('Đã khôi phục buổi học đang lưu trên tài khoản của bạn.');
      } else if (activeRunResult.status === 'rejected') {
        showFailure(activeRunResult.reason, 'Không kiểm tra được buổi học đang lưu.');
      }
    })();
    return () => {
      mounted = false;
    };
  }, [api]);

  function showFailure(cause: unknown, fallback: string) {
    if (cause instanceof ParentWorkflowApiError) {
      setError(cause.message);
      if (cause.requestId) setLastRequestId(cause.requestId);
      return;
    }
    setError(cause instanceof Error ? cause.message : fallback);
  }

  function syncRun(savedRun: ParentStoryRun) {
    setRun(savedRun);
    setTopic(savedRun.context_snapshot.topic);
    setAdultIdea(savedRun.context_snapshot.adult_confirmed_idea);
    setSelectedLesson(savedRun.lesson_pin_snapshot);
    setCandidate(savedRun.candidate);
    setConfirmedSubject(savedRun.subject_label ?? savedRun.candidate?.candidate_subject ?? '');
    setUnderstandingRevision(savedRun.understanding_revision ?? 0);
    setStory(parseParentStoryDraft(savedRun.story));
    setStorySha256(savedRun.story_sha256 ?? '');
    setStoryConfirmed(savedRun.story_status === 'CONFIRMED');
    setSubjectConfirmed(
      savedRun.run_state === 'PREPARATION_REVIEW'
      || savedRun.run_state === 'SCRIPT_GENERATING'
      || savedRun.run_state === 'SCRIPT_GENERATION_UNKNOWN'
      || savedRun.run_state === 'SCRIPT_REVIEW'
      || savedRun.run_state === 'COMPLETED',
    );
  }

  async function refreshRun() {
    if (!run) return;
    try {
      const result = await api.getStoryRun(run.run_id);
      syncRun(result.story_run);
      setLastRequestId(result.request_id);
      setNotice('Đã tải lại trạng thái đã lưu.');
    } catch (cause) {
      showFailure(cause, 'Không tải lại được trạng thái buổi học.');
    }
  }

  function resetWorkflow() {
    setRun(null);
    setDrawing(null);
    setCandidate(null);
    setConfirmedSubject('');
    setSubjectConfirmed(false);
    setUnderstandingRevision(0);
    setStory(null);
    setStorySha256('');
    setStoryConfirmed(false);
    setActivitySuggestions([]);
    setActivitySource('');
    setActivityLoading(false);
    setActivityError('');
    setActivitySkipped(false);
    setActivityUnknown(false);
    activitySkipRef.current = false;
    setRewriteInstruction('');
    setGuide(null);
  }

  function beginEditProfile(profile: ParentProfile) {
    setEditingProfileId(profile.parent_profile_id);
    setShowProfileForm(true);
    setDisplayName(profile.current_revision.display_name);
    setAgeMonths(String(profile.current_revision.age_months));
    setInterestsSummary(profile.current_revision.interests_summary);
    setConsentAccepted(false);
  }

  async function saveProfile() {
    setError('');
    setNotice('');
    const age = Number(ageMonths);
    if (!Number.isInteger(age) || age < 36 || age > 120) {
      setError('Nhập độ tuổi từ 36 đến 120 tháng.');
      return;
    }
    if (!displayName.trim()) {
      setError('Nhập tên gọi để nhận biết hồ sơ trẻ.');
      return;
    }
    if (editingProfileId) {
      const profile = profiles.find((item) => item.parent_profile_id === editingProfileId);
      if (!profile) return;
      setBusy('profile');
      try {
        const result = await api.updateProfile(profile, {
          age_months: age,
          display_name: displayName.trim(),
          interests_summary: interestsSummary.trim(),
        });
        setProfiles((items) => items.map((item) => item.parent_profile_id === editingProfileId ? result.profile : item));
        if (run?.parent_profile_id === editingProfileId) {
          setNotice('Đã lưu revision hồ sơ mới. Buổi đang mở vẫn dùng snapshot revision cũ.');
        } else {
          setNotice('Đã lưu revision hồ sơ mới.');
        }
        setEditingProfileId(null);
        setShowProfileForm(false);
      } catch (cause) {
        showFailure(cause, 'Không lưu được thay đổi hồ sơ.');
      } finally {
        setBusy('');
      }
      return;
    }
    if (!policy || !consentAccepted) {
      setError('Đọc nội dung và xác nhận đồng ý trước khi tạo hồ sơ.');
      return;
    }
    setBusy('profile');
    try {
      const result = await api.createProfile({
        age_months: age,
        display_name: displayName.trim(),
        interests_summary: interestsSummary.trim(),
        consent_accepted: true,
        consent_policy_version: policy.policy_version,
      });
      setProfiles((items) => [result.profile, ...items]);
      setSelectedProfileId(result.profile.parent_profile_id);
      setNotice('Đã tạo hồ sơ và lưu xác nhận quyền xử lý dữ liệu.');
      setShowProfileForm(false);
      setDisplayName('');
      setInterestsSummary('');
      setConsentAccepted(false);
    } catch (cause) {
      showFailure(cause, 'Không tạo được hồ sơ trẻ.');
    } finally {
      setBusy('');
    }
  }

  async function grantAuthorization(profile: ParentProfile) {
    if (!policy) {
      setError('Chưa tải được policy đồng ý. Kiểm tra cấu hình .env gốc.');
      return;
    }
    if (reconsentProfileId !== profile.parent_profile_id || !reconsentAccepted) {
      setError('Đọc policy và xác nhận đồng ý trước khi cấp quyền lại.');
      return;
    }
    setBusy('consent');
    setError('');
    try {
      const result = await api.grantAuthorization(profile.parent_profile_id, policy.policy_version);
      setProfiles((items) => items.map((item) => item.parent_profile_id === profile.parent_profile_id ? result.profile : item));
      setReconsentProfileId('');
      setReconsentAccepted(false);
      setNotice('Đã lưu xác nhận cho policy hiện hành.');
    } catch (cause) {
      showFailure(cause, 'Không lưu được xác nhận.');
    } finally {
      setBusy('');
    }
  }

  async function revokeAuthorization(profile: ParentProfile) {
    setBusy('consent');
    setError('');
    try {
      const result = await api.revokeAuthorization(profile.parent_profile_id);
      setProfiles((items) => items.map((item) => item.parent_profile_id === profile.parent_profile_id ? result.profile : item));
      setNotice('Đã thu hồi quyền. Hệ thống sẽ chặn các lần tạo run và gọi AI mới cho hồ sơ này.');
    } catch (cause) {
      showFailure(cause, 'Không thu hồi được quyền.');
    } finally {
      setBusy('');
    }
  }

  function archiveProfile(profile: ParentProfile) {
    Alert.alert(
      'Lưu trữ hồ sơ?',
      'Hồ sơ sẽ không dùng để tạo buổi mới và các quyền đang cấp sẽ bị thu hồi.',
      [
        {text: 'Hủy', style: 'cancel'},
        {
          text: 'Lưu trữ',
          style: 'destructive',
          onPress: () => {
            void (async () => {
              setBusy('profile');
              try {
                await api.archiveProfile(profile.parent_profile_id);
                setProfiles((items) => items.filter((item) => item.parent_profile_id !== profile.parent_profile_id));
                if (selectedProfileId === profile.parent_profile_id) setSelectedProfileId('');
                setNotice('Đã lưu trữ hồ sơ.');
              } catch (cause) {
                showFailure(cause, 'Không lưu trữ được hồ sơ.');
              } finally {
                setBusy('');
              }
            })();
          },
        },
      ],
    );
  }

  async function toggleGallery() {
    if (run) return;
    if (galleryOpen) {
      setGalleryOpen(false);
      return;
    }
    setError('');
    setGalleryLoading(true);
    try {
      const result = await api.listParentLessons();
      setLessons(result.items);
      setGalleryOpen(true);
      setNotice(result.items.length ? 'Chọn một bài học để áp dụng, hoặc tiếp tục không chọn.' : 'Thư viện hiện chưa có bài học được chia sẻ hoặc công khai.');
    } catch (cause) {
      showFailure(cause, 'Không tải được thư viện bài học. Bạn vẫn có thể tiếp tục mà không chọn giáo án.');
    } finally {
      setGalleryLoading(false);
    }
  }

  async function selectLesson(summary: ParentLessonSummary) {
    setError('');
    setLessonLoadingId(summary.lesson_id);
    try {
      const lesson = await api.getParentLesson(summary.lesson_id);
      if (lesson.version_id !== summary.version_id) {
        setError('Bài học vừa được cập nhật. Hãy tải lại Gallery rồi chọn phiên bản mới nhất.');
        return;
      }
      setSelectedLesson(lesson);
      if (!topic.trim()) setTopic(lesson.topic);
      setGalleryOpen(false);
      setNotice(`Đã chọn “${lesson.title}” · phiên bản ${lesson.version_no}.`);
    } catch (cause) {
      showFailure(cause, 'Không mở được bài học này. Hãy tải lại Gallery hoặc tiếp tục không chọn.');
    } finally {
      setLessonLoadingId('');
    }
  }

  async function createRun(): Promise<ParentStoryRun> {
    setError('');
    if (!selectedProfile || !selectedProfile.authorization_current) {
      throw new Error('Chọn hồ sơ có quyền xử lý dữ liệu đang hiệu lực.');
    }
    if (!policy) throw new Error('Chưa tải được quyền xử lý dữ liệu hiện hành.');
    const result = await api.createStoryRun({
      parent_profile_id: selectedProfile.parent_profile_id,
      expected_profile_revision_id: selectedProfile.current_revision.profile_revision_id,
      consent_policy_version: policy.policy_version,
      topic: topic.trim(),
      adult_confirmed_idea: adultIdea.trim(),
      context_confirmed: true,
      ...(selectedLesson ? {lesson_id: selectedLesson.lesson_id, lesson_version_id: selectedLesson.version_id} : {}),
    });
    setRun(result.story_run);
    setSelectedProfileId(result.story_run.parent_profile_id);
    setLastRequestId(result.request_id);
    setNotice('Đã lưu snapshot hồ sơ và các lựa chọn tùy chọn.');
    return result.story_run;
  }

  async function createGuide() {
    setError('');
    setNotice('');
    if (!guideEnabled) return;
    if (!topic.trim()) {
      setError('Nhập chủ đề trước khi tạo gợi ý vẽ.');
      return;
    }
    setBusy('guide');
    try {
      const response = await api.generateSketchGuide({topic: topic.trim(), difficulty: 'beginner', step_count: 3});
      setGuide(response.image_base64 ?? null);
      setLastRequestId(response.request_id);
      setNotice('Đã tạo gợi ý vẽ chung. Có thể bỏ qua để trẻ tự vẽ.');
    } catch (cause) {
      showFailure(cause, 'Không thể tạo gợi ý vẽ.');
    } finally {
      setBusy('');
    }
  }

  async function chooseDrawing(source: 'camera' | 'library') {
    setError('');
    setNotice('');
    try {
      const response = source === 'camera'
        ? await launchCamera({...PICKER_IMAGE_OPTIONS, cameraType: 'back', saveToPhotos: false})
        : await launchImageLibrary({...PICKER_IMAGE_OPTIONS, selectionLimit: 1});
      if (response.didCancel) {
        setNotice('Đã hủy chọn ảnh.');
        return;
      }
      if (response.errorCode) {
        setError(imagePickerErrorMessage(response.errorCode));
        return;
      }
      const asset = response.assets?.[0];
      const mediaType = asset ? resolveDrawingMediaType(asset.type, asset.fileName) : null;
      if (!asset?.uri || !asset.base64 || !mediaType) {
        setError('Chọn ảnh JPG hoặc PNG rõ nét từ tranh trẻ đã vẽ trên giấy.');
        return;
      }
      if (asset.base64.length > MAX_IMAGE_BASE64_CHARS) {
        setError('Ảnh quá lớn để gửi. Hãy chụp lại gần hơn hoặc chọn ảnh nhỏ hơn.');
        return;
      }
      setDrawing({uri: asset.uri, base64: asset.base64, mediaType});
      setCandidate(null);
      setSubjectConfirmed(false);
      setStory(null);
      setStoryConfirmed(false);
      setNotice('Đã chọn tranh trên giấy. Xem lại ảnh rồi gửi để nhận diện chủ thể.');
    } catch (cause) {
      showFailure(cause, 'Không mở được camera hoặc thư viện ảnh.');
    }
  }

  async function analyzeDrawing() {
    setError('');
    setNotice('');
    if (!drawing) {
      setError('Chụp hoặc chọn ảnh tranh trên giấy trước khi tiếp tục.');
      return;
    }
    setBusy('drawing');
    let activeRun = run;
    try {
      activeRun = activeRun ?? await createRun();
      const response = await api.analyzeDrawing(activeRun.run_id, drawing.base64, drawing.mediaType);
      if (!response.candidate || response.candidate.adult_confirmation_required !== true) {
        throw new Error('Backend không trả về đề xuất cần người lớn xác nhận.');
      }
      setCandidate(response.candidate);
      setConfirmedSubject(response.candidate.candidate_subject ?? '');
      setUnderstandingRevision(response.understanding_revision ?? 0);
      setSubjectConfirmed(false);
      setStory(null);
      setStorySha256('');
      setStoryConfirmed(false);
      setLastRequestId(response.request_id);
      const current = await api.getStoryRun(activeRun.run_id);
      setRun(current.story_run);
      setNotice('AI đã gợi ý chủ thể. Người lớn cần xác nhận hoặc sửa trước khi tạo kịch bản.');
    } catch (cause) {
      showFailure(cause, 'Không thể phân tích tranh.');
      const current = activeRun ? await api.getStoryRun(activeRun.run_id).catch(() => null) : null;
      if (current) syncRun(current.story_run);
    } finally {
      setBusy('');
    }
  }

  async function confirmSubject() {
    setError('');
    setNotice('');
    if (!run || !candidate || !confirmedSubject.trim() || !visibleFeatures.length || understandingRevision < 1) {
      setError('Cần có chủ thể và đặc điểm nhìn thấy trước khi xác nhận.');
      return;
    }
    setBusy('subject');
    try {
      const result = await api.confirmSubject(run.run_id, understandingRevision, confirmedSubject.trim());
      setUnderstandingRevision(result.understanding_revision);
      setSubjectConfirmed(true);
      const current = await api.getStoryRun(run.run_id);
      setRun(current.story_run);
      setCandidate(current.story_run.candidate ?? candidate);
      setNotice('Đã lưu xác nhận chủ thể.');
      void loadActivitySuggestions(current.story_run);
    } catch (cause) {
      showFailure(cause, 'Không lưu được xác nhận chủ thể.');
      const current = await api.getStoryRun(run.run_id).catch(() => null);
      if (current) {
        syncRun(current.story_run);
        setError('');
        setNotice('Đã tải lại trạng thái xác nhận từ máy chủ.');
      }
    } finally {
      setBusy('');
    }
  }

  async function loadActivitySuggestions(activeRun: ParentStoryRun | null = run) {
    if (!activeRun || !understandingRevision) return;
    activitySkipRef.current = false;
    setActivitySkipped(false);
    setActivityUnknown(false);
    setActivityError('');
    setActivityLoading(true);
    try {
      const result = await api.suggestActivities(activeRun.run_id, activeRun.understanding_revision ?? understandingRevision);
      if (activitySkipRef.current) return;
      setActivitySuggestions(result.activities);
      setActivitySource(result.source);
      setLastRequestId(result.request_id);
    } catch (cause) {
      const code = cause instanceof ParentWorkflowApiError ? cause.code : '';
      setActivityUnknown(code === 'MODAL_OUTCOME_UNKNOWN' || code === 'REQUEST_OUTCOME_UNKNOWN');
      setActivityError(cause instanceof Error ? cause.message : 'Không tải được gợi ý hoạt động.');
    } finally {
      setActivityLoading(false);
    }
  }

  function skipActivitySuggestions() {
    activitySkipRef.current = true;
    setActivitySkipped(true);
    setActivityLoading(false);
    setActivityError('');
  }

  async function generateStory(rewrite = '') {
    setError('');
    setNotice('');
    if (!run || !subjectConfirmed || understandingRevision < 1) {
      setError('Xác nhận chủ thể trước khi tạo kịch bản.');
      return;
    }
    setBusy('story');
    try {
      const response: ParentAiReceipt<unknown> = await api.generateStory(
        run.run_id,
        understandingRevision,
        rewrite.trim() || undefined,
      );
      const draft = parseParentStoryDraft(response.story);
      if (!draft || !response.review_required || !response.story_sha256) {
        throw new Error('Backend trả về kịch bản chưa đúng hợp đồng duyệt.');
      }
      setStory(draft);
      setStorySha256(response.story_sha256);
      if (response.story_run) syncRun(response.story_run);
      setStoryConfirmed(false);
      setRewriteInstruction('');
      setLastRequestId(response.request_id);
      setNotice('Đã lưu bản nháp kịch bản. Người lớn cần xem và xác nhận.');
    } catch (cause) {
      showFailure(cause, 'Không thể tạo kịch bản.');
      const current = await api.getStoryRun(run.run_id).catch(() => null);
      if (current) syncRun(current.story_run);
    } finally {
      setBusy('');
    }
  }

  async function confirmStory() {
    if (!run || !story || !storySha256 || !run.story_revision_no) return;
    setBusy('confirm-story');
    setError('');
    try {
      const result = await api.confirmStory(run.run_id, run.story_revision_no, storySha256);
      syncRun(result.story_run);
      setNotice('Đã xác nhận kịch bản và lưu quyết định người lớn.');
    } catch (cause) {
      showFailure(cause, 'Không lưu được xác nhận kịch bản.');
      const current = await api.getStoryRun(run.run_id).catch(() => null);
      if (current) {
        syncRun(current.story_run);
        setError('');
        setNotice('Đã tải lại trạng thái kịch bản từ máy chủ.');
      }
    } finally {
      setBusy('');
    }
  }

  const loading = busy !== '';
  const currentStep = !selectedProfile ? 0 : !run || !candidate ? 1 : !subjectConfirmed ? 2 : activitySkipped || Boolean(activityError) || Boolean(story) || busy === 'story' ? 4 : 3;
  const canCreateRun = Boolean(selectedProfile?.authorization_current && policy);
  const canCapture = !run || (run.current_input_revision ?? 1) <= 1;
  const steps = ['Hồ sơ', 'Chụp tranh', 'Xác nhận', 'Hoạt động', 'Kịch bản'];
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.eyebrow}>SKETCH2LIFE · PHỤ HUYNH</Text>
            <Text style={styles.title}>Bắt đầu từ tranh của con</Text>
            <Text style={styles.subtitle}>Chụp tranh trên giấy trước. Chủ đề và bài học chỉ thêm nếu bạn muốn.</Text>
          </View>
          {run ? <View style={styles.statusPill}><Text style={styles.statusText}>{statusLabel(run.run_state, run.story_status)}</Text></View> : null}
        </View>

        <View style={styles.stepper} accessibilityLabel="Các bước tạo câu chuyện">
          {steps.map((label, index) => (
            <View key={label} style={styles.stepperItem}>
              <View style={[styles.stepperDot, index < currentStep && styles.stepperDotDone, index === currentStep && styles.stepperDotCurrent]}>
                <Text style={[styles.stepperNumber, index <= currentStep && styles.stepperNumberActive]}>{index < currentStep ? '✓' : String(index + 1)}</Text>
              </View>
              <Text style={[styles.stepperLabel, index === currentStep && styles.stepperLabelCurrent]}>{label}</Text>
            </View>
          ))}
        </View>

        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        {notice ? <Text style={styles.notice}>{notice}</Text> : null}
        {lastRequestId ? <Text style={styles.requestId}>Mã yêu cầu: {lastRequestId}</Text> : null}

        <View style={styles.card}>
          <View style={styles.cardHeading}>
            <View style={styles.headingNumber}><Text style={styles.headingNumberText}>1</Text></View>
            <View style={styles.headingCopy}><Text style={styles.sectionTitle}>Hồ sơ trẻ</Text><Text style={styles.helper}>Chọn hồ sơ và quyền xử lý đang hiệu lực.</Text></View>
          </View>
          {profiles.map((profile) => (
            <View key={profile.parent_profile_id} style={styles.profileRow}>
              <Pressable
                accessibilityRole="radio"
                accessibilityState={{checked: selectedProfileId === profile.parent_profile_id}}
                disabled={Boolean(run)}
                style={[styles.profileChoice, selectedProfileId === profile.parent_profile_id && styles.profileChoiceSelected]}
                onPress={() => setSelectedProfileId(profile.parent_profile_id)}>
                <View style={styles.profileCopy}>
                  <Text style={styles.profileName}>{profile.current_revision.display_name}</Text>
                  <Text style={styles.helper}>{ageLabel(profile.current_revision.age_months)} · hồ sơ phiên bản {profile.current_revision.revision}</Text>
                  <Text style={profile.authorization_current ? styles.goodState : styles.pendingState}>
                    {profile.authorization_current ? 'Quyền xử lý đang hiệu lực' : 'Cần xác nhận lại quyền xử lý'}
                  </Text>
                </View>
                <Text style={styles.radioMark}>{selectedProfileId === profile.parent_profile_id ? '●' : '○'}</Text>
              </Pressable>
              <View style={styles.profileActions}>
                <SmallAction label="Sửa" disabled={loading || !profile.authorization_current || Boolean(run && run.parent_profile_id === profile.parent_profile_id)} onPress={() => beginEditProfile(profile)} />
                {!profile.authorization_current ? <SmallAction label="Xem chính sách" disabled={loading || !policy} onPress={() => {setReconsentProfileId(profile.parent_profile_id); setReconsentAccepted(false);}} /> : null}
                {profile.authorization_current ? <SmallAction label="Thu hồi quyền" disabled={loading} onPress={() => void revokeAuthorization(profile)} /> : null}
                <SmallAction label="Lưu trữ" disabled={loading || Boolean(run && run.parent_profile_id === profile.parent_profile_id)} onPress={() => archiveProfile(profile)} danger />
              </View>
              {!profile.authorization_current && selectedProfileId === profile.parent_profile_id && reconsentProfileId === profile.parent_profile_id ? (
                <View style={styles.consentPanel}>
                  <Text style={styles.consentCopy}>{policy?.consent_text ?? 'Chưa cấu hình chính sách đồng ý.'}</Text>
                  <Text style={styles.helper}>Phiên bản {policy?.policy_version ?? 'chưa cấu hình'} · Mục đích: cá nhân hóa câu chuyện</Text>
                  <Pressable style={styles.checkRow} onPress={() => setReconsentAccepted((value) => !value)} accessibilityRole="checkbox" accessibilityState={{checked: reconsentAccepted}}>
                    <Text style={styles.checkBox}>{reconsentAccepted ? '☑' : '□'}</Text><Text style={styles.helper}>Tôi đã đọc và đồng ý theo chính sách này.</Text>
                  </Pressable>
                  <ActionButton label="Cấp quyền theo chính sách hiện hành" disabled={loading || !policy || !reconsentAccepted} onPress={() => void grantAuthorization(profile)} />
                </View>
              ) : null}
            </View>
          ))}
          {!showProfileForm ? <ActionButton label="Tạo hồ sơ trẻ" disabled={loading || Boolean(run)} onPress={() => {setEditingProfileId(null); setShowProfileForm(true);}} secondary /> : null}
          {showProfileForm ? (
            <View style={styles.formBlock}>
              <Text style={styles.label}>{editingProfileId ? 'Sửa hồ sơ · lưu phiên bản mới' : 'Tạo hồ sơ'}</Text>
              <TextInput style={styles.input} value={displayName} onChangeText={setDisplayName} placeholder="Tên gọi trong gia đình" maxLength={120} accessibilityLabel="Tên hồ sơ trẻ" />
              <TextInput style={styles.input} value={ageMonths} onChangeText={setAgeMonths} placeholder="Tuổi theo tháng, 36–120" keyboardType="number-pad" accessibilityLabel="Tuổi theo tháng" />
              <TextInput style={[styles.input, styles.multilineInput]} value={interestsSummary} onChangeText={setInterestsSummary} placeholder="Sở thích liên quan (không bắt buộc)" maxLength={800} multiline accessibilityLabel="Sở thích" />
              {!editingProfileId ? <>
                <Text style={styles.consentCopy}>{policy?.consent_text ?? 'Chưa cấu hình chính sách đồng ý xử lý dữ liệu. Cần cấu hình phiên bản và nội dung được phê duyệt trong .env gốc.'}</Text>
                <Text style={styles.helper}>Phiên bản: {policy?.policy_version ?? 'chưa cấu hình'} · Mục đích: cá nhân hóa câu chuyện</Text>
                <Pressable style={styles.checkRow} onPress={() => setConsentAccepted((value) => !value)} accessibilityRole="checkbox" accessibilityState={{checked: consentAccepted}}>
                  <Text style={styles.checkBox}>{consentAccepted ? '☑' : '□'}</Text><Text style={styles.helper}>Tôi đã đọc và đồng ý cho xử lý dữ liệu theo mục đích này.</Text>
                </Pressable>
              </> : null}
              <ActionButton label={busy === 'profile' ? 'Đang lưu…' : editingProfileId ? 'Lưu phiên bản hồ sơ' : 'Tạo hồ sơ và lưu xác nhận'} disabled={loading || (!editingProfileId && (!policy || !consentAccepted))} onPress={() => void saveProfile()} />
              <ActionButton label="Đóng" disabled={loading} onPress={() => {setShowProfileForm(false); setEditingProfileId(null);}} secondary />
            </View>
          ) : null}
          {profiles.length === 0 && !policy ? <Text style={styles.warning}>Chính sách đồng ý chưa được cấu hình trong .env gốc. Hệ thống sẽ chặn tạo hồ sơ và gọi AI cho tới khi có cấu hình.</Text> : null}
        </View>

        <View style={styles.card}>
          <View style={styles.optionalHeading}><Text style={styles.optionalTitle}>Thêm gợi ý (không bắt buộc)</Text><View style={styles.optionalPill}><Text style={styles.optionalPillText}>TÙY CHỌN</Text></View></View>
          <Text style={styles.helper}>Có thể bỏ qua toàn bộ phần này. Ảnh tranh trên giấy vẫn là đầu vào bắt buộc.</Text>
          <Text style={styles.label}>Chủ đề, nếu đã biết</Text>
          <TextInput style={styles.input} value={topic} onChangeText={(value) => {setTopic(value); setGuide(null);}} placeholder="Ví dụ: con bướm" maxLength={120} editable={!run} />
          <Text style={styles.label}>Ý tưởng cho câu chuyện (không bắt buộc)</Text>
          <TextInput style={[styles.input, styles.multilineInput]} value={adultIdea} onChangeText={setAdultIdea} placeholder="Một gợi ý ngắn dành cho câu chuyện" maxLength={500} multiline editable={!run} />
          {!run ? <ActionButton label={galleryLoading ? 'Đang mở thư viện…' : galleryOpen ? 'Đóng thư viện bài học' : 'Chọn bài học từ thư viện'} disabled={loading || galleryLoading} onPress={() => void toggleGallery()} secondary /> : null}
          {selectedLesson ? <View style={styles.selectedLesson}>
            <Text style={styles.lessonEyebrow}>BÀI HỌC ĐÃ CHỌN · PHIÊN BẢN ĐƯỢC GHIM</Text>
            <Text style={styles.lessonTitle}>{selectedLesson.title}</Text>
            <Text style={styles.helper}>Phiên bản {selectedLesson.version_no} · {selectedLesson.activities.length} hoạt động</Text>
            {!run ? <SmallAction label="Bỏ chọn bài học" disabled={loading} onPress={() => setSelectedLesson(null)} /> : null}
          </View> : null}
          {galleryOpen ? <View style={styles.galleryList}>
            {lessons.length ? lessons.map((lesson) => (
              <Pressable key={lesson.lesson_id} style={styles.lessonChoice} disabled={Boolean(lessonLoadingId)} onPress={() => void selectLesson(lesson)}>
                <View style={styles.lessonChoiceCopy}><Text style={styles.profileName}>{lesson.title}</Text><Text style={styles.helper}>{lesson.topic} · {lesson.activity_count} hoạt động · {lesson.access_source === 'PUBLIC' ? 'Công khai' : 'Được chia sẻ'}</Text></View>
                <Text style={styles.lessonArrow}>{lessonLoadingId === lesson.lesson_id ? '…' : '›'}</Text>
              </Pressable>
            )) : <Text style={styles.helper}>Chưa có bài học được chia sẻ hoặc công khai. Bạn vẫn có thể tiếp tục không chọn.</Text>}
          </View> : null}
          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}><Text style={styles.label}>Gợi ý nét vẽ</Text><Text style={styles.helper}>Chỉ tạo khi bật. Đây là gợi ý tùy chọn để trẻ tham khảo.</Text></View>
            <Switch value={guideEnabled} onValueChange={(value) => {setGuideEnabled(value); if (!value) setGuide(null);}} />
          </View>
          {guideEnabled && !run ? <ActionButton label={busy === 'guide' ? 'Đang tạo gợi ý…' : 'Tạo gợi ý nét vẽ'} disabled={loading || !topic.trim()} onPress={() => void createGuide()} secondary /> : null}
          {guide ? <Image source={{uri: 'data:image/png;base64,' + guide}} style={styles.guideImage} resizeMode="contain" accessibilityLabel="Gợi ý nét vẽ tùy chọn" /> : null}
        </View>

        <View style={[styles.card, styles.captureCard]}>
          <View style={styles.cardHeading}>
            <View style={[styles.headingNumber, styles.headingNumberPrimary]}><Text style={[styles.headingNumberText, styles.headingNumberTextPrimary]}>2</Text></View>
            <View style={styles.headingCopy}><Text style={styles.sectionTitle}>Chụp tranh của con</Text><Text style={styles.helper}>Đây là bước bắt buộc. Cho trẻ vẽ trên giấy rồi chụp lại.</Text></View>
          </View>
          {!run ? (
            <View style={styles.savedContext}>
              <Text style={styles.label}>Ngữ cảnh sẽ dùng cho buổi này</Text>
              <Text style={styles.helper}>Hồ sơ: {selectedProfile?.current_revision.display_name ?? 'chưa chọn'}{selectedProfile ? ' · ' + ageLabel(selectedProfile.current_revision.age_months) : ''}</Text>
              <Text style={styles.helper}>Chủ đề: {topic.trim() || 'không đặt'} · Bài học: {selectedLesson ? `${selectedLesson.title} (v${selectedLesson.version_no})` : 'không chọn'}</Text>
              <Text style={styles.helper}>Khi nhấn xác nhận ảnh, ngữ cảnh này sẽ được lưu cùng buổi học.</Text>
            </View>
          ) : (
            <View style={styles.savedContext}>
              <Text style={styles.goodState}>Buổi học đã lưu · snapshot phiên bản {run.context_revision}</Text>
              <Text style={styles.helper}>Chủ đề: {run.context_snapshot.topic || 'không đặt'}{run.lesson_pin_snapshot ? ' · Bài học: ' + run.lesson_pin_snapshot.title + ' (v' + run.lesson_pin_snapshot.version_no + ')' : ''}</Text>
            </View>
          )}
          {canCapture ? <View style={styles.captureButtons}>
            <ActionButton label="Chụp ảnh tranh" disabled={loading || aiPending || Boolean(candidate) || !canCreateRun} onPress={() => void chooseDrawing('camera')} />
            <ActionButton label="Chọn ảnh có sẵn" disabled={loading || aiPending || Boolean(candidate) || !canCreateRun} onPress={() => void chooseDrawing('library')} secondary />
          </View> : <Text style={styles.notice}>Ảnh tranh đã được lưu riêng tư. Đang chờ nhận diện hoặc xác nhận chủ thể.</Text>}
          {drawing ? <>
            <Image source={{uri: drawing.uri}} style={styles.drawingPreview} resizeMode="contain" accessibilityLabel="Ảnh tranh trên giấy đã chọn" />
            <Text style={styles.helper}>Ảnh {drawing.mediaType === 'image/jpeg' ? 'JPG' : 'PNG'} · xem lại trước khi gửi.</Text>
            <ActionButton label={busy === 'drawing' ? 'Đang lưu và nhận diện…' : 'Xác nhận ngữ cảnh và phân tích tranh'} disabled={loading || aiPending || !canCreateRun} onPress={() => void analyzeDrawing()} />
            {!candidate ? <ActionButton label="Chụp lại" disabled={loading || aiPending || !canCreateRun} onPress={() => void chooseDrawing('camera')} secondary /> : null}
          </> : null}
          {!selectedProfile ? <Text style={styles.warning}>Chọn hoặc tạo hồ sơ trẻ trước khi chụp ảnh.</Text> : selectedProfile && !selectedProfile.authorization_current ? <Text style={styles.warning}>Cần xác nhận quyền xử lý hiện hành trước khi chụp ảnh.</Text> : null}
          {!policy ? <Text style={styles.warning}>Chưa tải được chính sách đồng ý hiện hành.</Text> : null}
          {outcomeUnknown ? <Text style={styles.warning}>Yêu cầu đang chờ đối soát. Không gửi lại để tránh tạo request trùng. Mã: {run?.error_code ?? 'chưa có'}</Text> : null}
          {aiPending && !outcomeUnknown ? <Text style={styles.notice}>AI đang xử lý ảnh đã lưu. Bạn có thể tải lại trạng thái sau đó.</Text> : null}
          {run?.error_code && !outcomeUnknown ? <>
            <Text style={styles.warning}>Buổi học gặp lỗi: {run.error_code}.</Text>
            {run.run_state === 'FAILED' ? <ActionButton label="Bắt đầu lại" disabled={loading} onPress={resetWorkflow} secondary /> : null}
          </> : null}
          {run ? <ActionButton label="Tải lại trạng thái" disabled={loading} onPress={() => void refreshRun()} secondary /> : null}
        </View>

        {candidate ? <View style={styles.card}>
          <View style={styles.cardHeading}>
            <View style={[styles.headingNumber, styles.headingNumberPrimary]}><Text style={[styles.headingNumberText, styles.headingNumberTextPrimary]}>3</Text></View>
            <View style={styles.headingCopy}><Text style={styles.sectionTitle}>Xác nhận chủ thể</Text><Text style={styles.helper}>AI đưa ra phỏng đoán; người lớn quyết định chủ thể đúng.</Text></View>
          </View>
          <Text style={styles.label}>AI nhận diện</Text>
          <TextInput style={styles.input} value={confirmedSubject} onChangeText={setConfirmedSubject} maxLength={160} placeholder="Sửa lại chủ thể nếu cần" editable={!subjectConfirmed && !loading} />
          <Text style={styles.helper}>Độ tin cậy tham khảo: {Math.round(candidate.confidence * 100)}%.</Text>
          <Text style={styles.label}>Đặc điểm nhìn thấy trong tranh</Text>
          {visibleFeatures.map((feature, index) => <Text key={String(index) + feature} style={styles.feature}>• {feature}</Text>)}
          {subjectConfirmed ? <Text style={styles.goodState}>Đã xác nhận “{confirmedSubject}”</Text> : <ActionButton label={busy === 'subject' ? 'Đang lưu xác nhận…' : 'Xác nhận chủ thể'} disabled={loading || !confirmedSubject.trim()} onPress={() => void confirmSubject()} />}
        </View> : null}

        {subjectConfirmed && run ? <View style={styles.card}>
          <View style={styles.optionalHeading}><View style={styles.headingCopy}><Text style={styles.sectionTitle}>Gợi ý hoạt động</Text><Text style={styles.helper}>Dựa trên chủ thể đã xác nhận{selectedLesson ? ' và bài học đã chọn' : ' trong tranh'}.</Text></View><View style={styles.optionalPill}><Text style={styles.optionalPillText}>CÓ THỂ BỎ QUA</Text></View></View>
          {activitySuggestions.length && !activitySkipped ? activitySuggestions.map((activity, index) => <View key={String(index) + activity.title} style={styles.activitySuggestion}>
            <Text style={styles.activityTitle}>{index + 1}. {activity.title}</Text>
            <Text style={styles.activityMeta}>{activity.activity_kind === 'outdoor' ? 'Ngoài trời' : activity.activity_kind === 'mixed' ? 'Trong nhà hoặc ngoài trời' : 'Trong nhà'}</Text>
            <Text style={styles.storyText}>{activity.objective}</Text>
            <Text style={styles.activityDetail}>Vật liệu: {activity.materials_text || 'Không cần vật liệu đặc biệt'}</Text>
            <Text style={styles.activityDetail}>Chuẩn bị: {activity.preparation_text || 'Có thể bắt đầu ngay'}</Text>
            <Text style={styles.activityDetail}>Cách làm: {activity.instructions_text}</Text>
            {activity.observation_notes ? <Text style={styles.activityDetail}>Người lớn quan sát: {activity.observation_notes}</Text> : null}
            {activity.safety_notes ? <Text style={styles.activitySafety}>Lưu ý: {activity.safety_notes}</Text> : null}
          </View>) : null}
          {activityLoading ? <View style={styles.activityLoading}><Text style={styles.activityLoadingIcon}>✦</Text><Text style={styles.helper}>Đang chuẩn bị gợi ý hoạt động… bạn vẫn có thể tiếp tục tạo câu chuyện.</Text></View> : null}
          {activitySource && !activitySkipped ? <Text style={styles.activityMeta}>{activitySource === 'PINNED_LESSON' ? 'Từ bài học đã ghim' : 'Gợi ý AI · cần người lớn xem lại'}</Text> : null}
          {activityError ? <Text style={styles.warning}>{activityError}{activityUnknown ? ' Kết quả đang được đối soát; không gửi lại yêu cầu này.' : ''}</Text> : null}
          {!activitySuggestions.length && !activityLoading && !activitySkipped && !activityUnknown ? <ActionButton label="Xem gợi ý hoạt động" disabled={loading} onPress={() => void loadActivitySuggestions(run)} secondary /> : null}
          {activitySkipped ? <Text style={styles.helper}>Đã bỏ qua gợi ý hoạt động cho buổi này.</Text> : !activityUnknown ? <SmallAction label="Bỏ qua gợi ý" onPress={skipActivitySuggestions} /> : null}
          <Text style={styles.helper}>Gợi ý chỉ để tham khảo. Bạn không cần chọn hoạt động để tiếp tục.</Text>
        </View> : null}

        {subjectConfirmed && run ? <View style={styles.card}>
          <View style={styles.cardHeading}>
            <View style={[styles.headingNumber, styles.headingNumberPrimary]}><Text style={[styles.headingNumberText, styles.headingNumberTextPrimary]}>4</Text></View>
            <View style={styles.headingCopy}><Text style={styles.sectionTitle}>Câu chuyện từ tranh</Text><Text style={styles.helper}>Tạo bản nháp, xem lại rồi người lớn xác nhận.</Text></View>
          </View>
          {!story ? <ActionButton label={busy === 'story' ? 'Đang tạo câu chuyện…' : 'Tạo câu chuyện tiếng Việt'} disabled={loading || aiPending} onPress={() => void generateStory()} /> : <>
            <Text style={styles.storyTitle}>{story.title}</Text>
            <Text style={styles.storyDuration}>{story.scenes.length} cảnh · {Math.round(story.duration_ms / 1000)} giây · phiên bản {run.story_revision_no ?? 1}</Text>
            <StorySection title="Mở đầu" body={story.story.opening} /><StorySection title="Diễn biến" body={story.story.middle} /><StorySection title="Kết thúc" body={story.story.ending} />
            {story.scenes.map((scene) => <View key={scene.scene_index} style={styles.sceneCard}><Text style={styles.sceneTitle}>Cảnh {scene.scene_index} · {scene.title}</Text><Text style={styles.storyText}>{scene.action}</Text><Text style={styles.narration}>{scene.narration}</Text></View>)}
            {!storyConfirmed && (run.story_revision_no ?? 1) < 4 ? <>
              <Text style={styles.helper}>Đã viết lại {Math.max(0, (run.story_revision_no ?? 1) - 1)}/3 lần. Gửi gợi ý để AI viết lại; không sửa trực tiếp từng cảnh.</Text>
              <TextInput style={[styles.input, styles.multilineInput]} value={rewriteInstruction} onChangeText={setRewriteInstruction} placeholder="Gợi ý cách viết lại (tối đa 400 ký tự)" maxLength={400} multiline editable={!loading} accessibilityLabel="Gợi ý AI viết lại câu chuyện" />
              <ActionButton label={busy === 'story' ? 'Đang viết lại…' : 'Gửi gợi ý viết lại'} disabled={loading || !rewriteInstruction.trim() || aiPending} onPress={() => void generateStory(rewriteInstruction)} secondary />
            </> : null}
            {storyConfirmed ? <Text style={styles.confirmed}>Đã xác nhận và lưu câu chuyện.</Text> : <ActionButton label={busy === 'confirm-story' ? 'Đang lưu xác nhận…' : 'Xác nhận câu chuyện'} disabled={loading || !storySha256} onPress={() => void confirmStory()} />}
          </>}
        </View> : null}

        {storyConfirmed ? <View style={styles.card}><Text style={styles.sectionTitle}>Tiếp theo</Text><Text style={styles.helper}>Câu chuyện đã được lưu. Các bước video và hoạt động sau khi xem video sẽ tiếp tục theo đúng bài học đã ghim, nếu có.</Text></View> : null}
        <Text style={styles.footer}>Ảnh, prompt và nội dung AI không được ghi vào log thiết bị.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}
function ActionButton({label, onPress, disabled, secondary}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  secondary?: boolean;
}): React.JSX.Element {
  return (
    <Pressable accessibilityRole="button" style={[styles.button, secondary && styles.buttonSecondary, disabled && styles.buttonDisabled]} disabled={disabled} onPress={onPress}>
      <Text style={[styles.buttonText, secondary && styles.buttonSecondaryText]}>{label}</Text>
    </Pressable>
  );
}

function SmallAction({label, onPress, disabled, danger}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  danger?: boolean;
}): React.JSX.Element {
  return (
    <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress} style={[styles.smallAction, danger && styles.smallActionDanger, disabled && styles.buttonDisabled]}>
      <Text style={[styles.smallActionText, danger && styles.smallActionDangerText]}>{label}</Text>
    </Pressable>
  );
}

function StorySection({title, body}: {title: string; body: string}): React.JSX.Element {
  return <View style={styles.storySection}><Text style={styles.sectionTitle}>{title}</Text><Text style={styles.storyText}>{body}</Text></View>;
}

function resolveDrawingMediaType(type: string | undefined, fileName: string | undefined): DrawingMediaType | null {
  if (type === 'image/png' || fileName?.toLowerCase().endsWith('.png')) return 'image/png';
  if (type === 'image/jpeg' || type === 'image/jpg' || fileName?.toLowerCase().match(/\.(jpe?g)$/)) return 'image/jpeg';
  return null;
}

function imagePickerErrorMessage(code: string): string {
  if (code === 'camera_unavailable') return 'Camera hiện không khả dụng trên thiết bị.';
  if (code === 'permission') return 'Thiết bị chưa cấp quyền camera hoặc thư viện ảnh.';
  return 'Không lấy được ảnh. Hãy thử lại hoặc chọn ảnh JPG/PNG.';
}

function ageLabel(ageMonths: number): string {
  const years = Math.floor(ageMonths / 12);
  const months = ageMonths % 12;
  return months === 0 ? `${years} tuổi` : `${years} tuổi ${months} tháng`;
}

function statusLabel(state: string, storyStatus: string | null): string {
  if (state === 'INPUT_PROCESSING') return 'Đang nhận tranh';
  if (state === 'SUBJECT_REVIEW') return 'Chờ xác nhận chủ thể';
  if (state === 'PREPARATION_REVIEW') return 'Chờ tạo kịch bản';
  if (state === 'SCRIPT_GENERATING') return 'Đang tạo kịch bản';
  if (state === 'SCRIPT_GENERATION_UNKNOWN') return 'Đang đối soát';
  if (state === 'SCRIPT_REVIEW' && storyStatus === 'CONFIRMED') return 'Đã xác nhận kịch bản';
  if (state === 'SCRIPT_REVIEW') return 'Chờ duyệt kịch bản';
  if (state === 'COMPLETED') return 'Đã xác nhận';
  if (state === 'FAILED') return 'Có lỗi';
  return state;
}

function parseParentStoryDraft(value: unknown): ParentStoryDraft | null {
  if (!isRecord(value) || value.schema_version !== 'sketch2life.story-revision.v1' || value.language !== 'vi') return null;
  if (typeof value.title !== 'string' || !isRecord(value.story) || !Array.isArray(value.scenes)) return null;
  const sections = value.story;
  if (![sections.opening, sections.middle, sections.ending].every((section) => typeof section === 'string' && section.trim())) return null;
  if (value.scenes.length < 5 || value.scenes.length > 15 || !Number.isInteger(value.duration_ms)) return null;
  let nextStart = 0;
  const scenes: StoryScene[] = [];
  for (let index = 0; index < value.scenes.length; index += 1) {
    const scene = value.scenes[index];
    if (
      !isRecord(scene)
      || scene.scene_index !== index + 1
      || typeof scene.title !== 'string'
      || typeof scene.action !== 'string'
      || typeof scene.narration !== 'string'
      || !Number.isInteger(scene.start_ms)
      || !Number.isInteger(scene.duration_ms)
      || scene.start_ms !== nextStart
      || (scene.duration_ms as number) <= 0
    ) return null;
    scenes.push({
      scene_index: scene.scene_index as number,
      title: scene.title,
      action: scene.action,
      narration: scene.narration,
      start_ms: scene.start_ms as number,
      duration_ms: scene.duration_ms as number,
    });
    nextStart += scene.duration_ms as number;
  }
  if (nextStart !== value.duration_ms || nextStart < 30_000 || nextStart > 90_000) return null;
  return {
    schema_version: 'sketch2life.story-revision.v1',
    language: 'vi',
    title: value.title,
    story: {
      opening: sections.opening as string,
      middle: sections.middle as string,
      ending: sections.ending as string,
    },
    duration_ms: value.duration_ms as number,
    scenes,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

const styles = StyleSheet.create({
  safeArea: {flex: 1, backgroundColor: '#FFF9EF'},
  container: {paddingHorizontal: 16, paddingTop: 12, paddingBottom: 42, gap: 12},
  header: {flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 2},
  headerText: {flex: 1},
  eyebrow: {color: '#6B8298', fontSize: 10, letterSpacing: 1.35, fontWeight: '800'},
  title: {color: '#263D56', fontSize: 24, fontWeight: '800', marginTop: 5},
  subtitle: {color: '#667789', fontSize: 12, marginTop: 5, lineHeight: 18},
  statusPill: {backgroundColor: '#E6F2FE', borderRadius: 14, paddingHorizontal: 10, paddingVertical: 6},
  statusText: {color: '#397EBE', fontSize: 10, fontWeight: '800'},
  stepper: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', paddingHorizontal: 1, paddingVertical: 4},
  stepperItem: {alignItems: 'center', gap: 5, flex: 1},
  stepperDot: {width: 25, height: 25, borderRadius: 13, backgroundColor: '#E9E6DF', alignItems: 'center', justifyContent: 'center'},
  stepperDotDone: {backgroundColor: '#B9D8F4'},
  stepperDotCurrent: {backgroundColor: '#4D9BE8', borderWidth: 2, borderColor: '#DCEEFF'},
  stepperNumber: {color: '#7F8A92', fontSize: 10, fontWeight: '800'},
  stepperNumberActive: {color: '#fff'},
  stepperLabel: {color: '#86919A', fontSize: 9, fontWeight: '600', textAlign: 'center'},
  stepperLabelCurrent: {color: '#2D6FA9', fontWeight: '800'},
  card: {backgroundColor: '#FFFFFF', borderColor: '#E8E5DE', borderWidth: 1, borderRadius: 19, padding: 15, gap: 10},
  captureCard: {borderColor: '#D3E8FA', borderWidth: 1.5, backgroundColor: '#FEFFFF'},
  cardHeading: {flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 1},
  headingNumber: {width: 30, height: 30, borderRadius: 15, backgroundColor: '#FFF0C7', alignItems: 'center', justifyContent: 'center'},
  headingNumberPrimary: {backgroundColor: '#4D9BE8'},
  headingNumberText: {color: '#9A6C17', fontSize: 13, fontWeight: '800'},
  headingNumberTextPrimary: {color: '#FFFFFF'},
  headingCopy: {flex: 1, gap: 2},
  sectionTitle: {color: '#2C435B', fontSize: 15, fontWeight: '800'},
  label: {color: '#3D5268', fontSize: 12, fontWeight: '700'},
  helper: {color: '#718091', fontSize: 11, lineHeight: 16, flex: 1},
  step: {color: '#5286B4', fontSize: 10, letterSpacing: 1.1, fontWeight: '800'},
  optionalHeading: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8},
  optionalTitle: {color: '#3D5268', fontSize: 13, fontWeight: '800', flex: 1},
  optionalPill: {backgroundColor: '#FFF2CE', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 5},
  optionalPillText: {color: '#8B6C22', fontSize: 8, fontWeight: '800', letterSpacing: 0.5},
  input: {backgroundColor: '#FFFFFF', borderColor: '#DCE3E9', borderWidth: 1, borderRadius: 12, minHeight: 44, paddingHorizontal: 12, color: '#2E4358', fontSize: 13},
  multilineInput: {minHeight: 76, paddingTop: 10, textAlignVertical: 'top'},
  warning: {backgroundColor: '#FFF5E6', borderColor: '#F0D8A9', borderWidth: 1, color: '#795B22', borderRadius: 12, padding: 10, fontSize: 11, lineHeight: 16},
  consentCopy: {backgroundColor: '#F7F8FA', color: '#4E6173', fontSize: 12, lineHeight: 18, padding: 11, borderRadius: 11},
  formBlock: {borderTopColor: '#E9EDF0', borderTopWidth: 1, paddingTop: 12, gap: 9},
  consentPanel: {backgroundColor: '#F7F8FA', borderRadius: 12, padding: 11, gap: 8},
  profileRow: {gap: 6, borderBottomColor: '#EEF0F1', borderBottomWidth: 1, paddingBottom: 9},
  profileChoice: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#FFFFFF', borderColor: '#E5E9EC', borderWidth: 1, borderRadius: 13, padding: 11},
  profileChoiceSelected: {borderColor: '#65A8E5', backgroundColor: '#F3F9FF'},
  profileCopy: {flex: 1, gap: 3},
  profileName: {color: '#2C435B', fontSize: 13, fontWeight: '800'},
  radioMark: {color: '#4D9BE8', fontSize: 18, paddingHorizontal: 6},
  profileActions: {flexDirection: 'row', flexWrap: 'wrap', gap: 6},
  smallAction: {borderColor: '#D5E4F1', borderWidth: 1, borderRadius: 9, paddingHorizontal: 10, paddingVertical: 6, alignSelf: 'flex-start'},
  smallActionText: {color: '#3F80B7', fontSize: 10, fontWeight: '700'},
  smallActionDanger: {borderColor: '#F0D4CF'},
  smallActionDangerText: {color: '#A34435'},
  goodState: {color: '#368263', fontSize: 11, fontWeight: '700'},
  pendingState: {color: '#9A6A1B', fontSize: 11, fontWeight: '700'},
  checkRow: {flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 4},
  checkBox: {color: '#4D9BE8', fontSize: 20, width: 24},
  toggleRow: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12, borderTopColor: '#EEF0F1', borderTopWidth: 1, paddingTop: 10, marginTop: 3},
  toggleCopy: {flex: 1, gap: 3},
  savedContext: {backgroundColor: '#F1F8FE', borderRadius: 12, padding: 11, gap: 7},
  captureButtons: {gap: 1},
  drawingPreview: {width: '100%', height: 220, backgroundColor: '#FFFFFF', borderRadius: 14, borderWidth: 1, borderColor: '#E4E9ED'},
  guideImage: {width: '100%', height: 180, backgroundColor: '#FFFFFF', borderRadius: 13, borderWidth: 1, borderColor: '#E5E9ED'},
  button: {backgroundColor: '#4D9BE8', borderRadius: 13, minHeight: 46, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 13, marginTop: 3},
  buttonSecondary: {backgroundColor: '#F1F7FD', borderColor: '#D6E7F5', borderWidth: 1},
  buttonDisabled: {opacity: 0.45},
  buttonText: {color: '#FFFFFF', fontSize: 13, fontWeight: '800', textAlign: 'center'},
  buttonSecondaryText: {color: '#397EBE'},
  error: {backgroundColor: '#FFF0EB', borderColor: '#EDB8A7', borderWidth: 1, color: '#9C3E2B', borderRadius: 12, padding: 10, fontSize: 12},
  notice: {backgroundColor: '#EDF6FE', borderColor: '#D1E7F8', borderWidth: 1, color: '#3D6E97', borderRadius: 12, padding: 10, fontSize: 11, lineHeight: 16},
  requestId: {color: '#98A0A7', fontSize: 9, marginTop: -8},
  feature: {color: '#53687B', fontSize: 12, lineHeight: 18},
  selectedLesson: {backgroundColor: '#FFF9E9', borderColor: '#F3E3B4', borderWidth: 1, borderRadius: 13, padding: 11, gap: 5},
  lessonEyebrow: {color: '#997A32', fontSize: 9, letterSpacing: 0.7, fontWeight: '800'},
  lessonTitle: {color: '#344E66', fontSize: 14, fontWeight: '800'},
  galleryList: {gap: 7, borderTopColor: '#EDF0F2', borderTopWidth: 1, paddingTop: 9},
  lessonChoice: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: 11, borderRadius: 12, backgroundColor: '#F7FAFC', borderColor: '#E4EBF0', borderWidth: 1},
  lessonChoiceCopy: {flex: 1, gap: 3},
  lessonArrow: {fontSize: 23, color: '#4D9BE8', paddingHorizontal: 4},
  activitySuggestion: {backgroundColor: '#F7FAFC', borderColor: '#E4EBF0', borderWidth: 1, borderRadius: 13, padding: 11, gap: 5},
  activityTitle: {color: '#2F4B63', fontSize: 13, fontWeight: '800'},
  activityMeta: {color: '#6284A1', fontSize: 10, fontWeight: '700'},
  activityDetail: {color: '#5C6D7A', fontSize: 11, lineHeight: 16},
  activitySafety: {color: '#8B6B24', backgroundColor: '#FFF5DF', padding: 8, borderRadius: 8, fontSize: 10, lineHeight: 15},
  activityLoading: {flexDirection: 'row', alignItems: 'center', gap: 9, backgroundColor: '#F5F9FC', borderRadius: 11, padding: 10},
  activityLoadingIcon: {color: '#E9B93F', fontSize: 18},
  storyTitle: {color: '#2F4B63', fontSize: 18, fontWeight: '800'},
  storyDuration: {color: '#788694', fontSize: 11},
  storySection: {backgroundColor: '#F5F8FA', borderRadius: 11, padding: 11, gap: 4},
  storyText: {color: '#4E6173', fontSize: 12, lineHeight: 18},
  sceneCard: {borderLeftColor: '#7CB5E8', borderLeftWidth: 3, paddingLeft: 10, gap: 4},
  sceneTitle: {color: '#344E66', fontSize: 12, fontWeight: '800'},
  narration: {color: '#697B8B', fontSize: 11, lineHeight: 16, fontStyle: 'italic'},
  confirmed: {color: '#368263', fontSize: 12, fontWeight: '800', paddingVertical: 5},
  footer: {color: '#97A1A9', textAlign: 'center', fontSize: 9},
});
