"""2D vector, mesh-deformed cutouts and continuous graphic transitions."""
from flat_engine import *

RIG_VS='''#version 330
in vec2 uv_in;out vec2 uv;out vec2 screen;
uniform vec2 center;uniform vec2 size;uniform vec2 resolution;
uniform float angle;uniform float clock;uniform float action;
void main(){
  uv=uv_in;vec2 p=(uv-.5)*size;
  float upper=1.-smoothstep(.40,.78,uv.y);
  float breath=sin(clock*1.8);
  float hair=smoothstep(.17,.40,abs(uv.x-.5))*smoothstep(.27,.55,uv.y);
  p.x+=size.y*(.0035*sin(clock*1.5)*upper+.0038*sin(clock*2.15+uv.y*5.)*hair);
  p.y-=size.y*.0025*breath*upper;
  vec2 hand=uv-(action<1.5?vec2(.86,.53):(action<2.5?vec2(.28,.51):vec2(.39,.74)));
  float local=exp(-dot(hand*vec2(8.,10.),hand*vec2(8.,10.)));
  p.y+=local*size.y*(action>2.5?.0025:.010)*sin(clock*(action<1.5?2.1:(action<2.5?3.8:16.)));
  p.x+=local*size.y*.004*cos(clock*2.1);
  mat2 r=mat2(cos(angle),sin(angle),-sin(angle),cos(angle));p=r*p+center;screen=p;
  gl_Position=vec4(p.x/resolution.x*2.-1.,1.-p.y/resolution.y*2.,0,1);
}'''
RIG_FS='''#version 330
in vec2 uv;in vec2 screen;uniform sampler2D image;uniform float opacity;
uniform vec4 clip_rect;out vec4 frag;
void main(){vec4 c=texture(image,uv);
float mask=step(clip_rect.x,screen.x)*step(clip_rect.y,screen.y)*step(screen.x,clip_rect.z)*step(screen.y,clip_rect.w);
frag=vec4(c.rgb,c.a*opacity*mask);}
'''
TRANSITION_FS='''#version 330
in vec2 uv;uniform sampler2D from_image;uniform sampler2D to_image;
uniform float progress;uniform int kind;out vec4 frag;
void main(){
 vec2 p=vec2(uv.x,1.-uv.y);float a=progress;float m=0.;
 if(kind==0){float r=mix(-.04,.88,a);m=1.-smoothstep(r-.035,r+.035,distance(p,vec2(.65,.53)));}
 else if(kind==1){float edge=mix(-.12,1.12,a);float d=p.x+.075*sin(p.y*6.283+a*3.);m=1.-smoothstep(edge-.04,edge+.04,d);}
 else if(kind==2){float d=abs(p.y-.5)+.10*sin(p.x*6.28+a*3.);float r=mix(-.12,.65,a);m=1.-smoothstep(r-.04,r+.04,d);}
 else{float r=mix(-.04,.81,a);float d=length((p-vec2(.5,.5))*vec2(1.15,1.));m=1.-smoothstep(r-.04,r+.04,d);}
 if(progress<=0.)m=0.;if(progress>=1.)m=1.;
 frag=mix(texture(from_image,uv),texture(to_image,uv),m);
}'''

class KineticEngine(FlatEngine):
    def __init__(self):
        super().__init__()
        c=self.ctx
        self.rig=c.program(vertex_shader=RIG_VS,fragment_shader=RIG_FS)
        self.rig['resolution'].value=(self.w,self.h)
        # Dense enough for continuous local hair/arm motion, no perspective.
        n=48;uv=[]
        for y in range(n):
            for x in range(n):
                a=(x/n,y/n);b=((x+1)/n,y/n);d=(x/n,(y+1)/n);e=((x+1)/n,(y+1)/n)
                uv.extend([a,b,d,b,e,d])
        vb=c.buffer(np.asarray(uv,dtype='f4').tobytes());self.rigva=c.vertex_array(self.rig,[(vb,'2f','uv_in')])
        self.stage=[c.framebuffer([c.texture((self.w,self.h),4)]) for i in range(2)]
        self.transition=c.program(vertex_shader=COPY_VS,fragment_shader=TRANSITION_FS)
        quad=np.array([[-1,-1],[1,-1],[-1,1],[1,-1],[1,1],[-1,1]],dtype='f4')
        qb=c.buffer(quad.tobytes());self.transitionva=c.vertex_array(self.transition,[(qb,'2f','pos')])
    def actor(self,key,t,center,height,alpha=1,action=1,angle=0,clip=(-10000,-10000,10000,10000)):
        if alpha<.001:return
        tx,(w,h)=self.texture(key);tx.use(0);p=self.rig
        p['image'].value=0;p['center'].value=tuple(center);p['size'].value=(w/h*height,height)
        p['clock'].value=t;p['action'].value=float(action);p['angle'].value=angle
        p['opacity'].value=alpha;p['clip_rect'].value=tuple(clip);self.rigva.render()
    def capture(self,i):self.ctx.copy_framebuffer(self.stage[i],self.ms)
    def merge(self,u,kind):
        self.ms.use();self.ctx.disable(moderngl.BLEND)
        for i,f in enumerate(self.stage):f.color_attachments[0].use(i)
        p=self.transition;p['from_image'].value=0;p['to_image'].value=1
        p['progress'].value=float(u);p['kind'].value=kind;self.transitionva.render()
        self.ctx.enable(moderngl.BLEND);self.ctx.blend_func=moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA
