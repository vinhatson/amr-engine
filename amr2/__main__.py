"""Đối chiếu amr (bản sách) với amr2 (bản sau chỉnh) trên cùng một bài thi."""

from __future__ import annotations

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
from typing import List, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amr2 import CorrectedModel, OIL_SHOCK_EVIDENCE, Regime, months   # noqa: E402
from amr2.estimate import ols_hac                                     # noqa: E402
from amr2.panel import BYMONTH, window                                # noqa: E402


def hr(t: str) -> None:
    print("\n" + t)
    print("─" * 88)


def rmse(e: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in e) / len(e))


OOS = [m for m in months("2025-11", "2026-07") if m in BYMONTH]


def main() -> None:
    hr("amr2 — ƯỚC LƯỢNG, mẫu dừng 2025-10")
    m = CorrectedModel().train()
    f = m.fit
    print(f"  mẫu {f.sample[0]} → {f.sample[1]}   n = {f.n}   R² = {f.r2:.4f}   "
          f"σ phần dư = {f.sigma:.3f}   Newey–West L = {f.lags}")
    label = {"cap": "D_cap   Δ chênh lệch 10 năm Mỹ–Đức (pp)",
             "oil": "D_trans 100·Δln Brent",
             "pol": "S_Fed   Δ lãi suất quỹ liên bang (pp)",
             "realcap": "D_cap thực",
             "const": "hằng số"}
    for k in f.terms:
        print(f"    {label.get(k,k):<42}{f.line(k)}")

    keep = f.significant(2.0)
    print(f"\n  Số hạng có ý nghĩa (|t| ≥ 2): {', '.join(keep) if keep else 'không có'}")
    m2 = CorrectedModel().train().prune()
    if tuple(m2.terms) != tuple(m.terms):
        print(f"  Sau khi tỉa: {', '.join(m2.fit.terms)}   R² = {m2.fit.r2:.4f}")
    model = m2

    hr(f"DỰ BÁO NGOÀI MẪU — {OOS[0]} đến {OOS[-1]}")
    print("  tháng     điểm   khoảng 90%        thực tế")
    fc = model.forecast_path(OOS)
    for x in fc:
        print("  " + x.line())

    called = [x for x in fc if not x.abstain]
    skipped = [x for x in fc if x.abstain]
    e_all = [x.point - x.actual for x in fc]
    a_all = [x.actual for x in fc]
    e_called = [x.point - x.actual for x in called]
    a_called = [x.actual for x in called]
    cover = sum(1 for x in fc if x.hit)
    cover_c = sum(1 for x in called if x.hit)
    sg = sum(1 for x in fc if (x.point > 0) == (x.actual > 0))
    sg_c = sum(1 for x in called if (x.point > 0) == (x.actual > 0))

    hr("CHẤM ĐIỂM")
    print(f"{'':<34}{'RMSE':>9}{'ngây thơ':>11}{'dấu':>8}{'bao phủ':>10}")
    print(f"{'tất cả chín tháng':<34}{rmse(e_all):>8.3f}%{rmse(a_all):>10.3f}%"
          f"{sg:>6}/9{cover:>8}/9")
    print(f"{'chỉ những tháng MÔ HÌNH GỌI':<34}{rmse(e_called):>8.3f}%"
          f"{rmse(a_called):>10.3f}%{sg_c:>6}/{len(called)}{cover_c:>8}/{len(called)}")
    print(f"\n  Từ chối gọi: {', '.join(x.month for x in skipped) or 'không tháng nào'}")
    for x in skipped:
        print(f"    {x.month}: {x.abstain_reason}")

    hr("SO SÁNH TRỰC TIẾP — amr so với amr2, cùng chín tháng")
    print(f"{'mô hình':<44}{'RMSE':>9}{'dấu':>8}{'gọi':>7}")
    print(f"{'amr  · sáu tầng, tham số quy ước, dự báo điểm':<44}{18.64:>8.2f}%{2:>6}/4{'4/4':>7}")
    print(f"{'      (chấm trên bốn mốc tích luỹ, không phải chín tháng)':<44}")
    print(f"{'ngây thơ · luôn dự báo 0':<44}{rmse(a_all):>8.3f}%{0:>6}/9{'9/9':>7}")
    print(f"{'amr2 · tất cả chín tháng':<44}{rmse(e_all):>8.3f}%{sg:>6}/9{'9/9':>7}")
    print(f"{'amr2 · chỉ tháng nó chịu gọi':<44}{rmse(e_called):>8.3f}%"
          f"{sg_c:>6}/{len(called)}{f'{len(called)}/9':>7}")

    hr("ĐIỀU amr2 LÀM MÀ amr KHÔNG")
    print("  1. Nó TỪ CHỐI GỌI ở tháng nó biết mình hỏng, và ngưỡng được NÊU RA")
    print("     bằng số — nên mệnh đề đó bác bỏ được. Đây là khuyết tật ISSUES #36")
    print("     ghi cho CS8, đóng lại.")
    print("  2. Nó in KHOẢNG chứ không in điểm, và khoảng rộng ra theo chế độ.")
    print("  3. Nó để DẤU cho dữ liệu quyết định. Hệ số dầu âm vi phạm quy ước")
    print("     Tầng 0 của sách, và nó âm ở mọi mốc cắt từ 2012.")
    print("  4. Nó không chứa tham số nào không nhận dạng được. Không có κ.")
    print()
    print("  " + OIL_SHOCK_EVIDENCE.replace("\n", "\n  "))

    hr("ĐỘ ỔN ĐỊNH CỦA HỆ SỐ THEO MỐC CẮT")
    print(f"{'cắt tại':<10}{'n':>5}", end="")
    for k in model.fit.terms:
        print(f"{k:>12}", end="")
    print()
    for cut in ("2012-12", "2016-12", "2019-12", "2021-12", "2023-12", "2025-10", "2026-07"):
        rows = window("2007-05", cut)
        if len(rows) < 40:
            continue
        ff = ols_hac(rows, [t for t in model.fit.terms if t != "const"],
                     const=("const" in model.fit.terms))
        print(f"{cut:<10}{ff.n:>5}", end="")
        for k in model.fit.terms:
            print(f"{ff.beta[k]:>12.4f}", end="")
        print()


if __name__ == "__main__":
    main()
