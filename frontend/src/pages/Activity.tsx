import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useClaimBackStore } from "../hooks/useClaimBackStore";
import { ClockIcon } from "../components/icons";
import { formatRelativeTime } from "../lib/format";

export function Activity() {
  const store = useClaimBackStore();
  const activity = store.getActivity();

  useEffect(() => {
    void store.loadDashboard();
  }, [store]);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="font-display text-3xl font-medium text-ink">Activity</h1>
        <p className="mt-2 max-w-xl text-ink-soft">
          A full audit trail of everything ClaimBack has done on your behalf, across every opportunity.
        </p>
      </div>

      <ol className="flex flex-col gap-5 border-l border-hairline pl-6">
        {activity.map((entry) => (
          <li key={entry.id} className="relative">
            <span className="absolute -left-[29px] top-1 flex h-5 w-5 items-center justify-center rounded-full bg-cream-100 text-ink-soft">
              <ClockIcon width={11} height={11} />
            </span>
            <p className="text-sm text-ink">
              <Link to={`/opportunities/${entry.opportunity_id}`} className="hover:underline">
                {entry.label}
              </Link>
            </p>
            <p className="mt-0.5 font-mono text-xs text-ink-faint">{formatRelativeTime(entry.timestamp)}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
