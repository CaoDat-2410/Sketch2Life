import React from 'react';

export interface AlertBannerProps {
  message: string;
  type?: 'info' | 'warning' | 'error';
}

export const SystemAlertBanner: React.FC<AlertBannerProps> = ({ message, type = 'info' }) => (
  <div className="p-3 mb-4 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-700 flex items-center justify-between">
    <span>{message}</span>
  </div>
);
