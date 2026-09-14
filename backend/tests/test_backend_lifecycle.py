import unittest

import backend.main as backend_main
from backend.config import settings
from backend.database.models import VaultDocument
from backend.database.repositories import SingleTableRepository
from backend.services.normalization_service import NormalizationService
from backend.tools import ledger_tools
from backend.workflow.approval_workflow import ApprovalWorkflow
from backend.workflow.events import DocumentUploadedEvent
from backend.workflow.ingestion_workflow import IngestionWorkflow
from backend.workflow.submission_workflow import SubmissionWorkflow


class BackendLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_extraction_backend = settings.extraction_backend
        settings.extraction_backend = "rules"

    def tearDown(self) -> None:
        settings.extraction_backend = self._original_extraction_backend

    def test_warranty_claim_lifecycle_ready_for_approval_then_submitted(self) -> None:
        original_submission_backend = settings.submission_backend
        settings.submission_backend = "stub"
        repository = SingleTableRepository()
        ingestion = IngestionWorkflow(repository)
        approval = ApprovalWorkflow(repository)
        submission = SubmissionWorkflow(repository)
        try:
            receipt_event = DocumentUploadedEvent(
                event_type="DOCUMENT_UPLOADED",
                user_id="usr_demo",
                doc_id="doc_receipt",
                doc_type_hint="RECEIPT",
                s3_uri="s3://claimback/raw/receipt.pdf",
                uploaded_at="2026-09-12T10:20:00Z",
                source="WEB_UPLOAD",
                raw_text=(
                    "Samsung Store Purchase Receipt\n"
                    "Purchase Date: 2026-06-15\n"
                    "Amount: $1,249.99\n"
                    "Model: RF28R7351SR\n"
                    "Serial: S28R7351SR-984210"
                ),
            )
            warranty_event = DocumentUploadedEvent(
                event_type="DOCUMENT_UPLOADED",
                user_id="usr_demo",
                doc_id="doc_warranty",
                doc_type_hint="WARRANTY",
                s3_uri="s3://claimback/raw/warranty.pdf",
                uploaded_at="2026-09-12T10:21:00Z",
                source="WEB_UPLOAD",
                raw_text=(
                    "Samsung Extended Warranty\n"
                    "Coverage Start: 2026-06-15\n"
                    "Coverage End: 2027-06-15\n"
                    "Covered Model: RF28R7351SR\n"
                    "Covered Serial: S28R7351SR-984210\n"
                    "Claim Channel: EMAIL"
                ),
            )
            invoice_event = DocumentUploadedEvent(
                event_type="DOCUMENT_UPLOADED",
                user_id="usr_demo",
                doc_id="doc_invoice",
                doc_type_hint="REPAIR_INVOICE",
                s3_uri="s3://claimback/raw/invoice.pdf",
                uploaded_at="2026-09-12T10:22:00Z",
                source="WEB_UPLOAD",
                raw_text=(
                    "Samsung Refrigerator Repair Invoice\n"
                    "Invoice Date: 2026-08-10\n"
                    "Amount: $420.00\n"
                    "Model: RF28R7351SR\n"
                    "Serial: S28R7351SR-984210\n"
                    "Repair: Compressor replacement"
                ),
            )

            ingestion.ingest_document(receipt_event)
            ingestion.ingest_document(warranty_event)
            result = ingestion.ingest_document(invoice_event)

            opportunity = result["opportunity"]
            self.assertEqual(opportunity.status, "READY_FOR_APPROVAL")
            self.assertEqual(opportunity.impact_amount, 420.0)
            self.assertTrue(result["evidence_plan"].is_complete)
            self.assertEqual(len(result["drafts"]), 1)

            approval_result = approval.process_decision(
                user_id="usr_demo",
                opportunity_id=opportunity.opportunity_id,
                decision="APPROVE",
            )
            self.assertEqual(approval_result.decision, "APPROVED")

            submission_result = submission.submit(opportunity.opportunity_id)
            self.assertEqual(submission_result["submission_job"].status, "SUBMITTED")
            self.assertEqual(submission_result["followup_task"].status, "PENDING")
        finally:
            settings.submission_backend = original_submission_backend

    def test_ledger_tools_detect_price_hikes_and_duplicates(self) -> None:
        repository = SingleTableRepository()
        ledger_tools.configure_repository(repository)

        ledger_tools.record_ledger_event("usr_demo", "SUBSCRIPTION", {
            "transaction_id": "tx_old",
            "merchant_name": "StreamBox",
            "amount": 9.99,
            "transaction_timestamp": "2026-08-01T00:00:00",
        })
        ledger_tools.record_ledger_event("usr_demo", "SUBSCRIPTION", {
            "transaction_id": "tx_new",
            "merchant_name": "StreamBox",
            "amount": 14.99,
            "transaction_timestamp": "2026-09-01T00:00:00",
        })
        price_change = ledger_tools.detect_price_change_candidates("usr_demo", "StreamBox")
        self.assertEqual(price_change["status"], "SUCCESS")
        self.assertEqual(price_change["data"]["price_changes"][0]["annual_impact"], 60.0)

        ledger_tools.record_ledger_event("usr_demo", "CARD", {
            "transaction_id": "tx_dup_1",
            "merchant_name": "Cafe Demo",
            "amount": 18.5,
            "transaction_timestamp": "2026-09-10T10:00:00",
        })
        ledger_tools.record_ledger_event("usr_demo", "CARD", {
            "transaction_id": "tx_dup_2",
            "merchant_name": "Cafe Demo",
            "amount": 18.5,
            "transaction_timestamp": "2026-09-10T10:03:00",
        })
        duplicates = ledger_tools.detect_duplicate_candidates("usr_demo", days=30)
        self.assertEqual(duplicates["status"], "SUCCESS")
        self.assertEqual(duplicates["data"]["duplicate_candidates"][0]["amount"], 18.5)

    def test_office_policy_matches_wifi_and_ride_documents(self) -> None:
        repository = SingleTableRepository()
        ingestion = IngestionWorkflow(repository)

        policy_event = DocumentUploadedEvent(
            event_type="DOCUMENT_UPLOADED",
            user_id="usr_demo",
            doc_id="doc_office_policy",
            doc_type_hint="POLICY",
            s3_uri="s3://claimback/raw/office-policy.pdf",
            uploaded_at="2026-09-01T10:00:00Z",
            source="WEB_UPLOAD",
            raw_text=(
                "Office Reimbursement Policy\n"
                "Employees are entitled to reimbursement for monthly WiFi, internet, broadband, cab, taxi, Uber, Ola, Rapido and ride expenses.\n"
                "Claim Channel: expense portal"
            ),
        )
        jio_event = DocumentUploadedEvent(
            event_type="DOCUMENT_UPLOADED",
            user_id="usr_demo",
            doc_id="doc_jio_bill",
            doc_type_hint="RECEIPT",
            s3_uri="s3://claimback/raw/jio.pdf",
            uploaded_at="2026-09-02T10:00:00Z",
            source="WEB_UPLOAD",
            raw_text="Jio AirFiber Bill Summary\nTotal Payable : 706.82\nAccount Number 411498411579",
        )
        uber_event = DocumentUploadedEvent(
            event_type="DOCUMENT_UPLOADED",
            user_id="usr_demo",
            doc_id="doc_uber_receipt",
            doc_type_hint="RECEIPT",
            s3_uri="s3://claimback/raw/uber.pdf",
            uploaded_at="2026-09-03T10:00:00Z",
            source="WEB_UPLOAD",
            raw_text="Uber Trip Receipt\nRide from Office to Home\nTotal Paid: USD 34.50",
        )

        ingestion.ingest_document(policy_event)
        jio_result = ingestion.ingest_document(jio_event)
        uber_result = ingestion.ingest_document(uber_event)

        self.assertEqual(jio_result["opportunity"].opportunity_type, "OFFICE_REIMBURSEMENT")
        self.assertEqual(jio_result["opportunity"].impact_amount, 706.82)
        self.assertEqual(uber_result["opportunity"].opportunity_type, "OFFICE_REIMBURSEMENT")
        self.assertEqual(uber_result["opportunity"].impact_amount, 34.5)
        self.assertEqual(len(repository.list_opportunities("usr_demo")), 2)

    def test_bank_statement_creates_subscription_price_hike_opportunity(self) -> None:
        repository = SingleTableRepository()
        ingestion = IngestionWorkflow(repository)

        result = ingestion.ingest_document(DocumentUploadedEvent(
            event_type="DOCUMENT_UPLOADED",
            user_id="usr_demo",
            doc_id="doc_hdfc_statement",
            doc_type_hint="LEDGER",
            s3_uri="s3://claimback/raw/hdfc.pdf",
            uploaded_at="2026-09-04T10:00:00Z",
            source="WEB_UPLOAD",
            raw_text=(
                "HDFC Bank Monthly Statement\n"
                "2026-08-01 NETFLIX.COM USD 15.49\n"
                "2026-09-01 NETFLIX.COM USD 22.99\n"
            ),
        ))

        opportunity = result["opportunity"]
        self.assertEqual(opportunity.opportunity_type, "BILL_PRICE_HIKE")
        self.assertEqual(opportunity.impact_amount, 90.0)
        self.assertEqual(opportunity.status, "READY_FOR_APPROVAL")

    def test_billing_statement_parser_extracts_jio_fields(self) -> None:
        parsed = NormalizationService().parse_document_text(
            "RECEIPT",
            (
                "Mr. Manan Yadav\n"
                "Statement Number 373524961074 Jio Number 1259356507\n"
                "Account Number 411498411579\n"
                "Billing Cycle Date : 26-JUL-2026\n"
                "Email: yadav.manan@outlook.com\n"
                "Registered Mobile Number: +919625020380\n"
                "AirFiber_599_3M\n"
                "Jio AirFiber Bill Summary\n"
                "Pay By : 01-AUG-2026\n"
                "Total Payable : 706.82\n"
                "Total Current Month Charges 706.82\n"
                "A. Plan Charges (Excluding Taxes)\n"
                "Total 599.00\n"
                "B. Taxes\n"
                "CGST 53.91\n"
                "SGST 53.91\n"
            ),
        )

        self.assertEqual(parsed["doc_type"], "BILLING_STATEMENT")
        self.assertEqual(parsed["title"], "Jio AirFiber Bill Summary")
        self.assertEqual(parsed["vendor_or_issuer"], "Reliance Jio Infocomm Ltd")
        self.assertGreaterEqual(parsed["confidence_score"], 0.9)

        facts = parsed["normalized_facts"]
        self.assertEqual(facts["customer_name"], "Mr. Manan Yadav")
        self.assertEqual(facts["statement_number"], "373524961074")
        self.assertEqual(facts["account_number"], "411498411579")
        self.assertEqual(facts["jio_number"], "1259356507")
        self.assertEqual(facts["billing_cycle"], "26-JUL-2026")
        self.assertEqual(facts["plan"], "AirFiber_599_3M")
        self.assertEqual(facts["due_date"], "01-AUG-2026")
        self.assertEqual(facts["total_amount"], 706.82)
        self.assertEqual(facts["currency"], "₹ (INR)")
        self.assertEqual(facts["email"], "yadav.manan@outlook.com")
        self.assertEqual(facts["mobile"], "+919625020380")

    def test_repair_invoice_parser_extracts_rich_dyson_fields(self) -> None:
        parsed = NormalizationService().parse_document_text(
            "REPAIR_INVOICE",
            (
                "Dyson Service Center Repair Invoice\n"
                "Official Dyson Authorized Service Center\n"
                "SERVICE CENTER INFO\n"
                "REPAIR DETAILS\n"
                "Dyson Service Center\n"
                "Authorized Repair Station\n"
                "Contact: support@dyson.com\n"
                "Repair Invoice: DYS-44021\n"
                "Service Date: 2026-08-30\n"
                "Customer Name: Manan Yadav\n"
                "Product: Dyson V15 Detect Cordless Vacuum\n"
                "Model: SV22\n"
                "Diagnosis / Issue: Battery fault; unit powers down under load.\n"
                "Service Action: Replaced defective click-in battery pack assembly.\n"
                "Line Item\n"
                "Cost (USD)\n"
                "Dyson SV22 Replacement Battery Pack Assembly\n"
                "USD $ 180.00\n"
                "TOTAL PAID\n"
                "USD $ 180.00\n"
                "Note: Serial number label photo not provided at time of service.\n"
            ),
        )

        self.assertEqual(parsed["doc_type"], "REPAIR_INVOICE")
        self.assertEqual(parsed["title"], "Dyson Service Center Repair Invoice")
        self.assertEqual(parsed["vendor_or_issuer"], "Dyson")

        facts = parsed["normalized_facts"]
        self.assertEqual(facts["invoice_number"], "DYS-44021")
        self.assertEqual(facts["invoice_date"], "2026-08-30")
        self.assertEqual(facts["service_date"], "2026-08-30")
        self.assertEqual(facts["customer_name"], "Manan Yadav")
        self.assertEqual(facts["product_name"], "Dyson V15 Detect Cordless Vacuum")
        self.assertEqual(facts["model_number"], "SV22")
        self.assertEqual(facts["diagnosis_issue"], "Battery fault; unit powers down under load.")
        self.assertEqual(facts["service_action"], "Replaced defective click-in battery pack assembly.")
        self.assertEqual(
            facts["repair_description"],
            "Battery fault; unit powers down under load. Replaced defective click-in battery pack assembly.",
        )
        self.assertEqual(facts["total_amount"], 180.0)
        self.assertEqual(facts["amount"], 180.0)

    def test_warranty_parser_extracts_multiline_dyson_fields(self) -> None:
        parsed = NormalizationService().parse_document_text(
            "WARRANTY",
            (
                "2-Year Limited Warranty Certificate\n"
                "Dyson Ltd. Guarantee & Product Support\n"
                "Product Line:\n"
                "Dyson V15 Detect Cordless Vacuum\n"
                "Model Number:\n"
                "SV22\n"
                "Warranty Start Date:\n"
                "2025-11-02\n"
                "Warranty End Date:\n"
                "2027-11-02 (2 Years Coverage)\n"
                "Covered Defects:\n"
                "Full coverage for manufacturing defects, motor faults, and battery pack faults.\n"
                "Support & Claims\n"
                "Channel:\n"
                "Email: support@dyson.com | Phone: 1-866-693-9766\n"
            ),
        )

        self.assertEqual(parsed["doc_type"], "WARRANTY")
        self.assertEqual(parsed["vendor_or_issuer"], "Dyson")

        facts = parsed["normalized_facts"]
        self.assertEqual(facts["model_number"], "SV22")
        self.assertEqual(facts["product_name"], "Dyson V15 Detect Cordless Vacuum")
        self.assertEqual(facts["coverage_start_date"], "2025-11-02")
        self.assertEqual(facts["coverage_end_date"], "2027-11-02 (2 Years Coverage)")
        self.assertEqual(facts["covered_defects"], "Full coverage for manufacturing defects, motor faults, and battery pack faults.")
        self.assertEqual(facts["claim_channel"], "Email: support@dyson.com | Phone: 1-866-693-9766")
        self.assertEqual(facts["claim_email"], "support@dyson.com")
        self.assertEqual(facts["claim_phone"], "1-866-693-9766")

    def test_llm_extractor_result_is_used_and_merged_with_rule_fallback(self) -> None:
        def fake_extractor(doc_type_hint: str, raw_text: str) -> dict:
            return {
                "doc_type": "warranty",
                "title": "2-Year Limited Warranty Certificate",
                "vendor_or_issuer": "Dyson",
                "confidence_score": 0.99,
                "normalized_facts": {
                    "Product Name": "Dyson V15 Detect Cordless Vacuum",
                    "model_number": "SV22",
                    "coverage_start_date": "2025-11-02",
                    "coverage_end_date": "2027-11-02",
                    "covered_defects": "Manufacturing defects, motor faults, and battery pack faults",
                    "claim_email": "support@dyson.com",
                },
            }

        parsed = NormalizationService(llm_extractor=fake_extractor).parse_document_text(
            "WARRANTY",
            "2-Year Limited Warranty Certificate\nModel Number:\nSV22\nEmail: support@dyson.com\n",
        )

        self.assertEqual(parsed["doc_type"], "WARRANTY")
        self.assertEqual(parsed["title"], "2-Year Limited Warranty Certificate")
        self.assertEqual(parsed["confidence_score"], 0.99)
        self.assertEqual(parsed["normalized_facts"]["product_name"], "Dyson V15 Detect Cordless Vacuum")
        self.assertEqual(parsed["normalized_facts"]["model_number"], "SV22")

    def test_llm_json_loader_recovers_object_from_provider_wrapper(self) -> None:
        payload = NormalizationService()._load_json_object(
            '{\n {"doc_type":"WARRANTY","normalized_facts":{"model_number":"SV22"}}'
        )

        self.assertEqual(payload["doc_type"], "WARRANTY")
        self.assertEqual(payload["normalized_facts"]["model_number"], "SV22")

    def test_document_payload_includes_original_pdf_preview_metadata(self) -> None:
        test_case = self

        class FakeS3Client:
            def generate_presigned_url(self, operation_name, Params, ExpiresIn):
                test_case.assertEqual(operation_name, "get_object")
                test_case.assertEqual(Params, {"Bucket": "claimback-raw", "Key": "uploads/usr_demo/doc_123/original_bill.pdf"})
                test_case.assertEqual(ExpiresIn, 3600)
                return "https://example.test/original_bill.pdf?signature=demo"

        original_get_boto3_client = backend_main.get_boto3_client
        backend_main.get_boto3_client = lambda service_name: FakeS3Client()
        try:
            document = VaultDocument(
                user_id="usr_demo",
                doc_id="doc_123",
                doc_type="BILLING_STATEMENT",
                title="Jio AirFiber Bill Summary",
                source_type="WEB_UPLOAD",
                vendor_or_issuer="Reliance Jio Infocomm Ltd",
                s3_uri="s3://claimback-raw/uploads/usr_demo/doc_123/original_bill.pdf",
                uploaded_at="2026-09-13T18:30:00Z",
                normalized_facts={"total_amount": 706.82},
                raw_ocr_text="Jio AirFiber Bill Summary",
                confidence_score=0.97,
            )

            payload = backend_main._document_payload(document)
        finally:
            backend_main.get_boto3_client = original_get_boto3_client

        self.assertEqual(payload["file_name"], "original_bill.pdf")
        self.assertEqual(payload["preview_url"], "https://example.test/original_bill.pdf?signature=demo")


if __name__ == "__main__":
    unittest.main()
