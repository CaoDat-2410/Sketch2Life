import React from 'react';

export const MontessoriMaterialList: React.FC<{ materials: string[] }> = ({ materials }) => (
  <ul className="text-xs text-slate-600 space-y-1.5">
    {materials.map((m, i) => <li key={i} className="flex items-center gap-2">📦 <span>{m}</span></li>)}
  </ul>
);
