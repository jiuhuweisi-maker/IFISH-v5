"""IFISH v5: an 83-second functional launch film, drawn and animated at 60 fps."""
from __future__ import annotations
import argparse,json,math,subprocess,sys,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from kinetic_engine import *

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'work';OUT=ROOT/'output';ASSETS=ROOT/'assets'
BG=(248,249,251);INK=(24,30,43);GRAY=(119,127,139);BLUE=(48,91,151);LIGHT=(204,222,245)
SAND=(154,109,77);WHITE=(223,223,231);TEAL=(66,158,164);DARK=(13,20,34)
COLORS=[BLUE,SAND,WHITE];NAMES=['深海蓝','暮砂棕','云瓷白']
MASTER=['01_deep_blue','02_dusk_sand','03_cloud_porcelain'];PRESENT='04_blue_presenting';RICE='05_blue_rice'
MONO='C:/Windows/Fonts/consola.ttf';BOLDEN='C:/Windows/Fonts/segoeuib.ttf'
BEAT=.7459;OFFSET=2.644
def beat(n):return OFFSET+n*BEAT
STARTS=[0,beat(8),beat(15),beat(29),beat(43),beat(57),beat(68),beat(77),beat(91),beat(99),83.]
TITLES=['流动的想法 · 二维开场','不止可爱','推理与解题','写作与改写','编程与运行','中英翻译','三种配色','只吃大米饭','功能收束','IFISH 品牌标志']

def C(x):return max(0.,min(1.,float(x)))
def E(x):return float(ease(x))
def L(a,b,u):return a+(b-a)*u
def pathmix(a,b,u):return np.asarray(a)*(1-u)+np.asarray(b)*u
def polyline_part(p,u):
    p=np.asarray(p);n=max(2,min(len(p),int(C(u)*(len(p)-1))+1));return p[:n]
def color(a,b,u):return tuple(round(L(x,y,u)) for x,y in zip(a,b))
def bezier(a,b,c,d,u):
    return (1-u)**3*np.array(a)+3*(1-u)**2*u*np.array(b)+3*(1-u)*u*u*np.array(c)+u**3*np.array(d)
def aligned_capsule(w,h,r):
    p=roundrect_path(w,h,r,240);index=int(np.argmin((p[:,0]+w/2)**2+p[:,1]**2))
    return np.roll(p,-index,axis=0)

class Film:
    def __init__(self):
        self.e=KineticEngine();self.w=1920;self.h=1080
        for p in ASSETS.glob('*.png'):self.e.texture(p.stem,p,trim=True)
        self.e.texture('shadow',shadow_image())
        self.rng=np.random.default_rng(5060)
        self.grains=self.rng.uniform(0,1,(42,5))
        self.methods=[self.opening,self.hero,self.reason,self.writing,self.coding,self.translate,self.finishes,self.rice,self.finale,self.brand]
    def label(self,s,x,y,size=52,font=CN,color=INK,alpha=1,align='left',scale=1,reveal=1,tracking=0,clip=None):
        if alpha<.001:return (0,0)
        im=text_image(s,size,font,color,tracking);w,h=im.width*scale,im.height*scale
        cx=x+w/2 if align=='left' else x-w/2 if align=='right' else x
        self.e.sprite(('txt',s,size,font,color,tracking),im,center=(cx,y+h/2),size=(w,h),alpha=alpha,reveal=cx-w/2+(w+4)*C(reveal),clip=clip or (-9999,-9999,9999,9999))
        return w,h
    def title(self,s,u,color=INK):
        a=E((u+.25)/.65);self.label(s,124,118+32*(1-a),84,CNM,color,a)
    def tag(self,s,x,y,u,color=BLUE):
        a=E((u+.15)/.6);self.label(s,x,y+18*(1-a),29,CN,color,a)
    def actor(self,k,t,x,y=990,height=790,alpha=1,action=1,angle=0):
        if alpha<.001:return
        self.e.sprite('shadow',center=(x,y+5),size=(height*.70,80),alpha=alpha*.5)
        self.e.actor(k,t,center=(x,y-height/2),height=height,alpha=alpha,action=action,angle=angle)
    def line(self,p,c=BLUE,width=4,alpha=1,progress=1):
        self.e.line(polyline_part(p,progress),rgba(c,alpha),width,roundcaps=True)
    def pill(self,s,x,y,w=210,h=72,fill=LIGHT,ink=BLUE,size=35,alpha=1):
        self.e.roundrect((x,y),(w,h),h/2,rgba(fill,alpha))
        self.label(s,x,y-h*.29,size,CN,ink,alpha,align='center')
    def check(self,x,y,u,s=1,c=BLUE):
        self.line(np.array([[-21,0],[-5,17],[28,-23]])*s+[x,y],c,5*s,progress=u)
    def spark(self,x,y,s=1,c=BLUE,alpha=1,phase=0):
        for j in range(4):
            a=math.pi/2*j+phase;self.line([[x+math.cos(a)*5*s,y+math.sin(a)*5*s],[x+math.cos(a)*22*s,y+math.sin(a)*22*s]],c,3*s,alpha)
    def whale(self,x,y,scale=1,alpha=1,assemble=1):
        e=self.e;s=scale;u=E(assemble)
        # Deliberately simple original 2D whale silhouette.
        e.roundrect((x-19*s,y+10*s),(171*s*u,101*s*u),51*s*u,rgba(BLUE,alpha))
        for side in [-1,1]:
            a=side*.75;leaf=leaf_path(120)
            leaf[:,0]*=93*s;leaf[:,1]*=230*s
            center=(L(x+150*s,x+38*s,u),L(y+side*86*s,y+8*s,u))
            e.polygon(transform(leaf,center,angle=a),rgba(BLUE,alpha))
        e.circle((x-69*s,y-2*s),6.5*s,rgba(BG,alpha*u))
        for j in range(3):
            a=(j-1)*.62;h=(23 if j==1 else 17)*s*u
            pts=roundrect_path(10*s*u,h,5*s*u,80)
            e.polygon(transform(pts,(x-35*s+(j-1)*19*s,y-66*s-(j==1)*6*s),angle=a),rgba(BLUE,alpha*u))
    def opening(self,t,u):
        e=self.e;e.begin(BG)
        # A broad flat mark swims in, becomes speech, then three drawn ribbons.
        q=E(u/1.25);cx=L(410,960,q);cy=540+55*math.sin(q*math.pi*2)*(1-q)
        if u<3.15:
            morph=E((u-1.05)/.88);shrink=E((u-2.55)/.6)
            w=L(43,540,morph)*(1-.63*shrink);h=L(43,290,morph)*(1-.38*shrink)
            e.roundrect((cx,cy),(w,h),L(22,130,morph),rgba(BLUE,1-shrink))
            tail=cubic((cx-w*.22,cy+h*.35),(cx-w*.23,cy+h*.7),(cx-w*.34,cy+h*.64),(cx-w*.36,cy+h*.46),55)
            if morph>.01:e.polygon(tail,rgba(BLUE,morph*(1-shrink)))
            self.label('你好。',cx,cy-61,100,CNM,(255,255,255),morph*(1-shrink),align='center',reveal=E((u-1.25)/.7))
            for j in range(3):
                p=cubic((cx-100-j*45,cy+24+j*10),(cx-270-j*30,cy-5),(cx-300-j*55,cy+65),(cx-390-j*40,cy+20),100)
                self.line(p,BLUE,10-j*2,(1-q)*.40)
        if u>=2.55:
            appear=E((u-2.55)/.6);tofan=E((u-4.13)/1.05);close=E((u-6.30)/1.35)
            for j in range(6):
                a=j*math.pi/3-.4+E((u-3.)/3.)*.6
                th=np.linspace(math.pi,3*math.pi,240,endpoint=False)
                ring=np.stack([np.cos(th)*(135+j*15),np.sin(th)*(135+j*15)],axis=1)
                angle=((j-2.5)*.79*E((u-4.5)/1.3)+E((u-5.3)/1.)*.47)*(1-close)
                center=(L(190*math.cos(angle),(j%3-1)*245,close),L(190*math.sin(angle),0,close))
                blade=leaf_path(240);blade[:,0]=(blade[:,0]-.5)*425;blade[:,1]*=650
                base=pathmix(blade,aligned_capsule(190,70,35),close)
                petal=transform(base,center,1,angle)
                p=pathmix(ring,petal,tofan)
                p=p+[960,540]
                col=COLORS[j%3];fill=E((u-4.4)/.65)
                if fill>.001:
                    e.polygon(p,rgba(col,appear*fill))
                    face=base.copy();face[:,1]*=.73;face[:,0]*=.985
                    face=pathmix(ring,transform(face,center,1,angle),tofan)+[960,540]
                    e.polygon(face,rgba(color(BG,col,close),appear*fill*(1-.35*close)))
                self.line(np.vstack([p,p[0]]),col,3,appear*(1-close))
            # Three broad capsules become the same circular aperture used next.
            converge=E((u-7.65)/.95)
            if converge>0:
                e.roundrect((960,540),(1920,1080),0,rgba(BG,converge))
                for j,c in enumerate(COLORS):
                    x=L(715+j*245,960,converge);r=L(35,76,converge)
                    e.circle((x,540),r,rgba(c,1-.45*converge))
        self.label('让想法，流动起来。',960,827,40,CNL,GRAY,E((u-6.7)/.65),align='center')
    def hero(self,t,u):
        e=self.e;e.begin(BG);a=E((u+.45)/1.)
        e.circle((1360,525),L(40,377,a),rgba((235,241,249)))
        self.actor(PRESENT,t,x=L(1510,1365,a),height=L(780,930,a),alpha=a,angle=-.008*math.sin(u))
        self.label('不止',125,300+50*(1-a),117,CNM,INK,a,reveal=E((u+.25)/.7))
        self.label('可爱。',120,470+50*(1-a),157,CNM,BLUE,a,reveal=E((u-.45)/.75))
        self.tag('一个有办法的小伙伴。',130,727,u-.8,GRAY)
        for j,c in enumerate([BLUE,TEAL,SAND]):
            k=E((u-.6-j*.12)/.8);ang=u*.8+j*2.1
            x=1360+390*math.cos(ang);y=530+280*math.sin(ang)
            e.circle((x,y),L(0,9,k),rgba(c,.55*k))
    def reason(self,t,u):
        e=self.e;e.begin(BG);self.title('问题，想明白。',u)
        self.tag('推理 · 解题',128,240,u-.15)
        focus=E((u-3.2)/1.8);dx=-240*focus
        a=E((u+.4)/.8);self.actor(PRESENT,t,335-800*focus,1010,710,alpha=a*(1-focus),angle=.007*math.sin(t*.9))
        self.pill('12 × 8 + 12 × 7 = ?',1215+dx,339,825,88,(235,241,250),BLUE,46,a)
        g=E((u-2*BEAT)/(2*BEAT));h=E((u-7*BEAT)/(1.5*BEAT));ans=E((u-10*BEAT)/BEAT)
        start=[830,950,1060,1180,1300,1420,1540]
        end=[935,1050,1190,1300,935,1050,1400]
        texts=['12','×','8','+','12','×','7']
        for j,s in enumerate(texts):
            x=L(start[j],end[j],g)+dx;y=497-57*math.sin(math.pi*g)*(1 if j in [0,4] else -.3)
            al=a*(1-h)*(1-g if j in [4,5] else 1)
            if j in [0,4]:
                e.roundrect((x,y+38),(111,85),19,rgba((222,235,253),al))
            ink=BLUE if j in [0,4] else INK;hh=text_image(s,69,ENB,ink).height
            self.label(s,x,y+38-hh/2,69,ENB,ink,al,align='center')
        for s,xx in [('(',1135+dx),(')',1475+dx)]:
            hh=text_image(s,83,EN,INK).height
            self.label(s,xx,535-hh/2,83,EN,INK,a*g*(1-h),align='center')
        self.label('12 × 15',1210+dx,485-20*ans,88,ENB,INK,a*h*(1-ans),align='center')
        self.label('180',1210+dx,433,172,ENB,BLUE,a*ans,align='center',scale=L(.85,1,ans))
        if ans>.01:self.check(1485+dx,560,E((u-11*BEAT)/BEAT),1.0)
        # The two eight/seven-row blocks physically combine into a 12 x 15 grid.
        for row in range(15):
            for col in range(12):
                x=1055+col*28+dx;y=730+row*13+(row>=8)*L(21,0,g)
                wave=1+math.sin(u*1.6-col*.17-row*.1)*.045
                e.circle((x,y),3.0*wave,rgba(BLUE if row<8 else TEAL,a*(.4+.4*ans)))
        self.label('把同一部分合起来。',1215+dx,643,32,CN,GRAY,a*(1-ans),align='center')
        self.label('一步一步，有答案。',1215+dx,646,34,CN,GRAY,a*ans,align='center')
    def writing(self,t,u):
        e=self.e;e.begin(BG);self.title('好想法，写出来。',u)
        self.tag('写作 · 改写',128,240,u-.15)
        a=E((u+.4)/.8);self.actor(PRESENT,t,320,1010,700,alpha=a)
        typed=E((u-.2)/1.4)
        self.pill('写一句海边的文案',1190,344,800,86,(235,241,250),BLUE,39,a)
        old=1-E((u-2.1)/1.)
        self.label('今天去海边。',780,507,66,CNL,GRAY,a*old,reveal=typed)
        strike=E((u-1.75)/.75)
        self.line([[774,550],[774+470*strike,550]],GRAY,3,a*old)
        for j,(s,c) in enumerate([('海风',BLUE),('日落',SAND),('心动',TEAL)]):
            q=E((u-2.1-j*.14)/1.2);out=E((u-4.6)/1.1)
            x=L(835+j*325,1050+j*70,out);y=507-110*math.sin(q*math.pi)*(.6+j*.15)+165*out
            self.pill(s,x,y,185,70,color(BG,c,.12),c,34,a*q*(1-out))
        # Individual glyphs travel from the idea area into a typeset sentence.
        glyphfont=ImageFont.truetype(CNM,99)
        for row,s in enumerate(['把日子，','交给海风。']):
            for j,ch in enumerate(s):
                q=E((u-4.05-row*1.6-j*.12)/1.25)
                baseline_shift=glyphfont.getbbox(ch)[1]-glyphfont.getbbox(s)[1]
                target=(775+j*100,468+row*136+baseline_shift)
                source=(895+j*160,415+row*60)
                pos=bezier(source,(source[0]+80,source[1]-100),(target[0]-40,target[1]-70),target,q)
                self.label(ch,*pos,99,CNM,INK if row==0 else BLUE,a*q,scale=L(.65,1,q))
        cursor=E((u-4.55)/3.)*(1-E((u-8.1)/.4))
        if cursor>.001:
            x=L(783,1660,E((u-5.7)/1.8));e.roundrect((x,665),(4,96),2,rgba(BLUE,cursor))
        p=cubic((770,818),(1010,875),(1390,760),(1690,813),180)
        self.line(p,BLUE,4,.28*a,progress=E((u-6.6)/2.))
        if u>6.6:
            q=E((u-6.6)/2.8);pt=bezier((770,818),(1010,875),(1390,760),(1690,813),q)
            e.circle(pt,10,rgba(BLUE))
    def coding(self,t,u):
        e=self.e;e.begin(DARK);self.title('代码，跑起来。',u,(247,249,253))
        self.tag('生成 · 调试 · 运行',128,240,u-.15,(128,170,226))
        a=E((u+.4)/.8);panel=(25,35,54)
        e.roundrect((545,611),(850,530),29,rgba(panel,a))
        for j,c in enumerate([(212,123,125),(224,191,121),(119,181,153)]):e.circle((158+j*27,383),6,rgba(c,a))
        code=[('const y = [3, 7, 4, 9, 6];',(151,194,250)),('ctx.beginPath();',(232,237,246)),('y.forEach((v, i) =>',(232,237,246)),('  ctx.lineTo(i * 80, 240 - v * 20));',(151,194,250)),('ctx.stroke();',(232,237,246))]
        for j,(s,c) in enumerate(code):
            self.label(s,157,445+j*59,29,MONO,c,a,reveal=E((u-.4-j*.56)/.7))
        run=E((u-6*BEAT)/.5);press=E((u-7*BEAT+.2)/.2)*(1-E((u-7*BEAT)/.22))
        self.pill('运行',834,801,154,58,color((66,107,164),(106,163,232),press),(255,255,255),28,a*run)
        # The code above is the exact polyline drawn on the right.
        plot=np.stack([np.linspace(1110,1750,5),725-np.array([3,7,4,9,6])*35],axis=1)
        grow=E((u-7*BEAT)/(2*BEAT))
        for k in range(4):self.line([[1080,426+k*108],[1785,426+k*108]],(59,77,105),1.5,a*.5)
        line=resample(plot,240);self.line(line,(144,192,253),7,a,progress=grow)
        for j,p in enumerate(plot):
            z=E((grow-j/4)/.2);e.circle(p,8*z,rgba((144,192,253),a))
            e.circle(p,16+3*math.sin(u*2+j),rgba((144,192,253),.10*a*z))
        if u>4.2:
            c=E((u-6*BEAT)/BEAT);pos=bezier((1080,985),(1020,841),(901,775),(842,805),c)
            arrow=np.array([[0,0],[0,27],[7,20],[14,35],[21,32],[14,17],[25,15]])+pos
            e.polygon(arrow,rgba((246,249,255),a*(1-E((u-7*BEAT-.15)/.5))))
        self.label('看得见的结果。',1435,835,38,CN,(185,202,224),a*E((u-6.3)/.6),align='center')
        if u>6.8:self.check(1118,955,E((u-6.8)/.5),.6,(134,198,168))
        self.label('运行完成',1154,933,27,CN,(134,198,168),a*E((u-6.8)/.5))
        leave=E((u-7*BEAT)/(1.5*BEAT))
        self.actor('06_blue_coding',t,L(1460,2080,leave),L(1040,1220,leave),620,alpha=a*(1-leave),action=3)
        if u>6.7:
            q=E((u-6.7)/3.2);idx=min(3,int(q*4));fraction=min(1,q*4-idx)
            p=plot[idx]*(1-fraction)+plot[idx+1]*fraction
            self.line([[p[0],p[1]+15],[p[0],773]],(117,154,207),2,a*.45)
            e.circle(p,12,rgba((241,247,255),a))
    def translate(self,t,u):
        e=self.e;e.begin(BG);self.title('不同语言，一样懂。',u)
        self.tag('理解 · 翻译',128,240,u-.15)
        a=E((u+.4)/.8);change=E((u-2.0)/2.4)
        self.pill('中文',560,371,165,64,(232,239,249),BLUE,30,a)
        self.pill('English',1360,371,190,64,(232,239,249),BLUE,30,a)
        arrow=cubic((710,371),(900,286),(1030,452),(1225,371),160)
        self.line(arrow,BLUE,4,a*.6,progress=E((u-.1)/1.1))
        point=bezier((710,371),(900,286),(1030,452),(1225,371),E((u-.8)/1.6));e.circle(point,8,rgba(BLUE,a))
        self.label('让灵感，自在流动。',960,L(502,468,change),88,CNM,INK,a*(1-.75*change),align='center',scale=L(1,.72,change))
        words=['Let ','your ','ideas ','flow.'];widths=[text_image(s,91,BOLDEN,BLUE).width-8 for s in words]
        wordfont=ImageFont.truetype(BOLDEN,91);wordtop=wordfont.getbbox('Let your ideas flow.')[1]
        cursor=960-sum(widths)/2
        for j,s in enumerate(words):
            q=E((u-2.0-j*.19)/1.5);x=L(480+j*285,cursor,q)
            y=608-100*math.sin(q*math.pi)+(wordfont.getbbox(s)[1]-wordtop)*q
            self.label(s,x,y,91,BOLDEN,BLUE,a*q,scale=L(.75,1,q));cursor+=widths[j]
        for j,c in enumerate([BLUE,TEAL,SAND]):
            p=cubic((400,810+j*20),(700,660+j*75),(1180,970-j*40),(1530,805+j*20),180)
            self.line(p,c,3,a*.18,progress=E((u-3.1-j*.1)/1.9))
            q=(max(0,u-3.1-j*.15)/3.9)%1
            pt=bezier((400,810+j*20),(700,660+j*75),(1180,970-j*40),(1530,805+j*20),q)
            e.circle(pt,6,rgba(c,a*E((u-3.1)/.7)*.6))
    def finishes(self,t,u):
        e=self.e;e.begin(BG);self.title('三种喜欢。',u)
        self.tag('深海蓝 · 暮砂棕 · 云瓷白',128,239,u-.15,GRAY)
        leave=E((u-5.3)/1.6)
        for j,k in enumerate(MASTER):
            enter=E((u+.45-j*.12)/1.05);pulse=1+.012*math.sin((u-j*.3)*1.9)
            x=L(960,448+j*512,enter)+(j-1)*90*leave;y=L(1140,916,enter)+210*leave
            self.actor(k,t,x,y,620*pulse,alpha=enter*(1-leave),angle=.009*math.sin(u*1.2+j))
            self.label(NAMES[j],x,967,34,CN,INK,E((u-.5-j*.1)/.65)*(1-leave),align='center')
            e.circle((x,1034),7,rgba(COLORS[j],enter))
        # A continuous selector travels through all three, once, over 6.7 seconds.
        sel=E((u-1.6)/2.8);x=L(448,1472,sel)
        self.line([[448,1034],[1472,1034]],(210,218,229),1.5,.7)
        e.circle((x,1034),14,(0,0,0,0),2,rgba(BLUE,.8))
    def rice(self,t,u):
        e=self.e;e.begin(BG);a=E((u+.4)/.8)
        self.label('这么能干，吃什么？',125,139,72,CNM,INK,a)
        self.actor(RICE,t,1405,1023,845,alpha=a,action=2,angle=.008*math.sin(u*1.6))
        self.label('只吃',137,337,63,CN,GRAY,a)
        # The user's exact joke is visible, with a genuinely animated strike-through.
        self.label('大白饭',128,462,105,CNM,GRAY,a)
        s=E((u-2.3)/.65)
        self.line([[119,528],[119+372*s,528]],BLUE,7,a)
        corrected=E((u-3.0)/.9)
        self.label('大米饭。',125,623+40*(1-corrected),118,CNM,BLUE,a*corrected,reveal=E((u-3.)/1.1))
        self.label('给点米饭，继续开工。',137,844,35,CN,GRAY,a*E((u-5.1)/.65))
        # Warm ivory rice grains travel as clean flat pills, never silver debris.
        for j,g in enumerate(self.grains):
            launch=3.7+g[0]*3.6;age=(u-launch)/1.75
            if not 0<age<1:continue
            p=bezier((700+g[1]*220,1010),(760+g[2]*270,400-g[3]*120),(1220,350),(1401,681),age)
            angle=age*3.5+g[4]*math.pi
            pp=roundrect_path(13+g[4]*6,6+g[3]*2,3,45)
            e.polygon(transform(pp,p,angle=angle),rgba((224,211,185),.75*math.sin(math.pi*age)))
        steam=E((u-4.0)/1.)
        for j in range(3):
            p=cubic((1367+j*25,690),(1350+j*25,653),(1395+j*25,641),(1370+j*25,601),80)
            p[:,0]+=math.sin(u*1.7+j)*7
            self.line(p,(178,190,204),2,steam*.4)
    def finale(self,t,u):
        e=self.e;e.begin(BG);a=E((u+.4)/.8)
        self.actor(PRESENT,t,1415,1005,875,alpha=a,angle=-.008*math.sin(u*1.1))
        lines=[('想得明白。',BLUE),('写得漂亮。',INK),('做得出来。',INK)]
        for j,(s,c) in enumerate(lines):
            k=E((u-j*1.25+.2)/.8)
            self.label(s,128,259+j*169+44*(1-k),98,CNM,c,a*k,reveal=k)
        # A single animated underline feeds the final whale logo assembly.
        p=cubic((140,845),(755,1010),(1160,660),(1710,834),240)
        self.line(p,BLUE,5,.35*a,progress=E((u-2.8)/2.5))
        if u>2.8:
            q=E((u-2.8)/3.2);pt=bezier((140,845),(755,1010),(1160,660),(1710,834),q);e.circle(pt,12,rgba(BLUE,a))
    def brand(self,t,u):
        e=self.e;e.begin(BG);a=E((u+.4)/1.1)
        self.whale(960,L(490,417,a),1.15,a,E((u+.35)/1.6))
        letters='IFISH';font=ImageFont.truetype(BOLDEN,124);adv=[font.getlength(ch)+5 for ch in letters];cursor=960-(sum(adv)-5)/2
        for j,ch in enumerate(letters):
            k=E((u-.7-j*.08)/.75)
            dy=font.getbbox(ch)[1]-font.getbbox(letters)[1]
            self.label(ch,cursor,579+40*(1-k)+dy,124,BOLDEN,INK,k);cursor+=adv[j]
        self.label('有想法，就有办法。',960,788,43,CN,GRAY,E((u-2.1)/.8),align='center')
    def frame(self,t):
        # Every chapter boundary is a moving soft-edged vector mask, never a cut.
        t=max(0,min(82.99999,t));i=min(9,int(np.searchsorted(STARTS,t,side='right')-1))
        boundary=None
        for j in range(1,10):
            if abs(t-STARTS[j])<.56:boundary=j;break
        if boundary is None:self.methods[i](t,t-STARTS[i])
        else:
            j=boundary;b=STARTS[j];self.methods[j-1](t,t-STARTS[j-1]);self.e.capture(0)
            self.methods[j](t,t-STARTS[j]);self.e.capture(1)
            self.e.merge(E((t-b+.56)/1.12),[0,1,2,3,1,2,0,1,3][j-1])
        return self.e

def previews(film):
    times=[.75,1.9,3.5,4.9,5.9,7.2,8.8,10.6,13.9,15.8,18.7,22.6,24.7,27.6,30.8,33.,35.4,38.7,41.8,44.6,46.5,49.,51.6,54.9,57.2,59.6,61.5,63.1,65.0,68.,71.6,73.9,76.8,78.8,80.8,82.7]
    sheet=Image.new('RGB',(1920,9*294),'#151a24');d=ImageDraw.Draw(sheet);font=ImageFont.truetype(EN,17)
    for i,t in enumerate(times):
        im=film.frame(t).image();im.save(WORK/'qa'/f'frame_{t:.2f}.jpg',quality=94)
        x=i%4*480;y=i//4*294;sheet.paste(im.resize((480,270),Image.Resampling.LANCZOS),(x,y));d.text((x+8,y+273),f'{t:.2f}s',font=font,fill='white')
    sheet.save(OUT/'IFISH_v5_storyboard.jpg',quality=94)
    film.frame(81.0).image().save(OUT/'IFISH_v5_cover.jpg',quality=96)
    print('PREVIEWS SAVED',flush=True)

def render(film,start=0,duration=83,name='IFISH_v5_83s_1080p60.mp4'):
    fps=60;total=round(duration*fps);dest=OUT/name
    cmd=['ffmpeg','-hide_banner','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1920x1080','-framerate','60','-i','pipe:0','-ss',str(start),'-i',str(ROOT/'source'/'reference_audio.m4s'),
      '-filter_complex',f'[0:v]vflip,scale=out_color_matrix=bt709:out_range=tv[v];[1:a]atrim=0:{duration},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.03,afade=t=out:st={duration-1.4}:d=1.4[a]',
      '-map','[v]','-map','[a]','-c:v','h264_nvenc','-preset','p7','-tune','hq','-rc','vbr','-cq','17','-b:v','11M','-maxrate','26M','-bufsize','26M','-pix_fmt','yuv420p','-profile:v','high',
      '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','320k','-ar','48000','-t',str(duration),'-movflags','+faststart','-metadata','title=IFISH | Ideas in motion',str(dest)]
    log=(WORK/'render_v5.log').open('w',encoding='utf-8');p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log);beg=time.time()
    try:
        for i in range(total):
            t=start+i/fps;film.e.start_accum()
            # 8x spatial AA and three samples across a 180-degree shutter.
            for dt in [-1/360,0,1/360]:film.frame(t+dt);film.e.sample(1/3)
            p.stdin.write(film.e.finish())
            if i%300==0:print(f'{i}/{total} frames | {t:.1f}s | elapsed {time.time()-beg:.1f}s',flush=True)
        p.stdin.close();rc=p.wait()
        if rc:raise RuntimeError(f'FFmpeg {rc}; inspect render_v5.log')
    except BaseException:p.kill();raise
    finally:log.close()
    print(f'SAVED {dest} | {dest.stat().st_size/1024/1024:.1f} MiB | elapsed {time.time()-beg:.1f}s',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preview-only',action='store_true');parser.add_argument('--start',type=float,default=0);parser.add_argument('--duration',type=float,default=83);parser.add_argument('--name',default='IFISH_v5_83s_1080p60.mp4');args=parser.parse_args()
    OUT.mkdir(exist_ok=True);(WORK/'qa').mkdir(exist_ok=True)
    timeline={'version':5,'duration':83,'fps':60,'frames':4980,'resolution':[1920,1080],'music':'Original user reference audio, continuous first 83 seconds','transition_duration':1.12,'graphics':'2D paths, C2 easing, animated text and live diagram/code output, local 2D character deformation','chapters':[{'start':STARTS[i],'end':STARTS[i+1],'name':TITLES[i]} for i in range(10)]}
    (WORK/'timeline_v5.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
    film=Film();print(f'GPU: {film.e.ctx.info["GL_RENDERER"]}',flush=True);previews(film)
    if not args.preview_only:render(film,args.start,args.duration,args.name)
