import json,subprocess,sys,os
import numpy as np, soundfile as sf
W=sys.argv[1]; SR=48000
A='/Volumes/SSD/CIBO Acervo/sfx/_global/'
segs=json.load(open(f'{W}/segs.json'))
TAIL=0.8
# 1) voz: mesmos trechos do job, do áudio 48 kHz da câmera, fades de 6 ms nas emendas
f=''.join(f"[0:a]atrim={s:.4f}:{e:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.006,afade=t=out:st={e-s-0.006:.4f}:d=0.006[a{i}];" for i,(s,e) in enumerate(segs))
f+=''.join(f'[a{i}]' for i in range(len(segs)))+f"concat=n={len(segs)}:v=0:a=1,apad=pad_dur={TAIL},highpass=f=80,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=140:makeup=2[o]"
subprocess.run(['ffmpeg','-v','error','-y','-i',f'{W}/src_48k.wav','-filter_complex',f,'-map','[o]','-ac','1','-ar',str(SR),f'{W}/voz.wav'],check=True)
voz,_=sf.read(f'{W}/voz.wav')
# restos de sílaba do take anterior nas emendas (tempo editado): silencia com rampa de 15 ms
for a0,b0 in json.load(open(f'{W}/mute.json')) if os.path.exists(f'{W}/mute.json') else []:
    i0,i1=int(a0*SR),int(b0*SR); r=int(0.015*SR)
    voz[i0:i1]=0; voz[i1:i1+r]*=np.linspace(0,1,r)
sf.write(f'{W}/voz.wav',voz,SR)
N=len(voz); DUR=N/SR
# 2) trilha: fim natural da faixa no fim do reel (backtiming), entrada com fade curto
MUS=json.load(open(f'{W}/reel.json'))['music']; MUS=MUS if os.path.isabs(MUS) else '/Volumes/SSD/CIBO Acervo/musica/_global/'+MUS   # trilha alterna por reel
mdur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',MUS],capture_output=True,text=True).stdout)
off=max(0,mdur-DUR)
# music_level: nivela o volume da TRILHA no tempo (o trecho escolhido pode ter um começo 12 dB mais forte que o resto;
# João, 13/10/2026: "no começo a música ficou muito alta"). Só na trilha; a voz nunca passa por normalização dinâmica.
LVL=json.load(open(f'{W}/reel.json')).get('music_level',False)
PRE=min(4.0,off) if LVL else 0.0   # o nivelador começa antes (aquecimento) e a sobra é descartada
af=(f'dynaudnorm=f=250:g=15:p=0.9:m=8,atrim=start={PRE:.3f},asetpts=PTS-STARTPTS,' if LVL else '')+'afade=t=in:d=0.8'
subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{off-PRE:.3f}','-t',f'{DUR+PRE:.3f}','-i',MUS,'-af',af,'-ac','1','-ar',str(SR),f'{W}/musica_raw.wav'],check=True)
# 2b) music_env: ganho da trilha por tempo, [[t, dB], ...] interpolado (ajuste pontual pedido pelo editor, sem mexer no resto)
ENV=json.load(open(f'{W}/reel.json')).get('music_env')
if ENV:
    m,_=sf.read(f'{W}/musica_raw.wav'); tt=np.arange(len(m))/SR
    g=10**(np.interp(tt,[e[0] for e in ENV],[e[1] for e in ENV])/20); sf.write(f'{W}/musica_raw.wav',m*g,SR)
# 3) SFX: o pico de cada som cai no instante do evento
ev=json.load(open(f'{W}/sfx.json'))
sfx=np.zeros(N)
for e in ev:
    # caminho absoluto = SFX do cliente (ex.: clique do João)
    x,sr=sf.read(e['f'] if os.path.isabs(e['f']) else A+e['f']+'.wav'); x=x.mean(1) if x.ndim>1 else x
    if sr!=SR: x=np.interp(np.arange(0,len(x),sr/SR),np.arange(len(x)),x)
    pk=int(np.argmax(np.abs(x)))
    st=int(e['t']*SR)-pk
    g=10**(e['db']/20); a=max(st,0); b=min(st+len(x),N)
    sfx[a:b]+=x[a-st:b-st]*g
sf.write(f'{W}/sfx.wav',sfx,SR)
# 4) mix: música com ducking pela voz, voz + SFX, normaliza para -14 LUFS / -1 dBTP
MDB=json.load(open(f'{W}/reel.json')).get('music_db',-6.5)   # ganho da trilha antes do ducking (João: bem mais baixo, 13/10/2026)
mixf=(f"[1:a]volume={MDB}dB[m];"
      "[0:a]asplit=2[v][vk];[m][vk]sidechaincompress=threshold=0.04:ratio=3:attack=30:release=400[md];"
      "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 1[mx]")
subprocess.run(['ffmpeg','-v','error','-y','-i',f'{W}/voz.wav','-i',f'{W}/musica_raw.wav','-i',f'{W}/sfx.wav','-filter_complex',mixf,'-map','[mx]','-ar',str(SR),f'{W}/mix_pre.wav'],check=True)
r=subprocess.run(['ffmpeg','-i',f'{W}/mix_pre.wav','-af','loudnorm=I=-13:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
j=json.loads(r[r.rfind('{'):r.rfind('}')+1])
g=-13.6-float(j['input_i'])
subprocess.run(['ffmpeg','-v','error','-y','-i',f'{W}/mix_pre.wav','-af',f'volume={g:.2f}dB,aresample=192000,alimiter=limit=0.85:attack=2:release=60:level=false,aresample=48000','-ar',str(SR),f'{W}/mix.wav'],check=True)
# faixas separadas para o editável: música já com o ducking, no mesmo ganho do mix
subprocess.run(['ffmpeg','-v','error','-y','-i',f'{W}/voz.wav','-i',f'{W}/musica_raw.wav','-filter_complex',f"[1:a]volume={MDB}dB[m];[m][0:a]sidechaincompress=threshold=0.04:ratio=3:attack=30:release=400[o]",'-map','[o]',f'{W}/musica.wav'],check=True)
print(f'dur {DUR:.2f}s, offset trilha {off:.2f}s, {len(ev)} SFX')

# voz x trilha: diferença de loudness (meta: trilha 16–20 dB abaixo da voz)
def lufs(f):
    r=subprocess.run(['ffmpeg','-i',f,'-af','ebur128','-f','null','-'],capture_output=True,text=True).stderr
    return float(r[r.rfind('I:'):].split()[1])
lv,lm=lufs(f'{W}/voz.wav'),lufs(f'{W}/musica.wav')
print(f'voz {lv:.1f} LUFS, trilha {lm:.1f} LUFS, diferença {lv-lm:.1f} dB')
