#!/usr/bin/env python3
"""Devolve cada clipe de áudio à sua faixa (A1 câmera, A2 voz, A3/A4 SFX; trilha intocada) sem render.
Nasceu do r03 (09/11/2026): corta_trecho embaralhou câmera/voz/SFX entre A1–A4 depois da emenda.
Clipe fora do lugar: desvincula do vídeo, guarda mídia + entrada/saída da fonte + posição, apaga e recoloca
(AppendToTimeline com trackIndex/recordFrame, endFrame exclusivo). uso: arruma_audio.py "TIMELINE" [--dry]"""
import sys, DaVinciResolveScript as d
NOME, DRY = sys.argv[1], '--dry' in sys.argv
p = d.scriptapp('Resolve').GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
tl = [p.GetTimelineByIndex(i + 1) for i in range(p.GetTimelineCount()) if p.GetTimelineByIndex(i + 1).GetName() == NOME][0]
p.SetCurrentTimeline(tl)
def tipo(it):
    n = it.GetMediaPoolItem().GetName() if it.GetMediaPoolItem() else ''
    return 'cam' if n.startswith('cam1_') else 'voz' if n.startswith('voz__') else 'trilha' if n.startswith('trilha__') else 'sfx'
ALVO = {'cam': [1], 'voz': [2], 'sfx': [3, 4]}
ocup = {k: [] for k in range(1, 5)}; mover = []
for k in range(1, 5):
    for it in tl.GetItemListInTrack('audio', k) or []:
        t = tipo(it)
        if t in ALVO and k in ALVO[t]: ocup[k].append((it.GetStart(), it.GetEnd()))
        elif t in ALVO: mover.append((k, t, it))
print(f'{len(mover)} clipe(s) fora da faixa:', {t: sum(1 for _, x, _ in mover if x == t) for t in ALVO})
if DRY: sys.exit()
info = []
for k, t, it in mover:
    info.append(dict(t=t, mpi=it.GetMediaPoolItem(), s=it.GetSourceStartFrame(), dur=it.GetDuration(), rec=it.GetStart()))
    tl.SetClipsLinked([it], False)
print('apagados:', tl.DeleteClips([it for _, _, it in mover], False))
falhas = 0
for c in sorted(info, key=lambda c: c['rec']):
    a, b = c['rec'], c['rec'] + c['dur']
    tr = next((k for k in ALVO[c['t']] if all(b <= x or a >= y for x, y in ocup[k])), ALVO[c['t']][-1])
    r = mp.AppendToTimeline([{'mediaPoolItem': c['mpi'], 'startFrame': c['s'], 'endFrame': c['s'] + c['dur'],
                              'trackIndex': tr, 'recordFrame': a, 'mediaType': 2}])
    if r: ocup[tr].append((a, b))
    else: falhas += 1
print('recolocados:', len(info) - falhas, 'falhas:', falhas)
for k, n in [(1, 'ÁUDIO câmera (ref.)'), (2, 'VOZ'), (3, 'SFX'), (4, 'SFX')]: tl.SetTrackName('audio', k, n)
for k in range(1, 5):
    its = tl.GetItemListInTrack('audio', k) or []
    print(k, tl.GetTrackName('audio', k), len(its), sorted({tipo(i) for i in its}))
