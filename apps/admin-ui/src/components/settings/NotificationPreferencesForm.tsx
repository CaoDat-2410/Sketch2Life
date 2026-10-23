import React from 'react';

export const NotificationPreferencesForm: React.FC = () => (
  <div className="p-5 bg-white rounded-xl border border-slate-100 shadow-sm">
    <h4 className="text-xs font-bold text-slate-900 mb-2">Thông báo quản trị</h4>
    <label className="flex items-center gap-2 text-xs text-slate-600">
      <input type="checkbox" defaultChecked /> Gửi cảnh báo khi có yêu cầu xóa COPPA mới
    </label>
  </div>
);
