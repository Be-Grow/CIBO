# -*- coding: utf-8 -*-
import os
import json,sys,os,math,subprocess
import numpy as np
from PIL import Image, ImageFilter

B=os.environ.get('WORK','.'); SRCDIR=os.environ.get('SRCDIR','.')
FPS=30
# FORMAT=16x9: versao horizontal (YouTube) do mesmo corte, quadro inteiro sem recorte.
HORIZ=os.environ.get('FORMAT','9x16')=='16x9'
W,H=(1920,1080) if HORIZ else (1080,1920)
# Burn tambem na saida. Desligado por padrao: esta skill e o motor de varios
# clientes e ligar mudaria a entrega de quem nao pediu. BURN_OUT=0.63 coloca o
# pico do asset (que estoura em 0,53s) encostado no ultimo quadro.
BURN_OUT=float(os.environ.get('BURN_OUT','0'))
INTRO=0.90; Z0=1.26; BLUR0=18.0

def sh(cmd):
    r=subprocess.run(cmd,shell=True,capture_output=True,text=True)
    if r.returncode: print(r.stderr[-3000:]); raise SystemExit(1)
    return r.stdout

ZOOM=float(os.environ.get('ZOOM_AMT','0.055'))   # 0 disables
# VENC=videotoolbox (opt-in): codifica na GPU do Mac. Aprovado no M4 pela skill
# video-render-optimizer (12/10/2026): 4,2x mais rapido, SSIM 0,9941 x 0,9952 do x264 slow
# crf18, 6,9 Mb/s. Hardware precisa de alvo e teto de bitrate, nao CRF: VT_MBPS/VT_MAX_MBPS.
VENC=os.environ.get('VENC','x264')
if VENC=='auto':
    # VENC=auto: a skill video-render-optimizer (hw_profile.py) detecta o hardware, escolhe o
    # encoder por benchmark e revalida de tempos em tempos. Sem ela ou com erro: x264.
    _hp=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','video-render-optimizer','scripts','hw_profile.py')
    try:
        _p=json.loads(subprocess.run([sys.executable,_hp,'env','--json'],capture_output=True,text=True,timeout=900).stdout)
        VENC=_p['VENC']
        for _k in ('VT_MBPS','VT_MAX_MBPS'): os.environ.setdefault(_k,_p[_k])
    except Exception as _e:
        print('VENC=auto: perfil de hardware indisponivel, usando x264:',_e); VENC='x264'
    os.environ['VENC']=VENC          # o make_reels usa o valor resolvido na chave de cache
_HW={'videotoolbox':('h264_videotoolbox',['-realtime','false']),'nvenc':('h264_nvenc',['-preset','p5','-rc','vbr']),
     'qsv':('h264_qsv',['-preset','medium']),'amf':('h264_amf',['-quality','balanced'])}
def venc_final(preset,crf):
    if VENC in _HW:
        b=float(os.environ.get('VT_MBPS','8')); m=float(os.environ.get('VT_MAX_MBPS','10')); n,x=_HW[VENC]
        return f'-c:v {n} -b:v {b:g}M -maxrate {m:g}M -bufsize {2*m:g}M {" ".join(x)} -profile:v high'
    return f'-c:v libx264 -preset {preset} -crf {crf}'
def venc_mid(preset,crf):
    """Intermediarios (passA, intro): na GPU com bitrate alto, ja que serao recodificados."""
    if VENC in _HW:
        n,x=_HW[VENC]; return ['-c:v',n,'-b:v','40M',*x,'-profile:v','high']
    return ['-c:v','libx264','-preset',preset,'-crf',crf]
# PASSA_DIRECT=1 (opt-in, so com ZOOM_AMT=0): o ffmpeg ja entrega o quadro em W x H e o
# Python so repassa os bytes. Sem zoom, o resize por quadro no PIL era tempo perdido.
PASSA_DIRECT=os.environ.get('PASSA_DIRECT')=='1' and ZOOM==0
def ease_quad(p): return 2*p*p if p<0.5 else 1-((-2*p+2)**2)/2

def passA(c,out):
    """Cut+crop+ken-burns. The zoom used to be done with ffmpeg's `zoompan`, which has a
    well-known bug: fed a continuously-changing video (not a still), it silently duplicates
    every other output frame, producing a regular judder that reads as shake. Fixed by doing
    the animated crop/zoom frame-by-frame in Python (PIL), the same technique make_intro()
    already used successfully - ffmpeg only decodes/encodes, no zoompan involved."""
    keeps=c['keeps']; n=len(keeps)
    # oversample relative to the FINAL output size (not the native crop size) so the zoom
    # only ever crops+lightly-downscales from an already-adequate source instead of upscaling.
    OS=int(H*(1+ZOOM+0.02)); OSW=int(W*(1+ZOOM+0.02))//2*2
    if PASSA_DIRECT: OS,OSW=H,W
    # `crop_h` (opt-in): recorte mais baixo que 1080, ancorado no topo, para deixar de fora
    # uma marca queimada no rodape do bruto (logo da transmissao). Largura = crop_h*9/16.
    ch=int(c.get('crop_h',1080))
    cw=1920 if HORIZ else (608 if ch==1080 else int(round(ch*9/16))//2*2)
    x=int((1920-cw)*c['cropx']); x=max(0,min(1920-cw,x))
    # Reenquadramento por plano de camera. Uma gravacao que alterna close e plano
    # aberto nao pode usar um recorte fixo: no plano aberto o corte fixo aponta
    # para o meio da mesa. `cropx_timeline` e uma lista [[tempo_no_fonte, cropx]]
    # e so pode mudar onde a camera corta de verdade — mudar o recorte numa
    # emenda dentro do mesmo plano faz a imagem deslizar de lado na tela.
    timeline=sorted((float(t),float(v)) for t,v in c.get('cropx_timeline',[]))
    def crop_expr(a,b):
        if HORIZ or not timeline: return str(x)
        if c.get('cropx_interp'):
            # Camera unica com a pessoa andando no palco (palestra em plano aberto): o
            # recorte acompanha por interpolacao linear entre os pontos da timeline, sem
            # degrau. Opt-in por clipe; o padrao continua sendo degrau por plano de camera.
            # tolerancia de 0,45 s: o snap de silencio move a borda do keep para dentro e
            # deixava os pontos do proprio trecho de fora -- o recorte caia no `cropx` do
            # primeiro trecho e a pessoa saia do quadro.
            pts=[(t-a,v) for t,v in timeline if a-0.45<=t<=b+0.45]
            if not pts:
                tn,vn=min(timeline,key=lambda p:min(abs(p[0]-a),abs(p[0]-b))); pts=[(0.0,vn)]
            expr=f'{pts[-1][1]:.5f}'
            for (t0,v0),(t1,v1) in reversed(list(zip(pts,pts[1:]))):
                expr=f'if(lt(t,{t1:.4f}),{v0:.5f}+({v1-v0:.5f})*(t-{t0:.4f})/{max(t1-t0,1e-3):.4f},{expr})'
            return f"'(iw-{cw})*clip({expr},0,1)'"
        # O decoder entra com -ss a + setpts=PTS-STARTPTS: t=0 e o primeiro quadro REAL
        # depois de `a` (ceil(a*fps)/fps), nao `a`. Sem descontar esse deslocamento a troca
        # de recorte saia 1 quadro atrasada: um quadro da camera nova com o recorte antigo
        # (LPA e Voce, 12/10/2026). Fonte CFR com quadros em k/fps.
        off=math.ceil(a*FPS-1e-6)/FPS-a
        atual=float(c['cropx']); mudancas=[]
        for t,v in timeline:
            if t<=a+1e-6: atual=v
            elif t<b-1e-6: mudancas.append((t-a-off,v))
        vals=[atual]+[v for _,v in mudancas]
        expr=f'{vals[-1]:.5f}'
        for j in range(len(mudancas)-1,-1,-1):
            expr=f'if(lt(t,{mudancas[j][0]:.5f}),{vals[j]:.5f},{expr})'
        return f"'(iw-{cw})*({expr})'"
    src=f'{SRCDIR}/{c["src"]}'
    base=1+ZOOM+0.02
    fsz=OSW*OS*3

    afc=[]
    for i,(a,b) in enumerate(keeps):
        afc.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
                    f"afade=t=in:st=0:d=0.035,afade=t=out:st={round(b-a-0.055,3)}:d=0.055[a{i}]")
    afc.append(''.join(f"[a{i}]" for i in range(n))+f"concat=n={n}:v=0:a=1[ac]")
    afc.append("[ac]aresample=48000,asetpts=N/SR/TB[ao]")
    audio_out=out+'.audio.m4a'
    sh(f'ffmpeg -y -v error -i "{src}" -filter_complex "{";".join(afc)}" -map "[ao]" '
       f'-c:a aac -b:a 192k "{audio_out}"')

    video_out=out+'.video.mp4'
    enc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an',*venc_mid('ultrafast','14'),
        '-pix_fmt','yuv420p',video_out],stdin=subprocess.PIPE)
    for i,(a,b) in enumerate(keeps):
        zin=(i%2==0)                      # alternate push-in / pull-out per beat
        zA,zB=(1.0,1.0+ZOOM) if zin else (1.0+ZOOM,1.0)
        nframes=max(1,round((b-a)*FPS))
        # -ss na entrada: antes o trim decodificava o arquivo desde o inicio para cada keep
        # (custo quadratico; 35 keeps numa janela de 9 min levaram 18 min).
        dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{a:.3f}','-i',src,'-filter_complex',
            f'[0:v]trim=duration={b-a:.3f},setpts=PTS-STARTPTS,crop={cw}:{1080 if HORIZ else ch}:x={crop_expr(a,b)}:y=0,'
            f'scale={OSW}:{OS}:flags=lanczos,format=rgb24[v]','-map','[v]','-f','rawvideo','-'],
            stdout=subprocess.PIPE)
        for k in range(nframes):
            buf=dec.stdout.read(fsz)
            if len(buf)<fsz: break
            if PASSA_DIRECT:
                enc.stdin.write(buf); continue
            im=Image.frombytes('RGB',(OSW,OS),buf)
            if ZOOM>0:
                p=k/max(1,nframes-1)
                e=ease_quad(p)
                z=base/(zA+(zB-zA)*e)
                cw2,ch2=OSW/z,OS/z
                x0=(OSW-cw2)/2; y0=(OS-ch2)/2
                im=im.crop((x0,y0,x0+cw2,y0+ch2)).resize((W,H),Image.LANCZOS)
            else:
                im=im.resize((W,H),Image.LANCZOS)
            enc.stdin.write(im.tobytes())
        dec.stdout.close(); dec.wait()
    enc.stdin.close(); enc.wait()
    sh(f'ffmpeg -y -v error -i "{video_out}" -i "{audio_out}" -map 0:v -map 1:a '
       f'-c:v copy -c:a copy -shortest "{out}"')
    os.remove(video_out); os.remove(audio_out)

def ease_io(p): return 4*p*p*p if p<0.5 else 1-((-2*p+2)**3)/2

def make_intro(passa,out):
    n=int(round(INTRO*FPS))
    raw=subprocess.run(f'ffmpeg -v error -i "{passa}" -frames:v {n} -f rawvideo -pix_fmt rgb24 -',
                       shell=True,capture_output=True).stdout
    fs=W*H*3
    p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an',*venc_mid('veryfast','16'),
        '-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for i in range(n):
        im=Image.frombytes('RGB',(W,H),raw[i*fs:(i+1)*fs])
        e=ease_io(i/(n-1))
        z=Z0-(Z0-1.0)*e
        bl=BLUR0*(1-e)**1.4
        cw,ch=int(W/z),int(H/z)
        im=im.crop(((W-cw)//2,(H-ch)//2,(W-cw)//2+cw,(H-ch)//2+ch)).resize((W,H),Image.LANCZOS)
        if bl>0.3: im=im.filter(ImageFilter.GaussianBlur(bl))
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()

def final(c,passa,intro,out,cover=None,preset='veryfast',crf=21,extra=''):
    """One single encode: cover + burn + captions + click + music mix -> deliverable."""
    k=c['name']
    fb=os.environ['FILMBURN']; cr=f'{B}/caps_{k}_rgb.mp4'; ca=f'{B}/caps_{k}_a.mp4'
    clk=f'{B}/clicks_{k}.wav'
    music=c.get('music'); mix=c.get('mix',{})
    ins=(f'-i "{passa}" -i "{intro}" -i "{fb}" -i "{cr}" -i "{ca}" -i "{clk}"')
    # loop limitado a duracao do clipe: com -stream_loop -1 sem -t a entrada nunca termina
    # e o encode chega ao fim do video mas trava sem fechar o arquivo (0% de CPU).
    if music: ins+=f' -stream_loop -1 -t {float(c["total"])+float(c.get("mix",{}).get("music_offset",0))+2:.2f} -i "{music}"'
    # `burn_at`: burns extras no meio do clipe (segundos no clipe, sem contar a capa),
    # com o pico do asset (0,53 s) sobre a emenda: transicao entre blocos de assunto.
    mids=[float(t) for t in c.get('burn_at',[])]
    # O audio do passA entra por uma segunda leitura do arquivo, no fim da lista. Com
    # [0:v] e [0:a] no mesmo demuxer, a fila do audio enchia esperando o mix e o video
    # parava junto: encode travado com 0% de CPU por volta de 2 min (clipes longos).
    aidx=6+bool(music)+bool(cover)
    f=(f"[0:v]trim=start={INTRO},setpts=PTS-STARTPTS[main];"
       f"[1:v][main]concat=n=2:v=1:a=0[vv];"
       f"[2:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=gbrp,split={2+len(mids)}[fbA][fbB]{''.join(f'[fbM{j}]' for j in range(len(mids)))};"
       f"[fbA]tpad=stop_mode=add:stop_duration={float(c["total"])+5:.1f}:color=black[fb1];"
       f"[fbB]tpad=start_mode=add:start_duration={max(float(c['total'])-BURN_OUT,0):.3f}:color=black,"
       f"tpad=stop_mode=add:stop_duration={float(c["total"])+5:.1f}:color=black[fb2];"
       f"[vv]format=gbrp[vvg];"
       f"[vvg][fb1]blend=all_mode=screen:shortest=1[vb1];"
       f"[vb1][fb2]blend=all_mode=screen:shortest=1[vm0];"
       +''.join(f"[fbM{j}]tpad=start_mode=add:start_duration={max(t-0.53,0):.3f}:color=black,"
                f"tpad=stop_mode=add:stop_duration={float(c["total"])+5:.1f}:color=black[fbm{j}];"
                f"[vm{j}][fbm{j}]blend=all_mode=screen:shortest=1[vm{j+1}];" for j,t in enumerate(mids))
       +f"[vm{len(mids)}]format=yuv420p[vb];"
       f"[3:v]format=yuva420p[c3];[c3][4:v]alphamerge[capa];"
       f"[vb][capa]overlay=x={(W-1080)//2}:y={os.environ.get('BAND_Y',810)}:format=auto:eof_action=pass,setsar=1[body];"
       f"[{aidx}:a][5:a]amix=inputs=2:duration=first:normalize=0"
       # `voice_af`: cadeia de audio da voz por clipe (ganho fixo, EQ, limitador de pico).
       f"{(','+c['voice_af']) if c.get('voice_af') else ''}[voice]")
    if music:
        music_db=float(mix.get('music_db',-26))
        music_offset=max(0.0,float(mix.get('music_offset',0)))
        music_fade_out=max(0.0,float(c['total'])-0.8)
        duck_threshold=float(mix.get('duck_threshold',0.08))
        duck_ratio=float(mix.get('duck_ratio',6))
        f+=(f";[6:a]atrim=start={music_offset:.3f},asetpts=PTS-STARTPTS,"
            f"volume={music_db:g}dB,afade=t=in:d=0.8,afade=t=out:st={music_fade_out:.3f}:d=0.8[music];"
            # [voice] e consumido duas vezes: sem asplit, o ffmpeg ligava o segundo uso ao
            # primeiro audio de entrada livre (o audio cru do passA) e o mix final saia sem
            # cliques e sem `voice_af`, em silencio.
            f"[voice]asplit=2[vsc][vmix];"
            f"[music][vsc]sidechaincompress=threshold={duck_threshold:.3f}:ratio={duck_ratio:g}:attack=12:release=420[duck];"
            f"[vmix][duck]amix=inputs=2:duration=first:normalize=0[abody]")
    else:
        f+=";[voice]anull[abody]"
    if cover:
        cd=1.0/FPS  # Instagram only needs one frame to grab a thumbnail from
        cover_idx=7 if music else 6
        ins+=f' -loop 1 -t {cd} -i "{cover}"'
        f+=(f";[{cover_idx}:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[cv];"
            f"[cv][body]concat=n=2:v=1:a=0[vfin];"
            f"anullsrc=r=48000:cl=stereo,atrim=0:{cd},asetpts=N/SR/TB[sil];"
            f"[sil][abody]concat=n=2:v=0:a=1[afin]")
    else:
        f+=";[body]null[vfin];[abody]anull[afin]"
    ins+=f' -i "{passa}"'
    nin=aidx+1; vl,al='vfin','afin'; tail=''
    # `overlays` (opt-in, por clipe): grafismos com alpha (ProRes 4444 do Remotion) na mesma
    # codificacao, em vez de recodificar o MP4 entregue. [{"file","t"(s no arquivo entregue),
    # "sfx":{"file","at"(s no arquivo entregue),"trim":[a,b],"gain"}}]
    for j,o in enumerate(c.get('overlays',[])):
        ins+=f' -i "{o["file"]}"'
        f+=(f";[{nin}:v]setpts=PTS+{float(o['t']):.3f}/TB[ov{j}];"
            f"[{vl}][ov{j}]overlay=0:0:eof_action=pass:format=auto[vov{j}]"); vl=f'vov{j}'; nin+=1
        if o.get('sfx'):
            x=o['sfx']; a,b=x.get('trim',[0,10])
            ins+=f' -i "{x["file"]}"'
            f+=(f";[{nin}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,volume={float(x.get('gain',1)):g},"
                f"adelay={int(float(x['at'])*1000)}:all=1[sx{j}];"
                f"[{al}][sx{j}]amix=inputs=2:duration=first:normalize=0[aov{j}]"); al=f'aov{j}'; nin+=1
    # BURN_END_INLINE=1 (opt-in): o mesmo fim do `burn_end.py` (video acaba seco, pico do burn
    # no ultimo quadro, resto sobre preto, cauda do audio em fade) sem uma segunda codificacao.
    if os.environ.get('BURN_END_INLINE')=='1':
        D=float(subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=duration',
                                '-of','csv=p=0',passa],capture_output=True,text=True).stdout)+(1.0/FPS if cover else 0)
        st,tot=D-0.53,D-0.53+1.4
        ins+=f' -i "{fb}" -f lavfi -i color=black:s={W}x{H}:r={FPS}:d=2.5'
        f+=(f";[{nin}:v]fps={FPS},scale={W}:{H},format=yuv420p,setsar=1[eb0];[{nin+1}:v]format=yuv420p,setsar=1[eb1];"
            f"[eb0][eb1]concat=n=2:v=1:a=0,format=gbrp,tpad=start_mode=add:start_duration={st:.3f}:color=black[ebt];"
            f"[{vl}]tpad=stop_mode=add:stop_duration={tot-D+0.1:.3f}:color=black,format=gbrp[ev];"
            f"[ev][ebt]blend=all_mode=screen:shortest=1,format=yuv420p[vend];"
            f"[{al}]apad=pad_dur={tot-D+0.1:.3f},afade=t=out:st={D-0.05:.3f}:d={tot-D+0.05:.3f}"
            +(f",alimiter=limit={os.environ['BURN_END_LIMIT']}:level=false" if os.environ.get('BURN_END_LIMIT') else '')
            +"[aend]"); vl,al='vend','aend'; nin+=2
        tail=f'-t {tot:.3f} '
        if os.environ.get('BURN_END_BT709'):
            tail+=('-color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 '
                   '-bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0 ')
    cmd=lambda v: (f'ffmpeg -y -v error {ins} -filter_complex "{f}" -map "[{vl}]" -map "[{al}]" '
                   f'{v} -pix_fmt yuv420p -c:a aac -b:a 160k '
                   f'{tail}{extra} -movflags +faststart "{out}"')
    try:
        sh(cmd(venc_final(preset,crf)))
    except SystemExit:
        if VENC not in _HW: raise
        # encoder de hardware falhou nesta maquina/sessao (ex.: sem acesso a GPU): refaz em CPU
        print(f'AVISO: {VENC} falhou no final, refazendo em libx264'); sh(cmd(f'-c:v libx264 -preset {preset} -crf {crf}'))

if __name__=='__main__':
    P=json.load(open(os.path.join(B,'plan.json'))); k=sys.argv[1]; c=P[k]
    passA(c,f'{B}/A_{k}.mp4'); print('passA ok')
    make_intro(f'{B}/A_{k}.mp4',f'{B}/I_{k}.mp4'); print('intro ok')
    final(c,f'{B}/A_{k}.mp4',f'{B}/I_{k}.mp4',f'{B}/{k}_vertical.mp4'); print('final ok')
