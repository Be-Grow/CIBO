#!/usr/bin/env python3
"""QA do MP4 entregue (Andrea, 20/10/2026): sincronia por trecho do bruto (áudio do render × áudio da câmera no mesmo
quadro; atraso em ms e correlação: bom = |atraso| < 40 ms e corr > 0,9; 0,26 foi a voz de outro vídeo), tela vermelha de
Media Offline e quadros pretos. Trechos lidos do timeline.fcpxml do pacote; bruto em 01_sources/_2997/vNN*.mov.
uso: ~/.claude/skills/content-hub/.venv/bin/python3 qa_render.py PROJETO"""
import subprocess,numpy as np,re,glob,os,unicodedata
import sys; P=sys.argv[1].rstrip('/')+'/'; nfc=lambda x: unicodedata.normalize('NFC',x)
def au(f,ss=0,d=None):
    c=['ffmpeg','-v','error','-ss',str(ss)]+(['-t',str(d)] if d else [])+['-i',f,'-ac','1','-ar','8000','-f','f32le','-']
    a=np.frombuffer(subprocess.run(c,capture_output=True).stdout,np.float32); e=np.abs(a)[:len(a)//40*40].reshape(-1,40).mean(1); return (e-e.mean())/(e.std()+1e-9)
fr=lambda s: eval(s[:-1]) if s!='0s' else 0
for f in sorted(glob.glob(P+'06_deliverables/*.mp4')):
    n=nfc(os.path.basename(f)[:-4]); x=open(P+'07_davinci/'+n+'/timeline.fcpxml',encoding='utf-8').read() if os.path.exists(P+'07_davinci/'+n) else open(next(P+'07_davinci/'+d for d in os.listdir(P+'07_davinci') if nfc(d)==n)+'/timeline.fcpxml',encoding='utf-8').read()
    mov=glob.glob(P+'01_sources/_2997/v'+n[:2]+'*.mov')[0]; res=[]
    for o,s,d in re.findall(r'<asset-clip[^>]*offset="([^"]*)" start="([^"]*)" duration="([^"]*)"[^>]*name="bruto',x):
        o,s,d=fr(o),fr(s),fr(d); w=min(d-0.6,6)
        if w<1.5: continue
        t0=o+d-w-0.3; r=au(f,t0,w); c=au(mov,s+(t0-o),w); m=min(len(r),len(c))
        cc=np.correlate(r[:m],c[:m],'full'); res.append(f'{o:.0f}s:{(cc.argmax()-(m-1))*5:+d}ms/{cc.max()/m:.2f}')
    raw=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf','fps=2,scale=64:36','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    a=np.frombuffer(raw,np.uint8).reshape(-1,36,64,3).astype(int); red=((a[...,0]>150)&(a[...,1]<60)&(a[...,2]<60)).mean(axis=(1,2))
    pret=(a.max(axis=3)<12).mean(axis=(1,2))
    print(n[:44], ' '.join(res), '| offline:', list(np.where(red>0.4)[0]/2)[:3], '| preto (s):', list(np.where(pret>0.95)[0]/2)[:4])
