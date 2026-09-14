import { NavLink } from "react-router-dom";
import { ActivityIcon, HomeIcon, VaultIcon } from "../icons";
import { cn } from "../../lib/cn";

const links = [
  { to: "/", label: "Dashboard", icon: HomeIcon, end: true },
  { to: "/vault", label: "Vault", icon: VaultIcon, end: false },
  { to: "/activity", label: "Activity", icon: ActivityIcon, end: false },
];

export function IconRailNav() {
  return (
    <nav className="sticky top-0 hidden h-[calc(100svh-53px)] w-48 shrink-0 flex-col border-r border-hairline bg-cream sm:flex">
      {/* Nav links — top section, scrolls if nav grows */}
      <div className="flex-1 overflow-y-auto px-3 py-5">
        <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-ink-faint/60">
          Menu
        </p>
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-forest-soft text-forest-dim"
                  : "text-ink-soft hover:bg-cream-100 hover:text-ink",
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  width={16}
                  height={16}
                  className={isActive ? "text-forest" : "text-ink-faint"}
                />
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>

      {/* Built-on — pinned footer, always visible, never scrolled out of view */}
      <div className="shrink-0 border-t border-hairline px-3 py-3">
        <p className="mb-2 text-[9px] font-semibold uppercase tracking-widest text-ink-faint/50">
          Built on
        </p>

        {/* AWS + Bedrock — side by side */}
        <div className="mb-1.5 grid grid-cols-2 gap-1">
          <a
            href="https://aws.amazon.com/"
            target="_blank"
            rel="noreferrer"
            title="Amazon Web Services"
            className="group flex flex-col items-center gap-0.5 rounded-lg px-1 py-1.5 transition-all duration-150 hover:bg-cream-100"
          >
            <img
              src="/aws.webp"
              alt="AWS"
              className="h-6 w-auto object-contain opacity-50 grayscale transition-all duration-200 group-hover:opacity-100 group-hover:grayscale-0"
            />
            <span className="text-[8px] font-semibold tracking-wide text-ink-faint/50 group-hover:text-ink-faint">
              AWS
            </span>
          </a>
          <a
            href="https://aws.amazon.com/bedrock/"
            target="_blank"
            rel="noreferrer"
            title="Amazon Bedrock"
            className="group flex flex-col items-center gap-0.5 rounded-lg px-1 py-1.5 transition-all duration-150 hover:bg-cream-100"
          >
            <img
              src="/bedrock.png"
              alt="Amazon Bedrock"
              className="h-6 w-auto object-contain opacity-50 grayscale transition-all duration-200 group-hover:opacity-100 group-hover:grayscale-0"
            />
            <span className="text-[8px] font-semibold tracking-wide text-ink-faint/50 group-hover:text-ink-faint">
              Bedrock
            </span>
          </a>
        </div>

        {/* Strands — full width centered */}
        <a
          href="https://strandsagents.com/"
          target="_blank"
          rel="noreferrer"
          title="Strands Agents SDK"
          className="group flex w-full items-center justify-center rounded-lg px-2 py-1 transition-all duration-150 hover:bg-cream-100"
        >
          <img
            src="/strands.png"
            alt="Strands Agents"
            className="h-5 w-auto object-contain opacity-50 grayscale transition-all duration-200 group-hover:opacity-90 group-hover:grayscale-0"
          />
        </a>
      </div>
    </nav>
  );
}
