"""LLM Router service for multi-provider support"""

from typing import Optional, AsyncGenerator, List, Dict, Any
from enum import Enum
from litellm import acompletion

from app.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    CLAUDE = "claude"
    OPENAI = "openai"
    LOCAL = "local"


class LLMRouter:
    """Router for multiple LLM providers using litellm"""

    # Model mapping
    MODELS = {
        LLMProvider.CLAUDE: "anthropic/claude-sonnet-4-20250514",
        LLMProvider.OPENAI: "openai/gpt-4o",
        LLMProvider.LOCAL: "ollama/llama3",
    }

    # Fast models for intent detection
    FAST_MODELS = {
        LLMProvider.CLAUDE: "anthropic/claude-3-5-haiku-20241022",
        LLMProvider.OPENAI: "openai/gpt-4o-mini",
    }

    def __init__(self, default_provider: LLMProvider = LLMProvider.CLAUDE):
        self.default_provider = default_provider

    def get_model_name(self, provider: LLMProvider, fast: bool = False) -> str:
        """Get the model name for a provider"""
        if fast and provider in self.FAST_MODELS:
            return self.FAST_MODELS[provider]
        return self.MODELS[provider]

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        stream: bool = True,
        **kwargs
    ) -> Any:
        """
        Send a chat request to the LLM

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Specific model to use (overrides provider)
            provider: LLM provider to use
            stream: Whether to stream the response
            **kwargs: Additional arguments for the LLM

        Returns:
            LLM response or async generator if streaming
        """
        if model:
            model_name = model
        else:
            provider = provider or self.default_provider
            model_name = self.get_model_name(provider)

        return await acompletion(
            model=model_name,
            messages=messages,
            stream=stream,
            **kwargs
        )

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response

        Yields:
            Text chunks from the LLM
        """
        response = await self.chat(
            messages=messages,
            model=model,
            provider=provider,
            stream=True,
            **kwargs
        )

        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    yield delta.content

    async def chat_complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """
        Get a complete chat response (non-streaming)

        Returns:
            Complete response text
        """
        response = await self.chat(
            messages=messages,
            model=model,
            provider=provider,
            stream=False,
            **kwargs
        )

        return response.choices[0].message.content


# Global router instance
llm_router = LLMRouter(
    default_provider=LLMProvider(settings.DEFAULT_LLM_MODEL)
)