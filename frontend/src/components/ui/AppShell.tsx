import { Outlet } from "react-router-dom";
import { TopBar } from "./TopBar";
import { IconRailNav } from "./IconRailNav";

export function AppShell() {
  return (
    <div className="flex min-h-svh flex-col">
      <TopBar />
      <div className="flex flex-1">
        <IconRailNav />
        <main className="min-w-0 flex-1 px-6 py-7 sm:px-8 sm:py-8">
          <div className="max-w-4xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
