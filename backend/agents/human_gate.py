"""
HumanGateAgent factory using Strands Agent SDK.
Prepares executive approval summaries for the user before any claim is submitted.
"""
from backend.agents.model_provider import create_strands_model

try:
    from strands import Agent
except ImportError:
    Agent = None


def create_human_gate_agent() -> Agent:
    if Agent is None:
        return None
    model = create_strands_model(temperature=0.1)
    if model is None:
        return None
    system_prompt = """You are HumanGateAgent.
Summarize claim opportunities into clear, concise, 1-click user approval cards.
Highlight estimated recovery value, recipient, and required user action."""
    return Agent(
        model=model,
        system_prompt=system_prompt,
        callback_handler=None
    )
