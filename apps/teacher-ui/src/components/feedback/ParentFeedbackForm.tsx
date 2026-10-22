import React from 'react';

export const ParentFeedbackForm: React.FC = () => (
  <div className="space-y-3">
    <textarea placeholder="Ghi chú quan sát chi tiết cho phụ huynh..." className="w-full text-xs p-3 border rounded-lg h-24" />
    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold">Gửi báo cáo cho phụ huynh</button>
  </div>
);
