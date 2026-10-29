import React from 'react';

export const ServiceHealthStatus: React.FC<{ serviceName: string; isUp: boolean }> = ({ serviceName, isUp }) => (
  <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-100 mb-2">
    <span className="text-xs font-medium text-slate-700">{serviceName}</span>
    <span className={`w-2.5 h-2.5 rounded-full ${isUp ? 'bg-emerald-500' : 'bg-rose-500'}`} />
  </div>
);
