# RESEARCH LOG — Bài học nghiên cứu Alpha

Nhật ký bài học tích luỹ. Mới nhất ở trên cùng. Ghi cả thất bại lẫn thành công kèm
nguyên nhân. Bí kíp kỹ thuật chi tiết (operators/patterns) nằm ở [mcp_skill.md](mcp_skill.md).

---

## 2026-06-15/16 — Reversal là cơ chế thắng trong regime hiện tại

**Bối cảnh:** universe TOP3000, neutralization Subindustry, delay=1, decay 2-5.

### ✅ Hoạt động: short-term mean-reversion trên price/volume
- **VWAP-deviation reversal** (close vs VWAP nhiều cửa sổ 5/7/10d) → nhiều alpha PASS.
- **VWAP-Open 5d** (`WjgreNdN`): S=1.87 F=1.36 TO=23.3% → **SUBMITTED_SUCCESS**.
- **Intraday Body reversal** (`(close-open)/open`, 5d, decay=2): S=1.74 F=0.98 — sát IQC,
  chỉ thiếu fitness 0.02 (TO 47% hơi cao → cần TO ≤ 45.7% hoặc tăng decay).

### ❌ KHÔNG hoạt động trong regime này (v16b)
- **Momentum 20d** (JT 1993): Sharpe ÂM (-1.05). Buy winners không có edge.
- **Amihud illiquidity / Low-Vol / 52wk-high**: Sharpe ≈ 0 hoặc âm. Các factor "risk premium"
  không cho tín hiệu ngắn hạn ở đây.
- **Overnight Gap reversal** (v18): S=0.09 — gap over-reaction không revert sạch.
- **HL-Midpoint reversal** (v18): S=1.21 F=0.62 — yếu.

### ⚠️ Decay KHÔNG phải lever để cứu Fitness (v18b)
Giả thuyết "tăng decay → giảm TO → Fitness lên" đã bị **bác bỏ bằng thực nghiệm**:

| Signal | decay2 | decay4 | decay6 | decay8 | decay10 |
|--------|--------|--------|--------|--------|---------|
| Intraday Body (Fitness) | **0.98** | 0.96 | 0.89 | — | — |
| Bollinger Z (Fitness) | — | — | — | 0.84 | 0.80 |

Tăng decay làm **Sharpe rớt nhanh hơn TO giảm** → Returns/TO và Fitness đều TỆ đi.
→ Lever đúng KHÔNG phải làm mượt tín hiệu nhanh, mà phải chọn **tín hiệu vốn dĩ
turnover thấp** (fundamental đổi chậm, hoặc VWAP-level), HOẶC lọc chỉ giao dịch
tín hiệu mạnh (`trade_when`). Fast price/volume reversal bị **trần Fitness ~0.9-0.98**.

### v19 — IC thô KHÔNG sống sót qua neutralization + `ts_max`/`ts_min` không khả dụng
Research IC (yfinance) chỉ ra range/volatility là tín hiệu duy nhất có IC thật
(price_range_10d ICIR_5d=0.43). Nhưng khi simulate trên WQB:
- `ts_max`/`ts_min` là **operator KHÔNG khả dụng** trên WQB FASTEXPR → công thức
  range max-min lỗi. Dùng `ts_std_dev(close,N)` làm proxy nếu muốn thử lại.
- High-Low Range % (long high-range) → **Sharpe −0.02, drawdown 59%**: range premium
  dương trên dữ liệu thô **biến mất sau group_neutralize(subindustry)** — đó là exposure
  beta/volatility bị risk-model loại. **Bài học: IC cross-section thô ≠ alpha tradable.**
- → Pivot sang FUNDAMENTAL (xem dưới): họ Fitness cao nhất lịch sử, không tương quan VWAP.

### 💎 Fundamental — họ Fitness cao nhất (proven, chưa có trong alpha_store.db)
Winner lịch sử (gold_alphas.json, field+công thức đã chạy được trên WQB):
- `rKWvzA3j` **F=1.64**: `group_rank(-ts_corr(est_ptp, est_fcf, 20), market)` — TOP3000|Market|3|0.08
- `1YgQo3gJ`: `ts_rank(ts_backfill(est_eps,60)/close, 60)` earnings-yield — TOP3000|Industry|3|0.08
- `6XEvXKmG`: EV/Cashflow valuation — TOP3000|Industry|3|0.08
- `Vk8jzqqJ`: earnings-yield momentum — TOP1000|Industry|3|0.08

Field hợp lệ: `est_eps, est_fcf, est_ptp, est_sales, est_tev, cashflow_op, enterprise_value, anl4_afv4_eps_mean, book_value`.
Operators thắng: `ts_corr, ts_rank, ts_zscore, ts_backfill`. Settings: Market/Industry, **decay=3** (KHÔNG 0).
⚠️ Có thể self-correlate với các fundamental đã submit trước đây → check self-corr sẽ bắt.

### 🎯 Vấn đề self-correlation
- Họ VWAP-deviation đã bão hoà → mọi biến thể VWAP tương quan cao lẫn nhau.
- WQB từ chối submit nếu `self_corr ≥ 0.7` VÀ Sharpe không hơn 10% so với alpha đã có.
- `P01mYX0E` bị loại do self_corr=0.80.
- **Hướng đi:** giữ cơ chế reversal (đang thắng) nhưng đổi INPUT để độc lập với VWAP:
  intraday body, overnight gap, close z-score (Bollinger), close-location + range filter.

---

## 2026-06-06 — (ĐÃ LỖI THỜI một phần) "Chỉ fundamental hoạt động"

> ⚠️ Kết luận phiên này — "price/volume KHÔNG có edge, chỉ fundamental mới pass" — đã bị
> **phản bác** bởi các phiên 06-15/16: reversal price/volume (VWAP, intraday body) thực sự
> pass IQC và submit được. Regime thị trường thay đổi, hoặc kết luận cũ quá vội. Giữ lại
> để tham khảo, KHÔNG còn là luật.

- 14 alpha test, 0 pass khi đó; price-momentum composites cho Sharpe âm.
- Quan sát còn đúng: **Fitness là nút thắt** — Sharpe 1.6 nhưng Fitness 0.9 vẫn FAIL;
  đừng cố "vá" Fitness 0.9→1.0 chỉ bằng chỉnh settings, công thức phải đổi.
- Quan sát còn đúng: turnover thấp (15-25%) → Returns/TO cao → Fitness cao;
  TO 40-60% thường kéo Fitness xuống.

---

## Bài học kỹ thuật chung (luôn áp dụng)

1. **Reserved keywords:** `growth` là từ khoá → không đặt tên biến trùng, nếu gặp lỗi
   "reserved variable name" thì đổi tên.
2. **Dừng sau 3 fail liên tiếp cùng cơ chế** → đổi họ tín hiệu, đừng phí slot.
3. **Mỗi biến thể phải khác biệt cơ bản**, không test 7 biến thể của cùng một công thức.
4. **Early-exit** khi Sharpe < 0.8 (công thức vô vọng, không cứu bằng settings).
5. Số slot simulate mỗi ngày có giới hạn → ưu tiên chất lượng giả thuyết.

## Session 2026-06-16 11:42 (auto)
- Steps [2, 3, 4, 5], simulated 5, IQC pass 3.
  - `rKWvzA3j` S=1.77 F=1.64 — Fundamental: EPS–FCF Estimate Correlation
  - `rKo1jeXj` S=1.76 F=1.29 — Fundamental: Earnings-Yield Z-Score (value)
  - `1Y7qwRpz` S=1.69 F=1.13 — Fundamental: Cashflow-to-EV Yield (value)

## Session 2026-06-17 10:15 (auto)
- Steps [4], simulated 1, IQC pass 0.

## Session 2026-06-17 10:18 (auto)
- Steps [4], simulated 2, IQC pass 0.

## Session 2026-06-17 10:23 (auto)
- Steps [4], simulated 1, IQC pass 0.

## Session 2026-06-17 10:34 (auto)
- Steps [4], simulated 3, IQC pass 0.

## Session 2026-06-17 11:04 (auto)
- Steps [4], simulated 6, IQC pass 2.
  - `d5xkGzNx` S=1.45 F=1.78 — Fundamental: EPS–CFO Estimate Correlation (market-neutral)
  - `e7OkXQmz` S=1.79 F=1.15 — Fundamental: CFO/Market-Cap Yield (WQB official example)

## Session 2026-06-17 11:08 (auto)
- Steps [4], simulated 1, IQC pass 0.

## Session 2026-06-17 11:12 (auto)
- Steps [4], simulated 1, IQC pass 1.
  - `d5xkGzNx` S=1.45 F=1.78 — Fundamental: EPS–CFO Estimate Correlation (market-neutral)

## Session 2026-06-17 11:16 (auto)
- Steps [4], simulated 1, IQC pass 0.

## Session 2026-06-17 11:21 (auto)
- Steps [4], simulated 1, IQC pass 1.
  - `MPpOP0AM` S=1.53 F=1.14 — Fundamental: CFO/Cap Yield Sector-Neutral (ts_rank, Sector neut)

## Session 2026-06-17 11:37 (auto)
- Steps [4], simulated 2, IQC pass 2.
  - `npg9xA2w` S=1.44 F=1.77 — Fundamental: PTP–CFO Divergence Correlation (estimate vs actual)
  - `YPp6L9j6` S=1.38 F=1.69 — Fundamental: FCF estimate–CFO Actual Divergence Correlation

## Session 2026-06-17 11:57 (auto)
- Steps [4], simulated 3, IQC pass 0.

## Session 2026-06-17 14:12 (auto)
- Steps [4], simulated 4, IQC pass 2.
  - `rKoYzGad` S=1.42 F=1.62 — Fundamental: EPS–EBITDA Divergence Correlation (new field)
  - `MPpOP0AM` S=1.53 F=1.14 — Fundamental: CFO/Cap Yield Sector-Neutral (ts_rank, Sector neut)

## Session 2026-06-18 22:58 (auto)
- Steps [2, 3, 4, 5], simulated 3, IQC pass 1.
  - `O0pa1ZWq` S=1.42 F=1.62 — Fundamental: EPS–EBITDA Divergence Correlation (new field)

---

## Session 2026-06-18 23:14 — Khám phá alternative data (options, sentiment, short interest)

**Bối cảnh:** Fundamental ts_corr đã bão hoà (self_corr cao). Nghiên cứu 5 họ hoàn toàn mới:
options (option8/9), analyst model (model16), short interest (model77), sentiment (snt1), social (scl12).

### Kết quả Batch 1 (7 candidates)

| Alpha | Signal | S | F | TO | Kết luận |
|-------|--------|---|---|----|----------|
| A1 IV Skew | `iv_put_270 - iv_call_270` | **+1.86** | 0.50 | 79.3% | Signal CỰC MẠNH, TO vượt 70% |
| A2 pcr_oi | `pcr_oi_270` | 0.14 | 0.01 | — | Không signal |
| B1 Analyst rev | `analyst_revision_rank_derivative` | — | — | — | Timeout (lỗi config cũ) |
| B2 fscore | `fscore_quality` | -0.52 | -0.14 | 10.3% | Ngược chiều |
| D1 snt1 | `snt1_cored1_score` | -0.70 | -0.23 | 21.0% | Ngược chiều |
| C1 short util | `mdl177_5shortsentimentfactor_act_util` | -0.95 | -0.34 | 57.3% | Ngược chiều |
| E1 buzz | `scl12_buzz ts_zscore 20d` | +0.70 | 0.08 | 120% | TO quá cao |

### Bài học Batch 1

1. **Options IV Skew là họ signal THỰC SỰ có alpha** — S=1.86 sau group_neutralize. Chỉ cần giảm TO.
   - `iv_put_270 - iv_call_270`: khi put IV cao hơn call IV → thị trường lo ngại downside → short sau đó underperform.
   - Cơ chế: IV skew capture tail-risk pricing, signal có đặc tính reversal.

2. **Tín hiệu "chiều ngược"** — B2, D1, C1 đều âm khi dùng chiều "tự nhiên":
   - `fscore_quality` cao → underperform (quality already priced in? mean-reversion?)
   - `snt1_cored1_score` cao (bullish sentiment) → underperform (contrarian)
   - `act_util` thấp → underperform (cần SHORT low util, LONG high util = short squeeze)
   - **Hướng xử lý:** flip dấu → chạy Batch 2.

3. **Social buzz với ts_zscore(20d) → TO=120%**: buzz thay đổi quá nhanh hàng ngày, cần window dài hơn hoặc ts_rank.

4. **Cần HTTP timeout** trong `requests.Session.get()`: nếu WQB không response, process treo vô thời hạn.
   File `wqb_automation.py` thiếu `timeout=` parameter trong polling call — cần fix sau.

### Batch 2 — kết quả (tune + flip)

| Alpha | S | F | TO | Ghi chú |
|-------|---|---|----|---------|
| A1-v2 ts_rank | 0.92 | 0.14 | 111% | ts_rank TĂNG TO (wrong fix) |
| A1-v3 ts_mean 5d | **1.48** | 0.61 | 28.3% | TO giảm nhưng Returns ~4.8%, F cấu trúc bị giới hạn |
| C1-v2 flip util | 0.95 | 0.34 | 57% | Hướng đúng: buy HIGH util (short squeeze) |
| D1-v2 contrarian snt | 0.70 | 0.23 | 21% | Contrarian sentiment quá yếu |
| B1-v2 analyst_rev | -0.86 | -0.59 | 3.5% | Ngược chiều cả hai phía, flip → ~+0.86 thôi |
| E1-v2 buzz ts_rank 60d | 0.27 | 0.02 | 131% | TO vẫn quá cao, buzz signal không dùng được |

**Kết luận Batch 2:**
- **Options IV Skew** có structural limit: Returns ~4.8% → F ≤ 0.61 dù S=1.86. Không thể vượt IQC bằng tune TO đơn thuần.
- **ts_rank() KHÔNG giảm TO** — là lỗi giả thuyết. Dùng ts_mean() mới giảm TO hiệu quả.
- **Sentiment/Buzz signals**: TO quá cao cho mọi cách dùng (zscore hay ts_rank). Cần data khác.
- **Short utilization** direction = buy HIGH util (S=0.95), nhưng standalone chưa đủ mạnh.

### Batch 3 đang chạy — Lý thuyết học thuật (2025)

Nguồn: ScienceDirect 2025, EFMA 2024, Sloan 1996, Cremers-Weinbaum 2010.

| Formula | Lý thuyết cơ sở |
|---------|-----------------|
| F1: `implied_volatility_mean_30 - ts_std_dev(returns,20)*15.87` | VRP: sell overpriced implied vol |
| F2: `implied_volatility_mean_30 - implied_volatility_mean_360` | IV term structure inversion = near-term stress |
| F3: `rank(call_IV-put_IV) + rank(util)` | Additive: bullish options + high short interest |
| F4: `mdl177_2_earningsqualityfactor_wcacc` | Sloan accruals anomaly (short high WCA) |
| F5: `mdl177_2_liquidityriskfactor_monchgsip` | Monthly ΔSI = follow smart shorts |
| F6: `rank(call-put_IV) + rank(gross_profit_to_assets)` | Options signal + Novy-Marx profitability |
