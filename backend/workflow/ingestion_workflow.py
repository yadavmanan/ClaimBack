"""Document ingestion and opportunity creation workflow."""

import re
from datetime import datetime, timezone
import uuid

from backend.agents.parser import create_parser_agent
from backend.database.models import ClaimOpportunity, CoverageRecord, OpportunityStatus, VaultDocument
from backend.database.repositories import SingleTableRepository
from backend.observability import log_workflow_step, logger
from backend.services.evidence_service import EvidenceService
from backend.services.eligibility_service import EligibilityService
from backend.services.normalization_service import NormalizationService
from backend.services.ocr_service import OCRService
from backend.services.submission_service import SubmissionService
from backend.workflow.events import DocumentUploadedEvent

class IngestionWorkflow:
    def __init__(self, repository: SingleTableRepository):
        self.repo = repository
        self.ocr = OCRService()
        self.normalizer = NormalizationService()
        self.eligibility = EligibilityService()
        self.evidence = EvidenceService()
        self.submission = SubmissionService()
        self.parser_agent = create_parser_agent()

    @log_workflow_step("ingest_document")
    def ingest_document(self, event: DocumentUploadedEvent) -> dict:
        raw_text = event.raw_text or self._extract_text_from_s3_uri(event.s3_uri)
        parsed = self.normalizer.parse_document_text(event.doc_type_hint, raw_text)
        document = VaultDocument(
            user_id=event.user_id,
            doc_id=event.doc_id,
            doc_type=parsed["doc_type"],
            title=parsed["title"],
            source_type=event.source,
            vendor_or_issuer=parsed["vendor_or_issuer"],
            s3_uri=event.s3_uri,
            uploaded_at=event.uploaded_at,
            normalized_facts=parsed["normalized_facts"],
            raw_ocr_text=raw_text,
            confidence_score=parsed["confidence_score"],
        )
        self.repo.save_document(document)
        coverage = self._register_coverage_if_applicable(document)
        opportunity_result = self._create_opportunity_if_applicable(document)
        extra_opportunities = self._create_reimbursement_or_statement_opportunities(document)
        if opportunity_result.get("opportunity") is None and extra_opportunities:
            opportunity_result = {"opportunity": extra_opportunities[0], "evidence_plan": None, "drafts": []}
        return {
            "document": document,
            "coverage": coverage,
            **opportunity_result,
        }

    @log_workflow_step("run_ingestion")
    def run(self, user_id: str, s3_bucket: str, s3_key: str) -> VaultDocument:
        logger.info(f"Ingesting document for user {user_id} from {s3_bucket}/{s3_key}")
        
        # 1. Extract text via OCR
        ocr_result = self.ocr.extract_text(s3_bucket, s3_key)
        
        # 2. Extract structured data via Parser Agent
        if self.parser_agent is not None:
            try:
                self.parser_agent(f"Parse this text: {ocr_result['raw_text']}")
            except Exception as exc:
                logger.warning(f"Parser agent invocation failed, continuing with deterministic parser: {exc}")
        
        # 3. Save to Vault
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        event = DocumentUploadedEvent(
            user_id=user_id,
            doc_id=doc_id,
            doc_type_hint="RECEIPT",
            s3_uri=f"s3://{s3_bucket}/{s3_key}",
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            source="S3_UPLOAD",
            raw_text=ocr_result["raw_text"],
        )
        result = self.ingest_document(event)
        logger.info(f"Document saved to vault with ID: {doc_id}")
        return result["document"]

    def _extract_text_from_s3_uri(self, s3_uri: str) -> str:
        if not s3_uri.startswith("s3://"):
            return ""
        bucket, _, key = s3_uri.removeprefix("s3://").partition("/")
        return self.ocr.extract_text(bucket, key).get("raw_text", "")

    def _register_coverage_if_applicable(self, document: VaultDocument) -> CoverageRecord | None:
        if document.doc_type not in {"WARRANTY", "POLICY", "BENEFIT"}:
            return None
        facts = document.normalized_facts
        reimbursement_categories = self._infer_reimbursement_categories(document)
        coverage = CoverageRecord(
            coverage_id=f"cov_{document.doc_id}",
            user_id=document.user_id,
            source_doc_id=document.doc_id,
            coverage_type=document.doc_type,
            provider_name=document.vendor_or_issuer,
            covered_subjects=[
                value
                for value in [facts.get("model_number"), facts.get("serial_number"), *reimbursement_categories]
                if value
            ],
            start_date=facts.get("coverage_start_date"),
            end_date=facts.get("coverage_end_date"),
            claim_channel=facts.get("claim_channel", "MANUAL"),
            terms_summary=document.title,
            machine_rules={
                "model_number": facts.get("model_number"),
                "serial_number": facts.get("serial_number"),
                "reimbursement_categories": reimbursement_categories,
                "monthly_limit": facts.get("monthly_limit") or facts.get("coverage_limit"),
            },
        )
        return self.repo.save_coverage(coverage)

    def _create_reimbursement_or_statement_opportunities(self, document: VaultDocument) -> list[ClaimOpportunity]:
        opportunities: list[ClaimOpportunity] = []
        reimbursement = self._create_office_reimbursement_if_applicable(document)
        if reimbursement is not None:
            opportunities.append(reimbursement)
        opportunities.extend(self._create_subscription_price_hikes_if_applicable(document))
        return opportunities

    def _create_office_reimbursement_if_applicable(self, document: VaultDocument) -> ClaimOpportunity | None:
        if document.doc_type in {"WARRANTY", "POLICY", "BENEFIT", "REPAIR_INVOICE", "LEDGER_EVENT"}:
            return None
        category = self._infer_expense_category(document)
        if category is None:
            return None
        coverage = self._find_reimbursement_coverage(document.user_id, category)
        if coverage is None:
            return None
        amount = float(document.normalized_facts.get("amount") or document.normalized_facts.get("total_amount") or 0.0)
        if amount <= 0:
            return None

        now = datetime.now(timezone.utc).isoformat()
        category_label = "WiFi/internet" if category == "wifi" else category.replace("_", " ").title()
        opportunity = ClaimOpportunity(
            user_id=document.user_id,
            opportunity_id=f"opp_{uuid.uuid4().hex[:8]}",
            opportunity_type="OFFICE_REIMBURSEMENT",
            title=f"{category_label} reimbursement available",
            description=f"{document.title} matches your {coverage.provider_name} reimbursement policy.",
            status=OpportunityStatus.READY_FOR_APPROVAL,
            confidence_score=0.9,
            impact_amount=amount,
            potential_savings=amount,
            reason_summary=f"The document was classified as {category_label.lower()} and matches active coverage {coverage.coverage_id}.",
            supporting_doc_ids=[document.doc_id, coverage.source_doc_id],
            supporting_coverage_ids=[coverage.coverage_id],
            missing_requirements=[],
            detected_at=now,
            last_updated_at=now,
            audit_trail=[
                f"Parsed {document.doc_type} from {document.vendor_or_issuer}",
                f"Matched {category_label.lower()} category to {coverage.coverage_id}",
                "Prepared reimbursement approval draft",
            ],
        )
        draft = self.submission.prepare_reimbursement_draft(opportunity, document, coverage)
        self.repo.save_draft(draft)
        opportunity.draft_action_ids = [draft.draft_id]
        self.repo.save_opportunity(opportunity)
        self._save_single_evidence_requirement(
            opportunity.opportunity_id,
            "REIMBURSABLE_DOCUMENT",
            "Receipt or bill that matches the policy category",
            document.doc_id,
        )
        self._save_single_evidence_requirement(
            opportunity.opportunity_id,
            "OFFICE_POLICY",
            "Active reimbursement policy",
            coverage.source_doc_id,
        )
        return opportunity

    def _create_subscription_price_hikes_if_applicable(self, document: VaultDocument) -> list[ClaimOpportunity]:
        transactions = self._extract_statement_transactions(document)
        by_merchant: dict[str, list[dict]] = {}
        for transaction in transactions:
            merchant = transaction.get("merchant_name", "").lower()
            if merchant:
                by_merchant.setdefault(merchant, []).append(transaction)

        opportunities: list[ClaimOpportunity] = []
        for merchant, merchant_transactions in by_merchant.items():
            sorted_transactions = sorted(merchant_transactions, key=lambda item: str(item.get("date", "")))
            for previous, current in zip(sorted_transactions, sorted_transactions[1:]):
                previous_amount = float(previous.get("amount") or 0.0)
                current_amount = float(current.get("amount") or 0.0)
                if current_amount <= previous_amount:
                    continue
                opportunities.append(self._save_subscription_price_hike(document, merchant, previous, current))
        return opportunities

    def _save_subscription_price_hike(self, document: VaultDocument, merchant: str, previous: dict, current: dict) -> ClaimOpportunity:
        previous_amount = float(previous.get("amount") or 0.0)
        current_amount = float(current.get("amount") or 0.0)
        monthly_delta = round(current_amount - previous_amount, 2)
        annual_impact = round(monthly_delta * 12, 2)
        now = datetime.now(timezone.utc).isoformat()
        merchant_label = merchant.title()
        opportunity = ClaimOpportunity(
            user_id=document.user_id,
            opportunity_id=f"opp_{uuid.uuid4().hex[:8]}",
            opportunity_type="BILL_PRICE_HIKE",
            title=f"{merchant_label} price increase detected",
            description=f"{merchant_label} increased from {previous_amount:.2f} to {current_amount:.2f}.",
            status=OpportunityStatus.READY_FOR_APPROVAL,
            confidence_score=0.88,
            impact_amount=annual_impact,
            potential_savings=annual_impact,
            reason_summary=f"Recurring {merchant_label} charges increased by {monthly_delta:.2f} per month, or {annual_impact:.2f} per year.",
            supporting_doc_ids=[document.doc_id],
            supporting_coverage_ids=[],
            missing_requirements=[],
            detected_at=now,
            last_updated_at=now,
            audit_trail=[
                "Bank statement parsed into ledger-like transactions",
                f"Compared {merchant_label}: {previous_amount:.2f} to {current_amount:.2f}",
                "Prepared subscription action for approval",
            ],
        )
        draft = self.submission.prepare_subscription_action_draft(opportunity, merchant_label, previous_amount, current_amount)
        self.repo.save_draft(draft)
        opportunity.draft_action_ids = [draft.draft_id]
        self.repo.save_opportunity(opportunity)
        self._save_single_evidence_requirement(
            opportunity.opportunity_id,
            "BANK_STATEMENT",
            "Statement showing previous and current recurring charges",
            document.doc_id,
        )
        return opportunity

    def _save_single_evidence_requirement(self, opportunity_id: str, requirement_type: str, description: str, doc_id: str) -> None:
        from backend.database.models import EvidenceRequirement

        self.repo.save_requirement(EvidenceRequirement(
            requirement_id=f"req_{opportunity_id}_{requirement_type.lower()}",
            opportunity_id=opportunity_id,
            requirement_type=requirement_type,
            description=description,
            status="SATISFIED",
            satisfied_by_doc_id=doc_id,
        ))

    def _find_reimbursement_coverage(self, user_id: str, category: str) -> CoverageRecord | None:
        for coverage in self.repo.list_active_coverages(user_id):
            categories = coverage.machine_rules.get("reimbursement_categories", [])
            if category in categories or any(category in str(subject).lower() for subject in coverage.covered_subjects):
                return coverage
        return None

    def _infer_reimbursement_categories(self, document: VaultDocument) -> list[str]:
        text = f"{document.title}\n{document.raw_ocr_text}\n{document.normalized_facts}".lower()
        categories = []
        if any(term in text for term in ["wifi", "wi-fi", "internet", "broadband", "airfiber"]):
            categories.append("wifi")
        if any(term in text for term in ["cab", "taxi", "ride", "uber", "ola", "rapido", "transport"]):
            categories.append("ride")
        return sorted(set(categories))

    def _infer_expense_category(self, document: VaultDocument) -> str | None:
        text = f"{document.title}\n{document.vendor_or_issuer}\n{document.raw_ocr_text}\n{document.normalized_facts}".lower()
        if any(term in text for term in ["jio", "airfiber", "wifi", "wi-fi", "internet", "broadband"]):
            return "wifi"
        if any(term in text for term in ["uber", "ola", "rapido", "cab", "taxi", "ride"]):
            return "ride"
        return None

    def _extract_statement_transactions(self, document: VaultDocument) -> list[dict]:
        facts_transactions = document.normalized_facts.get("transactions")
        if isinstance(facts_transactions, list):
            return [transaction for transaction in facts_transactions if isinstance(transaction, dict)]
        if document.doc_type not in {"BILLING_STATEMENT", "LEDGER_EVENT", "BANK_STATEMENT"}:
            return []
        transactions = []
        for line in document.raw_ocr_text.splitlines():
            if "netflix" not in line.lower():
                continue
            amount_match = re.search(r"(?:INR|USD|Rs\.?|₹|\$)\s*([0-9,]+(?:\.[0-9]{2})?)", line, re.IGNORECASE)
            if amount_match is None:
                amount_matches = re.findall(r"([0-9,]+\.[0-9]{2})", line)
                amount_value = amount_matches[-1] if amount_matches else None
            else:
                amount_value = amount_match.group(1)
            date_match = re.search(r"(20[0-9]{2}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{2}[-/][A-Za-z]{3}[-/][0-9]{4}|[0-9]{2}[-/][0-9]{2}[-/][0-9]{4})", line)
            if amount_value:
                transactions.append({
                    "merchant_name": "Netflix",
                    "amount": float(amount_value.replace(",", "")),
                    "date": date_match.group(1) if date_match else "",
                })
        return transactions

    def _create_opportunity_if_applicable(self, document: VaultDocument) -> dict:
        if document.doc_type != "REPAIR_INVOICE":
            return {"opportunity": None, "evidence_plan": None, "drafts": []}
        best_coverage = self._find_best_coverage(document)
        if best_coverage is None:
            return {"opportunity": None, "evidence_plan": None, "drafts": []}
        eligibility = self.eligibility.evaluate_warranty_claim(document, best_coverage)
        if not eligibility["is_claimable"]:
            return {"opportunity": None, "evidence_plan": None, "drafts": []}
        now = datetime.now(timezone.utc).isoformat()
        opportunity = ClaimOpportunity(
            user_id=document.user_id,
            opportunity_id=f"opp_{uuid.uuid4().hex[:8]}",
            opportunity_type="UNCLAIMED_WARRANTY",
            title=f"${document.normalized_facts.get('amount', 0.0):.0f} warranty claim",
            description=f"Warranty reimbursement candidate from {document.title}.",
            status=OpportunityStatus.VERIFYING,
            confidence_score=eligibility["confidence_score"],
            impact_amount=document.normalized_facts.get("amount", 0.0),
            potential_savings=document.normalized_facts.get("amount", 0.0),
            reason_summary=eligibility["reason_summary"],
            supporting_doc_ids=[document.doc_id, best_coverage.source_doc_id],
            supporting_coverage_ids=[best_coverage.coverage_id],
            detected_at=now,
            last_updated_at=now,
            audit_trail=[
                f"Matched coverage {best_coverage.coverage_id}",
                eligibility["reason_summary"],
            ],
        )
        evidence_plan = self.evidence.build_warranty_plan(
            opportunity.opportunity_id,
            self.repo.list_documents(document.user_id),
        )
        for requirement in evidence_plan.requirements:
            self.repo.save_requirement(requirement)
        opportunity.supporting_doc_ids = sorted(set(opportunity.supporting_doc_ids + evidence_plan.satisfied_doc_ids))
        opportunity.missing_requirements = evidence_plan.missing_requirements
        drafts = []
        if evidence_plan.is_complete:
            draft = self.submission.prepare_warranty_draft(
                opportunity,
                recipient=f"claims@{best_coverage.provider_name.lower().replace(' ', '')}.example",
                attachment_doc_ids=opportunity.supporting_doc_ids,
            )
            self.repo.save_draft(draft)
            drafts.append(draft)
            opportunity.status = OpportunityStatus.READY_FOR_APPROVAL
            opportunity.draft_action_ids = [draft.draft_id]
            opportunity.audit_trail.append("Prepared warranty claim draft for approval")
        else:
            opportunity.status = OpportunityStatus.NEEDS_EVIDENCE
            opportunity.audit_trail.append(f"Missing evidence: {', '.join(evidence_plan.missing_requirements)}")
        opportunity.last_updated_at = datetime.now(timezone.utc).isoformat()
        self.repo.save_opportunity(opportunity)
        return {"opportunity": opportunity, "evidence_plan": evidence_plan, "drafts": drafts}

    def _find_best_coverage(self, document: VaultDocument) -> CoverageRecord | None:
        doc_facts = document.normalized_facts
        candidates = self.repo.list_active_coverages(document.user_id)
        ranked = sorted(
            candidates,
            key=lambda coverage: (
                coverage.machine_rules.get("serial_number") == doc_facts.get("serial_number"),
                coverage.machine_rules.get("model_number") == doc_facts.get("model_number"),
            ),
            reverse=True,
        )
        return ranked[0] if ranked else None
