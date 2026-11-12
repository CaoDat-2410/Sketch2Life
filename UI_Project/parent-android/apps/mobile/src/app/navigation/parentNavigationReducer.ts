import type {ParentAppState, ParentChildProfile, ParentNavigationAction, ParentProfileContext, ParentRoute} from './parentRoutes';
import {parentMainRoutes} from './parentRoutes';

const blankContext = (): ParentProfileContext => ({interests: '', observations: '', achievements: '', outsideAppExperiences: ''});

const previewProfiles: readonly ParentChildProfile[] = [
  {id: 'child-demo-01', name: 'Bé Mây', age: '5 tuổi', color: '#E3F0E5', lifecycle: 'active', context: {interests: 'Cây cối, côn trùng', observations: 'Thích kể về những điều con nhìn thấy', achievements: '', outsideAppExperiences: 'Cùng gia đình chăm một chậu cây nhỏ'}},
  {id: 'child-demo-02', name: 'Bé An', age: '4 tuổi', color: '#F9EBDD', lifecycle: 'active', context: blankContext()},
];

export function createInitialParentState(): ParentAppState {
  return {
    route: 'login',
    history: [],
    previewMode: false,
    childId: 'child-demo-01',
    childName: 'Bé Mây',
    childAge: '5 tuổi',
    childProfiles: previewProfiles,
    activeRunChild: null,
    activeRunLesson: null,
    lessonId: null,
    lessonTitle: null,
    lessonVersion: null,
    scriptFollowingChoice: 'unset',
    suggestedActivityId: null,
    lineSketchEnabled: false,
    idea: '',
    transcript: '',
    subject: 'Con bướm',
    contextApproved: false,
    contextIncludedFields: [],
    rewritePrompt: '',
    rewriteCount: 0,
    storyConfirmed: false,
    generationState: 'not-requested',
    runCancelPending: false,
    videoReviewReason: '',
    videoRegenerationCount: 0,
    videoRegenerationPending: false,
    previousVideoHidden: false,
    pushPreference: 'not-enabled',
    feedbackRating: 0,
    feedbackNote: '',
    notice: null,
  };
}

export function reduceParentNavigation(
  state: ParentAppState,
  action: ParentNavigationAction,
): ParentAppState {
  switch (action.type) {
    case 'NAVIGATE': {
      if (action.route === 'activities' && state.generationState !== 'ready-preview') {
        return {...state, notice: 'Hoạt động chỉ xuất hiện sau khi video đã sẵn sàng.'};
      }
      if (action.route === 'video-player' && state.runCancelPending) {
        return {...state, notice: 'Run đang chờ xử lý hủy; chưa mở player trong preview.'};
      }
      if (action.route === 'video-player' && state.previousVideoHidden) {
        return {...state, notice: 'Video cũ đã được ẩn trong trạng thái preview tạo lại.'};
      }
      if (action.route === 'video-player' && state.generationState !== 'ready-preview') {
        return {...state, notice: 'Video chưa qua kiểm tra kỹ thuật và an toàn.'};
      }
      if (action.route === 'video-review' && (state.generationState !== 'ready-preview' || state.previousVideoHidden || state.runCancelPending)) {
        return {...state, notice: 'Chỉ có thể phản hồi sau khi kết quả video đã sẵn sàng trong preview.'};
      }
      if (action.route === state.route) return state;
      const history = parentMainRoutes.includes(action.route)
        ? []
        : [...state.history, state.route];
      return {...state, route: action.route, history, notice: null};
    }
    case 'BACK': {
      const previous = state.history[state.history.length - 1];
      if (previous) return {...state, route: previous, history: state.history.slice(0, -1), notice: null};
      return {...state, route: state.previewMode ? 'home' : 'login', notice: null};
    }
    case 'ENTER_PREVIEW':
      return {...createInitialParentState(), route: 'home', previewMode: true};
    case 'EXIT_PREVIEW':
      return {...createInitialParentState(), route: 'login'};
    case 'SELECT_CHILD':
      if (state.activeRunChild) {
        return {...state, notice: 'Run đã gắn với một hồ sơ trẻ; hãy hoàn tất hoặc hủy trước khi đổi hồ sơ.'};
      }
      if (!state.childProfiles.some((profile) => profile.id === action.id && profile.lifecycle === 'active')) {
        return {...state, notice: 'Hồ sơ này không còn khả dụng cho run mới.'};
      }
      return {...state, childId: action.id, childName: action.name, childAge: action.age, contextIncludedFields: [], contextApproved: false, notice: null};
    case 'SAVE_CHILD_PROFILE': {
      if (state.activeRunChild) return {...state, notice: 'Hãy hoàn tất hoặc hủy run trước khi sửa hồ sơ.'};
      const exists = state.childProfiles.some((profile) => profile.id === action.profile.id);
      const childProfiles = exists
        ? state.childProfiles.map((profile) => profile.id === action.profile.id ? action.profile : profile)
        : [...state.childProfiles, action.profile];
      const selected = action.profile.id === state.childId;
      return {
        ...state,
        childProfiles,
        ...(selected ? {childName: action.profile.name, childAge: action.profile.age} : {}),
        contextIncludedFields: selected ? [] : state.contextIncludedFields,
        contextApproved: selected ? false : state.contextApproved,
        notice: null,
      };
    }
    case 'ARCHIVE_CHILD_PROFILE':
      return {...state, childProfiles: state.childProfiles.map((profile) => profile.id === action.id ? {...profile, lifecycle: 'archived'} : profile), notice: null};
    case 'RESTORE_CHILD_PROFILE':
      return {...state, childProfiles: state.childProfiles.map((profile) => profile.id === action.id ? {...profile, lifecycle: 'active'} : profile), notice: 'Đã khôi phục trong phiên preview; chưa thay đổi dữ liệu thật.'};
    case 'REQUEST_CHILD_PROFILE_DELETE': {
      const target = state.childProfiles.find((profile) => profile.id === action.id);
      if (!target || target.lifecycle === 'delete-pending') return state;
      const childProfiles = state.childProfiles.map((profile) => profile.id === action.id ? {...profile, lifecycle: 'delete-pending' as const} : profile);
      const nextProfile = childProfiles.find((profile) => profile.lifecycle === 'active');
      const isRunChild = state.activeRunChild?.id === action.id;
      return {
        ...state,
        childProfiles,
        ...(state.childId === action.id && nextProfile ? {childId: nextProfile.id, childName: nextProfile.name, childAge: nextProfile.age} : {}),
        contextIncludedFields: state.childId === action.id ? [] : state.contextIncludedFields,
        contextApproved: state.childId === action.id ? false : state.contextApproved,
        runCancelPending: state.runCancelPending || isRunChild,
        notice: isRunChild
          ? 'Yêu cầu xóa hồ sơ đang chờ trong preview; run liên quan cũng cần được xử lý qua lifecycle của máy chủ.'
          : 'Hồ sơ đã khóa trong trạng thái DELETE_PENDING · preview; dữ liệu chưa bị xóa thật.',
      };
    }
    case 'SELECT_LESSON':
      if (state.activeRunChild) {
        return {...state, notice: 'Phiên bản giáo án đã được ghim cho run hiện tại.'};
      }
      return {...state, lessonId: action.id, lessonTitle: action.title, lessonVersion: action.version, scriptFollowingChoice: 'unset', notice: null};
    case 'SET_SCRIPT_FOLLOWING':
      return {...state, scriptFollowingChoice: action.value, notice: null};
    case 'SET_ACTIVITY_SUGGESTION':
      return {...state, suggestedActivityId: action.value, notice: null};
    case 'BEGIN_RUN_PREVIEW': {
      if (state.runCancelPending) return {...state, notice: 'Run trước đang chờ xử lý; chưa thể bắt đầu run khác.'};
      const profile = state.childProfiles.find((item) => item.id === state.childId);
      if (!profile || profile.lifecycle !== 'active') return {...state, notice: 'Chọn một hồ sơ đang hoạt động trước khi bắt đầu run.'};
      return {
        ...state,
        activeRunChild: state.activeRunChild ?? {id: state.childId, name: state.childName, age: state.childAge},
        activeRunLesson: state.activeRunLesson ?? (state.lessonId && state.lessonTitle && state.lessonVersion
          ? {id: state.lessonId, title: state.lessonTitle, version: state.lessonVersion, scriptFollowingChoice: state.scriptFollowingChoice}
          : null),
        notice: null,
      };
    }
    case 'SET_LINE_SKETCH':
      return {...state, lineSketchEnabled: action.enabled};
    case 'SET_IDEA':
      return {...state, idea: action.value};
    case 'SET_TRANSCRIPT':
      return {...state, transcript: action.value};
    case 'SET_SUBJECT':
      return {...state, subject: action.value};
    case 'APPROVE_CONTEXT':
      return {...state, contextApproved: true};
    case 'SET_CONTEXT_FIELD_INCLUDED': {
      const included = state.contextIncludedFields.includes(action.field);
      const contextIncludedFields = action.included && !included
        ? [...state.contextIncludedFields, action.field]
        : !action.included && included
          ? state.contextIncludedFields.filter((field) => field !== action.field)
          : state.contextIncludedFields;
      return {...state, contextIncludedFields, contextApproved: false};
    }
    case 'SET_REWRITE_PROMPT':
      return {...state, rewritePrompt: action.value};
    case 'REQUEST_REWRITE_PREVIEW':
      return {...state, notice: 'AI chưa kết nối; gợi ý chưa được gửi và lượt viết lại chưa bị tính.'};
    case 'CONFIRM_STORY':
      if (state.runCancelPending) return {...state, notice: 'Run đang chờ xử lý hủy; kịch bản chưa thể xác nhận lại.'};
      if (state.videoReviewReason && state.videoRegenerationCount >= 2 && !state.videoRegenerationPending) return {...state, notice: 'Đã đạt giới hạn hai lượt tạo lại trong bản preview.'};
      return {...state, storyConfirmed: true, generationState: 'not-requested'};
    case 'PREVIEW_GENERATION_STATE':
      if (state.runCancelPending) return {...state, notice: 'Run đang chờ xử lý hủy; trạng thái vẫn được giữ.'};
      return {...state, generationState: action.value};
    case 'PREVIEW_VIDEO_READY':
      if (state.runCancelPending) return {...state, notice: 'Run đang chờ xử lý hủy; chưa mở player trong preview.'};
      if (!state.storyConfirmed) return {...state, notice: 'Hãy xác nhận kịch bản trước khi mở player mẫu.'};
      if (state.videoReviewReason && state.videoRegenerationCount >= 2 && !state.videoRegenerationPending) return {...state, notice: 'Đã đạt giới hạn hai lượt tạo lại trong bản preview.'};
      return {...state, generationState: 'ready-preview', videoRegenerationPending: false, previousVideoHidden: false, route: 'video-player', history: [...state.history, state.route]};
    case 'SET_VIDEO_REVIEW_REASON':
      if (state.runCancelPending) return {...state, notice: 'Run đang chờ xử lý hủy; chưa thể gửi phản hồi video.'};
      return {...state, videoReviewReason: action.value};
    case 'ACCEPT_VIDEO_REGEN_PREVIEW':
      if (state.route !== 'video-review' || state.generationState !== 'ready-preview' || !state.videoReviewReason) return {...state, notice: 'Chọn lý do sau khi mở kết quả video sẵn sàng trong preview.'};
      if (state.runCancelPending) return {...state, notice: 'Run đang chờ xử lý hủy; chưa thể tạo lại video.'};
      if (state.videoRegenerationCount >= 2) return {...state, notice: 'Đã đạt giới hạn hai lượt tạo lại trong bản preview.'};
      return {
        ...state,
        videoRegenerationCount: state.videoRegenerationCount + 1,
        videoRegenerationPending: true,
        previousVideoHidden: true,
        storyConfirmed: false,
        generationState: 'not-requested',
        route: 'story-review',
        history: [...state.history, 'video-review'],
        notice: 'Yêu cầu tạo lại được mô phỏng là đã chấp nhận; video cũ đã ẩn trong preview. Chưa gọi máy chủ.',
      };
    case 'RETURN_TO_STORY_AFTER_LIMIT':
      if (state.route !== 'video-review' || state.videoRegenerationCount < 2 || state.videoRegenerationPending) return {...state, notice: 'Chỉ quay lại kịch bản sau khi đã đạt giới hạn tạo lại.'};
      return {...state, storyConfirmed: false, route: 'story-review', history: [...state.history, 'video-review'], notice: 'Đã quay lại kịch bản trong preview; không tạo thêm request video.'};
    case 'SET_RUN_CANCEL_PENDING':
      if (action.value && !state.activeRunChild) return {...state, notice: 'Chưa có run đang hoạt động để gửi yêu cầu hủy.'};
      return {...state, runCancelPending: action.value, notice: action.value ? 'Yêu cầu hủy đang chờ máy chủ; run vẫn được giữ trong preview.' : null};
    case 'SET_PUSH_PREFERENCE':
      return {...state, pushPreference: action.value, notice: action.value === 'enabled-preview'
        ? 'Đã bật trạng thái thông báo trong preview; chưa xin quyền Android hoặc đăng ký push.'
        : 'Đã tắt trạng thái thông báo trong preview; endpoint thật chưa được thay đổi.'};
    case 'SET_FEEDBACK_RATING':
      return {...state, feedbackRating: action.value};
    case 'SET_FEEDBACK_NOTE':
      return {...state, feedbackNote: action.value};
    case 'SHOW_NOTICE':
      return {...state, notice: action.value};
    case 'CLEAR_NOTICE':
      return {...state, notice: null};
    case 'RESET_RUN':
      if (state.runCancelPending) return {...state, notice: 'Run đang chờ kết quả hủy từ máy chủ; trạng thái chưa được xóa.'};
      return {
        ...state,
        route: 'home',
        history: [],
        activeRunChild: null,
        activeRunLesson: null,
        lessonId: null,
        lessonTitle: null,
        lessonVersion: null,
        scriptFollowingChoice: 'unset',
        suggestedActivityId: null,
        lineSketchEnabled: false,
        idea: '',
        transcript: '',
        subject: 'Con bướm',
        contextApproved: false,
        contextIncludedFields: [],
        rewritePrompt: '',
        rewriteCount: 0,
        storyConfirmed: false,
        generationState: 'not-requested',
        runCancelPending: false,
        videoReviewReason: '',
        videoRegenerationCount: 0,
        videoRegenerationPending: false,
        previousVideoHidden: false,
        notice: null,
      };
    default:
      return assertNever(action);
  }
}

function assertNever(value: never): never {
  throw new Error(`Unhandled Parent navigation action: ${String(value)}`);
}

export function isParentRoute(value: string): value is ParentRoute {
  return [
    'login', 'register', 'recovery', 'home', 'profiles', 'lesson-library', 'lesson-detail',
    'run-setup', 'capture', 'voice', 'understanding', 'context', 'activity-suggestions', 'story-review', 'generation',
    'video-player', 'video-review', 'activities', 'completion', 'session-feedback', 'history', 'sharing', 'quota', 'feedback',
    'notifications', 'settings', 'fixture',
  ].includes(value);
}
