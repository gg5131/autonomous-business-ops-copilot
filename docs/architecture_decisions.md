# Architectural Decisions Logs (ADR)

Documentation of core framework choices.

## 🏛️ ADR 1: LangGraph for Multi-Agent State Orchestrations
- **Decision**: Adopted LangGraph over sequential chains.
- **Justification**: LangGraph supports thread-safe state checkpointers and manual review interrupts. It is ideal for complex loops (e.g. going back to the planner after a human rejection).

## 📊 ADR 2: Pluggable SQLite Disk Cache for EmbeddingService
- **Decision**: Default to SQLite for embedding cache storage.
- **Justification**: Eliminates redundant remote LLM call latencies for query expansions, saving costs and running without external network requirements in local environments.

## 🔍 ADR 3: Hybrid Retrieval Blending
- **Decision**: Combine BM25 lexical keyword matches, ChromaDB vector dense clusters, and Neo4j entities traversals.
- **Justification**: Maximizes semantic coverage while retaining high keyword precision for item catalog codes.
