import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {classifyApiResponseError} from '../src/demo/apiResponseError.mjs';
import {buildP1ContextOptionsRequest} from '../src/demo/p1ContextOptionsRequest.mjs';
import {buildP1ActivitySuggestionsRequest} from '../src/demo/p1ActivitySuggestionsRequest.mjs';
import {buildP1ContextRequest} from '../src/demo/p1ContextRequest.mjs';
import {
  adjustChildAgeByMonths,
  adjustChildAgeByYears,
  formatChildAge,
  splitChildAgeMonths,
} from '../src/demo/childAge.mjs';
import {
  acceptPreferenceClassification,
  PREFERENCE_CLASSIFICATION_ATTEMPT_LIMIT,
  PreferenceRevisionGate,
} from '../src/demo/preferenceRevisionGate.mjs';
import {resetSessionBoundProfileAnswers} from '../src/demo/sessionProfileAnswers.mjs';

const root = resolve(import.meta.dirname, '..');
const files = [
  'BaoApp.tsx',
  'src/screens/Flow1Screens.tsx',
  'src/screens/Flow2Screens.tsx',
  'src/context/AppContext.tsx',
];
const forbiddenVisibleTerms = [
  'Lightning',
  'ExperienceSpec',
  'Pixi protocol',
  'Fine Motor',
  'Backend ',
];

for (const relativePath of files) {
  const source = readFileSync(resolve(root, relativePath), 'utf8');
  for (const term of forbiddenVisibleTerms) {
    if (source.includes(term)) {
      throw new Error(`${relativePath} still contains child-facing technical copy: ${term}`);
    }
  }
}

const flow1 = readFileSync(resolve(root, 'src/screens/Flow1Screens.tsx'), 'utf8');
const flow2 = readFileSync(resolve(root, 'src/screens/Flow2Screens.tsx'), 'utf8');
const shell = readFileSync(resolve(root, 'BaoApp.tsx'), 'utf8');
const appContext = readFileSync(resolve(root, 'src/context/AppContext.tsx'), 'utf8');
const apiClient = readFileSync(resolve(root, 'src/demo/api.ts'), 'utf8');
const removedActivityGateCopy = [
  'Bắt đầu kiểm tra',
  'Kiểm tra điều kiện của nhóm nhỏ',
  'Xác nhận điều kiện & xem gợi ý',
  'Bé đã thể hiện được hành vi nào?',
  'Vật liệu nào đang có?',
  'Tôi xác nhận có thể bảo đảm mức giám sát này cho hoạt động',
];
if (
  removedActivityGateCopy.some((copy) => flow2.includes(copy))
  || !flow2.includes('void prepareActivityWorkflow()')
  || !flow2.includes('activityRecommendationCards.map')
  || !flow2.includes("onPress={() => nav('profile')}")
  || !appContext.includes('workflowApi.readActivitySuggestions(')
  || appContext.includes('readiness_ids: profile.readiness_ids ?? []')
  || appContext.includes('available_material_option_ids: profile.available_material_option_ids ?? []')
  || !flow2.includes('toàn bộ hoạt động đã duyệt, đúng chủ đề và độ tuổi')
) {
  throw new Error('Activity entry must automatically show the complete topic/age list, without readiness/material filters or an intermediate checklist.');
}
if (
  splitChildAgeMonths(35).years !== 2
  || splitChildAgeMonths(35).months !== 11
  || splitChildAgeMonths(36).years !== 3
  || splitChildAgeMonths(155).years !== 12
  || splitChildAgeMonths(155).months !== 11
  || adjustChildAgeByMonths(35, 1) !== 36
  || adjustChildAgeByMonths(155, 1) !== 155
  || adjustChildAgeByMonths(0, -1) !== 0
  || adjustChildAgeByYears(35, 1) !== 47
  || adjustChildAgeByYears(155, 1) !== 155
  || formatChildAge(35) !== '2 tuổi 11 tháng'
  || formatChildAge(36) !== '3 tuổi'
) {
  throw new Error('Exact child-age input must preserve completed-month boundaries and stay within the SRS 0–155 month range.');
}
const requestProfile = {
  profile_declared_by: 'CAREGIVER',
  profile_recorded_at: '2026-09-30T00:00:00Z',
  interest_text: 'synthetic test only',
  avoid_text: '',
  proposed_interest_tags: [],
  proposed_avoid_tags: [],
  preference_tags_confirmed: false,
  interests: ['ANIMAL_GENERIC'],
  dislikes: [],
  readiness_ids: [],
  available_material_option_ids: ['MAT_PLANT_TRAY', 'GMAT-0055-PRIMARY'],
  adult_participating: true,
  caregiver_participating: null,
  learning_support_ids: [],
};
const sessionAnswersReset = resetSessionBoundProfileAnswers({
  ...requestProfile,
  adult_participating: true,
  caregiver_participating: true,
  readiness_ids: ['READY_HANDLES_PLANT_SAMPLE'],
  available_material_option_ids: ['MAT_PLANT_TRAY'],
});
if (
  sessionAnswersReset.adult_participating !== null
  || sessionAnswersReset.caregiver_participating !== null
  || sessionAnswersReset.readiness_ids !== null
  || sessionAnswersReset.available_material_option_ids !== null
  || sessionAnswersReset.interest_text !== requestProfile.interest_text
  || sessionAnswersReset.interests !== requestProfile.interests
  || sessionAnswersReset.preference_tags_confirmed !== requestProfile.preference_tags_confirmed
) {
  throw new Error('Ending a workflow must clear session-specific confirmation/readiness/material answers while retaining stable profile declarations.');
}
const mobileContextRequest = buildP1ContextOptionsRequest({
  ageMonths: 60,
  childProfile: requestProfile,
  candidateActivityIds: ['ACT-0001'],
  supervisionConfirmedActivityIds: ['ACT-0001'],
});
const unconfirmedSuggestionsRequest = buildP1ActivitySuggestionsRequest({
  ageMonths: 60,
  childProfile: requestProfile,
});
const confirmedSuggestionsRequest = buildP1ActivitySuggestionsRequest({
  ageMonths: 60,
  childProfile: {
    ...requestProfile,
    preference_tags_confirmed: true,
    interests: ['ANIMAL_GENERIC'],
  },
});
const olderP1ContextRequest = buildP1ContextRequest({
  sessionId: 'session-fixture',
  expectedSessionVersion: 2,
  context: {age_months: 36, caregiver_participating: true},
});
const underThreeP1ContextRequest = buildP1ContextRequest({
  sessionId: 'session-fixture',
  expectedSessionVersion: 2,
  context: {age_months: 35, caregiver_participating: true},
});
const contextualP1ContextRequest = buildP1ContextRequest({
  sessionId: 'session-fixture',
  expectedSessionVersion: 2,
  context: {age_months: 60, contextual_candidate_flow: true},
});
const completeListP1ContextRequest = buildP1ContextRequest({
  sessionId: 'session-fixture',
  expectedSessionVersion: 2,
  context: {
    age_months: 60,
    complete_activity_discovery_flow: true,
    adult_participating: true,
    caregiver_participating: false,
    readiness_ids: null,
    completed_activity_ids: null,
    available_material_option_ids: null,
    supervision_level: null,
    policy_flags: null,
    candidate_status: null,
    selected_activity_id: 'ACT-0102',
    selected_activity_version: 1,
  },
});
if (
  mobileContextRequest.contract_name !== 'P1ContextOptionsRequestV2'
  || mobileContextRequest.child_profile.available_material_option_ids.join(',')
    !== 'MAT_PLANT_TRAY,GMAT-0055-PRIMARY'
  || mobileContextRequest.child_profile.interests.length !== 0
  || mobileContextRequest.child_profile.preference_tags_confirmed !== false
  || mobileContextRequest.child_profile.interest_text !== undefined
  || mobileContextRequest.adult_participating !== true
  || mobileContextRequest.caregiver_participating !== false
  || mobileContextRequest.candidate_activity_ids.join(',') !== 'ACT-0001'
  || !apiClient.includes('JSON.stringify(buildP1ContextOptionsRequest({')
  || olderP1ContextRequest.contract_name !== 'P1ContextV1'
  || Object.hasOwn(olderP1ContextRequest, 'caregiver_participating')
  || underThreeP1ContextRequest.contract_name !== 'P1ContextV2'
  || underThreeP1ContextRequest.caregiver_participating !== true
  || contextualP1ContextRequest.contract_name !== 'P1ContextV3'
  || contextualP1ContextRequest.candidate_selection_mode !== 'CONTEXTUAL_SHORTLIST'
  || contextualP1ContextRequest.contextual_candidate_flow !== undefined
  || unconfirmedSuggestionsRequest.child_profile.interests.length !== 0
  || unconfirmedSuggestionsRequest.child_profile.dislikes.length !== 0
  || unconfirmedSuggestionsRequest.child_profile.interest_text !== undefined
  || unconfirmedSuggestionsRequest.child_profile.readiness_ids !== undefined
  || unconfirmedSuggestionsRequest.child_profile.available_material_option_ids !== undefined
  || confirmedSuggestionsRequest.child_profile.interests.join(',') !== 'ANIMAL_GENERIC'
  || confirmedSuggestionsRequest.child_profile.preference_tags_confirmed !== true
  || completeListP1ContextRequest.contract_name !== 'P1ContextV4'
  || completeListP1ContextRequest.candidate_selection_mode !== 'COMPLETE_TOPIC_AGE_LIST'
  || completeListP1ContextRequest.discovery_policy !== 'TOPIC_AGE_SAFETY_DISCOVERY_V1'
  || completeListP1ContextRequest.readiness_ids !== null
  || completeListP1ContextRequest.available_material_option_ids !== null
  || !apiClient.includes("/p1/activity-suggestions")
  || !apiClient.includes('buildP1ContextRequest({')
) {
  throw new Error('The new activity-discovery serializers must keep unconfirmed/raw preferences and removed readiness/material answers out of the request while using P1ContextV4.');
}
if (
  flow1.includes('selectedAgeGroup')
  || flow1.includes('setSelectedAgeGroup')
  || !flow1.includes('Tuổi hiện tại của bé')
  || !flow1.includes('Người chăm sóc sẽ ở bên và giám sát trực tiếp')
  || !flow1.includes('caregiver_participating: confirmed ? null : true')
  || !flow1.includes('const isUnderThree = selectedAgeMonths < 36')
  || !appContext.includes('const ageMonths = selectedAgeMonths')
) {
  throw new Error('The child profile must use exact age and explicitly gate under-three caregiver supervision through the main flow.');
}
const saveFeedbackStart = appContext.indexOf('const saveFeedback = async');
const saveFeedbackEnd = appContext.indexOf('const toggleAnalysisClaim', saveFeedbackStart);
const saveFeedbackImplementation = appContext.slice(saveFeedbackStart, saveFeedbackEnd);
if (
  saveFeedbackStart < 0
  || saveFeedbackEnd < 0
  || !saveFeedbackImplementation.includes('resetSessionBoundProfileAnswers(selectedChildLearningProfile)')
  || !saveFeedbackImplementation.includes("setSessionState('FEEDBACK_RECORDED')")
) {
  throw new Error('A completed workflow must clear session-specific adult/readiness/material answers before the next exploration.');
}
const classifierStart = appContext.indexOf('const classifySelectedChildPreferences = async');
const classifierEnd = appContext.indexOf('const resetSelectedChildLearningProfile =', classifierStart);
const classifierImplementation = appContext.slice(classifierStart, classifierEnd);
if (
  classifierStart < 0
  || classifierEnd < 0
  || classifierImplementation.includes('setChildLearningProfiles')
  || classifierImplementation.includes('proposed_interest_tags')
) {
  throw new Error('The classifier request must not mutate profile tags before the UI accepts its revision.');
}

const revisionGate = new PreferenceRevisionGate();
const firstRevision = revisionGate.current();
if (
  !revisionGate.canClassify()
  || !revisionGate.beginAttempt(firstRevision)
  || revisionGate.beginAttempt(firstRevision)
  || !revisionGate.markClassified(firstRevision)
  || revisionGate.canClassify()
) {
  throw new Error('A successfully classified preference revision must not submit twice.');
}
const proposal = {
  interest_tags: [{ concept_id: 'ANIMAL_GENERIC', label_vi: 'Động vật', confidence: 0.9 }],
  avoid_tags: [],
};
const staleCommitGate = new PreferenceRevisionGate();
const staleCommitRevision = staleCommitGate.current();
staleCommitGate.beginAttempt(staleCommitRevision);
staleCommitGate.advance();
if (
  acceptPreferenceClassification(
    staleCommitGate,
    staleCommitRevision,
    'child-a',
    'child-a',
    proposal,
  ) !== null
) {
  throw new Error('A stale classifier result must not produce a profile patch.');
}
const switchedChildGate = new PreferenceRevisionGate();
const switchedChildRevision = switchedChildGate.current();
switchedChildGate.beginAttempt(switchedChildRevision);
if (
  acceptPreferenceClassification(
    switchedChildGate,
    switchedChildRevision,
    'child-b',
    'child-a',
    proposal,
  ) !== null
) {
  throw new Error('A classifier result must not be applied after the active child changes.');
}
const acceptedGate = new PreferenceRevisionGate();
const acceptedRevision = acceptedGate.current();
acceptedGate.beginAttempt(acceptedRevision);
const acceptedPatch = acceptPreferenceClassification(
  acceptedGate,
  acceptedRevision,
  'child-a',
  'child-a',
  proposal,
);
if (
  !acceptedPatch
  || acceptedPatch.interests[0] !== 'ANIMAL_GENERIC'
  || acceptedPatch.preference_tags_confirmed !== false
) {
  throw new Error('A current classifier result must create an adult-unconfirmed proposal patch.');
}
const editedRevision = revisionGate.advance();
if (editedRevision === firstRevision || !revisionGate.canClassify() || !revisionGate.beginAttempt(editedRevision)) {
  throw new Error('Edited preference text must allow one new classification.');
}
const newerRevision = revisionGate.advance();
if (revisionGate.markClassified(editedRevision) || !revisionGate.canClassify()) {
  throw new Error('A stale classifier response must not complete a newer preference revision.');
}
if (
  !revisionGate.beginAttempt(newerRevision)
  || !revisionGate.markFailed(newerRevision)
  || revisionGate.canClassify()
  || revisionGate.beginAttempt(newerRevision)
) {
  throw new Error(`A preference revision must make at most ${PREFERENCE_CLASSIFICATION_ATTEMPT_LIMIT} classifier request.`);
}
revisionGate.advance();
if (!revisionGate.canClassify()) throw new Error('Editing after failed attempts must open one fresh revision.');
revisionGate.reset();
if (!revisionGate.canClassify()) {
  throw new Error('Changing child/profile must reset the classification revision gate.');
}

if (!flow1.includes('KeyboardAvoidingView') || !flow2.includes('KeyboardAvoidingView')) {
  throw new Error('Narration and feedback inputs must retain keyboard avoidance.');
}

const validValidation = classifyApiResponseError({
  body: { detail: [{ loc: ['body', 'profile'], type: 'value_error' }] },
  statusCode: 422,
  isJson: true,
});
const proxyValidation = classifyApiResponseError({
  body: null,
  statusCode: 422,
  isJson: false,
});
const proxyGateway = classifyApiResponseError({
  body: null,
  statusCode: 502,
  isJson: false,
});
const invalidSuccess = classifyApiResponseError({
  body: null,
  statusCode: 200,
  isJson: false,
  responseOk: true,
});
const invalidJsonSuccess = classifyApiResponseError({
  body: null,
  statusCode: 200,
  isJson: true,
  responseOk: true,
});
const typedFailure = classifyApiResponseError({
  body: { failure: { code: 'CLASSIFIER_UNAVAILABLE', safe_message: 'Dịch vụ AI chưa sẵn sàng.', retryable: true } },
  statusCode: 200,
  isJson: true,
});
const typedValidationFailure = classifyApiResponseError({
  body: {
    contract_name: 'MobileWorkflowResultV1',
    status: 'FAILED',
    failure: {
      code: 'REQUEST_VALIDATION_FAILED',
      safe_message: 'Một số thông tin hồ sơ chưa hợp lệ.',
      retryable: false,
    },
  },
  statusCode: 422,
  isJson: true,
});
if (
  validValidation.code !== 'REQUEST_VALIDATION_FAILED'
  || proxyValidation.code !== 'VALIDATION_RESPONSE_UNRECOGNIZED'
  || proxyGateway.code !== 'UPSTREAM_UNAVAILABLE'
  || invalidSuccess.code !== 'NON_JSON_RESPONSE'
  || invalidJsonSuccess.code !== 'INVALID_RESPONSE'
  || typedFailure.code !== 'CLASSIFIER_UNAVAILABLE'
  || typedFailure.retryable !== true
  || typedValidationFailure.code !== 'REQUEST_VALIDATION_FAILED'
  || typedValidationFailure.retryable !== false
  || typedValidationFailure.message !== 'Một số thông tin hồ sơ chưa hợp lệ.'
  || validValidation.message === proxyValidation.message
  || apiClient.includes('Backend returned an unreadable response.')
  || !apiClient.includes('await response.text()')
  || !apiClient.includes('classifyApiResponseError')
) {
  throw new Error('API errors must distinguish typed validation, proxy/non-JSON, upstream and invalid-success responses without exposing response bodies.');
}
if (!flow2.includes('Bức vẽ gốc của con vẫn an toàn ở đây.')) {
  throw new Error('Pixi failure must keep the original drawing visible.');
}
if (!flow2.includes('Dành cho người lớn') || !flow2.includes('Thử lại')) {
  throw new Error('Adult details and renderer recovery actions must remain available.');
}
if (!shell.includes('Về bước ảnh') || !shell.includes('Đóng') || !flow2.includes('Thử lại')) {
  throw new Error('Workflow errors must expose a truthful dismiss action and explicit screen-level retry.');
}
if (
  !flow2.includes("nav('pixi_intro')")
  || !flow2.includes("nav('video_placeholder')")
  || !flow2.includes("nav('activity_detail')")
) {
  throw new Error('Gate B, Pixi intro, video placeholder and outdoor activity order must remain explicit.');
}
if (
  !flow2.includes('OrientationLock.LANDSCAPE')
  || !flow2.includes('OrientationLock.PORTRAIT_UP')
  || !flow2.includes('RendererControlCommandSchema')
) {
  throw new Error('Landscape lifecycle and bounded Pixi playback controls must remain wired.');
}
if (!flow2.includes('Video chính sẽ được thêm ở phiên bản sau')) {
  throw new Error('The future-video surface must remain an honest placeholder.');
}
if (!flow2.includes('Đang tạo các hướng câu chuyện')) {
  throw new Error('Understanding must expose stage-aware loading instead of a frozen percentage.');
}
if (
  !flow1.includes('interest_unmapped')
  || !flow1.includes('avoid_unmapped')
  || !flow1.includes('classifiedPreferenceRevision')
  || !flow1.includes('PREFERENCE_CLASSIFICATION_ATTEMPT_LIMIT')
  || !flow1.includes('FEAT033_PROFILE_INPUT_P95')
  || !flow1.includes('if (!__DEV__)')
  || !flow1.includes('acceptPreferenceClassification')
  || !flow1.includes('sửa nội dung để chạy lại')
) {
  throw new Error('Preference classification/revision safeguards and dev-only, text-free input profiling must remain wired.');
}

console.log('UI_COPY_AND_RECOVERY_VALID');
