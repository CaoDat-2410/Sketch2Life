import React from "react";

export type IconName =
  | "home" | "camera" | "sparkle" | "users" | "search" | "arrow-right" | "arrow-left" | "clock" | "check"
  | "alert" | "lock" | "refresh" | "leaf" | "book" | "play" | "pause" | "user" | "image" | "wand"
  | "info" | "close" | "download" | "star" | "heart" | "video" | "plus" | "sun" | "moon" | "palette"
  | "wifi-off" | "chevron-down" | "chevron-right" | "share" | "message" | "trash" | "settings" | "shield"
  | "folder" | "bell" | "mic" | "stop" | "maximize" | "minimize" | "rotate" | "key" | "logout"
  | "volume" | "volume-off" | "help" | "edit" | "nav-home" | "nav-history" | "nav-create" | "nav-credits" | "nav-settings";

const PATHS: Record<IconName, React.ReactNode> = {
  home: (<><path d="M3.5 10.5L12 3.5l8.5 7" /><path d="M5.5 9.2v9.3a1.5 1.5 0 0 0 1.5 1.5h10a1.5 1.5 0 0 0 1.5-1.5V9.2" /><path d="M9.5 20v-5.5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1V20" /></>),
  camera: (<><path d="M4 8.5A2.5 2.5 0 0 1 6.5 6h1.2a1 1 0 0 0 .8-.4L9.6 4h4.8l1.1 1.6a1 1 0 0 0 .8.4h1.2A2.5 2.5 0 0 1 20 8.5v8A2.5 2.5 0 0 1 17.5 19h-11A2.5 2.5 0 0 1 4 16.5v-8Z" /><circle cx="12" cy="12.5" r="3.6" /></>),
  sparkle: (<><path d="M9 18h6M10 21h4" /><path d="M12 3a6 6 0 0 0-4 10.5c.7.6 1 1.4 1 2.3V16h6v-.2c0-.9.3-1.7 1-2.3A6 6 0 0 0 12 3Z" /></>),
  users: (<><circle cx="9" cy="8.5" r="3.2" /><path d="M3.5 19c.8-3 3-4.5 5.5-4.5s4.7 1.5 5.5 4.5" /><circle cx="17" cy="9.5" r="2.4" /><path d="M16.5 14.6c2.2.1 3.7 1.4 4.3 3.9" /></>),
  search: (<><circle cx="11" cy="11" r="6.5" /><path d="M20 20l-4.2-4.2" /></>),
  "arrow-right": (<path d="M5 12h14M13 6l6 6-6 6" />),
  "arrow-left": (<path d="M19 12H5M11 6l-6 6 6 6" />),
  clock: (<><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>),
  check: (<path d="M5 12.5l4.5 4.5L19 7.5" />),
  alert: (<><path d="M12 4l9 15.5H3L12 4Z" /><path d="M12 10v4M12 17h.01" /></>),
  lock: (<><rect x="5" y="10.5" width="14" height="9.5" rx="2.5" /><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" /></>),
  refresh: (<><path d="M20 11a8 8 0 0 0-14.3-4.2L4 8.5" /><path d="M4 4v4.5h4.5" /><path d="M4 13a8 8 0 0 0 14.3 4.2L20 15.5" /><path d="M20 20v-4.5h-4.5" /></>),
  leaf: (<><path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14" /><path d="M5 19c2-4 5-7 9-9" /></>),
  book: (<><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5V5.5Z" /><path d="M8 7h8M8 11h6" /></>),
  play: (<path d="M8 5.5v13l11-6.5-11-6.5Z" />),
  pause: (<><rect x="7" y="5.5" width="3.5" height="13" rx="1" /><rect x="13.5" y="5.5" width="3.5" height="13" rx="1" /></>),
  user: (<><circle cx="12" cy="8.5" r="3.5" /><path d="M5.5 19.5c1.5-3.2 4-4.5 6.5-4.5s5 1.3 6.5 4.5" /></>),
  image: (<><rect x="3.5" y="5" width="17" height="14" rx="3" /><circle cx="9" cy="10" r="1.7" /><path d="M4 17l5-4.5 3.5 3L16 12l4 4" /></>),
  wand: (<><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4L16.5 3.5Z" /><path d="M14.5 5.5l3 3" /></>),
  info: (<><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5M12 8h.01" /></>),
  close: (<path d="M6 6l12 12M18 6L6 18" />),
  download: (<><path d="M12 4v11M7 11l5 5 5-5" /><path d="M5 19h14" /></>),
  star: (<path d="M12 3.8l2.5 5.1 5.6.8-4.05 3.95.95 5.55L12 16.5l-5 2.7.95-5.55L3.9 9.7l5.6-.8L12 3.8Z" />),
  heart: (<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z" />),
  video: (<><rect x="3.5" y="6" width="12" height="12" rx="3" /><path d="M15.5 10.5l5-3v9l-5-3" /></>),
  plus: (<path d="M12 5v14M5 12h14" />),
  sun: (<><circle cx="12" cy="12" r="4" /><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M18.7 5.3l-1.4 1.4M6.7 17.3l-1.4 1.4" /></>),
  moon: (<path d="M20.4 14.6A8.5 8.5 0 0 1 9.4 3.6a8.5 8.5 0 1 0 11 11Z" />),
  palette: (<><path d="M12 3.5a8.5 8.5 0 1 0 0 17c1.4 0 2-1 1.5-2-.6-1.2.2-2.5 1.6-2.5H17a3.5 3.5 0 0 0 3.5-3.5C20.5 7 16.8 3.5 12 3.5Z" /><circle cx="8" cy="11" r="1" /><circle cx="11" cy="7.5" r="1" /><circle cx="15.5" cy="8.5" r="1" /></>),
  "wifi-off": (<><path d="M3 3l18 18" /><path d="M2 9a15 15 0 0 1 5-3M22 9a15 15 0 0 0-8-3.8M5.5 12.5a10 10 0 0 1 3.2-2M18.5 12.5A10 10 0 0 0 15 10.3M9 16a5 5 0 0 1 6 0" /><path d="M12 19.5h.01" /></>),
  "chevron-down": (<path d="M6 9l6 6 6-6" />),
  "chevron-right": (<path d="M9 6l6 6-6 6" />),
  share: (<><circle cx="6" cy="12" r="2.5" /><circle cx="17.5" cy="6" r="2.5" /><circle cx="17.5" cy="18" r="2.5" /><path d="M8.2 10.8l7.1-3.6M8.2 13.2l7.1 3.6" /></>),
  message: (<path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v8a2.5 2.5 0 0 1-2.5 2.5H11l-4.5 3.5V17A2.5 2.5 0 0 1 4 14.5v-8Z" />),
  trash: (<><path d="M5 7h14M10 7V4.5h4V7M7 7l.8 12.5h8.4L17 7" /><path d="M10 11v5M14 11v5" /></>),
  settings: (<><circle cx="12" cy="12" r="3" /><path d="M12 3v2.2M12 18.8V21M3 12h2.2M18.8 12H21M5.6 5.6l1.6 1.6M16.8 16.8l1.6 1.6M18.4 5.6l-1.6 1.6M7.2 16.8l-1.6 1.6" /></>),
  shield: (<><path d="M12 3l7.5 3v5.5c0 4.8-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.7-7.5-9.5V6L12 3Z" /><path d="M9 12l2 2 4-4" /></>),
  folder: (<path d="M3.5 7A2.5 2.5 0 0 1 6 4.5h4l2 2.2h6A2.5 2.5 0 0 1 20.5 9.2v8.3A2.5 2.5 0 0 1 18 20H6a2.5 2.5 0 0 1-2.5-2.5V7Z" />),
  bell: (<><path d="M6 10a6 6 0 0 1 12 0c0 5 2 6.5 2 6.5H4S6 15 6 10Z" /><path d="M10 19a2 2 0 0 0 4 0" /></>),
  mic: (<><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 10.5a7 7 0 0 0 14 0M12 17.5V21M8.5 21h7" /></>),
  stop: (<rect x="6.5" y="6.5" width="11" height="11" rx="2.5" />),
  maximize: (<path d="M8 3.5H5.5a2 2 0 0 0-2 2V8M20.5 8V5.5a2 2 0 0 0-2-2H16M3.5 16v2.5a2 2 0 0 0 2 2H8M16 20.5h2.5a2 2 0 0 0 2-2V16" />),
  minimize: (<path d="M8 3.5V6a2 2 0 0 1-2 2H3.5M20.5 8H18a2 2 0 0 1-2-2V3.5M3.5 16H6a2 2 0 0 1 2 2v2.5M16 20.5V18a2 2 0 0 1 2-2h2.5" />),
  rotate: (<><rect x="3" y="6" width="18" height="12" rx="2.5" /><path d="M9.5 10L7.5 12l2 2M14.5 10l2 2-2 2" /></>),
  key: (<><circle cx="8" cy="15" r="4" /><path d="M10.8 12.2L20 3M16 7l3 3M18 5l2 2" /></>),
  logout: (<><path d="M9 20H5.5A2 2 0 0 1 3.5 18V6A2 2 0 0 1 5.5 4H9" /><path d="M16 17l4.5-5L16 7M20.5 12H9" /></>),
  volume: (<><path d="M11 5L6 9H3v6h3l5 4V5Z" /><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12" /></>),
  "volume-off": (<><path d="M11 5L6 9H3v6h3l5 4V5Z" /><path d="M21 9l-6 6M15 9l6 6" /></>),
  help: (<><circle cx="12" cy="12" r="8.5" /><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .8-1 1.7M12 16.8h.01" /></>),
  edit: (<path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5Z" />),
  "nav-home": (<><path d="M4 10.4 12 4l8 6.4" /><path d="M6.4 9v9.1A1.9 1.9 0 0 0 8.3 20h7.4a1.9 1.9 0 0 0 1.9-1.9V9" /><path d="M10 20v-5.6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1V20" /><path d="M16 6.7v-2h2v3.6" /></>),
  "nav-history": (<><path d="M3.5 11a8.5 8.5 0 1 1 .2 2.5" /><path d="M3.5 4.5V11H10" /><path d="M12 7.5v4.8l3.2 2" /></>),
  "nav-create": (<><path d="M4 8.5A2.5 2.5 0 0 1 6.5 6h1.2a1 1 0 0 0 .8-.4L9.6 4h4.8l1.1 1.6a1 1 0 0 0 .8.4h1.2A2.5 2.5 0 0 1 20 8.5v8A2.5 2.5 0 0 1 17.5 19h-11A2.5 2.5 0 0 1 4 16.5v-8Z" /><circle cx="12" cy="12.5" r="3.1" /><path d="M18.5 2.8v4.4M16.3 5h4.4" /></>),
  "nav-credits": (<><ellipse cx="12" cy="6.5" rx="7.2" ry="3.2" /><path d="M4.8 6.5v5.4c0 1.8 3.2 3.3 7.2 3.3s7.2-1.5 7.2-3.3V6.5" /><path d="M4.8 11.9v5.3c0 1.8 3.2 3.3 7.2 3.3s7.2-1.5 7.2-3.3v-5.3" /><path d="M12 8v4" /></>),
  "nav-settings": (<><path d="M4 6h7M15 6h5M4 12h3M11 12h9M4 18h9M17 18h3" /><circle cx="13" cy="6" r="2" /><circle cx="9" cy="12" r="2" /><circle cx="15" cy="18" r="2" /></>),
};

export function Icon({
  name,
  size = 20,
  color = "currentColor",
  strokeWidth = 2,
  fill = "none",
}: {
  name: IconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
  fill?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={fill}
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={{ flexShrink: 0 }}
    >
      {PATHS[name]}
    </svg>
  );
}

/* Round tinted icon badge used as a visual anchor instead of text */
export function IconBadge({
  name,
  tone = "primary",
  size = 42,
}: {
  name: IconName;
  tone?: "primary" | "accent" | "mint" | "danger" | "neutral";
  size?: number;
}) {
  return (
    <span
      className={`icon-badge ${tone}`}
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size / 2.6),
      }}
      aria-hidden="true"
    >
      <Icon name={name} size={Math.round(size * 0.48)} />
    </span>
  );
}
