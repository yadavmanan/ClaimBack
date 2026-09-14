import { Link } from "react-router-dom";
import type { ClaimOpportunity } from "../types/models";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { formatCurrency } from "../lib/format";
import { ApproveIcon, ChevronRightIcon, DismissIcon, DuplicateIcon, ShieldIcon, SubscriptionIcon } from "./icons";
import { useClaimBackStore } from "../hooks/useClaimBackStore";

const typeMeta: Record<ClaimOpportunity["opportunity_type"], { label: string; icon: typeof ShieldIcon }> = {
  UNCLAIMED_WARRANTY: { label: "Warranty", icon: ShieldIcon },
  OFFICE_REIMBURSEMENT: { label: "Reimbursement", icon: ShieldIcon },
  BILL_PRICE_HIKE: { label: "Subscription", icon: SubscriptionIcon },
  DUPLICATE_CHARGE: { label: "Duplicate charge", icon: DuplicateIcon },
};

const statusMeta: Record<ClaimOpportunity["status"], { label: string; tone: "neutral" | "forest" | "alert" }> = {
  DETECTED: { label: "Detected", tone: "neutral" },
  VERIFYING: { label: "Verifying", tone: "neutral" },
  NEEDS_EVIDENCE: { label: "Needs one input", tone: "alert" },
  READY_FOR_APPROVAL: { label: "Ready for approval", tone: "forest" },
  APPROVED: { label: "Approved", tone: "forest" },
  SUBMITTING: { label: "Submitting", tone: "neutral" },
  SUBMITTED: { label: "Submitted", tone: "forest" },
  FOLLOWUP_PENDING: { label: "Follow-up pending", tone: "neutral" },
  RESOLVED: { label: "Resolved", tone: "forest" },
  DISMISSED: { label: "Dismissed", tone: "neutral" },
  FAILED: { label: "Failed", tone: "alert" },
};

export function OpportunityCard({ opportunity }: { opportunity: ClaimOpportunity }) {
  const store = useClaimBackStore();
  const { label: typeLabel, icon: TypeIcon } = typeMeta[opportunity.opportunity_type];
  const { label: statusLabel, tone } = statusMeta[opportunity.status];
  const isActionable = opportunity.status === "READY_FOR_APPROVAL";

  return (
    <div className="rounded-xl border border-hairline bg-white/70 p-4 transition-shadow hover:shadow-sm">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cream-100 text-ink-soft">
            <TypeIcon width={14} height={14} />
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1.5">
              <Badge>{typeLabel}</Badge>
              <Badge tone={tone}>{statusLabel}</Badge>
              <span className="font-mono text-[10px] text-ink-faint">
                {Math.round(opportunity.confidence_score * 100)}% confidence
              </span>
            </div>
            <Link to={`/opportunities/${opportunity.opportunity_id}`} className="mt-1.5 block">
              <h3 className="font-display text-base font-medium text-ink hover:underline leading-snug">
                {opportunity.title}
              </h3>
            </Link>
            <p className="mt-0.5 text-xs text-ink-soft line-clamp-2">{opportunity.description}</p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <p className="font-mono text-lg font-semibold text-forest">{formatCurrency(opportunity.impact_amount)}</p>
          <p className="text-[10px] text-ink-faint">claimable</p>
        </div>
      </div>

      {/* Footer row */}
      <div className="mt-3 flex items-center justify-between border-t border-hairline pt-3">
        <Link
          to={`/opportunities/${opportunity.opportunity_id}`}
          className="inline-flex items-center gap-1 text-xs font-medium text-ink-soft hover:text-ink"
        >
          View evidence & draft <ChevronRightIcon width={14} height={14} />
        </Link>

        {isActionable && (
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline-alert"
              className="h-7 rounded-lg px-3 text-xs"
              onClick={() => void store.dismissOpportunity(opportunity.opportunity_id)}
            >
              <DismissIcon width={12} height={12} /> Dismiss
            </Button>
            <Button
              variant="primary"
              className="h-7 rounded-lg px-3 text-xs"
              onClick={() => void store.approveOpportunity(opportunity.opportunity_id)}
            >
              <ApproveIcon width={12} height={12} /> Approve
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export { typeMeta, statusMeta };

