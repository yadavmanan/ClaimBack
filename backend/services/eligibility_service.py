"""Deterministic eligibility evaluation for claim candidates."""

from datetime import date
from typing import Any, Dict, Optional

from backend.database.models import CoverageRecord, VaultDocument

class EligibilityService:
    def calculate_score(self, doc_data: Dict[str, Any], policy_data: Dict[str, Any]) -> float:
        s_doc = 0.95 if doc_data.get("merchant") else 0.5
        s_policy = 0.90 if policy_data.get("coverage_id") else 0.4
        s_time = 0.85
        s_amount = 0.90
        
        weighted_score = (0.35 * s_doc) + (0.35 * s_policy) + (0.15 * s_time) + (0.15 * s_amount)
        return round(weighted_score, 2)

    def evaluate_warranty_claim(self, document: VaultDocument, coverage: CoverageRecord) -> Dict[str, Any]:
        doc_facts = document.normalized_facts
        rules = coverage.machine_rules
        identity_match_score = self._identity_match_score(doc_facts, rules)
        rule_validity_score = 1.0 if self._date_in_window(
            doc_facts.get("invoice_date") or doc_facts.get("purchase_date"),
            coverage.start_date,
            coverage.end_date,
        ) else 0.0
        evidence_seed_score = 0.80 if document.doc_id else 0.0
        confidence = round(
            (0.25 * document.confidence_score)
            + (0.30 * identity_match_score)
            + (0.30 * rule_validity_score)
            + (0.15 * evidence_seed_score),
            2,
        )
        return {
            "is_claimable": confidence >= 0.75 and rule_validity_score > 0,
            "confidence_score": confidence,
            "identity_match_score": identity_match_score,
            "rule_validity_score": rule_validity_score,
            "reason_summary": self._reason_summary(document, coverage, identity_match_score, rule_validity_score),
        }

    def _identity_match_score(self, doc_facts: Dict[str, Any], rules: Dict[str, Any]) -> float:
        model_matches = doc_facts.get("model_number") and doc_facts.get("model_number") == rules.get("model_number")
        serial_matches = doc_facts.get("serial_number") and doc_facts.get("serial_number") == rules.get("serial_number")
        if model_matches and serial_matches:
            return 1.0
        if model_matches or serial_matches:
            return 0.8
        return 0.2

    def _date_in_window(self, event_date: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> bool:
        if not event_date or not start_date or not end_date:
            return False
        parsed_event = date.fromisoformat(event_date)
        return date.fromisoformat(start_date) <= parsed_event <= date.fromisoformat(end_date)

    def _reason_summary(
        self,
        document: VaultDocument,
        coverage: CoverageRecord,
        identity_match_score: float,
        rule_validity_score: float,
    ) -> str:
        if identity_match_score >= 1 and rule_validity_score >= 1:
            return f"{coverage.provider_name} coverage matches the invoice model, serial number, and service date."
        return f"{coverage.provider_name} coverage partially matches {document.title}."
