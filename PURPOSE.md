# PURPOSE.md

## Product goal
A lightweight, self-hosted **agent platform** where users can:
1) create an account (simple username/password),
2) create projects,
3) upload/organize files per project (PPTX, XLSX, PDF, DOCX, CSV, etc.),
4) chat with their project (RAG over project files),
5) run a dedicated **PowerPoint Agent** that produces a new PPTX from the project knowledge base.

## Non-goals (for v1)
- Multi-tenant billing, SSO, OAuth providers.
- Visual workflow builder beyond a minimal “flow” definition (JSON/YAML) if needed.
- Long-running autonomous agents without explicit user initiation.
- Cross-project data sharing by default.

## Hard constraints
- Deployable via Docker Compose.
- Persistent storage via local DB volume(s).
- LLM calls exclusively via **Amazon Bedrock Runtime**.
- Everything else local: parsing, embeddings (if using Bedrock embeddings, still via Bedrock), slide generation.

## Core architecture (recommended)
### Services (containers)
- **api**: FastAPI backend (auth, projects, upload, chat, agent orchestration).
- **db**: PostgreSQL + pgvector (projects/users, chats, documents, vectors).
- **object-store**: MinIO (S3-compatible) for raw files and generated artifacts (PPTX outputs).
- **worker**: background jobs (ingest, embedding, PPT generation) using Celery/RQ + Redis (optional).
- **ui**: lightweight web UI (optional) — start with API + minimal admin UI.

### Data model (minimum)
- users(id, username, password_hash, created_at)
- projects(id, user_id, name, created_at)
- files(id, project_id, path, mime, sha256, size, created_at)
- chunks(id, file_id, ordinal, text, metadata_json)
- vectors(id, chunk_id, embedding vector)
- chats(id, project_id, user_id, created_at)
- messages(id, chat_id, role, content, created_at)
- artifacts(id, project_id, type, uri, metadata_json, created_at)

### Ingestion & RAG
- Parse: PPTX/XLSX/PDF/DOCX into text + structured metadata.
- Chunk: semantic chunking with conservative sizes.
- Embed: Bedrock embedding model (via API).
- Store: pgvector similarity search scoped to project_id.

### PowerPoint Agent (must-have)
- Input: “create deck” request (topic, audience, length, style) + project context from RAG.
- Planning: outline slides + key points + speaker notes + references.
- Generation: build .pptx locally using `python-pptx`.
- Optional: generate images via Bedrock image model (still via API), but keep optional for v1.

## UX baseline
- Project = folder-like namespace.
- Upload files to project; ingestion happens automatically.
- Chat endpoint: answers with citations to file/chunk.
- PPT endpoint: returns artifact link to generated .pptx.

## Licensing preferences
- Prefer MIT/Apache-2.0 dependencies.
- Avoid source-available licenses for core components.
