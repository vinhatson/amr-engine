# Layer W — Đặc tả lớp trọng số tham số

**Phần mở rộng cho** Vi Nhật Sơn, *The Architecture of Market Regimes: Modeling DXY
through Structural and Reflexive Layers* (Expanded and Consolidated Edition,
06-09-2026).

Tài liệu này đánh số tiếp nối hệ phương trình của sách: E1–E16 là của sách,
**E17–E28 là của phần mở rộng này**. Mọi ký hiệu giữ nguyên theo Appendix A.

---

## 0. Vấn đề mà Layer W giải

Trong sách, mọi trọng số là **hằng số**. Chương 17 báo cáo rằng dữ liệu từ chối
giữ chúng là hằng số:

> "λ₁ là một hằng số trong E9 và nhận dấu ngược nhau ở hai chế độ khi được ước
> lượng riêng" — Remark 11.3

> "các hệ số cơ học *có* co giãn theo σ_sys (Table 11.8), nên khôi phục κ_sys như
> một trạng thái ẩn duy nhất — điều Proposition 11.1 cho phép dù phân rã của nó
> là bất khả — là bước đơn lẻ hứa hẹn nhất trong danh sách này" — §17.8, hạng mục hai

Layer W là bước đó, được tổng quát hoá: **mọi trọng số trở thành một hàm bị chặn
của chính trạng thái mà mô hình tính ra, và các trọng số phản ứng lẫn nhau.**

Ba ràng buộc thiết kế giữ nó nằm *bên trong* sách chứ không phải bên cạnh sách:

| # | Ràng buộc | Kiểm chứng |
|---|-----------|------------|
| 1 | **Lồng khít tuyệt đối.** Tắt mọi tải trọng ⟹ engine tái tạo E9 từng số hạng | `test_nesting_exact`, `test_nesting_at_baseline_state` |
| 2 | **Không thêm dạng hàm mới.** Layer W dựng từ đúng cái logistic đã mang σ_sys, s_US, H_soc, Ψ_str và Λ(σ). §10.4: "sách có một hình chữ S." Vẫn đúng. | đọc `functions.py` |
| 3 | **Không trọng số nào rời vùng của nó.** Λ ánh xạ *ngặt* vào (0,1), nên E17 ánh xạ ngặt vào (lo, hi). Mọi biên mà ISSUES #9, #14, #26 và #3a áp đặt đều sống sót trước *bất kỳ* số hạng tương tác nào. | `test_weights_never_leave_their_zone` |

Layer W mang số 6 nhưng **cắt ngang**, không xếp chồng. Layers 0–5 là một tầng
điều biến: mỗi tầng thay đổi mức độ dữ dội mà tầng dưới truyền đi. Layer W không
nằm *trên* Layer 5; nó cắt qua cả sáu tầng, vì một trọng số thuộc về đúng cái
phương trình mà nó nằm trong. Gọi nó là tầng thứ bảy là mô tả sai kiến trúc —
bốn vai trò toán học của Table 10.4 không đổi vì nó.

---

## 1. E17 — Ánh xạ trọng số bị chặn

Với mỗi trọng số $w_k$ có vùng khả dụng $[\ell_k^-, \ell_k^+]$:

$$w_k(z,u) \;=\; \ell_k^- + (\ell_k^+ - \ell_k^-)\cdot \Lambda(d_k)$$

$$d_k \;=\; \ell_k \;+\; \underbrace{\sum_m \gamma_{km}\,(z_m - z_m^0)}_{\text{tải trạng thái bậc 1}} \;+\; \underbrace{\sum_{m\le n} \Gamma_{k,mn}\,(z_m - z_m^0)(z_n - z_n^0)}_{\text{bậc 2}} \;+\; \underbrace{\sum_{j\neq k} C_{kj}\,(u_j - u_j^0)}_{\text{ghép cặp trọng số, E18}}$$

với $\ell_k = \mathrm{logit}(u_k^0)$, $u_k^0 = (w_k^0 - \ell_k^-)/(\ell_k^+ - \ell_k^-)$,
và $\Lambda$ là logistic chuẩn.

### Vì sao tải trọng tác động lên **độ lệch** $(z_m - z_m^0)$ chứ không lên mức $z_m$

$z^0$ là trạng thái nền của Table 10.3. Nếu tải trọng tác động lên mức, Layer W
sẽ **âm thầm hiệu chỉnh lại bộ tham số đã công bố của sách** ngay khoảnh khắc
được bật, và không run nào còn so được với Figure 10.2. Với dạng lấy độ lệch:

- tại $z = z^0$, mọi trọng số bằng đúng giá trị nền *dù tải trọng lớn đến đâu*;
- một tải trọng đọc thành "hiệu ứng của việc dịch biến điều biến này một đơn vị
  đầy đủ khỏi nền" — đúng cách diễn giải mà Notation convention 3 của sách dành
  cho hệ số trên một biến bị chặn.

### Tính chất

| | Phát biểu | Hệ quả |
|---|---|---|
| **P1** | $w_k \in (\ell_k^-, \ell_k^+)$ với mọi $z$, mọi $C$ | Biên là *cấu trúc*, không phải kiểm tra lúc chạy. $\kappa_R$ không thể chạm 1. |
| **P2** | $\gamma = \Gamma = C = 0 \Rightarrow w_k \equiv w_k^0$ | E9 lồng khít. Phần mở rộng kiểm chứng được đối với chính thứ nó mở rộng. |
| **P2′** | $z = z^0 \Rightarrow w_k \equiv w_k^0$ với mọi $\gamma, \Gamma$ | Bộ tham số đã công bố giữ nguyên nghĩa tại trạng thái mà nó được công bố cho. |
| **P3** | $\partial w_k/\partial z_m = (\ell^+-\ell^-)\Lambda(1-\Lambda)\big(\gamma_{km} + \sum_n \Gamma_{k,mn}(z_n - z_n^0)\big)$ | Giảm dần ở hai cực — đúng dạng so sánh tĩnh mà E6 mang trong §7.7.5. |

**Một hành vi cần biết trước khi nó làm bạn bất ngờ:** một trọng số bị đẩy sát
biên vùng của nó có $\ell_k \to \pm\infty$ và **đóng băng** — không số hạng tương
tác nào dịch được nó. Đó là đúng chứ không phải lỗi (nó đã ở đúng cái biên mà
sách áp đặt), nhưng nghĩa là một thanh trượt ghim ở cuối dải sẽ tắt tương tác của
trọng số đó.

---

## 2. E18 — Hệ đồng thời của các trọng số

$$u \;=\; \Lambda\!\big(\ell + \Gamma(z - z^0) + C(u - u^0)\big)$$

Đây là điều người dùng hỏi khi hỏi "**phương trình tương tác giữa các trọng
số**": không phải một trọng số phản ứng với trạng thái, mà các trọng số phản ứng
**với nhau**, đồng thời, và nghiệm là một điểm bất động.

---

## 3. E19 — Tồn tại, duy nhất, và hệ số khuếch đại

> **Mệnh đề W.1 (Tồn tại, vô điều kiện).** Ánh xạ
> $u \mapsto \Lambda(\ell + \Gamma(z-z^0) + C(u-u^0))$ đưa khối lập phương lồi
> compact $[0,1]^K$ vào $(0,1)^K$ một cách liên tục. Theo định lý điểm bất động
> Brouwer, nó có ít nhất một điểm bất động, **với mọi ma trận ghép cặp $C$**.

Đây chính xác là tính tồn tại vô điều kiện mà sách chứng minh cho Layer 4 trong
Proposition 8.1. Hệ trọng số *luôn* ổn định ở đâu đó. Câu hỏi không bao giờ là
liệu nó có ổn định; mà là ở đâu, và liệu chỗ đó có duy nhất.

> **Mệnh đề W.2 (Co rút và duy nhất).** Jacobian có phần tử
> $\Lambda'(d_k)\,C_{kj}$, bị chặn bởi $|C_{kj}|/4$ vì $\Lambda' \le \tfrac14$.
> Hằng số Lipschitz theo chuẩn sup là $\tfrac14\max_k\sum_j |C_{kj}|$, nên
>
> $$\boxed{\;\max_k \sum_j |C_{kj}| \;<\; 4\;}$$
>
> khiến ánh xạ là co rút: điểm bất động **duy nhất**, **hút toàn cục** từ mọi
> điểm xuất phát, và đạt tới **theo cấp số nhân** với tốc độ $\tfrac14\|C\|_\infty$.

Đó là **đúng dạng** cận của Proposition 8.2 ($\eta\,\kappa_A\,g_1 < 4$), cho một
vòng lặp khác. Và đó là chủ đích: cả hai cận đều rơi ra từ một sự thật duy nhất,
rằng $\Lambda' \le \tfrac14$. Sách có một hình chữ S, nên nó có một hằng số co rút.

> **Hệ quả W.3 (Khuếch đại tham số).** Con số mà §17.4 gọi là "cho 'siêu giòn'
> một con số" — $1/(1-T')$ của Equation (8.10) — có bản sao ở đây:
>
> $$A_W \;=\; \frac{1}{1 - \|C\|_\infty/4}$$
>
> nhân hiệu ứng của mọi tải trọng, và **phân kỳ khi hệ trọng số tiến tới cùng
> cái biên đó**. Một mô hình hoá mà các trọng số của nó phản ứng mạnh với nhau
> giòn đúng theo cái nghĩa mà sách dùng cho thị trường.

Trên ngưỡng, engine **vẫn trả lời** và đánh dấu `unique = False`. Nó không âm
thầm chọn một nhánh.

---

## 4. E18′ — Ma trận ghép cặp: từng ô có một cơ chế

Không ô nào được thêm vì đối xứng, vì đầy đủ, hay vì một cặp nhìn hợp lý. **Một
ghép cặp không có cơ chế là một tham số tự do không có bằng chứng** — đúng thứ mà
Chương 11 dành bốn mươi trang để đếm.

| Ô | Dấu | Cơ chế trong sách |
|---|-----|-------------------|
| $a_\sigma \leftrightarrow a_H$ | **+** | §7.8 siêu giòn. Độ nhạy stress và đồng nhất niềm tin là hai nửa của một luận điểm: cú sốc truyền dữ dội *vì* các tác nhân phản ứng giống nhau. "Sóng thành tường." |
| $a_H \leftrightarrow a_I$ | **+** | §7.6 khuếch đại kép. Cùng một nguyên nhân công nghệ — cùng những nền tảng cung cấp mọi driver của cả hai — nên chúng tương quan trong thực tế, điều §8.3 ghi nhận trong khi Assumption 8.1 coi các driver là độc lập. |
| $a_M \leftarrow a_H$ | **−** | §7.6.2, kênh đối trọng mà bản gốc **không** ghi nhận. Tầng tâm lý-kỹ thuật chạm tới $\kappa_{sys}$ hai lần với dấu ngược nhau: trực tiếp qua $H_{soc}, I_{imp}$ (tăng) và gián tiếp qua $V_{meme} \to \lambda_f \to M_{shock}$ (giảm). Tăng ba lần $\lambda_f$ từ 0,05 lên 0,15 cắt ký ức năm 2018 từ 4,9 xuống 1,8. Sách ghi đây là **một dấu để ngỏ**; ô này làm nó *tính được*. |
| $\lambda_2 \leftarrow a_\sigma$ | **+** | §7.7.4: thiếu $(1+a_\sigma\sigma)$ thì mô hình không có biểu diễn nào cho $\kappa'(\sigma)>0$, "điều mà toàn bộ luận điểm độ lồi đặt lên". Hệ số lồi bậc hai là chỗ *còn lại* mang luận điểm ấy. Một luận điểm, hai phương trình, nên chúng đi cùng nhau. |
| $\varphi_R \leftrightarrow \kappa_R$ | **−** | Chốt chặn trùng đếm, nói thành lời. $R_{US}$ đặt **mức** cầu trú ẩn ở Layer 2 và làm suy giảm **truyền dẫn** ở Layer 3: "một đồng đô la do một nước Mỹ bất ổn chính trị phát hành vẫn là nơi trú ẩn nhưng trở thành bộ giảm chấn tệ hơn." Một cơ chế, tách qua hai tầng — nên dồn nặng vào một bên là bằng chứng chống lại việc dồn nặng vào bên kia. |
| $\varphi_G \leftrightarrow \gamma_G$ | **+** | Assumption 7.3 giữ $G_{pol}$ ra khỏi $\kappa_{sys}$ để tránh hệ số thứ ba trên một năng lực, "vì cho nó hệ số thứ ba ở đây sẽ khiến cả ba không nhận dạng được từ bất kỳ dữ liệu nào ta có". Hai cái còn lại là cùng một năng lực đọc hai lần và cũng *không* tách rời được; ô này **phát biểu** sự phụ thuộc thay vì giả vờ không có. |
| $w_F \leftrightarrow w_X$ | **−** | Table 11.6: composite $\sigma_{sys}$ hồi quy lên đô la *tệ hơn* chính thành phần ma sát của nó, và $p_{GPRD}$ tải $-0{,}24$ lên nhân tố mà các nhánh kia chia sẻ. Nhánh tin tức và nhánh funding là **thay thế** trong composite, không bổ sung. |
| $k_\Psi \leftarrow a_H$ | **+** | §10.7.4, cú sốc tự sự, dịch chuyển cả hai cùng lúc và không gì khác: $\kappa_{sys}$ 1,22 → 1,95 và $k_\Psi$ 6 → 28, không kênh cung/cầu nào bị chạm. Nắm giữ của tầng tự sự lên tầng phản thân và lên tầng thế tục là **một** nắm giữ. |
| $L_{max} \leftrightarrow \theta_0$ | **−** | Cả hai OPEN, cả hai trong E8, một chuỗi số liệu cho cả hai. Một sàn sâu và một ngưỡng muộn phát biểu *cùng một* luận điểm về quán tính hai lần, nên dữ liệu dịch được cái này phải dịch cái kia ngược lại. Ô này là một sự kiện về **nhận dạng**, không phải về kinh tế, và được gắn nhãn như vậy. |
| $\alpha_{prec} \leftrightarrow \lambda_1$ | **−** | Assumption 2.4 làm số hạng trú ẩn tách rời cộng tính khỏi khối cơ học trong log, và §10.7 là chỗ sách nói giả định đó *được xem xét* chứ không phải được thiết lập. Hai hệ số là **hai cách tham số hoá đối thủ** của một dòng chảy trú ẩn: cái nào mang nó thì cái kia mang ít đi. |

Với ma trận mặc định, $\|C\|_\infty = 0{,}70$, nên $A_W = 1{,}21$ — xa dưới cận 4.

---

## 5. E20 — Tỉ lệ trọng số

$$s_k \;=\; \frac{\big|\,(\partial \ln DXY/\partial w_k)\cdot(\ell_k^+ - \ell_k^-)\,\big|}{\sum_j \big|\,(\partial \ln DXY/\partial w_j)\cdot(\ell_j^+ - \ell_j^-)\,\big|}$$

**Vì sao nhân với dải khả dụng.** Đạo hàm thô $\partial/\partial w$ nằm trong đơn
vị của $w$, và các trọng số của mô hình này thuộc **sáu loại đơn vị khác nhau**:
một độ co giãn, một hệ số logit, một độ dốc, một ngưỡng, một tỉ lệ mất mát, một
trọng số hạng. Nhân với dải đặt **một** câu hỏi cho tất cả — "bao nhiêu phần của
dự báo thuộc trách nhiệm *vùng* của trọng số này?" — và câu hỏi đó có một đơn vị.
Đây đúng là phép chuẩn hoá mà Notation convention 3 của sách áp cho *biến*; ở đây
nó được áp cho *tham số*.

**Phiên bản toàn cục** (`monte_carlo`): lấy mẫu toàn bộ hình hộp khả thi và phân
rã phương sai đầu ra,
$$S_i = \frac{\mathrm{Var}_{x_i}\big(\mathbb{E}[Y\mid x_i]\big)}{\mathrm{Var}(Y)}$$
ước lượng bằng phân khoang, có hiệu chỉnh thiên lệch epsilon-bình phương. Với ma
trận ghép cặp bật, các trọng số tương tác, nên $\sum_i S_i \neq 1$ và **phần hụt
chính là thông tin**:

$$R_{\text{tương tác}} \;=\; 1 - \sum_i S_i$$

đo phần biến thiên của dự báo nằm ở **tương tác giữa các trọng số** chứ không ở
bất kỳ trọng số đơn lẻ nào. Đại lượng này **không có đối chứng trong sách**, vì ở
đó mọi trọng số là hằng số và không thể tương tác. Nó là thứ Layer W sinh ra để
nhìn thấy.

---

## 6. E21–E28 — Các biến bổ sung

Mỗi mục dưới đây đóng một khiếm khuyết mà Chương 17 **tự đặt tên**. Tất cả đều
**tắt mặc định**: bật một cái là một sự rời khỏi sách, và engine bắt người dùng
tự quyết định điều đó.

| | Đóng | Phát biểu | Vì sao sách không làm |
|---|------|-----------|------------------------|
| **E21** | Remark 11.3 | $\lambda_1(\sigma) = \lambda_1^{calm} + (\lambda_1^{crisis}-\lambda_1^{calm})\Lambda(\sigma)$ | Chính thiết bị $\Lambda$ của sách, áp lên chính vấn đề của sách. Sách giữ $\lambda_1$ là hằng số và ghi nhận dữ liệu từ chối giữ nó. |
| **E22** | **I37** | Tái định tâm độ lồi: $\lambda_1(\sigma-\bar\sigma) + \lambda_2(\sigma-\bar\sigma)^2$ với $\bar\sigma$ là trạng thái **vào** của đợt | "Đây là tính chất của *dạng hàm*, không phải của ước lượng, nên không ước lượng lại $\lambda_2$ nào gỡ được." Tái định tâm gỡ được. |
| **E23** | Table 5.5 | $w_X$ co giãn theo tần suất: nhánh địa chính trị có AR(1) = 0,503 so với 0,97+ của các nhánh thị trường, và dịch 20 điểm phân vị mỗi ngày | "Một phần ba biến trạng thái này dịch chuyển ở tần suất của tiêu đề báo." |
| **E24** | Assumption 9.1 | Bộ tổng hợp $f_{hard}$ mà sách *giả định tồn tại* và không bao giờ viết ra: $f_{hard} = w_C C_{alt}^{rộng} + w_T T_{frag} - w_{CT} C_{alt}^{rộng} T_{frag}$, với $C_{alt}^{rộng} = (1-w_{Au})C_{alt} + w_{Au}\,Au_{sub}$ | "Không có $C_{alt}$, Chương 9 không thể kiểm chứng được gì cả" (§17.8 hạng mục ba). §17.6.3 — **giả thuyết cứu duy nhất sống sót chính bài kiểm tra của nó** — cho thấy thay thế dự trữ bằng vàng *thuộc về* $C_{alt}$ và hiện đang nằm ngoài. |
| **E25** | §5.5.3 | Nhánh ngoại sinh phi quân sự $X_{health}$ trong E3 | "Proxy cho $X_{pand}$ không bao phủ đại dịch... 2020 — cú sốc phi tài chính rõ ràng nhất trong mẫu — chẳng được gì từ nó. Đây là bổ sung dữ liệu giá trị nhất còn lại cho tầng này." |
| **E26** | **I32** | $(1 + b_F f_{hard})$ gắn vào E8.2, cho Layer 5 một cạnh **vào** Layer 4 | Remark 10.2: "Không biến nào ngoài Layer 4 chạm tới $H_{soc}, I_{imp}, C_{loop}, V_{meme}$ hay $B_{phase}$." Sách **viết ra đúng số hạng này** rồi từ chối thêm, vì nó sẽ là tham số bất khả ước lượng thứ tám. Ở đây sự thiếu vắng **khôi phục được**, không âm thầm. |
| **E27** | **I34** | Kênh đảo chiều: $T_{frag} \to T_{frag}(1-r_{rev})$, $S_{off} \to S_{off}(1-r_{rev})$ | "Đồ thị dấu không chứa mũi tên nào hạ $S_{off}$ hay $T_{frag}$, nên mô hình không có biểu diễn nào cho **cưỡng chế chấm dứt cưỡng chế**." |
| **E28** | **I40** | Tách $D_{prec}$ theo đường cong: $w_{2y}$ đầu ngắn, $(1-w_{2y})$ đầu dài | "$D_{prec}$ là một vô hướng cho cả một đường cong... kỳ hạn hai năm giữ được tính trú ẩn mà kỳ hạn ba mươi năm đã mất." |

---

## 7. Hiệu chuẩn: trạng thái nền tái tạo Table 10.3

`WorldState()` mặc định **chính là** trạng thái nền của Table 10.3, tái tạo theo
từng số hạng chứ không phải xấp xỉ:

| Đại lượng | Sách nói | Engine |
|-----------|----------|--------|
| $\sigma_{sys}$ | 0,35 | 0,349 |
| $\Phi_{sys}$ | 0,70 | 0,700 |
| $s_{US,sys}$ | 0,70 | 0,701 |
| $f_{hard}$ | 0,34 | 0,342 |
| $H_{soc} = I_{imp}$ | 0,30 | 0,300 |
| $k_\Psi$ | 6 | 6,000 |
| $\Psi_{str}$ | — | 0,902 |
| $\kappa_{sys}$ | dải 1,2–2,0 | 1,460 |

**Hai điều phải nói ra.**

**Một.** $H_{soc} = I_{imp} = 0{,}30$ trong engine là **điểm bất động thật** của
Equation (8.8), không phải một cặp áp đặt bên cạnh nó. Table 10.3 áp đặt chúng;
Chương 8 nói chúng *là* điểm bất động. Hai điều đó chỉ tương thích với những giá
trị nhất định của $R_{div}$, $c_{L0}$, $c_{L1}$ — và cả ba đều **OPEN**. Engine
chọn bộ khiến chúng tương thích ($R_{div} = 0{,}3275$, $c_{L0} = 0{,}80$,
$c_{L1} = 1{,}18$) và **phát biểu lựa chọn đó** thay vì giấu nó. Hàm
`layers.implied_layer4` giải ngược ràng buộc cho bất kỳ cặp nào khác.

**Hai.** $\kappa_{sys} = 1{,}22$ của sách **không tái tạo chính xác được**, vì
Table 10.3 nêu **năm trong bảy** hệ số của $\kappa_{sys}$ và bỏ qua $a_V$ và
$a_A$. Engine đặt chúng nhỏ thay vì bịa, và kết quả rơi vào đúng dải mà chính
sách nêu.

---

## 8. Đối chiếu kịch bản: nơi engine khớp và nơi nó không

| Kịch bản | Engine | Sách | Lệch |
|----------|--------|------|------|
| Thanh khoản (§10.7.1) | +17,70% | +17,70% | 0,00 |
| + mở swap | +8,84% | "gỡ khoảng một nửa đỉnh" | ✓ (50,0%) |
| Trừng phạt (§10.7.2) | +2,83% | +4,75% | −1,92 |
| Trừng phạt, hai năm sau | −5,83% | −0,49% | −5,34 |
| Niềm tin (§10.7.3) | −4,30% | −4,30% | 0,00 |
| Tự sự (§10.7.4) | +10,53% | +9,70% | +0,83 |
| GFC 2008 (CS1) | +18,55% | +6,59% | **+11,96** |
| COVID 2020 (CS2) | +1,85% | +1,85% | 0,00 |
| Đợt tăng 2022 (CS5) | +27,64% | +15,45% | **+12,19** |

**Hai chỗ lệch lớn là cùng một chỗ lệch, và nó là I37.** Trên bộ tham số Table
10.3, một cú nhảy $\sigma$ lên 0,93 tự nó sinh hơn 13% từ khối trú ẩn. Đó chính
là điều §17.3 mô tả: cơ chế khủng hoảng **yếu nhất đúng ở chỗ có khủng hoảng**,
và ở đây nó biểu hiện ngược — một số hạng lồi được hiệu chuẩn cho giữa dải, bị
đánh giá ở cuối dải. Chạy lại với `--recentre` (E22) và phần vượt co lại.

**Engine không chỉnh cho khớp.** §10.7.5 báo cáo rằng chính mô phỏng của sách
**trượt** một kiểm tra tỉnh táo: đỉnh thanh khoản +17,7% lớn hơn khoảng một phần
tư so với bất cứ gì đồng đô la từng làm. Engine tái tạo cả hành vi **lẫn** phần
vượt, vì tách chúng ra nghĩa là chỉnh đi mất đúng con số mà §10.7.5 yêu cầu người
đọc giữ lại.

**Một căng thẳng nội tại được phát hiện khi chạy.** §10.7.4 nói $H_{soc}$ "nhảy
qua separatrix". Nhưng Assumption 8.4 duy trì $\eta < 4$ xuyên suốt Phần I–III,
và dưới ngưỡng đó Proposition 8.2 bảo đảm điểm bất động là **duy nhất và hút toàn
cục** — tức *không có separatrix nào để nhảy*. Engine chạy đúng theo Assumption
8.4, nên $H_{soc}$ **trôi** tới 0,77 thay vì nhảy, và $k_\Psi$ tới ~19 thay vì 28.
Muốn đúng con số của sách thì phải đặt $\eta \ge 4$, và khi đó engine cảnh báo
rằng kết quả đang đứng trên một trong ba nhánh.

---

## 9. Kết quả đầu tiên mà Layer W tạo ra

Chạy `python -m amr weights` tại trạng thái nền:

| Phương trình | Tỉ lệ trọng số |
|--------------|----------------|
| **E8 · Ψ_str** (Layer 5) | **50,6%** |
| **f_hard** (bộ tổng hợp E24, *do engine bổ sung*) | **17,5%** |
| E3 · σ_sys | 7,5% |
| E4 · Φ_sys | 7,2% |
| E6 · κ_sys | 6,6% |

**Hai phần ba độ nhạy tham số của mô hình nằm ở tầng mà Chương 17 tuyên bố là
không kiểm chứng được, và ở một bộ tổng hợp mà sách chưa từng viết ra.**

Proposition 9.3: vì $f_{hard}$ không có phép đo, cái vách không thể bị bác bỏ.
Kết hợp hai điều đó: **một nửa độ nhạy của mô hình nằm sau một tham số mà không
quan sát nào chạm tới được.** Đó không phải lý do bỏ mô hình; đó là lý do để
§17.8 hạng mục ba — *xây $C_{alt}$, và xây rộng hơn bản gốc định nghĩa* — đứng
đầu danh sách thay vì đứng thứ ba.

---

## 10. Tệp và lệnh

```
amr/registry.py     biến, trọng số, vùng khả dụng, nguồn gốc, tình trạng bằng chứng
amr/functions.py    hình chữ S duy nhất
amr/layers.py       E3–E8, E11–E14, bộ giải ngược Layer 4
amr/weightlayer.py  E17–E20: Layer W
amr/core.py         lắp ráp E9/E10, so sánh tĩnh
amr/qualitative.py  thang mũi tên, chế độ, quy kết, tình trạng bằng chứng
amr/scenarios.py    bốn cú sốc §10.7 + các tình huống Phần II
amr/sensitivity.py  khả thi, tornado, phân rã phương sai
amr/cli.py          giao diện dòng lệnh
tests/              35 kiểm thử, trong đó quan trọng nhất là tính lồng khít
```

```bash
python -m amr list                 # liệt kê kịch bản
python -m amr run sanctions        # bản đọc định tính đầy đủ
python -m amr weights              # tỉ lệ trọng số
python -m amr tornado              # vùng tuỳ biến, quét toàn dải
python -m amr mc --n 1500          # phân rã phương sai + phần tương tác
python -m amr check                # ràng buộc cấu trúc, có độ dư
python -m amr audit                # mọi kịch bản so với số liệu sách
python tests/test_engine.py        # 35 kiểm thử
```

---

*Engine này chỉ dành cho mục đích học thuật và minh hoạ, và kế thừa nguyên vẹn
mọi tuyên bố miễn trừ ở đầu cuốn sách: không có thông số nào trong đây được ước
lượng, 42 trên 55 tham số của mô hình gốc là OPEN, và không con số nào ở đây là
khuyến nghị đầu tư hay dự báo thị trường.*
