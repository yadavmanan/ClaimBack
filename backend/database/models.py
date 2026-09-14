"""ClaimBack single-table data models.

The production store is DynamoDB, but these models are intentionally plain
Pydantic objects so tests and local workflows can run against the in-memory
repository with the same item shape.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OpportunityStatus(str, Enum):
    DETECTED = "DETECTED"
    VERIFYING = "VERIFYING"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    FOLLOWUP_PENDING = "FOLLOWUP_PENDING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    FAILED = "FAILED"

class VaultDocument(BaseModel):
    user_id: str
    doc_id: str
    doc_type: str
    title: str
    source_type: str
    vendor_or_issuer: str
    s3_uri: str
    uploaded_at: str
    normalized_facts: Dict[str, Any] = Field(default_factory=dict)
    raw_ocr_text: str = ""
    confidence_score: float = 0.0

    @property
    def extracted_text(self) -> str:
        return self.raw_ocr_text

    @property
    def structured_data(self) -> Dict[str, Any]:
        return self.normalized_facts

    @property
    def pk(self) -> str:
        return f"USER#{self.user_id}"

    @property
    def sk(self) -> str:
        return f"DOC#{self.doc_id}"

class CoverageRecord(BaseModel):
    coverage_id: str
    user_id: str
    source_doc_id: str
    coverage_type: str
    provider_name: str
    covered_subjects: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    deductible: float = 0.0
    coverage_limit: Optional[float] = None
    claim_channel: str = "MANUAL"
    terms_summary: str = ""
    machine_rules: Dict[str, Any] = Field(default_factory=dict)
    status: str = "ACTIVE"

    @property
    def pk(self) -> str:
        return f"USER#{self.user_id}"

    @property
    def sk(self) -> str:
        return f"COVERAGE#{self.coverage_id}"

class LedgerEntry(BaseModel):
    transaction_id: str
    user_id: str
    merchant_name: str
    amount: float
    currency: str = "USD"
    category: str = "UNCATEGORIZED"
    transaction_timestamp: str
    source: str = "UNKNOWN"
    billing_period: Optional[str] = None
    raw_description: str = ""

    @property
    def pk(self) -> str:
        return f"USER#{self.user_id}"

    @property
    def sk(self) -> str:
        return f"LEDGER#{self.transaction_id}"

class ClaimOpportunity(BaseModel):
    user_id: str
    opportunity_id: str
    opportunity_type: str
    title: str
    description: str
    status: OpportunityStatus = OpportunityStatus.DETECTED
    confidence_score: float
    impact_amount: float = 0.0
    potential_savings: float = 0.0
    reason_summary: str = ""
    supporting_doc_ids: List[str] = Field(default_factory=list)
    supporting_coverage_ids: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    draft_action_ids: List[str] = Field(default_factory=list)
    submission_job_id: Optional[str] = None
    detected_at: str
    last_updated_at: str
    audit_trail: List[str] = Field(default_factory=list)

    @property
    def claim_type(self) -> str:
        return self.opportunity_type.lower()

    @property
    def estimated_value(self) -> float:
        return self.impact_amount

    @property
    def pk(self) -> str:
        return f"USER#{self.user_id}"

    @property
    def sk(self) -> str:
        return f"OPPORTUNITY#{self.opportunity_id}"

class EvidenceRequirement(BaseModel):
    requirement_id: str
    opportunity_id: str
    requirement_type: str
    description: str
    status: str = "MISSING"
    satisfied_by_doc_id: Optional[str] = None
    user_action_needed: Optional[str] = None

    @property
    def pk(self) -> str:
        return f"OPPORTUNITY#{self.opportunity_id}"

    @property
    def sk(self) -> str:
        return f"REQUIREMENT#{self.requirement_id}"

class ActionDraft(BaseModel):
    draft_id: str
    opportunity_id: str
    draft_type: str
    channel: str
    recipient: str
    subject: str
    body: str
    attachment_doc_ids: List[str] = Field(default_factory=list)
    structured_form_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: str

    @property
    def pk(self) -> str:
        return f"OPPORTUNITY#{self.opportunity_id}"

    @property
    def sk(self) -> str:
        return f"DRAFT#{self.draft_id}"

class SubmissionJob(BaseModel):
    submission_job_id: str
    opportunity_id: str
    submission_channel: str
    status: str = "PENDING"
    submitted_at: Optional[str] = None
    external_reference_id: Optional[str] = None
    delivery_receipt: Optional[str] = None
    failure_reason: Optional[str] = None
    next_followup_at: Optional[str] = None
    attempt_count: int = 0

    @property
    def pk(self) -> str:
        return f"OPPORTUNITY#{self.opportunity_id}"

    @property
    def sk(self) -> str:
        return f"SUBMISSION#{self.submission_job_id}"

class FollowUpTask(BaseModel):
    followup_task_id: str
    opportunity_id: str
    task_type: str
    due_at: str
    status: str = "PENDING"
    instructions: str
    channel: str

    @property
    def pk(self) -> str:
        return f"OPPORTUNITY#{self.opportunity_id}"

    @property
    def sk(self) -> str:
        return f"FOLLOWUP#{self.followup_task_id}"

class UserApproval(BaseModel):
    approval_id: str
    opportunity_id: str
    user_id: str
    decision: str
    decided_at: str
    approved_draft_ids: List[str] = Field(default_factory=list)
    approval_scope: str = "SUBMISSION"

    @property
    def pk(self) -> str:
        return f"OPPORTUNITY#{self.opportunity_id}"

    @property
    def sk(self) -> str:
        return f"APPROVAL#{self.approval_id}"
