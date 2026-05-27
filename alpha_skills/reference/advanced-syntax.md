# Advanced Syntax — Multi-line Expressions & Variables

WorldQuant Brain hỗ trợ cú pháp nâng cao cho phép viết alpha phức tạp, đọc được, và dễ debug.

---

## Cú Pháp Cơ Bản vs Nâng Cao

### Cách viết cơ bản (1 dòng)
```python
rank(ts_mean(returns, 10) / ts_std_dev(returns, 10))
```

### Cách viết nâng cao (multi-line với biến)
```python
lookback = 10;
signal   = ts_mean(returns, lookback) / (ts_std_dev(returns, lookback) + 0.001);
rank(signal)
```

**Quy tắc cú pháp:**
- Mỗi câu lệnh kết thúc bằng `;`
- Dòng cuối cùng KHÔNG có `;` — đó là giá trị trả về của alpha
- `lookback` là biến đặc biệt khai báo window mặc định
- Tên biến: chữ thường, underscore, không dùng tên operator đã có

---

## `lookback` — Biến Đặc Biệt

```python
// Khai báo lookback ở đầu — bắt buộc với một số operator
lookback = 20;

// Sau đó dùng trong các operator
signal = ts_mean(returns, lookback);
rank(signal)
```

**Khi nào cần `lookback`?** Khi formula phức tạp hoặc dùng nhiều operator với cùng window. Giúp thay đổi lookback toàn bộ formula chỉ bằng 1 chỗ.

---

## Variable Assignment

```python
// Gán biến trung gian
vol   = ts_std_dev(returns, 20);
ret5  = ts_delta(close, 5);
signal = -ret5 / (vol + 0.001);
rank(signal)
```

**Lợi ích:**
- Tái sử dụng tính toán tốn kém (tính 1 lần, dùng nhiều lần)
- Dễ debug từng phần
- Code rõ ràng hơn

**Ví dụ phức tạp — alpha từ IQC top 1.3%:**
```python
lookback = 10;
avg_ret  = power(ts_product(returns + 1, lookback), 1 / lookback);
a        = zscore(avg_ret);
when     = ts_rank(ts_std_dev(returns, 60), 126) > 0.55;
b        = trade_when(when, a, -1);
group_vector_neut(b, ts_mean(returns, 120), subindustry)
```

---

## Comments — Ghi Chú Trong Formula

```python
// Đây là comment kiểu C++
lookback = 20;  // lookback 20 ngày

# Đây cũng là comment
vol = ts_std_dev(returns, 20);  # volatility
rank(-vol)
```

**Dùng comment để:**
- Giải thích ý tưởng kinh tế
- Ghi nhớ settings tốt nhất
- Mark phần đang thử nghiệm

---

## Conditional Operators (Logic)

```python
// Toán tử logic
&&    // AND — cả hai điều kiện đúng
||    // OR  — ít nhất một điều kiện đúng
!     // NOT — đảo ngược

// Ví dụ:
when_vol  = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;
when_vol2 = ts_rank(volume / adv20, 5) > 0.7;
when      = when_vol && when_vol2;   // cả hai cùng đúng
```

**Dùng `or()` và `and()` thay vì `||` và `&&` nếu muốn:**
```python
and(condition1, condition2)  // tương đương condition1 && condition2
or(condition1, condition2)   // tương đương condition1 || condition2
```

---

## Regime-Based Alpha — Kỹ Thuật Quan Trọng Nhất

*Ý tưởng: Chỉ giao dịch khi thị trường ở đúng "chế độ" (regime) phù hợp với signal*

```python
// Template chuẩn:
lookback = 10;
signal = <alpha_formula>;
condition = <when_to_trade>;
trade_when(condition, signal, -1)
// -1 = giữ nguyên vị thế cũ khi không đủ điều kiện
// NaN = thoát vị thế hoàn toàn khi không đủ điều kiện
```

**Ví dụ proven (Sharpe 1.94, Fitness 1.35 — jglazar top 1.3%):**
```python
lookback = 10;
// Signal: mean reversion chuẩn hóa theo volatility
mr = -rank((close - ts_delay(close, 2)) / ts_delay(close, 2) / ts_std_dev(returns, 20));

// Regime: chỉ trade khi volatility đang cao (thị trường đang biến động)
when = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;

// Kết hợp
alpha = trade_when(when, mr, -1);
group_vector_neut(alpha, ts_mean(returns, 120), subindustry)
```

**Điều kiện regime phổ biến:**

| Regime | Condition | Ý nghĩa |
|---|---|---|
| Volatility cao | `ts_rank(ts_std_dev(returns,22), 252) > 0.55` | Market đang bất ổn |
| Volume đột biến | `ts_rank(volume / adv20, 5) > 0.7` | Có trading activity mạnh |
| Momentum mạnh | `ts_rank(abs(ts_delta(close,20)), 252) > 0.6` | Giá đang trend |
| Volatility thấp | `ts_rank(ts_std_dev(returns,22), 252) < 0.3` | Thị trường yên tĩnh |

**Kết hợp 2 regime:**
```python
// Chỉ trade khi vol CAO và volume CAO
when = (ts_rank(ts_std_dev(returns, 22), 252) > 0.55) &&
       (ts_rank(volume / adv20, 5) > 0.7);
```

---

## `group_vector_neut` — Orthogonalization Nâng Cao

Khác với `group_neutralize`, `group_vector_neut` loại bỏ thành phần tương quan với một vector driver cụ thể trong nhóm:

```python
// Cú pháp:
group_vector_neut(x, driver, group)

// Ví dụ: loại bỏ exposure với momentum dài hạn trong từng subindustry
signal = rank(-ts_delta(close, 5));
group_vector_neut(signal, ts_mean(returns, 120), subindustry)

// Loại bỏ size factor trong mỗi sector
group_vector_neut(signal, log(market_cap), sector)
```

**Khi nào dùng:** Khi muốn alpha không bị drive bởi một factor cụ thể (momentum, size, value) nhưng vẫn giữ được cross-sectional signal trong mỗi nhóm.

---

## Kết Hợp Thực Tế — Alpha Pattern Nâng Cao

```python
// Pattern 1: Vol-weighted mean reversion + regime filter
lookback = 10;
mr       = -rank(ts_delta(close, 5) / (ts_std_dev(returns, 20) + 0.001));
vol_regime = ts_rank(ts_std_dev(returns, 22), 252) > 0.5;
trade_when(vol_regime, mr, NaN)

// Pattern 2: Multi-component alpha với variable
vol  = ts_std_dev(returns, 20);
ret  = ts_delta(close, 5);
vol5 = ts_rank(volume, 20);
signal = -0.6 * rank(ret / (vol + 0.001)) + 0.4 * rank(vol5);
rank(signal)

// Pattern 3: Fundamental + momentum regime
lookback = 60;
value  = rank(-ts_backfill(pe));
mom    = ts_rank(ts_delta(close, 20), 252);
when   = mom > 0.5;   // chỉ mua value khi không momentum mạnh
trade_when(when, value, NaN)
```

---

## Lỗi Cú Pháp Thường Gặp

```python
// ❌ SAI — thiếu dấu ; giữa các dòng
vol = ts_std_dev(returns, 20)
rank(vol)

// ✅ ĐÚNG
vol = ts_std_dev(returns, 20);
rank(vol)

// ❌ SAI — dòng cuối có dấu ;
vol = ts_std_dev(returns, 20);
rank(vol);     // dòng cuối không được có ;

// ✅ ĐÚNG
vol = ts_std_dev(returns, 20);
rank(vol)

// ❌ SAI — dùng tên biến trùng với operator
rank = ts_std_dev(returns, 20);  // "rank" là tên operator!
rank(rank)

// ✅ ĐÚNG
vol_rank = ts_std_dev(returns, 20);
rank(vol_rank)
```