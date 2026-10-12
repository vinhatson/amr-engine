# AMR — Kiến trúc của các Chế độ Thị trường

Bản cài đặt chạy được của *The Architecture of Market Regimes: Modeling DXY
through Structural and Reflexive Layers* (Vi Nhật Sơn, 2026), cùng hai tầng
dựng thêm trên nó.

**[→ Mở panel tương tác ngay trên trình duyệt](#panel-tương-tác-không-cần-cài-gì)** ·
**[Hướng dẫn sử dụng (PDF)](docs/huong-dan-su-dung-vi.pdf)** ·
**[English README](README.md)** ·
**[Bài báo gốc (PDF)](docs/The_Architecture_of_Market_Regimes_Model.pdf)**

---

## Đây là cái gì

Chỉ số đô la (DXY) thường được mô hình hoá bằng **một** phương trình. Dự án này
mô hình nó bằng **sáu tầng tương tác** — dòng cơ học, trạng thái biến động, tầng
cấu trúc, tầng phản thân, tầng chiến lược, và tầng trọng số — rồi đặt một câu
hỏi mà phần lớn mô hình không đặt được: *thứ tự hai cú sốc ập đến có làm đổi
điểm cuối hay không?*

Có ba package, và chúng **cố tình** là ba thứ khác nhau:

| package | là gì | chạy độc lập |
|---|---|---|
| **`amr`** | mô hình của sách, sáu tầng ở dạng chuẩn, có kiểm tra biên | được |
| **`amr2`** | một mô hình **KHÁC** — sửa các lỗi của sách, khớp với dữ liệu FRED thật, có backtest ngoài mẫu | được, và cố tình **không** nhập `amr` |
| **`amr3`** | **CÙNG** mô hình với `amr`, đọc lại trong hệ toạ độ hình học: tấm, vết sẹo, phụ thuộc đường đi | nhập và chạy `amr` ở bên trong |

`amr2` đứng riêng vì nó là mô hình đối thủ, phải so sánh được.
`amr3` lồng `amr` vào trong vì nó là cùng mô hình đọc theo cách khác, và cách
chứng minh một lối đọc là trung thực chính là chạy bản gốc ở trong nó:

```
τ ≡ 0  →  overrides rỗng  →  ln DXY trùng khít amr, chênh lệch 0.000e+00
```

---

## Panel tương tác (không cần cài gì)

Ba trang HTML tự chứa. Tải về mở bằng trình duyệt nào cũng được, hoặc host trên
GitHub Pages — không cần Python, không cần server, không cần build.

| panel | bạn làm được gì |
|---|---|
| [`panels/regimes_panel.html`](panels/regimes_panel.html) | điều khiển trực tiếp sáu tầng; xem phân rã ba khối phản ứng |
| [`panels/geometry_panel.html`](panels/geometry_panel.html) | 78 biến xếp theo **vai hình học** thay vì theo phương trình |
| [`panels/manifold_panel.html`](panels/manifold_panel.html) | các tấm trong không gian 3D; bắn hai cú sốc theo hai thứ tự và xem có để lại vết sẹo không |

Chúng tải `three.js` và một font từ CDN nên lần vẽ đầu cần mạng. Còn lại — mô
hình, registry, các vector — đều đã nén sẵn trong file.

---

## Cài đặt

Python 3.9+. Phần lõi **không phụ thuộc gì cả** — chỉ thư viện chuẩn.

```bash
git clone https://github.com/<tên-tài-khoản>/amr-engine.git
cd amr-engine
python -m amr check          # ràng buộc cấu trúc, kèm độ dư từng cái
```

Phần hồi quy của `amr2` cũng không cần thêm gì; các chuỗi FRED đã nằm sẵn trong
[`data/series.py`](data/series.py), tải ngày 2026-10-09.

---

## Dùng nhanh

```bash
python -m amr list                 # các kịch bản, kèm điều sách nói về từng cái
python -m amr run narrative        # một bản đọc định tính đầy đủ
python -m amr weights              # tỉ lệ trọng số tại trạng thái hiện tại
python -m amr tornado              # quét từng trọng số trên toàn dải
python -m amr mc --n 1500          # phân rã phương sai; phần nằm ở tương tác
python -m amr audit                # mọi kịch bản đối chiếu số liệu sách

python -m amr2                     # mô hình sách đối đầu mô hình đã sửa
python -m amr3                     # bản đồ, ba phép đo, quét τ
```

```python
from amr import WorldState, Options, forecast, run_scenario

f = run_scenario("sanctions")
print(f.narrative_vi())

nen = WorldState()
soc = nen.shock(p_vix=0.95, p_stlfsi=0.80, bank=0.94, prec=1.10)
print(forecast(nen, soc).narrative_vi())
```

Mọi lệnh nhận các cờ mở rộng, và chúng đặt **trước** subcommand vì là cờ toàn
cục:

```bash
python -m amr --recentre run narrative        # đúng
python -m amr run narrative --recentre        # lỗi: unrecognized arguments
```

Danh sách cờ: `--recentre`, `--regime-lambda`, `--return-path`, `--reversal`,
`--health-leg`, `--split-prec`, `--funding-haven`, `--no-state`,
`--no-coupling`. Tất cả **tắt** theo mặc định: để các tải trọng của Layer W ở 0
thì engine tái tạo E9 đúng hệt.

---

## Kết quả đáng tranh luận

`amr3` đo ba đại lượng mà cả ba **bằng đúng 0** trong mô hình gốc — không phải
nhỏ, mà là 0, và 0 vì một lý do cấu trúc:

| | τ ≡ 0 | trễ · τ = 0,294 | mỏi · τ = 0,122 |
|---|---|---|---|
| giao hoán tử ‖[L₄, L₅]‖ | **0,000e+00** | **0,000e+00** | 1,720e-02 |
| holonomy H(γ) | **+0,000e+00** | **−7,318e-02** | **−4,056e-02** |
| dư âm sau khi gỡ sốc | **+0,000000** | **+0,027931** | **+0,011078** |

Tầng E9 của mô hình gốc là một hàm của trạng thái hiện tại và **không mang theo
lịch sử nào**, nên hai đường đi tới cùng một trạng thái **bắt buộc** cho cùng
một đầu ra. Nó không thiếu một số hạng — nó nằm trong một *lớp hàm* không thể
diễn đạt nổi "cái lỗ còn lại".

Điều đó biến thành một câu hỏi thực nghiệm, và câu hỏi này không cần đợt dữ
liệu dài:

> **Thứ tự hai cú sốc có đổi mức thường trực không, khi trạng thái cuối giữ
> nguyên?**
> Có → mỏi. Không → trễ.

Lưu ý: giao hoán tử của dạng **trễ** bằng 0 **theo đúng định nghĩa của toán tử**
(nó lấy cực đại theo lịch sử; hai thứ tự đi qua cùng tập trạng thái nên hai cực
đại bằng nhau), còn holonomy và dư âm thì khác 0 ở **cả hai** dạng. Vòng kín
quay về đúng trạng thái đầu; vết sẹo thì ở lại.

---

## Giới hạn, nói thẳng

Đọc hết phần này trước khi trích bất kỳ con số nào.

- **`amr` là định tính.** Nó cho ra thang mũi tên và phân rã ba khối, **không**
  phải một dự báo điểm đã hiệu chỉnh. Chạy `python -m amr audit` để thấy từng
  kịch bản đối chiếu số liệu của chính sách, và thấy khoảng cách.
- **`amr3` thêm đúng một tham số** (`τ`, phần pháp tuyến của tác động liên tấm)
  và **không thêm cạnh nào** — tập cạnh lấy nguyên từ trường `gamma` trong
  [`amr/registry.py`](amr/registry.py). Mặc định của nó là `0`, và đó là giả
  thuyết không.
- **Trên Σ₅ quy tắc độ căng là đúng hệt; trên Σ₁ nó là xấp xỉ**, vì `σ_sys` là
  hợp tuyến tính chứ không phải logistic. Code nói ra điều đó thay vì bỏ qua.
- **`amr2` là nơi có dữ liệu thật**, và nó báo cáo kết quả **ngoài mẫu**, không
  phải độ khớp trong mẫu. Một khuyết tật dữ liệu được mang theo chứ không giấu:
  CPI tháng 2025-10 **không tồn tại** (BLS không công bố vì đợt đóng cửa chính
  phủ liên bang bắt đầu 01/10/2025), nên tháng đó là nội suy tuyến tính và
  `row.cpi_imputed` bật `True`.
- **Khung hình học là một lối đọc, không phải một số chiều mới.** Mô hình hai
  tầng mà có vết sẹo thì đã là đâm xuyên; mô hình mười tầng mà không có vết sẹo
  thì vẫn chỉ là trượt. Bất biến đáng kể là **các toán tử tầng có giao hoán hay
  không**.

---

## Về ngôn ngữ của output

**Phần diễn giải bằng văn xuôi hiện chỉ có tiếng Việt** — phương thức là
`narrative_vi()`, và **chưa có** `narrative_en()`. Phần không phụ thuộc ngôn
ngữ là mọi thứ có cấu trúc, và đó cũng là phần lớn những gì bạn cần: các con
số, thang mũi tên, phân rã ba khối, `Forecast.blocks`, `.channels`,
`.evidence_mix`, `.sigma_response`, cùng tên biến và tên kênh (có sẵn trường
`name_en` trong `amr/registry.py`).

Nếu bạn muốn góp một tay, viết bộ render tiếng Anh là đóng góp hữu ích nhất cho
dự án này.

---

## Cấu trúc repo

```
amr/            mô hình của sách — sáu tầng, registry, CLI, phân tích độ nhạy
amr2/           mô hình đã sửa — bảng FRED, OLS/HAC, backtest
amr3/           lối đọc hình học — atlas, tấm, vết sẹo, toán tử
data/series.py  chuỗi FRED theo tháng, tải 2026-10-09
panels/         ba trang HTML tương tác, tự chứa
docs/           bài báo, hướng dẫn (EN/VI), ghi chú thiết kế
tests/          ba bộ kiểm thử; chạy cả ba trước khi tin bất cứ điều gì
tools/          script hiệu chỉnh kịch bản
SPEC.md         toàn bộ phần toán
```

---

## Kiểm thử

```bash
python tests/test_engine.py     # amr   — các tầng, biên, Table 10.3
python tests/test_amr2.py       # amr2  — tính toàn vẹn dữ liệu, 2026 không lọt vào tập huấn luyện
python tests/test_amr3.py       # amr3  — atlas phủ 78/78, lồng khít tại τ→0
```

Cả ba pass trên Python 3.12 / Windows, macOS và Linux. Các bộ test kiểm **cấu
trúc**, không chỉ kiểm output:
`test_atlas_covers_every_amr_variable_exactly_once` khẳng định 78/78, không
thêm không bớt.

---

## Tài liệu

- **[SPEC.md](SPEC.md)** — toàn bộ phần toán
- **[docs/huong-dan-su-dung-vi.pdf](docs/huong-dan-su-dung-vi.pdf)** — hướng dẫn sử dụng (bản [HTML](docs/huong-dan-su-dung-vi.html))
- **[docs/GUIDE.vi.md](docs/GUIDE.vi.md)** — hướng dẫn đầy đủ, giải thích từng lệnh
- **[docs/user-manual-en.pdf](docs/user-manual-en.pdf)** — bản tiếng Anh
- **[docs/The_Architecture_of_Market_Regimes_Model.pdf](docs/The_Architecture_of_Market_Regimes_Model.pdf)** — bài báo gốc

Ghi chú thiết kế viết trong lúc làm còn giữ ở
[`docs/amr3-notes-vi.md`](docs/amr3-notes-vi.md) và
[`docs/amr2-notes-vi.md`](docs/amr2-notes-vi.md). Chúng mang tính tranh luận hơn
là hướng dẫn, và đáng đọc nếu bạn muốn biết **vì sao** một lựa chọn được đưa ra.

---

## Góp sức

Rất hoan nghênh issue và pull request. Hai thứ giúp được nhiều nhất:

1. **Bộ render tiếng Anh** (`narrative_en()`). Template trong
   `amr/qualitative.py` chỉ chừng bốn mươi dòng; phần khó là văn xuôi nằm trong
   `amr/registry.py` và `amr/scenarios.py`. Các trường có cấu trúc thì đã độc
   lập ngôn ngữ rồi, nên đây là việc render, không phải việc mô hình hoá.
2. **Phản biện có bằng chứng.** Nếu bạn chỉ ra được rằng thứ tự hai cú sốc
   **không** làm đổi mức thường trực khi trạng thái cuối giữ nguyên, đó là một
   kết quả, và nó thuộc về một issue.

Xin giữ cho các bộ test còn xanh, và thêm test kèm theo mỗi thay đổi hành vi.

---

## Trích dẫn

Xem [CITATION.cff](CITATION.cff), hoặc:

> Vi Nhật Sơn (2026). *The Architecture of Market Regimes: Modeling DXY through
> Structural and Reflexive Layers.*

---

## Giấy phép

[Apache License 2.0](LICENSE) — cho phép dùng thương mại, sửa đổi và phân phối,
kèm điều khoản bằng sáng chế và yêu cầu ghi lại thay đổi của bạn. Xem
[NOTICE](NOTICE) cho điều khoản áp dụng với các bài báo PDF.
