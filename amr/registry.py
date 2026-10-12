"""
registry.py — Variable and weight registry for the AMR qualitative forecasting engine.

Source of record: Vi Nhat Son, "The Architecture of Market Regimes: Modeling DXY
through Structural and Reflexive Layers" (Expanded and Consolidated Edition,
6 September 2026).  Appendix A is the notation registry this file mirrors.

Every entry carries a PROVENANCE tag so that a value stated by the book is never
confused with a value this engine supplies:

    BOOK_STATED        a number printed in the book (chiefly Table 10.3)
    BOOK_IMPLIED       forced by the book's own worked example or argument
    BOOK_QUALITATIVE   the book states the direction / relative size, not the number
    ENGINE_CONVENTION  supplied here so the engine runs; the book leaves it OPEN
    OPEN               declared, bounded, signed, never valued (42 of 55 parameters)

and an EVIDENCE tag from the Chapter 17 scorecard, so that every arrow the engine
prints can be read together with what the record says about the channel it ran through.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Tags
# --------------------------------------------------------------------------- #

class Provenance(str, Enum):
    BOOK_STATED = "BOOK_STATED"
    BOOK_IMPLIED = "BOOK_IMPLIED"
    BOOK_QUALITATIVE = "BOOK_QUALITATIVE"
    ENGINE_CONVENTION = "ENGINE_CONVENTION"
    OPEN = "OPEN"


class Evidence(str, Enum):
    """Chapter 17's verdict on the channel, carried at the point of the claim."""
    SUPPORTED = "SUPPORTED"            # §17.4
    PARTIAL = "PARTIAL"                # mixed or single-episode support
    UNTESTED = "UNTESTED"              # no verdict; 46 of 110 predictions
    REFUTED = "REFUTED"                # §17.3
    UNIDENTIFIED = "UNIDENTIFIED"      # Prop. 11.1 / Prop. 13.2 — no data can fix it
    MEASURED_ZERO = "MEASURED_ZERO"    # estimable, estimated, zero (D_net)
    ADDED = "ADDED"                    # introduced by this engine, not in the book


class Layer(int, Enum):
    MECHANICAL = 0
    STATE = 1
    STRUCTURAL = 2
    REFLEXIVE = 3
    PSYCHO = 4
    SECULAR = 5
    WEIGHT = 6   # Layer W — transverse, not stacked.  See SPEC.md §1.


# --------------------------------------------------------------------------- #
# Channels (Layer 0)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Channel:
    key: str
    symbol: str
    name_en: str
    name_vi: str
    side: str                      # "D" numerator, "S" denominator
    alpha_calm: float              # calm-regime elasticity  (beta_calm if side == "S")
    alpha_crisis: float            # crisis-regime elasticity
    provenance: Provenance
    evidence: Evidence
    emergent: bool = False         # enters as 1 + X/Xbar  (ISSUES #29)
    note: str = ""


# Elasticity priors.
#
# Table 10.3 states ONE number per channel for nine channels.  The book's own
# Equation (2.9) makes every elasticity a logistic blend of a calm and a crisis
# value, so a single number is the blend evaluated at the baseline sigma = 0.35.
# The calm/crisis pairs below are chosen to reproduce the Table 10.3 number at
# sigma = 0.35 under the default (theta, sigma*) and to respect the direction and
# relative size the book states channel by channel:
#
#   D_trans  "the least state-dependent of the ten"               §3.1
#   D_debt   "alpha_crisis > alpha_calm — a large gap"            §3.2
#   D_cap    "alpha_calm > alpha_crisis"                          §3.3
#   D_res    "small calm-crisis gap ... institutional slowness"   §3.5
#   S_Fed    "a large calm-to-crisis gap with the crisis value smaller"  §4.1
#   S_bank   the binding constraint moves to balance sheets in crisis    §4.4
#
# Channels the book gives no number for are ENGINE_CONVENTION at an order of
# magnitude consistent with their neighbours.  None of this is an estimate.

DEMAND: List[Channel] = [
    Channel("trans", "D_trans", "Transactional demand", "Cầu giao dịch (thương mại, hàng hoá)",
            "D", 0.19, 0.22, Provenance.BOOK_STATED, Evidence.PARTIAL,
            note="Contractual, not discretionary; least state-dependent of the ten."),
    Channel("debt", "D_debt", "Debt-servicing demand", "Cầu trả nợ (hệ Eurodollar)",
            "D", 0.22, 0.62, Provenance.BOOK_STATED, Evidence.UNTESTED,
            note="The dollar short squeeze. Largest calm-to-crisis gap on the demand side."),
    Channel("cap", "D_cap", "Capital-asset demand", "Cầu tài sản vốn (tăng trưởng, chênh lệch lãi)",
            "D", 0.38, 0.12, Provenance.BOOK_STATED, Evidence.PARTIAL,
            note="Return-seeking; abandoned as stress rises. Hands off to D_prec at sigma*."),
    Channel("res", "D_res", "Reserve-management demand", "Cầu quản lý dự trữ",
            "D", 0.24, 0.27, Provenance.BOOK_STATED, Evidence.UNTESTED,
            note="Reserve managers do not rebalance weekly."),
    Channel("hedge", "D_hedge", "Hedging demand", "Cầu phòng hộ (chi phí FX swap)",
            "D", 0.10, 0.30, Provenance.ENGINE_CONVENTION, Evidence.UNTESTED,
            note="Basis is Tier 3; TED and SOFR-IORB stand in."),
    Channel("gamma", "D_gamma", "Derivative demand", "Cầu phái sinh (gamma của dealer)",
            "D", 0.05, 0.25, Provenance.ENGINE_CONVENTION, Evidence.UNTESTED,
            note="No adequate free substitute exists. Check against kappa_base (§7.2)."),
    Channel("net", "D_net", "Network demand", "Cầu mạng lưới (thanh toán, stablecoin)",
            "D", 0.02, 0.02, Provenance.BOOK_QUALITATIVE, Evidence.MEASURED_ZERO,
            emergent=True,
            note="Grew 74-fold; corr with the dollar -0.062, t = -0.55. Estimated, and zero."),
    Channel("micro", "D_micro", "Microstructural demand", "Cầu vi cấu trúc (mùa vụ)",
            "D", 0.02, 0.02, Provenance.BOOK_STATED, Evidence.UNTESTED,
            note="E2: 1.02 on the final day of each quarter, 1 otherwise."),
    Channel("hcap", "D_hcap", "Human-capital & IP demand", "Cầu vốn con người và sở hữu trí tuệ",
            "D", 0.06, 0.06, Provenance.ENGINE_CONVENTION, Evidence.UNTESTED,
            note="Flow, separated from the stock H_cap by ISSUES #24."),
]

# D_prec is NOT in the product.  ISSUES #7 excludes prec from index set I; it
# re-enters E9 as its own factor with the exponent alpha_prec(sigma), and the
# share s_US,sys multiplies it INSIDE the base per ISSUES #8 / §6.7.2.
D_PREC = Channel(
    "prec", "D_prec", "Safe-haven demand", "Cầu trú ẩn an toàn (chạy về chất lượng)",
    "D", 0.05, 0.40, Provenance.BOOK_STATED, Evidence.PARTIAL,
    note="Separate E9 factor. Table 10.3 states alpha_prec = 0.15 at the baseline state.")

SUPPLY: List[Channel] = [
    Channel("fed", "S_Fed", "Federal Reserve actions", "Hành động của Fed",
            "S", 0.38, 0.18, Provenance.BOOK_STATED, Evidence.PARTIAL,
            note="Large gap, crisis value smaller: in a shortage, reserves relieve less."),
    Channel("tsy", "S_Tsy", "U.S. Treasury actions", "Hành động của Kho bạc Mỹ",
            "S", 0.14, 0.18, Provenance.ENGINE_CONVENTION, Evidence.UNTESTED,
            note="TGA and bill issuance; the cash-management lever of §19.2.5."),
    Channel("coll", "S_coll", "Collateral availability", "Khả dụng tài sản thế chấp (repo)",
            "S", 0.18, 0.24, Provenance.BOOK_STATED, Evidence.PARTIAL,
            note="Includes S_shadow by ISSUES #5. RRPONTSYD blanks are zeros, not missing."),
    Channel("bank", "S_bank", "Bank balance-sheet capacity", "Năng lực bảng cân đối ngân hàng",
            "S", 0.18, 0.36, Provenance.BOOK_STATED, Evidence.UNTESTED,
            note="Unmeasured. The binding constraint in a crisis moves here."),
    Channel("swap", "S_swap", "Fed USD swap lines", "Đường hoán đổi USD của Fed",
            "S", 0.06, 0.28, Provenance.BOOK_STATED, Evidence.SUPPORTED, emergent=True,
            note="The only supply channel that can be opened deliberately and quickly."),
    Channel("ext", "S_ext", "External balance-of-payments flows", "Dòng cán cân thanh toán",
            "S", 0.21, 0.18, Provenance.BOOK_STATED, Evidence.PARTIAL,
            note="Enters as S_ext * exp(-delta_off * S_off)  (ISSUES #28, log-safe)."),
    Channel("crypto", "S_crypto", "Synthetic USD supply", "Nguồn cung USD tổng hợp (DeFi)",
            "S", 0.03, 0.03, Provenance.ENGINE_CONVENTION, Evidence.UNTESTED, emergent=True,
            note="Twin of D_net on the supply side; same measurement problem."),
]

CHANNELS: Dict[str, Channel] = {c.key: c for c in DEMAND + SUPPLY}
CHANNELS[D_PREC.key] = D_PREC


# --------------------------------------------------------------------------- #
# Weights (Layer W)
# --------------------------------------------------------------------------- #

@dataclass
class Weight:
    """A tunable coefficient, with the zone it may move in.

    lo/hi are the ADMISSIBLE range: the interval over which the book's own
    bounds and positivity constraints still hold.  The bounded weight map of
    E17 keeps every weight strictly inside (lo, hi) whatever the interaction
    terms do, so no interaction can push a weight out of its zone.
    """
    key: str
    symbol: str
    block: str
    name_vi: str
    base: float
    lo: float
    hi: float
    provenance: Provenance
    evidence: Evidence = Evidence.UNTESTED
    note: str = ""
    # z-drivers this weight responds to, and the strength of the response.
    # gamma[driver] is the linear loading; see E17.
    gamma: Dict[str, float] = field(default_factory=dict)
    # Second-order terms: gamma2[(driver_a, driver_b)] is the product loading.
    gamma2: Dict[Tuple[str, str], float] = field(default_factory=dict)

    def span(self) -> float:
        return self.hi - self.lo

    def u0(self) -> float:
        """Base position inside the zone, in (0, 1)."""
        s = self.span()
        if s <= 0:
            return 0.5
        return min(max((self.base - self.lo) / s, 1e-9), 1 - 1e-9)


# The modulator state vector z.  Every entry is in [0, 1], which is what makes
# a loading comparable across weights (the book's Notation convention 3).
Z_DRIVERS: Dict[str, str] = {
    "sigma":  "σ_sys — systemic instability index (Layer 1)",
    "phi":    "Φ_sys / Φ_max — shelter credibility, normalised (Layer 2)",
    "sus":    "s_US,sys — share of flight-to-quality the dollar captures (Layer 2)",
    "hsoc":   "H_soc — homogeneity of collective belief (Layer 4)",
    "iimp":   "I_imp — impulse efficiency (Layer 4)",
    "fhard":  "f_hard — accumulated hard drivers (Layer 5)",
    "rus":    "R_US — internal U.S. risk (Layer 2)",
    "psi":    "1 − Ψ_str — structural integrity already lost (Layer 5)",
}


def _W(*args, **kw) -> Weight:
    return Weight(*args, **kw)


WEIGHTS: Dict[str, Weight] = {w.key: w for w in [

    # ---- E3 : the state variable ----------------------------------------- #
    _W("w_sigma", "w_σ", "E3 · σ_sys", "Trọng số khối stress thị trường (VIX/MOVE)",
       1.00, 0.00, 3.00, Provenance.BOOK_STATED, Evidence.UNTESTED,
       note="Assumption 5.2 sets it to 1 as a stated convention. §17.8 item one is to "
            "estimate it. After the rank transform the weights are the ONLY thing that "
            "sets relative influence (§5.5.4)."),
    _W("w_X", "w_X", "E3 · σ_sys", "Trọng số cú sốc ngoại sinh (địa chính trị)",
       1.00, 0.00, 2.50, Provenance.BOOK_STATED, Evidence.REFUTED,
       note="At w_X = 1 a newspaper count outweighs the entire market block. The chain "
            "X_pand ⇒ σ_sys ⇒ DXY failed in three independent episodes (§17.3): the most "
            "replicated negative result in the book.",
       # ADDED (E23): the geopolitical leg moves at headline frequency — AR(1) 0.503
       # against 0.97+ for the market legs.  Its weight is scaled down at short horizons.
       gamma={"sigma": -0.40}),
    _W("w_F", "w_F", "E3 · σ_sys", "Trọng số ma sát thanh khoản liên thị trường",
       1.00, 0.00, 3.00, Provenance.BOOK_STATED, Evidence.SUPPORTED,
       note="The funding leg regresses on the dollar at t = +5.04 while the geopolitical "
            "leg gives t = -0.19. The composite performs worse than its own friction "
            "component (Table 11.6).",
       gamma={"sigma": 0.35}),
    _W("w_H", "w_H", "E3 · σ_sys", "Trọng số cú sốc phi quân sự (dịch bệnh, hạ tầng)",
       0.50, 0.00, 2.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED,
       note="ADDED. §5.5.3: GPRD measures war and terrorism, so 2020 — the clearest "
            "non-financial shock in the sample — gains nothing from the X_pand leg. "
            "'The single most valuable data addition remaining for this layer.'"),

    # ---- E4 : shelter credibility ---------------------------------------- #
    _W("phi_0", "φ_0", "E4 · Φ_sys", "Hệ số chặn của độ tin cậy nơi trú ẩn",
       0.192, 0.00, 1.50, Provenance.OPEN, Evidence.UNTESTED,
       note="Base chosen so that Φ_sys = 0.70 at the Table 10.3 baseline state, which "
            "is the value §10.7.3 starts its trust shock from. The coefficient itself "
            "is OPEN."),
    _W("phi_G", "φ_G", "E4 · Φ_sys", "Hệ số sức mạnh địa chính trị",
       0.50, 0.00, 1.50, Provenance.BOOK_STATED, Evidence.UNTESTED,
       note="0.5 is the original's CS7 assumption, retained and labelled.",
       # E15b is a logistic derivative: s(1-s) is 0.25 at s = 0.5 and 0.09 at s = 0.9.
       # Military capability buys less for a dominant currency than a contested one.
       gamma2={("sus", "sus"): -0.50}),
    _W("phi_R", "φ_R", "E4 · Φ_sys", "Hệ số rủi ro nội tại nước Mỹ",
       0.40, 0.00, 1.50, Provenance.OPEN, Evidence.PARTIAL,
       note="§6.8: R_US becomes explosive when the psycho-technical layer amplifies it — "
            "an interaction an affine Φ_sys cannot represent. The engine puts it here, in "
            "the weight, rather than adding a term to E4.",
       gamma={"hsoc": 0.60}),
    _W("phi_M", "φ_M", "E4 · Φ_sys", "Hệ số niềm tin thể chế",
       0.55, 0.00, 1.50, Provenance.OPEN, Evidence.UNTESTED,
       note="Sign corrected to POSITIVE by ISSUES #1."),
    _W("phi_T", "φ_T", "E4 · Φ_sys", "Hệ số phân mảnh địa chính trị",
       0.35, 0.00, 1.50, Provenance.OPEN, Evidence.UNTESTED),

    # ---- E5 : the safe-flow share ---------------------------------------- #
    _W("gam_0", "γ_0", "E5 · s_US", "Hệ số chặn của logistic thị phần trú ẩn",
       0.70, -2.00, 3.00, Provenance.OPEN, Evidence.UNTESTED,
       note="Base chosen so that s_US,sys = 0.70 at the baseline state — the value "
            "Table 10.3 states and CS7 assumes. The coefficient itself is OPEN."),
    _W("gam_G", "γ_G", "E5 · s_US", "Hệ số G_pol trong thị phần trú ẩn",
       1.00, 0.00, 3.00, Provenance.BOOK_STATED, Evidence.UNTESTED,
       note="1.0 assumed in CS7."),
    _W("gam_R", "γ_R", "E5 · s_US", "Hệ số R_US trong thị phần trú ẩn",
       0.80, 0.00, 3.00, Provenance.OPEN, Evidence.UNTESTED),
    _W("gam_E", "γ_E", "E5 · s_US", "Hệ số kỳ vọng lạm phát",
       0.60, 0.00, 3.00, Provenance.OPEN, Evidence.UNTESTED),
    _W("gam_T", "γ_T", "E5 · s_US", "Hệ số phân mảnh trong thị phần trú ẩn",
       0.50, 0.00, 3.00, Provenance.OPEN, Evidence.UNTESTED),

    # ---- E6 : reflexive acceleration ------------------------------------- #
    _W("kappa_base", "κ_base", "E6 · κ_sys", "Độ lồi nền (đòn bẩy cấu trúc)",
       0.90, 0.10, 2.00, Provenance.BOOK_STATED, Evidence.UNIDENTIFIED,
       note="An error in κ_base propagates into every elasticity at once (§10.7.5)."),
    _W("a_V", "a_V", "E6 · κ_sys", "Hệ số vận tốc truyền sốc",
       0.10, 0.00, 1.50, Provenance.ENGINE_CONVENTION, Evidence.UNIDENTIFIED,
       note="Table 10.3 states five of κ_sys's seven coefficients and omits this one. "
            "Set small rather than invented: the engine's baseline κ_sys then lands "
            "inside the book's own stated band (κ_sys ≈ 1.2-2.0 across the runs) "
            "without claiming to reproduce its exact 1.22."),
    _W("a_M", "a_M", "E6 · κ_sys", "Hệ số ký ức khủng hoảng",
       0.10, 0.00, 1.50, Provenance.ENGINE_CONVENTION, Evidence.UNIDENTIFIED,
       note="Omitted by Table 10.3; see a_V. The countervailing channel of §7.6.2: V_meme raises λ_f, which lowers "
            "M_shock, which lowers κ_sys — the opposite sign to a_H and a_I. The book "
            "records it as an open sign; here it is computable.",
       gamma={"hsoc": -0.45}),
    _W("a_A", "a_A", "E6 · κ_sys", "Hệ số siêu phản thân (meta-reflexivity)",
       0.10, 0.00, 1.50, Provenance.ENGINE_CONVENTION, Evidence.UNIDENTIFIED,
       note="Omitted by Table 10.3; see a_V."),
    _W("a_sigma", "a_σ", "E6 · κ_sys", "Hệ số stress hệ thống trong κ",
       0.60, 0.00, 1.50, Provenance.BOOK_STATED, Evidence.UNTESTED,
       note="Restored from E1 by ISSUES #3. Without it the model has no κ'(σ) > 0.",
       gamma={"hsoc": 0.50, "iimp": 0.30}),
    _W("kappa_R", "κ_R", "E6 · κ_sys", "Hệ số làm phẳng do rủi ro nội tại Mỹ",
       0.30, 0.00, 0.95, Provenance.BOOK_STATED, Evidence.UNIDENTIFIED,
       note="Assumption 7.2 needs κ_R < 1, enforced by the zone. Proposition 13.2: "
            "permanently unidentified — more episodes do not fix it."),
    _W("a_H", "a_H", "E6 · κ_sys", "Hệ số đồng nhất hoá niềm tin",
       0.50, 0.00, 2.00, Provenance.BOOK_STATED, Evidence.UNIDENTIFIED,
       note="Additive-one form by ISSUES #3a, so diversity dampens transmission rather "
            "than annihilating it."),
    _W("a_I", "a_I", "E6 · κ_sys", "Hệ số tức thời của xung hành động",
       0.40, 0.00, 2.00, Provenance.BOOK_STATED, Evidence.UNIDENTIFIED),

    # ---- Safe-haven exponential ------------------------------------------ #
    _W("lam_1", "λ_1", "Trú ẩn", "Hệ số tuyến tính của số hạng trú ẩn",
       0.08, -0.25, 0.25, Provenance.BOOK_STATED, Evidence.REFUTED,
       note="Proposition 10.3: the smile requires λ_1 < 0. Not one of 452 specifications "
            "gives a calm-regime slope negative and distinguishable from zero. Remark 11.3: "
            "λ_1 takes opposite signs in the two regimes when estimated separately — which "
            "is what the regime-switched form E21 represents.",
       gamma={"sigma": 0.60}),
    _W("lam_2", "λ_2", "Trú ẩn", "Hệ số bậc hai (độ lồi) của số hạng trú ẩn",
       0.15, 0.00, 0.45, Provenance.BOOK_STATED, Evidence.PARTIAL,
       note="I37: a convex term in a bounded variable delivers its largest increments in "
            "the middle of the range, and every scored episode but one begins with σ_sys "
            "already high. E22 re-centres it on the entry state."),
    _W("alpha_prec", "α_prec", "Trú ẩn", "Độ co giãn của cầu trú ẩn",
       0.15, 0.00, 0.60, Provenance.BOOK_STATED, Evidence.PARTIAL,
       gamma={"sigma": 0.70}),

    # ---- Regime switch ---------------------------------------------------- #
    _W("sigma_star", "σ*", "Λ(σ) · chuyển chế độ", "Ngưỡng chuyển chế độ dùng chung",
       0.55, 0.05, 0.95, Provenance.OPEN, Evidence.UNTESTED,
       note="Shared across all seventeen elasticities: regimes are a property of the "
            "system, not of each channel separately."),
    _W("theta", "θ", "Λ(σ) · chuyển chế độ", "Độ dốc chuyển chế độ dùng chung",
       8.00, 1.00, 40.00, Provenance.OPEN, Evidence.UNTESTED),

    # ---- E8 : structural integrity --------------------------------------- #
    _W("L_max", "L_max", "E8 · Ψ_str", "Mức mất tối đa của tính toàn vẹn cấu trúc",
       0.35, 0.01, 1.00, Provenance.BOOK_STATED, Evidence.UNTESTED,
       note="A claim about the world, not a nuisance parameter: L_max = 1 permits total "
            "collapse; L_max < 1 posits an irreducible floor of dollar demand."),
    _W("theta_0", "θ_0", "E8 · Ψ_str", "Ngưỡng tích luỹ của các động lực cứng",
       0.50, 0.05, 0.95, Provenance.BOOK_STATED, Evidence.UNTESTED,
       note="Assumption 9.2 holds the threshold fixed against the narrative layer. §9.8 "
            "calls that the most consequential place the chapter follows the original. "
            "The loading below is the departure, and it is zero by default.",
       gamma={"hsoc": 0.0}),
    _W("k_psi", "k_Ψ,base", "E8 · Ψ_str", "Tốc độ xói mòn cấu trúc (giá trị nền)",
       6.00, 0.50, 60.00, Provenance.BOOK_STATED, Evidence.UNTESTED,
       note="The BASELINE erosion speed. k_Ψ itself is k_Ψ(H_soc, V_meme, I_imp), and "
            "that state dependence lives in layers.k_psi_fn where the book puts it — "
            "this weight carries no state loading of its own, or the narrative layer "
            "would enter the erosion speed twice. In the narrative shock of §10.7.4 "
            "k_Ψ goes 6 → 28 with no demand or supply channel moving at all; the engine "
            "reproduces that through k_psi_fn, not through this weight."),

    # ---- Aggregators the book names but never specifies ------------------ #
    _W("w_Calt", "w_C", "f_hard (ADDED)", "Trọng số hạ tầng thay thế trong f_hard",
       0.55, 0.00, 1.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED,
       note="ADDED. Assumption 9.1 says C_alt and T_frag enter only through a scalar "
            "f_hard = f(C_alt, T_frag) increasing in both — and never gives f. E24 does."),
    _W("w_Tfrag", "w_T", "f_hard (ADDED)", "Trọng số phân mảnh trong f_hard",
       0.45, 0.00, 1.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED),
    _W("w_CT", "w_CT", "f_hard (ADDED)", "Hệ số tương tác C_alt × T_frag",
       0.25, -1.00, 1.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED,
       note="Sub-additive by default: fragmentation without an exit route accumulates "
            "pressure that the dollar still absorbs."),
    _W("w_gold", "w_Au", "f_hard (ADDED)", "Trọng số thay thế dự trữ bằng vàng trong C_alt",
       0.40, 0.00, 1.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED,
       note="ADDED. §17.6.3 — the one rescue hypothesis that survived its own test: "
            "reserve-asset substitution into gold belongs in C_alt and is currently "
            "outside it. A C_alt that counts only payment rails measures the wrong exit."),
    _W("delta_off", "δ_off", "E9 · S_ext", "Hệ số suy giảm do trừng phạt",
       0.80, 0.00, 3.00, Provenance.OPEN, Evidence.PARTIAL,
       note="Log-safe form by ISSUES #28: S_ext * exp(-δ_off S_off)."),
    _W("r_rev", "r_rev", "Đảo chiều (ADDED)", "Tốc độ đảo chiều cưỡng chế",
       0.00, 0.00, 1.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED,
       note="ADDED, closing I34. The sign graph contains no arrow that lowers S_off or "
            "T_frag, so the model has no representation of coercion that ends coercion. "
            "Zero by default: switching it on is a departure from the book."),
    _W("b_F", "b_F", "Đường về Layer 5→4 (ADDED)", "Hệ số kích hoạt tự sự từ động lực cứng",
       0.00, 0.00, 2.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED,
       note="ADDED, closing I32. The term (1 + b_F f_hard) on E8.2 is the one the book "
            "writes out and declines to add, because it would be an eighth inestimable "
            "parameter. Zero by default; the omission is recoverable by setting it."),
    _W("theta_sub", "Θ_sub", "Hạ tầng số (ADDED)", "Ngưỡng sự cố hạ tầng thành sự kiện tiền tệ",
       0.65, 0.05, 1.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED,
       note="ADDED, closing I36. CS8 states no magnitude at which a substrate failure "
            "becomes monetary, so no outage can refute the scenario and none can "
            "calibrate it. Stating the threshold makes the scenario refutable."),
    _W("w_prec_short", "w_2y", "D_prec (ADDED)", "Tỉ trọng đầu ngắn của đường cong trú ẩn",
       0.65, 0.00, 1.00, Provenance.ENGINE_CONVENTION, Evidence.ADDED,
       note="ADDED, closing I40. D_prec is one scalar for a whole curve; the two-year "
            "keeps the haven property the thirty-year has lost."),
]}


# --------------------------------------------------------------------------- #
# Latent modulators (Layers 2–5), with their measurement standing
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Latent:
    key: str
    symbol: str
    name_vi: str
    default: float
    layer: Layer
    measurement: str


LATENTS: Dict[str, Latent] = {l.key: l for l in [
    Latent("G_pol", "G_pol", "Sức mạnh địa chính trị", 0.70, Layer.STRUCTURAL,
           "Tier 3. No aggregator over three capacities; CS7 and CS10 apply "
           "incompatible measurement rules (ISSUES #33)."),
    Latent("R_US", "R_US", "Rủi ro nội tại nước Mỹ", 0.20, Layer.STRUCTURAL,
           "Latent; scale fixed to [0,1] by ISSUES #26. Protocol OPEN."),
    Latent("M_trust", "M_trust", "Niềm tin thể chế", 0.70, Layer.STRUCTURAL,
           "Latent. Inflation enters through it (ISSUES #25)."),
    Latent("T_frag", "T_frag", "Phân mảnh địa chính trị", 0.42, Layer.STRUCTURAL,
           "Substitute only: BIS triennial FX turnover. ~180 free SWIFT PDFs "
           "would close it."),
    Latent("E_inf", "E_inf", "Kỳ vọng lạm phát", 0.30, Layer.STRUCTURAL,
           "Observable: T5YIFR, MICH."),
    Latent("H_cap", "H_cap", "Tồn kho vốn con người và IP", 0.75, Layer.STRUCTURAL,
           "Latent stock; h(H_cap) maps it to the D_hcap flow (ISSUES #24)."),
    Latent("C_alt", "C_alt", "Hạ tầng thanh toán thay thế", 0.32, Layer.SECULAR,
           "Must be built, and built wider than the original defines it "
           "(§17.8 item three)."),
    Latent("V_USD", "V_USD", "Vận tốc truyền sốc", 0.60, Layer.REFLEXIVE,
           "Constructible from GDELT; the better measure needs intraday data."),
    Latent("M_shock", "M_shock", "Ký ức khủng hoảng", 0.45, Layer.REFLEXIVE,
           "Computed from E11–E14 given the crisis set Ω."),
    Latent("A_meta", "A_meta", "Siêu phản thân", 0.40, Layer.REFLEXIVE,
           "Latent; no series."),
    Latent("A_alg", "A_alg", "Cường độ khuếch đại thuật toán", 0.60, Layer.PSYCHO,
           "One of nine Layer-4 variables with zero series."),
    Latent("C_src", "C_src", "Tập trung nguồn nội dung", 0.65, Layer.PSYCHO,
           "Constructible."),
    Latent("P_AI", "P_AI", "Mức thâm nhập của AI tạo sinh", 0.55, Layer.PSYCHO,
           "No series."),
    Latent("T_exp", "T_exp", "Chỉ số thời lượng phơi nhiễm", 0.70, Layer.PSYCHO,
           "No series."),
    Latent("R_div", "R_div", "Sức kháng đa dạng còn lại", 0.3275, Layer.PSYCHO,
           "No series. The defensive variable of the layer. This value, with the "
           "c_L0 and c_L1 of Options, is what makes Table 10.3's stated baseline "
           "H_soc = I_imp = 0.30 an actual fixed point of Equation (8.8) rather than "
           "an imposed pair — see layers.implied_layer4."),
    Latent("S_access", "S_access", "Tốc độ tiếp cận (nghĩ → bấm)", 0.80, Layer.PSYCHO, "No series."),
    Latent("R_fric", "R_fric", "Ma sát kháng cự (nghi ngờ, xác nhận)", 0.40, Layer.PSYCHO, "No series."),
    Latent("P_habit", "P_habit", "Cường độ thói quen được lập trình", 0.65, Layer.PSYCHO, "No series."),
    Latent("E_sys", "E_sys", "Mức gắn kết hệ sinh thái", 0.70, Layer.PSYCHO, "No series."),
    Latent("S_off", "S_off", "Cường độ trừng phạt / phong toả tài sản", 0.15, Layer.MECHANICAL,
           "No series; frozen-reserve estimates, OFAC."),
    Latent("Au_sub", "Au_sub", "Thay thế dự trữ bằng vàng (ADDED)", 0.38, Layer.SECULAR,
           "ADDED. World Bank gold price and reserves incl./excl. gold; both free, both held."),
    Latent("X_health", "X_health", "Cú sốc ngoại sinh phi quân sự (ADDED)", 0.00, Layer.STATE,
           "ADDED. The X_pand proxy (GPRD) covers war and terrorism only."),
]}


# --------------------------------------------------------------------------- #
# Structural constraints — the feasible zone
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Constraint:
    key: str
    label_vi: str
    source: str


CONSTRAINTS: List[Constraint] = [
    Constraint("kappa_R_lt_1", "κ_R < 1 để κ_sys > 0", "Assumption 7.2"),
    Constraint("phi_pos", "Φ_sys > 0 trên vùng tham số", "Assumption 2.5 / §6.6.5"),
    Constraint("contraction", "η·κ_A·g_1 < 4 — điểm bất động Layer 4 là duy nhất", "Proposition 8.2"),
    Constraint("admissible_g", "g_0 ≥ 0 và g_0 + g_1 ≤ 1", "Assumption 8.3"),
    Constraint("weight_contraction", "max_k Σ_j |C_kj| < 4 — hệ trọng số hội tụ", "ADDED, E19"),
    Constraint("sigma_bounds", "σ_sys ∈ [0,1]", "Assumption 2.2 / ISSUES #9"),
    Constraint("psi_floor", "Ψ_str ∈ [1 − L_max, 1]", "ISSUES #14"),
    Constraint("smile", "λ_1 < 0 < λ_2 để có nụ cười đô la", "Proposition 10.3"),
]
