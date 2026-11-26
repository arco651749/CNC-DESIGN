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
 for(const n in CD.static){const c=CD.static[n];const cur=new THREE.CatmullRomCurve3(c.p.map(p=>new THREE.Vector3(...p)),false,'catmullrom',0.1);
  grp[c.f].add(new THREE.Mesh(new THREE.TubeGeometry(cur,48,c.D/2,10,false),mat))}
 function upd(){for(const n in CD.moving){const c=CD.moving[n];const q=pts(c).map(p=>new THREE.Vector3(...p));
  const g=new THREE.TubeGeometry(new THREE.CatmullRomCurve3(q),60,c.D/2,10,false);M[n].geometry.dispose();M[n].geometry=g}}
 const sp=setPose;setPose=function(){sp();upd()};upd();
})();
</script>''' % json.dumps(cd, ensure_ascii=False)
    i = html.rfind('</body>')
    return (html[:i] + js + html[i:], 1) if i > 0 else (html + js, 1)
