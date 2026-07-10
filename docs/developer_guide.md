# Developer Setup Guide

Follow these steps to run, format, and test the Copilot locally.

## Prerequisite Installers
- Python 3.11+
- Git
- Neo4j Database Server (or docker-compose setup)

## Setup Steps
1. Clone the repository and configure virtual environments:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```
2. Verify environmental variables configuration in `.env`:
   ```env
   APP_ENV=development
   GEMINI_API_KEY=your-api-key-here
   NEO4J_URI=bolt://localhost:7687
   ```
3. Run tests using `pytest`:
   ```bash
    # Windows PowerShell:
    $env:USE_TF="0"; python -m pytest
    # Linux / macOS:
    USE_TF=0 python -m pytest
    ```
4. Run Streamlit local development server:
   ```bash
   streamlit run frontend/app.py
   ```
