# Project Goals - WorldQuant Brain Alpha Automation System

## Mục tiêu chính

### 1. Tự động hóa quy trình tạo alpha
- Xây dựng pipeline tự động: nghiên cứu → tạo hypothesis → submit → phân tích → cải thiện
- Giảm thiểu công việc thủ công cho researcher
- Tăng tốc độ exploration các alpha patterns

### 2. Tối ưu hóa chất lượng alpha
- Đạt Sharpe >= 1.25 và Fitness >= 1.0
- Kiểm soát turnover (1-70%) và drawdown (<25%)
- Xây dựng knowledge base các alpha patterns thành công/thất bại

### 3. Học máy & evolution
- Lưu trữ gold alphas từ các phiên simulation
- Sinh mutation từ alpha thành công
- Áp dụng chiến lược trading (momentum, mean reversion, vwap deviation, ...)

### 4. Hỗ trợ IDE development
- Chạy được trực tiếp trên VS Code/Rider với debugging
- Cung cấp logs chi tiết tại `wqb_logs/`
- Screenshots tự động để diagnose UI issues

## Workflow tự động

```
[Research Papers] → [Knowledge Base] → [Hypothesis Generation]
                                        ↓
                              [Alpha Formula Creation]
                                        ↓
                              [Settings Grid Testing]
                                        ↓
                         [Simulation Result Collection]
                                        ↓
                              [Metrics Analysis]
                                        ↓
                             [Diagnosis & Fixing]
                                        ↓
                               [Knowledge Update]
```

## Các module chính

| Module | Chức năng |
|--------|----------|
| `alpha_agent.py` | Agent chính - autonomous loop |
| `wqb_automation.py` | Browser automation + submission |
| `stock_pipeline/` | Stock screening + factor computation |
| `alpha_skills/` | Knowledge base - themes, operators, IQC |
| `AGENTS_README.md` | Documentation chi tiết |

## Tiêu chí thành công

- ✅ Login WQB thành công
- ✅ Submit alpha và nhận kết quả (Sharpe, Fitness, Turnover)
- ✅ Lưu gold alpha vào `wqb_logs/gold_alphas.json`
- ✅ Chạy liên tục không crash
- ✅ Tự động cải thiện dựa trên kết quả