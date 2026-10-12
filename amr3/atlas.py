"""
atlas.py — ĐỊA CHỈ HÌNH HỌC của từng biến.

amr xếp biến theo PHƯƠNG TRÌNH nó xuất hiện trong đó: `block = "E4 · Φ_sys"`,
`block = "E6 · κ_sys"`. Đó là một cách xếp ĐẠI SỐ — câu hỏi được trả lời là
"đây là hệ số của công thức nào".

amr3 xếp cùng những biến ấy theo VỊ TRÍ HÌNH HỌC: biến nằm trên tấm nào, và
nó làm gì với tấm đó. Không biến nào bị thêm, không biến nào bị bỏ —
`tests/test_amr3.py::test_atlas_covers_every_amr_variable_exactly_once`
khẳng định điều đó trên chính registry của amr.

BỐN VAI, và chúng không phải nhãn dán mà là bốn thứ khác nhau về hình học:

  POSITION   dịch CHÍNH TẤM đi.  Các hệ số chặn: φ_0, γ_0, κ_base, θ_0, σ*.
             Đây là vai duy nhất một vết đâm có thể tác động tới — đâm xuyên
             nghĩa là tấm bị dịch, không phải điểm trên tấm bị dịch.

  TANGENT    dịch MỘT ĐIỂM TRÊN tấm.  Mọi độ co giãn α_i, β_j, và các tải
             trọng cùng tầng.  Toàn bộ amr sống ở vai này — đó là lý do nó
             trượt song song.

  CURVATURE  đặt tấm CONG bao nhiêu.  θ (độ dốc Λ), k_Ψ (tốc độ xói mòn),
             λ_2 (số hạng bậc hai), w_CT (số hạng tương tác).  Độ cong quyết
             định một vết đâm sâu tới đâu: giấy căng thì rách, giấy chùng thì
             dạt.  Nó không phải thừa số tuỳ ý — xem geometry.tautness.

  AMPLITUDE  đặt tấm có thể lệch TỐI ĐA bao nhiêu.  L_max, δ_off.

VÀ MỘT TRƯỜNG RIÊNG — `pierces`.  Trong registry của amr, trường `gamma` của
mỗi trọng số đã ghi sẵn các cạnh LIÊN TẦNG: `phi_R` mang `{'hsoc': 0.6}`, tức
Tầng 4 tác động lên Tầng 2.  amr đối xử với mọi cạnh đó như TIẾP TUYẾN — chúng
đổi hệ số, hệ số đổi tốc độ, tốc độ không đổi vị trí ngưỡng (Assumption 9.2).

`pierces` chỉ đọc lại cùng những cạnh ấy và hỏi thêm một câu: bao nhiêu phần
của tác động này là PHÁP TUYẾN.  Câu trả lời là τ, và τ ≡ 0 cho lại amr.

Việc phân phối lại là ĐỌC LẠI CÁI ĐÃ CÓ, không phải phát minh cái mới.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from amr.registry import CHANNELS, D_PREC, LATENTS, WEIGHTS   # noqa: E402


# --------------------------------------------------------------------------- #
# Sáu tấm, cộng một hướng trực giao mà chính cuốn sách đã khai
# --------------------------------------------------------------------------- #

class Sheet(Enum):
    """Sáu tấm, đánh số đúng như sáu tầng của sách, cộng hướng trú ẩn.

    HƯỚNG TRÚ ẨN không phải tầng thứ bảy.  §10.2 viết về khối trú ẩn: "cộng
    tính trong log và do đó ĐỘC LẬP với khối cơ học".  Đó đã là một phát biểu
    hình học — một hướng trực giao — và nó là chỗ DUY NHẤT trong cả cuốn sách
    hình học xuất hiện.  amr3 không mang hình học từ ngoài vào; nó lấy cái
    xuất hiện một lần ở §10.2 và hỏi tại sao chỉ một lần.
    """
    MECHANICAL = 0
    STATE      = 1
    STRUCTURAL = 2
    REFLEXIVE  = 3
    PSYCHO     = 4
    SECULAR    = 5
    HAVEN      = 9          # hướng trực giao của §10.2, không phải một tầng

    @property
    def vi(self) -> str:
        return {
            0: "Σ₀ cơ học", 1: "Σ₁ trạng thái", 2: "Σ₂ cấu trúc",
            3: "Σ₃ phản thân", 4: "Σ₄ tâm lý-kỹ thuật", 5: "Σ₅ thế kỷ",
            9: "⊥ trú ẩn",
        }[self.value]


class Role(Enum):
    POSITION  = "vị trí"      # dịch chính tấm
    TANGENT   = "tiếp tuyến"  # dịch một điểm trên tấm
    CURVATURE = "độ cong"     # tấm cong bao nhiêu
    AMPLITUDE = "biên độ"     # tấm lệch được tối đa bao nhiêu
    CARRIER   = "giá mang"    # biến ẩn / kênh: toạ độ, không phải hệ số


@dataclass(frozen=True)
class Address:
    """Địa chỉ hình học của một biến. Thay cho `block` của amr."""
    key: str
    sheet: Sheet
    role: Role
    note: str = ""
    # Các cạnh liên tầng mà biến này mang, đọc từ `gamma` của amr.
    # (tấm nguồn, tên biến trạng thái nguồn, tải trọng của amr)
    pierces: Tuple[Tuple[Sheet, str, float], ...] = ()


# --------------------------------------------------------------------------- #
# Vai của 39 trọng số
# --------------------------------------------------------------------------- #

_ROLES: Dict[str, Tuple[Sheet, Role, str]] = {
    # --- Σ₁ trạng thái ---------------------------------------------------- #
    "w_sigma":      (Sheet.STATE, Role.AMPLITUDE, "thang chung của σ_sys"),
    "w_X":          (Sheet.STATE, Role.TANGENT, "tải trọng ngoại sinh"),
    "w_F":          (Sheet.STATE, Role.TANGENT, "tải trọng tài chính"),
    "w_H":          (Sheet.STATE, Role.TANGENT, "tải trọng sức khoẻ, ADDED"),
    "sigma_star":   (Sheet.STATE, Role.POSITION,
                     "NGƯỠNG chuyển chế độ — vị trí tấm Σ₁, và là vị trí duy "
                     "nhất Λ(σ) biết tới"),
    "theta":        (Sheet.STATE, Role.CURVATURE,
                     "độ dốc Λ. Λ′ ≤ ¼ nên θ cũng chính là độ CĂNG tối đa"),

    # --- Σ₂ cấu trúc ------------------------------------------------------ #
    "phi_0":        (Sheet.STRUCTURAL, Role.POSITION, "chặn của Φ_sys"),
    "phi_G":        (Sheet.STRUCTURAL, Role.TANGENT, "năng lực chính quyền"),
    "phi_R":        (Sheet.STRUCTURAL, Role.TANGENT,
                     "tính bền của chế độ — và nó MANG cạnh 4→2"),
    "phi_M":        (Sheet.STRUCTURAL, Role.TANGENT, "lòng tin tiền tệ"),
    "phi_T":        (Sheet.STRUCTURAL, Role.TANGENT, "phân mảnh"),
    "gam_0":        (Sheet.STRUCTURAL, Role.POSITION, "chặn của s_US"),
    "gam_G":        (Sheet.STRUCTURAL, Role.TANGENT, "G_pol vào s_US"),
    "gam_R":        (Sheet.STRUCTURAL, Role.TANGENT, "R_US vào s_US"),
    "gam_E":        (Sheet.STRUCTURAL, Role.TANGENT, "E_inf vào s_US"),
    "gam_T":        (Sheet.STRUCTURAL, Role.TANGENT, "T_frag vào s_US"),
    "delta_off":    (Sheet.STRUCTURAL, Role.AMPLITUDE, "biên độ S_off, E9"),

    # --- Σ₃ phản thân ----------------------------------------------------- #
    "kappa_base":   (Sheet.REFLEXIVE, Role.POSITION,
                     "VỊ TRÍ tấm Σ₃. Prop. 11.1: không nhận dạng được — nên "
                     "đây là vị trí tấm mà chưa ai đo được"),
    "a_V":          (Sheet.REFLEXIVE, Role.TANGENT, "V_USD vào κ"),
    "a_M":          (Sheet.REFLEXIVE, Role.TANGENT, "M_shock vào κ — MANG cạnh 4→3"),
    "a_A":          (Sheet.REFLEXIVE, Role.TANGENT, "A_meta vào κ"),
    "a_sigma":      (Sheet.REFLEXIVE, Role.TANGENT, "σ vào κ — MANG cạnh 4→3"),
    "kappa_R":      (Sheet.REFLEXIVE, Role.CURVATURE, "độ hồi quy của κ"),
    "a_H":          (Sheet.REFLEXIVE, Role.TANGENT, "H_soc vào κ"),
    "a_I":          (Sheet.REFLEXIVE, Role.TANGENT, "I_imp vào κ"),
    "r_rev":        (Sheet.REFLEXIVE, Role.CURVATURE, "đảo chiều, ADDED, nền 0"),

    # --- Σ₅ thế kỷ -------------------------------------------------------- #
    "theta_0":      (Sheet.SECULAR, Role.POSITION,
                     "NGƯỠNG tích luỹ động lực cứng. Assumption 9.2 giữ nó CỐ "
                     "ĐỊNH trước tầng tự sự; §9.8 gọi đó là chỗ hệ quả lớn "
                     "nhất chương theo bản gốc. Đây là tờ giấy."),
    "k_psi":        (Sheet.SECULAR, Role.CURVATURE, "tốc độ xói mòn nền"),
    "L_max":        (Sheet.SECULAR, Role.AMPLITUDE, "độ sâu xói mòn tối đa"),
    "w_Calt":       (Sheet.SECULAR, Role.TANGENT, "C_alt vào f_hard"),
    "w_Tfrag":      (Sheet.SECULAR, Role.TANGENT, "T_frag vào f_hard"),
    "w_CT":         (Sheet.SECULAR, Role.CURVATURE, "tương tác C_alt × T_frag"),
    "w_gold":       (Sheet.SECULAR, Role.TANGENT, "Au_sub vào f_hard, ADDED"),
    "b_F":          (Sheet.SECULAR, Role.TANGENT,
                     "đường về 5→4, ISSUES #32, bị từ chối, nền 0"),

    # --- ⊥ trú ẩn --------------------------------------------------------- #
    "lam_1":        (Sheet.HAVEN, Role.TANGENT, "bậc nhất theo σ"),
    "lam_2":        (Sheet.HAVEN, Role.CURVATURE, "bậc hai theo σ — I37"),
    "alpha_prec":   (Sheet.HAVEN, Role.TANGENT, "số mũ phòng ngừa"),
    "w_prec_short": (Sheet.HAVEN, Role.TANGENT, "đầu ngắn của đường cong, ADDED"),

    # --- Σ₀ cơ học -------------------------------------------------------- #
    "theta_sub":    (Sheet.MECHANICAL, Role.POSITION, "hạ tầng số, ADDED"),
}

# Tấm nguồn của từng biến trạng thái xuất hiện trong `gamma` của amr.
_SOURCE_SHEET: Dict[str, Sheet] = {
    "sigma": Sheet.STATE,
    "hsoc":  Sheet.PSYCHO,
    "iimp":  Sheet.PSYCHO,
    "phi":   Sheet.STRUCTURAL,
    "fhard": Sheet.SECULAR,
    "psi":   Sheet.SECULAR,
    "kappa": Sheet.REFLEXIVE,
}

_LATENT_SHEET: Dict[str, Sheet] = {
    "MECHANICAL": Sheet.MECHANICAL, "STATE": Sheet.STATE,
    "STRUCTURAL": Sheet.STRUCTURAL, "REFLEXIVE": Sheet.REFLEXIVE,
    "PSYCHO": Sheet.PSYCHO, "SECULAR": Sheet.SECULAR,
}


def _build() -> Dict[str, Address]:
    out: Dict[str, Address] = {}

    for key, w in WEIGHTS.items():
        if key not in _ROLES:
            raise KeyError(f"trọng số {key!r} của amr chưa có địa chỉ hình học")
        sheet, role, note = _ROLES[key]
        edges: List[Tuple[Sheet, str, float]] = []
        for src, load in (w.gamma or {}).items():
            s = _SOURCE_SHEET.get(src)
            if s is None:
                raise KeyError(f"biến trạng thái nguồn {src!r} chưa gán tấm")
            if s is not sheet:                       # chỉ cạnh LIÊN tấm
                edges.append((s, src, float(load)))
        out[key] = Address(key, sheet, role, note, tuple(edges))

    for key, lat in LATENTS.items():
        name = lat.layer.name if hasattr(lat.layer, "name") else str(lat.layer)
        sheet = _LATENT_SHEET[name.split(".")[-1]]
        out[key] = Address(key, sheet, Role.CARRIER, f"biến ẩn Tầng {sheet.value}")

    for c in list(CHANNELS.values()) + [D_PREC]:
        if c.key in out:
            continue
        sheet = Sheet.HAVEN if c.key == "prec" else Sheet.MECHANICAL
        out[c.key] = Address(c.key, sheet, Role.CARRIER, f"kênh {c.side} {c.symbol}")

    return out


ATLAS: Dict[str, Address] = _build()


# --------------------------------------------------------------------------- #
# Tra cứu
# --------------------------------------------------------------------------- #

def on_sheet(sheet: Sheet) -> List[Address]:
    return [a for a in ATLAS.values() if a.sheet is sheet]


def with_role(role: Role) -> List[Address]:
    return [a for a in ATLAS.values() if a.role is role]


def position_weight(sheet: Sheet) -> str | None:
    """Trọng số VỊ TRÍ của một tấm — cái duy nhất một vết đâm dịch được.

    Σ₄ không có, và đó không phải thiếu sót: Remark 10.2 nói Tầng 4 "là một
    NGUỒN… nó tác động lên Tầng 3 và 5 và không bị gì tác động lại".  Một
    nguồn không có vị trí để bị dịch.  amr3 giữ nguyên điều đó bằng cách để
    τ_*4 ≡ 0 theo mặc định.
    """
    cands = [a.key for a in on_sheet(sheet) if a.role is Role.POSITION]
    order = {"sigma_star": 0, "phi_0": 0, "kappa_base": 0, "theta_0": 0, "theta_sub": 0}
    cands.sort(key=lambda k: order.get(k, 9))
    return cands[0] if cands else None


def cross_sheet_edges() -> List[Tuple[Sheet, Sheet, str, str, float]]:
    """Mọi cạnh liên tấm amr đã mã hoá trong `gamma`, không thêm không bớt.

    Trả về (tấm nguồn, tấm đích, biến nguồn, trọng số đích, tải trọng amr).
    """
    out = []
    for a in ATLAS.values():
        for src_sheet, src_var, load in a.pierces:
            out.append((src_sheet, a.sheet, src_var, a.key, load))
    out.sort(key=lambda r: (r[0].value, r[1].value, r[3]))
    return out


def unmeasured() -> Dict[Sheet, List[Tuple[str, str]]]:
    """Ô nào người dùng VẪN TỰ ĐIỀN, đọc từ trường `measurement` của amr.

    Đây không phải khuyết tật amr3 vá được. Nó là trạng thái thật, và việc duy
    nhất đúng để làm với nó là DÁN NHÃN, để một số tự điền không bị lẫn với một
    số đã đo. Chín biến Tầng 4 ghi nguyên văn "No series" trong registry; H_soc
    và I_imp thì cũng không phải đầu vào mà là điểm bất động của Eq (8.8) giải
    TỪ chín biến đó — nên một giá trị H_soc là hệ quả của chín ô tự điền.
    """
    hits: Dict[Sheet, List[Tuple[str, str]]] = {}
    for key, lat in LATENTS.items():
        low = (lat.measurement or "").strip().lower()
        if "no series" in low or "zero series" in low:
            tag = "không có chuỗi"
        elif "constructible" in low or "must be built" in low:
            tag = "dựng được, chưa dựng"
        elif low.startswith("latent"):
            tag = "biến ẩn, quy trình đo còn mở"
        elif low.startswith("substitute") or low.startswith("tier"):
            tag = "chỉ có biến thay thế"
        elif "proxy" in low and "only" in low:
            tag = "chỉ có biến thay thế"
        else:
            continue
        a = ATLAS.get(key)
        if a is None:
            continue
        hits.setdefault(a.sheet, []).append((key, tag))
    for v in hits.values():
        v.sort()
    return hits


def summary() -> str:
    lines = ["BẢN ĐỒ HÌNH HỌC — cùng biến, xếp lại theo vị trí", "─" * 84]
    for sheet in Sheet:
        addrs = on_sheet(sheet)
        if not addrs:
            continue
        lines.append(f"\n{sheet.vi}   ({len(addrs)} biến)")
        for role in (Role.POSITION, Role.TANGENT, Role.CURVATURE,
                     Role.AMPLITUDE, Role.CARRIER):
            ks = sorted(a.key for a in addrs if a.role is role)
            if ks:
                head = f"  {role.value:10s}"
                body = ", ".join(ks)
                lines.append(f"{head} {body}")
    lines.append("\nCẠNH LIÊN TẤM — đọc từ `gamma` của amr, không thêm cạnh nào")
    lines.append("─" * 84)
    for s, d, var, wk, load in cross_sheet_edges():
        lines.append(f"  Σ{s.value} → Σ{d.value}   {var:6s} → {wk:12s} tải {load:+.2f}")
    return "\n".join(lines)
