# Bàn giao công việc (WORK.md)

Tài liệu này được tạo ra để bàn giao trạng thái hiện tại của dự án **Alpha Generator MCP** cho các Agent kế thừa trong tương lai. Xin hãy đọc kỹ tài liệu này trước khi tiếp tục công việc.

## 1. Tổng quan Dự án
Alpha Generator là một hệ thống tự động hóa (Auto-Quant Workflow) kết hợp giữa trí tuệ nhân tạo (LLM Agent) và API của WorldQuant Brain. Hệ thống hoạt động như một **MCP Server**, cung cấp các công cụ cho các Agent để nghiên cứu, sinh ý tưởng, mô phỏng (simulate), chẩn đoán lỗi, và tiến hóa (mutate) các công thức Quantitative Trading Signals (Alphas).

## 2. Trạng thái Hiện tại (Tính đến Tháng 6/2026)

Hệ thống Core đã hoạt động ổn định và cực kỳ mượt mà.

### Các thành phần đã hoàn thiện:
- **`wqb_automation.py`**: Tự động hóa đăng nhập API và gửi/nhận kết quả mô phỏng từ WorldQuant Brain. Đã hỗ trợ xử lý lỗi, retry mechanism, và tự động refresh session.
- **`alpha_agent.py`**: Chứa logic chẩn đoán lỗi alpha (Diagnose) và bộ máy tiến hóa (Evolutionary Engine - lai ghép, đột biến tham số).
- **`mcp_server.py`**: Expose đầy đủ các tool quan trọng cho Agent (`generate_hypothesis`, `submit_alpha`, ~~`diagnose_alpha`~~, `search_knowledge_base`, `search_data_fields`, `mutate_from_gold`...).
  - <!-- TODO: diagnose_alpha tool — chưa implement -->
- Hệ thống đã có khả năng tự động phân loại và lưu trữ các Alpha đạt chuẩn (Sharpe >= 1.25, Fitness >= 1.0) vào file `wqb_logs/gold_alphas.json`.

### 🏆 Thành tựu nổi bật:
Hệ thống đã tự động tìm ra **1 Gold Alpha (V10)** vượt chuẩn gắt gao của WorldQuant:
- **Công thức:**
  ```javascript
  lookback = 5;
  volatility = ts_std_dev(returns, 20);
  price_signal = -ts_delta(close, lookback) / (volatility + 0.001);
  volume_signal = volume / adv20;
  signal = rank(price_signal) * rank(volume_signal);
  rank(signal)
  ```
- **Cấu hình:** `Universe: TOP3000 | Neutralization: Subindustry | Decay: 30 | Truncation: 0.05`
- **Kết quả:** Sharpe: 1.28 | Fitness: 1.02 | Turnover: 0.1633 | Drawdown: 0.0857

## 3. Các bước tiếp theo cần làm (Next Steps)
Căn cứ vào `IMPROVEMENT_PLAN.md`, dự án đang ở giữa **Phase 2**, và đây là các công việc cần tiếp tục triển khai:

1. **Market Condition & Stock Pipeline (Phase 2.2):**
   - Viết thêm tool `analyze_market_condition()` cho MCP.
   - Mục đích: Phân tích xu hướng thị trường hiện tại (ví dụ: đang bull, bear, hay biến động) hoặc nhóm ngành nào đang dẫn dắt để hệ thống tự động sinh ý tưởng có chủ đích thay vì sinh ngẫu nhiên.
   
2. **Advanced Diagnosis Engine (Phase 2.3):**
   - Nâng cấp hàm `diagnose()` trong `alpha_agent.py`. Hiện tại hàm này chỉ phân tích cơ bản (Turnover, Sharpe).
   - Cần phân tích sâu hơn: Drawdown analysis, Yearly Sharpe stability, và Regime performance.

3. **Production & Usability (Phase 3):**
   - Chuyển đổi quản lý state từ file JSON thô sang SQLite hoặc hệ thống quản lý session tốt hơn.
   - (Tùy chọn) Xây dựng Web Dashboard đơn giản (Streamlit/FastAPI) để con người dễ theo dõi tiến độ sinh Alpha.

## 4. Hướng dẫn cho Agent kế thừa
1. Khi bắt đầu, hãy đọc `IMPROVEMENT_PLAN.md` và `MCP_USAGE.md` để hiểu sâu hơn về kiến trúc.
2. Kiểm tra log trong `wqb_logs/` để xem lịch sử chạy.
3. Nếu bạn muốn viết code cho tính năng mới, hãy thêm logic vào `alpha_agent.py` và expose ra thành `@mcp.tool()` trong `mcp_server.py`.
4. Nếu bạn muốn hệ thống tiếp tục tự động tìm kiếm Alpha, hãy sử dụng tool `mutate_from_gold` để sinh ra công thức từ **Gold Alpha V10** và submit.

Chúc may mắn trên con đường tìm kiếm Alpha! 🚀
