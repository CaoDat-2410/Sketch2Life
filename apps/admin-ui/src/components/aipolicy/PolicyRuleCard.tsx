import React from 'react';

export const PolicyRuleCard: React.FC<{ title: string; desc: string }> = ({ title, desc }) => (
  <div className="p-4 bg-white rounded-xl border border-slate-100 shadow-sm mb-3">
    <h4 className="font-semibold text-xs text-slate-900">{title}</h4>
    <p className="text-xs text-slate-500 mt-1">{desc}</p>
  </div>
);
