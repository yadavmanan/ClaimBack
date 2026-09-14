import { Logo } from "./Logo";
import { ThemeSelector } from "./ThemeSelector";

export function TopBar() {
  return (
    <header className="flex items-center justify-between border-b border-hairline px-6 py-2.5">
      <Logo />
      <ThemeSelector />
    </header>
  );
}
