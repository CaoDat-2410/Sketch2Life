import React from 'react';

export const UserFilterBar: React.FC<{ onSearch?: (q: string) => void }> = ({ onSearch }) => (
  <div className="flex gap-3 mb-4">
    <input
      type="text"
      placeholder="Tìm theo tên hoặc email..."
      onChange={e => onSearch?.(e.target.value)}
      className="px-3 py-2 text-xs border border-slate-200 rounded-lg w-64 focus:outline-none focus:ring-1 focus:ring-blue-500"
    />
  </div>
);
