/* engine.js — E3…E9, Layer W, và lớp hình học, chuyển từ Python sang JS.
 *
 * Không hằng số nào viết cứng ở đây: tất cả đến từ R (registry xuất ra từ
 * amr/registry.py và amr/weightlayer.py). Mọi số hạng giữ đúng thứ tự phép
 * tính của bản Python, vì phép cộng dấu phẩy động không giao hoán và trang
 * này tự nhận là trùng khít.
 *
 * Kiểm: verify.js chạy 40 vector sinh từ chính engine Python.
 */
(function (root) {
"use strict";

const CLIP = 700.0;
function logistic(z){
  if (z >= 0){ if (z > CLIP) return 1.0 - 1e-300; const e = Math.exp(-z); return 1/(1+e); }
  if (z < -CLIP) return 1e-300;
  const e = Math.exp(z); return e/(1+e);
}
function logit(u){ u = Math.min(Math.max(u,1e-12),1-1e-12); return Math.log(u/(1-u)); }
function dlogistic(z){ const l = logistic(z); return l*(1-l); }
function clamp(x,lo,hi){ lo = lo===undefined?0:lo; hi = hi===undefined?1:hi;
  return Math.min(Math.max(x,lo),hi); }
function safeLog(x){ return Math.log(Math.max(x,1e-300)); }
function blend(calm,crisis,lam){ return calm + (crisis-calm)*lam; }

/* ── E17 + E18 — hệ trọng số ───────────────────────────────────────────── */
function solveWeights(R, z, ov, enState, enCoup){
  const Wd = R.weights, keys = Object.keys(Wd);
  const ZB = R.zbase;
  const u0 = {}, base = {}, ell = {};
  for (const k of keys){
    const w = Wd[k];
    let b = (ov && k in ov) ? ov[k] : w.b;
    b = Math.min(Math.max(b, w.lo + 1e-12), w.hi - 1e-12);
    base[k] = b;
    const span = w.hi - w.lo;
    let u = span > 0 ? (b - w.lo)/span : 0.5;
    u0[k] = Math.min(Math.max(u,1e-9),1-1e-9);
    ell[k] = logit(u0[k]);
  }
  const sd = {};
  for (const k of keys){
    const w = Wd[k]; let d = 0.0;
    if (enState){
      for (const m in w.g){
        const zb = (m in ZB) ? ZB[m] : 0.0;
        d += w.g[m] * (((m in z) ? z[m] : zb) - zb);
      }
      for (const t of w.g2){
        const m = t[0], n = t[1], g = t[2];
        const zbm = (m in ZB)?ZB[m]:0.0, zbn = (n in ZB)?ZB[n]:0.0;
        d += g * ((((m in z)?z[m]:zbm) - zbm) * ((((n in z)?z[n]:zbn)) - zbn));
      }
    }
    sd[k] = d;
  }
  const rows = {}; for (const k of keys) rows[k] = [];
  if (enCoup) for (const t of R.coupling){
    const k = t[0], j = t[1], c = t[2];
    if (k in rows && j in u0 && k !== j) rows[k].push([j,c]);
  }
  let cnorm = 0.0;
  for (const k of keys){ let s = 0.0; for (const r of rows[k]) s += Math.abs(r[1]);
    if (s > cnorm) cnorm = s; }

  let u = Object.assign({}, u0);
  const drive = {};
  let converged = false, it = 0;
  for (it = 1; it <= 500; it++){
    let delta = 0.0; const nu = {};
    for (const k of keys){
      let d = ell[k] + sd[k];
      for (const r of rows[k]) d += r[1]*(u[r[0]] - u0[r[0]]);
      drive[k] = d;
      const val = Math.abs(d - ell[k]) < 1e-15 ? u0[k] : logistic(d);
      const dd = Math.abs(val - u[k]); if (dd > delta) delta = dd;
      nu[k] = val;
    }
    u = nu;
    if (delta < 1e-13){ converged = true; break; }
  }
  const values = {};
  for (const k of keys){
    const w = Wd[k];
    values[k] = Math.abs(u[k] - u0[k]) < 1e-15 ? base[k] : w.lo + (w.hi - w.lo)*u[k];
  }
  return { values, base, position:u, drive, couplingNorm:cnorm,
           unique: cnorm < 4.0,
           amplification: cnorm < 4.0 ? 1/(1 - cnorm/4) : Infinity,
           iterations: it, converged };
}

/* ── E3 — σ_sys ───────────────────────────────────────────────────────── */
function sigmaSys(R, s, wS, wX, wF, wH){
  const O = R.opt;
  const market = 0.5*(s.p_vix + s.p_bondvol);
  const base = wS*market + wX*s.p_gpr + wH*s.p_health;
  const friction = 1.0 + wF*s.p_stlfsi;
  const composite = base*friction;
  const total = Math.max(base,1e-12);
  const z = (composite - O.c_bar)/Math.max(O.s_c,1e-9);
  const zFund = (s.p_stlfsi - 0.5)*4.0, zGen = (market - 0.5)*4.0;
  return { sigma:clamp(logistic(z)), composite,
           marketShare: wS*market/total, newsShare: wX*s.p_gpr/total,
           healthShare: wH*s.p_health/total, frictionMult: friction,
           sigmaFund: clamp(logistic(zFund)), sigmaGen: clamp(logistic(zGen)) };
}

/* ── E4 / E5 — Φ_sys, s_US ────────────────────────────────────────────── */
function phiSys(G,RU,M,T,p0,pG,pR,pM,pT){ return p0 + pG*G - pR*RU + pM*M - pT*T; }
function sUsSys(G,RU,E,T,g0,gG,gR,gE,gT){
  return logistic(g0 + gG*G - gR*RU - gE*E - gT*T);
}

/* ── E11–E13 — M_shock ────────────────────────────────────────────────── */
function mShock(R, lamF){
  const O = R.opt; let tot = 0.0;
  for (const c of R.omega){
    const age = O.t_now - c[0];
    if (age < 0) continue;
    const rho = Math.max(0.0, 1.0 - age/O.T_career);
    tot += c[1]*Math.exp(-lamF*age)*rho;
  }
  return clamp(tot/Math.max(O.mnorm,1e-9));
}

/* ── E6 — κ_sys ───────────────────────────────────────────────────────── */
function kappaSys(kb,V,M,A,sig,RU,H,I,aV,aM,aA,aS,kR,aH,aI){
  const f = {
    "κ_base": kb,
    "(1+a_V·V_USD)": 1+aV*V, "(1+a_M·M_shock)": 1+aM*M,
    "(1+a_A·A_meta)": 1+aA*A, "(1+a_σ·σ_sys)": 1+aS*sig,
    "(1−κ_R·R_US)": 1-kR*RU, "(1+a_H·H_soc)": 1+aH*H,
    "(1+a_I·I_imp)": 1+aI*I };
  let k = 1.0; for (const key in f) k *= f[key];
  const kmax = kb*(1+aV)*(1+aM)*(1+aA)*(1+aS)*(1+aH)*(1+aI);
  return { kappa:k, factors:f, kappaMax:kmax };
}

/* ── E7 ∘ E7b — điểm bất động Tầng 4, Eq (8.8) ───────────────────────── */
function psychoFixedPoint(R, L, bF, fHard){
  const O = R.opt;
  const kA = L.A_alg*L.C_src*L.P_AI*L.T_exp;
  const K = L.S_access*L.P_habit*L.E_sys/(1.0 + L.R_fric);
  let g0 = K*O.cL0, g1 = K*O.cL1;
  if (g0 + g1 > 1.0){ const sc = 1.0/(g0+g1); g0 *= sc; g1 *= sc; }
  let H = 0.5, it = 0;
  for (it = 1; it <= 500; it++){
    const I = g0 + g1*H;
    const Hn = logistic(O.eta*(kA*I - L.R_div));
    if (Math.abs(Hn - H) < 1e-12){ H = Hn; break; }
    H = Hn;
  }
  const I = g0 + g1*H;
  const contraction = 0.25*O.eta*kA*g1;
  const Tp = O.eta*kA*dlogistic(O.eta*(kA*I - L.R_div))*g1;
  const amp = Tp < 1.0 ? 1/(1-Tp) : Infinity;
  const V = O.v0*H*(1+O.bA*L.A_alg)*(1+O.bP*L.P_AI)*(1+bF*fHard);
  return { H_soc:clamp(H), I_imp:clamp(I), kappa_A:kA, g0, g1, contraction,
           unique: contraction < 4.0, amplification:amp, iterations:it,
           V_meme:V, B_phase:clamp(H*I) };
}

/* ── E24 / E8 — f_hard, Ψ_str, k_Ψ ───────────────────────────────────── */
function fHardAgg(Ca,Tf,Au,wC,wT,wCT,wAu){
  const Cw = (1-wAu)*Ca + wAu*Au;
  return clamp(wC*Cw + wT*Tf - wCT*Cw*Tf);
}
function psiStr(fh,Lmax,th0,kps){ return 1.0 - Lmax*logistic(kps*(fh - th0)); }
function kPsiFn(R,kb,H,V,I){
  const c = R.opt.kpsiC, O = R.opt;
  const num = (1+c[0]*H)*(1+c[1]*V)*(1+c[2]*I);
  const den = (1+c[0]*O.kpsiH0)*(1+c[1]*O.kpsiV0)*(1+c[2]*O.kpsiI0);
  return kb*num/Math.max(den,1e-12);
}

/* ── E9 — lắp toàn bộ, kèm vòng ngoài layers ↔ Layer W ───────────────── */
function run(R, state, ov, opt){
  opt = Object.assign({ enState:true, enCoup:true, enHealth:false,
    enReturn:false, enReversal:false, splitPrec:false, havenFunding:false,
    recentre:false, regimeLambda:false, susInside:true, reversal:0.0 }, opt||{});
  const L = state.latents, warn = [];
  let z = { sigma:0.35, phi:0.5, sus:0.70, hsoc:0.30, iimp:0.30,
            fhard:0.34, rus:("R_US" in L ? L.R_US : 0.2), psi:0.0 };
  let wsol=null, sig=null, psy=null, kap=null;
  let phi=0, sus=0, fh=0, kps=0, ms=0, psi=1.0, Tfrag=0, Soff=0;

  for (let outer = 0; outer < 12; outer++){
    wsol = solveWeights(R, z, ov, opt.enState, opt.enCoup);
    const W = wsol.values;

    sig = sigmaSys(R, state.sigmaInputs, W.w_sigma, W.w_X, W.w_F,
                   opt.enHealth ? W.w_H : 0.0);
    psy = psychoFixedPoint(R, L, opt.enReturn ? W.b_F : 0.0, z.fhard);

    Tfrag = L.T_frag; Soff = L.S_off;
    if (opt.enReversal && opt.reversal > 0){
      const r = W.r_rev*opt.reversal;
      Tfrag = clamp(Tfrag*(1-r)); Soff = clamp(Soff*(1-r));
    }
    fh = fHardAgg(L.C_alt, Tfrag, L.Au_sub, W.w_Calt, W.w_Tfrag, W.w_CT, W.w_gold);
    kps = kPsiFn(R, W.k_psi, psy.H_soc, psy.V_meme, psy.I_imp);
    psi = psiStr(fh, W.L_max, W.theta_0, kps);

    phi = phiSys(L.G_pol, L.R_US, L.M_trust, Tfrag, W.phi_0, W.phi_G, W.phi_R,
                 W.phi_M, W.phi_T);
    sus = sUsSys(L.G_pol, L.R_US, L.E_inf, Tfrag, W.gam_0, W.gam_G, W.gam_R,
                 W.gam_E, W.gam_T);

    ms = mShock(R, R.opt.lam_f);
    kap = kappaSys(W.kappa_base, L.V_USD, ms, L.A_meta, sig.sigma, L.R_US,
                   psy.H_soc, psy.I_imp, W.a_V, W.a_M, W.a_A, W.a_sigma,
                   W.kappa_R, W.a_H, W.a_I);

    const zn = { sigma:sig.sigma, phi:clamp(phi/2.0), sus, hsoc:psy.H_soc,
                 iimp:psy.I_imp, fhard:fh, rus:L.R_US, psi:clamp(1.0-psi) };
    let mx = 0.0;
    for (const k in z){ const d = Math.abs(zn[k]-z[k]); if (d > mx) mx = d; }
    z = zn;
    if (mx < 1e-11) break;
    if (outer === 11) warn.push("Vòng ngoài (layers ↔ Layer W) chưa hội tụ sau 12 lượt.");
  }

  const W = wsol.values;
  const lam = logistic(W.theta*(sig.sigma - W.sigma_star));
  const terms = [];
  let lnBracket = 0.0;

  for (const c of R.demand){
    const lvl = state.channels[c.k];
    const a = blend(c.ac, c.ax, lam);
    const lc = a*safeLog(lvl);
    lnBracket += lc;
    terms.push({ k:c.k, s:c.s, side:"D", lvl, exp:a, lc, ev:c.ev });
  }
  const aPrec = W.alpha_prec;
  const precLevel = state.channels[R.prec.k];
  const precBase = opt.susInside ? sus*precLevel : precLevel;
  const precExp  = opt.susInside ? aPrec : aPrec*sus;
  const lcP = precExp*safeLog(precBase);
  const lcPb = precExp*safeLog(opt.susInside ? sus : 1.0);
  lnBracket += (lcP - lcPb);
  terms.push({ k:"prec", s:R.prec.s, side:"D", lvl:precLevel, exp:precExp,
               lc:lcP - lcPb, ev:R.prec.ev });

  for (const c of R.supply){
    let lvl = state.channels[c.k];
    if (c.k === "ext") lvl = lvl*Math.exp(-W.delta_off*Soff);
    const b = blend(c.ac, c.ax, lam);
    const lc = -b*safeLog(lvl);
    lnBracket += lc;
    terms.push({ k:c.k, s:c.s, side:"S", lvl, exp:b, lc, ev:c.ev });
  }

  const mechanical = kap.kappa*lnBracket;
  const sigUse = opt.havenFunding ? sig.sigmaFund : sig.sigma;
  const l1 = W.lam_1, l2 = W.lam_2;
  const haven = (l1*sigUse + l2*sigUse*sigUse)*phi;
  const c0 = safeLog(state.DXY0);
  const lnDxy = safeLog(psi) + c0 + mechanical + haven;

  if (phi <= 0) warn.push("Φ_sys ≤ 0: số hạng trú ẩn ĐỔI DẤU thay vì co lại (§6.6.5).");
  if (W.kappa_R >= 1.0) warn.push("κ_R ≥ 1: κ_sys âm, mô hình đảo ngược (Assumption 7.2).");
  if (!psy.unique) warn.push("η·κ_A·g₁ = " + psy.contraction.toFixed(2)
    + " ≥ 4: điểm bất động Tầng 4 không duy nhất — tối đa ba cân bằng, cái giữa"
    + " bất ổn (Proposition 8.3). Kết quả đang đứng trên một nhánh.");
  if (!wsol.unique) warn.push("‖C‖∞ = " + wsol.couplingNorm.toFixed(2)
    + " ≥ 4: hệ trọng số không có nghiệm duy nhất (E19).");
  if (!wsol.converged) warn.push("Hệ trọng số chưa hội tụ trong số vòng lặp cho phép.");

  return { DXY:Math.exp(lnDxy), lnDXY:lnDxy, psi_str:psi, lnBracket, mechanical,
           haven, c0, sigma:sig, phi, s_us:sus, kappa:kap, psycho:psy,
           f_hard:fh, k_psi:kps, M_shock:ms, lam, weights:wsol, terms,
           warnings:warn, T_frag:Tfrag, S_off:Soff };
}

/* ── lớp hình học — phân rã, độ căng, vết sẹo ────────────────────────── */
const POS_WEIGHT = { 0:"theta_sub", 1:"sigma_star", 2:"phi_0", 3:"kappa_base",
                     4:null, 5:"theta_0", 9:null };

function tautness(arg){ return 4.0*dlogistic(arg); }

function newState(R){
  const lat = {}, ch = {};
  for (const k in R.latents) lat[k] = R.latents[k].d;
  for (const c of R.demand) ch[c.k] = 1.0;
  for (const c of R.supply) ch[c.k] = 1.0;
  ch[R.prec.k] = 1.0;
  return { latents:lat, channels:ch, sigmaInputs:Object.assign({}, R.sigin),
           DXY0:100.0 };
}
function copyState(s){
  return { latents:Object.assign({},s.latents), channels:Object.assign({},s.channels),
           sigmaInputs:Object.assign({},s.sigmaInputs), DXY0:s.DXY0 };
}

function Manifold(R, state, cfg){
  this.R = R;
  this.state = copyState(state || newState(R));
  this.cfg = Object.assign({ tau:{}, fragFeedback:false, amr:{}, baseOv:null,
    memory:"hysteresis", H_star:null, p:null, q:null, rho:null }, cfg||{});
  this._refKey = null; this._refTaut = null;
  const P = {}; for (const row of R.params) P[row[0]] = row[2];
  this.P = { H_star: this.cfg.H_star !== null ? this.cfg.H_star : P.H_star,
             p: this.cfg.p !== null ? this.cfg.p : P.p_depth,
             q: this.cfg.q !== null ? this.cfg.q : P.q_taut,
             rho: this.cfg.rho !== null ? this.cfg.rho : P.rho_frag };
  this.scar = {0:0,1:0,2:0,3:0,4:0,5:0,9:0};
  this.Tfrag0 = this.state.latents.T_frag;
  this.steps = [];
}

Manifold.prototype.overrides = function (base) {
  const ov = Object.assign({}, base||{});
  for (const sh in this.scar){
    if (this.scar[sh] <= 0) continue;
    const key = POS_WEIGHT[sh];
    if (!key) continue;
    const w = this.R.weights[key];
    ov[key] = Math.max(Math.max(w.lo, 0.05), w.b - this.scar[sh]);
  }
  return ov;
};

Manifold.prototype.referenceTaut = function (ov, fallback) {
  let empty = true; for (const k in ov){ empty = false; break; }
  if (empty) return fallback;
  const key = JSON.stringify([this.state.latents, this.state.channels,
                              this.state.sigmaInputs]);
  if (this._refKey === key) return this._refTaut;
  const r0 = run(this.R, this.state, null, this.cfg.amr);
  const Lmax = r0.weights.values.L_max;
  const kmax = Math.max(1e-9, r0.kappa.kappaMax);
  const c01 = x => Math.min(1-1e-12, Math.max(1e-12, x));
  const v = { 0:c01(r0.f_hard), 1:c01(r0.sigma.sigma), 2:c01(r0.phi),
              3:c01(r0.kappa.kappa/kmax), 4:c01(r0.psycho.H_soc),
              5:c01((1-r0.psi_str)/Math.max(1e-9,Lmax)), 9:c01(r0.sigma.sigma) };
  const out = {};
  for (const k in v) out[k] = tautness(Math.log(v[k]/(1-v[k])));
  this._refKey = key; this._refTaut = out;
  return out;
};

Manifold.prototype.step = function (move, baseOv) {
  if (baseOv === undefined || baseOv === null) baseOv = this.cfg.baseOv || null;
  if (move) {
    const s = copyState(this.state);
    if (move.latents) for (const k in move.latents) s.latents[k] = move.latents[k];
    if (move.channels) for (const k in move.channels) s.channels[k] = move.channels[k];
    if (move.sigmaInputs) for (const k in move.sigmaInputs) s.sigmaInputs[k] = move.sigmaInputs[k];
    this.state = s;
    if (move.latents && ("T_frag" in move.latents)) this.Tfrag0 = s.latents.T_frag;
  }
  if (this.cfg.fragFeedback)
    this.state.latents.T_frag = Math.min(1.0, this.Tfrag0 + this.P.rho*this.scar[2]);

  const ov = this.overrides(baseOv);
  const r = run(this.R, this.state, ov, this.cfg.amr);

  const Lmax = r.weights.values.L_max;
  const kmax = Math.max(1e-9, r.kappa.kappaMax);
  const c01 = x => Math.min(1-1e-12, Math.max(1e-12, x));
  const v = { 0:c01(r.f_hard), 1:c01(r.sigma.sigma), 2:c01(r.phi),
              3:c01(r.kappa.kappa/kmax), 4:c01(r.psycho.H_soc),
              5:c01((1-r.psi_str)/Math.max(1e-9,Lmax)), 9:c01(r.sigma.sigma) };
  const intensity = { 0:v[0], 1:v[1], 2:1-v[2], 3:v[3], 4:v[4], 5:v[5], 9:v[9] };
  const taut = {};
  for (const k in v) taut[k] = tautness(Math.log(v[k]/(1-v[k])));

  const HS = {};
  for (const k in this.R.hstar) HS[k] = +this.R.hstar[k];
  HS["4"] = this.P.H_star;

  // Độ cong THAM CHIẾU: cùng trạng thái ngoại sinh, KHÔNG có vết sẹo. Không có
  // bước này thì độ sâu đọc II từ tấm đã bị dịch, tức toán tử ăn đầu ra của
  // chính nó, và kết quả phụ thuộc cách chia thời gian.
  const tautRef = this.referenceTaut(ov, taut);

  const dt = (move && typeof move.dt === "number") ? move.dt : 1.0;
  const hyst = this.cfg.memory !== "fatigue";
  const decs = [];
  for (const e of this.R.edges){
    const src = String(e[0]), dst = String(e[1]);
    const t = this.cfg.tau[src+">"+dst] || 0.0;
    const excess = Math.max(0.0, intensity[src] - HS[src]);
    const tt = tautRef[dst] === undefined ? 0.0 : tautRef[dst];
    const depth = t*this.P.p*excess*(1.0 + this.P.q*tt);
    decs.push({ src:+src, dst:+dst, v:e[2], w:e[3], load:e[4], tau:t,
                tangential:(1-t)*e[4], normal:t*e[4], excess, taut:tt, depth });
  }
  const scarSnap = Object.assign({}, this.scar);
  for (const d of decs){
    if (d.depth <= 0) continue;
    if (!POS_WEIGHT[String(d.dst)]) continue;     // Σ₄ không có vị trí (Remark 10.2)
    const k = String(d.dst);
    if (hyst){ if (d.depth > this.scar[k]) this.scar[k] = d.depth; }
    else this.scar[k] += dt*d.depth;
  }

  const st = { i:this.steps.length, move: move ? move.name : "nền",
               r, intensity, taut, decs, overrides:ov,
               scar:scarSnap, scarAfter:Object.assign({},this.scar),
               T_frag:this.state.latents.T_frag };
  this.steps.push(st);
  return st;
};

function trace(R, moves, state, cfg, settle){
  const m = new Manifold(R, state, cfg);
  m.step(null);
  for (const mv of moves) m.step(mv);
  if (settle !== false) m.step(null);
  return m;
}
function invertMove(move, state){
  const o = { name:"gỡ "+move.name, latents:{}, channels:{}, sigmaInputs:{} };
  if (move.latents) for (const k in move.latents) o.latents[k] = state.latents[k];
  if (move.channels) for (const k in move.channels) o.channels[k] = state.channels[k];
  if (move.sigmaInputs) for (const k in move.sigmaInputs) o.sigmaInputs[k] = state.sigmaInputs[k];
  return o;
}
function commutator(R, a, b, state, cfg){
  const ab = trace(R,[a,b],state,cfg), ba = trace(R,[b,a],state,cfg);
  const la = ab.steps[ab.steps.length-1].r.lnDXY, lb = ba.steps[ba.steps.length-1].r.lnDXY;
  return { lnAB:la, lnBA:lb, norm:Math.abs(la-lb), scarAB:ab.scar, scarBA:ba.scar };
}
function holonomy(R, loop, state, cfg){
  const m = new Manifold(R, state, cfg);
  const base = m.step(null);
  const s0 = copyState(m.state);
  const close = { name:"đóng vòng", latents:{}, channels:{}, sigmaInputs:{} };
  for (const mv of loop){
    if (mv.latents) for (const k in mv.latents)
      if (!(k in close.latents)) close.latents[k] = s0.latents[k];
    if (mv.channels) for (const k in mv.channels)
      if (!(k in close.channels)) close.channels[k] = s0.channels[k];
    if (mv.sigmaInputs) for (const k in mv.sigmaInputs)
      if (!(k in close.sigmaInputs)) close.sigmaInputs[k] = s0.sigmaInputs[k];
  }
  for (const mv of loop) m.step(mv);
  m.step(close); m.step(null);
  const end = m.steps[m.steps.length-1].r.lnDXY;
  return { lnStart:base.r.lnDXY, lnEnd:end, value:end - base.r.lnDXY, scar:m.scar };
}
function residual(R, move, state, cfg){
  const m = new Manifold(R, state, cfg);
  const before = m.step(null);
  const inv = invertMove(move, m.state);
  const shocked = m.step(move);
  m.step(inv);
  const after = m.step(null);
  return { lnBefore:before.r.lnDXY, lnShocked:shocked.r.lnDXY, lnAfter:after.r.lnDXY,
           value: before.r.lnDXY - after.r.lnDXY, scar:m.scar };
}

root.AMR = { logistic, logit, dlogistic, clamp, safeLog, blend, solveWeights,
  sigmaSys, phiSys, sUsSys, mShock, kappaSys, psychoFixedPoint, fHardAgg,
  psiStr, kPsiFn, run, tautness, newState, copyState, Manifold, trace,
  commutator, holonomy, residual, invertMove, POS_WEIGHT };

})(typeof module !== "undefined" && module.exports ? module.exports : (this.window||this));
