import React from 'react';
import type { AdminUser } from '../../types/admin';

export const UserTable: React.FC<{ users?: AdminUser[] }> = ({ users = [] }) => (
  <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
    <table className="w-full text-left text-xs text-slate-600">
      <thead className="bg-slate-50 text-slate-500 border-b border-slate-100 font-semibold uppercase">
        <tr>
          <th className="px-4 py-3">Tên</th>
          <th className="px-4 py-3">Email</th>
          <th className="px-4 py-3">Vai trò</th>
          <th className="px-4 py-3">Trạng thái</th>
        </tr>
      </thead>
      <tbody>
        {users.map(u => (
          <tr key={u.id} className="border-b border-slate-50 hover:bg-slate-50/50">
            <td className="px-4 py-3 font-medium text-slate-900">{u.name}</td>
            <td className="px-4 py-3">{u.email}</td>
            <td className="px-4 py-3">{u.role}</td>
            <td className="px-4 py-3">{u.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
