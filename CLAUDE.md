# CLAUDE.md

This file instructs Claude Code / Claude agents working in this repository.

## Mission
Implement the platform described in PURPOSE.md with the constraints in SOUL.md:
- Docker-first
- Bedrock-only for all LLM/embedding calls
- Local containers for everything else
- Simple username/password auth
- Users → Projects → Files → Chat (RAG) + PowerPoint Agent (PPTX output)

## How to work in this repo (best-practice workflow)
Follow Claude Code best practices: keep changes small, run commands/tests, and maintain a clean repo narrative. (See Claude Code docs “Best Practices”.) 

### Execution rules
- Always use the provided Docker Compose services for running and testing.
- Never require global installs on the host; use container images or devcontainers.
- Never add a direct Anthropic SDK call; Bedrock only.
- Prefer deterministic builds: pin versions, use lockfiles, avoid “latest”.

### Change discipline
- Make incremental commits and keep diffs reviewable.
- Update docs alongside code (README, API docs, env templates).
- If you introduce a new dependency, justify it in docs and keep it minimal.

## Target repo layout (expected)
```
.
├─ docker-compose.yml
├─ .env.example
├─ SOUL.md
├─ PURPOSE.md
├─ CLAUDE.md
├─ services/
│  ├─ api/              # FastAPI app (auth, projects, upload, chat, ppt)
│  │  ├─ Dockerfile
│  │  └─ app/
│  ├─ worker/           # background ingestion + ppt generation (optional)
│  │  ├─ Dockerfile
│  │  └─ app/
│  └─ ui/               # optional minimal UI
├─ migrations/          # DB migrations (Alembic)
└─ scripts/             # utility scripts (ingest/test fixtures)
```

## Bedrock integration requirements
Use Amazon Bedrock Runtime APIs for Claude. Prefer AWS SDK (boto3) inside the api/worker containers. Use environment variables for:
- AWS_REGION
- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (or IAM role when deployed)
- BEDROCK_TEXT_MODEL_ID (Claude via Bedrock)
- BEDROCK_EMBED_MODEL_ID (Embeddings via Bedrock)

Reference AWS docs for invoking Claude on Bedrock and boto3’s `invoke_model`. 

## Persistence requirements
- PostgreSQL with pgvector for vectors + relational data.
- MinIO for object storage (raw uploads and generated PPTX).
- All persistent volumes declared in docker-compose.

## Auth requirements (simple)
- Username/password.
- Password hashing (bcrypt/argon2).
- JWT access token (short-lived) + refresh token (optional).
- Project access strictly scoped to owning user.

## “Chat with project” requirements
- Ingestion pipeline:
  - Accept upload → store raw file → enqueue parse/embed.
  - Extract text from: PPTX, XLSX, PDF, DOCX.
  - Chunk, embed via Bedrock embedding model, store vectors keyed by project_id.
- Chat pipeline:
  - Retrieve top-k chunks by similarity scoped to project_id.
  - Compose prompt with citations (file name + slide/sheet/page metadata).
  - Call Claude via Bedrock.
  - Return answer + citations + optional structured JSON.

## PowerPoint Agent requirements (must implement)
- Endpoint: `POST /projects/{id}/ppt`
- Produces a `.pptx` stored in MinIO and returns an artifact link.
- Uses:
  - RAG context from project vectors.
  - Claude via Bedrock for:
    - slide outline (JSON)
    - per-slide content (JSON)
    - speaker notes
- Builds PPTX locally with `python-pptx`.
- Deterministic templates: keep 1–2 base templates in-repo (e.g., `assets/templates/`).
- Add basic validation: slide count limits, text length limits.

## Minimal test plan
- Unit tests: auth, project scoping, vector retrieval, PPT builder.
- Integration tests: docker-compose up → ingest sample files → chat → generate ppt.
- Fixtures: include small sample PPTX/XLSX/PDF in `tests/fixtures/` (non-sensitive).

## Security constraints
- Validate uploads (size, mime, extension), store with content-hash names.
- Never execute untrusted macros or scripts from uploaded Office files.
- Sanitize any HTML output; default to plain text.
- Secrets only via env vars; never commit real keys.

## How to build and run

### Prerequisites
- Docker and Docker Compose installed on the host.
- AWS credentials with Bedrock access (set in `.env`).

### Setup
```bash
cp .env.example .env
# Edit .env: add AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, change SECRET_KEY
```

### Build and run
```bash
docker compose up --build -d
```
API will be available at `http://localhost:11434` (configurable via `API_PORT` in `.env`).

### Small instance considerations
- This is designed to run on small/cheap instances. Do NOT build containers locally if the instance has limited RAM/CPU.
- Prefer building images on a separate machine or CI pipeline and pulling them.
- If building locally, use `docker compose build --no-cache` one service at a time if memory is tight:
  ```bash
  docker compose build api
  docker compose build worker
  docker compose up -d
  ```
- The `migrate` service runs Alembic migrations automatically on startup.
- Worker concurrency defaults to 2; reduce to 1 on very small instances by editing the worker command in `docker-compose.yml`.

### Run unit tests (no Docker required)
```bash
# Install test dependencies
pip install -r services/api/requirements.txt -r services/worker/requirements.txt

# Run all tests
PYTHONPATH=services/api python3 -m pytest tests/api/ -v
PYTHONPATH=services/worker python3 -m pytest tests/worker/ -v
```

### Generate test fixtures (one-time)
```bash
python3 tests/fixtures/create_fixtures.py
```

## Definition of done (v1)
- `docker compose up` boots all services.
- User can register/login.
- User can create project.
- User can upload files.
- System ingests + embeds and supports chat with citations.
- User can request a PPT; receives downloadable `.pptx`.
