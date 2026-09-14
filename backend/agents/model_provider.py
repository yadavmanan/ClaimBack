"""Shared Strands model selection for ClaimBack agents.

Prefers an OpenAI-compatible endpoint when one is configured in settings.
That matches local setups where Bedrock is exposed through a Mantle/proxy style
`OPENAI_BASE_URL` + `OPENAI_API_KEY` pair rather than native Bedrock Runtime.
"""
from typing import Any

from backend.config import settings

try:
    from strands.models import BedrockModel, OpenAIModel
except ImportError:
    BedrockModel = None
    OpenAIModel = None


def create_strands_model(
    model_id: str | None = None,
    region_name: str | None = None,
    temperature: float = 0.1,
) -> Any:
    selected_model_id = settings.openai_model_id or model_id or settings.bedrock_model_id
    selected_region = region_name or settings.aws_region
    has_openai_compat = bool(settings.openai_base_url) and bool(settings.openai_api_key)

    if has_openai_compat:
        if OpenAIModel is None:
            return None
        return OpenAIModel(
            model_id=selected_model_id,
            client_args={
                "api_key": settings.openai_api_key,
                "base_url": settings.openai_base_url,
                "project": settings.openai_project_id or None,
            },
            params={"temperature": temperature},
            stream=False,
        )

    if BedrockModel is None:
        return None

    return BedrockModel(
        model_id=selected_model_id,
        region_name=selected_region,
        temperature=temperature,
    )