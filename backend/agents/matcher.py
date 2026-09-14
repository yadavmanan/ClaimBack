"""
PolicyMatcherAgent factory using Strands Agent SDK.
Matches extracted purchase facts against active coverage policies.
"""
from backend.agents.model_provider import create_strands_model
from backend.tools.policy_tools import find_matching_policies

try:
    from strands import Agent
except ImportError:
    Agent = None


def create_matcher_agent() -> Agent:
    if Agent is None:
        return None
    model = create_strands_model(temperature=0.2)
    if model is None:
        return None
    system_prompt = """You are PolicyMatcherAgent.
Match purchase facts against policy coverage rules.
Evaluate coverage eligibility, max amounts, and exclusions."""
    return Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[find_matching_policies],
        callback_handler=None
    )
