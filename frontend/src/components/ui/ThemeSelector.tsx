import { useState, useEffect, useRef } from "react";
import { PaletteIcon, CheckIcon } from "../icons";

export type ThemeId = "fintech" | "cream" | "obsidian" | "swiss" | "glacier";

interface ThemeOption {
  id: ThemeId;
  name: string;
  tagline: string;
  bgHex: string;
  cardHex: string;
  accentHex: string;
}

const THEMES: ThemeOption[] = [
  {
    id: "fintech",
    name: "FinTech Crisp",
    tagline: "Stripe & Linear modern SaaS slate",
    bgHex: "#f8fafc",
    cardHex: "#ffffff",
    accentHex: "#059669",
  },
  {
    id: "cream",
    name: "Warm Cream",
    tagline: "Classic calm heritage",
    bgHex: "#f7f5ef",
    cardHex: "#ffffff",
    accentHex: "#1f5d3a",
  },
  {
    id: "obsidian",
    name: "Obsidian & Mint",
    tagline: "High-tech dark mode agent",
    bgHex: "#090d14",
    cardHex: "#121822",
    accentHex: "#10b981",
  },
  {
    id: "swiss",
    name: "Swiss Editorial",
    tagline: "Luxury alabaster & racing green",
    bgHex: "#fbfbfa",
    cardHex: "#ffffff",
    accentHex: "#144d32",
  },
  {
    id: "glacier",
    name: "Glacier Clarity",
    tagline: "Cool ice-blue & electric cobalt",
    bgHex: "#f0f4f8",
    cardHex: "#ffffff",
    accentHex: "#2563eb",
  },
];

export function ThemeSelector() {
  const [currentTheme, setCurrentTheme] = useState<ThemeId>(() => {
    const saved = localStorage.getItem("claimback-theme") as ThemeId | null;
    return saved || "fintech";
  });
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Apply theme to html root
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", currentTheme);
    localStorage.setItem("claimback-theme", currentTheme);
  }, [currentTheme]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      window.addEventListener("mousedown", handleClickOutside);
      return () => window.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  const activeTheme = THEMES.find((t) => t.id === currentTheme) || THEMES[0];

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Theme setting button with theme symbol */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="group inline-flex items-center gap-2 rounded-full border border-hairline bg-cream-100/80 px-3 py-1.5 text-xs font-medium text-ink transition-all duration-150 hover:border-ink/20 hover:bg-cream-200"
        title="Change color theme"
        aria-label="Theme settings"
      >
        <span className="flex items-center justify-center text-forest transition-transform duration-200 group-hover:rotate-45">
          <PaletteIcon width={15} height={15} />
        </span>
        <span className="text-[11px] font-semibold tracking-tight text-ink">
          {activeTheme.name}
        </span>
        <span
          className="h-2 w-2 rounded-full border border-ink/10 shadow-xs"
          style={{ backgroundColor: activeTheme.accentHex }}
        />
      </button>

      {/* Popover Dropdown */}
      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-64 origin-top-right rounded-2xl border border-hairline bg-white/95 p-1.5 shadow-xl backdrop-blur-md transition-all duration-150 animate-in fade-in zoom-in-95">
          <div className="px-2.5 py-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">
              Color Theme
            </span>
          </div>

          <div className="flex flex-col gap-1">
            {THEMES.map((theme) => {
              const isSelected = theme.id === currentTheme;
              return (
                <button
                  key={theme.id}
                  type="button"
                  onClick={() => {
                    setCurrentTheme(theme.id);
                    setIsOpen(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl px-2.5 py-2 text-left transition-all duration-150 ${
                    isSelected
                      ? "bg-cream-100 font-semibold text-ink shadow-xs"
                      : "text-ink-soft hover:bg-cream-100/60 hover:text-ink"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {/* Swatch preview */}
                    <div
                      className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-black/10 shadow-xs"
                      style={{ backgroundColor: theme.bgHex }}
                    >
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: theme.accentHex }}
                      />
                    </div>

                    <div className="min-w-0">
                      <div className="text-xs leading-tight text-ink font-medium">
                        {theme.name}
                      </div>
                      <div className="text-[10px] text-ink-faint leading-tight truncate">
                        {theme.tagline}
                      </div>
                    </div>
                  </div>

                  {isSelected && (
                    <span className="shrink-0 text-forest pl-1">
                      <CheckIcon width={14} height={14} />
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
