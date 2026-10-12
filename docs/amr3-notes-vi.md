# amr3 — cùng mô hình, đọc trong hệ toạ độ hình học

```bash
python -m amr3                    # bản đồ, lồng khít, ba phép đo, quét τ, dải, phân mảnh
python tests/test_amr3.py         # 42 kiểm thử, gồm cả lồng khít τ→0
```

`amr3` **không** là mô hình thứ ba. Nó là chính `amr`, với 78 biến giữ nguyên, xếp lại theo **vị trí hình học** thay vì theo phương trình chúng là hệ số của. Và nó **nhập** `amr`, chạy `amr.run` ở trong — khác hẳn `amr2`, vốn cố tình không nhập để còn đứng riêng mà so.

Lý do khác nhau đó là lý do duy nhất đáng kể: `amr2` là một mô hình **khác**, nên phải độc lập. `amr3` là cùng mô hình **đọc khác**, nên phải **lồng khít**, và cách chứng minh lồng khít là chạy chính bản gốc ở trong.

```
τ ≡ 0  →  overrides rỗng  →  ln DXY trùng amr, chênh lệch 0.000e+00
```

---

## Phân phối lại: bốn vai, không phải sáu khối

`amr` xếp biến theo `block = "E4 · Φ_sys"` — xếp **đại số**, trả lời câu "đây là hệ số của công thức nào". `amr3` xếp theo bốn vai, và chúng là bốn thứ khác nhau về hình học:

| vai | làm gì | ví dụ |
|---|---|---|
| **vị trí** | dịch **chính tấm** | `θ_0`, `σ*`, `κ_base`, `φ_0` |
| **tiếp tuyến** | dịch **một điểm trên** tấm | mọi `α_i`, `β_j`, `φ_G`, `a_V` |
| **độ cong** | tấm **cong** bao nhiêu | `θ`, `k_Ψ`, `λ_2`, `w_CT` |
| **biên độ** | tấm lệch **tối đa** bao nhiêu | `L_max`, `δ_off` |

Toàn bộ `amr` sống ở vai **tiếp tuyến**. Đó là lý do nó trượt song song, và chỉ vai **vị trí** là vai một vết đâm tác động tới được: đâm xuyên nghĩa là tấm bị dịch, không phải điểm trên tấm bị dịch.

`tests/test_amr3.py::test_atlas_covers_every_amr_variable_exactly_once` khẳng định 78/78, không thêm không bớt.

---

## Một tham số mới duy nhất

```
τ_{ℓm} ∈ [0,1]     phần PHÁP TUYẾN của tác động từ tấm ℓ lên tấm m
a = a_∥ + a_⊥      a_∥ = (1−τ)·tải,   a_⊥ = τ·tải
```

Tập cạnh **không được thêm cái nào**. Nó lấy nguyên từ trường `gamma` trong `amr/registry.py`, nơi các tải trọng liên tầng đã được mã hoá sẵn:

| cạnh | biến nguồn | trọng số đích | vai đích | tải |
|---|---|---|---|---|
| Σ₁ → ⊥ | `sigma` | `alpha_prec` | tiếp tuyến | +0,70 |
| Σ₁ → ⊥ | `sigma` | `lam_1` | tiếp tuyến | +0,60 |
| Σ₄ → Σ₂ | `hsoc` | `phi_R` | tiếp tuyến | +0,60 |
| Σ₄ → Σ₃ | `hsoc` | `a_M` | tiếp tuyến | −0,45 |
| Σ₄ → Σ₃ | `hsoc` | `a_sigma` | tiếp tuyến | +0,50 |
| Σ₄ → Σ₃ | `iimp` | `a_sigma` | tiếp tuyến | +0,30 |
| **Σ₄ → Σ₅** | `hsoc` | **`theta_0`** | **vị trí** | **+0,00** |

Đúng một cạnh có tải bằng 0, nó là cạnh duy nhất trỏ vào một trọng số **vai vị trí**, và nó là cạnh con dao nói về. Ghi chú trong registry viết nguyên văn: *"The loading below is the departure, and it is zero by default."* Cửa đã lắp sẵn và khoá.

Σ₄ là tấm duy nhất **không có** trọng số vị trí, nên không đâm ngược lại được. Không phải thiếu sót — Remark 10.2: Tầng 4 *"là một nguồn… nó tác động lên Tầng 3 và 5 và không bị gì tác động lại."*

---

## Độ sâu vết đâm không tuỳ ý

```
Δξ_m = τ_{ℓm} · p · (src_ℓ − H*_ℓ)₊ · (1 + q · II_m)
II_m = 4 · Λ′(arg_m) ∈ [0,1]
```

Thừa số 4 không phải chuẩn hoá cho đẹp. `Λ′ ≤ ¼` là **chính** bất đẳng thức Proposition 8.2 dùng để lấy biên co `ηκ_A g₁ < 4`, và Layer W dùng để lấy biên `max_k Σ_j |C_kj| < 4`. Cùng một con số ¼ chặn tính co cũng chặn **độ căng**: tấm căng nhất đúng ở nơi nó dốc nhất, tức ở điểm uốn. Giấy căng thì rách, giấy chùng thì dạt.

Trên Σ₅ quy tắc này là **đúng hệt**, không xấp xỉ: `Ψ_str = 1 − L_max·Λ(k_Ψ(f_hard − θ_0))`, nên `(1−Ψ_str)/L_max = Λ(arg)` theo định nghĩa, và `4v(1−v) = 4Λ′(arg)`. Trên Σ₁ thì là xấp xỉ, vì `σ_sys` là hợp tuyến tính chứ không phải logistic — và điều đó được nói ra chứ không bỏ qua.

**Tính đơn điệu là tất cả.** `ξ_m(t)` không giảm, bao giờ. Mọi tính bất khả hoàn nguyên, mọi phụ thuộc đường đi, mọi giao hoán tử khác không đều chỉ từ một dấu `≥` mà ra. Không có cơ chế thứ hai nào được thêm.

---

## Ba đại lượng, cả ba bằng 0 trong `amr` theo lớp hàm

| | τ ≡ 0 | trễ · τ = 0,294 | mỏi · τ = 0,122 |
|---|---|---|---|
| giao hoán tử ‖[L₄, L₅]‖ | **0,000e+00** | **0,000e+00** | 1,720e-02 |
| holonomy H(γ) | **+0,000e+00** | **−7,318e-02** | **−4,056e-02** |
| dư âm sau khi gỡ sốc | **+0,000000** | **+0,027931** | **+0,011078** |

**Giao hoán tử tách đúng hai nhánh.** Dạng trễ lấy cực đại theo lịch sử; hai thứ tự đi qua cùng tập trạng thái nên cực đại bằng nhau, nên giao hoán tử bằng 0 **theo định nghĩa của toán tử**. Dạng mỏi tích phân, nên thứ tự có nghĩa. Holonomy và dư âm khác 0 ở cả hai: vòng kín về đúng trạng thái đầu, vết sẹo thì ở lại.

Câu hỏi thực nghiệm tương ứng, và nó không cần đợt dài: **thứ tự hai cú sốc có đổi mức thường trực không, khi trạng thái cuối giữ nguyên?** Có → mỏi. Không → trễ.

Hàng đầu không phải con số hiệu chỉnh ra. E9 là một hàm của `(D_i, S_j, σ, Φ, κ, Ψ)` và không mang theo lịch sử nào, nên hai đường tới cùng một trạng thái **bắt buộc** cho cùng một đầu ra. `amr` không thiếu một số hạng — nó nằm trong một **lớp hàm** không chứa hiện tượng "cái lỗ còn lại".

**Bất biến đúng không phải số chiều.** Một mô hình hai tầng có vết sẹo thì đã là đâm xuyên; một mô hình mười tầng không có vết sẹo thì vẫn là trượt. Bất biến đúng là các toán tử tầng **có giao hoán hay không** — và giao hoán tử là đại số, nên "hình học chứ không phải đại số" là phân đôi giả, trong khi phần nội dung của luận điểm thì đúng nguyên vẹn.

### Một bước lắng, và vì sao nó cần

Vết sẹo của một bước được cộng **sau** khi bước đó đọc số. Dừng ngay thì vết đâm cuối được ghi mà không phép đọc nào thấy nó, và giao hoán tử đo lẫn cả **thời điểm đọc** chứ không chỉ đo thứ tự. `trace(..., settle=True)` thêm một bước không toán tử, đưa mọi đường về cùng một quy ước quan sát.

---

## Hai dạng trí nhớ, và chúng là hai VẬT LÝ khác nhau

```python
Options3(memory=Memory.HYSTERESIS)   # mặc định — ξ = CỰC ĐẠI theo lịch sử
Options3(memory=Memory.FATIGUE)      #            ξ = TÍCH PHÂN theo dt
```

**HYSTERESIS** — chỉ cực trị của đường đi đếm; thời lượng không vào công thức. Đây là toán tử play/stop của lý thuyết trễ, và là dạng Baldwin–Krugman (1989) dùng cho chính tỉ giá. Mặc định, vì nó là nội dung của luận điểm, là toán tử chuẩn của tài liệu, và độc lập với tốc độ.

**FATIGUE** — thời lượng **thay thế được** biên độ. Quy tắc Miner trong mỏi vật liệu. Giữ lại vì nó nêu dự đoán **khác** và bác bỏ được, không phải vì nó là xấp xỉ của dạng kia.

| tổng dt | trễ | mỏi |
|---|---|---|
| 1 | 0,132064 | 0,132440 |
| 4 | 0,132064 | 0,200946 |
| 32 | **0,132064** | **0,840335** |

Hàng trễ phẳng tuyệt đối. Đó không phải xấp xỉ — thời lượng không có trong công thức.

## Độc lập với tốc độ, và hai lỗi đã sửa

Chia **cùng một đường đi** thành nhiều bước hơn thì kết quả phải không đổi. Đó là tính chất định nghĩa của mọi toán tử trễ. Bản trước hỏng ở hai chỗ:

| | tỉ lệ max/min trên 20 bước |
|---|---|
| bản trước (cộng dồn theo `step()`, II đọc từ tấm đã dịch) | **6,3×** |
| chỉ sửa sang cực đại | 2,1× |
| sửa cả hai | **1,000×** |

**Lỗi một.** Vết sẹo cộng theo mỗi lần gọi `step()`. Nhánh mỏi *được phép* phụ thuộc thời lượng — đó là nội dung của nó — nhưng thời lượng phải **khai báo** qua `Move(dt=...)`, không phải suy ra từ việc người dùng bấm `step()` bao nhiêu lần. Một bước `dt = 4` giờ cho đúng cùng kết quả như bốn bước `dt = 1`.

**Lỗi hai, và nó nặng hơn.** Độ cong `II` của tấm đích đọc từ chính tấm **đã bị dịch**, nên độ sâu vết dịch phụ thuộc vết dịch đã có — **toán tử ăn chính đầu ra của nó**. Giờ `II` lấy từ một lần chạy không có vết sẹo, nên độ sâu là phiếm hàm của **đường đi ngoại sinh** và không gì khác.

### Một kết quả đã RÚT LẠI

Bản trước báo một **đảo dấu** của hiệu ứng thứ tự ở `Λ ≈ 0,98`: cứng-trước đâm sâu hơn meme-trước. Đó là **tạo tác của lỗi hai** — thứ tự nào tạo vết sẹo sớm hơn thì tự thay đổi điều kiện cho bước sau. Sửa xong, meme-trước sâu hơn ở **mọi** biên độ, dấu nhất quán. `test_order_effect_has_one_consistent_sign_in_fatigue_mode` giữ kết quả đúng.

## Phát hiện: không giao hoán sống trong một DẢI (chỉ ở nhánh mỏi)

Quét biên độ ở `τ₄₅ = 1`, dạng **mỏi** — ở dạng trễ giao hoán tử bằng 0 ở mọi biên:

| biên | Λ(arg) | sẹo meme-trước | sẹo cứng-trước | ‖[L₄,L₅]‖ | ai sâu hơn |
|---|---|---|---|---|---|
| 0,74 | 0,585 | 0,0000 | 0,0000 | **0,000e+00** | — |
| 0,78 | 0,655 | 0,0378 | 0,0276 | 9,89e-03 | meme |
| **0,80** | 0,841 | **0,1815** | **0,1346** | **3,76e-02** ← đỉnh | meme |
| 0,84 | 0,992 | 0,5035 | 0,3896 | 1,50e-02 | meme |
| 0,88 | 1,000 | 0,8203 | 0,6630 | 4,39e-04 | meme |
| 0,96 | 1,000 | 1,1066 | 0,9167 | **0,000e+00** | meme |

Ba chế độ:

1. **biên < 0,77** — `H_soc` chưa qua `H*`. Không có vết đâm nào. Trượt.
2. **0,78 – 0,84** — có đâm, tấm chưa bão hoà. Đỉnh ở 0,80. Meme-trước đâm **sâu hơn** vì giấy còn đàn hồi.
3. **biên ≥ 0,86** — `Λ → 1`, tấm bão hoà ở `L_max`. Giao hoán tử **sập về 0**. Dấu **không** đảo.

Đây là chỗ hình học trả lại một thứ ẩn dụ **không** cho: con dao chỉ để lại cái lỗ **phụ thuộc thứ tự** trong một dải. Dưới dải giấy chỉ võng; trên dải giấy đã nát và thêm một nhát không đổi được đầu ra nữa — vì `L_max`, một trọng số vai **biên độ**, chặn tổng thiệt hại. Ở biên 0,95 hai thứ tự cho vết sẹo chênh 0,10 mà `ln DXY` chênh dưới 1e-3: bằng chứng rằng chặn nằm ở biên độ tấm, không ở độ sâu vết đâm.

Điểm hoà vốn của nhánh mỏi — bao nhiêu kỳ ở biên vừa thì bằng một kỳ ở biên cực đại — là **dự đoán bác bỏ được** của nhánh đó. Nhánh trễ nói phép so sánh ấy không có nội dung.

---

## Phân mảnh chính trị thôi là đầu vào

```
T_frag(t) = T_frag⁰ + ρ · ξ_2(t)        ρ = 0,50
```

| cấu hình | T_frag cuối | sẹo ξ₂ | ln DXY |
|---|---|---|---|
| `amr` — τ≡0, không phản hồi | 0,7000 | 0,0000 | 4,390845 |
| τ₄₂=0,262, không phản hồi | 0,7000 | 0,5540 | 4,205032 |
| τ₄₂=0,262, **có** phản hồi | **0,9051** | 0,5455 | 4,198951 |

Trong `amr`, `T_frag` là biến ẩn Tầng 2 người dùng **tự điền** (nền 0,420; đo thay bằng BIS triennial FX turnover). Ở đây nó thành **hệ quả** của việc tầng meme đâm qua tầng cấu trúc. Mặc định tắt (`fragmentation_feedback=False`).

---

## Đơn vị của pháp tuyến — bản đồ đã trả lời

Pháp tuyến của một tấm đo bằng **đơn vị của trọng số vai vị trí của tấm đó**:

| tấm | trọng số vị trí | là ngưỡng/mức trên | pháp tuyến đo bằng |
|---|---|---|---|
| Σ₅ | `θ_0` | `f_hard` | đơn vị `f_hard` |
| Σ₁ | `σ*` | `σ_sys` | đơn vị `σ_sys` |
| Σ₃ | `κ_base` | `κ` | đơn vị `κ` |
| Σ₂ | `φ_0` | `Φ` | đơn vị `Φ` |

Không phải quy ước áp từ ngoài: nó rơi ra từ **vai** của trọng số, và `atlas.py` đã gán vai. Khi đó τ có dạng ước lượng được: tiếp tuyến viết lại được thành một dịch chuyển `f_hard` tương đương nên thừa hưởng độ dai của `f_hard` và **hoàn nguyên**; pháp tuyến dịch `θ_0` nên **không**. Vậy **τ = tỉ phần thường trực của phản ứng** — Beveridge–Nelson, hoặc local projection chân trời dài.

## Trần của τ, suy từ dữ liệu

```
VR(36) = 0,884   z = −0,27      thành phần thường trực của ln DXY TỒN TẠI
VR(60) = 0,842   z = −0,28      (không phân biệt được với bước ngẫu nhiên)

cap + oil giải thích 48,2% biến thiên 36 tháng
phần dư 51,8%, và PHẲNG từ k = 6 tới k = 36

d(ln DXY)/dθ₀ = +48,31 điểm %/đơn vị
ξ₅ cần để sinh TOÀN BỘ phần dư    = 0,1319
ξ₅ một cú sốc cực đại ở τ=1       = 0,4492 (trễ) · 1,0856 (mỏi)
                                    ──────
                   τ ≤ 0,294 (trễ) · 0,122 (mỏi)
```

Chặn **trên**, không phải ước lượng điểm: phần dư còn chứa mọi thứ khác mà hai kênh không đo. τ vẫn chưa nhận dạng được điểm, nhưng nó thôi là một núm quay tự do — nó có trần, và trần đó bác bỏ được.

### Trần phụ thuộc DẠNG TRÍ NHỚ

Cùng ngân sách `ξ₅ = 0,1319`, một đơn vị τ sinh lượng ξ khác nhau ở hai dạng:

| dạng | ξ₅ ở τ = 1, một cú sốc | trần |
|---|---|---|
| trễ | 0,4492 | **0,294** |
| mỏi | 1,0856 | **0,122** |

Trần của nhánh mỏi giả định đợt kéo dài **một** kỳ; đợt dài hơn hạ nó xuống nữa, và đó là hệ quả của nhánh mỏi chứ không phải khuyết điểm. Một trần dùng chung sẽ là con số sai ở ít nhất một nhánh.

## Năm hằng số, mang đúng bộ thông tin 39 trọng số của `amr` phải mang

| | nền | vùng khả dụng | xuất xứ | bằng chứng |
|---|---|---|---|---|
| `τ` | 0,000 | [0,000 · 0,294] trễ · [0,000 · 0,122] mỏi | OPEN | PARTIAL |
| `H*` | 0,450 | [0,300 · 0,700] | ENGINE_CONVENTION | UNTESTED |
| `p` | 0,350 | [0,000 · 1,000] | ENGINE_CONVENTION | UNTESTED |
| `q` | 2,500 | [0,000 · 5,000] | ENGINE_CONVENTION | UNTESTED |
| `ρ` | 0,500 | [0,000 · 1,000] | ENGINE_CONVENTION | UNTESTED |

Bốn cái dưới **tôi đặt**. Ban đầu cả năm là float trần và `τ = 1,00` được nhận im lặng — đúng khuyết tật ISSUES #36 ghi cho CS8. Giá trị ngoài vùng giờ trả về **nhãn**, không trả về lỗi, theo đúng quy ước `core.run` ("returns a labelled answer rather than spinning").

## Mười chín ô người dùng vẫn tự điền

`atlas.unmeasured()` đọc trường `measurement` của chính `amr`:

| tấm | ô |
|---|---|
| Σ₄ | `A_alg` `C_src` `E_sys` `P_AI` `P_habit` `R_div` `R_fric` `S_access` `T_exp` |
| Σ₂ | `G_pol` `H_cap` `M_trust` `R_US` `T_frag` |
| Σ₃ | `A_meta` `V_USD` |
| Σ₅ | `Au_sub` `C_alt` |
| Σ₀ · Σ₁ | `S_off` · `X_health` |

Chín biến Tầng 4 ghi nguyên văn "No series". Và `H_soc` **không phải đầu vào**: nó là điểm bất động của Eq (8.8) giải **từ** chín ô đó, nên một giá trị `H_soc` là hệ quả của chín số tự điền, không phải một phép đo.

`amr3` **không vá** chỗ này. Nó dán nhãn, để số tự điền không lẫn với số đã đo. Đó là việc duy nhất đúng để làm với nó.

## Ba điều còn lại phải nói ra

**Một.** Bốn hằng số `H*`, `p`, `q`, `ρ` được **nêu bằng số** nên bác bỏ được ở sự kiện cực đoan kế tiếp — đó là toàn bộ điều được tuyên bố. Nhưng nêu bằng số thì chưa phải **ước lượng được**, và không ước lượng được chừng nào `H_soc` còn là hệ quả của chín ô tự điền.

**Hai.** Chuỗi DXY tháng 2006–2026 **không đủ** để chọn giữa hai nhánh. Chân trời 36 tháng cho khoảng sáu đợt độc lập; trên mẫu không chồng lấn cả biến đỉnh lẫn biến thời lượng đều mất ý nghĩa. Đây là ràng buộc **cỡ mẫu**, không sửa được bằng ước lượng khéo hơn. Phép thử nằm ở chiều chéo, trên bảng nhiều đồng tiền — đúng cách tài liệu trễ trong thương mại vẫn được kiểm.

**Ba.** Vết sẹo Σ₃ có lúc vượt biên của `kappa_base` và bị kẹp ở sàn `0,10`. Con số in ra là vết sẹo **trước** khi kẹp, nên nó lớn hơn phần thực sự đi vào mô hình. Kẹp thì được ghi, không bị làm lơ.

---

## Cái `amr3` KHÔNG làm

Nó không dự báo tốt hơn `amr2`. Nó không được kiểm trên dữ liệu ngoài mẫu, vì ba đại lượng nó đo — giao hoán tử, holonomy, dư âm — **chưa có chuỗi quan sát nào** để đối chiếu. Nó trả lời đúng một câu hỏi: *mô hình này có nằm trong lớp hàm chứa được hiện tượng đang nói tới hay không*, và câu trả lời ở `τ = 0` là không, với chênh lệch `0.000e+00`.

Giữ cả ba gói là để còn trả lời được ba câu khác nhau. Gộp lại thì mất cả ba.

---

*Vi Nhật Sơn · chỉ dành cho mục đích học thuật. Không con số nào ở đây là khuyến nghị đầu tư hay dự báo thị trường.*
