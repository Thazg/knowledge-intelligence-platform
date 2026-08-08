# Generation Benchmark v1

## 1. Overview

This benchmark evaluates the generation layer of the Enterprise AI Engineering Knowledge Platform.

The goal is to verify whether the end-to-end RAG pipeline can:

- answer factual questions using retrieved evidence,
- synthesize information across multiple sources,
- handle ambiguous questions conservatively,
- abstain when the available evidence is insufficient,
- produce valid citations,
- avoid unsupported claims,
- and maintain acceptable generation latency.

The benchmark contains 12 manually designed cases across 6 categories:

| Category | Cases |
|---|---:|
| Semantic | 2 |
| Lexical | 2 |
| Ambiguous | 2 |
| Version-specific | 2 |
| Cross-tool | 2 |
| Insufficient evidence | 2 |
| **Total** | **12** |

---

## 2. Pipeline Configuration

The evaluated pipeline is:

```text
User Query
    ↓
Weighted RRF Retrieval
    ↓
Top-10 Retrieved Chunks
    ↓
ContextBuilder
    ↓
PromptBuilder
    ↓
Qwen3 4B Instruct via Ollama
    ↓
Answer + Citations
```

### Retrieval

```text
Retriever: Weighted RRF
Dense weight: 0.7
BM25 weight: 0.3
RRF k: 60
Top-k: 10
```

### Context

```text
max_sources: 6
max_context_tokens: 4000
```

### Generator

```text
Model: qwen3:4b-instruct
Provider: Ollama
temperature: 0.0
num_predict: 384
```

---

## 3. Prompt Iteration

Three main benchmark iterations were used during prompt development.

### v1

Initial generation configuration used:

```text
num_predict = 280
```

The prompt successfully encouraged grounded answers and abstention, but several complex answers reached the output limit and were truncated.

Observed truncation included:

- gen-005
- gen-007
- gen-009
- gen-010

### v2

The output budget was increased to:

```text
num_predict = 384
```

Additional prompt rules were introduced for ambiguity handling and concise answers.

This improved ambiguous-query behavior, but the prompt became too aggressive in treating otherwise answerable questions as ambiguous. Some answers also became unnecessarily verbose.

### v3

The ambiguity and conciseness rules were refined.

The final prompt behavior emphasizes:

- directly answering sufficiently specified questions,
- treating a query as ambiguous only when missing information prevents a reliable answer,
- limiting ambiguous answers to high-level options,
- using only sources directly necessary for the answer,
- prioritizing answer completion over additional detail.

The final 12-case v3 benchmark had no output truncation. The highest completion length was 360 tokens, below the 384-token generation limit. :contentReference[oaicite:0]{index=0}

---

## 4. Final v3 Performance

### Token Usage

| Metric | Value |
|---|---:|
| Mean prompt tokens | 2954.25 |
| Mean completion tokens | 194.75 |
| Maximum completion tokens | 360 |

The 384-token output budget provides sufficient headroom for the current benchmark while keeping responses bounded. :contentReference[oaicite:1]{index=1}

### Latency

| Metric | Value |
|---|---:|
| Mean retrieval latency | 178.00 ms |
| Mean generation latency | 15,376.63 ms |
| Mean end-to-end latency | 15,554.84 ms |
| Median end-to-end latency | 17,609.48 ms |
| P95 end-to-end latency | 23,224.35 ms |

Generation dominates end-to-end latency, while retrieval remains comparatively small. Across the final run, retrieval was generally measured in hundreds of milliseconds whereas local LLM generation took several seconds to tens of seconds. :contentReference[oaicite:2]{index=2}

---

## 5. Case-Level Quality Review

| Case | Category | Result | Notes |
|---|---|---|---|
| gen-001 | Semantic | Pass | Grounded FastAPI dependency-injection explanation with relevant citations. |
| gen-002 | Semantic | Pass | Direct Kubernetes Deployment explanation without false ambiguity behavior. |
| gen-003 | Lexical | Pass | Correctly answers the explicit `kubectl create deployment` query. |
| gen-004 | Lexical | Pass | Grounded explanation of FastAPI Cloud. |
| gen-005 | Ambiguous | Partial | Useful answer, but still selects and lists many deployment technologies for an underspecified query. |
| gen-006 | Ambiguous | Partial | Provides useful scaling concepts but becomes overly specific to Kubernetes, Qdrant, and FastAPI. |
| gen-007 | Version-specific | Pass | Current FastAPI deployment guidance is summarized without truncation. |
| gen-008 | Version-specific | Pass | Grounded description of Kubernetes Deployments. |
| gen-009 | Cross-tool | Partial | Correctly avoids inventing unsupported FastAPI-on-Kubernetes instructions, but raw answer uses `[SOURCE N]` citation formatting despite prompt rules. |
| gen-010 | Cross-tool | Pass | Strong synthesis distinguishing Docker containerization from Kubernetes orchestration. |
| gen-011 | Insufficient evidence | Pass | Correctly refuses to fabricate project-specific Kubernetes YAML. |
| gen-012 | Insufficient evidence | Pass | Correctly refuses to infer future cloud-provider pricing from unrelated documentation. |

The final run therefore shows strong behavior for factual, lexical, version-specific, cross-tool, and insufficient-evidence queries, while ambiguous-query handling remains the clearest quality limitation. :contentReference[oaicite:3]{index=3}

---

## 6. Strong Behaviors

### Grounded answering

The system generally answers technical questions using retrieved documentation rather than relying on unsupported model knowledge.

For example, the Kubernetes Deployment cases use retrieved Kubernetes sources to explain desired state, ReplicaSets, rollouts, and self-healing behavior. :contentReference[oaicite:4]{index=4}

### Abstention

The strongest result in the benchmark is insufficient-evidence handling.

For the project-specific Kubernetes YAML case, the model explicitly states that the retrieved evidence does not contain enough information to construct the requested manifest instead of fabricating one. :contentReference[oaicite:5]{index=5}

The cloud-pricing case similarly refuses to identify a cheapest provider because the corpus does not contain the required pricing information. :contentReference[oaicite:6]{index=6}

### Cross-source synthesis

The Docker/Kubernetes case successfully distinguishes:

```text
Docker → application containerization
Kubernetes → orchestration and lifecycle management
```

while combining evidence from Docker and Kubernetes documentation. :contentReference[oaicite:7]{index=7}

---

## 7. Known Limitations

### Ambiguous-query handling

Queries such as:

```text
How should I deploy my API?
```

and:

```text
How do I make my application scalable?
```

remain challenging.

The retriever can return evidence from several valid but unrelated technology domains, after which the generator may attempt to synthesize too many of them into one answer. :contentReference[oaicite:8]{index=8}

This suggests that ambiguity handling is not exclusively a generation problem.

A future system could introduce:

```text
Query
  ↓
Intent / Ambiguity Classification
  ↓
Query Clarification or Routing
  ↓
Retrieval
```

rather than relying entirely on prompt instructions.

### Citation format compliance

The cross-tool FastAPI/Kubernetes case still produced raw citations such as:

```text
[SOURCE 3]
[SOURCE 6]
```

despite explicit instructions requiring `[3]` and `[6]`.

The citation parser currently handles this defensively, but raw-format compliance should be tracked separately from citation extraction success. :contentReference[oaicite:9]{index=9}

### Local inference latency

Local Qwen3 4B inference is the dominant latency component.

The current setup prioritizes:

- zero external API cost,
- local execution,
- reproducibility,
- provider independence,

rather than minimum serving latency.

Production optimization can later evaluate alternatives such as more optimized serving runtimes or different local models.

---

## 8. Production Candidate

The Generation v1 production candidate is:

```text
Retrieval
--------
Weighted RRF
Dense weight = 0.7
BM25 weight = 0.3
RRF k = 60

Context
-------
max_sources = 6
max_context_tokens = 4000

Generator
---------
qwen3:4b-instruct
Ollama
temperature = 0.0
num_predict = 384

Prompt
------
Prompt v3
```

This configuration provides the best balance observed during the current development benchmark between:

- grounding,
- citation behavior,
- answer completeness,
- abstention,
- ambiguity handling,
- bounded output length.

---

## 9. Decision

Prompt tuning is stopped after v3.

Further tuning against the same 12 benchmark cases risks overfitting the prompt to the evaluation set.

Future improvements should focus on structural system changes rather than repeatedly adjusting prompt wording.

The highest-priority future areas are:

1. explicit ambiguity / intent handling,
2. citation-format validation,
3. automated generation-quality evaluation,
4. local inference latency optimization,
5. a larger independently curated generation benchmark.

---

## 10. Conclusion

Generation Benchmark v1 demonstrates that the end-to-end RAG pipeline can retrieve evidence, construct bounded context, generate grounded technical answers, attach citations, and abstain when the corpus is insufficient.

The final v3 configuration eliminates the truncation problems observed in earlier prompt iterations while preserving strong insufficient-evidence behavior.

The remaining weaknesses are primarily ambiguous-query handling, citation-format compliance, and local generation latency.

Generation v1 is therefore considered sufficiently stable to proceed to the next system layer.