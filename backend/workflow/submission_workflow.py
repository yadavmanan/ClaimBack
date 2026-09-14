"""Outbound claim submission workflow."""

from datetime import datetime, timezone

from backend.database.models import OpportunityStatus
from backend.database.repositories import SingleTableRepository
from backend.observability import log_workflow_step, logger
from backend.services.submission_service import SubmissionService
from backend.services.tracking_service import TrackingService

class SubmissionWorkflow:
    def __init__(self, repository: SingleTableRepository):
        self.repo = repository
        self.submission_service = SubmissionService()
        self.tracking_service = TrackingService()

    @log_workflow_step("execute_claim_submission")
    def submit(self, opportunity_id: str, draft_payload: dict | None = None) -> dict:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if opportunity is None:
            raise ValueError(f"Opportunity {opportunity_id} was not found")
        if opportunity.status != OpportunityStatus.APPROVED:
            raise ValueError("Opportunity must be approved before submission")
        approvals = self.repo.list_approvals(opportunity_id)
        if not any(approval.decision == "APPROVED" for approval in approvals):
            raise ValueError("Explicit approval is required before submission")
        requirements = self.repo.list_requirements(opportunity_id)
        missing = [requirement for requirement in requirements if requirement.status != "SATISFIED"]
        if missing:
            raise ValueError("Evidence is incomplete")
        drafts = self.repo.list_drafts(opportunity_id)
        if not drafts:
            raise ValueError("No draft is available for submission")
        opportunity.status = OpportunityStatus.SUBMITTING
        opportunity.last_updated_at = datetime.now(timezone.utc).isoformat()
        self.repo.save_opportunity(opportunity)
        draft = drafts[0]
        submission_job = self.submission_service.create_submission_job(opportunity, draft)
        try:
            execution_result = self.submission_service.execute_submission(opportunity, draft)
        except Exception as exc:
            submission_job.status = "FAILED"
            submission_job.failure_reason = str(exc)
            submission_job.attempt_count += 1
            opportunity.status = OpportunityStatus.FAILED
            opportunity.last_updated_at = datetime.now(timezone.utc).isoformat()
            opportunity.audit_trail.append(f"Submission failed: {exc}")
            self.repo.save_submission_job(submission_job)
            self.repo.save_opportunity(opportunity)
            raise
        submission_job.status = "SUBMITTED"
        submission_job.submitted_at = datetime.now(timezone.utc).isoformat()
        submission_job.external_reference_id = execution_result.get("external_reference_id")
        submission_job.delivery_receipt = execution_result.get("delivery_receipt")
        submission_job.attempt_count += 1
        followup_task = self.tracking_service.create_followup_task(submission_job, delay_days=7)
        submission_job.next_followup_at = followup_task.due_at
        opportunity.status = OpportunityStatus.SUBMITTED
        opportunity.submission_job_id = submission_job.submission_job_id
        opportunity.last_updated_at = datetime.now(timezone.utc).isoformat()
        opportunity.audit_trail.append(f"Submitted via {submission_job.submission_channel}")
        self.repo.save_submission_job(submission_job)
        self.repo.save_followup_task(followup_task)
        self.repo.save_opportunity(opportunity)
        logger.info(f"Submitted claim {opportunity_id}, confirmation: {submission_job.external_reference_id}, follow-up: {followup_task.due_at}")
        return {
            "submission_job": submission_job,
            "followup_task": followup_task,
        }
