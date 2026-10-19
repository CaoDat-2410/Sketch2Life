import React from 'react';

export const ModelVersionSelector: React.FC = () => (
  <select className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white">
    <option value="qwen3-vl-8b">Qwen3-VL-8B (Default)</option>
    <option value="qwen3-vl-32b">Qwen3-VL-32B (High Accuracy)</option>
  </select>
);
