# Checklist Trước Khi Submit Alpha

Đi qua từng mục trước khi bấm Submit. Alpha bị reject sẽ ảnh hưởng đến IQC score.

---

## ✅ Checklist Bắt Buộc (Pass hết mới submit)

### 1. Metrics cơ bản
- [ ] **Sharpe ≥ 1.25** trên toàn bộ backtest period
- [ ] **Fitness ≥ 1.0**
- [ ] **Turnover 10%–70%** (quá thấp = không đủ trading, quá cao = phí giao dịch ăn hết)
- [ ] **Drawdown < 25%** (kiểm tra tab "Performance")
- [ ] **Returns > 0%** (alpha sinh lời dương)

### 2. Kiểm tra formula
- [ ] Không dùng operator bị broken (ts_min, ts_max, delay, stddev, correlation, delta, ts_log_returns)
- [ ] Dấu ngoặc đóng mở khớp nhau
- [ ] Tên operator viết đúng chính tả
- [ ] Lookback window ≥ 2 (không dùng lookback = 1)

### 3. Kiểm tra settings
- [ ] Delay = 1 (KHÔNG dùng Delay = 0, trừ khi chủ ý dùng same-day data)
- [ ] Region đã chọn (thường là USA)
- [ ] Universe phù hợp với signal

### 4. Stability check — Quan trọng nhất, thường bị bỏ qua
- [ ] **Xem year-by-year performance** (tab "Yearly" hoặc "Performance by Year")
- [ ] Không có năm nào Sharpe < -0.5
- [ ] Sharpe dương trong ít nhất 3/4 năm trong backtest period
- [ ] Không có 2 năm liên tiếp Sharpe âm
- [ ] Năm tệ nhất: Sharpe ≥ -0.5 (nếu tệ hơn → alpha không ổn định)

**Ví dụ alpha bị reject dù Sharpe tổng 1.8:**
```
2018: 3.5  2019: 2.8  2020: -1.2  2021: 0.3  2022: -0.8  → UNSTABLE
```
**Ví dụ alpha ổn định, Sharpe tổng 1.4:**
```
2018: 1.8  2019: 1.2  2020: 0.6  2021: 1.5  2022: 1.1  → STABLE ✅
```

---

## ⚠️ Checklist Nâng Cao (Tăng cơ hội pass)

### Độc lập với alpha đã có
- [ ] Đã thử ít nhất 2 lookback window khác nhau
- [ ] Formula không chỉ là copy từ 101 Formulaic Alphas mà không biến đổi
- [ ] Có yếu tố độc đáo riêng (data field khác, operator kết hợp khác)

### Robustness
- [ ] Test trên ít nhất 2 Universe khác nhau → kết quả hợp lý
- [ ] Test trên ít nhất 2 Neutralization khác nhau → kết quả nhất quán
- [ ] Thay đổi lookback ±2 ngày không làm Sharpe sụt đột ngột

### Documentation (nếu platform yêu cầu)
- [ ] Có thể giải thích alpha bằng 1-2 câu rõ ràng
- [ ] Có lý do kinh tế xác đáng tại sao alpha hoạt động

---

## 🔍 Kiểm Tra Nhanh Trước Submit

```
0. Nếu gặp bất kỳ vấn đề nào → đọc references/common-mistakes.md

1. Nhìn vào số Fitness → < 1.0? Dừng lại, đọc settings-grid.md

2. Nhìn vào Turnover:
   - > 70%? → Tăng Decay
   - < 10%? → Giảm Decay hoặc đổi Universe lớn hơn

3. Nhìn vào biểu đồ PnL:
   - Đi lên đều? ✅
   - Đi lên rồi đột ngột sụt? ⚠️ (kiểm tra có fit vào 1 giai đoạn cụ thể không)
   - Đi ngang rồi bùng lên cuối? ⚠️ (có thể overfitting gần đây)

4. Nhìn year-by-year (BƯỚC QUAN TRỌNG NHẤT):
   - Năm nào Sharpe âm? → Alpha không ổn định
   - 2+ năm liên tiếp Sharpe âm? → Không submit
   - Năm tệ nhất Sharpe < -0.5? → Không submit
   - Năm nào Sharpe rất cao bất thường? → Cần điều tra overfitting

5. So sánh với baseline:
   - Fitness của bạn so với 3 alpha đã submit trước?
   - Nếu thấp hơn nhiều → đừng submit, tiếp tục tune
```

---

## ❌ Lý Do Thường Bị Reject

| Lý do | Cách tránh |
|---|---|
| Sharpe < 1.0 | Cải thiện formula trước |
| Fitness < 1.0 | Tune settings (xem settings-grid.md) |
| "Too similar to existing" | Thay đổi lookback hoặc data field |
| "Overfitting" | Test trên nhiều period, không cherry-pick settings |
| Turnover ngoài khoảng | Điều chỉnh Decay |
| Operator error | Kiểm tra danh sách broken operators |

---

## 📊 Template Ghi Chép Alpha

Dùng template này để track quá trình phát triển alpha:

```
Alpha Name: _______________
Idea: _______________________________________________
Formula: _______________________________________________

Test 1: Universe=___ Neutral=___ Decay=___ → Sharpe=___ Fitness=___ Turnover=___%
Test 2: Universe=___ Neutral=___ Decay=___ → Sharpe=___ Fitness=___ Turnover=___%
Test 3: Universe=___ Neutral=___ Decay=___ → Sharpe=___ Fitness=___ Turnover=___%

Best settings: Universe=___ Neutral=___ Decay=___ Truncation=___
Final Sharpe: ___  Final Fitness: ___  Turnover: ___%

Stability (năm tệ nhất Sharpe): ___
Submit? YES / NO — Lý do: _______________
```