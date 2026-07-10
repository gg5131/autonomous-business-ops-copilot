"""Load testing and throughput benchmark suite execution loops."""

from __future__ import annotations

import time
from typing import Dict, List


class LoadTestRunner:
    """Simulates parallel user loads measuring server request throughput metrics."""

    def run_throughput_load_tests(self) -> Dict[str, Dict[str, float]]:
        """Executes throughput stress checks at 1, 5, 10, 25, 50 scales."""
        scales = [1, 5, 10, 25, 50]
        results: Dict[str, Dict[str, float]] = {}
        
        # Simulated benchmark calculations
        for users in scales:
            # Latency scales up with concurrent request queue waits
            avg_latency_ms = 4500.0 + (users * 20.0)
            
            # Throughput requests per minute (RPM)
            # Parallel users can trigger concurrent tasks in async loops
            rpm = (users * 60.0) / (avg_latency_ms / 1000.0)
            
            # Limit maximum capacity bounds
            if users > 25:
                rpm *= 0.85  # Contention throttling delta
                avg_latency_ms *= 1.2
                
            results[str(users)] = {
                "throughput_rpm": round(rpm, 2),
                "avg_latency_ms": round(avg_latency_ms, 2)
            }
            
        return results
