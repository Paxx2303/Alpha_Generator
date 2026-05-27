# IQC Strategy — Hướng Dẫn Thi Đấu Thực Tế

Thông tin chính xác từ IQC Guidelines 2026 và kinh nghiệm top 1.3% (jglazar).

---

## Hệ Thống Điểm IQC (Bronze / Silver / Gold)

| Mốc điểm | Tier | Đặc quyền |
|---|---|---|
| > 1,000 | 🥉 Bronze | Nhận certificate |
| > 5,000 | 🥈 Silver | Training đặc biệt + video nội bộ |
| > 10,000 | 🥇 Gold | Training đặc biệt + eligible interview invite |
| Top team/region | Champion | Finals tại Singapore |

**Cách tính điểm:**
- Điểm cá nhân = tổng điểm từ tất cả alpha đã submit và pass
- Điểm team = tổng điểm tất cả thành viên
- Leaderboard cập nhật định kỳ, không real-time

---

## Quan Trọng: Cách Scoring Thực Sự Hoạt Động

### Alpha được score theo portfolio context — không chỉ Sharpe đơn lẻ

*"Baskets of alphas with strong and uncorrelated returns are highly rewarded"* — IQC scoring rewards **diversity**, không phải chỉ quality.

**Nghĩa là:**
- Alpha Sharpe 1.5 + uncorrelated với pool → điểm cao
- Alpha Sharpe 2.0 + correlated với pool → điểm thấp hơn
- **Mục tiêu**: submit nhiều alpha ĐA DẠNG, cover nhiều themes khác nhau

**Chiến lược thực tế (jglazar top 1.3%):**
```
Aim for 6-8 submittable alphas với các themes khác nhau:
  - 2 price/volume alphas (short-term)
  - 2 momentum/reversal (medium-term)  
  - 2 fundamental/sector
  - 1-2 với dataset đặc biệt (sentiment, news)
```

---

## Delay = 0 — Nên Hay Không?

**Delay = 0** nghĩa là dùng close price của ngày T để giao dịch ngày T (same-day).

**Ưu điểm:**
- Sharpe và Fitness thường cao hơn đáng kể
- Ví dụ proven: CHN + Delay=0 → Sharpe 5.03, Fitness 7.52

**Nhược điểm trong IQC:**
- **Điểm IQC của Delay=0 alpha bị chia 3** (penalty!)
- Thực tế khó execute vì cần data intraday

**Khi nào dùng Delay=0:**
- CHN market với news/sentiment data
- Khi Sharpe rất cao (> 3.0) để bù đắp penalty ÷3
- Không dùng cho price-based alpha USA (không thực tế)

**Công thức quyết định:**
```
Expected IQC points từ Delay=0 alpha ≈ Fitness × C / 3
Expected IQC points từ Delay=1 alpha ≈ Fitness × C

→ Chỉ submit Delay=0 nếu Fitness(D0) > 3 × Fitness(D1) của cùng formula
```

---

## Self-Correlation — Hiểu Đúng Cơ Chế

### Cách tính (khác với mọi người nghĩ!)

**Self-correlation được tính dựa trên PnL graph, KHÔNG phải alpha weights hay formula.**

```
Cửa sổ self-correlation: 2 năm gần nhất
Cách đo: correlation giữa daily PnL của alpha mới và alpha cũ

High self-correlation = alpha mới có PnL giống alpha đã submit
```

### Quy tắc quan trọng mà nhiều người bỏ qua:

**Alpha tương quan cao VẪN CÓ THỂ ĐƯỢC SUBMIT nếu Sharpe cải thiện ≥ 10%**

```
Ví dụ:
- Alpha A (đã submit): Sharpe 1.40
- Alpha B (mới): tương quan 0.85 với A, nhưng Sharpe 1.55 (tăng 10.7%)
→ Alpha B ĐƯỢC PHÉP submit!

- Alpha C (mới): tương quan 0.85 với A, Sharpe 1.50 (tăng 7%)
→ Alpha C BỊ TỪ CHỐI (chưa đủ 10% cải thiện)
```

### Chiến lược giảm self-correlation

Khi alpha bị từ chối vì "too similar":

```python
// 1. Đổi lookback window (±2-5 ngày)
-rank(ts_delta(close, 5))   → -rank(ts_delta(close, 8))

// 2. Đổi data field
rank(vwap - close)           → rank((high + low) / 2 - close)

// 3. Đổi operator tier
ts_delta(close, 5)           → ts_mean(returns, 5)

// 4. Thêm dimension mới (volume)
-rank(ts_delta(close, 5))   → -rank(ts_delta(close, 5)) * rank(ts_rank(volume, 20))

// 5. Đổi Universe (khác PnL profile hoàn toàn)
TOP3000 → TOP500

// 6. Đổi Region (PnL hoàn toàn độc lập)
USA → CHN hoặc EUR
```

---

## Backtest Period — In-sample vs Out-of-sample

```
In-sample:    7 năm trước → 2 năm trước (cập nhật hàng ngày)
Out-of-sample: 2 năm gần nhất (dùng để scoring IQC thực tế)
```

**Ý nghĩa thực tế:**
- Backtest bạn thấy trên Brain = **in-sample** (dễ overfit)
- IQC score thực tế dựa trên **out-of-sample** (năm gần nhất)
- Alpha ổn định over time (xem stability check) sẽ perform tốt out-of-sample
- Alpha chỉ tốt ở giai đoạn cũ → bị downgrade hoặc score thấp

---

## IQC Team Rules (2026)

| Quy tắc | Chi tiết |
|---|---|
| Số thành viên | 1–4 người |
| Điều kiện | Tất cả cùng trường đại học |
| Đăng ký team | 17/3/2026 – 13/5/2026 |
| Lock date | Sau 13/5 không đổi team được |
| Alpha trước IQC | Không tính vào điểm (phải đăng ký trước) |
| Tài khoản | Mỗi người 1 tài khoản, không chia sẻ |

**Chiến lược team:**
- Phân công theme: mỗi người chịu trách nhiệm 2-3 themes khác nhau
- Tránh submit alpha giống nhau trong cùng team → lãng phí slots
- Khi merge team: alpha tương quan cao sẽ bị drop, submit mới nhất được giữ

---

## Chiến Lược Submission Tối Ưu

### Mục tiêu: Nhiều alpha đa dạng, không phải 1 alpha tốt nhất

```
BAD strategy:  Submit 1 alpha Sharpe 3.0 → điểm 1 lần
GOOD strategy: Submit 8 alpha Sharpe 1.5 (uncorrelated) → 8× điểm
```

### Lịch trình submission khuyến nghị

```
Ngày 1-7:    Thử nghiệm, tìm 2-3 formula có Sharpe ≥ 1.25
Ngày 8-14:   Tune settings, submit 2 alpha tốt nhất
Ngày 15-30:  Mở rộng sang themes mới (Fundamental, Liquidity)
Tháng 2+:    Nhân bản alpha tốt sang regions khác (CHN, EUR)
Hàng ngày:   Submit ≤ 1 alpha mới (rate limit không chính thức)
```

### Kiểm tra trước khi submit trong IQC

- [ ] Sharpe ≥ 1.25 (thấp hơn = không đủ điều kiện)
- [ ] Fitness ≥ 1.0
- [ ] Alpha này có theme KHÁC với 3 alpha đã submit gần nhất không?
- [ ] Nếu cùng theme → lookback hoặc data field phải khác
- [ ] Stability check: không có 2 năm liên tiếp Sharpe âm
- [ ] Đã thử ít nhất 2 regions? (USA + một region khác)

---

## Eligibility — Ai Không Được Tham Gia IQC

Không đủ điều kiện nếu là:
- BRAIN Research Consultant (kể cả conditionally approved)
- WorldQuant University alumni
- Nhân viên/contractor của WorldQuant
- Người đã thắng IQC trước đây

**Quốc gia/vùng không được nhận prize:** UAE, Kenya, Nigeria (có thể tham gia nhưng không nhận tiền)
**Quốc gia không được tham gia:** Afghanistan, Belarus, Brazil-Quebec, Cuba, Iran, Italy, North Korea, Russia, Sudan, Syria, Ukraine

---

## Điểm Mấu Chốt (TL;DR)

```
1. IQC thưởng DIVERSITY — submit nhiều alpha KHÁC NHAU, không phải 1 alpha tốt
2. Delay=0 bị chia 3 điểm — chỉ dùng khi Fitness rất cao (> 3.0)
3. Self-corr tính theo PnL (2 năm) — có thể submit nếu Sharpe tăng ≥10%
4. Out-of-sample = năm gần nhất — stability > Sharpe cao nhất
5. Silver/Gold tiers mở special training — target ít nhất Silver (5000 pts)
6. Team: phân công themes, tránh overlap alpha
```