import React from 'react';

export const ClassGroupCard: React.FC<{ title: string; count: number; onSelect?: () => void }> = ({ title, count, onSelect }) => (
  <div onClick={onSelect} className="p-4 bg-white rounded-xl border border-slate-100 shadow-sm hover:border-blue-300 cursor-pointer">
    <h4 className="font-bold text-sm text-slate-900">{title}</h4>
    <p className="text-xs text-slate-500 mt-1">{count} học sinh đang hoạt động</p>
  </div>
);
