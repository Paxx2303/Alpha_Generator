# GUIDE — Refactor từng bước theo kiến trúc v2

> Hướng dẫn thực thi [design.md](design.md). Mỗi bước **độc lập kiểm thử được**, có *mục tiêu → việc làm → tiêu chí xong (DoD) → cách verify*. Làm tuần tự; sau mỗi Phase, hệ thống vẫn chạy được (không "big bang").
>
> Quy ước: ✅ = bắt buộc cho v2 (Crawl + Processing); 🔵 = mở rộng tuỳ chọn (làm sau).
>
> **Nguyên tắc vàng:** giữ chữ ký các `@mcp.tool` và `HybridRetriever.search(query, top_k)` **không đổi** suốt quá trình, để Agent đang dùng không bị vỡ.

---

## Phase 0 — Chuẩn bị & chốt baseline ✅

**Mục tiêu:** có lưới an toàn trước khi đụng code.

**Việc làm**
1. Tạo branch: `git checkout -b refactor/v2-data-layer`.
2. Dọn rác đang gây hiểu nhầm: xoá `__pycache__/` cũ (đặc biệt `alpha_agent.cpython-310.pyc` — file nguồn không còn) để tránh import nhầm.
   - `git rm -r --cached __pycache__` và thêm `__pycache__/` vào `.gitignore`.
3. Pin thêm dependency vào `requirements.txt`: `numpy` (đã có), thêm `sentence-transformers` *hoặc* để mặc định hashing-embedding (xem Step 4 — không bắt buộc model nặng).
4. Viết một **smoke test** ghi lại hành vi hiện tại để so sánh sau refactor:
   - `python -c "import mcp_server"` → hiện **sẽ lỗi** ở `diagnose_alpha` import? Không (import lazy trong hàm) — nhưng gọi tool sẽ lỗi. Ghi chú lại.
   - `python run_pipeline.py --only index` chạy được trên dữ liệu hiện có.

**DoD / Verify:** branch sạch, `.gitignore` cập nhật, ghi chú baseline (cái gì chạy / cái gì gãy) vào PR description.

---

## Phase 1 — Storage Layer: `storage/store.py` ✅

**Mục tiêu:** một DAO SQLite duy nhất, thay cho JSON rải rác + 3 khối `sqlite3.connect` lặp trong `wqb_automation.py`.

**Việc làm**
1. Tạo `data/` và `config.py` thêm: `DATA_DIR = BASE_DIR / "data"`, `STORE_DB = DATA_DIR / "alpha_store.db"`.
2. Tạo `storage/store.py` với class `Store`:
   - `__init__(db_path=STORE_DB)` → mở connection, bật `PRAGMA journal_mode=WAL`.
   - `init_schema()` → tạo toàn bộ bảng ở [design.md §3.2](design.md). Dùng `CREATE TABLE IF NOT EXISTS`.
   - Upsert helpers: `upsert_datasets(rows)`, `upsert_datafields(rows)`, `upsert_operators(rows)` (dùng `INSERT ... ON CONFLICT(...) DO UPDATE`).
   - `set_crawl_state(key, cursor)` / `get_crawl_state(key)`.
   - Đọc: `query_datafields(region, universe, delay, type=None, search=None)`, `list_operators(category=None)`.
   - Migration helpers cho Phase 7: `insert_chunk`, `insert_chunk_vector`, `upsert_gold_alpha`, `insert_alpha_result`, `insert_failed`.
3. Không nhét logic nghiệp vụ vào `Store` — chỉ CRUD thuần.

**DoD / Verify**
- `python -c "from storage.store import Store; s=Store(); s.init_schema(); print('ok')"` tạo `data/alpha_store.db` với đủ bảng.
- Unit test `tests/test_store.py`: upsert 2 lần cùng khoá → vẫn 1 hàng (idempotent).

---

## Phase 2 — Ingestion Layer: `crawlers/` ✅

> Đây là trọng tâm "bổ sung crawl data". Làm `BaseCrawler` trước, rồi 3 crawler WQB.

### Step 2.1 — `crawlers/base.py`
**Việc làm**
- Class `BaseCrawler(client: WQBClient, store: Store, rate_limit_qps=2.0)`:
  - `request(url) -> dict`: bọc `tenacity` retry/backoff; xử lý `429` (đọc `Retry-After`), `5xx`; token-bucket theo `rate_limit_qps`; log `structlog` (`url,status,latency,rows`).
  - `run() -> CrawlResult` là **template method**; subclass override `fetch()` (generator các trang) và `persist(rows)`.
  - Checkpoint: `self.store.set_crawl_state(self.key, cursor)` sau mỗi trang; `run()` đọc `get_crawl_state` để resume.
- `CrawlResult` dataclass: `{fetched, upserted, skipped, resumed_from}`.

### Step 2.2 — `crawlers/wqb_datasets.py` → `WQBDatasetCrawler`
- Iterate ma trận `CRAWL_REGIONS × CRAWL_UNIVERSES × CRAWL_DELAYS × CRAWL_INSTRUMENTS` (thêm vào `config.py`, mặc định giữ `USA/TOP3000/1/EQUITY` để tương thích v1).
- Phân trang `/data-sets?...&limit=20&offset=N` (logic v1 ở [crawl_datasets.py:34](crawl_datasets.py#L34) tái sử dụng), `store.upsert_datasets`.

### Step 2.3 — `crawlers/wqb_datafields.py` → `WQBDataFieldCrawler`
- Với mỗi dataset (đọc từ bảng `datasets`), phân trang `/data-fields`.
- **Mới:** trích `type` (MATRIX/VECTOR/GROUP), `coverage`, `userCount`; khoá upsert `(id, region, universe, delay)`.
- Resume theo `(dataset_id, region, universe, delay, offset)`.

### Step 2.4 — `crawlers/wqb_operators.py` → `WQBOperatorCrawler`
- Gọi `/operators`; lưu `name, category, scope, definition` vào bảng `operators`.

### Step 2.5 — `run_crawl.py` (entrypoint)
- CLI: `python run_crawl.py --kind datasets,datafields,operators [--resume]`.
- Khởi tạo `WQBClient` (login), `Store`, chạy lần lượt crawler, in `CrawlResult`.

**DoD / Verify (Phase 2)**
- `python run_crawl.py --kind operators` → bảng `operators` có dữ liệu; chạy lại lần 2 không tăng số hàng (idempotent).
- Ngắt giữa chừng `datafields` rồi chạy lại `--resume` → tiếp tục, không crawl lại phần đã xong.
- Test offline `tests/test_crawler.py`: mock `request()` trả fixture JSON → kiểm `persist` upsert đúng số hàng (không gọi mạng).

---

## Phase 3 — Tách `wqb_automation.py` → `WQBClient` ✅

**Mục tiêu:** phần "gọi API thuần" dùng được bởi crawler; phần "ghi log/DB" chuyển sang `Store`.

**Việc làm**
1. Đổi tên/khúc tách: giữ file `wqb_automation.py` nhưng tách class `WQBClient` chỉ chứa: `login`, `refresh_login_if_needed`, `submit_alpha` (chỉ gọi + poll, trả metrics), `search_data_fields`, **mới** `list_operators()`.
2. Chuyển `save_raw_response`, `_save_log`, `_save_failed_combination`, `_save_gold_alpha` sang gọi `Store` (giữ wrapper cũ tạm thời để không vỡ caller).
3. `search_data_fields`: thêm tham số `force_live=False` — mặc định đọc `store.query_datafields(...)`, cache miss mới gọi API rồi upsert.
4. `list_operators`: đọc `store.list_operators()`, rỗng thì gọi `/operators` (qua crawler) rồi cache.

**DoD / Verify**
- `submit_alpha` vẫn trả đúng dict metrics như trước (so với baseline Phase 0).
- `search_data_fields("pe ratio")` trả kết quả từ store khi đã crawl, không gọi mạng (log xác nhận).

---

## Phase 4 — Processing Layer: nối liền & thêm embed ✅

> Sửa 2 lỗi gốc: (a) `process_datafields` tách rời, (b) classify↔chunk không join.

### Step 4.1 — `pipeline/ingest_datafields.py` (thay `process_datafields.py`)
- Class `IngestDataFieldsStep(BaseStep)`: đọc bảng `datafields`, mỗi field → một "document" (`id` + `description` + `dataset` + `coverage` + `type`) ghi vào bảng `documents`/`chunks` (mỗi field thường là 1 chunk ngắn → đặt `chunk_type="datafield"`, `category="datafield"`, `quality_score` theo `coverage`).
- Giữ `process_datafields.py` thành **shim** gọi step mới (in cảnh báo deprecated), xoá ở release sau.

### Step 4.2 — Sửa disconnect classify ↔ chunk
- Trong `pipeline/clean.py`/`classify.py`/`chunk.py`: cho `classify` chạy **trước** `chunk`, trả `{document_id: {category, quality_score}}`.
- `chunk.py`: khi tạo mỗi chunk, **gắn trực tiếp** `category` + `quality_score` của document cha vào `metadata` *và* ghi cột tương ứng trong bảng `chunks`. Bỏ `classification_index.json` sidecar.
- `compute_quality_score`: bổ sung nguồn điểm khi `source_type` trống (suy ra từ thư mục: `academic_papers`→paper, `documentation`→official_docs, …) để hết cảnh "quality=0".

### Step 4.3 — `pipeline/embed.py` → `EmbedStep`
- Sinh embedding cho mỗi chunk, lưu `chunk_vectors(chunk_id, dim, vector BLOB)`.
- `EMBED_MODEL` trong `config.py`. Hai lựa chọn:
  - **Nhẹ, không phụ thuộc:** hashing/TF-IDF vector (numpy) — đủ để bật hybrid, không cần tải model.
  - **Tốt hơn:** `sentence-transformers` (vd `all-MiniLM-L6-v2`) nếu môi trường cho phép.
- Lưu kèm `model` + `dim`; nếu khác với DB hiện tại → cảnh báo "cần re-embed" (đổi embedder = schema migration, theo best practice).

### Step 4.4 — Cập nhật `run_pipeline.py`
- Thứ tự mới: `clean → classify → chunk → embed → index`; thêm `ingest_datafields` vào `ALL_STEPS`.

**DoD / Verify**
- `python run_pipeline.py` chạy hết 6 bước, in stats từng bước.
- Truy vấn `chunks`: cột `category`/`quality_score` **khác 0/khác mặc định** cho phần lớn chunk (kiểm bằng SQL `SELECT category, COUNT(*) ...`).
- `chunk_vectors` có số hàng == số chunk.

---

## Phase 5 — Retrieval Layer: `retrieval/hybrid_retriever.py` ✅

**Mục tiêu:** nâng RAG keyword → hybrid, **không đổi chữ ký** `search(query, top_k)`.

**Việc làm**
1. Tạo `retrieval/hybrid_retriever.py` (copy nền từ `alpha_skills/knowledge_retriever.py`).
2. Đọc chunks + vectors từ `Store` (không còn đọc file rời).
3. `score = w_vec*cosine + w_kw*keyword + w_len*length_penalty + w_qual*quality/100` (trọng số trong `config.py`).
4. **Fallback**: nếu không có embedding cho query/chunk → `w_vec=0`, tự chuẩn hoá lại trọng số → hành vi về đúng v1 (không vỡ).
5. `mcp_server.search_knowledge_base` import từ module mới; giữ `alpha_skills/knowledge_retriever.py` thành shim re-export 1 release.

**DoD / Verify**
- `python -m retrieval.hybrid_retriever "momentum mean reversion"` trả top_k có `Score/Quality/Source`.
- So với v1 trên vài truy vấn: recall tốt hơn hoặc ít nhất không tệ hơn; `Quality` hiển thị giá trị thật (không còn toàn 50).

---

## Phase 6 — Diagnosis + Service Layer ✅

### Step 6.1 — `agent/tools/diagnose_alpha.py` (sửa import đang gãy)
- Rules-engine thuần (không mạng), input `{sharpe,fitness,turnover,drawdown,returns,margin}`, output `{verdict, issues, fixes}` theo ngưỡng IQC (Sharpe≥1.25, Fitness≥1.0, 0.01≤TO≤0.7, DD<0.15, Returns/TO≥0.40).
- Thêm `agent/__init__.py`, `agent/tools/__init__.py`.

### Step 6.2 — `mcp_server.py`
- Sửa import `diagnose_alpha` sang module mới (đã đúng path `agent.tools.diagnose_alpha` — nay file tồn tại).
- `search_data_fields` tool: thêm `force_live` (default False) đọc store trước.
- Thêm tool **mới** (tuỳ chọn nhưng khuyến nghị):
  - `list_operators(category: str = None)` → `WQBClient.list_operators`.
  - `refresh_local_data(kind: str = "all")` → chạy crawler tương ứng + pipeline `ingest_datafields`.

**DoD / Verify**
- `python -c "import mcp_server"` sạch; gọi `diagnose_alpha({"sharpe":0.91,"fitness":0.34,"turnover":32.6,"drawdown":7.5})` trả verdict + fixes (không crash).
- `list_operators("Time Series")` trả từ store.

---

## Phase 7 — Migration dữ liệu cũ ✅

**Mục tiêu:** không mất lịch sử khi chuyển sang store mới.

**Việc làm** — script `scripts/migrate_v1_to_v2.py`:
1. `gold_alphas.json` → bảng `gold_alphas`.
2. `wqb_logs/wqb_data.db` (bảng `alpha_results`, `raw_simulations`) → bảng `alpha_results`/`simulations`.
3. `wqb_logs/failed_alphas.json` → `failed_alphas`.
4. `alpha_skills/rawdata/fields_*.json` (nếu còn) → `datafields`.
5. In báo cáo số hàng migrate; **đọc-trước** dữ liệu cũ, không xoá (rollback = chỉ cần bỏ `alpha_store.db`).

**DoD / Verify:** số gold/alpha_results trong store khớp nguồn cũ; chạy lại migrate idempotent.

---

## Phase 8 — Dọn dẹp & tài liệu ✅

1. Xoá shim đã hết hạn (`process_datafields.py`, `crawl_datasets.py` cũ, `knowledge_retriever.py` cũ) sau khi caller đã chuyển.
2. Cập nhật `STARTUP_GUIDE.md` / `MCP_USAGE.md`: lệnh mới `run_crawl.py`, `run_pipeline.py` (6 bước), tool mới.
3. Cập nhật `WORK.md` cho khớp thực tế (gỡ phần mô tả `alpha_agent.py` không tồn tại).
4. README: sơ đồ tầng từ [design.md §2](design.md).

**DoD / Verify:** không còn import tới module đã xoá (`grep`); docs phản ánh đúng lệnh chạy được.

---

## Phase 9 (🔵 mở rộng — làm sau, lấy cảm hứng Qlib/VectorBT)

> Ngoài phạm vi "Crawl + Processing" của v2 nhưng đã chừa chỗ trong kiến trúc.

- **9.1 Operator-validation trước submit** (Qlib registry + worldquant-miner): trong `submit_alpha`, parse operator trong formula, đối chiếu bảng `operators`; chặn formula dùng operator không tồn tại → tiết kiệm quota.
- **9.2 Grid-sweep mining** (VectorBT-style): biến `run_research_cycle` thành sinh lưới `lookback × neutralization × decay × truncation`, submit hàng loạt (tôn trọng giới hạn/ngày), rerank theo `alpha_results`.
- **9.3 Provider abstraction đa nguồn** (OpenBB-style): thêm crawler giá/fundamental ngoài WQB sau cùng một `BaseCrawler`.
- **9.4 Orchestration tự vận hành** (LangGraph/CrewAI): state machine hypothesize→simulate→diagnose→mutate cho vòng nghiên cứu khép kín.

---

## Bảng tổng tiến độ

| Phase | Layer | Bắt buộc | Verify chính |
|------:|-------|:--------:|--------------|
| 0 | Chuẩn bị | ✅ | branch + baseline ghi lại |
| 1 | Storage `store.py` | ✅ | init_schema, upsert idempotent |
| 2 | Crawlers | ✅ | crawl + resume + offline test |
| 3 | `WQBClient` tách | ✅ | submit_alpha không đổi output |
| 4 | Pipeline (join + embed) | ✅ | chunks có category/quality thật |
| 5 | HybridRetriever | ✅ | search hybrid, fallback an toàn |
| 6 | Diagnosis + MCP | ✅ | import sạch, tool chạy |
| 7 | Migration | ✅ | số hàng khớp nguồn cũ |
| 8 | Dọn dẹp + docs | ✅ | không còn dangling import |
| 9 | Mở rộng (Qlib/VectorBT) | 🔵 | tuỳ chọn |

**Thứ tự an toàn nhất:** 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Mỗi Phase commit riêng, chạy được, dễ review & rollback.
