"""Opportunity detection and evaluation workflow."""

from datetime import datetime, timezone
import uuid

from backend.database.models import ClaimOpportunity, OpportunityStatus
from backend.database.repositories import SingleTableRepository
from backend.observability import log_workflow_step, logger
from backend.services.evidence_service import EvidenceService
from backend.services.eligibility_service import EligibilityService

class OpportunityWorkflow:
    def __init__(self, repository: SingleTableRepository):
        self.repo = repository
        self.eligibility = EligibilityService()
        self.evidence = EvidenceService()

    @log_workflow_step("evaluate_opportunity")
    def evaluate(self, user_id: str, doc_data: dict, policy_data: dict) -> ClaimOpportunity:
        score = self.eligibility.calculate_score(doc_data, policy_data)
        now = datetime.now(timezone.utc).isoformat()
        opp_id = f"opp_{uuid.uuid4().hex[:8]}"
        status = OpportunityStatus.DETECTED if score >= 0.70 else OpportunityStatus.FAILED
        opp = ClaimOpportunity(
            user_id=user_id,
            opportunity_id=opp_id,
            opportunity_type="WARRANTY_REIMBURSEMENT",
            title="Warranty reimbursement candidate",
            description="Opportunity created from deterministic score evaluation.",
            status=status,
            confidence_score=score,
            impact_amount=doc_data.get("amount", 0.0),
            potential_savings=doc_data.get("amount", 0.0),
            reason_summary="Eligibility score met the configured threshold." if score >= 0.70 else "Eligibility score did not meet the configured threshold.",
            detected_at=now,
            last_updated_at=now,
        )
        self.repo.save_opportunity(opp)
        logger.info(f"Created opportunity {opp_id} with score {score} and status {status}")
        return opp
