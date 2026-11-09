import React from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "./Icon";
import type { IconName } from "./Icon";
import { BrandMark } from "../../../shared/BrandMark";
import { AccessibleDialog } from "../../../shared/ui";

/* ---------- Inline-SVG illustrations ---------- */
export function Wordmark({ size = 34 }: { size?: number }) {
  return (
    <span className="wordmark">
      <BrandMark size={size} />
      <span>Sketch2Life</span>
    </span>
  );
}

export function Mascot({ size = 150, mic = false }: { size?: number; mic?: boolean }) {
  return (
    <svg className="art float" width={size} height={size * 1.15} viewBox="0 0 120 138" aria-hidden="true">
      <path d="M22 62c-4-30 12-52 38-52s42 22 38 52c-4 8-10 14-16 16H38c-6-2-12-8-16-16Z" fill="#5b3b2a" />
      <ellipse cx="60" cy="66" rx="31" ry="30" fill="#ffe0c2" />
      <path d="M30 56c6-20 22-26 34-24 14 2 24 10 26 24-12-6-24-10-34-10-10 0-18 4-26 10Z" fill="#5b3b2a" />
      <ellipse cx="48" cy="68" rx="4.5" ry="6" fill="#1e293b" />
      <ellipse cx="72" cy="68" rx="4.5" ry="6" fill="#1e293b" />
      <circle cx="49.5" cy="66" r="1.6" fill="#fff" />
      <circle cx="73.5" cy="66" r="1.6" fill="#fff" />
      <ellipse cx="40" cy="78" rx="6" ry="4" fill="#fda4af" opacity="0.7" />
      <ellipse cx="80" cy="78" rx="6" ry="4" fill="#fda4af" opacity="0.7" />
      <path d="M52 82c4 5 12 5 16 0" stroke="#be123c" strokeWidth="2.6" fill="none" strokeLinecap="round" />
      <path d="M34 98c0-6 12-10 26-10s26 4 26 10v34H34V98Z" fill="#3b82f6" />
      <path d="M44 92h32l-4 14H48l-4-14Z" fill="#fde68a" />
      <rect x="50" y="104" width="20" height="28" rx="6" fill="#2563eb" />
      <circle cx="56" cy="114" r="2.4" fill="#fbbf24" />
      <circle cx="64" cy="114" r="2.4" fill="#fbbf24" />
      {mic && <rect x="86" y="86" width="9" height="20" rx="4.5" fill="#475569" />}
      <path d="M92 86 108 66" stroke="#ffe0c2" strokeWidth="9" strokeLinecap="round" />
      <path d="m104 58 8-12" stroke="#fbbf24" strokeWidth="5" strokeLinecap="round" />
    </svg>
  );
}

export function Dino({ size = 110 }: { size?: number }) {
  return (
    <svg className="art float slow" width={size} height={size} viewBox="0 0 120 120" aria-hidden="true">
      <path d="M96 84c14 2 20-8 14-14-6 6-10 4-14 0" fill="#34d399" />
      <ellipse cx="58" cy="76" rx="36" ry="32" fill="#34d399" />
      <ellipse cx="58" cy="86" rx="22" ry="20" fill="#bbf7d0" />
      <circle cx="60" cy="44" r="26" fill="#34d399" />
      <path d="M44 20l6 10-12-2 6-8Zm16-4 6 12H54l6-12Zm16 4 6 8-12 2 6-10Z" fill="#fbbf24" />
      <circle cx="51" cy="44" r="6" fill="#fff" />
      <circle cx="71" cy="44" r="6" fill="#fff" />
      <circle cx="52" cy="45" r="3" fill="#1e293b" />
      <circle cx="72" cy="45" r="3" fill="#1e293b" />
      <ellipse cx="42" cy="55" rx="5" ry="3" fill="#fda4af" opacity="0.8" />
      <ellipse cx="80" cy="55" rx="5" ry="3" fill="#fda4af" opacity="0.8" />
      <path d="M52 56c5 6 13 6 18 0" stroke="#065f46" strokeWidth="2.6" fill="none" strokeLinecap="round" />
    </svg>
  );
}

export function Robot({ size = 120 }: { size?: number }) {
  return (
    <svg className="art float" width={size} height={size} viewBox="0 0 120 120" aria-hidden="true">
      <line x1="60" y1="8" x2="60" y2="22" stroke="#64748b" strokeWidth="4" strokeLinecap="round" />
      <circle cx="60" cy="8" r="6" fill="#fbbf24" />
      <rect x="22" y="22" width="76" height="58" rx="22" fill="#e0ecff" stroke="#3b82f6" strokeWidth="4" />
      <rect x="32" y="34" width="56" height="34" rx="14" fill="#1e3a8a" />
      <circle cx="48" cy="51" r="7" fill="#7dd3fc" />
      <circle cx="72" cy="51" r="7" fill="#7dd3fc" />
      <path d="M52 62c5 4 11 4 16 0" stroke="#7dd3fc" strokeWidth="3" fill="none" strokeLinecap="round" />
      <rect x="34" y="84" width="52" height="28" rx="12" fill="#3b82f6" />
      <circle cx="60" cy="98" r="6" fill="#fde68a" />
      <rect x="12" y="46" width="8" height="18" rx="4" fill="#93c5fd" />
      <rect x="100" y="46" width="8" height="18" rx="4" fill="#93c5fd" />
    </svg>
  );
}

export function SunDoodle({ size = 54 }: { size?: number }) {
  return (
    <svg className="art float slow delay" width={size} height={size} viewBox="0 0 60 60" aria-hidden="true">
      <g stroke="#fbbf24" strokeWidth="4" strokeLinecap="round">
        <path d="M30 4v8M30 48v8M4 30h8M48 30h8M11 11l5 5M44 44l5 5M49 11l-5 5M16 44l-5 5" />
      </g>
      <circle cx="30" cy="30" r="12" fill="#fde047" />
    </svg>
  );
}

export function StatusBarIcons() {
  return (
    <span className="row" style={{ gap: 6 }} aria-hidden="true">
      {/* Signal bars */}
      <svg width="16" height="12" viewBox="0 0 16 12" fill="currentColor">
        <rect x="1" y="8" width="2.5" height="3.5" rx="0.8" />
        <rect x="4.8" y="6" width="2.5" height="5.5" rx="0.8" />
        <rect x="8.6" y="3.5" width="2.5" height="8" rx="0.8" />
        <rect x="12.4" y="1" width="2.5" height="10.5" rx="0.8" />
      </svg>
      {/* Wi-Fi */}
      <svg width="15" height="12" viewBox="0 0 16 12" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
        <path d="M1.5 4.2a10 10 0 0 1 13 0" />
        <path d="M4.2 7a6 6 0 0 1 7.6 0" />
        <circle cx="8" cy="10" r="1.2" fill="currentColor" stroke="none" />
      </svg>
      {/* Battery */}
      <svg width="22" height="12" viewBox="0 0 24 12" fill="none">
        <rect x="1" y="1.5" width="19" height="9" rx="2.5" stroke="currentColor" strokeWidth="1.5" />
        <rect x="3" y="3.3" width="14" height="5.4" rx="1.2" fill="#10b981" />
        <path d="M21.5 4.2v3.6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    </span>
  );
}

export function ParentAvatarSvg({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true">
      <circle cx="24" cy="24" r="22" fill="#dbeafe" />
      <path d="M11 25c0-9 5.8-15 13-15s13 6 13 15c0 4-2 7-4 8H15c-2-1-4-4-4-8Z" fill="#472d21" />
      <circle cx="24" cy="24" r="10" fill="#ffe0c2" />
      <path d="M15 20c3-5 8-7 13-6 3 1 5 3 6 6-4-2-8-3-12-3-3 0-5 1-7 3Z" fill="#472d21" />
      <circle cx="20.5" cy="24" r="1.5" fill="#0f2447" />
      <circle cx="27.5" cy="24" r="1.5" fill="#0f2447" />
      <path d="M21 28c1.8 1.8 4.2 1.8 6 0" stroke="#e11d48" strokeWidth="1.8" fill="none" strokeLinecap="round" />
      <path d="M14 42c1.5-5.5 5.2-8 10-8s8.5 2.5 10 8" fill="#2563eb" />
    </svg>
  );
}

export function ChildAvatarSvg({ variant = 0, size = 34 }: { variant?: number; size?: number }) {
  const isBoy = variant % 2 === 1;
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true">
      <circle cx="24" cy="24" r="22" fill={isBoy ? "#d1fae5" : "#fef3c7"} />
      <path
        d={
          isBoy
            ? "M13 22c0-7 4.8-12 11-12s11 5 11 12H13Z"
            : "M10 26c-1-9 5-16 14-16s15 7 14 16c-2 3-4 5-6 5H16c-2 0-4-2-6-5Z"
        }
        fill={isBoy ? "#1e293b" : "#5b3b2a"}
      />
      <circle cx="24" cy="25" r="10.5" fill="#ffe0c2" />
      <path d="M14 20c3-4 8-5 12-4 3 .6 6 2 8 4-5-1.5-9-2-13-1.5-3 .3-5 1-7 1.5Z" fill={isBoy ? "#1e293b" : "#5b3b2a"} />
      <circle cx="20" cy="25" r="1.7" fill="#0f2447" />
      <circle cx="28" cy="25" r="1.7" fill="#0f2447" />
      <circle cx="17" cy="28" r="2.2" fill="#fda4af" opacity="0.75" />
      <circle cx="31" cy="28" r="2.2" fill="#fda4af" opacity="0.75" />
      <path d="M21 29c1.8 2 4.2 2 6 0" stroke="#be123c" strokeWidth="1.8" fill="none" strokeLinecap="round" />
      <path d="M14 42c1.5-5 5.2-7.5 10-7.5s8.5 2.5 10 7.5" fill={isBoy ? "#10b981" : "#3b82f6"} />
    </svg>
  );
}

/* ---------- Primitives ---------- */
export function TopBar({
  title,
  back = true,
  onBack,
  right,
}: {
  title?: string;
  back?: boolean;
  onBack?: () => void;
  right?: React.ReactNode;
}) {
  const nav = useNavigate();
  return (
    <div className="topbar">
      {back ? (
        <button type="button" className="round-btn" aria-label="Quay lại" onClick={onBack ?? (() => nav(-1))}>
          <Icon name="arrow-left" size={20} />
        </button>
      ) : (
        <span style={{ width: 44 }} />
      )}
      <div className="ttl">{title}</div>
      {right ?? <span style={{ width: 44 }} />}
    </div>
  );
}

const STEP_LABELS = ["Tùy chọn", "Chụp tranh", "Ý tưởng", "Kịch bản", "Video"];
export function StepChips({ current, optionalSkipped = false }: { current: number; optionalSkipped?: boolean }) {
  const stepStatus = optionalSkipped && current > 1 ? ", bước tùy chọn đã bỏ qua" : "";
  return (
    <ol
      className="steps"
      aria-label={`Tiến trình câu chuyện: bước ${current} trên ${STEP_LABELS.length}${stepStatus}`}
    >
      {STEP_LABELS.map((l, i) => {
        const n = i + 1;
        const skipped = optionalSkipped && current > 1 && n === 1;
        const cls = skipped ? "skipped" : n < current ? "done" : n === current ? "on" : "";
        const status = skipped
          ? "đã bỏ qua"
          : n === current
          ? "hiện tại"
          : n < current
          ? "đã hoàn tất"
          : "sắp tới";
        return (
          <li
            key={l}
            className={`step ${cls}`}
            aria-label={`Bước ${n}: ${l}, ${status}`}
            aria-current={n === current ? "step" : undefined}
          >
            <i aria-hidden="true">
              {skipped ? "–" : n < current ? <Icon name="check" size={12} strokeWidth={3} /> : n}
            </i>
            {i < STEP_LABELS.length - 1 && <span aria-hidden="true" className={`bar${skipped ? " is-skipped" : ""}`} />}
          </li>
        );
      })}
    </ol>
  );
}

export function Btn({
  children,
  tone,
  onClick,
  disabled,
  small,
  type = "button",
}: {
  children: React.ReactNode;
  tone?: "amber" | "mint" | "danger";
  onClick?: () => void;
  disabled?: boolean;
  small?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button type={type} className={`btn3d ${tone ?? ""} ${small ? "sm" : ""}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

export function Soft({
  children,
  onClick,
  small,
  red,
  disabled,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  small?: boolean;
  red?: boolean;
  disabled?: boolean;
}) {
  return (
    <button type="button" className={`btn-soft ${small ? "sm" : ""} ${red ? "red" : ""}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

export function Progress({ value, tone }: { value: number; tone?: "mint" | "amber" }) {
  return (
    <div className={`pbar ${tone ?? ""}`} role="progressbar" aria-valuenow={Math.round(value)} aria-valuemin={0} aria-valuemax={100}>
      <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

export function Note({
  tone,
  emoji,
  icon,
  children,
}: {
  tone: "amber" | "blue" | "mint" | "red";
  emoji?: string;
  icon?: IconName;
  children: React.ReactNode;
}) {
  const iconName: IconName =
    icon ??
    (tone === "mint"
      ? "check"
      : tone === "red"
      ? "alert"
      : emoji === "🛡️" || emoji === "🔒"
      ? "shield"
      : emoji === "🎬"
      ? "video"
      : emoji === "🎙️"
      ? "mic"
      : "sparkle");
  return (
    <div className={`note ${tone}`}>
      <span className="note-ico" aria-hidden="true">
        <Icon name={iconName} size={16} />
      </span>
      <div className="grow">{children}</div>
    </div>
  );
}

export function Switch({ on, onChange, label }: { on: boolean; onChange: () => void; label: string }) {
  return <button type="button" className={`switch ${on ? "on" : ""}`} role="switch" aria-checked={on} aria-label={label} onClick={onChange} />;
}

export function Waveform({ live }: { live: boolean }) {
  const hs = [18, 30, 46, 26, 58, 38, 64, 30, 50, 22, 44, 62, 34, 52, 24, 40, 56, 28, 48, 20, 36, 60, 30, 44];
  return (
    <div className={`wave ${live ? "live" : ""}`} aria-hidden="true">
      {hs.map((h, i) => (
        <i key={i} style={{ ["--h" as string]: `${h}px`, ["--d" as string]: `${(i % 8) * 0.11}s` } as React.CSSProperties} />
      ))}
    </div>
  );
}

export function Sheet({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <AccessibleDialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={title}
      className="is-sheet sheet"
      showClose={false}
      container={typeof document === "undefined" ? null : document.querySelector<HTMLElement>(".phone")}
    >
      <span className="grab" />
      <div className="row between">
        <h2 className="h2">{title}</h2>
        <button type="button" className="round-btn" aria-label="Đóng" onClick={onClose}>
          <Icon name="close" size={18} />
        </button>
      </div>
      {children}
    </AccessibleDialog>
  );
}

export const GRADS = ["g-sky", "g-sun", "g-mint", "g-pink", "g-violet"];

