import type {ParentWorkflowPort} from '../../features/parent-flow/parentWorkflowPort';
import {ParentDemoWorkflowAdapter} from '../../infrastructure/demo/ParentDemoWorkflowAdapter';

export interface ApiClientPort {
  get<TResponse>(path: string): Promise<TResponse>;
  post<TRequest, TResponse>(path: string, body: TRequest): Promise<TResponse>;
}

export interface AppDependencies {
  apiClient: ApiClientPort | null;
  parentWorkflow: ParentWorkflowPort;
}

/** Local demo composition. Replace the adapter here when a versioned API is approved. */
export function createDemoAppDependencies(): AppDependencies {
  return {
    apiClient: null,
    parentWorkflow: new ParentDemoWorkflowAdapter(),
  };
}
