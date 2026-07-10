"""Context Builder Service assembling knowledge, memory, and token budgeting limits."""

from __future__ import annotations

from typing import Any, Dict, List


class ContextBuilder:
    """Consolidates retrieved contexts and memory inputs into clean system prompts under budget limits."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token length using standard character ratio (1 token ~ 4 chars)."""
        if not text:
            return 0
        return len(text) // 4

    def build_context(
        self,
        retrieval_context: List[Dict[str, Any]],
        memory_context: List[Dict[str, Any]],
        max_tokens: int = 4000,
    ) -> str:
        """Merge contexts into a clean formatted string, respecting token budgets."""
        lines = []

        # 1. Format Historical memory context
        if memory_context:
            lines.append("## Historical Customer Context & Memories")
            for entry in memory_context:
                entry_str = f"- Ticket: {entry.get('ticket_title')}\n  Response: {entry.get('response')}"
                if self.estimate_tokens("\n".join(lines) + "\n" + entry_str) < (max_tokens // 3):
                    lines.append(entry_str)
                else:
                    lines.append("- [Memory truncated due to token budget]")
                    break
            lines.append("")

        # 2. Format Retrieval search context
        if retrieval_context:
            lines.append("## Retrieved Reference Policies & Knowledge Chunks")
            for doc in retrieval_context:
                doc_str = (
                    f"### Document: {doc.get('id')}\n"
                    f"Content: {doc.get('content')}\n"
                    f"Source: {doc.get('metadata', {}).get('source', 'unknown')}\n"
                )
                if self.estimate_tokens("\n".join(lines) + "\n" + doc_str) < max_tokens:
                    lines.append(doc_str)
                else:
                    lines.append("### [Additional reference documents truncated due to token budget]")
                    break

        return "\n".join(lines).strip()
