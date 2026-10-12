"""
qualitative.py — turning a number into the book's own qualitative vocabulary.

This is where the engine earns the word "định tính".  The monograph does not
forecast a level; it reads episodes through an arrow scale and a layer
attribution, and it attaches to every claim what the record says about the
channel the claim ran through.  This module does all three.

The arrow scale (How to Read This Book, §2.7.1):

    ↑ / ↓      small move; within the normal range of the variable
    ↑↑ / ↓↓    large move; a move of the size seen in a stress episode
    ↑↑↑ / ↓↓↓  extreme move; the largest observed, or a regime change
    ↔          no material change

"Where data exist, tables show both the arrow and the number; the arrow is a
summary of the number, never a substitute for it."  Every object this module
returns carries both.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from .core import Options, Result, WorldState, d_ln_dxy_d_sigma, run, smile_threshold
from .registry import CHANNELS, Evidence


# --------------------------------------------------------------------------- #
# The arrow scale
# --------------------------------------------------------------------------- #
#
# Calibrated on the book's own sample statements (§10.7.5):
#   the largest 21-day rise in DTWEXAFEGS across 2006-2026 is +14.05 per cent
#   the March 2020 episode is +7.54 per cent from 2020-03-09 to 2020-03-23
# so "the size seen in a stress episode" is the 3-to-7.5 band, and "the largest
# observed, or a regime change" begins where March 2020 ends.

ARROW_BANDS: Tuple[Tuple[float, str, str], ...] = (
    (0.5,  "↔",   "không đổi đáng kể"),
    (3.0,  "↑",   "biến động nhỏ, trong biên độ thường"),
    (7.5,  "↑↑",  "biến động lớn, cỡ một đợt căng thẳng"),
    (math.inf, "↑↑↑", "biến động cực đoan, cỡ lớn nhất từng quan sát hoặc đổi chế độ"),
)


@dataclass(frozen=True)
class Arrow:
    glyph: str
    pct: float
    gloss: str

    def __str__(self) -> str:
        return f"{self.glyph} {self.pct:+.2f}%"


def arrow(delta_ln: float) -> Arrow:
    """Map a log change to the book's arrow scale, in per cent."""
    pct = 100.0 * delta_ln
    a = abs(pct)
    for hi, glyph, gloss in ARROW_BANDS:
        if a < hi:
            if glyph == "↔":
                return Arrow("↔", pct, gloss)
            return Arrow(glyph if pct > 0 else glyph.replace("↑", "↓"), pct, gloss)
    return Arrow("↑↑↑" if pct > 0 else "↓↓↓", pct, ARROW_BANDS[-1][2])


# --------------------------------------------------------------------------- #
# Regime
# --------------------------------------------------------------------------- #

class Regime(str, Enum):
    CALM = "BÌNH LẶNG"
    TRANSITION = "CHUYỂN TIẾP"
    STRESS = "CĂNG THẲNG"
    CRISIS = "KHỦNG HOẢNG"


def classify_regime(sigma: float, lam: float) -> Tuple[Regime, str]:
    """Regime from σ_sys and the regime weight Λ(σ).

    The sample anchors are the book's own: σ_sys reaches 0.961 on 2008-12-01 and
    falls to 0.097 on 2018-10-02; it stands at or above 0.8 on 10.2 per cent of
    days and at or above 0.9 on 1.9 per cent.

    One property of the construction has to travel with any reading of it: the
    index REWARDS PERSISTENCE OVER PEAK SEVERITY.  2020 places fourth despite
    the VIX reaching its sample maximum of 82.69 that March, because a
    percentile-rank composite accumulates high-σ days and a long moderate
    episode outranks a short extreme one (§5.5.3).
    """
    if sigma >= 0.90:
        return Regime.CRISIS, "trên phân vị 98 của mẫu 2006–2026"
    if sigma >= 0.80:
        return Regime.STRESS, "trong 10,2% số ngày căng thẳng nhất của mẫu"
    if lam >= 0.5:
        return Regime.TRANSITION, "đã qua ngưỡng σ*: các độ co giãn đang chuyển sang giá trị khủng hoảng"
    return Regime.CALM, "dưới ngưỡng σ*: các độ co giãn ở giá trị bình lặng"


# --------------------------------------------------------------------------- #
# Attribution
# --------------------------------------------------------------------------- #

@dataclass
class BlockAttribution:
    name: str
    delta_ln: float
    arrow: Arrow
    share: float


@dataclass
class ChannelMove:
    key: str
    symbol: str
    side: str
    from_level: float
    to_level: float
    elasticity: float
    delta_ln_dxy: float
    arrow: Arrow
    evidence: str
    evidence_note: str


EVIDENCE_NOTE: Dict[str, str] = {
    "SUPPORTED": "Chương 17 xếp vào phần sống sót.",
    "PARTIAL": "Bằng chứng hỗn hợp hoặc chỉ một tình huống.",
    "UNTESTED": "Không có phán quyết — 46/110 dự báo của sách thuộc nhóm này.",
    "REFUTED": "Chương 17 xếp vào phần KHÔNG sống sót.",
    "UNIDENTIFIED": "Không nhận dạng được: thêm dữ liệu cũng không sửa (Prop. 11.1 / 13.2).",
    "MEASURED_ZERO": "Đo được, đã đo, và bằng không (ρ = −0,062; t = −0,55).",
    "ADDED": "Biến do engine bổ sung — không có trong sách, chưa qua kiểm chứng nào.",
}


@dataclass
class Forecast:
    """A qualitative reading of one move, with the number behind every arrow."""
    headline: Arrow
    regime: Regime
    regime_note: str
    sigma_from: float
    sigma_to: float
    kappa_from: float
    kappa_to: float
    psi_from: float
    psi_to: float
    blocks: List[BlockAttribution]
    channels: List[ChannelMove]
    dominant: str
    sigma_response: Dict[str, float]
    smile_sigma: Optional[float]
    warnings: List[str]
    evidence_mix: Dict[str, float]
    base: Result
    shocked: Result

    # ----------------------------------------------------------------- #
    def narrative_vi(self) -> str:
        """The reading, in the register of the book's own case-study template."""
        out: List[str] = []
        out.append(f"KẾT LUẬN: DXY {self.headline}  ({self.headline.gloss})")
        out.append(f"Chế độ: {self.regime.value} — {self.regime_note}")
        out.append(f"σ_sys {self.sigma_from:.3f} → {self.sigma_to:.3f}   "
                   f"κ_sys {self.kappa_from:.3f} → {self.kappa_to:.3f}   "
                   f"Ψ_str {self.psi_from:.4f} → {self.psi_to:.4f}")
        out.append("")
        out.append("PHÂN RÃ THEO KHỐI (Figure 10.2):")
        for b in self.blocks:
            out.append(f"  {b.name:<18} {b.arrow}   {b.share*100:5.1f}% của tổng tuyệt đối")
        out.append(f"  → Khối chi phối: {self.dominant}")
        out.append("")
        if self.channels:
            out.append("KÊNH DẪN (chỉ các kênh thực sự dịch chuyển):")
            for c in self.channels:
                out.append(f"  {c.symbol:<10} {c.from_level:.3f} → {c.to_level:.3f}   "
                           f"ε={c.elasticity:+.3f}   DXY {c.arrow}   [{c.evidence}]")
                out.append(f"             {c.evidence_note}")
            out.append("")
        r = self.sigma_response
        out.append("PHẢN ỨNG VỚI STRESS — ba thành phần, không phải một (Eq. 10.7):")
        out.append(f"  trú ẩn trực tiếp {r['direct_haven']:+.4f}   "
                   f"phản thân {r['reflexive']:+.4f}   "
                   f"chuyển chế độ {r['regime']:+.4f}   = {r['total']:+.4f}")
        if self.smile_sigma is None:
            out.append("  Không có nụ cười đô la trên bộ tham số này: cần λ₁ < 0 "
                       "(Proposition 10.3). Độ lồi λ₂ > 0 một mình chỉ làm dốc thêm "
                       "một phản ứng vốn đã dương, không thể đổi dấu.")
        else:
            out.append(f"  σ† = {self.smile_sigma:.3f} — phản ứng đổi dấu tại đây.")
        out.append("")
        out.append("TÌNH TRẠNG BẰNG CHỨNG của các kênh mang dự báo này:")
        for k, v in sorted(self.evidence_mix.items(), key=lambda kv: -kv[1]):
            out.append(f"  {k:<14} {v*100:5.1f}%")
        if self.warnings:
            out.append("")
            out.append("CẢNH BÁO:")
            for w in self.warnings:
                out.append(f"  ⚠ {w}")
        return "\n".join(out)


# --------------------------------------------------------------------------- #

def forecast(
    base_state: WorldState,
    shocked_state: WorldState,
    overrides: Optional[Dict[str, float]] = None,
    opt: Optional[Options] = None,
) -> Forecast:
    """Read one move the way Part II reads an episode.

    The differenced form E10b is what the case studies use, and §10.3 names the
    three approximations buried in its "≈" — it holds κ_sys, Φ_sys and the
    elasticities fixed across the window, it drops the cross-terms in
    Δκ_sys·ln(D*/S*), and Δσ² means (Δσ) applied to the squared term rather than
    the square of the change.  This function makes none of those approximations:
    it evaluates E9 twice and differences the results, so Δκ_sys is carried
    exactly.  That matters because Chapter 7 argues κ_sys moves most precisely in
    the crises the case studies examine.
    """
    opt = opt or Options()
    if opt.recentre_convexity and opt.sigma_anchor is None:
        # E22 anchors on the episode's ENTRY state, which is the whole point:
        # the convex term should bite from where the episode starts, not from
        # the middle of a range no episode occupies.
        entry = run(base_state, overrides, opt).sigma
        opt = Options(**{**opt.__dict__, "sigma_anchor": entry.sigma})

    b = run(base_state, overrides, opt)
    a = run(shocked_state, overrides, opt)

    d_total = a.ln_DXY - b.ln_DXY
    d_mech = a.mechanical - b.mechanical
    d_haven = a.haven - b.haven
    d_psi = math.log(max(a.psi_str, 1e-12)) - math.log(max(b.psi_str, 1e-12))

    raw = [("cơ học ×κ", d_mech), ("trú ẩn", d_haven), ("cấu trúc Ψ", d_psi)]
    tot_abs = sum(abs(v) for _, v in raw) or 1.0
    blocks = [BlockAttribution(n, v, arrow(v), abs(v) / tot_abs) for n, v in raw]
    dominant = max(blocks, key=lambda x: abs(x.delta_ln)).name

    # Channel-by-channel, evaluated at the shocked elasticity so the regime
    # switch is inside the attribution rather than outside it.
    bt = {t.key: t for t in b.terms}
    moves: List[ChannelMove] = []
    for t in a.terms:
        t0 = bt.get(t.key)
        if t0 is None:
            continue
        if abs(t.level - t0.level) < 1e-12 and abs(t.log_contrib - t0.log_contrib) < 1e-12:
            continue
        d = a.kappa.kappa * t.log_contrib - b.kappa.kappa * t0.log_contrib
        moves.append(ChannelMove(
            key=t.key, symbol=t.symbol, side=t.side,
            from_level=t0.level, to_level=t.level,
            elasticity=t.elasticity, delta_ln_dxy=d, arrow=arrow(d),
            evidence=t.evidence,
            evidence_note=EVIDENCE_NOTE.get(t.evidence, ""),
        ))
    moves.sort(key=lambda m: -abs(m.delta_ln_dxy))

    mix: Dict[str, float] = {}
    wsum = sum(abs(m.delta_ln_dxy) for m in moves) or 1.0
    for m in moves:
        mix[m.evidence] = mix.get(m.evidence, 0.0) + abs(m.delta_ln_dxy) / wsum

    regime, note = classify_regime(a.sigma.sigma, a.lam_weight)

    return Forecast(
        headline=arrow(d_total), regime=regime, regime_note=note,
        sigma_from=b.sigma.sigma, sigma_to=a.sigma.sigma,
        kappa_from=b.kappa.kappa, kappa_to=a.kappa.kappa,
        psi_from=b.psi_str, psi_to=a.psi_str,
        blocks=blocks, channels=moves, dominant=dominant,
        sigma_response=d_ln_dxy_d_sigma(a),
        smile_sigma=smile_threshold(a),
        warnings=sorted(set(b.warnings) | set(a.warnings)),
        evidence_mix=mix, base=b, shocked=a,
    )


# --------------------------------------------------------------------------- #
# The honesty block
# --------------------------------------------------------------------------- #

RESIDUAL_NOTE_VI = (
    "DƯ SỐ KHÔNG GIẢI THÍCH ĐƯỢC. Trên hai cuộc khủng hoảng trung tâm, mô hình "
    "giải thích +6,59 trên +18,33% của 2008 và +1,85 trên +7,54% của 2020 — dư "
    "số 64% và 76% (Table 11.7). Khối mà kiến trúc đặt ở trung tâm một cuộc "
    "khủng hoảng lại đóng góp ít nhất trong hai khối có dịch chuyển, và dư số "
    "không bám theo bất kỳ chênh lệch funding đo được nào. Ứng viên tốt nhất để "
    "giải thích nó là một κ_sys phụ thuộc trạng thái — tức chính đại lượng mà "
    "Proposition 11.1 tuyên bố không thể nhận dạng. Mọi con số engine in ra nên "
    "được đọc cùng với dư số này."
)

CONVEXITY_NOTE_VI = (
    "VỊ TRÍ CỦA ĐỘ LỒI (I37). Một số hạng lồi trên biến bị chặn cho mức tăng lớn "
    "nhất ở GIỮA dải. Mọi tình huống sách chấm điểm, trừ chiến tranh thương mại "
    "2018, đều bắt đầu khi σ_sys đã cao — nên cơ chế nhỏ nhất đúng ở chỗ nó được "
    "yêu cầu làm nhiều nhất. Đợt tăng 2022 là ca cực đoan: khởi điểm σ = 0,767, "
    "khối trú ẩn giải thích 0,34 trên 15,45%, dư số 97,8%. Đây là tính chất của "
    "DẠNG HÀM, không phải của ước lượng — ước lượng lại λ₂ không gỡ được. "
    "Tuỳ chọn recentre_convexity (E22) gỡ được."
)
