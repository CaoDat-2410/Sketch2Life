import React from 'react';

export const SecurityAuditToggle: React.FC = () => (
  <div className="p-5 bg-white rounded-xl border border-slate-100 shadow-sm">
    <h4 className="text-xs font-bold text-slate-900 mb-2">Chế độ kiểm toán nghiêm ngặt</h4>
    <p className="text-xs text-slate-500 mb-3">Tự động băm và mã hóa tất cả định danh nhạy cảm.</p>
    <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded border border-emerald-200">ĐANG BẬT</span>
  </div>
);
