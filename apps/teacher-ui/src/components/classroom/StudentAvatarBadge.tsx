import React from 'react';

export const StudentAvatarBadge: React.FC<{ name: string; avatarUrl?: string; status?: 'active' | 'idle' }> = ({ name, status = 'idle' }) => (
  <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-100 shadow-sm">
    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">
      {name[0]}
    </div>
    <span className="text-xs font-medium text-slate-800">{name}</span>
    <span className={`w-2 h-2 rounded-full ml-auto ${status === 'active' ? 'bg-emerald-500' : 'bg-slate-300'}`} />
  </div>
);
