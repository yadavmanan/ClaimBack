"""Typed workflow events exchanged by ClaimBack orchestrators."""

from typing import List, Optional

from pydantic import BaseModel

class DocumentUploadedEvent(BaseModel):
    event_type: str = "DOCUMENT_UPLOADED"
    user_id: str
    doc_id: str
    doc_type_hint: str
    s3_uri: str
    uploaded_at: str
    source: str
    raw_text: Optional[str] = None

class OpportunityEvaluatedEvent(BaseModel):
    event_type: str = "OPPORTUNITY_DETECTED"
    user_id: str
    opportunity_id: str
    opportunity_type: str
    impact_amount: float
    confidence_score: float
    supporting_doc_ids: List[str]
    missing_requirements: List[str]

class ActionApprovedEvent(BaseModel):
    event_type: str = "ACTION_APPROVED"
    user_id: str
    opportunity_id: str
    decision: str
