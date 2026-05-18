# 🧠 WorldQuant Brain Alpha System
> Hệ thống tự động cào dữ liệu, phân tích và tạo Alpha trên WorldQuant Brain  
> **Tech Stack:** Python 3.12 · Hermes Agent (NousResearch) · DeerFlow 2.0 (ByteDance) · LangGraph · Claude API · Docker

---

## 📌 Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                  WorldQuant Brain Platform                      │
│            platform.worldquantbrain.com (External)             │
└──────────────────┬────────────────────┬────────────────────────┘
                   │ Submit & Test       │ Scrape & Auth
┌──────────────────▼────────────────────────────────────────────┐
│                     API & Session Layer                        │
│  WQ-Brain (RussellDash332) · wq_new (TonyMa1) · Brainiac     │
└───────────┬────────────────────────────────┬──────────────────┘
            │                                │
┌───────────▼────────────────────┐  ┌────────▼──────────────────┐
│   DeerFlow 2.0 (ByteDance)     │◄►│  Hermes Agent (NousResearch)│
│  Planner·Researcher·Coder      │  │  Skills·Memory·MCP·Gateway │
└───────────┬────────────────────┘  └────────┬──────────────────┘
            │                               │
┌───────────▼───────────────────────────────▼───────────────────┐
│                   Alpha Pipeline (Python Core)                 │
│  [Scraper] → [Analyzer] → [Knowledge Base RAG] → [Generator]  │
└──────────────────────────────────┬────────────────────────────┘
                                   │
┌──────────────────────────────────▼────────────────────────────┐
│              Submission & Validation Layer                     │
│  [Validator] → [Simulator] → [Quality Gate] → [Auto Submit]   │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔬 Phân tích Open-Source Repos tích hợp

### 1. `RussellDash332/WQ-Brain` — Nền tảng API
**GitHub:** https://github.com/RussellDash332/WQ-Brain  
**Nguồn gốc:** Fork từ `AbnerTeng/WorldQuant-Brain`  
**Vai trò trong hệ thống:** WQ API Client base, session management, multi-thread logging

```python
# Tích hợp làm session & submit layer
from wq_brain.main import WQSession, AlphaSubmitter

session = WQSession(username, password)
submitter = AlphaSubmitter(session)
result = submitter.submit(alpha_expression)
```

Điểm mạnh: Xử lý auth session cookie tốt, multi-thread submission với ThreadPoolExecutor, CSV logging và rate limiting tuân thủ WQ daily limits.

---

### 2. `TonyMa1/wq_new` — Toolkit hoàn chỉnh nhất
**GitHub:** https://github.com/TonyMa1/wq_new  
**Vai trò:** Core alpha generator toolkit, clean modular architecture

```python
from alpha_gen.api.wq_client import WorldQuantClient
from alpha_gen.api.ai_client import AIClient
from alpha_gen.core.alpha_generator import AlphaGenerator

wq_client = WorldQuantClient(username, password)
ai_client = AIClient(api_key, model="claude-sonnet-4-20250514")
generator = AlphaGenerator(wq_client, ai_client)

alphas = generator.generate_expressions(
    region='USA', universe='TOP3000',
    strategy_type='momentum', count=5
)
# Refine alpha kém
refined = generator.polish_alphas(alphas, requirements="Reduce turnover, improve IR")
```

Điểm mạnh: Clean separation of concerns, unified API cho WQ + AI (OpenRouter compatible), có `mine_expressions` để khai thác biến thể từ expression gốc.

---

### 3. `zhutoutoutousan/worldquant-miner` — Miner đầy đủ nhất
**GitHub:** https://github.com/zhutoutoutousan/worldquant-miner  
**Vai trò:** Scraper + Generator + Genetic Evolution

Generation 2 features tích hợp vào hệ thống:

```
generation_two/
├── core/template_generator.py       ← Template-based generation engine
├── core/simulator_tester.py         ← Simulation runner & monitoring
├── core/expression_compiler.py      ← Multi-stage syntax validator
├── evolution/alpha_evolution_engine.py  ← Genetic algorithm evolution
├── evolution/self_optimizer.py      ← Adaptive parameter tuning
└── storage/backtest_storage.py      ← SQLite storage layer
```

---

### 4. `jdhruv1503/Brainiac` — RAG + Agentic Alpha
**GitHub:** https://github.com/jdhruv1503/Brainiac  
**Vai trò:** Pipeline đọc research papers → tạo alpha qua RAG

```
AlphaGenerator/ResearchPDFs/   ← Dump sách/papers vào đây
AlphaGenerator/Strategies/    ← Text strategy descriptions
Simulation/main.py             ← WQ backtest API (từ RussellDash332)
```

Tích hợp: Dùng LlamaParse parse PDF → LangChain RAG → alpha expression. Thay LlamaParse bằng PyPDF + Anthropic embeddings để không cần API key thêm.

---

### 5. `Harvey-Sun/World_Quant_Alphas` — 101 Alpha Baseline
**GitHub:** https://github.com/Harvey-Sun/World_Quant_Alphas  
**Vai trò:** Implement 101 formulaic alphas chuẩn làm template library và benchmark.

---

## 🤖 Tích hợp Hermes Agent

**Hermes** (NousResearch, MIT license, phát hành 2026) là backbone agent học từ kinh nghiệm.

### Vai trò của Hermes

Hermes hoạt động như bộ não trung tâm tự cải thiện theo thời gian:

- **Skills system** — Tự tạo skill files sau mỗi task thành công: "how to write momentum alpha", "what operators work for mean-reversion"
- **Persistent memory** — Nhớ qua sessions: alpha nào fail, pattern nào work, market regime nào đang active
- **Tool calling** — Gọi WQ API, đọc DB, chạy Python code, query knowledge base
- **MCP support** — Connect tới external tools (WQ Brain MCP server tự build)
- **Multi-platform gateway** — Nhận lệnh qua Telegram/Discord trong khi chạy trên VPS

### Cài đặt Hermes

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes setup   # Wizard cấu hình provider
hermes model   # Switch sang claude-sonnet-4-20250514
```

### Cấu hình Hermes cho WQ Alpha

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  wq-alpha:
    command: python
    args: ["-m", "wq_mcp_server"]
    env:
      WQ_USERNAME: "${WQ_USERNAME}"
      WQ_PASSWORD: "${WQ_PASSWORD}"
```

### Hermes Skill tự động tạo (ví dụ)

```markdown
# skills/momentum_alpha.md
## When to use
Khi cần tạo alpha momentum ngắn hạn (5-20 ngày lookback)

## Best practices
- Dùng ts_mean(returns, d) với d trong [5, 10, 20]
- Wrap bằng rank() để normalize cross-sectional
- Luôn thêm neutralization INDUSTRY
- Tránh look-ahead bias: không dùng future data

## Proven templates
rank(ts_mean(returns, 5)) * (-1)
rank(ts_mean(close/ts_mean(close, 20) - 1, 5))

## Known failures
- window < 3: Sharpe < 1.0 (quá noisy)
- Thiếu neutralize: high sector correlation → rejected
- Turnover > 80%: bị filter ngay vòng quality gate
```

---

## 🦌 Tích hợp DeerFlow 2.0

**DeerFlow** (ByteDance, MIT license) xử lý deep research và multi-agent task decomposition.

### Vai trò của DeerFlow

DeerFlow là research engine, xử lý các task phức tạp cần nhiều bước:

- **Coordinator** — Nhận high-level task, điều phối sub-agents
- **Planner** — Phân chia task thành parallel subtasks
- **Researcher** — Web search + crawl papers + query knowledge base
- **Coder** — Viết và chạy Python code trong Docker sandbox
- **Reporter** — Tổng hợp kết quả thành report/JSON

### Cài đặt DeerFlow

```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
make docker-init   # Pull sandbox image (một lần)
make docker-start  # Start services
```

### DeerFlow tasks trong hệ thống

```python
# Task 1: Research alpha ideas từ literature và web
deerflow.run("""
Tìm 5 alpha ideas mới từ papers gần đây về momentum trong thị trường châu Á.
Cho mỗi idea: rationale, operators WQ cần dùng, expected Sharpe.
Output: JSON list
""")

# Task 2: Phân tích failure patterns từ DB
deerflow.run("""
Đọc file alpha_store.db. Phân tích:
1. Alphas Sharpe < 1.0: pattern chung là gì?
2. Alphas approved: operators nào xuất hiện nhiều nhất?
Output: Markdown report với actionable insights.
""")

# Task 3: Tổng hợp kiến thức về data field mới
deerflow.run("""
Tìm cách sử dụng data field 'adv20' (average daily volume 20d) trong WQ Brain.
Tổng hợp: các alpha patterns dùng volume, so sánh hiệu quả.
""")
```

---

## 📚 Knowledge Base — Hermes học từ đây

Phần cốt lõi giúp Hermes tạo và phân tích alpha đúng/sai theo thời gian.

### Cấu trúc Knowledge Base

```
knowledge_base/
├── books/
│   ├── finding_alphas_2ed.pdf          ← WorldQuant CEO (2020) — QUAN TRỌNG NHẤT
│   ├── quantitative_trading_chan.pdf    ← Ernest Chan
│   ├── advances_in_fin_ml_prado.pdf    ← Marcos Lopez de Prado
│   └── 101_formulaic_alphas.pdf        ← Zura Kakushadze (template library)
│
├── wq_official/
│   ├── operator_reference.md           ← WQ Fast Expression operators đầy đủ
│   ├── data_fields_catalog.json        ← Tất cả data fields WQ (scrape từ platform)
│   ├── alpha_lifecycle_guide.md        ← Quy trình idea → approved
│   └── competition_rules.md           ← Rules WQ Brain
│
├── research_papers/
│   ├── momentum/                       ← Jegadeesh & Titman, Carhart...
│   ├── mean_reversion/                 ← DeBondt & Thaler, reversal effects
│   ├── fundamental/                    ← Piotroski F-score, earnings quality
│   ├── alternative_data/               ← News sentiment, social media signals
│   └── machine_learning/              ← ML factors, feature importance
│
├── alpha_history/
│   ├── approved_alphas.json           ← Alphas WQ đã approve
│   ├── rejected_reasons.json          ← Lý do reject + pattern tổng hợp
│   └── performance_log.json           ← Lịch sử Sharpe/Fitness theo thời gian
│
└── lessons_learned/
    ├── what_works.md                  ← Patterns thành công đã kiểm chứng
    ├── what_fails.md                  ← Lỗi thường gặp và cách tránh
    └── market_regime_notes.md         ← Ghi chú khi thị trường thay đổi chế độ
```

### Tài liệu cốt lõi Hermes cần học

| Tài liệu | Nội dung chính | Hermes học được gì |
|-----------|----------------|-------------------|
| **Finding Alphas** (Tulchinsky 2020) | Alpha design từ WQ practitioners, backtesting, diversity | Cách tư duy alpha, các loại bias cần tránh, alpha diversity |
| **Quantitative Trading** (E. Chan) | Build algo trading từ đầu, execution, risk | Position sizing, Sharpe interpretation, practical pitfalls |
| **Advances in Fin ML** (de Prado) | Purged CV, meta-labeling, feature importance | Tránh data leakage, evaluate alpha đúng cách |
| **101 Formulaic Alphas** (Kakushadze) | 101 alpha expressions WQ-ready | Template patterns, operator combinations |
| WQ Operator Reference | ts_mean, rank, zscore, ts_corr... | Syntax chính xác, khi nào dùng gì |
| Alpha History DB | Lịch sử thành công/thất bại | Feedback loop để không lặp lỗi cũ |

### RAG Pipeline

```python
# knowledge_base/rag_loader.py
from langchain_community.vectorstores import Chroma
from langchain_anthropic import AnthropicEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class WQKnowledgeBase:
    def __init__(self):
        self.embeddings = AnthropicEmbeddings()
        self.vectorstore = Chroma(
            collection_name="wq_alpha_knowledge",
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
    
    def load_pdf(self, path: str, source_tag: str):
        docs = PyPDFLoader(path).load_and_split(self.splitter)
        for doc in docs:
            doc.metadata["source"] = source_tag
        self.vectorstore.add_documents(docs)
        print(f"Loaded {len(docs)} chunks from {source_tag}")
    
    def load_all(self):
        sources = {
            "books/finding_alphas_2ed.pdf": "finding_alphas",
            "books/101_formulaic_alphas.pdf": "101_alphas",
            "wq_official/operator_reference.md": "wq_operators",
        }
        for path, tag in sources.items():
            self.load_pdf(path, tag)
    
    def get_alpha_context(self, strategy_type: str, n: int = 5) -> str:
        """Lấy context để generate alpha theo chiến lược"""
        query = f"WorldQuant alpha expression {strategy_type} strategy operators"
        docs = self.vectorstore.similarity_search(query, k=n)
        return "\n\n---\n\n".join(d.page_content for d in docs)
    
    def get_failure_context(self) -> str:
        """Lấy context về các lỗi thường gặp"""
        query = "alpha rejection reasons low Sharpe high turnover correlation"
        docs = self.vectorstore.similarity_search(query, k=3)
        return "\n\n".join(d.page_content for d in docs)
```

### Hermes cập nhật memory sau mỗi simulation

```python
def record_and_learn(expression: str, metrics: dict, status: str):
    """Sau mỗi simulation: lưu vào DB và update Hermes memory"""
    
    # 1. Lưu vào SQLite
    db.insert_alpha(expression, metrics, status)
    
    # 2. Phân tích bài học
    lesson = analyze_lesson(expression, metrics, status)
    
    # 3. Update Hermes persistent memory
    hermes.remember(f"""
    Alpha tested: {expression}
    Result: {status}
    Sharpe={metrics['sharpe']:.2f}, Fitness={metrics['fitness']:.2f}
    Turnover={metrics['turnover']:.1%}
    Lesson: {lesson}
    Operators used: {extract_operators(expression)}
    """)
    
    # 4. Nếu fail, thêm vào "what_fails.md"
    if status in ["low_sharpe", "high_correlation", "rejected"]:
        append_lesson("lessons_learned/what_fails.md", lesson)
    elif status == "approved":
        append_lesson("lessons_learned/what_works.md", lesson)
```

---

## 🏗️ Cấu trúc dự án đầy đủ

```
wq-alpha-system/
│
├── config/
│   ├── settings.yaml           # Cấu hình chung (ngưỡng, schedule)
│   ├── .env                    # Credentials — KHÔNG commit git
│   └── alpha_config.yaml       # Alpha parameters (region, universe...)
│
├── api_layer/                  # Layer 1: WQ API Integration
│   ├── wq_client.py            # Từ TonyMa1/wq_new (refactored)
│   ├── session_manager.py      # Từ RussellDash332/WQ-Brain
│   └── rate_limiter.py         # Đảm bảo không vượt WQ limits
│
├── orchestration/              # Layer 2: Agent Orchestration
│   ├── hermes_bridge.py        # Python ↔ Hermes Agent
│   ├── deerflow_bridge.py      # Python ↔ DeerFlow
│   └── task_router.py          # Phân loại task → đúng agent
│
├── pipeline/                   # Layer 3: Core Pipeline
│   ├── scraper/
│   │   ├── wq_scraper.py       # Cào alpha, leaderboard WQ
│   │   └── paper_scraper.py    # Cào research papers (DeerFlow)
│   ├── analyzer/
│   │   ├── alpha_analyzer.py   # Phân tích Sharpe/Fitness/Turnover
│   │   ├── pattern_finder.py   # Clustering, pattern recognition
│   │   └── correlation_check.py # Self-correlation với alphas hiện có
│   ├── generator/
│   │   ├── template_engine.py  # Từ worldquant-miner Gen2
│   │   ├── llm_generator.py    # Claude API qua Hermes
│   │   ├── genetic_engine.py   # Alpha evolution engine
│   │   └── expression_validator.py  # WQ syntax check
│   └── submission/
│       ├── simulator.py        # WQ backtest API
│       ├── quality_gate.py     # Sharpe/Fitness threshold check
│       └── auto_submit.py      # Daily limit safe submit
│
├── knowledge_base/             # Layer 4: RAG Knowledge
│   ├── books/                  # PDFs: Finding Alphas, etc.
│   ├── wq_official/            # WQ docs, operator reference
│   ├── research_papers/        # Academic papers
│   ├── alpha_history/          # Lịch sử alpha (JSON)
│   ├── lessons_learned/        # What works / what fails
│   ├── rag_loader.py           # Load docs → ChromaDB
│   └── rag_query.py            # Query context cho LLM
│
├── database/
│   ├── alpha_store.db          # SQLite: tất cả alphas + metrics
│   └── performance_log.db      # Log hiệu suất theo ngày
│
├── skills/                     # Hermes skill files (auto-generated)
│   ├── momentum_alpha.md
│   ├── mean_reversion_alpha.md
│   └── backtest_analysis.md
│
├── frontend/                   # React monitor UI
├── api_layer/
│   └── monitor_api.py          # FastAPI monitor backend + static serving
│
├── main.py                     # Entry point + scheduler
└── requirements.txt
```

---

## ⚙️ Tech Stack

```yaml
core:
  language: Python 3.12
  package_manager: uv

agent_framework:
  primary: Hermes Agent (NousResearch, MIT)   # Self-improving, MCP, memory
  research: DeerFlow 2.0 (ByteDance, MIT)    # Deep research, multi-agent
  orchestration: LangGraph + LangChain

llm_backends:
  primary: claude-sonnet-4-20250514           # Anthropic API
  fallback: OpenRouter (200+ models)
  local: Ollama + Hermes-3 (GPU recommended)

worldquant_repos:
  api_base: RussellDash332/WQ-Brain
  toolkit: TonyMa1/wq_new
  miner: zhutoutoutousan/worldquant-miner (Gen2)
  rag_agent: jdhruv1503/Brainiac
  baseline: Harvey-Sun/World_Quant_Alphas

storage:
  vector: ChromaDB (RAG + Hermes memory)
  relational: SQLite (alpha history, logs)
  documents: PyPDF + LangChain text splitter

monitoring:
  dashboard: React + FastAPI
  scheduling: schedule + cron
  notifications: Telegram (Hermes gateway)

execution:
  sandbox: Docker (DeerFlow requirement)
  deployment: VPS $5/mo hoặc local machine
```

---

## 🔄 Daily Pipeline

```
06:00  [DeerFlow]  Research: crawl papers mới, news, WQ leaderboard
07:00  [Analyzer]  Phân tích alpha trong DB, tìm patterns hôm nay
08:00  [Hermes]    Query knowledge base → build context → prompt Claude
08:30  [Generator] Tạo batch 20 alpha: LLM (10) + Template (5) + Genetic (5)
09:00  [Validator] Syntax check toàn bộ batch
09:30  [Simulator] Submit lên WQ Brain để backtest
10:30  [QualityGate] Filter: Sharpe>1.5, Fitness>1.0, Turnover 1%-70%
11:00  [Submit]    Nộp alpha đạt ngưỡng (max 3-5/ngày để an toàn)
11:30  [Hermes]    Cập nhật memory + skill files từ kết quả hôm nay
12:00  [Dashboard] Daily summary report
```

---

## 📊 Ngưỡng chất lượng Alpha

| Chỉ số | Tối thiểu | Tốt |
|--------|----------|-----|
| Sharpe | > 1.5 | > 2.0 |
| Fitness | > 1.0 | > 1.5 |
| Returns | > 5%/năm | > 10% |
| Turnover | 1% - 70% | 5% - 40% |
| Drawdown | < 30% | < 20% |
| Self-correlation | < 0.7 | < 0.5 |

---

## ⚠️ Lưu ý quan trọng

**WQ Rate Limits:** Simulation có giới hạn/ngày. Khuyến nghị max 3-5 submit/ngày. Delay ≥ 2s giữa API calls.

**Terms of Service:** Đọc kỹ ToS WQ Brain. Không spam simulation. Không redistribute alpha của người khác.

**Bảo mật:** Tất cả credentials trong `.env`, thêm vào `.gitignore` ngay từ đầu.

---

## 🗺️ Roadmap

| Phase | Mục tiêu | Tuần |
|-------|---------|------|
| 1 | API layer + WQ session (RussellDash332 + wq_new) | 1-2 |
| 2 | Knowledge Base + ChromaDB + RAG loader | 3-4 |
| 3 | Hermes Agent setup + WQ skills | 5-6 |
| 4 | Template + LLM generator | 7-8 |
| 5 | DeerFlow integration + research pipeline | 9-10 |
| 6 | Genetic algorithm + Auto-submit | 11-12 |
| 7 | Dashboard + Scheduler + Self-improvement loop | 13-14 |

---

## 🚀 Quick Start

```bash
# 1. Cài Hermes Agent
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes setup

# 2. Cài DeerFlow
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow && make docker-init && make docker-start

# 3. Setup project
git clone https://github.com/yourname/wq-alpha-system
cd wq-alpha-system
pip install -r requirements.txt
cp .env.example .env   # Điền credentials

# 4. Load knowledge base
python -m knowledge_base.rag_loader --load-all

# 5. Test pipeline
python main.py --run-once --dry-run

# 6. Chạy dashboard
python main.py --serve-ui

# 7. Auto schedule
python main.py --schedule
```

---

*Tài liệu này là bản sống — cập nhật khi hệ thống phát triển. Mỗi module sẽ có README chi tiết khi implement.*
