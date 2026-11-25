# Prep for a teardown of downloaded reels: prep_video + scene>0.3 cut list -> <dir>/prep/<key>/cuts.json.
# Run: python3 cartoons_prep.py <research-dir>   (raw mp4s in <research-dir>/raw/; ref_prep.py next to this file)
import sys, os, glob, json, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_prep
if len(sys.argv) < 2: sys.exit('usage: cartoons_prep.py <research-dir>')
base=sys.argv[1].rstrip('/')
for f in sorted(glob.glob(base+'/raw/*.mp4')):
    k=os.path.basename(f)[:-4]; out=f'{base}/prep/{k}'
    if os.path.exists(out+'/cuts.json'): continue
    dur=ref_prep.prep_video(f,out)
    r=subprocess.run(['ffmpeg','-v','info','-i',f,'-vf',"select='gt(scene,0.3)',showinfo",'-f','null','-'],capture_output=True,text=True,stdin=subprocess.DEVNULL)
    cuts=[round(float(x),1) for x in re.findall(r'pts_time:([\d.]+)',r.stderr)]
    json.dump({'duration':dur,'cuts':cuts},open(out+'/cuts.json','w'))
    print('ok',k,round(dur,1),len(cuts),flush=True)
