# Deployment Runbook

## 1. Purpose

This runbook documents how I deploy, verify, and troubleshoot the public v1 backend for Enterprise KIP.

The public deployment uses the lightweight cloud runtime profile:

```text
Render
  ↓
FastAPI
  ├── FastEmbed BGE
  ├── Exact BM25 query encoder
  ├── Qdrant Cloud
  └── Groq
```

The local Docker Compose stack remains separate and is not replaced by this deployment path.

---

## 2. Public Service

Current public API:

```text
https://enterprise-kip-api.onrender.com
```

Interactive Swagger UI:

```text
https://enterprise-kip-api.onrender.com/docs
```

Main operational endpoints:

```text
GET /health
GET /ready
GET /metrics
POST /v1/query
```

---

## 3. Deployment Artifacts

The cloud deployment uses:

```text
docker/Dockerfile.api.cloud
requirements-cloud.txt
deployment/artifacts/retrieval/rank-bm25-query-artifact-v1.json
```

The cloud image intentionally excludes local-only heavyweight dependencies such as:

```text
torch
sentence-transformers
rank-bm25
ollama
```

This keeps the deployment image much smaller than the full local runtime.

Validated cloud image size:

```text
~130.5 MB
```

---

## 4. Runtime Profile

The deployment must run with:

```text
RAG_PROFILE=cloud
```

The cloud profile wires:

```text
FastEmbedCloudDenseRetriever
RankBM25CloudRetriever
HybridRetriever
GroqGenerator
```

The application-level retrieval policy remains the same as the local v1 baseline:

```text
Dense weight       0.7
BM25 weight        0.3
RRF k              60
Retrieval top-k    10
Max context        4000 tokens
Max sources        6
```

---

## 5. Render Service Configuration

The Render Web Service is configured from the GitHub repository.

Expected settings:

```text
Branch            main
Runtime           Docker
Dockerfile Path   docker/Dockerfile.api.cloud
Root Directory    repository root
Region            Oregon (US West)
Instance Type     Free
Health Check      /health
```

The Docker entrypoint honors the platform-provided `PORT` variable while keeping `8000` as the local fallback.

I do not set `PORT` manually in Render.

---

## 6. Environment Variables

### Non-secret configuration

```text
RAG_PROFILE=cloud

QDRANT_URL=<Qdrant Cloud endpoint>
QDRANT_COLLECTION=enterprise_knowledge_cloud_bge_rank_bm25_v1

EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

BM25_QUERY_ARTIFACT_PATH=/app/deployment/artifacts/retrieval/rank-bm25-query-artifact-v1.json

GENERATION_MODEL=openai/gpt-oss-20b

DENSE_WEIGHT=0.7
BM25_WEIGHT=0.3
RRF_K=60
RETRIEVAL_TOP_K=10

MAX_CONTEXT_TOKENS=4000
MAX_CONTEXT_SOURCES=6

GENERATION_TIMEOUT_SECONDS=120
MAX_CONCURRENT_GENERATIONS=1
```

### Secrets

The deployment also requires:

```text
QDRANT_API_KEY
GROQ_API_KEY
```

I enter secret values directly in the Render environment settings.

Secret values must never be committed to Git, added to Docker build arguments, copied into documentation, or pasted into logs.

---

## 7. Health and Readiness

### Liveness

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

Render uses `/health` as the platform health-check endpoint.

I use liveness for the platform health check because temporary provider failures should not automatically mean the API process itself is dead.

### Readiness

```text
GET /ready
```

Expected cloud response:

```json
{
  "status": "ready",
  "dependencies": {
    "rag_service": "ready",
    "qdrant": "ready",
    "groq": "ready"
  }
}
```

`/ready` is the dependency-aware operational check.

A `503` from `/ready` means at least one required cloud dependency is unavailable or failed its readiness probe.

---

## 8. Deployment Smoke Test

After every deployment, I verify the service in this order.

### Step 1 — Liveness

```bash
curl -i https://enterprise-kip-api.onrender.com/health
```

Expected:

```text
HTTP 200
```

### Step 2 — Readiness

```bash
curl -i https://enterprise-kip-api.onrender.com/ready
```

Expected:

```text
HTTP 200
rag_service = ready
qdrant      = ready
groq        = ready
```

### Step 3 — Real RAG request

```bash
curl -X POST "https://enterprise-kip-api.onrender.com/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Docker BuildKit and how is it used during image builds?"}'
```

Expected behavior:

```text
HTTP 200
non-empty answer
retrieved sources
citations
configured generation model
latency metrics
```

### Step 4 — Invalid input boundary

```bash
printf '{"query":""}' |
  curl -i     -X POST     -H "Content-Type: application/json"     --data-binary @-     https://enterprise-kip-api.onrender.com/v1/query
```

Expected:

```text
HTTP 422
query validation failure
```

---

## 9. Metrics Verification

The service exposes Prometheus metrics at:

```text
GET /metrics
```

Useful deployment checks include:

```text
process_resident_memory_bytes
rag_queries_total
rag_retrieval_duration_seconds
rag_generation_duration_seconds
```

During public v1 validation, the hosted process used approximately:

```text
~317 MiB RSS
```

The Render Free memory budget was:

```text
512 MiB
```

Observed headroom during validation was therefore approximately:

```text
~195 MiB
```

This hosted number is the deployment reference.

The lower Docker-local warm RSS measurement is a separate characterization result and should not be presented as hosted production memory.

---

## 10. Public Performance Reference

A validated warm public request produced approximately:

```text
Backend end-to-end   ~2.9 s
Client end-to-end    ~3.4 s
```

Warm `/health` requests from the validation client were approximately:

```text
~0.3–0.7 s
```

I do not publish a fixed cold-start latency for v1 because the initial measurements included uncontrolled transport variability and were not collected under a controlled cold-start experiment.

---

## 11. Troubleshooting

### `/health` returns non-200

Check:

```text
Render service status
container startup logs
PORT binding
Dockerfile path
application startup exceptions
```

The cloud Dockerfile must start Uvicorn on the platform-provided `PORT`.

### `/health` is 200 but `/ready` is 503

Read the readiness body first.

Example:

```json
{
  "status": "not_ready",
  "dependencies": {
    "rag_service": "ready",
    "qdrant": "ready",
    "groq": "unavailable"
  }
}
```

Do not change code immediately.

First identify which dependency is unavailable.

#### `rag_service = unavailable`

Check:

```text
RAG_PROFILE
cloud configuration validation
BM25 artifact path
retriever initialization
generator initialization
```

#### `qdrant = unavailable`

Check:

```text
QDRANT_URL
QDRANT_API_KEY
QDRANT_COLLECTION
Qdrant Cloud cluster status
network connectivity
```

Do not print the API key while debugging.

#### `groq = unavailable`

Check:

```text
GROQ_API_KEY
GENERATION_MODEL
provider connectivity
readiness probe behavior
Groq availability
```

A transient readiness failure should be confirmed with another request before making a code change.

During the initial public deployment, one Groq readiness probe returned `503`, while real generation succeeded and a later readiness check returned `200`. I therefore did not patch the application without stronger evidence.

---

## 12. Query Failures

### HTTP 422

The request failed API validation.

Examples include:

```text
empty query
malformed JSON
query exceeding schema limits
```

These requests should not reach retrieval or generation.

### HTTP 503 — busy

The API may reject work when the configured generation capacity is already occupied.

The v1 cloud profile intentionally uses:

```text
MAX_CONCURRENT_GENERATIONS=1
```

Controlled rejection is preferred over unbounded in-process queue growth.

### Dependency error

Provider failures are normalized at the adapter boundary before reaching the API layer.

When investigating a provider failure, use:

```text
request ID
Render logs
readiness state
provider status
metrics
```

Do not expose credentials in diagnostic output.

---

## 13. Rebuild Validation

Before promoting Docker changes, I validate the cloud image locally.

Build:

```powershell
docker build `
  -f docker\Dockerfile.api.cloud `
  -t enterprise-kip-api:cloud-validation `
  .
```

Verify the expected cloud dependencies:

```powershell
docker run --rm enterprise-kip-api:cloud-validation `
  python -c "import fastapi,httpx,pydantic,pydantic_settings,qdrant_client,fastembed,prometheus_client; print('cloud runtime imports: OK')"
```

Verify that local-heavy packages are absent:

```powershell
docker run --rm enterprise-kip-api:cloud-validation `
  python -c "import importlib.util as u; print({'torch':u.find_spec('torch') is not None,'sentence_transformers':u.find_spec('sentence_transformers') is not None,'rank_bm25':u.find_spec('rank_bm25') is not None,'ollama':u.find_spec('ollama') is not None})"
```

Expected:

```text
torch                  False
sentence_transformers  False
rank_bm25              False
ollama                  False
```

---

## 14. Port Validation

The cloud Dockerfile supports both local Docker and platform execution.

Local default:

```text
PORT unset
→ Uvicorn binds to 8000
```

Platform:

```text
PORT provided
→ Uvicorn binds to platform port
```

A Render-style local check can be run with:

```powershell
docker run `
  --rm `
  --publish 8003:10000 `
  --env PORT=10000 `
  enterprise-kip-api:cloud-validation
```

Then verify:

```text
http://127.0.0.1:8003/health
```

---

## 15. Pre-Deploy Repository Gate

Before merging deployment-related changes, I run:

```powershell
ruff check .

pytest tests\ -q -m "not integration"

git diff --check
```

The test shell must not be contaminated with cloud environment variables when validating default local-profile behavior.

A previous validation run produced false failures because the shell still contained:

```text
RAG_PROFILE=cloud
```

The same tests passed in a clean shell.

---

## 16. Deployment Workflow

For normal v1 changes:

```text
feature branch
   ↓
local tests
   ↓
Docker validation when relevant
   ↓
pull request
   ↓
CI
   ↓
merge to main
   ↓
Render auto-deploy
   ↓
/health
   ↓
/ready
   ↓
real /v1/query smoke test
```

I keep the public service tracking `main`, not a long-lived feature branch.

---

## 17. Rollback Approach

If a new deployment introduces a regression:

1. Confirm the failure with `/health`, `/ready`, logs, and a real query.
2. Identify the last known-good commit on `main`.
3. Revert the faulty change through Git rather than editing the running container.
4. Let Render rebuild from the corrected `main`.
5. Repeat the deployment smoke test.

The deployment should remain reproducible from the repository.

Manual fixes inside a running container are not part of the v1 operational model.

---

## 18. Security Rules

I follow these rules for the public deployment:

```text
never commit provider API keys
never print secret values in diagnostics
never bake secrets into the Docker image
never pass secrets through Docker build arguments
rotate a key if it is accidentally exposed
keep .env files outside version control
```

Only non-secret configuration belongs in public documentation.

---

## 19. v1 Deployment Boundary

The public v1 deployment is deliberately simple:

```text
Render
+
Qdrant Cloud
+
Groq
```

I do not add orchestration complexity unless a measured requirement justifies it.

The deployment goal for v1 is:

```text
small image
→ bounded memory
→ reproducible configuration
→ observable runtime
→ predictable failures
→ public demo availability
```
