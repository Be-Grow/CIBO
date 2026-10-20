#!/usr/bin/env python3
"""Rastreio do rosto para o recorte 9:16 acompanhar quem fala numa gravação com câmera de mão ou pessoa que se mexe
(Andreia 01, 19/10/2026: com recorte fixo o rosto saía pela direita aos 28–46 s).
Detecta o rosto (YuNet) a cada 0,2 s no quadro já girado, tira os falsos (mediana) e suaviza como câmera virtual
(gaussiana de 0,7 s + zona morta). Grava [[t_fonte, cx, cy], …] em px do quadro girado.
uso: rastreio.py FONTE saida.json [--rotate cclock|clock] [--a A --b B]"""
import argparse, json, subprocess
from pathlib import Path
import numpy as np, cv2

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--rotate', default='')
ap.add_argument('--a', type=float, default=0); ap.add_argument('--b', type=float, default=0); ap.add_argument('--fps', type=float, default=5)
A = ap.parse_args()
rot = {'cclock': 'transpose=2,', 'clock': 'transpose=1,'}.get(A.rotate, '')
iw, ih = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', A.src],
                                 capture_output=True, text=True).stdout.strip().split(',')[:2])
if rot:
    iw, ih = ih, iw
s = 960 / iw; W, H = 960, round(ih * s / 2) * 2
cmd = ['ffmpeg', '-v', 'error'] + (['-ss', str(A.a)] if A.a else []) + ['-i', A.src] + (['-t', str(A.b - A.a)] if A.b else []) + \
      ['-vf', f'{rot}fps={A.fps},scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
raw = subprocess.run(cmd, capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
det = cv2.FaceDetectorYN.create(str(Path.home() / '.cache/yunet/face_detection_yunet_2023mar.onnx'), '', (W, H), 0.6, 0.3, 5000)
ts, xs, ys = [], [], []
for i, f in enumerate(fr):
    _, fs = det.detect(f)
    if fs is not None and len(fs):
        x, y, w, h = max(fs, key=lambda r: r[2] * r[3])[:4]
        ts.append(A.a + i / A.fps); xs.append((x + w / 2) / s); ys.append((y + h / 2) / s)
ts, xs, ys = map(np.array, (ts, xs, ys))
print(f'{len(ts)}/{len(fr)} quadros com rosto')
def med(v, k=5):
    p = np.pad(v, k // 2, mode='edge'); return np.array([np.median(p[i:i + k]) for i in range(len(v))])
xs, ys = med(xs), med(ys)
T = np.arange(A.a, A.a + len(fr) / A.fps, 1 / A.fps)
X, Y = np.interp(T, ts, xs), np.interp(T, ts, ys)
# zona morta: só anda quando o rosto sai ±40 px do alvo (o recorte não "nada" com cada gesto)
cam = [X[0]]
for v in X[1:]:
    d = v - cam[-1]; cam.append(cam[-1] + (d - np.sign(d) * 40 if abs(d) > 40 else 0))
sig = 0.7 * A.fps; k = np.arange(-3 * sig, 3 * sig + 1); g = np.exp(-k ** 2 / (2 * sig ** 2)); g /= g.sum()
Xs = np.convolve(np.pad(cam, len(k) // 2, mode='edge'), g, 'valid')[:len(T)]
Ys = np.convolve(np.pad(Y, len(k) // 2, mode='edge'), g, 'valid')[:len(T)]
json.dump([[round(float(t), 3), round(float(x), 1), round(float(y), 1)] for t, x, y in zip(T, Xs, Ys)], open(A.out, 'w'))
print(f'cx {Xs.min():.0f}–{Xs.max():.0f} (mediana {np.median(Xs):.0f}), cy mediana {np.median(Ys):.0f}')
