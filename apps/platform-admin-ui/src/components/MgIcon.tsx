import React from "react";

export type MgIconName =
  | "home" | "users" | "calendar" | "chart" | "shield" | "gear" | "building" | "book" | "grid"
  | "doc" | "bell" | "check" | "clock" | "school" | "play" | "plus" | "pencil" | "trash"
  | "eye" | "eyeoff" | "globe" | "chevron" | "chevdown" | "layers" | "more" | "search" | "arrow"
  | "userplus" | "list" | "lock";

const P: Record<MgIconName, React.ReactNode> = {
  home: <><path d="M4 11l8-7 8 7" /><path d="M6 10v9h12v-9" /><path d="M10 19v-5h4v5" /></>,
  users: <><circle cx="9" cy="8.5" r="3.2" /><path d="M3.5 19c.8-3 3-4.5 5.5-4.5s4.7 1.5 5.5 4.5" /><circle cx="17" cy="9.5" r="2.4" /><path d="M16.5 14.6c2.2.1 3.7 1.4 4.3 3.9" /></>,
  calendar: <><rect x="4" y="5.5" width="16" height="14.5" rx="3" /><path d="M8 3.5v4M16 3.5v4M4 10h16" /></>,
  chart: <><path d="M6 19V11M12 19V5M18 19v-6" /></>,
  shield: <><path d="M12 3.5l7 2.5v5.5c0 4.2-3 7.4-7 9-4-1.6-7-4.8-7-9V6l7-2.5Z" /><path d="M9 12l2.2 2.2L15.5 10" /></>,
  gear: <><circle cx="12" cy="12" r="3" /><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8" /></>,
  building: <><rect x="5" y="3.5" width="14" height="17" rx="2" /><path d="M9 8h2M13 8h2M9 12h2M13 12h2M10 20.5v-4h4v4" /></>,
  book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5V5.5Z" /><path d="M8 7h8M8 11h6" /></>,
  grid: <><rect x="4" y="4" width="6.5" height="6.5" rx="1.8" /><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.8" /><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.8" /><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.8" /></>,
  doc: <><path d="M6 3.5h8l4 4V20.5H6Z" /><path d="M14 3.5v4h4M9 12h6M9 16h6" /></>,
  bell: <><path d="M6 17V11a6 6 0 0 1 12 0v6l1.5 2h-15L6 17Z" /><path d="M10 21h4" /></>,
  check: <path d="M5 12.5l4.5 4.5L19 7.5" />,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>,
  school: <><path d="M3.5 10L12 4l8.5 6" /><path d="M5.5 10v9.5h13V10" /><path d="M10 19.5v-5h4v5" /></>,
  play: <path d="M8 5.5v13l11-6.5-11-6.5Z" />,
  plus: <path d="M12 5v14M5 12h14" />,
  pencil: <><path d="M5 19l1-4L16.5 4.5a2 2 0 0 1 3 3L9 18l-4 1Z" /></>,
  trash: <><path d="M5 7h14M10 7V4.5h4V7M7 7l.8 12.5h8.4L17 7" /><path d="M10 11v5M14 11v5" /></>,
  eye: <><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" /><circle cx="12" cy="12" r="3" /></>,
  eyeoff: <><path d="M3 3l18 18" /><path d="M10 6a9 9 0 0 1 2-.5c6 0 9.5 6.5 9.5 6.5a16 16 0 0 1-3 3.8M6.5 7.5A16 16 0 0 0 2.5 12S6 18.5 12 18.5c1.3 0 2.5-.3 3.6-.8" /></>,
  globe: <><circle cx="12" cy="12" r="8.5" /><path d="M3.5 12h17M12 3.5c2.5 2.5 3.5 5.5 3.5 8.5S14.500 18 12 20.500C9.500 18 8.500 15 8.500 12S9.500 6 12 3.500Z" /></>,
  chevron: <path d="M9 6l6 6-6 6" />,
  chevdown: <path d="M6 9l6 6 6-6" />,
  layers: <><path d="M12 4l8.500 4.500L12 13 3.500 8.500 12 4Z" /><path d="M3.500 12.500L12 17l8.500-4.500M3.500 16L12 20.500 20.500 16" /></>,
  more: <><circle cx="6" cy="12" r="1.3" /><circle cx="12" cy="12" r="1.3" /><circle cx="18" cy="12" r="1.3" /></>,
  search: <><circle cx="11" cy="11" r="6.500" /><path d="M20 20l-4.200-4.200" /></>,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  userplus: <><circle cx="9" cy="8.5" r="3.2" /><path d="M3.500 19c.8-3 3-4.500 5.500-4.500s4.700 1.500 5.500 4.500M18 8v6M15 11h6" /></>,
  list: <path d="M5 7h14M5 12h14M5 17h9" />,
  lock: <><rect x="5" y="10.500" width="14" height="9.500" rx="2.500" /><path d="M8 10.500V8a4 4 0 0 1 8 0v2.500" /></>,
};

export function MgIcon({ name, size = 20, color = "currentColor" }: { name: MgIconName; size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {P[name]}
    </svg>
  );
}
