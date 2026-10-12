"""Kiểm thử amr3 — và kiểm rằng amr, amr2 đều KHÔNG bị chạm vào.

    python tests/test_amr3.py
"""

import math
import sys

# --- UTF-8 console (Windows cp1252 would otherwise abort on the first
#     Vietnamese or Greek character printed below) ---
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):      # non-TTY or already wrapped
        pass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amr import Options, WorldState, run                              # noqa: E402
from amr.registry import CHANNELS, D_PREC, LATENTS, WEIGHTS           # noqa: E402
from amr3 import (                                                    # noqa: E402
    ATLAS, H_STAR, PARAMS, TAU_CEILING, TAU_CEILING_BY_MODE, Manifold, Memory,
    Move, Options3, Role, Sheet, Transversality, commutator, cross_sheet_edges,
    holonomy, residual, tautness, trace, unmeasured,
)
from amr3.atlas import position_weight                                # noqa: E402


def _meme(amp=0.95, dt=1.0):
    d = 1.0 - amp
    return Move(f"MEME({amp:.2f})", Sheet.PSYCHO,
                latents=(("A_alg", amp), ("C_src", amp), ("P_AI", amp),
                         ("T_exp", amp), ("S_access", amp), ("P_habit", amp),
                         ("E_sys", amp), ("R_div", d), ("A_meta", amp)), dt=dt)


def _episode(mode, amp, steps, dt, tau=None):
    """Một đợt: giữ cú sốc ở `amp` trong tổng thời lượng steps·dt."""
    o = Options3(tv=Transversality.knife(TAU_CEILING_BY_MODE[mode.value]
                                         if tau is None else tau), memory=mode)
    m = Manifold(opt=o)
    m.step(None)
    for _ in range(steps):
        m.step(_meme(amp, dt))
    m.step(HARD)
    m.step(None)
    return m.sheets[Sheet.SECULAR].scar


HARD = Move("CỨNG", Sheet.SECULAR,
            latents=(("C_alt", 0.62), ("T_frag", 0.70), ("Au_sub", 0.60)))
MEME = _meme(0.95)
BAND = _meme(0.80)          # trong dải không giao hoán
KNIFE = Transversality.knife()          # trần suy từ dữ liệu, dạng mặc định
OVER  = Transversality.knife(1.0)       # ngoài vùng, giữ để kiểm nhãn


# --------------------------------------------------------------------------- #
# Bản đồ — không biến nào bị thêm, không biến nào bị bỏ
# --------------------------------------------------------------------------- #

def test_atlas_covers_every_amr_variable_exactly_once():
    """Yêu cầu là 'giữ đầy đủ biến, chỉ khác phân phối'. Đây là chỗ kiểm nó."""
    expected = set(WEIGHTS) | set(LATENTS) | set(CHANNELS) | {D_PREC.key}
    assert set(ATLAS) == expected, (expected - set(ATLAS), set(ATLAS) - expected)
    assert len(ATLAS) == 78


def test_every_variable_has_exactly_one_sheet_and_one_role():
    for k, a in ATLAS.items():
        assert isinstance(a.sheet, Sheet) and isinstance(a.role, Role), k


def test_no_cross_sheet_edge_is_invented():
    """Tập cạnh phải lấy NGUYÊN từ `gamma` của amr, không thêm cạnh nào."""
    from_amr = set()
    for k, w in WEIGHTS.items():
        for src in (w.gamma or {}):
            from_amr.add((k, src))
    from_atlas = {(a.key, var) for a in ATLAS.values() for _, var, _ in a.pierces}
    assert from_atlas <= from_amr
    # và mỗi cạnh atlas bỏ qua phải là cạnh CÙNG tấm, không phải cạnh bị mất
    for k, src in from_amr - from_atlas:
        assert ATLAS[k].sheet is not Sheet.PSYCHO or src not in ("hsoc", "iimp")


def test_the_knife_edge_is_the_one_amr_set_to_zero():
    """Σ₄→Σ₅ là cạnh duy nhất amr để tải +0,00 — và nó là cạnh của luận điểm."""
    edges = {(s, d): load for s, d, _, _, load in cross_sheet_edges()}
    assert abs(edges[(Sheet.PSYCHO, Sheet.SECULAR)]) < 1e-15
    assert edges[(Sheet.PSYCHO, Sheet.STRUCTURAL)] > 0.5      # 4→2 thì SỐNG
    assert any(s is Sheet.PSYCHO and d is Sheet.REFLEXIVE for s, d in edges)


def test_psycho_sheet_has_no_position_weight():
    """Remark 10.2: Tầng 4 là một NGUỒN, không bị gì tác động lại.

    Một nguồn không có vị trí để bị dịch, nên nó không đâm được NGƯỢC lại.
    amr3 giữ nguyên tính một chiều đó chứ không âm thầm bỏ nó.
    """
    assert position_weight(Sheet.PSYCHO) is None
    for s in (Sheet.STATE, Sheet.STRUCTURAL, Sheet.REFLEXIVE, Sheet.SECULAR):
        assert position_weight(s) is not None, s


def test_secular_position_weight_is_theta_0():
    assert position_weight(Sheet.SECULAR) == "theta_0"
    assert ATLAS["theta_0"].role is Role.POSITION


# --------------------------------------------------------------------------- #
# Độ căng — chuẩn hoá bằng chính biên ¼ của sách
# --------------------------------------------------------------------------- #

def test_tautness_is_one_exactly_at_the_inflection():
    """II = 4Λ′, và Λ′ ≤ ¼ với dấu bằng tại 0 — cùng ¼ của Prop. 8.2."""
    assert abs(tautness(0.0) - 1.0) < 1e-12
    assert 0.0 <= tautness(5.0) < 0.1
    assert 0.0 <= tautness(-5.0) < 0.1
    for x in (-8.0, -2.0, 0.0, 2.0, 8.0):
        assert 0.0 <= tautness(x) <= 1.0 + 1e-12


def test_tautness_is_symmetric():
    for x in (0.5, 1.0, 3.0):
        assert abs(tautness(x) - tautness(-x)) < 1e-12


# --------------------------------------------------------------------------- #
# LỒNG KHÍT — τ ≡ 0 phải cho lại amr đúng chữ số máy
# --------------------------------------------------------------------------- #

def test_tau_zero_reproduces_amr_exactly():
    z = Options3(tv=Transversality.zero())
    assert abs(Manifold(opt=z).step(None).ln_DXY - run().ln_DXY) == 0.0


def test_tau_zero_leaves_no_scar_on_any_path():
    z = Options3(tv=Transversality.zero())
    for path in ([MEME, HARD], [HARD, MEME], [MEME, MEME, HARD, MEME]):
        assert trace(path, opt=z).scars() == {}


def test_tau_zero_produces_no_overrides():
    z = Options3(tv=Transversality.zero())
    for st in trace([MEME, HARD], opt=z).steps:
        assert st.overrides == {}


def test_all_three_measures_vanish_at_tau_zero():
    """Ba đại lượng bằng 0 trong amr không do hiệu chỉnh mà do LỚP HÀM."""
    z = Options3(tv=Transversality.zero())
    assert commutator(MEME, HARD, opt=z).norm == 0.0
    assert holonomy([MEME, HARD], opt=z).value == 0.0
    assert residual(MEME, opt=z).value == 0.0


def test_tau_zero_matches_amr_along_a_whole_path():
    """Không chỉ ở nền — mọi bước trên đường đi phải trùng amr."""
    z = Options3(tv=Transversality.zero())
    st = WorldState()
    for mv in (MEME, HARD):
        st = mv.apply(st)
    tj = trace([MEME, HARD], opt=z)
    assert abs(tj.ln_DXY - run(st, None, Options()).ln_DXY) < 1e-12


# --------------------------------------------------------------------------- #
# τ > 0 — ba đại lượng phải SỐNG
# --------------------------------------------------------------------------- #

def test_holonomy_is_non_zero_under_the_knife():
    """Đi một vòng KÍN rồi về đúng trạng thái đầu, và ln DXY KHÔNG về chỗ cũ."""
    h = holonomy([MEME, HARD], opt=Options3(tv=KNIFE))
    assert abs(h.value) > 1e-3
    assert not h.trivial


def test_irreversibility_under_the_knife():
    r = residual(MEME, opt=Options3(tv=KNIFE))
    assert r.value > 1e-3 and not r.reversible


def test_scar_is_monotone_non_decreasing():
    """Cơ chế duy nhất của amr3 là một dấu ≥. Kiểm chính dấu đó."""
    m = Manifold(opt=Options3(tv=KNIFE))
    seen = 0.0
    inv = None
    m.step(None)
    for mv in (MEME, HARD, MEME):
        m.step(mv)
        now = m.sheets[Sheet.SECULAR].scar
        assert now >= seen - 1e-15, (now, seen)
        seen = now
    # và gỡ sốc hoàn toàn cũng KHÔNG làm nó giảm
    m.step(MEME.inverse_of(WorldState()))
    assert m.sheets[Sheet.SECULAR].scar >= seen - 1e-15


def test_scar_and_holonomy_grow_with_tau():
    prev_scar, prev_hol = -1.0, -1.0
    for tau in (0.0, 0.1, 0.25, 0.5, 1.0):
        o = Options3(tv=Transversality.knife(tau))
        sc = trace([MEME, HARD], opt=o).final.scar(Sheet.SECULAR)
        hl = abs(holonomy([MEME, HARD], opt=o).value)
        assert sc >= prev_scar - 1e-12, tau
        assert hl >= prev_hol - 1e-12, tau
        prev_scar, prev_hol = sc, hl


def test_puncture_requires_crossing_the_threshold():
    """Dưới H* không có vết đâm nào, dù τ = 1. Ấn nhẹ thì giấy chỉ võng."""
    weak = _meme(0.70)
    tj = trace([weak, HARD], opt=Options3(tv=KNIFE))
    assert tj.final.sheets[Sheet.PSYCHO].intensity < H_STAR[Sheet.PSYCHO] + 1e-9
    assert tj.scars() == {}


# --------------------------------------------------------------------------- #
# Phát hiện: không giao hoán sống trong một DẢI
# --------------------------------------------------------------------------- #

def test_commutator_separates_the_two_memory_modes_exactly():
    """Phân biệt sắc nhất giữa hai nhánh, và nó không cần đợt dài.

    Dạng TRỄ lấy cực đại theo lịch sử. Hai thứ tự đi qua CÙNG tập trạng thái
    nên cực đại bằng nhau, nên giao hoán tử bằng 0 theo định nghĩa của toán tử
    — không phải do hiệu chỉnh. Dạng MỎI tích phân, nên thứ tự có nghĩa.

    Câu hỏi thực nghiệm tương ứng: thứ tự hai cú sốc có đổi mức thường trực
    không, khi trạng thái cuối giữ nguyên? Có → mỏi. Không → trễ.
    """
    hy = commutator(MEME, HARD, opt=Options3(tv=Transversality.knife(
        TAU_CEILING_BY_MODE["hysteresis"]), memory=Memory.HYSTERESIS))
    fa = commutator(MEME, HARD, opt=Options3(tv=Transversality.knife(
        TAU_CEILING_BY_MODE["fatigue"]), memory=Memory.FATIGUE))
    assert hy.norm == 0.0, hy.norm
    assert fa.norm > 1e-3, fa.norm


def test_hysteresis_keeps_holonomy_and_irreversibility():
    """Giao hoán tử tắt KHÔNG kéo theo hai đại lượng kia tắt.

    Vòng kín về đúng trạng thái đầu mà ln DXY không về; gỡ sốc hoàn toàn mà
    vẫn còn dư âm. Vết sẹo nằm ngoài trạng thái, nên trạng thái về được còn
    nó thì không.
    """
    o = Options3(tv=Transversality.knife(TAU_CEILING_BY_MODE["hysteresis"]),
                 memory=Memory.HYSTERESIS)
    assert abs(holonomy([MEME, HARD], opt=o).value) > 1e-3
    assert residual(MEME, opt=o).value > 1e-3


def test_non_commutativity_lives_in_a_band_not_a_half_line():
    """Ba chế độ. Chỉ chế độ giữa là chế độ luận điểm nói về.

    Dưới dải: chưa qua H*, không đâm. Trong dải: đâm, chưa bão hoà, thứ tự có
    nghĩa. Trên dải: Λ → 1, L_max chặn tổng thiệt hại, giao hoán tử SẬP.
    """
    o = Options3(tv=OVER, memory=Memory.FATIGUE)   # dải chỉ tồn tại ở nhánh mỏi
    below = commutator(_meme(0.74), HARD, opt=o).norm
    inside = commutator(_meme(0.80), HARD, opt=o).norm
    above = commutator(_meme(0.96), HARD, opt=o).norm
    assert below == 0.0
    assert inside > 1e-2
    assert above < inside / 100.0


def test_order_effect_has_one_consistent_sign_in_fatigue_mode():
    """Meme-trước đâm sâu hơn ở MỌI biên độ. Không có đảo dấu.

    Bản trước báo một đảo dấu ở Λ ≈ 0,98. Đó là TẠO TÁC của lỗi độ cong — độ
    sâu đọc II từ tấm đã bị dịch, nên thứ tự nào tạo vết sẹo sớm hơn thì tự
    thay đổi điều kiện cho bước sau. Sửa xong, dấu nhất quán.
    """
    o = Options3(tv=OVER, memory=Memory.FATIGUE)
    for amp in (0.80, 0.84, 0.88, 0.92, 0.96):
        mv = _meme(amp)
        a = trace([mv, HARD], opt=o).final.scar(Sheet.SECULAR)
        b = trace([HARD, mv], opt=o).final.scar(Sheet.SECULAR)
        assert a > b + 1e-9, (amp, a, b)


def test_saturation_is_caused_by_L_max_the_amplitude_weight():
    """Giao hoán tử sập vì L_max chặn, không vì vết sẹo thôi khác nhau.

    Ở biên cao, hai thứ tự cho vết sẹo chênh rõ rệt mà ln DXY gần trùng —
    bằng chứng rằng chặn nằm ở BIÊN ĐỘ tấm, không ở độ sâu vết đâm.
    """
    o = Options3(tv=OVER, memory=Memory.FATIGUE)
    mv = _meme(0.95)
    a = trace([mv, HARD], opt=o)
    b = trace([HARD, mv], opt=o)
    sa, sb = a.final.scar(Sheet.SECULAR), b.final.scar(Sheet.SECULAR)
    assert abs(sa - sb) > 0.05, (sa, sb)                 # vết sẹo chênh rõ
    assert abs(a.ln_DXY - b.ln_DXY) < 1e-3               # đầu ra thì không
    assert ATLAS["L_max"].role is Role.AMPLITUDE


# --------------------------------------------------------------------------- #
# Phân mảnh chính trị là ĐẦU RA
# --------------------------------------------------------------------------- #

def test_fragmentation_becomes_an_output_not_an_input():
    """'Lớp meme làm hỏng lớp cấu trúc, làm phân mảnh chính trị nếu đủ lớn.'"""
    base = trace([MEME, MEME, HARD],
                 opt=Options3(tv=Transversality.zero())).final.T_frag
    fed = trace([MEME, MEME, HARD],
                opt=Options3(tv=Transversality.full(),
                             fragmentation_feedback=True)).final.T_frag
    assert abs(base - 0.70) < 1e-9, "không phản hồi thì T_frag đúng cái đã điền"
    # Ngưỡng nhỏ hơn bản trước vì dạng trễ cho vết sẹo nhỏ hơn dạng tổng cũ —
    # đó là hệ quả của việc bỏ cộng dồn theo bước, không phải hiệu ứng yếu đi.
    assert fed > base + 0.05, (base, fed)


def test_fragmentation_feedback_is_off_by_default():
    assert Options3().fragmentation_feedback is False
    assert Options3().tv.is_zero


# --------------------------------------------------------------------------- #
# Độc lập với tốc độ — tính chất định nghĩa của toán tử trễ
# --------------------------------------------------------------------------- #

def test_scar_is_rate_independent_in_both_modes():
    """Chia cùng một đường đi thành nhiều bước hơn KHÔNG được đổi kết quả.

    Bản trước hỏng cả hai chỗ: cộng dồn theo mỗi lần gọi step() (6,3 lần trên
    20 bước), và đọc độ cong từ tấm ĐÃ BỊ DỊCH nên toán tử ăn đầu ra của chính
    nó (còn 2,1 lần kể cả ở dạng lấy cực đại). Sửa cả hai thì bằng đúng 1.
    """
    for mode in (Memory.HYSTERESIS, Memory.FATIGUE):
        ref = _episode(mode, 0.95, 1, 4.0)
        for k in (2, 4, 8, 20):
            got = _episode(mode, 0.95, k, 4.0 / k)
            assert abs(got - ref) < 1e-12, (mode, k, got, ref)


def test_hysteresis_ignores_duration_entirely():
    """Dạng trễ: chỉ cực trị của đường đi đếm. Hàng phải PHẲNG tuyệt đối."""
    ref = _episode(Memory.HYSTERESIS, 0.95, 1, 1.0)
    for T in (2.0, 4.0, 16.0, 32.0):
        assert abs(_episode(Memory.HYSTERESIS, 0.95, 1, T) - ref) < 1e-12, T


def test_fatigue_lets_duration_substitute_for_amplitude():
    """Dạng mỏi: thời lượng thay thế được biên độ, và điểm hoà vốn là một SỐ.

    Đây là mệnh đề bác bỏ được của nhánh mỏi — dạng trễ nói phép so sánh này
    không có nội dung, nên hai nhánh phân biệt được bằng dữ liệu.
    """
    short_extreme = _episode(Memory.FATIGUE, 0.95, 1, 1.0)
    prev = 0.0
    for T in (1.0, 2.0, 4.0, 8.0, 16.0, 32.0):
        now = _episode(Memory.FATIGUE, 0.80, 1, T)
        assert now > prev, T
        prev = now
    assert _episode(Memory.FATIGUE, 0.80, 1, 32.0) > short_extreme
    assert _episode(Memory.FATIGUE, 0.80, 1, 1.0) < short_extreme


def test_default_memory_is_hysteresis():
    assert Options3().memory is Memory.HYSTERESIS


def test_ceiling_depends_on_the_memory_mode():
    """Cùng ngân sách thực nghiệm, một đơn vị τ sinh ra lượng ξ khác nhau ở hai
    dạng, nên trần phải khác nhau. Một trần dùng chung sẽ là một con số sai ở
    ít nhất một nhánh."""
    assert TAU_CEILING_BY_MODE["fatigue"] < TAU_CEILING_BY_MODE["hysteresis"]
    assert TAU_CEILING == TAU_CEILING_BY_MODE[Options3().memory.value]
    assert PARAMS["tau"].hi == TAU_CEILING
    tv = Transversality.knife(0.20)
    assert tv.warnings(Memory.HYSTERESIS) == []
    assert len(tv.warnings(Memory.FATIGUE)) == 1


def test_reference_curvature_is_not_read_from_the_scarred_sheet():
    """Độ cong dùng để tính độ sâu phải đến từ cấu hình CHƯA có vết sẹo.

    Kiểm gián tiếp nhưng chặt: nếu nó đọc từ tấm đã dịch thì phép thử độc lập
    tốc độ ở trên không thể bằng 1 tới 1e-12.
    """
    m = Manifold(opt=Options3(tv=Transversality.knife(), memory=Memory.HYSTERESIS))
    m.step(None)
    m.step(_meme(0.95))          # tạo vết sẹo
    m.step(_meme(0.95))          # lần này overrides khác rỗng → tham chiếu được tính
    before = dict(m._ref_taut)
    assert before, "phải có tham chiếu một khi vết sẹo đã vào overrides"
    m.step(_meme(0.95))          # đầu vào không đổi → tham chiếu phải y hệt
    assert m._ref_taut == before, "tham chiếu phải không đổi khi đầu vào không đổi"
    # và nó phải KHÁC độ cong đọc từ tấm đã dịch, nếu không thì chẳng sửa gì
    assert any(abs(m._ref_taut[s] - m.sheets[s].taut) > 1e-9 for s in m._ref_taut)


# --------------------------------------------------------------------------- #
# Sổ sách: năm hằng số phải mang đúng bộ thông tin trọng số amr phải mang
# --------------------------------------------------------------------------- #

def test_every_amr3_constant_carries_provenance_and_a_zone():
    """Cả 39 trọng số của amr mang (base, lo, hi) + xuất xứ + bằng chứng.
    Năm hằng số của amr3 ban đầu là float trần. Đây là chỗ đóng khoảng đó."""
    assert set(PARAMS) == {"tau", "H_star", "p_depth", "q_taut", "rho_frag"}
    for k, p in PARAMS.items():
        assert p.lo <= p.base <= p.hi, k
        assert p.provenance is not None and p.evidence is not None, k
        assert len(p.note) > 20, k


def test_tau_default_is_zero_because_that_is_the_null():
    assert PARAMS["tau"].base == 0.0
    assert Options3().tv.is_zero


def test_tau_ceiling_is_stated_as_a_number_and_is_the_knife_default():
    """Trần phải là con số trong mã nguồn, không phải một câu trong README."""
    assert abs(TAU_CEILING - 0.294) < 1e-12
    assert PARAMS["tau"].hi == TAU_CEILING
    for _, _, v in Transversality.knife().active():
        assert v == TAU_CEILING


def test_out_of_zone_tau_is_labelled_not_refused():
    """Quy ước amr: cấu hình ngoài biên trả về NHÃN, không trả về lỗi."""
    assert Transversality.knife().warnings() == []
    w = Transversality.knife(1.0).warnings()
    assert len(w) == 1 and "ngoài vùng khả dụng" in w[0]
    tj = trace([MEME, HARD], opt=Options3(tv=OVER))
    assert any("ngoài vùng" in x for x in tj.final.warnings)
    assert tj.ln_DXY == tj.ln_DXY       # vẫn chạy ra số, không ném lỗi


def test_four_constants_are_labelled_as_mine_not_as_the_book_s():
    from amr.registry import Evidence, Provenance
    for k in ("H_star", "p_depth", "q_taut", "rho_frag"):
        assert PARAMS[k].provenance is Provenance.ENGINE_CONVENTION, k
        assert PARAMS[k].evidence is Evidence.UNTESTED, k
    assert PARAMS["tau"].provenance is Provenance.OPEN
    assert PARAMS["tau"].evidence is Evidence.PARTIAL


def test_hand_filled_cells_are_labelled_not_patched():
    """Câu trả lời cho 'ô đó người dùng vẫn tự điền?' — vẫn tự điền, và amr3
    không vá; nó dán nhãn để số tự điền không lẫn với số đã đo."""
    um = unmeasured()
    flat = {k for rows in um.values() for k, _ in rows}
    assert len(flat) >= 16
    for k in ("A_alg", "P_AI", "T_exp", "R_div", "S_access", "R_fric",
              "P_habit", "E_sys"):
        assert k in flat, k
    assert len(um[Sheet.PSYCHO]) >= 8
    # và chúng vẫn là CARRIER, tức toạ độ người dùng điền, không phải hệ số
    for k in flat:
        assert ATLAS[k].role is Role.CARRIER, k


# --------------------------------------------------------------------------- #
# amr và amr2 phải còn nguyên
# --------------------------------------------------------------------------- #

def test_amr_is_untouched():
    from amr.registry import DEMAND
    t = [c for c in DEMAND if c.key == "trans"][0]
    assert t.alpha_calm > 0 and t.alpha_crisis > 0
    assert WEIGHTS["kappa_base"].base == 0.90
    assert WEIGHTS["theta_0"].gamma == {"hsoc": 0.0}, "cửa phải còn khoá trong amr"
    o = Options()
    for flag in ("recentre_convexity", "regime_switched_lambda", "enable_return_path",
                 "enable_reversal", "enable_health_leg", "split_prec_curve",
                 "haven_on_funding_leg"):
        assert getattr(o, flag) is False
    r = run()
    assert abs(r.sigma.sigma - 0.35) < 0.01 and abs(r.phi - 0.70) < 0.01
    assert abs(r.k_psi - 6.0) < 0.01


def test_amr2_is_untouched():
    from amr2 import CorrectedModel, OIL_SHOCK_THRESHOLD
    assert OIL_SHOCK_THRESHOLD == 25.0
    m = CorrectedModel().train().prune()
    assert m.fit.sample[1] == "2025-10" and "pol" not in m.fit.terms


def test_amr3_mutates_nothing_in_amr_at_runtime():
    """amr3 NHẬP amr — chủ ý, và là cách chứng minh lồng khít.

    amr2 cố tình không nhập amr vì nó là mô hình KHÁC, phải đứng riêng để còn
    so được. amr3 là cùng mô hình đọc trong hệ toạ độ khác, nên nó phải chạy
    chính amr ở trong. Nhưng chạy ở trong thì phải không để lại dấu: vết sẹo
    đi qua `overrides` của một lần gọi, KHÔNG được ghi vào registry.
    """
    before_base = {k: w.base for k, w in WEIGHTS.items()}
    before_ln = run().ln_DXY

    trace([MEME, HARD], opt=Options3(tv=KNIFE, fragmentation_feedback=True))
    holonomy([MEME, HARD], opt=Options3(tv=Transversality.full()))
    residual(MEME, opt=Options3(tv=KNIFE))

    assert {k: w.base for k, w in WEIGHTS.items()} == before_base
    assert run().ln_DXY == before_ln, "amr phải cho đúng số cũ sau khi amr3 chạy"


def test_amr3_does_not_import_amr2():
    src = (ROOT / "amr3" / "model.py").read_text(encoding="utf-8")
    assert "from amr import" in src
    for line in src.splitlines():
        t = line.strip()
        if t.startswith(("import ", "from ")):
            assert "amr2" not in t, t


def test_world_state_is_never_mutated_in_place():
    """Move.apply phải trả BẢN SAO. Nếu không thì hai đường đi nhiễm nhau và
    mọi con số giao hoán tử ở trên đều vô nghĩa."""
    st = WorldState()
    snapshot = dict(st.latents)
    MEME.apply(st)
    assert dict(st.latents) == snapshot


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "data"))
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"  ok   {name}")
            except AssertionError as e:
                fails += 1; print(f"  FAIL {name}: {e}")
            except Exception as e:  # noqa: BLE001
                fails += 1; print(f"  ERR  {name}: {type(e).__name__}: {e}")
    print(f"\n{'FAILED' if fails else 'PASSED'} — {fails} lỗi")
    sys.exit(1 if fails else 0)
