import React from 'react';

export const RetentionPolicyForm: React.FC = () => (
  <div className="p-5 bg-white rounded-xl border border-slate-100 shadow-sm">
    <h4 className="text-xs font-bold text-slate-900 mb-2">Chính sách lưu trữ dữ liệu</h4>
    <select className="px-3 py-2 text-xs border rounded-lg w-full">
      <option value="30">30 ngày (Khuyến nghị chuẩn COPPA)</option>
      <option value="60">60 ngày</option>
      <option value="90">90 ngày</option>
    </select>
  </div>
);
