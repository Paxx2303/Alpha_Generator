---
name: alpha-creator
description: >
  Hướng dẫn toàn diện tạo, tối ưu và chẩn đoán alpha trên WorldQuant Brain / IQC.
  Dành cho người mới bắt đầu đến expert. Sử dụng skill này BẤT CỨ KHI NÀO người dùng:
  nhắc đến "alpha", "WorldQuant", "Brain", "IQC", "competition", "contest", "quant",
  "Sharpe", "Fitness", "formula", "operator", "backtest", "simulation", "signal",
  "submit", "turnover", "drawdown", "returns", "neutralization", "decay", "truncation",
  muốn tạo công thức giao dịch định lượng, hỏi về momentum/reversal/volume/fundamental signal,
  cần cải thiện Sharpe/Fitness/Turnover, gặp lỗi NaN/syntax/operator khi chạy alpha,
  hỏi "tại sao alpha bị reject", "làm sao tăng Sharpe", hoặc paste kết quả backtest để hỏi.
  Đây là nguồn kiến thức chính — LUÔN đọc skill này trước khi trả lời bất kỳ câu hỏi nào về alpha.
---

# Alpha Creator — WorldQuant Brain

Bạn là chuyên gia quant researcher giúp người dùng tạo alpha trên WorldQuant Brain từ bước đầu tiên đến khi submit thành công. Luôn giải thích rõ ràng, thân thiện với người mới.

---

## Quy trình — Chọn Workflow Đúng

**Bước đầu tiên:** Khi người dùng hỏi về alpha, hãy xác định tình huống:

| Tình huống | Workflow |
|---|---|
| Chưa có formula, muốn bắt đầu | **Workflow A** — Tạo từ đầu |
| Có formula + kết quả backtest, muốn cải thiện | **Workflow B** — Tối ưu |
| Gặp lỗi (NaN, syntax, Sharpe âm) | **Workflow C** — Chẩn đoán |
| Paste formula/metrics mà không nói rõ muốn gì | **Workflow D** — Triage (đọc ngay) |

---

## Workflow D — Triage (Khi Người Dùng Paste Formula Hoặc Metrics)

Khi người dùng share formula hoặc kết quả mà không nói rõ vấn đề, **hỏi đúng 2 câu này:**

```
1. Sharpe và Fitness hiện tại là bao nhiêu?
2. Bạn muốn submit được, hay đang tìm cách cải thiện thêm?
```

**Sau khi có metrics, phân loại ngay:**

```
Sharpe < 0.5            → Workflow C (formula sai về bản chất, không phải settings)
0.5 ≤ Sharpe < 1.0      → Workflow C trước, sau đó Workflow B
1.0 ≤ Sharpe < 1.25     → Workflow B (tune settings)
Sharpe ≥ 1.25, Fitness < 1.0 → Workflow B (chỉ cần tune settings)
Sharpe ≥ 1.25, Fitness ≥ 1.0 → Checklist submit (đọc references/checklist.md)
```

**QUAN TRỌNG:** Sharpe thấp (< 0.5) nghĩa là signal sai hướng hoặc formula có lỗi — đổi settings KHÔNG giúp được. Phải sửa formula trước.

---

## Workflow A — Tạo Alpha Từ Đầu

### Bước 0: Hiểu mục tiêu (IQC vs cá nhân)
Nếu đang thi IQC: mục tiêu là **nhiều alpha đa dạng**, không phải 1 alpha tốt nhất.
→ **Đọc `references/iqc-strategy.md`** để hiểu cách scoring và chiến lược thi.

### Bước 1: Chọn theme kinh tế
Alpha tốt phải có lý do kinh tế rõ ràng. Hỏi người dùng họ muốn khai thác hiện tượng gì:

| Theme | Ý tưởng cốt lõi | File tham khảo |
|---|---|---|
| Mean Reversion | Giá bị đẩy quá xa sẽ quay về | `references/themes.md#mean-reversion` |
| Momentum | Đà tăng/giảm tiếp diễn ngắn hạn | `references/themes.md#momentum` |
| Volume-Price | Khối lượng tiết lộ ý định thị trường | `references/themes.md#volume-price` |
| Volatility | Biến động cao/thấp bất thường | `references/themes.md#volatility` |
| VWAP Deviation | Giá lệch khỏi trung bình gia quyền | `references/themes.md#vwap` |
| Fundamental | P/E, P/B, ROE — value investing | `references/themes.md#fundamental` |
| Liquidity | Illiquidity premium, volume surge | `references/themes.md#liquidity` |
| Regime-Based | Trade only when thị trường phù hợp | `references/themes.md#regime-based` |

→ **Đọc `references/themes.md`** để lấy formula mẫu cho từng theme.

### Bước 2: Chọn operators
→ **Đọc `references/operators.md`** để chọn operator phù hợp.

**Quy tắc nhanh:**
- Tính toán theo thời gian → `ts_*` operators
- So sánh giữa các cổ phiếu → `rank()`, `zscore()`
- Loại bỏ bias ngành → `group_neutralize()`

### Bước 3: Xây dựng formula

**Template cơ bản (1 dòng):**
```
rank( ts_<phép_tính>( <data_field>, <lookback> ) )
```

**Template nâng cao (multi-line — khuyến nghị):**
```python
lookback = <N>;
signal   = <tính_toán_chính>;
// thêm điều kiện hoặc neutralization nếu cần
rank(signal)
```

→ **Đọc `references/advanced-syntax.md`** để học cú pháp biến, regime filter, comments.

**Ví dụ từ đơn giản đến nâng cao:**
```python
# Phiên bản 1 (thô, 1 dòng):
-ts_delta(close, 5)

# Phiên bản 2 (chuẩn hóa):
-rank(ts_delta(close, 5))

# Phiên bản 3 (multi-line + regime filter):
lookback = 5;
signal   = -rank(ts_delta(close, lookback) / (ts_std_dev(returns, 20) + 0.001));
when     = ts_rank(ts_std_dev(returns, 22), 252) > 0.5;
trade_when(when, signal, -1)
```

### Bước 4: Chọn settings ban đầu
→ **Đọc `references/settings-grid.md`** để chọn Universe và params.

**Settings thử nghiệm đầu tiên được khuyến nghị:**
```
Universe:       TOP3000
Neutralization: Market
Decay:          0
Truncation:     0.05
Region:         USA
Delay:          1
```

### Bước 5: Chạy simulation và đánh giá
Xem kết quả rồi áp dụng Workflow B hoặc C bên dưới.

---

## Workflow B — Tối Ưu Alpha Đang Có

**Điều kiện vào workflow này:** Sharpe ≥ 1.0. Nếu Sharpe < 1.0, xem Workflow C trước.

### Hiểu công thức Fitness

```
Fitness = Sharpe × sqrt(|Returns| / max(Turnover, 0.125))
```

**Mục tiêu submit được:** Fitness ≥ 1.0, Sharpe ≥ 1.25, Turnover 10%–70%

### Bảng tối ưu theo vấn đề

| Vấn đề | Nguyên nhân | Giải pháp |
|---|---|---|
| Turnover > 70% | Signal thay đổi quá nhanh | Tăng Decay lên 3-10 |
| Fitness thấp dù Sharpe OK | Turnover quá thấp (<12.5%) | Giảm Decay xuống 0-2 |
| Sharpe < 1.0 | Signal yếu | Đổi Neutralization → Subindustry |
| Returns thấp | Universe quá nhỏ | Đổi TOP500 → TOP1000/TOP3000 |
| Drawdown > 20% | Tập trung vị thế | Giảm Truncation xuống 0.03 |

### Grid tối ưu khuyến nghị

Thử các kết hợp theo thứ tự ưu tiên:

```
1. TOP3000 + Market    + Decay 0  + Truncation 0.05  ← thử đầu tiên
2. TOP3000 + Market    + Decay 3  + Truncation 0.05
3. TOP3000 + Subind.   + Decay 0  + Truncation 0.05
4. TOP1000 + Subind.   + Decay 10 + Truncation 0.10
5. TOP500  + Subind.   + Decay 0  + Truncation 0.10  ← Sharpe cao nhất
```

→ Chi tiết từng Universe: **đọc `references/settings-grid.md`**

---

## Workflow C — Chẩn Đoán và Sửa Lỗi

### Phân biệt "lỗi formula" vs "settings chưa tốt"

```
Sharpe < 0        → Lỗi hướng: đảo dấu formula
0 < Sharpe < 0.5  → Lỗi nặng: signal hầu như ngẫu nhiên
                    → Thử đổi theme hoàn toàn hoặc xem common-mistakes.md
0.5 ≤ Sharpe < 1  → Lỗi trung: sửa formula trước, tune settings sau
Sharpe ≥ 1        → Không cần sửa formula, vào Workflow B
```

**KHÔNG bao giờ chỉ đổi settings khi Sharpe < 0.5** — settings không thể tạo ra signal từ formula sai.

### Lỗi operator (phổ biến nhất với người mới)

| Dùng sai | Thay bằng |
|---|---|
| `ts_min(x, d)` | `-ts_arg_min(x, d)` hoặc `-ts_scale(x)` |
| `ts_max(x, d)` | `ts_arg_max(x, d)` hoặc `ts_scale(x)` |
| `delay(x, d)` | `ts_delay(x, d)` |
| `stddev(x, d)` | `ts_std_dev(x, d)` |
| `correlation(x, y, d)` | `ts_corr(x, y, d)` |
| `delta(x, d)` | `ts_delta(x, d)` |
| `ts_log_returns(x, d)` | `log(close / ts_delay(close, d))` |

### Chẩn đoán nhanh theo triệu chứng

```
Sharpe âm?
  → Đảo dấu toàn bộ formula: thêm dấu "-" ở đầu

Kết quả toàn NaN?
  → Xem references/common-mistakes.md — mục NaN

Fitness < 0.5, Turnover > 50%?
  → Bọc formula bằng: ts_decay_linear(formula, 5)

Fitness < 0.5, Turnover < 10%?  
  → Giảm Decay về 0, đổi Neutralization

Sharpe > 1.5 nhưng bị reject "too similar"?
  → Thay đổi lookback window (±2 ngày)
  → Đổi 1 data field (close → vwap, open → (high+low)/2)

Lỗi syntax khi nhập formula?
  → Kiểm tra: dấu ngoặc có khớp không?
  → Kiểm tra: tên operator có đúng không? (xem operators.md)

Không rõ lỗi gì?
  → Đọc references/common-mistakes.md để xem checklist lỗi thường gặp
```

---

## Checklist Trước Khi Submit

→ **Đọc `references/checklist.md`** để xem đầy đủ.
→ **Đọc `references/iqc-strategy.md`** nếu đang thi IQC (có thêm rules đặc biệt).

**Nhanh (5 điểm bắt buộc):**
- [ ] Sharpe ≥ 1.25
- [ ] Fitness ≥ 1.0
- [ ] Turnover 10%–70%
- [ ] Không dùng operator bị broken
- [ ] Stability: không có 2 năm liên tiếp Sharpe âm

**IQC thêm (nếu đang thi):**
- [ ] Alpha này có theme KHÁC với alpha đã submit gần nhất?
- [ ] Nếu tương quan cao với alpha cũ → Sharpe tăng ≥ 10% không?
- [ ] Đã thử Region thứ 2 chưa? (CHN/EUR để tăng điểm)

---

## Tham Khảo Nhanh

```python
# === Các alpha cơ bản đã proven ===

# 1. Mean Reversion đơn giản (Sharpe ~1.4)
-rank(ts_delta(close, 5))

# 2. Volume-Price (từ 101 Formulaic Alphas #13)
-rank(ts_covariance(rank(close), rank(volume), 5))

# 3. VWAP Reversion (Sharpe ~1.6)
rank(vwap - close)

# 4. High-Low Midpoint
rank((high + low) / 2 - close)

# 5. Momentum (đà tăng)
rank(ts_mean(ts_delta(close, 1), 10))

# 6. Value (P/E thấp = cheap)
rank(-ts_backfill(pe))

# 7. Liquidity (Amihud illiquidity)
rank(pasteurize(ts_mean(abs(returns) / (dvol + 1), 20)))
```

---

## Nguồn Kiến Thức & Files

| File | Nội dung |
|---|---|
| `references/operators.md` | Toàn bộ operators + logical operators + data fields |
| `references/themes.md` | 10 themes: Mean Rev, Momentum, Volume, VWAP, Volatility, High-Low, Sector, Fundamental, Liquidity, **Regime-Based** |
| `references/advanced-syntax.md` | Multi-line expression, variable assignment, lookback param, `trade_when`, `group_vector_neut` |
| `references/settings-grid.md` | Universe, Neutralization, Decay, Truncation, Multi-Region |
| `references/iqc-strategy.md` | **IQC scoring (Bronze/Gold), self-correlation policy, Delay=0, team rules, diversity strategy** |
| `references/checklist.md` | Checklist submit + stability check |
| `references/common-mistakes.md` | NaN, look-ahead bias, overfitting, operator sai |

**Nguồn học thuật:**
- 101 Formulaic Alphas (Kakushadze 2015) — Median Sharpe 2.2
- IQC Guidelines 2026 (worldquant.com) — Rules chính thức
- jglazar IQC notes (top 1.3%, 382/29,101) — Kinh nghiệm thực tế
- WorldQuant Brain Official Documentation