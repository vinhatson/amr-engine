"""
scenarios.py — the four stylised shocks of §10.7, and the episodes of Part II.

Table 10.3's parameter set is reproduced in `registry.WEIGHTS` as the base
values.  The book is emphatic about what it is: "a convention adopted for
illustration, not estimates: nothing in this book has estimated any of them, and
Chapter 11 explains why most of them cannot be.  They are chosen only so that
the qualitative behaviour is visible at plausible orders of magnitude."

§10.7.5 then reports a sanity check the simulation FAILS: the liquidity run
peaks at +17.7 per cent, roughly a quarter larger than anything the dollar has
ever done and more than twice the episode it is modelled on.  That is reported
rather than tuned away, and it locates the excess in κ_base, which multiplies
every elasticity at once.  The engine reproduces the behaviour, not the excess:
`BOOK_SANITY_CHECK` below records the gap so that a run can be compared with it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .core import Options, Result, WorldState, run
from .layers import SigmaInputs
from .qualitative import Forecast, forecast


BOOK_SANITY_CHECK = {
    "largest_21d_rise_pct": 14.05,       # DTWEXAFEGS, to 2008-10-27
    "march_2020_pct": 7.54,              # 2020-03-09 to 2020-03-23
    "book_liquidity_peak_pct": 17.7,     # §10.7.5 — larger than anything observed
    "gfc_2008_total_pct": 18.33,
    "gfc_2008_explained_pct": 6.59,      # residual 64%
    "covid_2020_explained_pct": 1.85,    # residual 76%
    "rally_2022_pct": 15.45,
    "rally_2022_haven_pct": 0.34,        # residual 97.8%
}


@dataclass
class Scenario:
    key: str
    title_vi: str
    source: str
    horizon_months: int
    note_vi: str
    build: Callable[[WorldState], WorldState]
    options: Dict[str, object] = field(default_factory=dict)
    book_prediction_vi: str = ""
    book_target_pct: Optional[float] = None
    gap_note_vi: str = ""


def _baseline() -> WorldState:
    """Table 10.3's baseline state.

    The engine's registry defaults are calibrated so that `WorldState()` IS that
    baseline, reproduced term by term rather than approximated:

        σ_sys 0.349 (stated 0.35)        Φ_sys 0.700 (stated 0.70)
        s_US,sys 0.701 (stated 0.70)     f_hard 0.342 (stated 0.34)
        H_soc = I_imp = 0.300 (stated)   k_Ψ 6.000 (stated 6)
        Ψ_str 0.902                      κ_sys 1.460 (stated band 1.2-2.0)

    H_soc and I_imp land on 0.30 as an actual FIXED POINT of Equation (8.8),
    not as an imposed pair: see `layers.implied_layer4` and the note on
    `Options.cL0`.  κ_sys cannot be reproduced exactly because Table 10.3 states
    five of its seven coefficients and omits a_V and a_A.
    """
    return WorldState()


BASELINE = _baseline


# --------------------------------------------------------------------------- #
# §10.7 — the four stylised shocks
# --------------------------------------------------------------------------- #

def _liquidity(s: WorldState) -> WorldState:
    """(a) sigma_sys jumps 0.35 -> 0.75 and decays with an eight-month constant; bank
    balance-sheet capacity contracts; precautionary demand surges.

    The book's reading: the dollar spikes and then gives it all back.  The
    mechanical block does the work in month 1, the swap lines reverse it from
    month 2, and the haven term decays with stress.  At twenty-four months the
    cumulative effect is +0.19 per cent - essentially nothing.  "That round trip
    is the model's account of March 2020, and it is the right shape."

    The sigma legs are solved so that sigma_sys lands on the stated 0.750.  The
    channel levels are solved so that the peak lands on the stated +17.7 per
    cent - which the book itself reports as a FAILED sanity check, a quarter
    larger than anything the dollar has ever done.  The engine reproduces the
    behaviour and the overshoot together, because separating them would mean
    tuning away the one number §10.7.5 asks the reader to keep.
    """
    return s.shock(p_vix=0.86, p_bondvol=0.82, p_stlfsi=0.60, p_gpr=0.34,
                   bank=0.9573, prec=1.1011, debt=1.0370, cap=0.9723, coll=0.9771)


def _liquidity_with_swaps(s: WorldState) -> WorldState:
    """The same shock at month 2, with the swap lines open.  S_swap is the only
    supply channel that can be opened deliberately and quickly, and in the
    book's run it removes roughly half the peak."""
    return _liquidity(s).shock(swap=1.21, fed=1.02)


def _sanctions(s: WorldState) -> WorldState:
    """(b) S_off rises, so S_ext^eff = S_ext*exp(-delta_off*S_off) falls and the
    mechanical block gains permanently.  Meanwhile T_frag accumulates and f_hard
    drifts toward theta_0, so Psi_str erodes.

    The most instructive of the four, because the two effects have OPPOSITE
    SIGNS and DIFFERENT TIME CONSTANTS.  The dollar is stronger for about
    twenty-two months and then the erosion overtakes the mechanical gain,
    crossing zero at month 22 and reaching -0.49 per cent by month 24 - still
    falling.  "The model says that weaponising the dollar works and then stops
    working", and it puts a horizon on the crossover that is entirely a function
    of how fast f_hard accumulates.

    Note what this scenario does NOT move: the stress legs.  The book's run
    raises S_off, not sigma_sys, and a scenario that quietly raised both would
    hand the geopolitical chain a result it has failed in three independent
    episodes (§17.3).
    """
    return s.shock(S_off=0.35, T_frag=0.52)


def _sanctions_late(s: WorldState) -> WorldState:
    """The same episode two years on, with the hard drivers accumulated past the
    threshold.  This is where the crossover happens."""
    return s.shock(S_off=0.35, T_frag=0.70, C_alt=0.52, Au_sub=0.58)


def _trust(s: WorldState) -> WorldState:
    """(c) M_trust falls, taking Phi_sys and s_US down with it, while R_US rises.
    Reserve and capital-account demand both fall.

    Note what happens in month 1: the dollar RISES, because stress is up and the
    haven term still works.  Then it falls steadily as the mechanical block
    registers the loss of demand.  "The model therefore predicts that a trust
    shock is initially indistinguishable from a risk shock and only separates
    after a quarter or two.  Any case study reading the first weeks of a trust
    episode as evidence of dollar strength is reading the model's transient."

    This builder is the SETTLED state, at the book's -4.3 per cent.  For the
    month-1 transient, run `trust_month1`.
    """
    return s.shock(M_trust=0.42, R_US=0.52, E_inf=0.52,
                   p_vix=0.62, p_stlfsi=0.55, res=0.9520, cap=0.9420)


def _trust_month1(s: WorldState) -> WorldState:
    """The transient: stress is already up, the mechanical loss has not yet
    registered.  The book puts the dollar at +2 per cent here."""
    return s.shock(M_trust=0.60, R_US=0.38, p_vix=0.62, p_stlfsi=0.55)


def _narrative(s: WorldState) -> WorldState:
    """(d) H_soc jumps the separatrix and I_imp with it, so kappa_sys and k_Psi
    both rise sharply.  NO demand or supply channel moves at all.

    The dollar appreciates 9.7 per cent in the book's run, and almost all of it
    is the Psi_str block: with f_hard below the threshold, the Layer-4
    bifurcation flattens the pre-threshold plateau and MEASURED structural
    integrity RISES.  Nothing has improved.  The system is now one f_hard
    excursion away from losing all of it at k_Psi = 28 instead of 6, and the
    width of that transition has fallen from wider than the whole admissible
    range to about 0.15 of it.

    "If this book has one counter-intuitive prediction, it is this one: a rising
    dollar is consistent with a system that has just become much more fragile,
    and on this parameter set the two are not merely consistent but causally
    linked."
    """
    return s.shock(A_alg=0.92, C_src=0.90, P_AI=0.88, T_exp=0.92, R_div=0.18,
                   S_access=0.95, R_fric=0.12, P_habit=0.90, E_sys=0.92)


def _gfc(s: WorldState) -> WorldState:
    """CS1.  +18.33 per cent, of which the model accounts for +6.59 - a residual
    of 64 per cent, and the residual tracks no measurable funding spread."""
    return s.shock(p_vix=0.99, p_bondvol=0.95, p_stlfsi=0.98, p_gpr=0.35,
                   prec=1.18, debt=1.09, bank=0.90, coll=0.91, cap=0.93,
                   fed=1.10, swap=1.40)


def _covid(s: WorldState) -> WorldState:
    """CS2.  +7.54 per cent, of which the model accounts for +1.85 - a residual
    of 76 per cent.  The distinctive feature is that POLICY REVERSED IT."""
    return s.shock(p_vix=1.00, p_bondvol=0.93, p_stlfsi=0.90, p_health=0.98,
                   prec=1.2006, debt=1.0804, bank=0.9168, coll=0.9079,
                   trans=0.9257, fed=1.1859, swap=1.7149)


def _rally_2022(s: WorldState) -> WorldState:
    """CS5.  The episode of §14.1.7, where the haven block accounts for 0.34 of a
    15.45 per cent move - a residual of 97.8 per cent, larger than 2008's or
    2020's.  Starting sigma = 0.767: the convexity mechanism is smallest exactly
    where it is asked to do the most work (I37)."""
    return s.shock(p_vix=0.70, p_bondvol=0.82, p_stlfsi=0.62, p_gpr=1.00,
                   S_off=0.45, T_frag=0.52, cap=1.06, debt=1.04,
                   fed=0.94, E_inf=0.70)


def _tariff_2025(s: WorldState) -> WorldState:
    """CS11.  The failure was a SEQUENCING error, not a refutation: E4 makes
    Phi_sys fall when R_US rises and M_trust falls, and Phi_sys multiplies the
    whole haven term - so a shock originating in the United States shrinks the
    haven channel at the same moment sigma_sys raises it.  The case study put the
    two effects in phases separated by an interval; the evidence is that they
    are SIMULTANEOUS (Proposition 16.1).  Running it here puts them
    simultaneous."""
    return s.shock(p_vix=0.78, p_stlfsi=0.58, R_US=0.48, M_trust=0.50,
                   trans=0.96, cap=0.95, E_inf=0.55)


def _iran_2026(s: WorldState) -> WorldState:
    """CS12.  The geopolitical index reached its fifth-highest month since 1985
    and the dollar did not move - the extreme end of the most replicated negative
    result in the book.  The funding leg sat at 0.228 throughout, and the engine
    is given exactly that: a maximal p_gpr against a quiet funding leg."""
    return s.shock(p_gpr=0.99, p_vix=0.52, p_stlfsi=0.228, trans=1.03)


SCENARIOS: Dict[str, Scenario] = {s.key: s for s in [
    Scenario("liquidity", "Cú sốc thanh khoản (§10.7.1)", "Figure 10.2(a)", 24,
             "σ nhảy 0,35 → 0,75, năng lực bảng cân đối co lại, cầu trú ẩn vọt lên.",
             _liquidity, book_target_pct=17.7,
             gap_note_vi="Sách tự báo đây là một kiểm tra tỉnh táo mà mô phỏng TRƯỢT: "
                         "đỉnh +17,7% lớn hơn khoảng một phần tư so với bất cứ gì đồng "
                         "đô la từng làm (+14,05%) và hơn gấp đôi chính đợt nó mô "
                         "phỏng (+7,54%). Engine tái tạo cả hành vi lẫn phần vượt.",
             book_prediction_vi="Vọt lên rồi trả lại hết: sau 24 tháng còn +0,19%. "
                                "Đường swap gỡ khoảng một nửa đỉnh."),
    Scenario("liquidity_swaps", "Thanh khoản + mở đường swap (tháng 2)", "§10.7.1", 24,
             "Cùng cú sốc, nhưng S_swap mở — kênh cung duy nhất mở được có chủ ý và nhanh.",
             _liquidity_with_swaps,
             book_prediction_vi="Khoảng một nửa đỉnh bị gỡ bỏ."),
    Scenario("sanctions", "Cú sốc trừng phạt (§10.7.2)", "Figure 10.2(b)", 24,
             "S_off tăng → S_ext hiệu dụng giảm; đồng thời T_frag tích luỹ, Ψ_str xói mòn.",
             _sanctions, book_target_pct=4.75,
             book_prediction_vi="Vũ khí hoá đồng đô la CÓ tác dụng, rồi THÔI tác dụng: "
                                "mạnh ~22 tháng, cắt zero ở tháng 22, −0,49% ở tháng 24 "
                                "và vẫn đang rơi."),
    Scenario("sanctions_late", "Trừng phạt, hai năm sau", "§10.7.2", 24,
             "Cùng tình huống với các động lực cứng đã tích luỹ.",
             _sanctions_late, book_target_pct=-0.49,
             book_prediction_vi="Xói mòn vượt qua phần được lợi cơ học."),
    Scenario("trust", "Cú sốc niềm tin (§10.7.3)", "Figure 10.2(c)", 24,
             "M_trust giảm → Φ_sys 0,70 → 0,48 và s_US 0,70 → 0,52; R_US tăng.",
             _trust, book_target_pct=-4.3,
             book_prediction_vi="Tháng 1 TĂNG +2% vì stress lên và số hạng trú ẩn còn "
                                "chạy; sau đó rơi đều về −4,3%. Cú sốc niềm tin ban đầu "
                                "KHÔNG phân biệt được với cú sốc rủi ro."),
    Scenario("narrative", "Cú sốc tự sự (§10.7.4)", "Figure 10.2(d)", 24,
             "H_soc vượt separatrix, I_imp theo sau. Không kênh cung/cầu nào dịch chuyển.",
             _narrative, book_target_pct=9.7,
             gap_note_vi="Một căng thẳng nội tại của chính sách: §10.7.4 nói H_soc "
                         "'nhảy qua separatrix', nhưng Assumption 8.4 duy trì η < 4 "
                         "xuyên suốt Phần I–III, và dưới ngưỡng đó Proposition 8.2 bảo "
                         "đảm điểm bất động là DUY NHẤT và hút toàn cục — tức KHÔNG CÓ "
                         "separatrix nào để nhảy. Engine chạy đúng theo Assumption 8.4, "
                         "nên H_soc trôi tới 0,77 thay vì nhảy, và k_Ψ tới ~19 thay vì 28. "
                         "Muốn tái tạo đúng con số của sách thì phải đặt η ≥ 4, và khi đó "
                         "engine sẽ cảnh báo rằng kết quả đang đứng trên một trong ba nhánh.",
             book_prediction_vi="Đô la lên 9,7%, gần như toàn bộ nằm ở khối Ψ. "
                                "Một đồng đô la đang lên TƯƠNG THÍCH với một hệ vừa trở "
                                "nên mong manh hơn nhiều — và trên bộ tham số này, hai "
                                "điều đó còn có quan hệ nhân quả."),
    Scenario("gfc2008", "Khủng hoảng tài chính 2008–09 (CS1)", "Ch.13", 3,
             "Đợt tăng lớn nhất trong mẫu: +18,33%.",
             _gfc, book_target_pct=6.59,
             gap_note_vi="Chênh lệch nằm ở khối trú ẩn: trên bộ tham số Table 10.3, "
                         "một cú nhảy σ lên 0,93 tự nó đã sinh hơn 13%. Đó chính là I37. "
                         "Chạy lại với --recentre (E22) để thấy phần vượt co lại.",
             book_prediction_vi="Mô hình giải thích +6,59 trên +18,33% — dư số 64%."),
    Scenario("covid2020", "Đại dịch 2020 (CS2)", "Ch.13", 1,
             "+7,54% từ 2020-03-09 đến 2020-03-23, rồi chính sách đảo ngược nó.",
             _covid, book_target_pct=1.85,
             book_prediction_vi="Mô hình giải thích +1,85 trên +7,54% — dư số 76%."),
    Scenario("rally2022", "Đợt tăng 2022 (CS5)", "Ch.14", 10,
             "Khởi điểm σ = 0,767 — ca cực đoan của I37.",
             _rally_2022, book_target_pct=15.45,
             gap_note_vi="Khởi điểm σ cao là cốt lõi của I37: số hạng lồi cho ít nhất "
                         "đúng ở nơi nó được yêu cầu nhiều nhất.",
             book_prediction_vi="Khối trú ẩn giải thích 0,34 trên 15,45% — dư số 97,8%, "
                                "lớn hơn cả 2008 lẫn 2020."),
    Scenario("tariff2025", "Đợt thuế quan 2025 (CS11)", "Ch.16", 2,
             "Cú sốc có nguồn gốc từ chính nước Mỹ: Φ_sys co lại đúng lúc σ_sys đẩy lên.",
             _tariff_2025,
             book_prediction_vi="Thất bại của CS11 là lỗi TRÌNH TỰ, không phải bác bỏ: "
                                "hai hiệu ứng đồng thời, không tách pha."),
    Scenario("iran2026", "Chiến tranh Iran & eo Hormuz 2026 (CS12)", "Ch.14", 2,
             "Chỉ số địa chính trị cao thứ năm kể từ 1985; đô la không dịch chuyển.",
             _iran_2026,
             book_prediction_vi="CS12 đạt 80% số dự báo kiểm chứng được. Nhưng chuỗi "
                                "X_pand ⇒ σ_sys ⇒ DXY vẫn không chạy."),
]}


def run_scenario(
    key: str,
    overrides: Optional[Dict[str, float]] = None,
    opt: Optional[Options] = None,
    base: Optional[WorldState] = None,
) -> Forecast:
    sc = SCENARIOS[key]
    b = base or _baseline()
    return forecast(b, sc.build(b), overrides, opt)


def run_all(overrides: Optional[Dict[str, float]] = None,
            opt: Optional[Options] = None) -> Dict[str, Forecast]:
    return {k: run_scenario(k, overrides, opt) for k in SCENARIOS}
