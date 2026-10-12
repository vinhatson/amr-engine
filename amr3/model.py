"""
model.py — engine amr3. Cùng 78 biến, phân phối lại theo hình học.

amr3 KHÔNG viết lại E9. Nó gọi `amr.run` nguyên vẹn, và chỉ thêm đúng một
thứ vào giữa: vết sẹo ξ, đi vào `overrides` của amr trên các trọng số VỊ TRÍ.

    ξ ≡ 0  →  overrides rỗng  →  amr.run không biết amr3 tồn tại
                              →  ln DXY TRÙNG KHÍT tới chữ số máy

Đó là lý do amr3 nhập amr, trong khi amr2 thì cố tình không. amr2 là một mô
hình KHÁC, nên phải đứng riêng để còn so được. amr3 là cùng mô hình ĐỌC THEO
HỆ TOẠ ĐỘ KHÁC, nên nó phải lồng khít, và cách chứng minh lồng khít là chạy
chính amr ở trong.

CƯỜNG ĐỘ VÀ ĐỘ CĂNG CỦA TỪNG TẤM, lấy từ Result của amr:

  tấm   cường độ               độ căng II = 4·v(1−v)
  Σ₀    f_hard                 v = f_hard
  Σ₁    σ_sys                  v = σ_sys
  Σ₂    1 − Φ_sys              v = Φ_sys
  Σ₃    κ_sys / κ_max          v = κ_sys/κ_max
  Σ₄    H_soc                  v = H_soc
  Σ₅    1 − Ψ_str              v = (1 − Ψ_str)/L_max   ← CHÍNH XÁC, không xấp xỉ

Dòng Σ₅ đáng nói riêng. Ψ_str = 1 − L_max·Λ(k_Ψ(f_hard − θ_0)), nên
(1 − Ψ_str)/L_max = Λ(arg) đúng bằng định nghĩa, và khi đó
4v(1−v) = 4Λ(1−Λ) = 4Λ′(arg).  Quy tắc độ căng duy nhất của amr3 TRÙNG với
đạo hàm logistic thật trên tấm thế kỷ — tấm mà toàn bộ luận điểm nói về.
Trên Σ₁ thì nó là xấp xỉ, vì σ_sys là hợp tuyến tính chứ không phải logistic,
và điều đó được nói ra chứ không bỏ qua.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from amr import Options, WorldState, run                              # noqa: E402
from amr.registry import WEIGHTS                                      # noqa: E402

from .atlas import ATLAS, Role, Sheet, cross_sheet_edges, position_weight
from .geometry import (
    H_STAR, P_DEPTH, PARAMS, Q_TAUT, TAU_CEILING, TAU_CEILING_BY_MODE,
    Decomposition, Memory, SheetState, Transversality, accumulate, decompose,
    position_overrides, tautness,
)
from .operators import Commutator, Holonomy, Move, Residual

# Hệ số phân mảnh: vết sẹo cấu trúc ĐẨY T_frag lên.
#
# Đây là chỗ luận điểm của tác giả có hệ quả cứng nhất. Trong amr, T_frag là
# một biến ẩn Tầng 2 với giá trị nền 0,420 mà người dùng TỰ ĐIỀN VÀO. Trong
# amr3 nó có thêm một thành phần SINH RA từ vết đâm:
#
#     T_frag(t) = T_frag⁰ + ρ · ξ_2(t)
#
# Tức phân mảnh chính trị thôi là đầu vào và thành ĐẦU RA của việc tầng meme
# đâm qua tầng cấu trúc. Đó đúng là câu "lớp meme làm hỏng lớp cấu trúc lâu
# dài, làm phân mảnh chính trị nếu đủ lớn", viết thành một dòng kiểm được.
RHO_FRAG = PARAMS["rho_frag"].base


@dataclass
class Options3:
    """Mọi sai khác so với amr nằm ở đây, và mọi cái mặc định TẮT."""
    tv: Transversality = field(default_factory=Transversality.zero)
    fragmentation_feedback: bool = False     # T_frag ← ξ_2
    amr: Options = field(default_factory=Options)

    # Dạng trí nhớ. Mặc định HYSTERESIS vì ba lý do, theo thứ tự quan trọng:
    # nó là nội dung của chính luận điểm (một vết, không phải mỏi tích luỹ);
    # nó là toán tử chuẩn của tài liệu trễ, với ba tính chất kiểm được; và nó
    # độc lập với tốc độ, nên kết quả không phụ thuộc cách chia nhỏ đường đi.
    # FATIGUE giữ lại vì nó nêu dự đoán khác và bác bỏ được — không phải vì
    # nó là một xấp xỉ của dạng kia.
    memory: Memory = Memory.HYSTERESIS


@dataclass
class Step:
    index: int
    move: str
    ln_DXY: float
    psi_str: float
    kappa: float
    phi: float
    H_soc: float
    f_hard: float
    sheets: Dict[Sheet, SheetState]
    overrides: Dict[str, float]
    decs: List[Decomposition]
    T_frag: float
    warnings: List[str] = field(default_factory=list)

    def scar(self, s: Sheet) -> float:
        st = self.sheets.get(s)
        return st.scar if st else 0.0


@dataclass
class Trajectory:
    steps: List[Step]

    @property
    def final(self) -> Step:
        return self.steps[-1]

    @property
    def ln_DXY(self) -> float:
        return self.steps[-1].ln_DXY

    def scars(self) -> Dict[Sheet, float]:
        return {s: st.scar for s, st in self.steps[-1].sheets.items() if st.scar > 0}


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #

class Manifold:
    """Sáu tấm có định hướng, có vết sẹo, mang trong nó chính engine amr."""

    def __init__(self, state: Optional[WorldState] = None,
                 opt: Optional[Options3] = None):
        self.state = (state or WorldState()).copy()
        self.opt = opt or Options3()
        self.sheets: Dict[Sheet, SheetState] = {
            s: SheetState(s) for s in Sheet
        }
        self._T_frag0 = self.state.latents["T_frag"]
        self._ref_key = None
        self._ref_taut: Dict[Sheet, float] = {}
        self.steps: List[Step] = []

    # -- đọc hình học ra khỏi Result của amr ------------------------------- #

    def _read(self, r) -> None:
        L_max = r.weights.values.get("L_max", WEIGHTS["L_max"].base)
        kmax = max(1e-9, r.kappa.kappa_max)
        v = {
            Sheet.MECHANICAL: _c01(r.f_hard),
            Sheet.STATE:      _c01(r.sigma.sigma),
            Sheet.STRUCTURAL: _c01(r.phi),
            Sheet.REFLEXIVE:  _c01(r.kappa.kappa / kmax),
            Sheet.PSYCHO:     _c01(r.psycho.H_soc),
            Sheet.SECULAR:    _c01((1.0 - r.psi_str) / max(1e-9, L_max)),
            Sheet.HAVEN:      _c01(r.sigma.sigma),
        }
        intens = {
            Sheet.MECHANICAL: v[Sheet.MECHANICAL],
            Sheet.STATE:      v[Sheet.STATE],
            Sheet.STRUCTURAL: 1.0 - v[Sheet.STRUCTURAL],   # MẤT lòng tin
            Sheet.REFLEXIVE:  v[Sheet.REFLEXIVE],
            Sheet.PSYCHO:     v[Sheet.PSYCHO],
            Sheet.SECULAR:    v[Sheet.SECULAR],            # = Λ(arg), độ xói mòn
            Sheet.HAVEN:      v[Sheet.HAVEN],
        }
        for s, st in self.sheets.items():
            st.intensity = intens[s]
            # II = 4·v(1−v) = 4·Λ′ khi v là một logistic; trên Σ₅ là đúng hệt.
            st.arg = _logit(v[s])

    # -- độ cong tham chiếu, ở cấu hình chưa có vết sẹo -------------------- #

    def _reference_taut(self, r, ov: Dict[str, float]) -> Dict[Sheet, float]:
        if not ov:
            return {s: st.taut for s, st in self.sheets.items()}
        key = (tuple(sorted(self.state.latents.items())),
               tuple(sorted(self.state.channels.items())))
        if self._ref_key == key:
            return self._ref_taut
        saved = {s: (st.intensity, st.arg, st.scar) for s, st in self.sheets.items()}
        r0 = run(self.state, None, self.opt.amr)
        self._read(r0)
        out = {s: st.taut for s, st in self.sheets.items()}
        for s, (i, a, sc) in saved.items():
            self.sheets[s].intensity, self.sheets[s].arg, self.sheets[s].scar = i, a, sc
        self._ref_key, self._ref_taut = key, out
        return out

    # -- một bước --------------------------------------------------------- #

    def step(self, move: Optional[Move] = None) -> Step:
        if move is not None:
            self.state = move.apply(self.state)

        # Phản hồi CỘNG LÊN giá trị ngoại sinh hiện hành, không ghi đè nó.
        # Nếu một toán tử vừa đặt T_frag, đó là giá trị ngoại sinh mới — vết sẹo
        # cộng lên trên nó. Viết sai chỗ này thì một cú sốc cứng đặt T_frag = 0,70
        # bị kéo tụt về T_frag⁰ = 0,420 + ρξ₂, và phản hồi lại làm GIẢM phân mảnh.
        if move is not None and any(k == "T_frag" for k, _ in move.latents):
            self._T_frag0 = self.state.latents["T_frag"]
        if self.opt.fragmentation_feedback:
            sc2 = self.sheets[Sheet.STRUCTURAL].scar
            self.state.latents["T_frag"] = min(1.0, self._T_frag0 + RHO_FRAG * sc2)

        ov = position_overrides(self.sheets)
        r = run(self.state, ov or None, self.opt.amr)
        self._read(r)

        # Độ cong THAM CHIẾU: chạy lại cùng trạng thái ngoại sinh nhưng KHÔNG
        # có vết sẹo, để độ sâu vết dịch là phiếm hàm của đường đi ngoại sinh
        # chứ không của vết sẹo đã có. Không có bước này thì toán tử ăn chính
        # đầu ra của nó, và kết quả phụ thuộc cách chia thời gian.
        # Kết quả được nhớ lại: trạng thái ngoại sinh giữ nguyên thì không
        # chạy thêm lần nào.
        taut_ref = self._reference_taut(r, ov)

        decs = decompose(cross_sheet_edges(), self.sheets, self.opt.tv, taut_ref)
        accumulate(self.sheets, decs, self.opt.memory,
                   move.dt if move is not None else 1.0)

        st = Step(
            index=len(self.steps), move=(move.name if move else "nền"),
            ln_DXY=r.ln_DXY, psi_str=r.psi_str, kappa=r.kappa.kappa, phi=r.phi,
            H_soc=r.psycho.H_soc, f_hard=r.f_hard,
            sheets={s: SheetState(s, x.intensity, x.arg, x.scar)
                    for s, x in self.sheets.items()},
            overrides=dict(ov), decs=decs,
            T_frag=self.state.latents["T_frag"],
            warnings=list(self.opt.tv.warnings(self.opt.memory)) + list(r.warnings),
        )
        self.steps.append(st)
        return st

    def walk(self, moves: Sequence[Optional[Move]]) -> Trajectory:
        for m in moves:
            self.step(m)
        return Trajectory(self.steps)


def _c01(x: float) -> float:
    return min(1.0 - 1e-12, max(1e-12, float(x)))


def _logit(v: float) -> float:
    v = _c01(v)
    return math.log(v / (1.0 - v))


# --------------------------------------------------------------------------- #
# Ba phép đo
# --------------------------------------------------------------------------- #

def trace(moves: Sequence[Move], state: Optional[WorldState] = None,
          opt: Optional[Options3] = None, settle: bool = True) -> Trajectory:
    """Đi hết đường, rồi LẮNG một bước.

    Bước lắng không phải trang trí. Vết sẹo của một bước được cộng SAU khi
    bước đó đọc số, nên nếu dừng ngay thì vết đâm cuối cùng được ghi mà không
    phép đọc nào thấy nó — và khi đó giao hoán tử đo lẫn cả thời điểm đọc chứ
    không chỉ đo thứ tự. Một bước lắng, không toán tử nào, đưa mọi đường về
    cùng một quy ước quan sát: cái lỗ đã có, và phép đo kế tiếp nhìn thấy nó.
    """
    m = Manifold(state, opt)
    seq = [None, *moves] + ([None] if settle else [])
    return m.walk(seq)


def commutator(a: Move, b: Move, state: Optional[WorldState] = None,
               opt: Optional[Options3] = None) -> Commutator:
    """‖[L_a, L_b]‖. Cùng hai sự kiện, đảo thứ tự, CÙNG trạng thái cuối.

    Trạng thái cuối giống nhau là điều kiện bắt buộc của phép thử: nếu khác
    thì chênh lệch chỉ nói hai trạng thái khác nhau, chẳng nói gì về thứ tự.
    """
    ab = trace([a, b], state, opt)
    ba = trace([b, a], state, opt)
    return Commutator(a.name, b.name, ab.ln_DXY, ba.ln_DXY,
                      ab.scars(), ba.scars())


def holonomy(loop: Sequence[Move], state: Optional[WorldState] = None,
             opt: Optional[Options3] = None) -> Holonomy:
    """H(γ) trên một vòng KÍN: bước cuối phải đưa trạng thái về đúng đầu.

    Hàm tự đóng vòng: nó chạy nền, ghi trạng thái, đi hết vòng, rồi gắn thêm
    một toán tử gỡ đưa MỌI biến đã bị chạm về giá trị nền. Nếu còn chênh lệch
    thì chênh lệch đó không nằm trong trạng thái — nó nằm trong vết sẹo.
    """
    m = Manifold(state, opt)
    base = m.step(None)
    base_state = m.state.copy()

    touched_ch: Dict[str, float] = {}
    touched_lat: Dict[str, float] = {}
    touched_sig: Dict[str, float] = {}
    for mv in loop:
        for k, _ in mv.channels:
            touched_ch.setdefault(k, base_state.channels[k])
        for k, _ in mv.latents:
            touched_lat.setdefault(k, base_state.latents[k])
        for k, _ in mv.sigma_legs:
            touched_sig.setdefault(k, getattr(base_state.sigma_inputs, k))

    close = Move("đóng vòng", loop[-1].sheet,
                 tuple(touched_ch.items()), tuple(touched_lat.items()),
                 tuple(touched_sig.items()))
    tj = m.walk([*loop, close, None])
    return Holonomy([mv.name for mv in loop] + ["đóng vòng"],
                    base.ln_DXY, tj.ln_DXY, tj.scars())


def residual(move: Move, state: Optional[WorldState] = None,
             opt: Optional[Options3] = None) -> Residual:
    """Sốc rồi gỡ sốc hoàn toàn. §10.1.3 nói con số này bằng 0."""
    m = Manifold(state, opt)
    before = m.step(None)
    inv = move.inverse_of(m.state)
    shocked = m.step(move)
    m.step(inv)
    after = m.step(None)          # lắng: cái lỗ đã có, phép đo kế tiếp thấy nó
    return Residual(move.name, before.ln_DXY, shocked.ln_DXY, after.ln_DXY,
                    Trajectory(m.steps).scars())
