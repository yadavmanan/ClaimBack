"""FastAPI app for the ClaimBack backend."""

from datetime import datetime, timezone
from pathlib import Path
import re
import uuid
from typing import Any, Dict, Optional
from urllib.parse import unquote

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.aws_clients import get_boto3_client
from backend.config import settings
from backend.runtime import get_repository
from backend.workflow.approval_workflow import ApprovalWorkflow
from backend.workflow.followup_workflow import FollowUpWorkflow
from backend.workflow.ingestion_workflow import IngestionWorkflow
from backend.workflow.submission_workflow import SubmissionWorkflow
from backend.workflow.events import DocumentUploadedEvent


app = FastAPI(title="ClaimBack Backend", version="0.1.0")

cors_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DocumentIngestRequest(BaseModel):
    user_id: str
    doc_type_hint: str
    s3_uri: str = ""
    source: str = "API"
    raw_text: Optional[str] = None
    doc_id: Optional[str] = None
    uploaded_at: Optional[str] = None


class OpportunityDecisionRequest(BaseModel):
    user_id: str
    decision: str = Field(description="APPROVE, APPROVED, DISMISSED, or REJECTED")


class SubmitOpportunityRequest(BaseModel):
    draft_payload: Optional[Dict[str, Any]] = None


def _repo():
    return get_repository()


def _ingestion_workflow() -> IngestionWorkflow:
    return IngestionWorkflow(_repo())


def _approval_workflow() -> ApprovalWorkflow:
    return ApprovalWorkflow(_repo())


def _submission_workflow() -> SubmissionWorkflow:
    return SubmissionWorkflow(_repo())


def _followup_workflow() -> FollowUpWorkflow:
    return FollowUpWorkflow(_repo())


def _safe_filename(filename: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-")
    return safe_name or "upload.bin"


def _split_s3_uri(s3_uri: str) -> tuple[str, str] | None:
    if not s3_uri.startswith("s3://"):
        return None
    bucket, _, key = s3_uri.removeprefix("s3://").partition("/")
    if not bucket or not key:
        return None
    return bucket, unquote(key)


def _document_payload(document: Any) -> Dict[str, Any]:
    payload = jsonable_encoder(document)
    s3_location = _split_s3_uri(document.s3_uri)
    if s3_location is None:
        return payload

    bucket, key = s3_location
    payload["file_name"] = Path(key).name
    try:
        payload["preview_url"] = get_boto3_client("s3").generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )
    except Exception:
        payload["preview_url"] = None
    return payload


def _ingestion_result_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    payload = jsonable_encoder(result)
    if result.get("document") is not None:
        payload["document"] = _document_payload(result["document"])
    return payload


def _activity_from_repository(user_id: str) -> list[Dict[str, Any]]:
    documents = _repo().list_documents(user_id)
    opportunities = _repo().list_opportunities(user_id)
    entries: list[Dict[str, Any]] = []
    for document in documents:
        entries.append(
            {
                "id": f"doc-{document.doc_id}",
                "opportunity_id": document.doc_id,
                "label": f"Uploaded document: {document.title} ({document.vendor_or_issuer})",
                "timestamp": document.uploaded_at,
            }
        )
    for opportunity in opportunities:
        entries.append(
            {
                "id": f"opp-{opportunity.opportunity_id}-detected",
                "opportunity_id": opportunity.opportunity_id,
                "label": f"New claim opportunity detected: {opportunity.title}",
                "timestamp": opportunity.detected_at,
            }
        )
        for index, note in enumerate(opportunity.audit_trail):
            entries.append(
                {
                    "id": f"opp-{opportunity.opportunity_id}-audit-{index}",
                    "opportunity_id": opportunity.opportunity_id,
                    "label": f"{opportunity.title}: {note}",
                    "timestamp": opportunity.last_updated_at,
                }
            )
    return sorted(entries, key=lambda entry: entry["timestamp"], reverse=True)


@app.get("/health")
def health() -> Dict[str, Any]:
    try:
        repository_status = _repo().healthcheck()
        return {
            "status": "ok",
            "environment": settings.environment,
            "aws_region": settings.aws_region,
            "repository": repository_status,
            "ocr_backend": settings.ocr_backend,
            "submission_backend": settings.submission_backend,
            "model_route": "openai-compatible" if settings.openai_base_url and settings.openai_api_key else "native-bedrock",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/documents/ingest")
def ingest_document(request: DocumentIngestRequest) -> Dict[str, Any]:
    if not request.raw_text and not request.s3_uri:
        raise HTTPException(status_code=400, detail="Either raw_text or s3_uri must be provided")

    event = DocumentUploadedEvent(
        user_id=request.user_id,
        doc_id=request.doc_id or f"doc_{uuid.uuid4().hex[:8]}",
        doc_type_hint=request.doc_type_hint,
        s3_uri=request.s3_uri,
        uploaded_at=request.uploaded_at or datetime.now(timezone.utc).isoformat(),
        source=request.source,
        raw_text=request.raw_text,
    )
    try:
        result = _ingestion_workflow().ingest_document(event)
        return _ingestion_result_payload(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/users/{user_id}/documents/upload")
def upload_document(
    user_id: str,
    file: UploadFile = File(...),
    doc_type_hint: str = Form(default="RECEIPT"),
) -> Dict[str, Any]:
    if not settings.claimback_raw_documents_bucket:
        raise HTTPException(status_code=500, detail="CLAIMBACK_RAW_DOCUMENTS_BUCKET must be configured")

    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    safe_name = _safe_filename(file.filename or "upload.bin")
    key = f"uploads/{user_id}/{doc_id}/{safe_name}"
    bucket = settings.claimback_raw_documents_bucket

    try:
        get_boto3_client("s3").upload_fileobj(
            file.file,
            bucket,
            key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
        event = DocumentUploadedEvent(
            user_id=user_id,
            doc_id=doc_id,
            doc_type_hint=doc_type_hint,
            s3_uri=f"s3://{bucket}/{key}",
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            source="WEB_UPLOAD",
        )
        result = _ingestion_workflow().ingest_document(event)
        return _ingestion_result_payload(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/users/{user_id}/documents")
def list_documents(user_id: str, doc_type: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    documents = _repo().list_documents(user_id, doc_type)
    return {"documents": [_document_payload(document) for document in documents]}


@app.get("/api/users/{user_id}/opportunities")
def list_opportunities(user_id: str, status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    opportunities = _repo().list_opportunities(user_id, status)
    return {"opportunities": jsonable_encoder(opportunities)}


@app.get("/api/users/{user_id}/coverages")
def list_coverages(user_id: str) -> Dict[str, Any]:
    coverages = _repo().list_active_coverages(user_id)
    return {"coverages": jsonable_encoder(coverages)}


@app.get("/api/users/{user_id}/activity")
def list_activity(user_id: str) -> Dict[str, Any]:
    return {"activity": jsonable_encoder(_activity_from_repository(user_id))}


@app.get("/api/opportunities/{opportunity_id}")
def get_opportunity(opportunity_id: str) -> Dict[str, Any]:
    opportunity = _repo().get_opportunity(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"opportunity": jsonable_encoder(opportunity)}


@app.get("/api/opportunities/{opportunity_id}/requirements")
def list_requirements(opportunity_id: str) -> Dict[str, Any]:
    requirements = _repo().list_requirements(opportunity_id)
    return {"requirements": jsonable_encoder(requirements)}


@app.get("/api/opportunities/{opportunity_id}/drafts")
def list_drafts(opportunity_id: str) -> Dict[str, Any]:
    drafts = _repo().list_drafts(opportunity_id)
    return {"drafts": jsonable_encoder(drafts)}


@app.get("/api/opportunities/{opportunity_id}/traces")
def list_traces(opportunity_id: str) -> Dict[str, Any]:
    opportunity = _repo().get_opportunity(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    traces = [
        {
            "id": f"{opportunity_id}-trace-{index}",
            "opportunity_id": opportunity_id,
            "agent": "EvidencePlanner" if "Missing evidence" in note else "Matcher",
            "summary": note,
            "detail": note,
            "timestamp": opportunity.last_updated_at,
            "raw": {"audit_index": index},
        }
        for index, note in enumerate(opportunity.audit_trail)
    ]
    return {"traces": jsonable_encoder(traces)}


@app.post("/api/opportunities/{opportunity_id}/decision")
def decide_opportunity(opportunity_id: str, request: OpportunityDecisionRequest) -> Dict[str, Any]:
    try:
        approval = _approval_workflow().process_decision(request.user_id, opportunity_id, request.decision)
        opportunity = _repo().get_opportunity(opportunity_id)
        return {"approval": jsonable_encoder(approval), "opportunity": jsonable_encoder(opportunity)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/opportunities/{opportunity_id}/submit")
def submit_opportunity(opportunity_id: str, request: SubmitOpportunityRequest) -> Dict[str, Any]:
    try:
        result = _submission_workflow().submit(opportunity_id, request.draft_payload)
        return jsonable_encoder(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/followups/sweep")
def run_followup_sweep() -> Dict[str, Any]:
    try:
        updated_count = _followup_workflow().run_sweep()
        return {"updated_followups": updated_count}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc