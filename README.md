# Autonomous Business Operations Copilot

An enterprise-grade, GraphRAG-powered Multi-Agent AI system with Human-in-the-Loop review, Explainability, Long-Term Memory, and Business Intelligence.

---

## 🚀 Overview

The **Autonomous Business Operations Copilot** automates complex business operations such as ticket triage, customer support, policy lookup, knowledge retrieval, response drafting, and reporting. It keeps humans in control by requiring manual approval or edits for high-risk actions.

### Core Features
- **LangGraph Orchestration Engine**: Dynamic planner and multi-agent coordination with parallel execution.
- **GraphRAG Pipeline**: Advanced entity extraction, Neo4j knowledge graph storage, community detection (Leiden), and hybrid retrieval.
- **Explainability**: Decision-path tracing and graph-visualized context mapping for review.
- **Long-Term Memory**: Episodic, semantic, and procedural memory built on LangGraph stores.
- **Confidence Engine**: Groundedness, citation coverage, hallucination, and policy compliance verification.
- **Enterprise Security**: Input validation, prompt injection defense, and automatic PII masking.

---

## 🛠️ Project Structure

```
autonomous-biz-copilot/
├── README.md                         # This file
├── pyproject.toml                    # Modern Python packaging configuration
├── docker-compose.yml                # Neo4j, Postgres, ChromaDB orchestration
├── Dockerfile                        # Multi-stage production container
├── Makefile                          # Helper development commands
├── .env.example                      # Configuration template
├── requirements.txt                  # Python requirements (links to pyproject.toml)
│
├── configs/                          # Config files (Settings, Agents, Retrieval, Prompts)
│   ├── settings.py
│   ├── agents.yaml
│   ├── retrieval.yaml
│   ├── prompts.yaml
│   └── logging.yaml
│
├── src/                              # Source Code
│   ├── api/                          # FastAPI Layer
│   ├── agents/                       # Multi-Agent Modules (14 specialized agents)
│   ├── orchestrator/                 # LangGraph Engine
│   ├── retrieval/                    # Hybrid Retrieval (BM25, vector, graph)
│   ├── knowledge_graph/              # GraphRAG Engine
│   ├── okf/                          # Open Knowledge Format (OKF) parsers
│   ├── memory/                       # Long-Term Memory Store & Learners
│   ├── confidence/                   # Confidence Scoring Engine
│   ├── explainability/               # Decision Path Tracing
│   ├── evaluation/                   # RAGAS & DeepEval pipeline
│   ├── benchmark/                    # Benchmark Suite & Baselines
│   ├── security/                     # PII, Injection, RBAC defenses
│   ├── tools/                        # External Tool Registry
│   ├── ingestion/                    # Document ingestion (PDF, CSV, OCR)
│   ├── database/                     # PostgreSQL/SQLite models & migrations
│   ├── observability/                # Langfuse, tracing, cost tracking
│   └── synthetic/                    # Synthetic data generator
│
├── frontend/                         # Streamlit Dashboard Page Structure
│   ├── app.py                        # Main entry point
│   ├── pages/                        # Specialized sub-dashboards
│   └── components/                   # Visual dashboard widgets
│
├── knowledge/                        # Seed Knowledge Base (OKF format)
├── tests/                            # Unit, Integration, and E2E Tests
├── docs/                             # Architecture and Guides
└── scripts/                          # Seeding, setup, and benchmark scripts
```

---

## ⚡ Quick Start

### 1. Prerequisites
- **Python**: `>=3.11`
- **Docker**: For running database and graph search infrastructure

### 2. Installation
Create a virtual environment and install dependencies:
```bash
make dev
```

### 3. Start Database Services
Run PostgreSQL, Neo4j, and ChromaDB via Docker Compose:
```bash
make docker-up
```

### 4. Running the Application
- **API Server**: `make api` (runs FastAPI on port 8000)
- **Frontend Dashboard**: `make frontend` (runs Streamlit on port 8501)
