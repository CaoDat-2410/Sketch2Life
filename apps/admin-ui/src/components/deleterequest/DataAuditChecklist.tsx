import React from 'react';

export const DataAuditChecklist: React.FC = () => (
  <ul className="text-xs text-slate-600 space-y-2">
    <li className="flex items-center gap-2">✓ Xóa ảnh nét vẽ gốc khỏi lưu trữ tạm</li>
    <li className="flex items-center gap-2">✓ Xóa bản ghi nhận dạng giọng nói ASR</li>
    <li className="flex items-center gap-2">✓ Băm mờ định danh hồ sơ trong nhật ký audit</li>
  </ul>
);
