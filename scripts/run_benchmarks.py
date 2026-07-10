#!/usr/bin/env python
"""Master benchmark execution entrypoint running dataset generation, evaluations, and reports."""

import os
import sys

# Ensure project root is in Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.synthetic.generator import SyntheticDatasetGenerator
from src.benchmark.comparator import PipelineComparator
from src.benchmark.runner import LoadTestRunner
from src.benchmark.report import ReportCompiler


def main() -> None:
    """Executes the complete benchmark suite."""
    print("[START] Starting Benchmark Suite Phase 7...")
    
    # 1. Dataset Generation
    print("[DATASET] Generating Synthetic golden dataset samples...")
    gen = SyntheticDatasetGenerator()
    dataset = gen.generate_golden_dataset(num_samples=50)
    print(f"[SUCCESS] Generated {len(dataset)} ticket cases under evaluation/golden_dataset/.")
    
    # 2. Pipeline Evaluations
    print("[EVAL] Running 5-Way comparisons pipeline run checks...")
    comparator = PipelineComparator()
    totals = comparator.run_comparative_suite(dataset)
    print("[SUCCESS] Finished comparisons averages calculations.")
    
    # 3. Load Testing Throughputs
    print("[LOAD] Running concurrent throughput load testing benchmarks...")
    load_runner = LoadTestRunner()
    load_stats = load_runner.run_throughput_load_tests()
    print("[SUCCESS] Completed load tests simulation.")
    
    # 4. Reports Compilation
    print("[REPORT] Compiling Markdown tables and summary JSON files...")
    compiler = ReportCompiler()
    compiler.compile_reports(totals, load_stats)
    print("[DONE] Benchmark suite run completed successfully!")



if __name__ == "__main__":
    main()
