"""Query Engine executing intent detection and query expansion via Gemini API with rule-based fallback."""

from __future__ import annotations

import httpx
from typing import List, Literal

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class QueryEngineService:
    """Manages search intents and expands search queries using LLM or fallback heuristics."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.gemini.api_key
        self.model = settings.gemini.model_default

    async def _call_gemini(self, prompt: str) -> str:
        """Helper to invoke Gemini API generateContent endpoint."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return str(text).strip()
            else:
                logger.error("Gemini API call failed", status_code=response.status_code, body=response.text)
                raise RuntimeError(f"Gemini API returned status code {response.status_code}")

    async def detect_intent(self, query: str) -> Literal["lookup", "summary"]:
        """Determine if the user query is a specific detail search (lookup) or high-level overview (summary)."""
        logger.info("Detecting search query intent", query=query)
        if not self.api_key:
            # Rule-based fallback
            return self._detect_intent_fallback(query)

        prompt = (
            "Analyze the search query below and classify it into one of two intents:\n"
            "- 'lookup': searching for specific policies, facts, procedures, contacts, numbers, or details.\n"
            "- 'summary': searching for overviews, reports, histories, overall trends, aggregates, or themes.\n\n"
            f"Query: \"{query}\"\n\n"
            "Respond ONLY with one word: 'lookup' or 'summary'."
        )

        try:
            response_text = await self._call_gemini(prompt)
            cleaned = response_text.lower().strip().replace("'", "").replace('"', "")
            if cleaned in ["lookup", "summary"]:
                return cleaned  # type: ignore
            return "lookup"
        except Exception as e:
            logger.warn("Gemini intent detection failed; using fallback heuristics.", error=str(e))
            return self._detect_intent_fallback(query)

    def _detect_intent_fallback(self, query: str) -> Literal["lookup", "summary"]:
        """Fallback check for summary indicator keywords in the query."""
        keywords = ["summary", "overall", "report", "aggregate", "history", "trend", "overview", "summarize"]
        normalized = query.lower()
        if any(kw in normalized for kw in keywords):
            return "summary"
        return "lookup"

    async def expand_query(self, query: str, num_queries: int = 3) -> List[str]:
        """Generate alternative variations of the query to expand retrieval context."""
        logger.info("Expanding query variations", query=query, num_queries=num_queries)
        if not self.api_key:
            return self._expand_query_fallback(query)

        prompt = (
            f"Generate exactly {num_queries} alternative variations of the search query below.\n"
            "These variations should capture synonyms, related terms, and different phrasing "
            "to maximize search recall in a retrieval engine.\n\n"
            f"Query: \"{query}\"\n\n"
            "Return the variations separated ONLY by newlines. Do not add numbers, bullet points, or comments."
        )

        try:
            response_text = await self._call_gemini(prompt)
            queries = [q.strip() for q in response_text.split("\n") if q.strip()]
            # Filter bullet/number prefixes if any escaped the format instructions
            clean_queries: List[str] = []
            for q in queries:
                cleaned = re.sub(r"^\d+[\.\-\s]+", "", q).strip().replace('"', "")
                if cleaned:
                    clean_queries.append(cleaned)
            return clean_queries[:num_queries]
        except Exception as e:
            logger.warn("Gemini query expansion failed; using fallback heuristics.", error=str(e))
            return self._expand_query_fallback(query)

    def _expand_query_fallback(self, query: str) -> List[str]:
        """Simple token-based fallback query expansion."""
        # Returns the original query and simple sub-queries or base splits
        variations = [query]
        words = query.split()
        if len(words) > 3:
            # First half
            variations.append(" ".join(words[: len(words) // 2]))
            # Second half
            variations.append(" ".join(words[len(words) // 2 :]))
        else:
            variations.append(f"{query} details")
            variations.append(f"retrieve {query}")
        return variations
