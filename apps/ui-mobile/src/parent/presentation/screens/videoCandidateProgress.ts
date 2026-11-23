import type { ParentVideoCandidateV1 } from '../../domain/types';

export type VideoCandidateProgressStep = {
  id: 'prepare' | 'queue' | 'animate' | 'save';
  label: string;
  state: 'complete' | 'current' | 'upcoming';
};

const phaseLabels = [
  { id: 'prepare', label: 'Chuẩn bị ảnh và kịch bản' },
  { id: 'queue', label: 'Chờ lượt xử lý' },
  { id: 'animate', label: 'Tạo chuyển động' },
  { id: 'save', label: 'Kiểm tra và lưu bản xem thử' },
] as const;

const currentPhaseByState: Partial<Record<ParentVideoCandidateV1['state'], number>> = {
  STAGING: 0,
  DISPATCHING: 1,
  QUEUED: 1,
  GENERATING: 2,
};

export function videoCandidateProgressFor(
  state: ParentVideoCandidateV1['state'],
): VideoCandidateProgressStep[] | null {
  if (state === 'FAILED' || state === 'AWAITING_RECONCILIATION') return null;

  const currentPhase = state === 'CANDIDATE_READY'
    ? phaseLabels.length
    : currentPhaseByState[state];

  if (currentPhase === undefined) return null;

  return phaseLabels.map((phase, index) => ({
    ...phase,
    state: index < currentPhase ? 'complete' : index === currentPhase ? 'current' : 'upcoming',
  }));
}
