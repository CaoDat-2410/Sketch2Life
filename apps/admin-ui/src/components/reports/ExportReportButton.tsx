import React from 'react';

export const ExportReportButton: React.FC<{ onExport: () => void }> = ({ onExport }) => (
  <button onClick={onExport} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800">
    Xuất báo cáo PDF / CSV
  </button>
);
