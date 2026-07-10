# Contributing to Autonomous Business Ops Copilot

Thank you for contributing! Please follow these development standards.

## Code Standards
- **Style**: Format code using `black`.
- **Linting**: Check code using `ruff check`.
- **Type Checking**: Verify strict typing with `mypy`.
- **Testing**: Run `pytest` before submitting pull requests.

## Workflow Setup
1. Clone the repository.
2. Setup virtual environments:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```
3. Run tests:
   ```bash
   pytest
   ```
