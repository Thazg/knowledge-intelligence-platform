# E2E Human Semantic Review v1

## Frozen input

- Cases: `benchmarks/e2e/cases_v1.jsonl`
- Results: `benchmarks/e2e/results_v1.jsonl`
- Corpus: `data/processed/chunks_fixed.jsonl`
- Results SHA256: `5A8721341BED4A03A886996BC5A2F3BDEE0A5753691674980D1BF95A8B52F1A2`
- Corpus SHA256: `574E06F89E9EB1B709E015D92A40DC646754004B78FBEDAE0BB77FAD4379B57A`

## Review policy

Judge only from the query, answer, and exact retrieved evidence shown below.
Do not silently use external knowledge to repair unsupported claims.

The evidence content is reconstructed from the canonical chunk corpus using the exact chunk_id returned by the canonical E2E HTTP run.

Scores: `2 = pass`, `1 = partial`, `0 = fail`, `N/A = not applicable`.

---

# e2e-001

**Category:** `semantic`

**Expected behavior:** `answer_with_evidence`

## Query

Why can a startup probe prevent a slow-starting Kubernetes container from being restarted too early?

## Model answer

A startup probe prevents a slow-starting Kubernetes container from being restarted too early because it is only executed at startup and allows the application time to complete its initialization before any other probes (such as liveness or readiness) are run [1]. Unlike liveness and readiness probes, which are periodic and may trigger restarts before the container is fully ready, the startup probe ensures that Kubernetes does not execute these probes until the application has successfully started [1][2]. As a result, if the startup probe fails, the container is restarted only after the startup phase is complete, preventing premature restarts due to initialization delays [5]. This mechanism enables containers to warm up caches or load data without being interrupted by early probe failures [1].

## API citations

```json
[
  {
    "citation_id": "1",
    "document_id": "d19cca3025dbdd3a53f170ac028946eb32bdebab0fc97bfc8e9da71e15e10b62",
    "chunk_id": "4b906e979b9b41f328920b287bc68a988b6b7cbd9ccad938dd45fb9f48c583dc"
  },
  {
    "citation_id": "2",
    "document_id": "f204e7064c8daf099e0a58c360cbc7a27600fc0fdbc54a0ca3cb8be7b4370043",
    "chunk_id": "32ef943dcbdbc6c4ef511fb9729d8240f2d2993eb478c8734e99ce5f2994a6c2"
  },
  {
    "citation_id": "5",
    "document_id": "2bf1d62603779b8160b51fb9fd0a1f0b5614a1012638b527b0a4cd7870ada8ab",
    "chunk_id": "cd7bb5595a76592fb96074e8189943c414ea360f0c300b9cb160d32e4f4f460c"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `kubernetes`
- Title: `Pod Lifecycle`
- Document ID: `d19cca3025dbdd3a53f170ac028946eb32bdebab0fc97bfc8e9da71e15e10b62`
- Chunk ID: `4b906e979b9b41f328920b287bc68a988b6b7cbd9ccad938dd45fb9f48c583dc`

```text
or makes a network request.

Based on the probe results, Kubernetes can restart unhealthy containers
or stop sending traffic to containers that are not ready.

The kubelet can optionally perform and react to three kinds of probes on running
containers, each serving a different purpose. For probe mechanisms (`exec`,
`grpc`, `httpGet`, `tcpSocket`), configuration fields, and detailed usage
guidance, see [Liveness, Readiness, and Startup Probes](/docs/concepts/workloads/pods/probes/).

### Startup probe

Startup probes verify whether the application within a container is started.
If a startup probe is configured, Kubernetes does not execute liveness or
readiness probes until the startup probe succeeds, allowing the application
time to finish its initialization.

This type of probe is only executed at startup, unlike liveness and readiness
probes, which are run periodically.

If the startup probe fails, the kubelet kills the container, and the container
is subjected to its [restart policy](/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy).

### Liveness probe

Liveness probes determine when to restart a container.
For example, liveness probes could catch a deadlock, where an application is
running, but unable to make progress. Restarting a container in such a state
can help to make the application more available despite bugs.

If a container fails its liveness probe more times than the configured tolerance,
the kubelet restarts that container.
Liveness probes do not wait for readiness probes to succeed. If you want to
wait before executing a liveness probe, you can either define
`initialDelaySeconds` or use a startup probe.

### Readiness
```

### Source [2]

- Source: `kubernetes`
- Title: `Liveness, Readiness, and Startup Probes`
- Document ID: `f204e7064c8daf099e0a58c360cbc7a27600fc0fdbc54a0ca3cb8be7b4370043`
- Chunk ID: `32ef943dcbdbc6c4ef511fb9729d8240f2d2993eb478c8734e99ce5f2994a6c2`

```text
the initial delay.

## Configuration fields {#configure-probes}

[Probes](/docs/reference/generated/kubernetes-api/{{< param "version" >}}/#probe-v1-core)
have a number of fields that you can use to more precisely control the behavior of startup,
liveness and readiness checks. For example:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: probe-example
spec:
  containers:
  - name: app
    image: registry.k8s.io/e2e-test-images/agnhost:2.40
    ports:
    - containerPort: 8080
    startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      failureThreshold: 30
      periodSeconds: 10
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      periodSeconds: 5
```

`initialDelaySeconds`
: Number of seconds after the container has started before startup, liveness or readiness probes are initiated. If a startup probe is defined, liveness and readiness probe delays do not begin until the startup probe has succeeded. In some older Kubernetes versions, the initialDelaySeconds might be ignored if periodSeconds was set to a value higher than initialDelaySeconds. However, in current versions, initialDelaySeconds is always honored and the probe will not start until after this initial delay. Defaults to 0 seconds. Minimum value is 0.

`periodSeconds`
: How often (in seconds) to
```

### Source [3]

- Source: `kubernetes`
- Title: `Configure Liveness, Readiness and Startup Probes`
- Document ID: `eb567743c33204ccd497f87cb637f34805e599a60a3066fa55044f2c94677228`
- Chunk ID: `630eb4d3d7b13d3e129a41d72f0dbfc647058bb4cd4bed8399ae8ba355232beb`

```text
traffic does not reach a container that is not ready
for it, and that containers are restarted when they fail.

## {{% heading "whatsnext" %}}

* Learn more about
  [Liveness, Readiness and Startup Probes](/docs/concepts/workloads/pods/probes/).
* For the full specification of probe-related fields, see the API reference:
  [Pod](/docs/reference/kubernetes-api/workload-resources/pod-v1/),
  [Container](/docs/reference/kubernetes-api/workload-resources/pod-v1/#Container),
  [Probe](/docs/reference/kubernetes-api/workload-resources/pod-v1/#Probe)
```

### Source [4]

- Source: `kubernetes`
- Title: `What Happens After A Node Restart`
- Document ID: `4ae290a762c0503d337b49a3355c7f9417ac141b45db1a198ae82e96a41eb582`
- Chunk ID: `be4a9a30a81d304d622d1de5978d79291fa3279cd777ede644b5e36f83a40296`

```text
` [probes](/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)
  fail for the duration of the restart, because the kubelet cannot run commands
  inside containers. With a short timeout and failure threshold, a failing
  liveness probe can cause a container to be restarted, and a failing readiness
  probe can cause the Pod to flap out of the `Ready` state.

* The node is reported as `NotReady` by the kubelet, which blocks scheduling of
  new Pods onto the node.

* Container operations such as restarts, initialization, and status updates are
  delayed until the runtime is available again.

* If an
  {{< glossary_tooltip term_id="init-container" text="init container" >}} was executing
  when the runtime restarted, its execution state can be lost, in which case the
  init container runs again.

* In rare cases, interrupting an operation at a precise moment can leave state
  inconsistent:

  * An interrupted image pull may leave inconsistent image layers, which can
    render the image unusable until it is pulled again.

  * An interrupted sandbox creation, if it is terminated in the middle of a CNI
    or NRI call, may leave the sandbox in an inconsistent state, with CNI only
    partially initialized and the possibility of a resource leak.

Interrupting an operation at a precise moment is a low-probability situation, so
restarting a container runtime is generally a safe operation. On a heavily loaded
node, where every operation is slower, the window for interrupting a critical
operation is larger and the probability of hitting one of these edge cases
increases.

## Impact of a node reboot

A node reboot is the most disruptive of these events, because every container on
the node stops. A reboot encompasses both a container runtime
```

### Source [5]

- Source: `kubernetes`
- Title: `Pod`
- Document ID: `2bf1d62603779b8160b51fb9fd0a1f0b5614a1012638b527b0a4cd7870ada8ab`
- Chunk ID: `cd7bb5595a76592fb96074e8189943c414ea360f0c300b9cb160d32e4f4f460c`

```text
or not. Constraints on the rules: - At most 20 rules are allowed. - Rules can have the same action. - Identical rules are not forbidden in validations. When rules are specified, container MUST set RestartPolicy explicitly even it if matches the Pod's RestartPolicy.</td>
    </tr>
    <tr>
      <td><code>securityContext</code><br/><em><a href="{{< ref "#SecurityContext" >}}">SecurityContext</a></em></td>
      <td>SecurityContext defines the security options the container should be run with. If set, the fields of SecurityContext override the equivalent fields of PodSecurityContext. More info: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/</td>
    </tr>
    <tr>
      <td><code>startupProbe</code><br/><em><a href="{{< ref "#Probe" >}}">Probe</a></em></td>
      <td>StartupProbe indicates that the Pod has successfully initialized. If specified, no other probes are executed until this completes successfully. If this probe fails, the Pod will be restarted, just as if the livenessProbe failed. This can be used to provide different probe parameters at the beginning of a Pod's lifecycle, when it might take a long time to load data or warm a cache, than during steady-state operation. This cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-
```

### Source [6]

- Source: `kubernetes`
- Title: `Running ZooKeeper, A Distributed System Coordinator`
- Document ID: `73bcb070bcbbdb38d4d5a8cd683ecb4ae445ceb33d5e54c541c8ef0e60278a45`
- Chunk ID: `f6798722168b27d82789b3d677364d4a39b8ff5778d3503f3e4486fd2b895f86`

```text
the ZooKeeper process in Pod `zk-0` with the following command.

```shell
kubectl exec zk-0 -- pkill java
```

The termination of the ZooKeeper process caused its parent process to terminate. Because the `RestartPolicy` of the container is Always, it restarted the parent process.

```
NAME      READY     STATUS    RESTARTS   AGE
zk-0      1/1       Running   0          21m
zk-1      1/1       Running   0          20m
zk-2      1/1       Running   0          19m
NAME      READY     STATUS    RESTARTS   AGE
zk-0      0/1       Error     0          29m
zk-0      0/1       Running   1         29m
zk-0      1/1       Running   1         29m
```

If your application uses a script (such as `zkServer.sh`) to launch the process
that implements the application's business logic, the script must terminate with the
child process. This ensures that Kubernetes will restart the application's
container when the process implementing the application's business logic fails.

### Testing for liveness

Configuring your application to restart failed processes is not enough to
keep a distributed system healthy. There are scenarios where
a system's processes can be both alive and unresponsive, or otherwise
unhealthy. You should use liveness probes to notify Kubernetes
that your application's processes are unhealthy and it should restart them.

The Pod `template` for the `zk` `StatefulSet` specifies a liveness probe.

```yaml
  livenessProbe:
    exec:
      command:
      - sh
      - -c
      - "zookeeper-ready 2181"
    initialDelaySeconds: 15
    timeoutSeconds: 5
```

The probe calls a bash script that uses
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-002

**Category:** `semantic`

**Expected behavior:** `answer_with_evidence`

## Query

How are LangGraph checkpoints and long-term memory different when preserving information across executions?

## Model answer

LangGraph checkpoints and long-term memory differ in scope and purpose when preserving information across executions. Checkpoints provide short-term, thread-scoped memory that tracks the ongoing conversation and graph state within a single execution session, enabling continuity across steps, interruption recovery, and time travel [1][2]. They are used to resume execution after a failure or interruption and maintain message history within a thread [4][5]. In contrast, long-term memory is stored in a separate store and persists across threads and sessions, allowing retrieval of user-specific or application-level data (e.g., preferences, profiles) regardless of the current thread or session [1][2][3]. This enables shared, durable knowledge that can be accessed across multiple interactions and runs [3][5]. Thus, checkpoints preserve state within a thread for continuity and fault tolerance, while long-term memory stores persistent, cross-thread data for broader application-level recall [1][2].

## API citations

```json
[
  {
    "citation_id": "1",
    "document_id": "43a6d508fe857efc43952bc9e98567ed4d5c6c23351e2099402cd27e3448bdfe",
    "chunk_id": "4395607499ae4f3188b300dea45ca6fefa8ef4a8d256d606ce8862a38e3b05f4"
  },
  {
    "citation_id": "2",
    "document_id": "89cceb7d2e06b8c7149f6154fe4c198084bc94781c7cd001b215040c4bd251c7",
    "chunk_id": "955aa4d98603d27d2b929cfe4ac6bea1e66955c74e3b049154024e02602e93bd"
  },
  {
    "citation_id": "4",
    "document_id": "76c834cdabd7f08af4191f0d2bac6ec2545821679863c6d3b6a06d4a019012d5",
    "chunk_id": "70efec76518e21ad8f895de469b2d0a47cb1377f7577e2689051673dbcc2cf3a"
  },
  {
    "citation_id": "5",
    "document_id": "78e9959749656104e11b8f24b1a9bb6583073cfb394868784873866348956403",
    "chunk_id": "6c106efdb52e42ae53e619a7a3e691a6eacf48ab0531f200d8b78f2a99e7f384"
  },
  {
    "citation_id": "3",
    "document_id": "176fc6ab3f3c445b4224ee303b9d727645f48cafdc8634047059d209ba798b44",
    "chunk_id": "cb9825a657907b271bd10e857fb7a21b0f83feaec8fc1c158c70585483b28de7"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `langchain`
- Title: `Persistence`
- Document ID: `43a6d508fe857efc43952bc9e98567ed4d5c6c23351e2099402cd27e3448bdfe`
- Chunk ID: `4395607499ae4f3188b300dea45ca6fefa8ef4a8d256d606ce8862a38e3b05f4`

```text
---
title: Persistence
description: LangGraph's persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
---

{/* Anchor stubs for backwards-compatible deep links */}
<a id="checkpoints" />
<a id="threads" />
<a id="memory-store" />
<a id="checkpointer-libraries" />
<a id="pending-writes" />
<a id="durability-modes" />

Persistence lets LangGraph applications keep useful information beyond a single graph run. It matters when an agent needs to continue a conversation, resume after an interruption, recover from a failure, or remember information across interactions.

LangGraph provides two complementary persistence systems:

- **[Checkpointers](/oss/langgraph/checkpointers)** persist a thread's graph state as checkpoints. Use them for short-term, thread-scoped memory, including conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance.
- **[Stores](/oss/langgraph/stores)** persist application-defined data outside the graph state. Use them for long-term, cross-thread memory, including user preferences, facts, and shared knowledge.

Most applications can use both: a [checkpointer](/oss/langgraph/checkpointers) tracks the current thread, and a [store](/oss/langgraph/stores) tracks durable information across threads.

## Quickstart

Compile your graph with a checkpointer, a store, or both:

:::python
```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

checkpointer
```

### Source [2]

- Source: `langchain`
- Title: `Memory overview`
- Document ID: `89cceb7d2e06b8c7149f6154fe4c198084bc94781c7cd001b215040c4bd251c7`
- Chunk ID: `955aa4d98603d27d2b929cfe4ac6bea1e66955c74e3b049154024e02602e93bd`

```text
---
title: Memory overview
sidebarTitle: Memory
---

[Memory](/oss/langgraph/add-memory) is a system that remembers information about previous interactions. For AI agents, memory is crucial because it lets them remember previous interactions, learn from feedback, and adapt to user preferences. As agents tackle more complex tasks with numerous user interactions, this capability becomes essential for both efficiency and user satisfaction.

This conceptual guide covers two types of memory, based on their recall scope:

* [Short-term memory](#short-term-memory), or [thread](/oss/langgraph/checkpointers#threads)-scoped memory, tracks the ongoing conversation by maintaining message history within a session. LangGraph manages short-term memory as a part of your agent's [state](/oss/langgraph/graph-api#state). State is persisted to a database using a [checkpointer](/oss/langgraph/checkpointers#checkpoints) so the thread can be resumed at any time. Short-term memory updates when the graph is invoked or a step is completed, and the State is read at the start of each step.
* [Long-term memory](#long-term-memory) stores user-specific or application-level data across sessions and is shared _across_ conversational threads. It can be recalled _at any time_ and _in any thread_. Memories are scoped to any custom namespace, not just within a single thread ID. LangGraph provides [stores](/oss/langgraph/stores) ([reference doc](https://langchain-ai.github.io/langgraph/reference/store/#langgraph.store.base.BaseStore)) to let you save and recall long
```

### Source [3]

- Source: `langchain`
- Title: `Context overview`
- Document ID: `176fc6ab3f3c445b4224ee303b9d727645f48cafdc8634047059d209ba798b44`
- Chunk ID: `cb9825a657907b271bd10e857fb7a21b0f83feaec8fc1c158c70585483b28de7`

```text
and historical interactions. The LangGraph store acts as [long-term memory](/oss/concepts/memory#long-term-memory) across multiple runs. This can be used to read or update persistent facts (e.g., user profiles, preferences, prior interactions).

## Learn more

- [Memory conceptual overview](/oss/concepts/memory)
- [Short-term memory in LangChain](/oss/langchain/short-term-memory)
- [Memory in LangGraph](/oss/langgraph/add-memory)
```

### Source [4]

- Source: `langchain`
- Title: `Checkpointers`
- Document ID: `76c834cdabd7f08af4191f0d2bac6ec2545821679863c6d3b6a06d4a019012d5`
- Chunk ID: `70efec76518e21ad8f895de469b2d0a47cb1377f7577e2689051673dbcc2cf3a`

```text
for these workflows as the person has to be able to view the state of a graph at any point in time, and the graph has to be able to resume execution after the person has made any updates to the state. See [Interrupts](/oss/langgraph/interrupts) for examples.
- **Memory**: Checkpointers allow for ["memory"](/oss/concepts/memory) between interactions. In the case of repeated human interactions (like conversations) any follow up messages can be sent to that thread, which will retain its memory of previous ones. See [Add memory](/oss/langgraph/add-memory) for information on how to add and manage conversation memory using checkpointers.
- **Time travel**: Checkpointers allow for ["time travel"](/oss/langgraph/use-time-travel), allowing users to replay prior graph executions to review and / or debug specific graph steps. In addition, checkpointers make it possible to fork the graph state at arbitrary checkpoints to explore alternative trajectories.
- **Fault-tolerance**: Checkpointing provides fault-tolerance and error recovery: if one or more nodes fail at a given superstep, you can restart your graph from the last successful step.
<a id="pending-writes"></a>
- **Pending writes**: When a graph node fails mid-execution at a given [super-step](#super-steps), LangGraph stores pending checkpoint writes from any other nodes that completed successfully at that super-step. When you resume graph execution from that super-step you don't re-run the successful nodes.

## Core concepts

### Threads

A thread is a unique ID or thread identifier assigned to each checkpoint saved
```

### Source [5]

- Source: `langchain`
- Title: `Short-term memory`
- Document ID: `78e9959749656104e11b8f24b1a9bb6583073cfb394868784873866348956403`
- Chunk ID: `6c106efdb52e42ae53e619a7a3e691a6eacf48ab0531f200d8b78f2a99e7f384`

```text
messages alternate between human inputs and model responses, resulting in a list of messages that grows longer over time. Because context windows are limited, many applications can benefit from using techniques to remove or "forget" stale information.

<Tip>
    Need to remember information **across** conversations? Use [long-term memory](/oss/langchain/long-term-memory) to store and recall user-specific or application-level data across different threads and sessions.
</Tip>

## Usage

To add short-term memory (thread-level persistence) to an agent, you need to specify a `checkpointer` when creating an agent.

<Info>
    LangChain's agent manages short-term memory as a part of your agent's state.

    By storing these in the graph's state, the agent can access the full context for a given conversation while maintaining separation between different threads.

    State is persisted to a database (or memory) using a checkpointer so the thread can be resumed at any time.

    Short-term memory updates when the agent is invoked or a step (like a tool call) is completed, and the state is read at the start of each step.
</Info>

:::python

<ShortTermMemoryUsagePy />

:::
:::js

<ShortTermMemoryUsageJs />

:::

### In production

In production, use a checkpointer backed by a database:

:::python
```shell
pip install langgraph-checkpoint-postgres
```

```python
from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver  # [!code highlight]

def get_user_info() -> str:
    """Look up information about the current user."""
```

### Source [6]

- Source: `langchain`
- Title: `Going to production`
- Document ID: `df1a153e9f8c4c96b669c9ab6b0ca2f7807034095c671f31809791cac2544b4e`
- Chunk ID: `cb85752feaec9e84a7e742de0f802d4b3f1b12f99b9f9309dd22819c3d09925d`

```text
. For long-running deep agents that spawn many subagents, this means a mid-run failure doesn't lose completed work.

![Durable execution: when a worker crashes mid-run, another worker picks the run up from the latest checkpoint](/oss/images/deepagents/production/durable-execution.png)

Checkpointing also enables:

- **Indefinite [interrupts](/oss/langgraph/interrupts).** Human-in-the-loop workflows can pause for minutes or days and resume exactly where they left off.
- **[Time travel](/oss/langgraph/use-time-travel).** Every checkpointed step is a snapshot you can rewind to, letting you replay from an earlier state if something goes wrong.
- **Safe handling of sensitive operations.** For workflows involving payments or other irreversible actions, checkpoints provide an audit trail and a recovery point to inspect the exact state that led to an action.

<Tip>
[LangSmith Deployments](/langsmith/deployment) configure a persistent checkpointer automatically. If you are self-hosting, see [persistence](/oss/langgraph/persistence) for setup instructions.
</Tip>

## Memory

Without memory, every conversation starts from scratch. Memory lets your agent retain information across conversations (user preferences, learned instructions, past experiences) so it can personalize its behavior over time. For an overview of memory types, see the [memory concepts guide](/oss/concepts/memory).

![Short-term memory is scoped to a single thread via checkpoints; long-term memory persists across threads via the store](/oss/images/deepagents/production/memory.png
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-003

**Category:** `semantic`

**Expected behavior:** `answer_with_evidence`

## Query

How does a Qdrant payload index help the query planner choose a strategy for filtered vector search?

## Model answer

A Qdrant payload index helps the query planner choose a strategy for filtered vector search by enabling efficient filtering on specific payload fields during the semantic search phase. The payload index acts as a helper data structure that extends the HNSW graph, allowing filtering criteria to be applied within a single-pass graph traversal rather than before or after the vector search [6]. This integration allows the query planner to accurately estimate filter cardinality, which informs the selection of an optimal search strategy [1]. By providing fast access to payload attributes, the payload index reduces the need for full-scan searches on unindexed segments and enables the query planner to make more informed decisions about how to traverse the HNSW graph [1][6]. As a result, filtered vector search becomes both faster and more precise, especially when queries involve compound conditions on multiple fields [5]. For best performance, payload indexes should be created before data ingestion to ensure the optimizer can build the HNSW graph efficiently and avoid performance degradation from unindexed field filtering [3][4].

## API citations

```json
[
  {
    "citation_id": "6",
    "document_id": "e154d98effce45799f10eabf64fc430ce781d56872a4c7bd5c988321f9820d0a",
    "chunk_id": "c2504b87641a766ef23666195fe3810d93c5b87e0ec541b5770d2f320d459fb2"
  },
  {
    "citation_id": "1",
    "document_id": "7e655cddc2ab6cbef3cf19e644b9d35a9f1c3b5464c66857c35f2cbee4788225",
    "chunk_id": "79dc1880f0bbb2854e55aecc252ec3000246915b06c495899132e6f71c16cd0e"
  },
  {
    "citation_id": "5",
    "document_id": "5fcad0aecd090ff5a230e84fd3181db2bd7bbe6a695ae37a82339d9fe59eeeec",
    "chunk_id": "0ce70d15a6699b5251924967b91435b16d426538cf4e05ba2b76fe2048b7e89d"
  },
  {
    "citation_id": "3",
    "document_id": "1b528062e45b1ef934123e421128b610c2ba048d5e01eef1d70456ab65837430",
    "chunk_id": "47c3fab074ff92083f3239c60f1b086c77a0c289ed4c6a39a9daeec676e206a9"
  },
  {
    "citation_id": "4",
    "document_id": "d888e348b68815c8fd7fee3cc41ea2c28405e0c914ca8e00d10f901df18575b6",
    "chunk_id": "27a78d074e8c12434771a5bbd0ef1017d9052ab9e6c857e48d471fad09985fe7"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `qdrant`
- Title: `Indexing`
- Document ID: `7e655cddc2ab6cbef3cf19e644b9d35a9f1c3b5464c66857c35f2cbee4788225`
- Chunk ID: `79dc1880f0bbb2854e55aecc252ec3000246915b06c495899132e6f71c16cd0e`

```text
---
title: Indexing
short_description: "Combine HNSW vector indexes with payload indexes in Qdrant for fast filtered search across structured fields."
description: "Configure HNSW vector indexes and payload indexes in Qdrant to accelerate similarity search with filters on structured fields and high-cardinality metadata."
weight: 30
aliases:
  - ../indexing
---

# Indexing

A key feature of Qdrant is the effective combination of vector and traditional indexes. It is essential to have this because for vector search to work effectively with filters, having a vector index only is not enough. In simpler terms, a vector index speeds up vector search, and payload indexes speed up filtering.

The indexes in the segments exist independently, but the parameters of the indexes themselves are configured for the whole collection.

Not all segments automatically have indexes.
Their necessity is determined by the [optimizer](/documentation/ops-optimization/optimizer/) settings and depends, as a rule, on the number of stored points.

## Payload Index

Payload index in Qdrant is similar to the index in conventional document-oriented databases.
This index is built for a specific field and type, and is used for quick point requests by the corresponding filtering condition. The index is also used to accurately estimate the filter cardinality, which helps the [query planning](/documentation/search/search/#query-planning) choose a search strategy.

Creating an index requires additional computational resources and memory, so choosing fields to be indexed is essential. Qdrant does not make this choice but grants it to the user.

The following field types support payload indexing:

* `keyword` - for [keyword](/documentation/manage-data/payload/#keyword) payload, affects [Match]
```

### Source [2]

- Source: `qdrant`
- Title: `Filtering`
- Document ID: `9743b7d467a5ddfcb60690265a257f366c021157e42b1e7e31c2842679c16b32`
- Chunk ID: `61951539ac0962c013831c9a14c056b83c7fe43c7e0363eedc2a1c3be84853cd`

```text
---
title: Filtering
short_description: "Combine vector similarity with payload filters in Qdrant to enforce business rules and refine search results."
description: "Filter Qdrant search results with payload conditions on metadata and IDs, combining database-style clauses with vector similarity for precise retrieval."
weight: 10
aliases:
  - ../filtering
---

# Filtering

With Qdrant, you can set conditions when searching or retrieving points.
For example, you can impose conditions on both the [payload](/documentation/manage-data/payload/) and the `id` of the point.

Setting additional conditions is important when it is impossible to express all the features of the object in the embedding.
Examples include a variety of business requirements: stock availability, user location, or desired price range.

<aside role="status">
For performant filtering, create <a href="/documentation/manage-data/indexing/#payload-index">payload indexes</a> for the fields you plan to filter on. For best results, create payload indexes before ingesting data. Refer to <a href="/documentation/manage-data/indexing/#create-a-payload-index">Create a Payload Index</a> for more information.
</aside>

## Filtering clauses

Qdrant allows you to combine conditions in clauses.
Clauses are different logical operations, such as `OR`, `AND`, and `NOT`.
Clauses can be recursively nested into each other so that you can reproduce an arbitrary boolean expression.

Let's take a look at the clauses implemented in Qdrant.

Suppose we have a set of points with the following payload:

```json
[
  { "id": 1, "city": "
```

### Source [3]

- Source: `qdrant`
- Title: `Low-Latency Search`
- Document ID: `1b528062e45b1ef934123e421128b610c2ba048d5e01eef1d70456ab65837430`
- Chunk ID: `47c3fab074ff92083f3239c60f1b086c77a0c289ed4c6a39a9daeec676e206a9`

```text
---
title: Low-Latency Search
short_description: "Tune Qdrant for low-latency vector search with quantization, HNSW indexing, sharding, and replica routing strategies."
description: "Reduce Qdrant search latency by tuning HNSW indexes, quantization, sharding, and replica routing for fast vector retrieval in distributed deployments."
weight: 35
aliases:
  - /documentation/guides/low-latency-search/
---

# Tips for Low-Latency Search with Qdrant

## Create Payload Indexes

If your search queries include filters, create [payload indexes](/documentation/manage-data/indexing/#payload-index) for the fields you filter on. Payload indexes are the primary way to improve filtered search performance in Qdrant. For best results, create payload indexes **before** uploading data.

Queries that filter on unindexed fields are not only slower; they can also unnecessarily consume cluster resources, negatively impacting the latency of other search queries. Consider [blocking queries that filter on unindexed fields](/documentation/manage-data/indexing/#block-queries-that-filter-on-unindexed-fields). This rejects queries that would degrade performance at the API boundary, surfacing misconfigured indexes as errors rather than latency spikes.

## Scale Horizontally with Replicas

Qdrant can be deployed in a [distributed configuration](/documentation/scaling/distributed_deployment/). In distributed mode, multiple instances of Qdrant, called peers, operate as a single entity, called a cluster. Data is stored in [collections](/documentation/manage-data/collections/
```

### Source [4]

- Source: `qdrant`
- Title: `Qdrant Fundamentals`
- Document ID: `d888e348b68815c8fd7fee3cc41ea2c28405e0c914ca8e00d10f901df18575b6`
- Chunk ID: `27a78d074e8c12434771a5bbd0ef1017d9052ab9e6c857e48d471fad09985fe7`

```text
supports live updates for vector data, with newly inserted, updated and deleted vectors available for immediate search. The system uses full-scan search on unindexed segments during background index updates.

### My search results contain vectors with null values. Why?

By default, Qdrant tries to minimize network traffic and doesn't return vectors in search results.
But you can force Qdrant to do so by setting the `with_vector` parameter of the Search/Scroll to `true`.

If you're still seeing `"vector": null` in your results, it might be that the vector you're passing is not in the correct format, or there's an issue with how you're calling the upsert method.

### How can I search without a vector?

You are likely looking for the [scroll](/documentation/manage-data/points/#scroll-points) method. It allows you to retrieve the records based on filters or even iterate over all the records in the collection.

### My filtered vector search is slow. What should I check first?

Add a [payload index](/documentation/manage-data/indexing/#payload-index) on all the fields you're filtering by. Payload indexing often produces larger speedups for filtered queries than other optimizations such as changes to Hierarchical Navigable Small World (HNSW) parameters.

For best results, create payload indexes **before** uploading data. When uploading data later, rebuild the HNSW index by [making a minimal change](/documentation/manage-data/indexing/#rebuild-the-hnsw-index) to `m` or `ef_construct` (for example, from 100 to 101). Queries continue to be served by the old index until the
```

### Source [5]

- Source: `qdrant`
- Title: `None`
- Document ID: `5fcad0aecd090ff5a230e84fd3181db2bd7bbe6a695ae37a82339d9fe59eeeec`
- Chunk ID: `0ce70d15a6699b5251924967b91435b16d426538cf4e05ba2b76fe2048b7e89d`

```text
Create a payload index by specifying the field name and setting its schema to 'keyword'. This allows for more efficient searching with filters in Qdrant. Indexing fields can impact the vector index as well. It is recommended to index fields that might heavily influence search results. For example, indexing the object ID, which is unique for each record, will be more efficient than indexing by color with only a few possible values. Qdrant will prioritize using the most restrictive index in compound queries involving multiple fields.
```

### Source [6]

- Source: `qdrant`
- Title: `Overview`
- Document ID: `e154d98effce45799f10eabf64fc430ce781d56872a4c7bd5c988321f9820d0a`
- Chunk ID: `c2504b87641a766ef23666195fe3810d93c5b87e0ec541b5770d2f320d459fb2`

```text
constrained, and ensure you have fast NVMe storage.

### Filtering {#filtering}

Vector search alone can provide a decent search experience to your users; however, semantic similarity is rarely the only factor you have to consider. Embeddings won’t capture attributes such as price, and typically, a filter on a specific payload attribute has to be applied. To make that filtering effective, there are some specific Qdrant mechanisms you should be aware of, including with **payload indexes**.

### Payload Indexes {#payload-indexes}

The payload index is a helper data structure that enables effective filtering on a particular payload attribute. It’s a concept familiar from relational databases, where we create an index on a column that we often filter by. Similarly, in Qdrant, you should also make a payload index on a field used for filtering.

A unique aspect of the payload index is that it extends the HNSW graph, allowing filtering criteria to be applied during the semantic search phase. That means it’s a single-pass graph traversal, rather than pre- or post-filtering, which both have some drawbacks.

*![HNSW Graph with Filtering](/docs/gettingstarted/Orientation-Guide-Diagram-4.png)*

The fact that a payload index extends the HNSW graph means it’s more efficient to create it before indexing the data, as the optimizer will need to build the graph once. However, in some cases, you may already have a collection with a lot of vectors and recognize a need to filter by a specific attribute. In such cases, you can still create a payload index, yet **it won't immediately affect the HNSW graph**.

<aside role="status">
The HNSW graph will only get
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-004

**Category:** `lexical`

**Expected behavior:** `answer_with_evidence`

## Query

What does COPY --from do in a multi-stage Dockerfile?

## Model answer

The `COPY --from` directive in a multi-stage Dockerfile copies files or artifacts from a previous stage in the build process to the current stage. This allows you to selectively transfer only the necessary built outputs (such as compiled binaries) from a build stage to a final runtime stage, while excluding the build tools and intermediate files that are not needed in the final image [1][2]. For example, in a Go application, the compiled binary is built in a build stage and then copied to a minimal runtime stage using `COPY --from=builder /app/myapp .` [5]. This practice helps create smaller, more secure, and minimal final images [6].

## API citations

```json
[
  {
    "citation_id": "1",
    "document_id": "7de220a995db5ecc993cab31acad5d55427de6f161658643a302651c1a51090e",
    "chunk_id": "1f0a794f9f03af3fa87476992d6fb1abbd3a80de8c0b65349ee5489fab8c8e21"
  },
  {
    "citation_id": "2",
    "document_id": "5072a6270494f070b4c4d0597b717d0e5dfd8d5c7db889dc2b73487af53d910e",
    "chunk_id": "5fc6c84a416a0dc4edf4d0862668d0acf7142feb73d201ee5095bbd2d807bcbc"
  },
  {
    "citation_id": "5",
    "document_id": "6d0a37daced60d5f86dd50674f690c0bf3ab9c213d170d96eacc7b59e33771e8",
    "chunk_id": "1144c07dc6d6af57789958da6c4882bd2b1d4c1efc75416d8d1bfd1cca6ceec8"
  },
  {
    "citation_id": "6",
    "document_id": "708e0b8e0fe7c95da20b7042e348d253fc5dc65af32068702028109afa00208f",
    "chunk_id": "888ab70eedc4f04aa37b4e082a842e2ca89521361c9200682dd5a04be13fc587"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `docker`
- Title: `Multi-stage builds`
- Document ID: `7de220a995db5ecc993cab31acad5d55427de6f161658643a302651c1a51090e`
- Chunk ID: `1f0a794f9f03af3fa87476992d6fb1abbd3a80de8c0b65349ee5489fab8c8e21`

```text
---
title: Multi-stage builds
linkTitle: Multi-stage
weight: 10
description: |
  Learn about multi-stage builds and how you can use
  them to improve your builds and get smaller images
keywords: build, best practices
aliases:
- /engine/userguide/eng-image/multistage-build/
- /develop/develop-images/multistage-build/
---

Multi-stage builds are useful to anyone who has struggled to optimize
Dockerfiles while keeping them easy to read and maintain.

## Use multi-stage builds

With multi-stage builds, you use multiple `FROM` statements in your Dockerfile.
Each `FROM` instruction can use a different base, and each of them begins a new
stage of the build. You can selectively copy artifacts from one stage to
another, leaving behind everything you don't want in the final image.

The following Dockerfile has two separate stages: one for building a binary,
and another where the binary gets copied from the first stage into the next stage.

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:{{% param "example_go_version" %}}
WORKDIR /src
COPY <<EOF ./main.go
package main

import "fmt"

func main() {
  fmt.Println("hello, world")
}
EOF
RUN go build -o /bin/hello ./main.go

FROM scratch
COPY --from=0 /bin/hello /bin/hello
CMD ["/bin/hello"]
```

You only need the single Dockerfile. No need for a separate build script. Just
run `docker build`.

```console
$ docker build -t hello
```

### Source [2]

- Source: `docker`
- Title: `Multi-stage builds`
- Document ID: `5072a6270494f070b4c4d0597b717d0e5dfd8d5c7db889dc2b73487af53d910e`
- Chunk ID: `5fc6c84a416a0dc4edf4d0862668d0acf7142feb73d201ee5095bbd2d807bcbc`

```text
like JavaScript or Ruby or Python, you can build and minify your code in one stage, and copy the production-ready files to a smaller runtime image. This optimizes your image for deployment.
- For compiled languages, like C or Go or Rust, multi-stage builds let you compile in one stage and copy the compiled binaries into a final runtime image. No need to bundle the entire compiler in your final image.

Here's a simplified example of a multi-stage build structure using pseudo-code. Notice there are multiple `FROM` statements and a new `AS <stage-name>`. In addition, the `COPY` statement in the second stage is copying `--from` the previous stage.

```dockerfile
# Stage 1: Build Environment
FROM builder-image AS build-stage
# Install build tools (e.g., Maven, Gradle)
# Copy source code
# Build commands (e.g., compile, package)

# Stage 2: Runtime environment
FROM runtime-image AS final-stage
#  Copy application artifacts from the build stage (e.g., JAR file)
COPY --from=build-stage /path/in/build/stage /path/to/place/in/final/stage
# Define runtime configuration (e.g., CMD, ENTRYPOINT)
```

This Dockerfile uses two stages:

- The build stage uses a base image containing build tools needed to compile your application. It includes commands to install build tools, copy source code, and execute build commands.
- The final stage uses a smaller base image suitable for running your application. It copies the compiled artifacts (a JAR file, for example) from the build stage. Finally, it defines the runtime configuration (using `CMD` or `ENTRYPOINT
```

### Source [3]

- Source: `docker`
- Title: `Using Bake with additional contexts`
- Document ID: `53d9c6682b7013f0f713817fb349dbee6585df95717a10689ca1af6a0f9fcbca`
- Chunk ID: `68199b9cb3b9e7584b756271dff003d14165bfcf9785dc94900ca79149b4ecda`

```text
{title=Dockerfile}
FROM golang
COPY --from=src . .
```

```hcl {title=docker-bake.hcl}
# Running `docker buildx bake app` will result in `src` not pointing
# to some previous build stage but to the client filesystem, not part of the context.
target "app" {
  contexts = {
    src = "../path/to/source"
  }
}
```

## Using a target as a build context

To use a result of one target as a build context of another, specify the target
name with `target:` prefix.

```dockerfile {title=baseapp.Dockerfile}
FROM scratch
```

```dockerfile {title=Dockerfile}
# syntax=docker/dockerfile:1
FROM baseapp
RUN echo "Hello world"
```

```hcl {title=docker-bake.hcl}
target "base" {
  dockerfile = "baseapp.Dockerfile"
}

target "app" {
  contexts = {
    baseapp = "target:base"
  }
}
```

In most cases you should just use a single multi-stage Dockerfile with multiple
targets for similar behavior. This case is only recommended when you have
multiple Dockerfiles that can't be easily merged into one.
```

### Source [4]

- Source: `docker`
- Title: `Go language-specific guide`
- Document ID: `b1bd070e804ad26ec6cae2776262f5c4a7737bbaa6dc5f80581ac36ea1d8f050`
- Chunk ID: `7daa2ea0edd6f3b8534895fa685f1802f9340d748dc695607c426bd12fdbe2d5`

```text
s convenient to use it to keep the file paths short for improved
readability.

Now, all that is left to do is to tell Docker what command to run when your
image is used to start a container.

You do this with the `CMD` command:

```dockerfile
CMD ["/docker-gs-ping"]
```

Here's the complete `Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:1.19

# Set destination for COPY
WORKDIR /app

# Download Go modules
COPY go.mod go.sum ./
RUN go mod download

# Copy the source code. Note the slash at the end, as explained in
# https://docs.docker.com/reference/dockerfile/#copy
COPY *.go ./

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -o /docker-gs-ping

# Optional:
# To bind to a TCP port, runtime parameters must be supplied to the docker command.
# But we can document in the Dockerfile what ports
# the application is going to listen on by default.
# https://docs.docker.com/reference/dockerfile/#expose
EXPOSE 8080

# Run
CMD ["/docker-gs-ping"]
```

The `Dockerfile` may also contain comments. They always begin with a `#` symbol,
and must be at the beginning of a line. Comments are there for your convenience
to allow documenting your `Dockerfile`.

There is also a concept of Dockerfile directives, such as the `syntax` directive
you added. The directives must always be at the very top of
```

### Source [5]

- Source: `docker`
- Title: `Migrate from Wolfi`
- Document ID: `6d0a37daced60d5f86dd50674f690c0bf3ab9c213d170d96eacc7b59e33771e8`
- Chunk ID: `1144c07dc6d6af57789958da6c4882bd2b1d4c1efc75416d8d1bfd1cca6ceec8`

```text
/build/building/multi-stage.md). All stages in your
Dockerfile should use a hardened image. While intermediary stages will typically
use images tagged as `dev` or `sdk`, your final runtime stage should use a runtime image.

Utilize the build stage to compile your application and copy the resulting
artifacts to the final runtime stage. This ensures that your final image is
minimal and secure.

The following example shows a multi-stage Dockerfile with a build stage and runtime stage:

```dockerfile
# Build stage
FROM dhi.io/golang:1.25-alpine3.24-dev AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

# Runtime stage
FROM dhi.io/golang:1.25-alpine3.24
WORKDIR /app
COPY --from=builder /app/myapp .
ENTRYPOINT ["/app/myapp"]
```

After updating your Dockerfile, build and test your application. If you encounter
issues, see the [Troubleshoot](/manuals/dhi/how-to/troubleshoot.md) guide for common
problems and solutions.

## Language-specific examples

See the examples section for language-specific migration examples:

- [Go](examples/go.md)
- [Python](examples/python.md)
- [Node.js](examples/node.md)
```

### Source [6]

- Source: `docker`
- Title: `Migrate from Alpine or Debian`
- Document ID: `708e0b8e0fe7c95da20b7042e348d253fc5dc65af32068702028109afa00208f`
- Chunk ID: `888ab70eedc4f04aa37b4e082a842e2ca89521361c9200682dd5a04be13fc587`

```text
> [!NOTE]
>
> Multi-stage builds are recommended to keep your final image minimal and
> secure. Single-stage builds are supported, but they include the full `dev` image
> and therefore result in a larger image with a broader attack surface.

To ensure that your final image is as minimal as possible, you should use a
[multi-stage build](/manuals/build/building/multi-stage.md). All stages in your
Dockerfile should use a hardened image. While intermediary stages will typically
use images tagged as `dev` or `sdk`, your final runtime stage should use a runtime image.

Utilize the build stage to compile your application and copy the resulting
artifacts to the final runtime stage. This ensures that your final image is
minimal and secure.

The following example shows a multi-stage Dockerfile with a build stage and runtime stage:

```dockerfile
# Build stage
FROM dhi.io/golang:1.25-debian13-dev AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

# Runtime stage
FROM dhi.io/golang:1.25-debian13
WORKDIR /app
COPY --from=builder /app/myapp .
ENTRYPOINT ["/app/myapp"]
```

After updating your Dockerfile, build and test your application. If you encounter
issues, see the [Troubleshoot](/manuals/dhi/how-to/troubleshoot.md) guide for common
problems and solutions.

## Language-specific examples

See the examples section for language-specific migration examples:

- [Go](examples/go.md)
- [Python](examples/python.md)
- [Node.js]
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-005

**Category:** `lexical`

**Expected behavior:** `answer_with_evidence`

## Query

What does envFrom do when a Kubernetes Pod consumes a ConfigMap?

## Model answer

When a Kubernetes Pod consumes a ConfigMap using `envFrom`, it instructs Kubernetes to set all key-value pairs from the ConfigMap as environment variables in the container. Each key in the ConfigMap becomes an environment variable with the same name, and the value is assigned to that variable [5]. This allows the container to access configuration data directly via environment variables without needing to parse configuration files [1]. The `envFrom` field can also include a prefix to modify the environment variable names, but this is not specified in the provided sources [5]. 

For example, if a ConfigMap contains keys `SPECIAL_LEVEL` and `SPECIAL_TYPE`, using `envFrom` will result in environment variables named `SPECIAL_LEVEL` and `SPECIAL_TYPE` being set in the container [2]. This mechanism enables dynamic configuration updates without requiring changes to the container image or restarts, especially when used in conjunction with Deployments [6]. 

However, if a Pod only needs specific values from the ConfigMap, the `env.valueFrom` syntax should be used instead to select individual keys [1].

## API citations

```json
[
  {
    "citation_id": "5",
    "document_id": "fe9b044f0e012cbbfbf1596f880cfbf2535d4f6be61035732bfd69ba072a4af0",
    "chunk_id": "da17bdada9494c4001879526fb6ef287804061d07279564c3ece4ba7af4cb42e"
  },
  {
    "citation_id": "1",
    "document_id": "ff938757c6f456e32f60e79106a4f0e6182bd9bd524852e70bb40d987e0d2693",
    "chunk_id": "0fe9a7c160bf4dd31eb07082e84b7d3d54a7bc73a56ea1308b85ab27ea308cbd"
  },
  {
    "citation_id": "2",
    "document_id": "fc4bb067d2176daa62d7f960cc97bfd617f269a331857ccd39f8d4871deb1986",
    "chunk_id": "a8f92db98f21953a66e098e3422b9fe4036ba912c1a8c10b3a0ab5b1a0687ef7"
  },
  {
    "citation_id": "6",
    "document_id": "f49192a7d5201f41c31690f034a3c2a86e6242db842dcf44363c5e8b36d6405d",
    "chunk_id": "01ebceafc3eb2666fc9dfc73d5d3e414c17ffca7218019c8eac98aaaf914df3a"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `kubernetes`
- Title: `ConfigMaps`
- Document ID: `ff938757c6f456e32f60e79106a4f0e6182bd9bd524852e70bb40d987e0d2693`
- Chunk ID: `0fe9a7c160bf4dd31eb07082e84b7d3d54a7bc73a56ea1308b85ab27ea308cbd`

```text
apply -f myconfigmap.yaml
```

The following Pod consumes the content of the ConfigMap as environment variables:

{{% code_sample file="configmap/env-configmap.yaml" %}}

The `envFrom` field instructs Kubernetes to create environment variables from the sources nested within it.
The inner `configMapRef` refers to a ConfigMap by its name and selects all its key-value pairs.
Add the Pod to your cluster, then retrieve its logs to see the output from the printenv command.
This should confirm that the two key-value pairs from the ConfigMap have been set as environment variables:

```shell
kubectl apply -f env-configmap.yaml
```
```shell
kubectl logs pod/env-configmap
```
The output is similar to this:
```console
...
username: "k8s-admin"
access_level: "1"
...
```

Sometimes a Pod won't require access to all the values in a ConfigMap.
For example, you could have another Pod which only uses the username value from the ConfigMap.
For this use case, you can use the `env.valueFrom` syntax instead, which lets you select individual keys in
a ConfigMap. The name of the environment variable can also be different from the key within the ConfigMap.
For example:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: env-configmap
spec:
  containers:
  - name: envars-test-container
    image: nginx
    en
```

### Source [2]

- Source: `kubernetes`
- Title: `Configure a Pod to Use a ConfigMap`
- Document ID: `fc4bb067d2176daa62d7f960cc97bfd617f269a331857ccd39f8d4871deb1986`
- Chunk ID: `a8f92db98f21953a66e098e3422b9fe4036ba912c1a8c10b3a0ab5b1a0687ef7`

```text
.io/examples/configmap/configmap-multikeys.yaml
  ```

* Use `envFrom` to define all of the ConfigMap's data as container environment variables. The
  key from the ConfigMap becomes the environment variable name in the Pod.

  {{% code_sample file="pods/pod-configmap-envFrom.yaml" %}}

  Create the Pod:

  ```shell
  kubectl create -f https://kubernetes.io/examples/pods/pod-configmap-envFrom.yaml
  ```
  Now, the Pod's output includes environment variables `SPECIAL_LEVEL=very` and
  `SPECIAL_TYPE=charm`.

  Once you're happy to move on, delete that Pod:
  ```shell
  kubectl delete pod dapi-test-pod --now
  ```

## Use ConfigMap-defined environment variables in Pod commands

You can use ConfigMap-defined environment variables in the `command` and `args` of a container
using the `$(VAR_NAME)` Kubernetes substitution syntax.

For example, the following Pod manifest:

{{% code_sample file="pods/pod-configmap-env-var-valueFrom.yaml" %}}

Create that Pod, by running:

```shell
kubectl create -f https://kubernetes.io/examples/pods/pod-configmap-env-var-valueFrom.yaml
```

That pod produces the following output from the `test-container` container:
```shell
kubectl logs dapi-test-
```

### Source [3]

- Source: `kubernetes`
- Title: `Updating Configuration via a ConfigMap`
- Document ID: `1c6ba0fbd655a4ded61dec7774a0f7f3c9b8f5aee4423adf2b1311d1fdae7c9d`
- Chunk ID: `ca78833068ca5f3f0570569bb3532d76623b8f2ef8ac7b9e0b0d982a88f8b276`

```text
---
title: Updating Configuration via a ConfigMap
content_type: tutorial
weight: 20
---

<!-- overview -->
This page provides a step-by-step example of updating configuration within a Pod via a ConfigMap
and builds upon the [Configure a Pod to Use a ConfigMap](/docs/tasks/configure-pod-container/configure-pod-configmap/) task.
At the end of this tutorial, you will understand how to change the configuration for a running application.
This tutorial uses the `alpine` and `nginx` images as examples.

## {{% heading "prerequisites" %}}
{{< include "task-tutorial-prereqs.md" >}}

You need to have the [curl](https://curl.se/) command-line tool for making HTTP requests from
the terminal or command prompt. If you do not have `curl` available, you can install it. Check the
documentation for your local operating system.

## {{% heading "objectives" %}}
* Update configuration via a ConfigMap mounted as a Volume
* Update environment variables of a Pod via a ConfigMap
* Update configuration via a ConfigMap in a multi-container Pod
* Update configuration via a ConfigMap in a Pod possessing a Sidecar Container

<!-- lessoncontent -->

## Update configuration via a ConfigMap mounted as a Volume {#rollout-configmap-volume}

Use the `kubectl create configmap` command to create a ConfigMap from
[literal values](/docs/tasks/configure-pod
```

### Source [4]

- Source: `kubernetes`
- Title: `Volumes`
- Document ID: `584b08cd3402d5a758f30913228dac03a8c2feff3953c5a0c0fb876a4f0bbb78`
- Chunk ID: `f6fbf84115eb3524bef4247e9a3e791f64b12205ecab8d05f27ed7b0116eb669`

```text
.
Volumes are mounted at [specified paths](#using-subpath) within the container filesystem.
For each container defined within a Pod, you must independently specify where
to mount each volume that the container uses.

Volumes cannot mount within other volumes (but see [Using subPath](#using-subpath)
for a related mechanism). Also, a volume cannot contain a hard link to anything in
a different volume.

## Types of volumes {#volume-types}

Kubernetes supports several types of volumes.

### configMap

A [ConfigMap](/docs/tasks/configure-pod-container/configure-pod-configmap/)
provides a way to inject configuration data into Pods.
The data stored in a ConfigMap can be referenced in a volume of type
`configMap` and then consumed by containerized applications running in a Pod.

When referencing a ConfigMap, you provide the name of the ConfigMap in the
volume. You can customize the path to use for a specific
entry in the ConfigMap. The following configuration shows how to mount
the `log-config` ConfigMap onto a Pod called `configmap-pod`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-pod
spec:
  containers:
    - name: test
      image: busybox:1.28
      command: ['sh', '-c', 'echo "The app is running!" && tail -f /dev/null']
      volumeMounts:
        - name: config-vol
          mountPath: /etc/config
  volumes:
    - name: config-vol
      configMap:
        name: log-confi
```

### Source [5]

- Source: `kubernetes`
- Title: `Define Environment Variables for a Container`
- Document ID: `fe9b044f0e012cbbfbf1596f880cfbf2535d4f6be61035732bfd69ba072a4af0`
- Chunk ID: `da17bdada9494c4001879526fb6ef287804061d07279564c3ece4ba7af4cb42e`

```text
---
title: Define Environment Variables for a Container
content_type: task
weight: 20
---

<!-- overview -->

This page shows how to define environment variables for a container
in a Kubernetes Pod.

## {{% heading "prerequisites" %}}

{{< include "task-tutorial-prereqs.md" >}}

<!-- steps -->

## Define an environment variable for a container

When you create a Pod, you can set environment variables for the containers
that run in the Pod. To set environment variables, include the `env` or
`envFrom` field in the configuration file.

The `env` and `envFrom` fields have different effects.

`env`
: allows you to set environment variables for a container, specifying a value directly for each variable that you name.

`envFrom`
: allows you to set environment variables for a container by referencing either a ConfigMap or a Secret.
 When you use `envFrom`, all the key-value pairs in the referenced ConfigMap or Secret
 are set as environment variables for the container.
 You can also specify a common prefix string.

You can read more about [ConfigMap](/docs/tasks/configure-pod-container/configure-pod-configmap/#configure-all-key-value-pairs-in-a-configmap-as-container-environment-variables)
and [Secret](/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables).

This
```

### Source [6]

- Source: `kubernetes`
- Title: `Custom Resources`
- Document ID: `f49192a7d5201f41c31690f034a3c2a86e6242db842dcf44363c5e8b36d6405d`
- Chunk ID: `01ebceafc3eb2666fc9dfc73d5d3e414c17ffca7218019c8eac98aaaf914df3a`

```text
end-user data (such as images, PII, etc.) or other large-scale data processed by applications.
- The natural operations on the objects are not CRUD-y.
- The API is not easily modeled as objects.
- You chose to represent pending operations with an operation ID or an operation object.

## Should I use a ConfigMap or a custom resource?

Use a ConfigMap if any of the following apply:

* There is an existing, well-documented configuration file format, such as a `mysql.cnf` or
  `pom.xml`.
* You want to put the entire configuration into one key of a ConfigMap.
* The main use of the configuration file is for a program running in a Pod on your cluster to
  consume the file to configure itself.
* Consumers of the file prefer to consume via file in a Pod or environment variable in a pod,
  rather than the Kubernetes API.
* You want to perform rolling updates via Deployment, etc., when the file is updated.

{{< note >}}
Use a {{< glossary_tooltip text="Secret" term_id="secret" >}} for sensitive data, which is similar
to a ConfigMap but more secure.
{{< /note >}}

Use a custom resource (CRD or Aggregated API) if most of the following apply:

* You want to use Kubernetes client libraries and CLIs to create and update the new resource.
* You want top-level support from `kubectl`; for example, `kubectl get my-object object-name`.
* You want to build new automation that watches for updates on the new object, and then CRUD other
  objects, or vice versa.
* You want to write
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-006

**Category:** `lexical`

**Expected behavior:** `answer_with_evidence`

## Query

What does generate() do when generating text with a Transformers model?

## Model answer

The `generate()` method in a Transformers model is used to generate text by producing the next token(s) given an initial input (prompt) and a sequence of previously generated tokens. It operates by extending the input sequence step-by-step, using the model's learned parameters to predict the next token, and continues until it reaches a predefined maximum length or an end-of-sequence token [4]. The method is part of the `GenerationMixin` and is available for all models with generative capabilities [4]. After generating the token IDs, the output is decoded back into human-readable text using `batch_decode` [1]. This process enables applications such as text completion, chatbot responses, and other natural language generation tasks [4].

## API citations

```json
[
  {
    "citation_id": "4",
    "document_id": "bad1550c979284d5b68b4286385a81f3d2612a551d6ffc2c672b0b3b3f5ff4eb",
    "chunk_id": "cb756617263284fdca6fdf0e90b952e2407d55698be9358732c46869b1e0c170"
  },
  {
    "citation_id": "1",
    "document_id": "3e4b11acaf9fd360f785c5c7a441d87fdd8d8eafdcc34a93e7f3f7dd59b978bf",
    "chunk_id": "77728f65e0993a1bd4b33db1ea07cb54b90eca0228feeae1356bc74a63ed2135"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `huggingface`
- Title: `Quickstart`
- Document ID: `3e4b11acaf9fd360f785c5c7a441d87fdd8d8eafdcc34a93e7f3f7dd59b978bf`
- Chunk ID: `77728f65e0993a1bd4b33db1ea07cb54b90eca0228feeae1356bc74a63ed2135`

```text
`~GenerationMixin.generate`] to generate text. Decode the token ids back into text with [`~PreTrainedTokenizerBase.batch_decode`].

```py
generated_ids = model.generate(**model_inputs, max_length=30)
tokenizer.batch_decode(generated_ids)[0]
'<s> The secret to baking a good cake is 100% in the preparation. There are so many recipes out there,'
```

> [!TIP]
> Skip ahead to the [Trainer](#trainer-api) section to learn how to fine-tune a model.

## Pipeline

The [`Pipeline`] class is the most convenient way to run inference with a pretrained model. It supports many tasks such as text generation, image segmentation, automatic speech recognition, document question answering, and more.

> [!TIP]
> Refer to the [Pipeline](./main_classes/pipelines) API reference for a complete list of available tasks.

Create a [`Pipeline`] object and select a task. By default, [`Pipeline`] downloads and caches a default pretrained model for a given task. Pass the model name to the `model` parameter to choose a specific model.

<hfoptions id="pipeline-tasks">
<hfoption id="text generation">

Use [`Accelerator`] to automatically detect an available accelerator for inference.

```py
from transformers import pipeline
from accelerate import Accelerator

device = Accelerator().device

pipe = pipeline("text-generation", model="meta-llama/Llama-2-7b-hf", device=device)
```

Prompt [`Pipeline`] with some initial text to generate
```

### Source [2]

- Source: `huggingface`
- Title: `Generation strategies`
- Document ID: `c3212105dbfc98a9e6e2c9391b088c1366baefd8b49016f046fb16cfbc9d556c`
- Chunk ID: `a0c92d65a1fab93cc3dfad3870a47fd4e6e9f32ef0e859b85ab9b4819209dccb`

```text
the model you've designed your method with, and it is meant to be part of a working self-contained model-generate pair. When the model in this repository is loaded, your custom generation method will override `generate`. Don't worry -- your generation method can still be loaded with any other Transformers model, as explained in the section above.

If you simply want to copy an existing model, you can do

```py
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("source/model_repo")
model = AutoModelForCausalLM.from_pretrained("source/model_repo")
tokenizer.save_pretrained("your/generation_method", push_to_hub=True)
model.save_pretrained("your/generation_method", push_to_hub=True)
```

#### generate.py

This is the core of your generation method. It *must* contain a method named `generate`, and this method *must* contain a `model` argument as its first argument. `model` is the model instance, which means you have access to all attributes and methods in the model, including the ones defined in [`GenerationMixin`] (like the base `generate` method).

> [!WARNING]
> `generate.py` must be placed in a folder named `custom_generate`, and not at the root level of the repository. The file paths for this feature are hardcoded.

Under the hood, when the base [`~GenerationMixin.generate`] method is called with a `custom_generate` argument, it first checks its Python requirements (if any)
```

### Source [3]

- Source: `huggingface`
- Title: `Glossary`
- Document ID: `965f0dcfee27a779ecb0d9605edcf318f5c3574d2ae623d4a7829ea65206eb8e`
- Chunk ID: `12f3e3ab9754bb3d745bc6852a238a91ead09fca595db7c4e20d56b569f5266a`

```text
with another kind of inputs (for instance images).

## N

### Natural language generation (NLG)

All tasks related to generating text (for instance, [Write With Transformers](https://transformer.huggingface.co/), translation).

### Natural language processing (NLP)

A generic way to say "deal with texts".

### Natural language understanding (NLU)

All tasks related to understanding what is in a text (for instance classifying the
whole text, individual words).

## P

### pipeline

A pipeline in 🤗 Transformers is an abstraction referring to a series of steps that are executed in a specific order to preprocess and transform data and return a prediction from a model. Some example stages found in a pipeline might be data preprocessing, feature extraction, and normalization.

For more details, see [Pipelines for inference](https://huggingface.co/docs/transformers/pipeline_tutorial).

### PipelineParallel (PP)

Parallelism technique in which the model is split up vertically (layer-level) across multiple GPUs, so that only one or
several layers of the model are placed on a single GPU. Each GPU processes in parallel different stages of the pipeline
and working on a small chunk of the batch. Learn more about how PipelineParallel works [here](perf_train_gpu_many#from-naive-model-parallelism-to-pipeline-parallelism).

### pixel values

A tensor of the numerical representations of an image that is passed to a model. The pixel values have a shape of [`batch_size`, `num_channels`, `height`, `width`], and are generated from an image processor.

### pooling

An
```

### Source [4]

- Source: `huggingface`
- Title: `Text generation`
- Document ID: `bad1550c979284d5b68b4286385a81f3d2612a551d6ffc2c672b0b3b3f5ff4eb`
- Chunk ID: `cb756617263284fdca6fdf0e90b952e2407d55698be9358732c46869b1e0c170`

```text
<!--Copyright 2024 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

⚠️ Note that this file is in Markdown but contains specific syntax for our doc-builder (similar to MDX) that may not be
rendered properly in your Markdown viewer.

-->

# Text generation

[[open-in-colab]]

Text generation is the most popular application for large language models (LLMs). A LLM is trained to generate the next word (token) given some initial text (prompt) along with its own generated outputs up to a predefined length or when it reaches an end-of-sequence (`EOS`) token.

In Transformers, the [`~GenerationMixin.generate`] API handles text generation, and it is available for all models with generative capabilities. This guide will show you the basics of text generation with [`~GenerationMixin.generate`] and some common pitfalls to avoid.

> [!TIP]
> For the following commands, please make sure [`transformers serve` is running](https://huggingface.co/docs/transformers/main/en/serving).
>
> ```shell
> transformers chat Qwen/Qwen2.5-0.5B-Instruct
> ```

## Default
```

### Source [5]

- Source: `huggingface`
- Title: `Translation`
- Document ID: `0256a3a8d7e285bad2cc821f44f5fb23cc6ab7afed41fbf014eded073190c6ec`
- Chunk ID: `277c01dd18290da5465e11ebdce356a4d8c5b93cf399fe1a14e403530b947938`

```text
> inputs = tokenizer(text, return_tensors="pt").input_ids
```

Use the [`~generation.GenerationMixin.generate`] method to create the translation. For more details about the different text generation strategies and parameters for controlling generation, check out the [Text Generation](../main_classes/text_generation) API.

```py
>>> from transformers import AutoModelForSeq2SeqLM

>>> model = AutoModelForSeq2SeqLM.from_pretrained("username/my_awesome_opus_books_model")
>>> outputs = model.generate(inputs, max_new_tokens=40, do_sample=True, top_k=30, top_p=0.95)
```

Decode the generated token ids back into text:

```py
>>> tokenizer.decode(outputs[0], skip_special_tokens=True)
'Les lignées partagent des ressources avec des bactéries enfixant l'azote.'
```
```

### Source [6]

- Source: `huggingface`
- Title: `Qwen2MoE`
- Document ID: `c3360cc751ead5630d55832f52d515a2bdc9435ff98b1b917686b5212ee53ed2`
- Chunk ID: `2908279a72d4edd209da7df6b155096276918fe6a644bbd79691a7d16c5f6999`

```text
language tasks.

The example below demonstrates how to generate text with [`Pipeline`], [`AutoModel`], and from the command line.

<hfoptions id="usage">
<hfoption id="Pipeline">

```python
from transformers import pipeline

pipe = pipeline(
    task="text-generation",
    model="Qwen/Qwen1.5-MoE-A2.7B",
    device_map=0
)

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Tell me about the Qwen2 model family."},
]
outputs = pipe(messages, max_new_tokens=256, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
print(outputs[0]["generated_text"][-1]['content'])
```

</hfoption>
<hfoption id="AutoModel">

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen1.5-MoE-A2.7B-Chat",
    device_map="auto",
    attn_implementation="sdpa"
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen1.5-MoE-A2.7B-Chat")

prompt = "Give me a short introduction to large language models."
messages = [
    {"role": "system", "content": "You are a helpful assistant
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-007

**Category:** `ambiguous`

**Expected behavior:** `qualified_answer`

## Query

How should I persist state in my AI application?

## Model answer

To persist state in your AI application, you should use a checkpointer to manage short-term memory (thread-level persistence) and a store for long-term memory (cross-thread, durable persistence). 

For short-term memory, configure a `checkpointer` in your agent's `config` with a `thread_id` to enable thread-scoped memory persistence. This allows the agent to maintain context across invocations within a session, with state automatically persisted via the checkpointer [5]. In production, use a database-backed checkpointer such as `PostgresSaver` to ensure durability and scalability [5].

For long-term memory—such as user preferences, accumulated knowledge, or research progress—use a `CompositeBackend` that routes specific memory paths (e.g., `/memories/`) to a LangGraph Store. This provides durable, cross-thread persistence and allows the agent to store and recall information across sessions [6]. The agent can create memory files on demand using filesystem tools like `write_file` or `edit_file`, and you do not need to pre-populate these paths [6].

Ensure your `thread_id` is under 255 characters when using database-backed checkpointers to avoid errors, and use UUIDs or hashes if needed [3]. 

In summary, combine a checkpointer for short-term memory and a store with a `CompositeBackend` for long-term memory to achieve robust, scalable state persistence [1][3][6].

## API citations

```json
[
  {
    "citation_id": "5",
    "document_id": "78e9959749656104e11b8f24b1a9bb6583073cfb394868784873866348956403",
    "chunk_id": "6c106efdb52e42ae53e619a7a3e691a6eacf48ab0531f200d8b78f2a99e7f384"
  },
  {
    "citation_id": "6",
    "document_id": "74ffbf98a6bfcecf23865da4040fe88d0ff0c89f28e02708cf92c1e988e8f185",
    "chunk_id": "064dd0cfb2a8a98d469fde363b57909ae229bdd31dcb412021bf7dad2fb671e5"
  },
  {
    "citation_id": "3",
    "document_id": "43a6d508fe857efc43952bc9e98567ed4d5c6c23351e2099402cd27e3448bdfe",
    "chunk_id": "09353451d3a63e1e55b343417b479a9a671384840052d619154a981100c9121e"
  },
  {
    "citation_id": "1",
    "document_id": "1f2b16c995416a275a31710376c8335842c57ef2f786a34527fb2978679bfe02",
    "chunk_id": "da3327c07542102872dc4c992c7f476f370ac82602f76ff7740c60f9b1a5a8c5"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `langchain`
- Title: `Anthropic middleware integration`
- Document ID: `1f2b16c995416a275a31710376c8335842c57ef2f786a34527fb2978679bfe02`
- Chunk ID: `da3327c07542102872dc4c992c7f476f370ac82602f76ff7740c60f9b1a5a8c5`

```text
_id to persist state across invocations
config: RunnableConfig = {"configurable": {"thread_id": "my-session"}}

# First invocation: Record some memories
result = agent.invoke(
    {"messages": [HumanMessage("Remember that the project deadline is March 15th and code review deadline is March 10th")]},
    config=config,
)

# The agent creates memory files, which are stored in state
print("Memory files created:", list(result["memory_files"].keys()))

# Second invocation: Search the memories we just recorded
# State is automatically persisted via the checkpointer
result = agent.invoke(
    {"messages": [HumanMessage("Search my memories for project deadlines")]},
    config=config,
)
print(result["messages"][-1].content)
```

```text
Memory files created: ['/memories/project_info.md']
```

```text
I found your project deadlines in my memory! Here's what I have recorded:

## Important Deadlines
- **Code Review Deadline:** March 10th
- **Project Deadline:** March 15th

## Notes
- Code review must be completed 5 days before final project deadline
- Need to ensure all code is ready for review by March 10th

Is there anything specific about these deadlines you'd like to know or update?
```

</Accordion>

</AccordionGroup>
```

### Source [2]

- Source: `kubernetes`
- Title: `StatefulSets`
- Document ID: `4b3e19046458e56e2abd7762654058e6620827b93bea8bd2218eff7e26ae88ea`
- Chunk ID: `4c9374e35e935c4d56747af92d193b3c8bed430b64dc5ea2ce24594e2556fa5a`

```text
---
reviewers:
- enisoc
- erictune
- foxish
- janetkuo
- kow3ns
- smarterclayton
title: StatefulSets
api_metadata:
- apiVersion: "apps/v1"
  kind: "StatefulSet"
content_type: concept
description: >-
  A StatefulSet runs a group of Pods, and maintains a sticky identity for each of those Pods. This is useful for managing
  applications that need persistent storage or a stable, unique network identity.
weight: 30
hide_summary: true # Listed separately in section index
---

<!-- overview -->

StatefulSet is the workload API object used to manage stateful applications.

{{< glossary_definition term_id="statefulset" length="all" >}}

<!-- body -->

## Using StatefulSets

StatefulSets are valuable for applications that require one or more of the
following:

* Stable, unique network identifiers.
* Stable, persistent storage.
* Ordered, graceful deployment and scaling.
* Ordered, automated rolling updates.

In the above, stable is synonymous with persistence across Pod (re)scheduling.
If an application doesn't require any stable identifiers or ordered deployment,
deletion, or scaling, you should deploy your application using a workload object
that provides a set of stateless replicas.
[Deployment](/docs/concepts/workloads/controllers/deployment/) or
[ReplicaSet](/docs/concepts/workloads/controllers/replicaset/) may be better suited to your stateless needs.

## Limitations

* The storage for a given Pod must either be provisioned by a
  [PersistentVolume Provisioner](/docs/concepts/storage/dynamic-provisioning/)
  based on the
```

### Source [3]

- Source: `langchain`
- Title: `Persistence`
- Document ID: `43a6d508fe857efc43952bc9e98567ed4d5c6c23351e2099402cd27e3448bdfe`
- Chunk ID: `09353451d3a63e1e55b343417b479a9a671384840052d619154a981100c9121e`

```text
](/langsmith/agent-server), you do not need to implement or configure checkpointers or stores manually. The server handles persistence infrastructure behind the scenes.
</Info>

## Checkpointer vs. store

| | Checkpointer | Store |
| ---- | ---- | ---- |
| Persists | Graph state snapshots | Application-defined key-value data |
| Scope | A single thread | Across threads |
| Memory type | Short-term, thread-scoped memory | Long-term, cross-thread memory |
| Use for | Conversation continuity, human-in-the-loop, time travel, and fault tolerance | User preferences, facts, and shared knowledge |
| Access pattern | Pass a `thread_id` in graph config | Read and write items from nodes or application code |
| Full guide | [Checkpointers](/oss/langgraph/checkpointers) | [Stores](/oss/langgraph/stores) |

## Troubleshooting common issues

### PostgresSaver: `thread_id` too long

When using `PostgresSaver` (or `AsyncPostgresSaver`), the `thread_id` is stored in a column with limited length. If your `thread_id` exceeds the column size, you will see a database error.

**Fix:** Keep `thread_id` values under 255 characters. Use a UUID or hash if you need deterministic IDs:

:::python
```python
import uuid

config = {"configurable": {"thread_id": str(uuid.uuid4())[:255]}}
```
:::

### `MemorySaver
```

### Source [4]

- Source: `langchain`
- Title: `Subgraphs`
- Document ID: `756b1b698d13b5a6821587e983d07e93bd565091b5613557b1c09808bb91fbd6`
- Chunk ID: `f15cc2b2dafd41dc8a998462bd0697b534b91bcdde0638e5b3a1c9946e675d7b`

```text
/langgraph/persistence).
</Note>

<Info>
The examples below use LangChain's @[`create_agent`], which is a common way to build agents. `create_agent` produces a [LangGraph graph](/oss/langgraph/graph-api) under the hood, so all subgraph persistence concepts apply directly. If you're building with raw LangGraph `StateGraph`, the same patterns and configuration options apply—see the [Graph API](/oss/langgraph/graph-api) for details.
</Info>

### Stateful

Stateful subgraphs inherit the parent graph's checkpointer, which enables [interrupts](/oss/langgraph/interrupts), [persistence](/oss/langgraph/persistence), and state inspection. The two stateful modes differ in how long state is retained.

#### Per-invocation (default)

<Tip>
This is the recommended mode for most applications, including [multi-agent](/oss/langchain/multi-agent) systems where subagents are invoked as tools. It supports [interrupts](/oss/langgraph/interrupts), [persistence](/oss/langgraph/persistence), and parallel calls while keeping each invocation isolated.
</Tip>

Use per-invocation persistence when each call to the subgraph is independent and the subagent doesn't need to remember anything from previous calls. This is the most common pattern, especially for [multi-agent](/oss/langchain/multi-agent) systems where subagents handle one-off requests like "look up this customer's order" or "summarize this document."

Omit `checkpointer` or
```

### Source [5]

- Source: `langchain`
- Title: `Short-term memory`
- Document ID: `78e9959749656104e11b8f24b1a9bb6583073cfb394868784873866348956403`
- Chunk ID: `6c106efdb52e42ae53e619a7a3e691a6eacf48ab0531f200d8b78f2a99e7f384`

```text
messages alternate between human inputs and model responses, resulting in a list of messages that grows longer over time. Because context windows are limited, many applications can benefit from using techniques to remove or "forget" stale information.

<Tip>
    Need to remember information **across** conversations? Use [long-term memory](/oss/langchain/long-term-memory) to store and recall user-specific or application-level data across different threads and sessions.
</Tip>

## Usage

To add short-term memory (thread-level persistence) to an agent, you need to specify a `checkpointer` when creating an agent.

<Info>
    LangChain's agent manages short-term memory as a part of your agent's state.

    By storing these in the graph's state, the agent can access the full context for a given conversation while maintaining separation between different threads.

    State is persisted to a database (or memory) using a checkpointer so the thread can be resumed at any time.

    Short-term memory updates when the agent is invoked or a step (like a tool call) is completed, and the state is read at the start of each step.
</Info>

:::python

<ShortTermMemoryUsagePy />

:::
:::js

<ShortTermMemoryUsageJs />

:::

### In production

In production, use a checkpointer backed by a database:

:::python
```shell
pip install langgraph-checkpoint-postgres
```

```python
from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver  # [!code highlight]

def get_user_info() -> str:
    """Look up information about the current user."""
```

### Source [6]

- Source: `langchain`
- Title: `Context engineering in Deep Agents`
- Document ID: `74ffbf98a6bfcecf23865da4040fe88d0ff0c89f28e02708cf92c1e988e8f185`
- Chunk ID: `064dd0cfb2a8a98d469fde363b57909ae229bdd31dcb412021bf7dad2fb671e5`

```text
different threads and conversations.
Deep agents can use long-term memory for storing user preferences, accumulated knowledge, research progress, or any information that should persist beyond a single session.

To use long-term memory, you must use a `CompositeBackend` that routes specific paths (typically `/memories/`) to a LangGraph Store, which provides durable cross-thread persistence.
The `CompositeBackend` is a hybrid storage system where some files persist indefinitely while others remain scoped to a single thread.

:::python
<ContextEngineeringLongTermMemoryPy />
:::

:::js
<ContextEngineeringLongTermMemoryJs />
:::

You do not need to pre-populate `/memories/` with files.
You provide the backend config, store, and system prompt instructions that tell the agent *what* to save and *where*.
For example, you may prompt the agent to store preferences in `/memories/preferences.txt`.
The path starts empty and the agent creates files on demand using its filesystem tools (`write_file`, `edit_file`) when users share information worth remembering.

To pre-seed memories, use the [Store API](/langsmith/custom-store) when deploying on LangSmith.
See [Long-term memory](/oss/deepagents/memory) for setup and use cases.

## Best practices

1. **Start with the right input context** – Keep memory minimal for always-relevant conventions; use focused skills for task-specific capabilities.
2. **Leverage subagents for heavy work** – Delegate multi-step, output-heavy tasks to keep the main agent's context clean.
3. **Adjust subagent outputs in configuration** – If
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-008

**Category:** `ambiguous`

**Expected behavior:** `qualified_answer`

## Query

How should I make vector search faster?

## Model answer

To make vector search faster, you should:

1. Add a payload index on all fields used for filtering, as payload indexing often produces larger speedups for filtered queries than other optimizations [2].
2. Ensure that payload indexes are created before uploading data, and rebuild the HNSW index with a minimal change (e.g., increasing `m` or `ef_construct` from 100 to 101) to achieve better performance [2].
3. Use quantization methods, which are popular among users and can speed up retrieval, especially when applied to static embeddings [3].
4. Consider using static embeddings, which can drastically reduce the time required to create vectors from data, even on a consumer-grade laptop without GPU acceleration [3].

These steps are supported by the provided sources and directly address performance optimization in vector search.

## API citations

```json
[
  {
    "citation_id": "2",
    "document_id": "d888e348b68815c8fd7fee3cc41ea2c28405e0c914ca8e00d10f901df18575b6",
    "chunk_id": "27a78d074e8c12434771a5bbd0ef1017d9052ab9e6c857e48d471fad09985fe7"
  },
  {
    "citation_id": "3",
    "document_id": "015e13f54d8b69d6d3ce8d6c6673412c3022e77cab4f85249fd97b4fb29db412",
    "chunk_id": "b63634ed951be249edbfab38da705ea02be81c6c4d8eace896451a099cdf735d"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `qdrant`
- Title: `Understanding Vector Search in Qdrant`
- Document ID: `0da09f12d67cb33e4ba7cdc1ab48126961bbcf9592c715170ba4286ca9d6e8e6`
- Chunk ID: `8672efe68ccbf938d3a40a1997164a65ec1f327c45d8b2f14ee0871aec79fbcd`

```text
---
title: Understanding Vector Search in Qdrant
short_description: "Understand how vector search works, why it goes beyond keyword matching, and where Qdrant fits in the modern retrieval ecosystem."
description: "Learn how vector search uses embeddings to retrieve by semantic meaning, how it differs from keyword search, and where Qdrant fits in the retrieval stack."
weight: 10
social_preview_image: /docs/gettingstarted/vector-social.png
---

# How Does Vector Search Work in Qdrant?

<p align="center"><iframe width="560" height="315" src="https://www.youtube.com/embed/mXNrhyw4q84?si=wruP9wWSa8JW4t78" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></p>

If you are still trying to figure out how vector search works, please read ahead. This document describes how vector search is used, covers Qdrant's place in the larger ecosystem, and outlines how you can use Qdrant to augment your existing projects.

For those who want to start writing code right away, visit our [Complete Beginners tutorial](/documentation/tutorials-basics/search-beginners/) to build a search engine in 5-15 minutes.

## A Brief History of Search

Human memory is unreliable. Thus, as long as
```

### Source [2]

- Source: `qdrant`
- Title: `Qdrant Fundamentals`
- Document ID: `d888e348b68815c8fd7fee3cc41ea2c28405e0c914ca8e00d10f901df18575b6`
- Chunk ID: `27a78d074e8c12434771a5bbd0ef1017d9052ab9e6c857e48d471fad09985fe7`

```text
supports live updates for vector data, with newly inserted, updated and deleted vectors available for immediate search. The system uses full-scan search on unindexed segments during background index updates.

### My search results contain vectors with null values. Why?

By default, Qdrant tries to minimize network traffic and doesn't return vectors in search results.
But you can force Qdrant to do so by setting the `with_vector` parameter of the Search/Scroll to `true`.

If you're still seeing `"vector": null` in your results, it might be that the vector you're passing is not in the correct format, or there's an issue with how you're calling the upsert method.

### How can I search without a vector?

You are likely looking for the [scroll](/documentation/manage-data/points/#scroll-points) method. It allows you to retrieve the records based on filters or even iterate over all the records in the collection.

### My filtered vector search is slow. What should I check first?

Add a [payload index](/documentation/manage-data/indexing/#payload-index) on all the fields you're filtering by. Payload indexing often produces larger speedups for filtered queries than other optimizations such as changes to Hierarchical Navigable Small World (HNSW) parameters.

For best results, create payload indexes **before** uploading data. When uploading data later, rebuild the HNSW index by [making a minimal change](/documentation/manage-data/indexing/#rebuild-the-hnsw-index) to `m` or `ef_construct` (for example, from 100 to 101). Queries continue to be served by the old index until the
```

### Source [3]

- Source: `qdrant`
- Title: `Static Embeddings`
- Document ID: `015e13f54d8b69d6d3ce8d6c6673412c3022e77cab4f85249fd97b4fb29db412`
- Chunk ID: `b63634ed951be249edbfab38da705ea02be81c6c4d8eace896451a099cdf735d`

```text
the text is not different compared to any other model
client.upsert(
    "my_collection",
    points=[
        models.PointStruct(
            id=uuid.uuid4().hex,
            vector=model.encode("Hello, world!"),
            payload={"static": "Hello, world!"},
        )
    ]
)
```

The retrieval is not going to be any faster just because you use static embeddings. However, **you will experience a
huge speedup in creating the vectors from your data**, what is usually a bottleneck. The Hugging Face blog post mentions
that the model might be even up to 400x faster on a CPU than the state-of-the-art embedding model.

We didn't perform any proper benchmarking of the encoding speed, but one of the experiments done on `TREC-COVID` dataset
from [BeIR](https://github.com/beir-cellar/beir) shows that we can **encode and fully index 171K documents in Qdrant in
around 7.5 minutes**. All of it done on a consumer-grade laptop, without GPU acceleration.

## Quantization of the static embeddings

What can actually make the retrieval faster is the use of Matryoshka Embeddings, as the `static-retrieval-mrl-en-v1`
model was trained with that technique in mind. However, that's not the only way to speed up search. Quantization
methods are really popular among our users, and we were curious to check if they might be applied to the static
embeddings with the same success.

We took the `static-retrieval-mrl-en-v1` model and tested it on various
```

### Source [4]

- Source: `qdrant`
- Title: `Search`
- Document ID: `945b90377c7801e7df9518832f52efff02f78067dea19a100984355cbccdc30a`
- Chunk ID: `3395417624bf74e7cf271f9b9097ba17532483b1819f8d47ff29d08f9fe66adf`

```text
how to combine them with vector search.

## Search Relevance

[Search Relevance](/documentation/search/search-relevance/) describes techniques to improve result ranking beyond raw vector similarity, including score boosting and re-ranking strategies.

## Low-Latency Search

[Low-Latency Search](/documentation/search/low-latency-search/) covers configuration and design patterns for achieving the fastest possible query response times.
```

### Source [5]

- Source: `langchain`
- Title: `Chroma integration`
- Document ID: `b8e13941f621759759a26e6133562b1fb30e15facc2f4b088cc4b4bb90af0ce2`
- Chunk ID: `4b89907e7b3775e4e3ba4487a36937051c653601749a1bffc047cd187bf5c12f`

```text
`python
vector_store.delete(ids=uuids[-1])
```

## Query vector store

Once your vector store has been created and the relevant documents have been added you will most likely wish to query it during the running of your chain or agent.

### Query directly

#### Similarity search

Performing a simple similarity search can be done as follows:

```python
results = vector_store.similarity_search(
    "LangChain provides abstractions to make working with LLMs easy",
    k=2,
    filter={"source": "tweet"},
)
for res in results:
    print(f"* {res.page_content} [{res.metadata}]")
```

#### Similarity search with score

If you want to execute a similarity search and receive the corresponding scores you can run:

```python
results = vector_store.similarity_search_with_score(
    "Will it be hot tomorrow?", k=1, filter={"source": "news"}
)
for res, score in results:
    print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")
```

#### Search by vector

You can also search by vector:

```python
results = vector_store.similarity_search_by_vector(
    embedding=embeddings.embed_query("I love green eggs and ham!"), k=1
)
for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")
```

#### Other search methods

There are a variety of other search methods that are not covered in this notebook, such as MM
```

### Source [6]

- Source: `qdrant`
- Title: `Reranking for Better Search`
- Document ID: `387977fc7f81950f7f5589bf770ad0cacf8cc867e1c1434f33e299cf4ff8361d`
- Chunk ID: `451f73e66abf3ed5bf77b5fc79fb8c92f7fbf0093cb6722b0758eed2ba9b6a50`

```text
model,
                          input_type="search_query",
                          embedding_types=['float'])
```

---

After that, we'll move on to retrieve results using vector search and apply reranking on the results. This two-stage process is super efficient because we’re grabbing a small set of the most relevant documents first, which is much faster than reranking a huge dataset.

### Vector Search

This snippet grabs the top 10 most relevant points from your Qdrant collection using the query embedding.

```python
search_result = client.query_points(
    collection_name="basic-search-rerank", query=query_embeddings.embeddings.float_[0], limit=10
).points
```

---

Here’s how it works: we use the query_points method to search within the "basic-search-rerank" collection. It compares the query embedding (the first embedding in query_embeddings) against all the document embeddings, pulling up the 10 closest matches. The matching points get stored in search_result.

And here’s a sneak peek at what you’ll get from the vector search:

| **ID** | **Document** | **Score** |
| --- | --- | --- |
| 0 | In machine learning, feature scaling is the process of normalizing the range of independent... | 0.71 |
| 10 | In deep learning, feature scaling helps stabilize the learning process, allowing for... | 0.69 |
| 1 | Feature scaling is commonly used in data preprocessing to ensure that features are on the... | 0.68 |
|
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-009

**Category:** `ambiguous`

**Expected behavior:** `qualified_answer`

## Query

How should I handle long-running work in my API?

## Model answer

To handle long-running work in your API, you should use a workflow that breaks complex tasks into smaller, manageable units and manages execution with asynchronous task handling. The Functional API in LangChain supports this by using `@task` to represent discrete units of work that can be executed asynchronously within an entrypoint, returning a future-like object that can be awaited or resolved synchronously [5]. 

For long-running operations, you can implement a node that processes data in batches and includes periodic heartbeats to signal activity, which helps prevent timeouts and maintains process stability [6]. For example, a long-running node can process batches of data and call `runtime.heartbeat()` to refresh the timeout, ensuring the process remains active and does not time out [6].

Additionally, to manage resource usage and ensure cleanup, always clean up sessions or tasks when done to release resources [4]. This includes using a cleanup function to terminate tasks and release allocated resources, especially when dealing with long-running operations that may otherwise lead to resource exhaustion [4].

These patterns ensure that long-running work is both manageable and resilient, with clear execution flow and proper resource management [5][6].

## API citations

```json
[
  {
    "citation_id": "5",
    "document_id": "6e6d9cf81f7319bb9d339600079a23146fe31b3f7c742193f42a53c101404e52",
    "chunk_id": "94909aa3580794a39b7eecb1e40dc18660e72e64653f8aceba9c854dd1d6c0d6"
  },
  {
    "citation_id": "6",
    "document_id": "28970dc377906d895b13eb9cd12dbe078078ceffa9fbcac656706ba06fb4f604",
    "chunk_id": "3be0b52942b0b8663e6bc53f04903ff646e1bcc885df19c87f05a1e77cd1f3be"
  },
  {
    "citation_id": "4",
    "document_id": "2ff23ffd7b9c23b2c25e1bcfd939a280898ecb0f4e9d7dc5469ed3482ec77e83",
    "chunk_id": "1330a8a946bba54a9ae827285319f2f6d15f3e4be49209ea295629c6db0c5025"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `fastapi`
- Title: `Deployments Concepts { #deployments-concepts }`
- Document ID: `03e8ad3174ef1e2249a83d26b22b953e37a343bc25935aa38a08a5eeecfa243d`
- Chunk ID: `fa03390e683aa821b4bb438fc07aca06c102051771ecbc40bcc0c7de61b0125b`

```text
**always running**, uninterrupted, so that your clients can always access it. This is of course, unless you have a specific reason why you want it to run only in certain situations, but most of the time you want it constantly running and **available**.

### In a Remote Server { #in-a-remote-server }

When you set up a remote server (a cloud server, a virtual machine, etc.) the simplest thing you can do is use `fastapi run` (which uses Uvicorn) or something  similar, manually, the same way you do when developing locally.

And it will work and will be useful **during development**.

But if your connection to the server is lost, the **running process** will probably die.

And if the server is restarted (for example after updates, or migrations from the cloud provider) you probably **won't notice it**. And because of that, you won't even know that you have to restart the process manually. So, your API will just stay dead. 😱

### Run Automatically on Startup { #run-automatically-on-startup }

In general, you will probably want the server program (e.g. Uvicorn) to be started automatically on server startup, and without needing any **human intervention**, to have a process always running with your API (e.g. Uvicorn running your FastAPI app).

### Separate Program { #separate-program }

To achieve this, you will normally have a **separate program** that would make sure your application is run on startup. And in many cases, it would also make sure other components or applications are also run, for example, a database.

### Example Tools to Run at Startup { #example
```

### Source [2]

- Source: `docker`
- Title: `How to build an AI-powered code quality workflow with SonarQube and E2B`
- Document ID: `024de53291fba74024de6783f18a5af2ab3837c0c99b312cd9116180685c6771`
- Chunk ID: `bfb88f7e523f3c8242e58e91271bb87109ab51f49310281d69454aa1fd68a26b`

```text
1. Use `timeoutMs: 0` (TypeScript) or `timeout_ms=0` (Python) for complex workflows to allow unlimited time:

   {{< tabs group="language" >}}
   {{< tab name="TypeScript" >}}

   ```typescript
   await sbx.commands.run(
     `echo '${prompt}' | claude -p --dangerously-skip-permissions`,
     {
       timeoutMs: 0, // No timeout
       onStdout: console.log,
       onStderr: console.log,
     },
   );
   ```

   {{< /tab >}}
   {{< tab name="Python" >}}

   ```python
   await sbx.commands.run(
       f"echo '{prompt}' | claude -p --dangerously-skip-permissions",
       timeout_ms=0,  # No timeout
       on_stdout=print,
       on_stderr=print,
   )
   ```

   {{< /tab >}}
   {{< /tabs >}}

2. Break complex workflows into smaller, focused tasks.
3. Monitor your Anthropic API credit usage.
4. Add checkpoints in prompts: "After each step, show progress before continuing".

### Sandbox cleanup errors

Issue: Sandboxes aren't being cleaned up properly, leading to resource exhaustion.

Solution: Always use proper error handling with cleanup in the `finally` block:

{{< tabs group="language" >}}
{{< tab name="TypeScript" >}}

```typescript
async function robustWorkflow() {
  let sbx: Sandbox | undefined;

  try {
    sbx = await Sandbox.betaCre
```

### Source [3]

- Source: `kubernetes`
- Title: `Kubernetes Metrics Reference`
- Document ID: `db5ee5e55a1972c2f5e66d0cfecabfd6ead18ca6229a08f500e6cbded30b2d2b`
- Chunk ID: `824841d173efe3cde94a1c04f4cf0af0199a106433fda93e93ff6a05265b6678`

```text
request handlers after the associated requests have been timed out by the apiserver</div>
    <ul>
    <li><label class="metric_detail">Stability Level:</label><span class="metric_stability_level">ALPHA</span></li>
    <li data-type="counter"><label class="metric_detail">Type:</label> <span class="metric_type">Counter</span></li>
    <li class="metric_labels_varying"><label class="metric_detail">Labels:</label><span class="metric_label">source</span><span class="metric_label">status</span></li><li class="metric_component_endpoints"><label class="metric_detail">Components:</label><ul><li>kube-apiserver (/metrics)</li></ul></li></ul>
    </div><div class="metric" data-stability="alpha">
    <div class="metric_name">apiserver_request_sli_duration_seconds</div>
    <div class="metric_help">Response latency distribution (not counting webhook duration and priority & fairness queue wait times) in seconds for each verb, group, version, resource, subresource, scope and component.</div>
    <ul>
    <li><label class="metric_detail">Stability Level:</label><span class="metric_stability_level">ALPHA</span></li>
    <
```

### Source [4]

- Source: `langchain`
- Title: `Amazon Bedrock agentcore code interpreter integration`
- Document ID: `2ff23ffd7b9c23b2c25e1bcfd939a280898ecb0f4e9d7dc5469ed3482ec77e83`
- Chunk ID: `1330a8a946bba54a9ae827285319f2f6d15f3e4be49209ea295629c6db0c5025`

```text
"].invoke(
    {"command": "python long_running_script.py"},
    config=config
)
# Returns a task_id

# Check task status
status = tools_by_name["get_task"].invoke(
    {"task_id": "task-abc123"},
    config=config
)
print(status)

# Stop a running task if needed
tools_by_name["stop_task"].invoke(
    {"task_id": "task-abc123"},
    config=config
)
```

## Session cleanup

Always clean up sessions when done to release resources:

```python
# Clean up all sessions
await toolkit.cleanup()

# Or clean up a specific thread's session
await toolkit.cleanup(thread_id="session-123")
```

---

## API reference

For detailed documentation of all features and configurations, see:

- [langchain-aws API reference](https://reference.langchain.com/python/langchain-aws)
- [Amazon Bedrock AgentCore documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
```

### Source [5]

- Source: `langchain`
- Title: `Functional API overview`
- Document ID: `6e6d9cf81f7319bb9d339600079a23146fe31b3f7c742193f42a53c101404e52`
- Chunk ID: `94909aa3580794a39b7eecb1e40dc18660e72e64653f8aceba9c854dd1d6c0d6`

```text
and function calls. Unlike many data orchestration frameworks that require restructuring code into an explicit pipeline or DAG, the Functional API allows you to incorporate these capabilities without enforcing a rigid execution model.

The Functional API uses two key building blocks:

:::python
* **`@entrypoint`**: Marks a function as the starting point of a workflow, encapsulating logic and managing execution flow, including handling long-running tasks and interrupts.
* **@[`@task`]**: Represents a discrete unit of work, such as an API call or data processing step, that can be executed asynchronously within an entrypoint. Tasks return a future-like object that can be awaited or resolved synchronously.
:::

:::js
* **`entrypoint`**: An entrypoint encapsulates workflow logic and manages execution flow, including handling long-running tasks and interrupts.
* **`task`**: Represents a discrete unit of work, such as an API call or data processing step, that can be executed asynchronously within an entrypoint. Tasks return a future-like object that can be awaited or resolved synchronously.
:::

This provides a minimal abstraction for building workflows with state management and streaming.

<Tip>
For information on how to use the functional API, see [Use Functional API](/oss/langgraph/use-functional-api).
</Tip>

## Functional API vs. Graph API

For users who prefer a more declarative approach, LangGraph's [Graph API](/oss/langgraph/graph-api) allows you to define workflows using a Graph paradigm. Both APIs share the same underlying runtime, so you can use them together in the
```

### Source [6]

- Source: `langchain`
- Title: `Fault tolerance`
- Document ID: `28970dc377906d895b13eb9cd12dbe078078ceffa9fbcac656706ba06fb4f604`
- Chunk ID: `3be0b52942b0b8663e6bc53f04903ff646e1bcc885df19c87f05a1e77cd1f3be`

```text
"long_running_node")
builder.add_edge("long_running_node", END)
```
:::

:::js
```typescript
import {
  StateGraph,
  StateSchema,
  START,
  END,
  type Runtime,
} from "@langchain/langgraph";
import * as z from "zod";

const State = new StateSchema({
  result: z.string(),
});

const longRunningNode = async (
  state: typeof State.State,
  runtime: Runtime<typeof State>
) => {
  for (const batch of fetchBatches()) {
    process(batch);
    runtime.heartbeat?.(); // [!code highlight]
  }
  return { result: "done" };
};

const graph = new StateGraph(State)
  .addNode("longRunningNode", longRunningNode, {
    timeout: { idleTimeout: 30_000, refreshOn: "heartbeat" },
  })
  .addEdge(START, "longRunningNode")
  .addEdge("longRunningNode", END)
  .compile();
```
:::

`runtime.heartbeat()` is a no-op outside an idle-timed attempt, so you can call it unconditionally.

### NodeTimeoutError

When a timeout fires, LangGraph raises @[`NodeTimeoutError`] with structured context about which limit was hit:

:::python
| Attribute | Type | Description |
| --------- | ---- | ----------- |
| `node` | `
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-010

**Category:** `version_specific`

**Expected behavior:** `answer_with_evidence`

## Query

How does current Docker documentation distinguish the legacy docker-compose CLI from the docker compose CLI?

## Model answer

The current Docker documentation distinguishes the legacy docker-compose CLI from the docker compose CLI by the command syntax and underlying implementation. The legacy CLI, first released in 2014, is written in Python and is invoked with `docker-compose` [6]. In contrast, the newer Docker Compose CLI, introduced in 2020 as Compose v2 and implemented in Go, is invoked with `docker compose` [6]. The documentation notes that Compose v2 ignores the top-level version element in the compose.yaml file, and that the `docker compose` command is now part of the Docker CLI, serving as a drop-in replacement for `docker-compose` [3]. Additionally, the standalone legacy version of Docker Compose uses the `-compose` syntax (e.g., `docker-compose up`) and is deprecated in favor of Docker Desktop or the Docker Compose plugin [2]. Compose v5, released in 2025, uses the same `docker compose` command and is functionally identical to Compose v2, with the primary distinction being the introduction of an official Go SDK [6].

## API citations

```json
[
  {
    "citation_id": "6",
    "document_id": "618c274419a926311dbf502416d3d75f5357d2b1293ca1b304fb7a4ee260b364",
    "chunk_id": "4cdad5054cf9905b2e57bb7e64a106b8afa80562de145da163629af72bd0bfaa"
  },
  {
    "citation_id": "3",
    "document_id": "7a0500cb3c396722f17c4d93cca1e9dd936cf4d1a03f1946ef4e9613d64e7bfc",
    "chunk_id": "26807d228a1562d93901f10b9a2ec4a4bb2a9be9b43a03d0f87549855c9bf805"
  },
  {
    "citation_id": "2",
    "document_id": "500f254a487f81c8e6883272b703c7a76cfdebef9f950ef8e951e3e3d2481cd0",
    "chunk_id": "43e2b2d4a757a422e8daa24e0f635fbfd7cefe177e78220ae0e6409b7470c17a"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `docker`
- Title: `History and development of Docker Compose`
- Document ID: `69a543f51a596ca07a468ead27a8b8c258a8a85119b80a06583d61b7da1b3ca8`
- Chunk ID: `f89c8451dcbd265fc66d51d9a2158cd0242654b399bc5f8640ca12f6a89ea1b4`

```text
---
title: History and development of Docker Compose
linkTitle: History and development
description: Explore the evolution of Docker Compose from v1 to v5, including CLI changes, YAML versioning, and the Compose Specification.
keywords: compose, compose yaml, swarm, migration, compatibility, docker compose vs docker-compose
weight: 30
aliases:
- /compose/history/
---

This page provides:
 - A brief history of the development of the Docker Compose CLI
 - A clear explanation of the major versions and file formats that make up Compose v1, v2, and v5
 - The main differences between Compose v1, v2, and v5

## Introduction

![Image showing the main differences between Compose v1, Compose v2, and Compose v5](../images/v1-versus-v2-versus-v5.png)

The diagram above highlights the key differences between Docker Compose v1, v2, and v5. Today, the supported Docker Compose CLI versions are Compose v2 and Compose v5, both of which are defined by the [Compose Specification](/reference/compose-file/_index.md).

The diagram provides a high-level comparison of file formats, command-line syntax, and supported top-level elements. This is covered in more detail in the following sections.

### Docker Compose CLI versioning

Compose v1 was first released in 2014. It was written in Python and invoked with `docker-compose`.
Typically, Compose v1 projects include a top-level `version` element in the `compose.yaml` file, with values ranging from `2.0` to `3.8`, which refer to the specific [file formats](#compose-file-format-version
```

### Source [2]

- Source: `docker`
- Title: `Install the Docker Compose standalone (Legacy)`
- Document ID: `500f254a487f81c8e6883272b703c7a76cfdebef9f950ef8e951e3e3d2481cd0`
- Chunk ID: `43e2b2d4a757a422e8daa24e0f635fbfd7cefe177e78220ae0e6409b7470c17a`

```text
---
title: Install the Docker Compose standalone (Legacy)
linkTitle: Standalone (Legacy)
description: Instructions for installing the legacy Docker Compose standalone tool on Linux and Windows Server
keywords: install docker-compose, standalone docker compose, docker-compose windows server, install docker compose linux, legacy compose install
toc_max: 3
weight: 20
---

> [!WARNING]
>
> This install scenario is not recommended and is only supported for backward compatibility purposes.
> Use [Docker Desktop](/manuals/desktop/_index.md) or the
> [Docker Compose plugin](/manuals/compose/install/linux.md) instead.
> Use the standalone binary only if you cannot use either of these options.

This page contains instructions on how to install Docker Compose standalone on Linux or Windows Server, from the command line.

> [!WARNING]
>
> The Docker Compose standalone uses the `-compose` syntax instead of the current standard syntax `compose`.
> For example, you must type `docker-compose up` when using Docker Compose standalone, instead of `docker compose up`.
> Use it only for backward compatibility.

## On Linux

1. To download and install the Docker Compose standalone, run:

   ```console
   $ curl -SL https://github.com/docker/compose/releases/download/{{% param "compose_version" %}}/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
   ```

2. Apply executable permissions to the standalone binary in the target path for the installation.

   ```console
   $ chmod +x /usr/local/bin/docker-compose
   ```
```

### Source [3]

- Source: `docker`
- Title: `Docker Desktop for Mac 3.x release notes`
- Document ID: `7a0500cb3c396722f17c4d93cca1e9dd936cf4d1a03f1946ef4e9613d64e7bfc`
- Chunk ID: `26807d228a1562d93901f10b9a2ec4a4bb2a9be9b43a03d0f87549855c9bf805`

```text
Desktop now includes the beta version of Compose V2, which supports the `docker compose` command as part of the Docker CLI. While `docker-compose` is still supported and maintained, Compose V2 implementation relies directly on the compose-go bindings which are maintained as part of the specification. The compose command in the Docker CLI supports most of the `docker-compose` commands and flags. It is expected to be a drop-in replacement for `docker-compose`. There are a few remaining flags that have yet to be implemented, see the docker-compose compatibility list for more information about the flags that are supported in the new compose command. If you run into any problems with Compose V2, you can easily switch back to Compose v1 by either by making changes in Docker Desktop **Experimental** Settings, or by running the command `docker-compose disable-v2`. Let us know your feedback on the new ‘compose’ command by creating an issue in the [Compose-CLI](https://github.com/docker/compose-cli/issues) GitHub repository.

### Upgrades

- [Compose V2 beta](https://github.com/docker/compose-cli/releases/tag/v2.0.0-beta.4)
  - Fixed a bug where a container cannot be started when a file is bind-mounted into a nested mountpoint. Fixes [docker/compose-cli#1795](https://github.com/docker/compose-cli/issues/1795).
  - Added support for container links and external links.
  - Introduced the `docker compose logs --since --until` option.
  - `docker compose con
```

### Source [4]

- Source: `docker`
- Title: `Install Docker Desktop on Fedora`
- Document ID: `8cab6ddb708b7bca0df15a4ea015d83f4331a419a8cb76695eb198231b614513`
- Chunk ID: `c5f67446cd95ac5469992d14da0f3766346ad073da2c4f4e98d83cbd536181d5`

```text
`/usr/bin/docker`.
  This is because the classic Docker CLI is installed at `/usr/bin/docker`. The Docker Desktop installer also installs a Docker CLI binary that includes cloud-integration capabilities and is essentially a wrapper for the Compose CLI, at`/usr/local/bin/com.docker.cli`. The symlink ensures that the wrapper can access the classic Docker CLI.

## Launch Docker Desktop

{{% include "desktop-linux-launch.md" %}}

## Upgrade Docker Desktop

Once a new version for Docker Desktop is released, the Docker UI shows a notification.
You need to first remove the previous version and then download the new package each time you want to upgrade Docker Desktop. Run:

```console
$ sudo dnf remove docker-desktop
$ sudo dnf install ./docker-desktop-x86_64.rpm
```

## Next steps

- Explore [Docker's subscriptions](https://www.docker.com/pricing?ref=Docs&refAction=DocsDesktopFedoraInstall) to see what Docker can offer you.
- Take a look at the [Docker workshop](/get-started/workshop/_index.md) to learn how to build an image and run it as a containerized application.
- [Explore Docker Desktop](/manuals/desktop/use-desktop/_index.md) and all its features.
- [Troubleshooting](/manuals/desktop/troubleshoot-and-support/troubleshoot/_index.md) describes common problems, workarounds, how to run and submit diagnostics,
```

### Source [5]

- Source: `docker`
- Title: `Compose file reference`
- Document ID: `2488dd679a8002fe49dbd32d0a14ab727e6cf2ede03d8857e387b81683997dde`
- Chunk ID: `b85f59f4a22d93d26f941c03ca413e1fba5fa48ce85a2bf3ffdcdd3d60b3c06c`

```text
file/
  - /compose/reference/overview/
---

> **New to Docker Compose?**
>
> Find more information about the [key features and use cases of Docker Compose](/manuals/compose/intro/features-uses.md) or [try the quickstart guide](/manuals/compose/gettingstarted.md).

The Compose Specification is the latest and recommended version of the Compose file format. It helps you define a [Compose file](/manuals/compose/intro/compose-application-model.md) which is used to configure your Docker application’s services, networks, volumes, and more.

Legacy versions 2.x and 3.x of the Compose file format were merged into the Compose Specification. It is implemented in versions 1.27.0 and above (also known as Compose v2) of the Docker Compose CLI.

The Compose Specification on Docker Docs is the Docker Compose implementation. If you wish to implement your own version of the Compose Specification, see the [Compose Specification repository](https://github.com/compose-spec/compose-spec).

Use the following links to navigate key sections of the Compose Specification.

> [!TIP]
>
> Want a better editing experience for Compose files in VS Code?
> Check out the [Docker DX](https://marketplace.visualstudio.com/items?itemName=docker.docker) extension for linting, code navigation, and vulnerability scanning.

{{< grid >}}
```

### Source [6]

- Source: `docker`
- Title: `Frequently asked questions about Docker Compose`
- Document ID: `618c274419a926311dbf502416d3d75f5357d2b1293ca1b304fb7a4ee260b364`
- Chunk ID: `4cdad5054cf9905b2e57bb7e64a106b8afa80562de145da163629af72bd0bfaa`

```text
---
description: Answers to common questions about Docker Compose, including v1 vs v2, commands, shutdown behavior, and development setup.
keywords: docker compose faq, docker compose questions, docker-compose vs docker compose, docker compose json, docker compose stop delay, run multiple docker compose
title: Frequently asked questions about Docker Compose
linkTitle: FAQs
weight: 10
tags: [FAQ]
aliases:
- /compose/faq/
---

### What is the difference between `docker compose` and `docker-compose`

Version one of the Docker Compose command-line binary was first released in 2014. It was written in Python, and is invoked with `docker-compose`. Typically, Compose v1 projects include a top-level version element in the `compose.yaml` file, with values ranging from 2.0 to 3.8, which refer to the specific file formats.

Version two of the Docker Compose command-line binary was announced in 2020, is written in Go, and is invoked with `docker compose`. Compose v2 ignores the version top-level element in the compose.yaml file.

Compose v5, released in 2025, uses the same `docker compose` command and is functionally identical to Compose v2. Its primary distinction is the introduction of an official [Go SDK](/manuals/compose/compose-sdk.md).

For further information, see [History and development of Compose](/manuals/compose/intro/history.md).

### What's the difference between `up`, `run`, and `start`?

Typically, you want `docker compose up`. Use `up` to start or restart all the
services defined in
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-011

**Category:** `version_specific`

**Expected behavior:** `answer_with_evidence`

## Query

What does current FastAPI documentation recommend instead of the deprecated tiangolo/uvicorn-gunicorn-fastapi base image?

## Model answer

The current FastAPI documentation recommends building a custom Docker image from scratch instead of using the deprecated `tiangolo/uvicorn-gunicorn-fastapi` base image [1]. This is because Uvicorn now supports managing and restarting workers via the `--workers` command line option, eliminating the need for Gunicorn to manage Uvicorn processes [1]. The documentation states that building a custom image is essentially the same amount of code as using a base image and is preferable, especially in Kubernetes environments where cluster-level replication is already configured [1]. Therefore, users should avoid the deprecated base image and instead build their own Docker image for FastAPI [1].

## API citations

```json
[
  {
    "citation_id": "1",
    "document_id": "6527bed73fabaacf86451f71870e3d0de965813fa3beb129902fe567a5a8f815",
    "chunk_id": "6a861ef45f5981dca517f005e92de7ae9d7e5f4437ea86bf12fd0f9c43e46fde"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `fastapi`
- Title: `FastAPI in Containers - Docker { #fastapi-in-containers-docker }`
- Document ID: `6527bed73fabaacf86451f71870e3d0de965813fa3beb129902fe567a5a8f815`
- Chunk ID: `6a861ef45f5981dca517f005e92de7ae9d7e5f4437ea86bf12fd0f9c43e46fde`

```text
container, right before starting the process with the app.

### Base Docker Image { #base-docker-image }

There used to be an official FastAPI Docker image: [tiangolo/uvicorn-gunicorn-fastapi](https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker). But it is now deprecated. ⛔️

You should probably **not** use this base Docker image (or any other similar one).

If you are using **Kubernetes** (or others) and you are already setting **replication** at the cluster level, with multiple **containers**. In those cases, you are better off **building an image from scratch** as described above: [Build a Docker Image for FastAPI](#build-a-docker-image-for-fastapi).

And if you need to have multiple workers, you can simply use the `--workers` command line option.

/// note | Technical Details

The Docker image was created when Uvicorn didn't support managing and restarting dead workers, so it was needed to use Gunicorn with Uvicorn, which added quite some complexity, just to have Gunicorn manage and restart the Uvicorn worker processes.

But now that Uvicorn (and the `fastapi` command) support using `--workers`, there's no reason to use a base Docker image instead of building your own (it's pretty much the same amount of code 😅).

///

## Deploy the Container Image { #deploy-the-container-image }

After having a Container (Docker) Image there are several ways to deploy
```

### Source [2]

- Source: `fastapi`
- Title: `Tutorial - User Guide { #tutorial-user-guide }`
- Document ID: `ca010678ccaff28143d3d553a4f0938a843e47b586574053775373ae3ff818c5`
- Chunk ID: `ef59ce1a427c28b6fb53a0fce9b708df01e5a5dfd2021f879f90b5065c3a051d`

```text
`, `README.md`, or other files. You will create the application files yourself in the next steps of this tutorial.

Then `cd awesome-project` enters the new project directory before adding FastAPI.

`uv` will use a compatible Python version already installed on your system, or download one if needed.

When you run `uv add`, it selects compatible versions of FastAPI and all the packages FastAPI depends on. It records the exact versions in `uv.lock`, making it possible to install the same package versions later on another computer or when deploying the application.

Creating or updating this file is called [**locking** the project dependencies](https://docs.astral.sh/uv/concepts/projects/sync/). `uv` does this automatically when you add a package.

///

/// details | FastAPI installation options

When you install with `uv add "fastapi[standard]"` it comes with some default optional standard dependencies, including `fastapi-cloud-cli`, which allows you to deploy to [FastAPI Cloud](https://fastapicloud.com).

If you don't want to have those optional dependencies, you can instead install `uv add fastapi`.

If you want to install the standard dependencies but without the `fastapi-cloud-cli`, you can install with `uv add "fastapi[standard-no-fastapi-cloud-cli]"`.

///

/// details | Using `pip` instead

If you prefer to manage a virtual environment and packages manually, create and activate a virtual environment and then install FastAPI with `pip install "fastapi[standard]"`.
```

### Source [3]

- Source: `qdrant`
- Title: `Implement Cohere RAG connector`
- Document ID: `eabf05df8682ee449e6759b247b2e4a7e8597fd9f6d7048e55c46499b5f3d5af`
- Chunk ID: `ae62f1a249a255b98db0b0194bbdba2744745853e6ab42e4477f704409f18b85`

```text
limit=2,
    ).points
    return SearchResults(
        results=[
            Document(**point.payload)
            for point in results
        ]
    )
```

Our app might be launched locally for the development purposes, given we have the `uvicorn` server installed:

```shell
uvicorn main:app
```

FastAPI exposes an interactive documentation at `http://localhost:8000/docs`, where we can test our endpoint. The
`/search` endpoint is available there.

![FastAPI documentation](/documentation/tutorials/cohere-rag-connector/fastapi-openapi.png)

We can interact with it and check the documents that will be returned for a specific query. For example, we want to know
recall what we are supposed to do regarding the infrastructure for your projects.

```shell
curl -X "POST" \
    -H "Content-type: application/json" \
    -d '{"query": "Is there anything I have to do regarding the project infrastructure?"}' \
    "http://localhost:8000/search"
```

The output should look like following:

```json
{
  "results": [
    {
      "title": "Cloud Migration Strategy",
      "text": "Draft a plan for migrating our current on-premise infrastructure to the cloud. The plan should cover the selection of a cloud provider, cost analysis, and a phased migration approach. Identify critical applications for the first phase and any potential risks or challenges. Schedule a meeting with the IT department to discuss the plan."
    },
    {
      "title": "Project Alpha Review",
      "text": "Review the current progress of Project Alpha, focusing on the integration of the new API. Check for
```

### Source [4]

- Source: `fastapi`
- Title: `Alternatives, Inspiration and Comparisons { #alternatives-inspiration-and-comparisons }`
- Document ID: `cf9554d7d46f195574190a63b70766302a62539150bda735b07d6737221f7d7e`
- Chunk ID: `15b7b8606cdedb1ee12b58fe5af956eef54485583ee19717d7b975a81785ea4d`

```text
Technical Details

It used [`uvloop`](https://github.com/MagicStack/uvloop) instead of the default Python `asyncio` loop. That's what made it so fast.

It clearly inspired Uvicorn and Starlette, that are currently faster than Sanic in open benchmarks.

///

/// tip | Inspired **FastAPI** to

Find a way to have a crazy performance.

That's why **FastAPI** is based on Starlette, as it is the fastest framework available (tested by third-party benchmarks).

///

### [Falcon](https://falconframework.org/) { #falcon }

Falcon is another high performance Python framework, it is designed to be minimal, and work as the foundation of other frameworks like Hug.

It is designed to have functions that receive two parameters, one "request" and one "response". Then you "read" parts from the request, and "write" parts to the response. Because of this design, it is not possible to declare request parameters and bodies with standard Python type hints as function parameters.

So, data validation, serialization, and documentation, have to be done in code, not automatically. Or they have to be implemented as a framework on top of Falcon, like Hug. This same distinction happens in other frameworks that are inspired by Falcon's design, of having one request object and one response object as parameters.

/// tip | Inspired **FastAPI** to

Find ways to get great performance.

Along with Hug (as Hug is based on Falcon) inspired **FastAPI** to declare a `response` parameter in functions.

Although in FastAPI it's optional, and is used mainly to set headers
```

### Source [5]

- Source: `fastapi`
- Title: `Path Operation Configuration { #path-operation-configuration }`
- Document ID: `22312c7bef6ea427b0bd916b58a26f63cf3a014d6981a05e1d8c444923c30110`
- Chunk ID: `128d4788cb5ba9702bfd324c10bf3a16490d947e0476354824e5bbced43b4c1c`

```text
't provide one, **FastAPI** will automatically generate one of "Successful response".

///

<img src="/img/tutorial/path-operation-configuration/image03.png">

## Deprecate a *path operation* { #deprecate-a-path-operation }

If you need to mark a *path operation* as <dfn title="obsolete, recommended not to use it">deprecated</dfn>, but without removing it, pass the parameter `deprecated`:

{* ../../docs_src/path_operation_configuration/tutorial006_py310.py hl[16] *}

It will be clearly marked as deprecated in the interactive docs:

<img src="/img/tutorial/path-operation-configuration/image04.png">

Check how deprecated and non-deprecated *path operations* look:

<img src="/img/tutorial/path-operation-configuration/image05.png">

## Recap { #recap }

You can configure and add metadata for your *path operations* easily by passing parameters to the *path operation decorators*.
```

### Source [6]

- Source: `fastapi`
- Title: `SQL (Relational) Databases { #sql-relational-databases }`
- Document ID: `7a4e00fcad592463e696602127de47e0c9cd1f4a46462c3479ea67f493da9ea8`
- Chunk ID: `2c2d984a6eab6e60c9791d54401a51f6a21e64520b7fde18292e98ece4b0759a`

```text
/docs_src/sql_databases/tutorial002_an_py310.py ln[96:103] hl[101] *}

### Run the App Again { #run-the-app-again }

You can run the app again:

<div class="termy">

```console
$ uv run fastapi dev

<span style="color: green;">INFO</span>:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

</div>

If you go to the `/docs` API UI, you will see that it is now updated, and it won't expect to receive the `id` from the client when creating a hero, etc.

<div class="screenshot">
<img src="/img/tutorial/sql-databases/image02.png">
</div>

## Recap { #recap }

You can use [**SQLModel**](https://sqlmodel.tiangolo.com/) to interact with a SQL database and simplify the code with *data models*  and *table models*.

You can learn a lot more at the **SQLModel** docs, there's a longer mini [tutorial on using SQLModel with **FastAPI**](https://sqlmodel.tiangolo.com/tutorial/fastapi/). 🚀
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-012

**Category:** `version_specific`

**Expected behavior:** `answer_with_evidence`

## Query

What does current FastAPI documentation recommend instead of startup and shutdown event handlers?

## Model answer

The current FastAPI documentation recommends using the `lifespan` parameter of the `FastAPI` app instead of `startup` and `shutdown` event handlers [1]. It explicitly states that if you provide a `lifespan` parameter, `startup` and `shutdown` event handlers will no longer be called, and it's all `lifespan` or all events, not both [1]. Therefore, the recommended approach is to use the `lifespan` parameter rather than standalone startup and shutdown event handlers.

## API citations

```json
[
  {
    "citation_id": "1",
    "document_id": "78b25bcb3b1ed8f18a03094b22b5e824ec8175ebb405c598999c161e79df51f0",
    "chunk_id": "4e399fecc97b128da28ccb2fa519f415f56082eda7dee8e6a0770e1a3607bb9f"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `fastapi`
- Title: `Lifespan Events { #lifespan-events }`
- Document ID: `78b25bcb3b1ed8f18a03094b22b5e824ec8175ebb405c598999c161e79df51f0`
- Chunk ID: `4e399fecc97b128da28ccb2fa519f415f56082eda7dee8e6a0770e1a3607bb9f`

```text
) { #alternative-events-deprecated }

/// warning

The recommended way to handle the *startup* and *shutdown* is using the `lifespan` parameter of the `FastAPI` app as described above. If you provide a `lifespan` parameter, `startup` and `shutdown` event handlers will no longer be called. It's all `lifespan` or all events, not both.

You can probably skip this part.

///

There's an alternative way to define this logic to be executed during *startup* and during *shutdown*.

You can define event handlers (functions) that need to be executed before the application starts up, or when the application is shutting down.

These functions can be declared with `async def` or normal `def`.

### `startup` event { #startup-event }

To add a function that should be run before the application starts, declare it with the event `"startup"`:

{* ../../docs_src/events/tutorial001_py310.py hl[8] *}

In this case, the `startup` event handler function will initialize the items "database" (just a `dict`) with some values.

You can add more than one event handler function.

And your application won't start receiving requests until all the `startup` event handlers have completed.

### `shutdown` event { #shutdown-event }

To add a function that should be run when the application is shutting down, declare it with the event `"shutdown"`:

{* ../../docs_src/events/tutorial002_py310.py hl[6] *}

Here, the
```

### Source [2]

- Source: `fastapi`
- Title: `Benchmarks { #benchmarks }`
- Document ID: `0d67b8f953bedca13ba9a97991c18b4ea2810719ff78d4800063aac1f6bff6cb`
- Chunk ID: `97dfb94f61eb24c9a027888a64d03aeb1389900e28fec6c68ca73c278efa5c07`

```text
't even add overhead to running applications, it is generated on startup).
    * If you didn't use FastAPI and used Starlette directly (or another tool, like Sanic, Flask, Responder, etc) you would have to implement all the data validation and serialization yourself. So, your final application would still have the same overhead as if it was built using FastAPI. And in many cases, this data validation and serialization is the biggest amount of code written in applications.
    * So, by using FastAPI you are saving development time, bugs, lines of code, and you would probably get the same performance (or better) you would if you didn't use it (as you would have to implement it all in your code).
    * If you are comparing FastAPI, compare it against a web application framework (or set of tools) that provides data validation, serialization and documentation, like Flask-apispec, NestJS, Molten, etc. Frameworks with integrated automatic data validation, serialization and documentation.
```

### Source [3]

- Source: `fastapi`
- Title: `Tutorial - User Guide { #tutorial-user-guide }`
- Document ID: `ca010678ccaff28143d3d553a4f0938a843e47b586574053775373ae3ff818c5`
- Chunk ID: `de4b4a040dffdf1c799a9e14758edf6886c9b07432cd48f16c762bdab743a8e1`

```text
Application startup complete.
```

</div>

It is **HIGHLY encouraged** that you write or copy the code, edit it and run it locally.

Using it in your editor is what really shows you the benefits of FastAPI, seeing how little code you have to write, all the type checks, autocompletion, etc.

---

## Install FastAPI { #install-fastapi }

The first step is to set up your project and add FastAPI.

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/), then create a project and add FastAPI:

<div class="termy">

```console
$ uv init awesome-project --bare
$ cd awesome-project
$ uv add "fastapi[standard]"

---> 100%
```

</div>

`uv add` creates the project's virtual environment in `.venv`, adds FastAPI to `pyproject.toml`, and creates `uv.lock` so the same package versions can be installed later.

/// details | What these commands do

* `uv init`: create a new Python project.
* `awesome-project`: create the project in a new directory with this name.
* `--bare`: create only the minimal `pyproject.toml` file, without generating a sample `main.py`, `README.md`, or other files. You will create the application files yourself in the next steps of this tutorial.

Then `cd awesome-project` enters the new project directory before adding FastAPI.

`uv` will use a compatible Python version already installed on your system, or download
```

### Source [4]

- Source: `fastapi`
- Title: `Deployments Concepts { #deployments-concepts }`
- Document ID: `03e8ad3174ef1e2249a83d26b22b953e37a343bc25935aa38a08a5eeecfa243d`
- Chunk ID: `e8b474309c68765a3640640d59949556f367f45c963a0c73016f44119de38190`

```text
program }

To achieve this, you will normally have a **separate program** that would make sure your application is run on startup. And in many cases, it would also make sure other components or applications are also run, for example, a database.

### Example Tools to Run at Startup { #example-tools-to-run-at-startup }

Some examples of the tools that can do this job are:

* Docker
* Kubernetes
* Docker Compose
* Docker in Swarm Mode
* Systemd
* Supervisor
* Handled internally by a cloud provider as part of their services
* Others...

I'll give you more concrete examples in the next chapters.

## Restarts { #restarts }

Similar to making sure your application is run on startup, you probably also want to make sure it is **restarted** after failures.

### We Make Mistakes { #we-make-mistakes }

We, as humans, make **mistakes**, all the time. Software almost *always* has **bugs** hidden in different places. 🐛

And we as developers keep improving the code as we find those bugs and as we implement new features (possibly adding new bugs too 😅).

### Small Errors Automatically Handled { #small-errors-automatically-handled }

When building web APIs with FastAPI, if there's an error in our code, FastAPI will normally contain it to the single request that triggered the error. 🛡

The client will get a **500 Internal Server Error** for that request, but the application will continue working for the next requests instead of just crashing completely.

### Bigger Errors - Crashes { #bigger-errors-crashes }

Nevertheless, there might be cases where we write some code that **crashes the entire application** making Uvicorn and Python crash. 💥

And
```

### Source [5]

- Source: `fastapi`
- Title: `Alternatives, Inspiration and Comparisons { #alternatives-inspiration-and-comparisons }`
- Document ID: `cf9554d7d46f195574190a63b70766302a62539150bda735b07d6737221f7d7e`
- Chunk ID: `64046b605d13753229b29974ad900f7b34e45d439ad23bc23cc56c5680caa82f`

```text
**FastAPI** then takes that JSON Schema data and puts it in OpenAPI, apart from all the other things it does.

///

### [Starlette](https://starlette.dev/) { #starlette }

Starlette is a lightweight <dfn title="The new standard for building asynchronous Python web applications">ASGI</dfn> framework/toolkit, which is ideal for building high-performance asyncio services.

It is very simple and intuitive. It's designed to be easily extensible, and have modular components.

It has:

* Seriously impressive performance.
* WebSocket support.
* In-process background tasks.
* Startup and shutdown events.
* Test client built on HTTPX.
* CORS, GZip, Static Files, Streaming responses.
* Session and Cookie support.
* 100% test coverage.
* 100% type annotated codebase.
* Few hard dependencies.

Starlette is currently the fastest Python framework tested. Only surpassed by Uvicorn, which is not a framework, but a server.

Starlette provides all the basic web microframework functionality.

But it doesn't provide automatic data validation, serialization or documentation.

That's one of the main things that **FastAPI** adds on top, all based on Python type hints (using Pydantic). That, plus the dependency injection system, security utilities, OpenAPI schema generation, etc.

/// note | Technical Details

ASGI is a new "standard" being developed by Django core team members. It is still not a "Python standard" (a PEP), although they are in the process of doing that.

Nevertheless, it is already being used as a "standard" by several tools
```

### Source [6]

- Source: `fastapi`
- Title: `FastAPI { #fastapi }`
- Document ID: `282cd364ed129676331707f1f4ae2834a515ffc121b41ef3c02d6213bf371215`
- Chunk ID: `14acaa767d375089a4526cc25f06ce8c225f9c12b95462bb6ca4a977ca1bd368`

```text
8000                  │
 │                                                     │
 │  API docs: http://127.0.0.1:8000/docs               │
 │                                                     │
 │  Running in development mode, for production use:   │
 │                                                     │
 │  fastapi run                                        │
 │                                                     │
 ╰─────────────────────────────────────────────────────╯

INFO:     Will watch for changes in these directories: ['/home/user/code/awesomeapp']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [2248755] using WatchFiles
INFO:     Started server process [2248757]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

</div>

<details markdown="1">
<summary>About the command <code>fastapi dev</code>...</summary>

The command `fastapi dev` reads your `main.py` file automatically, detects the **FastAPI** app in it, and starts a server using [Uvicorn](https://uvicorn.dev).

By default, `fastapi dev` will start with auto-reload enabled for local development.

You can read more about it in the [FastAPI CLI docs](https://fastapi.tiangolo.com/fastapi-cli/).

</details>

### Check it { #check-it }

Open your browser at [http://127.0.0.1:8000/items/5?q=somequery](http://127.0.0.1:8000/items/5?q=somequery).

You will see the JSON response
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-013

**Category:** `cross_tool`

**Expected behavior:** `answer_with_evidence`

## Query

How can a LangGraph RAG workflow use Qdrant for retrieval while keeping workflow-state persistence separate?

## Model answer

A LangGraph RAG workflow can use Qdrant for retrieval by integrating Qdrant's vector search capabilities as a retrieval node within the LangGraph workflow. LangGraph supports the addition of retrieval tools, such as those from LangChain, which can leverage Qdrant for vector similarity search [2]. This allows the workflow to retrieve relevant documents based on semantic similarity during execution.

To keep workflow-state persistence separate from retrieval, LangGraph provides built-in state management and persistence mechanisms that operate independently of the retrieval layer [2]. Since Qdrant is used solely for retrieval (i.e., fetching documents via vector search), and LangGraph manages the state (e.g., agent memory, intermediate steps, and execution history), the state persistence is handled by LangGraph’s internal mechanisms, while Qdrant remains a dedicated retrieval service with no direct involvement in state storage.

Thus, the workflow can maintain a clear separation: Qdrant handles document retrieval, and LangGraph manages the agent’s state, enabling both efficient retrieval and persistent, stateful execution [2].

[2]

## API citations

```json
[
  {
    "citation_id": "2",
    "document_id": "5fb1044b39a459160a19fe058cafd641d1d98746d7b884a004cd016a1046f516",
    "chunk_id": "191c068649e52500255d3add650e1b163e31c99c44f8bf4d1cee960d12825e41"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `qdrant`
- Title: `Agentic RAG with LangGraph`
- Document ID: `b1bcbb85f1f8599df8bdfd5603fc41e70deb47e3160809efd9c56e6fc75cc7a5`
- Chunk ID: `5a09ba8ebdcfbcccfc4a573ecf5edbfd19d10da6edccfad2a747456342217247`

```text
---
title: Agentic RAG with LangGraph
short_description: "Build an agentic RAG system with LangGraph and Qdrant that orchestrates multi-step retrieval, web search, and tool selection."
description: "Tutorial: build an agentic RAG workflow using LangGraph for state management and Qdrant for vector retrieval, with multi-source routing and tool orchestration."
weight: 15
partition: ecosystem
hideInSidebar: true
aliases:
  - /documentation/agentic-rag-langgraph/
---
# Agentic RAG with LangGraph and Qdrant

| Time: 45 min | Level: Intermediate |
| --- | ----------- |

Traditional Retrieval-Augmented Generation (RAG) systems follow a straightforward path: query → retrieve → generate. Sure, this works well for many scenarios. But let’s face it—this linear approach often struggles when you're dealing with complex queries that demand multiple steps or pulling together diverse types of information.

[Agentic RAG](https://qdrant.tech/articles/agentic-rag/) takes things up a notch by introducing AI agents that can orchestrate multiple retrieval steps and smartly decide how to gather and use the information you need. Think of it this way: in an Agentic RAG workflow, RAG becomes just one powerful tool in a much bigger and more versatile toolkit.

By combining LangGraph’s robust state management with Qdrant’s cutting-edge vector search, we’ll build a system that doesn’t just answer questions—it tackles complex, multi-step information retrieval tasks with finesse.

## What We’ll Build

We’re building an AI agent to answer questions about Hugging Face and Transformers documentation using LangGraph. At the heart of our AI agent lies LangGraph,
```

### Source [2]

- Source: `qdrant`
- Title: `LangGraph`
- Document ID: `5fb1044b39a459160a19fe058cafd641d1d98746d7b884a004cd016a1046f516`
- Chunk ID: `191c068649e52500255d3add650e1b163e31c99c44f8bf4d1cee960d12825e41`

```text
---
title: LangGraph
short_description: "Add Qdrant retrieval nodes to LangGraph workflows in Python or JavaScript to ground stateful, multi-actor agent applications in your data."
description: "Use Qdrant retrieval tools in LangGraph workflows to build stateful, multi-actor agents that combine LangChain components with hybrid vector search."
aliases: [ ../integrations/langgraph/ ]
---

# LangGraph

[LangGraph](https://github.com/langchain-ai/langgraph) is a library for building stateful, multi-actor applications, ideal for creating agentic workflows. It provides fine-grained control over both the flow and state of your application, crucial for creating reliable agents.

You can define flows that involve cycles, essential for most agentic architectures, differentiating it from DAG-based solutions. Additionally, LangGraph includes built-in persistence, enabling advanced human-in-the-loop and memory features.

LangGraph works seamlessly with all the components of LangChain. This means we can utilize Qdrant's [Langchain integration](/documentation/frameworks/langchain/) to create retrieval nodes in LangGraph, available in both Python and Javascript!

## Usage

- Install the required dependencies

```python
$ pip install langgraph langchain_community langchain_qdrant fastembed
```

```typescript
$ npm install @langchain/langgraph langchain @langchain/qdrant @langchain/openai
```

- Create a retriever tool to add to the LangGraph workflow.

```python

from langchain.tools.retriever import create_retriever_tool
```

### Source [3]

- Source: `qdrant`
- Title: `Dynamiq`
- Document ID: `87981d183d7754af3a711b28698dbc71c1556ff5c285337b713bf82ab580ab33`
- Chunk ID: `2163ec8505e77a4ae44118ac1e128f2c7b0a82b0657e728dc412969b518ce514`

```text
---
title: Dynamiq
short_description: "Add Qdrant as a writer, retriever, or agent memory inside Dynamiq Gen AI workflows to orchestrate RAG and tool-using LLM agents."
description: "Use Qdrant in Dynamiq Gen AI workflows for document writing, retrieval, and agent memory to power RAG pipelines and tool-augmented LLM agents."
---

# Dynamiq

Dynamiq is your all-in-one Gen AI framework, designed to streamline the development of AI-powered applications. Dynamiq specializes in orchestrating retrieval-augmented generation (RAG) and large language model (LLM) agents.

Qdrant is a vector database available in Dynamiq, capable of serving multiple roles. It can be used for writing and retrieving documents, acting as memory for agent interactions, and functioning as a retrieval tool that agents can call when needed.

## Installing

First, ensure you have the `dynamiq` library installed:

```bash
$ pip install dynamiq
```

## Retriever node

The QdrantDocumentRetriever node enables efficient retrieval of relevant documents based on vector similarity search.

```python
from dynamiq.nodes.retrievers import QdrantDocumentRetriever
from dynamiq import Workflow

# Define a retriever node to fetch most relevant documents
retriever_node = QdrantDocumentRetriever(
    index_name="default",
    top_k=5,  # Optional: Maximum number of documents to retrieve
    filters={...}  # Optional: Additional filtering conditions
)

# Create a workflow and add the retriever node
wf = Workflow()
wf.flow.add_nodes
```

### Source [4]

- Source: `qdrant`
- Title: `LangChain`
- Document ID: `62872036ea48d1b65ab9411a5ac952f9ea62cddc1cbab2130a93cd850307fb8c`
- Chunk ID: `32faadbac2057e3699b42fe657c599d7e7d16534cc53b3c7b52ecd71c7cab06f`

```text
---
title: LangChain
short_description: "Build LangChain apps with Qdrant as the vector store, supporting dense, sparse, and hybrid retrieval for semantic search and RAG."
description: "Use the LangChain Qdrant integration to power semantic search and RAG with dense, sparse, and hybrid retrieval over your documents and embeddings."
aliases:
  - ../integrations/langchain/
  - /documentation/overview/integrations/langchain/
---

# LangChain

LangChain is a library that makes developing Large Language Model-based applications much easier. It unifies the interfaces
to different libraries, including major embedding providers and Qdrant. Using LangChain, you can focus on the business value instead of writing the boilerplate.

LangChain distributes the Qdrant integration as a partner package.

It might be installed with pip:

```bash
pip install langchain-qdrant
```

The integration supports searching for relevant documents using dense/sparse and hybrid retrieval.

Qdrant acts as a vector index that may store the embeddings with the documents used to generate them. There are various ways to use it, but calling `QdrantVectorStore.from_texts` or `QdrantVectorStore.from_documents` is probably the most straightforward way to get started:

```python
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

doc_store = QdrantVectorStore.from_texts(
    texts, embeddings, url="<qdrant-url>", api_key="<qdrant-api
```

### Source [5]

- Source: `qdrant`
- Title: `n8n Workflow Automation`
- Document ID: `a6b8f385be386ae9053d55cf91b3a3c03319bb2f4d57f0ad45427a3a934619c1`
- Chunk ID: `b7b146239370575006f98d383922eaf65258852b3a916a674fcc8931e5140a16`

```text
---
title: n8n Workflow Automation
short_description: "Automate Qdrant workflows in n8n: build no-code pipelines for vector search, recommendations, and unstructured data analysis."
description: "Tutorial: connect Qdrant to n8n to automate vector search, recommendations, and unstructured data workflows using a low-code visual pipeline builder."
weight: 35
#partition: ecosystem
social_preview_image: /documentation/examples/qdrant-n8n-2/preview/social_preview.png
aliases:
  - /blog/qdrant-n8n-beyond-simple-similarity-search/
  - /documentation/qdrant-n8n/

---

<!-- ![n8n-qdrant](/documentation/examples/qdrant-n8n-2/cover.png) -->

# Automate Qdrant Workflows with n8n

| Time: 45 min | Level: Intermediate |
| --- | ----------- |

This tutorial shows how to combine Qdrant with [n8n](https://n8n.io/) low-code automation platform to cover **use cases beyond basic Retrieval-Augmented Generation (RAG)**. You'll learn how to use vector search for **recommendations** and **unstructured big data analysis**.

<aside role="status">
  Since this tutorial was created, <a href="https://qdrant.tech/documentation/platforms/n8n/">an official Qdrant node for n8n</a> has been released. It simplifies workflow
```

### Source [6]

- Source: `qdrant`
- Title: `Essential Examples`
- Document ID: `803bef4cb1a4f1617242b8e9264462dec5652c7fa71bd6eb2ff6145ad51354e7`
- Chunk ID: `378ef397e7ce65925f94d2a969358a83426bee5793f8f7d3565d49bf5ebcf0f0`

```text
---
title: Essential Examples
short_description: "Hands-on Qdrant integration tutorials: connect AI agents, RAG pipelines, ingestion stacks, and automation tools to a vector database."
description: "Step-by-step tutorials integrating Qdrant with LangChain, LlamaIndex, n8n, AWS S3, and other AI ecosystem tools to build production retrieval pipelines."
weight: 1200
partition: ecosystem
---
# Integration Examples

*Step-by-step guides for connecting Qdrant to the broader AI ecosystem and data stacks.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [5-Minute RAG with DeepSeek](/documentation/tutorials-build-essentials/rag-deepseek/) | Build a RAG pipeline with DeepSeek enrichment. | <span class="pill">Python</span> | 5m | <span class="text-green">Beginner</span> |
| [Agentic RAG with CrewAI](/documentation/tutorials-build-essentials/agentic-rag-crewai-zoom/) | Step-by-step multi-agent RAG system. | <span class="pill">CrewAI</span> | 45m | <span class="text-green">Beginner</span> |
| [n8n Workflow Automation](/documentation/tutorials-build-essentials/qdrant-n8n/) | Combine Qdrant with low-code n8n workflows. | <span class="pill">n8n</span> | 45m |
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-014

**Category:** `cross_tool`

**Expected behavior:** `answer_with_evidence`

## Query

For a Transformers inference service running on Kubernetes, which responsibilities belong to Transformers model serving and which belong to Kubernetes service exposure?

## Model answer

For a Transformers inference service running on Kubernetes:

- **Transformers model serving** responsibilities include model loading, inference execution, request handling, and supporting features such as quantization, continuous batching, and attention backends (e.g., flash attention) [5]. The `transformers serve` CLI provides a lightweight server that handles REST API endpoints like `/v1/chat/completions` and supports model loading from the Hugging Face Hub [4][5].

- **Kubernetes service exposure** responsibilities include defining a service that exposes the application to external traffic via a service endpoint, enabling load balancing, service discovery, and traffic routing across Pods [1][3]. A Kubernetes Service abstracts the set of Pods and provides a stable network endpoint, allowing clients to access the inference service without needing to know the underlying Pod details or IP addresses [1][3].

Thus, model serving logic and inference execution are handled by the Transformers library and its inference tools (e.g., `transformers serve`), while Kubernetes manages the network exposure, load balancing, and service discovery for the deployed inference service [1][3].

## API citations

```json
[
  {
    "citation_id": "5",
    "document_id": "7f6e38d43e1a9e062243553cefb1bae249456ab282b422f734c8ed8367f28ae2",
    "chunk_id": "a6a667e600639aa42400d506a53dc4dee7a5cd4a2c9346ac9542ed2d82a38905"
  },
  {
    "citation_id": "4",
    "document_id": "42d305c44939a6d3bfbf8d31ad5faf47762c11a7f1f0f98f147cffc32bc196bf",
    "chunk_id": "1a8339850f987ee3d57531c176e208faddfda1bcc84e5bcc419857f747a43490"
  },
  {
    "citation_id": "1",
    "document_id": "d8209ddf0b20378c9c14b1167a74193a287994409523b99637f97cfc5f494585",
    "chunk_id": "df45fcad57a5b633768f7db8e9c8a4596ca71dc0ba94ade2e7ff01d1d761dbd9"
  },
  {
    "citation_id": "3",
    "document_id": "14557c0297d48b74387af4d4bd856dc2b310cc90138810befd8e451e4d22e0a0",
    "chunk_id": "926ad448026875a61aa22625df9696c5d9ac9e4442c7bb3dfd0f70765376b351"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `kubernetes`
- Title: `Using a Service to Expose Your App`
- Document ID: `d8209ddf0b20378c9c14b1167a74193a287994409523b99637f97cfc5f494585`
- Chunk ID: `df45fcad57a5b633768f7db8e9c8a4596ca71dc0ba94ade2e7ff01d1d761dbd9`

```text
/controllers/replicaset/)
might then dynamically drive the cluster back to the desired state via the creation
of new Pods to keep your application running. As another example, consider an image-processing
backend with 3 replicas. Those replicas are exchangeable; the front-end system should
not care about backend replicas or even if a Pod is lost and recreated. That said,
each Pod in a Kubernetes cluster has a unique IP address, even Pods on the same Node,
so there needs to be a way of automatically reconciling changes among Pods so that your
applications continue to function.

{{% alert %}}
_A Kubernetes Service is an abstraction layer which defines a logical set of Pods and
enables external traffic exposure, load balancing and service discovery for those Pods._
{{% /alert %}}

A [Service](/docs/concepts/services-networking/service/) in Kubernetes is an abstraction
which defines a logical set of Pods and a policy by which to access them. Services
enable a loose coupling between dependent Pods. A Service is defined using YAML or JSON,
like all Kubernetes object manifests. The set of Pods targeted by a Service is usually
determined by a _label selector_ (see below for why you might want a Service without
including a `selector` in the spec).

Although each Pod has a unique IP address, those IPs are not exposed outside the
cluster without a Service. Services allow your applications to receive traffic.
Services can be exposed in different ways by specifying a `type` in the `spec` of the Service:

* _ClusterIP_ (default) - Exposes the Service on an internal IP in the cluster. This
type makes the Service only reachable from within the cluster.

* _NodePort_ - Exposes the Service on the
```

### Source [2]

- Source: `huggingface`
- Title: `Transformers`
- Document ID: `ce25e7e156857feddd8bdd8080be7f70c4a558678316f023c940c80d80bc2afe`
- Chunk ID: `2ccd2d32bfd3f281c09c6dd97fa09b82d1f3361569e59dab5c1704ff439f3351`

```text
, Unsloth, DeepSpeed, FSDP, PyTorch-Lightning, ...), inference engines (vLLM, SGLang, TGI, ...),
and adjacent modeling libraries (llama.cpp, mlx, ...) which leverage the model definition from `transformers`.

We pledge to help support new state-of-the-art models and democratize their usage by having their model definition be
simple, customizable, and efficient.

There are over 1M+ Transformers [model checkpoints](https://huggingface.co/models?library=transformers&sort=trending) on the [Hugging Face Hub](https://huggingface.com/models) you can use.

Explore the [Hub](https://huggingface.com/) today to find a model and use Transformers to help you get started right away.

Explore the [Models Timeline](./models_timeline) to discover the latest text, vision, audio and multimodal model architectures in Transformers.

## Features

Transformers provides everything you need for inference or training with state-of-the-art pretrained models. Some of the main features include:

- [Pipeline](./pipeline_tutorial): Simple and optimized inference class for many machine learning tasks like text generation, image segmentation, automatic speech recognition, document question answering, and more.
- [Trainer](./trainer): A comprehensive trainer that supports features such as mixed precision, torch.compile, and FlashAttention for training and distributed training for PyTorch models.
- [generate](./llm_tutorial): Fast text generation with large language models (LLMs) and vision language models (VLMs), including support for
```

### Source [3]

- Source: `kubernetes`
- Title: `Service`
- Document ID: `14557c0297d48b74387af4d4bd856dc2b310cc90138810befd8e451e4d22e0a0`
- Chunk ID: `926ad448026875a61aa22625df9696c5d9ac9e4442c7bb3dfd0f70765376b351`

```text
---
reviewers:
- bprashanth
title: Service
api_metadata:
- apiVersion: "v1"
  kind: "Service"
feature:
  title: Service discovery and load balancing
  description: >
    No need to modify your application to use an unfamiliar service discovery mechanism. Kubernetes gives Pods their own IP addresses and a single DNS name for a set of Pods, and can load-balance across them.
description: >-
  Expose an application running in your cluster behind a single outward-facing
  endpoint, even when the workload is split across multiple backends.
content_type: concept
weight: 10
---

<!-- overview -->

{{< glossary_definition term_id="service" length="short" prepend="In Kubernetes, a Service is" >}}

A key aim of Services in Kubernetes is that you don't need to modify your existing
application to use an unfamiliar service discovery mechanism.
You can run code in Pods, whether this is a code designed for a cloud-native world, or
an older app you've containerized. You use a Service to make that set of Pods available
on the network so that clients can interact with it.

If you use a {{< glossary_tooltip term_id="deployment" >}} to run your app,
that Deployment can create and destroy Pods dynamically. From one moment to the next,
you don't know how many of those Pods are working and healthy; you might not even know
what those healthy Pods are named.
Kubernetes {{< glossary_tooltip term_id="pod" text="Pods" >}} are created and destroyed
to match the desired state of your cluster. Pods are ephemeral resources (you should not
expect that an individual Pod is reliable
```

### Source [4]

- Source: `huggingface`
- Title: `Serve CLI`
- Document ID: `42d305c44939a6d3bfbf8d31ad5faf47762c11a7f1f0f98f147cffc32bc196bf`
- Chunk ID: `1a8339850f987ee3d57531c176e208faddfda1bcc84e5bcc419857f747a43490`

```text
<!--Copyright 2025 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

⚠️ Note that this file is in Markdown but contains specific syntax for our doc-builder (similar to MDX) that may not be
rendered properly in your Markdown viewer.

-->

# Serve CLI

The `transformers serve` CLI is a lightweight option for local or self-hosted servers. It avoids the extra runtime and operational overhead of dedicated inference engines like vLLM. Use it for evaluation, experimentation, and moderate load deployments. Features like [continuous batching](../continuous_batching) increase throughput and lower latency.

> [!TIP]
> For large scale production deployments, use vLLM or SGLang with a Transformer model as the backend. Learn more in the [Inference backends](../community_integrations/transformers_as_backend) guide.

The `transformers serve` command spawns a local server compatible with the [OpenAI SDK](https://platform.openai.com/docs/overview). The server works with many third-party applications and supports the REST APIs below.

- `/v1/chat/completions` for text, image, audio, and video requests
- `/v1
```

### Source [5]

- Source: `huggingface`
- Title: `Server optimizations`
- Document ID: `7f6e38d43e1a9e062243553cefb1bae249456ab282b422f734c8ed8367f28ae2`
- Chunk ID: `a6a667e600639aa42400d506a53dc4dee7a5cd4a2c9346ac9542ed2d82a38905`

```text
transformers serve` is compatible with all quantization methods in Transformers. It supports pre-quantized models and runtime quantization.

Pre-quantized models don't require any changes. They offer the best balance between performance and accuracy. Install the appropriate quantization library. Then pass the pre-quantized model from the Hub to the `model` argument.

```sh
curl http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B-GGUF",
    "stream": true,
    "input": "Tell me a three sentence bedtime story about a unicorn."
  }'
```

Use `--quantization` to quantize a model at runtime. This is useful for new checkpoints or finetunes without pre-quantized weights. Only [bitsandbytes](../quantization/bitsandbytes) 4-bit and 8-bit quantization are supported.

```sh
transformers serve \
  --quantization bnb-4bit
```

## Attention backend

An optimized [attention backend](../attention_interface) improves memory efficiency and speeds up inference.

```sh
transformers serve \
  --continuous-batching \
  --attn-implementation "flash_attention_2"
```

### Apple Silicon (Metal flash attention)

Install [kernels](https://github.com/huggingface/kernels) to make `transformers serve` default to [kernels-community/metal-flash-sdpa](https://huggingface.co/kernels-community/metal-flash
```

### Source [6]

- Source: `huggingface`
- Title: `vLLM`
- Document ID: `4c8eb0477ead4fd51ed9654605ca2b2efdbcc34e6c565b1a010d949cabb0a95a`
- Chunk ID: `6f114e63719c49a82163ff1e8b0a857c0d4a5217f7d77e4faa3d480d55a882d1`

```text
-model-impl transformers` to the `vllm serve` command for online serving.

```bash
vllm serve meta-llama/Llama-3.2-1B \
    --task generate \
    --model-impl transformers
```

## Transformers integration

1. [`AutoConfig.from_pretrained`] loads the model's `config.json` from the Hub or your Hugging Face cache. vLLM checks the `architectures` field against its internal model registry to determine which vLLM model class to use.
2. If the model isn't in the registry, vLLM calls [`AutoModel.from_config`] to load the Transformers model implementation instead.
3. [`AutoTokenizer.from_pretrained`] loads the tokenizer files. vLLM caches some tokenizer internals to reduce overhead during inference.
4. Model weights download from the Hub in safetensors format.

Setting `model_impl="transformers"` bypasses the vLLM model registry and loads directly from Transformers. vLLM replaces most model modules (MoE, attention, linear layers) with its own optimized versions while keeping the Transformers model structure.

## Resources

- [vLLM docs](https://docs.vllm.ai/en/latest/models/supported_models.html#transformers) for more usage examples and tips.
- [Integration with Hugging Face](https://docs.vllm.ai/en/latest/design/huggingface_integration/) explains how vLLM integrates with Transformers.
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-015

**Category:** `cross_tool`

**Expected behavior:** `answer_with_evidence`

## Query

What responsibilities belong to FastAPI versus Qdrant when building a vector-search API?

## Model answer

The responsibilities of FastAPI and Qdrant when building a vector-search API are as follows:

- **Qdrant** is responsible for handling the storage and retrieval of high-dimensional vectors through its vector database and similarity search engine. It manages the indexing, querying, and matching of vector embeddings, providing an API service for vector-based search operations [1]. Qdrant also supports asynchronous operations, enabling high-throughput, concurrent applications by leveraging its async Python client with ASGI-style frameworks [3].

- **FastAPI** is responsible for building and exposing the API layer of the service. It provides the endpoints that interact with Qdrant, allowing clients to send queries and receive search results. FastAPI serves as the web framework that wraps the vector search functionality, offering a fast, type-safe, and asynchronous interface for building the backend of the API [2][4].

In summary, Qdrant handles the core vector search operations (storage, indexing, and retrieval), while FastAPI manages the API layer, exposing these operations via HTTP endpoints [1][2][4].

## API citations

```json
[
  {
    "citation_id": "1",
    "document_id": "b59a86aa2d56cfb3fc1f86198db8dd02de251fe8ff663145958d0576d4c5dfed",
    "chunk_id": "5fafc9dde7a2a9855eb5fd96c4d1b272eb0a63c6fb9cc1e40385fe1bc71514ba"
  },
  {
    "citation_id": "3",
    "document_id": "1e5b99fe58d7f18a50c836305d12a9baf8cf944b1d4d98e60460f24e6829c0ab",
    "chunk_id": "a7250b78b1d25367564f41e63120548325513dfbd0b3f205bea792aeed38f4a3"
  },
  {
    "citation_id": "2",
    "document_id": "47b9147db524362808813fbbc81814042223473351f86183ff00f19a03f46c02",
    "chunk_id": "99ac55f3ddc777a7071fc9f095fae9cfa7893cc70f8b79e3e037fc41914e417e"
  },
  {
    "citation_id": "4",
    "document_id": "a6e0be4b18f2208576eeca2e6f823b26ffa7281bd6c6e248dc4a082c78644ab1",
    "chunk_id": "b2e8fbaa4898b9095dac59370d5617dbbd0009869991e4888d43206273401396"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `qdrant`
- Title: `5-Minute RAG with DeepSeek`
- Document ID: `b59a86aa2d56cfb3fc1f86198db8dd02de251fe8ff663145958d0576d4c5dfed`
- Chunk ID: `5fafc9dde7a2a9855eb5fd96c4d1b272eb0a63c6fb9cc1e40385fe1bc71514ba`

```text
!
FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
PyTorch is a machine learning framework based on the Torch library, used for applications such as computer vision and natural language processing.

Answer:
```

Our current prompt is much longer, and we also used a couple of strategies to make the responses even better:

1. The LLM has the role of software architect.
2. We provide more context to answer the question.
3. If the context contains no meaningful information, the model shouldn't make up an answer.

Let's find out if that works as expected.

**Question:**

```python
query_deepseek(metaprompt)
```
**Answer:**

```bash
'To build a web service using vector embeddings for search, you can use the following tools:\n\n1. **Qdrant**: As a vector database and similarity search engine, Qdrant will handle the storage and retrieval of high-dimensional vectors. It provides an API service for searching and matching vectors, making it ideal for applications that require vector-based search functionality.\n\n2. **FastAPI**: This web framework is perfect for building the API layer of your web service. It is fast, easy to use, and based on Python type hints, which makes it a great choice for developing the backend of your service. FastAPI will allow you to expose endpoints that interact with Qdrant for vector search operations.\n\n3. **PyTorch**: If you need to generate vector embeddings from your data (e.g., text, images), PyTorch can be
```

### Source [2]

- Source: `qdrant`
- Title: `Build a Hybrid Search API`
- Document ID: `47b9147db524362808813fbbc81814042223473351f86183ff00f19a03f46c02`
- Chunk ID: `99ac55f3ddc777a7071fc9f095fae9cfa7893cc70f8b79e3e037fc41914e417e`

```text
---
title: Build a Hybrid Search API
short_description: "Build a hybrid search service with Qdrant and FastEmbed by combining dense and sparse embeddings behind a FastAPI endpoint."
description: "Tutorial: build a hybrid search API with Qdrant and FastEmbed that fuses dense and sparse embeddings, served through a FastAPI application."
aliases:
  - /documentation/tutorials/hybrid-search-fastembed/
  - /documentation/beginner-tutorials/hybrid-search-fastembed/
  - /documentation/tutorials-search-engineering/hybrid-search-fastembed/
weight: 50
---

# Build a Search API with Qdrant's FastEmbed

| Time: 20 min | Level: Beginner | Output: [GitHub](https://github.com/qdrant/qdrant_demo/) |
| --- | ----------- | ----------- |----------- |

This tutorial shows you how to build and deploy your own hybrid search service to look through descriptions of companies from [startups-list.com](https://www.startups-list.com/) and pick the most similar ones to your query.
The website contains the company names, descriptions, locations, and a picture for each entry.

As we have already written on our [blog](/articles/hybrid-search/), there is no single definition of hybrid search.
In this tutorial we are covering the case with a combination of dense and [sparse embeddings](/articles/sparse-vectors/).
The former ones refer to the embed
```

### Source [3]

- Source: `qdrant`
- Title: `Async API`
- Document ID: `1e5b99fe58d7f18a50c836305d12a9baf8cf944b1d4d98e60460f24e6829c0ab`
- Chunk ID: `a7250b78b1d25367564f41e63120548325513dfbd0b3f205bea792aeed38f4a3`

```text
---
title: Async API
short_description: "Build high-throughput, concurrent applications on Qdrant with the async Python client and ASGI-style web frameworks."
description: "Tutorial: use Qdrant's async Python API with FastAPI and other ASGI frameworks to build non-blocking, high-throughput vector search applications."
aliases:
  - /documentation/tutorials/async-api/
  - /documentation/database-tutorials/async-api/
weight: 4
---

# Build High-Throughput Applications with Qdrant's Async API

| Time: 25 min | Level: Intermediate |
| --- | ----------- |

Asynchronous programming is being broadly adopted in the Python ecosystem. Tools such as FastAPI [have embraced this new
paradigm](https://fastapi.tiangolo.com/async/), but it is also becoming a standard for ML models served as SaaS. For example, the Cohere SDK
[provides an async client](https://github.com/cohere-ai/cohere-python/blob/856a4c3bd29e7a75fa66154b8ac9fcdf1e0745e0/src/cohere/client.py#L189) next to its synchronous counterpart.

Databases are often launched as separate services and are accessed via a network. All the interactions with them are IO-bound and can
be performed asynchronously so as not to waste time actively waiting for a server response. In Python, this is achieved by
using [
```

### Source [4]

- Source: `qdrant`
- Title: `Build a Semantic Search API`
- Document ID: `a6e0be4b18f2208576eeca2e6f823b26ffa7281bd6c6e248dc4a082c78644ab1`
- Chunk ID: `b2e8fbaa4898b9095dac59370d5617dbbd0009869991e4888d43206273401396`

```text
---
title: Build a Semantic Search API
short_description: "Build a neural semantic search service on Qdrant using sentence-transformer embeddings and a FastAPI search endpoint."
description: "Tutorial: build a neural search service that encodes text with sentence transformers, indexes vectors in Qdrant, and serves results through FastAPI."
aliases:
  - /documentation/tutorials/neural-search/
  - /documentation/beginner-tutorials/neural-search/
  - /documentation/tutorials-search-engineering/neural-search/
weight: 30
---

# Build a Semantic Search API with Qdrant

| Time: 30 min | Level: Beginner | Output: [GitHub](https://github.com/qdrant/qdrant_demo/tree/sentense-transformers) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1kPktoudAP8Tu8n8l-iVMOQhVmHkWV_L9?usp=sharing)   |
| --- | ----------- | ----------- |----------- |

This tutorial shows you how to build and deploy your own neural search service to look through descriptions of companies from [startups-list.com](https://www.startups-list.com/) and pick the most similar ones to your query. The website contains the company names, descriptions, locations, and a picture for each entry.

A neural
```

### Source [5]

- Source: `qdrant`
- Title: `FastEmbed & Qdrant`
- Document ID: `3011ccb546313f3187a896115dd9c3a13fe24a4fb6591a9e5d2825d52c66b5e4`
- Chunk ID: `236931aaf56b5457b95a58628528a882b3468f6937492b885bd1aea85b18a4ef`

```text
---
title: "FastEmbed & Qdrant"
short_description: "Build semantic search end-to-end using Qdrant Client and FastEmbed — generate embeddings, create a collection, and run vector queries in a few lines."
description: "Use Qdrant Client with FastEmbed to build end-to-end semantic search: generate embeddings, create a collection, and query for the most relevant documents."
weight: 20
---

# Using FastEmbed with Qdrant for Vector Search

## Install Qdrant Client and FastEmbed
```python
pip install "qdrant-client[fastembed]>=1.14.2"
```

## Initialize the client
Qdrant Client has a simple in-memory mode that lets you try semantic search locally.
```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")  # Qdrant is running from RAM.
```

## Add data
Now you can add two sample documents, their associated metadata, and a point `id` for each.

```python
docs = [
    "Qdrant has a LangChain integration for chatbots.",
    "Qdrant has a LlamaIndex integration for agents.",
]
metadata = [
    {"source": "langchain-docs"},
    {"source": "llamaindex-docs"},
]
ids = [42, 2]

```
## Create a collection

Qdrant stores vectors and associated metadata in collections.
Collection requires vector parameters to be set during creation.
In this tutorial, we'll be using `BAAI/bge-small-en`
```

### Source [6]

- Source: `qdrant`
- Title: `Documentation`
- Document ID: `20d13f0f0da75810cae21208a9b72b343fd7903ed733ab161fc4e3ba1be367e4`
- Chunk ID: `f2b3c5e6a7d5b701ec9dca016e6a5281a3ca844abd3a11c2e5112a5066569053`

```text
---
title: Documentation
short_description: "Build with Qdrant: install, run, and scale a vector search engine across self-hosted, Cloud, Hybrid Cloud, and Private Cloud deployments."
description: "Official Qdrant documentation for vector search and retrieval — quickstarts, deployment guides, integrations, and references for self-hosted and Qdrant Cloud."
weight: 2
hideTOC: true
breadcrumb: false
content:
  - partial: "documentation/banners/banner-a"
    title: Qdrant Documentation
    description: Qdrant is an AI-native vector search and a semantic search engine. You can use it to extract meaningful information from unstructured data.
    linkDescription: <a href="https://github.com/qdrant/qdrant_demo/" target="_blank">Clone this repo now</a> and build a search engine in five minutes.
    cloudButton:
      text: Cloud Quickstart
      url: /documentation/cloud-quickstart/
    localButton:
      text: Local Quickstart
      url: /documentation/quickstart/
      contained: true
  - partial: documentation/banners/banner-d
    developingTitle: Introducing Qdrant Edge
    developingDescription: Qdrant Edge is a lightweight, embedded vector search engine for in-process retrieval — no background services, minimal memory footprint, and no network required. Built for robots, kiosks, mobile devices, and any environment requiring offline-capable AI search.
    developingBlock:
      title: Run vector search anywhere, even offline
      button:
        text: Get Started
        url: /documentation/edge/edge-quickstart/
      image:
        src: /img/rocket.svg
        alt: Rocket
  - partial: documentation/sections/cards-section
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-016

**Category:** `insufficient`

**Expected behavior:** `insufficient_evidence`

## Query

What CPU and memory limits should I set for my Kubernetes Pod to handle exactly 500 requests per second?

## Model answer

The available sources do not provide a direct method or formula to calculate specific CPU and memory limits based on a request rate of 500 requests per second. While the sources explain how to configure CPU and memory requests and limits for Pods [1][2][4][5], they do not establish a relationship between request rate (e.g., 500 requests per second) and required CPU or memory resources.

Therefore, based on the provided information, it is not possible to determine exact CPU and memory limits for a Kubernetes Pod to handle 500 requests per second. The sources support configuration of resource requests and limits [1][2][4][5], but lack the performance modeling or throughput-to-resource mapping needed to derive specific values from a request rate.

Answer: The available sources do not provide sufficient information to determine specific CPU and memory limits for a Kubernetes Pod to handle exactly 500 requests per second. [1][2][4][5]

## API citations

```json
[
  {
    "citation_id": "1",
    "document_id": "b532700c42ff9bd35886dbc88a1ad31871d876442188d92f6672f7c1c1b09000",
    "chunk_id": "7e7bcb380a84b9840416f3810b7f9c51844e1e58ec29d91a9cf02a0865226d5a"
  },
  {
    "citation_id": "2",
    "document_id": "dd331c4450e49499920966c67f41858a8419448787aa0e29da447927002e0798",
    "chunk_id": "377228f31ee2296ea920d6b1dcc1f9fa7b3937bafb336c96701f4feb6d8a82bc"
  },
  {
    "citation_id": "4",
    "document_id": "f06a8d814d2df4435365f04bbd44396d2295fb1453bb554fe7f8ccb057881bc1",
    "chunk_id": "8fe58d84316fdd2b795c6fcb459146ae2c5461c493cf461221c50b09d7d14124"
  },
  {
    "citation_id": "5",
    "document_id": "9b34135c345f5524e5488329d9e5242afc20983d8e6a26dcbb292528d5fcdcee",
    "chunk_id": "7724247183d781f62b98595c61a5358718b90bd9d27e2b139f0ee27b07769583"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `kubernetes`
- Title: `Assign CPU Resources to Containers and Pods`
- Document ID: `b532700c42ff9bd35886dbc88a1ad31871d876442188d92f6672f7c1c1b09000`
- Chunk ID: `7e7bcb380a84b9840416f3810b7f9c51844e1e58ec29d91a9cf02a0865226d5a`

```text
request, Kubernetes automatically assigns a memory request that matches
the limit.

## Motivation for CPU requests and limits

By configuring the CPU requests and limits of the Containers that run in your
cluster, you can make efficient use of the CPU resources available on your cluster
Nodes. By keeping a Pod CPU request low, you give the Pod a good chance of being
scheduled. By having a CPU limit that is greater than the CPU request, you accomplish two things:

* The Pod can have bursts of activity where it makes use of CPU resources that happen to be available.
* The amount of CPU resources a Pod can use during a burst is limited to some reasonable amount.

## Clean up

Delete your namespace:

```shell
kubectl delete namespace cpu-example
```

## {{% heading "whatsnext" %}}

### For app developers

* [Assign Memory Resources to Containers and Pods](/docs/tasks/configure-pod-container/assign-memory-resource/)

* [Assign Pod-level CPU and memory resources](/docs/tasks/configure-pod-container/assign-pod-level-resources/)

* [Configure Quality of Service for Pods](/docs/tasks/configure-pod-container/quality-service-pod/)

* [Resize CPU and Memory Resources assigned to Containers](/docs/tasks/configure-pod-container/resize-container-resources/)

* [Resize Pod-level CPU and Memory Resources](/docs/tasks/configure-pod-container/resize-pod-resources/)

### For cluster administrators

* [Configure Default Memory Requests and Limits for a Namespace](
```

### Source [2]

- Source: `kubernetes`
- Title: `Control Memory Management Policies on a Node`
- Document ID: `dd331c4450e49499920966c67f41858a8419448787aa0e29da447927002e0798`
- Chunk ID: `377228f31ee2296ea920d6b1dcc1f9fa7b3937bafb336c96701f4feb6d8a82bc`

```text
memory: "200Mi"
        cpu: "2"
        example.com/device: "1"
```

Also, a pod sharing CPU(s) runs in the `Guaranteed` QoS class, when `requests` are equal to `limits`.

```yaml
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      limits:
        memory: "200Mi"
        cpu: "300m"
        example.com/device: "1"
      requests:
        memory: "200Mi"
        cpu: "300m"
        example.com/device: "1"
```

Notice that both CPU and memory requests must be specified for a Pod to lend it to Guaranteed QoS class.

## {{% heading "whatsnext" %}}

- Read [Troubleshooting Topology Management](/docs/tasks/debug/debug-cluster/topology/)
- Read the [KEP](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/1769-memory-manager) (Kubernetes enhancement proposal) for memory manager
* Read about [Pod-level resource managers](/docs/concepts/workloads/resource-managers/#pod-level-resource-managers).
```

### Source [3]

- Source: `kubernetes`
- Title: `Assign Memory Resources to Containers and Pods`
- Document ID: `05f0e08b44e7ac7043123d77b4295df7fb55ec1bea00c089b5f73a7d4ae3c4a5`
- Chunk ID: `5fe0c895ddb51a859c36f7b4c26225ab29fd527f0b5ac62e00ac212cbfd517a7`

```text
/kubernetes-api/{{< param "version" >}}/#limitrange-v1-core)
to specify a default value for the memory limit.

## Motivation for memory requests and limits

By configuring memory requests and limits for the Containers that run in your
cluster, you can make efficient use of the memory resources available on your cluster's
Nodes. By keeping a Pod's memory request low, you give the Pod a good chance of being
scheduled. By having a memory limit that is greater than the memory request, you accomplish two things:

* The Pod can have bursts of activity where it makes use of memory that happens to be available.
* The amount of memory a Pod can use during a burst is limited to some reasonable amount.

## Clean up

Delete your namespace. This deletes all the Pods that you created for this task:

```shell
kubectl delete namespace mem-example
```

## {{% heading "whatsnext" %}}

### For app developers

* [Assign CPU Resources to Containers and Pods](/docs/tasks/configure-pod-container/assign-cpu-resource/)

* [Assign Pod-level CPU and memory resources](/docs/tasks/configure-pod-container/assign-pod-level-resources/)

* [Configure Quality of Service for Pods](/docs/tasks/configure-pod-container/quality-service-pod/)

* [Resize CPU and Memory Resources assigned to Containers](/docs/tasks/configure-pod-container/resize-container-resources/)

### For cluster administrators

* [Configure Default Memory Requests and Limits for a
```

### Source [4]

- Source: `kubernetes`
- Title: `Assign Pod-level CPU and memory resources`
- Document ID: `f06a8d814d2df4435365f04bbd44396d2295fb1453bb554fe7f8ccb057881bc1`
- Chunk ID: `8fe58d84316fdd2b795c6fcb459146ae2c5461c493cf461221c50b09d7d14124`

```text
: 50Mi
...
  -
    name: pod-resources-demo-ctr-2
    resources: {}
...
  resources:
    limits:
      cpu: "1"
      memory: 200Mi
    requests:
      cpu: "1"
      memory: 100Mi
...
```

Since pod-level requests and limits are specified, the request guarantees for both
containers in the pod will be equal 1 core or CPU and 100Mi of memory. Additionally,
both containers together won't be able to use more resources than specified in the
pod-level limits, ensuring they cannot exceed a combined total of 200 MiB of memory
and 1 core of CPU.

## Clean up

Delete your namespace:

```shell
kubectl delete namespace pod-resources-example
```

## {{% heading "whatsnext" %}}

### For application developers

* [Assign Memory Resources to Containers and Pods](/docs/tasks/configure-pod-container/assign-memory-resource/)

* [Assign CPU Resources to Containers and Pods](/docs/tasks/configure-pod-container/assign-cpu-resource/)

### For cluster administrators

* [Configure Default Memory Requests and Limits for a Namespace](/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/)

* [Configure Default CPU Requests and Limits for a Namespace](/docs/tasks/administer-cluster/manage-resources/cpu-default-namespace/)

* [Configure Minimum and Maximum Memory Constraints for a Namespace](/docs/tasks/administer-cluster/manage-resources/memory-constraint-namespace/)

* [Configure Minimum and Maximum CPU Constraints for a Names
```

### Source [5]

- Source: `kubernetes`
- Title: `Resource Management for Pods and Containers`
- Document ID: `9b34135c345f5524e5488329d9e5242afc20983d8e6a26dcbb292528d5fcdcee`
- Chunk ID: `7724247183d781f62b98595c61a5358718b90bd9d27e2b139f0ee27b07769583`

```text
{{< skew currentVersion >}}
only supports resource requests or limits for specific resource types: `cpu` and /
or `memory` and / or `hugepages`. With this feature, Kubernetes allows you to declare an overall resource
budget for the Pod, which is especially helpful when dealing with a large number of
containers where it can be difficult to accurately gauge individual resource needs.
Additionally, it enables containers within a Pod to share idle resources with each
other, improving resource utilization.

For a Pod, you can specify resource limits and requests for CPU and memory by including the following:
* `spec.resources.limits.cpu`
* `spec.resources.limits.memory`
* `spec.resources.limits.hugepages-<size>`
* `spec.resources.requests.cpu`
* `spec.resources.requests.memory`
* `spec.resources.requests.hugepages-<size>`

## Resource units in Kubernetes

### CPU resource units {#meaning-of-cpu}

Limits and requests for CPU resources are measured in *cpu* units.
In Kubernetes, 1 CPU unit is equivalent to **1 physical CPU core**,
or **1 virtual core**, depending on whether the node is a physical host
or a virtual machine running inside a physical machine.

Fractional requests are allowed. When you define a container with
`spec.containers[].resources.requests.cpu` set to `0.5`, you are requesting half
as much CPU time compared to if you asked for `1.0` CPU.
For CPU resource units, the [quantity](/docs/reference/kubernetes-api/common-definitions/quantity/) expression `0.1` is equivalent to the
expression `100m`,
```

### Source [6]

- Source: `kubernetes`
- Title: `Limit Ranges`
- Document ID: `c5ec6d0c7f58fee25c58d39a6fceb28dc4858abb10e745f0a10bf121d3febc24`
- Chunk ID: `815f57084a6c7246d7ecfde96dce6231ff7784122eb1aeb868bcc4a3ac6d0a7b`

```text
to request 100m of CPU with a max limit of 500m for CPU and request 200Mi
  for Memory with a max limit of 600Mi for Memory.
- Define default CPU limit and request to 150m and memory default request to 300Mi for
  Containers started with no cpu and memory requests in their specs.

In the case where the total limits of the namespace is less than the sum of the limits
of the Pods/Containers, there may be contention for resources. In this case, the
Containers or Pods will not be created.

Neither contention nor changes to a LimitRange will affect already created resources.

## {{% heading "whatsnext" %}}

For examples on using limits, see:

- [how to configure minimum and maximum CPU constraints per namespace](/docs/tasks/administer-cluster/manage-resources/cpu-constraint-namespace/).
- [how to configure minimum and maximum Memory constraints per namespace](/docs/tasks/administer-cluster/manage-resources/memory-constraint-namespace/).
- [how to configure default CPU Requests and Limits per namespace](/docs/tasks/administer-cluster/manage-resources/cpu-default-namespace/).
- [how to configure default Memory Requests and Limits per namespace](/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/).
- [how to configure minimum and maximum Storage consumption per namespace](/docs/tasks/administer-cluster/limit-storage-consumption/#limitrange-to-limit-requests-for-storage).
- a [detailed example on configuring quota per namespace](/docs/tasks/administer-cluster
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-017

**Category:** `insufficient`

**Expected behavior:** `insufficient_evidence`

## Query

Which Qdrant HNSW settings will guarantee p95 search latency below 20 milliseconds on my laptop?

## Model answer

The available sources do not provide specific Qdrant HNSW settings that will guarantee p95 search latency below 20 milliseconds on a laptop. While the sources discuss general strategies for low-latency search, such as tuning HNSW parameters, quantization, and managing read-write contention [1][2][3], they do not specify exact HNSW configuration values (e.g., `m`, `ef_construct`, `hnsw_ef`) or their guaranteed impact on p95 latency under laptop-level hardware constraints.

Moreover, the sources indicate that search latency is influenced by system resources (CPU, memory, I/O), background optimizer activity, and data volume, and that performance trade-offs exist between speed, precision, and memory usage [1][3][5]. However, no configuration is stated to *guarantee* p95 latency below 20 milliseconds on a laptop, and no empirical data or benchmarks are provided to support such a claim.

Therefore, based on the provided sources, it is not possible to determine which HNSW settings will guarantee p95 search latency below 20 milliseconds on a laptop. The evidence is insufficient to make a definitive technical recommendation. 

[1][2][3][5]

## API citations

```json
[
  {
    "citation_id": "1",
    "document_id": "1b528062e45b1ef934123e421128b610c2ba048d5e01eef1d70456ab65837430",
    "chunk_id": "47c3fab074ff92083f3239c60f1b086c77a0c289ed4c6a39a9daeec676e206a9"
  },
  {
    "citation_id": "2",
    "document_id": "ee9b4b5c61e964c516e42d5320a4f9cc1353f6529b0397ed103970d960708ae1",
    "chunk_id": "abcfd806a9c654d6bf380d81ea9153e312eabdcc14e3c53c93f0e2b51ccaf8c9"
  },
  {
    "citation_id": "3",
    "document_id": "8f2e53caefcf2aedddd6a7f0cbfa2c8a3f265f5c68bdc01486c3d2d6364d956a",
    "chunk_id": "81b6a8863982f30af24ec0144d5fedf99779da787cf9bd7bfce364f44417277c"
  },
  {
    "citation_id": "5",
    "document_id": "c18318b1567f1df614a2f4efe24563d757f033e17a7cb6958a7fb32c78d1b698",
    "chunk_id": "3d9577b2847cea3a203f33833c6b56fb6347b96eed2726b914a737ac88101301"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `qdrant`
- Title: `Low-Latency Search`
- Document ID: `1b528062e45b1ef934123e421128b610c2ba048d5e01eef1d70456ab65837430`
- Chunk ID: `47c3fab074ff92083f3239c60f1b086c77a0c289ed4c6a39a9daeec676e206a9`

```text
---
title: Low-Latency Search
short_description: "Tune Qdrant for low-latency vector search with quantization, HNSW indexing, sharding, and replica routing strategies."
description: "Reduce Qdrant search latency by tuning HNSW indexes, quantization, sharding, and replica routing for fast vector retrieval in distributed deployments."
weight: 35
aliases:
  - /documentation/guides/low-latency-search/
---

# Tips for Low-Latency Search with Qdrant

## Create Payload Indexes

If your search queries include filters, create [payload indexes](/documentation/manage-data/indexing/#payload-index) for the fields you filter on. Payload indexes are the primary way to improve filtered search performance in Qdrant. For best results, create payload indexes **before** uploading data.

Queries that filter on unindexed fields are not only slower; they can also unnecessarily consume cluster resources, negatively impacting the latency of other search queries. Consider [blocking queries that filter on unindexed fields](/documentation/manage-data/indexing/#block-queries-that-filter-on-unindexed-fields). This rejects queries that would degrade performance at the API boundary, surfacing misconfigured indexes as errors rather than latency spikes.

## Scale Horizontally with Replicas

Qdrant can be deployed in a [distributed configuration](/documentation/scaling/distributed_deployment/). In distributed mode, multiple instances of Qdrant, called peers, operate as a single entity, called a cluster. Data is stored in [collections](/documentation/manage-data/collections/
```

### Source [2]

- Source: `qdrant`
- Title: `Read-Write Contention`
- Document ID: `ee9b4b5c61e964c516e42d5320a4f9cc1353f6529b0397ed103970d960708ae1`
- Chunk ID: `abcfd806a9c654d6bf380d81ea9153e312eabdcc14e3c53c93f0e2b51ccaf8c9`

```text
---
title: Read-Write Contention
short_description: "Tune Qdrant under continuous ingestion to reduce optimizer contention and keep query latency low."
description: "A step-by-step guide to reducing read-write contention in Qdrant when the background optimizer competes with search queries under continuous write load."
weight: 15
---

# Troubleshoot Read-Write Contention

Qdrant is designed to index and optimize data as it arrives. While serving search queries, Qdrant's [background optimizer](/documentation/ops-optimization/optimizer/) continuously builds [HNSW indexes](/documentation/manage-data/indexing/#vector-index), merges segments, and applies quantization. Queries and the background optimizer compete for the same CPU time, memory bandwidth, and I/O (read-write contention). Qdrant's defaults don't prioritize either, but you can make several configuration changes to shift the balance.

This guide walks through a set of configuration changes to improve read latency under heavy write load. The steps are ordered by impact: start with step 1 and stop when your latency target is met. After each step, measure read latency and write throughput. If a change doesn't improve latency enough or causes unacceptable throughput loss, revert it and move to the next step.

## Step 1: Prevent Reads from Large Unindexed Segments

*Requires Qdrant v1.17.1 or later. `prevent_unoptimized` is an experimental feature.*

Under heavy write load, the optimizer can fall behind. When that happens, searches need to perform a full scan over large unindexed segments, which increases query latency
```

### Source [3]

- Source: `qdrant`
- Title: `Optimize Performance`
- Document ID: `8f2e53caefcf2aedddd6a7f0cbfa2c8a3f265f5c68bdc01486c3d2d6364d956a`
- Chunk ID: `81b6a8863982f30af24ec0144d5fedf99779da787cf9bd7bfce364f44417277c`

```text
---
title: Optimize Performance
short_description: "Tune Qdrant performance with quantization, on-disk storage, and HNSW parameters to balance speed, precision, and memory usage."
description: "Optimize Qdrant performance with quantization, on-disk vector storage, and HNSW tuning to balance search speed, precision, and memory consumption."
weight: 5
aliases:
  - /documentation/tutorials/optimize
  - /documentation/ops-optimization/optimize
  - /documentation/operations/optimize
---

# Optimizing Qdrant Performance: Three Scenarios

Different use cases require different balances between memory usage, search speed, and precision. Qdrant is designed to be flexible and customizable so you can tune it to your specific needs.

This guide will walk you three main optimization strategies:

- High Speed Search & Low Memory Usage
- High Precision & Low Memory Usage
- High Precision & High Speed Search

![qdrant resource tradeoffs](/docs/tradeoff.png)

<aside role="status">
This page covers the <code>memory</code> parameter introduced in Qdrant v1.19. If you're using an older version, see the <a href="/documentation/ops-configuration/memory-tiers/#legacy-settings">Legacy Settings</a> section for how to map the new parameter to the old ones.
</aside>

## 1. High-Speed Search with Low Memory Usage

To achieve high search speed with minimal memory usage, you can store vectors on disk while minimizing the number of disk reads. Vector quantization is a technique that compresses vectors, allowing more of them to be stored in memory, thus reducing the need to read from disk.

To
```

### Source [4]

- Source: `qdrant`
- Title: `Database Optimization`
- Document ID: `632ec0c09ae5de9e388f2d3c399d4e866f0181fce4228c8a84cb0e9e04a34ed8`
- Chunk ID: `4b062149b1bca9f81a88b8fbc75e80be7cb226e5b566a0327575f37fac6b82af`

```text
need to store many vectors and minimize costs by compromising some search speed. In this case, pay attention to the disk speed instead. More about it in the article about [Memory Consumption](/articles/memory-consumption/).

### I configured on-disk vector storage, but memory usage is still high. Why?

Firstly, memory usage metrics as reported by `top` or `htop` may be misleading. They are not showing the minimal amount of memory required to run the service.
If the RSS memory usage is 10 GB, it doesn't mean that it won't work on a machine with 8 GB of RAM.

Qdrant uses many techniques to reduce search latency, including caching disk data in RAM and preloading data from disk to RAM.
As a result, the Qdrant process might use more memory than the minimum required to run the service.

> Unused RAM is wasted RAM

If you want to limit the memory usage of the service, we recommend using [limits in Docker](https://docs.docker.com/config/containers/resource_constraints/#memory) or Kubernetes.

### My search latency increases under heavy write load. What should I do?

Qdrant's background optimizer runs continuously, building HNSW indexes, merging segments, and applying quantization, while also serving search queries. Under heavy write load, the optimizer and queries compete for the same CPU, memory, and I/O. Here are the main levers to reduce that contention, ordered by impact:

- **Prevent reads from large unindexed segments.** Enable [`prevent_unoptimized`](/documentation/ops-optimization/optimizer/#prevent-reads-from-large-un
```

### Source [5]

- Source: `qdrant`
- Title: `Vertical Scaling`
- Document ID: `c18318b1567f1df614a2f4efe24563d757f033e17a7cb6958a7fb32c78d1b698`
- Chunk ID: `3d9577b2847cea3a203f33833c6b56fb6347b96eed2726b914a737ac88101301`

```text
(/documentation/manage-data/quantization/) for the tradeoffs between quantization methods, and monitor actual memory usage before and after resizing (see [Monitor Collection Memory Usage](/documentation/ops-monitoring/memory-usage/)).

<aside role="status">To get a more detailed sizing estimate, try the <a href="https://sizing.qdrant.tech/">Qdrant Sizing Calculator</a>.</aside>

On top of the vector data itself, budget for the HNSW index, which typically adds 20% to 30% overhead, along with payload indexes and the write-ahead log. Reserve about 20% headroom for optimizer operations and operating system cache.

## When Vertical Scaling Is No Longer Enough

These signals mean it's time to scale horizontally instead of resizing further:

- Your data volume exceeds what a single node can hold, even with quantization.
- CPU on your largest available node size is already maxed out with unacceptable query latency.
- Disk I/O is saturated. Adding nodes gives you more independent disk throughput.
- You need fault tolerance, which requires replicating data across nodes.

When you hit these limits, see [Horizontal Scaling](/documentation/scaling/horizontal-scaling/) and [Distributed Deployment](/documentation/scaling/distributed_deployment/) for how to scale out.

## Best Practices

- Load test before scaling down RAM. Cache eviction after downsizing can cause a latency regression.
- Keep RAM usage below 80%. Memory pressure in Qdrant causes a performance cliff, not a gradual slowdown.
- Set the replication factor to two or higher before resizing in Qdrant Cloud. A rolling restart without replicas causes downtime.
-
```

### Source [6]

- Source: `qdrant`
- Title: `Measuring ANN Recall`
- Document ID: `ad3e443f6cfbcc35c2d33daf4e73d810964c9bf18ff399c09b657103e53bc793`
- Chunk ID: `41382fbed92dbd5b0eacddf89adab0b73dd5eb41752a8e0fa37e47f823705766`

```text
the graph, improving recall at the cost of higher query latency. To see the effect, raise `hnsw_ef` (for example, to 256) and run the evaluation again.

Recall should increase at the cost of higher query latency.

![ANN Recall advanced mode with HNSW parameters](/documentation/tutorials/retrieval-quality/search-quality-advanced.png)

If `hnsw_ef` alone does not get you to your recall target, the build-time parameters `m` and `ef_construct` set the ceiling on the recall approximate search can achieve. Changing them requires rebuilding the HNSW index. For the trade-offs and how to choose values, see [HNSW Indexing Fundamentals](/course/essentials/day-2/what-is-hnsw/) in the Qdrant Essentials course.

## Automate in CI with Python

The Web UI is the fastest way to check recall interactively. For continuous integration or scripted regression tests, the Qdrant client exposes the same exact-search mode via `search_params=models.SearchParams(exact=True)`. Compare the ANN and exact top-k sets yourself and compute recall@k.

This helper takes a list of query vectors and returns the average recall@k. Use a representative sample of query vectors from your workload (typically 20–50, embedded with the same model your collection uses) as your test set.

```python
from qdrant_client import QdrantClient, models

def avg_recall_at_k(
    client: QdrantClient,
    collection_name: str,
    test_vectors: list,
    k: int,
) -> float:
    recalls = []
    for vector in test_vectors:
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

---

# e2e-018

**Category:** `insufficient`

**Expected behavior:** `insufficient_evidence`

## Query

Which Docker base image is guaranteed to have no known vulnerabilities today?

## Model answer

The available sources do not specify which Docker base image is guaranteed to have no known vulnerabilities today. While the sources mention policies such as "Approved Base Images" [2] and vulnerability scanning tools like Grype [5], they do not identify a specific base image that is guaranteed to have no known vulnerabilities. Additionally, no base image is explicitly stated as being free of vulnerabilities in the provided content. Therefore, based on the information given, it cannot be determined which Docker base image is guaranteed to have no known vulnerabilities today.

## API citations

```json
[
  {
    "citation_id": "2",
    "document_id": "98c1cdb94136243af8667d50169469799fed4abd6c280ae2e997eab2bc55a34a",
    "chunk_id": "506eb7a3d611c7227bc75f47fe08f0909997c0fe7f34252474b7f338c0aab404"
  },
  {
    "citation_id": "5",
    "document_id": "213d08f711ee84a48ba63941c682b07f894f69480aa57606e1e0f7d3230b3e71",
    "chunk_id": "3d2df90874da4513379e1fea117576e72ca700ba968e8e6a86a226956d6e4377"
  }
]
```

## Exact retrieved evidence

### Source [1]

- Source: `docker`
- Title: `Policy Evaluation`
- Document ID: `01c5f11c13a58080f05cfd721715bc1c97c3752bed36fa0142bb309102c553af`
- Chunk ID: `5bf5232549dfde80a4145fc1cc002ae59e8d55b0d59e57d8952a8ec30566a5d3`

```text
[No base image data](#no-base-image-data).

### High-Profile Vulnerabilities

The **High-Profile Vulnerabilities** policy type checks whether your images
contain vulnerabilities from a [curated list of widely recognized, high-impact
CVEs](./local.md#default-high-profile-cves), including Log4Shell, Spring4Shell,
and XZ backdoor. The list is updated as new high-profile vulnerabilities are
disclosed.

You can configure which CVEs are considered high-profile and enable tracking
of CISA's Known Exploited Vulnerabilities catalog.

### Supply Chain Attestations

The **Supply Chain Attestations** policy type checks whether your images have
[SBOM](/manuals/build/metadata/attestations/sbom.md) and
[provenance](/manuals/build/metadata/attestations/slsa-provenance.md)
attestations. Images are non-compliant if they lack either attestation type.

To ensure compliance, build with attestations:

```console
$ docker buildx build --provenance=true --sbom=true -t <IMAGE> --push .
```

### Default Non-Root User

The **Default Non-Root User** policy type detects images configured to run as
the `root` user. Use the
[`USER`](/reference/dockerfile.md#user) Dockerfile instruction to set a
non-root default user for the runtime stage.

### Approved Base Images

The **Approved Base Images** policy type ensures the base images you use match
a configurable allowlist of g
```

### Source [2]

- Source: `docker`
- Title: `Docker Scout release notes`
- Document ID: `98c1cdb94136243af8667d50169469799fed4abd6c280ae2e997eab2bc55a34a`
- Chunk ID: `506eb7a3d611c7227bc75f47fe08f0909997c0fe7f34252474b7f338c0aab404`

```text
03-14

The **All critical vulnerabilities** policy has been removed.
The **No fixable critical or high vulnerabilities** policy provides similar functionality,
and will be updated in the future to allow for more extensive customization,
making the now-removed **All critical vulnerabilities** policy redundant.

### 2024-01-26

**Azure Container Registry** integration graduated from
[Early Access](../../release-lifecycle.md#early-access-ea) to
[General Availability](../../release-lifecycle.md#general-availability-ga).

For more information and setup instructions, see
[Integrate Azure Container Registry](../integrations/registry/acr.md).

### 2024-01-23

New **Approved Base Images** policy, which lets you restrict which base
images you allow in your builds. You define the allowed base images using a
pattern. Base images whose image reference don't match the specified patterns
cause the policy to fail.

### 2024-01-12

New **Default non-root user** policy, which flags images that would run as the
`root` superuser with full system administration privileges by default.
Specifying a non-root default user for your images can help strengthen your
runtime security.

### 2024-01-11

[Beta](../../release-lifecycle.md#beta) launch of a new GitHub app for integrating
Docker Scout with your source code management, and a remediation feature for
helping you improve policy compliance.

Remediation is a new capability for Docker Scout to provide contextual,
recommended actions based on policy evaluation results on how you can improve
compliance.

The GitH
```

### Source [3]

- Source: `docker`
- Title: `Docker Scout image analysis`
- Document ID: `e171d40c79870af72adbbb62a41b84aba4ef38c3663816ea3d9d8ad2868798f9`
- Chunk ID: `c7330830b21d1827d6bc645e8b4ec5aaf939b93891a984c151aaefe495a282bc`

```text
```console
$ docker scout quickview traefik:latest
    ✓ SBOM of image already cached, 311 packages indexed

  Your image  traefik:latest  │    0C     2H     8M     1L
  Base image  alpine:3        │    0C     0H     0M     0L
```

If your the base image is out of date, the `quickview` command also shows how
updating your base image would change the vulnerability exposure of your image.

```console
$ docker scout quickview postgres:13.1
    ✓ Pulled
    ✓ Image stored for indexing
    ✓ Indexed 187 packages

  Your image  postgres:13.1                 │   17C    32H    35M    33L
  Base image  debian:buster-slim            │    9C    14H     9M    23L
  Refreshed base image  debian:buster-slim  │    0C     1H     6M    29L
                                            │    -9    -13     -3     +6
  Updated base image  debian:stable-slim    │    0C     0H     0M    17L
                                            │    -9    -14     -9     -6
```

#### CVEs

The `docker scout cves` command gives you a complete view of all the
vulnerabilities in the image. This command supports several flags that lets you
specify more precisely which vulnerabilities you're interested in, for example,
by severity or package type:

```console
$ docker scout cves --format only-packages --only-vuln-packages \
  --only-severity critical postgres:13.1
    ✓ SBOM of image already cached, 187 packages indexed
    ✗ Detected 10 vulnerable packages with a total of 17 vulnerabilities

     Name            Version         Type        Vulnerabilities
─────────────────────────────────
```

### Source [4]

- Source: `docker`
- Title: `Docker security non-events`
- Document ID: `78b50f8d64dbe279ccc5a1c4de849ab9ba3b563e956aeac3a2e0754459b5d942`
- Chunk ID: `5313c27f98311772f66a1d29d292536042facff662b84c3ee69f404f85301e49`

```text
---
description: Review of security vulnerabilities Docker mitigated
keywords: Docker, Docker documentation,  security, security non-events
title: Docker security non-events
---

This page lists security vulnerabilities which Docker mitigated, such that
processes run in Docker containers were never vulnerable to the bug—even before
it was fixed. This assumes containers are run without adding extra capabilities
or not run as `--privileged`.

The list below is not even remotely complete. Rather, it is a sample of the few
bugs we've actually noticed to have attracted security review and publicly
disclosed vulnerabilities. In all likelihood, the bugs that haven't been
reported far outnumber those that have. Luckily, since Docker's approach to
secure by default through apparmor, seccomp, and dropping capabilities, it
likely mitigates unknown bugs just as well as it does known ones.

Bugs mitigated:

* [CVE-2013-1956](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2013-1956),
[1957](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2013-1957),
[1958](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2013-1958),
[1959](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2013-1959),
[1979](https://cve.mitre.org/cgi-bin/cvename
```

### Source [5]

- Source: `docker`
- Title: `Scan Docker Hardened Images`
- Document ID: `213d08f711ee84a48ba63941c682b07f894f69480aa57606e1e0f7d3230b3e71`
- Chunk ID: `3d2df90874da4513379e1fea117576e72ca700ba968e8e6a86a226956d6e4377`

```text
:${{ env.SHA }}
          only-severities: critical,high
          exit-code: true

      - name: Push image
        if: success()
        run: |
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ env.SHA }}
```

The `exit-code: true` parameter ensures that the workflow fails if any critical or
high-severity vulnerabilities are detected, preventing the deployment of
insecure images.

> [!NOTE]
>
> The `--provenance=mode=max` and `--sbom=true` flags are required so that
> Docker Scout can trace the DHI base image lineage and correctly apply its
> VEX statements. Enabling the containerd image store via
> `docker/setup-docker-action` allows BuildKit to store attestations locally
> without pushing to a registry first. Without the containerd image store,
> Docker Engine rejects the build with: `Attestation is not supported for the docker driver.
> Switch to a different driver, or turn on the containerd image store, and try again.`
> The `Push image` step runs only if the scan passes, using `if: success()`
> to ensure images are only pushed to the registry when they are free of
> critical or high-severity vulnerabilities.

For more details on using Docker Scout in CI, see [Integrating Docker
Scout with other systems](/manuals/scout/integrations/_index.md).

## Grype

[Grype](https://github.com/anchore/grype) is an open-source scanner that checks
container images against vulnerability databases like the NVD and distro
advisories.
```

### Source [6]

- Source: `docker`
- Title: `Common Vulnerabilities and Exposures (CVEs)`
- Document ID: `a1e8966cb95220ad3cf5555593f06148debb0a133cf08de326ab3b6d3368f286`
- Chunk ID: `38b973961b26827b4ea85b8befccc1040fa9891db3e2c9d31353456aa298b4e6`

```text
---
aliases:
  - /dhi/core-concepts/cves/
title: Common Vulnerabilities and Exposures (CVEs)
linktitle: CVEs
description: Understand what CVEs are, how Docker Hardened Images reduce exposure, and how to scan images for vulnerabilities using popular tools.
keywords: docker cve scan, grype vulnerability scanner, trivy image scan, vex attestation, secure container images
---

## What are CVEs?

CVEs are publicly disclosed cybersecurity flaws in software or hardware. Each
CVE is assigned a unique identifier (e.g., CVE-2024-12345) and includes a
standardized description, allowing organizations to track and address
vulnerabilities consistently.

In the context of Docker, CVEs often pertain to issues within base images, or
application dependencies. These vulnerabilities can range from minor bugs to
critical security risks, such as remote code execution or privilege escalation.

## Why are CVEs important?

Regularly scanning and updating Docker images to mitigate CVEs is crucial for
maintaining a secure and compliant environment. Ignoring CVEs can lead to severe
security breaches, including:

- Unauthorized access: Exploits can grant attackers unauthorized access to
  systems.
- Data breaches: Sensitive information can be exposed or stolen.
- Service disruptions: Vulnerabilities can be leveraged to disrupt services or
  cause downtime.
- Compliance violations: Failure to address known vulnerabilities can lead to
  non-compliance with industry regulations and standards.

## How Docker Hardened Images help mitigate CVEs

Docker Hardened Images (DHIs) are crafted to minimize the risk of CVEs from the
outset. By adopting a security-first approach, DHIs offer several advantages in
CVE mitigation:

- Reduced attack
```

## Human scores

- Correctness: `TODO`
- Faithfulness: `TODO`
- Citation correctness: `TODO`
- Citation completeness: `TODO`
- Evidence sufficiency: `TODO`
- Ambiguity handling: `TODO`
- Multi-source synthesis: `TODO`
- Abstention: `TODO`

**Verdict:** `TODO`

**Severity / blocker:** `TODO`

**Reviewer notes:**

TODO

