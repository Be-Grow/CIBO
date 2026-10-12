import json,sys,numpy as np,subprocess,wave
import os
SR=48000
def shutter():
    n=int(0.055*SR); t=np.arange(n)/SR
    rng=np.random.default_rng(7)
    noise=rng.standard_normal(n)
    env=np.exp(-t*95)
    a=noise*env
    n2=int(0.035*SR); t2=np.arange(n2)/SR
    b=rng.standard_normal(n2)*np.exp(-t2*160)
    a[:n2]+=b*0.8
    # band-limit: simple one-pole hp + lp
    y=np.copy(a); prev=0
    for k in range(1,len(y)): y[k]=0.92*(y[k-1]+a[k]-a[k-1])
    z=np.copy(y); s=0
    for k in range(len(z)):
        s=s+0.35*(z[k]-s); z[k]=s
    z/= (np.max(np.abs(z))+1e-9)
    z*=0.16
    z[:24]*=np.linspace(0,1,24)
    z[-200:]*=np.linspace(1,0,200)
    return z.astype(np.float32)
# Cliques aprovados pelo usuario (12/10/2026: "sempre use esses aqui"). CLICK aceita
# varios arquivos separados por '|' e alterna entre eles; vazio = estes dois.
DEFAULT_CLICKS='/Volumes/SSD/Music/Sound/Músicas edicao/click lens.wav|/Users/bruno/CIBO/skills/fernanda-produto/assets/camera_click.mp3'
def _load(fp):
    raw=subprocess.run(f'ffmpeg -v error -i "{fp}" -f s16le -ar {SR} -ac 1 -',
                       shell=True,capture_output=True).stdout
    a=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768.0
    pk=float(np.abs(a).max()) or 1.0
    return (a/pk*float(os.environ.get('CLICK_GAIN','0.22'))).astype(np.float32)
def load_click():
    fps=[f for f in (os.environ.get('CLICK') or DEFAULT_CLICKS).split('|') if f and os.path.exists(f)]
    return [_load(f) for f in fps] or [shutter()]
CL=load_click()
def variants(a):
    """CLICK_VARIANTS=1: o arquivo traz varias batidas (ex.: camera_click.mp3 com 4); separa
    cada uma pelo envelope (> -40 dB) para alternar entre elas em vez de repetir a mesma."""
    h=240; n=len(a)//h
    if n==0: return [a]
    env=np.abs(a[:n*h]).reshape(n,h).max(1); thr=env.max()*0.01
    out=[]; on=None
    for i,v in enumerate(env):
        if v>thr and on is None: on=i
        if v<=thr and on is not None:
            if (i-on)*h>0.02*SR: out.append(a[max(0,on*h-int(0.01*SR)):i*h])
            on=None
    return out or [a]
# cada arquivo vira uma ou mais batidas (o camera_click.mp3 traz 4); alterna entre todas
VARS=[v for a in CL for v in (variants(a) if len(a)>2*SR and os.environ.get('CLICK_VARIANTS','1')!='0' else [a])]  # so arquivo longo (varias batidas) e dividido
MIN_GAP=float(os.environ.get('CLICK_MIN_GAP','0'))   # s entre cliques; 0 = sem limite (padrao antigo)
def build(clip,out):
    dur=clip['total']+0.2
    buf=np.zeros(int(dur*SR),dtype=np.float32)
    last=-9.0; n=0
    for idx,c in enumerate(clip['caps']):
        if not c.get('any') or idx==0: continue  # never click over the opening hook word
        t=c['s']+0.03
        if MIN_GAP and t-last<MIN_GAP: continue   # sem rajada de cliques
        last=t; cl=VARS[n%len(VARS)]; n+=1
        i=int(t*SR)
        j=min(len(buf),i+len(cl))
        buf[i:j]+=cl[:j-i]
    st=np.stack([buf,buf],1)
    st=np.clip(st,-1,1)
    pcm=(st*32767).astype('<i2').tobytes()
    w=wave.open(out,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm); w.close()
if __name__=='__main__':
    P=json.load(open(os.path.join(B,'plan.json'))); k=sys.argv[1]
    build(P[k],os.path.join(B,'clicks_%s.wav'%k)); print('ok')
