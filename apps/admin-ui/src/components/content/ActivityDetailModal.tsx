import React from 'react';

export const ActivityDetailModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  return <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center"><button onClick={onClose}>Đóng</button></div>;
};
