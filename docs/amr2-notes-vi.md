# amr2 — bản sau chỉnh

Bản đối chứng của `amr`. **`amr` không bị chạm vào** — `tests/test_amr2.py::test_amr_is_untouched` khẳng định điều đó, và `test_amr2_does_not_import_amr` khẳng định hai gói không nói chuyện với nhau.

```bash
python -m amr2                    # ước lượng + dự báo ngoài mẫu + đối chiếu
python tests/test_amr2.py         # 22 kiểm thử
```

---

## Bốn thay đổi, mỗi cái do một kết quả đòi hỏi

| | thay đổi | kết quả buộc phải sửa |
|---|---|---|
| 1 | **Bỏ số mũ κ**, cộng tính trong log | κ_sys không nhận dạng được (Prop. 11.1); đặt nó ở vị trí số mũ biến bất định tham số thành bất định nhân. Bỏ: RMSE 18,64% → 4,31% |
| 2 | **Hệ số ước lượng**, không quy ước | §11.5.1: hệ số hồi quy là tích κ·α, κ đã bị hấp thụ. Dạng cộng tính với hệ số ước lượng là dạng ĐÚNG, không phải xấp xỉ |
| 3 | **Dấu do dữ liệu đặt** | Quy ước Tầng 0 — kênh cầu nâng đô la — sai trên dầu ở mọi mốc cắt từ 2012, t chưa bao giờ yếu hơn −6,6 |
| 4 | **Tầng 1 hạ xuống vai trò mô tả** | σ_sys hỏng 2/2 mũi tên, mang 9,3/24 điểm sai số, và tắt đi thì được thêm một dấu đúng |

Giữ lại từ `amr`: đồ thị dấu **Tầng 2** (giữ 4/4 trong bảng điểm 2026) làm lớp phủ định tính chạy song song, không vào số học. Các định lý Chương 8 giữ nguyên giá trị nhưng được dán nhãn **kiến trúc**, không phải mệnh đề kiểm chứng được.

---

## Ước lượng — mẫu dừng 2025-10, không quan sát 2026 nào chạm vào

n = 222 · R² = 0,356 · Newey–West L = 4

| số hạng | hệ số | s.e. | t |
|---|---|---|---|
| `cap` Δ chênh lệch 10 năm Mỹ–Đức (pp) | **+5,757** | 0,874 | **+6,58** |
| `oil` 100·Δln Brent | **−0,089** | 0,012 | **−7,68** |
| `pol` Δ lãi suất quỹ liên bang (pp) | −0,338 | 0,627 | −0,54 → **bị tỉa** |

Quy tắc tỉa `|t| ≥ 2` chạy **trên mẫu huấn luyện và chỉ trên đó**, nên nó không phải chọn lọc sau khi biết kết quả.

---

## Phát hiện cốt lõi: ở cực đoan, dấu của dầu thôi quan trọng

| tháng | Δln Brent | Δln DXY |
|---|---|---|
| 2008-10 | −31,7% | **+6,85%** |
| 2008-11 | −31,1% | **+3,21%** |
| 2020-03 | −49,5% | **+1,14%** |
| 2026-03 | **+35,9%** | **+1,72%** |

Trong **mọi** tháng có `|Δln Brent| ≥ 30%` của cả mẫu, đô la **tăng** — bất kể dầu lên hay xuống. Ba tháng đầu đều là dầu sụp, nên quan hệ tuyến tính âm *có vẻ* đúng ở đó. 2026-03 là tháng dầu **vọt** cực đoan đầu tiên trong mẫu, và lõi tuyến tính dự −3,5% trong khi đô la +1,7%.

Đọc đúng không phải "kênh dầu đảo dấu một lần" mà là: **ở cực đoan, kênh dầu ngừng là một kênh.** Đô la lên vì thứ khác tiếp quản. Đó chính là cơ chế chuyển giao mà sách đặt ra ở §3.3 — nhưng công tắc nằm trên **độ lớn cú sốc hàng hoá**, không nằm trên σ_sys.

`amr2` xử lý bằng cách gỡ lõi tuyến tính trong vùng đó và thay bằng một **tiên nghiệm chế độ** dựng trên năm quan sát trước 2026 (`+2,54%`, 4/5 tháng đô la tăng). Ngưỡng 25% chọn từ mẫu huấn luyện: 30% cho 3/3 nhưng ba quan sát là quá ít; 20% bắt đầu lẫn tháng khác loại.

---

## Ngoài mẫu — chín tháng, 2025-11 đến 2026-07

| tháng | điểm | khoảng 90% | thực tế | |
|---|---|---|---|---|
| 2025-11 | −0,01 | [−2,12 , +2,09] | +0,94 | ✓ |
| 2025-12 | −0,34 | [−2,45 , +1,76] | −1,33 | ✓ |
| 2026-01 | +0,05 | [−2,06 , +2,15] | −0,38 | ✓ |
| 2026-02 | −0,76 | [−2,86 , +1,35] | −0,92 | ✓ |
| **2026-03** | **+2,54** | [−3,11 , +8,19] | **+1,72** | ✓ ⚑ tiên nghiệm chế độ |
| 2026-04 | −0,42 | [−2,53 , +1,68] | −0,55 | ✓ |
| 2026-05 | +0,57 | [−1,54 , +2,67] | −0,18 | ✓ |
| 2026-06 | +2,28 | [+0,18 , +4,39] | +1,72 | ✓ |
| 2026-07 | +0,22 | [−1,89 , +2,32] | +0,67 | ✓ |

| mô hình | RMSE | dấu | bao phủ |
|---|---|---|---|
| `amr` sáu tầng, quy ước | **18,64%** | 2/4 | — |
| ngây thơ, luôn 0 | 1,072% | 0/9 | — |
| **`amr2` cả chín tháng** | **0,656%** | **6/9** | **9/9** |
| `amr2` chỉ tháng lõi tuyến tính gọi | 0,633% | 5/8 | 8/8 |

**2026-03 là phép thử thật của tiên nghiệm chế độ**, vì tiên nghiệm dựng xong trước khi tháng đó xảy ra. Lõi tuyến tính sai −5,23 điểm; tiên nghiệm sai +0,82.

---

## Ba điều phải nói ra

**Một.** Ngưỡng 25% và tiên nghiệm `+2,54%` dựng từ **năm** quan sát. Năm không phải một mẫu. Chúng được **nêu ra bằng số** nên chúng bác bỏ được ở sự kiện cực đoan *tiếp theo* — đó là toàn bộ điều được tuyên bố, và nó là khuyết tật ISSUES #36 (CS8 không nêu ngưỡng nên không sự cố nào bác bỏ được) đóng lại.

**Hai.** Bao phủ 9/9 một phần là vì khoảng rộng (±2,1 điểm cho tháng thường). Khoảng 90% dựng từ σ phần dư của hồi quy; nó trung thực chứ không chặt.

**Ba.** CPI tháng **2025-10 không tồn tại** — BLS không công bố vì đợt đóng cửa chính phủ liên bang. Giá trị trong `data/series.py` là nội suy tuyến tính, cờ `cpi_imputed` bật ở tháng đó, và biến `realcap` phụ thuộc nó. Đây đúng loại lỗi §11.5.2 bắt được với RRPONTSYD, nên nó được đánh dấu thay vì làm lơ.

---

## Cái amr2 KHÔNG làm

Nó không thay thế `amr` và không phải một mô hình DXY tốt hơn theo nghĩa thông thường. Nó là **lõi hai kênh đã ước lượng của chính cuốn sách**, cộng một công tắc chế độ đặt đúng chỗ dữ liệu nói, cộng quyền từ chối gọi. Mọi thứ còn lại của kiến trúc sáu tầng đã bị gỡ vì nó không có chuỗi số liệu, không nhận dạng được, hoặc đã hỏng khi kiểm.

Giữ cả hai gói là để còn trả lời được câu "sửa có ăn thua không". Gộp lại thì mất khả năng đó.

---

*Chỉ dành cho mục đích học thuật. Không con số nào ở đây là khuyến nghị đầu tư hay dự báo thị trường.*
