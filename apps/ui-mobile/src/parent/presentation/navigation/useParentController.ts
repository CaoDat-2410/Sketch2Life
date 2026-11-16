import { useState } from 'react';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import { parseStoryDraft } from '../../domain/storyDraft';
import type {
  ParentAudioTranscription,
  ConsentPolicy,
  LessonDetail,
  LessonInvitation,
  LessonSummary,
  ParentCandidate,
  ParentGroupInvitation,
  ParentProfile,
  ParentUser,
  StoryDraft,
  StoryRun,
  SuggestedActivity,
} from '../../domain/types';
import type { AppStep, SelectedAudio, SelectedPhoto, TimedEvent } from './workflowTypes';

export function useParentController(application: ParentApplicationModule) {
  const [step, setStep] = useState<AppStep>('auth');
  const [policy, setPolicy] = useState<ConsentPolicy | null>(null);
  const [currentUser, setCurrentUser] = useState<ParentUser | null>(null);
  const [profiles, setProfiles] = useState<ParentProfile[]>([]);
  const [profile, setProfile] = useState<ParentProfile | null>(null);
  const [profileBeingEdited, setProfileBeingEdited] = useState<ParentProfile | null>(null);
  const [activeRun, setActiveRun] = useState<StoryRun | null>(null);
  const [topic, setTopic] = useState('');
  const [idea, setIdea] = useState('');
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [lessonLoading, setLessonLoading] = useState(false);
  const [lessonLoadingId, setLessonLoadingId] = useState('');
  const [lessonError, setLessonError] = useState('');
  const [galleryMode, setGalleryMode] = useState<'gallery' | 'picker'>('gallery');
  const [galleryLesson, setGalleryLesson] = useState<LessonDetail | null>(null);
  const [lessonInvitations, setLessonInvitations] = useState<LessonInvitation[]>([]);
  const [groupInvitations, setGroupInvitations] = useState<ParentGroupInvitation[]>([]);
  const [accountError, setAccountError] = useState('');
  const [guideEnabled, setGuideEnabled] = useState(false);
  const [guideBase64, setGuideBase64] = useState('');
  const [guideBusy, setGuideBusy] = useState(false);
  const [guideError, setGuideError] = useState('');
  const [photo, setPhoto] = useState<SelectedPhoto | null>(null);
  const [audio, setAudioValue] = useState<SelectedAudio | null>(null);
  const [audioAttempted, setAudioAttempted] = useState(false);
  const [transcript, setTranscript] = useState<ParentAudioTranscription | null>(null);
  const [transcriptText, setTranscriptText] = useState('');
  const [transcriptError, setTranscriptError] = useState('');
  const [run, setRun] = useState<StoryRun | null>(null);
  const [candidate, setCandidate] = useState<ParentCandidate | null>(null);
  const [subject, setSubject] = useState('');
  const [understandingRevision, setUnderstandingRevision] = useState(0);
  const [activities, setActivities] = useState<SuggestedActivity[]>([]);
  const [activitySource, setActivitySource] = useState('');
  const [activityAttempted, setActivityAttempted] = useState(false);
  const [activityError, setActivityError] = useState('');
  const [story, setStory] = useState<StoryDraft | null>(null);
  const [storySha256, setStorySha256] = useState('');
  const [storyAttempted, setStoryAttempted] = useState(false);
  const [storyConfirmed, setStoryConfirmed] = useState(false);
  const [rewriteCount, setRewriteCount] = useState(0);
  const [rewriteInstruction, setRewriteInstruction] = useState('');
  const [events, setEvents] = useState<TimedEvent[]>([]);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [authError, setAuthError] = useState('');
  const [bootstrapBusy, setBootstrapBusy] = useState(false);

  async function timeRequest<T>(stage: string, request: () => Promise<T>): Promise<T> {
    const started = Date.now();
    try {
      const result = await request();
      setEvents((items) => [...items, { stage, status: 'PASS', durationMs: Date.now() - started, requestId: requestIdOf(result) }]);
      return result;
    } catch (cause) {
      setEvents((items) => [...items, {
        stage,
        status: 'FAIL',
        durationMs: Date.now() - started,
        requestId: cause instanceof ParentApplicationError ? cause.requestId : undefined,
        code: cause instanceof ParentApplicationError ? cause.code : undefined,
      }]);
      throw cause;
    }
  }

  async function loadParentData(): Promise<void> {
    setBootstrapBusy(true);
    setError('');
    try {
      const user = await application.account.currentUser();
      if (!user) throw new Error('Không tìm thấy phiên đăng nhập.');
      setCurrentUser(user);
      setStep('home');
      const [policyResult, profilesResult, activeResult] = await Promise.allSettled([
        application.profiles.getConsentPolicy(),
        application.profiles.listProfiles(),
        application.learning.getActiveRun(),
      ]);
      if (policyResult.status === 'fulfilled') setPolicy(policyResult.value.policy);
      else setError(displayError(policyResult.reason));
      if (profilesResult.status === 'rejected') {
        setError(displayError(profilesResult.reason));
        return;
      }
      const activeProfiles = profilesResult.value.profiles.filter((item) => item.state === 'ACTIVE');
      setProfiles(activeProfiles);
      if (activeResult.status === 'fulfilled') {
        setActiveRun(activeResult.value.story_run);
        const saved = activeResult.value.story_run;
        if (saved) restoreRun(saved, activeProfiles);
      } else {
        setError((previous) => previous || `Không kiểm tra được buổi đang mở: ${displayError(activeResult.reason)}`);
      }
    } catch (cause) {
      setAuthError(displayError(cause));
    } finally {
      setBootstrapBusy(false);
    }
  }

  function restoreRun(saved: StoryRun, availableProfiles = profiles): void {
    setRun(saved);
    setProfile(availableProfiles.find((item) => item.parent_profile_id === saved.parent_profile_id) ?? null);
    setTopic(saved.context_snapshot.topic);
    setIdea(saved.context_snapshot.adult_confirmed_idea);
    setCandidate(saved.candidate);
    setSubject(saved.subject_label ?? saved.candidate?.candidate_subject ?? '');
    setUnderstandingRevision(saved.understanding_revision ?? 0);
    const parsed = parseStoryDraft(saved.story);
    setStory(parsed);
    setStorySha256(saved.story_sha256 ?? '');
    if (saved.story_status === 'CONFIRMED') setStoryConfirmed(true);
    else if (parsed || saved.candidate) setError('Có một buổi học đang mở. Chọn “Tiếp tục buổi đang mở” ở Trang chủ để quay lại.');
  }

  async function authenticate(action: 'signin' | 'signup', email: string, password: string): Promise<void> {
    setBusy('auth');
    setAuthError('');
    try {
      if (action === 'signin') await application.account.signIn(email, password);
      else await application.account.signUp(email, password);
      await loadParentData();
    } catch (cause) {
      setAuthError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function signInWithGoogle(idToken: string): Promise<void> {
    setBusy('auth');
    setAuthError('');
    try {
      await application.account.signInWithGoogle(idToken);
      await loadParentData();
    } catch (cause) {
      setAuthError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function createProfile(input: { displayName: string; ageMonths: number; interests: string }): Promise<ParentProfile> {
    if (!policy) throw new Error('Chưa tải được nội dung quyền xử lý.');
    setBusy('profile');
    setError('');
    try {
      const response = await application.profiles.create({
        age_months: input.ageMonths,
        display_name: input.displayName.trim(),
        interests_summary: input.interests.trim(),
        consent_accepted: true,
        consent_policy_version: policy.policy_version,
      });
      setProfiles((items) => [response.profile, ...items]);
      setProfile(response.profile);
      return response.profile;
    } catch (cause) {
      setError(displayError(cause));
      throw cause;
    } finally {
      setBusy('');
    }
  }

  async function createProfileAndReturn(input: { displayName: string; ageMonths: number; interests: string }): Promise<ParentProfile> {
    const created = await createProfile(input);
    setStep('profile');
    return created;
  }

  async function updateProfile(input: { displayName: string; ageMonths: number; interests: string }): Promise<ParentProfile> {
    if (!profileBeingEdited) throw new Error('Chưa chọn hồ sơ cần cập nhật.');
    setBusy('profile-update');
    setError('');
    try {
      const { profile: revised } = await application.profiles.revise(profileBeingEdited.parent_profile_id, {
        expected_revision: profileBeingEdited.current_revision.revision,
        age_months: input.ageMonths,
        display_name: input.displayName.trim(),
        interests_summary: input.interests.trim(),
      });
      setProfiles((items) => items.map((item) => item.parent_profile_id === revised.parent_profile_id ? revised : item));
      setProfile(revised);
      setProfileBeingEdited(null);
      setStep('profile');
      return revised;
    } catch (cause) {
      setError(displayError(cause));
      throw cause;
    } finally {
      setBusy('');
    }
  }

  async function authorizeProfile(target: ParentProfile): Promise<void> {
    if (!policy) return;
    setBusy('authorize');
    setError('');
    try {
      const { profile: updated } = await application.profiles.grantAuthorization(target.parent_profile_id, policy.policy_version);
      replaceProfile(updated);
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function revokeProfileAuthorization(target: ParentProfile): Promise<void> {
    setBusy('revoke');
    setError('');
    try {
      const { profile: updated } = await application.profiles.revokeAuthorization(target.parent_profile_id);
      replaceProfile(updated);
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function archiveProfile(target: ParentProfile): Promise<void> {
    setBusy('archive');
    setError('');
    try {
      await application.profiles.archive(target.parent_profile_id);
      setProfiles((items) => items.filter((item) => item.parent_profile_id !== target.parent_profile_id));
      if (profile?.parent_profile_id === target.parent_profile_id) setProfile(null);
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  function replaceProfile(updated: ParentProfile): void {
    setProfiles((items) => items.map((item) => item.parent_profile_id === updated.parent_profile_id ? updated : item));
    if (profile?.parent_profile_id === updated.parent_profile_id) setProfile(updated);
  }

  function continueWithProfile(target: ParentProfile): void {
    setError('');
    if (!target.authorization_current) {
      setError('Cần xác nhận quyền xử lý dữ liệu còn hiệu lực trước khi tiếp tục.');
      return;
    }
    if (activeRun) {
      setError(`Hồ sơ đã có buổi học đang mở (${activeRun.run_state}). Không tạo buổi mới để tránh trùng dữ liệu.`);
      return;
    }
    setProfile(target);
    setStep('topic');
  }

  async function openLessons(mode: 'gallery' | 'picker' = 'picker'): Promise<void> {
    setGalleryMode(mode);
    setGalleryLesson(null);
    setStep(mode === 'gallery' ? 'lesson-library' : 'lessons');
    setLessonLoading(true);
    setLessonError('');
    try {
      const page = await application.lessons.list();
      setLessons(page.items);
      if (mode === 'gallery') {
        const [lessonInvites, groupInvites] = await Promise.allSettled([
          application.lessons.listInvitations(),
          application.lessons.listGroupInvitations(),
        ]);
        if (lessonInvites.status === 'fulfilled') setLessonInvitations(lessonInvites.value.items);
        else setLessonError(displayError(lessonInvites.reason));
        if (groupInvites.status === 'fulfilled') setGroupInvitations(groupInvites.value.items);
        else setLessonError((previous) => previous || displayError(groupInvites.reason));
      }
    } catch (cause) {
      setLessonError(displayError(cause));
    } finally {
      setLessonLoading(false);
    }
  }

  async function chooseLesson(lessonId: string): Promise<void> {
    setLessonLoadingId(lessonId);
    setLessonError('');
    try {
      const detail = await application.lessons.get(lessonId);
      if (galleryMode === 'picker') {
        setLesson(detail);
        setStep('topic');
      } else {
        setGalleryLesson(detail);
      }
    } catch (cause) {
      setLessonError(displayError(cause));
    } finally {
      setLessonLoadingId('');
    }
  }

  async function acceptLessonInvitation(invitationId: string): Promise<void> {
    await respondToInvitation(() => application.lessons.acceptInvitation(invitationId));
  }

  async function declineLessonInvitation(invitationId: string): Promise<void> {
    await respondToInvitation(() => application.lessons.declineInvitation(invitationId));
  }

  async function acceptGroupInvitation(membershipId: string): Promise<void> {
    await respondToInvitation(() => application.lessons.acceptGroupInvitation(membershipId));
  }

  async function respondToInvitation(action: () => Promise<unknown>): Promise<void> {
    try {
      await action();
      await openLessons('gallery');
    } catch (cause) {
      setLessonError(displayError(cause));
    }
  }

  async function createGuide(): Promise<void> {
    if (!guideEnabled || !topic.trim()) return;
    setGuideBusy(true);
    setGuideError('');
    try {
      const receipt = await timeRequest('FLUX.3 · line-sketch', () => application.learning.generateSketchGuide(topic.trim()));
      if (!receipt.image_base64) throw new Error('Modal không trả về ảnh line-sketch.');
      setGuideBase64(receipt.image_base64);
    } catch (cause) {
      setGuideError(displayError(cause));
    } finally {
      setGuideBusy(false);
    }
  }

  function setAudio(value: SelectedAudio | null): void {
    setAudioValue(value);
    setAudioAttempted(false);
    setTranscript(null);
    setTranscriptText('');
    setTranscriptError('');
  }

  async function confirmContextAndAnalyze(): Promise<void> {
    if (busy) return;
    if (!profile || !policy || !photo) {
      setError('Chọn hồ sơ, xác nhận quyền và chụp ảnh trước khi tiếp tục.');
      return;
    }
    if (activeRun && activeRun.run_id !== run?.run_id) {
      setError(`Đã có buổi học đang mở (${activeRun.run_state}); không tạo thêm buổi mới.`);
      return;
    }
    let currentRun = run;
    try {
      setError('');
      if (!currentRun) {
        setBusy('understanding');
        const { story_run: createdRun } = await application.learning.createRunForDrawing({
          profile,
          policyVersion: policy.policy_version,
          topic,
          adultIdea: idea,
          imageBase64: photo.base64,
          contextConfirmed: true,
          lesson,
        });
        currentRun = createdRun;
        setRun(createdRun);
        setActiveRun(createdRun);
      }

      if (audio && !audioAttempted) {
        const audioRun = currentRun;
        if (!audioRun) throw new Error('Không tạo được buổi học để gắn bản ghi âm.');
        setAudioAttempted(true);
        setTranscript(null);
        setTranscriptText('');
        setTranscriptError('');
        setStep('transcript-review');
        setBusy('transcription');
        try {
          const receipt = await timeRequest('Whisper · nhận dạng ý tưởng', () => application.learning.transcribeAudio(
            audioRun.run_id,
            { uri: audio.uri, file_name: audio.fileName, media_type: audio.mediaType },
          ));
          setTranscript(receipt);
          setTranscriptText(receipt.transcript_raw);
        } catch (cause) {
          setTranscriptError(displayError(cause));
        } finally {
          setBusy('');
        }
        return;
      }

      await analyzeDrawingForRun(currentRun);
    } catch (cause) {
      setError(displayError(cause));
      setBusy('');
    }
  }

  async function analyzeDrawingForRun(targetRun: StoryRun): Promise<void> {
    if (!photo) return;
    setBusy('understanding');
    setError('');
    try {
      const understanding = await timeRequest(
        'Qwen3.5-VL · hiểu tranh',
        () => application.learning.understandDrawing(targetRun.run_id, photo.base64, photo.mediaType),
      );
      if (!understanding.candidate) throw new Error('API phản hồi nhưng thiếu candidate chủ thể.');
      setCandidate(understanding.candidate);
      setSubject(understanding.candidate.candidate_subject ?? '');
      setUnderstandingRevision(understanding.understanding_revision ?? 1);
      setStep('understanding');
    } catch (cause) {
      try {
        const [latestRun, latestActiveRun] = await Promise.all([
          application.learning.getRun(targetRun.run_id),
          application.learning.getActiveRun(),
        ]);
        setRun(latestRun.story_run);
        setActiveRun(latestActiveRun.story_run);
      } catch {
        // Preserve the original AI failure when the follow-up state refresh also fails.
      }
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function confirmReviewedTranscript(): Promise<void> {
    if (busy) return;
    if (!run || !transcript) {
      setTranscriptError('Chưa có bản nhận dạng để xác nhận. Bạn có thể tiếp tục không dùng âm thanh.');
      return;
    }
    setTranscriptError('');
    setBusy('transcript-confirmation');
    let confirmedText: string | null = null;
    try {
      const receipt = await timeRequest('Parent · xác nhận transcript', () => application.learning.confirmTranscript(
        run.run_id,
        transcript.transcript_revision_no,
        transcriptText,
      ));
      confirmedText = receipt.transcript_text;
      setIdea(receipt.transcript_text);
    } catch (cause) {
      setTranscriptError(displayError(cause));
    } finally {
      setBusy('');
    }
    if (confirmedText !== null) await analyzeDrawingForRun(run);
  }

  async function continueWithoutAudio(): Promise<void> {
    if (!run) {
      setTranscriptError('Chưa tạo được buổi học. Quay lại bước xác nhận rồi thử tiếp.');
      return;
    }
    setTranscript(null);
    setTranscriptText('');
    await analyzeDrawingForRun(run);
  }

  async function confirmSubject(): Promise<void> {
    if (!run || !candidate || !subject.trim() || !understandingRevision) return;
    setBusy('subject');
    setError('');
    try {
      const response = await application.learning.confirmSubject(run.run_id, understandingRevision, subject.trim());
      setUnderstandingRevision(response.understanding_revision);
      setRun((current) => current ? { ...current, subject_label: subject.trim(), run_state: 'PREPARATION_REVIEW' } : current);
      setCandidate({ ...candidate, candidate_subject: subject.trim(), decision: 'CONFIRMED_BY_ADULT' });
      setActivityAttempted(false);
      setActivities([]);
      setActivityError('');
      setStep('activity');
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function requestActivities(): Promise<void> {
    if (!run || !understandingRevision || activityAttempted) return;
    setActivityAttempted(true);
    setBusy('activity');
    setActivityError('');
    try {
      const receipt = await timeRequest(
        'Qwen3.5 · chọn hoạt động phù hợp',
        () => application.learning.suggestActivities(run.run_id, understandingRevision),
      );
      setActivities(receipt.activities);
      setActivitySource(receipt.selection_mode);
    } catch (cause) {
      setActivityError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function requestStory(instruction?: string): Promise<void> {
    if (!run || !understandingRevision || (storyAttempted && !instruction) || (rewriteCount >= 3 && instruction)) return;
    setStoryAttempted(true);
    if (instruction) setRewriteCount((count) => count + 1);
    setBusy(instruction ? 'rewrite' : 'story');
    setError('');
    try {
      const { updatedRun, parsed, hash } = await timeRequest(
        instruction ? 'Qwen3.5 · viết lại kịch bản' : 'Qwen3.5 · tạo kịch bản',
        async () => {
          const receipt = await application.learning.generateStory(run.run_id, understandingRevision, instruction, rewriteCount);
          const nextRun = receipt.story_run ?? (await application.learning.getRun(run.run_id)).story_run;
          const parsedStory = parseStoryDraft(receipt.story ?? nextRun.story);
          if (!parsedStory) throw new Error('Story không khớp schema story-revision.v1 (cần 5–15 cảnh, 30–90 giây).');
          const storyHash = receipt.story_sha256 ?? nextRun.story_sha256 ?? '';
          if (!storyHash) throw new Error('Story response thiếu story_sha256.');
          return { updatedRun: nextRun, parsed: parsedStory, hash: storyHash };
        },
      );
      setRun(updatedRun);
      setStory(parsed);
      setStorySha256(hash);
      setRewriteInstruction('');
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function confirmStory(): Promise<void> {
    if (!run || !story || !storySha256 || !run.story_revision_no) return;
    setBusy('confirm-story');
    setError('');
    try {
      const receipt = await application.learning.confirmStory(run.run_id, run.story_revision_no, storySha256);
      setRun(receipt.story_run);
      setActiveRun(receipt.story_run);
      setStoryConfirmed(true);
      setStep('handoff');
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  function resumeActiveRun(): void {
    if (!activeRun) return;
    restoreRun(activeRun);
    if (activeRun.story_status === 'CONFIRMED') setStep('handoff');
    else if (parseStoryDraft(activeRun.story)) setStep('story');
    else if (activeRun.candidate) setStep('understanding');
    else setError('Buổi đang mở chưa có dữ liệu đủ để khôi phục màn tiếp theo. Không tạo buổi mới để tránh trùng.');
  }

  async function changePassword(currentPassword: string, nextPassword: string): Promise<void> {
    setAccountError('');
    setBusy('password');
    try {
      await application.account.changePassword(currentPassword, nextPassword);
    } catch (cause) {
      setAccountError(displayError(cause));
      throw cause;
    } finally {
      setBusy('');
    }
  }

  async function resetCurrentPassword(): Promise<void> {
    if (!currentUser?.email) throw new Error('Không có email đăng nhập để gửi hướng dẫn.');
    await application.account.resetPassword(currentUser.email);
  }

  async function resetPassword(email: string): Promise<void> {
    await application.account.resetPassword(email);
  }

  async function signOut(): Promise<void> {
    await application.account.signOut();
    setCurrentUser(null);
    setProfiles([]);
    setProfile(null);
    setPolicy(null);
    setActiveRun(null);
    setStep('auth');
    setAuthError('');
    resetWorkflow();
  }

  function resetWorkflow(): void {
    setTopic(''); setIdea(''); setLesson(null); setPhoto(null); setRun(null); setCandidate(null); setSubject('');
    setAudioValue(null); setAudioAttempted(false); setTranscript(null); setTranscriptText(''); setTranscriptError('');
    setUnderstandingRevision(0); setActivities([]); setActivitySource(''); setActivityAttempted(false); setActivityError('');
    setStory(null); setStorySha256(''); setStoryAttempted(false); setStoryConfirmed(false); setRewriteCount(0); setRewriteInstruction('');
    setGuideBase64(''); setGuideEnabled(false); setEvents([]); setError(''); setBusy('');
  }

  return {
    step, setStep, policy, currentUser, profiles, profile, setProfile, profileBeingEdited, setProfileBeingEdited,
    publicSettings: application.publicSettings,
    activeRun, topic, setTopic, idea, setIdea, lesson, setLesson, lessons, lessonLoading, lessonLoadingId, lessonError,
    galleryMode, galleryLesson, lessonInvitations, groupInvitations, accountError, guideEnabled, setGuideEnabled,
    guideBase64, guideBusy, guideError, photo, setPhoto, audio, setAudio, transcript, transcriptText, setTranscriptText,
    transcriptError, audioAttempted, transcriptBusy: busy === 'transcription' || busy === 'transcript-confirmation',
    run, candidate, subject, setSubject, understandingRevision,
    activities, activitySource, activityAttempted, activityError, story, storySha256, storyAttempted,
    storyConfirmed, rewriteCount, rewriteInstruction, setRewriteInstruction, events, busy, error, authError, bootstrapBusy,
    loadParentData, authenticate, signInWithGoogle, resetPassword, createProfileAndReturn, updateProfile, authorizeProfile,
    revokeProfileAuthorization, archiveProfile, continueWithProfile, openLessons, chooseLesson, acceptLessonInvitation,
    declineLessonInvitation, acceptGroupInvitation, createGuide, confirmContextAndAnalyze,
    confirmReviewedTranscript, continueWithoutAudio, confirmSubject,
    requestActivities, requestStory, confirmStory, resumeActiveRun, changePassword, resetCurrentPassword, signOut,
    resetWorkflow, backToProfile: () => { setStep('profile'); setError(''); },
    clearError: () => setError(''),
  };
}

function displayError(cause: unknown): string {
  if (cause instanceof ParentApplicationError) {
    return `${cause.message} · ${cause.code}${cause.requestId ? ` · ${cause.requestId}` : ''}`;
  }
  return cause instanceof Error ? cause.message : 'Có lỗi không xác định.';
}

function requestIdOf(value: unknown): string | undefined {
  if (typeof value === 'object' && value !== null && 'request_id' in value) {
    const requestId = (value as { request_id?: unknown }).request_id;
    return typeof requestId === 'string' ? requestId : undefined;
  }
  return undefined;
}
