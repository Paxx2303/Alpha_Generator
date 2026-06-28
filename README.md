# Alpha Generator v3 — Tài Liệu Kỹ Thuật Đầy Đủ

**Phiên bản:** 3.0 | **Cập nhật:** 2026-06-22  
**Mục tiêu:** AI researcher tự động nghiên cứu alpha signals 24/7 trên WorldQuant Brain (WQB).

---

## Mục Lục

1. [Kiến Trúc Tổng Thể](#1-kiến-trúc-tổng-thể)
2. [Cấu Trúc Thư Mục](#2-cấu-trúc-thư-mục)
3. [Workflow 1 — Research Cycle (Luồng Chính)](#3-workflow-1--research-cycle-luồng-chính)
4. [Workflow 2 — WQB Simulation (Chi Tiết API)](#4-workflow-2--wqb-simulation-chi-tiết-api)
5. [Workflow 3 — MCP Tools (9 Công Cụ)](#5-workflow-3--mcp-tools-9-công-cụ)
6. [Workflow 4 — Knowledge Base (ChromaDB)](#6-workflow-4--knowledge-base-chromadb)
7. [Workflow 5 — Storage Layer (SQLite)](#7-workflow-5--storage-layer-sqlite)
8. [Workflow 6 — Observation Dashboard](#8-workflow-6--observation-dashboard)
9. [Workflow 7 — Deployment (CI/CD)](#9-workflow-7--deployment-cicd)
10. [IQC Pass Criteria](#10-iqc-pass-criteria)
11. [Trạng Thái Alpha Pool](#11-trạng-thái-alpha-pool)

---

## 1. Kiến Trúc Tổng Thể

```
GCE VM (alpha-vm, e2-standard-4, asia-east1-c)
│
├── DeerFlow (Docker Compose, port 8000)
│   ├── gateway    — FastAPI, nhận request từ runner.py
│   ├── backend    — LLM orchestration (OpenRouter / Owl Alpha)
│   ├── frontend   — Next.js UI (port 2026, debug only)
│   └── [provisioner disabled]
│
├── MCP Server (port 8765, SSE)
│   └── core/mcp/server.py — 9 tools cho DeerFlow
│
├── Streamlit Dashboard (Docker, port 8080)
│   └── observation/app.py — 5 pages, đọc data từ volume mount
│
├── Cron (0 */6 * * *)
│   └── operation/runner.py — kick-off DeerFlow mỗi 6 tiếng
│
└── Local Storage (không cần cloud)
    ├── data/alpha_store.db  — SQLite, 12 tables/views
    ├── data/chroma/         — ChromaDB (semantic embeddings)
    ├── data/theory_log.json — Theories từ save_theory()
    ├── data/research_status.json — Trạng thái cycle hiện tại
    └── mcp_skill.md         — Operator rules, known patterns

GCS (alpha-backups-*)
└── Backup: alpha_store.db, theory_log.json, mcp_skill.md (30 ngày)
```

**Luồng điều khiển tổng quát:**
```
cron (6h) → runner.py → POST /api/chat/stream → DeerFlow
    → MCP tools (9 tools qua SSE) → WQB REST API
    → Store kết quả → SQLite + ChromaDB + JSON files
    → Streamlit đọc real-time qua volume mount
```

---

## 2. Cấu Trúc Thư Mục

```
Alpha_Generator/
│
├── core/                        — Não của hệ thống
│   ├── mcp/
│   │   ├── server.py            — FastMCP, SSE port 8765, đăng ký 9 tools
│   │   └── tools/
│   │       ├── research.py      — get_skill_knowledge, search_knowledge_base, search_data_fields
│   │       ├── alpha.py         — submit_alpha, get_gold_alphas, diagnose_alpha, mutate_formula
│   │       └── memory.py        — save_theory, update_skill
│   └── knowledge/
│       ├── vector_store.py      — ChromaDB wrapper (2 collections: alpha_knowledge, wqb_fields)
│       ├── source_registry.py   — Source effectiveness tracking
│       ├── entities.py          — Pydantic models: OperatorFact, FieldFact, AlphaPattern
│       └── graph.py             — Skeleton, dùng khi ≥200 alphas
│
├── operation/                   — Lớp điều phối
│   ├── runner.py                — Entry point cron; POST tới DeerFlow, stream SSE response
│   ├── deerflow/
│   │   ├── config.yaml          — LLM: OpenRouter + Owl Alpha
│   │   ├── extensions_config.json — MCP server SSE: http://host.docker.internal:8765/sse
│   │   └── skills/alpha-research/SKILL.md — Hướng dẫn workflow cho DeerFlow AI
│   ├── crawlers/
│   │   ├── base.py              — BaseCrawler: rate-limit, paging, resume từ crawl_state
│   │   ├── wqb_datasets.py      — GET /data-sets → upsert_datasets()
│   │   ├── wqb_datafields.py    — GET /data-fields → upsert_datafields()
│   │   └── wqb_operators.py     — GET /operators → upsert_operators()
│   └── analytics/               — IC analysis (hypothesize, explore, describe)
│
├── observation/                 — Dashboard
│   ├── app.py                   — Streamlit entry, auto-refresh 5s
│   ├── pages/
│   │   ├── 1_Observatory.py     — research_status.json → agent state, cycle count
│   │   ├── 2_Alpha_Lab.py       — gold_alphas table, filter by sharpe/fitness/family
│   │   ├── 3_Theory_Notebook.py — theory_log.json → humanized research theories
│   │   ├── 4_Knowledge_Map.py   — ChromaDB stats, semantic search UI
│   │   └── 5_Source_Intel.py    — source_domain_stats / source_type_stats views
│   └── utils/db.py              — SQLite helpers (read-only), path = /app/data/ (volume)
│
├── storage/
│   └── store.py                 — Store class: SQLite DAO, 12 tables, PRAGMA WAL
│
├── backup/
│   ├── backup_manager.py        — Local (7 ngày) + GCS (30 ngày)
│   └── restore.py               — restore --latest --source gcs
│
├── deploy/
│   ├── Dockerfile.observation   — python:3.11-slim, COPY . ., streamlit run
│   ├── docker-compose.override.yml — thêm streamlit service + volume mount vào DeerFlow compose
│   ├── vm-setup.sh              — idempotent bootstrap: Docker, Ollama, clone, pip, cron, MCP server
│   └── cloud-run/service-glm.yaml — Cloud Run GPU cho GLM-5.2 (tương lai)
│
├── .github/workflows/deploy.yml — 1 job: deploy-vm (SSH IAP → vm-setup.sh)
│
├── wqb_automation.py            — WQBAutomation class: REST client, login, submit, poll, self-corr
├── config.py                    — Tất cả constants (paths, EMBED_MODEL, crawl settings, RAG weights)
├── mcp_skill.md                 — Operator reference, proven patterns (được AI cập nhật)
└── data/
    ├── alpha_store.db           — SQLite database (tất cả dữ liệu)
    ├── chroma/                  — ChromaDB persistent storage
    ├── theory_log.json          — [{id, title, body, confidence, tags, created_at}]
    └── research_status.json     — {agent_state, current_cycle, current_task, last_updated}
```

---

## 3. Workflow 1 — Research Cycle (Luồng Chính)

Đây là vòng lặp cốt lõi. Xảy ra mỗi 6 tiếng tự động.

### Bước 1: Cron kích hoạt runner.py

```
cron: 0 */6 * * *
    → cd /app/alpha-generator
    → python3 operation/runner.py
```

**`operation/runner.py::main()`**
1. Load `.env` từ `operation/deerflow/.env` (nếu tồn tại) vào `os.environ`.
2. Gọi `run_cycle()`.

**`run_cycle()`**:
1. `_read_cycle()` — đọc `current_cycle` từ `data/research_status.json`.
2. `cycle = current_cycle + 1`.
3. `GET {DEERFLOW_URL}/api/models` — kiểm tra DeerFlow đang chạy. Nếu fail → ghi `status=error`, exit.
4. `_write_status("running", "Initialising research cycle", cycle)` → ghi `research_status.json`.
5. Tạo `thread_id = "alpha-cycle-{cycle}-{timestamp}"`.
6. `POST {DEERFLOW_URL}/api/chat/stream` với body:
   ```json
   {
     "messages": [{"role": "user", "content": RESEARCH_PROMPT}],
     "thread_id": "alpha-cycle-42-1750000000"
   }
   ```
7. Stream SSE response từ DeerFlow:
   - Mỗi dòng `data: {...}` được parse JSON.
   - `type == "tool_call"` → ghi `current_task = "Tool: {name}"` vào `research_status.json`.
   - `type == "message"` + `role == "assistant"` → lưu 120 ký tự cuối vào `last_message`.
8. Timeout = 1800 giây (30 phút).
9. Kết thúc: `_write_status("idle", "Cycle complete", cycle)`.

### Bước 2: DeerFlow nhận RESEARCH_PROMPT

DeerFlow (LLM = Owl Alpha via OpenRouter) đọc `SKILL.md` workflow và thực hiện theo thứ tự:

1. Gọi `get_skill_knowledge` — tải operator rules.
2. Gọi `get_gold_alphas` — xem signal families đã có.
3. Chọn một family **chưa có** trong gold alphas.
4. Gọi `search_knowledge_base(query)` — tìm patterns liên quan.
5. Gọi `search_data_fields(query)` — xác minh field names tồn tại trên WQB.
6. Gọi `submit_alpha(formula, settings)` — backtest.
7. Nếu fail: gọi `diagnose_alpha(metrics)` → `mutate_formula(formula)` → thử lại.
8. Gọi `save_theory(title, body, confidence, tags)` — ghi nhận insight.

Mỗi tool call được route qua SSE đến MCP server tại `http://host.docker.internal:8765/sse`.

### Luồng hoàn chỉnh (sequence):

```
runner.py
    │
    ├── POST /api/chat/stream ──────────────────────────────────► DeerFlow
    │                                                                │
    │   ◄── SSE: tool_call: get_skill_knowledge ──────────────────  │
    │   SSE tool result: mcp_skill.md content ───────────────────►  │
    │                                                                │
    │   ◄── SSE: tool_call: get_gold_alphas ──────────────────────  │
    │   SSE tool result: [{formula, sharpe, fitness}] ───────────►  │
    │                                                                │
    │   ◄── SSE: tool_call: search_knowledge_base ────────────────  │
    │   SSE tool result: top-5 ChromaDB chunks ───────────────────►  │
    │                                                                │
    │   ◄── SSE: tool_call: search_data_fields ───────────────────  │
    │   SSE tool result: [{id, description, coverage}] ──────────►  │
    │                                                                │
    │   ◄── SSE: tool_call: submit_alpha ─────────────────────────  │
    │       │                                                         │
    │       ▼                                                         │
    │   WQB REST API                                                  │
    │   POST /simulations → 201 + Location header                     │
    │   GET /simulations/{id} (poll 2s, rồi 5s intervals)            │
    │   GET /alphas/{alpha_id} → {sharpe, fitness, turnover}         │
    │   GET /alphas/{id} → check SELF_CORRELATION                    │
    │   → save_alpha_result() + upsert_gold_alpha() nếu pass         │
    │       │                                                         │
    │   SSE tool result: {sharpe, fitness, turnover, status} ──────►  │
    │                                                                │
    │   ◄── SSE: tool_call: diagnose_alpha (nếu fail) ────────────  │
    │   ◄── SSE: tool_call: mutate_formula (nếu fail) ────────────  │
    │   ◄── SSE: tool_call: submit_alpha (mutation) ───────────────  │
    │                                                                │
    │   ◄── SSE: tool_call: save_theory ──────────────────────────  │
    │   → append to data/theory_log.json ─────────────────────────►  │
    │                                                                │
    ◄── SSE: message (assistant final summary) ────────────────────  │
    │
    └── _write_status("idle", "Cycle complete", 42)
        → data/research_status.json
```

---

## 4. Workflow 2 — WQB Simulation (Chi Tiết API)

**File:** `wqb_automation.py` — class `WQBAutomation`

### 4.1 Khởi tạo và Login

**`load_config()`**:
- Ưu tiên 1: env vars `WQB_EMAIL`, `WQB_PASSWORD`.
- Ưu tiên 2: `wqb_config.json` (gitignored).

**`WQBAutomation.__init__(config)`**:
- Tạo `requests.Session()`.
- Set `base_url = "https://api.worldquantbrain.com"`.

**`login()`**:
```
POST /authentication
Headers: Authorization: Basic base64(email:password)
         Content-Type: application/json

→ 201: login OK, lưu headers, lưu last_login_time
→ khác: log error, return False
```

**`refresh_login_if_needed()`**:
- Nếu `time.time() - last_login_time > 14400` (4 giờ) → gọi `login()` lại.

### 4.2 submit_alpha(formula, settings_str)

Được gọi từ MCP tool `submit_alpha()` trong `core/mcp/tools/alpha.py`.

**Bước 1: Parse settings_str**
```
"TOP3000|Subindustry|3|0.08"
→ universe="TOP3000", neutralization="SUBINDUSTRY", decay=3, truncation=0.08
```

**Bước 2: Kiểm tra failed_alphas**
```python
_get_store().is_failed(formula, settings_str)
# Nếu đã biết fail → return {"error": "Rejected: Known failed combination"}
```

**Bước 3: POST /simulations**
```json
{
  "type": "REGULAR",
  "regular": "group_rank(-ts_corr(est_ptp, est_fcf, 20), market)",
  "settings": {
    "instrumentType": "EQUITY",
    "region": "USA",
    "universe": "TOP3000",
    "delay": 1,
    "decay": 3,
    "neutralization": "SUBINDUSTRY",
    "truncation": 0.08,
    "pasteurization": "ON",
    "unitHandling": "VERIFY",
    "nanHandling": "OFF",
    "language": "FASTEXPR",
    "visualization": false
  }
}
```

Response: `201 Created` + `Location: /simulations/{sim_id}`

**Bước 4: Poll simulation**
```
GET /simulations/{sim_id}
→ {"status": "PENDING|RUNNING|COMPLETE|WARNING|ERROR", "progress": 0.0-1.0, "alpha": "alpha_id"}

Poll interval: 2s → sau đó 5s
Timeout: config.timeout_ms / 1000 (mặc định 300s)
```

**Bước 5: Lấy metrics**
```
GET /alphas/{alpha_id}
→ {
    "id": "WjgreNdN",
    "is": {
      "sharpe": 1.87,
      "fitness": 1.36,
      "turnover": 0.233,
      "returns": 0.12,
      "margin": 0.008,
      "drawdown": -0.15,
      "checks": [
        {"name": "SELF_CORRELATION", "value": 0.45, "result": "PASS"}
      ]
    }
  }
```

**`_extract_metrics_from_api()`**: lấy từ `alpha_data["is"]` các field: sharpe, fitness, turnover, returns, margin, drawdown, self_correlation.

**Bước 6: Đánh giá kết quả**
```
Nếu fitness >= 0.5:
    save_simulation() → bảng simulations
    _save_log() → save_alpha_result() → bảng alpha_results

Nếu Sharpe >= 1.25 AND Fitness >= 1.0 AND Turnover ∈ [1%, 70%]:
    check_self_correlation(alpha_id)
        GET /alphas/{id} → checks[SELF_CORRELATION]
        passes = result != "FAIL"
    
    Nếu passes:
        status = "UNSUBMITTED"
        _save_gold_alpha() → upsert_gold_alpha() → bảng gold_alphas
    Else:
        status = "CORRELATED"
        save_failed() → bảng failed_alphas
Else:
    save_failed() → bảng failed_alphas
```

**Retry logic** (via `@retry` tenacity):
- `wait_exponential(min=4, max=10)`, `stop_after_attempt(3)`.
- Chỉ retry khi có exception (network error, 429 rate limit).

### 4.3 search_data_fields(query, limit)

**Cache-first strategy**:
```python
# 1. Thử store local trước (nhanh, offline)
store.query_datafields(region="USA", universe="TOP3000", delay=1, search=query)
    → SELECT * FROM datafields WHERE region='USA' AND id LIKE '%query%' ... LIMIT 20

# 2. Nếu store trống → live API
GET /data-fields?instrumentType=EQUITY&region=USA&universe=TOP3000&delay=1&search=query&limit=20
    → cache kết quả vào store.upsert_datafields()
```

---

## 5. Workflow 3 — MCP Tools (9 Công Cụ)

**File:** `core/mcp/server.py` — FastMCP, SSE transport, port 8765.

DeerFlow connect qua `extensions_config.json`:
```json
{"type": "sse", "url": "http://host.docker.internal:8765/sse"}
```

Server khởi động bởi vm-setup.sh:
```bash
MCP_TRANSPORT=sse MCP_PORT=8765 nohup python3 core/mcp/server.py &
```

---

### Tool 1: `get_skill_knowledge()`
**File:** `core/mcp/tools/research.py`

```
Input:  (không có)
Output: string — toàn bộ nội dung mcp_skill.md

Luồng:
MCP_SKILL_PATH = BASE_DIR / "mcp_skill.md"
→ MCP_SKILL_PATH.read_text("utf-8")
→ Fallback: docs/legacy_sources.md nếu không có mcp_skill.md
```

Chứa: operator docs, broken operators (ts_max, ts_min, delay), proven settings, composite examples.

**Khi nào gọi:** Đầu mỗi session — DeerFlow load rule trước khi làm gì khác.

---

### Tool 2: `search_knowledge_base(query, top_k=5)`
**File:** `core/mcp/tools/research.py`

```
Input:  query: str, top_k: int (default 5)
Output: string — formatted top-k chunks với score + metadata

Luồng:
→ VectorStore() — khởi tạo ChromaDB client tại data/chroma/
    → chromadb.PersistentClient(path=str(chroma_dir))
    → embedding_function = SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
    → get_or_create_collection("alpha_knowledge", hnsw:space=cosine)
→ vs.search(query, top_k=5)
    → collection.query(query_texts=[query], n_results=min(top_k, col.count()))
    → trả về: [{content, score=1-distance, metadata}]
→ Format output: "**[1]** (score=0.823) *paper / academic_papers*\n{content}"
```

**Score**: cosine similarity = `1 - cosine_distance`. Score cao = liên quan nhiều.

---

### Tool 3: `search_data_fields(query, limit=20)`
**File:** `core/mcp/tools/research.py`

```
Input:  query: str (tên field hoặc từ khóa), limit: int
Output: list[dict] — [{id, description, type, coverage, user_count}]

Luồng:
→ WQBAutomation(config) — load từ env vars hoặc wqb_config.json
→ auto.search_data_fields(query, limit)
    → Thử store local (datafields table) trước
    → Nếu miss: GET /data-fields?search=query → cache → return
```

**Mục đích:** DeerFlow xác minh field như `est_ptp`, `est_fcf`, `adv20` tồn tại trên WQB trước khi dùng trong formula.

---

### Tool 4: `submit_alpha(formula, settings=None)`
**File:** `core/mcp/tools/alpha.py`

```
Input:
  formula:  str — "group_rank(-ts_corr(est_ptp, est_fcf, 20), market)"
  settings: dict — {"universe":"TOP3000","neutralization":"Subindustry","decay":3,"truncation":0.08}
            (default: TOP3000|Subindustry|3|0.08)
Output: str — JSON với {sharpe, fitness, turnover, status, self_correlation}

Luồng:
→ _get_automation() — singleton WQBAutomation, login nếu chưa
→ auto.submit_alpha(formula, settings_str)  [xem Workflow 2 chi tiết]
    ↳ automation chạy Submission Check đầy đủ (IS hard checks + self-correlation),
      set `status`, và tự ghi gold_alphas / failed_alphas. Đây là single source
      of truth cho verdict — xem docs/adr/0001.
→ Store().save_alpha_result(result)   → bảng alpha_results (tool này là writer duy nhất)
→ return json.dumps(result, indent=2)
```

> **Verdict nằm ở `status`**, KHÔNG tính lại ở MCP tool.
> `UNSUBMITTED` = gold (đã lưu) · `CORRELATED` = self-corr ≥ 0.7 · `FAIL_CHECKS` = hard IS check fail.
> Một alpha có thể đạt Sharpe/Fitness/Turnover nhưng vẫn `CORRELATED` → không phải gold.

---

### Tool 5: `get_gold_alphas()`
**File:** `core/mcp/tools/alpha.py`

```
Input:  (không có)
Output: str — JSON array của tất cả gold alphas trong DB

Luồng:
→ Store().get_gold_alphas()
    → SELECT * FROM gold_alphas
→ return json.dumps(alphas, indent=2)
```

DeerFlow dùng để tránh submit formula quá giống alpha hiện có (self-corr > 0.7).

---

### Tool 6: `diagnose_alpha(metrics)`
**File:** `core/mcp/tools/alpha.py`

```
Input:  metrics: dict — {sharpe: float, fitness: float, turnover: float, drawdown: float}
Output: dict — {pass: bool, issues: [...], fixes: [...]}

Rules:
  sharpe < 1.25   → issue + fix: "Try group_neutralize or increase lookback"
  fitness < 1.0   → issue + fix: "Add truncate(signal, 0.08)"
  turnover < 0.10 → issue + fix: "Reduce decay (try decay=1 or 0)"
  turnover > 0.70 → issue + fix: "Increase decay (try decay=6 or 10)"
```

Rule-based, không gọi API. Cho DeerFlow biết phải sửa gì.

---

### Tool 7: `mutate_formula(formula, n=3)`
**File:** `core/mcp/tools/alpha.py`

```
Input:  formula: str, n: int (max mutations trả về)
Output: list[str] — list n formula variants

Mutations (theo thứ tự):
1. Rút ngắn lookback: regex tìm ", {number})" → nhân 0.6
   e.g. ", 20)" → ", 12)"
2. Kéo dài lookback: nhân 2
   e.g. ", 20)" → ", 40)"
3. Thay "close" → "vwap"
4. Bọc volatility: "(formula) / (ts_std_dev(returns, 20) + 0.001)"

→ return mutations[:n]
```

---

### Tool 8: `save_theory(title, body, confidence, source_url, tags)`
**File:** `core/mcp/tools/memory.py`

```
Input:
  title:      str — "Earnings Surprise → Next-Day Reversal"
  body:       str — 2-5 câu giải thích plain language
  confidence: float 0.0-1.0
  source_url: str — URL nguồn tham khảo
  tags:       list[str] — ["momentum", "earnings"]
Output: str — "Theory 'X' saved (id=t0042, confidence=0.8)"

Luồng:
→ Đọc data/theory_log.json (list hiện tại)
→ Tạo entry với id="t{len+1:04d}", created_at=UTC now
→ Append vào list
→ Ghi lại data/theory_log.json (indent=2, ensure_ascii=False)
```

Hiển thị trên trang "Theory Notebook" của dashboard.

---

### Tool 9: `update_skill(lesson, category)`
**File:** `core/mcp/tools/memory.py`

```
Input:
  lesson:   str — "ts_min is broken on WQB, use ts_arg_min instead"
  category: str — operator|field|settings|strategy|source|general
Output: str — "Lesson recorded [OPERATOR] on 2026-06-22"

Luồng:
→ Tạo entry: "### [2026-06-22] [OPERATOR]\n{lesson}\n"
→ Append vào mcp_skill.md (mode 'a')
```

Cập nhật "institutional memory" — AI tự học và ghi nhớ.

---

## 6. Workflow 4 — Knowledge Base (ChromaDB)

**File:** `core/knowledge/vector_store.py` — class `VectorStore`

### 6.1 Collections

```
ChromaDB tại data/chroma/
├── alpha_knowledge  — Academic papers, brain tips, platform guides, research insights
└── wqb_fields       — WQB field/operator facts
```

Cả 2 collections dùng:
- **Embedding model:** `all-MiniLM-L6-v2` (SentenceTransformers, 384 dimensions)
- **Distance metric:** cosine (HNSW index)

### 6.2 Thêm chunks vào ChromaDB

**`add_chunks(chunks: list[dict])`**:
```python
# Mỗi chunk:
{
  "id": "doc_001_chunk_003",
  "content": "Earnings momentum: stocks with positive surprise ...",
  "metadata": {
    "source_id": "arxiv_2023_001",
    "source_type": "paper",
    "category": "academic_papers"
  }
}
→ collection.add(ids=[...], documents=[...], metadatas=[...])
# ChromaDB tự embed content qua SentenceTransformer
```

### 6.3 Semantic Search

**`search(query, top_k=5, collection="alpha_knowledge")`**:
```python
results = col.query(query_texts=[query], n_results=min(top_k, col.count()))
# ChromaDB embed query → tìm n_results gần nhất bằng HNSW cosine search
# Trả về: documents, distances, metadatas

# Convert:
score = round(1 - distance, 4)  # cosine similarity, range [0, 1]
```

### 6.4 Embedding Model

Config: `config.py` → `EMBED_MODEL = "st:all-MiniLM-L6-v2"`  
Nhưng `vector_store.py` hardcode `EMBED_MODEL = "all-MiniLM-L6-v2"` trực tiếp.  
Model được download lần đầu vào `~/.cache/torch/sentence_transformers/`.

### 6.5 Source Intelligence (knowledge_sources table)

```
Mỗi chunk gắn source_id qua bảng chunk_sources (chunk_id, source_id)

Khi alpha pass/fail:
    store.record_source_alpha(source_id, status)
    → UPDATE knowledge_sources
        SET alphas_tested = alphas_tested + 1,
            alphas_gold   = alphas_gold + (1 if gold else 0)
        WHERE id = source_id

Tính effectiveness:
    eff_pct = alphas_gold / alphas_tested * 100

DeerFlow đọc priority_sources():
    SELECT ... ORDER BY eff_pct DESC, alphas_gold DESC LIMIT 5
    → Ưu tiên crawl/search các domain/type hiệu quả nhất
```

---

## 7. Workflow 5 — Storage Layer (SQLite)

**File:** `storage/store.py` — class `Store`  
**Database:** `data/alpha_store.db` (SQLite, WAL mode)

### 7.1 Schema — 12 Tables + 2 Views

```sql
-- WQB Metadata (từ crawlers)
datasets        (id, name, region, universe, delay, field_count, ...)
datafields      (id, dataset_id, region, universe, delay, type, description, coverage, ...)
operators       (name, category, scope, definition, ...)

-- RAG Corpus (documents từ papers/blogs)
documents       (id, source, source_type, category, quality_score, raw_path)
chunks          (id, document_id, content, category, quality_score, word_count)
chunk_vectors   (chunk_id, model, dim, vector BLOB)  ← backup, ChromaDB là primary

-- Alpha Results
simulations     (sim_id, formula, settings, status, raw, ts)
alpha_results   (id, formula, settings, sharpe, fitness, turnover, returns, margin, drawdown, ts)
gold_alphas     (id, name, formula, settings, sharpe, fitness, turnover, returns, drawdown, status)
failed_alphas   (formula, settings, sharpe, fitness, ts)  ← tránh retry

-- Crawl Checkpoints
crawl_state     (key, cursor, updated_at)  ← resume sau khi bị interrupt

-- Source Intelligence
knowledge_sources (id, url, source_domain, source_type, alphas_tested, alphas_gold, is_blacklisted)
chunk_sources     (chunk_id, source_id)

-- Views
source_domain_stats  ← GROUP BY source_domain, tính effectiveness_pct
source_type_stats    ← GROUP BY source_domain, source_type, ORDER BY effectiveness_pct DESC
```

### 7.2 Các Operations Quan Trọng

**Upsert (idempotent)**:
```sql
INSERT INTO gold_alphas (...) VALUES (...)
ON CONFLICT(id) DO UPDATE SET name=excluded.name, status=excluded.status
```

**WAL mode**: `PRAGMA journal_mode=WAL` — cho phép đọc concurrent trong khi đang ghi.

**`chunks_missing_vectors()`**:
```sql
SELECT c.* FROM chunks c
LEFT JOIN chunk_vectors v ON v.chunk_id = c.id
WHERE v.chunk_id IS NULL
```
Dùng để biết chunk nào chưa được embed.

**`priority_sources(top_n=5)`**:
```sql
SELECT *, ROUND(CAST(alphas_gold AS REAL)/alphas_tested*100, 1) as eff_pct
FROM knowledge_sources
WHERE is_blacklisted = 0 AND alphas_tested > 0
ORDER BY eff_pct DESC, alphas_gold DESC
LIMIT 5
```

---

## 8. Workflow 6 — Observation Dashboard

**File:** `observation/app.py` + 5 pages  
**Chạy trên:** VM port 8080 (Docker container, volume mount từ `data/`)

### 8.1 Data Sources

```python
# observation/utils/db.py
ROOT = Path(__file__).parent.parent.parent  # = /app (trong container)
DB_PATH = ROOT / "data" / "alpha_store.db"  # = /app/data/alpha_store.db
                                             # ← volume mount từ /app/alpha-generator/data/
THEORY_LOG_PATH    = ROOT / "data" / "theory_log.json"
RESEARCH_STATUS_PATH = ROOT / "data" / "research_status.json"
RESEARCH_LOG_PATH  = ROOT / "RESEARCH_LOG.md"
MCP_SKILL_PATH     = ROOT / "mcp_skill.md"
```

Volume mount trong `docker-compose.override.yml`:
```yaml
volumes:
  - /app/alpha-generator/data:/app/data:ro
  - /app/alpha-generator/RESEARCH_LOG.md:/app/RESEARCH_LOG.md:ro
  - /app/alpha-generator/mcp_skill.md:/app/mcp_skill.md:ro
```

**Read-only mount** — dashboard không bao giờ ghi vào DB.

SQLite connection:
```python
def _conn():
    if not DB_PATH.exists(): return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

### 8.2 Các Trang Dashboard

**Page 1 — Observatory** (`research_status.json`):
- Agent state: running/idle/error
- Current cycle number
- Current task (last tool call)
- Last updated timestamp
- Auto-refresh 5s

**Page 2 — Alpha Lab** (`gold_alphas` table):
- Filter theo sharpe ≥, fitness ≥, turnover range
- Group by formula family
- Metrics: sharpe, fitness, turnover, drawdown
- Decode settings: `"TOP3000|Subindustry|3|0.08"` → columns

**Page 3 — Theory Notebook** (`theory_log.json`):
- List các theory được DeerFlow `save_theory()`
- Hiển thị: title, body, confidence bar, tags, source URL
- Chronological, mới nhất trên đầu

**Page 4 — Knowledge Map** (`alpha_knowledge` ChromaDB collection):
- Collection stats: bao nhiêu chunks trong `alpha_knowledge`, `wqb_fields`
- Semantic search UI: nhập query → top-5 results

**Page 5 — Source Intel** (`source_domain_stats` view):
- Bar chart: effectiveness_pct theo source_domain
- Table: source_type breakdown
- Xem nguồn nào → nhiều gold alphas nhất

---

## 9. Workflow 7 — Deployment (CI/CD)

### 9.1 GitHub Actions → GCE VM

**Trigger:** `git push origin main`

**Job: `deploy-vm`** (`.github/workflows/deploy.yml`):

1. **Authenticate GCP**: Workload Identity Federation (WIF), không cần service account key.
   ```
   GitHub OIDC token → GCP WIF pool → service account token
   ```

2. **Write .env to VM** (SSH IAP):
   ```bash
   # Tạo .env với tất cả secrets, encode base64
   printf '%s\n' "WQB_EMAIL=..." "OPENROUTER_KEY=..." | base64 -w0
   # SSH vào VM qua Identity-Aware Proxy (không cần public IP)
   gcloud compute ssh alpha-vm --tunnel-through-iap \
     --command="echo '${ENV_B64}' | base64 -d > /tmp/alpha-deerflow.env"
   ```

3. **Bootstrap or update VM**:
   ```bash
   git clone / git reset --hard origin/main
   bash deploy/vm-setup.sh  # idempotent
   ```

### 9.2 vm-setup.sh (idempotent bootstrap)

```bash
# 1. Install Docker (nếu chưa có)
curl -fsSL https://get.docker.com | sh

# 2. Install docker-compose-plugin

# 3. Clone DeerFlow + Alpha Generator (hoặc git pull)

# 4. Sync configs vào DeerFlow dir:
cp operation/deerflow/config.yaml /app/deer-flow/config.yaml
cp operation/deerflow/extensions_config.json /app/deer-flow/extensions_config.json
cp operation/deerflow/skills/.../SKILL.md /app/deer-flow/skills/custom/alpha-research/

# 5. Load .env từ /tmp/alpha-deerflow.env

# 6. Install Python deps:
pip3 install -r /app/alpha-generator/requirements.txt

# 7. Setup cron:
"0 */6 * * * cd /app/alpha-generator && python3 operation/runner.py >> /app/logs/runner.log 2>&1"

# 8. Start DeerFlow compose:
docker compose \
  --env-file /app/deer-flow/.env \
  -f docker/docker-compose.yaml \
  -f /app/alpha-generator/deploy/docker-compose.override.yml \
  up -d --build --force-recreate
# → Khởi động: gateway, backend, frontend, provisioner(disabled), streamlit

# 9. Start MCP server (SSE mode):
pkill -f "alpha-generator/core/mcp/server.py" || true
MCP_TRANSPORT=sse MCP_PORT=8765 \
  nohup python3 /app/alpha-generator/core/mcp/server.py \
  >> /app/logs/mcp-server.log &
# Poll http://localhost:8765/sse đến khi ready
```

### 9.3 Docker — Streamlit Container

**`Dockerfile.observation`**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-observation.txt .
RUN pip install --no-cache-dir -r requirements-observation.txt
COPY . .
EXPOSE 8080
CMD ["streamlit", "run", "observation/app.py",
     "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
```

Được build + start bởi docker-compose.override.yml.

---

## 10. IQC Pass Criteria

Alpha pass khi **tất cả** điều kiện thỏa:

| Metric | Threshold | Formula |
|--------|-----------|---------|
| **Sharpe** | ≥ 1.25 | Annualized risk-adjusted return |
| **Fitness** | ≥ 1.0 | `Sharpe × √(|Returns| / max(Turnover, 0.125))` |
| **Turnover** | 10% – 70% | Phần trăm portfolio thay đổi mỗi ngày |
| **Self-Correlation** | < 0.7 (với gold alphas) | Kiểm tra bởi WQB, quyết định có submit không |

**Operators bị cấm** (broken trên WQB): `ts_max`, `ts_min`, `delay`

**Settings chuẩn:**
```
universe=TOP3000, region=USA, neutralization=Subindustry, decay=3, truncation=0.08
delay=1, pasteurization=ON, language=FASTEXPR
```

---

## 11. Trạng Thái Alpha Pool

| Alpha ID | Formula Family | Sharpe | Fitness | Turnover | Status |
|----------|----------------|--------|---------|----------|--------|
| `WjgreNdN` | VWAP-Open 5d Deviation | 1.87 | 1.36 | 23.3% | SUBMITTED_SUCCESS |
| `58vYJp15` | VWAP 5d Reversal Decay=2 | 1.75 | 1.02 | 34.7% | UNSUBMITTED |
| `d5QrbL2g` | VWAP 7d Reversal Decay=5 | 1.65 | 1.17 | 22.0% | UNSUBMITTED |
| `Gro90oex` | VWAP 5d Reversal Decay=5 | 1.65 | 1.16 | 21.0% | UNSUBMITTED |
| `1YgWwo8W` | Vol-Adj Price Reversal | 1.58 | 1.00 | 30.3% | UNSUBMITTED |
| `wpeWEV9d` | VWAP 10d Reversal Decay=5 | 1.47 | 1.07 | 18.3% | UNSUBMITTED |
| `P01mYX0E` | VWAP-dev + Close Loc | 1.85 | 1.10 | 30.3% | CORRELATED (0.80) |

**Nhận xét:** Họ VWAP-deviation bão hòa. DeerFlow cần khám phá: earnings quality, analyst revisions, institutional flow, cross-sectional momentum, liquidity anomalies.

**Mục tiêu 3 tháng:** 20 gold alphas (hiện tại: 8).

---

## Quick Start (Manual Testing)

```bash
# Chạy 1 research cycle thủ công
python operation/runner.py --dry-run  # test kết nối, không gọi DeerFlow

# Kiểm tra alpha pool
python -c "from storage.store import Store; s=Store(); print(s.get_gold_alphas())"

# Test MCP server local
MCP_TRANSPORT=sse MCP_PORT=8765 python core/mcp/server.py

# Crawl WQB datafields
python operation/crawlers/wqb_datafields.py

# Chạy dashboard local
streamlit run observation/app.py --server.port 8080
```
