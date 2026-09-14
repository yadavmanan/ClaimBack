"""Strands tools for ledger and transaction monitoring."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from backend.database.models import LedgerEntry
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
def query_transactions(user_id: str, merchant: str, days: int = 90) -> Dict[str, Any]:
    """Query recent transactions for a user."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    transactions = [
        tx for tx in _repository.list_ledger_entries(user_id)
        if merchant.lower() in tx.merchant_name.lower() and datetime.fromisoformat(tx.transaction_timestamp) >= cutoff
    ]
    return _envelope([tx.model_dump() for tx in transactions])

@tool
def search_ledger_transactions(user_id: str, merchant: str) -> Dict[str, Any]:
    """Search ledger transactions for a specific user and merchant."""
    return _envelope({"transactions": query_transactions(user_id, merchant, days=365)["data"]})

@tool
def detect_price_change_candidates(user_id: str, merchant: str) -> Dict[str, Any]:
    """Detect recurring price changes or increase candidates in ledger history."""
    entries = sorted(
        [tx for tx in _repository.list_ledger_entries(user_id) if merchant.lower() in tx.merchant_name.lower()],
        key=lambda tx: tx.transaction_timestamp,
    )
    changes = []
    for previous, current in zip(entries, entries[1:]):
        if current.amount > previous.amount:
            changes.append({
                "merchant_name": current.merchant_name,
                "previous_amount": previous.amount,
                "new_amount": current.amount,
                "monthly_delta": round(current.amount - previous.amount, 2),
                "annual_impact": round((current.amount - previous.amount) * 12, 2),
                "transaction_ids": [previous.transaction_id, current.transaction_id],
            })
    return _envelope({"price_changes": changes})

@tool
def record_ledger_event(user_id: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Record an audited ledger event or adjustment."""
    transaction_id = details.get("transaction_id", f"tx_{len(_repository.list_ledger_entries(user_id)) + 1}")
    entry = LedgerEntry(
        transaction_id=transaction_id,
        user_id=user_id,
        merchant_name=details.get("merchant_name", details.get("merchant", "Unknown")),
        amount=float(details.get("amount", 0.0)),
        currency=details.get("currency", "USD"),
        category=details.get("category", event_type),
        transaction_timestamp=details.get("transaction_timestamp", details.get("date", datetime.now(timezone.utc).isoformat())),
        source=details.get("source", "TOOL"),
        billing_period=details.get("billing_period"),
        raw_description=details.get("raw_description", ""),
    )
    _repository.save_ledger_entry(entry)
    return _envelope({"event_id": transaction_id, "status": "RECORDED"})

@tool
def detect_duplicate_candidates(user_id: str, days: int = 30) -> Dict[str, Any]:
    """Detect candidate duplicate or near-duplicate charges across accounts."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    groups: Dict[tuple[str, float], list[LedgerEntry]] = defaultdict(list)
    for tx in _repository.list_ledger_entries(user_id):
        if datetime.fromisoformat(tx.transaction_timestamp) >= cutoff:
            groups[(tx.merchant_name.lower(), tx.amount)].append(tx)
    duplicates = []
    for (_, amount), transactions in groups.items():
        if len(transactions) > 1:
            duplicates.append({
                "merchant_name": transactions[0].merchant_name,
                "amount": amount,
                "transaction_ids": [tx.transaction_id for tx in transactions],
                "confidence_score": 0.86,
            })
    return _envelope({"duplicate_candidates": duplicates})
