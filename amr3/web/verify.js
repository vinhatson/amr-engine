const fs=require('fs');
const AMR=require('./engine.js').AMR;
const R=JSON.parse(fs.readFileSync(__dirname+'/reg.json','utf8'));
const V=JSON.parse(fs.readFileSync(__dirname+'/vecs.json','utf8'));
let worst={}, nbad=0;
const track=(k,a,b)=>{const d=Math.abs(a-b); if(!(k in worst)||d>worst[k])worst[k]=d; return d;};
V.forEach((v,i)=>{
  const st={latents:v.lat, channels:v.ch, sigmaInputs:v.sg, DXY0:100.0};
  const r=AMR.run(R, st, v.ov, {});
  const chk=[['ln',r.lnDXY,v.out.ln],['psi',r.psi_str,v.out.psi],['phi',r.phi,v.out.phi],
    ['sus',r.s_us,v.out.sus],['kap',r.kappa.kappa,v.out.kap],['kmax',r.kappa.kappaMax,v.out.kmax],
    ['sig',r.sigma.sigma,v.out.sig],['H',r.psycho.H_soc,v.out.H],['I',r.psycho.I_imp,v.out.I],
    ['V',r.psycho.V_meme,v.out.V],['fh',r.f_hard,v.out.fh],['kps',r.k_psi,v.out.kps],
    ['ms',r.M_shock,v.out.ms],['lam',r.lam,v.out.lam],['brk',r.lnBracket,v.out.brk],
    ['hav',r.haven,v.out.hav],['cn',r.weights.couplingNorm,v.out.cn]];
  let bad=null;
  for(const [k,a,b] of chk){ if(track(k,a,b)>1e-9) bad=bad||[k,a,b]; }
  for(const k in v.out.w){ if(track('w:'+k, r.weights.values[k], v.out.w[k])>1e-9) bad=bad||['w.'+k,r.weights.values[k],v.out.w[k]]; }
  if(bad){ nbad++; if(nbad<=3) console.log(`vector ${i} LỆCH ${bad[0]}: js=${bad[1]} py=${bad[2]}`); }
});
const ks=Object.keys(worst).sort((a,b)=>worst[b]-worst[a]);
console.log(`\n${V.length} vector, ${nbad} lệch quá 1e-9`);
console.log('sai số tuyệt đối lớn nhất, 8 trường tệ nhất:');
ks.slice(0,8).forEach(k=>console.log(`  ${k.padEnd(16)} ${worst[k].toExponential(3)}`));
