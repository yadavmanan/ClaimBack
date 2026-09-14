"""Evidence completeness service."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from backend.database.models import EvidenceRequirement, VaultDocument


class EvidencePlan(BaseModel):
    requirements: List[EvidenceRequirement] = Field(default_factory=list)
    satisfied_doc_ids: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return not self.missing_requirements

class EvidenceService:
    def verify_requirements(self, user_id: str, required_types: List[str], user_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        existing_types = {doc.get("doc_type") for doc in user_docs}
        missing = [req for req in required_types if req not in existing_types]
        return {
            "is_complete": len(missing) == 0,
            "missing_requirements": missing
        }

    def build_warranty_plan(self, opportunity_id: str, documents: List[VaultDocument]) -> EvidencePlan:
        templates = {
            "purchase_receipt": "Purchase receipt",
            "warranty_document": "Warranty or registration proof",
            "repair_invoice": "Repair invoice",
            "model_number": "Model number",
            "serial_number": "Serial number",
        }
        receipt = self._find_document(documents, "RECEIPT")
        warranty = self._find_document(documents, "WARRANTY")
        invoice = self._find_document(documents, "REPAIR_INVOICE")
        evidence_map = {
            "purchase_receipt": receipt.doc_id if receipt else None,
            "warranty_document": warranty.doc_id if warranty else None,
            "repair_invoice": invoice.doc_id if invoice else None,
            "model_number": self._doc_with_fact(documents, "model_number"),
            "serial_number": self._doc_with_fact(documents, "serial_number"),
        }
        requirements: List[EvidenceRequirement] = []
        missing: List[str] = []
        satisfied_doc_ids: List[str] = []
        for requirement_type, description in templates.items():
            doc_id = evidence_map[requirement_type]
            status = "SATISFIED" if doc_id else "MISSING"
            if doc_id:
                satisfied_doc_ids.append(doc_id)
            else:
                missing.append(requirement_type)
            requirements.append(EvidenceRequirement(
                requirement_id=f"req_{opportunity_id}_{requirement_type}",
                opportunity_id=opportunity_id,
                requirement_type=requirement_type,
                description=description,
                status=status,
                satisfied_by_doc_id=doc_id,
                user_action_needed=None if doc_id else f"Upload {description.lower()}.",
            ))
        return EvidencePlan(
            requirements=requirements,
            satisfied_doc_ids=sorted(set(satisfied_doc_ids)),
            missing_requirements=missing,
        )

    def _find_document(self, documents: List[VaultDocument], doc_type: str) -> VaultDocument | None:
        return next((doc for doc in documents if doc.doc_type == doc_type), None)

    def _doc_with_fact(self, documents: List[VaultDocument], fact_name: str) -> str | None:
        match = next((doc for doc in documents if doc.normalized_facts.get(fact_name)), None)
        return match.doc_id if match else None
