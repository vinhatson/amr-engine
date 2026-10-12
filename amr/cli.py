"""
cli.py — command line.

    python -m amr list                     liệt kê các kịch bản
    python -m amr run sanctions            chạy một kịch bản, in bản đọc định tính
    python -m amr run narrative --json     cùng kết quả, dạng JSON
    python -m amr weights                  tỉ lệ trọng số tại trạng thái nền
    python -m amr tornado --top 20         vùng tuỳ biến: swing trên toàn dải
    python -m amr mc --n 1500              phân rã phương sai trên vùng khả thi
    python -m amr check                    kiểm tra ràng buộc cấu trúc
    python -m amr audit                    chạy mọi kịch bản, đối chiếu với sách
"""

from __future__ import annotations

import argparse
import json
import sys

# --- UTF-8 console (Windows cp1252 would otherwise abort on the first
#     Vietnamese or Greek character printed below) ---
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):      # non-TTY or already wrapped
        pass
from dataclasses import asdict, is_dataclass
from typing import Any, Dict

from .core import Options, WorldState, run
from .qualitative import CONVEXITY_NOTE_VI, RESIDUAL_NOTE_VI
from .registry import WEIGHTS
from .scenarios import BOOK_SANITY_CHECK, SCENARIOS, run_scenario
from .sensitivity import feasibility, interaction_residual, monte_carlo, tornado
from .weightlayer import block_shares, weight_shares
from .core import make_evaluator


def _opts(a: argparse.Namespace) -> Options:
    return Options(
        enable_state_interaction=not a.no_state,
        enable_weight_coupling=not a.no_coupling,
        recentre_convexity=a.recentre,
        regime_switched_lambda=a.regime_lambda,
        enable_return_path=a.return_path,
        enable_reversal=a.reversal,
        enable_health_leg=a.health_leg,
        split_prec_curve=a.split_prec,
        haven_on_funding_leg=a.funding_haven,
    )


def _hr(title: str) -> None:
    print()
    print(title)
    print("─" * max(len(title), 60))


def cmd_list(a) -> None:
    _hr("KỊCH BẢN")
    for k, s in SCENARIOS.items():
        print(f"  {k:<18} {s.title_vi}")
        print(f"  {'':<18} nguồn: {s.source} · chân trời {s.horizon_months} tháng")
        print(f"  {'':<18} {s.note_vi}")
        if s.book_prediction_vi:
            print(f"  {'':<18} SÁCH NÓI: {s.book_prediction_vi}")
        print()


def cmd_run(a) -> None:
    f = run_scenario(a.scenario, opt=_opts(a))
    if a.json:
        print(json.dumps({
            "scenario": a.scenario,
            "headline_pct": f.headline.pct,
            "arrow": f.headline.glyph,
            "regime": f.regime.value,
            "sigma": [f.sigma_from, f.sigma_to],
            "kappa": [f.kappa_from, f.kappa_to],
            "psi": [f.psi_from, f.psi_to],
            "blocks": {b.name: b.delta_ln for b in f.blocks},
            "dominant": f.dominant,
            "sigma_response": f.sigma_response,
            "smile_sigma": f.smile_sigma,
            "evidence_mix": f.evidence_mix,
            "warnings": f.warnings,
        }, ensure_ascii=False, indent=2))
        return

    sc = SCENARIOS[a.scenario]
    _hr(f"{sc.title_vi}   [{sc.source}]")
    print(sc.note_vi)
    if sc.book_prediction_vi:
        print(f"\nSÁCH NÓI: {sc.book_prediction_vi}")
    print()
    print(f.narrative_vi())
    print()
    print(RESIDUAL_NOTE_VI)


def cmd_weights(a) -> None:
    opt = _opts(a)
    ev = make_evaluator(WorldState(), opt)
    rows = weight_shares(ev, z={}, overrides=None)
    _hr("TỈ LỆ TRỌNG SỐ — ∂lnDXY/∂w nhân với dải khả dụng của chính trọng số đó")
    print(f"{'trọng số':<14}{'khối':<22}{'hướng':>6}{'tỉ lệ':>9}   đạo hàm × dải")
    for r in rows[: a.top]:
        if r.share < 1e-6:
            continue
        d = "↑" if r.direction > 0 else ("↓" if r.direction < 0 else "·")
        print(f"{r.symbol:<14}{r.block:<22}{d:>6}{r.share*100:8.2f}%   {r.scaled:+.5f}")
    _hr("GỘP THEO PHƯƠNG TRÌNH")
    for b, s in block_shares(rows).items():
        print(f"  {b:<24}{s*100:6.2f}%")


def cmd_tornado(a) -> None:
    bars = tornado(opt=_opts(a))
    _hr("VÙNG TUỲ BIẾN — biên độ lnDXY khi quét trọng số trên TOÀN dải khả dụng")
    print(f"{'trọng số':<14}{'khối':<22}{'tại lo':>10}{'tại hi':>10}{'biên độ':>11}{'tỉ lệ':>9}")
    for b in bars[: a.top]:
        print(f"{b.symbol:<14}{b.block:<22}{b.at_lo:10.4f}{b.at_hi:10.4f}"
              f"{b.swing:+11.4f}{b.share*100:8.2f}%")


def cmd_mc(a) -> None:
    mc = monte_carlo(opt=_opts(a), n=a.n)
    _hr(f"MONTE CARLO trên vùng khả thi — n = {mc.n}")
    print(f"  ln DXY: trung bình {mc.mean:.4f}   độ lệch {mc.sd:.4f}")
    print(f"  phân vị 5/50/95: {mc.q05:.4f} / {mc.q50:.4f} / {mc.q95:.4f}")
    print(f"  tỉ lệ rút thăm thoả mọi ràng buộc cứng: {mc.feasible_fraction*100:.1f}%")
    _hr("PHÂN RÃ PHƯƠNG SAI — S_i bậc nhất")
    print(f"{'trọng số':<14}{'khối':<22}{'S_i':>9}{'tương quan':>12}")
    for s in mc.shares[: a.top]:
        if s.first_order < 1e-4:
            continue
        print(f"{s.symbol:<14}{s.block:<22}{s.first_order*100:8.2f}%{s.correlation:+12.3f}")
    r = interaction_residual(mc)
    print()
    print(f"  Phần phương sai nằm ở TƯƠNG TÁC giữa các trọng số: {r*100:.1f}%")
    print("  (Không có đối chứng trong sách: ở đó mọi trọng số là hằng số nên không")
    print("   thể tương tác. Đây chính là đại lượng Layer W sinh ra để nhìn thấy.)")


def cmd_check(a) -> None:
    res = run(WorldState(), None, _opts(a))
    _hr("RÀNG BUỘC CẤU TRÚC")
    for c in feasibility(res):
        mark = "✓" if c.ok else "✗"
        print(f"  {mark} {c.label_vi:<46} = {c.value:9.4f}  ({c.bound}, "
              f"dư {c.slack:+.4f})   [{c.source}]")
    if res.warnings:
        _hr("CẢNH BÁO")
        for w in res.warnings:
            print(f"  ⚠ {w}")
    _hr("TRẠNG THÁI TẦNG")
    print(f"  σ_sys {res.sigma.sigma:.4f}   Φ_sys {res.phi:.4f}   s_US {res.s_us:.4f}")
    print(f"  κ_sys {res.kappa.kappa:.4f} (trần {res.kappa.kappa_max:.4f})")
    print(f"  H_soc {res.psycho.H_soc:.4f}   I_imp {res.psycho.I_imp:.4f}   "
          f"η·κ_A·g₁ {res.psycho.contraction:.4f}")
    print(f"  khuếch đại Layer 4 = 1/(1−T′) = {res.psycho.amplification:.3f}")
    print(f"  f_hard {res.f_hard:.4f}   k_Ψ {res.k_psi:.3f}   Ψ_str {res.psi_str:.4f}")
    print(f"  ‖C‖∞ {res.weights.coupling_norm:.3f}   "
          f"khuếch đại Layer W = {res.weights.amplification:.3f}")
    moved = res.weights.moved()
    if moved:
        _hr("TRỌNG SỐ BỊ LUẬT TƯƠNG TÁC DỊCH CHUYỂN")
        for k, b, v, d in moved[:15]:
            print(f"  {WEIGHTS[k].symbol:<12} {b:8.4f} → {v:8.4f}   ({d*100:+6.1f}%)")


def cmd_audit(a) -> None:
    opt = _opts(a)
    _hr("ĐỐI CHIẾU MỌI KỊCH BẢN VỚI SỐ LIỆU SÁCH BÁO CÁO")
    print(f"{'kịch bản':<18}{'ENGINE':>11}{'SÁCH':>9}{'lệch':>9}  "
          f"{'chế độ':<14}{'khối chi phối':<15}   σ      κ")
    rows = []
    for k, sc in SCENARIOS.items():
        f = run_scenario(k, opt=opt)
        tgt = sc.book_target_pct
        gap = (f.headline.pct - tgt) if tgt is not None else None
        rows.append((k, sc, f, tgt, gap))
        t = f"{tgt:+.2f}%" if tgt is not None else "—"
        g = f"{gap:+.2f}" if gap is not None else "—"
        print(f"{k:<18}{f.headline.pct:+10.2f}%{t:>9}{g:>9}  "
              f"{f.regime.value:<14}{f.dominant:<15}{f.sigma_to:6.3f} {f.kappa_to:6.3f}")

    notes = [(k, sc.gap_note_vi) for k, sc, _, _, _ in rows if sc.gap_note_vi]
    if notes:
        _hr("VỀ CÁC CHỖ LỆCH")
        for k, n in notes:
            print(f"  {k}: {n}")

    _hr("MỐC KIỂM TRA CỦA SÁCH")
    for k, v in BOOK_SANITY_CHECK.items():
        print(f"  {k:<28}{v:8.2f}%")
    print()
    print(CONVEXITY_NOTE_VI)
    print()
    print(RESIDUAL_NOTE_VI)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="amr", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    for flag, helptext in [
        ("--no-state", "tắt phụ thuộc trạng thái của trọng số (E17)"),
        ("--no-coupling", "tắt ghép cặp trọng số (E18)"),
        ("--recentre", "bật tái định tâm độ lồi (E22, đóng I37)"),
        ("--regime-lambda", "bật λ₁ chuyển chế độ (E21, Remark 11.3)"),
        ("--return-path", "bật đường về Layer 5 → Layer 4 (E26, đóng I32)"),
        ("--reversal", "bật kênh đảo chiều cưỡng chế (E27, đóng I34)"),
        ("--health-leg", "bật nhánh sốc ngoại sinh phi quân sự (E25)"),
        ("--split-prec", "tách D_prec theo đường cong (E28, đóng I40)"),
        ("--funding-haven", "số hạng trú ẩn chạy theo nhánh funding"),
    ]:
        p.add_argument(flag, action="store_true", help=helptext)

    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)

    r = sub.add_parser("run")
    r.add_argument("scenario", choices=sorted(SCENARIOS))
    r.add_argument("--json", action="store_true")
    r.set_defaults(fn=cmd_run)

    w = sub.add_parser("weights"); w.add_argument("--top", type=int, default=25)
    w.set_defaults(fn=cmd_weights)

    t = sub.add_parser("tornado"); t.add_argument("--top", type=int, default=25)
    t.set_defaults(fn=cmd_tornado)

    m = sub.add_parser("mc")
    m.add_argument("--n", type=int, default=1500)
    m.add_argument("--top", type=int, default=25)
    m.set_defaults(fn=cmd_mc)

    sub.add_parser("check").set_defaults(fn=cmd_check)
    sub.add_parser("audit").set_defaults(fn=cmd_audit)

    a = p.parse_args(argv)
    a.fn(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
