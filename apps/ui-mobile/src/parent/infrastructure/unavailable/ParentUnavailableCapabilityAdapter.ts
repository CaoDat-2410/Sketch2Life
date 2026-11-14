import {
  createUnavailableCapabilityState,
  createUnavailableOperationState,
} from '../../application/ports/ParentCapabilityPorts';
import type {
  ParentCapabilityId,
  ParentCapabilityPort,
  ParentCapabilityState,
  ParentOperationPort,
  ParentOperationState,
  ParentCapabilityUnavailableReason,
} from '../../application/ports/ParentCapabilityPorts';

export class ParentUnavailableCapabilityAdapter implements ParentCapabilityPort, ParentOperationPort {
  constructor(private readonly reason: ParentCapabilityUnavailableReason = 'capability-not-configured') {}

  capabilityState(capability: ParentCapabilityId): ParentCapabilityState {
    return createUnavailableCapabilityState(capability, this.reason);
  }

  operationState<T>(): ParentOperationState<T> {
    return createUnavailableOperationState<T>(this.reason);
  }
}
