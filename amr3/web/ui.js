(function(){
"use strict";
const A = window.AMR, R = window.REG;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const hx  = n => new THREE.Color(css(n) || "#888");

/* ── số ───────────────────────────────────────────────────────────────── */
const dc = (v,n) => (v===undefined||v===null||!isFinite(v)) ? "—"
  : v.toFixed(n===undefined?3:n).replace(".",",");
function sci(v,sign){
  if (!isFinite(v)) return "∞";
  if (Math.abs(v) < 1e-15) return (sign?"+":"")+"0,000e+0";
  const [m,e] = v.toExponential(3).split("e");
  return (sign && v>0 ? "+" : "") + m.replace(".",",")
    + "e" + (+e>=0?"+":"-") + Math.abs(+e);
}
const SUB = {0:"₀",1:"₁",2:"₂",3:"₃",4:"₄",5:"₅",9:"⊥"};
const SHN = {0:"Σ₀ cơ học",1:"Σ₁ trạng thái",2:"Σ₂ cấu trúc",3:"Σ₃ phản thân",
  4:"Σ₄ tâm lý-kỹ thuật",5:"Σ₅ thế kỷ",9:"⊥ trú ẩn"};
const SHORD = [0,1,2,3,4,5,9];

/* ── ô tự điền: tra từ R.hand ─────────────────────────────────────────── */
const HAND = {};
for (const sh in R.hand) for (const row of R.hand[sh]) HAND[row[0]] = row[1];

/* ── phân loại khoá ───────────────────────────────────────────────────── */
const CHKEYS = {};
R.demand.forEach(c => CHKEYS[c.k] = c);
R.supply.forEach(c => CHKEYS[c.k] = c);
CHKEYS[R.prec.k] = R.prec;
const SIGK = [["p_vix","p_VIX"],["p_bondvol","p_bondvol"],["p_gpr","p_GPRD"],
  ["p_stlfsi","p_STLFSI"],["p_health","p_health"]];
const kindOf = k => (k in R.weights) ? "w" : ((k in R.latents) ? "l"
  : ((k in CHKEYS) ? "c" : null));

/* ── trạng thái trang ─────────────────────────────────────────────────── */
const P0 = {}; R.params.forEach(r => P0[r[0]] = r[2]);
const S = { st:A.newState(R), ov:{}, tau:{}, geo:{}, A:{}, B:{},
            memory:"hysteresis", dt:1.0 };
function reset(){
  S.st = A.newState(R);
  S.ov = {};
  S.tau = {};
  for (const e of R.edges) S.tau[e[0]+">"+e[1]] = 0.0;
  S.geo = { H_star:P0.H_star, p:P0.p_depth, q:P0.q_taut, rho:P0.rho_frag };
  S.memory = "hysteresis"; S.dt = 1.0;
  S.A = {}; S.B = {};
  ["A_alg","C_src","P_AI","T_exp","S_access","P_habit","E_sys","A_meta"]
    .forEach(k => S.A[k] = 0.90);
  S.A.R_div = 0.10;
  S.B = { C_alt:0.62, T_frag:0.70, Au_sub:0.60 };
}
reset();

/* ── xây bảng điền số ─────────────────────────────────────────────────── */
function row(key, label, get, set, lo, hi, step, hand, sym){
  const f = document.createElement("div");
  f.className = "f" + (hand ? " hand" : "");
  const id = "i_" + key.replace(/[^\w]/g,"_");
  f.innerHTML = '<label for="'+id+'">'+(sym||key)
    + (label ? '<i>'+label+'</i>' : '') + '</label>'
    + '<input type="number" id="'+id+'" step="'+step+'" min="'+lo+'" max="'+hi+'">'
    + '<input type="range" id="'+id+'_r" min="'+lo+'" max="'+hi+'" step="'+step+'" '
    + 'aria-label="'+(sym||key)+'">';
  const num = f.querySelector("input[type=number]"), rng = f.querySelector("input[type=range]");
  const sync = () => { const v = get(); num.value = v; rng.value = v; };
  const push = v => {
    v = parseFloat(v); if (!isFinite(v)) return;
    set(Math.min(Math.max(v,lo),hi)); sync(); schedule();
  };
  num.addEventListener("change", () => push(num.value));
  rng.addEventListener("input", () => push(rng.value));
  f.__sync = sync; sync();
  return f;
}

const SECS = [];
function section(title, count, open){
  const d = document.createElement("details");
  d.className = "sec"; if (open) d.open = true;
  d.innerHTML = '<summary>'+title+'<i>'+count+'</i></summary>';
  const box = document.createElement("div");
  box.className = "fields"; d.appendChild(box);
  document.getElementById("secs").appendChild(d);
  SECS.push(d);
  return box;
}

function buildInputs(){
  document.getElementById("secs").innerHTML = ""; SECS.length = 0;

  for (const sh of SHORD){
    const lat = [], wgt = [];
    for (const k in R.atlas){
      const a = R.atlas[k];
      if (a.sh !== sh) continue;
      const kd = kindOf(k);
      if (kd === "w") wgt.push(k); else lat.push(k);
    }
    lat.sort(); wgt.sort();
    const extra = (sh === 1) ? SIGK.length : 0;
    const n = lat.length + wgt.length + extra;
    if (!n) continue;
    const box = section(SHN[sh], n + " biến", sh === 4 || sh === 5);

    if (sh === 1) for (const [k,lbl] of SIGK)
      box.appendChild(row("sg_"+k, lbl, () => S.st.sigmaInputs[k],
        v => S.st.sigmaInputs[k] = v, 0, 1, 0.01, false, lbl));

    for (const k of lat){
      const kd = kindOf(k);
      if (kd === "l"){
        const L = R.latents[k];
        box.appendChild(row(k, L.vi, () => S.st.latents[k],
          v => S.st.latents[k] = v, 0, 1, 0.01, k in HAND, L.s));
      } else if (kd === "c"){
        const c = CHKEYS[k];
        box.appendChild(row(k, c.vi, () => S.st.channels[k],
          v => S.st.channels[k] = v, 0.3, 3.0, 0.01, false, c.s));
      }
    }
    for (const k of wgt){
      const w = R.weights[k];
      box.appendChild(row(k, w.vi, () => (k in S.ov) ? S.ov[k] : w.b,
        v => S.ov[k] = v, w.lo, w.hi, (w.hi-w.lo)/200, false, w.s));
    }
  }

  const tb = section("số hoành τ trên bảy cạnh", R.edges.length + " cạnh", true);
  for (const e of R.edges){
    const key = e[0]+">"+e[1];
    tb.appendChild(row("tau_"+key, "qua "+e[3], () => S.tau[key],
      v => S.tau[key] = v, 0, 1, 0.002, false,
      "τ Σ"+SUB[e[0]]+"→Σ"+SUB[e[1]]));
  }

  const gb = section("bốn hằng số hình học", "4", false);
  const GM = [["H_star","H*","ngưỡng trên cường độ Σ₄"],
    ["p","p","độ sâu mỗi đơn vị vượt ngưỡng"],
    ["q","q","hệ số độ cong"],["rho","ρ","vết dịch Σ₂ → T_frag"]];
  const PK = { H_star:"H_star", p:"p_depth", q:"q_taut", rho:"rho_frag" };
  for (const [k,sym,lbl] of GM){
    const pr = R.params.find(r => r[0] === PK[k]);
    gb.appendChild(row("geo_"+k, lbl, () => S.geo[k], v => S.geo[k] = v,
      pr[3], pr[4], (pr[4]-pr[3])/200, true, sym));
  }

  const pb = section("hai nhiễu để đo ba đại lượng",
    Object.keys(S.A).length + " + " + Object.keys(S.B).length, false);
  const hd = t => { const h = document.createElement("p");
    h.className = "fh"; h.textContent = t; pb.appendChild(h); };
  hd("nhiễu a — các giá mang Σ₄");
  for (const k of Object.keys(S.A))
    pb.appendChild(row("A_"+k, R.latents[k].vi, () => S.A[k],
      v => S.A[k] = v, 0, 1, 0.01, false, R.latents[k].s));
  hd("thời lượng nhiễu a, tính bằng kỳ · chỉ có nghĩa ở dạng mỏi");
  pb.appendChild(row("dt", "tổng thời lượng trên ngưỡng", () => S.dt,
    v => S.dt = v, 0.25, 32, 0.25, false, "dt"));
  hd("nhiễu b — các giá mang Σ₅");
  for (const k of Object.keys(S.B))
    pb.appendChild(row("B_"+k, R.latents[k].vi, () => S.B[k],
      v => S.B[k] = v, 0, 1, 0.01, false, R.latents[k].s));
}

/* ── khung nhìn 3-D ───────────────────────────────────────────────────── */
const cv = document.getElementById("gl");
const rend = new THREE.WebGLRenderer({canvas:cv, antialias:true, alpha:true});
rend.setPixelRatio(Math.min(devicePixelRatio||1,2));
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(40,1,0.1,200);
const SW = 3.4, SD = 2.5, LH = 1.34, TRAVEL = 0.80, NSEG = 14;
const lanes = {}, G = {};

function label(text, tok, w, align){
  const c = document.createElement("canvas"), s = 2;
  c.width = 384*s; c.height = 56*s;
  const g = c.getContext("2d"); g.scale(s,s);
  g.font = "500 30px 'Roboto Mono', monospace";
  g.fillStyle = css(tok) || "#888";
  g.textBaseline = "middle"; g.textAlign = (align === "r") ? "right" : "left";
  g.fillText(text, align === "r" ? 382 : 2, 28);
  const t = new THREE.CanvasTexture(c); t.minFilter = THREE.LinearFilter;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({map:t,transparent:true,
    depthWrite:false, depthTest:false}));
  sp.scale.set(w||2.3, (w||2.3)*56/384, 1);
  return sp;
}
function dashRect(y, tok, op){
  const g = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(-SW/2,0,-SD/2), new THREE.Vector3(SW/2,0,-SD/2),
    new THREE.Vector3(SW/2,0,SD/2), new THREE.Vector3(-SW/2,0,SD/2),
    new THREE.Vector3(-SW/2,0,-SD/2)]);
  const l = new THREE.Line(g, new THREE.LineDashedMaterial({color:hx(tok),
    dashSize:0.1, gapSize:0.08, transparent:true, opacity:op}));
  l.computeLineDistances(); l.position.y = y; return l;
}

function buildScene(){
  while (scene.children.length) scene.remove(scene.children[0]);
  const LANE = {0:0,1:1,2:2,3:3,4:4,5:5,9:2.5};
  SHORD.forEach(sh => {
    const base = LANE[sh]*LH;
    lanes[sh] = base;
    const geo = new THREE.PlaneGeometry(SW, SD, NSEG, Math.round(NSEG*SD/SW));
    geo.rotateX(-Math.PI/2);
    const pos0 = Float32Array.from(geo.attributes.position.array);
    const fill = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({color:hx("--sheet"),
      transparent:true, opacity:0.1, side:THREE.DoubleSide, depthWrite:false}));
    const wire = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({color:hx("--sheet"),
      wireframe:true, transparent:true, opacity:0.3, depthWrite:false}));
    const grp = new THREE.Group(); grp.add(fill); grp.add(wire);
    const lb = label(SHN[sh], "--muted", 2.9, "r");
    lb.position.set(-SW/2 - 2.45, 0.30, 0.10);
    const vl = label("", "--fg", 2.7, "l");
    vl.position.set(SW/2 + 1.70, 0.18, 0.10);
    grp.add(lb); grp.add(vl);
    if (sh === 9) {
      grp.rotation.z = Math.PI/2;
      grp.scale.setScalar(0.52);
      grp.position.x = SW*1.62;
      lb.position.set(0.30, -SW/2 - 2.0, 0.10);
      lb.scale.multiplyScalar(1/0.52);
      vl.visible = false;
    }
    scene.add(grp);
    const lo = dashRect(base, "--muted", 0.45), hi = dashRect(base + TRAVEL, "--muted", 0.45);
    const gh = dashRect(base, "--scar", 0.0);
    scene.add(lo); scene.add(hi); scene.add(gh);
    G[sh] = { grp, geo, pos0, fill, wire, lo, hi, gh, lb, vl, base };
  });
  G.arrows = [];
  for (let i = 0; i < R.edges.length*2; i++){
    const a = new THREE.ArrowHelper(new THREE.Vector3(1,0,0), new THREE.Vector3(),
      0.001, hx(i%2 ? "--norm" : "--tang").getHex(), 0.19, 0.11);
    scene.add(a); G.arrows.push(a);
  }
  G.rings = {};
  for (const sh of SHORD){
    const t = new THREE.Mesh(new THREE.TorusGeometry(0.17,0.024,8,26),
      new THREE.MeshBasicMaterial({color:hx("--scar"),transparent:true,opacity:0}));
    t.rotation.x = Math.PI/2; scene.add(t); G.rings[sh] = t;
  }
}

let yaw = -0.58, pitch = 0.235, dist = 15.2, drag = false, px = 0, py = 0;
const FOCUS = new THREE.Vector3(-0.30, LH*2.72, 0.20);
function place(){
  cam.position.set(FOCUS.x + dist*Math.cos(pitch)*Math.sin(yaw),
    FOCUS.y + dist*Math.sin(pitch),
    FOCUS.z + dist*Math.cos(pitch)*Math.cos(yaw));
  cam.lookAt(FOCUS);
}
cv.addEventListener("pointerdown", e => { drag = true; px = e.clientX; py = e.clientY;
  cv.classList.add("drag"); cv.setPointerCapture(e.pointerId); });
cv.addEventListener("pointerup", e => { drag = false; cv.classList.remove("drag");
  try{ cv.releasePointerCapture(e.pointerId); }catch(_){} });
cv.addEventListener("pointermove", e => { if(!drag) return;
  yaw -= (e.clientX-px)*0.006;
  pitch = Math.max(-0.25, Math.min(1.1, pitch + (e.clientY-py)*0.005));
  px = e.clientX; py = e.clientY; place(); });
cv.addEventListener("wheel", e => { e.preventDefault();
  dist = Math.max(7, Math.min(26, dist + Math.sign(e.deltaY)*0.7)); place();
}, {passive:false});
/* Khung hẹp thì bề ngang mới là ràng buộc, nên nhãn và tấm ⊥ co vào cùng lúc
   camera lùi ra — nếu chỉ lùi camera thì mô hình teo lại giữa hai dải trống. */
let narrow = null;
function relayout(nw){
  if (nw === narrow) return;
  narrow = nw;
  // Ở khung hẹp, chữ 3-D xuống còn vài pixel nên vô dụng. Tắt nhãn và để bảng
  // bên dưới mang số; khung nhìn khi đó chỉ còn là hình, và hình thì lớn lên.
  for (const sh of SHORD){
    const g = G[sh]; if (!g) continue;
    g.lb.visible = !nw;
    g.vl.visible = !nw && sh !== 9;
    if (sh === 9) g.grp.position.x = SW*(nw ? 1.02 : 1.62);
    else {
      g.lb.position.set(-SW/2 - 2.45, 0.30, 0.10);
      g.vl.position.set(SW/2 + 1.70, 0.18, 0.10);
    }
  }
  FOCUS.x = nw ? SW*0.42 : -0.30;
}
function fit(){
  const t = Math.tan(cam.fov*Math.PI/360);
  const ex = narrow ? 3.9 : 7.4, ey = narrow ? 4.3 : 4.6;
  dist = Math.min(30, Math.max(8, Math.max(ey/t, ex/(t*cam.aspect))*1.04));
  place();
}
function resize(){
  const w = cv.clientWidth, h = cv.clientHeight; if(!w||!h) return;
  rend.setSize(w,h,false); cam.aspect = w/h; cam.updateProjectionMatrix();
  relayout(cam.aspect < 1.35); fit(); schedule();
}

/* ── tính và vẽ ───────────────────────────────────────────────────────── */
function moveA(){ return { name:"a", latents:Object.assign({}, S.A), dt:S.dt }; }
function moveB(){ return { name:"b", latents:Object.assign({}, S.B) }; }
function cfg(){
  return { tau:Object.assign({}, S.tau), fragFeedback:false,
    baseOv:Object.assign({}, S.ov), memory:S.memory,
    H_star:S.geo.H_star, p:S.geo.p, q:S.geo.q, rho:S.geo.rho, amr:{} };
}

function compute(){
  const c = cfg(), stt = A.copyState(S.st);
  const t = A.trace(R, [moveA(), moveB()], stt, c);
  const last = t.steps[t.steps.length-1];
  return {
    last,
    comm: A.commutator(R, moveA(), moveB(), stt, c),
    hol:  A.holonomy(R, [moveA(), moveB()], stt, c),
    res:  A.residual(R, moveA(), stt, c),
    scar: t.scar
  };
}

function paint(){
  let Q;
  try { Q = compute(); }
  catch(err){ document.getElementById("warns").innerHTML =
    '<div class="warn"><k>lỗi tính</k><span>'
    + String(err.message||err) + "</span></div>"; return; }

  const st = Q.last, r = st.r, W = r.weights.values;

  document.getElementById("hLn").textContent  = dc(r.lnDXY,6);
  document.getElementById("hPsi").textContent = dc(r.psi_str,5);
  document.getElementById("hKap").textContent = dc(r.kappa.kappa,4);
  document.getElementById("hLam").textContent = dc(r.lam,4);
  let sT = 0, sN = 0, sS = 0;
  for (const d of st.decs){ sT += Math.abs(d.tangential); sN += Math.abs(d.normal); }
  for (const k in Q.scar) sS += Q.scar[k];
  document.getElementById("hTang").textContent = dc(sT,3);
  document.getElementById("hNorm").textContent = dc(sN,3);
  document.getElementById("hScar").textContent = dc(sS,4);

  const G4 = (id,el,v,txt) => { document.getElementById(el).textContent = txt;
    document.getElementById(id).dataset.z = Math.abs(v) < 1e-12 ? "1" : "0"; };
  G4("gC","vC",Q.comm.norm, sci(Q.comm.norm,false));
  G4("gH","vH",Q.hol.value, sci(Q.hol.value,true));
  G4("gR","vR",Q.res.value, (Q.res.value>=0?"+":"") + dc(Q.res.value,6));
  document.getElementById("vCn").textContent = dc(r.weights.couplingNorm,3);
  document.getElementById("vCt").textContent = dc(r.psycho.contraction,3);

  const cap = (R.ceilings && R.ceilings[S.memory]) || R.ceiling;
  const over = Object.keys(S.tau).filter(k => S.tau[k] > cap + 1e-12);
  if (over.length) r.warnings = r.warnings.concat(
    ["τ = " + dc(Math.max.apply(null, over.map(k => S.tau[k])), 3)
     + " vượt trần " + dc(cap, 3) + " của dạng "
     + (S.memory === "fatigue" ? "mỏi" : "trễ")
     + ". Cùng ngân sách thực nghiệm, một đơn vị τ sinh lượng ξ khác nhau ở hai"
     + " dạng, nên trần khác nhau: trễ " + dc(R.ceilings.hysteresis,3)
     + ", mỏi " + dc(R.ceilings.fatigue,3) + "."]);
  const wb = document.getElementById("warns");
  wb.innerHTML = r.warnings.length
    ? '<div class="warn"><k>engine</k>'
      + r.warnings.map(w => "<span>"+w+"</span>").join("") + "</div>" : "";

  /* ── hình học ─────────────────────────────────────────────────────── */
  const inten = st.intensity, taut = st.taut;
  for (const sh of SHORD){
    const g = G[sh], pk = A.POS_WEIGHT[String(sh)];
    let u = 0.5, hasPos = !!pk, val = null, zone = null, moved = 0;
    if (hasPos){
      const w = R.weights[pk];
      val = W[pk]; zone = [w.lo, w.hi];
      u = (val - w.lo) / Math.max(1e-12, w.hi - w.lo);
      const b0 = (pk in S.ov) ? S.ov[pk] : w.b;
      moved = Math.max(0, b0 - val);
    }
    const y = g.base + TRAVEL*Math.min(1,Math.max(0,u));
    const II = taut[sh] === undefined ? 0 : taut[sh];
    const scar = Q.scar[String(sh)] || 0;
    const dent = Math.min(0.46, scar*0.9);

    const p = g.geo.attributes.position, b = g.pos0;
    const rmax2 = (SW/2)*(SW/2) + (SD/2)*(SD/2);
    for (let i = 0; i < p.count; i++){
      const x = b[i*3], z = b[i*3+2], r2 = x*x + z*z;
      p.array[i*3+1] = b[i*3+1]
        + II*0.16*(r2/rmax2)                       // độ cong: II = 4Λ′
        - dent*Math.exp(-r2/(2*0.40*0.40));        // vị trí đã dịch tại chỗ
    }
    p.needsUpdate = true; g.geo.computeBoundingSphere();
    g.grp.position.y = y;
    g.fill.material.opacity = 0.05 + 0.26*Math.min(1,Math.max(0,inten[sh]||0));
    g.wire.material.opacity = 0.16 + 0.34*Math.min(1,Math.max(0,inten[sh]||0));
    g.lo.visible = g.hi.visible = hasPos;
    g.gh.position.y = g.base + TRAVEL*(hasPos
      ? ((((pk in S.ov) ? S.ov[pk] : R.weights[pk].b) - zone[0])
         / Math.max(1e-12, zone[1]-zone[0])) : 0.5);
    g.gh.material.opacity = moved > 1e-9 ? 0.75 : 0.0;
    g.vl.material.map.dispose();
    const txt = hasPos
      ? (R.weights[pk].s + " " + dc(val,3) + (moved>1e-9 ? "  ↓"+dc(moved,3) : ""))
      : "không có vị trí";
    const nl = label(txt, moved>1e-9 ? "--scar" : (hasPos ? "--fg" : "--muted"),
                     2.7, "l");
    g.vl.material = nl.material; g.vl.scale.copy(nl.scale);
    g.vl.visible = !narrow && sh !== 9;
    G.rings[sh].position.set(g.grp.position.x, y - dent + 0.012, g.grp.position.z);
    G.rings[sh].material.opacity = scar > 1e-9 ? 0.9 : 0.0;
    G.rings[sh].scale.setScalar(0.8 + Math.min(1.9, scar*2.0));
  }

  st.decs.forEach((d,i) => {
    const gt = G[d.dst]; if (!gt) return;
    const yT = gt.grp.position.y;
    const at = G.arrows[i*2], an = G.arrows[i*2+1];
    const L = 1.45, MIN = 0.16;
    const off = -SD/2 + 0.3 + (i%7)*(SD-0.6)/6;
    const x0 = -SW/2 + 0.26, y0 = yT + 0.05;
    at.position.set(x0, y0, off);
    at.setDirection(new THREE.Vector3(1,0,0));
    at.setLength(Math.max(MIN, Math.abs(d.tangential)*L), 0.17, 0.1);
    at.visible = Math.abs(d.tangential) > 0.004;
    an.position.set(x0, y0, off);
    an.setDirection(new THREE.Vector3(0,-1,0));
    an.setLength(Math.max(MIN, Math.abs(d.normal)*L), 0.17, 0.1);
    an.visible = Math.abs(d.normal) > 0.004;
  });

  /* ── bảng ─────────────────────────────────────────────────────────── */
  const nvar = {}; for (const k in R.atlas){
    const s = R.atlas[k].sh; nvar[s] = (nvar[s]||0)+1; }
  document.getElementById("tSheets").innerHTML = SHORD.map(sh => {
    const pk = A.POS_WEIGHT[String(sh)];
    const w = pk ? R.weights[pk] : null;
    const val = pk ? W[pk] : null;
    const b0 = pk ? ((pk in S.ov) ? S.ov[pk] : w.b) : null;
    const mv = pk ? Math.max(0, b0 - val) : 0;
    const raw = Q.scar[String(sh)] || 0;
    const capped = pk && raw > mv + 1e-9;
    const span = w ? Math.max(1e-12, w.hi - w.lo) : 1;
    const wMv  = w ? 54*Math.min(1, mv/span) : 0;
    const wCap = w ? 54*Math.min(1 - Math.min(1,mv/span), (raw-mv)/span) : 0;
    const bar = (v, cls) => '<span class="track"><i class="fill '+cls
      + '" style="width:'+(54*Math.min(1,Math.max(0,v))).toFixed(1)+'px"></i></span>';
    return '<tr><td>'+SHN[sh]+"</td>"
      + '<td class="k">'+(w ? w.s : "—")+"</td>"
      + '<td class="z">'+(w ? "["+dc(w.lo,2)+", "+dc(w.hi,2)+"]" : "—")+"</td>"
      + "<td>"+(w ? dc(val,4) : "—")+"</td>"
      + '<td class="'+(raw>1e-9?"s":"z")+'">'+(raw>1e-9 ? dc(raw,4) : "0")+"</td>"
      + '<td class="'+(mv>1e-9?"s":"z")+'">'+(w ? (mv>1e-9 ? "−"+dc(mv,4) : "0") : "—")
        + (w ? '<span class="track"><i class="fill s" style="width:'+wMv.toFixed(1)
             + 'px"></i><i class="cap" style="width:'+Math.max(0,wCap).toFixed(1)
             + 'px"></i></span>' : "")
        + "</td>"
      + "<td>"+dc(inten[sh],4)+bar(inten[sh]||0,"")+"</td>"
      + "<td>"+dc(taut[sh],4)+bar(taut[sh]||0,"t")+"</td>"
      + '<td class="z">'+(nvar[sh]||0)+"</td></tr>";
  }).join("");

  document.getElementById("tEdges").innerHTML = st.decs.map(d => {
    const a = R.atlas[d.w];
    return "<tr>"
      + "<td>Σ"+SUB[d.src]+" → Σ"+SUB[d.dst]+"</td>"
      + '<td class="k">'+d.v+"</td>"
      + '<td class="k">'+d.w+"</td>"
      + '<td class="z">'+(a?a.role:"—")+"</td>"
      + '<td class="'+(Math.abs(d.load)<1e-12?"z":"")+'">'
        + (d.load>=0?"+":"")+dc(d.load,2)+"</td>"
      + '<td class="'+(d.tau>1e-9?"":"z")+'">'+dc(d.tau,3)+"</td>"
      + '<td class="g">'+dc(d.tangential,3)+"</td>"
      + '<td class="'+(Math.abs(d.normal)>1e-9?"n":"z")+'">'+dc(d.normal,3)+"</td>"
      + '<td class="'+(d.excess>1e-9?"":"z")+'">'+dc(d.excess,4)+"</td>"
      + '<td class="'+(d.depth>1e-9?"s":"z")+'">'+dc(d.depth,5)+"</td></tr>";
  }).join("");

  const mx = r.terms.reduce((s,t) => Math.max(s, Math.abs(t.lc)), 1e-9);
  document.getElementById("tTerms").innerHTML = r.terms.map(t =>
    "<tr><td>"+t.s+"</td>"
    + '<td class="z">'+t.side+"</td>"
    + "<td>"+dc(t.lvl,4)+"</td><td>"+dc(t.exp,4)+"</td>"
    + '<td class="'+(t.lc<0?"n":"g")+'">'+(t.lc>=0?"+":"")+dc(t.lc,5)+"</td>"
    + '<td><span class="track"><i class="fill '+(t.lc<0?"n":"t")+'" style="width:'
    + (54*Math.abs(t.lc)/mx).toFixed(1)+'px"></i></span></td>'
    + '<td class="z">'+t.ev+"</td></tr>").join("");
}

let pending = false;
function schedule(){ if (pending) return; pending = true;
  requestAnimationFrame(() => { pending = false; paint(); }); }

function syncAll(){
  document.querySelectorAll(".f").forEach(f => { if (f.__sync) f.__sync(); });
}
document.getElementById("bBase").addEventListener("click", () => {
  reset(); syncAll(); schedule(); });
document.getElementById("bRand").addEventListener("click", () => {
  const rnd = (a,b) => a + Math.random()*(b-a);
  for (const k in S.st.latents) S.st.latents[k] = +rnd(0.05,0.95).toFixed(3);
  for (const k in S.st.channels) S.st.channels[k] = +Math.exp(rnd(-0.3,0.3)).toFixed(4);
  for (const [k] of SIGK) S.st.sigmaInputs[k] = +rnd(0.05,0.95).toFixed(3);
  for (const e of R.edges) S.tau[e[0]+">"+e[1]] = +rnd(0, R.ceiling).toFixed(3);
  syncAll(); schedule();
});
const mHy = document.getElementById("mHy"), mFa = document.getElementById("mFa");
function setMemory(m){
  S.memory = m;
  mHy.setAttribute("aria-pressed", String(m === "hysteresis"));
  mFa.setAttribute("aria-pressed", String(m === "fatigue"));
  schedule();
}
mHy.addEventListener("click", () => setMemory("hysteresis"));
mFa.addEventListener("click", () => setMemory("fatigue"));

document.getElementById("bOpen").addEventListener("click",
  () => SECS.forEach(d => d.open = true));
document.getElementById("bShut").addEventListener("click",
  () => SECS.forEach(d => d.open = false));

function loop(){ rend.render(scene, cam); requestAnimationFrame(loop); }
buildInputs(); buildScene(); resize(); paint(); loop();
addEventListener("resize", resize);
matchMedia("(prefers-color-scheme: dark)").addEventListener("change",
  () => location.reload());
})();
