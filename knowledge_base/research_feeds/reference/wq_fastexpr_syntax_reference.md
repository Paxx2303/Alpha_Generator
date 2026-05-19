# WorldQuant FASTEXPR Syntax Reference (2026-05-19)

## Mục đích
File này giúp Hermes và DeerFlow tạo ra các alpha **hợp lệ** theo chuẩn WorldQuant Brain FASTEXPR.  
Tránh các lỗi phổ biến: markdown, giải thích, code block, operator không hỗ trợ.

---

## 1. Cú pháp cơ bản

### Quy tắc bắt buộc
- Mỗi alpha là **một dòng duy nhất**
- Chỉ chứa **biểu thức toán học**, không có giải thích
- Sử dụng **chỉ các operator được hỗ trợ**
- Có thể dùng dấu ngoặc `()` để nhóm

### Ví dụ đúng
```python
rank(ts_mean(returns, 20) / ts_std_dev(returns, 60))
rank(ts_corr(volume, returns, 20)) * rank(ts_delta(close, 20) / ts_std_dev(close, 60))
```

### Ví dụ sai
```python
Here are 10 good alphas:
1. rank(...)
2. ts_mean(...)
```

---

## 2. Các Operator & Function được hỗ trợ

### A. Transformation
| Function          | Cú pháp                              | Mô tả                              | Ví dụ |
|-------------------|--------------------------------------|------------------------------------|-------|
| `rank`            | `rank(expr)`                         | Cross-sectional rank (0-1)         | `rank(close)` |
| `zscore`          | `zscore(expr)` hoặc `zscore(expr, N)` | Z-score theo thời gian hoặc cross-sectional | `zscore(returns)` |
| `abs`             | `abs(expr)`                          | Giá trị tuyệt đối                  | `abs(ts_delta(close, 5))` |

### B. Time Series Functions
| Function          | Cú pháp                              | Mô tả                              | Ví dụ |
|-------------------|--------------------------------------|------------------------------------|-------|
| `ts_mean`         | `ts_mean(expr, N)`                   | Trung bình trượt N ngày            | `ts_mean(returns, 20)` |
| `ts_delta`        | `ts_delta(expr, N)`                  | Chênh lệch N ngày                  | `ts_delta(close, 5)` |
| `ts_std_dev`      | `ts_std_dev(expr, N)`                | Độ lệch chuẩn trượt N ngày         | `ts_std_dev(returns, 20)` |
| `ts_corr`         | `ts_corr(expr1, expr2, N)`           | Tương quan giữa 2 chuỗi trong N ngày | `ts_corr(volume, returns, 20)` |
| `ts_rank`         | `ts_rank(expr, N)`                   | Rank trong cửa sổ N ngày           | `ts_rank(returns, 20)` |

### C. Các phép toán cơ bản
- `+`, `-`, `*`, `/`
- Dấu âm: `-expr`

---

## 3. Các trường dữ liệu được dùng phổ biến

| Field     | Mô tả                          | Ví dụ sử dụng |
|-----------|--------------------------------|---------------|
| `close`   | Giá đóng cửa                   | `ts_delta(close, 5)` |
| `volume`  | Khối lượng giao dịch           | `ts_corr(volume, returns, 20)` |
| `returns` | Tỷ suất sinh lời               | `ts_mean(returns, 20)` |
| `vwap`    | Giá trung bình theo khối lượng | `ts_delta(vwap, 5)` |

---

## 4. Các Pattern Alpha Tốt (Khuyến nghị)

### Pattern 1: Volume Confirmation
```python
rank(ts_corr(volume, returns, N))
rank(volume / ts_mean(volume, N))
rank(ts_delta(volume, N) / ts_mean(volume, N))
```

### Pattern 2: Volatility Normalization
```python
rank(ts_delta(close, N) / ts_std_dev(close, N))
rank(ts_mean(returns, N) / ts_std_dev(returns, N))
```

### Pattern 3: Price Dislocation
```python
rank(close / ts_mean(close, N) - 1)
rank(-ts_delta(close, N) / ts_std_dev(close, N))
```

### Pattern 4: Combined (Volume + Volatility)
```python
rank(ts_corr(volume, returns, 20)) * rank(ts_delta(close, 20) / ts_std_dev(close, 60))
rank(ts_mean(returns, 20) / ts_std_dev(returns, 60)) * rank(volume / ts_mean(volume, 20))
```

---

## 5. Các Lỗi Thường Gặp & Cách Tránh

| Lỗi                              | Ví dụ sai                          | Cách sửa |
|----------------------------------|------------------------------------|----------|
| Trả về markdown                  | `Here are 10 alphas: 1. rank(...)` | Chỉ trả về biểu thức |
| Dùng operator không hỗ trợ       | `ts_min`, `ts_max`, `ts_sum`       | Chỉ dùng các function ở trên |
| Dùng `N` thay vì số cụ thể       | `ts_mean(returns, N)`              | Thay bằng 5, 10, 20, 60 |
| Thêm giải thích                  | `This alpha captures momentum`     | Không thêm text |
| Dùng `ts_rank` với window quá nhỏ | `ts_rank(returns, 3)`              | Nên dùng ≥ 10 |

---

## 6. Quy tắc Tối ưu khi Tạo Alpha

1. **Luôn ưu tiên Fitness trước**
2. **Bắt buộc có volume component** (trừ khi strategy là pure momentum)
3. **Dùng volatility normalization** (`/ ts_std_dev(...)`) để giảm nhiễu
4. **Tránh motif lặp** với các alpha đã approved gần đây
5. **Dùng lookback 20 hoặc 60** thay vì chỉ 5 để giảm turnover
6. **Kết hợp nhiều motif** (volume + volatility + price dislocation)

---

## 7. Ví dụ Alpha Hoàn Chỉnh (Mẫu cho Hermes)

```python
rank(ts_corr(volume, returns, 20)) * rank(ts_delta(close, 20) / ts_std_dev(close, 60))
rank(ts_mean(returns, 20) / ts_std_dev(returns, 60)) - rank(volume / ts_mean(volume, 20))
rank(ts_delta(volume, 20) / ts_mean(volume, 60)) * rank(-ts_delta(close, 20) / ts_std_dev(close, 60))
rank(ts_rank(returns, 20) - ts_rank(volume / ts_mean(volume, 20), 20))
rank(abs(ts_delta(close, 20)) / ts_std_dev(close, 60)) * rank(volume / ts_mean(volume, 20))
```

---

**File này nên được đưa vào Theory RAG** để Hermes đọc mỗi lần tạo alpha.
**Cập nhật lần cuối:** 2026-05-19
