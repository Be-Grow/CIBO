#!/usr/bin/env python3
"""Contraste WCAG dos pares texto/fundo de um tema do reel-motion.
uso: contraste.py temas/<tema>.json   (sai com erro se algum par fica abaixo do mínimo)"""
import json, sys
from pathlib import Path

D = {'paper': '#F2ECE4', 'paper2': '#E9E1D6', 'ink': '#2B2522', 'ink2': '#6E625B', 'terra': '#D9694A', 'terraDark': '#B9533A',
     'peach': '#FFC7A8', 'white': '#FFFBF5', 'video': '#FFFBF5', 'onAccent': '#FFFBF5', 'pill': '#FFFBF5', 'bg': '#0f0d0c'}
# (texto, fundo, mínimo, onde aparece)
PARES = [('ink', 'paper', 4.5, 'texto do painel'), ('ink', 'paper2', 4.5, 'texto do painel (degradê)'),
         ('ink2', 'paper', 4.5, 'rótulo secundário'), ('terra', 'paper', 3.0, 'destaque em título grande'),
         ('ink', 'white', 4.5, 'texto em card claro'), ('white', 'ink', 4.5, 'texto em card invertido'),
         ('onAccent', 'terra', 4.5, 'pílula/card de destaque'), ('ink', 'pill', 4.5, 'pílula'),
         ('video', 'terraDark', 4.5, 'faixa da capa / título sobre faixa')]


def hexrgb(h):
    h = h.strip()
    if h.startswith('rgba') or h.startswith('rgb'):
        return [float(v) / 255 for v in h[h.index('(') + 1:-1].split(',')[:3]]
    h = h.lstrip('#')[:6]
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def lum(c):
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = map(f, hexrgb(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


th = json.load(open(sys.argv[1]))
C = {**D, **th.get('theme', {}).get('colors', {})}
ruim = 0
for a, b, m, onde in PARES + [tuple(x) for x in th.get('pares_extra', [])]:
    r = ratio(C[a], C[b]); ok = r >= m; ruim += not ok
    print(f"{'OK ' if ok else 'BAIXO'} {r:5.2f}:1 (mín {m}) {a} {C[a]} sobre {b} {C[b]} — {onde}")
sys.exit(1 if ruim else 0)
