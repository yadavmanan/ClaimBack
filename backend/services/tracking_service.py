"""Tracking and follow-up scheduling service."""

from datetime import datetime, timedelta, timezone

from backend.database.models import FollowUpTask, SubmissionJob

class TrackingService:
    def schedule_followup(self, opportunity_id: str, delay_days: int = 14) -> dict:
        scheduled_date = (datetime.now(timezone.utc) + timedelta(days=delay_days)).strftime("%Y-%m-%d")
        return {
            "task_id": f"task_{opportunity_id}",
            "scheduled_for": scheduled_date,
            "status": "SCHEDULED"
        }

    def create_followup_task(self, submission_job: SubmissionJob, delay_days: int = 7) -> FollowUpTask:
        due_at = (datetime.now(timezone.utc) + timedelta(days=delay_days)).isoformat()
        return FollowUpTask(
            followup_task_id=f"followup_{submission_job.opportunity_id}",
            opportunity_id=submission_job.opportunity_id,
            task_type="PROVIDER_ACK_CHECK",
            due_at=due_at,
            status="PENDING",
            instructions="Check whether the provider acknowledged or responded to the submitted claim.",
            channel="INTERNAL",
        )
