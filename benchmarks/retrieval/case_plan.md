# Retrieval Evaluation Benchmark Plan

## 1. Objective

This document defines the target evaluation benchmark for the Enterprise
Knowledge Intelligence retrieval system.

The benchmark is designed to evaluate retrieval quality across multiple types
of technical queries rather than optimizing only for simple semantic search.

The final benchmark contains:

```text
100 evaluation cases
```

distributed equally across five query categories:

| Category | Target Cases |
|---|---:|
| Semantic | 20 |
| Lexical | 20 |
| Ambiguous | 20 |
| Version-specific | 20 |
| Cross-tool | 20 |
| **Total** | **100** |

Each category contributes exactly 20% of the benchmark.

This prevents aggregate metrics from being dominated by one query type.

---

# 2. Benchmark Goals

The benchmark should answer the following questions:

1. How well does dense retrieval handle semantic paraphrases?
2. How well does BM25 handle exact technical terminology?
3. Does hybrid retrieval provide consistent improvements?
4. Does query rewriting improve difficult semantic queries?
5. Does query rewriting hurt strongly lexical queries?
6. Can the retriever disambiguate underspecified technical questions?
7. Can the retriever distinguish version-specific documentation?
8. Can the system retrieve evidence from multiple technologies for cross-tool
   questions?
9. How well does the system retrieve multiple relevant documents?
10. How stable are retrieval improvements across query categories?

---

# 3. Benchmark Categories

## 3.1 Semantic

Semantic queries describe a concept without necessarily using the same
terminology as the target document.

Example:

```text
How can a LangGraph workflow pause for human approval and continue later?
```

The relevant documentation may primarily use the term:

```text
interrupt
```

Semantic retrieval should perform particularly well on this category.

---

## 3.2 Lexical

Lexical queries contain highly specific technical terms such as:

- class names;
- API names;
- configuration keys;
- CLI commands;
- file names;
- protocol names;
- algorithm names.

Examples:

```text
.dockerignore
BackgroundTasks
HNSW
ConfigMap
Depends
```

BM25 is expected to benefit from these signals.

---

## 3.3 Ambiguous

Ambiguous queries intentionally avoid the canonical terminology used by the
documentation.

Example:

```text
How can I save graph progress and continue it later?
```

Possible concepts include:

```text
state
checkpointing
persistence
interrupts
memory
```

The retriever must infer the intended concept from context.

---

## 3.4 Version-Specific

Version-specific queries involve:

- migration;
- deprecation;
- compatibility;
- old versus new APIs;
- behavior changes;
- removed features.

These queries test whether retrieval can distinguish highly similar
documentation associated with different versions or generations of an API.

---

## 3.5 Cross-Tool

Cross-tool queries require documentation from multiple technologies.

Example:

```text
How should I deploy a FastAPI application on Kubernetes?
```

A useful retrieval result may require documents from:

```text
FastAPI
+
Kubernetes
```

These queries represent the core enterprise documentation intelligence use
case.

---

# 4. Relevance Scale

Ground truth uses graded relevance:

```text
3 = directly answers the query
2 = strongly relevant supporting document
1 = useful background or partially relevant
0 = not relevant
```

Example:

```json
{
  "relevant_documents": [
    {
      "source": "qdrant",
      "path": "search/text-search/hybrid-search.md",
      "relevance": 3
    },
    {
      "source": "qdrant",
      "path": "search/_index.md",
      "relevance": 1
    }
  ]
}
```

---

# 5. Ground-Truth Rules

A case must not become `active` until:

1. The document exists in the current indexed corpus.
2. The document actually addresses the query.
3. `source` matches retrieval metadata.
4. `path` exactly matches retrieval metadata.
5. Relevant documents are manually reviewed.
6. Multiple valid documents are included when appropriate.
7. Relevance grades are manually assigned.
8. Ground truth is not selected purely because a retriever ranked it highly.

Retrievers may be used to discover candidate documents, but retrieval output
must not automatically define ground truth.

---

# 6. Case Status

Cases can have:

```text
planned
needs_review
active
```

Meaning:

### planned

The query has been designed but ground truth has not yet been investigated.

### needs_review

Candidate relevant documents have been identified but manual verification is
not finished.

### active

Ground truth has been manually reviewed and the case can participate in the
benchmark.

---

# 7. Benchmark Versioning

Historical benchmarks must be preserved.

## Legacy Benchmark

```text
11 cases
```

Used for historical comparison with early retrieval experiments.

---

## Expanded Benchmark v1

```text
15 cases
```

Introduced:

- corrected Qdrant documentation;
- multiple relevant documents;
- category-based evaluation.

---

## Balanced Benchmark v2

Target:

```text
100 cases
```

Distribution:

```text
20 semantic
20 lexical
20 ambiguous
20 version-specific
20 cross-tool
```

This becomes the primary retrieval benchmark.

---

# 8. Semantic Cases — 20

Thirteen semantic cases are already active.

| ID | Query | Primary Source | State |
|---|---|---|---|
| `docker_cache_001` | How does Docker build cache work and when is it invalidated? | Docker | ✅ Active |
| `kubernetes_configmap_001` | How does a Kubernetes ConfigMap provide configuration to a Pod? | Kubernetes | ✅ Active |
| `kubernetes_liveness_001` | What is the difference between liveness, readiness, and startup probes in Kubernetes? | Kubernetes | ✅ Active |
| `fastapi_background_tasks_001` | How do background tasks work in FastAPI? | FastAPI | ✅ Active |
| `fastapi_middleware_001` | How do I add middleware to a FastAPI application? | FastAPI | ✅ Active |
| `fastapi_validation_001` | How does FastAPI validate request bodies using Pydantic models? | FastAPI | ✅ Active |
| `langgraph_checkpoint_001` | How do LangGraph checkpointers persist graph state between executions? | LangGraph | ✅ Active |
| `langgraph_interrupt_001` | How can a LangGraph workflow pause for human approval and resume later? | LangGraph | ✅ Active |
| `langgraph_state_001` | How is shared state defined and updated in a LangGraph graph? | LangGraph | ✅ Active |
| `langgraph_memory_001` | What is the difference between short-term and long-term memory in LangGraph? | LangGraph | ✅ Active |
| `qdrant_filter_001` | How do Qdrant payload filters restrict vector search results? | Qdrant | ✅ Active |
| `qdrant_hybrid_001` | How does hybrid search combine dense and sparse vectors in Qdrant? | Qdrant | ✅ Active |
| `qdrant_payload_index_001` | Why should payload fields be indexed in Qdrant? | Qdrant | ✅ Active |
| `docker_multistage_semantic_001` | How can Docker build an application without keeping build tools in the final image? | Docker | Planned |
| `kubernetes_resource_limits_semantic_001` | How can Kubernetes prevent one container from consuming unlimited CPU or memory? | Kubernetes | Planned |
| `fastapi_dependency_semantic_001` | How can shared application logic be automatically supplied to FastAPI endpoints? | FastAPI | Planned |
| `langgraph_branching_semantic_001` | How can a LangGraph workflow choose different execution paths based on state? | LangGraph | Planned |
| `qdrant_similarity_semantic_001` | How does Qdrant determine which stored vectors are closest to a query vector? | Qdrant | Planned |
| `huggingface_generation_semantic_001` | How can a Transformers model generate text from an input prompt? | Hugging Face | Planned |
| `huggingface_tokenization_semantic_001` | How is raw text converted into model inputs for Transformers models? | Hugging Face | Planned |

---

# 9. Lexical Cases — 20

Two lexical cases are already active.

| ID | Query | Primary Source | State |
|---|---|---|---|
| `docker_dockerignore_001` | How does a `.dockerignore` file reduce the Docker build context? | Docker | ✅ Active |
| `qdrant_collection_001` | How do I create a Qdrant collection with cosine distance? | Qdrant | ✅ Active |
| `docker_buildkit_001` | What is Docker BuildKit and how is it used during image builds? | Docker | Planned |
| `docker_copy_001` | What does the Dockerfile `COPY` instruction do? | Docker | Planned |
| `docker_entrypoint_001` | What is the difference between Dockerfile `ENTRYPOINT` and `CMD`? | Docker | Planned |
| `kubernetes_kubectl_001` | What does `kubectl apply` do? | Kubernetes | Planned |
| `kubernetes_configmap_lexical_001` | How is `ConfigMap` referenced from a Pod specification? | Kubernetes | Planned |
| `kubernetes_imagepullpolicy_001` | How does `imagePullPolicy` control Kubernetes image pulling? | Kubernetes | Planned |
| `kubernetes_restartpolicy_001` | What does `restartPolicy` control in a Kubernetes Pod? | Kubernetes | Planned |
| `fastapi_depends_001` | How does FastAPI's `Depends` function declare a dependency? | FastAPI | Planned |
| `fastapi_backgroundtasks_lexical_001` | How is FastAPI `BackgroundTasks` used inside a path operation? | FastAPI | Planned |
| `fastapi_http_exception_001` | How do I raise an `HTTPException` in FastAPI? | FastAPI | Planned |
| `fastapi_basemodel_001` | How is a Pydantic `BaseModel` used for FastAPI request bodies? | FastAPI | Planned |
| `langgraph_command_001` | What does the LangGraph `Command` object do? | LangGraph | Planned |
| `langgraph_interrupt_lexical_001` | How is `interrupt()` used inside a LangGraph node? | LangGraph | Planned |
| `langgraph_messagesstate_001` | What is `MessagesState` in LangGraph? | LangGraph | Planned |
| `qdrant_hnsw_001` | How is the HNSW index configured in Qdrant? | Qdrant | Planned |
| `qdrant_payload_index_lexical_001` | How do I create a Qdrant payload index? | Qdrant | Planned |
| `huggingface_autotokenizer_001` | How is `AutoTokenizer.from_pretrained()` used? | Hugging Face | Planned |
| `huggingface_automodel_001` | What does `AutoModel.from_pretrained()` load? | Hugging Face | Planned |

---

# 10. Ambiguous Cases — 20

These queries intentionally avoid canonical documentation terminology.

| ID | Query | Intended Concept | Source | State |
|---|---|---|---|---|
| `docker_context_ambiguous_001` | How can I avoid sending unnecessary files when building an image? | `.dockerignore` / build context | Docker | Planned |
| `docker_cache_ambiguous_001` | Why does rebuilding an image sometimes reuse old steps? | Build cache | Docker | Planned |
| `docker_layers_ambiguous_001` | Why does changing one build step cause later image steps to run again? | Layer/cache invalidation | Docker | Planned |
| `docker_small_image_ambiguous_001` | How can I keep compilers and build tools out of my final container? | Multi-stage build | Docker | Planned |
| `kubernetes_health_ambiguous_001` | How can Kubernetes tell whether my application is ready to receive traffic? | Readiness probe | Kubernetes | Planned |
| `kubernetes_restart_ambiguous_001` | How can Kubernetes detect that my application is stuck and restart it? | Liveness probe | Kubernetes | Planned |
| `kubernetes_configuration_ambiguous_001` | How can I give configuration values to containers without rebuilding the image? | ConfigMap | Kubernetes | Planned |
| `kubernetes_secrets_ambiguous_001` | Where should a Pod get sensitive configuration such as credentials? | Secret | Kubernetes | Planned |
| `fastapi_shared_logic_ambiguous_001` | How can multiple API endpoints reuse the same setup logic? | Dependencies | FastAPI | Planned |
| `fastapi_after_response_ambiguous_001` | How can my API perform work after returning the response? | Background tasks | FastAPI | Planned |
| `fastapi_validation_ambiguous_001` | How can the API reject malformed JSON before my endpoint logic runs? | Request validation | FastAPI | Planned |
| `fastapi_cross_cutting_ambiguous_001` | How can I run logic for every incoming request and outgoing response? | Middleware | FastAPI | Planned |
| `langgraph_persistence_ambiguous_001` | How can I save graph progress and continue it later? | Checkpointing | LangGraph | Planned |
| `langgraph_human_ambiguous_001` | How can a workflow stop and wait for a person before continuing? | Interrupts | LangGraph | Planned |
| `langgraph_shared_data_ambiguous_001` | How can multiple graph steps read and modify the same information? | State | LangGraph | Planned |
| `langgraph_long_memory_ambiguous_001` | How can information survive beyond a single conversation or graph run? | Long-term memory | LangGraph | Planned |
| `qdrant_metadata_ambiguous_001` | How can I search only vectors whose metadata matches certain conditions? | Payload filtering | Qdrant | Planned |
| `qdrant_keyword_semantic_ambiguous_001` | How can search use both meaning and exact keyword matching? | Hybrid search | Qdrant | Planned |
| `qdrant_speed_filter_ambiguous_001` | How can filtering remain fast when the collection becomes large? | Payload indexing | Qdrant | Planned |
| `huggingface_model_input_ambiguous_001` | How do I turn user text into something a Transformer model can process? | Tokenization | Hugging Face | Planned |

---

# 11. Version-Specific Cases — 20

Every case in this category must be verified against the current corpus before
activation.

If the corpus does not contain sufficient version evidence, the case must
remain `planned`.

| ID | Query | Source | State |
|---|---|---|---|
| `fastapi_pydantic_v1_v2_001` | What changes when using FastAPI with Pydantic v1 versus Pydantic v2? | FastAPI | Planned |
| `fastapi_pydantic_migration_001` | How should FastAPI applications migrate models from Pydantic v1 to v2? | FastAPI | Planned |
| `fastapi_deprecated_feature_001` | Which older FastAPI patterns are currently deprecated and what should replace them? | FastAPI | Planned |
| `fastapi_python_version_001` | Which Python-version-dependent FastAPI syntax is shown differently in the documentation? | FastAPI | Planned |
| `kubernetes_deprecated_api_001` | How does Kubernetes document deprecated API versions and their replacements? | Kubernetes | Planned |
| `kubernetes_removed_api_001` | Which Kubernetes APIs were removed and what versions replace them? | Kubernetes | Planned |
| `kubernetes_ingress_version_001` | How did the Kubernetes Ingress API change between older beta versions and `networking.k8s.io/v1`? | Kubernetes | Planned |
| `kubernetes_version_skew_001` | What version skew is supported between Kubernetes components? | Kubernetes | Planned |
| `docker_compose_version_001` | How has Docker Compose file/version handling changed in current Docker documentation? | Docker | Planned |
| `docker_builder_version_001` | How does modern BuildKit-based Docker build behavior differ from the legacy builder? | Docker | Planned |
| `docker_deprecated_instruction_001` | Which Docker Engine features are deprecated or retired in current Docker documentation? | Docker | Planned |
| `docker_api_version_001` | How does Docker handle API version compatibility between clients and daemons? | Docker | Planned |
| `huggingface_autogptq_deprecation_001` | What should Transformers users use now that AutoGPTQ is no longer supported? | Hugging Face | Planned |
| `fastapi_form_model_version_001`| From which FastAPI version are Pydantic models supported for form fields? | FastAPI | planned |
| `fastapi_header_model_version_001` | From which FastAPI version can Pydantic models be used for header parameters? | FastAPI | planned |
| `kubernetes_kms_version_001` | How did Kubernetes support for KMS v1 and KMS v2 change across recent releases? | Kubernetes | planned |
| `qdrant_upgrade_001` | What should users check when upgrading Qdrant between versions? | Qdrant | Planned |
| `kubernetes_compatibility_version_001` | What compatibility and emulation controls were introduced for Kubernetes control-plane components starting in v1.32? | Kubernetes | planned |
| `langgraph_api_migration_001` | Which LangGraph APIs changed or require migration in newer documentation? | LangGraph | Planned |
| `langgraph_deprecated_pattern_001` | Which older LangGraph workflow patterns have been replaced by newer APIs? | LangGraph | Planned |

---

# 12. Cross-Tool Cases — 20

Cross-tool cases should normally contain multiple relevant documents from
different sources.

| ID | Query | Relevant Sources | State |
|---|---|---|---|
| `fastapi_docker_001` | How should I containerize a FastAPI application with Docker? | FastAPI + Docker | Planned |
| `fastapi_kubernetes_001` | How should I deploy a FastAPI application on Kubernetes? | FastAPI + Kubernetes | Planned |
| `fastapi_docker_kubernetes_001` | How can I package a FastAPI service in Docker and deploy it to Kubernetes? | FastAPI + Docker + Kubernetes | Planned |
| `fastapi_qdrant_001` | How can a FastAPI endpoint query vectors stored in Qdrant? | FastAPI + Qdrant | Planned |
| `fastapi_huggingface_001` | How can Transformers model inference be wrapped behind a FastAPI endpoint? | FastAPI + Hugging Face | Planned |
| `langgraph_fastapi_001` | How can I expose a LangGraph workflow through a FastAPI endpoint? | LangGraph + FastAPI | Planned |
| `langgraph_qdrant_001` | How can a LangGraph workflow retrieve information from Qdrant? | LangGraph + Qdrant | Planned |
| `langgraph_fastapi_qdrant_001` | How can a FastAPI service run a LangGraph workflow that retrieves context from Qdrant? | LangGraph + FastAPI + Qdrant | Planned |
| `langgraph_docker_001` | How can I package a LangGraph application in a Docker container? | LangGraph + Docker | Planned |
| `langgraph_kubernetes_001` | How can a LangGraph application be packaged as a service and deployed as a Kubernetes workload? | LangGraph + Kubernetes | Planned |
| `huggingface_qdrant_001` | How can embeddings from a Transformers model be stored and searched in Qdrant? | Hugging Face + Qdrant | Planned |
| `huggingface_fastapi_qdrant_001` | How can FastAPI generate embeddings with Transformers and search them in Qdrant? | Hugging Face + FastAPI + Qdrant | Planned |
| `huggingface_docker_001` | How can a Transformers inference application be packaged with Docker? | Hugging Face + Docker | Planned |
| `huggingface_kubernetes_001` | How can a containerized Transformers inference service run on Kubernetes? | Hugging Face + Kubernetes | Planned |
| `docker_kubernetes_001` | How does a Docker container image become a running workload in Kubernetes? | Docker + Kubernetes | Planned |
| `docker_kubernetes_config_001` | How should configuration be separated between a Docker image and Kubernetes runtime configuration? | Docker + Kubernetes | Planned |
| `docker_kubernetes_health_001` | How should container health behavior be configured when running Docker images in Kubernetes? | Docker + Kubernetes | Planned |
| `qdrant_docker_001` | How can Qdrant be run as a Docker container with persistent storage? | Qdrant + Docker | Planned |
| `qdrant_kubernetes_001` | How could a Qdrant service be deployed and exposed in Kubernetes? | Qdrant + Kubernetes | Planned |
| `rag_stack_001` | How can FastAPI, LangGraph, Transformers, and Qdrant work together in a RAG service? | FastAPI + LangGraph + Hugging Face + Qdrant | Planned |

---

# 13. Final Target Distribution

Once all ground truth is verified:

| Category | Cases | Share |
|---|---:|---:|
| Semantic | 20 | 20% |
| Lexical | 20 | 20% |
| Ambiguous | 20 | 20% |
| Version-specific | 20 | 20% |
| Cross-tool | 20 | 20% |
| **Total** | **100** | **100%** |

---

# 14. Evaluation Metrics

The benchmark should report:

## Ranking Metrics

```text
Hit@1
Hit@3
Hit@5
Hit@10
MRR
```

## Multi-Relevance Metrics

```text
Recall@3
Recall@5
Recall@10
```

## Graded-Relevance Metrics

```text
nDCG@3
nDCG@5
nDCG@10
```

---

# 15. Per-Category Evaluation

Every retrieval strategy must report metrics independently for:

```text
semantic
lexical
ambiguous
version_specific
cross_tool
```

Example:

| Strategy | Semantic MRR | Lexical MRR | Ambiguous MRR | Version MRR | Cross-tool MRR |
|---|---:|---:|---:|---:|---:|
| Dense | — | — | — | — | — |
| BM25 | — | — | — | — | — |
| Weighted RRF | — | — | — | — | — |
| Multi-Query | — | — | — | — | — |

---

# 16. Macro Metrics

In addition to overall metrics, the benchmark should report macro-average
metrics.

Example:

```text
Macro MRR
=
(
    semantic MRR
    + lexical MRR
    + ambiguous MRR
    + version-specific MRR
    + cross-tool MRR
) / 5
```

Macro metrics ensure every query category contributes equally even if the
benchmark composition changes in the future.

---

# 17. Ground-Truth Expansion Workflow

The 100-case plan should not be activated all at once.

Recommended workflow:

```text
Plan query
    ↓
Search current corpus
    ↓
Inspect candidate documents
    ↓
Assign relevance grades
    ↓
Mark needs_review
    ↓
Manual verification
    ↓
Mark active
```

Suggested verification batches:

```text
Batch 1: Lexical
Batch 2: Ambiguous
Batch 3: Version-specific
Batch 4: Cross-tool
Batch 5: Remaining semantic cases
```

The plan can contain all 100 cases immediately, but only verified cases
participate in official benchmark results.

---

# 18. Retrieval Strategies to Benchmark

Every completed benchmark version should evaluate at least:

```text
Dense Retrieval
BM25 Retrieval
Weighted RRF
Weighted Multi-Query
```

Experimental strategies may include:

```text
Cross-Encoder Reranking
Multi-Query + Reranking
Adaptive Query Rewriting
Parent-Child Retrieval
```

---

# 19. Benchmark Integrity Rules

Once the 100-case benchmark is finalized:

1. Do not repeatedly tune retrieval weights against all 100 cases.
2. Freeze the benchmark.
3. Preserve historical result reports.
4. Prefer development and held-out splits for future tuning.
5. Never change ground truth simply because a retriever performs poorly.
6. Any ground-truth correction must be justified by documentation evidence.
7. Generated query rewrites used for evaluation must remain frozen.

---

# 20. Future Train / Development / Test Split

Once enough cases exist, the dataset may be divided into:

```text
Development set
Held-out test set
```

For example:

```text
60 development cases
40 held-out cases
```

or expanded beyond 100 cases so that a larger held-out benchmark can be
maintained.

The held-out set should not be used for tuning retrieval weights.

---

# 21. Current Benchmark Baseline

Expanded Benchmark v1 currently contains:

```text
15 active cases
```

Current results:

| Strategy | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR |
|---|---:|---:|---:|---:|---:|
| Dense | 0.4667 | 0.7333 | 0.9333 | 1.0000 | 0.6611 |
| BM25 | 0.5333 | 0.8000 | 0.8667 | 1.0000 | 0.6929 |
| Weighted RRF | 0.5333 | 0.8667 | **1.0000** | 1.0000 | 0.7078 |
| Weighted Multi-Query | 0.5333 | 0.8667 | 0.8667 | 1.0000 | **0.7083** |

These values serve as the checkpoint before the balanced 100-case benchmark
is introduced.

---

# 22. Next Step

The next implementation milestone is:

```text
Ground Truth Expansion — Lexical Category
```

Current lexical cases:

```text
2 / 20 verified
```

The remaining lexical cases should be investigated against the current corpus
before activation.

Retriever tuning should remain paused while the benchmark is being expanded.