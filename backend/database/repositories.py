"""Repository implementations for local memory and DynamoDB single-table storage."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from backend.aws_clients import get_boto3_resource
from backend.config import settings
from backend.database.models import (
    ActionDraft,
    ClaimOpportunity,
    CoverageRecord,
    EvidenceRequirement,
    FollowUpTask,
    LedgerEntry,
    SubmissionJob,
    UserApproval,
    VaultDocument,
)

ModelType = TypeVar("ModelType", bound=BaseModel)


def _serialize_model(model: BaseModel) -> Dict[str, Any]:
    item_data = model.model_dump(mode="json")
    item_data["PK"] = getattr(model, "pk")
    item_data["SK"] = getattr(model, "sk")
    item_data["entity_type"] = model.__class__.__name__
    return item_data


def _to_dynamodb(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [_to_dynamodb(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dynamodb(item) for key, item in value.items()}
    return value


def _from_dynamodb(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, list):
        return [_from_dynamodb(item) for item in value]
    if isinstance(value, dict):
        return {key: _from_dynamodb(item) for key, item in value.items()}
    return value


class InMemorySingleTableRepository:
    def __init__(self, table_name: str = "ClaimBackSingleTable"):
        self.table_name = table_name
        self._db: Dict[str, Dict[str, Any]] = {}

    def put_item(self, pk: str, sk: str, item_data: Dict[str, Any]) -> None:
        if pk not in self._db:
            self._db[pk] = {}
        self._db[pk][sk] = item_data

    def get_item(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        return self._db.get(pk, {}).get(sk)

    def query_by_pk(self, pk: str, sk_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        partition_items = self._db.get(pk, {})
        if not sk_prefix:
            return list(partition_items.values())
        return [item for sk, item in partition_items.items() if sk.startswith(sk_prefix)]

    def delete_item(self, pk: str, sk: str) -> None:
        if pk in self._db and sk in self._db[pk]:
            del self._db[pk][sk]

    def save_model(self, model: BaseModel) -> None:
        item_data = _serialize_model(model)
        self.put_item(item_data["PK"], item_data["SK"], item_data)

    def _get_model(self, pk: str, sk: str, model_type: Type[ModelType]) -> Optional[ModelType]:
        item = self.get_item(pk, sk)
        return model_type(**item) if item else None

    def _query_models(self, pk: str, sk_prefix: str, model_type: Type[ModelType]) -> List[ModelType]:
        return [model_type(**item) for item in self.query_by_pk(pk, sk_prefix)]

    def save_document(self, document: VaultDocument) -> VaultDocument:
        self.save_model(document)
        return document

    def get_document(self, user_id: str, doc_id: str) -> Optional[VaultDocument]:
        return self._get_model(f"USER#{user_id}", f"DOC#{doc_id}", VaultDocument)

    def list_documents(self, user_id: str, doc_type: Optional[str] = None) -> List[VaultDocument]:
        documents = self._query_models(f"USER#{user_id}", "DOC#", VaultDocument)
        if doc_type is None:
            return documents
        return [doc for doc in documents if doc.doc_type == doc_type]

    def save_coverage(self, coverage: CoverageRecord) -> CoverageRecord:
        self.save_model(coverage)
        return coverage

    def list_active_coverages(self, user_id: str) -> List[CoverageRecord]:
        return [
            coverage
            for coverage in self._query_models(f"USER#{user_id}", "COVERAGE#", CoverageRecord)
            if coverage.status == "ACTIVE"
        ]

    def save_ledger_entry(self, ledger_entry: LedgerEntry) -> LedgerEntry:
        self.save_model(ledger_entry)
        return ledger_entry

    def list_ledger_entries(self, user_id: str) -> List[LedgerEntry]:
        return self._query_models(f"USER#{user_id}", "LEDGER#", LedgerEntry)

    def save_opportunity(self, opportunity: ClaimOpportunity) -> ClaimOpportunity:
        self.save_model(opportunity)
        return opportunity

    def get_opportunity(self, opportunity_id: str) -> Optional[ClaimOpportunity]:
        for partition in self._db.values():
            item = next((value for key, value in partition.items() if key == f"OPPORTUNITY#{opportunity_id}"), None)
            if item:
                return ClaimOpportunity(**item)
        return None

    def list_opportunities(self, user_id: str, status: Optional[str] = None) -> List[ClaimOpportunity]:
        opportunities = self._query_models(f"USER#{user_id}", "OPPORTUNITY#", ClaimOpportunity)
        if status is None:
            return opportunities
        return [opp for opp in opportunities if opp.status == status]

    def save_requirement(self, requirement: EvidenceRequirement) -> EvidenceRequirement:
        self.save_model(requirement)
        return requirement

    def list_requirements(self, opportunity_id: str) -> List[EvidenceRequirement]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "REQUIREMENT#", EvidenceRequirement)

    def save_draft(self, draft: ActionDraft) -> ActionDraft:
        self.save_model(draft)
        return draft

    def list_drafts(self, opportunity_id: str) -> List[ActionDraft]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "DRAFT#", ActionDraft)

    def save_approval(self, approval: UserApproval) -> UserApproval:
        self.save_model(approval)
        return approval

    def list_approvals(self, opportunity_id: str) -> List[UserApproval]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "APPROVAL#", UserApproval)

    def save_submission_job(self, submission_job: SubmissionJob) -> SubmissionJob:
        self.save_model(submission_job)
        return submission_job

    def list_submission_jobs(self, opportunity_id: str) -> List[SubmissionJob]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "SUBMISSION#", SubmissionJob)

    def save_followup_task(self, followup_task: FollowUpTask) -> FollowUpTask:
        self.save_model(followup_task)
        return followup_task

    def list_followup_tasks(self, opportunity_id: str) -> List[FollowUpTask]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "FOLLOWUP#", FollowUpTask)

    def list_due_followup_tasks(self, as_of: Optional[str] = None) -> List[FollowUpTask]:
        cutoff = as_of or datetime.now(timezone.utc).isoformat()
        due_tasks: List[FollowUpTask] = []
        for partition in self._db.values():
            for sk, item in partition.items():
                if not sk.startswith("FOLLOWUP#"):
                    continue
                if item.get("status") != "PENDING":
                    continue
                if item.get("due_at", "") <= cutoff:
                    due_tasks.append(FollowUpTask(**item))
        return due_tasks

    def healthcheck(self) -> Dict[str, Any]:
        return {"backend": "memory", "table_name": self.table_name, "ok": True}


class DynamoDBSingleTableRepository:
    def __init__(self, table_name: str, endpoint_url: str | None = None):
        try:
            from boto3.dynamodb.conditions import Attr, Key
        except ImportError as exc:
            raise RuntimeError("boto3 must be installed to use the DynamoDB repository") from exc

        self.table_name = table_name
        self.Attr = Attr
        self.Key = Key
        dynamodb = get_boto3_resource("dynamodb", endpoint_url=endpoint_url)
        self.table = dynamodb.Table(table_name)

    def put_item(self, pk: str, sk: str, item_data: Dict[str, Any]) -> None:
        payload = {**item_data, "PK": pk, "SK": sk}
        self.table.put_item(Item=_to_dynamodb(payload))

    def get_item(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        response = self.table.get_item(Key={"PK": pk, "SK": sk})
        item = response.get("Item")
        return _from_dynamodb(item) if item else None

    def query_by_pk(self, pk: str, sk_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        query_kwargs: Dict[str, Any] = {"KeyConditionExpression": self.Key("PK").eq(pk)}
        if sk_prefix:
            query_kwargs["KeyConditionExpression"] = self.Key("PK").eq(pk) & self.Key("SK").begins_with(sk_prefix)

        items: List[Dict[str, Any]] = []
        response = self.table.query(**query_kwargs)
        items.extend(_from_dynamodb(item) for item in response.get("Items", []))
        while "LastEvaluatedKey" in response:
            response = self.table.query(ExclusiveStartKey=response["LastEvaluatedKey"], **query_kwargs)
            items.extend(_from_dynamodb(item) for item in response.get("Items", []))
        return items

    def delete_item(self, pk: str, sk: str) -> None:
        self.table.delete_item(Key={"PK": pk, "SK": sk})

    def save_model(self, model: BaseModel) -> None:
        item_data = _serialize_model(model)
        self.put_item(item_data["PK"], item_data["SK"], item_data)

    def _get_model(self, pk: str, sk: str, model_type: Type[ModelType]) -> Optional[ModelType]:
        item = self.get_item(pk, sk)
        return model_type(**item) if item else None

    def _query_models(self, pk: str, sk_prefix: str, model_type: Type[ModelType]) -> List[ModelType]:
        return [model_type(**item) for item in self.query_by_pk(pk, sk_prefix)]

    def _scan(self, filter_expression: Any) -> List[Dict[str, Any]]:
        response = self.table.scan(FilterExpression=filter_expression)
        items = [_from_dynamodb(item) for item in response.get("Items", [])]
        while "LastEvaluatedKey" in response:
            response = self.table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(_from_dynamodb(item) for item in response.get("Items", []))
        return items

    def save_document(self, document: VaultDocument) -> VaultDocument:
        self.save_model(document)
        return document

    def get_document(self, user_id: str, doc_id: str) -> Optional[VaultDocument]:
        return self._get_model(f"USER#{user_id}", f"DOC#{doc_id}", VaultDocument)

    def list_documents(self, user_id: str, doc_type: Optional[str] = None) -> List[VaultDocument]:
        documents = self._query_models(f"USER#{user_id}", "DOC#", VaultDocument)
        if doc_type is None:
            return documents
        return [doc for doc in documents if doc.doc_type == doc_type]

    def save_coverage(self, coverage: CoverageRecord) -> CoverageRecord:
        self.save_model(coverage)
        return coverage

    def list_active_coverages(self, user_id: str) -> List[CoverageRecord]:
        return [
            coverage
            for coverage in self._query_models(f"USER#{user_id}", "COVERAGE#", CoverageRecord)
            if coverage.status == "ACTIVE"
        ]

    def save_ledger_entry(self, ledger_entry: LedgerEntry) -> LedgerEntry:
        self.save_model(ledger_entry)
        return ledger_entry

    def list_ledger_entries(self, user_id: str) -> List[LedgerEntry]:
        return self._query_models(f"USER#{user_id}", "LEDGER#", LedgerEntry)

    def save_opportunity(self, opportunity: ClaimOpportunity) -> ClaimOpportunity:
        self.save_model(opportunity)
        return opportunity

    def get_opportunity(self, opportunity_id: str) -> Optional[ClaimOpportunity]:
        items = self._scan(self.Attr("SK").eq(f"OPPORTUNITY#{opportunity_id}"))
        return ClaimOpportunity(**items[0]) if items else None

    def list_opportunities(self, user_id: str, status: Optional[str] = None) -> List[ClaimOpportunity]:
        opportunities = self._query_models(f"USER#{user_id}", "OPPORTUNITY#", ClaimOpportunity)
        if status is None:
            return opportunities
        return [opp for opp in opportunities if opp.status == status]

    def save_requirement(self, requirement: EvidenceRequirement) -> EvidenceRequirement:
        self.save_model(requirement)
        return requirement

    def list_requirements(self, opportunity_id: str) -> List[EvidenceRequirement]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "REQUIREMENT#", EvidenceRequirement)

    def save_draft(self, draft: ActionDraft) -> ActionDraft:
        self.save_model(draft)
        return draft

    def list_drafts(self, opportunity_id: str) -> List[ActionDraft]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "DRAFT#", ActionDraft)

    def save_approval(self, approval: UserApproval) -> UserApproval:
        self.save_model(approval)
        return approval

    def list_approvals(self, opportunity_id: str) -> List[UserApproval]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "APPROVAL#", UserApproval)

    def save_submission_job(self, submission_job: SubmissionJob) -> SubmissionJob:
        self.save_model(submission_job)
        return submission_job

    def list_submission_jobs(self, opportunity_id: str) -> List[SubmissionJob]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "SUBMISSION#", SubmissionJob)

    def save_followup_task(self, followup_task: FollowUpTask) -> FollowUpTask:
        self.save_model(followup_task)
        return followup_task

    def list_followup_tasks(self, opportunity_id: str) -> List[FollowUpTask]:
        return self._query_models(f"OPPORTUNITY#{opportunity_id}", "FOLLOWUP#", FollowUpTask)

    def list_due_followup_tasks(self, as_of: Optional[str] = None) -> List[FollowUpTask]:
        cutoff = as_of or datetime.now(timezone.utc).isoformat()
        items = self._scan(
            self.Attr("SK").begins_with("FOLLOWUP#")
            & self.Attr("status").eq("PENDING")
            & self.Attr("due_at").lte(cutoff)
        )
        return [FollowUpTask(**item) for item in items]

    def healthcheck(self) -> Dict[str, Any]:
        self.table.load()
        return {
            "backend": "dynamodb",
            "table_name": self.table_name,
            "table_status": self.table.table_status,
            "ok": True,
        }


SingleTableRepository = InMemorySingleTableRepository


def build_repository():
    backend = settings.repository_backend.strip().lower()
    if backend == "dynamodb":
        return DynamoDBSingleTableRepository(
            table_name=settings.dynamodb_table_name,
            endpoint_url=settings.dynamodb_endpoint_url or None,
        )
    return InMemorySingleTableRepository(table_name=settings.dynamodb_table_name)
