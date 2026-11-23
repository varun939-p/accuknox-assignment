# Assignment 2

## 1. Self-rating (LLM, Deep Learning, AI, ML)

Scale: A = can code independently, B = can code under supervision, C = little or no understanding.

| Area | Rating | Scope |
|---|---|---|
| LLM | A | I build LLM features end to end on my own: prompt and JSON-schema design, output validation, retries and fallbacks, token budgeting, streaming, and RAG pipelines. |
| AI | A | I ship AI-backed products independently, including the backend around the model: tool and agent workflows, hybrid deterministic + model scoring, evals, and failure handling. |
| Deep Learning | B | I understand transformers, embeddings and how training works, and I use pretrained models comfortably; training or fine-tuning my own models is where I want review. |
| ML | B | I can build and evaluate standard scikit-learn pipelines; feature choices, leakage checks and model selection on real data are where I want a reviewer. |

## 2. Key architectural components of an LLM-based chatbot

```
  Client (web chat / Slack / API)
     |
     v
  +-------------------------------+
  | API gateway + auth            |   user, tenant, roles, rate limits, session
  +-------------------------------+
     |
     v
  +-------------------------------+
  | Input guardrails              |   PII/DLP redaction, prompt-injection
  |                               |   screening, size caps
  +-------------------------------+
     |
     v
  +-------------------------------+      +------------------------------+
  | Orchestrator / router         |----->| Hybrid retriever             |
  | intent, model tier, tool plan |      | BM25 + dense, tenant/ACL     |
  +-------------------------------+      | filters in the query, rerank |
     |                                   +------------------------------+
     v                                       |
  +-------------------------------+          | chunks + source ids
  | Context builder               |<---------+
  | token budget, history summary |
  +-------------------------------+
     |
     v
  +-------------------------------+      +------------------------------+
  | LLM gateway                   |<---->| Tool sandbox (agentic only)  |
  | streaming, timeouts, retries, |      | allow-listed tools, user-    |
  | fallback model, token caps    |      | scoped creds, egress limits  |
  +-------------------------------+      +------------------------------+
     |
     v
  +-------------------------------+
  | Output guardrails             |   secret/DLP scan, grounding check,
  |                               |   schema validation
  +-------------------------------+
     |
     v
  Response (streamed to client)

  ......................................................................
  : Observability + evals (side channel, every stage): trace id,       :
  : latency, token counts, retrieval ids, guardrail verdicts -> logs   :
  : with PII redacted, dashboards, offline eval sets                   :
  ......................................................................
```

### API and session layer

Authentication happens once at the edge, and the tenant id and roles travel downstream as trusted request context, never as something the prompt can set. Conversation state lives server-side with a TTL. Rate limits apply per user and per tenant, because one chat request can cost as much as thousands of normal API calls.

### Input and output guardrails

On the way in, PII and secrets are redacted before text reaches logs or a third-party model, and a classifier plus simple heuristics screen for direct prompt injection. Filters lower the risk but never remove it, so the real control is least privilege: the model should not be able to do anything the user could not do. On the way out, the answer is scanned for secrets and PII, checked against the retrieved sources, and schema-validated when the caller expects structured output. Streaming makes this harder; I scan per sentence or per chunk and accept a small latency cost instead of streaming unchecked tokens.

### Retrieval and context budgeting

Retrieval is hybrid because embeddings blur exact identifiers: "CVE-2024-3094" and an error code need lexical (BM25) matching, while paraphrased questions need dense vectors. Tenant and ACL filters go inside the retrieval query, so an unauthorized chunk never reaches the prompt. Retrieved text is untrusted input, since indirect prompt injection hides in indexed documents. The context builder gives each part a fixed token budget (system prompt, summarized history, top reranked chunks) and keeps source ids so the answer can cite them.

### Model gateway

All provider calls go through one gateway that owns API keys, per-call timeouts, `max_tokens`, retries with jitter on 429 and 5xx only, a fallback model, and cost accounting per tenant. Streaming starts at the gateway, so time to first token is measured there.

### Tool execution boundary

In an agentic setup the model only proposes tool calls. The executor validates arguments against a schema, checks the end user's permissions (not the bot's), runs the tool with short-lived user-scoped credentials and an egress allow-list, and asks for confirmation before destructive actions. Tool output goes back to the model as untrusted data, the same as retrieved chunks.

### Observability and evals

Every stage emits a trace span: request id, latency, token counts, retrieved chunk ids, and guardrail verdicts, redacted before logging. An offline eval set (golden questions, known injection payloads, cross-tenant probes) runs on every prompt, model, or retriever change, because quality regressions in LLM systems are silent.

| Component | Primary failure mode | Mitigation |
|---|---|---|
| API / session | Cross-tenant data bleed through sessions or caches | Tenant id taken only from the auth token; cache keys include tenant and ACL hash |
| Input guardrails | Direct prompt injection ("ignore previous instructions") | Injection screening, no secrets in the system prompt, least-privilege tools |
| Retriever | Indirect prompt injection planted in an indexed document | Chunks passed as delimited data, provenance kept, tool calls gated by user confirmation |
| Retriever | Chunk from another tenant or a restricted doc retrieved | ACL filter applied inside the vector query, not after it |
| Context builder | Stale or conflicting context gives a confident wrong answer | Freshness metadata, deletes propagated from the source, citations required |
| LLM gateway | Latency or token spikes, provider outage | Timeouts, `max_tokens`, retry only on 429/5xx, fallback model, per-tenant budgets |
| Tool sandbox | Model-driven destructive call or data exfiltration | Allow-listed tools, schema-checked args, user-scoped creds, egress allow-list |
| Output guardrails | PII or secret leakage, ungrounded claims | DLP and entropy-based secret scan, grounding check against cited chunks, refuse when unsupported |

## 3. Vector databases and which one I would choose

### How they work

An embedding model maps a piece of text to a fixed-length vector (for example 1024 floats) so that texts with similar meaning land close together. The query is embedded with the same model, and search becomes a nearest-neighbour problem. The similarity metric should match how the model was trained. Cosine similarity compares angle only and is the usual choice for text. Dot product also counts magnitude and is cheaper; on normalized vectors it ranks results exactly like cosine. L2 (Euclidean) distance on normalized vectors gives the same ranking as cosine too, but it matters for models trained on unnormalized vectors.

Exact kNN compares the query with every stored vector. At 8M vectors x 1024 dims x 4 bytes that is about 33 GB scanned per query, which is roughly a second of memory bandwidth on one CPU node, and it grows linearly with the corpus. Approximate nearest neighbour (ANN) indexes give up a little recall to avoid the full scan:

- **HNSW** builds a layered proximity graph and walks it greedily from a sparse top layer down to the dense bottom layer. With sensible `M` and `ef_search` values it reaches 95-99% recall at single-digit to tens of milliseconds, but it keeps the graph and vectors in RAM, and deletes leave tombstones that need compaction.
- **IVF-PQ** clusters vectors with k-means and searches only the nearest few clusters (`nprobe`), while product quantization compresses each vector from kilobytes to tens of bytes. Memory drops by an order of magnitude or more; recall drops too, so results are usually re-scored on full vectors, and the clustering has to be retrained when the data distribution shifts.

Metadata filtering is where real systems break. Post-filtering runs ANN first and drops results the user may not see; when a tenant owns 0.1% of the data, the top 100 hits can contain zero allowed rows, and the user gets an empty or poor answer. Pre-filtering restricts the search to allowed rows, but on an HNSW graph that can disconnect the walk, because the allowed nodes are only reachable through filtered-out ones, and recall collapses. A production engine needs filter-aware graph traversal, a query planner that falls back to exact search when a filter is very selective, or physical partitioning per tenant.

### Hypothetical problem

A multi-tenant RAG assistant over security runbooks, CVE advisories and cloud policies: about 8M chunks across hundreds of isolated customer workspaces. Every query must be restricted to one tenant and the user's RBAC groups, advisories and policies change daily (incremental upserts and deletes, including withdrawn advisories), and users search both semantically ("how do we contain a compromised node") and by exact identifier (`CVE-2024-3094`, a Kubernetes policy name like `disallow-privileged-containers`).

| | Qdrant | pgvector (PostgreSQL) | Pinecone | FAISS |
|---|---|---|---|---|
| Filtered ANN performance | Filter-aware HNSW with payload indexes; planner switches to exact search for very selective filters | Good with HNSW plus iterative index scans (0.8+); highly selective filters still need tuning | Filtering built into the index; namespaces isolate tenants | No metadata model; only ID-selector filtering, the rest is yours to build |
| Hybrid (sparse + dense) | Native sparse vectors, fused with dense results (RRF) in one query | Combine with Postgres full-text search in SQL and fuse ranks yourself | Supported through sparse-dense vectors | Dense only |
| Deployment / data residency | Self-host (Docker/Kubernetes, Apache-2.0) inside a customer VPC, or managed cloud | Wherever your Postgres runs; row-level security available | Managed service only, no self-hosted build; "data never leaves our VPC" is hard to meet | In-process library, runs anywhere |
| Operational overhead | One more stateful service to run, back up and upgrade | Lowest if Postgres is already operated; large HNSW builds need memory tuning | Lowest to run; cost and vendor lock-in instead | High: persistence, sharding, updates and replication are all custom |
| Best fit | Large, filtered, multi-tenant search with strict residency | Up to a few million vectors next to relational data | Teams that want zero ops and can use a SaaS | Offline batch similarity, research, static corpora, GPU search |

### Recommendation: Qdrant

Qdrant fits the hard parts of this problem directly. It is written in Rust, so memory use is predictable with no GC pauses, and it can keep int8-quantized vectors in RAM (about 8 GB for this corpus instead of 33 GB) while the full vectors stay on disk for re-scoring. Its HNSW graph is built with extra links for indexed payload fields, so a search filtered to `tenant_id` and `acl_groups` stays connected and fast instead of collapsing the way pre-filtered HNSW does. Sparse vectors live next to the dense ones and are fused in a single query, which is what makes `CVE-2024-3094` or an exact policy name match reliably while paraphrased questions still work. Tenants share one collection with a tenant payload index, so per-tenant graph building and data locality come without running hundreds of collections. Upserts by a deterministic point id make re-ingestion idempotent, and delete-by-filter removes a withdrawn advisory in one call. Finally, it self-hosts inside the customer VPC, which settles data residency. The service layer adds the tenant and ACL filters from the auth token on every query; the client never supplies them.

I would not pick Qdrant below roughly 500k to 1M vectors when PostgreSQL is already in the stack: pgvector with HNSW and row-level security handles that size, keeps vectors in the same transaction as the source rows, and removes a whole distributed service to operate. Qdrant also does not replace the source of truth, so it adds a sync path where updates and deletes can go missing, and that path needs its own tests and monitoring.
