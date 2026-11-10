import React from "react";

export type RoleDashboardIconName =
  | "home" | "camera" | "sparkle" | "users" | "search" | "arrow-right" | "arrow-left" | "clock" | "check"
  | "alert" | "lock" | "refresh" | "leaf" | "book" | "play" | "pause" | "user" | "image" | "wand"
  | "info" | "close" | "download" | "upload" | "star" | "heart" | "video" | "plus" | "sun" | "moon"
  | "palette" | "wifi-off" | "chevron-down" | "share" | "message" | "trash" | "settings" | "edit" | "eye"
  | "eye-off" | "shield" | "maximize" | "minimize" | "log-out" | "copy"
  | "calendar" | "chart" | "gear" | "building" | "grid" | "doc" | "bell" | "school" | "pencil" | "eyeoff"
  | "globe" | "chevron" | "chevdown" | "layers" | "more" | "arrow" | "userplus" | "list" | "logout";

const arrowRight = <path d="M4.5 12h15M13 5.5 19.5 12 13 18.5" />;
const arrowLeft = <path d="M19.5 12h-15M11 5.5 4.5 12l6.5 6.5" />;
const chevronRight = <path d="m9 5.5 6.5 6.5L9 18.5" />;
const chevronDown = <path d="m5.5 9 6.5 6.5L18.5 9" />;
const eyeOff = <><path d="m3.5 3.5 17 17" /><path d="M10.1 10.1a2.7 2.7 0 0 0 3.8 3.8" /><path d="M9.4 5.5A10.5 10.5 0 0 1 12 5.2c6 0 9.5 6.8 9.5 6.8a16.4 16.4 0 0 1-3.1 4.1M6.2 6.4C3.8 8.1 2.5 12 2.5 12S6 18.8 12 18.8c1.1 0 2.1-.2 3.1-.6" /></>;
const edit = <><path d="m14.7 5.3 4 4" /><path d="m4.5 19.5 4.2-1L18.9 8.3a2.8 2.8 0 0 0-4-4L4.7 14.5l-.2 5Z" /></>;
const logout = <><path d="m10 17.5 5.5-5.5L10 6.5" /><path d="M15.5 12H4M13 3.5h5A2.5 2.5 0 0 1 20.5 6v12a2.5 2.5 0 0 1-2.5 2.5h-5" /></>;
const settings = <><circle cx="12" cy="12" r="3.1" /><path d="M12 3v2.4M12 18.6V21M3 12h2.4M18.6 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8" /></>;
const eye = <><path d="M2.6 12s3.4-6.3 9.4-6.3 9.4 6.3 9.4 6.3-3.4 6.3-9.4 6.3S2.6 12 2.6 12Z" /><circle cx="12" cy="12" r="3" /></>;
const clock = <><circle cx="12" cy="12" r="8.8" /><path d="M12 7v5.2l3.4 2" /></>;
const calendar = <><rect x="3.8" y="5" width="16.4" height="15.2" rx="3" /><path d="M8 3.5v3M16 3.5v3M4 9.5h16M8.2 13h.1M12 13h.1M15.8 13h.1M8.2 16.5h.1M12 16.5h.1" /></>;
const check = <path d="m5.2 12.4 4.2 4.2L18.8 7.2" />;
const shield = <><path d="M12 3.2 19 6v5.4c0 4.1-2.9 7.6-7 9.4-4.1-1.8-7-5.3-7-9.4V6l7-2.8Z" /><path d="m8.8 12.2 2.1 2.1 4.5-4.6" /></>;
const users = <><circle cx="9" cy="8.2" r="3" /><path d="M3.1 19c.7-3.1 2.8-4.8 5.9-4.8s5.2 1.7 5.9 4.8" /><circle cx="17.3" cy="9.2" r="2.3" /><path d="M16 14.4c2.5-.1 4.3 1.4 4.9 4.1" /></>;
const building = <><rect x="5" y="3.6" width="14" height="17" rx="2.4" /><path d="M8.5 8h2M13.5 8h2M8.5 12h2M13.5 12h2M10 20.5v-4h4v4" /></>;
const book = <><path d="M4 6.2A2.7 2.7 0 0 1 6.7 3.5H20v16H6.7A2.7 2.7 0 0 0 4 22.2V6.2Z" /><path d="M8.1 7.5h7.8M8.1 11.5h6" /></>;
const school = <><path d="m3.5 9.6 8.5-6 8.5 6" /><path d="M5.3 9.2v10.6h13.4V9.2M9.5 19.8v-5.1h5v5.1M8 11.5h.1M12 11.5h.1M16 11.5h.1" /></>;
const bell = <><path d="M6.2 16.8V11a5.8 5.8 0 0 1 11.6 0v5.8l1.5 2H4.7l1.5-2Z" /><path d="M10 21h4" /></>;
const chart = <><path d="M4.5 19.5h15" /><rect x="6" y="11" width="3.2" height="7.5" rx="1" /><rect x="10.4" y="5.5" width="3.2" height="13" rx="1" /><rect x="14.8" y="8.5" width="3.2" height="10" rx="1" /></>;
const heart = <path d="M20.4 9.1c0 5.7-8.4 10.1-8.4 10.1S3.6 14.8 3.6 9.1a4.5 4.5 0 0 1 8.4-2.2 4.5 4.5 0 0 1 8.4 2.2Z" />;
const star = <path d="m12 3.4 2.5 5.2 5.8.8-4.2 4.1 1 5.8-5.1-2.7-5.1 2.7 1-5.8-4.2-4.1 5.8-.8L12 3.4Z" />;
const image = <><rect x="3.5" y="5" width="17" height="14" rx="3" /><circle cx="9" cy="10" r="1.6" /><path d="m4.4 16.7 4.2-3.9 3.2 2.7 3.3-3 4.5 4" /></>;
const video = <><rect x="3.2" y="5.4" width="12.6" height="13.2" rx="3" /><path d="m15.8 10 5-3v10l-5-3" /></>;
const message = <path d="M5.8 4.5h12.4a2.3 2.3 0 0 1 2.3 2.3v8.3a2.3 2.3 0 0 1-2.3 2.3h-6l-5.7 3.8v-3.8H5.8a2.3 2.3 0 0 1-2.3-2.3V6.8a2.3 2.3 0 0 1 2.3-2.3Z" />;
const lock = <><rect x="5" y="10.3" width="14" height="10" rx="2.6" /><path d="M8 10.3V7.8a4 4 0 0 1 8 0v2.5" /></>;

const PATHS: Record<RoleDashboardIconName, React.ReactNode> = {
  home: <><path d="m3.5 10.8 8.5-7.2 8.5 7.2" /><path d="M5.6 9.5v9.1A1.4 1.4 0 0 0 7 20h10a1.4 1.4 0 0 0 1.4-1.4V9.5" /><path d="M9.7 20v-5.4a1.2 1.2 0 0 1 1.2-1.2h2.2a1.2 1.2 0 0 1 1.2 1.2V20" /></>,
  camera: <><path d="M4.2 8.3A2.8 2.8 0 0 1 7 5.5h1.2l1.4-1.8h4.8l1.4 1.8H17a2.8 2.8 0 0 1 2.8 2.8v7.9A2.8 2.8 0 0 1 17 19H7a2.8 2.8 0 0 1-2.8-2.8V8.3Z" /><circle cx="12" cy="12.2" r="3.4" /></>,
  sparkle: <><path d="m12 3.2 1.5 5.2 5.3 1.6-5.3 1.5-1.5 5.3-1.6-5.3-5.2-1.5 5.2-1.6L12 3.2Z" /><path d="m19 16 .7 2.2 2.1.7-2.1.6L19 21.7l-.6-2.2-2.2-.6 2.2-.7L19 16Z" /></>,
  users,
  search: <><circle cx="10.8" cy="10.8" r="6.2" /><path d="m15.3 15.3 5.2 5.2" /></>,
  "arrow-right": arrowRight,
  "arrow-left": arrowLeft,
  clock,
  check,
  alert: <><path d="m12 3.6 9 16H3l9-16Z" /><path d="M12 9v4.5M12 17h.1" /></>,
  lock,
  refresh: <><path d="M20 10a8 8 0 0 0-14.2-4L4 8M4 3.8V8h4.2M4 14a8 8 0 0 0 14.2 4L20 16M20 20.2V16h-4.2" /></>,
  leaf: <><path d="M5 19c0-8.2 5-13.2 14-14 0 9-4.8 13.6-13 14Z" /><path d="M5 19c2.7-4.3 5.7-7.4 9.5-9.8" /></>,
  book,
  play: <path d="M8.3 5.6v12.8L19 12 8.3 5.6Z" />,
  pause: <><rect x="7" y="5.5" width="3.7" height="13" rx="1.3" /><rect x="13.3" y="5.5" width="3.7" height="13" rx="1.3" /></>,
  user: <><circle cx="12" cy="8.3" r="3.5" /><path d="M5.2 19.5c1.2-3.1 3.4-4.7 6.8-4.7s5.6 1.6 6.8 4.7" /></>,
  image,
  wand: <><path d="m15.8 4.1 4.1 4.1L8 20l-4 .9.9-4L15.8 4.1Z" /><path d="m14 6 4 4M5 4v3M3.5 5.5h3M20 13.5v2M19 14.5h2" /></>,
  info: <><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5M12 8h.1" /></>,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  download: <><path d="M12 3.8v11.4M7.4 11l4.6 4.7 4.6-4.7" /><path d="M5 20h14" /></>,
  upload: <><path d="M12 15.2V3.8M7.4 8.5 12 3.8l4.6 4.7M4.3 16.4v2A1.6 1.6 0 0 0 5.9 20h12.2a1.6 1.6 0 0 0 1.6-1.6v-2" /></>,
  star,
  heart,
  video,
  plus: <path d="M12 5v14M5 12h14" />,
  sun: <><circle cx="12" cy="12" r="3.8" /><path d="M12 2.8v2M12 19.2v2M2.8 12h2M19.2 12h2M5.5 5.5 7 7M17 17l1.5 1.5M18.5 5.5 17 7M7 17l-1.5 1.5" /></>,
  moon: <path d="M20 14.1A8.4 8.4 0 0 1 9.9 4 8.4 8.4 0 1 0 20 14.1Z" />,
  palette: <><path d="M12 3.5a8.5 8.5 0 1 0 0 17c1.5 0 2.1-1.1 1.5-2.2-.6-1.2.2-2.4 1.6-2.4H17a3.5 3.5 0 0 0 3.5-3.5C20.5 7 16.8 3.5 12 3.5Z" /><circle cx="8" cy="11" r="1" /><circle cx="11.3" cy="7.5" r="1" /><circle cx="15.5" cy="8.7" r="1" /></>,
  "wifi-off": <><path d="m3.5 3.5 17 17M2.5 9a15 15 0 0 1 5-3M21.5 9a15 15 0 0 0-8-3.8M5.5 12.5a10 10 0 0 1 3.2-2M18.5 12.5a10 10 0 0 0-3.2-2M9 16a5 5 0 0 1 6 0M12 20h.1" /></>,
  "chevron-down": chevronDown,
  share: <><circle cx="6" cy="12" r="2.2" /><circle cx="18" cy="6" r="2.2" /><circle cx="18" cy="18" r="2.2" /><path d="m8 11 7.8-4M8 13l7.8 4" /></>,
  message,
  trash: <><path d="M5 7.5h14M9.5 7.5V4.2h5v3.3M7 7.5l1 12h8l1-12M10 11v5M14 11v5" /></>,
  settings,
  edit,
  eye,
  "eye-off": eyeOff,
  shield,
  maximize: <><path d="M8.5 3.5h-5v5M15.5 3.5h5v5M8.5 20.5h-5v-5M15.5 20.5h5v-5" /></>,
  minimize: <><path d="M4 8.5h5v-5M20 8.5h-5v-5M4 15.5h5v5M20 15.5h-5v5" /></>,
  "log-out": logout,
  copy: <><rect x="8.5" y="8.5" width="11" height="11" rx="2.2" /><path d="M15 5v-.2A1.8 1.8 0 0 0 13.2 3H5a2 2 0 0 0-2 2v8.2A1.8 1.8 0 0 0 4.8 15H5" /></>,
  calendar,
  chart,
  gear: settings,
  building,
  grid: <><rect x="4" y="4" width="7" height="7" rx="2" /><rect x="13" y="4" width="7" height="7" rx="2" /><rect x="4" y="13" width="7" height="7" rx="2" /><rect x="13" y="13" width="7" height="7" rx="2" /></>,
  doc: <><path d="M6 3.7h8l4 4V20H6V3.7Z" /><path d="M14 3.7v4h4M9 12h6M9 16h6" /></>,
  bell,
  school,
  pencil: edit,
  eyeoff: eyeOff,
  globe: <><circle cx="12" cy="12" r="8.7" /><path d="M3.5 12h17M12 3.3c2.4 2.6 3.5 5.5 3.5 8.7s-1.1 6.1-3.5 8.7c-2.4-2.6-3.5-5.5-3.5-8.7s1.1-6.1 3.5-8.7Z" /></>,
  chevron: chevronRight,
  chevdown: chevronDown,
  layers: <><path d="m12 3.5 8.5 4.6L12 12.7 3.5 8.1 12 3.5Z" /><path d="m3.5 12.4 8.5 4.6 8.5-4.6M3.5 16.3l8.5 4.5 8.5-4.5" /></>,
  more: <><circle cx="5.5" cy="12" r="1.2" /><circle cx="12" cy="12" r="1.2" /><circle cx="18.5" cy="12" r="1.2" /></>,
  arrow: arrowRight,
  userplus: <><circle cx="9" cy="8.2" r="3" /><path d="M3.1 19c.7-3.1 2.8-4.8 5.9-4.8s5.2 1.7 5.9 4.8M18 8v6M15 11h6" /></>,
  list: <path d="M6 6.8h13M6 12h13M6 17.2h9" />,
  logout,
};

const TINTS: Partial<Record<RoleDashboardIconName, React.ReactNode>> = {
  home: <path d="m3.5 10.8 8.5-7.2 8.5 7.2v7.8a1.4 1.4 0 0 1-1.4 1.4H6.9a1.4 1.4 0 0 1-1.4-1.4v-7.8Z" />,
  camera: <><rect x="4.2" y="5.5" width="15.6" height="13.5" rx="3" /><circle cx="12" cy="12.2" r="3.9" /></>,
  sparkle: <path d="m12 3.2 1.6 5.2 5.2 1.6-5.2 1.6-1.6 5.2-1.6-5.2-5.2-1.6 5.2-1.6L12 3.2Z" />,
  users,
  calendar: <><rect x="3.8" y="5" width="16.4" height="15.2" rx="3" /><path d="M4 9.5h16" /></>,
  chart: <><rect x="6" y="11" width="3.2" height="7.5" rx="1" /><rect x="10.4" y="5.5" width="3.2" height="13" rx="1" /><rect x="14.8" y="8.5" width="3.2" height="10" rx="1" /></>,
  shield: <path d="M12 3.2 19 6v5.4c0 4.1-2.9 7.6-7 9.4-4.1-1.8-7-5.3-7-9.4V6l7-2.8Z" />,
  gear: <circle cx="12" cy="12" r="7.5" />,
  settings: <circle cx="12" cy="12" r="7.5" />,
  building: <rect x="5" y="3.6" width="14" height="17" rx="2.4" />,
  book: <path d="M4 6.2A2.7 2.7 0 0 1 6.7 3.5H20v16H6.7A2.7 2.7 0 0 0 4 22.2V6.2Z" />,
  school: <path d="m3.5 9.6 8.5-6 8.5 6v9.7H3.5Z" />,
  grid: <><rect x="4" y="4" width="7" height="7" rx="2" /><rect x="13" y="4" width="7" height="7" rx="2" /><rect x="4" y="13" width="7" height="7" rx="2" /><rect x="13" y="13" width="7" height="7" rx="2" /></>,
  doc: <path d="M6 3.7h8l4 4V20H6V3.7Z" />,
  bell: <path d="M6.2 16.8V11a5.8 5.8 0 0 1 11.6 0v5.8l1.5 2H4.7l1.5-2Z" />,
  check: <><circle cx="12" cy="12" r="9" /><path d="m7.8 12.3 2.8 2.8 5.8-5.9" /></>,
  clock: <circle cx="12" cy="12" r="8.8" />,
  play: <path d="M8.3 5.6v12.8L19 12 8.3 5.6Z" />,
  user: <><circle cx="12" cy="8.3" r="3.5" /><path d="M5.2 19.5c1.2-3.1 3.4-4.7 6.8-4.7s5.6 1.6 6.8 4.7" /></>,
  image: <><rect x="3.5" y="5" width="17" height="14" rx="3" /><path d="m4.4 16.7 4.2-3.9 3.2 2.7 3.3-3 4.5 4" /></>,
  message: <path d="M5.8 4.5h12.4a2.3 2.3 0 0 1 2.3 2.3v8.3a2.3 2.3 0 0 1-2.3 2.3h-6l-5.7 3.8v-3.8H5.8a2.3 2.3 0 0 1-2.3-2.3V6.8a2.3 2.3 0 0 1 2.3-2.3Z" />,
  video: <><rect x="3.2" y="5.4" width="12.6" height="13.2" rx="3" /><path d="m15.8 10 5-3v10l-5-3" /></>,
  heart,
  star,
  leaf: <path d="M5 19c0-8.2 5-13.2 14-14 0 9-4.8 13.6-13 14Z" />,
  palette: <path d="M12 3.5a8.5 8.5 0 1 0 0 17c1.5 0 2.1-1.1 1.5-2.2-.6-1.2.2-2.4 1.6-2.4H17a3.5 3.5 0 0 0 3.5-3.5C20.5 7 16.8 3.5 12 3.5Z" />,
};

export function Icon({
  name,
  size = 20,
  color = "currentColor",
  strokeWidth = 1.85,
  fill = "none",
}: {
  name: RoleDashboardIconName;
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
      <g fill={color} fillOpacity={0.16} stroke="none">{TINTS[name]}</g>
      <g>{PATHS[name]}</g>
    </svg>
  );
}

export function IconBadge({
  name,
  tone = "primary",
  size = 44,
}: {
  name: RoleDashboardIconName;
  tone?: "primary" | "accent" | "mint" | "danger" | "neutral";
  size?: number;
}) {
  const tones = {
    primary: { bg: "var(--primary-50, #E8EAFF)", fg: "var(--primary, #1F2DE6)" },
    accent: { bg: "var(--accent-50, #FEF3C7)", fg: "var(--accent, #B45309)" },
    mint: { bg: "var(--mint-50, #E6F8F0)", fg: "var(--mint, #047857)" },
    danger: { bg: "var(--danger-50, #FEE2E2)", fg: "var(--danger, #DC2626)" },
    neutral: { bg: "var(--surface-2, #E2E5EA)", fg: "var(--ink-2, #5D6470)" },
  }[tone];
  return (
    <span style={{
      width: size,
      height: size,
      borderRadius: size / 2.6,
      background: tones.bg,
      color: tones.fg,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
    }}>
      <Icon name={name} size={Math.round(size * 0.5)} />
    </span>
  );
}

export type RolePortalIconName = RoleDashboardIconName;
export function RolePortalIcon({ name, size = 20, color = "currentColor" }: { name: RolePortalIconName; size?: number; color?: string }) {
  return <Icon name={name} size={size} color={color} />;
}