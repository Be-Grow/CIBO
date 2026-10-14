#!/usr/bin/env python3
"""Mede, no MP4 final, o quadro em que o NOME da logo aparece e o instante em que o som salta,
e diz a diferença. Use antes de entregar e sempre que o cliente falar "a música entra cedo/tarde".

Uso: sincronia.py VIDEO.mp4 [--de 11.0] [--ate 12.5] [--regiao 1120:135:400:530]
  --regiao  crop w:h:x:y da faixa do nome (padrão = wordmark da vinheta 1080p do template)
Para passar: |diferença| <= 33 ms (1 quadro a 30 fps). LPA v5: nome 11,767 s, som 11,780 s (+13 ms).
"""
import argparse, subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('--de', type=float, default=11.0); ap.add_argument('--ate', type=float, default=12.5)
ap.add_argument('--regiao', default='1120:135:400:530')
a = ap.parse_args()
d = a.ate - a.de
w, h = map(int, a.regiao.split(':')[:2])
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a.de), '-t', str(d), '-i', a.video, '-vf', f'crop={a.regiao},format=gray',
                      '-f', 'rawvideo', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).mean((1, 2))
vis = a.de + int(np.argmax(fr - fr[:3].mean() > 15)) / 30
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a.de), '-t', str(d), '-i', a.video, '-ac', '1', '-ar', '8000',
                                  '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
win = 80  # 10 ms
e = np.array([20 * np.log10(np.sqrt((x[i:i + win] ** 2).mean()) + 1e-9) for i in range(0, len(x) - win, win)])
k0 = int((vis - a.de) * 100)
base = e[max(0, k0 - 40):max(1, k0 - 5)].max()  # som nos 0,4 s antes do nome
jump = np.where(e[max(0, k0 - 40):] > base + 4)[0]
aud = a.de + (max(0, k0 - 40) + int(jump[0])) * 0.01 if len(jump) else float('nan')
if not len(jump):
    raise SystemExit(f'nome aparece {vis:.3f}s | som NÃO salta: já estava alto antes do nome (música entrou cedo demais) — FORA')
dif = 1000 * (aud - vis)
print(f'nome aparece {vis:.3f}s | som salta {aud:.3f}s | diferença {dif:+.0f} ms ' + ('ok' if abs(dif) <= 33 else 'FORA (> 1 quadro)'))
