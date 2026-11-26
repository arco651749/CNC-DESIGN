# -*- coding: utf-8 -*-
"""Injected into the v14 motion pages (04 / 08): the corrugated conduits of freecad/v14/22_conduit_v14.py (output/v14/conduits.json),
recomputed whenever the axes move with the same rule as the check: fixed length, cubic Bezier through the anchors."""
import os, json

def inject(html, root):
    cd = json.load(open(os.path.join(root, 'output', 'v14', 'conduits.json'), encoding='utf-8'))
    js = '''<script>
const CD=%s;
(function(){
 const mat=new THREE.MeshStandardMaterial({color:0x26282c,metalness:0.05,roughness:0.85});
 const off=f=>f==='s'?[0,0,0]:f==='y'?[0,P.y,0]:f==='x'?[P.x,0,0]:[P.x,0,P.z];
 const bz=(a,b,c,d,t)=>{const u=1-t;return a.map((_,i)=>u*u*u*a[i]+3*u*u*t*b[i]+3*u*t*t*c[i]+t*t*t*d[i])};
 const len=q=>{let s=0;for(let i=1;i<q.length;i++)s+=Math.hypot(q[i][0]-q[i-1][0],q[i][1]-q[i-1][1],q[i][2]-q[i-1][2]);return s};
 function pts(c){const oa=off(c.a[0]),ob=off(c.b[0]);const A=c.a[1].map((v,i)=>v+oa[i]),B=c.b[1].map((v,i)=>v+ob[i]);
  const mk=h=>{const p1=A.map((v,i)=>v+h*c.a[2][i]),p2=B.map((v,i)=>v-h*c.b[2][i]);const q=[];for(let k=0;k<=40;k++)q.push(bz(A,p1,p2,B,k/40));return q};
  let lo=0,hi=c.L;if(len(mk(0))>c.L)return mk(0);while(len(mk(hi))<c.L&&hi<10*c.L)hi*=1.5;
  for(let k=0;k<30;k++){const m=(lo+hi)/2;if(len(mk(m))<c.L)lo=m;else hi=m}return mk((lo+hi)/2)}
 const M={};for(const n in CD.moving){M[n]=new THREE.Mesh(new THREE.BufferGeometry(),mat);scene.add(M[n])}
 const grp={s:scene,y:gY,x:gX,z:gZ};
 for(const n in CD.static){const c=CD.static[n];const cur=new THREE.CatmullRomCurve3(c.p.map(p=>new THREE.Vector3(...p)),false,'catmullrom',0.1);
  grp[c.f].add(new THREE.Mesh(new THREE.TubeGeometry(cur,48,c.D/2,10,false),mat))}
 function upd(){for(const n in CD.moving){const c=CD.moving[n];const q=pts(c).map(p=>new THREE.Vector3(...p));
  const g=new THREE.TubeGeometry(new THREE.CatmullRomCurve3(q),60,c.D/2,10,false);M[n].geometry.dispose();M[n].geometry=g}}
 const sp=setPose;setPose=function(){sp();upd()};upd();
})();
</script>''' % json.dumps(cd, ensure_ascii=False)
    i = html.rfind('</body>')
    return (html[:i] + js + html[i:], 1) if i > 0 else (html + js, 1)
