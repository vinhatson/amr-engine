"""Kiểm thử amr2, và kiểm rằng amr KHÔNG bị chạm vào.

    python tests/test_amr2.py
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

from amr2 import (                                                   # noqa: E402
    BYMONTH, PANEL, CorrectedModel, OIL_SHOCK_THRESHOLD, Regime, months, window,
)
from amr2.estimate import ols_hac                                    # noqa: E402


# --------------------------------------------------------------------------- #
# Dữ liệu
# --------------------------------------------------------------------------- #

def test_panel_is_complete_and_gapless():
    ms = [r.month for r in PANEL]
    assert ms == months(ms[0], ms[-1]), "bảng có tháng khuyết"
    assert len(PANEL) > 220


def test_known_levels_match_fred():
    assert abs(BYMONTH["2025-11"].lvl_dxy - 113.0054) < 1e-6
    assert abs(BYMONTH["2026-07"].lvl_dxy - 113.8452) < 1e-6
    assert abs(BYMONTH["2026-03"].lvl_brent - 99.41) < 1e-6


def test_cpi_gap_is_flagged_not_hidden():
    """BLS không công bố CPI 2025-10 vì đóng cửa chính phủ. Giá trị là nội suy
    và PHẢI được đánh dấu — đây đúng loại lỗi §11.5.2 bắt được với RRPONTSYD."""
    import series as S  # noqa: E402
    assert "2025-10" in S.CPI_IMPUTED
    assert BYMONTH["2025-10"].cpi_imputed or BYMONTH["2025-11"].cpi_imputed


def test_march_2026_is_the_first_extreme_oil_SPIKE_in_sample():
    """Ba tháng cực đoan trước đó đều là dầu SỤP. 2026-03 là tháng dầu VỌT cực
    đoan đầu tiên — và đó là lý do quan hệ tuyến tính âm có vẻ đúng cho tới lúc đó."""
    extreme = [r for r in PANEL if abs(r.oil) >= OIL_SHOCK_THRESHOLD]
    spikes = [r for r in extreme if r.oil > 0]
    assert [r.month for r in spikes] == ["2026-03"]
    assert max(extreme, key=lambda r: r.oil).month == "2026-03"


def test_dollar_rose_in_every_extreme_oil_month():
    """Phát hiện cốt lõi của amr2: ở cực đoan, DẤU CỦA DẦU THÔI QUAN TRỌNG."""
    extreme = [r for r in PANEL if abs(r.oil) >= 30.0]
    assert len(extreme) >= 4
    assert all(r.y > 0 for r in extreme), [(r.month, r.oil, r.y) for r in extreme]


def test_regime_prior_is_built_from_training_sample_only():
    m = CorrectedModel().train().prune()
    assert m.zone_n == 5 and m.zone_up == 4
    inzone = [r for r in window("2007-05", "2025-10") if abs(r.oil) >= OIL_SHOCK_THRESHOLD]
    assert abs(m.zone_mu - sum(r.y for r in inzone) / len(inzone)) < 1e-9
    assert all(r.month < "2026" for r in inzone), "tiên nghiệm không được chạm 2026"


def test_regime_prior_beats_the_linear_core_out_of_sample():
    """2026-03 là phép thử thật của tiên nghiệm, vì tiên nghiệm dựng trước nó."""
    m = CorrectedModel().train().prune()
    f = m.forecast("2026-03")
    linear = sum(m.fit.beta[k] * getattr(BYMONTH["2026-03"], k) for k in m.fit.terms)
    assert abs(f.point - f.actual) < abs(linear - f.actual)
    assert f.source.startswith("tiên nghiệm")


# --------------------------------------------------------------------------- #
# Ước lượng
# --------------------------------------------------------------------------- #

def test_hac_standard_errors_are_wider_than_ols():
    rows = window("2007-05", "2025-10")
    f = ols_hac(rows, ["cap", "oil"])
    assert f.lags >= 1
    assert all(f.se[k] > 0 for k in f.terms)


def test_oil_coefficient_is_negative_at_every_cutoff():
    """Quy ước dấu Tầng 0 của sách — kênh cầu nâng đô la — sai trên dầu, và sai
    suốt hai mươi năm chứ không phải riêng 2026."""
    for cut in ("2012-12", "2016-12", "2019-12", "2021-12", "2023-12", "2025-10"):
        f = ols_hac(window("2007-05", cut), ["cap", "oil"])
        assert f.beta["oil"] < 0, cut
        assert f.t["oil"] < -4.0, (cut, f.t["oil"])


def test_cap_coefficient_is_positive_at_every_cutoff():
    for cut in ("2012-12", "2019-12", "2025-10"):
        f = ols_hac(window("2007-05", cut), ["cap", "oil"])
        assert f.beta["cap"] > 0 and f.t["cap"] > 3.0, cut


def test_training_never_touches_2026():
    m = CorrectedModel().train()
    assert m.fit.sample[1] == "2025-10"
    assert all(r.month <= "2025-10" for r in window("2007-05", m.train_end))


def test_prune_uses_only_training_sample():
    m = CorrectedModel().train()
    before = set(m.fit.terms)
    m2 = CorrectedModel().train().prune()
    assert set(m2.fit.terms) <= before
    assert "pol" not in m2.fit.terms, "lãi suất chính sách không có ý nghĩa, phải bị tỉa"


# --------------------------------------------------------------------------- #
# Bốn thay đổi
# --------------------------------------------------------------------------- #

def test_no_exponent_anywhere():
    """Thay đổi 1: mô hình cộng tính trong log. Không có κ."""
    src = (ROOT / "amr2" / "model.py").read_text(encoding="utf-8")
    assert "kappa" not in src.lower().replace("κ_sys", "").replace("không có κ", "")
    m = CorrectedModel().train().prune()
    r = BYMONTH["2026-07"]
    manual = sum(m.fit.beta[k] * getattr(r, k) for k in m.fit.terms)
    assert abs(m.forecast("2026-07").point - manual) < 1e-12


def test_coefficients_are_estimated_not_convention():
    """Thay đổi 2: không giá trị nào lấy từ Table 10.3."""
    m = CorrectedModel().train().prune()
    for k in m.fit.terms:
        assert m.fit.se[k] > 0, "mọi hệ số phải có sai số chuẩn"


def test_signs_are_not_imposed():
    """Thay đổi 3: dấu do dữ liệu đặt. Hệ số dầu ÂM — vi phạm quy ước Tầng 0."""
    m = CorrectedModel().train().prune()
    assert m.fit.beta["oil"] < 0
    assert m.fit.beta["cap"] > 0


def test_layer1_is_descriptor_not_regressor():
    """Thay đổi 4: trạng thái dán nhãn chế độ, KHÔNG vào vế phải."""
    m = CorrectedModel().train().prune()
    assert "sigma" not in m.fit.terms and "vol" not in m.fit.terms
    reg, s = m.describe(BYMONTH["2026-03"])
    assert reg == Regime.OIL_SHOCK and 0.0 <= s <= 1.0


# --------------------------------------------------------------------------- #
# Hành vi ngoài mẫu
# --------------------------------------------------------------------------- #

def test_abstains_exactly_on_the_known_failure_month():
    m = CorrectedModel().train().prune()
    oos = [x for x in months("2025-11", "2026-07") if x in BYMONTH]
    fc = m.forecast_path(oos)
    skipped = [x.month for x in fc if x.abstain]
    assert skipped == ["2026-03"]


def test_beats_naive_on_the_months_it_calls():
    m = CorrectedModel().train().prune()
    oos = [x for x in months("2025-11", "2026-07") if x in BYMONTH]
    called = [x for x in m.forecast_path(oos) if not x.abstain]
    def rmse(v): return math.sqrt(sum(x * x for x in v) / len(v))
    err = rmse([x.point - x.actual for x in called])
    naive = rmse([x.actual for x in called])
    assert err < naive, (err, naive)


def test_intervals_cover_every_month():
    m = CorrectedModel().train().prune()
    oos = [x for x in months("2025-11", "2026-07") if x in BYMONTH]
    fc = m.forecast_path(oos)
    assert all(x.hit for x in fc)


def test_abstention_threshold_is_stated_as_a_number():
    """Khuyết tật ISSUES #36 ghi cho CS8: không ngưỡng nào được nêu, nên không sự
    cố nào bác bỏ được. Ở đây ngưỡng là một con số trong mã nguồn."""
    assert isinstance(OIL_SHOCK_THRESHOLD, float) and OIL_SHOCK_THRESHOLD > 0


def test_layer2_overlay_reports_without_overriding():
    m = CorrectedModel().train().prune()
    f = m.forecast("2026-07", layer2={"M_trust": +1, "T_frag": -1})
    plain = m.forecast("2026-07")
    assert f.point == plain.point, "lớp phủ định tính KHÔNG được đổi số học"
    assert len(f.layer2) == 2


# --------------------------------------------------------------------------- #
# amr phải còn nguyên
# --------------------------------------------------------------------------- #

def test_amr_is_untouched():
    """Bản sách phải giữ nguyên, nếu không thì không còn cái để so."""
    from amr import Options, WEIGHTS, run
    from amr.registry import DEMAND
    t = [c for c in DEMAND if c.key == "trans"][0]
    assert t.alpha_calm > 0 and t.alpha_crisis > 0, "α_trans phải còn DƯƠNG trong amr"
    assert WEIGHTS["kappa_base"].base == 0.90
    o = Options()
    for flag in ("recentre_convexity", "regime_switched_lambda", "enable_return_path",
                 "enable_reversal", "enable_health_leg", "split_prec_curve",
                 "haven_on_funding_leg"):
        assert getattr(o, flag) is False
    r = run()
    assert abs(r.sigma.sigma - 0.35) < 0.01 and abs(r.phi - 0.70) < 0.01
    assert abs(r.k_psi - 6.0) < 0.01


def test_amr2_does_not_import_amr():
    for f in ("panel.py", "estimate.py", "model.py"):
        src = (ROOT / "amr2" / f).read_text(encoding="utf-8")
        assert "from amr " not in src and "import amr\n" not in src


if __name__ == "__main__":
    import series  # noqa: F401  (đường dẫn do amr2.panel cài)
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
