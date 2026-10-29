import React from 'react';

export const LogDetailDrawer: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  return <div className="fixed right-0 top-0 bottom-0 w-80 bg-white shadow-2xl p-6 z-50"><button onClick={onClose}>Đóng</button></div>;
};
