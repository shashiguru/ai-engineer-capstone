# ai-engineer-capstone

FastAPI API with a `/chat` endpoint backed by OpenAI.

## Prereqs

- **Python**: 3.12+ (`pyproject.toml` requires `>=3.12`)
- **OPENAI_API_KEY**: required for `/chat`

## Setup

Create a `.env` file in the repo root (same folder as `pyproject.toml`):

```bash
cp env.example .env
```

Edit `.env` and set `OPENAI_API_KEY=...`.

## Install & run (recommended: uv)

```bash
python -m pip install --upgrade pip
python -m pip install uv

uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Install & run (pip + venv)

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip

python -m pip install fastapi "uvicorn[standard]" openai pydantic python-dotenv structlog

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Verify

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **Health**:

```bash
curl http://127.0.0.1:8000/health
```

- **Chat**:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello!"}'
```