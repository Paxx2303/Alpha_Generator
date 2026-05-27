# Operators Reference — WorldQuant Brain

Tất cả operator hợp lệ với ví dụ cụ thể. Dùng file này khi cần chọn operator phù hợp.

---

## Time Series Operators (`ts_*`)
*Tính toán theo trục thời gian — so sánh mỗi cổ phiếu với chính nó trong quá khứ*

| Operator | Cú pháp | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `ts_delta` | `ts_delta(x, d)` | Thay đổi so với d ngày trước | `ts_delta(close, 5)` → close hôm nay - close 5 ngày trước |
| `ts_delay` | `ts_delay(x, d)` | Giá trị d ngày trước | `ts_delay(close, 1)` → giá đóng cửa hôm qua |
| `ts_mean` | `ts_mean(x, d)` | Trung bình d ngày | `ts_mean(volume, 20)` → volume trung bình 20 ngày |
| `ts_std_dev` | `ts_std_dev(x, d)` | Độ lệch chuẩn d ngày | `ts_std_dev(close, 20)` → volatility 20 ngày |
| `ts_rank` | `ts_rank(x, d)` | Thứ hạng trong d ngày gần nhất (0→1) | `ts_rank(volume, 20)` → 1.0 = volume cao nhất 20 ngày |
| `ts_corr` | `ts_corr(x, y, d)` | Tương quan giữa x và y trong d ngày | `ts_corr(close, volume, 10)` |
| `ts_covariance` | `ts_covariance(x, y, d)` | Hiệp phương sai trong d ngày | `ts_covariance(rank(close), rank(volume), 5)` |
| `ts_sum` | `ts_sum(x, d)` | Tổng d ngày | `ts_sum(volume, 5)` → tổng volume 5 ngày |
| `ts_decay_linear` | `ts_decay_linear(x, d)` | Trung bình gia quyền tuyến tính (ngày gần = trọng số cao) | `ts_decay_linear(signal, 5)` → làm mượt signal |
| `ts_scale` | `ts_scale(x)` | Chuẩn hóa về tổng = 1 | `ts_scale(close)` |
| `ts_zscore` | `ts_zscore(x, d)` | Z-score theo d ngày | `ts_zscore(close, 20)` |
| `ts_arg_max` | `ts_arg_max(x, d)` | Số ngày kể từ đỉnh cao nhất trong d ngày | `ts_arg_max(close, 20)` → 0 nếu hôm nay là đỉnh |
| `ts_arg_min` | `ts_arg_min(x, d)` | Số ngày kể từ đáy thấp nhất trong d ngày | `ts_arg_min(close, 20)` |
| `ts_backfill` | `ts_backfill(x)` | Điền giá trị NaN bằng giá trị gần nhất | `ts_backfill(close)` |
| `ts_av_diff` | `ts_av_diff(x, d)` | Chênh lệch với trung bình d ngày | `ts_av_diff(close, 20)` = close - ts_mean(close,20) |
| `ts_regression` | `ts_regression(y, x, d, lag, type)` | Hệ số hồi quy tuyến tính | `ts_regression(close, volume, 20, 0, "slope")` |
| `trade_when` | `trade_when(cond, x, y)` | Trả về x nếu cond đúng, y nếu sai | `trade_when(volume > 0, x, NaN)` |
| `ts_product` | `ts_product(x, d)` | Tích d ngày (dùng cho compound returns) | `ts_product(1 + returns, 20) - 1` |
| `ts_moment` | `ts_moment(x, d, k)` | Moment bậc k trong d ngày (k=3: skewness) | `ts_moment(returns, 20, 3)` |
| `ts_entropy` | `ts_entropy(x, d)` | Entropy phân phối giá trị trong d ngày | `ts_entropy(volume, 20)` |
| `pasteurize` | `pasteurize(x)` | Chuyển NaN/Inf thành 0, giữ giá trị khác | `pasteurize(log(volume / adv20))` |
| `filter` | `filter(x, cond)` | Chỉ giữ giá trị khi cond = true, còn lại = NaN | `filter(rank(close), volume > adv20)` |
| `vector_neut` | `vector_neut(x, y)` | Loại bỏ thành phần y từ x (orthogonalize) | `vector_neut(signal, rank(market_cap))` |
| `vector_proj` | `vector_proj(x, y)` | Chiếu x lên y (phần giống y nhất) | `vector_proj(signal, rank(returns))` |
| `sigmoid` | `sigmoid(x)` | Hàm sigmoid = 1/(1+e^-x), ép về (0,1) | `sigmoid(zscore(close))` |
| `tanh` | `tanh(x)` | Hàm tanh, ép về (-1,1) | `tanh(zscore(volume))` |
| `is_nan` | `is_nan(x)` | Trả về 1 nếu x = NaN, else 0 | `filter(x, !is_nan(volume))` |
| `kth_element` | `kth_element(x, d, k)` | Giá trị thứ k (nhỏ nhất→lớn nhất) trong d ngày | `kth_element(close, 20, 5)` → giá trị thứ 5 nhỏ nhất |
| `last_diff_value` | `last_diff_value(x, d)` | Giá trị cuối cùng khác với giá trị hiện tại trong d ngày | `last_diff_value(close, 5)` |
| `days_from_last_change` | `days_from_last_change(x, hump)` | Số ngày kể từ lần thay đổi cuối (vượt ngưỡng hump) | `days_from_last_change(close, 0.01)` |

**Lookback windows phổ biến:** 5 (1 tuần), 10 (2 tuần), 20 (1 tháng), 60 (1 quý)

---

## Cross-Sectional Operators
*So sánh giữa tất cả cổ phiếu trong cùng một ngày*

| Operator | Cú pháp | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `rank` | `rank(x)` | Thứ hạng (0→1) trong universe | `rank(close)` → 1.0 = giá cao nhất trong universe |
| `zscore` | `zscore(x)` | Z-score cross-sectional | `zscore(volume)` → chuẩn hóa volume ngày hôm nay |
| `normalize` | `normalize(x)` | Chuẩn hóa tổng = 1 | `normalize(signal)` |
| `scale` | `scale(x)` | Scale về leverage = 1 | `scale(signal)` |
| `winsorize` | `winsorize(x, std)` | Cắt outlier tại ±std độ lệch chuẩn | `winsorize(signal, 4)` |
| `quantile` | `quantile(x, driver, n)` | Chia thành n nhóm theo driver | `quantile(returns, market_cap, 5)` |

**Quan trọng:** `rank()` là operator được dùng phổ biến nhất — luôn thử bọc formula bằng `rank()` trước.

---

## Group Operators
*Tính toán trong nhóm (ngành, sector)*

| Operator | Cú pháp | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `group_neutralize` | `group_neutralize(x, group)` | Trừ đi trung bình nhóm | `group_neutralize(rank(close), sector)` |
| `group_rank` | `group_rank(x, group)` | Rank trong nội bộ nhóm | `group_rank(close, industry)` |
| `group_zscore` | `group_zscore(x, group)` | Z-score trong nhóm | `group_zscore(volume, sector)` |
| `group_vector_neut` | `group_vector_neut(x, driver, group)` | Loại bỏ thành phần tương quan với driver trong từng nhóm | `group_vector_neut(signal, ts_mean(returns,120), subindustry)` |

**Groups hợp lệ:** `market`, `sector`, `industry`, `subindustry`, `country`, `exchange`

**Khác nhau giữa `group_neutralize` và `group_vector_neut`:**
- `group_neutralize(x, sector)` → trừ trung bình sector (đơn giản)
- `group_vector_neut(x, momentum, sector)` → loại bỏ thành phần momentum trong mỗi sector (phức tạp, mạnh hơn)

---

## Vector Operators
*Tính trên toàn bộ vector alpha (scalar output)*

| Operator | Cú pháp | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `vec_avg` | `vec_avg(x)` | Trung bình của toàn bộ alpha vector | `x - vec_avg(x)` → demeaned |
| `vec_sum` | `vec_sum(x)` | Tổng của toàn bộ alpha vector | `x / vec_sum(abs(x))` → normalized |

---

## Logical Operators

| Operator | Cú pháp | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `&&` | `cond1 && cond2` | AND — cả hai đúng | `vol_high && vol_surge` |
| `\|\|` | `cond1 \|\| cond2` | OR — ít nhất một đúng | `cheap \|\| momentum` |
| `!` | `!cond` | NOT — đảo ngược | `!is_nan(pe)` |
| `and()` | `and(cond1, cond2)` | AND (dạng hàm) | `and(vol>1, ret>0)` |
| `or()` | `or(cond1, cond2)` | OR (dạng hàm) | `or(vol>2, ret>0.05)` |
| `is_nan` | `is_nan(x)` | 1 nếu NaN, 0 nếu không | `filter(x, !is_nan(pe))` |

---

## Arithmetic Operators

| Operator | Cú pháp | Ví dụ |
|---|---|---|
| `abs` | `abs(x)` | `abs(ts_delta(close, 5))` → độ lớn thay đổi |
| `log` | `log(x)` | `log(close / ts_delay(close, 1))` → log returns |
| `sign` | `sign(x)` | `sign(ts_delta(close, 1))` → +1 hoặc -1 |
| `sqrt` | `sqrt(x)` | `sqrt(volume)` |
| `power` | `power(x, e)` | `power(rank(close), 2)` |
| `max` | `max(x, y)` | `max(signal, 0)` → giữ chỉ phần dương |
| `min` | `min(x, y)` | `min(signal, 1)` |
| `if_else` | `if_else(cond, x, y)` | `if_else(volume > ts_mean(volume,20), rank(close), 0)` |

---

## Data Fields (Inputs)

### Price & Volume (phổ biến nhất)

| Field | Mô tả |
|---|---|
| `open` | Giá mở cửa |
| `high` | Giá cao nhất ngày |
| `low` | Giá thấp nhất ngày |
| `close` | Giá đóng cửa (dùng nhiều nhất) |
| `volume` | Khối lượng giao dịch (số cổ phiếu) |
| `dvol` | Dollar volume = close × volume (thanh khoản thực) |
| `vwap` | Volume-Weighted Average Price |
| `returns` | Daily returns = (close - prev_close) / prev_close |
| `adv5` | Average Daily Volume 5 ngày |
| `adv20` | Average Daily Volume 20 ngày (proxy cho thanh khoản) |

### Market & Size

| Field | Mô tả |
|---|---|
| `market_cap` | Vốn hóa thị trường (= close × sharesout) |
| `cap` | Alias của market_cap trong một số context |
| `sharesout` | Số cổ phiếu lưu hành |

### Fundamental (cần WorldQuant data subscription)

| Field | Mô tả | Ví dụ dùng |
|---|---|---|
| `pb` | Price-to-Book ratio | `rank(-pb)` → value investing |
| `pe` | Price-to-Earnings ratio | `rank(-pe)` → cheap stocks |
| `ps` | Price-to-Sales ratio | `rank(-ps)` |
| `pcf` | Price-to-Cash-Flow | `rank(-pcf)` |
| `debt_to_assets` | Đòn bẩy tài chính | `rank(-debt_to_assets)` |
| `roe` | Return on Equity | `rank(roe)` |
| `roa` | Return on Assets | `rank(roa)` |
| `sales` | Doanh thu | `rank(ts_delta(sales, 252))` |
| `ebitda` | EBITDA | `rank(ebitda / market_cap)` |

### Short Selling & Sentiment

| Field | Mô tả |
|---|---|
| `short_ratio` | Short interest / avg volume (borrow pressure) |
| `short_interest` | Số cổ phiếu đang bị short |

**Lưu ý với fundamental fields:**
- Cập nhật theo quý (quarterly) — dùng lookback ≥ 60 ngày
- Kết hợp với `ts_backfill()` để tránh NaN giữa các kỳ báo cáo
- Ví dụ an toàn: `rank(ts_backfill(pe))` thay vì `rank(pe)` trực tiếp

---

## Operators BỊ BROKEN — KHÔNG DÙNG

```
❌ ts_min      → dùng -ts_arg_min hoặc -ts_scale
❌ ts_max      → dùng ts_arg_max hoặc ts_scale  
❌ delay       → dùng ts_delay
❌ stddev      → dùng ts_std_dev
❌ correlation → dùng ts_corr
❌ delta       → dùng ts_delta
❌ ts_log_returns → dùng log(close / ts_delay(close, d))
```