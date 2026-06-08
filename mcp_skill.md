---
name: wqb-alpha-generator
description: Comprehensive skill for creating WorldQuant Brain alphas. Grounded in 118 real simulations — 10 passed IQC.
---

# Skill: wqb-alpha-generator

Expert Quant Researcher knowledge base cho WorldQuant Brain (WQB).
**Đọc toàn bộ file này trước khi tạo bất kỳ formula nào.**

---

## 1. MCP Tools

| Tool | Khi nào dùng |
|------|-------------|
| `get_skill_knowledge()` | **Bắt buộc đầu session** |
| `search_knowledge_base(query)` | Trước khi tạo theme mới |
| `search_data_fields(query, limit)` | Tìm field name thực tế trên WQB |
| `submit_alpha(formula, settings)` | Simulate — luôn test trước |
| `diagnose_alpha(metrics)` | Sau mỗi sim — phân tích issue |

---

## 2. IQC Criteria — Phải pass HẾT 4 điều kiện

```
Sharpe           ≥ 1.25
Fitness          ≥ 1.0
Turnover         : 10% – 70%
Sub-universe Sharpe ≥ cutoff (~0.78 với TOP3000, ~0.70 với TOP1000)

Fitness = Sharpe × √( |Returns| / max(Turnover, 0.125) )
```

**Thực tế từ 118 sims: 76% fail vì Fitness thấp, 14% fail vì Sharpe thấp.**
**Sub-universe Sharpe thấp = signal mạnh overall nhưng yếu trong từng sub-group.**
→ Fix: dùng Industry/Subindustry neutralization thay Market

### Tính Fitness nhanh trước khi submit

```
S=1.4, TO=40%, Ret=12% → F = 1.4 × √(0.12/0.40) = 0.77  ❌
S=1.4, TO=20%, Ret=10% → F = 1.4 × √(0.10/0.20) = 0.99  ❌
S=1.6, TO=25%, Ret=13% → F = 1.6 × √(0.13/0.25) = 1.15  ✅
S=1.3, TO=17%, Ret=11% → F = 1.3 × √(0.11/0.17) = 1.05  ✅
```

**Rule of thumb: cần `Returns/Turnover ≥ 0.55` để pass với Sharpe ~1.3**

---

## 3. Formula Patterns — Proven từ 10 alphas đã pass IQC

### 🔑 Insight quan trọng nhất từ data thực tế:

**80% alphas pass dùng `close`** — price-based signals HOẠT ĐỘNG khi kết hợp đúng.
**60% pass dùng `group_neutralize` + `group_rank`** — neutralization là bắt buộc.
**40% pass dùng `ts_delta`** — simple price difference có edge.
**40% pass dùng `returns` + `volume`** — price/volume combination có edge.

---

### Pattern A: Vol-Adjusted Price Reversal + Decay cao (Sharpe 1.29-1.62, Fitness 1.02-1.06)

```python
// Proven với Decay 10-30: TO giảm xuống 16-30% → Fitness tăng cao
lookback = 5;
volatility = ts_std_dev(returns, 20);
price_signal = -ts_delta(close, lookback) / (volatility + 0.001);
volume_signal = volume / adv20;
vol_signal = rank(price_signal) * rank(volume_signal);

price_rev = -rank(ts_delta(close, 3));
0.6 * vol_signal + 0.4 * price_rev
```
*Settings: TOP3000|Industry|30|0.05 → S=1.29, F=1.02, TO=17%*
*Settings: TOP3000|Subindustry|10|0.08 → S=1.62, F=1.06, TO=30%*

**Key insight: Decay cao (10-30) là cách hiệu quả nhất để reduce TO về 15-30%**

---

### Pattern B: VWAP-Weighted Return (Sharpe 1.99, Fitness 1.01)

```python
lookback = 5;
raw_ret = ts_sum(returns * volume, lookback) / (ts_sum(volume, lookback) + 1);
vol_std = ts_std_dev(returns, 20);
signal = -rank(raw_ret / (vol_std + 0.001));
// Blend với price reversal
price_rev = -rank(ts_delta(close, 3));
0.6 * signal + 0.4 * price_rev
```
*Settings: TOP3000|Subindustry|0|0.08 → S=1.99, F=1.01, TO=65%*

**⚠️ TO cao (65%) → Fitness barely pass. Nếu TO tăng thêm → fail.**

---

### Pattern C: Fundamental Correlation (Sharpe 1.77, Fitness 1.64 — BEST Fitness)

```python
signal = group_rank(-ts_corr(est_ptp, est_fcf, 20), market);
group_neutralize(signal, market)
```
*Settings: TOP3000|Market|3|0.08 → S=1.77, F=1.64, TO=16%*

---

### Pattern D: Fundamental Yield Momentum (Sharpe 1.56-1.77, Fitness 1.06-1.10)

```python
// Version 1 — TOP1000
eps_yield = ts_backfill(anl4_afv4_eps_mean, 60) / close;
signal = group_rank(ts_rank(eps_yield, 60), industry);
group_neutralize(signal, industry)
```
*Settings: TOP1000|Industry|3|0.08 → S=1.56, F=1.10, TO=22%*

```python
// Version 2 — EV/CF
ev_cf = enterprise_value / cashflow_op;
signal = group_rank(-ts_zscore(ev_cf, 63), industry);
group_neutralize(signal, industry)
```
*Settings: TOP1000|Industry|3|0.08 → S=1.45, F=1.06, TO=18%*

---

### Pattern E: Intraday Open-Close Reversal (Sharpe 1.56, Fitness 1.02)

```python
intraday = (close - open) / (open + 0.001);
smooth = ts_mean(intraday, 3);
signal = group_rank(-smooth, market);
group_neutralize(signal, market)
```
*Settings: TOP3000|Market|3|0.05 → S=1.56, F=1.02, TO=58%*

---

## 4. Settings — Data từ 118 simulations

### Pass Rate theo Settings

| Settings | Pass/Total | Rate | Ghi chú |
|----------|-----------|------|---------|
| TOP1000\|Industry\|3\|0.08 | 2/3 | **67%** | Best reliable |
| TOP3000\|Subindustry\|10\|0.08 | 1/2 | 50% | Decay cao giảm TO |
| TOP3000\|Subindustry\|30\|0.05 | 1/1 | 100% | Very high decay |
| TOP3000\|Industry\|30\|0.05 | 1/4 | 25% | Decay 30 thường pass |
| TOP3000\|Market\|3\|0.08 | 1/3 | 33% | Fundamental signals |
| **TOP3000\|Market\|0\|0.05** | **0/13** | **0%** | ❌ Tránh hoàn toàn |
| TOP3000\|Subindustry\|0\|0.05 | 0/6 | 0% | ❌ Tránh |
| TOP3000\|Market\|5\|0.05 | 0/3 | 0% | ❌ Không pass |

### ⚠️ Settings Grid — thứ tự thử

```
1. TOP1000|Industry|3|0.08          ← highest pass rate (67%)
2. TOP3000|Subindustry|10|0.08      ← Decay cao giảm TO hiệu quả
3. TOP3000|Market|3|0.08            ← Fundamental signals
4. TOP3000|Industry|3|0.08          ← General purpose
5. TOP3000|Subindustry|30|0.05      ← Nếu signal chậm
```

**TRÁNH: TOP3000|Market|0|0.05 — 0/13 pass (không bao giờ dùng)**

---

## 5. Fitness Fix — Khi Sharpe OK nhưng Fitness thấp

```
Fitness thấp (< 1.0)?
│
├─ TO > 40%?
│    → Tăng Decay MẠNH: thử 10, 15, 20, 30
│    → Decay 30 đã cho TO = 16-17% (rất hiệu quả)
│    → KHÔNG chỉ tăng từ 3→5 (quá ít, không đủ)
│
├─ Returns < 10%?
│    → Dùng TOP1000 thay TOP3000 (liquid stocks, higher returns)
│    → Tăng Truncation: 0.05 → 0.08
│    → Blend VWAP signal: ts_sum(returns*volume) / ts_sum(volume)
│
├─ TO 20-35% nhưng Returns < 9%?
│    → Đổi sang TOP1000
│    → Thêm volume component: × rank(volume/adv20)
│
└─ Vẫn fail sau Decay cao?
     → Đổi formula hoàn toàn — settings không cứu được formula yếu
```

---

## 6. Valid & Broken Operators

### ✅ Valid
`ts_corr`, `ts_rank`, `ts_zscore`, `ts_delta`, `ts_mean`, `ts_std_dev`,
`ts_decay_linear`, `ts_sum`, `ts_backfill`, `ts_delay`, `ts_av_diff`,
`ts_regression`, `ts_covariance`, `ts_scale`, `ts_arg_max`, `ts_arg_min`,
`trade_when`, `rank`, `normalize`, `zscore`, `winsorize`, `scale`, `quantile`,
`group_neutralize`, `group_rank`, `group_zscore`, `group_vector_neut`

### ❌ BROKEN — Không dùng

| Operator | Thay bằng |
|----------|-----------|
| `pasteurize` | Không available trên account này |
| `ts_log_returns` | `log(close / ts_delay(close, d))` |
| `ts_min`, `ts_max` | `ts_arg_min`, `ts_arg_max` |
| `delay`, `delta`, `stddev`, `correlation` | `ts_delay`, `ts_delta`, `ts_std_dev`, `ts_corr` |

### 🚨 Reserved Variable Names (không dùng làm tên biến)
- `growth` → dùng `grw`, `g_rate`, `s_rate`
- Nếu gặp "reserved variable name" error → đổi tên biến

### ⚠️ Field Type Restrictions
- `ts_backfill` chỉ dùng với **MATRIX** fields, KHÔNG dùng với EVENT fields
- EVENT fields: `volume_standard_deviation_2`, `revision_fiscal_*`, `anl4_*_flag`

---

## 7. Valid Field Names (verified trên account)

### Price/Volume (MATRIX)
```
close, open, high, low, vwap, returns, volume, adv20, adv60, cap, sharesout
```

### Fundamental — PHẢI wrap ts_backfill()
```
// Earnings estimates (VERIFIED)
anl4_afv4_eps_mean              ← EPS mean estimate (proven in portfolio)
est_eps, est_fcf, est_ptp       ← Analyst estimates (proven)
enterprise_value, cashflow_op   ← EV, CF (proven)
earnings_per_share_median_value ← EPS median
earnings_per_share_standard_deviation  ← analyst dispersion
earnings_momentum_composite_score      ← pre-built WQB score
earnings_per_share_reported_value      ← actual reported EPS
eps_reported_avg

// Revenue/Book
revenue                         ← verified MATRIX
bookvalue_ps                    ← book value per share
book_value_per_share_2          ← actual book value per share

// Debt
debt, debt_lt                   ← total debt, long-term debt

// Analyst Sentiment (VERIFIED)
snt1_d1_netrecpercent           ← % buy minus % sell recommendations
snt1_d1_earningsrevision        ← 1-month change in mean EPS estimate
snt1_d1_netearningsrevision     ← net % analysts raising vs lowering estimates
snt1_d1_uptargetpercent         ← % analysts raising price target
snt1_d1_downtargetpercent       ← % analysts lowering price target
snt1_d1_analystcoverage         ← number of analysts covering stock
snt1_d1_fundamentalfocusrank    ← fundamental rank 0-100

// Valuation composite (WQB pre-built)
fscore_value                    ← composite over/underpriced score
mdl177_valanalystmodel_qva_valuation ← valuation rank
mdl177_deepvaluefactor_bp_alt   ← book-to-price ratio
```

### ❌ Fields NOT on this account
```
roe, roa, pe, pb, ebitda, est_tev   ← "unknown variable" error
operating_cash_flow                  ← "invalid data field" error
```

---

## 8. Self-Correlation — Portfolio hiện tại

| Alpha | Theme | Fields | Neutralization |
|-------|-------|--------|----------------|
| Vk8jzqqJ | EPS Yield Level | anl4_afv4_eps_mean / close | Industry |
| 6XEvXKmG | EV/CF Value | enterprise_value / cashflow_op | Industry |
| rKWvzA3j | FCF-Price Corr | ts_corr(est_ptp, est_fcf) | Market |
| 9qRKPxx1 | Intraday Open-Close | (close-open)/open | Market |

**Self-correlation limit: < 0.70. Cần khác biệt ≥ 2/3 chiều: field, operator, neutralization.**

**Themes chưa dùng (ưu tiên):**
- Analyst sentiment: `snt1_d1_netrecpercent`, `snt1_d1_earningsrevision`
- Revenue momentum: `revenue` + `ts_zscore`
- Book value yield: `bookvalue_ps / close`
- Earnings dispersion: `earnings_per_share_standard_deviation`
- WQB composite: `earnings_momentum_composite_score`, `fscore_value`
- Vol-adjusted price reversal + Decay cao (đã proven pass, theme khác portfolio)

---

## 9. Checklist trước khi submit

```
[ ] Tính Fitness trước: Sharpe × √(Returns / max(TO, 0.125)) ≥ 1.0?
[ ] Sharpe ≥ 1.25?
[ ] Turnover 10-70%? (nếu > 40% → cân nhắc tăng Decay)
[ ] Sub-universe Sharpe đủ cao? → dùng Industry/Subindustry, KHÔNG dùng Market nếu signal yếu trong sub-group
[ ] Không dùng broken operators? (pasteurize, ts_min, ts_max)
[ ] Fundamental fields có ts_backfill()?
[ ] Không dùng EVENT fields với ts_backfill?
[ ] Không dùng reserved variable names? (growth, ...)
[ ] Không dùng unavailable fields? (roe, roa, pe, pb, ebitda)
[ ] Self-correlation < 0.70 với 4 alphas trong portfolio?
[ ] Không dùng TOP3000|Market|0|0.05? (0/13 pass rate)
```

---

## 10. Stop & Rethink — Sau 3 consecutive failures

1. **Phân tích failure pattern:** Fitness thấp? Sharpe thấp? Error?
2. **Fitness thấp → tăng Decay MẠNH (10, 20, 30)** không phải chỉ 3→5
3. **Sharpe thấp → đổi formula hoàn toàn**, settings không cứu được
4. **Error → kiểm tra field names** dùng `search_data_fields()` trước khi test
5. **Đổi hướng:** price/volume ↔ fundamental ↔ composite, short-term ↔ medium-term

---

## 11. Lessons từ 118 simulations

### ✅ Proven HOẠT ĐỘNG
- **Price/volume + Decay cao (10-30)**: Vol-adjusted reversal với Decay 10-30 → TO 16-30% → Fitness pass
- **VWAP-weighted returns**: `ts_sum(returns*volume, d) / (ts_sum(volume, d)+1)` → Returns cao hơn ts_delta 30%
- **Fundamental correlation**: `ts_corr(est_ptp, est_fcf, 20)` + Market → Fitness 1.64 (best)
- **Fundamental yield**: `ts_backfill(est_eps, 60) / close` + `ts_rank(60)` → stable pass
- **Intraday reversal**: `(close-open)/open` + Market + Decay 3 → TO 58%, Fitness 1.02
- `group_neutralize` + `group_rank` là cặp operators hiệu quả nhất (60% alphas pass dùng cả 2)
- TOP1000 có pass rate 67% (cao nhất) — liquid stocks dễ pass hơn

### ❌ Proven KHÔNG hiệu quả
- `TOP3000|Market|0|0.05` — 0/13 pass (NEVER use)
- `-rank(ts_delta(close, 5))` đơn độc — Fitness max 0.82, không bao giờ pass
- Price-volume composites đơn giản (price_mom × vol_trend) → Sharpe âm
- `mdl77_oput_put_siratio` với ts_zscore — Sharpe 0.41
- Fields không có trên account: roe, roa, pe, pb, ebitda, est_tev
- Truncation 0.01 — Returns quá thấp

### 🔧 Bugs đã fix
- `search_data_fields` cần `universe=TOP3000` param
- `_submit_to_exchange` response 403 = SELF_CORRELATION fail
- `pasteurize` không available → dùng `winsorize`
- `ts_backfill` crash với EVENT fields

---

## 12. Project Structure

```
mcp_skill.md               ← file này (single source of truth)
wqb_automation.py          ← REST API client cho WQB
config.py                  ← tất cả paths
submit_best_daily_alpha.py ← submit alpha tốt nhất
gold_alphas.json           ← alpha đã pass IQC
wqb_logs/wqb_data.db       ← SQLite: 118 simulation history
agent/tools/diagnose_alpha.py ← phân tích metrics
_analyze_sim_history.py    ← phân tích toàn bộ lịch sử
_find_valid_fields.py      ← tìm field names hợp lệ
```
