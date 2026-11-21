# -*- coding: utf-8 -*-
"""Injected into the v13 motion pages (04 / 08): camera field of view, a tool-setting button and the tool-setting light path.
FOV: telecentric beam 13.4 x 11.2 (long side along X) from the lens front down WD 110, focal-plane patch; moves with Z.
Tool setting: moves Z up, then X / Y, then Z down to the measuring pose (prism under the camera, tool tip at the fold height);
the prism cover flips open on the last move; there the light path is drawn (the straight-down FOV beam is hidden meanwhile): lens -> down to the prism -> turned 90 deg by the mirror-coated hypotenuse -> across to the tool.
Optical axis = centre of the C-mount adapter ring (the lens box is off-centre because of its light port). All positions are read from the part bounding boxes in the page, so the page follows the model."""
import re

JS_SETUP = r"""
// ---- camera field of view (moves with Z) and tool-setting light path
const lb=bb['Camera_lens'],ab=bb['Camera_CS_C_adapter'],LC={x:(ab.min.x+ab.max.x)/2,y:(ab.min.y+ab.max.y)/2,z:lb.min.z},FW=13.4,FH=11.2,WD=110;
const fovG=new THREE.Group();gZ.add(fovG);
const fovM=new THREE.MeshBasicMaterial({color:0x22b8e6,transparent:true,opacity:.16,depthWrite:false,side:THREE.DoubleSide});
const fovB=new THREE.Mesh(new THREE.BoxGeometry(FW,FH,WD),fovM);fovB.position.set(LC.x,LC.y,LC.z-WD/2);fovG.add(fovB);
const fovE=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(FW,FH,WD)),new THREE.LineBasicMaterial({color:0x0b8fc0}));fovE.position.copy(fovB.position);fovG.add(fovE);
const fovP=new THREE.Mesh(new THREE.PlaneGeometry(FW,FH),new THREE.MeshBasicMaterial({color:0x22b8e6,transparent:true,opacity:.6,depthWrite:false,side:THREE.DoubleSide}));
fovP.position.set(LC.x,LC.y,LC.z-WD);fovG.add(fovP);
const mb_=bb['Tool_mirror'],MC={x:(mb_.min.x+mb_.max.x)/2,y:(mb_.min.y+mb_.max.y)/2,z:(mb_.min.z+mb_.max.z)/2};
const MEAS={x:+(MC.x-LC.x).toFixed(1),y:+(LC.y-MC.y).toFixed(1),z:+(MC.z-tip.z).toFixed(1)};
const lp=new THREE.Group();scene.add(lp);lp.visible=false;
const lpM=new THREE.MeshBasicMaterial({color:0xff3b30,transparent:true,opacity:.3,depthWrite:false,side:THREE.DoubleSide});
const lpV=new THREE.Mesh(new THREE.BoxGeometry(FW,FH,1),lpM),lpH=new THREE.Mesh(new THREE.BoxGeometry(1,FH,FW),lpM);lp.add(lpV,lpH);
const lpL=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(),new THREE.Vector3(),new THREE.Vector3()]),new THREE.LineBasicMaterial({color:0xd0021b}));lp.add(lpL);
const lpD=new THREE.Mesh(new THREE.SphereGeometry(1.6,16,12),new THREE.MeshBasicMaterial({color:0xd0021b}));lp.add(lpD);
let goQ=[],tsetOn=false,fovOn=true,covA=0;
const covM=gY.children.find(m=>m.userData&&m.userData.n==='Mirror_cover'),covP=new THREE.Group();
if(covM){const cb=bb['Mirror_cover'];covP.position.set(cb.min.x,(cb.min.y+cb.max.y)/2,cb.max.z);gY.add(covP);const t=covP.position;
 covM.geometry.translate(-t.x,-t.y,-t.z);if(covM.children[0])covM.children[0].geometry.translate(-t.x,-t.y,-t.z);covP.add(covM)}
function atMeas(){return Math.abs(P.x-MEAS.x)<.3&&Math.abs(P.y-MEAS.y)<.3&&Math.abs(P.z-MEAS.z)<.3}
function upLight(){const open=tsetOn&&(atMeas()||goQ.length==1);const ct=open?-Math.PI:0,dc=ct-covA;if(Math.abs(dc)>1e-3){covA+=Math.sign(dc)*Math.min(Math.abs(dc),0.06);covP.rotation.y=covA}
 lp.visible=tsetOn&&atMeas()&&Math.abs(covA+Math.PI)<0.05;fovG.visible=fovOn&&!lp.visible;if(!lp.visible)return;
 const lx=LC.x+P.x,ly=LC.y,lz=LC.z+P.z,fx=MC.x,fy=MC.y+P.y,fz=MC.z,tx=tip.x+P.x-2.5;
 lpV.scale.z=lz-fz;lpV.position.set(lx,ly,(lz+fz)/2);lpH.scale.x=tx-fx;lpH.position.set((fx+tx)/2,fy,fz);
 lpL.geometry.setFromPoints([new THREE.Vector3(lx,ly,lz),new THREE.Vector3(fx,fy,fz),new THREE.Vector3(tx,fy,fz)]);lpD.position.set(fx,fy,fz)}
"""
JS_STEP = (" if(goQ.length){const t=goQ[0],d=Math.hypot(t.x-P.x,t.y-P.y,t.z-P.z),v=dt*200;"
           "if(d<=v){P={...t};goQ.shift();if(!goQ.length&&tsetOn)st.textContent=tsetMsg()}"
           "else P={x:P.x+(t.x-P.x)*v/d,y:P.y+(t.y-P.y)*v/d,z:P.z+(t.z-P.z)*v/d};setPose()}\n upLight();\n")
JS_BUTTONS = ("function tsetMsg(){const dn=(LC.z+MEAS.z-MC.z).toFixed(0),ac=(tip.x+MEAS.x-MC.x).toFixed(0);"
              "return '對刀位置 X '+MEAS.x+'、Y '+MEAS.y+'、Z '+MEAS.z+'：相機往下看稜鏡（'+dn+' mm），斜邊鏡面把視線轉 90° 到刀具（'+ac+' mm），"
              "光路 '+dn+' + '+ac+' = 110 = WD；刀尖在視野中心高度，紅線是視野中心'}"
              "btn('tset').onclick=()=>{manual('移動到對刀位置：先抬 Z，再走 X／Y，最後下 Z');tsetOn=true;probeT=0;btn('probe').textContent='探頭 伸出';"
              "btn('probe').classList.remove('on');const zs=Math.max(P.z,30);goQ=[{x:P.x,y:P.y,z:zs},{x:MEAS.x,y:MEAS.y,z:zs},{...MEAS}]};"
              "btn('fov').onclick=()=>{fovOn=!fovOn;btn('fov').textContent='視野 '+(fovOn?'開':'關');btn('fov').classList.toggle('on',fovOn)};"
              "btn('fov').classList.add('on');")


def inject(html):
    n = []
    html, k = re.subn(r"(// state\n)", lambda m: JS_SETUP + m.group(1), html, count=1); n.append(k)
    html, k = re.subn(r"( ctl\.update\(\);R\.render\(scene,cam\);requestAnimationFrame\(step\)\})", lambda m: JS_STEP + m.group(1), html, count=1); n.append(k)
    html, k = re.subn(r'(<button id="trail")', '<button id="tset">對刀位置</button><button id="fov">視野 開</button>\\1', html, count=1); n.append(k)
    k = html.count("bg();setPose();btn('play')")
    html = html.replace("bg();setPose();btn('play')", JS_BUTTONS + "bg();setPose();btn('play')", 1); n.append(min(k, 1))
    # manual moves end the tool-setting mode's motion queue
    html, k = re.subn(r"function manual\(t\)\{", "function manual(t){goQ=[];", html, count=1); n.append(k)
    return html, n
