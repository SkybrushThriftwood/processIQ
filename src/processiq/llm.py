"""Centralized LLM factory for ProcessIQ.

All LLM calls should go through this module to ensure consistent
configuration, logging, and error handling across the application.

Usage:
    from processiq.llm import get_chat_model

    # For general chat/generation
    model = get_chat_model()
    response = model.invoke([HumanMessage(content="...")])

    # For task-specific model (uses per-task config from settings)
    from processiq.config import TASK_ANALYSIS
    model = get_chat_model(task=TASK_ANALYSIS)
    response = model.invoke([HumanMessage(content="...")])

    # For structured output (Pydantic model response)
    from processiq.models import SomeSchema
    structured = get_chat_model().with_structured_output(SomeSchema)
    result = structured.invoke([HumanMessage(content="...")])

    # Override provider/model for specific calls (overrides task config too)
    model = get_chat_model(provider="openai", model="gpt-4o")
"""

import logging

from langchain_core.language_models import BaseChatModel

from processiq.config import settings
from processiq.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def get_chat_model(
    *,
    task: str | None = None,
    analysis_mode: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> BaseChatModel:
    """Get a LangChain chat model based on configuration.

    Resolution order (first non-None wins):
    1. Explicit parameters (provider, model, temperature)
    2. Analysis mode preset (if mode and task provided)
    3. Task-specific env var config
    4. Global settings (llm_provider, llm_model, llm_temperature)

    Args:
        task: Task name for task-specific config (extraction, clarification, etc.).
        analysis_mode: Analysis mode preset (cost_optimized, balanced, deep_analysis).
        provider: Override the configured provider ("anthropic", "openai", "ollama").
        model: Override the configured model.
        temperature: Override the configured temperature.

    Returns:
        A LangChain BaseChatModel instance.

    Raises:
        ConfigurationError: If the provider is not supported or API key is missing.
    """
    # Get resolved config (applies analysis mode, provider, and task overrides)
    resolved_provider, resolved_model, resolved_temp = settings.get_resolved_config(
        task=task, analysis_mode=analysis_mode, provider=provider
    )

    # Apply explicit overrides (highest priority)
    provider = provider or resolved_provider
    model = model or resolved_model
    temperature = temperature if temperature is not None else resolved_temp

    task_info = f" (task={task})" if task else ""
    mode_info = f" [mode={analysis_mode}]" if analysis_mode else ""
    logger.info(
        "Using LLM: %s/%s (temperature=%.1f)%s%s",
        provider,
        model,
        temperature,
        task_info,
        mode_info,
    )

    if provider == "anthropic":
        return _get_anthropic_model(model, temperature)
    elif provider == "openai":
        return _get_openai_model(model, temperature)
    elif provider == "ollama":
        return _get_ollama_model(model, temperature)
    else:
        raise ConfigurationError(
            message=f"Unsupported LLM provider: {provider}",
            config_key="llm_provider",
            user_message=f"Provider '{provider}' is not supported. Use 'anthropic', 'openai', or 'ollama'.",
        )


def _get_anthropic_model(model: str, temperature: float) -> BaseChatModel:
    """Create an Anthropic chat model."""
    from langchain_anthropic import ChatAnthropic

    api_key = settings.anthropic_api_key.get_secret_value()
    if not api_key:
        raise ConfigurationError(
            message="Anthropic API key not configured",
            config_key="anthropic_api_key",
            user_message="Please set ANTHROPIC_API_KEY in your environment or .env file.",
        )

    return ChatAnthropic(
        model=model,  # pyright: ignore[reportCallIssue]
        api_key=api_key,
        temperature=temperature,
        max_tokens=4096,  # pyright: ignore[reportCallIssue]
    )


def _get_openai_model(model: str, temperature: float) -> BaseChatModel:
    """Create an OpenAI chat model."""
    from langchain_openai import ChatOpenAI

    api_key = settings.openai_api_key.get_secret_value()
    if not api_key:
        raise ConfigurationError(
            message="OpenAI API key not configured",
            config_key="openai_api_key",
            user_message="Please set OPENAI_API_KEY in your environment or .env file.",
        )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=4096,  # pyright: ignore[reportCallIssue]
    )


def _get_ollama_model(model: str, temperature: float) -> BaseChatModel:
    """Create an Ollama chat model (local LLM)."""
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model,
        base_url=settings.ollama_base_url,
        temperature=temperature,
    )
