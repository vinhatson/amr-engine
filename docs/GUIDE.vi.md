# AMR Engine — Hướng dẫn đầy đủ

Mọi thứ bạn cần để chạy ba package, đọc hiểu chúng nói gì, và biết **không**
được khẳng định điều gì. Bản ngắn là [README.vi.md](../README.vi.md).

**Mục lục**

1. [Bạn cần package nào?](#1-bạn-cần-package-nào)
2. [Cài đặt](#2-cài-đặt)
3. [Các panel — bắt đầu từ đây](#3-các-panel--bắt-đầu-từ-đây)
4. [`amr` — mô hình của sách](#4-amr--mô-hình-của-sách)
5. [`amr2` — mô hình đã sửa](#5-amr2--mô-hình-đã-sửa)
6. [`amr3` — lối đọc hình học](#6-amr3--lối-đọc-hình-học)
7. [Ba phép đo](#7-ba-phép-đo)
8. [Trễ hay mỏi](#8-trễ-hay-mỏi)
9. [Kiểm thử](#9-kiểm-thử)
10. [Được và không được khẳng định điều gì](#10-được-và-không-được-khẳng-định-điều-gì)
11. [Xử lý sự cố](#11-xử-lý-sự-cố)

---

## 1. Bạn cần package nào?

Ba package, ba thứ khác nhau. Chọn theo việc bạn muốn làm.

| bạn muốn… | dùng | vì sao |
|---|---|---|
| khám phá mô hình một cách tương tác | **các panel** | không cần cài, chạy trong trình duyệt |
| đọc mô hình của sách ở dạng code | **`amr`** | sáu tầng ở dạng chuẩn |
| xem nó khớp với dữ liệu thật | **`amr2`** | bảng FRED, OLS/HAC, ngoài mẫu |
| hỏi xem thứ tự cú sốc có quan trọng không | **`amr3`** | tấm, vết sẹo, phụ thuộc đường đi |

Quan hệ giữa chúng mới là phần thú vị:

- **`amr2` cố tình KHÔNG nhập `amr`.** Nó là một mô hình *khác* — các lỗi của
  sách đã được sửa — và nó phải đứng độc lập để còn so sánh được.
- **`amr3` cố tình CÓ nhập `amr`, và chạy `amr` ở bên trong nó.** Nó là *cùng*
  mô hình trong hệ toạ độ khác, và cách chứng minh một lối đọc là trung thực
  chính là chạy bản gốc ở trong nó.

`amr3` **không** phải mô hình thứ ba. Nó là `amr`, với cả 78 biến giữ nguyên,
xếp lại theo **vị trí hình học** thay vì theo việc chúng là hệ số của phương
trình nào.

---

## 2. Cài đặt

Python 3.9 trở lên. **Không phụ thuộc gì** — chỉ thư viện chuẩn, cho cả ba
package.

```bash
git clone https://github.com/vinhatson/amr-engine.git
cd amr-engine
python -m amr check
```

Phần hồi quy của `amr2` cũng không cần thêm gì. Các chuỗi FRED đã nằm sẵn trong
[`data/series.py`](../data/series.py), tải ngày 2026-10-09.

### Lưu ý cho Windows

Không cần làm gì thêm. Các entry point tự đặt stdout của chúng về UTF-8, nên
console mặc định hiện đúng tiếng Việt và chữ Hy Lạp thay vì crash ngay ký tự đầu.

### Quan trọng: chạy từ gốc repo

`amr3` nhập `amr`, và `amr2` nạp `data/series.py` theo đường dẫn tương đối so
với **gốc repo**. Hãy chạy lệnh từ thư mục trên cùng của bản clone, không phải
từ bên trong một thư mục package.

---

## 3. Các panel — bắt đầu từ đây

Ba trang HTML tự chứa trong [`panels/`](../panels/). Không Python, không server,
không build. Tải repo về rồi mở bất cứ cái nào bằng trình duyệt, hoặc host chúng
trên GitHub Pages.

| panel | nó làm gì |
|---|---|
| `regimes_panel.html` | điều khiển trực tiếp sáu tầng; phân rã ba khối phản ứng tức thì |
| `geometry_panel.html` | 78 biến xếp theo **vai hình học** thay vì theo phương trình |
| `manifold_panel.html` | các tấm trong 3D; bắn hai cú sốc theo hai thứ tự và xem có để lại vết sẹo không |

Chúng tải `three.js` và một webfont từ CDN nên lần vẽ đầu cần mạng. Còn lại —
mô hình, registry, các vector — đều đã nén sẵn trong file.

`manifold_panel.html` là cái nên mở nếu bạn chỉ mở một. Nó có cả 78 biến dưới
dạng slider nhóm theo tấm (Σ₀ cơ học, Σ₁ trạng thái, Σ₂ cấu trúc, v.v.), một
preset `Table 10.3`, một **con dao** bạn mở đóng được, và một công tắc chuyển
giữa hai mô hình trí nhớ. Nó là luận điểm của dự án này ở dạng **chạm được**.

### Serve chúng ở local

Mở file trực tiếp cũng được. Nếu bạn muốn serve:

```bash
cd panels
python -m http.server 8901
# → http://127.0.0.1:8901/manifold_panel.html
```

---

## 4. `amr` — mô hình của sách

Bản cài đặt chạy được của *The Architecture of Market Regimes* (Vi Nhật Sơn,
2026): cả sáu tầng ở dạng chuẩn sau ISSUES, có kiểm tra biên, cộng thêm một tầng
ngang Layer W cho các trọng số.

### Các lệnh

```bash
python -m amr list                 # liệt kê kịch bản, kèm điều sách nói về từng cái
python -m amr run sanctions        # chạy một kịch bản, in bản đọc định tính
python -m amr run narrative --json # cùng kết quả, dạng JSON
python -m amr weights              # tỉ lệ trọng số tại trạng thái nền
python -m amr tornado --top 20     # vùng tuỳ biến: swing trên toàn dải
python -m amr mc --n 1500          # phân rã phương sai trên vùng khả thi
python -m amr check                # ràng buộc cấu trúc, kèm độ dư từng cái
python -m amr audit                # mọi kịch bản, đối chiếu số liệu sách
```

### Các kịch bản

Mười một cái, có tên:

```
liquidity   liquidity_swaps   sanctions   sanctions_late   trust
narrative   gfc2008   covid2020   rally2022   tariff2025   iran2026
```

Năm cái cuối là các nghiên cứu tình huống lịch sử (CS1, CS2, CS5, CS11, CS12).
Dùng `python -m amr list` để xem sách khẳng định gì về từng cái — bản liệt kê in
ra **kết quả mà chính sách nêu** ngay cạnh kịch bản, và đó là điều làm cho
`audit` có ý nghĩa.

### Các cờ mở rộng

Đây là cờ **toàn cục** và đặt **trước** subcommand:

```bash
python -m amr --recentre run narrative        # đúng
python -m amr run narrative --recentre        # lỗi: unrecognized arguments
```

| cờ | bật cái gì |
|---|---|
| `--no-state` | **tắt**: phụ thuộc trạng thái của trọng số (E17) |
| `--no-coupling` | **tắt**: ghép cặp trọng số (E18) |
| `--recentre` | tái định tâm độ lồi (E22, đóng I37) |
| `--regime-lambda` | λ₁ chuyển chế độ (E21, Remark 11.3) |
| `--return-path` | đường về Layer 5 → Layer 4 (E26, đóng I32) |
| `--reversal` | kênh đảo chiều cưỡng chế (E27, đóng I34) |
| `--health-leg` | nhánh sốc ngoại sinh phi quân sự (E25) |
| `--split-prec` | tách `D_prec` theo đường cong (E28, đóng I40) |
| `--funding-haven` | số hạng trú ẩn chạy theo nhánh funding |

Mọi mở rộng đều **tắt** theo mặc định. Để các tải trọng của Layer W ở 0 thì
engine tái tạo E9 **đúng hệt**, tới độ chính xác máy — đó là một tính chất **đã
được test**, không phải một lời khẳng định suông.

### Từ Python

```python
from amr import WorldState, Options, forecast, run_scenario

f = run_scenario("sanctions")
print(f.narrative_vi())

nen = WorldState()
soc = nen.shock(p_vix=0.95, p_stlfsi=0.80, bank=0.94, prec=1.10)
g = forecast(nen, soc)

# output có cấu trúc, độc lập ngôn ngữ
print(g.blocks)           # phân rã ba khối, kèm tỉ lệ
print(g.channels)         # chỉ các kênh thực sự dịch chuyển
print(g.evidence_mix)     # tình trạng bằng chứng theo Chương 17, dạng tỉ lệ
print(g.sigma_response)   # direct_haven / reflexive / regime / total

# bật một mở rộng
print(run_scenario("gfc2008", opt=Options(recentre_convexity=True)).narrative_vi())
```

### Cách đọc một bản đọc

```
KẾT LUẬN: DXY ↑ +2.83%  (biến động nhỏ, trong biên độ thường)
Chế độ: BÌNH LẶNG — dưới ngưỡng σ*: các độ co giãn ở giá trị bình lặng
σ_sys 0.349 → 0.349   κ_sys 1.460 → 1.460   Ψ_str 0.9022 → 0.8861

PHÂN RÃ THEO KHỐI (Figure 10.2):
  cơ học ×κ          ↑↑ +4.79%    70.9% của tổng tuyệt đối
  trú ẩn             ↔ -0.16%      2.4% của tổng tuyệt đối
  cấu trúc Ψ         ↓ -1.80%     26.7% của tổng tuyệt đối
  → Khối chi phối: cơ học ×κ
```

**Phân rã theo khối là output quan trọng nhất**, hơn cả con số phần trăm ở đầu.
Nó cho bạn biết **cơ chế nào** mang cú dịch chuyển đó. Một mức +2,83% mà 71% là
cơ học là một khẳng định **khác** với một mức +2,83% mà 71% là cấu trúc, và
engine luôn nói cho bạn biết bạn đang có cái nào.

Bản đọc cũng báo **tình trạng bằng chứng** của mọi kênh mà dự báo chạy qua
(Chương 17): `UNTESTED`, `PARTIAL`, v.v., dưới dạng tỉ lệ. Một dự báo được mang
chủ yếu bởi các kênh `UNTESTED` là một **giả thuyết**, và engine nói ra điều đó
thay vì để các chữ số thập phân ngụ ý điều khác.

### Về ngôn ngữ

**Phần diễn giải văn xuôi chỉ có tiếng Việt.** Phương thức là `narrative_vi()`;
**không có** `narrative_en()`. Phần độc lập ngôn ngữ là mọi thứ có cấu trúc —
các con số, thang mũi tên, phân rã khối, `blocks`, `channels`, `evidence_mix`,
`sigma_response` — cộng thêm trường `name_en` mà
[`amr/registry.py`](../amr/registry.py) mang cho mọi kênh và mọi biến.

Nên bạn hoàn toàn có thể điều khiển mô hình và đọc output bằng tiếng Anh ngay
hôm nay, bằng cách dùng các trường có cấu trúc. Một bộ render tiếng Anh là đóng
góp hữu ích nhất mà ai đó có thể làm cho repo này.

---

## 5. `amr2` — mô hình đã sửa

```bash
python -m amr2        # mô hình sách đối đầu mô hình đã sửa, cùng một bài thi
```

Đây là một **mô hình khác**, không phải một bản tinh chỉnh: các lỗi của sách đã
được sửa, rồi khớp với dữ liệu thật. Nó **không** nhập `amr`, một cách có chủ
đích, để hai cái so sánh được mà không cái nào nhiễm cái nào.

### Dữ liệu

Các chuỗi FRED theo tháng, tải 2026-10-09, nằm sẵn trong
[`data/series.py`](../data/series.py):

| chuỗi | là gì |
|---|---|
| `TWEXAFEGSMTH` | chỉ số đô la AFE danh nghĩa, trung bình tháng — **biến phụ thuộc** |
| `GS10` | UST 10 năm |
| `IRLTLT01DEM156N` | trái phiếu chính phủ Đức 10 năm |
| `POILBREUSDM` | Brent, USD/thùng |
| `FEDFUNDS` | lãi suất quỹ liên bang hiệu dụng — chân **GIÁ** của `S_Fed` |
| `CPIAUCSL` | CPI-U, để dựng lãi suất thực |

Không chuỗi nào là Tier 3, và không chuỗi nào bị thay thế âm thầm.

### Một khuyết tật dữ liệu, mang theo chứ không giấu

**CPI tháng 2025-10 KHÔNG TỒN TẠI.** BLS không công bố, vì đợt đóng cửa chính
phủ liên bang bắt đầu 01/10/2025. Giá trị dùng ở đây là **nội suy tuyến tính**,
và `row.cpi_imputed` bật `True` ở tháng đó.

Đây đúng là loại lỗi mà §11.5.2 của chính cuốn sách bắt được với `RRPONTSYD` —
một ô trống bị đọc thành một con số — nên nó được **đánh dấu** thay vì làm lơ.
Nếu bạn dùng `amr2`, hãy kiểm `cpi_imputed` trước khi tin một kết quả phụ thuộc
tháng đó.

### Nó báo cáo gì

Kết quả **ngoài mẫu**, không phải độ khớp trong mẫu. `tests/test_amr2.py` có
`test_training_never_touches_2026`, test này **fail** nếu dữ liệu 2026 lọt vào
cửa sổ huấn luyện. Việc test đó tồn tại chính là lý do khẳng định "ngoài mẫu"
có giá trị.

---

## 6. `amr3` — lối đọc hình học

```bash
python -m amr3        # bản đồ, kiểm tra lồng khít, ba phép đo, quét τ
```

Cùng mô hình với `amr`, cả 78 biến, xếp lại theo vị trí hình học.

### Bốn vai, không phải sáu khối

`amr` xếp biến theo `block = "E4 · Φ_sys"` — xếp **đại số**, trả lời câu "đây là
hệ số của công thức nào". `amr3` xếp theo bốn vai, và chúng là bốn thứ khác nhau
**về hình học**:

| vai | làm gì | ví dụ |
|---|---|---|
| **vị trí** | dịch **chính tấm** | `θ_0`, `σ*`, `κ_base`, `φ_0` |
| **tiếp tuyến** | dịch **một điểm trên** tấm | mọi `α_i`, `β_j`, `φ_G`, `a_V` |
| **độ cong** | tấm **cong** bao nhiêu | `θ`, `k_Ψ`, `λ_2`, `w_CT` |
| **biên độ** | tấm lệch **tối đa** bao nhiêu | `L_max`, `δ_off` |

Còn có vai `CARRIER` cho các biến **mang một giá** thay vì định một hình dạng.

**Toàn bộ `amr` sống ở vai tiếp tuyến.** Đó là lý do nó trượt song song, và lý
do chỉ vai **vị trí** là vai mà một vết đâm chạm tới được: đâm xuyên nghĩa là
**tấm** bị dịch, không phải một điểm trên tấm bị dịch.

`test_atlas_covers_every_amr_variable_exactly_once` khẳng định 78/78 — không
thêm, không bớt.

### Bảy tấm

```
MECHANICAL   STATE   STRUCTURAL   REFLEXIVE   PSYCHO   SECULAR   HAVEN
```

Σ₄ là tấm duy nhất **không có** trọng số vị trí, nên không gì đâm ngược vào nó
được. Đó không phải thiếu sót — Remark 10.2 của sách nói Tầng 4 *"là một
nguồn… nó tác động lên Tầng 3 và 5 và không bị gì tác động lại."*

### Đúng một tham số mới

```
τ_{ℓm} ∈ [0,1]     phần PHÁP TUYẾN của tác động từ tấm ℓ lên tấm m
a = a_∥ + a_⊥      a_∥ = (1−τ)·tải,   a_⊥ = τ·tải
```

**Không thêm cạnh nào.** Tập cạnh lấy nguyên từ trường `gamma` trong
`amr/registry.py`, nơi các tải trọng liên tầng đã được mã hoá sẵn. Đúng **một**
cạnh trong số đó có tải bằng 0, và nó là cạnh duy nhất trỏ vào một trọng số
**vai vị trí**: `Σ₄ → Σ₅`, `hsoc → theta_0`. Ghi chú trong chính registry viết:
*"The loading below is the departure, and it is zero by default."* Cửa đã lắp
sẵn và khoá.

```python
from amr3 import Options3, Transversality, Memory

Options3(tv=Transversality.zero())        # τ ≡ 0 — giả thuyết không, và là mặc định
Options3(tv=Transversality.knife())       # τ = 0,294, mức trần
Options3(tv=Transversality.knife(0.15))   # giá trị nào bạn muốn
```

`TAU_CEILING` là `0.294`, và nó **khác nhau** theo mô hình trí nhớ:

```python
TAU_CEILING_BY_MODE == {"hysteresis": 0.294, "fatigue": 0.122}
```

### Độ sâu vết đâm không tuỳ ý

```
Δξ_m = τ_{ℓm} · p · (src_ℓ − H*_ℓ)₊ · (1 + q · II_m)
II_m = 4 · Λ′(arg_m) ∈ [0,1]
```

Thừa số 4 không phải chuẩn hoá cho đẹp. `Λ′ ≤ ¼` là **chính** bất đẳng thức mà
Proposition 8.2 dùng để lấy biên co `ηκ_A g₁ < 4`, và mà Layer W dùng để lấy
biên `max_k Σ_j |C_kj| < 4`. Cùng một con số ¼ chặn tính co thì cũng chặn **độ
căng**: tấm căng nhất đúng ở nơi nó dốc nhất, tức ở điểm uốn. Giấy căng thì
rách, giấy chùng thì dạt.

Trên Σ₅ quy tắc này là **đúng hệt**, không xấp xỉ: vì
`Ψ_str = 1 − L_max·Λ(k_Ψ(f_hard − θ_0))` nên `(1−Ψ_str)/L_max = Λ(arg)` theo
định nghĩa, và `4v(1−v) = 4Λ′(arg)`. **Trên Σ₁ thì là xấp xỉ**, vì `σ_sys` là
hợp tuyến tính chứ không phải logistic — và điều đó được **nói ra** chứ không bỏ
qua.

### Tính đơn điệu là tất cả

`ξ_m(t)` không giảm, bao giờ. Mọi tính bất khả hoàn nguyên, mọi phụ thuộc đường
đi, mọi giao hoán tử khác không đều chỉ từ một dấu `≥` mà ra. Không có cơ chế
thứ hai nào được thêm.

### Từ Python

```python
from amr3 import (Options3, Transversality, Memory, Move, Sheet,
                  trace, commutator, holonomy, residual)
from amr import WorldState

state = WorldState()
opt   = Options3(tv=Transversality.knife(), memory=Memory.HYSTERESIS)

# các trường của Options3: tv, fragmentation_feedback, amr, memory
# trace(moves, state, opt, settle)
```

`trace(..., settle=True)` thêm **một bước lắng** không toán tử. Bạn **cần** nó:
vết sẹo của một bước được cộng **sau** khi bước đó đọc số, nên dừng ngay thì vết
đâm cuối được ghi mà không phép đọc nào thấy nó, và lúc đó giao hoán tử sẽ đo
lẫn cả **thời điểm đọc** chứ không chỉ đo thứ tự. Bước lắng đưa mọi đường về
cùng một quy ước quan sát.

---

## 7. Ba phép đo

`amr3` đo ba đại lượng mà cả ba **bằng đúng 0** trong `amr`:

| | τ ≡ 0 | trễ · τ = 0,294 | mỏi · τ = 0,122 |
|---|---|---|---|
| giao hoán tử ‖[L₄, L₅]‖ | **0,000e+00** | **0,000e+00** | 1,720e-02 |
| holonomy H(γ) | **+0,000e+00** | **−7,318e-02** | **−4,056e-02** |
| dư âm sau khi gỡ sốc | **+0,000000** | **+0,027931** | **+0,011078** |

Cột đầu **không** phải kết quả hiệu chỉnh. Tầng E9 là một hàm của
`(D_i, S_j, σ, Φ, κ, Ψ)` và không mang theo lịch sử nào, nên hai đường đi tới
cùng một trạng thái **bắt buộc** cho cùng một đầu ra. `amr` không thiếu một số
hạng — nó nằm trong một **lớp hàm** không thể chứa hiện tượng "cái lỗ còn lại".

**Giao hoán tử tách đúng hai nhánh.** Dạng trễ lấy cực đại theo lịch sử; hai thứ
tự đi qua cùng tập trạng thái nên hai cực đại bằng nhau, nên giao hoán tử bằng 0
**theo định nghĩa của toán tử**. Dạng mỏi tích phân, nên thứ tự có nghĩa.
Holonomy và dư âm khác 0 ở **cả hai**: vòng kín về đúng trạng thái đầu, vết sẹo
thì ở lại.

### Câu hỏi thực nghiệm

Câu này không cần đợt dữ liệu dài:

> **Thứ tự hai cú sốc có đổi mức thường trực không, khi trạng thái cuối giữ
> nguyên?**
>
> Có → mỏi. Không → trễ.

### Bất biến đúng không phải số chiều

Một mô hình hai tầng mà có vết sẹo thì đã là đâm xuyên; một mô hình mười tầng mà
không có vết sẹo thì vẫn chỉ là trượt. Bất biến đáng kể là các toán tử tầng **có
giao hoán hay không** — và giao hoán tử là **đại số**, nên "hình học chứ không
phải đại số" là một **phân đôi giả**, dù phần nội dung của luận điểm thì đúng
nguyên vẹn. Repo này tự nói ra điều đó về chính cách nó đóng khung vấn đề, thay
vì tô hồng.

---

## 8. Trễ hay mỏi

Đây là hai **VẬT LÝ** khác nhau, không phải hai xấp xỉ của cùng một thứ.

```python
Options3(memory=Memory.HYSTERESIS)   # mặc định — ξ = CỰC ĐẠI theo lịch sử
Options3(memory=Memory.FATIGUE)      #            ξ = TÍCH PHÂN theo dt
```

**HYSTERESIS (trễ)** — chỉ các cực trị của đường đi được tính; thời lượng không
vào công thức. Đây là toán tử play/stop của lý thuyết trễ, và là dạng
Baldwin–Krugman (1989) dùng cho chính tỉ giá. Nó là mặc định vì nó là nội dung
của luận điểm, là toán tử chuẩn của tài liệu, và **độc lập với tốc độ**.

**FATIGUE (mỏi)** — thời lượng **thay thế được** biên độ. Quy tắc Miner trong
mỏi vật liệu. Nó được giữ lại vì nó nêu một dự đoán **khác** và **bác bỏ được**,
không phải vì nó xấp xỉ cái kia.

| tổng dt | trễ | mỏi |
|---|---|---|
| 1 | 0,132064 | 0,132440 |
| 4 | 0,132064 | 0,200946 |
| 32 | **0,132064** | **0,840335** |

Hàng trễ phẳng tuyệt đối. Đó không phải xấp xỉ — thời lượng không có trong công
thức.

### Độc lập với tốc độ

Chia **cùng một đường đi** thành nhiều bước hơn thì kết quả phải không đổi. Đó
là tính chất **định nghĩa** của mọi toán tử trễ, và
`test_scar_is_rate_independent_in_both_modes` giữ code đúng theo nó. Hai lỗi
trước đây làm hỏng đúng chỗ này và đã được sửa; test đó tồn tại để chúng không
quay lại.

---

## 9. Kiểm thử

```bash
python tests/test_engine.py     # amr   — các tầng, biên, Table 10.3
python tests/test_amr2.py       # amr2  — toàn vẹn dữ liệu, 2026 không lọt vào
python tests/test_amr3.py       # amr3  — atlas 78/78, lồng khít tại τ→0
```

Chạy cả ba **từ gốc repo**. Tất cả pass trên Python 3.12, trên Windows, macOS
và Linux.

Các bộ test này kiểm **cấu trúc**, không chỉ kiểm output. Vài cái đáng biết:

- `test_atlas_covers_every_amr_variable_exactly_once` — 78/78
- `test_tau_zero_reproduces_amr_exactly` — khẳng định lồng khít
- `test_tau_zero_matches_amr_along_a_whole_path` — lồng khít **dọc một quỹ
  đạo**, không chỉ tại một điểm
- `test_scar_is_monotone_non_decreasing` — một dấu `≥` mà mọi thứ dựa lên
- `test_scar_is_rate_independent_in_both_modes` — tính chất của toán tử trễ
- `test_the_knife_edge_is_the_one_amr_set_to_zero` — cạnh tải-0 duy nhất
- `test_world_state_is_never_mutated_in_place`
- `test_amr2_is_untouched` và `test_amr3_does_not_import_amr2` — tính độc lập
  của mô hình đối thủ được **cưỡng chế**, không chỉ là ý định
- `test_training_never_touches_2026` — bảo đảm ngoài mẫu

---

## 10. Được và không được khẳng định điều gì

**`amr` là định tính.** Nó cho ra thang mũi tên và phân rã ba khối, không phải
một dự báo điểm đã hiệu chỉnh. `python -m amr audit` chạy mọi kịch bản đối chiếu
số liệu của chính sách, để khoảng cách **hiện ra** thay vì bị ngụ ý.

**Bạn ĐƯỢC:**
- báo cáo khối nào chi phối một cú dịch chuyển, và với tỉ lệ bao nhiêu
- báo cáo **hướng** và độ lớn theo thang mũi tên
- báo cáo tình trạng bằng chứng của các kênh mang một kết quả
- báo cáo rằng một kết quả có **vững** hay không khi bật một cờ mở rộng
- báo cáo các con số **ngoài mẫu** của `amr2` **đúng như là** con số ngoài mẫu
- báo cáo ba phép đo của `amr3`, **kèm nêu rõ mô hình trí nhớ**

**Bạn KHÔNG ĐƯỢC:**
- trích một con số phần trăm của `amr` như một dự báo đã hiệu chỉnh
- trích một kết quả mà không nói nó do mô hình trí nhớ nào sinh ra — trễ và mỏi
  là hai vật lý khác nhau và cho những con số khác nhau
- trích một kết quả τ > 0 mà không nêu τ, vì cả mặc định lẫn giả thuyết không
  của nó đều là 0
- coi quy tắc độ căng trên Σ₁ là **đúng hệt**; nó chỉ đúng hệt trên Σ₅
- coi khung hình học là một khẳng định về **số chiều**
- dùng tháng 2025-10 của `amr2` mà không kiểm `cpi_imputed`

Nếu một kết luận sống sót qua **cả hai** mô hình trí nhớ, một đợt quét τ, và các
cờ mở rộng, thì bạn có một thứ **mang tính cấu trúc**.

---

## 11. Xử lý sự cố

**`ModuleNotFoundError: No module named 'amr'`**
Bạn đang chạy từ bên trong một thư mục package, hoặc `amr3`/`amr2` không thấy
gốc repo. Hãy chạy từ thư mục trên cùng của bản clone.

**`ModuleNotFoundError: No module named 'series'`**
`amr2` nạp `data/series.py` theo đường dẫn tương đối so với gốc repo. Hãy đảm
bảo `data/` có mặt và bạn đang ở trên cùng của bản clone.

**`amr: error: unrecognized arguments: --recentre`**
Các cờ mở rộng là **toàn cục** và đặt **trước** subcommand:
`python -m amr --recentre run narrative`.

**`amr run: error: the following arguments are required: scenario`**
`run` cần một tên kịch bản. `python -m amr list` hiện danh sách.

**Panel 3D trắng trơn**
Nó cần `three.js` từ CDN, nên lần tải đầu đòi có mạng. Nếu bạn offline, hãy tải
`https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js` về rồi trỏ
`<script src=…>` vào bản local. Panel trắng kèm lỗi console `THREE is not
defined` đúng là trường hợp này.

**Chữ trong panel hiện ra như `Äa táº¡p`**
Đó là lỗi **mã hoá ký tự**, và nó không nên xảy ra — mỗi panel đã khai báo
`<meta charset="utf-8">` ngay những byte đầu. Nếu bạn thấy nó, rất có thể file
đã bị một editor lưu lại ở một encoding không phải UTF-8.

**Lỗi Unicode trong console**
Đáng lẽ không xảy ra; các entry point tự đặt stdout về UTF-8. Nếu bạn gặp, xin
báo OS, terminal và phiên bản Python — cách chữa tạm là đặt
`PYTHONIOENCODING=utf-8`.

---

## Xem thêm

- [README.vi.md](../README.vi.md) — bản ngắn
- [README.md](../README.md) — English
- [GUIDE.en.md](GUIDE.en.md) — hướng dẫn này bằng tiếng Anh
- [../SPEC.md](../SPEC.md) — toàn bộ phần toán
- [huong-dan-su-dung-vi.pdf](huong-dan-su-dung-vi.pdf) — sổ tay `amr3`
- [amr3-notes-vi.md](amr3-notes-vi.md) / [amr2-notes-vi.md](amr2-notes-vi.md) —
  ghi chú thiết kế, mang tính tranh luận hơn là hướng dẫn
- [The_Architecture_of_Market_Regimes_Model.pdf](The_Architecture_of_Market_Regimes_Model.pdf) —
  bài báo gốc
