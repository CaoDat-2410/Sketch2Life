import { ParentApplicationError } from './ParentApplicationError';
import {
  isParentStoryRunLifecycleEnvelope,
  type ParentStoryRunEnvelopeV1,
  type ParentStoryRunResultV1,
} from '../domain/types';

/**
 * FR-C-08: from DELETE_PENDING on, the server answers a run read with the content-free lifecycle
 * projection. A flow that needs the live run stops with the lifecycle state as its error code.
 */
export function requireLiveStoryRun(result: ParentStoryRunResultV1): ParentStoryRunEnvelopeV1 {
  if (isParentStoryRunLifecycleEnvelope(result)) {
    throw new ParentApplicationError(
      result.lifecycle.run_state,
      'Buổi học đã được xóa hoặc đang được xóa.',
      result.request_id,
    );
  }
  return result;
}
