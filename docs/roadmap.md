# Development Roadmap & Known Limitations

## Future Improvements
- **Redis Memory Cache**: Swap out the default SQLite caching mechanism in EmbeddingService with a high-throughput Redis instance.
- **Tesseract Fine-Tuning**: Optimize OCR parsing capabilities on custom company tables and invoices.
- **Multimodal Agents**: Upgrade sub-agents to accept and process image/video assets directly using Gemini-2.5-flash vision capabilities.
- **Advanced Graph Algorithms**: Integrate NetworkX PageRank metrics to weight node traversals relative to global centrality scores.

## Known Limitations
- **Cold Boot Latency**: Initial SentenceTransformer model initialization takes 3-5 seconds depending on hardware capacity.
- **Graph Schema Locks**: Simultaneous Neo4j writes during heavy parallel load runs may trigger locks warning.
- **SQLite Concurrency**: Development fallbacks run on single-thread SQLite databases and do not support highly concurrent multi-write operations.
