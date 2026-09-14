"""Model factory: one place that decides which LLM backs every Strands agent."""

from __future__ import annotations

from functools import lru_cache

from strands.models import Model

from ..config import settings


@lru_cache(maxsize=4)
def get_model(role: str = "default") -> Model:
    provider = settings.model_provider.lower()
    if provider == "anthropic":
        from strands.models.anthropic import AnthropicModel

        return AnthropicModel(
            model_id=settings.anthropic_model_id, max_tokens=settings.model_max_tokens
        )
    if provider in ("openai", "chatgpt"):
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            model_id=settings.openai_model_id,
            params={"max_completion_tokens": settings.model_max_tokens},
        )
    if provider == "bedrock":
        # Used by the deployed AgentCore runtime (AWS credentials from the role). Not offered in
        # the dashboard, which asks for an Anthropic or OpenAI key instead.
        from strands.models import BedrockModel

        return BedrockModel(
            model_id=settings.bedrock_model_id,
            region_name=settings.aws_region,
            max_tokens=settings.model_max_tokens,
        )
    raise ValueError(f"Unknown RH_MODEL_PROVIDER={settings.model_provider!r}")
