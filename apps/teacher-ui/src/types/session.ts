export type SessionStep = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export interface OrchestrationSession {
  sessionId: string;
  classId: string;
  currentStep: SessionStep;
  gateAStatus: 'pending' | 'approved' | 'rejected';
  gateBStatus: 'pending' | 'approved' | 'rejected';
  startedAt: string;
  completedAt?: string;
}
