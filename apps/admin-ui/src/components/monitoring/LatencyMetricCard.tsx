import React from 'react';

export const LatencyMetricCard: React.FC<{ endpoint: string; p95: number }> = ({ endpoint, p95 }) => (
  <div className="p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
    <span className="text-xs font-mono text-slate-500">{endpoint}</span>
    <p className="text-xl font-bold text-slate-900 mt-1">{p95}ms <span className="text-xs font-normal text-slate-400">p95</span></p>
  </div>
);
