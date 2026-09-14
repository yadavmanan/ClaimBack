"""OCR service with a local stub mode and an AWS Textract mode."""

from io import BytesIO
from typing import Any, Dict

from backend.aws_clients import get_boto3_client
from backend.config import settings


class OCRService:
    def __init__(self):
        self.backend = settings.ocr_backend.strip().lower()
        self.textract_client = None
        self.s3_client = None
        if self.backend == "textract":
            self.textract_client = get_boto3_client("textract")
            self.s3_client = get_boto3_client("s3")

    def extract_text(self, s3_bucket: str, s3_key: str) -> Dict[str, Any]:
        if self.backend != "textract":
            return {
                "s3_uri": f"s3://{s3_bucket}/{s3_key}",
                "raw_text": "SAMSUNG REPAIR CENTER\nDate: 2026-08-10\nTotal: $245.00\nInvoice #: INV-9921",
                "confidence": 0.98,
                "provider": "stub",
            }

        if s3_key.lower().endswith(".pdf"):
            return self._extract_pdf_text(s3_bucket, s3_key)

        response = self.textract_client.detect_document_text(
            Document={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}}
        )
        lines = [
            block.get("Text", "")
            for block in response.get("Blocks", [])
            if block.get("BlockType") == "LINE" and block.get("Text")
        ]
        line_confidences = [
            float(block.get("Confidence", 0.0))
            for block in response.get("Blocks", [])
            if block.get("BlockType") == "LINE"
        ]
        confidence = round(sum(line_confidences) / len(line_confidences), 2) if line_confidences else 0.0

        return {
            "s3_uri": f"s3://{s3_bucket}/{s3_key}",
            "raw_text": "\n".join(lines),
            "confidence": confidence,
            "provider": "textract",
            "raw_response": response,
        }

    def _extract_pdf_text(self, s3_bucket: str, s3_key: str) -> Dict[str, Any]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf must be installed to process uploaded PDF files") from exc

        response = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        pdf_bytes = response["Body"].read()
        reader = PdfReader(BytesIO(pdf_bytes))
        lines = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                lines.append(text.strip())
        raw_text = "\n\n".join(lines)
        if not raw_text:
            raise ValueError("No selectable text found in PDF. Upload an image file or enable async Textract for scanned PDFs.")
        return {
            "s3_uri": f"s3://{s3_bucket}/{s3_key}",
            "raw_text": raw_text,
            "confidence": 1.0,
            "provider": "pypdf",
        }
