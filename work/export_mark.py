"""Export the same original 2D whale mark used by the film as SVG and RGBA PNG."""
import math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from flat_engine import leaf_path,roundrect_path,transform

OUT=Path(__file__).resolve().parents[1]/'output';BLUE=(48,91,151);SIZE=(340,230);S=6
im=Image.new('RGBA',(SIZE[0]*S,SIZE[1]*S));d=ImageDraw.Draw(im)
body=(45.5,79.5,216.5,180.5)
d.rounded_rectangle(tuple(round(v*S) for v in body),radius=round(50.5*S),fill=(*BLUE,255))
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 230"><title>IFISH whale mark</title><defs><mask id="eye"><rect width="340" height="230" fill="white"/><circle cx="81" cy="118" r="6.5" fill="black"/></mask></defs><g fill="#305b97" mask="url(#eye)"><rect x="45.5" y="79.5" width="171" height="101" rx="50.5"/>']
for side in [-1,1]:
    leaf=leaf_path(120);leaf[:,0]*=93;leaf[:,1]*=230;p=transform(leaf,(188,128),angle=side*.75)
    d.polygon([(round(x*S),round(y*S)) for x,y in p],fill=(*BLUE,255))
    svg.append('<polygon points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in p)+'"/>')
for j in range(3):
    h=23 if j==1 else 17;p=transform(roundrect_path(10,h,5,80),(115+(j-1)*19,54-(j==1)*6),angle=(j-1)*.62)
    d.polygon([(round(x*S),round(y*S)) for x,y in p],fill=(*BLUE,255))
    svg.append('<polygon points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in p)+'"/>')
d.ellipse(tuple(round(v*S) for v in (74.5,111.5,87.5,124.5)),fill=(0,0,0,0))
svg.append('</g></svg>');(OUT/'IFISH_mark.svg').write_text(''.join(svg),encoding='utf-8')
im.resize((1360,920),Image.Resampling.LANCZOS).save(OUT/'IFISH_mark.png')
print('Mark exported')
