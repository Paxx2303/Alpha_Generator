# Settings Grid — WorldQuant Brain

Hướng dẫn chọn Universe, Neutralization, Decay, Truncation cho từng loại alpha.

---

## Tổng Quan Các Tham Số

```
Universe:       Nhóm cổ phiếu giao dịch (TOP200 → TOP3000)
Neutralization: Loại bỏ bias thị trường/ngành
Decay:          Làm mượt signal theo thời gian (0 = không làm mượt)
Truncation:     Giới hạn kích thước vị thế tối đa (0.01 = 1%)
Delay:          1 (mặc định, dùng data ngày hôm qua để tránh look-ahead)
Region:         USA (mặc định, stable nhất)
```

---

## Universe

| Universe | Số cổ phiếu | Đặc điểm | Khi nào dùng |
|---|---|---|---|
| **TOP200** | 200 | Thanh khoản cao nhất, ít alpha tìm thấy | VWAP, intraday, blue-chip signals |
| **TOP500** | 500 | Balance tốt, Sharpe cao nhất (~2.0) | Signals mạnh, Subindustry neutral |
| **TOP1000** | 1,000 | Phổ biến nhất, nhiều alpha valid | Hầu hết các loại alpha |
| **TOP3000** | 3,000 | Nhiều cổ phiếu nhỏ, returns cao hơn | Lần thử đầu tiên, market neutral |

**Khuyến nghị cho người mới:** Bắt đầu với **TOP3000**, sau đó thử TOP1000.

---

## Neutralization

| Loại | Ý nghĩa | Khi nào dùng |
|---|---|---|
| **None** | Không loại bỏ bias | Alpha đã rất clean, volume-based |
| **Market** | Trừ đi trung bình toàn thị trường | Price-volume alpha, mean reversion, default tốt |
| **Sector** | Trừ đi trung bình theo sector (11 nhóm) | Khi không muốn bet vào ngành cụ thể |
| **Industry** | Trừ đi trung bình theo industry | Alpha cross-industry |
| **Subindustry** | Trừ đi trung bình theo sub-industry (68+ nhóm) | Sharpe cao nhất, dùng với TOP500 |

**Quan trọng (IQC top 1.3%):**
> Price-volume alpha → dùng **Market**, KHÔNG phải Subindustry
> Subindustry làm giảm Sharpe nhưng tăng Fitness cho fundamental alphas

---

## Decay

Decay d = trung bình gia quyền tuyến tính trong d ngày. Decay 0 = không làm mượt.

| Decay | Turnover thường thấy | Khi nào dùng |
|---|---|---|
| **0** | 30%–70% | Signal rõ ràng, ít nhiễu |
| **3** | 15%–40% | Turnover hơi cao, cần giảm nhẹ |
| **5** | 10%–25% | Cân bằng tốt nhất cho hầu hết alpha |
| **10** | 5%–15% | Signal thay đổi chậm, fundamental alpha |
| **20+** | < 5% | Hiếm dùng, Fitness thường thấp |

**Công thức:** Nếu Turnover > 50%, thử Decay = 5. Nếu Turnover > 70%, thử Decay = 10.

---

## Truncation

Giới hạn % NAV tối đa cho một vị thế. Thấp hơn = phân tán rủi ro hơn.

| Truncation | Ý nghĩa | Khi nào dùng |
|---|---|---|
| **0.01** (1%) | Rất phân tán | Large universe, nhiều cổ phiếu |
| **0.05** (5%) | Cân bằng (mặc định) | TOP3000, hầu hết alpha |
| **0.10** (10%) | Ít cổ phiếu hơn | TOP500, TOP1000 |
| **0.20** (20%) | Tập trung | TOP200, signals rất mạnh |

---

## Bảng Settings Đã Proven (IQC Research)

| Rank | Universe | Neutralization | Decay | Truncation | Sharpe | Fitness |
|---|---|---|---|---|---|---|
| 🥇 Tốt nhất | TOP500 | Subindustry | 0 | 0.10 | ~2.02 | ~2.30 |
| 🥈 Phổ biến | TOP1000 | Subindustry | 10 | 0.10 | ~1.80 | ~1.42 |
| 🥉 Cho người mới | TOP3000 | Market | 3 | 0.05 | ~1.39 | ~1.11 |

---

## Grid Thử Nghiệm Theo Thứ Tự

Khi có alpha formula mới, thử theo thứ tự này:

```
Vòng 1 — Kiểm tra signal có tồn tại:
  TOP3000 | Market | Decay 0 | Truncation 0.05

Vòng 2 — Giảm Turnover nếu > 50%:
  TOP3000 | Market | Decay 5 | Truncation 0.05

Vòng 3 — Tăng Sharpe:
  TOP3000 | Subindustry | Decay 0 | Truncation 0.05

Vòng 4 — Tối ưu Fitness:
  TOP1000 | Subindustry | Decay 10 | Truncation 0.10

Vòng 5 — Maximizing Sharpe:
  TOP500  | Subindustry | Decay 0  | Truncation 0.10
```

**Dừng khi:** Fitness ≥ 1.0 VÀ Sharpe ≥ 1.25 VÀ Turnover 10%–70%

---

## Multi-Region Strategy

Chạy cùng formula trên nhiều region có thể nhân số lần submit mà không cần tạo formula mới.

| Region | Đặc điểm | Lưu ý |
|---|---|---|
| **USA** | Thanh khoản cao nhất, data đầy đủ, stable nhất | Bắt đầu ở đây |
| **EUR** | Thanh khoản tốt, cấu trúc ngành khác USA | Kiểm tra Subindustry neutral |
| **CHN** | Nhiều cổ phiếu nhỏ lẻ, mean reversion mạnh hơn | Top Universe nhỏ hơn (TOP500) |
| **JPN** | Giá trị thấp, P/B thường < 1, fundamental works well | Fundamental alpha tốt hơn |
| **KOR** | Biến động cao hơn USA | Decay cao hơn để giảm Turnover |
| **AUS** | Ít cổ phiếu, universe nhỏ | Truncation cao hơn (0.10) |

**Quy trình multi-region:**
```
1. Tạo alpha tốt trên USA (Sharpe ≥ 1.5, Fitness ≥ 1.2)
2. Copy sang EUR với cùng settings → check Sharpe có ≥ 1.0 không
3. Thử CHN — nếu alpha dựa trên price behavior, thường hoạt động
4. JPN — tốt cho value alpha (P/B, P/E)
5. KHÔNG chỉ chạy region khác để "may ra đạt" — cần lý do kinh tế
```

**Khi nào KHÔNG nên thử region khác:**
- Formula dùng data chỉ có ở USA (một số fundamental fields)
- Formula phụ thuộc vào thị trường giờ giao dịch (VWAP intraday)
- Sharpe ở USA < 1.0 — sửa formula trước đã

---

## Hiểu Kết Quả Simulation
Fitness:        Chỉ số tổng hợp. ≥ 1.0 mới được xem xét submit
Returns (%):    Lợi nhuận hàng năm (annualized). Cao hơn tốt hơn
Turnover (%):   % danh mục thay đổi mỗi ngày. Cần 10%–70%
Drawdown (%):   Thua lỗ tối đa từ đỉnh. < 20% là tốt

Công thức Fitness:
  Fitness = Sharpe × sqrt(|Returns| / max(Turnover, 0.125))
```

### Đọc kết quả nhanh:

```
Sharpe < 0           → Đảo dấu formula ngay
0 < Sharpe < 1.0     → Signal yếu, cần cải thiện formula
1.0 ≤ Sharpe < 1.25  → Borderline, thử đổi settings
Sharpe ≥ 1.25        → Tốt, tối ưu Fitness
Sharpe ≥ 2.0         → Rất tốt, kiểm tra submit

Fitness < 0.5        → Cần sửa nhiều
0.5 ≤ Fitness < 1.0  → Gần được, tune settings
Fitness ≥ 1.0        → Có thể submit (còn cần pass các check khác)

Turnover < 5%        → Decay quá cao, giảm Decay
Turnover > 70%       → Tăng Decay
```