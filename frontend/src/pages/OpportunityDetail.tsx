import { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useClaimBackStore } from "../hooks/useClaimBackStore";
import { ProgressChecklist } from "../components/ui/ProgressChecklist";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { AgentTracePanel } from "../components/AgentTracePanel";
import { statusMeta, typeMeta } from "../components/OpportunityCard";
import { formatCurrency, formatDate } from "../lib/format";
import { ApproveIcon, ChevronRightIcon, DismissIcon, MailIcon } from "../components/icons";

export function OpportunityDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const store = useClaimBackStore();
  const opportunity = id ? store.getOpportunity(id) : undefined;
  const error = store.getError();

  useEffect(() => {
    if (id) {
      void store.loadOpportunityDetails(id);
    }
  }, [id, store]);

  if (!opportunity) {
    return (
      <div className="flex flex-col gap-4">
        <p className="text-ink-soft">{error ? `Opportunity not found: ${error}` : "Loading opportunity..."}</p>
        <Link to="/" className="text-sm font-medium text-forest hover:underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const requirements = store.getRequirements(opportunity.opportunity_id);
  const drafts = store.getDrafts(opportunity.opportunity_id);
  const traces = store.getTraces(opportunity.opportunity_id);
  const { label: typeLabel } = typeMeta[opportunity.opportunity_type];
  const { label: statusLabel, tone } = statusMeta[opportunity.status];
  const isActionable = opportunity.status === "READY_FOR_APPROVAL";

  return (
    <div className="flex flex-col gap-8">
      <Link to="/" className="inline-flex w-fit items-center gap-1 text-sm text-ink-faint hover:text-ink">
        <ChevronRightIcon width={14} height={14} className="rotate-180" />
        Back to dashboard
      </Link>

      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{typeLabel}</Badge>
            <Badge tone={tone}>{statusLabel}</Badge>
            <span className="font-mono text-xs text-ink-faint">
              {Math.round(opportunity.confidence_score * 100)}% confidence
            </span>
          </div>
          <h1 className="mt-2 font-display text-3xl font-medium text-ink">{opportunity.title}</h1>
          <p className="mt-2 max-w-xl text-ink-soft">{opportunity.description}</p>
        </div>
        <div className="text-right">
          <p className="font-mono text-3xl font-semibold text-forest">{formatCurrency(opportunity.impact_amount)}</p>
          <p className="text-xs text-ink-faint">claimable value</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        <div className="flex flex-col gap-8 lg:col-span-2">
          <section className="rounded-2xl border border-hairline bg-white/60 p-6">
            <h2 className="font-display text-lg font-medium text-ink">Why ClaimBack found this</h2>
            <p className="mt-2 text-sm text-ink-soft">{opportunity.reason_summary}</p>

            <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-ink-faint">Evidence</h3>
            <div className="mt-3">
              <ProgressChecklist requirements={requirements} />
            </div>
          </section>

          {drafts.map((draft) => (
            <section key={draft.draft_id} className="rounded-2xl border border-hairline bg-white/60 p-6">
              <div className="flex items-center gap-2 text-ink-faint">
                <MailIcon width={16} height={16} />
                <h2 className="text-xs font-semibold uppercase tracking-wide">Prepared by the Drafter agent</h2>
              </div>
              <div className="mt-3 rounded-xl bg-cream-100 p-4 font-mono text-xs text-ink-soft">
                <p>
                  <span className="text-ink-faint">To:</span> {draft.recipient}
                </p>
                <p className="mt-1">
                  <span className="text-ink-faint">Subject:</span> {draft.subject}
                </p>
                <hr className="my-3 border-hairline" />
                <p className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-ink">{draft.body}</p>
              </div>
            </section>
          ))}

          {isActionable && (
            <div className="flex items-center justify-end gap-3">
              <Button
                variant="outline-alert"
                onClick={() => {
                  store.dismissOpportunity(opportunity.opportunity_id);
                  navigate("/");
                }}
              >
                <DismissIcon width={16} height={16} /> Dismiss
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  store.approveOpportunity(opportunity.opportunity_id);
                }}
              >
                <ApproveIcon width={16} height={16} /> Approve & submit
              </Button>
            </div>
          )}
        </div>

        <aside className="lg:col-span-1">
          <div className="rounded-2xl border border-hairline bg-white/60 p-6">
            <h2 className="font-display text-lg font-medium text-ink">Agent activity</h2>
            <p className="mt-1 text-xs text-ink-faint">Live trace from the Strands multi-agent pipeline</p>
            <div className="mt-4">
              <AgentTracePanel events={traces} />
            </div>
            <p className="mt-4 text-xs text-ink-faint">
              Detected {formatDate(opportunity.detected_at)} · Updated {formatDate(opportunity.last_updated_at)}
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
