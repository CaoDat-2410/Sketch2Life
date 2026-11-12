// Crisp vector SVG icons matching the leader's SRSv3.1 UI design mockups

export function CloudBadgeIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="flex-shrink-0">
      <circle cx="12" cy="12" r="11" fill="#E0F2FE" />
      <path
        d="M7.5 16.5H16.2C18.02 16.5 19.5 15.02 19.5 13.2C19.5 11.52 18.25 10.13 16.62 9.93C16.06 7.68 14.03 6 11.6 6C8.73 6 6.4 8.33 6.4 11.2C6.4 11.38 6.41 11.55 6.43 11.72C5.32 12.16 4.5 13.24 4.5 14.5C4.5 15.6 5.4 16.5 6.5 16.5H7.5Z"
        fill="white"
        stroke="#0284C7"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="10.2" cy="12.3" r="0.9" fill="#0F172A" />
      <circle cx="13.8" cy="12.3" r="0.9" fill="#0F172A" />
      <path
        d="M10.8 14C11.2 14.5 12.8 14.5 13.2 14"
        stroke="#0284C7"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function LeafBadgeIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="flex-shrink-0">
      <circle cx="12" cy="12" r="11" fill="#DCFCE7" />
      <path
        d="M17.5 6.5C11.5 6.5 7 10.5 7 16.5C13 16.5 17.5 12.5 17.5 6.5Z"
        fill="#22C55E"
        stroke="#15803D"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path
        d="M7 16.5L14.5 9.5"
        stroke="#DCFCE7"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function FlowerBadgeIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="flex-shrink-0">
      <circle cx="12" cy="12" r="11" fill="#FFE4E6" />
      <circle cx="12" cy="7.5" r="2.6" fill="#F43F5E" />
      <circle cx="16.2" cy="10.6" r="2.6" fill="#F43F5E" />
      <circle cx="14.6" cy="15.4" r="2.6" fill="#F43F5E" />
      <circle cx="9.4" cy="15.4" r="2.6" fill="#F43F5E" />
      <circle cx="7.8" cy="10.6" r="2.6" fill="#F43F5E" />
      <circle cx="12" cy="11.8" r="2.3" fill="#FACC15" />
    </svg>
  )
}

export function SunBadgeIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="flex-shrink-0">
      <circle cx="12" cy="12" r="11" fill="#FEF3C7" />
      <circle cx="12" cy="12" r="4.5" fill="#F59E0B" />
      <path
        d="M12 4.5V6M12 18V19.5M4.5 12H6M18 12H19.5M6.7 6.7L7.8 7.8M16.2 16.2L17.3 17.3M17.3 6.7L16.2 7.8M7.8 16.2L6.7 17.3"
        stroke="#D97706"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function SproutBadgeIcon({
  size = 16,
  color = '#16A34A',
}: {
  size?: number
  color?: string
}) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" className="flex-shrink-0">
      <path
        d="M10 17V9"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M10 11C10 7.5 13 5 16.5 5C16.5 8.5 14 11 10 11Z"
        fill={color}
        fillOpacity="0.2"
        stroke={color}
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M10 12.5C10 9.5 7.5 7.5 4 7.5C4 10.5 6.5 12.5 10 12.5Z"
        fill={color}
        fillOpacity="0.2"
        stroke={color}
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function GreenCheckCircle({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" className="flex-shrink-0">
      <circle cx="10" cy="10" r="9" fill="#16A34A" />
      <path
        d="M6.2 10.3L8.7 12.8L14 7.5"
        stroke="white"
        strokeWidth="2.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function BlueCheckBox({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" className="flex-shrink-0">
      <rect x="1.5" y="1.5" width="17" height="17" rx="4.5" fill="#1D63F2" />
      <path
        d="M6 10.2L8.6 12.8L14.2 7.2"
        stroke="white"
        strokeWidth="2.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
