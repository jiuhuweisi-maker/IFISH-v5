"""Audit the delivered bitstream, continuous source music, and temporal joins."""
import json,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'work'/'qa';OUT=ROOT/'output'
VIDEO=OUT/'IFISH_v5_83s_1080p60.mp4'
def run(cmd):return subprocess.check_output(cmd)
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(VIDEO)]))
v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'60/1',4980)
assert abs(float(probe['format']['duration'])-83)<.001
assert a['channels']==2 and a['codec_name']=='aac'
check=subprocess.run(['ffmpeg','-v','error','-i',str(VIDEO),'-f','null','-'],capture_output=True,text=True)
assert check.returncode==0 and not check.stderr.strip(),check.stderr
raw=run(['ffmpeg','-v','error','-i',str(VIDEO),'-vf','scale=256:144,format=gray','-f','rawvideo','-pix_fmt','gray','-'])
frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,144,256).astype(np.int16)
assert len(frames)==4980
diff=np.abs(np.diff(frames,axis=0));delta=diff.mean(axis=(1,2));changed=(diff>2).mean(axis=(1,2))
peaks=[]
for i in np.argsort(delta)[-16:][::-1]:
    peaks.append({'time':round((int(i)+1)/60,4),'mean_luma_difference':round(float(delta[i]),4)})
joins=[];timeline=json.loads((ROOT/'work'/'timeline_v5.json').read_text(encoding='utf-8'))
for ch in timeline['chapters'][1:]:
    t=ch['start'];i=round(t*60);area=delta[max(0,i-15):i+15]
    joins.append({'time':t,'mean_luma_difference_at_center':round(float(delta[min(i,len(delta)-1)]),4),'max_in_half_second':round(float(area.max()),4)})
spikes=[]
for i in range(30,len(delta)-30):
    local=np.r_[delta[i-20:i-2],delta[i+3:i+21]];med=max(.02,float(np.median(local)))
    if delta[i]>.8 and delta[i]/med>7:
        spikes.append({'time':round((i+1)/60,4),'difference':round(float(delta[i]),4),'ratio':round(float(delta[i]/med),2)})
def frame(t,w=480,h=270):
    raw=run(['ffmpeg','-v','error','-ss',str(t),'-i',str(VIDEO),'-frames:v','1','-vf',f'scale={w}:{h}','-f','rawvideo','-pix_fmt','rgb24','-'])
    return Image.frombytes('RGB',(w,h),raw)
def contact(times,name,cols=4):
    w,h=480,270;rows=(len(times)+cols-1)//cols
    sheet=Image.new('RGB',(cols*w,rows*(h+25)),'#111722');d=ImageDraw.Draw(sheet);f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    for i,t in enumerate(times):
        x=i%cols*w;y=i//cols*(h+25);sheet.paste(frame(t),(x,y));d.text((x+8,y+h+3),f'{t:.3f}s',font=f,fill='white')
    sheet.save(QA/name,quality=94)
contact([1.9,3.15,4.8,5.9,6.4,6.8,7.2,7.6,8.1,8.5,8.9,9.3],'encoded_opening.jpg')
contact([15.6,18.7,20.1,22.4,25.8,28.8,30.4,33.1,36.2,39.1,40.6,43.8,46.8,48.9,50.9,52.8],'encoded_features.jpg')
contact([54.8,57.0,59.2,60.0,61.9,62.5,63.1,63.9,65.0,68.5,73.7,80.4],'encoded_finishes_rice_brand.jpg')
contact([13.35,13.65,13.85,14.05,34.25,34.55,34.75,34.95,59.6,59.9,60.1,60.4],'encoded_transitions.jpg')
wav=QA/'final_audio.wav'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(VIDEO),'-ac','1','-ar','22050','-c:a','pcm_s16le',str(wav)],check=True)
def samples(p):
    with wave.open(str(p),'rb') as f:return np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)
reference_wav=QA/'source_audio.wav'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(ROOT/'source'/'reference_audio.m4s'),'-ac','1','-ar','22050','-c:a','pcm_s16le',str(reference_wav)],check=True)
source=samples(reference_wav);final=samples(wav)
lo,hi=round(.2*22050),round(81.3*22050)
corr=float(np.corrcoef(source[lo:hi],final[lo:hi])[0,1]);assert corr>.98,corr
result={'file':VIDEO.relative_to(ROOT).as_posix(),'duration_seconds':float(probe['format']['duration']),'resolution':[v['width'],v['height']],'fps':v['r_frame_rate'],'frames':int(v['nb_frames']),'size_bytes':int(probe['format']['size']),'decode_errors':check.stderr.strip(),'music_correlation':corr,'largest_frame_differences':peaks,'chapter_joins':joins,'isolated_temporal_spikes_for_review':spikes,'functional_demo_seconds':round(timeline['chapters'][6]['start']-timeline['chapters'][2]['start'],3),'color_section_seconds':round(timeline['chapters'][6]['end']-timeline['chapters'][6]['start'],3),'new_builtin_generated_action_assets':3}
(QA/'verification_v5.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
