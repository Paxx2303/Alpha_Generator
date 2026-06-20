# Architecture Alternatives for the Knowledge Layer

This document records architectural options considered for the knowledge core.
Current choice: **ChromaDB + SQLite** (see rationale below).

---

## Option A: Columnar Store (DuckDB / Parquet) — CONSIDERED

**Concept:** Store all chunks as Parquet files, query with DuckDB SQL.

**Pros:**
- Extremely fast analytical queries (filter by category, source_type, date range)
- Zero server process — embedded like SQLite
- Native pandas/arrow interop

**Cons:**
- No native vector search — would need a separate vector index (FAISS)
- Two systems to maintain (DuckDB for metadata + FAISS for embeddings)
- Overkill for < 100k chunks

**When to switch:** If chunk count exceeds 500k and we need complex analytical queries on the corpus.

---

## Option B: Graph Database (Neo4j / NetworkX) — PARTIALLY ADOPTED

**Concept:** Nodes = fields, operators, patterns; edges = co-occurrence in gold alphas.

**Pros:**
- Discover hidden relationships: "which fields co-appear in gold alphas?"
- Traversal: "find all operators connected to est_ptp with ≥ 3 gold alpha appearances"

**Cons:**
- High operational complexity (Neo4j requires server, memory)
- NetworkX (in-memory) doesn't scale past ~10k nodes
- Needs sufficient gold alpha density to show useful patterns (> 200 alphas)

**Adopted:** `core/knowledge/graph.py` skeleton (NetworkX, in-memory, not yet used).
**When to activate:** Once we accumulate 200+ gold alphas.

---

## Option C: Event Store (Append-Only Log) — NOT ADOPTED

**Concept:** Every research event (hypothesis generated, alpha tested, theory saved) is an immutable event. State is derived by replaying events.

**Pros:**
- Perfect audit trail
- Can replay to any historical state
- Great for debugging DeerFlow research decisions

**Cons:**
- Significant implementation overhead
- Overkill for current scale
- Our backup/restore system serves the reliability need more simply

**When to consider:** If we want to analyse DeerFlow's decision-making process in depth (post-200 gold alphas).

---

## Option D: Vector DB as Primary Store (Pinecone / Weaviate) — NOT ADOPTED

**Concept:** Use a cloud vector database instead of local ChromaDB.

**Pros:**
- Managed service, no local storage
- Built-in scalability

**Cons:**
- Network latency on every search (DeerFlow research loop has many searches)
- Cost ($$$) for production use
- Data leaves GCP environment

**When to consider:** If moving beyond single-region GCP and need multi-region search.

---

## Current Choice: ChromaDB (local) + SQLite

| Need | Solution |
|------|----------|
| Semantic search on chunks | ChromaDB (`all-MiniLM-L6-v2`) |
| Alpha/simulation history | SQLite (`alpha_store.db`) |
| Source effectiveness tracking | SQLite (`knowledge_sources` table) |
| Theory log | JSON file (`data/theory_log.json`) |
| Graph relationships | NetworkX skeleton (inactive until needed) |

**Why this wins now:**
- Zero external dependencies
- Works on GCE VM without internet (after setup)
- ChromaDB is local — no latency
- SQLite ACID guarantees for critical simulation data
- Easy backup (just copy files)
