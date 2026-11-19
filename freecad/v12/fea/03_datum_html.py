# -*- coding: utf-8 -*-
"""v12 datum plate FEA, step 3: interactive HTML of the datum (Y-axis base) plate results (offline: three.js + OrbitControls copied from the
v4 motion page).  Case switch, colour = von Mises or |displacement|, deformation scale slider, key numbers.
Run:  python freecad/v12/fea/03_datum_html.py      Out: output/v12/fea/Datum_plate_FEA.html"""
import os, json, base64, re
import numpy as np

ROOT = os.environ.get('CNC_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FEA = os.path.join(ROOT, 'output', 'v12', 'fea')
MOTION = os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html')
R = json.load(open(os.path.join(FEA, 'datum_results.json'), encoding='utf-8'))
H = json.load(open(os.path.join(FEA, 'datum_loads.json'), encoding='utf-8'))

ids = np.load(os.path.join(FEA, 'datum_node_ids.npy'))
xyz = np.load(os.path.join(FEA, 'datum_node_xyz.npy'))
tets = np.load(os.path.join(FEA, 'datum_tets.npy'))[:, :4]          # corner nodes of C3D10
pos_of = {int(n): k for k, n in enumerate(ids)}
T = np.vectorize(pos_of.get)(tets)
# boundary faces = faces used by exactly one tet
F = np.concatenate([T[:, [0, 1, 2]], T[:, [0, 1, 3]], T[:, [0, 2, 3]], T[:, [1, 2, 3]]])
key = np.sort(F, axis=1)
_, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
B = F[cnt[inv.ravel()] == 1]
used = np.unique(B)
remap = -np.ones(len(ids), dtype=np.int64); remap[used] = np.arange(len(used))
Bf = remap[B].astype(np.uint32)
P = xyz[used].astype(np.float32)
print('surface nodes', len(used), 'triangles', len(Bf))

b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode('ascii')
cases = []
for name, c in R['cases'].items():
    U = np.load(os.path.join(FEA, name + '_U.npy'))[used].astype(np.float32)
    VM = np.load(os.path.join(FEA, name + '_VM.npy'))[used].astype(np.float32)
    cases.append({'name': name, 'u': b64(U), 'vm': b64(VM), 'info': c})
data = {'p': b64(P), 'i': b64(Bf), 'cases': cases, 'bbox': H['plate_bbox'], 'risers': H['risers'], 'feet': H['feet'], 'blocks': H['blocks'],
        'gm': R['gantry']['mass_kg'], 'tm': R['table']['mass_kg'], 'pm': R['plate_mass_kg'], 'tc': R['travel_change']}

src = open(MOTION, encoding='utf-8').read()
scripts = re.findall(r'<script>(.*?)</script>', src, re.S)
THREE_JS, ORBIT_JS = scripts[0], scripts[1]

LABEL = {'A_table_centre': 'A 工作台在中間', 'B_table_load_pos_y-250': 'B 工作台在上料位置 Y−250',
         'C_table_rear_y+150': 'C 工作台在後端 Y+150', 'D_centre_plus_100N_cut': 'D 中間＋切削力 100 N'}
html = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Y 軸底板應力分析</title>
<style>
:root{--bg:#eef0f1;--panel:rgba(255,255,255,.93);--ink:#1b2326;--mute:#5b676c;--line:#cfd6d8;--acc:#d9682b;--btn:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15191b;--panel:rgba(28,33,36,.93);--ink:#e8ecee;--mute:#9aa7ac;--line:#3a4448;--acc:#ef8a4f;--btn:#232a2d}}
:root[data-theme="dark"]{--bg:#15191b;--panel:rgba(28,33,36,.93);--ink:#e8ecee;--mute:#9aa7ac;--line:#3a4448;--acc:#ef8a4f;--btn:#232a2d}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font-family:"Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;overflow:hidden}
#c{position:fixed;inset:0;width:100%;height:100%;display:block}
#ui{position:fixed;top:16px;left:16px;width:340px;max-height:calc(100% - 32px);overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
h1{font-size:17px;margin:0 0 4px}.sub{font-size:12px;color:var(--mute);margin-bottom:10px;line-height:1.5}
.row{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
button{font:inherit;font-size:13px;padding:6px 10px;border:1px solid var(--line);background:var(--btn);color:var(--ink);border-radius:6px;cursor:pointer}
button.on{background:var(--acc);border-color:var(--acc);color:#fff}
label{display:grid;grid-template-columns:96px 1fr 52px;align-items:center;gap:6px;font-size:13px;margin:6px 0}
input[type=range]{width:100%;accent-color:var(--acc)}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:6px}td{padding:3px 0;border-bottom:1px solid var(--line)}td:last-child{text-align:right;font-family:ui-monospace,Menlo,monospace}
.bar{height:12px;border-radius:3px;background:linear-gradient(90deg,#30123b,#4662d7,#36aaf9,#1ae4b6,#72fe5e,#c8ef34,#faba39,#f66b19,#ca2a04,#7a0403)}
.lg{display:flex;justify-content:space-between;font-size:11px;color:var(--mute);margin-top:2px;font-family:ui-monospace,monospace}
.note{font-size:11.5px;color:var(--mute);line-height:1.55;margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
@media (max-width:640px){#ui{top:auto;bottom:12px;left:12px;right:12px;width:auto;max-height:45%}}
h1{cursor:pointer}h1::after{content:' ▾';font-size:12px;color:var(--mute)}#ui.min h1::after{content:' ▸'}#ui.min>*:not(h1){display:none}
</style></head><body><canvas id="c"></canvas>
<div id="ui"><h1 onclick="this.parentNode.classList.toggle('min')">Y 軸底板（基準底板）應力分析 v12</h1>
<div class="sub">CalculiX 線性靜態 · Q235 t20（E 210 GPa）· 底座 4 個墊高塊固定 · 拖曳旋轉、滾輪縮放</div>
<div class="row" id="cases"></div>
<div class="row"><button id="mvm">von Mises 應力</button><button id="mu" class="on">變形量</button><button id="theme">深/淺色</button></div>
<label>變形放大<input id="sc" type="range" min="0" max="20000" step="250" value="5000"><span id="scv">5000×</span></label>
<div class="bar"></div><div class="lg"><span id="lmin"></span><span id="lunit"></span><span id="lmax"></span></div>
<table id="tb"></table>
<div class="note" id="note"></div></div>
<script>__THREE__</script>
<script>__ORBIT__</script>
<script>
const D=__DATA__;const LABEL=__LABEL__;
function b64(s,T){const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new T(u.buffer)}
const P=b64(D.p,Float32Array),I=b64(D.i,Uint32Array);
const C=D.cases.map(c=>({name:c.name,u:b64(c.u,Float32Array),vm:b64(c.vm,Float32Array),info:c.info}));
const cv=document.getElementById('c'),ren=new THREE.WebGLRenderer({canvas:cv,antialias:true});ren.setPixelRatio(Math.min(devicePixelRatio,2));
const scene=new THREE.Scene(),cam=new THREE.PerspectiveCamera(35,1,1,20000);cam.up.set(0,0,1);
const bb=D.bbox,ctr=new THREE.Vector3((bb[0]+bb[1])/2,(bb[2]+bb[3])/2,(bb[4]+bb[5])/2);
cam.position.set(ctr.x+700,ctr.y-1100,ctr.z+800);const ctl=new THREE.OrbitControls(cam,cv);ctl.target.copy(ctr);ctl.update();
scene.add(new THREE.HemisphereLight(0xffffff,0x444444,0.9));const dl=new THREE.DirectionalLight(0xffffff,0.55);dl.position.set(-1,-2,3);scene.add(dl);
const g=new THREE.BufferGeometry(),pos=new Float32Array(P.length),col=new Float32Array(P.length);
g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('color',new THREE.BufferAttribute(col,3));g.setIndex(new THREE.BufferAttribute(I,1));
const mesh=new THREE.Mesh(g,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));scene.add(mesh);
const edges=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BufferGeometry().setAttribute('position',new THREE.BufferAttribute(P,3)).setIndex(new THREE.BufferAttribute(I,1)),30),new THREE.LineBasicMaterial({color:0x222222,transparent:true,opacity:.35}));scene.add(edges);
// fixed column contact (ghost boxes) + rail strips
function ghost(x0,x1,y0,y1,z0,z1,c,o){const m=new THREE.Mesh(new THREE.BoxGeometry(x1-x0,y1-y0,z1-z0),new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:o,depthWrite:false}));m.position.set((x0+x1)/2,(y0+y1)/2,(z0+z1)/2);scene.add(m);return m}
D.risers.forEach(r=>ghost(r[0]-30,r[0]+30,r[1]-30,r[1]+30,bb[4]-60,bb[4],0x7a8a92,.35));Object.values(D.feet).forEach(f=>ghost(f[0],f[1],f[2],f[3],bb[5],bb[5]+18,0xd9682b,.18));Object.values(D.blocks).forEach(f=>ghost(f[0],f[1],f[2],f[3],bb[5],bb[5]+12,0x2f5d73,.22));
const TURBO=[[48,18,59],[70,98,215],[54,170,249],[26,228,182],[114,254,94],[200,239,52],[250,186,57],[246,107,25],[202,42,4],[122,4,3]];
function ramp(t){t=Math.min(1,Math.max(0,t))*(TURBO.length-1);const i=Math.floor(t),f=t-i,a=TURBO[i],b=TURBO[Math.min(i+1,TURBO.length-1)];return[(a[0]+(b[0]-a[0])*f)/255,(a[1]+(b[1]-a[1])*f)/255,(a[2]+(b[2]-a[2])*f)/255]}
let ci=0,mode='u',sc=5000;
function update(){const c=C[ci],u=c.u,n=P.length/3;let vals=new Float32Array(n),lo=1e30,hi=-1e30;
 for(let k=0;k<n;k++){pos[3*k]=P[3*k]+u[3*k]*sc;pos[3*k+1]=P[3*k+1]+u[3*k+1]*sc;pos[3*k+2]=P[3*k+2]+u[3*k+2]*sc;
  const v=mode==='vm'?c.vm[k]:Math.hypot(u[3*k],u[3*k+1],u[3*k+2])*1000;vals[k]=v;if(v<lo)lo=v;if(v>hi)hi=v}
 lo=0;for(let k=0;k<n;k++){const r=ramp((vals[k]-lo)/(hi-lo||1));col[3*k]=r[0];col[3*k+1]=r[1];col[3*k+2]=r[2]}
 g.attributes.position.needsUpdate=true;g.attributes.color.needsUpdate=true;g.computeVertexNormals();edges.visible=sc===0;
 document.getElementById('lmin').textContent=lo.toFixed(mode==='vm'?1:1);document.getElementById('lmax').textContent=hi.toFixed(mode==='vm'?2:2);
 document.getElementById('lunit').textContent=mode==='vm'?'MPa':'µm';
 const f=c.info;document.getElementById('tb').innerHTML=[
  ['工作台位置 Y',f.table_y_mm+' mm'],['切削力',f.cut_force_N+' N'],['前／後滑塊對受力',f.block_pair_N[0]+' / '+f.block_pair_N[1]+' N'],
  ['最大 von Mises',f.max_vm_MPa+' MPa'],['對降伏 235 MPa 安全係數',f.safety_factor_yield_235],
  ['底板最大變形',(f.max_disp_mm*1000).toFixed(1)+' µm'],
  ['滑塊面下沉 L1 / R1',f.block_uz_um.Y_block_L1+' / '+f.block_uz_um.Y_block_R1+' µm'],['滑塊面下沉 L2 / R2',f.block_uz_um.Y_block_L2+' / '+f.block_uz_um.Y_block_R2+' µm'],
  ['工作台前後傾',f.table_pitch_urad+' µrad'],['Y 線軌扭轉',f.rail_twist_urad+' µrad'],
  ['左／右腳座傾斜',f.foot_tilt_urad.L+' / '+f.foot_tilt_urad.R+' µrad']]
  .map(r=>'<tr><td>'+r[0]+'</td><td>'+r[1]+'</td></tr>').join('')}
const cs=document.getElementById('cases');C.forEach((c,k)=>{const b=document.createElement('button');b.textContent=LABEL[c.name]||c.name;b.className=k===0?'on':'';b.onclick=()=>{ci=k;[...cs.children].forEach((x,j)=>x.className=j===k?'on':'');update()};cs.appendChild(b)});
document.getElementById('mvm').onclick=()=>{mode='vm';mvm.className='on';mu.className='';update()};
document.getElementById('mu').onclick=()=>{mode='u';mu.className='on';mvm.className='';update()};
document.getElementById('sc').oninput=e=>{sc=+e.target.value;document.getElementById('scv').textContent=sc+'×';update()};
document.getElementById('theme').onclick=()=>{const r=document.documentElement,d=getComputedStyle(r).getPropertyValue('--bg').trim()==='#15191b';r.dataset.theme=d?'light':'dark';bg()};
function bg(){scene.background=new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--bg').trim())}
const T=D.tc;document.getElementById('note').innerHTML='負載：龍門 '+D.gm+' kg 壓在兩個腳座（橘色框），Y 軸移動件含 3 kg 工件 '+D.tm+' kg 壓在 4 顆滑塊（藍色框），底板自重 '+D.pm+' kg。灰色方塊＝底座墊高塊（固定）。<br><b>工作台從後端走到上料位置的變化</b>（靜止的變形組裝時已調掉，只有變化會進到加工）：工作台前後傾 '+T.table_pitch_urad_B_minus_C+' µrad、線軌扭轉 '+T.rail_twist_urad_B_minus_C+' µrad、腳座傾斜 左 '+T.foot_tilt_urad_B_minus_C.L+' / 右 '+T.foot_tilt_urad_B_minus_C.R+' µrad。<br>簡化：腳座、滑塊、墊高塊視為完全貼合；底座鋁擠框視為剛體（實際會更軟）。';
function resize(){const w=innerWidth,h=innerHeight;ren.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix()}addEventListener('resize',resize);
bg();resize();update();(function loop(){ren.render(scene,cam);requestAnimationFrame(loop)})();
</script></body></html>'''
html = (html.replace('__THREE__', THREE_JS).replace('__ORBIT__', ORBIT_JS)
        .replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
        .replace('__LABEL__', json.dumps(LABEL, ensure_ascii=False)))
out = os.path.join(FEA, 'Datum_plate_FEA.html')
open(out, 'w', encoding='utf-8', newline='\n').write(html)
print('HTML', out, round(len(html) / 1e6, 2), 'MB')
