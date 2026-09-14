import { Link } from "react-router-dom";

interface LogoProps {
  className?: string;
  showBadge?: boolean;
}

export function Logo({ className = "", showBadge = true }: LogoProps) {
  return (
    <Link
      to="/"
      className={`group flex items-center gap-2.5 no-underline select-none transition-transform duration-150 active:scale-[0.98] ${className}`}
      title="ClaimBack — Autonomous Financial Recovery"
    >
      {/* Bespoke Logomark */}
      <div className="relative flex h-8 w-8 items-center justify-center">
        {/* Ambient subtle glow on hover */}
        <div className="absolute inset-0 rounded-xl bg-forest/20 blur-md opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

        <svg
          viewBox="0 0 32 32"
          width="32"
          height="32"
          className="relative drop-shadow-xs transition-transform duration-200 group-hover:scale-105"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Primary Brand Gradient: uses theme accent */}
            <linearGradient id="cb-logo-bg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="var(--color-forest)" />
              <stop offset="100%" stopColor="var(--color-forest-dim)" />
            </linearGradient>

            {/* Inner Ribbon Gradient */}
            <linearGradient id="cb-ribbon-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0.75" />
            </linearGradient>

            {/* Accent Gold/Mint Return Node */}
            <linearGradient id="cb-accent-node" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="var(--color-alert)" />
              <stop offset="100%" stopColor="#f59e0b" />
            </linearGradient>
          </defs>

          {/* Squircle Outer Base */}
          <rect
            x="1"
            y="1"
            width="30"
            height="30"
            rx="8.5"
            fill="url(#cb-logo-bg)"
            stroke="rgba(255,255,255,0.15)"
            strokeWidth="1"
          />

          {/* Precision Shield + Recovery Loop Mark */}
          {/* Left C-Arc & Outer Vault Armor */}
          <path
            d="M16 6.5C11.8 6.5 8.5 8.2 8.5 12.8C8.5 18.5 13.2 22.8 16 25.2C18.8 22.8 23.5 18.5 23.5 12.8C23.5 8.2 20.2 6.5 16 6.5Z"
            stroke="url(#cb-ribbon-grad)"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="rgba(255,255,255,0.06)"
          />

          {/* Dynamic Capital Return Arrow (Loops back inwards) */}
          <path
            d="M19.8 13.2C19.8 11.2 18.1 9.8 16 9.8C13.8 9.8 12.2 11.4 12.2 13.6C12.2 16.5 15.5 17.5 18.5 18.8C19.2 19.1 19.8 19.8 19.8 20.6"
            stroke="url(#cb-ribbon-grad)"
            strokeWidth="1.9"
            strokeLinecap="round"
          />

          {/* Autonomous Pulse Indicator Dot */}
          <circle cx="12.5" cy="20.2" r="1.6" fill="url(#cb-accent-node)" />
        </svg>
      </div>

      {/* Brand Wordmark */}
      <div className="flex items-center gap-2">
        <div className="flex items-baseline tracking-tight">
          <span className="font-sans text-[17px] font-semibold text-ink tracking-[-0.02em]">
            Claim
          </span>
          <span className="font-sans text-[17px] font-bold text-forest tracking-[-0.02em]">
            Back
          </span>
        </div>

        {showBadge && (
          <span className="rounded-md border border-hairline bg-cream-100/90 px-1.5 py-0.5 text-[9.5px] font-mono font-medium tracking-wider uppercase text-ink-faint shadow-2xs">
            Agent
          </span>
        )}
      </div>
    </Link>
  );
}
