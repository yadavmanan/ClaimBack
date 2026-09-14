"""
EvidencePlannerAgent factory using Strands Agent SDK.
Determines required evidence documents for an identified opportunity.
"""
from backend.agents.model_provider import create_strands_model
from backend.tools.evidence_tools import check_evidence_completeness

try:
    from strands import Agent
except ImportError:
    Agent = None


def create_evidence_planner_agent() -> Agent:
    if Agent is None:
        return None
    model = create_strands_model(temperature=0.1)
    if model is None:
        return None
    system_prompt = """You are EvidencePlannerAgent.
Identify missing documentation needed to satisfy policy claim requirements.
Generate structured evidence checklists."""
    return Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[check_evidence_completeness],
        callback_handler=None
    )
