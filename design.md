# DESIGN — Alpha_Generator Architecture (v2)

> Tài liệu kiến trúc cho lần refactor lớn. Mục tiêu của bản v2 là **củng cố tầng Crawl (thu thập dữ liệu) và tầng Processing (xử lý dữ liệu)** — hai mắt xích đang yếu nhất hiện nay — đồng thời chuẩn hoá toàn hệ thống thành các tầng (layer) rõ ràng để Agent (Claude/Cursor) dùng như một MCP skill cao cấp.
>
> Đọc kèm: [guide.md](guide.md) — hướng dẫn refactor từng bước theo đúng kiến trúc trong tài liệu này.

---

## 1. Bối cảnh & Vấn đề hiện tại (v1)

Hệ thống v1 là một MCP server cho phép Agent nghiên cứu/sinh/mô phỏng Alpha trên WorldQuant Brain (WQB), kèm một knowledge base RAG. Sau khi đọc toàn bộ code, đây là các điểm yếu cốt lõi:

### 1.1 Tầng Crawl (yếu)
| Vấn đề | Vị trí | Hệ quả |
|--------|--------|--------|
| Chỉ crawl **metadata datafields** cho **một** cấu hình hardcode (`USA / EQUITY / TOP3000 / delay=1`) | [crawl_datasets.py:10](crawl_datasets.py#L10) | Bỏ lỡ EUR/ASI/CHN, các universe khác, delay 0 |
| **Không** crawl `/operators` | — | Agent phụ thuộc danh sách operator hardcode trong [mcp_skill.md](mcp_skill.md), dễ lỗi thời |
| Không resume / không incremental — mỗi lần chạy ghi đè toàn bộ | [crawl_datasets.py:54](crawl_datasets.py#L54) | Tốn thời gian, mất dữ liệu khi crash giữa chừng |
| Dùng `print`, retry sơ sài (chỉ 429 cho fields), tuần tự + `sleep` | [crawl_datasets.py:84](crawl_datasets.py#L84) | Chậm, khó debug, không có log có cấu trúc |
| Lưu ra hàng loạt `fields_<id>.json` rời rạc | [crawl_datasets.py:98](crawl_datasets.py#L98) | Khó truy vấn, không có schema, không khử trùng lặp |
| Không phân loại field `MATRIX` / `VECTOR` / `GROUP` | — | Agent không biết field nào cần `vec_*` operator |

### 1.2 Tầng Processing (yếu, phân mảnh)
| Vấn đề | Vị trí | Hệ quả |
|--------|--------|--------|
| **Hai đường xử lý tách rời**: `process_datafields.py` (xử lý field WQB) và `pipeline/` (xử lý doc markdown → chunks) không nối với nhau | [process_datafields.py](process_datafields.py) vs [pipeline/](pipeline/) | Datafields đã crawl **không** vào được knowledge base RAG |
| `classify.py` tính `category` + `quality_score` rồi ghi ra **sidecar** `classification_index.json`, **không bao giờ join lại vào chunks** | [classify.py:152](pipeline/classify.py#L152), [chunk.py:46](pipeline/chunk.py#L46) | Chunk mất nhãn → retriever mặc định `quality_score=50` ("bug quality_score=0") |
| RAG là **keyword/substring TF**, không có embedding/vector dù tên gọi là "vector index" | [knowledge_retriever.py:42](alpha_skills/knowledge_retriever.py#L42) | Không bắt được ngữ nghĩa, recall thấp |
| `quality_score` phụ thuộc `source_type` trong front-matter — đa số doc không có | [classify.py:86](pipeline/classify.py#L86) | Điểm chất lượng gần như vô dụng |

### 1.3 Tầng Service/Agent (nợ kỹ thuật)
- `mcp_server.py` import `from agent.tools.diagnose_alpha import ...` và `alpha_agent` — **các file này không tồn tại trong source** (chỉ còn `.pyc` cũ trong `__pycache__`). Tool `diagnose_alpha` sẽ crash khi gọi. Xem [mcp_server.py:141](mcp_server.py#L141).
- Tài liệu (`WORK.md`) mô tả nhiều thứ "đã hoàn thiện" nhưng thực tế chưa có trong repo.

> **Nguyên tắc thiết kế v2:** tách bạch tầng, chuẩn hoá I/O giữa các tầng qua **một SQLite store + schema rõ ràng**, biến mọi nguồn dữ liệu (WQB API + tài liệu ngoài) thành **plugin crawler** đổ vào cùng một pipeline xử lý, và nâng RAG lên **hybrid (vector + keyword)**.

---

## 2. Kiến trúc tổng thể (v2)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          AGENT LAYER (MCP client)                          │
│                    Claude / Cursor  ── gọi MCP tools                        │
└───────────────────────────────┬──────────────────────────────────────────┘
                                 │  stdio (MCP)
┌───────────────────────────────▼──────────────────────────────────────────┐
│                       SERVICE LAYER  (mcp_server.py)                        │
│  get_skill_knowledge · search_data_fields · search_knowledge_base ·        │
│  submit_alpha · diagnose_alpha · get_gold_alphas · mutate_formula ·        │
│  (mới) list_operators · refresh_local_data                                 │
└───────┬───────────────────────────────┬───────────────────────────┬───────┘
        │                               │                           │
┌───────▼─────────┐        ┌────────────▼────────────┐    ┌─────────▼────────┐
│ RETRIEVAL LAYER │        │   EXECUTION LAYER       │    │  DIAGNOSIS LAYER │
│ HybridRetriever │        │   WQBClient             │    │  diagnose_alpha  │
│ vector+keyword  │        │ (login/submit/poll/...) │    │  (rules engine)  │
│ +quality rerank │        │  wqb_automation.py      │    │  agent/tools/    │
└───────┬─────────┘        └────────────┬────────────┘    └──────────────────┘
        │ reads                         │ reads/writes
┌───────▼───────────────────────────────▼──────────────────────────────────┐
│                          STORAGE LAYER  (data/)                            │
│   SQLite  alpha_store.db                                                   │
│   ├─ datasets, datafields, operators        (crawled metadata)            │
│   ├─ documents, chunks, chunk_vectors       (RAG corpus + embeddings)     │
│   ├─ simulations, alpha_results, gold_alphas, failed_alphas (run history) │
│   └─ crawl_state                            (checkpoints / incremental)   │
│   + final_dataset/  (exported search_index.json, embeddings.npy)          │
└───────▲───────────────────────────────────────────────────────────────────┘
        │ writes
┌───────┴───────────────────────────────────────────────────────────────────┐
│                       PROCESSING LAYER  (pipeline/)                         │
│   clean → classify → chunk → embed → index   (steps có chung BaseStep)     │
│   + ingest_datafields  (đưa field WQB vào cùng corpus)                     │
└───────▲───────────────────────────────────────────────────────────────────┘
        │ writes raw
┌───────┴───────────────────────────────────────────────────────────────────┐
│                       INGESTION LAYER  (crawlers/)                          │
│   BaseCrawler  (session · retry/backoff · rate-limit · checkpoint · log)   │
│   ├─ WQBDatasetCrawler      (/data-sets)                                   │
│   ├─ WQBDataFieldCrawler    (/data-fields, ma trận region×universe×delay)  │
│   ├─ WQBOperatorCrawler     (/operators)                                   │
│   └─ ExternalDocCrawler     (papers / investopedia / brain tips → markdown)│
└────────────────────────────────────────────────────────────────────────────┘
```

**Luồng dữ liệu một chiều, idempotent:**
`Crawlers → (raw tables / raw markdown) → Pipeline steps → (chunks + vectors + indexed tables) → Retrieval/Service → Agent`.

---

## 3. Chi tiết từng tầng

### 3.1 Ingestion Layer — `crawlers/`

Mọi crawler kế thừa `BaseCrawler` để dùng chung hạ tầng (tham khảo pattern tách concern của `worldquant-miner`, lưu DB theo `q3yi/worldquant`):

```python
# crawlers/base.py
class BaseCrawler:
    def __init__(self, client: WQBClient, store: Store, *, rate_limit_qps=2.0): ...
    def request(self, url) -> dict:          # retry+backoff (tenacity), xử lý 429/5xx
    def checkpoint(self, key, cursor): ...   # ghi crawl_state để resume
    def resume_from(self, key) -> cursor: ...
    def run(self) -> CrawlResult:            # template method, mỗi subclass override fetch()
```

| Crawler | Endpoint | Iterate over | Ghi vào |
|---------|----------|--------------|---------|
| `WQBDatasetCrawler` | `/data-sets` | region × universe × delay × instrumentType | `datasets` |
| `WQBDataFieldCrawler` | `/data-fields` | mỗi dataset × (region,universe,delay) | `datafields` (kèm cột `type` MATRIX/VECTOR/GROUP, `coverage`, `user_count`) |
| `WQBOperatorCrawler` | `/operators` | — | `operators` (name, category, definition, scope) |
| `ExternalDocCrawler` | URL list cấu hình | danh sách nguồn | markdown vào `RAW_DATA_DIR` (đầu vào pipeline) |

Cải tiến bắt buộc so với v1:
- **Ma trận cấu hình** đọc từ `config.py` (`CRAWL_REGIONS`, `CRAWL_UNIVERSES`, `CRAWL_DELAYS`) thay vì hardcode.
- **Incremental / resume**: trước khi gọi API, đọc `crawl_state`; chỉ fetch phần thiếu. Upsert theo khoá tự nhiên (`field_id, region, universe, delay`).
- **Structured logging** (`structlog`) thay cho `print`; mỗi request log `url, status, latency, rows`.
- **Rate-limit tập trung** trong `BaseCrawler.request` (token bucket), không rải `sleep` khắp nơi.

### 3.2 Storage Layer — `data/alpha_store.db` (SQLite)

Một `Store` class (thin DAO) bọc SQLite, dùng chung cho cả crawler, pipeline và automation. Thay thế việc rải JSON + 3 hàm `sqlite3.connect` lặp lại trong `wqb_automation.py`.

Bảng chính:

```sql
datasets(id TEXT PK, name, region, universe, delay, instrument_type, field_count, raw JSON, crawled_at)
datafields(id, dataset_id, region, universe, delay, type, description,
           coverage REAL, user_count INT, raw JSON, crawled_at,
           PRIMARY KEY(id, region, universe, delay))
operators(name PK, category, scope, definition, raw JSON, crawled_at)

documents(id PK, source, source_type, category, quality_score INT, ingested_at, raw_path)
chunks(id PK, document_id, content, category, quality_score INT, word_count, chunk_type)
chunk_vectors(chunk_id PK, dim INT, vector BLOB)         -- embeddings (np.float32)

simulations(sim_id PK, formula, settings, status, raw JSON, ts)
alpha_results(id PK AUTOINCREMENT, formula, settings, sharpe, fitness, turnover,
              returns, margin, drawdown, ts, full JSON)
gold_alphas(id PK, name, formula, settings, sharpe, fitness, turnover, returns,
            drawdown, margin, status)
failed_alphas(formula, settings, sharpe, fitness, ts)

crawl_state(key PK, cursor JSON, updated_at)             -- resume checkpoints
```

Lưu ý migration: dữ liệu cũ (`gold_alphas.json`, `wqb_logs/wqb_data.db`, `fields_*.json`) được nạp một lần qua script migrate (xem guide §Step 7).

### 3.3 Processing Layer — `pipeline/`

Giữ pattern `BaseStep.run() -> StepResult` (đã tốt). Thay đổi:

1. **Hợp nhất `process_datafields.py` thành bước pipeline** `IngestDataFieldsStep`: đọc bảng `datafields`, sinh "document" mô tả mỗi field (id + description + dataset + coverage) và đẩy vào cùng corpus `documents/chunks`. → datafields trở thành một phần của RAG.
2. **Sửa "disconnect" classify↔chunk**: `classify` chạy *trước* và trả về `{category, quality_score}` theo `document_id`; `chunk` **gắn trực tiếp** nhãn này vào từng chunk (cột `category`, `quality_score` trong bảng `chunks`). Bỏ sidecar không ai đọc.
3. **Bước mới `EmbedStep`**: sinh embedding cho mỗi chunk, lưu `chunk_vectors`. Model cấu hình hoá (`EMBED_MODEL`); coi việc đổi model là *schema migration* (lưu `dim` + `model` để phát hiện lệch và re-embed).
4. **`IndexStep`** xuất artifact phục vụ retrieval: `search_index.json` (keyword) + `embeddings.npy`/lưu trong `chunk_vectors` (vector). Train/val/test split giữ nguyên.

Thứ tự mới: `clean → classify → chunk → embed → index` (+ `ingest_datafields` chạy song song nhánh trước `chunk`).

### 3.4 Retrieval Layer — `HybridRetriever`

Nâng `KnowledgeRetriever` thành hybrid, vẫn giữ chữ ký `search(query, top_k)` để `mcp_server` không phải đổi:

```
score = w_vec   * cosine(query_emb, chunk_emb)      # ngữ nghĩa  (mới)
      + w_kw    * keyword_similarity(query, chunk)   # giữ từ v1 (BM25/bigram)
      + w_len   * length_penalty(chunk)
      + w_qual  * quality_score/100                  # nay đã có thật từ chunks
```

- Trọng số trong `config.py`. Khi chưa có embedding (fallback) → tự động về chế độ keyword như v1 (không vỡ).
- Quality giờ lấy từ cột `chunks.quality_score` thật, không còn mặc định 50.

### 3.5 Execution Layer — `wqb_automation.py` → `WQBClient`

Tách phần "gọi API thuần" (login/submit/poll/search_data_fields/operators) khỏi phần "ghi log/DB". Phần ghi chuyển qua `Store`. Giữ retry/backoff (`tenacity`) đã có. Thêm `list_operators()` đọc từ `operators` table (fallback gọi `/operators` rồi cache).

### 3.6 Diagnosis Layer — `agent/tools/diagnose_alpha.py` (tạo mới)

Hiện `mcp_server` import file không tồn tại. Tạo một rules-engine thuần, không phụ thuộc mạng:
- Input: `{sharpe, fitness, turnover, drawdown, returns, margin}`.
- Output: `{verdict: pass|fail, issues: [...], fixes: [...]}` dựa trên ngưỡng IQC (Sharpe ≥ 1.25, Fitness ≥ 1.0, 0.01 ≤ TO ≤ 0.7, DD < 0.15) và heuristic Returns/TO ≥ 0.40.

### 3.7 Service Layer — `mcp_server.py`

Giữ nguyên các tool hiện có; **sửa import** sang module mới; bổ sung:
- `list_operators(category=None)` — phục vụ Agent thay vì đọc hardcode.
- `refresh_local_data(kind="datafields|operators|all")` — kích hoạt crawler + pipeline để làm tươi store.
- `search_data_fields` đọc **store trước** (nhanh, offline), chỉ gọi API khi cache miss hoặc `force_live=True`.

---

## 4. Cấu trúc thư mục mục tiêu

```
Alpha_Generator/
├─ config.py                  # + CRAWL_REGIONS/UNIVERSES/DELAYS, EMBED_MODEL, RAG weights
├─ data/
│  ├─ alpha_store.db          # SQLite store hợp nhất
│  └─ final_dataset/          # search_index.json, embeddings, splits
├─ crawlers/                  # ◀ MỚI — Ingestion Layer
│  ├─ base.py                 # BaseCrawler
│  ├─ wqb_datasets.py
│  ├─ wqb_datafields.py
│  ├─ wqb_operators.py
│  └─ external_docs.py
├─ pipeline/                  # Processing Layer (mở rộng)
│  ├─ base.py  clean.py  classify.py  chunk.py
│  ├─ embed.py               # ◀ MỚI
│  ├─ ingest_datafields.py   # ◀ MỚI (thay process_datafields.py)
│  └─ index.py
├─ storage/
│  └─ store.py               # ◀ MỚI — DAO bọc SQLite
├─ retrieval/
│  └─ hybrid_retriever.py    # nâng cấp knowledge_retriever.py
├─ agent/
│  └─ tools/diagnose_alpha.py # ◀ MỚI (sửa import đang gãy)
├─ wqb_automation.py          # → WQBClient (chỉ I/O API)
├─ mcp_server.py              # Service Layer
├─ run_pipeline.py            # + bước embed/ingest_datafields
└─ run_crawl.py               # ◀ MỚI — entrypoint chạy crawler
```

`process_datafields.py` và `crawl_datasets.py` được thay thế (giữ lại tạm như shim gọi sang module mới trong 1 release, rồi xoá — xem guide).

---

## 5. Ranh giới & hợp đồng giữa các tầng (contracts)

| Từ → Đến | Hợp đồng (interface ổn định) |
|----------|------------------------------|
| Crawler → Storage | `Store.upsert_datafields(rows)`, `upsert_operators(rows)`, `set_crawl_state(key, cursor)` |
| Storage → Pipeline | đọc `datafields`, ghi `documents/chunks/chunk_vectors` |
| Pipeline → Retrieval | `chunks(content, category, quality_score)` + `chunk_vectors(vector)` |
| Retrieval → Service | `HybridRetriever.search(query, top_k) -> markdown str` (không đổi chữ ký) |
| Execution → Service | `WQBClient.submit_alpha/search_data_fields/list_operators` |
| Service → Agent | danh sách `@mcp.tool` (giữ tương thích ngược) |

Giữ **chữ ký công khai không đổi** ở ranh giới Service↔Agent và Retrieval↔Service để refactor không phá Agent đang dùng.

---

## 6. Nguyên tắc chất lượng (Definition of Done cho v2)

1. **Idempotent**: chạy lại crawler/pipeline không tạo trùng lặp (upsert theo khoá).
2. **Resumable**: crawler crash giữa chừng → chạy lại tiếp tục từ `crawl_state`.
3. **Observability**: mọi tầng dùng `structlog`; mỗi bước in `summary + stats`.
4. **No dangling imports**: `python -c "import mcp_server"` chạy sạch; mọi tool gọi được.
5. **Backward-compatible MCP**: tên + chữ ký tool cũ giữ nguyên; thêm tool mới là tuỳ chọn.
6. **Test**: mỗi crawler/pipeline step có unit test trên fixture nhỏ (không gọi mạng thật).
7. **Migration an toàn**: dữ liệu cũ (gold/logs/fields) nạp được vào store mới, có thể rollback.

---

## 7. Tham chiếu (cách các hệ thống khác làm)

- **q3yi/worldquant** — `crawl.py` lưu fields vào **SQLite** (`alpha.db`), phân theo `type=MATRIX/VECTOR` và `dataset_id`. → cơ sở cho schema `datafields` có cột `type` + DB-backed.
- **zhutoutoutousan/worldquant-miner** — tách concern rõ: *generator / orchestrator / expression-miner / submitter*; giới hạn đồng thời, batch + retry; phân loại matrix/vector; validate biểu thức theo operator trước khi submit. → cơ sở cho tách tầng + `WQBOperatorCrawler`.
- **RussellDash332/WQ-Brain**, **Brainiac (jdhruv1503)** — pattern login/submit tối giản & agentic alpha builder. → tham chiếu Service/Agent.
- **RAG best practices 2025** (Unstructured, Databricks): chunk mang metadata `topic/date/source`, embedding domain-specialized hơn generic 12–30%, ingest **incremental** theo modified-time, đổi embedder = schema migration. → cơ sở cho `EmbedStep`, fix metadata join, incremental crawl.

---

## 8. Bài học từ các stack quant production (Qlib · VectorBT · OpenBB · LEAN/Nautilus)

Dự án này **không phải** một execution engine — WQB chính là sàn backtest/live của ta. Vì vậy LEAN, NautilusTrader, FinRL, Freqtrade, Hummingbot (execution/RL/market-making) nằm **ngoài phạm vi** core, chỉ mượn pattern *orchestration*. Hai hệ liên quan trực tiếp nhất tới tầng Crawl + Processing của ta là **Qlib** (data + alpha research) và **VectorBT** (alpha mining hàng loạt); **OpenBB** soi sáng cho abstraction đa nguồn.

| Hệ tham chiếu | Lớp tương ứng trong ta | Pattern mượn về |
|---------------|------------------------|-----------------|
| **Microsoft Qlib** (data layer + factor research, gần WQB nhất) | Storage + Processing | (a) **Data Catalog** dạng cache cục bộ cho field/operator (Qlib cache feature theo cột, point-in-time); (b) **expression/operator registry** tách rời data — ta tách `operators` table để validate biểu thức trước khi submit; (c) **incremental data update** (`get_data` chỉ tải phần thiếu) ↔ `crawl_state`. |
| **VectorBT** (vectorized backtest hàng nghìn chiến lược) | Orchestration / mining loop | **Parameter-grid sweep**: thay vì mutate ngẫu nhiên, sinh lưới tham số (lookback × neutralization × decay × truncation) rồi chấm điểm hàng loạt; lưu kết quả vào `alpha_results` để rerank. Định hình `mutate_formula` + research-cycle thành một sweep có hệ thống. |
| **OpenBB** (data terminal đa provider) | Ingestion | **Provider abstraction**: mọi nguồn (WQB API, papers, investopedia, sau này Polygon/Alpaca) nấp sau một interface chung — chính là `BaseCrawler`. Mở đường thêm nguồn dữ liệu giá/fundamental ngoài WQB mà không đụng pipeline. |
| **LEAN / NautilusTrader** | (ngoài phạm vi core) | Tách **research ↔ execution** rõ ràng; event-driven. Ta giữ ranh giới: Processing/Retrieval = research; `WQBClient` = execution adapter. Không tự viết matching engine. |
| **DeerFlow / CrewAI / LangGraph** | Service/Agent | **Orchestration layer** cho research-cycle tự vận hành (state machine: hypothesize → simulate → diagnose → mutate). Hiện do Agent + MCP đảm nhiệm; ghi nhận là hướng nâng cấp `run_research_cycle`. |

**Ba điều chỉnh cụ thể vào kiến trúc v2 nhờ các hệ trên:**

1. **Data Catalog (Qlib-style)** — bảng `datafields`/`operators` không chỉ là dump crawl mà là *catalog truy vấn được*: thêm chỉ mục theo `type`, `dataset_id`, `coverage`; `search_data_fields` phục vụ offline từ catalog (đã nêu §3.7). Đây là phiên bản thu nhỏ của Qlib data layer áp cho dữ liệu WQB.
2. **Operator registry để validate** (Qlib + worldquant-miner) — trước khi `submit_alpha`, đối chiếu các operator trong formula với bảng `operators`; chặn sớm formula dùng operator không tồn tại/đã hỏng, tiết kiệm quota simulation/ngày.
3. **Mining loop dạng grid sweep (VectorBT-style)** — tài liệu hoá `run_research_cycle` thành vòng lặp sinh-lưới + chấm điểm + lưu `alpha_results`, thay cho mutation rời rạc. (Triển khai ở Phase sau — xem guide.)

> Phạm vi v2 tập trung Crawl + Processing; các ý (2)(3) được đưa vào guide như **Phase mở rộng (tuỳ chọn)** để không làm phình lần refactor đầu.

Sources:
- https://github.com/q3yi/worldquant
- https://github.com/zhutoutoutousan/worldquant-miner
- https://github.com/RussellDash332/WQ-Brain
- https://github.com/jdhruv1503/Brainiac
- https://unstructured.io/insights/rag-systems-best-practices-unstructured-data-pipeline
- https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089
- https://github.com/microsoft/qlib
- https://vectorbt.dev
- https://openbb.co
- https://www.quantconnect.com/lean
- https://nautilustrader.io
