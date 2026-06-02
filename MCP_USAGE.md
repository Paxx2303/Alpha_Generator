# Hướng dẫn sử dụng Alpha Generator MCP Server

Tài liệu này hướng dẫn cách các AI Agent (Claude, Cursor, Grok...) sử dụng **Alpha Generator MCP Server** như một công cụ chuyên nghiệp để tự động hóa nghiên cứu và tìm kiếm Alpha (Quantitative Trading Signals) trên WorldQuant Brain.

## Các Tool (Công cụ) có sẵn

### 1. Khám phá & Lên ý tưởng (Exploration & Ideation)
- **`search_data_fields`**: Khám phá các tập dữ liệu có sẵn trên WorldQuant Brain (ví dụ: gõ "sales", "sentiment" để lấy ID của các biến số cơ bản/thay thế). **Luôn chạy tool này đầu tiên nếu bạn muốn thử nghiệm một biến số lạ.**
- **`generate_hypothesis`**: Lấy ý tưởng chiến lược giao dịch (Themes) từ kho tàng kiến thức của Alpha Generator. Các theme này đã được chứng minh là có hiệu quả trên WQB (ví dụ: Mean Reversion, Statistical Arbitrage, Cross-Sectional Momentum).

### 2. `submit_alpha(formula, settings, dry_run)`
Gửi công thức alpha lên WQ Brain để chạy mô phỏng.
- `formula`: Công thức alpha (VD: `rank(ts_delta(close, 20))`).
- `settings`: Cấu hình chạy (VD: `{"universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05}`).
- `dry_run`: `True` mặc định (để an toàn). Chuyển thành `False` khi muốn gửi lên API thật.

### 3. `diagnose_alpha(metrics_json)`
Sử dụng để phân tích kết quả mô phỏng (từ `submit_alpha`) và nhận đề xuất sửa lỗi.
- Trả về danh sách các vấn đề và cách khắc phục (ví dụ: "HIGH_TURNOVER" -> "Increase Decay").

### 4. `list_gold_alphas(limit, min_sharpe)`
Lấy danh sách các Alpha xuất sắc đã được tìm thấy trước đây.
- Sử dụng công cụ này để tìm cảm hứng hoặc làm nền tảng cho việc tiến hóa (mutation).

### 5. `mutate_from_gold(base_formula, n)`
Sử dụng **Evolutionary Engine** để tạo ra các biến thể mới từ một công thức alpha.
- Nó sẽ tự động thay đổi lookback period, đổi dấu, thay toán tử, v.v. để tìm các phiên bản tốt hơn.

### 6. `run_research_cycle(goal, max_cycles, theme_focus)`
Kích hoạt agent nội bộ để nó tự động chạy vòng lặp tìm kiếm. Nó sẽ tự tạo hypothesis, submit, diagnose và lặp lại cho đến khi tìm được alpha tốt hoặc hết số lượt `max_cycles`.

---

## Ví dụ Quy trình hoạt động (Workflow) cho Agent

**Bước 1:** Khởi tạo ý tưởng
```python
# Gọi tool
generate_hypothesis(theme="mean_reversion")
```

**Bước 2:** Chạy thử nghiệm (Submit)
```python
# Gửi lên WorldQuant Brain
submit_alpha(
    formula="-rank(ts_mean(returns, 5))", 
    settings={"universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05},
    dry_run=False
)
```

**Bước 3:** Chẩn đoán lỗi nếu kết quả không tốt
```python
# Dùng kết quả trả về từ submit_alpha
diagnose_alpha(metrics_json='{"sharpe": 0.8, "turnover": 150}')
# Sẽ nhận được lời khuyên: "Turnover > 70. Increase Decay"
```

**Bước 4:** Lấy cảm hứng từ Gold Alphas và Tiến hóa
```python
list_gold_alphas(min_sharpe=1.5)
mutate_from_gold(base_formula="rank(ts_delta(close, 20))", n=3)
```

> [!TIP]
> Sử dụng `run_research_cycle` khi muốn giao phó toàn bộ quá trình research cho server, bạn chỉ cần ngồi đợi kết quả trả về!
