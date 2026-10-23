import React from 'react';

export const ErasureCountdownTimer: React.FC<{ remainingHours: number }> = ({ remainingHours }) => (
  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-center">
    <span className="text-2xl font-black text-amber-900">{remainingHours}h 00m</span>
    <p className="text-xs font-semibold text-amber-700 mt-1">Thời hạn xử lý xóa bỏ COPPA còn lại</p>
  </div>
);
