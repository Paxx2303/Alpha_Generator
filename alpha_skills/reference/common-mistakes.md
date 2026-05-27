# Common Mistakes — Lỗi Thường Gặp

Tổng hợp lỗi phổ biến nhất khi tạo alpha. Đọc khi gặp kết quả bất thường.

---

## 1. NaN / Lỗi Không Có Kết Quả

**Triệu chứng:** Simulation báo lỗi, Sharpe = N/A, hoặc mọi giá trị đều NaN.

**Nguyên nhân thường gặp:**

### 1a. Chia cho zero
```python
# ❌ SAI — high == low khi stock không có giao dịch
rank((close - low) / (high - low))

# ✅ ĐÚNG — thêm epsilon nhỏ
rank((close - low) / (high - low + 0.001))
```

### 1b. Log của số âm hoặc zero
```python
# ❌ SAI — volume có thể = 0 ngày không giao dịch
log(volume)

# ✅ ĐÚNG
log(volume + 1)
# hoặc
pasteurize(log(volume))
```

### 1c. Chia cho standard deviation = 0
```python
# ❌ SAI — khi cổ phiếu không biến động trong d ngày, stddev = 0
(close - ts_mean(close, 5)) / ts_std_dev(close, 5)

# ✅ ĐÚNG
pasteurize((close - ts_mean(close, 5)) / (ts_std_dev(close, 5) + 0.001))
```

### 1d. Fundamental fields không có data mọi ngày
```python
# ❌ SAI — pe chỉ update theo quý, ngày khác = NaN
rank(pe)

# ✅ ĐÚNG — backfill lấp đầy NaN
rank(ts_backfill(pe))
```

### 1e. ts_corr / ts_covariance với một chuỗi hằng số
```python
# ❌ SAI — nếu x không thay đổi trong d ngày → corr = NaN
ts_corr(rank(close), 1, 10)

# ✅ ĐÚNG — đảm bảo cả hai input đều có variance
ts_corr(rank(close), rank(volume), 10)
```

**Cách debug NaN nhanh:**
```python
# Bước 1: Thêm pasteurize() bọc toàn bộ
pasteurize( <formula của bạn> )

# Bước 2: Nếu vẫn lỗi, tách từng phần
# Chạy thử: rank(close) → có kết quả không?
# Chạy thử: rank(volume) → có kết quả không?
# Chạy thử: ts_corr(rank(close), rank(volume), 10) → có kết quả không?
```

---

## 2. Look-Ahead Bias (Lỗi Nghiêm Trọng Nhất)

**Triệu chứng:** Sharpe cực cao bất thường (> 4.0), nhưng alpha thực tế thua lỗ.

**Định nghĩa:** Dùng data của tương lai để dự báo tương lai → kết quả giả tạo.

**Ví dụ lỗi:**
```python
# ❌ NGUY HIỂM — ts_delay(close, 0) = giá hôm nay, không phải hôm qua
rank(ts_delay(close, 0) - ts_delay(close, 5))
# Điều này sử dụng close price của NGÀY HIỆN TẠI để ra lệnh, 
# thực tế không thể làm được vì chưa biết giá đóng cửa khi giao dịch

# ✅ AN TOÀN — luôn dùng Delay = 1 trong settings
# Với Delay = 1: data ngày t-1 được dùng để giao dịch ngày t
```

**Quy tắc tránh look-ahead bias:**
1. **LUÔN để Delay = 1** trong settings (mặc định an toàn)
2. Tránh dùng `ts_delay(x, 0)` — không có ý nghĩa thực tiễn
3. Không dùng data intraday nếu không hiểu rõ thời điểm data available

---

## 3. Overfitting — Alpha Tốt Giả

**Triệu chứng:** Sharpe cao trên full period nhưng một vài năm cuối rất tệ, hoặc chỉ tốt trong giai đoạn cụ thể.

**Dấu hiệu nhận biết:**
```
Year-by-year performance:
  2018: Sharpe 3.5  ← rất tốt
  2019: Sharpe 2.8
  2020: Sharpe -1.2  ← tệ (COVID crash)
  2021: Sharpe 0.3
  2022: Sharpe -0.8  ← tệ liên tiếp
  2023: Sharpe 0.5

→ Alpha này đang overfit vào 2018-2019, không ổn định
```

**Kiểm tra robustness:**
```python
# Test 1: Thay đổi lookback ±2 ngày
# Nếu Sharpe sụt mạnh khi lookback = 6 thay vì 5 → overfitting

# Test 2: Thay đổi Universe
# TOP3000 Sharpe 1.8 nhưng TOP1000 Sharpe 0.4 → signal yếu

# Test 3: Thay đổi Neutralization
# Market Sharpe 1.6 nhưng Subindustry Sharpe 0.2 → alpha chỉ là sector bet
```

**Quy tắc:** Alpha tốt = Sharpe ổn định qua ít nhất 3 năm trong backtest period.

---

## 4. Signal Quá Yếu — Sharpe 0.3-0.8 Không Cải Thiện Được

**Nguyên nhân:**
- Formula không capture được thông tin thực sự
- Lookback window không phù hợp với hiện tượng kinh tế

**Thử theo thứ tự:**
```
1. Đảo dấu formula (Sharpe 0.4 → có khi thành 1.2)
2. Thay đổi data field (close → vwap → returns)
3. Thay đổi lookback: 5 → 10 → 20 ngày
4. Thêm rank() bọc bên ngoài nếu chưa có
5. Đổi operator: ts_delta → ts_mean → ts_std_dev
6. Nếu vẫn < 0.8 sau 5 bước → bỏ formula, thử theme khác
```

---

## 5. Turnover Bất Thường

### Turnover > 100% (không hợp lệ)
```python
# ❌ SAI — formula thay đổi hướng mỗi ngày
sign(ts_delta(close, 1))  # → long/short flip mỗi ngày → Turnover 200%

# ✅ FIX — thêm smoothing
ts_decay_linear(sign(ts_delta(close, 1)), 10)
# hoặc dùng lookback dài hơn
sign(ts_delta(close, 10))
```

### Turnover < 2% (quá thấp)
```python
# Nguyên nhân: signal thay đổi rất chậm (fundamental) hoặc Decay quá cao
# Fix: Giảm Decay về 0, hoặc kết hợp với price signal nhanh hơn
```

---

## 6. Lỗi Operator Phổ Biến Nhất

| Người mới hay viết | Vấn đề | Cần viết |
|---|---|---|
| `rank(close, 20)` | rank() không nhận lookback | `ts_rank(close, 20)` |
| `corr(x, y, 10)` | operator không tồn tại | `ts_corr(x, y, 10)` |
| `std(returns, 20)` | operator không tồn tại | `ts_std_dev(returns, 20)` |
| `log_return(close, 1)` | operator không tồn tại | `log(close / ts_delay(close, 1))` |
| `ts_rank(x)` | thiếu lookback | `ts_rank(x, 20)` |
| `group_neutralize(x)` | thiếu group | `group_neutralize(x, sector)` |
| `rank(x) * rank(y)` | scale bị lệch | dùng `rank(rank(x) * rank(y))` |

---

## 7. Lỗi Logic — Alpha Ngược Chiều

**Triệu chứng:** Sharpe âm nhỏ (khoảng -0.5 đến -1.5).

**Giải thích:** Formula đúng về mặt kinh tế nhưng đang shorting cái nên long và ngược lại.

```python
# Nếu bạn muốn mua cổ phiếu có momentum (tăng nhiều)
rank(ts_delta(close, 20))   # đúng hướng

# Nhưng nếu bạn vô tình đảo dấu
-rank(ts_delta(close, 20))  # sẽ short momentum → Sharpe âm

# Fix: thêm dấu "-" ở đầu (hoặc bỏ "-" nếu đã có)
```

**Quy tắc nhớ:**
- `rank(...)` cao = long nhiều → phải đảm bảo x cao = cổ phiếu bạn muốn mua
- Nếu muốn mua cổ phiếu "giảm nhiều" → dùng `-rank(ts_delta(close, 5))` (dấu âm ở ngoài)

---

## 8. Checklist Debug Nhanh

Khi gặp bất kỳ vấn đề nào:

```
□ Có NaN? → pasteurize(), ts_backfill(), tránh chia zero
□ Sharpe âm? → thêm dấu "-" ở đầu formula
□ Sharpe < 0.5? → signal quá yếu, thử đổi theme
□ Turnover > 100%? → tăng Decay hoặc dùng lookback dài hơn
□ Turnover < 2%? → giảm Decay về 0
□ Sharpe cao bất thường (> 4.0)? → kiểm tra look-ahead bias
□ Sharpe ổn định 2018-2019 nhưng tệ 2020-2022? → overfitting
□ Operator lỗi? → xem bảng operators.md
```