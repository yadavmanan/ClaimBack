"""Strands tools for outbound submissions."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from backend.database.models import FollowUpTask, SubmissionJob
from backend.database.repositories import SingleTableRepository

try:
    from strands import tool
except ImportError:
    def tool(func):
        return func

_repository = SingleTableRepository()


def configure_repository(repository: SingleTableRepository) -> None:
    global _repository
    _repository = repository


def _envelope(data: Any = None, error: Optional[str] = None) -> Dict[str, Any]:
    return {"status": "ERROR" if error else "SUCCESS", "data": data, "error": error}

@tool
def create_submission_job(opportunity_id: str, recipient: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Queue an outbound submission job."""
    job = SubmissionJob(
        submission_job_id=f"sub_{opportunity_id}",
        opportunity_id=opportunity_id,
        submission_channel=payload.get("channel", "EMAIL"),
        status="PENDING",
        external_reference_id=recipient,
    )
    _repository.save_submission_job(job)
    return _envelope(job.model_dump())


@tool
def mark_submission_submitted(opportunity_id: str, submission_job_id: str, external_reference_id: str) -> Dict[str, Any]:
    job = next((item for item in _repository.list_submission_jobs(opportunity_id) if item.submission_job_id == submission_job_id), None)
    if job is None:
        return _envelope(error="submission job not found")
    job.status = "SUBMITTED"
    job.submitted_at = datetime.now(timezone.utc).isoformat()
    job.external_reference_id = external_reference_id
    job.attempt_count += 1
    _repository.save_submission_job(job)
    return _envelope(job.model_dump())


@tool
def mark_submission_failed(opportunity_id: str, submission_job_id: str, failure_reason: str) -> Dict[str, Any]:
    job = next((item for item in _repository.list_submission_jobs(opportunity_id) if item.submission_job_id == submission_job_id), None)
    if job is None:
        return _envelope(error="submission job not found")
    job.status = "FAILED"
    job.failure_reason = failure_reason
    _repository.save_submission_job(job)
    return _envelope(job.model_dump())


@tool
def schedule_followup_task(opportunity_id: str, submission_job_id: str, days_until_due: int = 7) -> Dict[str, Any]:
    task = FollowUpTask(
        followup_task_id=f"followup_{submission_job_id}",
        opportunity_id=opportunity_id,
        task_type="PROVIDER_ACK_CHECK",
        due_at=(datetime.now(timezone.utc) + timedelta(days=days_until_due)).isoformat(),
        status="PENDING",
        instructions="Check provider response status.",
        channel="INTERNAL",
    )
    _repository.save_followup_task(task)
    return _envelope(task.model_dump())


@tool
def record_provider_response(opportunity_id: str, submission_job_id: str, response_status: str, response_body: str) -> Dict[str, Any]:
    job = next((item for item in _repository.list_submission_jobs(opportunity_id) if item.submission_job_id == submission_job_id), None)
    if job is None:
        return _envelope(error="submission job not found")
    job.delivery_receipt = response_body
    job.status = response_status.upper()
    _repository.save_submission_job(job)
    return _envelope(job.model_dump())
