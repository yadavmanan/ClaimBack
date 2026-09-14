"""Document extraction and normalization utilities."""

import json
import re
from typing import Any, Callable, Dict, Optional

from backend.config import settings

LLMExtractor = Callable[[str, str], Dict[str, Any]]

class NormalizationService:
    DOCUMENT_TYPES = {
        "RECEIPT": "RECEIPT",
        "PURCHASE_RECEIPT": "RECEIPT",
        "INVOICE": "REPAIR_INVOICE",
        "REPAIR_INVOICE": "REPAIR_INVOICE",
        "WARRANTY": "WARRANTY",
        "POLICY": "POLICY",
        "BENEFIT": "BENEFIT",
        "LEDGER": "LEDGER_EVENT",
    }

    def __init__(self, llm_extractor: Optional[LLMExtractor] = None):
        self.llm_extractor = llm_extractor

    def normalize_doc_type(self, raw_type: str) -> str:
        return self.DOCUMENT_TYPES.get(raw_type.strip().upper(), raw_type.strip().upper())

    def normalize_merchant(self, raw_name: str) -> str:
        clean = raw_name.strip().upper()
        if "SAMSUNG" in clean:
            return "SAMSUNG"
        return clean

    def normalize_amount(self, raw_amount: Any) -> float:
        if isinstance(raw_amount, (int, float)):
            return float(raw_amount)
        clean_str = str(raw_amount).replace("$", "").replace(",", "").strip()
        return float(clean_str)

    def normalize_date(self, raw_date: str) -> str:
        return raw_date.strip()

    def parse_document_text(self, doc_type_hint: str, raw_text: str) -> Dict[str, Any]:
        if self._should_use_llm():
            llm_result = self._parse_document_text_with_llm(doc_type_hint, raw_text)
            if llm_result is not None:
                return llm_result

        return self._parse_document_text_with_rules(doc_type_hint, raw_text)

    def _parse_document_text_with_rules(self, doc_type_hint: str, raw_text: str) -> Dict[str, Any]:
        doc_type = self._infer_doc_type(doc_type_hint, raw_text)
        title = self._infer_title(doc_type, raw_text)
        total_amount = self._extract_amount(raw_text)
        billing_facts = self._extract_billing_statement_facts(raw_text) if doc_type == "BILLING_STATEMENT" else {}
        repair_facts = self._extract_repair_invoice_facts(raw_text) if doc_type == "REPAIR_INVOICE" else {}
        warranty_facts = self._extract_warranty_facts(raw_text) if doc_type in {"WARRANTY", "POLICY", "BENEFIT"} else {}
        facts = {
            "amount": total_amount,
            "total_amount": total_amount,
            "purchase_date": self._extract_first_label(raw_text, ["Purchase Date"]),
            "invoice_date": self._extract_first_label(raw_text, ["Invoice Date", "Service Date"]),
            "coverage_start_date": self._extract_first_label(raw_text, ["Coverage Start", "Warranty Start Date"]),
            "coverage_end_date": self._extract_first_label(raw_text, ["Coverage End", "Warranty End Date"]),
            "model_number": self._extract_first_label(raw_text, ["Model Number", "Model", "Covered Model"]),
            "serial_number": self._extract_first_label(raw_text, ["Serial", "Covered Serial"]),
            "claim_channel": self._extract_first_label(raw_text, ["Claim Channel", "Channel"]),
            "repair_description": self._extract_first_label(raw_text, ["Repair", "Diagnosis / Issue", "Service Action"]),
            **repair_facts,
            **warranty_facts,
            **billing_facts,
        }
        normalized_facts = {key: value for key, value in facts.items() if value not in (None, "")}
        vendor = self._infer_vendor(title, raw_text)
        confidence = self._estimate_confidence(normalized_facts)
        return {
            "doc_type": doc_type,
            "title": title,
            "vendor_or_issuer": vendor,
            "normalized_facts": normalized_facts,
            "confidence_score": confidence,
        }

    def _should_use_llm(self) -> bool:
        backend = settings.extraction_backend.strip().lower()
        if self.llm_extractor is not None:
            return True
        return backend in {"llm", "openai"} and bool(settings.openai_api_key) and bool(settings.openai_model_id or settings.bedrock_model_id)

    def _parse_document_text_with_llm(self, doc_type_hint: str, raw_text: str) -> Optional[Dict[str, Any]]:
        try:
            payload = self.llm_extractor(doc_type_hint, raw_text) if self.llm_extractor else self._call_openai_extractor(doc_type_hint, raw_text)
            return self._normalize_llm_payload(payload, doc_type_hint, raw_text)
        except Exception:
            return None

    def _call_openai_extractor(self, doc_type_hint: str, raw_text: str) -> Dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai must be installed to use EXTRACTION_BACKEND=llm") from exc

        client_kwargs: Dict[str, Any] = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        if settings.openai_project_id:
            client_kwargs["project"] = settings.openai_project_id

        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=settings.openai_model_id or settings.bedrock_model_id,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured data from OCR text for financial, warranty, bill, receipt, "
                        "invoice, policy, service, and claim documents. Return only JSON with keys: "
                        "doc_type, title, vendor_or_issuer, normalized_facts, confidence_score. "
                        "Use concise snake_case fact keys. Preserve exact IDs, dates, amounts, emails, phone numbers, "
                        "product names, model numbers, serial numbers, coverage dates, line items, repair details, "
                        "claim channels, taxes, account numbers, and notes when present. Do not invent missing values."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Doc type hint: {doc_type_hint}\n\nOCR text:\n{raw_text}",
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        return self._load_json_object(content)

    def _load_json_object(self, content: str) -> Dict[str, Any]:
        decoder = json.JSONDecoder()
        for index, character in enumerate(content):
            if character != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(content[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        raise json.JSONDecodeError("No JSON object found", content, 0)

    def _normalize_llm_payload(self, payload: Dict[str, Any], doc_type_hint: str, raw_text: str) -> Dict[str, Any]:
        fallback = self._parse_document_text_with_rules(doc_type_hint, raw_text)
        doc_type = self.normalize_doc_type(str(payload.get("doc_type") or fallback["doc_type"]))
        title = str(payload.get("title") or fallback["title"]).strip()
        vendor = str(payload.get("vendor_or_issuer") or fallback["vendor_or_issuer"]).strip()
        facts = payload.get("normalized_facts")
        if not isinstance(facts, dict):
            facts = {}

        normalized_facts = dict(fallback["normalized_facts"])
        normalized_facts.update(self._clean_facts(facts))
        if "amount" not in normalized_facts and "total_amount" in normalized_facts:
            normalized_facts["amount"] = normalized_facts["total_amount"]
        if "total_amount" not in normalized_facts and "amount" in normalized_facts:
            normalized_facts["total_amount"] = normalized_facts["amount"]

        confidence = payload.get("confidence_score", fallback["confidence_score"])
        try:
            confidence_score = float(confidence)
        except (TypeError, ValueError):
            confidence_score = fallback["confidence_score"]

        return {
            "doc_type": doc_type,
            "title": title,
            "vendor_or_issuer": vendor,
            "normalized_facts": normalized_facts,
            "confidence_score": round(max(0.0, min(confidence_score, 1.0)), 2),
        }

    def _clean_facts(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}
        for key, value in facts.items():
            if value in (None, "", [], {}):
                continue
            normalized_key = re.sub(r"[^a-zA-Z0-9]+", "_", str(key).strip().lower()).strip("_")
            if not normalized_key:
                continue
            if normalized_key in {"amount", "total_amount", "tax_amount", "cgst", "sgst", "plan_charges"}:
                try:
                    value = self.normalize_amount(value)
                except (TypeError, ValueError):
                    pass
            cleaned[normalized_key] = value
        return cleaned

    def _infer_doc_type(self, doc_type_hint: str, raw_text: str) -> str:
        hint = self.normalize_doc_type(doc_type_hint)
        text = raw_text.upper()

        if any(marker in text for marker in ["BILL SUMMARY", "STATEMENT NUMBER", "ACCOUNT NUMBER", "TOTAL PAYABLE", "CURRENT PLAN"]):
            return "BILLING_STATEMENT"
        if "WARRANTY" in text:
            return "WARRANTY"
        if "POLICY" in text:
            return "POLICY"
        if "REPAIR" in text and "INVOICE" in text:
            return "REPAIR_INVOICE"
        return hint

    def _infer_title(self, doc_type: str, raw_text: str) -> str:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for keyword in ["bill summary", "billing statement", "repair invoice", "invoice", "warranty", "receipt", "statement"]:
            for line in lines:
                if keyword in line.lower():
                    return line
        return self._first_non_empty_line(raw_text) or doc_type.replace("_", " ").title()

    def _extract_amount(self, text: str) -> Optional[float]:
        currency_prefix = r"(?:[A-Z]{3}\s+)?[₹`$]?"
        patterns = [
            rf"Total\s+Payable\s*:?\s*{currency_prefix}\s*([0-9,]+(?:\.[0-9]{{2}})?)",
            rf"Total\s+Paid\s*:?\s*{currency_prefix}\s*([0-9,]+(?:\.[0-9]{{2}})?)",
            rf"Total\s+Current\s+(?:Month\s+)?Charges(?:\s*\(A\+B\))?\s*:?\s*{currency_prefix}\s*([0-9,]+(?:\.[0-9]{{2}})?)",
            rf"Amount\s*:?\s*{currency_prefix}\s*([0-9,]+(?:\.[0-9]{{2}})?)",
            rf"Total\s*:?\s*{currency_prefix}\s*([0-9,]+(?:\.[0-9]{{2}})?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.normalize_amount(match.group(1))
        return None

    def _extract_label(self, text: str, label: str) -> Optional[str]:
        lines = [line.strip() for line in text.splitlines()]
        label_pattern = re.compile(rf"^{re.escape(label)}\s*:?\s*(.*)$", re.IGNORECASE)
        for index, line in enumerate(lines):
            match = label_pattern.match(line)
            if not match:
                continue
            same_line_value = match.group(1).strip()
            if same_line_value:
                return same_line_value
            next_value = self._next_value_line(lines, index + 1)
            if next_value:
                return next_value
        return None

    def _extract_first_label(self, text: str, labels: list[str]) -> Optional[str]:
        for label in labels:
            value = self._extract_label(text, label)
            if value:
                return value
        return None

    def _extract_repair_invoice_facts(self, text: str) -> Dict[str, Any]:
        diagnosis = self._extract_first_label(text, ["Diagnosis / Issue", "Diagnosis", "Issue"])
        service_action = self._extract_first_label(text, ["Service Action", "Repair Action", "Action Taken"])
        repair_description = self._combine_repair_description(diagnosis, service_action)

        return {
            "invoice_number": self._extract_first_label(text, ["Repair Invoice", "Invoice #", "Invoice Number"]),
            "service_date": self._extract_first_label(text, ["Service Date", "Invoice Date"]),
            "customer_name": self._extract_first_label(text, ["Customer Name", "Customer"]),
            "product_name": self._extract_first_label(text, ["Product", "Item", "Device"]),
            "diagnosis_issue": diagnosis,
            "service_action": service_action,
            "repair_description": repair_description,
        }

    def _extract_warranty_facts(self, text: str) -> Dict[str, Any]:
        return {
            "product_name": self._extract_first_label(text, ["Product Line", "Product", "Covered Product"]),
            "covered_defects": self._extract_first_label(text, ["Covered Defects", "Coverage", "Covered Repairs"]),
            "support_channel": self._extract_first_label(text, ["Claim Channel", "Channel"]),
            "claim_email": self._extract_email(text),
            "claim_phone": self._extract_phone(text),
        }

    def _next_value_line(self, lines: list[str], start_index: int) -> Optional[str]:
        for line in lines[start_index:]:
            if not line:
                continue
            if line.isupper() and not re.search(r"[0-9@$]", line) and len(line.split()) <= 4:
                continue
            return line
        return None

    def _combine_repair_description(self, diagnosis: Optional[str], service_action: Optional[str]) -> Optional[str]:
        parts = [part for part in [diagnosis, service_action] if part]
        if not parts:
            return None
        return " ".join(parts)

    def _extract_billing_statement_facts(self, text: str) -> Dict[str, Any]:
        cgst = self._extract_numeric_after_label(text, "CGST")
        sgst = self._extract_numeric_after_label(text, "SGST")
        total_tax = None
        if cgst is not None and sgst is not None:
            total_tax = round(cgst + sgst, 2)

        return {
            "customer_name": self._extract_customer_name(text),
            "billing_cycle": self._extract_label(text, "Billing Cycle Date") or self._extract_label(text, "Billing Cycle"),
            "due_date": self._extract_label(text, "Pay By"),
            "account_number": self._extract_digits_after_label(text, "Account Number"),
            "statement_number": self._extract_digits_after_label(text, "Statement Number"),
            "jio_number": self._extract_digits_after_label(text, "Jio Number"),
            "plan": self._extract_plan(text),
            "plan_charges": self._extract_plan_charges(text),
            "cgst": cgst,
            "sgst": sgst,
            "total_tax": total_tax,
            "currency": self._infer_currency(text),
            "email": self._extract_email(text),
            "mobile": self._extract_mobile(text),
        }

    def _extract_customer_name(self, text: str) -> Optional[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:4]:
            if re.match(r"^(Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+", line, re.IGNORECASE):
                return line
        return self._extract_label(text, "Customer")

    def _extract_numeric_after_label(self, text: str, label: str) -> Optional[float]:
        match = re.search(rf"{re.escape(label)}[^0-9]*([0-9,]+(?:\.[0-9]{{2}})?)", text, re.IGNORECASE)
        if not match:
            return None
        return self.normalize_amount(match.group(1))

    def _extract_digits_after_label(self, text: str, label: str) -> Optional[str]:
        match = re.search(rf"{re.escape(label)}[^0-9]*([0-9]{{5,}})", text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_plan(self, text: str) -> Optional[str]:
        labeled_plan = self._extract_label(text, "Current Plan")
        if labeled_plan:
            return labeled_plan
        match = re.search(r"\bAirFiber_[A-Za-z0-9_]+\b", text)
        return match.group(0) if match else None

    def _extract_plan_charges(self, text: str) -> Optional[float]:
        match = re.search(r"Plan\s+Charges.*?Total\s+([0-9,]+(?:\.[0-9]{2})?)", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return self.normalize_amount(match.group(1))

    def _infer_currency(self, text: str) -> Optional[str]:
        if "INR" in text.upper() or "₹" in text or "(`)" in text:
            return "₹ (INR)"
        if "JIO" in text.upper() or "AIRFIBER" in text.upper():
            return "₹ (INR)"
        if "$" in text or "USD" in text.upper():
            return "USD"
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_mobile(self, text: str) -> Optional[str]:
        match = re.search(r"(?:Registered\s+Mobile(?:\s+Number)?\s*:?\s*)(\+?[0-9][0-9\s-]{9,})", text, re.IGNORECASE)
        return re.sub(r"\s+", "", match.group(1)) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        match = re.search(r"Phone\s*:\s*(\+?[0-9][0-9\s().-]{7,})", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _estimate_confidence(self, normalized_facts: Dict[str, Any]) -> float:
        if not normalized_facts:
            return 0.65
        confidence = 0.7 + min(len(normalized_facts), 10) * 0.027
        return round(min(confidence, 0.97), 2)

    def _first_non_empty_line(self, text: str) -> Optional[str]:
        for line in text.splitlines():
            if line.strip():
                return line.strip()
        return None

    def _infer_vendor(self, title: str, raw_text: str) -> str:
        combined = f"{title}\n{raw_text}".upper()
        if "JIO" in combined:
            return "Reliance Jio Infocomm Ltd"
        if "SAMSUNG" in combined:
            return "Samsung"
        if "DYSON" in combined:
            return "Dyson"
        return title.split()[0] if title else "Unknown"
