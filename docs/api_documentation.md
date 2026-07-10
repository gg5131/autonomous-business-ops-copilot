# API Documentation

The Autonomous Business Ops Copilot exposes asynchronous FastAPI REST endpoints.

## 🚀 Core API Endpoints

### 1. Ingest Documents
- **Endpoint**: `POST /api/v1/ingest/upload`
- **Payload**: `multipart/form-data` containing document files.
- **Response**:
  ```json
  {
    "status": "success",
    "filename": "refund_policy.pdf",
    "chunks_count": 5
  }
  ```

### 2. Process Support Ticket
- **Endpoint**: `POST /api/v1/tickets/process`
- **Request Body**:
  ```json
  {
    "ticket_id": "t-100",
    "title": "Refund window issue",
    "description": "Requested refund for monthly CloudSync Pro subscription. Window expired 2 days ago.",
    "customer_id": "c-200"
  }
  ```
- **Response**:
  ```json
  {
    "run_id": "run-uuid-000",
    "status": "Human Review Required",
    "draft_response": "We received your refund request...",
    "overall_confidence": 0.885
  }
  ```

### 3. Retrieve Memory Context
- **Endpoint**: `GET /api/v1/memory/episodic`
- **Query Params**: `query=refund`
- **Response**: List of previous episodic log dicts.
