// Mirrors backend/database/models.py Pydantic models — keep field names in sync.

export type OpportunityStatus =
  | "DETECTED"
  | "VERIFYING"
  | "NEEDS_EVIDENCE"
  | "READY_FOR_APPROVAL"
  | "APPROVED"
  | "SUBMITTING"
  | "SUBMITTED"
  | "FOLLOWUP_PENDING"
  | "RESOLVED"
  | "DISMISSED"
  | "FAILED";

export type OpportunityType =
  | "UNCLAIMED_WARRANTY"
  | "OFFICE_REIMBURSEMENT"
  | "BILL_PRICE_HIKE"
  | "DUPLICATE_CHARGE";

export interface VaultDocument {
  user_id: string;
  doc_id: string;
  doc_type: "RECEIPT" | "WARRANTY" | "POLICY" | "INVOICE" | string;
  title: string;
  source_type: string;
  vendor_or_issuer: string;
  s3_uri: string;
  uploaded_at: string;
  normalized_facts: Record<string, unknown>;
  raw_ocr_text?: string;
  confidence_score: number;
  preview_url?: string;
  file_name?: string;
}

export interface CoverageRecord {
  coverage_id: string;
  user_id: string;
  source_doc_id: string;
  coverage_type: string;
  provider_name: string;
  covered_subjects: string[];
  start_date?: string | null;
  end_date?: string | null;
  deductible: number;
  coverage_limit?: number | null;
  claim_channel: string;
  terms_summary: string;
  status: string;
}

export interface EvidenceRequirement {
  requirement_id: string;
  opportunity_id: string;
  requirement_type: string;
  description: string;
  status: "SATISFIED" | "MISSING";
  satisfied_by_doc_id?: string | null;
  user_action_needed?: string | null;
}

export interface ActionDraft {
  draft_id: string;
  opportunity_id: string;
  draft_type: string;
  channel: string;
  recipient: string;
  subject: string;
  body: string;
  attachment_doc_ids: string[];
  created_at: string;
}

export interface ClaimOpportunity {
  user_id: string;
  opportunity_id: string;
  opportunity_type: OpportunityType;
  title: string;
  description: string;
  status: OpportunityStatus;
  confidence_score: number;
  impact_amount: number;
  potential_savings: number;
  reason_summary: string;
  supporting_doc_ids: string[];
  supporting_coverage_ids: string[];
  missing_requirements: string[];
  draft_action_ids: string[];
  submission_job_id?: string | null;
  detected_at: string;
  last_updated_at: string;
  audit_trail: string[];
}

/** Not a backend model — drives the live Strands agent trace panel in the UI. */
export interface AgentTraceEvent {
  id: string;
  opportunity_id: string;
  agent: "Parser" | "Matcher" | "EvidencePlanner" | "Drafter" | "HumanGate" | "Auditor";
  summary: string;
  detail: string;
  timestamp: string;
  raw: Record<string, unknown>;
}

/** Not a backend model — drives the global Activity page timeline. */
export interface ActivityEntry {
  id: string;
  opportunity_id: string;
  label: string;
  timestamp: string;
}
