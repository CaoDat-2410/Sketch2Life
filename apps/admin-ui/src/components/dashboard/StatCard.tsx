import React from 'react';

export interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  isPositive?: boolean;
  iconName?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, change, isPositive }) => (
  <div className="bg-white rounded-xl p-5 border border-slate-100 shadow-sm">
    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
    <div className="flex items-baseline justify-between mt-2">
      <span className="text-2xl font-bold text-slate-900">{value}</span>
      {change && (
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${isPositive ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
          {change}
        </span>
      )}
    </div>
  </div>
);
