#!/usr/bin/env python3
"""Mede como o Resolve interpreta position/scale do FCPXML do reel-motion (conform none) para fontes de tamanhos diferentes
numa timeline 1080x1920. Cada fonte tem um quadrado vermelho e um verde em posições conhecidas; o teste importa o XML num
projeto de teste, lê Pan/Tilt/Zoom pela API, RENDERIZA (still do Resolve vem do cache e mente) e mede onde os quadrados caíram.
uso: resolve_transform_teste.py [--corr]   (--corr aplica a correção do motor: davinci.corrige_resolve)
Saída por fonte: escala pedida × escala vista, deslocamento pedido × visto (px da timeline)."""
import subprocess, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path.home() / '.claude/skills/reel-motion/scripts'))
import fusion_kit as K
T = Path('/Volumes/SSD/CIBO/tmp/transf_teste'); T.mkdir(parents=True, exist_ok=True)
VW, VH = (1920, 1080) if '--h' in sys.argv else (1080, 1920); N = 30
ROT = -90 if '--rot' in sys.argv else 0
FONTES = [(1920, 1080), (3840, 2160)] if ROT else [(1920, 1080), (1280, 720), (3840, 2160), (1080, 1920), (2160, 3840)]
CASOS = [(0.0, 0.0), (5.0, 0.0), (0.0, 4.0)]                       # posição x, y em % da altura (como o motor grava)
CORR = '--corr' in sys.argv
tt = lambda n: f'{n * 1001}/30000s'


def fonte(w, h):
    f = T / f'src_{w}x{h}.mp4'
    if not f.exists():
        q = max(24, w // 40); ax, bx, cy = int(w * 0.4), int(w * 0.6), h // 2
        vf = f'drawbox=x={ax - q // 2}:y={cy - q // 2}:w={q}:h={q}:color=red:t=fill,drawbox=x={bx - q // 2}:y={cy - q // 2}:w={q}:h={q}:color=lime:t=fill'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=black:s={w}x{h}:r=30000/1001:d=4', '-vf', vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '12', str(f)], check=True)
    return f


def corrige(w, h, x, y, s):
    if not CORR: return x, y, s
    import importlib.util
    sp = importlib.util.spec_from_file_location('rc', Path.home() / '.claude/skills/reel-motion/scripts/resolve_conforma.py'); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m.corrige(w, h, VW, VH, x, y, s, ROT)


plano, assets, clips, off = [], [], [], 0
for i, (w, h) in enumerate(FONTES):
    f = fonte(w, h); s = round((300 if VW > VH or ROT else 400) / (0.2 * w), 5)                 # quadrados a 400 px um do outro se 1 px fonte = 1 px timeline
    assets.append(f'<asset id="a{i + 1}" name="{f.name}" start="0s" duration="{tt(120)}" hasVideo="1" hasAudio="0" format="r1">\n  <media-rep kind="original-media" src="{f.as_uri()}"/>\n</asset>')
    for (px, py) in CASOS:
        x, y, sx = corrige(w, h, px, py, s)
        clips.append(f'<asset-clip ref="a{i + 1}" lane="1" offset="{tt(off)}" start="{tt(10)}" duration="{tt(N)}" srcEnable="video" name="t{len(plano)}"><adjust-conform type="none"/><adjust-transform position="{x:.4f} {y:.4f}" scale="{sx:.5f} {sx:.5f}" rotation="{ROT}"/></asset-clip>')
        plano.append(dict(w=w, h=h, px=px, py=py, s=s, off=off)); off += N
xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
<resources>
<format id="r1" name="FFVideoFormat{VW}x{VH}p2997" frameDuration="1001/30000s" width="{VW}" height="{VH}" colorSpace="1-1-1 (Rec. 709)"/>
{chr(10).join(assets)}
</resources>
<library><event name="TRANSF"><project name="TRANSF">
<sequence format="r1" duration="{tt(off)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
<spine>
<gap name="reel" offset="0s" start="0s" duration="{tt(off)}">
{chr(10).join(clips)}
</gap>
</spine>
</sequence></project></event></library>
</fcpxml>
'''
(T / 'transf.fcpxml').write_text(xml)
K.limite(420)
print('timeline', VW, 'x', VH, '| rotação', ROT, '| correção', CORR)
r, pm, p = K.resolve(); antes = p.GetName() if p else None
assert not antes or antes.startswith('Untitled Project') or antes == 'TESTE transform', f'feche o projeto "{antes}" antes do teste'
p, novo = K.abre_projeto(pm, 'CIBO testes', 'TESTE transform')
for k, v in dict(timelineResolutionWidth=str(VW), timelineResolutionHeight=str(VH), timelineFrameRate='29.97').items(): p.SetSetting(k, v)
mp = p.GetMediaPool()
if K.timelines(p): mp.DeleteTimelines(K.timelines(p))
tl = mp.ImportTimelineFromFile(str(T / 'transf.fcpxml'), {'timelineName': 'TRANSF'}); assert tl, 'importação falhou'
p.SetCurrentTimeline(tl)
its = [i for k in range(1, tl.GetTrackCount('video') + 1) for i in (tl.GetItemListInTrack('video', k) or [])]
its.sort(key=lambda i: i.GetStart()); lidos = [{q: i.GetProperty(q) for q in ('Pan', 'Tilt', 'ZoomX')} for i in its]
out = T / 'render'; out.mkdir(exist_ok=True); nome = f'transf_{time.strftime("%H%M%S")}'
p.DeleteAllRenderJobs(); assert p.LoadRenderPreset('H.264 Master')
assert p.SetRenderSettings({'TargetDir': str(out), 'CustomName': nome, 'SelectAllFrames': True, 'ExportVideo': True, 'ExportAudio': False}), 'SetRenderSettings'
j = p.AddRenderJob(); assert j; p.StartRendering([j])
while p.IsRenderingInProgress(): time.sleep(1)
st = p.GetRenderJobStatus(j); assert st.get('JobStatus') == 'Complete', st
mp4 = next(out.glob(nome + '*'))
print(f'{"fonte":>10} {"pos%":>9} | {"Pan":>8} {"Tilt":>8} {"Zoom":>6} | escala pedida→vista | desloc. pedido→visto (px)')
pior = 0
for c, lido in zip(plano, lidos):
    t = (c['off'] + N // 2) * 1001 / 30000
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', str(mp4), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    im = np.frombuffer(raw, np.uint8).reshape(VH, VW, 3).astype(int)
    def cen(m):
        ys, xs = np.nonzero(m); return (xs.mean(), ys.mean()) if len(xs) > 20 else None
    A = cen((im[..., 0] > 150) & (im[..., 1] < 90)); B = cen((im[..., 1] > 150) & (im[..., 0] < 90))
    quer = (c['px'] * VH / 100, -c['py'] * VH / 100)
    if A and B:
        esc = float(np.hypot(B[0] - A[0], B[1] - A[1])) / (0.2 * c['w']); dx = (A[0] + B[0]) / 2 - VW / 2; dy = (A[1] + B[1]) / 2 - VH / 2
        pior = max(pior, abs(esc / c['s'] - 1) * 100, abs(dx - quer[0]), abs(dy - quer[1]))
        vis = f'{c["s"]:.3f}→{esc:.3f} (×{esc / c["s"]:.3f}) | ({quer[0]:+.0f},{quer[1]:+.0f})→({dx:+.0f},{dy:+.0f})'
    else:
        vis = 'quadrados fora do quadro'; pior = 999
    print(f'{c["w"]:>5}x{c["h"]:<4} {c["px"]:>4.0f},{c["py"]:<4.0f} | {lido["Pan"]:>8.2f} {lido["Tilt"]:>8.2f} {lido["ZoomX"]:>6.3f} | {vis}')
pm.SaveProject(); pm.CloseProject(p); pm.GotoRootFolder(); pm.OpenFolder('CIBO testes'); pm.DeleteProject('TESTE transform')
print('pior erro:', round(pior, 1), '(px ou %)', '| OK' if pior < 3 else '| FORA')
sys.exit(0 if pior < 3 else 1)
