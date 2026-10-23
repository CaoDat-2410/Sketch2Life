import React from 'react';

export const JobQueueGauge: React.FC<{ active: number; waiting: number }> = ({ active, waiting }) => (
  <div className="p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
    <h4 className="text-xs font-semibold text-slate-700">Hàng đợi AI Jobs</h4>
    <div className="flex gap-4 mt-2 text-xs">
      <div>Đang chạy: <span className="font-bold text-blue-600">{active}</span></div>
      <div>Đang chờ: <span className="font-bold text-amber-600">{waiting}</span></div>
    </div>
  </div>
);
