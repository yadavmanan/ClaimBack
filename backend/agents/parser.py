"""
DocumentParserAgent factory using Strands Agent SDK.
Extracted structured financial fields from OCR text.
"""
from backend.agents.model_provider import create_strands_model

try:
    from strands import Agent
except ImportError:
    Agent = None


def create_parser_agent() -> Agent:
    if Agent is None:
        return None
    model = create_strands_model(temperature=0.1)
    if model is None:
        return None
    system_prompt = """You are DocumentParserAgent.
Extract: merchant_name, transaction_date, total_amount, line_items, tax_amount, invoice_number.
Return strictly structured JSON."""
    return Agent(
        model=model,
        system_prompt=system_prompt,
        callback_handler=None
    )
