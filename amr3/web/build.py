#!/usr/bin/env python3
"""build.py — sinh reg.json, vector kiểm, và lắp manifold_panel.html.

Trang in ra câu "khớp bản Python tới 3,6e-15". Một tuyên bố như thế phải lặp
lại được, nếu không nó đúng là loại khuyết tật ISSUES #36 ghi cho CS8.

    python amr3/web/build.py            # sinh reg.json + vecs.json + gvecs.json
    node   amr3/web/verify.js           # 40 vector E3–E9 + Layer W
    node   amr3/web/verify2.js          # 12 vector lớp hình học
    python amr3/web/build.py --assemble # lắp lại trang

Bản JS là bản CHUYỂN, không phải bản xấp xỉ: nó giữ đúng thứ tự phép tính của
bản Python, vì phép cộng dấu phẩy động không giao hoán.
"""
from __future__ import annotations
import json, math, random, sys
from pathlib import Path

# --- UTF-8 console (Windows cp1252 would otherwise abort on printing) ---
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

from amr import Options, WorldState, run                                 # noqa: E402
from amr.registry import (CHANNELS, DEMAND, D_PREC, LATENTS, SUPPLY,     # noqa: E402
                          WEIGHTS)
from amr.layers import DEFAULT_OMEGA, SigmaInputs                        # noqa: E402
from amr.weightlayer import DEFAULT_COUPLING, Z_BASELINE                 # noqa: E402
from amr3 import (Memory, Move, Options3, Sheet, Transversality,         # noqa: E402
                  commutator, holonomy, residual, trace, unmeasured)
from amr3.atlas import ATLAS, cross_sheet_edges                          # noqa: E402
from amr3.geometry import (H_STAR, PARAMS, TAU_CEILING,                  # noqa: E402
                            TAU_CEILING_BY_MODE)

# Ghi chú dùng trong trang nói bằng ngôn ngữ hình học thuần. Văn bản trong
# engine giữ nguyên; chỉ bản xuất ra web được viết lại.
NEUTRAL_NOTE = {
    "theta_0": ("NGƯỠNG tích luỹ động lực cứng, và là trọng số VỊ TRÍ của Σ₅. "
                "Assumption 9.2 giữ nó cố định trước tầng Σ₄; §9.8 gọi đó là chỗ "
                "hệ quả lớn nhất chương theo bản gốc. Tải trọng Σ₄→Σ₅ là chỗ rời "
                "đi, và nó bằng 0 theo mặc định."),
}
NEUTRAL_PARAM = {
    "H_star": ("ngưỡng trên cường độ tấm nguồn; dưới nó mọi tác động là tiếp tuyến "
               "dù τ bằng bao nhiêu. TÔI ĐẶT. H_soc không có chuỗi quan sát nào nên "
               "ngưỡng này chưa ước lượng được — chỉ nêu bằng số để bác bỏ được."),
    "q_taut": ("hệ số độ cong: tấm đích cong hơn thì thành phần vuông góc vào sâu "
               "hơn bấy nhiêu lần. TÔI ĐẶT. Dạng của số hạng thì không — II = 4Λ′ "
               "lấy từ chính biên Λ′ ≤ ¼ của Proposition 8.2 và của E19."),
}


def registry() -> dict:
    si = SigmaInputs()
    reg = dict(
        demand=[dict(k=c.key, s=c.symbol, vi=c.name_vi, ac=c.alpha_calm,
                     ax=c.alpha_crisis, ev=c.evidence.value) for c in DEMAND],
        supply=[dict(k=c.key, s=c.symbol, vi=c.name_vi, ac=c.alpha_calm,
                     ax=c.alpha_crisis, ev=c.evidence.value) for c in SUPPLY],
        prec=dict(k=D_PREC.key, s=D_PREC.symbol, vi=D_PREC.name_vi,
                  ac=D_PREC.alpha_calm, ax=D_PREC.alpha_crisis,
                  ev=D_PREC.evidence.value),
        weights={k: dict(s=w.symbol, vi=w.name_vi, b=w.base, lo=w.lo, hi=w.hi,
                         pv=w.provenance.value, ev=w.evidence.value,
                         g=dict(w.gamma or {}),
                         g2=[[m, n, v] for (m, n), v in (w.gamma2 or {}).items()])
                 for k, w in WEIGHTS.items()},
        latents={k: dict(s=l.symbol, vi=l.name_vi, d=l.default,
                         L=getattr(l.layer, "name", str(l.layer)),
                         meas=l.measurement) for k, l in LATENTS.items()},
        coupling=[[k, j, c] for (k, j), c in DEFAULT_COUPLING.items()],
        zbase=dict(Z_BASELINE),
        omega=[[c.year, c.severity] for c in DEFAULT_OMEGA],
        opt=dict(t_now=2026.75, lam_f=0.08, eta=3.0, cL0=0.8, cL1=1.18,
                 c_bar=1.30, s_c=0.55, T_career=25.0, mnorm=13.0,
                 kpsiC=[2.2, 1.0, 0.8], kpsiV0=0.23617, kpsiH0=0.30,
                 kpsiI0=0.30, v0=0.4, bA=0.8, bP=0.6),
        sigin=dict(p_vix=si.p_vix, p_bondvol=si.p_bondvol, p_gpr=si.p_gpr,
                   p_stlfsi=si.p_stlfsi, p_health=si.p_health),
        atlas={k: dict(sh=a.sheet.value, role=a.role.value,
                       note=NEUTRAL_NOTE.get(k, a.note),
                       p=[[s.value, v, l] for s, v, l in a.pierces])
               for k, a in ATLAS.items()},
        edges=[[s.value, d.value, v, w, l] for s, d, v, w, l in cross_sheet_edges()],
        hstar={str(s.value): v for s, v in H_STAR.items()},
        params=[[p.key, p.symbol, p.base, p.lo, p.hi, p.provenance.value,
                 p.evidence.value, NEUTRAL_PARAM.get(p.key, p.note)]
                for p in PARAMS.values()],
        ceiling=TAU_CEILING,
        ceilings=dict(TAU_CEILING_BY_MODE),
        hand={str(s.value): [[k, t] for k, t in rows]
              for s, rows in unmeasured().items()},
    )
    return reg


def core_vectors(n: int = 40, seed: int = 20261009) -> list:
    random.seed(seed)
    LK, CK = list(LATENTS), list(CHANNELS) + ["prec"]
    SG = ("p_vix", "p_bondvol", "p_gpr", "p_stlfsi", "p_health")
    out = []
    for _ in range(n):
        st = WorldState()
        for k in LK:
            st.latents[k] = round(random.uniform(0.02, 0.98), 4)
        for k in CK:
            st.channels[k] = round(math.exp(random.uniform(-0.35, 0.35)), 6)
        for a in SG:
            setattr(st.sigma_inputs, a, round(random.uniform(0.02, 0.98), 4))
        ov = {k: round(WEIGHTS[k].lo + random.uniform(0.1, 0.9)
                       * (WEIGHTS[k].hi - WEIGHTS[k].lo), 5)
              for k in random.sample(list(WEIGHTS), 6)}
        r = run(st, ov, Options())
        out.append(dict(
            lat={k: st.latents[k] for k in LK},
            ch={k: st.channels[k] for k in CK},
            sg={a: getattr(st.sigma_inputs, a) for a in SG},
            ov=ov,
            out=dict(ln=r.ln_DXY, psi=r.psi_str, phi=r.phi, sus=r.s_us,
                     kap=r.kappa.kappa, kmax=r.kappa.kappa_max,
                     sig=r.sigma.sigma, H=r.psycho.H_soc, I=r.psycho.I_imp,
                     V=r.psycho.V_meme, fh=r.f_hard, kps=r.k_psi,
                     ms=r.M_shock, lam=r.lam_weight, brk=r.ln_bracket,
                     hav=r.haven, cn=r.weights.coupling_norm,
                     w=dict(r.weights.values))))
    return out


def geo_vectors(n: int = 12, seed: int = 777) -> list:
    random.seed(seed)
    out = []
    for i in range(n):
        tau = round(random.uniform(0.0, 1.0), 3)
        mode = Memory.HYSTERESIS if i % 2 == 0 else Memory.FATIGUE
        dtv = round(random.uniform(0.3, 3.0), 2)
        amp = round(random.uniform(0.55, 0.99), 3)
        ml = {k: amp for k in ("A_alg", "C_src", "P_AI", "T_exp", "S_access",
                               "P_habit", "E_sys", "A_meta")}
        ml["R_div"] = round(1.0 - amp, 3)
        hl = {"C_alt": round(random.uniform(0.2, 0.9), 3),
              "T_frag": round(random.uniform(0.2, 0.9), 3),
              "Au_sub": round(random.uniform(0.1, 0.8), 3)}
        M = Move("MEME", Sheet.PSYCHO, latents=tuple(ml.items()), dt=dtv)
        H = Move("CUNG", Sheet.SECULAR, latents=tuple(hl.items()))
        full = i % 2 == 0
        o = Options3(tv=(Transversality.full(tau) if full
                         else Transversality.knife(tau)),
                     fragmentation_feedback=(i % 3 == 0), memory=mode)
        c, h, r = commutator(M, H, opt=o), holonomy([M, H], opt=o), residual(M, opt=o)
        tj = trace([M, H], opt=o)
        out.append(dict(
            tau=tau, full=full, fb=(i % 3 == 0), mode=mode.value, dt=dtv,
            mlat=ml, hlat=hl,
            comm=c.norm, lnAB=c.ln_ab, lnBA=c.ln_ba, hol=h.value, res=r.value,
            scar={str(s.value): v for s, v in tj.scars().items()},
            ln=tj.ln_DXY, Tfrag=tj.final.T_frag,
            th0=tj.final.overrides.get("theta_0", WEIGHTS["theta_0"].base),
            inten={str(s.value): st.intensity for s, st in tj.final.sheets.items()},
            taut={str(s.value): st.taut for s, st in tj.final.sheets.items()}))
    return out


def assemble() -> Path:
    reg = HERE / "reg.json"
    out = ROOT / "manifold_panel.html"
    parts = [
        (HERE / "head.html").read_text(encoding="utf-8"),
        (HERE / "body.html").read_text(encoding="utf-8"),
        '\n<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/'
        '0.128.0/three.min.js"></script>\n<script>\n',
        (HERE / "engine.js").read_text(encoding="utf-8"),
        "\nwindow.REG=" + reg.read_text(encoding="utf-8") + ";\n</script>\n<script>\n",
        (HERE / "ui.js").read_text(encoding="utf-8"),
        "</script>\n",
    ]
    out.write_text("".join(parts), encoding="utf-8")
    return out


def main() -> None:
    dump = lambda p, o: (HERE / p).write_text(
        json.dumps(o, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    dump("reg.json", registry())
    dump("vecs.json", core_vectors())
    dump("gvecs.json", geo_vectors())
    print(f"reg.json · vecs.json (40) · gvecs.json (12)  →  {HERE}")
    if "--assemble" in sys.argv:
        print("lắp xong →", assemble())


if __name__ == "__main__":
    main()
