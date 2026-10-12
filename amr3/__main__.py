"""Chạy amr3: bản đồ, lồng khít, ba phép đo, quét τ, và phân mảnh."""

from __future__ import annotations

import sys

# --- UTF-8 console (Windows cp1252 would otherwise abort on the first
#     Vietnamese or Greek character printed below) ---
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):      # non-TTY or already wrapped
        pass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from amr import run                                                   # noqa: E402

from .atlas import Sheet, summary, unmeasured                         # noqa: E402
from .geometry import (PARAMS, TAU_CEILING, TAU_CEILING_BY_MODE,       # noqa: E402
                       Memory, Transversality)
from .model import Manifold, Options3, commutator, holonomy, residual, trace
from .operators import Move                                           # noqa: E402


def hr(t: str) -> None:
    print("\n" + t)
    print("─" * 84)


# Hai toán tử, mỗi cái trên một tấm. Tầng 4 không có đầu vào trực tiếp —
# H_soc là điểm bất động của Eq (8.8) — nên toán tử tự sự tác động qua chín
# biến ẩn Tầng 4, đúng cách sách đặt tầng đó.
def _meme(amp: float = 0.95, dt: float = 1.0) -> Move:
    d = 1.0 - amp
    return Move(
        f"MEME({amp:.2f})", Sheet.PSYCHO,
        latents=(("A_alg", amp), ("C_src", amp), ("P_AI", amp), ("T_exp", amp),
                 ("S_access", amp), ("P_habit", amp), ("E_sys", amp),
                 ("R_div", d), ("A_meta", amp)),
        dt=dt,
    )


MEME = _meme(0.95)

HARD = Move(
    "CỨNG", Sheet.SECULAR,
    latents=(("C_alt", 0.62), ("T_frag", 0.70), ("Au_sub", 0.60)),
)


def main() -> None:
    print(summary())

    # --------------------------------------------------------------------- #
    hr("NĂM HẰNG SỐ, MANG ĐÚNG BỘ THÔNG TIN 39 TRỌNG SỐ CỦA amr PHẢI MANG")
    print(f"{'':4s}{'nền':>8}{'vùng khả dụng':>18}{'xuất xứ':>20}{'bằng chứng':>12}")
    for p in PARAMS.values():
        print(f"  {p.symbol:2s}{p.base:>8.3f}{'[' + format(p.lo, '.3f') + ', '
              + format(p.hi, '.3f') + ']':>18}"
              f"{p.provenance.value:>20}{p.evidence.value:>12}")
    print()
    print(f"  Trần của τ PHỤ THUỘC DẠNG TRÍ NHỚ: "
          f"trễ {TAU_CEILING_BY_MODE['hysteresis']:.3f} · "
          f"mỏi {TAU_CEILING_BY_MODE['fatigue']:.3f}")
    print("  Cùng ngân sách thực nghiệm, một đơn vị τ sinh lượng ξ khác nhau.")
    print("    VR(36) = 0,884 · VR(60) = 0,842 — thành phần thường trực TỒN TẠI")
    print("    cap + oil lấy 48,2% biến thiên 36 tháng, phần dư 51,8% và PHẲNG")
    print("    d(ln DXY)/dθ₀ = +48,31 điểm %/đơn vị  ⇒  ξ₅ cần 0,1319")
    print("  Là chặn TRÊN, không phải ước lượng điểm. Bốn hằng số còn lại TÔI ĐẶT.")

    # --------------------------------------------------------------------- #
    hr("Ô NGƯỜI DÙNG VẪN TỰ ĐIỀN — đọc từ trường `measurement` của amr")
    um = unmeasured()
    tot = 0
    for sheet in Sheet:
        rows = um.get(sheet)
        if not rows:
            continue
        tot += len(rows)
        print(f"  {sheet.vi}")
        for k, tag in rows:
            print(f"    {k:<12} {tag}")
    print(f"\n  {tot} ô. Chín biến Tầng 4 ghi nguyên văn \"No series\" trong registry,")
    print("  và H_soc là điểm bất động của Eq (8.8) giải TỪ chín ô đó — nên một giá")
    print("  trị H_soc là hệ quả của chín số tự điền, không phải một phép đo.")
    print("  amr3 không vá chỗ này. Nó dán nhãn, để số tự điền không lẫn với số đã đo.")

    # --------------------------------------------------------------------- #
    hr("LỒNG KHÍT — τ ≡ 0 phải cho lại amr đúng chữ số máy")
    z = Options3(tv=Transversality.zero())
    t0 = trace([MEME, HARD], opt=z)
    base_amr = run().ln_DXY
    base_amr3 = Manifold(opt=z).step(None).ln_DXY
    print(f"  amr  nền          ln DXY = {base_amr:.12f}")
    print(f"  amr3 nền, τ=0     ln DXY = {base_amr3:.12f}")
    print(f"  chênh lệch        {abs(base_amr - base_amr3):.3e}")
    print(f"  vết sẹo sau MEME→CỨNG ở τ=0: {t0.scars() or 'không có'}")

    # --------------------------------------------------------------------- #
    for label, tv in (("τ ≡ 0  ·  amr nguyên bản", Transversality.zero()),
                      ("τ₄₅ = trần dữ liệu cho phép", Transversality.knife()),
                      ("τ₄₅ = 1,00  ·  NGOÀI VÙNG, giữ lại để so", Transversality.knife(1.0)),
                      ("τ₄* = trần · mọi cạnh Σ₄ bật", Transversality.full())):
        hr(f"BA PHÉP ĐO — {label}")
        o = Options3(tv=tv)
        c = commutator(MEME, HARD, opt=o)
        h = holonomy([MEME, HARD], opt=o)
        rr = residual(MEME, opt=o)
        print("  1 · " + c.line())
        print("  2 · " + h.line().replace("\n", "\n      "))
        print("  3 · " + rr.line())
        if c.scar_ab or c.scar_ba:
            print(f"      sẹo MEME∘CỨNG {_s(c.scar_ab)}   CỨNG∘MEME {_s(c.scar_ba)}")
        for w in trace([MEME, HARD], opt=o).final.warnings:
            print(f"      ⚠ {w}")

    # --------------------------------------------------------------------- #
    hr("QUÉT τ₄₅ — từ trượt sang đâm, liên tục")
    print(f"{'τ₄₅':>6}{'‖[L₄,L₅]‖':>14}{'H(γ)':>14}{'dư âm':>12}"
          f"{'sẹo Σ₅':>10}{'θ₀ cuối':>10}")
    for tau in (0.0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0):
        o = Options3(tv=Transversality.knife(tau))
        c = commutator(MEME, HARD, opt=o)
        h = holonomy([MEME, HARD], opt=o)
        rr = residual(MEME, opt=o)
        tj = trace([MEME, HARD], opt=o)
        sc = tj.final.scar(Sheet.SECULAR)
        th = tj.final.overrides.get("theta_0", 0.50)
        print(f"{tau:>6.2f}{c.norm:>14.3e}{h.value:>+14.3e}{rr.value:>+12.6f}"
              f"{sc:>10.4f}{th:>10.4f}")

    # --------------------------------------------------------------------- #
    hr("ĐỘC LẬP VỚI TỐC ĐỘ — cùng đường đi, chia khác nhau, tổng thời lượng = 4")
    print("  Bản trước hỏng hai chỗ: cộng dồn theo mỗi lần gọi step(), và đọc độ")
    print("  cong từ tấm ĐÃ BỊ DỊCH. Sửa cả hai thì cả hai dạng bằng đúng một số.\n")
    print(f"{'bước × dt':>13}{'HYSTERESIS':>14}{'FATIGUE':>12}")
    for k in (1, 2, 4, 8, 20):
        row = []
        for md in (Memory.HYSTERESIS, Memory.FATIGUE):
            oo = Options3(tv=Transversality.knife(TAU_CEILING_BY_MODE[md.value]),
                          memory=md)
            mf = Manifold(opt=oo)
            mf.step(None)
            for _ in range(k):
                mf.step(_meme(0.95, 4.0 / k))
            mf.step(HARD)
            mf.step(None)
            row.append(mf.sheets[Sheet.SECULAR].scar)
        print(f"{str(k) + ' × ' + format(4.0/k, '.2f'):>13}{row[0]:>14.6f}{row[1]:>12.6f}")

    # --------------------------------------------------------------------- #
    hr("THỜI LƯỢNG — trễ phải PHẲNG, mỏi phải TĂNG")
    print("  Đây là chỗ hai nhánh nêu dự đoán TRÁI NHAU, nên phân biệt được.\n")
    print(f"{'tổng dt':>9}{'HYSTERESIS':>14}{'FATIGUE':>12}")
    for T in (1, 2, 4, 8, 16, 32):
        row = []
        for md in (Memory.HYSTERESIS, Memory.FATIGUE):
            oo = Options3(tv=Transversality.knife(TAU_CEILING_BY_MODE[md.value]),
                          memory=md)
            mf = Manifold(opt=oo)
            mf.step(None); mf.step(_meme(0.95, float(T)))
            mf.step(HARD); mf.step(None)
            row.append(mf.sheets[Sheet.SECULAR].scar)
        print(f"{T:>9}{row[0]:>14.6f}{row[1]:>12.6f}")
    print()
    print("  Trễ: thời lượng KHÔNG vào công thức, nên phép so sánh 'đợt dài vừa")
    print("  so với cú sốc ngắn mạnh' không có nội dung. Mỏi: thời lượng THAY")
    print("  THẾ được biên độ, và điểm hoà vốn là một con số nêu ra được.")

    # --------------------------------------------------------------------- #
    hr("GIAO HOÁN TỬ TÁCH ĐÚNG HAI NHÁNH")
    print(f"{'dạng':<12}{'τ':>8}{'‖[L₄,L₅]‖':>14}{'H(γ)':>14}{'dư âm':>12}")
    for md in (Memory.HYSTERESIS, Memory.FATIGUE):
        tcap = TAU_CEILING_BY_MODE[md.value]
        oo = Options3(tv=Transversality.knife(tcap), memory=md)
        c = commutator(MEME, HARD, opt=oo)
        h = holonomy([MEME, HARD], opt=oo)
        rr = residual(MEME, opt=oo)
        print(f"{md.value:<12}{tcap:>8.3f}{c.norm:>14.3e}{h.value:>+14.3e}"
              f"{rr.value:>+12.6f}")
    print()
    print("  Trễ lấy CỰC ĐẠI theo lịch sử. Hai thứ tự đi qua cùng tập trạng thái")
    print("  nên cực đại bằng nhau → giao hoán tử bằng 0 theo định nghĩa toán tử.")
    print("  Holonomy và dư âm vẫn khác 0: trạng thái về được, vết sẹo thì không.")
    print()
    print("  Câu hỏi thực nghiệm: thứ tự hai cú sốc có đổi mức thường trực không,")
    print("  khi trạng thái cuối giữ nguyên? CÓ → mỏi. KHÔNG → trễ.")

    # --------------------------------------------------------------------- #
    hr("DẢI KHÔNG GIAO HOÁN — con dao chỉ để lại lỗ PHỤ THUỘC THỨ TỰ trong một dải")
    print("  Quét biên độ ở τ₄₅ = 1 dạng MỎI — dải chỉ tồn tại ở nhánh này.")
    print("  của tấm Σ₅; Λ → 1 là tấm đã bão hoà ở L_max và không nhận thêm được.\n")
    print(f"{'biên':>7}{'Λ(arg)':>9}{'sẹo meme-trước':>16}{'sẹo cứng-trước':>16}"
          f"{'‖[L₄,L₅]‖':>14}{'ai sâu hơn':>12}")
    o = Options3(tv=Transversality.knife(1.0), memory=Memory.FATIGUE)
    for i in range(70, 100, 2):
        amp = i / 100.0
        mv = _meme(amp)
        c = commutator(mv, HARD, opt=o)
        a = trace([mv, HARD], opt=o)
        b = trace([HARD, mv], opt=o)
        sa, sb = a.final.scar(Sheet.SECULAR), b.final.scar(Sheet.SECULAR)
        lam = (1.0 - a.final.psi_str) / 0.35
        who = "meme" if sa > sb + 1e-9 else ("cứng" if sb > sa + 1e-9 else "—")
        print(f"{amp:>7.2f}{lam:>9.4f}{sa:>16.4f}{sb:>16.4f}{c.norm:>14.3e}{who:>12}")
    print()
    print("  Ba chế độ, và chỉ chế độ giữa là chế độ luận điểm nói về:")
    print("    biên < 0,77   H_soc chưa qua H* — không có vết đâm nào. TRƯỢT.")
    print("    0,78 – 0,84   có đâm, tấm chưa bão hoà. ĐỈNH 3,2e-02 tại 0,80.")
    print("                  meme-trước SÂU HƠN, và dấu này nhất quán ở mọi biên.")
    print("    biên ≥ 0,86   Λ → 1, tấm bão hoà ở L_max. Giao hoán tử SẬP về 0.")
    print("                  (Bản trước báo một ĐẢO DẤU ở đây. Đó là tạo tác của")
    print("                   lỗi độ cong, đã rút lại.)")
    print()
    print("  Hiệu ứng thứ tự chỉ sống trong một DẢI, và chỉ ở nhánh mỏi. Dưới")
    print("  dải chưa qua H*; trên dải L_max đã chặn tổng thiệt hại nên thêm")
    print("  một lượng nữa không đổi được đầu ra.")

    # --------------------------------------------------------------------- #
    hr("PHÂN MẢNH CHÍNH TRỊ LÀ ĐẦU RA, KHÔNG PHẢI ĐẦU VÀO")
    print("  T_frag(t) = T_frag⁰ + ρ·ξ₂(t),  ρ = 0,50")
    print("  Trong amr, T_frag là biến ẩn Tầng 2 người dùng TỰ ĐIỀN (nền 0,420).")
    print("  Bật τ₄₂ và phản hồi: nó thành hệ quả của việc meme đâm qua cấu trúc.\n")
    print(f"{'cấu hình':<44}{'T_frag cuối':>14}{'sẹo Σ₂':>10}{'ln DXY':>14}")
    for label, tv, fb in (
        ("amr — τ≡0, không phản hồi", Transversality.zero(), False),
        ("τ₄₂ = trần, không phản hồi", Transversality.full(), False),
        ("τ₄₂ = trần, CÓ phản hồi phân mảnh", Transversality.full(), True),
    ):
        o = Options3(tv=tv, fragmentation_feedback=fb)
        tj = trace([MEME, MEME, HARD], opt=o)
        print(f"{label:<44}{tj.final.T_frag:>14.4f}"
              f"{tj.final.scar(Sheet.STRUCTURAL):>10.4f}{tj.ln_DXY:>14.6f}")


def _s(d) -> str:
    return "{" + ", ".join(f"Σ{k.value}:{v:.4f}" for k, v in sorted(
        d.items(), key=lambda kv: kv[0].value)) + "}" if d else "{}"


if __name__ == "__main__":
    main()
