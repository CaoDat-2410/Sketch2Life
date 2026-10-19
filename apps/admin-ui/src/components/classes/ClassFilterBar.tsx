import React from 'react';

export const ClassFilterBar: React.FC = () => (
  <div className="flex gap-2 mb-4">
    <button className="px-3 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-lg">Tất cả lớp</button>
    <button className="px-3 py-1.5 text-xs font-medium bg-white text-slate-600 border rounded-lg">Lớp 3-4 tuổi</button>
    <button className="px-3 py-1.5 text-xs font-medium bg-white text-slate-600 border rounded-lg">Lớp 5-6 tuổi</button>
  </div>
);
