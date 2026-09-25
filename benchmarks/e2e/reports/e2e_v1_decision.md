# E2E RAG Validation v1 — Final Decision

## Decision

**Validation milestone status:** COMPLETE

**E2E v1 release gate:** NOT PASSED

The production RAG path completed runtime and structural validation successfully, but the frozen human semantic evaluation identified one blocking failure in ambiguous-query handling.

The correct engineering decision is therefore to close E2E Validation v1 as a completed evaluation milestone while **not declaring the current RAG behavior semantically release-ready**.

## Scope

E2E v1 validates the canonical user-facing path:

Client → FastAPI → RAGService → RAGPipeline → Weighted RRF retrieval → ContextBuilder → Prompt v3 → Ollama generation → HTTP response

The benchmark contains 18 frozen cases across six categories:

- semantic: 3
- lexical: 3
- ambiguous: 3
- version_specific: 3
- cross_tool: 3
- insufficient: 3

Expected behaviors:

- answer_with_evidence: 12
- qualified_answer: 3
- insufficient_evidence: 3

## Runtime validation

### Canonical run #1

The first canonical run exposed production-relevant infrastructure failures.

Observed sequence:

1. Cases `e2e-001` through `e2e-015` completed successfully.
2. `e2e-016` encountered a transient Qdrant/Docker DNS resolution failure.
3. The original benchmark runner timed out client-side while server-side processing continued.
4. Subsequent requests were therefore contaminated by the degraded runtime.
5. Docker events confirmed an Ollama model-runner OOM during the failure window.

The first run was preserved as failed-run evidence and was not mixed with retries.

### Remediation

Two targeted runtime changes were made:

- benchmark runner changed to fail fast after the first runtime failure;
- WSL2 memory budget increased to `10GB`.

Observed Docker memory after restart:

`9.712 GiB`

A recovery smoke test then completed successfully with no new Ollama OOM event.

### Canonical run #2

Result:

- 18 / 18 cases completed
- 18 unique case IDs
- 0 transport errors
- 0 non-200 responses
- 0 request-ID mismatches
- 0 empty answers
- expected generation model used for all cases
- no Ollama OOM / kill / restart events observed

**Runtime verdict: PASS**

## Deterministic structural validation

Structural evaluator result:

- 18 / 18 structural pass
- 111 raw citations
- 111 valid citations
- 0 invalid citation IDs
- 0 citation-format violations
- 0 citation-to-source mapping errors
- 0 duplicate source citation IDs
- 0 missing required-evidence cases
- 0 missing benchmark cases
- 0 duplicate benchmark cases
- 0 unknown benchmark cases

The evaluator parses raw citation IDs independently from the API citation objects, so invalid raw citations cannot be hidden by response parsing.

**Structural verdict: PASS**

## Human semantic validation

Frozen human review result:

- PASS: 12 / 18
- PARTIAL: 5 / 18
- FAIL: 1 / 18
- pass rate: 66.7%
- pass-or-partial rate: 94.4%

Partial cases:

- `e2e-001`
- `e2e-005`
- `e2e-007`
- `e2e-008`
- `e2e-013`

Failing case:

- `e2e-009`

Blocking case:

- `e2e-009`

**Semantic verdict: FAIL**

## Breakdown by expected behavior

### answer_with_evidence

- 12 cases
- 9 PASS
- 3 PARTIAL
- 0 FAIL
- pass rate: 75.0%
- pass-or-partial rate: 100%

### insufficient_evidence

- 3 cases
- 3 PASS
- 0 PARTIAL
- 0 FAIL
- pass rate: 100%

This is a strong result. The system correctly refused to invent:

- exact Kubernetes CPU/memory sizing from request rate alone;
- HNSW settings guaranteed to achieve a laptop-specific latency target;
- a Docker image guaranteed to have no known vulnerabilities today.

### qualified_answer

- 3 cases
- 0 PASS
- 2 PARTIAL
- 1 FAIL
- pass rate: 0%
- pass-or-partial rate: 66.7%

This is the primary capability gap identified by E2E v1.

## Primary blocking finding

### `e2e-009`

Query:

> How should I handle long-running work in my API?

The query is intentionally underspecified.

Retrieved evidence drifted toward LangGraph-specific execution patterns. The generated answer then presented LangGraph tasks and heartbeat mechanisms as general API guidance without clearly qualifying the LangGraph assumption.

This violates the required `qualified_answer` behavior.

The problem is not simply that retrieval returned imperfect evidence. The generator failed to recognize that the evidence was narrower than the user's question and generalized implementation-specific guidance beyond the justified scope.

**Classification:** semantic blocker

## Other notable findings

### `e2e-001`

The answer correctly explained the purpose of Kubernetes startup probes overall, but contained a localized incorrect statement about restart timing after startup-probe failure.

### `e2e-005`

The core `envFrom` explanation was correct, but the answer added an unsupported claim implying dynamic environment-variable updates without container restart.

### `e2e-007`

The LangGraph persistence recommendation was technically supported, but the generic query did not establish that LangGraph was being used or what persistence lifetime was required.

The answer should have qualified those assumptions.

### `e2e-008`

The answer suggested static embeddings as a way to make vector search faster.

The exact retrieved evidence explicitly states that static embeddings do not make retrieval itself faster; they accelerate vector creation.

### `e2e-013`

The high-level separation between Qdrant retrieval and LangGraph workflow persistence was reasonable, but some claims were stronger than the directly retrieved evidence supported.

## Dimension-level findings

Mean score on a 0–2 scale:

- correctness: 1.7222
- faithfulness: 1.7222
- citation correctness: 1.7222
- citation completeness: 1.9444
- evidence sufficiency: 1.7222
- ambiguity handling: 0.6667
- multi-source synthesis: 1.6667
- abstention: 2.0000

The dominant weakness is therefore not citation mechanics or abstention.

It is **ambiguity handling and evidence-scope qualification**.

## Decision

E2E Validation v1 has successfully validated the complete production path and exposed a real behavioral weakness.

The system is:

- runtime-integrated;
- structurally reliable;
- citation-safe under the deterministic checks;
- strong at recognizing insufficient evidence;
- strong on version-specific questions;
- generally effective on direct evidence-backed questions;
- not yet reliable enough on ambiguous or underspecified questions.

Therefore:

**E2E v1 semantic release gate remains FAILED.**

This failure is retained as benchmark evidence and must not be erased by tuning against the frozen validation cases.

## Remediation policy

The frozen E2E v1 cases must not be used as a development tuning set.

Do not:

- rewrite `e2e-007`, `e2e-008`, or `e2e-009`;
- tune Prompt v3 specifically to those outputs;
- modify retrieval specifically to make these 18 cases pass;
- repeatedly rerun E2E v1 until it becomes green.

Instead:

1. preserve E2E v1 as historical validation evidence;
2. create a separate ambiguity-handling development set;
3. characterize failure modes on new development queries;
4. implement a general solution for underspecified-query qualification;
5. add targeted regression tests for the general behavior;
6. validate the remediation with a new untouched E2E validation set.

## Operational lessons from E2E v1

E2E validation also identified two production-engineering issues that earlier component tests did not expose:

1. client timeout did not cancel server-side work, allowing later benchmark requests to become contaminated;
2. Ollama model-runner memory pressure could fail generation even while the parent Ollama service remained running.

The benchmark runner was hardened with fail-fast behavior, and the local runtime memory budget was explicitly frozen.

These findings demonstrate why full HTTP-path E2E validation was necessary even though all individual RAG components had already been implemented and tested.

## Provenance

- Manifest SHA256: `2190EDA38BB4E849E2A4FF84B97EF07436455861FC93F10D9D716377D2D194FE`
- Canonical results SHA256: `5A8721341BED4A03A886996BC5A2F3BDEE0A5753691674980D1BF95A8B52F1A2`
- Structural report SHA256: `9D490C93CCFCA75592519659692FD6E1B9F8C2DECE0AF30C9C5CE84F41E9A3EC`
- Human review packet SHA256: `19785C3843939EA56177303595605DBB16875FFC2D1D3342FB8BF8D8BB76FEEF`
- Human scores SHA256: `899F303FE91E8F06B9BB6D01D6B2400C724BE26203B65EABFB29CE3F68863461`
- Semantic report SHA256: `591B4E55C2353C36FDB247AF066F9E7AA0866413216EF5B6DCE8987792878F58`
- Corpus SHA256: `574E06F89E9EB1B709E015D92A40DC646754004B78FBEDAE0BB77FAD4379B57A`

Canonical results:

`benchmarks/e2e/results_v1.jsonl`

Structural report:

`benchmarks/e2e/reports/e2e_structural_v1.json`

Human semantic scores:

`benchmarks/e2e/review/human_scores_v1.jsonl`

Semantic report:

`benchmarks/e2e/reports/e2e_semantic_v1.json`

## Next milestone

With E2E Validation v1 complete, the project proceeds to:

**Production Hardening**

The ambiguity-handling blocker remains an explicit remediation item and should be addressed using new development data rather than the frozen E2E v1 validation set.
