"""
ClaimBack - Subscription Auditor Agent
Specialized Strands agent for interpreting subscription price change notices, computing financial impact,
and proposing action options (cancel, downgrade, retain).
"""
import json
from typing import Dict, Any, Optional
from backend.agents.model_provider import create_strands_model
from backend.config import DEFAULT_MODEL_ID, DEFAULT_REGION, DEFAULT_TEMPERATURE
from backend.tools.ledger_tools import detect_price_change_candidates, record_ledger_event

try:
    from strands import Agent
except ImportError:
    Agent = None

SUBSCRIPTION_AUDITOR_PROMPT = """
You are the SubscriptionAuditorAgent for ClaimBack, an autonomous financial recovery system.

Your responsibilities:
1. Analyze subscription price change notices, emails, or ledger transaction deltas.
2. Calculate monthly and annual price increases and financial impact.
3. Identify effective dates, cancellation deadlines, and contract terms.
4. Recommend concrete options for the user: cancel, downgrade, negotiate, or retain.
5. Use available tools to fetch candidate price change transactions when needed.

Guidelines:
- Maintain low temperature and strictly grounded factual analysis.
- Output clear financial metrics (previous_price, new_price, delta_amount, annual_impact).
- Never hallucinate terms or prices not backed by inputs.
"""


def create_subscription_auditor_agent(
    model_id: str = DEFAULT_MODEL_ID,
    region_name: str = DEFAULT_REGION,
    temperature: float = DEFAULT_TEMPERATURE,
) -> Optional[Agent]:
    """Factory function for SubscriptionAuditorAgent."""
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
        system_prompt=SUBSCRIPTION_AUDITOR_PROMPT,
        tools=[detect_price_change_candidates, record_ledger_event],
        callback_handler=None,
    )


def audit_subscription_price_change(
    user_id: str,
    notice_text: str,
    transaction_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper function to run the SubscriptionAuditorAgent deterministically."""
    agent = create_subscription_auditor_agent()
    if agent is None:
        return {"status": "ERROR", "message": "Strands SDK not installed or agent unavailable"}
    prompt = f"User ID: {user_id}\nNotice Text:\n{notice_text}"
    if transaction_id:
        prompt += f"\nAssociated Transaction ID: {transaction_id}"
    
    response = agent(prompt)
    return {
        "status": "SUCCESS",
        "result": response.message if hasattr(response, "message") else str(response),
    }
