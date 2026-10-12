const fs=require('fs'), AMR=require('./engine.js').AMR;
const R=JSON.parse(fs.readFileSync(__dirname+'/reg.json','utf8'));
const G=JSON.parse(fs.readFileSync(__dirname+'/gvecs.json','utf8'));
let worst={}, nbad=0;
const tr=(k,a,b)=>{const d=Math.abs(a-b); if(!(k in worst)||d>worst[k])worst[k]=d; return d;};
G.forEach((g,i)=>{
  const tau={};
  for(const e of R.edges){ const s=String(e[0]),d=String(e[1]);
    if(g.full ? s==="4" : (s==="4"&&d==="5")) tau[s+">"+d]=g.tau; }
  const cfg={tau, fragFeedback:g.fb, memory:g.mode};
  const M={name:"MEME",latents:g.mlat,dt:g.dt}, H={name:"CUNG",latents:g.hlat};
  const c=AMR.commutator(R,M,H,null,cfg);
  const h=AMR.holonomy(R,[M,H],null,cfg);
  const r=AMR.residual(R,M,null,cfg);
  const t=AMR.trace(R,[M,H],null,cfg);
  const last=t.steps[t.steps.length-1];
  let bad=null;
  const chk=[['comm',c.norm,g.comm],['lnAB',c.lnAB,g.lnAB],['lnBA',c.lnBA,g.lnBA],
    ['hol',h.value,g.hol],['res',r.value,g.res],['ln',last.r.lnDXY,g.ln],
    ['Tfrag',last.T_frag,g.Tfrag],
    ['th0',last.overrides.theta_0===undefined?R.weights.theta_0.b:last.overrides.theta_0,g.th0]];
  for(const [k,a,b] of chk) if(tr(k,a,b)>1e-9) bad=bad||[k,a,b];
  for(const s in g.scar) if(tr('scar'+s,(t.scar[s]||0),g.scar[s])>1e-9) bad=bad||['scar'+s,t.scar[s],g.scar[s]];
  for(const s in g.inten) if(tr('int'+s,last.intensity[s],g.inten[s])>1e-9) bad=bad||['int'+s,last.intensity[s],g.inten[s]];
  for(const s in g.taut) if(tr('taut'+s,last.taut[s],g.taut[s])>1e-9) bad=bad||['taut'+s,last.taut[s],g.taut[s]];
  if(bad){nbad++; if(nbad<=4) console.log(`vector ${i} (tau=${g.tau} full=${g.full} fb=${g.fb}) LỆCH ${bad[0]}: js=${bad[1]} py=${bad[2]}`);}
});
const ks=Object.keys(worst).sort((a,b)=>worst[b]-worst[a]);
console.log(`\n${G.length} vector hình học, ${nbad} lệch quá 1e-9`);
ks.slice(0,6).forEach(k=>console.log(`  ${k.padEnd(10)} ${worst[k].toExponential(3)}`));
