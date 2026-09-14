"""
ActionDrafterAgent factory using Strands Agent SDK.
Drafts formal claim submission packages and letters.
"""
from backend.agents.model_provider import create_strands_model

try:
    from strands import Agent
except ImportError:
    Agent = None


def create_drafter_agent() -> Agent:
    if Agent is None:
        return None
    model = create_strands_model(temperature=0.3)
    if model is None:
        return None
    system_prompt = """You are ActionDrafterAgent.
Generate formal, polite, and comprehensive claim submission letters.
Include exact purchase dates, amounts, policy clauses, and evidence attachments."""
    return Agent(
        model=model,
        system_prompt=system_prompt,
        callback_handler=None
    )
