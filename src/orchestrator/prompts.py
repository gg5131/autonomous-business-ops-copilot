"""Prompt registry loader externalizing agent prompt strings from Python modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

PROMPT_PATH = Path("./configs/prompts.yaml")


class PromptRegistry:
    """Loads system and user prompt templates dynamically from configs/prompts.yaml."""

    def __init__(self, prompt_path: Path | str | None = None) -> None:
        self.prompt_path = Path(prompt_path or PROMPT_PATH)
        self._prompts: Dict[str, str] = {}
        self.load_prompts()

    def load_prompts(self) -> None:
        """Loads prompt configurations, using rule-based fallbacks if file is missing."""
        if not self.prompt_path.exists():
            logger.warn("prompts.yaml not found; loading default fallback templates.", path=str(self.prompt_path))
            self._prompts = {
                "planner_system_prompt": "You are the Planner Agent. Construct a dynamic execution plan.",
                "triage_system_prompt": "You are the Triage Agent. Classify ticket category and urgency.",
                "research_system_prompt": "You are the Research Agent. Summarize findings.",
                "policy_system_prompt": "You are the Policy Agent. Extract policy details.",
                "draft_system_prompt": "You are the Draft Agent. Formulate responses.",
                "fact_checker_system_prompt": "You are the Fact Checker Agent. Verify response claims.",
            }
            return

        try:
            with open(self.prompt_path, mode="r", encoding="utf-8") as f:
                self._prompts = yaml.safe_load(f) or {}
            logger.info("Successfully loaded prompts configuration registry.", templates_loaded=len(self._prompts))
        except Exception as e:
            logger.error("Failed to parse prompts configuration file", error=str(e))
            raise

    def get_prompt(self, name: str) -> str:
        """Fetch template by name with fallback configuration strings."""
        val = self._prompts.get(name)
        if not val:
            logger.warn("Prompt template key not found; returning fallback stub.", key=name)
            return f"You are the {name.replace('_system_prompt', '').title()} Agent."
        return val
