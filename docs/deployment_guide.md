# Deployment Guide

Detailed configurations for containerized production setups.

## 🐳 Docker Container Deployment

The project provides a multi-container `docker-compose.yml` defining the following services:
- **FastAPI Backend Application**: The core reasoning and retrieval routing API service.
- **Neo4j Community Graph Database**: High-speed graph entities search engine.
- **PostgreSQL Database**: Persistent storage for agent state checkpointers.

### Launch Containers
1. Build and boot up all instances in detached mode:
   ```bash
   docker-compose up --build -d
   ```
2. Verify services status:
   ```bash
   docker-compose ps
   ```
3. Run initialization scripts to seed the graph database constraints:
   ```bash
   docker-compose exec backend python scripts/setup_neo4j.py
   ```
4. Access the Streamlit dashboard on port `8501`.
