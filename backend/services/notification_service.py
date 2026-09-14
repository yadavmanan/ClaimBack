"""Exception notification service."""

from typing import Any, Dict, List

from backend.database.models import ClaimOpportunity

class NotificationService:
    def format_missing_evidence_card(self, opportunity_id: str, missing_items: List[str]) -> Dict[str, Any]:
        items_str = ", ".join(missing_items)
        return {
            "title": "Additional Document Needed",
            "message": f"To proceed with your claim ({opportunity_id}), please upload: {items_str}.",
            "action_required": "UPLOAD_DOCUMENT"
        }

    def format_approval_card(self, opportunity: ClaimOpportunity) -> Dict[str, Any]:
        return {
            "title": opportunity.title,
            "impact_amount": opportunity.impact_amount,
            "confidence_score": opportunity.confidence_score,
            "verified": opportunity.supporting_doc_ids,
            "missing": opportunity.missing_requirements,
            "next_action": "APPROVE" if not opportunity.missing_requirements else "UPLOAD_EVIDENCE",
        }
