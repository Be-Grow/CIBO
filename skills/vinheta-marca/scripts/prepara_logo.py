#!/usr/bin/env python3
"""Recorta a logo (PNG com alpha) em faixas horizontais — símbolo, nome, assinatura — para animar
cada uma no seu tempo, e grava cada faixa com margem transparente (evita a borda retangular quando
glow/blur/drop-shadow passam do limite da imagem).

Uso: prepara_logo.py LOGO.png PASTA_PUBLIC [--pad 120] [--gap 10]
Saída: PASTA_PUBLIC/logo_part0.png ... e PASTA_PUBLIC/logo.json (lido pelo config.ts do template).
A 1ª faixa (de cima) é tratada como símbolo. Prefira a versão HORIZONTAL da logo (símbolo em cima,
nome numa linha, assinatura embaixo) para 16:9; confira a folha impressa no fim.
"""
import argparse, json, os
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('logo'); ap.add_argument('public')
ap.add_argument('--pad', type=int, default=120)
ap.add_argument('--gap', type=int, default=10, help='linhas vazias mínimas entre faixas')
a = ap.parse_args()

im = Image.open(a.logo).convert('RGBA')
al = np.array(im)[:, :, 3] > 20
rows = al.sum(1) > 0
bands, s, empty = [], None, 0
for y, r in enumerate(rows):
    if r:
        if s is None: s = y
        empty = 0
    elif s is not None:
        empty += 1
        if empty >= a.gap:
            bands.append((s, y - empty + 1)); s = None; empty = 0
if s is not None: bands.append((s, len(rows)))
if len(bands) < 2:
    print('AVISO: só 1 faixa — o símbolo encosta no texto. Use a logo horizontal ou recorte à mão.')

cols = np.where(al.any(0))[0]
cx = (cols[0] + cols[-1] + 1) / 2
top0 = bands[0][0]
parts = []
os.makedirs(a.public, exist_ok=True)
for k, (y0, y1) in enumerate(bands):
    sub = al[y0:y1]
    xs = np.where(sub.any(0))[0]
    x0, x1 = xs[0], xs[-1] + 1
    crop = im.crop((x0, y0, x1, y1))
    out = Image.new('RGBA', (crop.width + 2 * a.pad, crop.height + 2 * a.pad), (0, 0, 0, 0))
    out.paste(crop, (a.pad, a.pad))
    f = f'logo_part{k}.png'
    out.save(os.path.join(a.public, f))
    parts.append({'file': f, 'w': int(x1 - x0), 'h': int(y1 - y0), 'top': int(y0 - top0), 'dx': float((x0 + x1) / 2 - cx)})
    print(f'{f}: {x1 - x0}x{y1 - y0} top={y0 - top0} dx={(x0 + x1) / 2 - cx:+.0f}')
meta = {'srcW': int(cols[-1] + 1 - cols[0]), 'srcH': int(bands[-1][1] - top0), 'pad': a.pad, 'parts': parts}
json.dump(meta, open(os.path.join(a.public, 'logo.json'), 'w'), indent=1)
print('logo.json gravado:', len(parts), 'faixas')
