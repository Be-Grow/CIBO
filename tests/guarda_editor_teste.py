#!/usr/bin/env python3
"""Trava "o que o editor mexeu é dele" sem o DaVinci: timeline simulada, a CIBO marca, o editor mexe, a CIBO tem que
perceber, dizer O QUE mudou e recusar apagar. uso: python3 tests/guarda_editor_teste.py"""
import os, sys, tempfile
from pathlib import Path
os.environ['CIBO_TIMELINES'] = str(Path(tempfile.mkdtemp()) / 'tl.json')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/reel-motion/scripts'))
import guarda_editor as G


class It:
    def __init__(s, n, a, b, zoom=1.0): s.n, s.a, s.b, s.pr = n, a, b, {'Pan': 0.0, 'ZoomX': zoom, 'ZoomY': zoom}
    def GetName(s): return s.n
    def GetStart(s): return s.a
    def GetEnd(s): return s.b
    def GetLeftOffset(s): return 0
    def GetFusionCompCount(s): return 0
    def GetProperty(s, k): return s.pr.get(k)


class TL:
    def __init__(s, v, a): s.v, s.a = v, a
    def GetTrackCount(s, ty): return {'video': len(s.v), 'audio': len(s.a), 'subtitle': 0}[ty]
    def GetItemListInTrack(s, ty, k): return (s.v if ty == 'video' else s.a)[k - 1]
    def GetName(s): return 'r02'
    def GetUniqueId(s): return 'u1'
    def GetSetting(s, k): return '30'


class P:
    def GetName(s): return 'proj'


class MP:
    def DeleteTimelines(s, l): raise AssertionError('apagou a timeline do editor')


p = P(); tl = TL([[It('bruto.mp4', 0, 240), It('bruto.mp4', 240, 480)], [It('motion.mov', 0, 480)]], [[It('voz.wav', 0, 480)]])
G.marca(p, tl)
assert G.o_que_mudou(p, tl) == [] and not G.editor_mexeu(p, tl)[0], 'acusou mudança sem o editor mexer'
tl.v[0][1].b = 440; tl.v[0][0].pr['ZoomX'] = 1.2; tl.v[1][0] = It('lettering.mov', 30, 90); tl.a[0].append(It('whoosh.wav', 238, 250))
mud = ' | '.join(G.o_que_mudou(p, tl))
for esperado in ('mudou o corte', 'zoom', 'tirou "motion.mov"', 'pôs "lettering.mov"', 'A1: pôs "whoosh.wav"'):
    assert esperado in mud, f'não percebeu: {esperado} ({mud})'
try:
    G.apaga(MP(), p, tl, 'reimporto'); raise AssertionError('deixou apagar')
except G.EditorMexeu:
    pass
print('OK guarda_editor: percebe, descreve e não apaga o que o editor mexeu')
