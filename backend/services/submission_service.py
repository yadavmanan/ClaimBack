"""Submission package preparation and dispatch service."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.aws_clients import get_boto3_client
from backend.config import settings
from backend.database.models import ActionDraft, ClaimOpportunity, SubmissionJob


class SubmissionService:
    def __init__(self):
        self.backend = settings.submission_backend.strip().lower()
        self.ses_client = None
        if self.backend == "ses":
            self.ses_client = get_boto3_client("sesv2")

    def execute_submission(self, opportunity: ClaimOpportunity, draft: ActionDraft) -> Dict[str, Any]:
        if self.backend != "ses":
            return {
                "status": "SUCCESS",
                "external_reference_id": f"CONF-{opportunity.opportunity_id.upper()}",
                "delivery_receipt": f"Stubbed delivery to {draft.recipient}",
            }

        if not settings.ses_from_email:
            raise ValueError("SES_FROM_EMAIL must be configured when SUBMISSION_BACKEND=ses")

        destination_email = settings.submission_recipient_override or draft.recipient
        send_kwargs = {
            "FromEmailAddress": settings.ses_from_email,
            "Destination": {"ToAddresses": [destination_email]},
            "Content": {
                "Simple": {
                    "Subject": {"Data": draft.subject},
                    "Body": {"Text": {"Data": draft.body}},
                }
            },
        }
        if settings.ses_reply_to_email:
            send_kwargs["ReplyToAddresses"] = [settings.ses_reply_to_email]

        message = self.ses_client.send_email(**send_kwargs)
        return {
            "status": "SUCCESS",
            "external_reference_id": message["MessageId"],
            "delivery_receipt": f"SES delivery queued for {destination_email}",
        }

    def prepare_warranty_draft(
        self,
        opportunity: ClaimOpportunity,
        recipient: str,
        attachment_doc_ids: List[str],
    ) -> ActionDraft:
        return ActionDraft(
            draft_id=f"draft_{opportunity.opportunity_id}_email",
            opportunity_id=opportunity.opportunity_id,
            draft_type="WARRANTY_CLAIM_EMAIL",
            channel="EMAIL",
            recipient=recipient,
            subject=opportunity.title,
            body=(
                f"Please review the attached warranty reimbursement request for "
                f"{opportunity.title}. The requested reimbursement amount is "
                f"${opportunity.impact_amount:.2f}."
            ),
            attachment_doc_ids=attachment_doc_ids,
            structured_form_fields={"claim_amount": opportunity.impact_amount},
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def prepare_reimbursement_draft(self, opportunity: ClaimOpportunity, document: Any, coverage: Any) -> ActionDraft:
        return ActionDraft(
            draft_id=f"draft_{opportunity.opportunity_id}_reimbursement",
            opportunity_id=opportunity.opportunity_id,
            draft_type="OFFICE_REIMBURSEMENT_REQUEST",
            channel="SELF",
            recipient="Expense approval queue",
            subject=opportunity.title,
            body=(
                f"Submit {document.title} for reimbursement under {coverage.provider_name}. "
                f"Claim amount: {opportunity.impact_amount:.2f}."
            ),
            attachment_doc_ids=opportunity.supporting_doc_ids,
            structured_form_fields={"claim_amount": opportunity.impact_amount, "policy_id": coverage.coverage_id},
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def prepare_subscription_action_draft(
        self,
        opportunity: ClaimOpportunity,
        merchant_name: str,
        previous_amount: float,
        current_amount: float,
    ) -> ActionDraft:
        return ActionDraft(
            draft_id=f"draft_{opportunity.opportunity_id}_subscription",
            opportunity_id=opportunity.opportunity_id,
            draft_type="SUBSCRIPTION_PRICE_REVIEW",
            channel="SELF",
            recipient="You",
            subject=opportunity.title,
            body=(
                f"Review {merchant_name}: recurring charge changed from {previous_amount:.2f} to "
                f"{current_amount:.2f}. Approving this marks the savings action for follow-up."
            ),
            attachment_doc_ids=opportunity.supporting_doc_ids,
            structured_form_fields={
                "previous_amount": previous_amount,
                "current_amount": current_amount,
                "annual_impact": opportunity.impact_amount,
            },
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def create_submission_job(self, opportunity: ClaimOpportunity, draft: ActionDraft) -> SubmissionJob:
        return SubmissionJob(
            submission_job_id=f"sub_{opportunity.opportunity_id}",
            opportunity_id=opportunity.opportunity_id,
            submission_channel=draft.channel,
            status="PENDING",
            attempt_count=0,
        )
