"""Evaluation metrics calculations helper including Levenshtein edit distance."""

from __future__ import annotations

import numpy as np


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
        
    if len(s2) == 0:
        return len(s1)
        
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]


def calculate_normalized_edit_distance(original: str, edited: str) -> float:
    """Calculates edit distance normalized by maximum string length (ranges 0.0 to 1.0)."""
    max_len = max(len(original), len(edited))
    if max_len == 0:
        return 0.0
    return float(levenshtein_distance(original, edited)) / max_len


def calculate_approval_rate(runs_results: list[dict[str, any]]) -> float:
    """Computes percentage of runs approved without any manual edits."""
    if not runs_results:
        return 0.0
    unmodified = 0
    for run in runs_results:
        original = run.get("draft", "")
        edited = run.get("final_response", original)
        if calculate_normalized_edit_distance(original, edited) < 0.05:  # Tolerance threshold
            unmodified += 1
    return (unmodified / len(runs_results)) * 100.0
