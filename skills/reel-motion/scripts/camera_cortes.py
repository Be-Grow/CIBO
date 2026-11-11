#!/usr/bin/env python3
"""Câmera de YouTube nos cortes (Bruno, 11/11/2026: "zoom in que no corte volta pro que era" e "num corte pula pra um zoom
maior e depois volta"). Planeja um estado de câmera POR TAKE e grava em reel.json "camera_moves" (lidos pelo davinci.py,
keyframes no bruto no Resolve, ancorados no rosto, sem render):
  aberto   = enquadramento normal, parado
  empurra  = zoom in lento durante o take inteiro; no corte volta seco para o aberto (nunca zoom out)
  fechado  = no corte salta para um zoom maior e fica; no corte seguinte volta
Regras: nunca o mesmo estado duas vezes seguidas; take curto (< --curto s, lasca/remendo) herda o estado do anterior para não
piscar; take longo (> --longo s) nunca fica parado aberto (vira empurra). Sem zoom além da escala nativa: a soma fica abaixo
de --teto (bruto 4K em timeline 1080 aguenta 2,0).
uso: camera_cortes.py PROJ rNN [--push 0.07] [--salto 0.16] [--curto 2.5] [--longo 16] [--ver]"""
import argparse, json, sys
from pathlib import Path

a = argparse.ArgumentParser(); a.add_argument('proj'); a.add_argument('reel')
a.add_argument('--push', type=float, default=0.07); a.add_argument('--salto', type=float, default=0.16)
a.add_argument('--curto', type=float, default=2.5); a.add_argument('--longo', type=float, default=16.0)
a.add_argument('--teto', type=float, default=1.3); a.add_argument('--ver', action='store_true')
A = a.parse_args()
W = Path(A.proj) / '04_work' / A.reel
S = json.load(open(W / 'segs.json')); S = S.get('segs', S) if isinstance(S, dict) else S
# fronteiras em QUADROS, com a mesma conta do davinci.py (fr(acc)): o estado troca meio quadro antes do 1º quadro do take,
# senão sobra 1 quadro aberto antes do salto (visto no YT 01) ou o zoom vaza para o último quadro do take anterior
_c = json.load(open(W / 'reel.json')); FD = 1 / 30 if str(_c.get('fps', '')) in ('30', '30.0') else 1001 / 30000
t = 0.0; takes = []; borda = []
for s, e in S:
    q0, q1 = max(0, round(t / FD)), max(0, round((t + e - s) / FD))
    takes.append((t, t + e - s)); borda.append(((q0 - 0.5) * FD, (q1 - 0.5) * FD)); t += e - s
CICLO = ['empurra', 'fechado', 'aberto', 'fechado', 'empurra', 'aberto']
plano, ant, k = [], None, 0
for i, (s, e) in enumerate(takes):
    d = e - s
    if d < A.curto and ant:                       # lasca: mantém o que estava (sem piscar zoom num remendo de meio segundo)
        est = 'fechado' if ant == 'fechado' else 'aberto'
        plano.append(est); continue
    est = CICLO[k % len(CICLO)]; k += 1
    if est == ant:
        est = CICLO[k % len(CICLO)]; k += 1
    if est == 'aberto' and d > A.longo:
        est = 'empurra'
    if i == len(takes) - 1:
        est = 'aberto'                            # encerramento parado
    plano.append(est); ant = est
mv = []
for (s, e), (b0, b1), est in zip(takes, borda, plano):
    if est == 'empurra':
        mv.append({'t': round(b0, 5), 'kind': 'zoom', 'amount': min(A.push * max(1.0, min(2.0, (e - s) / 12)), A.teto - 1), 'until': round(b1 - 0.0005, 5), 'hold_until': round(b1 - 0.0005, 5), 'estado': est})
    elif est == 'fechado':
        mv.append({'t': round(b0 - 0.0004, 5), 'kind': 'zoom', 'amount': A.salto, 'until': round(b0, 5), 'hold_until': round(b1 - 0.0005, 5), 'estado': est})
from collections import Counter
print(f'{len(takes)} takes:', dict(Counter(plano)), '| sequência:', ' '.join(p[0].upper() for p in plano))
if A.ver:
    sys.exit(0)
c = json.load(open(W / 'reel.json')); c['camera_moves'] = mv; c['camera_davinci'] = True
json.dump(c, open(W / 'reel.json', 'w'), ensure_ascii=False, indent=1)
print(f'gravado em reel.json: {len(mv)} movimentos (empurra +{A.push:.0%} por ~12 s, salto +{A.salto:.0%}); depois: reel.py PROJ {A.reel} davinci')
