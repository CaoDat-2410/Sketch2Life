import React from 'react';
import type { AdminUser } from '../../types/admin';

export const UserDetailModal: React.FC<{ user: AdminUser | null; onClose: () => void }> = ({ user, onClose }) => {
  if (!user) return null;
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 max-w-md w-full shadow-xl">
        <h3 className="text-base font-bold text-slate-900 mb-2">{user.name}</h3>
        <p className="text-xs text-slate-500 mb-4">{user.email}</p>
        <button onClick={onClose} className="px-4 py-2 bg-slate-100 rounded-lg text-xs font-semibold">Đóng</button>
      </div>
    </div>
  );
};
