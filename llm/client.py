import asyncio
import logging
from typing import Optional, List, Dict, Any, Union, AsyncGenerator
import httpx
import openai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from core.settings import settings
from core.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMClient:
    """Stateless LLM client with retry, streaming, and token counting.
    支持多个 Provider: OpenAI/DeepSeek/豆包
    """

    def __init__(self):
        base_url = getattr(settings, 'openai_base_url', None) or None
        timeout = getattr(settings, 'llm_timeout', 60) or 60
        
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=base_url,
            timeout=timeout
        )
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIConnectionError, openai.APITimeoutError, openai.RateLimitError, httpx.ConnectTimeout)),
        before_sleep=lambda retry_state: logger.warning(f"Retrying LLM call: {retry_state.attempt_number}")
    )
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        response_format: Optional[Dict] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Generate a response from the LLM."""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format

            if stream:
                return await self._stream_generate(**kwargs)
            else:
                response = await self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
        except Exception as e:
            logger.exception("LLM generation failed")
            raise LLMError(f"LLM generation failed: {e}") from e

    async def _stream_generate(self, **kwargs):
        response = await self.client.chat.completions.create(**kwargs, stream=True)
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def count_tokens(self, text: str) -> int:
        """Approximate token count using tiktoken if available."""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except ImportError:
            # Fallback: rough estimate (4 chars per token)
            return len(text) // 4

    async def structured_output(self, messages: List[Dict], schema: Dict) -> Dict:
        """Request structured JSON output."""
        response = await self.generate(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse JSON response: {e}")


llm_client = LLMClient()


# 兼容函数

async def chat_completion(messages: List[Dict], **kwargs):
    """兼容函数：同步聊天完成"""
    return await llm_client.generate(messages, **kwargs)

async def chat_completion_json(messages: List[Dict], **kwargs):
    """兼容函数：JSON 格式返回"""
    return await llm_client.structured_output(messages, {})

async def stream_completion(messages: List[Dict], **kwargs):
    """兼容函数：流式输出"""
    return await llm_client.generate(messages, stream=True, **kwargs)
