export function Logo({ height = 28 }: { height?: number }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }} aria-label="Sketch2Life">
      <svg width={height} height={height} viewBox="0 0 48 48" aria-hidden="true">
        {/* Stem */}
        <path
          d="M24 43V23"
          stroke="#2563EB"
          strokeWidth="3.8"
          strokeLinecap="round"
          fill="none"
        />
        {/* Left Blue Sprout Wing */}
        <path
          d="M24 29C11 29 5 21 5 10c11 0 19 6 19 19z"
          fill="#2563EB"
        />
        {/* Right Mint & Yellow Sprout Wing */}
        <path
          d="M24 25C24 12 31 5 43 5c0 12-7 20-19 20z"
          fill="#ECFDF5"
          stroke="#FBBF24"
          strokeWidth="3.6"
          strokeLinejoin="round"
        />
        <path
          d="M29 19c3.2-3.2 6.5-5.2 10-6.2"
          stroke="#34D399"
          strokeWidth="3.2"
          strokeLinecap="round"
          fill="none"
        />
        <circle cx="15" cy="18" r="2.2" fill="#FFFFFF" opacity="0.85" />
      </svg>
      <span
        style={{
          fontWeight: 800,
          fontSize: Math.round(height * 0.78),
          color: "#0F172A",
          letterSpacing: "-0.025em",
        }}
      >
        Sketch2Life
      </span>
    </span>
  );
}
