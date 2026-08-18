# Reproducibility and Operations

## 1. Purpose

This document records how I reproduce the v1 repository state, validate changes, and keep benchmark, runtime, and deployment results traceable.

The goal is not to make every historical experiment reproducible from a single command. The goal is to make the **frozen v1 production path** reproducible and to keep benchmark decisions tied to versioned artifacts.

---

## 2. Supported Python Version

The v1 repository targets:

```text
CPython 3.13
```

For local development I use:

```powershell
python --version
python -m pip install -r requirements-dev.txt
```

The development requirements include the runtime requirements plus the tools used by the default quality gate.

---

## 3. Clean Repository Validation

Before validating a branch, I first confirm the active branch and working tree:

```powershell
git branch --show-current
git status --short
git log --oneline --decorate -8
```

The repository may contain local exploratory artifacts that are intentionally untracked.

I never use:

```text
git add .
```

Instead, I stage only the files that belong to the current change.

---

## 4. Default Quality Gate

The default non-integration gate is:

```powershell
ruff check .

pytest tests\ -q -m "not integration"

git diff --check
```

The current v1 validation baseline reached:

```text
216 passed
2 deselected
1 non-blocking warning
```

The warning came from the FastAPI/Starlette test client dependency boundary and was not treated as a v1 deployment blocker.

---

## 5. Test Environment Isolation

The default configuration profile is:

```text
RAG_PROFILE=local
```

Cloud environment variables can contaminate configuration tests if they remain in the shell.

Before running the default test suite, I verify that cloud-only variables are not unintentionally set:

```powershell
Write-Host "RAG_PROFILE =" $env:RAG_PROFILE
Write-Host "QDRANT_URL =" $env:QDRANT_URL
Write-Host "GROQ_API_KEY set =" ([bool]$env:GROQ_API_KEY)
```

For a clean default-profile test shell I expect:

```text
RAG_PROFILE =
QDRANT_URL =
GROQ_API_KEY set = False
```

A previous full-suite run produced five false failures because `RAG_PROFILE=cloud` was still present in the shell. The same tests passed immediately in a clean shell.

---

## 6. Local Runtime Profile

The local profile is the full production-style reference stack:

```text
FastAPI
Qdrant
Ollama
Prometheus
Grafana
```

The repository-root Compose file is:

```text
docker-compose.yml
```

Validate it with:

```powershell
docker compose config --quiet
```

Build the API image with:

```powershell
docker compose build api
```

The local profile uses:

```text
SentenceTransformers BAAI/bge-small-en-v1.5
Local Qdrant
rank_bm25.BM25Okapi
Weighted RRF
Ollama qwen3:4b-instruct
```

The cloud profile must not replace this reference path.

---

## 7. Cloud Runtime Profile

The cloud profile uses:

```text
FastEmbed BGE
Qdrant Cloud dense vectors
Qdrant Cloud exact BM25 sparse vectors
Weighted RRF
Groq
```

Cloud packaging is defined by:

```text
docker/Dockerfile.api.cloud
requirements-cloud.txt
deployment/artifacts/retrieval/rank-bm25-query-artifact-v1.json
```

Build it with:

```powershell
docker build `
  -f docker\Dockerfile.api.cloud `
  -t enterprise-kip-api:cloud-validation `
  .
```

---

## 8. Cloud Dependency Boundary

The cloud image should contain the lightweight runtime dependencies:

```powershell
docker run --rm enterprise-kip-api:cloud-validation `
  python -c "import fastapi,httpx,pydantic,pydantic_settings,qdrant_client,fastembed,prometheus_client; print('cloud runtime imports: OK')"
```

It should not install the local heavyweight stack:

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

The validated v1 cloud image was approximately:

```text
130.5 MB
```

---

## 9. Cloud Artifact Integrity

The exact BM25 cloud query artifact is versioned at:

```text
deployment/artifacts/retrieval/rank-bm25-query-artifact-v1.json
```

The frozen SHA256 is:

```text
FCD2CA656B1A704F43AAA432216E4CA827C1DA740310C7FE2D08D14FA4BAE0E6
```

Verify it with:

```powershell
Get-FileHash `
  deployment\artifacts\retrieval\rank-bm25-query-artifact-v1.json `
  -Algorithm SHA256
```

A hash mismatch means the deployment artifact has changed and must not be treated as the frozen v1 artifact without revalidation.

---

## 10. Retrieval Reproducibility

The canonical retrieval reports are stored under:

```text
benchmarks/retrieval/reports/
```

The production-default local Weighted RRF result is:

```text
Hit@10      0.9300
Recall@10   0.8392
nDCG@10     0.6788
MRR         0.7247
```

The final cloud-compatible retrieval result is:

```text
Hit@10      0.9300
Recall@10   0.8208
nDCG@10     0.6677
MRR         0.7119
```

I treat the benchmark reports and manifests as the canonical record of those results.

Exploratory review files and temporary benchmark outputs are not promoted automatically.

---

## 11. Exact BM25 Parity Evidence

Before full cloud migration, the custom sparse representation was validated against local `rank_bm25`.

The parity canary used:

```text
500 chunks
100 query texts
```

Result:

```text
Exact top-10 order            100 / 100
Mean top-10 local coverage    1.000000
Maximum shared score delta    0.0000024688
Mismatched queries            0
```

This evidence is the basis for treating the cloud sparse query encoder as rank_bm25-compatible for the v1 deployment path.

---

## 12. Generation Reproducibility

The local generation benchmark is documented under:

```text
benchmarks/generation/reports/generation_benchmark_v1.md
```

That benchmark evaluates:

```text
Ollama
qwen3:4b-instruct
prompt v3
```

The public deployment later uses:

```text
Groq
openai/gpt-oss-20b
```

These are different runtime profiles and should not be presented as the same benchmark.

The cloud generation configuration includes:

```text
GENERATION_TIMEOUT_SECONDS=120
MAX_CONCURRENT_GENERATIONS=1
```

GPT-OSS-specific request handling preserves answer budget and rejects successful provider responses that contain no final answer content.

---

## 13. E2E Reproducibility

The frozen E2E v1 benchmark contains:

```text
18 cases
```

It covers:

```text
lexical
semantic
ambiguous
cross-tool
version-specific
insufficient-evidence
```

The E2E benchmark is intentionally separate from the earlier generation-development set.

Its purpose is to validate the real application path:

```text
FastAPI
→ RAGService
→ RAGPipeline
→ retrieval
→ context
→ prompt
→ generation
→ API response
```

Canonical decision artifact:

```text
benchmarks/e2e/reports/e2e_v1_decision.md
```

---

## 14. Public Runtime Verification

The deployed service is:

```text
https://enterprise-kip-api.onrender.com
```

Basic checks:

```powershell
curl.exe -i https://enterprise-kip-api.onrender.com/health

curl.exe -i https://enterprise-kip-api.onrender.com/ready
```

Expected cloud readiness:

```text
rag_service = ready
qdrant      = ready
groq        = ready
```

A real RAG smoke test should verify:

```text
HTTP 200
non-empty answer
sources
citations
generation model
latency metrics
```

---

## 15. Hosted Runtime Reference

The public Render validation observed approximately:

```text
Hosted RSS              ~317 MiB
Render memory budget    512 MiB
Observed headroom       ~195 MiB
```

A representative warm public request observed:

```text
Backend E2E             ~2.9 s
Client E2E              ~3.4 s
```

Warm public `/health` transport measurements were approximately:

```text
~0.3–0.7 s
```

I do not freeze a cold-start number because the initial samples included uncontrolled transport variability.

---

## 16. Metrics

Prometheus metrics are exposed at:

```text
GET /metrics
```

Useful runtime signals include:

```text
process_resident_memory_bytes
rag_queries_total
rag_retrieval_duration_seconds
rag_generation_duration_seconds
```

The public deployment validation confirmed that these metrics were available after real requests.

Metrics should be interpreted with provenance:

```text
Docker-local memory
≠
hosted Render memory
```

I keep those measurements separate in documentation.

---

## 17. Git Workflow

My normal workflow is:

```text
main
  ↓
feature branch
  ↓
small scoped change
  ↓
targeted validation
  ↓
full quality gate
  ↓
selective staging
  ↓
commit
  ↓
push
  ↓
pull request
  ↓
CI
  ↓
merge
```

For deployment-related work:

```text
merge to main
  ↓
Render auto-deploy
  ↓
/health
  ↓
/ready
  ↓
real query smoke test
```

---

## 18. Selective Staging

Before every commit:

```powershell
git status --short
```

Then I stage only intended files, for example:

```powershell
git add docs/06_reproducibility_and_operations.md
```

I review the staged change with:

```powershell
git diff --cached --stat
git diff --cached
```

This is especially important because benchmark development can leave many local review artifacts and probe scripts that are useful for analysis but do not belong in the release commit.

---

## 19. What Is Frozen in v1

The v1 production path freezes:

```text
deterministic hybrid retrieval
Weighted RRF
grounded context construction
cited generation
bounded generation concurrency
profile-aware readiness
public cloud deployment
```

Automatic adaptive routing is not part of the v1 production path.

Autonomous LangGraph behavior is also outside the frozen v1 boundary.

Future experiments can build on v1 without changing the benchmark record that justified the original production decisions.

---

## 20. Reproducibility Principle

I use the following rule for production decisions:

```text
version the inputs
→ record the configuration
→ measure the result
→ preserve the report
→ promote only validated artifacts
```

The repository should make it possible to distinguish:

```text
production baseline
from
benchmark experiment
from
temporary local analysis
```

That distinction is part of the v1 engineering design, not just repository cleanup.
