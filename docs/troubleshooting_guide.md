# Troubleshooting Guide

Solutions for common system issues.

## 🛠️ SQLite Embedding Cache Locks
- **Issue**: SQLite database locks during concurrent batch writes.
- **Solution**: Configure a transaction timeout in `sqlite3.connect` or upgrade to the pluggable Redis cache model.

## 🕸️ Neo4j Bolt Connection Failures
- **Issue**: System cannot boot or connect to `bolt://localhost:7687`.
- **Solution**: Verify that Docker containers are active (`docker ps`) and constraints have been seeded using `scripts/setup_neo4j.py`.

## 🧠 Cold Boot Model Initialization Lag
- **Issue**: The first ticket run takes more than 10 seconds.
- **Solution**: The local SentenceTransformer model is downloading on first run. Pre-download the model in Docker builds.
