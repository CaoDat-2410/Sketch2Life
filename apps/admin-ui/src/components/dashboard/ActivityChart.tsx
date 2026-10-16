import React from 'react';

export const ActivityChart: React.FC = () => (
  <div className="bg-white rounded-xl p-6 border border-slate-100 shadow-sm">
    <h3 className="text-sm font-semibold text-slate-800 mb-4">Lưu lượng phiên học theo thời gian</h3>
    <div className="h-48 flex items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
      <span className="text-xs text-slate-400">Biểu đồ phiên học thời gian thực</span>
    </div>
  </div>
);
