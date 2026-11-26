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
 function pts(c){const v=c.ax==='x'?P.x:c.ax==='y'?P.y:P.z;const V=c.v;let k=0;while(k<V.length-2&&v>V[k+1])k++;
  const u=Math.max(0,Math.min(1,(v-V[k])/(V[k+1]-V[k])));const A=c.s[k],B=c.s[k+1];
  return A.map((p,i)=>[p[0]+(B[i][0]-p[0])*u+(c.shiftx?P.x:0),p[1]+(B[i][1]-p[1])*u,p[2]+(B[i][2]-p[2])*u])}
 const M={};for(const n in CD.moving){M[n]=new THREE.Mesh(new THREE.BufferGeometry(),mat);scene.add(M[n])}
 const grp={s:scene,y:gY,x:gX,z:gZ};
 for(const n in CD.static){const c=CD.static[n];if(!c.D){const a=c.p[0],b=c.p[1];const m=new THREE.Mesh(new THREE.BoxGeometry(b[0]-a[0],b[1]-a[1],b[2]-a[2]),
   new THREE.MeshStandardMaterial({color:0xb8bec6,metalness:0.2,roughness:0.6}));m.position.set((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2);grp[c.f].add(m);continue}
  const cur=new THREE.CatmullRomCurve3(c.p.map(p=>new THREE.Vector3(...p)),false,'catmullrom',0.1);
  grp[c.f].add(new THREE.Mesh(new THREE.TubeGeometry(cur,48,c.D/2,10,false),mat))}
 if(CD.box){const a=CD.box[0],b=CD.box[1];const m=new THREE.Mesh(new THREE.BoxGeometry(b[0]-a[0],b[1]-a[1],b[2]-a[2]),
   new THREE.MeshStandardMaterial({color:0x8fa3b8,transparent:true,opacity:0.22,depthWrite:false}));m.position.set((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2);scene.add(m);
  for(const g of (CD.glands||[])){const r=new THREE.Mesh(new THREE.CylinderGeometry(g[3]/2+4,g[3]/2+4,4,24),new THREE.MeshStandardMaterial({color:0xd08a2c}));
   r.rotation.x=Math.PI/2;r.position.set(g[0],g[1],g[2]);scene.add(r)}}
 function upd(){for(const n in CD.moving){const c=CD.moving[n];const q=pts(c).map(p=>new THREE.Vector3(...p));
  const g=new THREE.TubeGeometry(new THREE.CatmullRomCurve3(q),60,c.D/2,10,false);M[n].geometry.dispose();M[n].geometry=g}}
 const sp=setPose;setPose=function(){sp();upd()};upd();
})();
</script>''' % json.dumps(cd, ensure_ascii=False)
    i = html.rfind('</body>')
    return (html[:i] + js + html[i:], 1) if i > 0 else (html + js, 1)
