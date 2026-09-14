"""Follow-up sweep workflow."""

from datetime import datetime, timezone

from backend.database.models import OpportunityStatus
from backend.database.repositories import SingleTableRepository
from backend.observability import log_workflow_step, logger

class FollowUpWorkflow:
    def __init__(self, repository: SingleTableRepository):
        self.repo = repository

    @log_workflow_step("run_followup_sweep")
    def run_sweep(self) -> int:
        logger.info("Executing periodic follow-up sweep across active claims...")
        now = datetime.now(timezone.utc).isoformat()
        updated = 0
        for task in self.repo.list_due_followup_tasks(as_of=now):
            opportunity = self.repo.get_opportunity(task.opportunity_id)
            if opportunity is None:
                continue
            task.status = "DUE"
            opportunity.status = OpportunityStatus.FOLLOWUP_PENDING
            opportunity.last_updated_at = datetime.now(timezone.utc).isoformat()
            opportunity.audit_trail.append("Follow-up task is due")
            self.repo.save_followup_task(task)
            self.repo.save_opportunity(opportunity)
            updated += 1
        return updated
