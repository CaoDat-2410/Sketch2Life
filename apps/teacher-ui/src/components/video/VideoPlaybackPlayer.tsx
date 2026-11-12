import React from 'react';

export const VideoPlaybackPlayer: React.FC<{ videoUrl?: string }> = ({ videoUrl }) => (
  <div className="aspect-video bg-black rounded-xl overflow-hidden flex items-center justify-center text-white text-xs">
    {videoUrl ? <video src={videoUrl} controls className="w-full h-full" /> : <span>▶ Trình phát video bài học bảng trắng</span>}
  </div>
);
