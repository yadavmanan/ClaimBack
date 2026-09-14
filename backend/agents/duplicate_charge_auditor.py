"""
ClaimBack - Duplicate Charge Auditor Agent
Specialized Strands agent for interpreting potential duplicate transactions, calculating dispute amounts,
and drafting merchant support dispute requests.
"""
import json
from typing import Dict, Any, Optional
from backend.agents.model_provider import create_strands_model
from backend.config import DEFAULT_MODEL_ID, DEFAULT_REGION, DEFAULT_TEMPERATURE
from backend.tools.ledger_tools import detect_duplicate_candidates

try:
    from strands import Agent
except ImportError:
    Agent = None

DUPLICATE_AUDITOR_PROMPT = """
You are the DuplicateChargeAuditorAgent for ClaimBack, an autonomous financial recovery system.

Your responsibilities:
1. Analyze suspect duplicate or near-duplicate transactions from card feeds or bank ledgers.
2. Verify transaction metadata (merchant name, amount, timestamp proximity, transaction reference).
3. Evaluate whether the charge is a true duplicate versus a legitimate recurring charge or multi-item purchase.
4. Calculate the total refundable duplicate amount.
5. Prepare a structured dispute summary and draft merchant support outreach message.

Guidelines:
- Ground all findings strictly in provided transaction records.
- Clearly state the duplicate confidence score and reason for potential dispute.
- Output clear transaction pairs and delta calculations.
"""


def create_duplicate_charge_auditor_agent(
    model_id: str = DEFAULT_MODEL_ID,
    region_name: str = DEFAULT_REGION,
    temperature: float = DEFAULT_TEMPERATURE,
) -> Optional[Agent]:
    """Factory function for DuplicateChargeAuditorAgent."""
    if Agent is None:
        return None
    model = create_strands_model(
        model_id=model_id,
        region_name=region_name,
        temperature=temperature,
    )
    if model is None:
        return None
    return Agent(
        model=model,
        system_prompt=DUPLICATE_AUDITOR_PROMPT,
        tools=[detect_duplicate_candidates],
        callback_handler=None,
    )


def audit_duplicate_transactions(
    user_id: str,
    raw_transaction_data: str,
) -> Dict[str, Any]:
    """Helper function to run the DuplicateChargeAuditorAgent deterministically."""
    agent = create_duplicate_charge_auditor_agent()
    if agent is None:
        return {"status": "ERROR", "message": "Strands SDK not installed or agent unavailable"}
    prompt = f"User ID: {user_id}\nTransaction Data:\n{raw_transaction_data}"
    
    response = agent(prompt)
    return {
        "status": "SUCCESS",
        "result": response.message if hasattr(response, "message") else str(response),
    }
