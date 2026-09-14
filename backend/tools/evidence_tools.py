"""Strands tools for evidence management."""

from typing import Any, Dict, List, Optional

from backend.database.models import EvidenceRequirement
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
def list_required_evidence_templates(opportunity_type: str) -> Dict[str, Any]:
    templates = {
        "UNCLAIMED_WARRANTY": ["purchase_receipt", "warranty_document", "repair_invoice", "model_number", "serial_number"],
        "DUPLICATE_CHARGE": ["matching_transactions", "time_proximity", "merchant_similarity"],
        "BILL_PRICE_HIKE": ["previous_charge", "new_charge", "price_change_notice"],
    }
    return _envelope(templates.get(opportunity_type.upper(), []))


@tool
def create_evidence_requirement(opportunity_id: str, requirement_type: str, description: str, user_action_needed: str = "") -> Dict[str, Any]:
    requirement = EvidenceRequirement(
        requirement_id=f"req_{opportunity_id}_{requirement_type}",
        opportunity_id=opportunity_id,
        requirement_type=requirement_type,
        description=description,
        status="MISSING",
        user_action_needed=user_action_needed or description,
    )
    _repository.save_requirement(requirement)
    return _envelope(requirement.model_dump())


@tool
def resolve_evidence_requirement(opportunity_id: str, requirement_id: str, doc_id: str) -> Dict[str, Any]:
    requirement = next((req for req in _repository.list_requirements(opportunity_id) if req.requirement_id == requirement_id), None)
    if requirement is None:
        return _envelope(error="requirement not found")
    requirement.status = "SATISFIED"
    requirement.satisfied_by_doc_id = doc_id
    requirement.user_action_needed = None
    _repository.save_requirement(requirement)
    return _envelope(requirement.model_dump())


@tool
def search_evidence_matches(user_id: str, requirement_type: str) -> Dict[str, Any]:
    matching_docs = [doc for doc in _repository.list_documents(user_id) if requirement_type.lower() in doc.doc_type.lower()]
    return _envelope([doc.model_dump() for doc in matching_docs])

@tool
def check_evidence_completeness(opportunity_id: str, required_types: List[str]) -> Dict[str, Any]:
    """Check missing evidence items for an opportunity."""
    requirements = _repository.list_requirements(opportunity_id)
    satisfied = {req.requirement_type for req in requirements if req.status == "SATISFIED"}
    missing = [requirement_type for requirement_type in required_types if requirement_type not in satisfied]
    return _envelope({"opportunity_id": opportunity_id, "missing_items": missing, "is_complete": not missing})
