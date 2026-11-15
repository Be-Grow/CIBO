#!/usr/bin/env python3
"""Teste de fumaça do Resolve + Fusion pela API (reel-motion/scripts/fusion_kit.py), ~30 s, com o Resolve aberto.
Cria "CIBO testes/TESTE fusion_kit", monta 2 clipes (um aparado), aplica zoom com motion blur nos dois, entrada/saída num
terceiro, confere as curvas lidas de volta e o comp gravado, apaga o projeto e devolve o que estava aberto.
Rode depois de mexer em qualquer script que fala com o Resolve:  python3 ~/CIBO/tests/fusion_kit_teste.py"""
import subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / '.claude/skills/reel-motion/scripts'))
import fusion_kit as K
T = Path('/Volumes/SSD/CIBO/tmp/fusion_kit_teste'); T.mkdir(parents=True, exist_ok=True); V = T / 'teste_cam.mp4'
if not V.exists():
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=1080x1920:rate=30000/1001:duration=6', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(V)], check=True)
K.limite(240)
r, pm, p = K.resolve(); antes = p.GetName() if p else None
assert not antes or antes.startswith('Untitled Project') or antes == 'TESTE fusion_kit', f'feche o projeto "{antes}" antes do teste (não mexo em projeto do editor)'
p, novo = K.abre_projeto(pm, 'CIBO testes', 'TESTE fusion_kit')
for k, v in dict(timelineResolutionWidth='1080', timelineResolutionHeight='1920', timelineFrameRate='29.97').items(): p.SetSetting(k, v)
mp = p.GetMediaPool()
if K.timelines(p): mp.DeleteTimelines(K.timelines(p))
cl = mp.ImportMedia([str(V)])[0]; tl = mp.CreateEmptyTimeline('TESTE'); tl.SetTrackName('video', 1, 'CÂMERA bruto'); s0 = tl.GetStartFrame()
for ini, rec in ((0, 0), (60, 90), (0, 180)):
    assert mp.AppendToTimeline([{'mediaPoolItem': cl, 'startFrame': ini, 'endFrame': ini + 90, 'trackIndex': 1, 'recordFrame': s0 + rec, 'mediaType': 1}])
a, b, c = K.itens(tl, 'CÂMERA bruto'); ok = []
ok.append(K.zoom(a, [(15, 1.0), (30, 1.10), (51, 1.10), (75, 1.0)], T / 'comps/a.comp') == [1.0, 1.1, 1.1, 1.0])
ok.append(K.zoom(b, [(15, 1.0), (30, 1.12), (74, 1.12), (75, 1.0)], T / 'comps/b.comp') == [1.0, 1.12, 1.12, 1.0])     # clipe aparado
K.entra_sai(c, T / 'comps/c.comp'); ok.append(c.GetFusionCompCount() == 1)
txt = (T / 'comps/a.comp').read_text()
ok.append('ShutterAngle = Input { Value = 360' in txt and 'MotionBlur = Input { Value = 1' in txt)
ok.append(all(i.GetFusionCompCount() == 1 for i in (a, b, c)))
pm.SaveProject(); pm.CloseProject(p); pm.GotoRootFolder(); pm.OpenFolder('CIBO testes'); apagou = pm.DeleteProject('TESTE fusion_kit')
print('zoom clipe inteiro, zoom clipe aparado, entra/sai, shutter 360 gravado, 1 comp por clipe:', ok, '| projeto de teste apagado:', apagou)
sys.exit(0 if all(ok) else 1)
