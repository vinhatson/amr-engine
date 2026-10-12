"""
amr2.model — mô hình sau chỉnh.

BỐN THAY ĐỔI SO VỚI amr/, và mỗi cái do một kết quả cụ thể của phiên đối chiếu
2026 đòi hỏi. Không cái nào là sở thích.

1. BỎ SỐ MŨ κ.  amr/ nâng rổ cơ học lên luỹ thừa κ_sys, một tham số mà
   Proposition 11.1 nói là không nhận dạng được. Đặt một tham số không nhận dạng
   ở vị trí số mũ biến bất định tham số thành bất định NHÂN ở đầu ra. Bỏ nó hạ
   RMSE 2026 từ 18,64% xuống 4,31%. Ở đây mô hình cộng tính trong log.

2. HỆ SỐ ĐƯỢC ƯỚC LƯỢNG, KHÔNG PHẢI QUY ƯỚC.  §11.5.1 nói rõ hệ số hồi quy là
   TÍCH κ·α, tức κ đã bị hấp thụ. Nên dạng cộng tính với hệ số ước lượng là dạng
   đúng, không phải một phép xấp xỉ.

3. DẤU DO DỮ LIỆU ĐẶT, KHÔNG DO QUY ƯỚC TẦNG 0.  Quy ước của sách — kênh cầu
   nâng đô la — SAI trên dầu, với t chưa bao giờ yếu hơn −8 ở bất kỳ mốc cắt nào
   từ 2012 tới nay. Mô hình này không áp dấu lên bất cứ hệ số nào.

4. TẦNG 1 HẠ XUỐNG VAI TRÒ MÔ TẢ.  σ_sys hỏng 2/2 mũi tên trong bảng điểm 2026,
   mang 9,3 trên 24 điểm sai số, và tắt nó đi thì ĐƯỢC THÊM một dấu đúng. Ở đây
   trạng thái vẫn được tính, nhưng nó KHÔNG phải một hồi quy tố. Nó chỉ dán nhãn
   chế độ, nới khoảng dự báo, và kích hoạt quyền từ chối gọi.

CÁI ĐƯỢC GIỮ LẠI TỪ amr/:
  · Đồ thị dấu Tầng 2, giữ 4/4 trong bảng điểm 2026, làm một lớp phủ ĐỊNH TÍNH
    chạy song song chứ không vào số học.
  · Các định lý Chương 8 — chúng là toán, dữ liệu không bác được — nhưng được
    dán nhãn KIẾN TRÚC, không phải mệnh đề kiểm chứng được.

VÀ MỘT THỨ amr/ KHÔNG CÓ: mô hình này tự khai chế độ hỏng của chính nó.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .estimate import Fit, ols_hac
from .panel import BYMONTH, PANEL, Row, window


# --------------------------------------------------------------------------- #
# Chế độ hỏng đã biết
# --------------------------------------------------------------------------- #
#
# §17.3 của sách nói cơ chế khủng hoảng yếu nhất đúng ở nơi có khủng hoảng. Dữ
# liệu 2026 nói mạnh hơn: nó ĐẢO DẤU ở đó. Kênh dầu âm và có ý nghĩa ở mọi mốc
# cắt từ 2012, mạnh dần theo độ lớn cú sốc — rồi lật ngược ở cú sốc dầu lớn nhất
# trong mẫu.
#
# ISSUES #36 ghi cho CS8 khuyết tật "không ngưỡng nào được nêu, nên không sự cố
# nào bác bỏ được kịch bản". Ngưỡng dưới đây được NÊU, nên mô hình này bác được.

OIL_SHOCK_THRESHOLD = 25.0     # |100·Δln Brent| mỗi tháng

# Vì sao 25 chứ không phải 30. Trên MẪU HUẤN LUYỆN (2007-05 → 2025-10):
#     ngưỡng 30%  →  n = 3, đô la tăng 3/3   — sạch, nhưng ba quan sát là quá ít
#                                               cho một tiên nghiệm
#     ngưỡng 25%  →  n = 5, đô la tăng 4/5, trung bình +2,54%
#     ngưỡng 20%  →  n = 8, đô la tăng 6/8, và bắt đầu lẫn các tháng khác loại
# Chọn 25. Ngưỡng và tiên nghiệm đều dựng CHỈ từ mẫu huấn luyện, nên 2026-03 là
# một phép thử thật của chúng chứ không phải nguồn của chúng.

OIL_SHOCK_EVIDENCE = (
    "Trong MỌI tháng có |Δln Brent| cực đoan của cả mẫu — 2008-10, 2008-11, "
    "2020-03 và 2026-03 — đô la TĂNG, bất kể dầu lên hay xuống. Ba tháng đầu là "
    "dầu SỤP (−31,7%, −31,1%, −49,5%) nên quan hệ tuyến tính âm có vẻ đúng ở đó; "
    "2026-03 là tháng dầu VỌT cực đoan đầu tiên trong mẫu, và quan hệ tuyến tính "
    "dự −3,5% trong khi đô la +1,7%. Đọc đúng không phải 'kênh dầu đảo dấu một "
    "lần' mà là: Ở CỰC ĐOAN, KÊNH DẦU NGỪNG LÀ MỘT KÊNH. Dấu của dầu thôi quan "
    "trọng, và đô la lên vì thứ khác tiếp quản. Đó chính là cơ chế chuyển giao mà "
    "sách đặt ra — nhưng công tắc nằm trên ĐỘ LỚN CÚ SỐC HÀNG HOÁ, không nằm trên "
    "σ_sys. Tiên nghiệm dưới đây dựng trên năm quan sát trước 2026 và không nhiều "
    "hơn thế."
)


class Regime:
    CALM = "BÌNH LẶNG"
    NORMAL = "BÌNH THƯỜNG"
    STRESSED = "CĂNG THẲNG"
    OIL_SHOCK = "CỰC ĐOAN HÀNG HOÁ — LÕI TUYẾN TÍNH KHÔNG ÁP DỤNG"


# --------------------------------------------------------------------------- #
# Lớp phủ định tính Tầng 2
# --------------------------------------------------------------------------- #

LAYER2_ARROWS = {
    "M_trust": ("M_trust ↑ ⇒ Φ_sys ↑ ⇒ DXY ↑", +1, "§6.6 + Ch.18 — giữ trong 2026"),
    "R_US":    ("R_US ↓ ⇒ Φ_sys ↑ ⇒ DXY ↑", -1, "§6.3 — giữ trong 2026"),
    "T_frag":  ("T_frag ↓ ⇒ Φ_sys ↑, s_US ↑ ⇒ DXY ↑", -1, "§6.5 — giữ trong 2026"),
    "foreign": ("Cú sốc nguồn gốc NGOÀI Mỹ ⇒ Φ_sys không co ⇒ trú ẩn chạy",
                +1, "Prop. 16.1 — giữ trong 2026, khủng hoảng trái phiếu Pháp"),
}


@dataclass
class Forecast:
    month: str
    point: float                      # 100·Δln DXY dự báo
    lo: float
    hi: float
    regime: str
    abstain: bool
    abstain_reason: str
    contributions: Dict[str, float]
    warnings: List[str]
    layer2: List[Tuple[str, str]] = field(default_factory=list)
    actual: Optional[float] = None
    source: str = "lõi tuyến tính"      # hoặc "tiên nghiệm chế độ (n=5)"

    @property
    def width(self) -> float:
        return self.hi - self.lo

    @property
    def hit(self) -> Optional[bool]:
        if self.actual is None:
            return None
        return self.lo <= self.actual <= self.hi

    def line(self) -> str:
        a = f"{self.actual:+.2f}" if self.actual is not None else "  —  "
        mark = "" if self.actual is None else ("  ✓" if self.hit else "  ✗")
        flag = f"  ⚑ {self.source}" if self.abstain else ""
        return (f"{self.month}  {self.point:+6.2f}  "
                f"[{self.lo:+6.2f},{self.hi:+6.2f}]  thực tế {a}{mark}{flag}")


# --------------------------------------------------------------------------- #

@dataclass
class CorrectedModel:
    """Lõi cơ học cộng tính, ước lượng, với trạng thái làm MÔ TẢ."""

    terms: Sequence[str] = ("cap", "oil", "pol")
    const: bool = False
    train_end: str = "2025-10"
    train_start: str = "2007-05"
    z: float = 1.645                       # khoảng 90%
    fit: Optional[Fit] = None
    _desc: Dict[str, float] = field(default_factory=dict)
    zone_n: int = 0
    zone_mu: float = 0.0
    zone_sd: float = float("nan")
    zone_up: int = 0

    # ---- huấn luyện ------------------------------------------------------- #
    def train(self) -> "CorrectedModel":
        rows = window(self.train_start, self.train_end)
        self.fit = ols_hac(rows, self.terms, const=self.const)
        self._build_descriptor(rows)
        return self

    def prune(self, t_min: float = 2.0) -> "CorrectedModel":
        """Giữ lại chỉ các số hạng có ý nghĩa, rồi ước lượng lại.

        Quy tắc này KHÔNG nhìn vào dữ liệu ngoài mẫu. Nó chạy trên mẫu huấn luyện
        và chỉ trên mẫu huấn luyện, nên nó không phải là chọn lọc sau khi biết
        kết quả.
        """
        assert self.fit is not None, "gọi train() trước"
        keep = [k for k in self.fit.significant(t_min) if k != "const"]
        if not keep:
            return self
        self.terms = tuple(keep)
        return self.train()

    # ---- bộ mô tả trạng thái (Tầng 1, đã hạ cấp) -------------------------- #
    def _build_descriptor(self, rows: Sequence[Row]) -> None:
        """σ mô tả: KHÔNG phải hồi quy tố.

        Dựng từ chính dữ liệu đã có — biến động thực hiện của đô la, độ lớn cú
        sốc dầu, độ lớn cú sốc lãi suất — chứ không từ VIX hay STLFSI, nên nó
        không cần thêm chuỗi nào và không thể nhập lậu vào vế phải.
        """
        ys = [r.y for r in rows]
        inzone = [r.y for r in rows if abs(r.oil) >= OIL_SHOCK_THRESHOLD]
        n = len(inzone)
        mu = sum(inzone) / n if n else 0.0
        sd = (math.sqrt(sum((v - mu) ** 2 for v in inzone) / (n - 1))
              if n > 1 else float("nan"))
        self._desc = {
            "vol_sample": sorted(abs(v) for v in ys),
            "oil_sample": sorted(abs(r.oil) for r in rows),
            "cap_sample": sorted(abs(r.cap) for r in rows),
        }
        self.zone_n = n
        self.zone_mu = mu
        self.zone_sd = sd
        self.zone_up = sum(1 for v in inzone if v > 0)

    @staticmethod
    def _rank(x: float, sample: Sequence[float]) -> float:
        if not sample:
            return 0.5
        lo = sum(1 for s in sample if s < x)
        return lo / len(sample)

    def describe(self, r: Row) -> Tuple[str, float]:
        if not self._desc:
            return Regime.NORMAL, 0.5
        p_oil = self._rank(abs(r.oil), self._desc["oil_sample"])
        p_cap = self._rank(abs(r.cap), self._desc["cap_sample"])
        s = 0.5 * p_oil + 0.5 * p_cap
        if abs(r.oil) >= OIL_SHOCK_THRESHOLD:
            return Regime.OIL_SHOCK, s
        if s >= 0.85:
            return Regime.STRESSED, s
        if s <= 0.30:
            return Regime.CALM, s
        return Regime.NORMAL, s

    # ---- dự báo ------------------------------------------------------------ #
    def forecast(self, month: str,
                 layer2: Optional[Dict[str, int]] = None) -> Forecast:
        assert self.fit is not None, "gọi train() trước"
        r = BYMONTH[month]
        x = {k: getattr(r, k) for k in self.fit.terms if k != "const"}
        if self.const:
            x["const"] = 1.0
        point = self.fit.predict(x)
        contrib = {k: self.fit.beta[k] * x.get(k, 0.0) for k in self.fit.terms}

        regime, s = self.describe(r)
        half = self.z * self.fit.sigma
        warn: List[str] = []
        abstain, why = False, ""

        source = "lõi tuyến tính"
        if regime == Regime.OIL_SHOCK:
            # Lõi tuyến tính KHÔNG áp dụng ở đây. Thay bằng tiên nghiệm chế độ,
            # dựng chỉ từ mẫu huấn luyện, và nói rõ nó chỉ có bấy nhiêu quan sát.
            point = self.zone_mu
            contrib = {"tiên nghiệm chế độ": self.zone_mu}
            half = self.z * (self.zone_sd if self.zone_sd == self.zone_sd
                             else self.fit.sigma * 3)
            source = f"tiên nghiệm chế độ (n={self.zone_n})"
            abstain, why = True, (
                f"|Δln Brent| = {abs(r.oil):.1f}% ≥ ngưỡng {OIL_SHOCK_THRESHOLD:.0f}%. "
                f"Lõi tuyến tính bị GỠ BỎ; thay bằng tiên nghiệm chế độ "
                f"{self.zone_mu:+.2f}% dựng trên {self.zone_n} quan sát trước 2026 "
                f"({self.zone_up}/{self.zone_n} tháng đô la tăng).")
            warn.append(OIL_SHOCK_EVIDENCE)
        elif regime == Regime.STRESSED:
            half *= 1.5
            warn.append(f"Độ lớn cú sốc ở phân vị {100*s:.0f} của mẫu huấn luyện; "
                        f"khoảng được nới 50%.")

        if r.cpi_imputed and "realcap" in self.fit.terms:
            warn.append("CPI tháng này hoặc tháng trước là NỘI SUY — BLS không "
                        "công bố 2025-10 vì đóng cửa chính phủ.")

        l2: List[Tuple[str, str]] = []
        if layer2:
            for key, direction in layer2.items():
                if key not in LAYER2_ARROWS or direction == 0:
                    continue
                label, sign, prov = LAYER2_ARROWS[key]
                implied = sign * direction          # +1 nghĩa là mũi tên đẩy đô la LÊN
                agree = (implied > 0) == (point > 0)
                l2.append((label,
                           ("đồng thuận" if agree else "NGƯỢC với số học") + f"  [{prov}]"))
            if any("NGƯỢC" in v for _k, v in l2):
                warn.append("Lớp phủ Tầng 2 ngược chiều với lõi cơ học. Tầng 2 giữ "
                            "4/4 trong bảng điểm 2026; bất đồng là lý do để giảm "
                            "tin cậy, không phải để ghi đè.")

        return Forecast(
            month=month, point=point, lo=point - half, hi=point + half,
            regime=regime, abstain=abstain, abstain_reason=why,
            contributions=contrib, warnings=warn, layer2=l2,
            actual=r.y, source=source,
        )

    def forecast_path(self, months_: Sequence[str],
                      layer2: Optional[Dict[str, int]] = None) -> List[Forecast]:
        return [self.forecast(m, layer2) for m in months_ if m in BYMONTH]
