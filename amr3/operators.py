"""
operators.py — tấm thành TOÁN TỬ, và ba đại lượng bằng 0 trong amr theo định nghĩa.

Luận điểm "đâm xuyên chứ không trượt song song" có đúng một đối ứng đại số, và
đối ứng đó KHÔNG phải số chiều:

    trượt song song   ⟺   các toán tử tầng GIAO HOÁN
    đâm xuyên         ⟺   các toán tử tầng KHÔNG giao hoán

Một mô hình hai tầng có vết sẹo thì đã là đâm xuyên.  Một mô hình mười tầng
không có vết sẹo thì vẫn là trượt.  Đếm chiều là bất biến sai; giao hoán tử
là bất biến đúng.  Và giao hoán tử là ĐẠI SỐ — nên "hình học chứ không phải
đại số" là phân đôi giả, trong khi phần nội dung của luận điểm thì đúng
nguyên vẹn.

BA ĐẠI LƯỢNG, cả ba đo được, cả ba bằng 0 trong amr không phải do hiệu chỉnh
mà do lớp hàm:

  1. GIAO HOÁN TỬ   ‖[L_ℓ, L_m]‖ = |ln DXY(ℓ rồi m) − ln DXY(m rồi ℓ)|
     Hai đường, cùng sự kiện, đảo thứ tự, cùng trạng thái cuối.

  2. HOLONOMY       H(γ) = |ln DXY(cuối) − ln DXY(đầu)| trên một vòng KÍN
     Đi một vòng rồi về đúng điểm xuất phát.  Trượt thì về đúng chỗ cũ.
     Đâm thì mang theo cái lỗ.  Đây là tên hình học của chính "cái lỗ còn lại",
     và nó là bất biến chuẩn của một liên thông có độ xoắn.

  3. DƯ ÂM          R = ln DXY(trước) − ln DXY(sau khi gỡ sốc hoàn toàn)
     §10.1.3: "E8 hoàn nguyên hoàn toàn theo f_hard."  Nên R ≡ 0 trong amr,
     và §9.5 ghi nhận đúng hệ quả: mô hình không biểu diễn được đà phục hồi
     của đồng bảng Anh thập niên 1930 nếu không tự tay hạ f_hard.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .atlas import Sheet


# --------------------------------------------------------------------------- #
# Toán tử: một tác động lên thế giới, có tên và nằm trên một tấm
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Move:
    """Một tác động. `sheet` là tấm nó XUẤT PHÁT từ, không phải tấm nó tới.

    `dt` là THỜI LƯỢNG tác động này giữ nguyên, tính bằng kỳ. Nó chỉ có nghĩa
    ở dạng trí nhớ FATIGUE, nơi thiệt hại tích phân theo thời gian trên ngưỡng.
    Khai báo nó ở đây thay vì suy ra từ số lần gọi step() là cách giữ kết quả
    độc lập với cách người dùng chia nhỏ đường đi: một bước dt = 4 cho đúng
    cùng vết sẹo như bốn bước dt = 1.
    """
    name: str
    sheet: Sheet
    channels: Tuple[Tuple[str, float], ...] = ()
    latents: Tuple[Tuple[str, float], ...] = ()
    sigma_legs: Tuple[Tuple[str, float], ...] = ()
    dt: float = 1.0

    def apply(self, state):
        st = state.copy()
        for k, v in self.channels:
            st.channels[k] = v
        for k, v in self.latents:
            st.latents[k] = v
        for k, v in self.sigma_legs:
            setattr(st.sigma_inputs, k, v)
        return st

    def inverse_of(self, state) -> "Move":
        """Toán tử gỡ: đưa đúng những biến này về giá trị chúng đang có.

        Dùng để kiểm hoàn nguyên. Nó gỡ TRẠNG THÁI, và chỉ trạng thái — vết
        sẹo không nằm trong trạng thái nên không gỡ được, và đó là cả vấn đề.
        """
        return Move(
            name=f"gỡ {self.name}", sheet=self.sheet,
            channels=tuple((k, state.channels[k]) for k, _ in self.channels),
            latents=tuple((k, state.latents[k]) for k, _ in self.latents),
            sigma_legs=tuple((k, getattr(state.sigma_inputs, k))
                             for k, _ in self.sigma_legs),
            dt=self.dt,
        )


# --------------------------------------------------------------------------- #
# Ba đại lượng
# --------------------------------------------------------------------------- #

@dataclass
class Commutator:
    a: str
    b: str
    ln_ab: float
    ln_ba: float
    scar_ab: Dict[Sheet, float] = field(default_factory=dict)
    scar_ba: Dict[Sheet, float] = field(default_factory=dict)

    @property
    def norm(self) -> float:
        return abs(self.ln_ab - self.ln_ba)

    @property
    def commutes(self) -> bool:
        return self.norm < 1e-12

    def line(self) -> str:
        tag = "GIAO HOÁN" if self.commutes else "KHÔNG giao hoán"
        return (f"[{self.a}, {self.b}]   {self.a}∘{self.b} = {self.ln_ab:.10f}   "
                f"{self.b}∘{self.a} = {self.ln_ba:.10f}   "
                f"‖·‖ = {self.norm:.3e}   {tag}")


@dataclass
class Holonomy:
    loop: List[str]
    ln_start: float
    ln_end: float
    scar: Dict[Sheet, float] = field(default_factory=dict)

    @property
    def value(self) -> float:
        return self.ln_end - self.ln_start

    @property
    def trivial(self) -> bool:
        return abs(self.value) < 1e-12

    def line(self) -> str:
        tag = "TẦM THƯỜNG — về đúng chỗ cũ" if self.trivial else "KHÁC KHÔNG — mang theo cái lỗ"
        return (f"vòng {' → '.join(self.loop)}\n"
                f"  đầu {self.ln_start:.10f}   cuối {self.ln_end:.10f}   "
                f"H(γ) = {self.value:+.3e}   {tag}")


@dataclass
class Residual:
    move: str
    ln_before: float
    ln_shocked: float
    ln_after: float
    scar: Dict[Sheet, float] = field(default_factory=dict)

    @property
    def value(self) -> float:
        return self.ln_before - self.ln_after

    @property
    def reversible(self) -> bool:
        return abs(self.value) < 1e-12

    def line(self) -> str:
        tag = "HOÀN NGUYÊN TOÀN PHẦN" if self.reversible else "BẤT KHẢ HOÀN NGUYÊN"
        return (f"{self.move}: trước {self.ln_before:.8f} → sốc {self.ln_shocked:.8f} "
                f"→ gỡ {self.ln_after:.8f}   dư âm {self.value:+.6f}   {tag}")
