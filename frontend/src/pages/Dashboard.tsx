import { useEffect, useMemo } from "react";
import { useClaimBackStore } from "../hooks/useClaimBackStore";
import { PeaceMeter } from "../components/ui/PeaceMeter";
import { StatNumber } from "../components/ui/StatNumber";
import { OpportunityCard } from "../components/OpportunityCard";
import { DocumentIcon, VaultIcon, ActivityIcon } from "../components/icons";

const OPEN_STATUSES = new Set(["DETECTED", "VERIFYING", "NEEDS_EVIDENCE", "READY_FOR_APPROVAL"]);

export function Dashboard() {
  const store = useClaimBackStore();
  const error = store.getError();
  const opportunities = store.getOpportunities();
  const documents = store.getDocuments();

  useEffect(() => {
    void store.loadDashboard();
  }, [store]);

  const { open, history, totalRecoverable } = useMemo(() => {
    const open = opportunities.filter((o) => OPEN_STATUSES.has(o.status));
    const history = opportunities.filter((o) => !OPEN_STATUSES.has(o.status));
    const totalRecoverable = open.reduce((sum, o) => sum + o.impact_amount, 0);
    return { open, history, totalRecoverable };
  }, [opportunities]);

  return (
    <div className="flex flex-col gap-6">
      <PeaceMeter openCount={open.length} totalRecoverable={totalRecoverable} />

      {error && (
        <div className="rounded-xl border border-alert/30 bg-alert/10 px-4 py-3 text-sm text-alert">
          {error}
        </div>
      )}

      {/* Stat strip */}
      <div className="grid grid-cols-3 divide-x divide-hairline overflow-hidden rounded-xl border border-hairline bg-white/60">
        <div className="px-5 py-4">
          <div className="flex items-center gap-1.5 text-ink-faint">
            <DocumentIcon width={13} height={13} />
            <span className="text-[11px] font-semibold uppercase tracking-wider">Docs monitored</span>
          </div>
          <p className="mt-1.5 font-mono text-2xl font-semibold text-ink">{documents.length}</p>
        </div>
        <div className="px-5 py-4">
          <div className="flex items-center gap-1.5 text-ink-faint">
            <VaultIcon width={13} height={13} />
            <span className="text-[11px] font-semibold uppercase tracking-wider">Recoverable now</span>
          </div>
          <StatNumber value={totalRecoverable} className="mt-1.5 block font-mono text-2xl font-semibold text-forest" />
        </div>
        <div className="px-5 py-4">
          <div className="flex items-center gap-1.5 text-ink-faint">
            <ActivityIcon width={13} height={13} />
            <span className="text-[11px] font-semibold uppercase tracking-wider">Open claims</span>
          </div>
          <p className="mt-1.5 font-mono text-2xl font-semibold text-ink">{open.length}</p>
        </div>
      </div>

      {open.length > 0 && (
        <section className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <h2 className="font-display text-lg font-medium text-ink">Needs your attention</h2>
            <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-alert text-[10px] font-bold text-white">
              {open.length}
            </span>
          </div>
          <div className="flex flex-col gap-3">
            {open.map((opp) => (
              <OpportunityCard key={opp.opportunity_id} opportunity={opp} />
            ))}
          </div>
        </section>
      )}

      {history.length > 0 && (
        <section className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <h2 className="font-display text-lg font-medium text-ink-soft">History</h2>
            <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-cream-200 px-1.5 text-[10px] font-semibold text-ink-faint">
              {history.length}
            </span>
          </div>
          <div className="flex flex-col gap-2.5 opacity-75">
            {history.map((opp) => (
              <OpportunityCard key={opp.opportunity_id} opportunity={opp} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
