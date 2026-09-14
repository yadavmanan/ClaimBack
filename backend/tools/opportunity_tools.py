"""Strands tools for claim opportunities."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.database.models import ClaimOpportunity, OpportunityStatus
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
def create_claim_opportunity(
    user_id: str,
    opportunity_id: str,
    opportunity_type: str,
    title: str,
    description: str,
    confidence_score: float,
    impact_amount: float = 0.0,
    supporting_doc_ids: List[str] | None = None,
    supporting_coverage_ids: List[str] | None = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    opportunity = ClaimOpportunity(
        user_id=user_id,
        opportunity_id=opportunity_id,
        opportunity_type=opportunity_type,
        title=title,
        description=description,
        status=OpportunityStatus.DETECTED,
        confidence_score=confidence_score,
        impact_amount=impact_amount,
        potential_savings=impact_amount,
        supporting_doc_ids=supporting_doc_ids or [],
        supporting_coverage_ids=supporting_coverage_ids or [],
        detected_at=now,
        last_updated_at=now,
    )
    _repository.save_opportunity(opportunity)
    return _envelope(opportunity.model_dump())


@tool
def update_claim_opportunity(opportunity_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    opportunity = _repository.get_opportunity(opportunity_id)
    if opportunity is None:
        return _envelope(error="opportunity not found")
    updated = opportunity.model_copy(update={**updates, "last_updated_at": datetime.now(timezone.utc).isoformat()})
    _repository.save_opportunity(updated)
    return _envelope(updated.model_dump())


@tool
def attach_supporting_records(opportunity_id: str, doc_ids: List[str], coverage_ids: List[str]) -> Dict[str, Any]:
    opportunity = _repository.get_opportunity(opportunity_id)
    if opportunity is None:
        return _envelope(error="opportunity not found")
    opportunity.supporting_doc_ids = sorted(set(opportunity.supporting_doc_ids + doc_ids))
    opportunity.supporting_coverage_ids = sorted(set(opportunity.supporting_coverage_ids + coverage_ids))
    opportunity.last_updated_at = datetime.now(timezone.utc).isoformat()
    _repository.save_opportunity(opportunity)
    return _envelope(opportunity.model_dump())


@tool
def list_open_opportunities(user_id: str) -> Dict[str, Any]:
    closed = {OpportunityStatus.RESOLVED, OpportunityStatus.DISMISSED, OpportunityStatus.FAILED}
    opportunities = [opp for opp in _repository.list_opportunities(user_id) if opp.status not in closed]
    return _envelope([opp.model_dump() for opp in opportunities])


@tool
def get_opportunity_by_id(opportunity_id: str) -> Dict[str, Any]:
    opportunity = _repository.get_opportunity(opportunity_id)
    return _envelope(opportunity.model_dump() if opportunity else None, None if opportunity else "opportunity not found")

@tool
def save_claim_opportunity(user_id: str, claim_type: str, estimated_value: float, confidence_score: float) -> Dict[str, Any]:
    """Create or update a claim opportunity in the database."""
    opportunity_id = f"opp_{len(_repository.list_opportunities(user_id)) + 1}"
    return create_claim_opportunity(
        user_id=user_id,
        opportunity_id=opportunity_id,
        opportunity_type=claim_type.upper(),
        title=claim_type.replace("_", " ").title(),
        description="Agent-created claim opportunity.",
        confidence_score=confidence_score,
        impact_amount=estimated_value,
    )
