"""Strands tools for vault document access."""

from typing import Any, Dict, List, Optional

from backend.database.models import VaultDocument
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
def save_document_to_vault(
    user_id: str,
    doc_id: str,
    doc_type: str,
    title: str,
    source_type: str,
    vendor_or_issuer: str,
    s3_uri: str,
    uploaded_at: str,
    normalized_facts: Dict[str, Any],
    raw_ocr_text: str = "",
    confidence_score: float = 0.0,
) -> Dict[str, Any]:
    document = VaultDocument(
        user_id=user_id,
        doc_id=doc_id,
        doc_type=doc_type,
        title=title,
        source_type=source_type,
        vendor_or_issuer=vendor_or_issuer,
        s3_uri=s3_uri,
        uploaded_at=uploaded_at,
        normalized_facts=normalized_facts,
        raw_ocr_text=raw_ocr_text,
        confidence_score=confidence_score,
    )
    _repository.save_document(document)
    return _envelope(document.model_dump())


@tool
def get_document_by_id(user_id: str, doc_id: str) -> Dict[str, Any]:
    document = _repository.get_document(user_id, doc_id)
    return _envelope(document.model_dump() if document else None, None if document else "document not found")


@tool
def search_documents_for_user(user_id: str, query: str = "") -> Dict[str, Any]:
    query_lower = query.lower()
    documents = _repository.list_documents(user_id)
    if query_lower:
        documents = [
            doc for doc in documents
            if query_lower in doc.title.lower()
            or query_lower in doc.vendor_or_issuer.lower()
            or query_lower in doc.raw_ocr_text.lower()
        ]
    return _envelope([doc.model_dump() for doc in documents])


@tool
def list_documents_by_type(user_id: str, doc_type: str) -> Dict[str, Any]:
    return _envelope([doc.model_dump() for doc in _repository.list_documents(user_id, doc_type)])


@tool
def get_documents_by_model_or_serial(user_id: str, model_number: str = "", serial_number: str = "") -> Dict[str, Any]:
    documents = [
        doc for doc in _repository.list_documents(user_id)
        if (model_number and doc.normalized_facts.get("model_number") == model_number)
        or (serial_number and doc.normalized_facts.get("serial_number") == serial_number)
    ]
    return _envelope([doc.model_dump() for doc in documents])

@tool
def get_vault_document(user_id: str, doc_id: str) -> Dict[str, Any]:
    """Retrieve a vault document by ID."""
    return get_document_by_id(user_id, doc_id)

@tool
def list_user_documents(user_id: str) -> Dict[str, Any]:
    """List all documents for a user."""
    return search_documents_for_user(user_id)
