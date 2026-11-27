import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np
from matplotlib.patches import Rectangle
plt.rcParams['font.family']='WenQuanYi Zen Hei'; plt.rcParams['axes.unicode_minus']=False
def U(y0,z0,y1,z1,zb,n=60):          # hanging U: fixed leg (y0,z0) down, moving leg (y1,z1) down, bottom at zb
    r=abs(y1-y0)/2; yc=(y0+y1)/2
    l0=np.linspace(z0,zb+r,10); l1=np.linspace(zb+r,z1,10)
    t=np.linspace(np.pi,2*np.pi,n) if y1>y0 else np.linspace(0,-np.pi,n)
    ay=yc+r*np.cos(t)*(1 if y1>y0 else 1); az=zb+r+r*np.sin(t)
    if y1<y0: ay=yc+r*np.cos(t); az=zb+r+r*np.sin(t)
    Y=np.r_[np.full(10,y0),ay,np.full(10,y1)]; Z=np.r_[l0,az,l1]; return Y,Z
fig,ax=plt.subplots(3,2,figsize=(15,17))
def frame_side(a,title):
    a.set_title(title,fontsize=13); a.set_xlabel('y (mm)  ← 前　　後 →'); a.set_ylabel('z (mm)')
    a.add_patch(Rectangle((255,241),191,250,fc='#ddd',ec='k')); a.text(350,380,'柱頂電箱\n(L板)',ha='center')
    a.add_patch(Rectangle((162,230),20,260,fc='#bbb',ec='k')); a.text(150,500,'X底板',ha='right',fontsize=9)
    a.plot([570,570],[-60,450],'k',lw=2); a.text(575,300,'後護罩',fontsize=9)
    a.add_patch(Rectangle((-145,-20),327,20,fc='#ccc',ec='k')); a.text(20,-40,'基準底板',ha='center',fontsize=9)
    a.plot([-300,600],[-90,-90],'b',lw=1); a.text(-290,-80,'水盤底',color='b',fontsize=9)
    a.set_xlim(-480,620); a.set_ylim(-110,520); a.set_aspect('equal'); a.grid(alpha=.3)
def table_side(a,Y,ls,lab):
    a.add_patch(Rectangle((-210+Y,70),474,40,fc='#f3c38a' if ls=='-' else 'none',ec='#b07020',ls=ls,lw=1.5,alpha=.8))
    a.add_patch(Rectangle((265+Y,70),147,96,fc='#555' if ls=='-' else 'none',ec='#333',ls=ls))
    a.text(20+Y,118,lab,ha='center',fontsize=9,color='#804000')
def frame_top(a,title):
    a.set_title(title,fontsize=13); a.set_xlabel('x (mm)'); a.set_ylabel('y (mm)  ↑ 後')
    a.add_patch(Rectangle((-380,255),760,191,fc='#eee',ec='k',ls='--')); a.text(250,420,'柱頂電箱(上方)',fontsize=9)
    a.plot([-484,-484],[-600,570],'k',lw=2); a.text(-480,-560,'左護罩',fontsize=9); a.plot([-484,484],[570,570],'k',lw=2)
    a.set_xlim(-500,300); a.set_ylim(-480,600); a.set_aspect('equal'); a.grid(alpha=.3)
def table_top(a,Y,ls,lab):
    a.add_patch(Rectangle((-220,-210+Y),440,474,fc='#f3c38a' if ls=='-' else 'none',ec='#b07020',ls=ls,lw=1.5,alpha=.6))
    a.add_patch(Rectangle((-40,265+Y),80,147,fc='#555' if ls=='-' else 'none',ec='#333',ls=ls))
    a.text(0,-150+Y,lab,ha='center',fontsize=9,color='#804000')
# row 0: current
a=ax[0,0]; frame_side(a,'現在（錯）：側視，接頭在 x -120'); table_side(a,-250,'--','Y -250'); table_side(a,150,'-','工作台 Y +150')
for Yp,c in ((-250,'#888'),(150,'k')):
    y,z=U(330,202,395+Yp,200,25 if Yp>0 else 22); a.plot(y,z,c,lw=5,alpha=.8)
a.plot(330,236,'gs',ms=10); a.annotate('穿過工作台！',(335,90),(380,0),color='r',fontsize=13,arrowprops=dict(color='r'))
a=ax[0,1]; frame_top(a,'現在（錯）：上視'); table_top(a,-250,'--','Y -250'); table_top(a,150,'-','Y +150')
a.plot([-120,-120],[330,330],'gs',ms=10); a.plot([-120,0],[330,545],'k',lw=5,alpha=.7); a.text(-110,300,'接頭 (-120,330)\n在工作台路徑上',color='r')
# row 1: option A
a=ax[1,0]; frame_side(a,'方案 A：側視（浪管在 x -265 平面，工作台外側）'); table_side(a,-250,'--','Y -250'); table_side(a,150,'-','Y +150')
for Yp,c in ((-250,'#888'),(150,'k')):
    y1=250+Yp; y,z=U(300,236,y1,95,20 if Yp<0 else 60); a.plot(y,z,c,lw=5,alpha=.8)
a.plot(300,250,'gs',ms=10); a.text(290,200,'固定接頭\n(電箱下)',ha='right',color='g')
a.text(-460,30,'活動端：工作台左後角支架\n(跟著工作台走，往下吊)',fontsize=9,color='g')
a.text(-460,430,'側視看起來跟工作台重疊，\n其實浪管在工作台左邊 x -265\n（見右邊上視）',fontsize=10,color='b')
a=ax[1,1]; frame_top(a,'方案 A：上視'); table_top(a,-250,'--','Y -250'); table_top(a,150,'-','Y +150')
a.plot([-265,-265],[0,400],'k',lw=5,alpha=.7); a.plot(-265,300,'gs',ms=10); a.text(-470,300,'固定接頭\n(-265, 300)',color='g')
for Yp in (-250,150): a.plot([-265,-220],[250+Yp,250+Yp],color='g',lw=3); a.plot(-265,250+Yp,'go',ms=8)
a.annotate('Y馬達線沿工作台後面\n固定到馬達',(-100,414),(-100,520),fontsize=9,arrowprops=dict(arrowstyle='->'))
a.text(-300,-300,'浪管整段在 x < -250\n（工作台 x -220 外）',fontsize=10,color='b')
# row 2: option B
a=ax[2,0]; frame_side(a,'方案 B：側視（接頭留 x -120，往後到 y 470）'); table_side(a,-250,'--','Y -250'); table_side(a,150,'-','Y +150')
for Yp,c in ((-250,'#888'),(150,'k')):
    y,z=U(470,236,395+Yp,200,-20 if Yp<0 else -85); a.plot(y,z,c,lw=5,alpha=.8)
a.plot(470,250,'gs',ms=10); a.text(-460,430,'浪管在 x -120，Y 馬達在 x -40..40，\n側視重疊但實際不碰',fontsize=10,color='b'); a.text(480,260,'固定接頭\n(頂板後方再加支架)',fontsize=9,color='g')
a.annotate('Y+150 時\nU底垂到水盤',(430,-80),(200,-70),color='r',arrowprops=dict(color='r'))
a=ax[2,1]; frame_top(a,'方案 B：上視'); table_top(a,-250,'--','Y -250'); table_top(a,150,'-','Y +150')
a.plot(-120,470,'gs',ms=10); a.text(-110,480,'(-120,470)',color='g'); a.text(-300,-300,'浪管要加長，\n跟後護罩、Y馬達間隙很小',fontsize=10,color='r')
plt.tight_layout(); plt.savefig('/home/user/CNC-DESIGN/docs/sketches/y_conduit_options.png',dpi=90)
