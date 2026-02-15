# Planar

Self-hosted agent platform: upload documents, chat with them (RAG), generate PowerPoint decks — all powered by Amazon Bedrock.

## Quick Start

```bash
git clone git@github.com:koshyviv/planar.git
cd planar
cp .env.example .env
```

Edit `.env` — you **must** set these two:
```
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

Also change `SECRET_KEY` to something random.

Then:
```bash
docker compose up --build -d
```

Open **http://localhost:11434** in your browser.

## What You Can Do

1. **Register/Login** — simple username + password
2. **Create a project** — a workspace for your files
3. **Upload files** — PDF, PPTX, XLSX, DOCX, CSV, TXT (max 50MB each)
4. **Chat** — ask questions about your files, get answers with citations
5. **Generate PPTX** — AI builds a slide deck from your project knowledge

## Services

| Service | Port | Purpose |
|---------|------|---------|
| api | 11434 | FastAPI backend + UI |
| db | 5432 | PostgreSQL + pgvector |
| redis | 6379 | Celery broker |
| minio | 9000/9001 | Object storage |
| worker | — | Background ingestion + PPT generation |

## Run Tests (no Docker needed)

```bash
pip install -r services/api/requirements.txt -r services/worker/requirements.txt
PYTHONPATH=services/api pytest tests/api/ -v
PYTHONPATH=services/worker pytest tests/worker/ -v
```

## Small Instance Tips

- Build one service at a time if RAM is tight: `docker compose build api && docker compose build worker`
- Reduce worker concurrency: edit `--concurrency=2` to `--concurrency=1` in `docker-compose.yml`
- API port is configurable via `API_PORT` in `.env`
