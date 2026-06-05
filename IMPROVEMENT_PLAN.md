# Alpha_Generator - Detailed Improvement Plan

**Mục tiêu cuối cùng:**  
Chuyển project thành **một MCP Tool mạnh và chuyên nghiệp** để các Agent (Claude, Cursor, Grok, v.v.) có thể sử dụng như một skill cao cấp để nghiên cứu, tạo, tối ưu và submit Alpha trên WorldQuant Brain.

---

## Tổng quan các vấn đề hiện tại

### 1. MCP Server (Quan trọng nhất)
- Nhiều tool quan trọng chưa được expose.
- `_save_gold_alpha` chưa implement.
- Chưa có autonomous research cycle.
- Error handling và logging yếu.

### 2. Core Automation (`wqb_automation.py`)
- Error handling chưa robust.
- Không có retry mechanism.
- Chưa tự động refresh session khi expire.

### 3. Alpha Agent (`alpha_agent.py`)
- Code bị truncate ở một số hàm.
- Chưa có evolutionary mutation từ Gold Alphas.
- Chưa kết nối chặt chẽ với MCP.

### 4. Khác
- Thiếu logging hệ thống.
- Chưa integrate Stock Pipeline.
- Documentation cho MCP chưa tốt.

---

## IMPROVEMENT PLAN - CHI TIẾT THEO PHASE

### **Phase 0: Chuẩn bị (1-2 giờ)**

1. Cài đặt logging chuyên nghiệp
   ```bash
   pip install structlog rich python-dotenv
   ```

2. Tạo file `.env.example` và `.env`
   ```env
   WQB_EMAIL=your_email@gmail.com
   WQB_PASSWORD=your_password
   LOG_LEVEL=INFO
   MAX_SIMULATIONS_PER_DAY=150
   ```

3. Tạo thư mục logs và gold_alphas nếu chưa có.

---

### **Phase 1: Critical Fixes (1-2 ngày)**

**1.1 Cải thiện `wqb_automation.py`**
- Thêm decorator `@retry_with_backoff`
- Thêm logging structlog
- Implement `refresh_login_if_needed()`
- Thêm `save_raw_response()` cho debug
- Tối ưu polling simulation result

**1.2 Hoàn thiện `alpha_agent.py`**
- Merge/complete hàm `select_best_variant`, `evolve_hypothesis`
- Implement `_save_gold_alpha(formula, metrics, theme, score)`
- Thêm mutation engine (mutate parameters, add regime filters, change operators)

**1.3 Nâng cấp `mcp_server.py`**

Thêm các tools sau (bắt buộc):

```python
@mcp.tool()
async def generate_hypothesis(theme: str = None, avoid_themes: list = None) -> dict

@mcp.tool()
async def submit_alpha(formula: str, settings: dict, dry_run: bool = True) -> dict

<!-- @mcp.tool()
async def diagnose_alpha(alpha_id: str) -> dict
# TODO: diagnose_alpha tool — chưa implement -->

@mcp.tool()
async def list_gold_alphas(limit: int = 20, min_sharpe: float = 0.0) -> list

@mcp.tool()
async def run_research_cycle(goal: str, max_cycles: int = 10, theme_focus: str = None) -> dict

@mcp.tool()
async def mutate_from_gold(base_formula: str = None, n: int = 5) -> list
```

---

### **Phase 2: Skill Enhancement (3-5 ngày)**

**2.1 Evolutionary Intelligence (✅ COMPLETED)**
- Đã tạo module `evolution` ngay trong `alpha_agent.py`:
  - Thêm Genetic-style mutation (thay đổi rank, neutralization, toán tử, sign flip).
  - Thêm Crossover (`mutate_crossover`) giữa các gold alphas.
  - Thêm Parameter noise (`mutate_parameters`) để tự động tìm thông số tối ưu.
- Đã expose toàn bộ dưới dạng MCP Tools: `mutate_from_gold`, `mutate_crossover_from_gold`, `mutate_parameters_from_gold`.

**2.2 Stock Pipeline Integration**
- Tạo tool: `analyze_market_condition()` → gợi ý theme mạnh hiện tại
- Kết nối với `stock_pipeline/` để generate idea từ top performing stocks

**2.3 Advanced Diagnosis Engine**
- Phân tích:
  - Yearly Sharpe stability
  - Drawdown analysis
  - Regime performance (bull/bear/volatility)
  - Correlation với các gold alphas khác

**2.4 Knowledge Base Self-Improvement**
- Sau mỗi cycle thành công → tự động update `Skill.md`

---

### **Phase 3: Production & Usability (3-4 ngày)**

1. **Rate Limiting & Safety**
   - Giới hạn số simulation/ngày
   - Dry-run mode mặc định
   - Confirmation trước khi submit thật

2. **State Management**
   - Lưu session, gold_alphas, knowledge trong SQLite hoặc JSON

3. **Documentation**
   - Viết `MCP_USAGE.md` chi tiết cách Claude sử dụng tool này
   - Ví dụ prompt cho Agent

4. **Testing**
   - Viết unit test cho core functions
   - Integration test cho MCP tools

---

### **Phase 4: Nice-to-have (sau khi ổn định)**

- Web Dashboard (Streamlit/FastAPI)
- Alpha ranking & comparison
- Auto submit mode (với confirmation)
- Export alpha package (formula + settings + report)

---

## Ưu tiên thực hiện ngay (Next 48 hours)

1. Phase 1.1 → Fix `wqb_automation.py` (robustness)
2. Phase 1.2 → Hoàn thiện `alpha_agent.py` + `_save_gold_alpha`
3. Phase 1.3 → Update `mcp_server.py` với đầy đủ tools
4. Test MCP connection với Claude

---

## Tiêu chí hoàn thành MCP Tool "Mạnh"

- Agent có thể gọi `run_research_cycle("Tạo alpha Sharpe > 1.8 trên US stocks", max_cycles=20)` và chạy autonomous.
- Có cơ chế học hỏi từ gold alphas.
- Error handling tốt, ít crash.
- Logging rõ ràng để debug.
- Dễ dàng extend thêm skills mới.
