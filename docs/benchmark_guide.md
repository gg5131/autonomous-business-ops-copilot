# Benchmark Guide

Overview of performance benchmark setups.

## ⚡ Throughput & Stress Load Testing
- Configures parallel mock user threads executing batches of 50 ticket operations concurrently.
- Measures maximum Capacity Limits (RPM) and response time latency curves.

## 📊 5-Way Pipeline Comparisons
Metrics are computed across five layouts:
1. **Manual Baseline**: Extrapolates human agent processing speeds.
2. **Single LLM**: Tests direct Gemini requests without indexing or retrieval context.
3. **Traditional RAG**: ChromaDB Vector dense searches feeding Gemini.
4. **Multi-Agent (No Graph)**: Orchestration loops using only vector dense references.
5. **Full GraphRAG**: The complete GraphRAG multi-agent implementation.
