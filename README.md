# Alpha Generator — WorldQuant Brain Automation

Hệ thống tự động tạo, tối ưu và submit alpha signals lên WorldQuant Brain.

## Kiến trúc

```
Pipeline Stock (Python)
  └── run_pipeline.py → stock_pipeline/
      DataFetcher, AlphaFactorEngine, StockScreener

WQB Automation (REST API)
  └── wqb_automation.py
      API Login → Submit Formula → Đọc kết quả

Alpha Agent (Autonomous Loop)
  └── alpha_agent.py
      Research → Hypothesis → Submit → Analyze → Improve

MCP Server
  └── mcp_server.py
      Cung cấp bộ công cụ MCP cho Claude/Cursor
```

## Quick Start

```bash
# 1. Chạy stock screening pipeline
python run_pipeline.py --universe TOP500 --top-n 20

# 2. Test WQB login
python wqb_automation.py --formula "-rank(ts_delta(close,5))"

# 3. Chạy autonomous agent
python alpha_agent.py
python alpha_agent.py --headless       # Không bắt buộc với API mới
python alpha_agent.py --quick          # dry-run, không submit
python alpha_agent.py --max-cycles 10  # tối đa 10 vòng
```

## File Structure

| File | Chức năng |
|---|---|
| `mcp_server.py` | MCP Server cung cấp 6 tools nghiên cứu Alpha |
| `wqb_automation.py` | REST API auto login + submit alpha + đọc kết quả |
| `alpha_agent.py` | Autonomous agent: loop research → submit → analyze |
| `run_pipeline.py` | CLI chạy stock screening pipeline |
| `stock_pipeline/` | Modules: DataFetcher, AlphaFactorEngine, StockScreener |
| `alpha_skills/Skill.md` | Knowledge base: themes, operators, settings, IQC strategy |

## WQB Automation

```bash
# Formula + settings
python wqb_automation.py --formula "rank(vwap - close)" --settings "TOP500|Subindustry|3|0.10"

# Batch từ file
python wqb_automation.py --file alpha_list.txt

# Nhập tay
python wqb_automation.py --interactive
```

## Credentials

Set env vars hoặc `wqb_config.json`:
```json
{
    "email": "your_email",
    "password": "your_password",
    "headless": false,
    "timeout_ms": 300000
}
```

## Output

| File | Nội dung |
|---|---|
| `wqb_logs/alpha_*.json` | Kết quả alpha (Sharpe, Fitness, Turnover, yearly) |
| `wqb_logs/gold_alphas.json` | Alpha đã pass (Sharpe ≥ 1.25 + Fitness ≥ 1.0) |
| `wqb_logs/*.png` | Screenshot debug các bước |
| `pipeline_output/pipeline_results.json` | Stock screening results |
| `pipeline_output/top_stocks_daily.csv` | Top stock picks theo ngày |

## Stock Pipeline

```bash
# Custom
python run_pipeline.py --universe TOP1000 --top-n 30 --start 2024-01-01
python run_pipeline.py --tickers AAPL MSFT GOOGL --no-cache
```

18 alpha factors: mean reversion, momentum, volume-price, VWAP, volatility, liquidity, money flow.

## Troubleshooting

- **Login fail**: xem `wqb_logs/login_failed.png` + `after_login.png`
- **Simulation lỗi**: check `wqb_logs/page_debug.html`
- **Timeout submit**: tăng `timeout_ms` trong config
- **Formula syntax error**: xem Skill.md → operators reference
