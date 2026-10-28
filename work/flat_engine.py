"""Orthographic 2D path renderer. No perspective, lighting, depth or 3D meshes."""
from __future__ import annotations
import math
from pathlib import Path
from functools import lru_cache
import numpy as np
import moderngl
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps

CN='C:/Windows/Fonts/msyh.ttc';CNL='C:/Windows/Fonts/msyhl.ttc';CNM='C:/Windows/Fonts/msyhbd.ttc'
EN='C:/Windows/Fonts/arial.ttf';ENB='C:/Windows/Fonts/arialbd.ttf';SCRIPT='C:/Windows/Fonts/segoesc.ttf'
def ease(t):
    t=np.clip(t,0,1);return t*t*t*(t*(t*6-15)+10)
def cubic(a,b,c,d,n=100):
    t=np.linspace(0,1,n)[:,None];return (1-t)**3*np.array(a)+3*(1-t)**2*t*np.array(b)+3*(1-t)*t*t*np.array(c)+t**3*np.array(d)
def resample(points,n=240,closed=False):
    p=np.asarray(points,dtype=float)
    if closed and np.linalg.norm(p[0]-p[-1])>.01:p=np.vstack([p,p[0]])
    lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    if lengths[-1]<1e-8:return np.tile(p[0],(n,1))
    u=np.linspace(0,lengths[-1],n,endpoint=not closed)
    return np.stack([np.interp(u,lengths,p[:,0]),np.interp(u,lengths,p[:,1])],axis=1)
def transform(p,center=(960,540),scale=1,angle=0):
    c,s=math.cos(angle),math.sin(angle);m=np.array([[c,-s],[s,c]])
    return np.asarray(p)@m.T*scale+np.asarray(center)
def circle_path(r=1,n=240,phase=0):
    t=np.linspace(phase,phase+2*math.pi,n,endpoint=False);return np.stack([np.cos(t)*r,np.sin(t)*r],axis=1)
def roundrect_path(width,height,radius,n=240):
    p=[]
    for cx,cy,a in [(width/2-radius,-height/2+radius,-math.pi/2),(width/2-radius,height/2-radius,0),(-width/2+radius,height/2-radius,math.pi/2),(-width/2+radius,-height/2+radius,math.pi)]:
        t=np.linspace(a,a+math.pi/2,40);p.extend(np.stack([cx+radius*np.cos(t),cy+radius*np.sin(t)],axis=1))
    return resample(p,n,True)
def leaf_path(n=240):
    p=np.vstack([cubic((0,0),(.3,-.10),(.85,-.07),(1,0),90),cubic((1,0),(.85,.07),(.3,.10),(0,0),90)])
    return resample(p,n,True)
def rgba(c,a=1):return tuple(v/255 for v in c[:3])+(a,)

FLAT_VS='''#version 330
in vec2 pos;uniform vec2 resolution;void main(){gl_Position=vec4(pos.x/resolution.x*2.-1.,1.-pos.y/resolution.y*2.,0,1);}
'''
FLAT_FS='''#version 330
uniform vec4 color;out vec4 frag;void main(){frag=color;}
'''
SHAPE_VS='''#version 330
in vec2 uv_in;out vec2 uv;uniform vec2 center;uniform vec2 size;uniform vec2 resolution;
void main(){uv=uv_in;vec2 p=(uv-.5)*(size+vec2(4))+center;gl_Position=vec4(p.x/resolution.x*2.-1.,1.-p.y/resolution.y*2.,0,1);}
'''
SHAPE_FS='''#version 330
in vec2 uv;uniform vec2 size;uniform float radius;uniform float stroke;uniform vec4 color;uniform vec4 outline;out vec4 frag;
void main(){vec2 p=(uv-.5)*(size+vec2(4));vec2 q=abs(p)-(size*.5-vec2(radius));float d=length(max(q,0.))+min(max(q.x,q.y),0.)-radius;
float outer=1.-smoothstep(-.6,.6,d);float inner=1.-smoothstep(-.6,.6,d+stroke);vec4 c=mix(outline,color,inner);frag=vec4(c.rgb,c.a*outer);}
'''
TEX_VS='''#version 330
in vec2 uv_in;out vec2 uv;out vec2 screen;uniform vec2 center;uniform vec2 size;uniform vec2 resolution;uniform float angle;uniform vec4 source_rect;
void main(){vec2 p=(uv_in-.5)*size;mat2 r=mat2(cos(angle),sin(angle),-sin(angle),cos(angle));p=r*p+center;screen=p;
uv=source_rect.xy+uv_in*source_rect.zw;gl_Position=vec4(p.x/resolution.x*2.-1.,1.-p.y/resolution.y*2.,0,1);}
'''
TEX_FS='''#version 330
in vec2 uv;in vec2 screen;uniform sampler2D image;uniform float opacity;uniform vec4 clip_rect;uniform vec3 iris;uniform float iris_on;uniform float reveal;uniform float reverse;
out vec4 frag;void main(){vec4 c=texture(image,uv);
float rect=step(clip_rect.x,screen.x)*step(clip_rect.y,screen.y)*step(screen.x,clip_rect.z)*step(screen.y,clip_rect.w);
float radial=1.-smoothstep(iris.z-1.,iris.z+1.,length(screen-iris.xy));
float wipe=1.-smoothstep(reveal-2.,reveal+2.,screen.x);wipe=mix(wipe,1.-wipe,reverse);
frag=vec4(c.rgb,c.a*opacity*rect*mix(1.,radial,iris_on)*wipe);}
'''
COPY_VS='''#version 330
in vec2 pos;out vec2 uv;void main(){uv=pos*.5+.5;gl_Position=vec4(pos,0,1);}
'''
COPY_FS='''#version 330
in vec2 uv;uniform sampler2D image;uniform float weight;out vec4 frag;void main(){frag=texture(image,uv)*weight;}
'''

class FlatEngine:
    def __init__(self,w=1920,h=1080):
        self.w,self.h=w,h;self.ctx=moderngl.create_standalone_context(require=330);c=self.ctx
        self.ms=c.framebuffer([c.renderbuffer((w,h),4,samples=8)])
        self.resolve=c.framebuffer([c.texture((w,h),4)])
        self.accum=c.framebuffer([c.texture((w,h),4,dtype='f2')])
        self.out=c.framebuffer([c.texture((w,h),4)])
        self.flat=c.program(vertex_shader=FLAT_VS,fragment_shader=FLAT_FS)
        self.shape=c.program(vertex_shader=SHAPE_VS,fragment_shader=SHAPE_FS)
        self.tex=c.program(vertex_shader=TEX_VS,fragment_shader=TEX_FS)
        self.copy=c.program(vertex_shader=COPY_VS,fragment_shader=COPY_FS)
        for p in [self.flat,self.shape,self.tex]:p['resolution'].value=(w,h)
        self.buf=c.buffer(reserve=5000000,dynamic=True);self.va=c.vertex_array(self.flat,[(self.buf,'2f','pos')])
        uv=np.array([[0,0],[1,0],[0,1],[1,0],[1,1],[0,1]],dtype='f4')
        vb=c.buffer(uv.tobytes());self.shapeva=c.vertex_array(self.shape,[(vb,'2f','uv_in')]);self.texva=c.vertex_array(self.tex,[(vb,'2f','uv_in')])
        ndc=c.buffer((uv*2-1).astype('f4').tobytes());self.copyva=c.vertex_array(self.copy,[(ndc,'2f','pos')]);self.textures={}
    def begin(self,bg=(247,247,247)):
        self.ms.use();self.ms.clear(*(v/255 for v in bg),1)
        self.ctx.disable(moderngl.DEPTH_TEST);self.ctx.enable(moderngl.BLEND);self.ctx.blend_func=moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA
    def triangles(self,pts,color):
        if len(pts)==0 or color[3]<.001:return
        p=np.asarray(pts,dtype='f4').reshape(-1,2);self.flat['color'].value=color;self.buf.write(p.tobytes());self.va.render(vertices=len(p))
    def polygon(self,points,color):
        p=np.asarray(points,dtype='f4');mid=p.mean(axis=0)
        tri=np.stack([np.broadcast_to(mid,p.shape),p,np.roll(p,-1,axis=0)],axis=1)
        self.triangles(tri,color)
    def line(self,points,color,width=2,closed=False,roundcaps=False):
        p=np.asarray(points,dtype='f4')
        if len(p)<2 or color[3]<.001:return
        if closed:p=np.vstack([p,p[0]])
        d=np.diff(p,axis=0);d/=np.maximum(np.linalg.norm(d,axis=1,keepdims=True),1e-8)
        n=np.stack([-d[:,1],d[:,0]],axis=1)
        avg=np.vstack([n[0],n[:-1]+n[1:],n[-1]])
        avg/=np.maximum(np.linalg.norm(avg,axis=1,keepdims=True),1e-6)
        # Limited miters avoid spikes while retaining smooth Bezier joins.
        den=np.r_[1,np.maximum((avg[1:-1]*n[1:]).sum(axis=1),.4),1]
        offsets=avg*(width/2/den[:,None]);a=p[:-1];b=p[1:];an=offsets[:-1];bn=offsets[1:]
        tri=np.stack([a+an,a-an,b+bn,b+bn,a-an,b-bn],axis=1)
        self.triangles(tri,color)
        if roundcaps and not closed:
            self.roundrect(p[0],(width,width),width/2,color);self.roundrect(p[-1],(width,width),width/2,color)
    def roundrect(self,center,size,radius,color,stroke=0,outline=(0,0,0,0)):
        if max(color[3],outline[3])<.001 or min(size)<=0:return
        p=self.shape;p['center'].value=tuple(center);p['size'].value=tuple(size);p['radius'].value=min(radius,min(size)/2)
        p['color'].value=color;p['stroke'].value=stroke;p['outline'].value=outline;self.shapeva.render()
    def circle(self,center,r,color,stroke=0,outline=(0,0,0,0)):
        if r>0:self.roundrect(center,(r*2,r*2),r,color,stroke,outline)
    def texture(self,key,image=None,trim=False):
        if key not in self.textures:
            im=Image.open(image).convert('RGBA') if isinstance(image,(str,Path)) else image.convert('RGBA')
            if trim:
                box=im.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()
                if box:im=im.crop(box)
            tx=self.ctx.texture(im.size,4,im.tobytes());tx.build_mipmaps();tx.filter=moderngl.LINEAR_MIPMAP_LINEAR,moderngl.LINEAR;tx.repeat_x=False;tx.repeat_y=False
            self.textures[key]=(tx,im.size)
        return self.textures[key]
    def sprite(self,key,image=None,center=(960,540),size=None,height=None,alpha=1,angle=0,clip=(-10000,-10000,10000,10000),iris=None,reveal=10000,reverse=0,source=(0,0,1,1)):
        if alpha<.001:return
        tx,(iw,ih)=self.texture(key,image)
        if size is None:size=(iw/ih*height,height) if height else (iw,ih)
        p=self.tex;tx.use(0);p['image'].value=0;p['center'].value=tuple(center);p['size'].value=tuple(size);p['opacity'].value=alpha;p['angle'].value=angle
        p['clip_rect'].value=tuple(clip);p['iris'].value=tuple(iris or (960,540,2000));p['iris_on'].value=float(iris is not None)
        p['reveal'].value=reveal;p['reverse'].value=reverse;p['source_rect'].value=source;self.texva.render()
    def start_accum(self):self.accum.use();self.accum.clear(0,0,0,0)
    def sample(self,weight=1):
        self.ctx.copy_framebuffer(self.resolve,self.ms);self.accum.use()
        self.ctx.enable(moderngl.BLEND);self.ctx.blend_func=moderngl.ONE,moderngl.ONE
        self.resolve.color_attachments[0].use(0);self.copy['image'].value=0;self.copy['weight'].value=weight;self.copyva.render()
    def finish(self):
        self.out.use();self.ctx.disable(moderngl.BLEND);self.accum.color_attachments[0].use(0)
        self.copy['weight'].value=1;self.copyva.render();return self.out.read(components=3,alignment=1)
    def image(self):
        self.start_accum();self.sample();return ImageOps.flip(Image.frombytes('RGB',(self.w,self.h),self.finish()))

@lru_cache(maxsize=256)
def text_image(text,size,font=EN,color=(26,26,28),tracking=0):
    f=ImageFont.truetype(font,size*2);d=ImageDraw.Draw(Image.new('RGBA',(1,1)));box=d.textbbox((0,0),text,font=f)
    width=math.ceil(sum(d.textlength(c,font=f) for c in text)+(len(text)-1)*tracking*2) if tracking else box[2]-box[0]
    im=Image.new('RGBA',(max(2,width+16),box[3]-box[1]+16));draw=ImageDraw.Draw(im);x=8
    if tracking:
        for c in text:draw.text((x,8-box[1]),c,font=f,fill=(*color,255));x+=draw.textlength(c,font=f)+tracking*2
    else:draw.text((8-box[0],8-box[1]),text,font=f,fill=(*color,255))
    return im.resize((im.width//2,im.height//2),Image.Resampling.LANCZOS)
def shadow_image():
    im=Image.new('RGBA',(800,150));ImageDraw.Draw(im).ellipse((140,55,660,95),fill=(25,25,30,45));return im.filter(ImageFilter.GaussianBlur(22))
