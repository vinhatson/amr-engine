"""
geometry.py — phân rã tiếp tuyến / pháp tuyến, độ căng, và vết sẹo.

MỘT THAM SỐ MỚI DUY NHẤT, và nó có nghĩa hình học rõ ràng:

    τ_{ℓm} ∈ [0,1]   phần PHÁP TUYẾN của tác động từ tấm ℓ lên tấm m

    τ = 0  →  tác động hoàn toàn TIẾP TUYẾN. Nó đổi hệ số trên tấm m, hệ số
              đổi tốc độ, tốc độ không đổi vị trí tấm. Trượt song song.
              Đây là amr, và nó là amr với mọi tầng, mọi cạnh.
    τ = 1  →  tác động hoàn toàn PHÁP TUYẾN. Nó không đổi hệ số nào cả; nó
              dịch chính tấm m. Đâm xuyên.
    0<τ<1  →  cả hai, và ĐÚNG phép phân rã a = a_∥ + a_⊥ của hình học vi phân.

ĐỘ SÂU VẾT ĐÂM KHÔNG TUỲ Ý.  Nó là

    Δξ_m = τ_{ℓm} · p · (src_ℓ − H*_ℓ)₊ · (1 + q · II_m)

trong đó II_m là ĐỘ CĂNG của tấm m, định nghĩa bằng

    II_m = 4 · Λ′(arg_m) ∈ [0,1]

và thừa số 4 không phải chuẩn hoá cho đẹp.  Λ′ ≤ ¼ là chính bất đẳng thức
Proposition 8.2 dùng để lấy biên co ηκ_A g₁ < 4, và Layer W dùng để lấy biên
max_k Σ_j |C_kj| < 4.  Cùng một con số ¼ chặn tính co cũng chặn độ căng:
tấm CĂNG NHẤT đúng ở nơi nó DỐC NHẤT, tức ở điểm uốn.  Giấy căng thì rách,
và chỗ căng nhất là chỗ Λ dốc nhất.  Đó là hình học của chính cuốn sách, đọc
theo hướng khác.

TÍNH ĐƠN ĐIỆU LÀ TẤT CẢ.  ξ_m(t) không giảm, bao giờ.  Vị trí tấm là
pos_m(t) = pos_m⁰ − ξ_m(t).  Rút dao ra thì lực hết, cái lỗ còn.  Mọi tính
bất khả hoàn nguyên, mọi phụ thuộc đường đi, mọi giao hoán tử khác không của
amr3 đều chỉ từ một dấu ≥ này mà ra — không có cơ chế thứ hai nào được thêm.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from amr.functions import logistic                                   # noqa: E402
from amr.registry import Evidence, Provenance                        # noqa: E402

from .atlas import ATLAS, Role, Sheet, cross_sheet_edges, position_weight


# --------------------------------------------------------------------------- #
# Năm hằng số, và chúng phải mang xuất xứ như 39 trọng số của amr
# --------------------------------------------------------------------------- #
#
# Cả 39 trọng số trong amr/registry.py đều mang (base, lo, hi) cộng xuất xứ và
# tình trạng bằng chứng. Năm hằng số của amr3 ban đầu là float trần, và τ = 1,00
# được nhận im lặng dù đã vượt chặn suy từ dữ liệu. Đó đúng là khuyết tật
# ISSUES #36 ghi cho CS8: một giá trị không gì bác bỏ được.
#
# CHẶN TRÊN CỦA τ, và nó suy từ dữ liệu chứ không từ sách:
#
#   VR(36) = 0,884  z = −0,27   thành phần thường trực của ln DXY TỒN TẠI
#   VR(60) = 0,842  z = −0,28   (không phân biệt được với bước ngẫu nhiên)
#   cap + oil giải thích 48,2% biến thiên 36 tháng; phần dư 51,8% và PHẲNG
#     từ k = 6 tới k = 36 — nên phần thường trực chưa ai giải thích là có thật
#   d(ln DXY)/dθ₀ = +48,31 điểm %/đơn vị        (engine, tại trạng thái nền)
#   ξ₅ cần để sinh TOÀN BỘ phần dư đó  = 0,1319 đơn vị θ₀
#   ξ₅ một cú sốc meme cực đại ở τ = 1 = 0,5040 đơn vị θ₀
#   ⇒ τ ≤ 0,262
#
# Đây là chặn TRÊN, không phải ước lượng điểm: phần dư còn chứa mọi thứ khác
# mà hai kênh không đo. τ vẫn chưa nhận dạng được điểm, nhưng nó thôi là một
# núm quay tự do — nó có trần, và trần đó bác bỏ được.

# Trần phụ thuộc DẠNG TRÍ NHỚ, và phải như thế: cùng một ngân sách thực nghiệm
# (ξ₅ = 0,1319 đơn vị θ₀ để sinh toàn bộ phần dư thường trực) mua được lượng τ
# khác nhau, vì một đơn vị τ sinh ra lượng ξ khác nhau ở hai dạng.
#
#   hysteresis  ξ₅ ở τ = 1, một cú sốc = 0,4492  →  τ ≤ 0,294
#   fatigue     ξ₅ ở τ = 1, một cú sốc = 1,0856  →  τ ≤ 0,122
#
# Trần của nhánh mỏi giả định đợt kéo dài MỘT kỳ. Đợt dài hơn hạ trần xuống
# nữa, và đó là một hệ quả của nhánh mỏi chứ không phải một khuyết điểm.
TAU_CEILING_BY_MODE: Dict[str, float] = {
    "hysteresis": 0.294,
    "fatigue":    0.122,
}
TAU_CEILING = TAU_CEILING_BY_MODE["hysteresis"]      # dạng mặc định


@dataclass(frozen=True)
class Param:
    """Một hằng số của amr3, mang đúng bộ thông tin trọng số amr phải mang."""
    key: str
    symbol: str
    base: float
    lo: float
    hi: float
    provenance: Provenance
    evidence: Evidence
    note: str = ""

    def check(self, v: float) -> Optional[str]:
        if v < self.lo - 1e-12 or v > self.hi + 1e-12:
            return (f"{self.symbol} = {v:.4g} ngoài vùng khả dụng "
                    f"[{self.lo:.4g}, {self.hi:.4g}] — {self.note}")
        return None


PARAMS: Dict[str, Param] = {
    "tau": Param(
        "tau", "τ", 0.0, 0.0, TAU_CEILING, Provenance.OPEN, Evidence.PARTIAL,
        "chặn trên suy từ phần thường trực 36 tháng chưa giải thích, và PHỤ "
        "THUỘC DẠNG TRÍ NHỚ: 0,294 ở dạng trễ, 0,122 ở dạng mỏi. Chưa nhận "
        "dạng được điểm. Nền 0,0 vì đó là amr, và là giả thuyết không."),
    "H_star": Param(
        "H_star", "H*", 0.45, 0.30, 0.70,
        Provenance.ENGINE_CONVENTION, Evidence.UNTESTED,
        "ngưỡng đâm trên H_soc. TÔI ĐẶT. H_soc không có chuỗi quan sát nào, "
        "nên ngưỡng này chưa ước lượng được — chỉ nêu bằng số để bác bỏ được."),
    "p_depth": Param(
        "p_depth", "p", 0.35, 0.00, 1.00,
        Provenance.ENGINE_CONVENTION, Evidence.UNTESTED,
        "độ sâu mỗi đơn vị vượt ngưỡng. TÔI ĐẶT."),
    "q_taut": Param(
        "q_taut", "q", 2.50, 0.00, 5.00,
        Provenance.ENGINE_CONVENTION, Evidence.UNTESTED,
        "giấy căng sâu hơn giấy chùng bao nhiêu lần. TÔI ĐẶT. Dạng của số hạng "
        "thì không: II = 4Λ′ lấy từ chính biên Λ′ ≤ ¼ của Prop. 8.2."),
    "rho_frag": Param(
        "rho_frag", "ρ", 0.50, 0.00, 1.00,
        Provenance.ENGINE_CONVENTION, Evidence.UNTESTED,
        "vết sẹo cấu trúc đẩy T_frag lên bao nhiêu. TÔI ĐẶT."),
}


# --------------------------------------------------------------------------- #
# Độ căng — dạng cơ bản thứ hai, chuẩn hoá bằng chính biên ¼ của sách
# --------------------------------------------------------------------------- #

def dlogistic(x: float) -> float:
    s = logistic(x)
    return s * (1.0 - s)


def tautness(arg: float) -> float:
    """II = 4·Λ′(arg) ∈ [0,1].  Bằng 1 đúng tại điểm uốn, arg = 0.

    Λ′(x) = Λ(1−Λ) ≤ ¼ với dấu bằng tại x = 0.  Nhân 4 đưa về [0,1] mà không
    thêm hằng số nào không có trong sách: cùng ¼ cho biên co Prop. 8.2 và
    biên ghép trọng số Layer W.
    """
    return 4.0 * dlogistic(arg)


# --------------------------------------------------------------------------- #
# Cường độ của từng tấm — một số vô hướng "tấm này đang kêu to tới đâu"
# --------------------------------------------------------------------------- #

@dataclass
class SheetState:
    """Trạng thái hình học của một tấm ở một thời điểm.

    intensity  cường độ, trong [0,1] — nguồn của mọi vết đâm tấm này gây ra
    arg        đối số logistic của tấm — quyết định ĐỘ CĂNG của nó
    scar       ξ ≥ 0, đơn điệu không giảm, trừ vào vị trí tấm
    """
    sheet: Sheet
    intensity: float = 0.0
    arg: float = 0.0
    scar: float = 0.0

    @property
    def taut(self) -> float:
        return tautness(self.arg)


# Ngưỡng đâm: dưới mức này tác động hoàn toàn tiếp tuyến, dù τ bằng bao nhiêu.
# Một con dao ấn nhẹ lên giấy thì giấy chỉ võng xuống. Mọi giá trị đều NÊU
# BẰNG SỐ để sự kiện cực đoan kế tiếp bác bỏ được — khuyết tật ISSUES #36.
H_STAR: Dict[Sheet, float] = {
    Sheet.MECHANICAL: 0.60,
    Sheet.STATE:      0.60,
    Sheet.STRUCTURAL: 0.50,
    Sheet.REFLEXIVE:  0.60,
    Sheet.PSYCHO:     PARAMS["H_star"].base,   # tầng meme — thấp nhất, có chủ ý
    Sheet.SECULAR:    0.50,
    Sheet.HAVEN:      0.99,     # hướng trực giao: không đâm, theo định nghĩa
}

P_DEPTH = PARAMS["p_depth"].base
Q_TAUT  = PARAMS["q_taut"].base


# --------------------------------------------------------------------------- #
# Ma trận hoành τ
# --------------------------------------------------------------------------- #

@dataclass
class Transversality:
    """τ trên từng cạnh LIÊN TẤM mà amr đã mã hoá. Mặc định toàn 0 = amr.

    Không cạnh nào được thêm.  Tập cạnh lấy nguyên từ `gamma` của
    amr/registry.py qua atlas.cross_sheet_edges(), nên τ là một câu hỏi đặt
    LÊN cấu trúc có sẵn, không phải một cấu trúc mới.
    """
    tau: Dict[Tuple[Sheet, Sheet], float] = field(default_factory=dict)

    @classmethod
    def zero(cls) -> "Transversality":
        return cls({(s, d): 0.0 for s, d, *_ in cross_sheet_edges()})

    def warnings(self, mode=None) -> List[str]:
        """Giá trị ngoài vùng khả dụng trả về NHÃN, không trả về lỗi.

        Đó là quy ước của amr: §core.run "capped so that a configuration
        outside the contraction bound returns a labelled answer rather than
        spinning".  Quay τ lên 1,00 vẫn chạy — nhưng kết quả mang theo một dòng
        nói rằng nó ở ngoài mức dữ liệu cho phép.
        """
        P = PARAMS["tau"]
        hi = P.hi
        if mode is not None:
            key = getattr(mode, "value", str(mode))
            hi = TAU_CEILING_BY_MODE.get(key, P.hi)
        out: List[str] = []
        for (s, d), v in sorted(self.tau.items(), key=lambda kv: kv[0][0].value):
            if v > hi + 1e-12 or v < P.lo - 1e-12:
                out.append(
                    f"Σ{s.value}→Σ{d.value}: {P.symbol} = {v:.4g} ngoài vùng khả dụng "
                    f"[{P.lo:.4g}, {hi:.4g}] — {P.note}")
        return out

    @classmethod
    def knife(cls, value: float = TAU_CEILING) -> "Transversality":
        """Chỉ Σ₄ → Σ₅ bật. Đúng con dao của luận điểm, không hơn.

        Σ₄→Σ₅ là cạnh amr để tải +0,00 (`theta_0`, gamma={'hsoc': 0.0}), kèm
        ghi chú "The loading below is the departure, and it is zero by
        default."  Bật τ_45 là bật đúng cái cửa sách đã lắp sẵn và khoá.
        """
        t = cls.zero()
        t.tau[(Sheet.PSYCHO, Sheet.SECULAR)] = float(value)
        return t

    @classmethod
    def full(cls, value: float = TAU_CEILING) -> "Transversality":
        """Mọi cạnh Σ₄ → * bật. Tầng meme đâm qua tất cả những gì nó chạm."""
        t = cls.zero()
        for (s, d) in list(t.tau):
            if s is Sheet.PSYCHO:
                t.tau[(s, d)] = float(value)
        return t

    def get(self, src: Sheet, dst: Sheet) -> float:
        return self.tau.get((src, dst), 0.0)

    @property
    def is_zero(self) -> bool:
        return all(abs(v) < 1e-15 for v in self.tau.values())

    def active(self) -> List[Tuple[Sheet, Sheet, float]]:
        return [(s, d, v) for (s, d), v in sorted(
            self.tau.items(), key=lambda kv: (kv[0][0].value, kv[0][1].value))
            if abs(v) > 1e-15]


# --------------------------------------------------------------------------- #
# Phân rã một tác động
# --------------------------------------------------------------------------- #

@dataclass
class Decomposition:
    """Một cạnh liên tấm, tách thành hai phần. Đây là a = a_∥ + a_⊥."""
    src: Sheet
    dst: Sheet
    src_var: str
    weight_key: str
    load: float           # tải trọng của amr, nguyên không đổi
    tau: float
    tangential: float     # a_∥ — vào hệ số trên tấm đích, như amr vẫn làm
    normal: float         # a_⊥ — vào VỊ TRÍ tấm đích, amr không có chỗ nhận
    excess: float         # (src − H*)₊
    taut: float           # II của tấm đích
    depth: float          # Δξ đóng góp vào vết sẹo tấm đích

    @property
    def slides(self) -> bool:
        return abs(self.normal) < 1e-15


def decompose(
    edges: Iterable[Tuple[Sheet, Sheet, str, str, float]],
    sheets: Dict[Sheet, SheetState],
    tv: Transversality,
    taut_ref: Optional[Dict[Sheet, float]] = None,
) -> List[Decomposition]:
    """Tách từng cạnh liên tấm thành phần tiếp tuyến và phần pháp tuyến.

    Phần tiếp tuyến giữ NGUYÊN tải trọng của amr khi τ = 0, nên không có chỗ
    nào amr bị sửa ngầm: tổng |a_∥| + |a_⊥| = |a| với mọi τ.

    `taut_ref` LÀ SỬA CHỮA THỨ HAI, và nó quan trọng hơn vẻ ngoài.  Độ cong
    II của tấm đích trước đây đọc từ chính tấm ĐÃ BỊ DỊCH, nên độ sâu vết dịch
    phụ thuộc vào vết dịch đã có — toán tử ăn chính đầu ra của nó.  Hậu quả đo
    được: chia cùng một đường đi thành nhiều bước hơn cho vết dịch khác đi, kể
    cả ở dạng lấy cực đại (2,1 lần trên 20 bước).

    Với `taut_ref` lấy từ một lần chạy KHÔNG có vết sẹo, độ sâu thành một phiếm
    hàm của ĐƯỜNG ĐI NGOẠI SINH và không gì khác.  Đo lại: 1,000 lần.
    """
    out: List[Decomposition] = []
    for src, dst, var, wk, load in edges:
        t = tv.get(src, dst)
        s_int = sheets[src].intensity if src in sheets else 0.0
        excess = max(0.0, s_int - H_STAR[src])
        if taut_ref is not None:
            taut = taut_ref.get(dst, 0.0)
        else:
            taut = sheets[dst].taut if dst in sheets else 0.0
        depth = t * P_DEPTH * excess * (1.0 + Q_TAUT * taut)
        out.append(Decomposition(
            src=src, dst=dst, src_var=var, weight_key=wk, load=load, tau=t,
            tangential=(1.0 - t) * load, normal=t * load,
            excess=excess, taut=taut, depth=depth,
        ))
    return out


# --------------------------------------------------------------------------- #
# Tích luỹ vết sẹo — chỗ duy nhất tính bất khả hoàn nguyên được sinh ra
# --------------------------------------------------------------------------- #

class Memory(Enum):
    """Hai dạng trí nhớ, và chúng là HAI VẬT LÝ KHÁC NHAU, không phải hai
    cách xấp xỉ cùng một thứ.

    HYSTERESIS — ξ = cực đại theo lịch sử của độ sâu.
        Chỉ CỰC TRỊ của đường đi đếm; thời lượng không vào công thức.  Đây là
        toán tử play/stop của lý thuyết trễ, và là dạng Baldwin–Krugman (1989)
        dùng cho chính tỉ giá: một đợt đủ lớn để vượt chi phí chìm thì để lại
        dấu, và tỉ giá quay về chỗ cũ cũng không xoá được dấu ấy.
        Tính chất định nghĩa: ĐỘC LẬP VỚI TỐC ĐỘ.

    FATIGUE — ξ = tích phân của độ sâu theo thời gian trên ngưỡng.
        Thời lượng THAY THẾ ĐƯỢC biên độ.  Đây là quy tắc Miner trong mỏi vật
        liệu.  Nó có dự đoán riêng, bác bỏ được: với tham số mặc định, 32 kỳ ở
        biên 0,80 gây hại gấp 3,8 lần một kỳ ở biên 0,95, và điểm hoà vốn nằm
        quanh 6 kỳ.  Dạng trễ nói phép so sánh ấy không có nội dung.

    Hai nhánh nêu dự đoán TRÁI NHAU nên phân biệt được bằng dữ liệu — nhưng
    không phải bằng một chuỗi tỉ giá đơn lẻ: 246 tháng với chân trời 36 tháng
    cho khoảng sáu đợt độc lập, và trên mẫu không chồng lấn cả hai biến đỉnh
    lẫn thời lượng đều mất ý nghĩa.  Phép thử nằm ở chiều chéo, trên bảng nhiều
    đồng tiền, đúng như cách tài liệu trễ trong thương mại vẫn được kiểm.
    """
    HYSTERESIS = "hysteresis"
    FATIGUE = "fatigue"


def accumulate(
    sheets: Dict[Sheet, SheetState],
    decs: Iterable[Decomposition],
    mode: Memory = Memory.HYSTERESIS,
    dt: float = 1.0,
) -> Dict[Sheet, float]:
    """Ghi độ sâu vào vết sẹo. ĐƠN ĐIỆU — ξ không bao giờ giảm, ở cả hai dạng.

    Không có cơ chế quên, không có hồi phục.  Khác biệt duy nhất giữa hai dạng
    là CỰC ĐẠI hay TÍCH PHÂN.

    `dt` LÀ SỬA CHỮA THỨ NHẤT.  Bản trước cộng dồn theo mỗi lần gọi step(), nên
    chia cùng một đường đi thành nhiều bước hơn cho vết sẹo to lên 6,3 lần —
    kết quả phụ thuộc cách chia thời gian chứ không chỉ phụ thuộc đường đi.
    Nhánh mỏi ĐƯỢC PHÉP phụ thuộc thời lượng; đó là nội dung của nó.  Nhưng
    thời lượng phải được KHAI BÁO qua dt, không phải suy ra từ việc người dùng
    bấm step() bao nhiêu lần.
    """
    added: Dict[Sheet, float] = {}
    for d in decs:
        if d.depth <= 0.0:
            continue
        st = sheets.get(d.dst)
        if st is None:
            continue
        if position_weight(d.dst) is None:
            continue        # Σ₄ không có vị trí để bị dịch — Remark 10.2
        if mode is Memory.HYSTERESIS:
            if d.depth > st.scar:
                added[d.dst] = added.get(d.dst, 0.0) + (d.depth - st.scar)
                st.scar = d.depth
        else:
            inc = dt * d.depth
            st.scar += inc
            added[d.dst] = added.get(d.dst, 0.0) + inc
    return added


def position_overrides(
    sheets: Dict[Sheet, SheetState],
    floor: float = 0.05,
) -> Dict[str, float]:
    """Vết sẹo → overrides trọng số cho amr.run.

    Đây là toàn bộ giao diện giữa amr3 và amr, và nó là lý do amr3 lồng khít:
    ξ ≡ 0 cho dict RỖNG, dict rỗng cho lại amr đúng từng chữ số máy.
    """
    from amr.registry import WEIGHTS
    ov: Dict[str, float] = {}
    for sheet, st in sheets.items():
        if st.scar <= 0.0:
            continue
        key = position_weight(sheet)
        if key is None:
            continue
        w = WEIGHTS[key]
        ov[key] = max(max(w.lo, floor), w.base - st.scar)
    return ov
