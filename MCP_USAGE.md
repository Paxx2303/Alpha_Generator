# Hướng dẫn sử dụng Alpha Generator MCP Server

Tài liệu này hướng dẫn cách các AI Agent (Claude, Cursor, Grok...) sử dụng **Alpha Generator MCP Server** như một công cụ chuyên nghiệp để tự động hóa nghiên cứu và tìm kiếm Alpha (Quantitative Trading Signals) trên WorldQuant Brain.

## ⚠️ STARTUP - Call This First!

**BEFORE doing anything else**, call this tool to load domain knowledge:

```python
get_skill_knowledge()
```

This returns the complete `mcp_skill.md` containing all rules, operators, IQC criteria, and examples. **This is mandatory** — you'll make bad alphas without this knowledge!

---

## Các Tool (Công cụ) có sẵn

### 0. Knowledge & Setup (LOAD THIS FIRST!)
- **`get_skill_knowledge()`**: ⭐ **CALL THIS AT STARTUP** — Returns complete mcp_skill.md with:
  - Valid/broken operators reference
  - IQC criteria (Sharpe ≥ 1.25, Fitness ≥ 1.0)
  - Advanced optimization techniques
  - Proven settings grid
  - Examples of high-quality alphas
  - This is the single source of truth for domain knowledge!

### 1. Khám phá & Lên ý tưởng (Exploration & Ideation)

### 1. Khám phá & Lên ý tưởng (Exploration & Ideation)
- **`search_data_fields(query, limit)`**: Khám phá các tập dữ liệu có sẵn trên WorldQuant Brain (ví dụ: gõ "sales", "sentiment" để lấy ID của các biến số cơ bản/thay thế). **Luôn chạy tool này đầu tiên nếu bạn muốn thử nghiệm một biến số lạ.**
- **`search_knowledge_base(query, top_k)`**: Tìm kiếm các bài báo khoa học và lý thuyết tài chính định lượng trong kho dữ liệu (JSON) để làm cơ sở (rationale) cho Alpha. Tránh việc sinh công thức theo kiểu khớp đường cong (curve-fitting).
- **`generate_hypothesis(theme)`**: Lấy ý tưởng chiến lược giao dịch từ kho tàng kiến thức nội bộ.

### 2. Mô phỏng & Chẩn đoán (Simulation & Diagnosis)
- **`submit_alpha(formula, settings, dry_run)`**: Gửi công thức alpha lên WQ Brain để chạy mô phỏng.
  - `formula`: Công thức alpha (VD: `rank(ts_delta(close, 20))`).
  - `settings`: Cấu hình chạy (VD: `{"universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05}`).
  - `dry_run`: `True` mặc định (để an toàn). Chuyển thành `False` khi muốn gửi lên API thật.
<!-- - **`diagnose_alpha(metrics_json)`**: Sử dụng để phân tích kết quả mô phỏng (từ `submit_alpha`) và nhận đề xuất sửa lỗi (VD: "HIGH_TURNOVER -> Increase Decay").
  - TODO: diagnose_alpha tool — chưa implement -->

### 3. Tiến hóa Alpha (Evolution)
- **`list_gold_alphas(limit, min_sharpe)`**: Lấy danh sách các Alpha xuất sắc đã được tìm thấy trước đây.
- **`mutate_from_gold(base_formula, n)`**: Sử dụng Evolutionary Engine để tạo ra các biến thể mới từ một công thức alpha.

---

## Ví dụ Quy trình hoạt động (Workflow) cho Agent

**Bước 0:** Load skill knowledge (MANDATORY!)
```python
get_skill_knowledge()
# Lưu toàn bộ nội dung này vào context của bạn!
```

**Bước 1:** Đọc lý thuyết (Bắt buộc)
```python
search_knowledge_base(query="mean reversion volatility")
# Trích xuất được insight: Cần chuẩn hóa biến động (Vol-normalized)
```

**Bước 2:** Chạy thử nghiệm (Submit)
```python
# Gửi lên WorldQuant Brain
submit_alpha(
    formula="-group_rank(ts_delta(close, 5) / (ts_std_dev(returns, 20) + 0.001), subindustry)", 
    settings={"universe": "TOP1000", "neutralization": "Market", "decay": 0, "truncation": 0.05},
    dry_run=False
)
```

**Bước 3:** Lấy cảm hứng từ Gold Alphas và Tiến hóa
```python
list_gold_alphas(min_sharpe=1.5)
mutate_from_gold(base_formula="rank(ts_delta(close, 20))", n=3)
```

<!-- **Chẩn đoán lỗi nếu kết quả không tốt** (TODO: diagnose_alpha — chưa implement)
```python
diagnose_alpha(metrics_json='{"sharpe": 0.8, "turnover": 150}')
# Sẽ nhận được lời khuyên: "Turnover > 70. Increase Decay"
``` -->

> [!TIP]
> Hệ thống này được thiết kế để AI là người ra quyết định chính (Interactive Quant Researcher). Hãy chủ động phân tích thay vì phó mặc cho vòng lặp!
