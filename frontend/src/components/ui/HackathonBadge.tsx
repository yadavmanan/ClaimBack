/** Contains ALL of the hackathon-banner styling (pixel font + neon accents) — nowhere else in the app. */
export function HackathonBadge() {
  return (
    <a
      href="https://www.hackathon.dev/"
      target="_blank"
      rel="noreferrer"
      className="group inline-flex items-center gap-2 rounded-full border border-ink/10 bg-ink px-3 py-1.5 no-underline"
    >
      <span
        className="h-2 w-2 shrink-0 rounded-[1px]"
        style={{ background: "var(--color-hackathon-green)" }}
      />
      <span className="font-pixel text-[9px] leading-none text-cream">Agents for Humans</span>
      <span
        className="h-2 w-2 shrink-0 rounded-[1px]"
        style={{ background: "var(--color-hackathon-pink)" }}
      />
    </a>
  );
}
