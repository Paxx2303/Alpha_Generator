# Alpha Generator — WorldQuant Brain

Hệ thống nghiên cứu & tạo Alpha (tín hiệu giao dịch định lượng) trên WorldQuant Brain (WQB),
kết hợp LLM Agent (Claude/Cursor) làm "Quant Researcher" với WQB REST API.

## Bắt đầu nhanh

1. **Credentials:** điền `wqb_config.json` (email/password) — file này gitignored.
2. **Đọc quy trình:** [WORKFLOW.md](WORKFLOW.md) — 5 bước Explore → Descriptive → Analysis → Predict → Action + luật vận hành.
3. **Bí kíp tín hiệu:** [mcp_skill.md](mcp_skill.md) — operators, patterns, settings grid (cập nhật liên tục).
4. **Chạy pipeline:** `python run_research.py` → full 5-step methodology (Explore→Descriptive→Analysis→Predict→Action). Kết quả durable: `data/alpha_store.db` + `RESEARCH_LOG.md`.
5. **Kiểm tra pool:** `python check_db.py` → liệt kê gold alphas trong `data/alpha_store.db`.

## Kiến trúc

- **`wqb_automation.py`** — client REST API (`api.worldquantbrain.com`). Login Basic Auth →
  `POST /simulations` → poll progress → `GET /alphas/{id}` lấy metrics. KHÔNG dùng Selenium/Playwright.
- **`config.py` / `wqb_config.json`** — cấu hình credentials.
- **`mcp_server.py`** — MCP bridge: `search_knowledge_base`, `search_data_fields`, `submit_alpha`…
- **`run_research.py`** — điểm vào DUY NHẤT; thực thi 5-step methodology end-to-end.
- **`analytics/hypothesize.py`** — sinh alpha hypothesis với dead-operator guard + fundamental anchors.
- **`alpha_skills/chunks/`** — knowledge base RAG (brain_tips, academic_papers, platform_guides, core_concepts).
- **`crawlers/` `pipeline/` `storage/`** — v2 catalog crawl: WQB datasets/datafields/operators → `alpha_store.db`.
- **`data/alpha_store.db`** — DB thật (bảng `gold_alphas`). `wqb_logs/` chứa log + DB legacy.

## IQC (tiêu chí pass)

`Sharpe ≥ 1.25` & `Fitness ≥ 1.0` & `Turnover ∈ [1%, 70%]`
trong đó `Fitness = Sharpe × sqrt(Returns / max(Turnover, 0.125))`.

## Trạng thái pool (cập nhật 2026-06-16)

| Alpha | Mô tả | S | F | TO | Status |
|-------|-------|---|---|----|--------|
| `WjgreNdN` | VWAP-Open 5d Deviation | 1.87 | 1.36 | 23.3% | SUBMITTED_SUCCESS |
| `58vYJp15` | VWAP 5d Reversal Decay=2 | 1.75 | 1.02 | 34.7% | UNSUBMITTED |
| `d5QrbL2g` | VWAP 7d Reversal Decay=5 | 1.65 | 1.17 | 22.0% | UNSUBMITTED |
| `Gro90oex` | VWAP 5d Reversal Decay=5 | 1.65 | 1.16 | 21.0% | UNSUBMITTED |
| `1YgWwo8W` | Vol-Adj Price Reversal | 1.58 | 1.00 | 30.3% | UNSUBMITTED |
| `wpeWEV9d` | VWAP 10d Reversal Decay=5 | 1.47 | 1.07 | 18.3% | UNSUBMITTED |
| `P01mYX0E` | VWAP-dev + Close Loc | 1.85 | 1.10 | 30.3% | CORRELATED (0.80) |

> Họ VWAP-deviation đã bão hoà (tương quan cao lẫn nhau). Hướng tiếp theo: reversal trên
> input mới (intraday body, overnight gap, z-score) để giữ self-corr < 0.7. Xem [RESEARCH_LOG.md](RESEARCH_LOG.md).
