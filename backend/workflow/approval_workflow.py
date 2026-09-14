"""Human approval gate workflow."""

from datetime import datetime, timezone
import uuid

from backend.database.models import OpportunityStatus, UserApproval
from backend.database.repositories import SingleTableRepository
from backend.observability import log_workflow_step, logger

class ApprovalWorkflow:
    def __init__(self, repository: SingleTableRepository):
        self.repo = repository

    @log_workflow_step("process_user_decision")
    def process_decision(self, user_id: str, opportunity_id: str, decision: str) -> UserApproval:
        normalized_decision = decision.upper()
        if normalized_decision == "APPROVE":
            normalized_decision = "APPROVED"
        if normalized_decision not in {"APPROVED", "DISMISSED", "REJECTED"}:
            raise ValueError("decision must be APPROVE, APPROVED, DISMISSED, or REJECTED")
        opportunity = self.repo.get_opportunity(opportunity_id)
        if opportunity is None:
            raise ValueError(f"Opportunity {opportunity_id} was not found")
        if opportunity.user_id != user_id:
            raise ValueError("Approval user does not own this opportunity")
        if normalized_decision == "APPROVED" and opportunity.status != OpportunityStatus.READY_FOR_APPROVAL:
            raise ValueError("Opportunity is not ready for approval")
        approval_id = f"app_{uuid.uuid4().hex[:8]}"
        approval = UserApproval(
            approval_id=approval_id,
            opportunity_id=opportunity_id,
            user_id=user_id,
            decided_at=datetime.now(timezone.utc).isoformat(),
            decision=normalized_decision,
            approved_draft_ids=opportunity.draft_action_ids if normalized_decision == "APPROVED" else [],
            approval_scope="SUBMISSION",
        )
        opportunity.status = OpportunityStatus.APPROVED if normalized_decision == "APPROVED" else OpportunityStatus.DISMISSED
        opportunity.last_updated_at = datetime.now(timezone.utc).isoformat()
        opportunity.audit_trail.append(f"User decision recorded: {normalized_decision}")
        self.repo.save_approval(approval)
        self.repo.save_opportunity(opportunity)
        logger.info(f"Opportunity {opportunity_id} transition to {opportunity.status} by user decision")
        return approval
