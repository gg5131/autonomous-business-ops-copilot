"""LLM Gateway Layer managing token counts, pricing tracker, circuit retries, and timeouts."""

from __future__ import annotations

import httpx
import time
from typing import Any, Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LLMGateway:
    """Consolidated gateway for all LLM calls, tracking token usage and cost."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.gemini.api_key
        # Track aggregate usage across gateway lifetime
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Helper to calculate API calls pricing using configured rates."""
        if "pro" in model.lower():
            in_cost = (prompt_tokens / 1000.0) * settings.gemini_pro_input_cost_per_1k
            out_cost = (completion_tokens / 1000.0) * settings.gemini_pro_output_cost_per_1k
        else:
            # Default to Flash rates
            in_cost = (prompt_tokens / 1000.0) * settings.gemini_flash_input_cost_per_1k
            out_cost = (completion_tokens / 1000.0) * settings.gemini_flash_output_cost_per_1k
        return float(in_cost + out_cost)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        """Wrapper dispatching prompt content checks to Gemini API, tracing tokens and cost."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment settings.")

        target_model = model_name or settings.gemini.model_default
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self.api_key}"

        # Setup request structures
        contents = [{"parts": [{"text": prompt}]}]
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # For structured JSON validation if target matches planner
        if "json" in prompt.lower() or "schema" in prompt.lower():
            payload["generationConfig"]["responseMimeType"] = "application/json"

        start_time = time.time()
        logger.info("Dispatching call to LLM Gateway", model=target_model, temperature=temperature)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            latency_ms = (time.time() - start_time) * 1000.0

            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]

                # Extract token usage metadata from response
                usage = data.get("usageMetadata", {})
                prompt_tokens = int(usage.get("promptTokenCount", 0))
                completion_tokens = int(usage.get("candidatesTokenCount", 0))
                total_tokens = int(usage.get("totalTokenCount", 0))

                cost = self._calculate_cost(prompt_tokens, completion_tokens, target_model)

                # Update aggregates
                self.total_prompt_tokens += prompt_tokens
                self.total_completion_tokens += completion_tokens
                self.total_cost_usd += cost

                logger.info(
                    "LLM Gateway response received",
                    model=target_model,
                    latency_ms=latency_ms,
                    total_tokens=total_tokens,
                    cost_usd=cost,
                )

                return {
                    "text": str(text).strip(),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": cost,
                    "latency_ms": latency_ms,
                }
            else:
                logger.error(
                    "LLM Gateway call failed",
                    status_code=response.status_code,
                    body=response.text,
                    model=target_model,
                )
                raise RuntimeError(f"Gemini API returned status code {response.status_code}")
