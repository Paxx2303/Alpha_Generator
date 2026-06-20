# WORKFLOW — Quy trình nghiên cứu Alpha (WorldQuant Brain)

Quy trình chuẩn gồm **5 bước**, đi tuần tự. Không nhảy thẳng tới simulate khi chưa
có cơ sở dữ liệu/giả thuyết.

```
EXPLORE  →  DESCRIPTIVE  →  ANALYSIS  →  PREDICT  →  ACTION
 (data)      (data)         (data)      (data)
```

---

## 1. EXPLORE DATA — Khám phá dữ liệu
**Mục tiêu:** biết WQB có những dataset/field nào dùng được.

- `search_data_fields()` (MCP) hoặc crawler trong `crawlers/` để liệt kê field.
- Xác định nhóm dữ liệu: price/volume (`close, open, high, low, volume, returns, vwap`),
  fundamental (`est_*, eps, enterprise_value, cashflow_op, anl4_*`), news/sentiment, options.
- Ghi lại field nào tồn tại, delay, region (USA), universe (TOP3000…).

**Xong khi:** có danh sách field ứng viên + nhóm tín hiệu định thử.

## 2. DESCRIPTIVE DATA — Mô tả dữ liệu
**Mục tiêu:** hiểu bản chất field trước khi đưa vào công thức.

- Coverage (bao nhiêu % universe có giá trị), tần suất cập nhật, đơn vị.
- Ý nghĩa kinh tế của field; reserved keyword cần tránh (vd `growth` là từ khoá → đổi tên biến).
- Phân phối/độ nhiễu: field fundamental đổi chậm (TO thấp), price/volume nhiễu cao (TO cao).

**Xong khi:** biết field nào sạch, ý nghĩa, và kỳ vọng turnover sơ bộ.

## 3. ANALYSIS DATA — Phân tích & giả thuyết
**Mục tiêu:** dựng giả thuyết tín hiệu có cơ sở, ước lượng độc lập (self-corr).

- Cơ sở học thuật: `search_knowledge_base()` (mean-reversion, momentum, illiquidity…).
- Phân tích IC / hướng tín hiệu: reversal (`-rank(...)`) vs momentum (`rank(...)`).
- **Đa dạng họ tín hiệu** — tránh cụm cùng cơ chế (họ VWAP-deviation đã bão hoà).
  Ước lượng self-correlation kỳ vọng với pool hiện có TRƯỚC khi simulate.

**Xong khi:** có giả thuyết + công thức nháp + lý do tin self-corr sẽ < 0.7.

## 4. PREDICT DATA — Dự đoán (simulate)
**Mục tiêu:** biến giả thuyết thành alpha và đo bằng simulation. Alpha = mô hình dự đoán.

- `submit_alpha(formula, settings, auto_submit=False)` → **SIMULATE ONLY**.
- Settings chuẩn: `TOP3000|<Neutralization>|<Decay>|<Truncation>`, delay=1.
- Đọc metrics: Sharpe, Fitness, Turnover, Returns, Drawdown.
- **IQC:** `Sharpe ≥ 1.25` & `Fitness ≥ 1.0` & `Turnover ∈ [1%, 70%]`.
  - Fitness: `F = S × sqrt(R / max(TO, 0.125))`. Sharpe cao + Fitness < 1.0 vẫn FAIL.
  - Early-exit nếu `Sharpe < 0.8` (đừng tinh chỉnh settings cho công thức vô vọng).

**Xong khi:** có kết quả PASS/FAIL ghi vào session log (auto-deleted sau run, durable summary vào `RESEARCH_LOG.md`).

## 5. ACTION — Hành động
**Mục tiêu:** với alpha PASS, kiểm tra cổng submit và lưu trữ.

1. **Self-correlation check** (bắt buộc): `check_self_correlation(alpha_id)`.
   - corr ≥ 0.7 và Sharpe không hơn 10% → `status=CORRELATED` (loại, không submit được).
   - corr OK → `status=UNSUBMITTED`, lưu vào `gold_alphas` (DB `data/alpha_store.db`).
2. **Submission check** (khi được yêu cầu): `submit_saved_alpha(alpha_id)` → `POST /submit`.
   - ⚠️ Pass hết các cổng = **submit thật, không hoàn tác được** → `SUBMITTED_SUCCESS`.
   - Fail = trả về check nào hỏng, KHÔNG submit (`FAIL_CHECKS` / `CORRELATED`).
3. **Ghi bài học** vào `RESEARCH_LOG.md` / `mcp_skill.md` (xem Rules §3).

**Xong khi:** alpha đã được phân loại trạng thái và bài học đã ghi lại.

---

## OPERATING RULES (Luật vận hành)

1. **AI là bộ não duy nhất.** Không brute-force sinh công thức bằng script if/else.
   Phân tích Sharpe/Fitness/Turnover và ghép hàm (`rank`, `ts_*`, `group_neutralize`…)
   bằng suy luận của LLM trên khung chat.
2. **SIMULATE ONLY, không auto-submit.** `auto_submit=False` luôn. Người dùng duyệt thủ công
   trước khi submit. Submit chỉ chạy khi được yêu cầu rõ ràng (xem Bước 5).
3. **Tiến hoá kỹ năng bằng tay.** Sau mỗi vòng đời, ghi bài học vào `mcp_skill.md`
   (bí kíp) và `RESEARCH_LOG.md` — đây là bộ nhớ sống của dự án.
4. **Dừng & nghĩ lại sau 3 lần fail liên tiếp.** Đừng phí slot thử biến thể của một
   cơ chế đã chứng minh vô hiệu — đổi sang họ tín hiệu khác.
5. **Self-correlation bắt buộc** sau mỗi IQC pass, trước khi tính là gold alpha.
6. DB thật: `data/alpha_store.db` (bảng `gold_alphas`). `wqb_logs/wqb_data.db` là legacy.

## Kiến trúc thực thi (hiện tại)
- `wqb_automation.py` — client **REST API** (`api.worldquantbrain.com`), KHÔNG dùng
  Selenium/Playwright. Login bằng Basic Auth → `POST /simulations` → poll → `/alphas/{id}`.
- `config.py` / `wqb_config.json` — credentials. `mcp_server.py` — MCP bridge cho Agent.
- **`run_research.py`** — điểm vào DUY NHẤT. Thực thi toàn bộ 5 bước, không dùng script rời.
  ```
  python run_research.py                    # full 5 bước, simulate top 6
  python run_research.py --steps 1,2,3      # chỉ research (không simulate)
  python run_research.py --top 2            # simulate 2 hypothesis
  python run_research.py --no-submit-check  # simulate nhưng không bấm /submit
  python run_research.py --keep-logs        # giữ lại scratch log
  ```
- `analytics/hypothesize.py` — sinh hypothesis, lọc dead-operator, ưu tiên WQB-validated signal.
- `analytics/explore.py`, `analytics/market_data.py`, `analytics/describe.py` — Steps 2-3.
- `crawlers/`, `storage/` — v2 catalog crawl (Step 1: WQB datasets/datafields/operators).
- `alpha_skills/chunks/` — knowledge base RAG (brain_tips, academic_papers, platform_guides…).
- `data/alpha_store.db` — DB thật (bảng `gold_alphas`). Kết quả durable sau mỗi run.
