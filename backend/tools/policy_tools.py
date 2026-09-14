"""Strands tools for coverage policy registration and lookup."""

from datetime import date
from typing import Any, Dict, List, Optional

from backend.database.models import CoverageRecord
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
def register_coverage_record(
    user_id: str,
    coverage_id: str,
    source_doc_id: str,
    coverage_type: str,
    provider_name: str,
    covered_subjects: List[str],
    start_date: str,
    end_date: str,
    claim_channel: str = "MANUAL",
    terms_summary: str = "",
    machine_rules: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    coverage = CoverageRecord(
        coverage_id=coverage_id,
        user_id=user_id,
        source_doc_id=source_doc_id,
        coverage_type=coverage_type,
        provider_name=provider_name,
        covered_subjects=covered_subjects,
        start_date=start_date,
        end_date=end_date,
        claim_channel=claim_channel,
        terms_summary=terms_summary,
        machine_rules=machine_rules or {},
    )
    _repository.save_coverage(coverage)
    return _envelope(coverage.model_dump())


@tool
def list_active_coverages(user_id: str) -> Dict[str, Any]:
    return _envelope([coverage.model_dump() for coverage in _repository.list_active_coverages(user_id)])


@tool
def find_candidate_coverages(user_id: str, model_number: str = "", serial_number: str = "") -> Dict[str, Any]:
    candidates = []
    for coverage in _repository.list_active_coverages(user_id):
        rules = coverage.machine_rules
        if (model_number and rules.get("model_number") == model_number) or (serial_number and rules.get("serial_number") == serial_number):
            candidates.append(coverage)
    return _envelope([coverage.model_dump() for coverage in candidates])


@tool
def get_coverage_by_id(user_id: str, coverage_id: str) -> Dict[str, Any]:
    match = next((coverage for coverage in _repository.list_active_coverages(user_id) if coverage.coverage_id == coverage_id), None)
    return _envelope(match.model_dump() if match else None, None if match else "coverage not found")


@tool
def calculate_upcoming_deadlines(user_id: str, as_of: str) -> Dict[str, Any]:
    today = date.fromisoformat(as_of)
    deadlines = []
    for coverage in _repository.list_active_coverages(user_id):
        if coverage.end_date:
            days_until = (date.fromisoformat(coverage.end_date) - today).days
            if 0 <= days_until <= 45:
                deadlines.append({"coverage_id": coverage.coverage_id, "due_at": coverage.end_date, "days_until": days_until})
    return _envelope(deadlines)

@tool
def find_matching_policies(user_id: str, merchant: str, category: str) -> Dict[str, Any]:
    """Find active coverage policies matching a merchant or category."""
    matches = [coverage for coverage in _repository.list_active_coverages(user_id) if merchant.lower() in coverage.provider_name.lower() or category.lower() in coverage.coverage_type.lower()]
    return _envelope([coverage.model_dump() for coverage in matches])
