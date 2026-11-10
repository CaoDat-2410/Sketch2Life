import React, {useEffect, useMemo, useState} from 'react';
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
  type ParentAiReceipt,
  type ParentConsentPolicy,
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
  const [contextConfirmed, setContextConfirmed] = useState(false);
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
        setContextConfirmed(true);
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
    setContextConfirmed(true);
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
    setRewriteInstruction('');
    setGuide(null);
    setContextConfirmed(false);
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

  async function createRun() {
    setError('');
    setNotice('');
    if (!selectedProfile || !selectedProfile.authorization_current) {
      setError('Chọn hồ sơ có quyền xử lý dữ liệu đang hiệu lực.');
      return;
    }
    if (!topic.trim()) {
      setError('Nhập chủ đề của buổi vẽ.');
      return;
    }
    if (!contextConfirmed) {
      setError('Người lớn cần xác nhận snapshot tuổi, chủ đề và ý tưởng trước khi tiếp tục.');
      return;
    }
    setBusy('run');
    try {
      const result = await api.createStoryRun({
        parent_profile_id: selectedProfile.parent_profile_id,
        expected_profile_revision_id: selectedProfile.current_revision.profile_revision_id,
        consent_policy_version: policy?.policy_version ?? '',
        topic: topic.trim(),
        adult_confirmed_idea: adultIdea.trim(),
        context_confirmed: true,
      });
      resetWorkflow();
      setRun(result.story_run);
      setSelectedProfileId(result.story_run.parent_profile_id);
      setContextConfirmed(true);
      setLastRequestId(result.request_id);
      setNotice('Đã lưu StoryRun và snapshot context đã xác nhận. Bây giờ hãy chụp hoặc chọn tranh trên giấy.');
    } catch (cause) {
      showFailure(cause, 'Không tạo được buổi học.');
      const current = await api.getActiveStoryRun().catch(() => null);
      if (current?.story_run) {
        syncRun(current.story_run);
        setError('');
        setNotice('Buổi học đã được lưu trên máy chủ và được khôi phục.');
      }
    } finally {
      setBusy('');
    }
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
    if (!run || !drawing) {
      setError('Tạo buổi học rồi chụp hoặc chọn ảnh tranh trước.');
      return;
    }
    setBusy('drawing');
    try {
      const response = await api.analyzeDrawing(run.run_id, drawing.base64, drawing.mediaType);
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
      const current = await api.getStoryRun(run.run_id);
      setRun(current.story_run);
      setNotice('AI đã gợi ý chủ thể. Người lớn cần xác nhận hoặc sửa trước khi tạo kịch bản.');
    } catch (cause) {
      showFailure(cause, 'Không thể phân tích tranh.');
      const current = await api.getStoryRun(run.run_id).catch(() => null);
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
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.eyebrow}>SKETCH2LIFE · PHỤ HUYNH</Text>
            <Text style={styles.title}>Tranh của con thành câu chuyện</Text>
            <Text style={styles.subtitle}>Người lớn hướng dẫn và xác nhận ở từng bước. Tranh được vẽ trên giấy.</Text>
          </View>
          {run ? <View style={styles.statusPill}><Text style={styles.statusText}>{statusLabel(run.run_state, run.story_status)}</Text></View> : null}
        </View>

        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        {notice ? <Text style={styles.notice}>{notice}</Text> : null}
        {lastRequestId ? <Text style={styles.requestId}>Mã yêu cầu: {lastRequestId}</Text> : null}

        <View style={styles.card}>
          <Text style={styles.step}>01 · HỒ SƠ TRẺ</Text>
          <Text style={styles.sectionTitle}>Chọn hồ sơ thuộc tài khoản của bạn</Text>
          {profiles.map((profile) => (
            <View key={profile.parent_profile_id} style={styles.profileRow}>
              <Pressable
                accessibilityRole="radio"
                accessibilityState={{checked: selectedProfileId === profile.parent_profile_id}}
                style={[styles.profileChoice, selectedProfileId === profile.parent_profile_id && styles.profileChoiceSelected]}
                onPress={() => setSelectedProfileId(profile.parent_profile_id)}>
                <View style={styles.profileCopy}>
                  <Text style={styles.profileName}>{profile.current_revision.display_name}</Text>
                  <Text style={styles.helper}>{ageLabel(profile.current_revision.age_months)} · revision {profile.current_revision.revision}</Text>
                  <Text style={profile.authorization_current ? styles.goodState : styles.pendingState}>
                    {profile.authorization_current ? 'Đã đồng ý theo policy hiện hành' : 'Cần xác nhận lại quyền xử lý'}
                  </Text>
                </View>
                <Text style={styles.radioMark}>{selectedProfileId === profile.parent_profile_id ? '●' : '○'}</Text>
              </Pressable>
              <View style={styles.profileActions}>
                <SmallAction label="Sửa" disabled={loading || !profile.authorization_current || Boolean(run && run.parent_profile_id === profile.parent_profile_id)} onPress={() => beginEditProfile(profile)} />
                {!profile.authorization_current ? <SmallAction label="Xem policy" disabled={loading || !policy} onPress={() => {setReconsentProfileId(profile.parent_profile_id); setReconsentAccepted(false);}} /> : null}
                {profile.authorization_current ? <SmallAction label="Thu hồi" disabled={loading} onPress={() => void revokeAuthorization(profile)} /> : null}
                <SmallAction label="Lưu trữ" disabled={loading || Boolean(run && run.parent_profile_id === profile.parent_profile_id)} onPress={() => archiveProfile(profile)} danger />
              </View>
              {!profile.authorization_current && selectedProfileId === profile.parent_profile_id && reconsentProfileId === profile.parent_profile_id ? (
                <View style={styles.consentPanel}>
                  <Text style={styles.consentCopy}>{policy?.consent_text ?? 'Chưa cấu hình consent policy.'}</Text>
                  <Text style={styles.helper}>Phiên bản {policy?.policy_version ?? 'chưa cấu hình'} · Mục đích: cá nhân hóa story</Text>
                  <Pressable style={styles.checkRow} onPress={() => setReconsentAccepted((value) => !value)} accessibilityRole="checkbox" accessibilityState={{checked: reconsentAccepted}}>
                    <Text style={styles.checkBox}>{reconsentAccepted ? '☑' : '□'}</Text>
                    <Text style={styles.helper}>Tôi đã đọc và đồng ý theo policy này.</Text>
                  </Pressable>
                  <ActionButton label="Cấp quyền theo policy hiện hành" disabled={loading || !policy || !reconsentAccepted} onPress={() => void grantAuthorization(profile)} />
                </View>
              ) : null}
            </View>
          ))}
          {!showProfileForm ? (
            <ActionButton label="Tạo hồ sơ trẻ" disabled={loading || Boolean(run)} onPress={() => {setEditingProfileId(null); setShowProfileForm(true);}} secondary />
          ) : null}
          {showProfileForm ? (
            <View style={styles.formBlock}>
              <Text style={styles.label}>{editingProfileId ? 'Sửa hồ sơ · tạo revision mới' : 'Tạo hồ sơ'}</Text>
              <TextInput style={styles.input} value={displayName} onChangeText={setDisplayName} placeholder="Tên gọi trong gia đình" maxLength={120} accessibilityLabel="Tên hồ sơ trẻ" />
              <TextInput style={styles.input} value={ageMonths} onChangeText={setAgeMonths} placeholder="Tuổi theo tháng, 36–120" keyboardType="number-pad" accessibilityLabel="Tuổi theo tháng" />
              <TextInput style={[styles.input, styles.multilineInput]} value={interestsSummary} onChangeText={setInterestsSummary} placeholder="Sở thích liên quan, không nhập thông tin nhạy cảm" maxLength={800} multiline accessibilityLabel="Sở thích" />
              {!editingProfileId ? (
                <>
                  <Text style={styles.consentCopy}>{policy?.consent_text ?? 'Chưa cấu hình policy đồng ý xử lý dữ liệu. Hãy nhập phiên bản và nội dung đã được phê duyệt trong .env gốc.'}</Text>
                  <Text style={styles.helper}>Phiên bản: {policy?.policy_version ?? 'chưa cấu hình'} · Mục đích: cá nhân hóa story</Text>
                  <Pressable style={styles.checkRow} onPress={() => setConsentAccepted((value) => !value)} accessibilityRole="checkbox" accessibilityState={{checked: consentAccepted}}>
                    <Text style={styles.checkBox}>{consentAccepted ? '☑' : '□'}</Text>
                    <Text style={styles.helper}>Tôi đã đọc nội dung trên và đồng ý cho xử lý dữ liệu theo mục đích này.</Text>
                  </Pressable>
                </>
              ) : null}
              <ActionButton
                label={busy === 'profile' ? 'Đang lưu…' : editingProfileId ? 'Lưu revision hồ sơ' : 'Tạo hồ sơ và lưu đồng ý'}
                disabled={loading || (!editingProfileId && (!policy || !consentAccepted))}
                onPress={() => void saveProfile()}
              />
              <ActionButton label="Đóng" disabled={loading} onPress={() => {setShowProfileForm(false); setEditingProfileId(null);}} secondary />
            </View>
          ) : null}
          {profiles.length === 0 && !policy ? <Text style={styles.warning}>Consent policy chưa có trong .env gốc. Profile creation và AI sẽ fail-closed cho tới khi policy version/text được cấu hình.</Text> : null}
        </View>

        <View style={styles.card}>
          <Text style={styles.step}>02 · CHUẨN BỊ BUỔI VẼ</Text>
          <Text style={styles.label}>Chủ đề</Text>
          <TextInput style={styles.input} value={topic} onChangeText={setTopic} placeholder="Ví dụ: con bướm trong vườn" maxLength={120} editable={!run} />
          <Text style={styles.label}>Ý tưởng người lớn muốn gợi vào kịch bản (không bắt buộc)</Text>
          <TextInput style={[styles.input, styles.multilineInput]} value={adultIdea} onChangeText={setAdultIdea} placeholder="Gợi ý ngắn, tối đa 500 ký tự" maxLength={500} multiline editable={!run} />
          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}>
              <Text style={styles.label}>Gợi ý line sketch (tùy chọn)</Text>
              <Text style={styles.helper}>Chỉ tạo khi bật và bấm nút. Gợi ý không nhận hồ sơ, ảnh tranh hoặc context của trẻ.</Text>
            </View>
            <Switch value={guideEnabled} onValueChange={(value) => {setGuideEnabled(value); if (!value) setGuide(null);}} />
          </View>
          {guideEnabled ? <ActionButton label={busy === 'guide' ? 'Đang tạo gợi ý…' : 'Tạo gợi ý vẽ'} disabled={loading || Boolean(run)} onPress={() => void createGuide()} secondary /> : null}
          {guide ? <Image source={{uri: `data:image/png;base64,${guide}`}} style={styles.guideImage} resizeMode="contain" accessibilityLabel="Line sketch gợi ý" /> : null}
          {!run ? (
            <>
              <Pressable style={styles.checkRow} onPress={() => setContextConfirmed((value) => !value)} accessibilityRole="checkbox" accessibilityState={{checked: contextConfirmed}}>
                <Text style={styles.checkBox}>{contextConfirmed ? '☑' : '□'}</Text>
                <Text style={styles.helper}>
                  Tôi xác nhận dùng tuổi {selectedProfile ? ageLabel(selectedProfile.current_revision.age_months) : 'trong hồ sơ đã chọn'}, sở thích trong hồ sơ, chủ đề và ý tưởng ở trên làm snapshot cho buổi này.
                </Text>
              </Pressable>
              <ActionButton
                label={busy === 'run' ? 'Đang lưu buổi học…' : 'Lưu snapshot và bắt đầu'}
                disabled={loading || !selectedProfile || !selectedProfile.authorization_current || !contextConfirmed}
                onPress={() => void createRun()}
              />
              {!selectedProfile ? <Text style={styles.helper}>Tạo hoặc chọn hồ sơ để tiếp tục.</Text> : null}
              {selectedProfile && !selectedProfile.authorization_current ? <Text style={styles.warning}>Cần đồng ý theo policy hiện hành trước khi tạo buổi học.</Text> : null}
            </>
          ) : (
            <View style={styles.savedContext}>
              <Text style={styles.goodState}>Snapshot đã lưu · context revision {run.context_revision}</Text>
              <Text style={styles.helper}>Profile revision: {run.profile_revision_ref.slice(0, 8)}… · SHA-256: {run.context_snapshot_sha256.slice(0, 12)}…</Text>
              <Text style={styles.helper}>Tuổi: {ageLabel(run.context_snapshot.age_months)} · Chủ đề: {run.context_snapshot.topic || 'chưa đặt'}</Text>
              {run.context_snapshot.interests_summary ? <Text style={styles.helper}>Sở thích đã xác nhận: {run.context_snapshot.interests_summary}</Text> : null}
              {run.context_snapshot.adult_confirmed_idea ? <Text style={styles.helper}>Ý tưởng người lớn: {run.context_snapshot.adult_confirmed_idea}</Text> : null}
              <ActionButton label="Tải lại trạng thái buổi học" disabled={loading} onPress={() => void refreshRun()} secondary />
            </View>
          )}
        </View>

        {run ? (
          <>
            <View style={styles.card}>
              <Text style={styles.step}>03 · VẼ VÀ CHỤP TRANH</Text>
              <Text style={styles.helper}>Cho trẻ vẽ trên giấy trước. Ảnh chỉ được tải lên backend riêng tư sau khi bạn bấm phân tích.</Text>
              <View style={styles.captureButtons}>
                <ActionButton label="Chụp bằng camera" disabled={loading || aiPending || Boolean(candidate)} onPress={() => void chooseDrawing('camera')} />
                <ActionButton label="Chọn ảnh từ thư viện" disabled={loading || aiPending || Boolean(candidate)} onPress={() => void chooseDrawing('library')} secondary />
              </View>
              {drawing ? (
                <>
                  <Image source={{uri: drawing.uri}} style={styles.drawingPreview} resizeMode="contain" accessibilityLabel="Ảnh tranh trẻ đã chọn" />
                  <Text style={styles.helper}>Ảnh {drawing.mediaType === 'image/jpeg' ? 'JPG' : 'PNG'} · xem trước trước khi gửi.</Text>
                  <ActionButton label={busy === 'drawing' ? 'Đang lưu và phân tích…' : 'Lưu ảnh và phân tích tranh'} disabled={loading || aiPending || Boolean(candidate)} onPress={() => void analyzeDrawing()} />
                  {!candidate ? <ActionButton label="Chụp/chọn ảnh khác" disabled={loading || aiPending} onPress={() => void chooseDrawing('camera')} secondary /> : null}
                </>
              ) : run.current_input_revision && run.current_input_revision > 1 ? (
                <Text style={styles.notice}>Ảnh tranh đã lưu riêng tư cho buổi này. Tải lại trạng thái nếu yêu cầu nhận diện đang xử lý.</Text>
              ) : null}
              {outcomeUnknown ? <Text style={styles.warning}>Yêu cầu đang chờ đối soát. Không tự gửi lại để tránh tạo request trùng. Mã: {run.error_code ?? 'chưa có'}</Text> : null}
              {aiPending && !outcomeUnknown ? <Text style={styles.notice}>AI đang xử lý yêu cầu đã lưu. Không gửi lại; hãy tải lại trạng thái sau đó.</Text> : null}
              {run.error_code && !outcomeUnknown ? (
                <>
                  <Text style={styles.warning}>Buổi học bị lỗi ở bước trước: {run.error_code}. Không gửi lại request chưa rõ kết quả.</Text>
                  {run.run_state === 'FAILED' ? <ActionButton label="Bắt đầu lại buổi này" disabled={loading} onPress={resetWorkflow} secondary /> : null}
                </>
              ) : null}
            </View>

            {candidate ? (
              <View style={styles.card}>
                <Text style={styles.step}>04 · NGƯỜI LỚN XÁC NHẬN CHỦ THỂ</Text>
                <Text style={styles.label}>AI nhìn thấy có thể là</Text>
                <TextInput style={styles.input} value={confirmedSubject} onChangeText={setConfirmedSubject} maxLength={160} placeholder="Nhập chủ thể đúng nếu gợi ý chưa chính xác" editable={!subjectConfirmed && !loading} />
                <Text style={styles.helper}>Độ tin cậy: {Math.round(candidate.confidence * 100)}% · Luôn cần người lớn xác nhận.</Text>
                <Text style={styles.label}>Đặc điểm nhìn thấy trong tranh</Text>
                {visibleFeatures.map((feature, index) => <Text key={`${index}-${feature}`} style={styles.feature}>• {feature}</Text>)}
                {subjectConfirmed ? (
                  <Text style={styles.goodState}>Đã lưu chủ thể “{confirmedSubject}” · understanding revision {understandingRevision}</Text>
                ) : (
                  <ActionButton label={busy === 'subject' ? 'Đang lưu xác nhận…' : 'Xác nhận chủ thể'} disabled={loading || !confirmedSubject.trim()} onPress={() => void confirmSubject()} />
                )}
              </View>
            ) : null}

            {subjectConfirmed ? (
              <View style={styles.card}>
                <Text style={styles.step}>05 · KỊCH BẢN</Text>
                <Text style={styles.helper}>Kịch bản được tạo theo StoryRun và snapshot đã lưu. AI chỉ tạo bản nháp; bạn cần xem rồi xác nhận.</Text>
                {!story ? <ActionButton label={busy === 'story' ? 'Đang tạo kịch bản…' : 'Tạo kịch bản tiếng Việt'} disabled={loading || aiPending} onPress={() => void generateStory()} /> : null}
                {story ? (
                  <>
                    <Text style={styles.storyTitle}>{story.title}</Text>
                    <Text style={styles.storyDuration}>{story.scenes.length} cảnh · {Math.round(story.duration_ms / 1000)} giây · revision {run.story_revision_no ?? 1}</Text>
                    <StorySection title="Mở đầu" body={story.story.opening} />
                    <StorySection title="Diễn biến" body={story.story.middle} />
                    <StorySection title="Kết thúc" body={story.story.ending} />
                    {story.scenes.map((scene) => (
                      <View key={scene.scene_index} style={styles.sceneCard}>
                        <Text style={styles.sceneTitle}>Cảnh {scene.scene_index} · {scene.title}</Text>
                        <Text style={styles.storyText}>{scene.action}</Text>
                        <Text style={styles.narration}>{scene.narration}</Text>
                      </View>
                    ))}
                    {!storyConfirmed && (run.story_revision_no ?? 1) < 4 ? (
                      <>
                        <Text style={styles.helper}>Lần viết lại: {Math.max(0, (run.story_revision_no ?? 1) - 1)}/3. Gửi gợi ý để AI viết lại; không sửa trực tiếp từng cảnh.</Text>
                        <TextInput
                          style={[styles.input, styles.multilineInput]}
                          value={rewriteInstruction}
                          onChangeText={setRewriteInstruction}
                          placeholder="Gợi ý cách AI viết lại, tối đa 400 ký tự"
                          maxLength={400}
                          multiline
                          editable={!loading}
                          accessibilityLabel="Gợi ý AI viết lại kịch bản"
                        />
                        <ActionButton
                          label={busy === 'story' ? 'Đang viết lại…' : 'Gửi gợi ý viết lại cho AI'}
                          disabled={loading || !rewriteInstruction.trim() || aiPending}
                          onPress={() => void generateStory(rewriteInstruction)}
                          secondary
                        />
                      </>
                    ) : null}
                    {storyConfirmed ? <Text style={styles.confirmed}>Đã xác nhận và lưu kịch bản.</Text> : <ActionButton label={busy === 'confirm-story' ? 'Đang lưu xác nhận…' : 'Tôi xác nhận kịch bản này'} disabled={loading || !storySha256} onPress={() => void confirmStory()} />}
                  </>
                ) : null}
              </View>
            ) : null}

            {storyConfirmed ? (
              <View style={styles.card}>
                <Text style={styles.step}>06 · TIẾP THEO</Text>
                <Text style={styles.helper}>Kịch bản đã được xác nhận và lưu. StoryRun vẫn được giữ để tiếp tục với bước video và hoạt động ngoài trời khi các API đó được nối.</Text>
              </View>
            ) : null}
          </>
        ) : null}

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
  sectionTitle: {color: '#38483c', fontSize: 12, fontWeight: '800'},
  input: {backgroundColor: '#fff', borderColor: '#ddd5c9', borderWidth: 1, borderRadius: 11, minHeight: 42, paddingHorizontal: 12, color: '#2c302b'},
  multilineInput: {minHeight: 78, paddingTop: 10, textAlignVertical: 'top'},
  helper: {color: '#777267', fontSize: 11, lineHeight: 16, flex: 1},
  warning: {backgroundColor: '#fff5e8', borderColor: '#ead2a9', borderWidth: 1, color: '#795b22', borderRadius: 12, padding: 10, fontSize: 11, lineHeight: 16},
  consentCopy: {backgroundColor: '#f7f4ed', color: '#4e5048', fontSize: 12, lineHeight: 18, padding: 11, borderRadius: 10},
  formBlock: {borderTopColor: '#eee7dc', borderTopWidth: 1, paddingTop: 12, gap: 9},
  consentPanel: {backgroundColor: '#f7f4ed', borderRadius: 12, padding: 11, gap: 8},
  profileRow: {gap: 5, borderBottomColor: '#eee7dc', borderBottomWidth: 1, paddingBottom: 8},
  profileChoice: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#fff', borderColor: '#eee7dc', borderWidth: 1, borderRadius: 12, padding: 10},
  profileChoiceSelected: {borderColor: '#2f7259', backgroundColor: '#f0f7f2'},
  profileCopy: {flex: 1, gap: 3},
  profileName: {color: '#2c372f', fontSize: 14, fontWeight: '800'},
  radioMark: {color: '#2f7259', fontSize: 18, paddingHorizontal: 6},
  profileActions: {flexDirection: 'row', flexWrap: 'wrap', gap: 6},
  smallAction: {borderColor: '#d9e4dc', borderWidth: 1, borderRadius: 9, paddingHorizontal: 10, paddingVertical: 6},
  smallActionText: {color: '#2f7259', fontSize: 10, fontWeight: '700'},
  smallActionDanger: {borderColor: '#edd0c8'},
  smallActionDangerText: {color: '#a34435'},
  goodState: {color: '#2f7259', fontSize: 11, fontWeight: '700'},
  pendingState: {color: '#9a6a1b', fontSize: 11, fontWeight: '700'},
  checkRow: {flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 4},
  checkBox: {color: '#2f7259', fontSize: 20, width: 24},
  toggleRow: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12, borderTopColor: '#eee7dc', borderTopWidth: 1, paddingTop: 10, marginTop: 3},
  toggleCopy: {flex: 1, gap: 3},
  savedContext: {backgroundColor: '#f0f7f2', borderRadius: 11, padding: 11, gap: 7},
  guideImage: {width: '100%', height: 180, backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#eee7dc'},
  drawingPreview: {width: '100%', height: 210, backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#eee7dc'},
  captureButtons: {gap: 3},
  button: {backgroundColor: '#2f7259', borderRadius: 12, minHeight: 44, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 12, marginTop: 4},
  buttonSecondary: {backgroundColor: '#e8f0e9', borderColor: '#c8d8cc', borderWidth: 1},
  buttonDisabled: {opacity: 0.45},
  buttonText: {color: '#fff', fontSize: 13, fontWeight: '800', textAlign: 'center'},
  buttonSecondaryText: {color: '#2f7259'},
  error: {backgroundColor: '#fff0eb', borderColor: '#edb8a7', borderWidth: 1, color: '#9c3e2b', borderRadius: 12, padding: 10, fontSize: 12},
  notice: {backgroundColor: '#e8f3eb', borderColor: '#c8dfcf', borderWidth: 1, color: '#335d43', borderRadius: 12, padding: 10, fontSize: 12},
  requestId: {color: '#938c7e', fontSize: 9, marginTop: -8},
  feature: {color: '#4f5149', fontSize: 12, lineHeight: 18},
  storyTitle: {color: '#2b3d32', fontSize: 18, fontWeight: '800'},
  storyDuration: {color: '#777267', fontSize: 11},
  storySection: {backgroundColor: '#f7f4ed', borderRadius: 10, padding: 11, gap: 4},
  storyText: {color: '#4e5048', fontSize: 12, lineHeight: 18},
  sceneCard: {borderLeftColor: '#85b5a0', borderLeftWidth: 3, paddingLeft: 10, gap: 4},
  sceneTitle: {color: '#38483c', fontSize: 12, fontWeight: '800'},
  narration: {color: '#6d6659', fontSize: 11, lineHeight: 16, fontStyle: 'italic'},
  confirmed: {color: '#2f7259', fontSize: 12, fontWeight: '800', paddingVertical: 5},
  footer: {color: '#938c7e', textAlign: 'center', fontSize: 9},
});
