export const sessionService = {
  createSession: async (data: any) => ({ sessionId: 'ses-101' }),
  getLiveSession: async (id: string) => ({ sessionId: id, step: 2 }),
  advanceStep: async (id: string, step: number) => {},
};
