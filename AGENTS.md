# Repository Guidelines

## Project Structure & Module Organization

This repository is a FastAPI backend for Retell AI voice calls and MongoDB persistence. Application code lives in `app/`: `main.py` wires the API, `config.py` loads environment settings, and `database.py` manages MongoDB. HTTP handlers are grouped under `app/routes/`, Retell integration belongs in `app/services/`, and Pydantic request/response types live in `app/schemas/` and `app/models/`. Tests are in `tests/`; mirror the application area being tested and name files `test_<feature>.py`. Keep generated files such as `__pycache__/` and `.pytest_cache/` out of commits.

## Build, Test, and Development Commands

Create and activate a local environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the API with `uvicorn app.main:app --reload --port 8000`. Run all tests with `pytest`; target one module with `pytest tests/test_main.py -q`. There is no separate build step. Before local runs, copy `.env.example` to `.env` and provide valid Retell and MongoDB values.

## Coding Style & Naming Conventions

Follow PEP 8 with four-space indentation. Use `snake_case` for modules, functions, and variables; `PascalCase` for Pydantic models and test classes; and uppercase names for environment-backed constants. Add type hints to public functions and concise docstrings where behavior is not obvious. Keep route handlers thin: validation belongs in Pydantic schemas, external API work in services, and persistence in database helpers. No formatter or linter is configured, so match the surrounding code and keep imports grouped as standard library, third party, then local.

## Testing Guidelines

Tests use `pytest` with FastAPI's `TestClient` and `unittest.mock`. Name tests `test_<behavior>` and cover success, validation, and failure paths. Mock Retell and MongoDB calls; unit tests should not depend on live credentials or services. Run `pytest` before opening a pull request. No coverage threshold is currently configured.

## Commit & Pull Request Guidelines

Git history is not available in this checkout, so no repository-specific commit convention can be inferred. Use short, imperative subjects such as `Add webhook signature validation`, and keep unrelated changes separate. Pull requests should explain the behavior change, list verification commands, link relevant issues, and call out API or environment-variable changes. Include example requests/responses for endpoint changes; screenshots are only useful for documentation or consumer-facing output.

## Security & Configuration

Never commit `.env`, API keys, webhook secrets, connection strings, transcripts, or customer data. Update `.env.example` with placeholders whenever configuration changes, and avoid logging sensitive payloads.
