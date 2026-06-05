# Project Goals - WorldQuant Brain Interactive Alpha Automation

## Mục tiêu chính

### 1. Tự động hóa Giao tiếp API qua MCP
- Xây dựng một MCP Server vững chắc đóng vai trò làm cầu nối giữa AI Assistant (như Claude) và WorldQuant Brain API.
- Thay vì để một script (như `alpha_agent.py`) chạy ngầm một cách mù quáng, chúng ta trao quyền cho AI Assistant trở thành một **Quant Researcher** thực thụ: tự đọc tài liệu, tự nghĩ ý tưởng và tự gửi API.

### 2. Tối ưu hóa chất lượng alpha bằng Lý thuyết học thuật
- Đạt Sharpe >= 1.25 và Fitness >= 1.0.
- Kiểm soát turnover (10%-70%) và drawdown (<15%).
- Đảm bảo **mọi Alpha** được sinh ra đều có cơ sở từ các bài báo khoa học thông qua công cụ `search_knowledge_base` (RAG). Khắc phục tình trạng "curve fitting" (khớp đường cong) vô căn cứ.

### 3. Hỗ trợ quy trình Interactive Exploration
- Khám phá các data fields lạ (Alternative Data, Sentiment, Fundamentals) bằng API để làm phong phú dữ liệu đầu vào.
- Lưu trữ các "Gold Alphas" (thành công) để AI có thể thực hiện Mutation (tiến hóa) lên các dạng công thức phức tạp hơn.

## Workflow Tương tác (Interactive Workflow)

Khác với quy trình tự động cũ, quy trình hiện tại là sự giao tiếp liên tục giữa User và AI:

```
[User Request] ──────────────────────────┐
                                         ↓
[AI Assistant] ──> (search_knowledge) ──> [Knowledge Base (Papers)]
      │
      ├──> (search_data_fields) ──────> [WQB API]
      │
      └──> (submit_alpha) ────────────> [WQB Simulation]
                                         │
[AI Assistant] <── (analyze_results) <────┘
      │
      └──> Đề xuất tinh chỉnh, thay đổi Settings, sửa công thức
      
      <!-- TODO: diagnose_alpha tool — chưa implement -->
```

## Các module chính

| Module | Chức năng |
|--------|----------|
| `mcp_server.py` | Cổng giao tiếp MCP (Tool Provider). |
| `wqb_automation.py` | Module xử lý kỹ thuật (Login, Submit, Parse kết quả). |
| `alpha_skills/knowledge_retriever.py` | Engine RAG tìm kiếm lý thuyết Quant. |
| `mcp_skill.md` | Bộ não (Quy tắc, IQC, Themes) hướng dẫn AI hoạt động. |

## Tiêu chí thành công

- ✅ AI tự do tra cứu lý thuyết và đưa ra ý tưởng có căn cứ.
- ✅ AI gửi lệnh lên WQB qua công cụ MCP thành công.
- ✅ Lưu trữ được các Gold Alphas vào `wqb_logs/gold_alphas.json`.
- ✅ Quy trình linh hoạt, User có thể can thiệp ở bất kỳ bước nào (ví dụ: chỉ định Data Field cần dùng).