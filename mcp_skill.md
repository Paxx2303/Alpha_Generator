---
name: wqb-alpha-generator
description: Tự động hóa việc tạo, gửi và đánh giá các chiến lược giao dịch định lượng (Alphas) trên WorldQuant Brain. Cung cấp bộ khung kiến thức toán học và kỹ thuật tối ưu hóa chỉ số Turnover, Fitness và Sharpe.
---

# Tên Kỹ năng (Skill): wqb-alpha-generator

Kỹ năng này cung cấp một bộ công cụ hoàn chỉnh để tác nhân AI có thể đóng vai trò là một Quant Researcher, tự động tương tác với nền tảng WorldQuant Brain (WQB) thông qua REST API trực tiếp.

## Các tính năng chính (Features)

1. **Quản lý Phiên (Session Management):**
   - Đăng nhập an toàn vào WQB bằng Basic Auth.
   - Quản lý cookies và headers để vượt qua các giới hạn API.

2. **Gửi và Giám sát Alpha (Submission & Monitoring):**
   - Đóng gói công thức toán học (`formula`) và cấu hình (`settings` như Universe, Decay, Neutralization) vào payload JSON.
   - Gửi Alpha trực tiếp lên API `/simulations`.
   - Giám sát ngầm tiến trình chạy (Progress) và trạng thái (COMPLETE, WARNING, ERROR) thông qua việc poll API. Tránh bị chặn do vượt quá `CONCURRENT_SIMULATION_LIMIT_EXCEEDED`.

3. **Trích xuất và Phân tích Chỉ số (Metrics Extraction):**
   - Tự động bóc tách các chỉ số cốt lõi từ phản hồi API: `Sharpe`, `Fitness`, `Turnover`, `Returns`.
   - Lưu trữ lịch sử chạy vào thư mục `logs/` định dạng JSON để phục vụ phân tích chéo.

## Kiến thức Lõi và Kỹ thuật Tối ưu (Core Knowledge - `Skill.md`)

AI sử dụng bộ từ điển cấu trúc công thức được định nghĩa trong `Skill.md` để sinh ra các Alpha. 

**Tiêu chuẩn IQC (In-Sample Quality Criteria):**
- **Sharpe Ratio:** $\ge 1.25$
- **Fitness:** $\ge 1.0$
- **Turnover:** $\le 0.7$

**Các kỹ thuật tối ưu hóa chuyên sâu (Advanced Optimization):**

1. **Giảm Turnover (Chi phí vòng quay cao):**
   - *Làm mượt (Smoothing):* Sử dụng hàm `ts_decay_linear(signal, days)` để giảm sự biến động liên tục của tín hiệu.
   - *Cập nhật lười biếng (Lazy Updating):* Kết hợp `trade_when` và `ts_delay` để chỉ đổi vị thế khi giá thay đổi vượt ngưỡng (ví dụ: `trade_when(abs(returns) > 0.02, signal, ts_delay(signal, 1))`).
   - Tăng thiết lập biến môi trường `Decay` lên 3, 5, hoặc 10.

2. **Tăng Returns & Fitness:**
   - *Trộn tín hiệu (Signal Blending):* Cộng gộp nhiều tín hiệu yếu thành một tín hiệu mạnh (ví dụ: Price Momentum + Volume Reversion).
   - *Cắt gọt chặt chẽ (Stricter Truncation):* Giảm Truncation xuống `0.01` để chỉ giao dịch top 1% cổ phiếu có niềm tin cao nhất.
   - *Trung hòa Nhóm (Group Neutralization):* Sử dụng `Neutralization = Subindustry` để loại bỏ rủi ro hệ thống, chỉ lấy Alpha thuần túy từ nội bộ ngành.

## Cấu trúc Dự án (Project Structure)

- `wqb_automation.py`: Client tương tác API cốt lõi, xử lý HTTP requests và parse kết quả.
- `run_auto_loop.py`: Kịch bản mẫu để chạy một loạt các công thức liên tiếp.
- `alpha_agent.py`: Agent chịu trách nhiệm sinh công thức toán học ngẫu nhiên hoặc dựa trên Theme (Momentum, Mean Reversion, v.v.).
- `alpha_skills/Skill.md`: Bách khoa toàn thư chứa cú pháp, ràng buộc operator của WQB và mẹo tinh chỉnh.
- `.env`: Chứa thông tin đăng nhập WQB_EMAIL và WQB_PASSWORD.

## Khi nào nên sử dụng kỹ năng này?

- Khi người dùng muốn mô phỏng (simulate) một ý tưởng định lượng thành công thức thực tế trên WQB.
- Khi người dùng cung cấp một Alpha bị lỗi (Turnover cao, Fitness thấp) và yêu cầu AI tự động chuẩn đoán, sửa lỗi và nộp lại cho đến khi pass tiêu chuẩn IQC.
- Khi cần tạo nhanh hàng loạt biến thể của một công thức (thay đổi lookback days, operators) để brute-force tìm ra thông số tối ưu nhất.
