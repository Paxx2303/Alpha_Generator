# Alpha Generator — WorldQuant Brain Automation via MCP

Hệ thống cung cấp một công cụ MCP (Model Context Protocol) chuyên nghiệp giúp các AI Agent (như Claude, Cursor) đóng vai trò là Interactive Quant Researcher, cho phép AI tự động tra cứu lý thuyết, tạo Alpha, và tương tác trực tiếp với API của WorldQuant Brain.

## Kiến trúc Mới (Interactive AI Quant Researcher)

Thay vì phó mặc cho một vòng lặp tự động (Autonomous Loop) hoạt động máy móc, dự án này được thiết kế để AI Assistant chủ động:
1. Đọc và trích xuất lý thuyết từ **Knowledge Base** (các bài báo học thuật).
2. Viết công thức Alpha sắc bén dựa trên các **Themes** kinh điển.
3. Gửi công thức đến WQB thông qua **MCP Tools**.
4. Tự phân tích kết quả (Sharpe, Fitness) và tinh chỉnh qua từng lần thử.

```
AI Assistant (Claude/Cursor)
  │
  ├──> [Knowledge Base] Trích xuất lý thuyết (RAG)
  │
  └──> MCP Server (mcp_server.py)
         └──> WQB Automation (wqb_automation.py)
                └──> WorldQuant Brain API
```

## Quick Start

```bash
# 1. Chạy stock screening pipeline (nếu cần dữ liệu local)
python run_pipeline.py --universe TOP500 --top-n 20

# 2. Khởi động MCP Server để kết nối với AI Agent
# Cấu hình file mcp_server.py trong Claude Desktop / Cursor
```

## File Structure

| File | Chức năng |
|---|---|
| `mcp_server.py` | MCP Server cung cấp các công cụ nghiên cứu Alpha cho AI. |
| `wqb_automation.py` | REST API auto login + submit alpha + parse metrics từ WQB. |
| `submit_single.py` | Script tiện ích để submit một công thức nhanh qua CLI. |
| `run_pipeline.py` | CLI chạy stock screening pipeline (sử dụng dữ liệu Yahoo Finance). |
| `stock_pipeline/` | Modules phân tích nội bộ: DataFetcher, AlphaFactorEngine, StockScreener. |
| `mcp_skill.md` | Single Source of Truth cho kỹ năng tạo Alpha (Themes, IQC rules). |
| `alpha_skills/` | Kho lưu trữ các lý thuyết (Knowledge Base JSON) và module `knowledge_retriever.py`. |

## Cấu hình Credentials

Set biến môi trường (Environment Variables) hoặc tạo file `wqb_config.json`:
```json
{
    "email": "your_email",
    "password": "your_password",
    "headless": false,
    "timeout_ms": 300000
}
```

## Logs & Output

| File | Nội dung |
|---|---|
| `wqb_logs/alpha_*.json` | Kết quả của từng alpha được submit (Sharpe, Fitness, Turnover). |
| `wqb_logs/gold_alphas.json` | Danh sách các Alpha đã Pass (Sharpe ≥ 1.25 + Fitness ≥ 1.0). |
| `pipeline_output/` | Kết quả trả về từ `stock_pipeline/`. |
