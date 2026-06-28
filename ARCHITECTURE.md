# Alpha Generator — Tài Liệu Kiến Trúc Chi Tiết

**Phiên bản:** 3.0  
**Cập nhật:** 2026-06-28  
**Trạng thái:** v3 hoàn chỉnh; GCP deployment đang triển khai

---

## MỤC LỤC

1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Kiến Trúc 3 Layer](#2-kiến-trúc-3-layer)
3. [CORE — Brain & Knowledge](#3-core--brain--knowledge)
4. [OPERATION — DeerFlow AI Researcher](#4-operation--deerflow-ai-researcher)
5. [OBSERVATION — Dashboard](#5-observation--dashboard)
6. [WQB Automation — API Client](#6-wqb-automation--api-client)
7. [Data & Storage](#7-data--storage)
8. [Deploy & CI/CD](#8-deploy--cicd)
9. [Automation Check Tools](#9-automation-check-tools)
10. [Luồng Dữ Liệu End-to-End](#10-luồng-dữ-liệu-end-to-end)
11. [Vấn Đề Đã Biết & Fix Priority](#11-vấn-đề-đã-biết--fix-priority)
12. [Roadmap](#12-roadmap)

---

## 1. Tổng Quan Hệ Thống

Alpha Generator là một **AI researcher tự động** chạy 24/7 trên GCP, mục tiêu tìm ra alpha signals trên WorldQuant Brain (WQB) mà không cần can thiệp thủ công.

### Vision
- AI tự nghiên cứu, test, và ghi nhận kết quả
- User chỉ cần mở dashboard để quan sát
- Kỹ năng quant phát triển song song thông qua Theory Notebook

### Mục Tiêu 3 Tháng
| Metric | Hiện tại | Target |
|--------|----------|--------|
| Gold alphas | 8 | ≥ 20 |
| Research cycles/tuần | Manual | ≥ 10 (tự động) |
| Nguồn được crawl | 1 | ≥ 3 loại |
| Data loss incidents | 0 | 0 |

### Gold Alpha Threshold
```
Sharpe    ≥ 1.25
Fitness   ≥ 1.0   (= Sharpe × √(|Returns| / max(TO, 0.125)))
Turnover  10–70%
Self-correlation < 0.7
```

---

## 2. Kiến Trúc 3 Layer

```
┌─────────────────────── GCP ──────────────────────────────────┐
│                                                               │
│  GCE VM: alpha-vm (e2-standard-4, 4vCPU/16GB)               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                                                        │   │
│  │  [OPERATION] research_daemon.py  ──► DeerFlow Docker  │   │
│  │       │                                    │           │   │
│  │       │ poll gold count                    │ SSE       │   │
│  │       ▼                                    ▼           │   │
│  │  [CORE]  alpha_store.db (SQLite)    MCP Server :8765  │   │
│  │          ChromaDB (vectors)         (FastMCP SSE)     │   │
│  │          SourceRegistry                    │           │   │
│  │                                            │ REST API  │   │
│  │  [OBSERVATION] Streamlit :8080    WQB API (cloud)     │   │
│  │       │                                               │   │
│  │       └── read-only mount (/app/data)                │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  [GCS] alpha-backups-* ← backup_manager.py (mỗi 4h)         │
│  [Cloud Run] alpha-obs (Streamlit, tương lai)                │
└───────────────────────────────────────────────────────────────┘
```

### Stack Cốt Lõi
```
DeerFlow (ByteDance, Docker)
  → OpenRouter API (DeepSeek-Chat, Ultra mode: 5 plans / 30 steps)
  → MCP Server (FastMCP, SSE port 8765)
  → WQB REST API (api.worldquantbrain.com)
  → SQLite (alpha_store.db) + ChromaDB (vectors)
  → Streamlit Dashboard (read-only)
```

---

## 3. CORE — Brain & Knowledge

### 3.1 MCP Server (`core/mcp/server.py`)

**Transport:** SSE trên port 8765  
**DeerFlow kết nối qua:** `extensions_config.json` → `{"type": "sse", "url": "http://host.docker.internal:8765/sse"}`

**8 Tools đã đăng ký:**

| Tool | Chức năng |
|------|-----------|
| `submit_alpha(formula, settings)` | Submit formula lên WQB, poll kết quả, lưu DB |
| `get_gold_alphas()` | Lấy tất cả gold alphas từ SQLite |
| `diagnose_alpha(metrics)` | Phân tích Sharpe/Fitness/Turnover, trả về fix recommendations |
| `mutate_formula(formula, n)` | Sinh n biến thể: lookback ×0.6, ×2, close→vwap, vol-norm |
| `save_theory(title, body, confidence, tags)` | Ghi theory vào Theory Notebook |
| `update_skill(content)` | Cập nhật SKILL.md với kiến thức mới |
| `search_data_fields(keywords)` | Tìm WQB field names từ metadata DB |
| `get_skill_knowledge(market_setting, topic)` | Trả về theories + gold alphas + failed patterns |

### 3.2 Knowledge Layer (`core/knowledge/`)

**ChromaDB Vector Store** (`vector_store.py`)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (dim=384)
- Lưu chunks của research papers, blog posts, WQB docs
- Semantic search cho DeerFlow khi tìm relevant knowledge

**Source Registry** (`source_registry.py`)
- SQLite-based: lưu effectiveness score theo từng nguồn
- Metric: `effectiveness = (alphas_gold + 1) / (alphas_tested + 2)` (Bayesian smoothing)
- `priority_sources()` → DeerFlow đọc đầu mỗi cycle để chọn domain hiệu quả nhất

**Phân loại nguồn — 2 tầng:**
```
source_domain           source_type
─────────────           ────────────────────────────────
general_quant    →      arxiv, ssrn, quant_blog, book, research_report
wqb_specific     →      wqb_forum, wqb_docs, brain_tips, manual
```

**Entities** (`entities.py`)
- Pydantic models: `OperatorFact`, `FieldFact`, `AlphaPattern`

**Knowledge Graph** (`graph.py`)
- Skeleton only (NetworkX) — kích hoạt sau khi có ≥ 200 alphas
- Node: operators, fields, patterns; Edge: co-occurs / contradicts

### 3.3 Config (`config.py`)

Key settings:
```python
EMBED_MODEL  = "st:all-MiniLM-L6-v2"   # semantic search (production)
EMBED_DIM    = 384
TOP_K_RESULTS = 5
HYBRID_VEC_WEIGHT = 0.45  # vector sim
HYBRID_KW_WEIGHT  = 0.30  # keyword overlap
```

WQB formula categories để keyword scoring: `technical_indicators`, `quantitative_methods`, `platform_guides`, `academic_papers`, `research_insights`, `core_concepts`.

---

## 4. OPERATION — DeerFlow AI Researcher

### 4.1 DeerFlow Config (`operation/deerflow/config.yaml`)

```yaml
# Ultra Research Mode
max_plan_iterations: 5    # Fast=1, Pro=3, Ultra=5
max_step_num: 30          # Fast=3, Pro=10, Ultra=30
enable_background_investigation: true

models:
  - name: openrouter
    model: deepseek/deepseek-chat
    api_key: $OPENROUTER_KEY
    base_url: https://openrouter.ai/api/v1
    max_tokens: 16384
    temperature: 0.6
    request_timeout: 600.0   # 10 min per session
```

### 4.2 Research Daemon (`operation/research_daemon.py`)

Daemon tự động điều phối toàn bộ research loop:

**Market Setting Rotation (15 settings):**
```
TOP1000|INDUSTRY|3|0.08       ← highest empirical pass rate
TOP1000|SUBINDUSTRY|3|0.08
TOP1000|SECTOR|3|0.08
TOP1000|MARKET|3|0.08
TOP1000|NONE|3|0.08
TOP3000|INDUSTRY|3|0.08
TOP3000|SUBINDUSTRY|3|0.08
... (total 15 settings)
TOP200|INDUSTRY|3|0.08
```

**Rotation Logic:**
- Poll mỗi 120s
- Rotate khi: `1 gold alpha found` OR `1 hour elapsed`
- State được persist tại `data/research_state.json`

**Trigger DeerFlow:**
```python
# POST /api/chat/stream với Ultra mode params
# Header: X-Internal-Token (bypass CSRF)
# Không cần consume stream — DeerFlow nghiên cứu trong Docker
```

**DeerFlow API endpoint:** `http://localhost:8001` (exposed qua docker-compose.override.yml)

### 4.3 Research SKILL (`operation/deerflow/skills/alpha-research/SKILL.md`)

Workflow 9 bước cho mỗi session:

```
Step 1: Load Context        → get_skill_knowledge(setting, topic)
Step 2: Choose Formula Family
        - Corr Divergence: -ts_corr(a, b, window)
        - Rank Momentum: ts_rank(field, window)
        - Cross-sectional Z: -ts_zscore(field, window)
        - Reversal: -(close-open)/open
        - Delta Momentum: ts_delta(field,s)/ts_std_dev(field,l)
Step 3: Find Fields         → search_data_fields(keywords)
Step 4: Build Formula       → rank → group_neutralize → truncate(0.08)
Step 5: Submit & Diagnose   → submit_alpha() + diagnose_alpha()
Step 6: Compare with Theory → get_skill_knowledge() lần 2
Step 7: Mutate & Iterate    → mutate_formula(formula, 3)
Step 8: Record Finding      → save_theory()
Step 9: Decide Next Action
```

**Hard Constraints:**
- NEVER guess field names — luôn dùng `search_data_fields` trước
- NEVER use `ts_min`, `ts_max`, `delay` (broken trên WQB)
- Test ≥ 10 formula variations mỗi session
- Test ≥ 3 operator families trước khi khai báo setting exhausted

### 4.4 Crawlers (`crawlers/`)

| File | Chức năng |
|------|-----------|
| `wqb_datasets.py` | Crawl WQB dataset metadata |
| `wqb_datafields.py` | Crawl field names và descriptions |
| `wqb_operators.py` | Crawl operator documentation |

Base crawler: `base.py` — token-bucket rate limiting (2.0 QPS), offset paging (20/page).

---

## 5. OBSERVATION — Dashboard

### 5.1 Streamlit App (`observation/app.py`)

**Deploy:** Docker container trên GCE VM (port 8080)  
**Data access:** Read-only volume mount `/app/alpha-generator/data:/app/data:ro`

**5 Pages:**

| Page | File | Nội dung |
|------|------|----------|
| Observatory | `1_Observatory.py` | DeerFlow live status, agent state, current cycle |
| Alpha Lab | `2_Alpha_Lab.py` | Tất cả alphas, filter theo setting, group by formula family |
| Theory Notebook | `3_Theory_Notebook.py` | Theories AI học được, confidence scores, tags |
| Knowledge Map | `4_Knowledge_Map.py` | ChromaDB stats, semantic search interface |
| Source Intel | `5_Source_Intel.py` | Source effectiveness analysis, gold rate per domain |

**Home page metrics:**
- Agent Status (running/stopped)
- Gold Alphas count
- Total Simulations count

---

## 6. WQB Automation — API Client

### 6.1 `wqb_automation.py`

**Authentication:**
```python
# Basic Auth → POST /authentication
# Session cookie refresh mỗi 4 giờ
creds = base64.b64encode(f"{email}:{password}".encode())
headers = {"Authorization": f"Basic {creds}"}
```

**Submit Alpha Flow:**
```python
POST /simulations  → nhận Location header (sim_url)
GET sim_url        → poll mỗi 2s → 5s
  status: "STARTED" / "RUNNING" / "COMPLETE" / "ERROR"
→ parse metrics: sharpe, fitness, turnover
→ check IS checks (self-correlation)
→ lưu vào alpha_store.db
```

**Failed combination cache:**
- Lưu formula+settings đã fail vào SQLite
- Skip ngay nếu gặp lại → tiết kiệm API calls

**Config (`wqb_config.json`):**
```json
{
  "email": "...",
  "password": "...",
  "url": "https://api.worldquantbrain.com",
  "headless": true,
  "timeout_ms": 300000
}
```
Hoặc qua env vars: `WQB_EMAIL`, `WQB_PASSWORD`, `WQB_URL`

---

## 7. Data & Storage

### 7.1 SQLite (`data/alpha_store.db`)

**Tables:**
```sql
alpha_results      — mọi simulation (formula, settings, sharpe, fitness, turnover, status)
gold_alphas        — alphas pass threshold (id, formula, settings, sharpe, fitness)
knowledge_sources  — nguồn được crawl (url, domain, type, crawled_at)
chunk_sources      — mapping chunk_id → source_id
failed_combos      — formula+settings đã fail (để skip)
simulations        — raw simulation data từ WQB API
```

### 7.2 ChromaDB

- Collection: `alpha_knowledge`
- Metadata per chunk: `source_id`, `domain`, `type`, `url`, `crawled_at`
- Embedding: `all-MiniLM-L6-v2` (local inference)

### 7.3 State Files

| File | Nội dung |
|------|----------|
| `data/research_state.json` | Daemon state: setting index, gold count, session timer |
| `theory_log.json` | Theories được AI ghi nhận |
| `gold_alphas.json` | Legacy JSON (xem mục 11 — dual source issue) |
| `RESEARCH_LOG.md` | Human-readable research log |
| `mcp_skill.md` | Hand-curated operator/field facts |

---

## 8. Deploy & CI/CD

### 8.1 Docker Compose

**Base:** DeerFlow's `docker/docker-compose.yaml`  
**Override:** `deploy/docker-compose.override.yml`

Services:
```yaml
gateway:    DeerFlow backend (port 8001, exposed to localhost only)
frontend:   DeerFlow UI (Next.js)
provisioner: disabled (LocalSandbox mode)
streamlit:  Observation dashboard (port 8080)
```

**Volume mounts:**
```yaml
# Streamlit đọc data từ VM filesystem
/app/alpha-generator/data → /app/data (read-only)
/app/alpha-generator/RESEARCH_LOG.md → /app/RESEARCH_LOG.md (read-only)

# DeerFlow load custom skills
/app/deer-flow/skills/custom → /app/skills/custom (read-only)
```

### 8.2 CI/CD (`deploy/`) 

**GitHub Actions — 2 jobs song song:**
```
Job 1: Build Dockerfile.observation → push gcr.io → deploy Cloud Run
Job 2: SSH IAP → alpha-vm → git pull → docker compose up
```

**Auth:** Workload Identity Federation (không cần service account key)  
```
Pool: projects/939562981836/.../my-github-pool
SA: deploy-sa@project-d9243352-39fe-44a5-90d.iam.gserviceaccount.com
```

**IAM Roles:**
```
roles/iam.workloadIdentityUser        ← GitHub Actions WIF
roles/iam.serviceAccountTokenCreator  ← token_format: access_token
roles/artifactregistry.writer         ← push Docker images
roles/run.admin                       ← deploy Cloud Run
roles/iam.serviceAccountUser          ← Cloud Run SA
roles/compute.admin                   ← SSH IAP to VM
```

### 8.3 VM Setup (`deploy/vm-setup.sh`)

Idempotent — chạy lại nhiều lần không hỏng:
```bash
# Cài Docker, git, Python deps
# Start MCP Server: MCP_TRANSPORT=sse python core/mcp/server.py
# Start research_daemon.py (systemd service)
# Clone DeerFlow repo, copy override config
```

### 8.4 GCP Resources

| Resource | Machine | Est. Cost |
|----------|---------|-----------|
| GCE VM alpha-vm | e2-standard-4 (4vCPU/16GB) | ~$100/tháng |
| Cloud Run alpha-obs | 2Gi RAM, 1CPU, min=0 | ~$5/tháng |
| Cloud Run GPU alpha-glm | n1-standard-4 + T4/L4, min=0 | $0 idle / $0.45/hr |
| GCS backup bucket | Standard, 30d retention | ~$1/tháng |

---

## 9. Automation Check Tools

### 9.1 `check_self_corr.py` — Kiểm tra Self-Correlation

Dùng để verify gold alphas trước khi submit lên WQB.

```bash
# Check tất cả gold alphas
python check_self_corr.py

# Check 1 alpha cụ thể
python check_self_corr.py --id abc123

# Chỉ check alphas chưa submit
python check_self_corr.py --unsubmitted

# Điều chỉnh delay giữa API calls (default 3s)
python check_self_corr.py --delay 5.0
```

**Output:**
```
===========================================================================
  SELF-CORRELATION CHECK — N gold alphas (threshold < 0.7)
===========================================================================
  [OK]  abc123  1.45  1.12  0.3421  PASS        formula name...
  [!!]  def456  1.30  1.05  0.7823  FAIL        formula name...
  [??]  ghi789  1.28  1.01    None  PENDING     formula name...

  SUMMARY: 6 PASS  |  1 FAIL (corr>=0.7)  |  1 PENDING/UNKNOWN
```

**Logic:**
- `GET /alphas/{id}` → parse `is.checks[]` array
- Tìm check với `name == "SELF_CORRELATION"`
- PASS: `result != FAIL` AND `value < 0.7`
- Retry on 429 với exponential backoff (10s, 20s, 30s...)

### 9.2 `research_batch_j.py` — Batch Research

Script chạy batch research ngoài daemon (xem file để biết chi tiết).

### 9.3 `wqb_automation.py` — Manual CLI

```python
# Dùng trực tiếp từ code
from wqb_automation import WQBAutomation, load_config

config = load_config()
bot = WQBAutomation(config)
bot.start()
bot.login()

result = bot.submit_alpha("rank(-ts_corr(est_ptp, close, 20))", "TOP3000|Subindustry|3|0.08")
print(result)

bot.stop()
```

---

## 10. Luồng Dữ Liệu End-to-End

```
① research_daemon.py khởi động
   └─ load_state() từ data/research_state.json
   └─ lấy baseline gold count từ SQLite

② call_deerflow_research(setting)
   └─ POST http://localhost:8001/api/chat/stream
   └─ Header: X-Internal-Token (bypass CSRF)
   └─ Body: Ultra mode prompt với setting cụ thể

③ DeerFlow nhận prompt → SKILL.md workflow
   └─ Step 1: alpha-wqb.get_skill_knowledge()
      └─ MCP Server → SQLite + ChromaDB query
   └─ Step 3: alpha-wqb.search_data_fields(keywords)
      └─ MCP Server → crawlers metadata
   └─ Step 5: alpha-wqb.submit_alpha(formula, settings)
      └─ MCP Server → wqb_automation.py
         └─ POST api.worldquantbrain.com/simulations
         └─ Poll until COMPLETE
         └─ Lưu kết quả → alpha_store.db

④ Nếu gold alpha:
   └─ upsert_gold_alpha() → gold_alphas table
   └─ save_theory() → theory_log.json
   └─ backup_manager.trigger() → GCS

⑤ research_daemon.py poll (mỗi 120s)
   └─ get_gold_count_in_db() tăng → rotate setting
   └─ Hoặc 1h elapsed → rotate setting
   └─ call_deerflow_research(next_setting)

⑥ Observation Dashboard (real-time)
   └─ Streamlit đọc /app/data/alpha_store.db (volume mount)
   └─ Hiển thị metrics, alphas, theories
```

---

## 11. Vấn Đề Đã Biết & Fix Priority

### CRITICAL

| ID | Vấn đề | Fix |
|----|--------|-----|
| C1 | **[ĐÃ FIX code]** IP hardcode `34.81.142.38` trong deploy.yml + docker-compose.override.yml → đổi sau stop/start (IP mới `104.199.179.72`) | deploy.yml lấy IP động + override dùng `${VM_EXTERNAL_IP}`. Còn lại: reserve static IP trên GCP. Xem `docs/adr/0002` |
| C2 | Cron overlap: nếu cycle > 6h, 2 cycles chạy đồng thời → data race SQLite | Thêm `flock -n /tmp/runner.lock` |

### HIGH

| ID | Vấn đề | Fix |
|----|--------|-----|
| H0 | **[ĐÃ FIX]** MCP `submit_alpha` chạy `_is_gold` riêng (chỉ Sharpe/Fitness/Turnover) → re-promote alpha `CORRELATED`/`FAIL_CHECKS` thành gold | Xóa verdict logic khỏi MCP tool; automation là single source of truth. Xem `docs/adr/0001` |
| H1 | MCP server docstring nói "stdio" nhưng thực tế chạy SSE | Đã sửa trong lần cập nhật này |
| H2 | vm-setup.sh pip install thiếu `chromadb`, `sentence-transformers` | Đổi thành `pip3 install -r requirements.txt` |
| H3 | Dashboard Cloud Run không có shared filesystem với VM | Giải pháp đã implement: chạy Streamlit trên VM (docker-compose.override.yml) |

### MEDIUM

| ID | Vấn đề | Fix |
|----|--------|-----|
| M1 | `gold_alphas.json` vs `gold_alphas` SQLite table — hai nguồn truth | Chọn SQLite, xóa JSON file và references |
| M2 | Dashboard không có authentication | Thêm basic auth trong Streamlit via `st.secrets` |
| M3 | Source effectiveness metric thiếu statistical significance | Đã implement Bayesian smoothing: `(gold+1)/(tested+2)` |
| M4 | RESEARCH_PROMPT hardcode 3 hypothesis families trong runner.py | Dynamic rotation từ danh sách lớn hơn |

### LOW

| ID | Vấn đề | Fix |
|----|--------|-----|
| L1 | `ALPHA_SKILLS_DIR` v1 artifact trong config.py | Xóa dead code |
| L2 | Knowledge graph trong architecture diagram nhưng chưa implement | Thêm "(skeleton)" label vào diagram |

---

## 12. Roadmap

### Phase 1 — Hoàn thiện Deploy (Hiện tại)
- [ ] Run #6: First successful Cloud Run deploy
- [ ] VM alpha-vm created + vm-setup.sh executed
- [ ] DeerFlow running với OpenRouter key
- [ ] GitHub var `VM_READY=true` → enable VM update job
- [ ] GCS backup bucket created
- [ ] Static IP cho VM (fix C1)

### Phase 2 — Sau 20 Gold Alphas
- **Knowledge Graph:** Kích hoạt `core/knowledge/graph.py` — NetworkX graph of operators/fields
- **Portfolio Construction:** Equal weight portfolio từ gold alphas, track portfolio Sharpe
- **Multi-Market:** Mở rộng sang Europe TOP1200, Asia Pacific

### Phase 3 — Autonomous Improvement
- **Auto Hypothesis từ Failure Patterns:** DeerFlow tự sinh hypothesis ngược từ fail patterns
- **Source Discovery:** Tự tìm nguồn mới từ citations trong papers
- **Weekly Reports:** PDF report tự động qua email mỗi tuần

### Phase 4 — Scale
- **Multi-LLM:** GLM-5.2 local + OpenRouter fallback, so sánh alpha quality
- **Parallel Agents:** 3 DeerFlow instances song song: momentum / mean-reversion / fundamental

---

*File này là tài liệu tham khảo chính. Cập nhật khi architecture hoặc deployment thay đổi.*
