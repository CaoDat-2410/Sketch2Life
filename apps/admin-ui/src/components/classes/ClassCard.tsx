import React from 'react';

export interface ClassCardProps {
  name: string;
  guideName: string;
  studentCount: number;
}

export const ClassCard: React.FC<ClassCardProps> = ({ name, guideName, studentCount }) => (
  <div className="bg-white rounded-xl p-5 border border-slate-100 shadow-sm">
    <h4 className="font-bold text-sm text-slate-900">{name}</h4>
    <p className="text-xs text-slate-500 mt-1">Người hướng dẫn: {guideName}</p>
    <div className="mt-4 pt-3 border-t border-slate-100 text-xs font-semibold text-blue-600">
      {studentCount} Học sinh
    </div>
  </div>
);
