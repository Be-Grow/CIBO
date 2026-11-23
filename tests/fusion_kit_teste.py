#!/usr/bin/env python3
"""Teste de fumaça do Resolve + Fusion pela API (reel-motion/scripts/fusion_kit.py), ~30 s, com o Resolve aberto.
Cria "CIBO testes/TESTE fusion_kit", monta 2 clipes (um aparado), aplica zoom com motion blur nos dois, entrada/saída num
terceiro, confere as curvas lidas de volta e o comp gravado, apaga o projeto e devolve o que estava aberto.
Rode depois de mexer em qualquer script que fala com o Resolve:  python3 /Volumes/SSD/CIBO/repo/tests/fusion_kit_teste.py"""
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
for k, v in dict(timelineResolutionWidth='1080', timelineResolutionHeight='1920', timelineFrameRate='29.97', timelineInputResMismatchBehavior='scaleToCrop').items(): p.SetSetting(k, v)
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
# travas de 23/11/2026: Fusion em clipe com Pan é recusado; ciclo de .drt não pode mudar Pan/Tilt/Zoom
VH = T / 'teste_horizontal_4k.mp4'                               # bruto 16:9 em timeline 9:16 no scaleToCrop (caso da Michelle)
if not VH.exists():
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=3840x2160:rate=30000/1001:duration=4', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', str(VH)], check=True)
clh = mp.ImportMedia([str(VH)])[0]
assert mp.AppendToTimeline([{'mediaPoolItem': clh, 'startFrame': 0, 'endFrame': 90, 'trackIndex': 1, 'recordFrame': s0 + 270, 'mediaType': 1}])
d = K.itens(tl, 'CÂMERA bruto')[3]; d.SetProperty('Pan', 100.0); d.SetProperty('ZoomX', 1.2); d.SetProperty('ZoomY', 1.2)
print('Pan gravado 100, lido logo depois:', d.GetProperty('Pan'))
try:
    K.zoom(d, [(15, 1.0), (30, 1.1)], T / 'comps/d.comp'); barrou = False
except AssertionError:
    barrou = True
ok.append(barrou and d.GetFusionCompCount() == 0 and abs(float(d.GetProperty('Pan')) - 100) < 0.01)
foto = K.transforms(tl); drt = T / 'ciclo.drt'; drt.unlink(missing_ok=True)
assert tl.Export(str(drt), r.EXPORT_DRT, r.EXPORT_NONE), 'exportação .drt falhou'
nv = mp.ImportTimelineFromFile(str(drt), {'timelineName': 'TESTE drt'}); assert nv, 'importação .drt falhou'
dn = K.itens(nv, 'CÂMERA bruto')[3]; pan_drt = float(dn.GetProperty('Pan'))
fixos = K.reaplica_transforms(nv, foto, 'TESTE drt')
ok.append(abs(float(dn.GetProperty('Pan')) - 100) < 0.01 and abs(float(dn.GetProperty('ZoomX')) - 1.2) < 0.01)
print(f'Pan depois do .drt: {pan_drt} (pedido 100); regravados: {fixos}')
K.salva(pm); pm.CloseProject(p); pm.GotoRootFolder(); pm.OpenFolder('CIBO testes'); apagou = pm.DeleteProject('TESTE fusion_kit')
print('zoom clipe inteiro, zoom clipe aparado, entra/sai, shutter 360 gravado, 1 comp por clipe, Fusion+Pan barrado, Pan intacto depois do .drt:', ok, '| projeto de teste apagado:', apagou)
sys.exit(0 if all(ok) else 1)
