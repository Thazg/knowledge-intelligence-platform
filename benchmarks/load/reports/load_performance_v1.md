# Load & Performance Testing v1

## 1. Overview

This report characterizes the local production-style runtime behavior of the Enterprise Knowledge Intelligence Platform RAG API under steady-state, burst, periodic, and stochastic request patterns.

The goal is not to establish a universal system capacity number. The goal is to measure the behavior of the current frozen runtime topology, identify the practical no-rejection operating region, verify overload handling, and document production implications.

### Runtime under test

- API process topology: 1 Uvicorn process
- Generation concurrency: 1 slot
- Generation timeout: 120 seconds
- Generator: Ollama `qwen3:4b-instruct`
- Retrieval: Dense + BM25 weighted RRF
- Dense weight: 0.7
- BM25 weight: 0.3
- RRF k: 60
- Retrieval top-k: 10
- Context max sources: 6
- Context max tokens: 4000
- Qdrant collection: `enterprise_knowledge_fixed_bge_small`
- Embedding model: `BAAI/bge-small-en-v1.5`
- Representative query: `What is a Kubernetes Deployment?`

No Locust or k6 dependency was added. The benchmark uses a lightweight Python runner built with `httpx.AsyncClient`, asyncio, deterministic request IDs, latency summaries, and JSON output. Prometheus is used as an independent server-side observability cross-check.

---

## 2. Runtime Topology

The API uses one cached RAG service instance in one Uvicorn process. The Ollama generator protects generation with a process-local bounded semaphore configured for one concurrent generation.

Effective generation capacity for this topology is therefore:

```text
API processes = 1
generation slots per process = 1
effective concurrent generations = 1
```

Generation admission occurs at the generator boundary, after retrieval, context construction, and prompt preparation. As a result, requests that are eventually rejected as busy may still consume retrieval work before the generation slot is checked.

This behavior is important when interpreting overload tests.

---

## 3. Methodology

Four complementary load shapes were used.

### 3.1 Warm steady-state baseline

A closed-loop single-client run measured normal warm performance without concurrency pressure.

### 3.2 Burst concurrency

Small fixed request sets were released concurrently at C=2, C=5, and C=10 to validate generation admission behavior and rejection latency.

### 3.3 Fixed-periodic open-loop arrivals

Requests were scheduled independently of response completion at fixed arrival intervals. This was used to identify the observed no-rejection operating region under regular traffic.

### 3.4 Poisson open-loop arrivals

Requests were scheduled using exponential inter-arrival times with deterministic seeds. This approximates burstier stochastic traffic and tests sensitivity to arrival clustering.

Three seeds were used:

- `20260816`
- `20260817`
- `20260818`

The Poisson runs use the same target rates and duration per point so that rate-level behavior can be compared across seeds.

### 3.5 Measurement rules

- Warm-up requests are excluded from measured results.
- Client timeout is longer than the server generation timeout.
- Each measured request carries a unique `X-Request-ID`.
- `503` responses matching the production busy-detail message are classified as `busy`.
- Other `503` responses are classified separately as `dependency_503`.
- Successful responses expose retrieval, context-build, generation, and end-to-end stage timings.
- Scheduler launch lag is measured for open-loop workloads.
- Raw local outputs remain in `.benchmark-results/`; canonical results are summarized in this report and the paired JSON file.

---

## 4. Warm Steady-State Baseline

A 10-request C=1 run produced:

| Metric | Result |
|---|---:|
| Requests | 10 |
| Success | 10 / 10 |
| Busy | 0 |
| Success rate | 100% |
| Successful throughput | 0.3038 answers/s |
| Client mean | 3291.43 ms |
| Client P95 | 3311.34 ms |
| Retrieval mean | 77.44 ms |
| Generation mean | 3209.54 ms |
| Server E2E mean | 3287.05 ms |
| Server E2E P95 | 3306.94 ms |

Generation accounts for approximately 97.6% of successful server-side end-to-end latency in this run.

The reciprocal of the measured throughput is approximately 3.29 seconds per successful answer.

### Cold versus warm behavior

An early warm-up required approximately 26.4 seconds before the model was resident, while measured warm requests were approximately 3.3 seconds.

Later warm-ups also showed cold-start values around 24-33 seconds when the model had unloaded between runs.

Cold-start latency is therefore intentionally separated from steady-state latency.

---

## 5. Burst Overload

Burst tests produced:

| Concurrency | 200 | Busy 503 | Busy rate | Success E2E | Busy latency |
|---:|---:|---:|---:|---:|---:|
| 2 | 1 | 1 | 50% | ~3.78 s | ~336 ms |
| 5 | 1 | 4 | 80% | ~3.57 s | ~632 ms |
| 10 | 1 | 9 | 90% | ~3.86 s | ~1.28 s |

The effective generation capacity remained one request at a time.

Increasing burst concurrency did not increase useful throughput. Instead, excess requests were rejected with controlled `503 busy` responses.

No crash, client timeout, request-ID mismatch, or uncontrolled server error was observed in these burst tests.

The increasing busy latency under larger bursts is consistent with requests performing work before generation admission.

---

## 6. Closed-Loop Zero-Backoff Stress

A 30-second C=2 duration test generated a zero-backoff retry pattern:

- 317 total requests
- 9 successes
- 308 busy rejections
- 97.2% busy rate
- 0.2926 successful answers/s
- 0 request-ID mismatches

This scenario is intentionally treated as a stress case rather than a realistic user workload.

It demonstrates that a client retrying immediately on `503` can generate substantial pre-admission request pressure while useful generation throughput remains near the single-slot baseline.

The API remained stable and rejected excess work rather than accumulating an unbounded generation queue.

---

## 7. Fixed-Periodic Capacity Characterization

The most useful stable points were:

| Target rate | Observed result | Interpretation |
|---:|---|---|
| 0.20 RPS | 12/12 success | Stable |
| 0.25 RPS | 15/15 success | Stable |
| 0.30 RPS | 9/18 success, 9 busy | Rejection observed |
| 0.35 RPS | 11/22 success, 11 busy | Phase-locked overlap |
| 0.50 RPS | 15/30 success, 15 busy | Saturated |

A diagnostic rerun at 0.35 RPS showed the exact sequence:

```text
success -> busy -> success -> busy -> ...
```

The scheduler P95 launch lag was approximately 18.6 ms, so the behavior was not caused by load-generator drift.

At 0.35 RPS, arrivals occur roughly every 2.86 seconds, while successful generation takes roughly 3.7-3.8 seconds. A request therefore frequently arrives while the single generation slot is still occupied.

### Periodic conclusion

The observed no-rejection operating region for regular periodic traffic extends through 0.25 RPS.

Admission rejection appears between 0.25 and 0.30 RPS for this runtime and representative query.

This report intentionally does **not** claim that system capacity is exactly 0.25 RPS.

---

## 8. Poisson / Bursty Traffic

Three deterministic seeds were run at each target rate for 120 seconds.

### 8.1 Per-seed results

| Target | Seed | Arrivals | Success | Busy | Success rate |
|---:|---:|---:|---:|---:|---:|
| 0.20 | 20260816 | 20 | 13 | 7 | 65.0% |
| 0.20 | 20260817 | 20 | 14 | 6 | 70.0% |
| 0.20 | 20260818 | 23 | 15 | 8 | 65.2% |
| 0.25 | 20260816 | 26 | 9 | 17 | 34.6% |
| 0.25 | 20260817 | 32 | 17 | 15 | 53.1% |
| 0.25 | 20260818 | 32 | 17 | 15 | 53.1% |
| 0.30 | 20260816 | 36 | 13 | 23 | 36.1% |
| 0.30 | 20260817 | 38 | 19 | 19 | 50.0% |
| 0.30 | 20260818 | 42 | 19 | 23 | 45.2% |

### 8.2 Pooled results

| Target | Total arrivals | Success | Busy | Pooled success rate | Pooled busy rate |
|---:|---:|---:|---:|---:|---:|
| 0.20 RPS | 63 | 42 | 21 | 66.7% | 33.3% |
| 0.25 RPS | 90 | 43 | 47 | 47.8% | 52.2% |
| 0.30 RPS | 116 | 51 | 65 | 44.0% | 56.0% |

Scheduler P95 launch lag remained approximately 15-20 ms across these runs.

No request-ID mismatch was observed.

### Poisson conclusion

Burstiness materially reduces acceptance even when the long-run average arrival rate is below the periodic no-rejection region.

This is expected for the current topology:

```text
request
  -> retrieval
  -> generation admission
       -> slot free: generate
       -> slot busy: 503
```

With one generation slot and no queue, closely spaced arrivals can collide even when average RPS is relatively low.

---

## 9. Resource & Observability Validation

Post-test runtime validation showed:

- API restart count: `0`
- `/ready`: `ready`
- RAG service: `ready`
- Qdrant: `ready`
- Ollama: `ready`

### Post-run resource snapshot

| Service | Memory snapshot |
|---|---:|
| API | ~1.03 GiB |
| Qdrant | ~519 MiB |
| Grafana | ~182 MiB |
| Prometheus | ~28 MiB |
| Ollama | ~40 MiB |

These values are **post-run snapshots**, not peak-load measurements. Ollama had already released the resident model at the time of the snapshot, so its value must not be interpreted as inference-time peak memory.

### Prometheus correlation

Prometheus reported:

- `POST /v1/query 200`: 107
- `POST /v1/query 503`: 86
- `rag_queries_total{status="success"}`: 107
- `rag_queries_total{status="error"}`: 86
- `rag_query_errors_total{error_type="DependencyBusyError"}`: 86

Therefore all 86 recorded RAG errors in this runtime window were controlled busy-admission errors.

The HTTP request histogram counted all 193 POST requests.

However:

- retrieval histogram count: 107
- generation histogram count: 107
- end-to-end RAG histogram count: 107

These stage histograms therefore represent the successful path only and do not capture work performed by requests that are eventually rejected as busy.

This is an observability gap worth documenting for future improvement.

---

## 10. Key Findings

1. **Generation is the dominant latency component.**  
   Warm successful requests spend approximately 3.2-3.8 seconds in generation, while retrieval is typically tens to low hundreds of milliseconds.

2. **Single-slot admission control prevents unbounded generation concurrency.**  
   Burst traffic produces deterministic busy rejection instead of queue growth or API instability.

3. **Useful throughput does not scale with request concurrency in the current topology.**  
   Additional concurrency mostly increases controlled rejection.

4. **Regular traffic is materially easier to serve than bursty traffic.**  
   Periodic traffic was rejection-free through the observed 0.25 RPS point, while stochastic arrivals produced meaningful busy rejection even at a 0.20 RPS target.

5. **Admission occurs late in the pipeline.**  
   Busy requests can still consume retrieval work before being rejected at generation.

6. **The runtime remained stable during characterization.**  
   No API restart occurred, readiness remained healthy, request IDs remained consistent, and observed overload errors were normalized as `DependencyBusyError`.

7. **Current stage metrics exclude rejected-query stage cost.**  
   HTTP-level metrics capture all traffic, while retrieval/generation/E2E histograms currently reflect only successful queries.

---

## 11. Limitations

These results characterize one specific local runtime and should not be generalized beyond it without remeasurement.

Key limitations:

- Single local machine
- GTX 1660 Ti 6 GB GPU
- One API process
- One concurrent generation slot
- One representative benchmark query
- Small samples for some percentile estimates
- Cold-start behavior varies depending on model residency
- Docker resource snapshots were taken after runs, not continuously at peak load
- Stage histograms exclude rejected-query work
- Periodic results are sensitive to service-time/arrival phase relationships
- Poisson results have stochastic variance despite use of three deterministic seeds
- No distributed load generator was used
- No multi-instance API or multi-generator scaling was tested

---

## 12. Production Implications

The current design is suitable for a low-throughput deployment where predictable overload rejection is preferred over unbounded queueing.

For higher burst tolerance or throughput, future work should evaluate the following as separate design decisions rather than apply them blindly:

- admission before expensive retrieval work;
- bounded queueing with explicit latency budgets;
- more than one generation slot when hardware capacity permits;
- multiple API/generation workers with globally coherent capacity controls;
- improved busy/backpressure semantics for clients;
- rejected-path stage-cost metrics;
- continuous CPU/GPU/memory sampling during benchmark windows.

Any such optimization should follow the project rule:

```text
baseline -> targeted hypothesis -> smallest change -> verification -> comparison
```

---

## 13. Decision

**Load & Performance Testing v1 is complete.**

The current runtime has been characterized across warm steady-state, burst overload, fixed-periodic capacity, stochastic Poisson arrivals, and post-test observability/resource validation.

The benchmark runner is sufficient for this milestone; no Locust or k6 dependency is required.

The canonical performance conclusion is:

> The current single-generation deployment serves regular periodic traffic without observed admission rejection through 0.25 RPS in the measured local configuration, with rejection appearing between 0.25 and 0.30 RPS. Bursty stochastic traffic materially reduces acceptance even below that periodic region because generation capacity is limited to one slot with no queue, while the service remains stable and rejects overload with controlled `503` responses.
