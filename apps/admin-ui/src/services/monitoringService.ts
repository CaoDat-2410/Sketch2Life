export const monitoringService = {
  getLatency: async () => ({ p95: 142 }),
  getQueueMetrics: async () => ({ active: 4, waiting: 0 }),
};
