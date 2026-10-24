export const settingsService = {
  getSettings: async () => ({ retentionDays: 30, strictAudit: true }),
  updateSettings: async (_settings: any) => {},
};
