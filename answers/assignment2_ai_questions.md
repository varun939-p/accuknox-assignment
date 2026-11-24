# Assignment 2

## 1. Self-rating

| Area | Rating |
|---|---|
| LLM | A |
| AI | A |
| Deep Learning | B |
| ML | B |

A = can code independently, B = can code under supervision, C = little or no understanding.

I build LLM features on my own, from prompt and schema design to output validation and RAG. I would want a reviewer when training or fine-tuning my own models, or tuning classic ML models on real data.

## 2. Architecture of an LLM-based chatbot

```
Client --> API --> Input guardrails --> Retrieval + prompt builder
                                                  |
Response <-- Output check <-- LLM <---------------+
```

### API

The API authenticates the user and attaches the tenant id and roles to the request. The prompt can never change these values. It also keeps chat history on the server and rate-limits each user, since model calls are expensive.

### Input guardrails

PII and secrets are redacted before text reaches logs or a third-party model. A classifier plus simple rules flag likely prompt injection. Filters only lower the risk, so the real control is that the model never gets more access than the user.

### Retrieval and prompt builder

The question is embedded and matched against a vector store, alongside keyword search for exact terms like CVE IDs. Tenant and permission filters run inside the search, so the model never sees a document the user cannot open. Retrieved text is treated as untrusted, because injected instructions can hide in indexed documents. The builder then fits the system prompt, recent history and top chunks into a fixed token budget.

### LLM

All model calls go through one client with timeouts, a max token limit and retries on 429 or 5xx errors. A fallback model covers provider outages. Responses are streamed so the user sees output quickly.

### Output check

The answer is scanned for secrets and PII before it is returned. It is also checked against the retrieved sources so unsupported claims can be dropped. When the caller expects JSON, the output is validated against a schema.

### Logging and evals

Each request logs a trace id, latency, token counts and retrieved chunk ids. A small eval set of known questions and injection attempts runs after every prompt or model change.

## 3. Vector databases

### How they work

An embedding model turns text into a fixed-length vector, so texts with similar meaning land close together. A query is embedded with the same model, and search returns the nearest stored vectors. Cosine similarity compares direction only and is the usual choice for text. Dot product is cheaper and gives the same ranking when vectors are normalized.

Exact search compares the query with every stored vector, so query time grows with the data. ANN indexes give up a little recall to avoid that full scan. HNSW builds a layered graph of neighbours and walks it from coarse to fine layers. Each query only touches a small part of the data.

Real queries also filter on metadata such as tenant or document type. Filtering after the ANN search can leave a small tenant with no results at all. Filtering inside the search fixes this, but engines differ a lot in how well they handle it.

### Problem

A security assistant searches runbooks, advisories and CVE notes across many isolated customer workspaces. Every query must stay inside one tenant. Users ask questions in plain language, but they also search for exact IDs like `CVE-2024-3094`.

### Options

| Database | Good at | Concern here |
|---|---|---|
| Qdrant | Filtered HNSW, built-in sparse + dense hybrid search | One more service to run |
| pgvector | Lives inside Postgres, SQL filters and row-level security | Large indexes and selective filters need tuning |
| Pinecone | Fully managed, namespaces per tenant | Hard to keep data inside a customer VPC |

### Why Qdrant

Exact CVE IDs are the main reason. Qdrant stores sparse and dense vectors together and fuses them in one query, so `CVE-2024-3094` matches exactly while paraphrased questions still work. Payload filters on `tenant_id` and access groups run inside the HNSW search, so small tenants still get full results. It is open source and self-hostable, so it can run inside the customer's VPC.

If the dataset were small and Postgres was already in the stack, I would just use pgvector.
