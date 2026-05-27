# Alpha Themes — Ý Tưởng & Formula Mẫu

Mỗi theme có lý do kinh tế, công thức mẫu, và gợi ý biến thể. Dùng làm điểm xuất phát khi tạo alpha mới.

---

## Mean Reversion
*Lý thuyết: Giá bị đẩy quá xa khỏi giá trị hợp lý sẽ quay trở lại*

**Khi nào áp dụng:** Sau những ngày biến động mạnh bất thường

```python
# === Cơ bản ===
# Mua cổ phiếu giảm nhiều nhất tuần qua
-rank(ts_delta(close, 5))

# === Có smoothing ===
# Làm mượt signal để giảm Turnover
rank(ts_decay_linear(-ts_delta(close, 5), 3))

# === Dùng returns thay vì price ===
-rank(ts_mean(returns, 5))

# === Kết hợp nhiều lookback ===
-rank(ts_mean(returns, 5) + ts_mean(returns, 10))
```

**Settings khuyến nghị:** TOP3000, Market neutralization, Decay 0-3, Truncation 0.05
**Lookback tốt nhất:** 5-20 ngày (ngắn hạn)

**Biến thể nâng cao:**
```python
# Mean reversion lọc theo volume thấp (tránh momentum trap)
if_else(ts_rank(volume, 20) < 0.5, -rank(ts_delta(close, 5)), 0)
```

---

## Momentum
*Lý thuyết: Đà tăng/giảm mạnh thường tiếp diễn trong ngắn hạn*

**Khi nào áp dụng:** Thị trường trending, volume cao

```python
# === Momentum ngắn hạn (1-5 ngày) ===
rank(ts_mean(returns, 5))

# === Momentum trung hạn (1-3 tháng) ===
rank(ts_delta(close, 20))

# === Momentum trừ đi reversal ngắn ===
# Dùng 20 ngày momentum, bỏ qua 1 tuần gần nhất (tránh reversal)
rank(ts_delta(ts_delay(close, 5), 15))

# === Rank-based momentum ===
ts_mean(rank(returns), 10)
```

**Settings khuyến nghị:** TOP1000-TOP3000, Subindustry neutralization, Decay 3-5
**Lookback tốt nhất:** 20-60 ngày (trung hạn)

**Cảnh báo:** Momentum ngắn hạn (<5 ngày) thường bị reversal. Momentum dài hạn (>60 ngày) thường quá chậm.

---

## Volume-Price
*Lý thuyết: Khối lượng giao dịch bất thường tiết lộ thông tin ẩn về cổ phiếu*

**Khi nào áp dụng:** Khi muốn khai thác thông tin từ trading activity

```python
# === Tương quan âm giữa price và volume ===
# Alpha #13 từ "101 Formulaic Alphas" — đã proven
-rank(ts_covariance(rank(close), rank(volume), 5))

# === Volume surge + price thấp ===
# Volume đột biến nhưng giá không tăng → bán
rank(ts_rank(volume, 20)) * -rank(ts_delta(close, 5))

# === Dòng tiền âm/dương ===
# close > open → money flow dương
rank(ts_sum(sign(close - open) * volume, 10))

# === Volume-weighted returns ===
rank(ts_mean(returns * volume, 5) / ts_mean(volume, 5))
```

**Settings khuyến nghị:** TOP3000, Market neutralization, Decay 0
**Data fields:** `volume`, `close`, `open`, `vwap`

---

## VWAP Deviation
*Lý thuyết: Giá lệch xa VWAP (trung bình gia quyền volume) thường quay về*

**Khi nào áp dụng:** Intraday patterns, mean reversion ngắn hạn

```python
# === Cơ bản: lệch khỏi VWAP ===
rank(vwap - close)

# === Chuẩn hóa theo volatility ===
rank((vwap - close) / ts_std_dev(close, 20))

# === VWAP reversion với volume filter ===
rank((vwap - close) / close) * rank(ts_rank(volume, 20))

# === Kết hợp với peak timing (IQC top alpha) ===
(vwap - close) / close / (ts_decay_linear(rank(ts_arg_max(close, 30)), 1) + 0.15)
```

**Settings khuyến nghị:** TOP200-TOP500, Market neutralization, Decay 0, Truncation 0.01

---

## Volatility
*Lý thuyết: Biến động tăng/giảm bất thường có thể dự báo được*

**Khi nào áp dụng:** Sau giai đoạn thị trường yên tĩnh hoặc hỗn loạn

```python
# === Short volatility (cổ phiếu biến động thấp outperform) ===
-rank(ts_std_dev(returns, 20))

# === Volatility reversal ===
# Biến động cao gần đây → sẽ giảm
-rank(ts_std_dev(returns, 5) / ts_std_dev(returns, 20))

# === Spike detection ===
# Phát hiện biến động bất thường
-rank(ts_std_dev(returns, 5) - ts_mean(ts_std_dev(returns, 5), 20))

# === Range-based volatility ===
rank(-ts_mean((high - low) / close, 10))
```

**Settings khuyến nghị:** TOP1000, Subindustry neutralization, Decay 5
**Cảnh báo:** Low-volatility factor có thể bị factor overcrowding

---

## High-Low Midpoint
*Lý thuyết: Giá đóng cửa lệch khỏi trung điểm high-low phản ánh sức mạnh ngày*

```python
# === Cơ bản ===
rank((high + low) / 2 - close)

# === Nhiều ngày ===
rank(ts_mean((high + low) / 2 - close, 5))

# === Chuẩn hóa theo range ===
rank((close - low) / (high - low + 0.001))
```

---

## Sector Relative
*Lý thuyết: Cổ phiếu mạnh nhất trong ngành sẽ tiếp tục mạnh*

```python
# === Rank trong ngành ===
group_rank(returns, industry)

# === Lệch khỏi trung bình ngành ===
rank(returns) - group_rank(returns, industry)

# === Volume bất thường so với ngành ===
rank(volume / adv20) - group_rank(volume / adv20, sector)
```

---

## Regime-Based Alpha (Kỹ Thuật Nâng Cao)
*Lý thuyết: Signal chỉ hoạt động trong một số điều kiện thị trường cụ thể — lọc theo "chế độ" (regime)*

**Khi nào áp dụng:** Khi signal của bạn bị noise nhiều → thêm điều kiện lọc sẽ tăng Sharpe đáng kể

```python
// === Template chuẩn ===
lookback = 10;
signal    = <alpha_formula>;
condition = <khi_nào_thị_trường_phù_hợp>;
trade_when(condition, signal, -1)
// -1 = giữ vị thế cũ khi không đủ điều kiện (ít turnover hơn NaN)

// === Alpha proven (Sharpe 1.94, top 1.3% IQC) ===
lookback = 10;
mr   = -rank((close - ts_delay(close, 2)) / ts_delay(close, 2) / (ts_std_dev(returns, 20) + 0.001));
when = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;
b    = trade_when(when, mr, -1);
group_vector_neut(b, ts_mean(returns, 120), subindustry)

// === Volatility + Volume regime ===
lookback    = 10;
signal      = 0.6 * (-rank(ts_delta(close, 5) / (ts_std_dev(returns, 20) + 0.001)))
              + 0.4 * rank(volume / adv20);
vol_regime  = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;
vol_surge   = ts_rank(volume / adv20, 5) > 0.7;
when        = vol_regime && vol_surge;
trade_when(when, signal, -1)

// === Momentum-conditional value ===
// Value chỉ hoạt động khi momentum không quá mạnh
lookback = 60;
value    = rank(-ts_backfill(pe));
mom_rank = ts_rank(ts_delta(close, 20), 252);
when     = mom_rank < 0.7;   // không trade khi momentum quá mạnh
trade_when(when, value, NaN)
```

**Settings khuyến nghị:** TOP3000, Subindustry neutralization, Decay 3-5, Truncation 0.05
**Lưu ý:** Dùng `-1` (giữ vị thế) thay vì `NaN` (thoát hoàn toàn) để giảm Turnover

→ Chi tiết về cú pháp nâng cao: **đọc `references/advanced-syntax.md`**

```python
# === Momentum + Volume confirmation ===
rank(ts_delta(close, 10)) * rank(ts_rank(volume, 20))

# === Mean Reversion + Low Volatility ===
rank(-ts_delta(close, 5) * -ts_std_dev(returns, 20))

# === VWAP + Momentum ===
rank(vwap - close) + rank(ts_mean(returns, 10))
```

**Lưu ý khi kết hợp:** Mỗi component nên được `rank()` trước khi cộng lại để đảm bảo cùng scale.

---

## Fundamental
*Lý thuyết: Cổ phiếu rẻ theo giá trị cơ bản (P/E, P/B thấp) sẽ outperform dài hạn — "Value Investing" định lượng hóa*

**Khi nào áp dụng:** Muốn khai thác thông tin tài chính (báo cáo quý), không phụ thuộc vào giá ngắn hạn

```python
# === Value: P/E thấp = cheap = mua ===
rank(-ts_backfill(pe))

# === Value: P/B thấp ===
rank(-ts_backfill(pb))

# === Quality: ROE cao = doanh nghiệp tốt ===
rank(ts_backfill(roe))

# === Kết hợp Value + Quality ===
rank(-ts_backfill(pe)) + rank(ts_backfill(roe))

# === Earnings Yield ===
rank(1 / ts_backfill(pe))

# === EV/EBITDA ===
rank(-ts_backfill(ebitda) / market_cap)

# === Momentum trong fundamental (Sales growth) ===
rank(ts_delta(ts_backfill(sales), 252))
```

**Settings khuyến nghị:** TOP500-TOP1000, Subindustry neutralization, Decay 10-20, Truncation 0.10
**Lookback:** 60-252 ngày (cập nhật theo quý)
**Lưu ý quan trọng:**
- LUÔN dùng `ts_backfill()` với fundamental fields để xử lý NaN giữa các kỳ báo cáo
- Turnover sẽ rất thấp (< 5%) → cần Decay thấp hoặc kết hợp với price signal

---

## Liquidity
*Lý thuyết: Cổ phiếu kém thanh khoản có premium, và bất thường thanh khoản tiết lộ thông tin*

**Khi nào áp dụng:** Khai thác illiquidity premium hoặc thanh khoản đột biến

```python
# === Amihud Illiquidity (cổ phiếu kém lỏng → premium) ===
# Illiquidity = |returns| / dollar_volume
rank(ts_mean(abs(returns) / (close * volume + 1), 20))

# === Đảo ngược: thanh khoản cao → tốt (large cap focus) ===
rank(-ts_mean(abs(returns) / (close * volume + 1), 20))

# === Volume bất thường so với trung bình ===
rank(volume / adv20)

# === Dollar volume bất thường ===
rank(dvol / ts_mean(dvol, 20))

# === Turnover ratio (volume / sharesout) ===
rank(volume / sharesout)

# === Thanh khoản giảm đột ngột → tín hiệu bearish ===
rank(-ts_delta(adv20, 5))

# === Short ratio cao → crowded short → squeeze risk ===
rank(-ts_backfill(short_ratio))
```

**Settings khuyến nghị:** TOP3000, Market neutralization, Decay 3-5, Truncation 0.05
**Cảnh báo:** `close * volume` có thể rất lớn — dùng `pasteurize()` nếu thấy NaN/Inf:
```python
rank(pasteurize(ts_mean(abs(returns) / (dvol + 1), 20)))
```
