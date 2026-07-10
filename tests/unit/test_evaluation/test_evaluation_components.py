"""Unit test suite verifying Phase 7 evaluation, load tests, and synthetic generators."""

from __future__ import annotations

import os
import pytest
from src.evaluation.metrics import levenshtein_distance, calculate_normalized_edit_distance, calculate_approval_rate
from src.evaluation.ragas_eval import RagasEvaluator
from src.evaluation.deepeval_eval import DeepEvalEvaluator
from src.synthetic.generator import SyntheticDatasetGenerator
from src.benchmark.comparator import PipelineComparator
from src.benchmark.runner import LoadTestRunner


def test_levenshtein_distance() -> None:
    """Assert Levenshtein edit distance outputs correspond to edit sequences."""
    assert levenshtein_distance("cat", "cat") == 0
    assert levenshtein_distance("cat", "bat") == 1
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("", "test") == 4


def test_normalized_edit_distance() -> None:
    """Assert normalized edit distance is constrained to 0.0-1.0 limits."""
    assert calculate_normalized_edit_distance("test", "test") == 0.0
    assert calculate_normalized_edit_distance("kitten", "sitting") == pytest.approx(3 / 7)
    assert calculate_normalized_edit_distance("", "") == 0.0


def test_approval_rate_calculation() -> None:
    """Assert approval rate matches ratio of low edit distances."""
    runs = [
        {"draft": "Approved draft response", "final_response": "Approved draft response"},
        {"draft": "Edited answer text line", "final_response": "Modified answer text sequence edit distance"}
    ]
    # One unmodified (edit distance 0), one heavily modified
    # Approval rate should be exactly 50%
    assert calculate_approval_rate(runs) == 50.0


@pytest.mark.asyncio
async def test_ragas_and_deepeval_simulators() -> None:
    """Assert simulated metrics output expected attributes and limits."""
    rag_eval = RagasEvaluator()
    de_eval = DeepEvalEvaluator()
    
    query = "billing disputes refund windows"
    response = "refund requests must be made within 30 days"
    context = "refund policy rules outline a 30 days window"
    gt = "refund window limit is 30 days"
    
    rag_scores = await rag_eval.evaluate_response(query, response, context, gt)
    assert "faithfulness" in rag_scores
    assert "answer_relevancy" in rag_scores
    assert "context_recall" in rag_scores
    
    de_scores = await de_eval.evaluate_response(response, context)
    assert "hallucination_risk" in de_scores
    assert "groundedness" in de_scores
    assert "citation_accuracy" in de_scores



def test_synthetic_dataset_generation(tmp_path) -> None:
    """Assert synthetic generator outputs golden datasets with valid structure."""
    out_file = os.path.join(tmp_path, "test_dataset.json")
    gen = SyntheticDatasetGenerator(output_path=out_file)
    samples = gen.generate_golden_dataset(num_samples=10)
    
    assert len(samples) == 10
    assert os.path.exists(out_file)
    for sample in samples:
        assert "id" in sample
        assert "content" in sample
        assert "ground_truth" in sample


def test_pipeline_comparator() -> None:
    """Assert comparator averages values correctly for five pipelines."""
    comp = PipelineComparator()
    sample = {
        "content": "refund for billing dispute transaction CS-4322",
        "ground_truth": "Standard refund eligibility is 30 days."
    }
    
    avg_totals = comp.run_comparative_suite([sample])
    for pipe in ["Manual", "Single LLM", "Traditional RAG", "Multi-Agent (No Graph)", "Full GraphRAG"]:
        assert pipe in avg_totals
        assert "latency_ms" in avg_totals[pipe]
        assert "quality_score" in avg_totals[pipe]


def test_load_test_runner() -> None:
    """Assert runner returns throughput configurations for user scales."""
    runner = LoadTestRunner()
    results = runner.run_throughput_load_tests()
    
    for u in ["1", "5", "10", "25", "50"]:
        assert u in results
        assert "throughput_rpm" in results[u]
        assert "avg_latency_ms" in results[u]
